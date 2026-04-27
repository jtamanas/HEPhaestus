# Router Contract Audit — `/dark-matter-constraints` WS-1

**Produced by:** WS-1 cycle-1 (output-contract verification)
**Branch:** `dmc/ws1-r1-20260425`
**Status:** committed; survives run-dir reaping

---

## Purpose

`router_contract.json` is a load-bearing manifest that enumerates every cross-tool field name, config key, and status enum that the `/dark-matter-constraints` router consumes from its three producer skills (`/maddm`, `/micromegas`, `/drake`). The manifest exists because field-name drift between router and producer is silent by default: the router reads a JSON key that the producer has renamed, gets `null`, and the pipeline continues without surfacing the mismatch. `router_contract.json` makes this contract machine-checkable: `test_router_contract.py` fails loudly when reality and manifest disagree, giving WS-4 helpers a stable foundation to build against without inventing field names.

---

## Scope (9 entries)

The manifest's `output_fields` section contains **9 entries**: 4 from MadDM, 4 from micrOMEGAs, and 1 from DRAKE. This mirrors the router's Step 4 cross-check table (`SKILL.md` lines 136–141), which surfaces four observables (Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩(v→0)) for two producers (MadDM and micrOMEGAs), plus one DRAKE Ωh² row from Step 5.

The neutron cross-section rows (σ_SI(n) and σ_SD(n) from micrOMEGAs) are **out of scope today**: they are already covered by `plugins/shared/schemas/tests/test_scattering_schema.py` through the `scattering/v1` contract, and the router's Step 4 table does not surface neutron rows in the user-facing cross-check output. WS-4 W4-G defines the promotion path: if WS-4 adds neutron rows to the router's Step 4 table, the manifest extends to 11 entries (4+6+1) and the T1 gate suite must be re-run.

---

## Drift policy

When `test_router_contract.py` detects a mismatch between the manifest and reality, it fails with one of six classified drift codes. Each code names the failure mode unambiguously so the manager can triage and WS-4 can act.

`DRIFT_PRODUCER_DOC_GAP` fires when the manifest says a field is in a producer schema or SKILL.md, but it cannot be found there — for example, if a field documented in `router_contract.json` is absent from `scattering.schema.json`'s `properties`, or absent from the producer SKILL.md reading section. `DRIFT_PRODUCER_RENAMED` fires when the producer SKILL.md has renamed a field and the manifest entry is stale. `DRIFT_ROUTER_INVENTED_NAME` fires when the router uses a field name that no producer documents — the default-cynical interpretation is that the router is wrong and must be brought to the producer's name. `DRIFT_DOCUMENTED_BUT_ABSENT` fires when a field is documented in the producer SKILL.md but missing from the real-run fixture — the entry's `audit_status` becomes `documented_but_absent` and the test asserts the row is gated. `DRIFT_PRESENT_BUT_UNDOCUMENTED` fires when a fixture contains a field nobody documents — the test soft-warns (does not fail), the audit report records `UNDOCUMENTED_OUTPUT_FIELD`, and the manager decides whether to adopt or ignore; undocumented fields could be model-class-specific and must not be silently promoted. `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY` fires when two lines in the same SKILL.md contradict each other about a field name — the confirmed case today is `maddm/SKILL.md` line 164 (`sigmav_xf`) vs line 176 (`sigmav_total`); the test xfails this row until WS-4 W4-C reconciles it.

No drift code triggers an auto-fix on either side of the contract. The test fails loudly; the manager and WS-4 own the resolution.

---

## Pending rows (xfail policy)

Four manifest entries carry `audit_status` values starting with `pending_`. Each corresponds to a known gap that WS-4 must close before the entry can be promoted to `verified_*` or `schema_pinned`. The test suite xfails one dedicated test per pending entry; xfail reasons all contain the string `"WS-4"` so the acceptance gate can grep for them.

**`pending_producer_doc_fix` — row 4: `sigmav_total` from MadDM.** `maddm/SKILL.md` line 176 emits `sigmav_total` in the JSON dict, and the router reads `sigmav_total` (Step 4, line 141). However, line 164 of the same SKILL.md reads-section documents the field as `sigmav_xf`. This is `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`. The synthetic fixture uses `sigmav_total` (the canonical name the router actually reads). WS-4 W4-C must reconcile line 164 to match line 176; once fixed, this row's `audit_status` promotes to `verified_against_synthetic`.

**`pending_schema` — row 5: `omega_h2` from micrOMEGAs stdout.** micrOMEGAs emits Ωh² on stdout via `Omega h^2 = <value>` (a `stdout_regex` parse). There is no `relic/v1` schema today that machine-checks this field. WS-4 W4-A/W4-B must deliver `plugins/shared/schemas/relic.schema.json`; once it exists and the micrOMEGAs SKILL.md documents `relic.json` as a per-run output, this row promotes to `schema_pinned`.

**`pending_schema` — row 8: `sigma_v_zero` from micrOMEGAs stdout.** micrOMEGAs emits ⟨σv⟩(v→0) on stdout via `sigma_v(v=0) = <value> cm^3/s`. There is no `annihilation/v1` schema today. WS-4 W4-A/W4-B must deliver `plugins/shared/schemas/annihilation.schema.json`; once it exists, this row promotes to `schema_pinned`.

**`pending_producer_topology_fix` — `drake_install_detect_status` enum.** The router's Step 5 Branch 2 consumes `activation_required` from `/drake-install detect` output. However, `drake/SKILL.md` lines 84–86 state that `detect` returns only `configured`, `found`, or `missing`; `activation_required` is emitted by `use-path`. The status table in `drake/SKILL.md` therefore does not list `activation_required` as a valid `detect` return value, creating a topology mismatch. WS-4 W4-E must reconcile by either extending `/drake-install detect` to emit `activation_required` (preferred), or by rewriting the router's Branch 2 to read `activation_required` from `use-path` rather than `detect`.

---

## Schema fix plan deferred to WS-4

The existing `scattering/v1` schema (`plugins/shared/schemas/scattering.schema.json`) covers only the four nucleon cross-section fields for the `scatter` subcommand. The Ωh² and ⟨σv⟩(v→0) fields from micrOMEGAs stdout have no machine-checked schema today.

WS-4 will deliver two new sibling schemas: `plugins/shared/schemas/relic.schema.json` (schema version `relic/v1`, containing `omega_h2`, `xf`, `m_dm_gev`, `source`, `source_run`, `cosmology`) and `plugins/shared/schemas/annihilation.schema.json` (schema version `annihilation/v1`, containing `sigma_v_zero`, `channel_fractions`, `m_dm_gev`, `source`, `source_run`). Both schemas permit `null` for their primary observable field so that `OMEGA_UNCONVERGED` and absent-field cases round-trip cleanly without a schema violation.

A `scattering/v2` approach was explicitly rejected: bumping the existing schema would force `/ddcalc` (the current `scattering/v1` consumer) to validate against a schema containing relic and annihilation fields that `/ddcalc` has no business reading. Three pinned schemas — one per physical observable category — keep each consumer's contract tight. WS-1 scopes the schema shape; WS-4 commits the files.

---

## Symlink convention

The two micrOMEGAs fixtures (`summary_singletDM.json` and `stdout_synthetic.txt`) are symlinked from the producer skill's test fixtures directory rather than copied. The symlinks use **relative paths** with exactly four levels of `../` from `plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/fixtures/micromegas/` up to `plugins/hep-ph-toolkit/skills/`, then forward into `micromegas/tests/fixtures/<file>`. Relative symlinks survive worktree relocation because both the link and the target move together within the git tree. If a future platform or toolchain breaks relative symlinks (e.g., a Windows CI runner without symlink developer-mode enabled), the mitigation is to switch to git-tracked copies and accept the duplication; the T2 acceptance gate verifies both that the symlink is relative (`readlink` matches `^\.\./\.\./`) and that it resolves to the correct producer fixtures directory. WS-1 adopts relative cross-skill symlinks as the canonical convention for consumer-side fixtures that have authoritative producer-side copies.

---

## Out-of-scope and WS-4 hand-off

WS-1 does not modify any producer SKILL.md, does not ship `relic.schema.json` or `annihilation.schema.json`, does not wire the test into CI (WS-2), and does not run real MadDM (WS-3 catches). The following edits are explicitly queued for WS-4 to re-derive and execute against the live worktree at WS-4 start:

- **W4-A:** `plugins/hep-ph-toolkit/skills/micromegas/SKILL.md` — add `relic.json` (validated against `relic/v1`) and `annihilation.json` (validated against `annihilation/v1`) to the per-run output table (line 99 area) and schema example blocks (line 226 area). Closes the two `pending_schema` xfails once `relic/v1` and `annihilation/v1` ship.
- **W4-B:** Ship `plugins/shared/schemas/relic.schema.json` and `plugins/shared/schemas/annihilation.schema.json` per the shapes specified in `brainstorm/ws1_synthesis.md` §4. Same closure as W4-A.
- **W4-C:** `plugins/hep-ph-toolkit/skills/maddm/SKILL.md` line 164 — reconcile from the legacy annihilation field name to `sigmav_total` (matches line 176's emitted JSON and the router's Step 4 table). Closes the `pending_producer_doc_fix` xfail for row 4.
- **W4-D:** `plugins/hep-ph-toolkit/skills/dark-matter-constraints/SKILL.md` Step 5 Branch 2 (~line 213) — make DRAKE's Ωh² field name explicit (`omega_h2`, lowercase, matching `drake/SKILL.md` line 207's emitted dict). No xfail closure — this is a clarity edit.
- **W4-E:** `plugins/hep-ph-toolkit/skills/drake/SKILL.md` lines 84–86 — either extend `detect` to emit `activation_required` (preferred), or change the router's Step 5 Branch 2 to read `activation_required` from `use-path` output. Closes the `pending_producer_topology_fix` xfail for the `drake_install_detect_status` enum.
- **W4-F:** Author `verify_router_field_contract`, `check_prereqs`, `detect_drake`, `extract_field` helpers per `brainstorm/ws1_synthesis.md` §7 helper boundary. These helpers consume `router_contract.json`; they must not hardcode any field name found in the manifest.
- **W4-G:** If WS-4 surfaces neutron rows in the router's Step 4 cross-check table, extend the manifest from 9 to 11 entries (4+6+1) and re-run the T1 gate suite.

Additionally, the scan-mode CSV columns (`sigma_si_p`, `sigma_sd_p`, `sigma_v_0` in `scan_index.csv`) diverge from `scattering/v1` names (`sigma_si_proton_cm2`, etc.). WS-1 records this finding but does not gate it — scan execution is v1.1-deferred per `micromegas/SKILL.md` line 108. v1.1 must align column names before scan ships.

The real MadDM fixture replacement is forwarded to WS-3: when WS-3's dark-SU(3) playtest produces `MadDM_results.txt`, the synthetic fixture `tests/fixtures/maddm/MadDM_results_synthetic.txt` should be replaced by the real run output. WS-3's playtest report must include a "MadDM contract verification" subsection asserting fixture-vs-reality parity for the field names and regex shapes documented in this manifest.
