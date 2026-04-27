# WS-1 Audit Report — run-20260425-dmc

**Run date:** 2026-04-25
**Branch:** `dmc/ws1-r1-20260425`
**Worktree:** `/Users/yianni/Projects/hep-ph-agents-worktrees/dmc-ws1-r1`
**Status:** T1–T5 complete; T6 in progress

---

## Artifacts shipped (T1–T4)

The following files were created and committed to branch `dmc/ws1-r1-20260425`:

**`router_contract.json`** — the load-bearing manifest enumerating 9 output_fields, 3 config_keys, and 1 status_enum. Located at `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json`. The manifest is versioned `router_contract/v1` and validated against its co-located self-schema.

**`router_contract.schema.json`** — the self-schema for the manifest, co-located at `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json`. Uses JSON Schema Draft 2020-12 with `additionalProperties: false` at every object level. Contains closed enums for `audit_status` (7 literals), `produced_by` (4 literals), and `model_class_certification` (4 literals). The `source_locator` property is a `oneOf` with 4 branches (`regex`, `stdout_regex`, `schema_ref`, `json_pointer`).

**`test_router_contract.py`** — the executable contract test at `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`. 21 test functions (including 4 dedicated xfail tests for pending rows). Expected runtime: 17 PASS + 4 XFAIL. Reads manifest from `ROUTER_CONTRACT_PATH` env var if set (enables negative-control gate). All drift codes surface in assertion messages.

**`AUDIT.md`** — the permanent audit narrative at `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md`. Committed and survives run-dir reaping. Contains: Purpose, Scope, Drift policy, Pending rows, Schema fix plan, Symlink convention, Out-of-scope/WS-4 hand-off sections.

**Synthetic fixtures:**
- `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` — STRUCTURED FAKE; header present; uses canonical field names.
- `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt` — STRUCTURED FAKE; header present; Wolfram stdout shape with `Omega h^2 = 0.1197`.

**Symlinks (relative, 4 levels of ../):**
- `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json` → `../../../../micromegas/tests/fixtures/summary_singletDM.json`
- `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/stdout_synthetic.txt` → `../../../../micromegas/tests/fixtures/stdout_synthetic.txt`

---

## Live producer-doc findings

### Finding 1: `sigmav_xf` vs `sigmav_total` inconsistency in maddm/SKILL.md

`maddm/SKILL.md` line 164 (reading-section bullet for the annihilation cross-section) references the legacy field name. Line 176 (the emitted JSON dict) uses `sigmav_total`. The router's Step 4 cross-check table (`dark-matter-constraints/SKILL.md` line 141) reads `sigmav_total`. The synthetic fixture uses `sigmav_total`.

**Classification:** `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`
**Manifest status:** row 4 carries `audit_status: pending_producer_doc_fix`
**Resolution:** WS-4 W4-C must reconcile maddm/SKILL.md line 164 to the canonical field name `sigmav_total`.

### Finding 2: `activation_required` topology gap in drake/SKILL.md

`drake/SKILL.md` lines 84–86 explicitly note that `activation_required` is emitted by `use-path`, not `detect`. The `detect` subcommand's status table (lines 76–83) lists only `configured`, `found`, `missing`. The router's Step 5 Branch 2 (`dark-matter-constraints/SKILL.md` line 205) branches on `activation_required` from what the context implies is a `detect` invocation.

The `detect` table in drake/SKILL.md does NOT list `activation_required` as a row. This is the topology mismatch that the xfail test `test_drake_install_detect_documents_subset` checks: it looks for `activation_required` as a pipe-delimited table row in the detect section, and correctly fails (XFAIL) because it is only in a Note, not in the table.

**Classification:** `pending_producer_topology_fix` on `drake_install_detect_status` status_enum
**Resolution:** WS-4 W4-E must either extend `/drake-install detect` to emit `activation_required`, or rewrite router Step 5 Branch 2 to read `activation_required` from `use-path` output.

### Finding 3: scan_index.csv column-name drift

`micromegas/SKILL.md` line 104 defines `scan_index.csv` columns including `sigma_si_p`, `sigma_sd_p`, `sigma_v_0`. These names diverge from `scattering/v1`'s `sigma_si_proton_cm2`, `sigma_sd_proton_cm2`. Scan execution is v1.1-deferred per `micromegas/SKILL.md` line 108.

**Classification:** `UNDOCUMENTED_OUTPUT_FIELD` (scan column naming not gated by contract test)
**Resolution:** Not gated in WS-1. v1.1 must align column names before scan ships. AUDIT.md records the finding; no manifest entry added (scan is v1.1-deferred per plan §7).

### Finding 4: undocumented fields in MadDM synthetic fixture

The MadDM synthetic fixture contains `sigma_SI_neutron`, `sigma_SI_proton`, `sigma_SD_neutron`, `sigma_SD_proton` fields (using the MadDM SKILL.md naming convention with underscores and SI/SD capitalization). These field names are present in maddm/SKILL.md's reading section but are NOT in the manifest's `output_fields` because the router's Step 4 cross-check table does not surface the neutron rows or the raw SI/SD field names (the manifest uses `sigma_si_proton` / `sigma_sd_proton` lowercase as router-consumed names). The test `test_no_undocumented_fields_in_fixtures` soft-warns with `DRIFT_PRESENT_BUT_UNDOCUMENTED` for `sigma_SD_neutron`, `sigma_SD_proton`, `sigma_SI_neutron`, `sigma_SI_proton`.

**Classification:** `DRIFT_PRESENT_BUT_UNDOCUMENTED`
**Resolution:** These are valid MadDM output fields that the manifest intentionally excludes (neutron rows are out of scope per adjudication §9 row 1). WS-4 W4-G defines the promotion path if neutron rows are added to the router table. Manager: no action required unless WS-4 promotes neutron rows.

---

## Negative-control gate outcome

The negative-control gate was run successfully:

1. The manifest was cloned to `/tmp/router_contract_mutated.json`.
2. The first output_fields entry's `field_name` was mutated to `"WRONG_NAME_DELIBERATE"`.
3. `test_router_contract.py` was run against the mutated clone via `ROUTER_CONTRACT_PATH` env var.
4. The test exited nonzero (RC=1). Drift codes surfaced in the output:
   - `DRIFT_ROUTER_INVENTED_NAME: field 'WRONG_NAME_DELIBERATE' (downstream=maddm) not found as a word in router SKILL.md`
   - `DRIFT_PRODUCER_DOC_GAP` also surfaced (field not found in producer SKILL.md).
5. Re-running against the original manifest produced exit 0.

The negative-control gate confirms the contract test has real teeth.

---

## WS-3 forward gate

When WS-3 (dark-SU(3) end-to-end playtest) produces `MadDM_results.txt` from a real MadDM run, the synthetic fixture `tests/fixtures/maddm/MadDM_results_synthetic.txt` should be replaced with the real output. WS-3's playtest report must include a "MadDM contract verification" subsection asserting fixture-vs-reality parity for:
- Field names: `Omegah2`, `sigma_SI_proton`, `sigma_SD_proton`, `sigmav_total` (canonical names)
- Regex shapes: `^Omegah2\s*=`, `^sigma_SI_proton\s*=`, etc. (whitespace and capitalization stability)
- No appearance of the legacy field name in the actual MadDM 3.2+ output

---

## WS-4 forward gates

See `contracts/AUDIT.md` §"Out-of-scope and WS-4 hand-off" for the full W4-A through W4-G edit list. Closing xfails requires:

| Xfail test | Closes when |
|---|---|
| `test_pending_producer_doc_fix_maddm_sigmav_total` | maddm/SKILL.md line 164 reconciled to canonical field name (W4-C) |
| `test_pending_schema_micromegas_omega_h2` | `relic.schema.json` ships with `omega_h2` property (W4-A/W4-B) |
| `test_pending_schema_micromegas_sigma_v_zero` | `annihilation.schema.json` ships with `sigma_v_zero` property (W4-A/W4-B) |
| `test_drake_install_detect_documents_subset` | drake/SKILL.md detect TABLE includes `activation_required` (W4-E) |
