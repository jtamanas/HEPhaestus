# WS-1 Synthesis — Output-contract verification (final design)

**Synthesizer:** synthesis agent (3-agent brainstorm)
**Inputs:** `ws1_propose.md`, `ws1_critique.md`, `briefs/ROUTING_LENS.md`
**Verified independently:** `plugins/shared/schemas/scattering.schema.json` (47 lines, draft 2020-12, `additionalProperties: false`, `scattering/v1`), `plugins/shared/schemas/tests/test_scattering_schema.py` (already test-protected), `dark-matter-constraints/SKILL.md` (Step 4 table at lines 136-141; Step 5 DRAKE at lines 152-216), `maddm/SKILL.md` (output schema at lines 152-181 — internal `sigmav_xf`/`sigmav_total` drift confirmed), `micromegas/SKILL.md` (lines 226-239 schema example; lines 205-221 stdout regex contract; line 104 scan CSV columns), `drake/SKILL.md` (status enum at lines 76-86; result dict at lines 204-214).

The proposal's structural skeleton (manifest + test + audit doc, contract-as-code, fix-router-not-physics) survives. The critique's load-bearing finding — `scattering.schema.json` already exists — reshapes the manifest from "flat field-map" to "thin index that points into existing schemas where they exist." The synthesis below picks one option on each of the seven open decisions, justifies each under the routing lens, and pins the artifact list down to what WS-4 can mechanically consume.

---

## 1. Final deliverable shape

Five new artifacts. Two are load-bearing (manifest + test). One is permanent narrative (committed AUDIT.md). One is run-dir narrative (audit report). One is a synthetic fixture set under the consumer skill.

```
plugins/constraints/skills/dark-matter-constraints/
├── SKILL.md                                            (existing; documented edits flagged for WS-4)
├── contracts/
│   ├── router_contract.json                            (NEW — WS-1 — load-bearing manifest)
│   └── AUDIT.md                                        (NEW — WS-1 — permanent audit narrative)
└── tests/
    ├── __init__.py                                     (NEW)
    ├── test_router_contract.py                         (NEW — WS-1 — executable contract test)
    └── fixtures/
        ├── maddm/MadDM_results_synthetic.txt           (NEW — STRUCTURED FAKE, labelled)
        ├── micromegas/summary_singletDM.json           (NEW — symlink to producer fixture)
        ├── micromegas/stdout_synthetic.txt             (NEW — symlink to producer fixture)
        └── drake/stdout_drake_synthetic.txt            (NEW — STRUCTURED FAKE, labelled)

plugins/shared/schemas/                                 (existing schema family — extended in WS-4, NOT WS-1)
├── scattering.schema.json                              (existing; UNTOUCHED in WS-1)
├── relic.schema.json                                   (FUTURE — WS-4 deliverable, scoped here)
└── annihilation.schema.json                            (FUTURE — WS-4 deliverable, scoped here)

.shift-manager/run-20260425-dmc/state/
└── ws1_audit_report.md                                 (NEW — run-dir-only operational log)
```

**Total new artifacts in WS-1:** 1 manifest, 1 permanent AUDIT.md, 1 test, 2 synthetic fixtures, 2 fixture symlinks, 1 run-dir narrative. Schema additions (`relic.schema.json`, `annihilation.schema.json`) are *scoped* by WS-1 but *delivered* by WS-4 — WS-1 specifies the shape, WS-4 commits the file.

### Manifest shape (`router_contract.json`)

Three top-level sections corresponding to the three contract classes the critique identified. Each entry carries enough metadata that the test can dispatch a checker without further LLM judgment.

```json
{
  "schema_version": "router_contract/v1",
  "router_skill": "plugins/constraints/skills/dark-matter-constraints/SKILL.md",

  "output_fields": [
    {
      "observable": "Omega_h2",
      "downstream": "maddm",
      "field_name": "Omegah2",
      "produced_by": "agent_parsed",
      "source_artifact": "MadDM_results.txt",
      "source_locator": {"kind": "regex", "pattern": "^Omegah2\\s*=\\s*"},
      "defined_in": "plugins/monte-carlo-tools/skills/maddm/SKILL.md#reading-maddm-output",
      "fixture": "plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt",
      "audit_status": "verified_against_synthetic",
      "model_class_certification": "unproven",
      "router_table_row": "Step 4 Ωh² MadDM"
    },
    {
      "observable": "sigma_si_proton",
      "downstream": "micromegas",
      "field_name": "sigma_si_proton_cm2",
      "produced_by": "summary_json",
      "source_artifact": "summary.json",
      "source_locator": {"kind": "schema_ref", "schema": "scattering/v1", "json_pointer": "/properties/sigma_si_proton_cm2"},
      "defined_in": "plugins/shared/schemas/scattering.schema.json",
      "fixture": "plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json",
      "audit_status": "schema_pinned",
      "model_class_certification": "scatter_subcommand_only",
      "router_table_row": "Step 4 σ_SI(p) micrOMEGAs"
    }
    // ... 11 entries total — see Section 2
  ],

  "config_keys": [
    {
      "key": "config.maddm_path",
      "type": "path_or_bool",
      "writer": "/maddm-install",
      "reader": "/dark-matter-constraints SKILL.md Step 1",
      "audit_status": "documented"
    }
    // 3 config-key entries
  ],

  "status_enums": [
    {
      "enum_name": "drake_install_detect_status",
      "literals": ["configured", "found", "missing", "activation_required"],
      "writer": "/drake-install detect",
      "reader": "/dark-matter-constraints SKILL.md Step 5 Branch 2",
      "audit_status": "verified_in_writer_skill"
    }
    // 1 status-enum entry, plus the blocker codes if scope expands
  ]
}
```

The locator union (`{kind: regex|schema_ref|stdout_regex|json_pointer}`) is what makes WS-4's helpers mechanical: the helper dispatches on `kind` and never invents a parsing strategy.

---

## 2. Scope (numbered, exhaustive)

### 2a. Output fields (11 entries)

Mirrors the proposer's enumeration but augmented with `produced_by` and `source_locator`. The `produced_by` enum is `{summary_json, stdout_regex, agent_parsed, install_detect_json}`.

| # | Observable | Downstream | Field | produced_by | source_artifact |
|---|---|---|---|---|---|
| 1 | Ωh² | maddm | `Omegah2` | `agent_parsed` | `MadDM_results.txt` |
| 2 | Ωh² | micromegas | `omega_h2` | `stdout_regex` | `stdout.log` |
| 3 | σ_SI(p) | maddm | `sigma_si_proton` | `agent_parsed` | `MadDM_results.txt` |
| 4 | σ_SI(p) | micromegas | `sigma_si_proton_cm2` | `summary_json` | `summary.json` (`scattering/v1`) |
| 5 | σ_SD(p) | maddm | `sigma_sd_proton` | `agent_parsed` | `MadDM_results.txt` |
| 6 | σ_SD(p) | micromegas | `sigma_sd_proton_cm2` | `summary_json` | `summary.json` (`scattering/v1`) |
| 7 | ⟨σv⟩(v→0) | maddm | `sigmav_total` | `agent_parsed` | `MadDM_results.txt` |
| 8 | ⟨σv⟩(v→0) | micromegas | `sigma_v_zero` | `stdout_regex` | `stdout.log` |
| 9 | Ωh² | drake | `omega_h2` | `agent_parsed` | DRAKE stdout |
| 10 | σ_SI(n) | micromegas | `sigma_si_neutron_cm2` | `summary_json` | `summary.json` (`scattering/v1`) |
| 11 | σ_SD(n) | micromegas | `sigma_sd_neutron_cm2` | `summary_json` | `summary.json` (`scattering/v1`) |

Entries 10/11 are added because the existing schema requires them (`scattering/v1`'s `required` list includes both nucleons). The router doesn't currently surface neutron rows in the user-facing table, but the schema commits the contract for them, so the manifest must reflect that — otherwise WS-4's helper builds against a partial picture.

### 2b. Config keys (3 entries)

`config.maddm_path`, `config.micromegas_path`, `config.drake_path`. All read in router prereq/Step 5.

### 2c. Status enums (1 entry)

`/drake-install detect` `status` enum: `["configured", "found", "missing", "activation_required"]`. The router hard-codes literal-equality against these strings in Step 5 Branch 2; a producer-side rename would silently break routing. (Note: per `drake/SKILL.md` line 84-86, `detect` returns only `configured|found|missing` — `activation_required` comes from `use-path`. The manifest records both, with a note flagging this internal `/drake-install` topology nuance — a finding the router should clean up in WS-4.)

### 2d. Explicitly out of scope

- Numerical correctness (values, only field-name presence).
- Router blocker-code enum (`MADDM_MISSING`, `DRAKE_MISSING`, etc.) — these are router-internal, not cross-tool contracts. No drift risk; the router is the sole producer and consumer.
- Scan-mode CSV columns. Scan execution is v1.1-deferred per `micromegas/SKILL.md` line 108. The audit records the column-naming inconsistency (`sigma_si_p` vs `sigma_si_proton_cm2`) as a future drift gate but does NOT add the scan columns to the v1 manifest. **Routing-lens note: scan column names depend on choices that may be revisited in v1.1, so adding them now would commit code to a non-final contract.**
- Per-subcommand schemas for `relic`, `annihilate`, `indirect` outputs. Their existence is the *finding* that motivates the WS-4 schema split (Section 4 below). WS-1 does not commit code to currently-unwritten schemas.

---

## 3. Drift policy

**One decision: flag-only with manager adjudication, never auto-fix.** No silent edits to either side of any contract.

The lens says: "A contract between tools (field names, schemas, exit codes) → Deterministic helper (code)." Both sides are load-bearing. The proposer's "fix the router" default is wrong because it masks producer regressions (the critique's strongest point — confirmed by the `scattering.schema.json` evidence: silently bending the router to fit a producer schema gap is not a fix, it's a cover-up).

### Rule ladder

When the executable test detects drift between manifest and reality, it fails with one of these classifications:

1. **`DRIFT_PRODUCER_DOC_GAP`** — manifest says `summary.json` carries `omega_h2`, schema says it doesn't. The `omega_h2` and `sigma_v_zero` cases fall here. Action: **block WS-4 implementation until schema decision lands** (Section 4). Test fails loudly.

2. **`DRIFT_PRODUCER_RENAMED`** — producer SKILL.md renamed a field; manifest stale. Action: WS-4 manager decides whether the new name is canonical (manifest updates) or producer must revert (producer rolls back). Never auto-update the manifest.

3. **`DRIFT_ROUTER_INVENTED_NAME`** — router uses a name no producer documents. Action: same as above — manager triages. Default-cynical: the router is wrong and must be brought to the producer's name.

4. **`DRIFT_DOCUMENTED_BUT_ABSENT`** — field documented in producer SKILL.md, missing from real-run fixture. Action: manifest entry's `audit_status` becomes `documented_but_absent`; the test asserts the row is gated (either present, or annotated `optional`). Not fatal to router operation, but blocks shipping that entry as `verified`.

5. **`DRIFT_PRESENT_BUT_UNDOCUMENTED`** — fixture contains a field nobody documents. Action: do NOT add to manifest. Audit report flags `UNDOCUMENTED_OUTPUT_FIELD`; manager decides whether to document and adopt or intentionally ignore. Critical for model-agnosticism — undocumented fields could be model-class-specific (e.g. an MSSM-only block).

6. **`DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`** — e.g. MadDM `sigmav_xf` (line 164) vs `sigmav_total` (line 176). Action: audit report flags it; producer must reconcile *before* WS-4 builds against the field. Manager decides which is canonical (current evidence: `sigmav_total` is what the router uses, so it likely wins, but the test can't ratify this — the producer SKILL.md must commit to one).

The test never silently passes when reality and manifest disagree. The test never auto-updates anything. Audit narrative records the finding; manager and WS-4 own the resolution.

---

## 4. Schema/contract fix plan

The micrOMEGAs schema is the only producer-side contract that today is *machine-checked*. The proposer's recommendation (add `omega_h2` and `sigma_v_zero` to `scattering.schema.json`) is wrong on two counts: (i) `additionalProperties: false` and `"const": "scattering/v1"` mean adding fields requires a version bump or a new schema; (ii) "scattering" is the wrong category for a relic-density or annihilation field — the name is contract too.

### Decision: split into three sibling schemas, do not bump `scattering/v1`.

WS-4 will deliver:

```
plugins/shared/schemas/scattering.schema.json     (existing, UNTOUCHED — the v1 contract stands)
plugins/shared/schemas/relic.schema.json          (NEW — relic/v1)
plugins/shared/schemas/annihilation.schema.json   (NEW — annihilation/v1)
```

`relic/v1` shape (proposed by WS-1, ratified by WS-4):

```json
{
  "schema_version": {"const": "relic/v1"},
  "m_dm_gev": {"type": "number", "exclusiveMinimum": 0},
  "omega_h2": {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}]},
  "xf": {"oneOf": [{"type": "null"}, {"type": "number"}]},
  "source": {"enum": ["micromegas", "maddm", "drake"]},
  "source_run": {"type": "string", "minLength": 1},
  "cosmology": {"const": "standard_thermal"}
}
```

`annihilation/v1` shape:

```json
{
  "schema_version": {"const": "annihilation/v1"},
  "m_dm_gev": {"type": "number", "exclusiveMinimum": 0},
  "sigma_v_zero": {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}]},
  "channel_fractions": {"type": "object"},
  "source": {"enum": ["micromegas", "maddm"]},
  "source_run": {"type": "string", "minLength": 1}
}
```

`null` is permitted on the cross-section so `OMEGA_UNCONVERGED` and "field absent" cases (per `micromegas/SKILL.md` line 221) round-trip cleanly without a schema violation.

### Doc updates required (queued for WS-4, NOT WS-1)

WS-1 produces an explicit edit list. WS-1 does not perform the edits — that would be a producer-side change, and the lens says producers own their schemas.

1. `plugins/constraints/skills/micromegas/SKILL.md` — line 99: add `relic.json (validated against relic/v1)` and `annihilation.json (validated against annihilation/v1)` to the per-run output table; line 226: add `relic.json` and `annihilation.json` schema examples mirroring the existing `summary.json` example.
2. `plugins/monte-carlo-tools/skills/maddm/SKILL.md` — reconcile lines 164 (`sigmav_xf`) and 176 (`sigmav_total`); commit to `sigmav_total` (matches what the router reads).
3. `plugins/constraints/skills/dark-matter-constraints/SKILL.md` — line 213: name DRAKE's field explicitly (`omega_h2`, lowercase, matching the writer's emitted dict per `drake/SKILL.md` line 207).
4. `plugins/monte-carlo-tools/skills/drake/SKILL.md` — clarify the `activation_required` topology: it's emitted by `use-path`, but the router consumes it from `detect` *via* the merged status (see `dark-matter-constraints/SKILL.md` Step 5 Branch 2 line 205). One side must yield. Recommendation: `/drake-install detect` adopts `activation_required` so the router's branch table is accurate.

### Why three schemas, not `scattering/v2`

A `scattering/v2` carrying relic and annihilation fields would mean `/ddcalc` (the existing `scattering/v1` consumer) and the router both validate against the same omnibus schema, but `/ddcalc` has no business reading `omega_h2`. The contract gets less specific, not more. Three pinned schemas keep each consumer's contract tight and let producers emit zero, one, two, or three artifacts per run.

---

## 5. Fixture strategy

**Decision: consumer-side placement.** Fixtures live under `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/<producer>/`. Use symlinks for fixtures the producer already maintains (micrOMEGAs has both — no duplication), copy synthetics for producers that don't (MadDM, DRAKE).

### Why consumer-side

The contract is the *router's*. The fixture exists to verify *the router's* manifest, not to validate the producer's own outputs (the producer skills have their own tests). Co-locating fixtures with the test that consumes them is the lens-aligned choice — it keeps the contract test self-contained and avoids polluting producer skills with consumer-driven artifacts. Symlinks for already-existing producer fixtures avoid drift between two copies.

### Lifecycle

- **WS-1 ships:** synthetic for MadDM (`MadDM_results_synthetic.txt`, labelled `STRUCTURED FAKE` per existing micrOMEGAs convention), synthetic for DRAKE, symlinks for micrOMEGAs.
- **WS-3 produces:** real `MadDM_results.txt` from the dark-SU(3) playtest. Synthesizer commits a follow-up gate: when WS-3's run output lands, the synthetic fixture is *replaced* by the real run output (renamed, retaining the byte-stable real-MadDM format). The manifest test then auto-uses the real fixture.
- **No WS-3:** WS-1 ships with synthetic-only AND a tracked open task in the audit report. Synthesizer accepts the risk that a deferred WS-3 means we never run real MadDM under WS-1's contract; the model-agnosticism caveat (Section 6.4) compensates.

### Why no empirical MadDM run inside WS-1

See Section 6.4 below — decision is no, with explicit consequences for WS-4.

### Fixture format details

Each synthetic fixture must:
1. Carry a header comment `# STRUCTURED FAKE — synthetic fixture for router contract test, NOT a real run`.
2. Match the documented producer-side regex shape exactly (case-strict, whitespace as documented).
3. Include every field the manifest references for that producer, plus zero "extra" fields (so the test can verify both presence and *exclusivity* if the manifest declares it).

---

## 6. Per-decision resolutions

### Decision 1 — Manifest authority vs `scattering.schema.json`

**Reference, do not duplicate.** Manifest entries with `produced_by: summary_json` carry a `source_locator: {kind: schema_ref, schema: "scattering/v1", json_pointer: "/properties/<name>"}`. The test resolves the pointer against the loaded schema and asserts the field exists with the expected type. The schema remains the single source of truth for `scatter` outputs; the manifest indexes into it. This avoids two-source-of-truth drift between the manifest and the schema (the critique's #5 risk). For producers that have no schema today (MadDM, DRAKE, micrOMEGAs stdout), the manifest carries the regex/locator inline — there's nothing to reference.

### Decision 2 — Drift policy default

**Flag-only with manager adjudication.** Auto-fixing the consumer (proposer's default) masks producer regressions; auto-fixing the producer would have WS-1 silently mutate every downstream skill, which is out of WS-1's mandate. Lens-aligned default: code makes the contract loud, humans (or WS-4 with explicit decisions logged in `MANAGER_DECISIONS.md`) make the call. Rule ladder in Section 3 covers every case.

### Decision 3 — Schema fix shape for `omega_h2` / `sigma_v_zero`

**Split into `relic/v1` and `annihilation/v1` (separate schemas, sibling files). Scoped by WS-1, delivered by WS-4.** Bumping to `scattering/v2` pollutes the contract for the existing consumer (`/ddcalc`); regex-only stdout reads kill model-agnosticism (regex shape is the most fragile contract there is, per the critique's argument against the regex downgrade). Three pinned schemas, one per physical observable category, each consumer's contract stays tight.

### Decision 4 — Empirical MadDM run in WS-1 scope

**No.** Two reasons. (a) WS-1's stated charter is *contract verification*, not *empirical validation* — running MadDM blurs that line and forces WS-1 to depend on `/maddm-install` succeeding, which is a cross-WS dependency the lens says to avoid. (b) WS-3 (dark-SU(3) end-to-end playtest) WILL produce real MadDM run output, and the fixture-replacement gate (Section 5) routes it to where it's needed.

**Consequence accepted:** WS-4 must keep MadDM output parsing in the LLM, not in a deterministic helper. The manifest entries for MadDM carry `model_class_certification: "unproven"`. This costs us potentially-mechanizable code, but the lens explicitly lists `read_maddm_output` as risk-of-non-agnostic — keeping it LLM is the conservative choice. If WS-3 produces evidence of model-class invariance later, WS-4.1 can promote MadDM parsing to a helper.

**WS-3 must catch:** (i) whether MadDM's real output format matches the synthetic (any deviation = `DRIFT_PRODUCER_DOC_GAP`); (ii) whether `Omegah2` line shape (capitalization, whitespace, exponent format) is stable. WS-3's playtest report must include a "MadDM contract verification" subsection asserting fixture-vs-reality parity.

### Decision 5 — Fixture placement

**Consumer-side: `dark-matter-constraints/tests/fixtures/<producer>/`.** Lens-aligned (the contract is the router's), keeps WS-1's deliverables self-contained, avoids two copies via symlinks for already-existing producer fixtures. The proposer's producer-side placement was the wrong call — it pollutes producer skills with artifacts only WS-1 cares about.

### Decision 6 — Manifest scope

**All three classes (output_fields + config_keys + status_enums) in one manifest, three sections.** The critique was right that conflating them in a flat list is wrong; splitting into three manifests would multiply the test plumbing without value. Three sections in one JSON file gives WS-4 helpers a single load point with clear dispatch by section. `output_fields` is the largest section (11 entries); `config_keys` and `status_enums` are small (3 and 1) but cover real contracts the router currently consumes.

### Decision 7 — Audit-doc permanence

**Both.** Permanent narrative at `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` (committed; survives run-dir reaping; WS-4 references it). Run-dir-only operational log at `.shift-manager/run-20260425-dmc/state/ws1_audit_report.md` (transient; captures the live audit findings, manager decisions, drift findings as they happen during this specific run). The two files diverge after WS-1 ships: AUDIT.md is the contract narrative ("this is what the router promises"), the run-dir doc is the audit history ("this is what we found and decided"). Critic was right that run-dir-only loses information after archival.

---

## 7. Handoff to WS-4

For each WS-1 artifact, the WS-4 consumer is named explicitly. WS-4 helpers must not hardcode any of these — they read from the manifest.

| WS-1 artifact | WS-4 consumer | Mechanism |
|---|---|---|
| `router_contract.json` | `verify_router_field_contract()` helper (load + dispatch) | `json.load`; iterate `output_fields`, dispatch on `produced_by`; iterate `config_keys` for `check_prereqs()`; iterate `status_enums` for `detect_drake()` enum-literal check |
| `test_router_contract.py` | WS-2 test harness (the actual pytest invocation lives in WS-2; the test file is committed in WS-1) | WS-2 wires this into CI; WS-1 just makes it pass |
| `tests/fixtures/maddm/MadDM_results_synthetic.txt` | `read_maddm_output()` LLM-side parser (NOT a helper) | LLM uses fixture for fixture-driven parse practice; the contract test only verifies field-name presence |
| `tests/fixtures/micromegas/summary_singletDM.json` (symlink) | `extract_field()` helper for scatter path | Helper opens, validates against `scattering/v1`, extracts top-level keys |
| `tests/fixtures/drake/stdout_drake_synthetic.txt` | `read_drake_output()` LLM-side parser (NOT a helper) | Same pattern as MadDM |
| `contracts/AUDIT.md` | WS-4 SKILL.md rewrite reference | WS-4 SKILL.md cites AUDIT.md for the "why this field, why these names" narrative |
| Scoped `relic.schema.json` and `annihilation.schema.json` (specs) | WS-4 implementation deliverable (WS-4 commits the files) | WS-1 ships the spec in §4; WS-4 ships the file |

### Helper boundary that WS-1 fixes for WS-4

**Code-side (helpers WS-4 will build):**
- `verify_router_field_contract(manifest_path, fixtures_root) -> Result` — dispatches per-entry. Pure I/O + string match + jsonschema validation. Model-agnostic (string presence is invariant under model class).
- `check_prereqs(config, manifest_path) -> Result` — drives `config_keys` section. Pure file-existence.
- `detect_drake(manifest_path) -> Status` — drives the `status_enums` section. Asserts `/drake-install detect` JSON `status` is one of the manifest-listed literals; otherwise blocks. Pure tool-state check.
- `extract_field(json_path, key, schema_version) -> value` — for `summary_json` rows. Validates schema version, extracts top-level key. Safe because schema is pinned.

**LLM-side (stays as agent prose per lens):**
- `read_maddm_output()` — until model-class invariance is empirically proven (WS-3 may unblock).
- `read_drake_output()` — DRAKE produces unstructured Wolfram stdout; no contract to enforce.
- `compare_dm()` numerical adjudication — the manifest gates which rows exist; the rel-diff arithmetic is mechanical (could be code) but the "which rows are comparable" decision stays LLM until multi-component DM is in scope.

WS-4's SKILL.md rewrite must mirror this split exactly. The manifest is the canonical input; the SKILL.md prose explains the LLM-side judgment. No helper invents a field name; no LLM-side prose hard-codes one.

---

## 8. Risks accepted

Things WS-1 chose to live with rather than fix.

1. **Synthetic-only fixtures for MadDM and DRAKE.** Real-format drift (e.g. `Omegah2 = 2.92e-01` vs `Omegah2  = 2.92E-01` — two-space, capital E) won't be caught until WS-3 runs. Mitigation: case-strict, whitespace-tolerant regex in the manifest's `source_locator` (`\s*=\s*` not literal ` = `); WS-3 explicitly tasked with parity check.

2. **MadDM parsing stays LLM, not helper.** Section 6.4. We forfeit potentially-mechanizable code in exchange for not committing to a possibly-non-agnostic contract. WS-4.1 can promote later if WS-3 produces evidence.

3. **DRAKE has no real contract.** DRAKE emits unstructured Wolfram stdout. The manifest entry exists (entry #9) so the router-side comparison surfaces a known field name, but no machine check can validate DRAKE-side output. WS-1 cannot fix this; DRAKE itself would need to commit to a structured output, which is upstream work.

4. **Scan-mode CSV column drift is unaddressed.** Scan execution is v1.1-deferred; column names diverge from `scattering/v1` (`sigma_si_p` vs `sigma_si_proton_cm2`). WS-1 records the finding in AUDIT.md and audit_report.md but doesn't gate it. v1.1 must align before scan ships.

5. **`/drake-install detect` `activation_required` topology is fuzzy.** Per `drake/SKILL.md` line 84-86, `detect` returns only `configured|found|missing`; `activation_required` is `use-path`-emitted. The router's Step 5 Branch 2 reads `activation_required` from `detect`. The manifest records both literals; WS-4 must either fix the producer (extend `detect`) or fix the router (split the branches by which subcommand returned what). Synthesizer punts to WS-4 because it's a producer-side topology change, not a contract fix.

6. **Manifest schema versioning.** `router_contract/v1` is pinned in the manifest itself. If WS-4 reshapes (e.g. adds a fourth contract class), the manifest must bump to v2 in lockstep. Mitigation: manifest test asserts `schema_version == "router_contract/v1"`; bumping the schema is a deliberate, loud act.

7. **Per-subcommand schema enumeration is partial.** Only `scatter` has `scattering/v1` today; `relic` and `annihilation` schemas are *scoped* by WS-1 but *delivered* by WS-4. Until WS-4 lands those files, the manifest's entries for `omega_h2` and `sigma_v_zero` carry `audit_status: pending_schema` and the test xfails those rows with a clear message ("relic/v1 schema not yet delivered — see WS-4"). This is a known temporary state, not a permanent gap.

8. **The router's neutron-cross-section rows aren't in user-facing output.** Manifest entries 10/11 exist (because the schema requires them) but the router's Step 4 cross-check table doesn't surface neutron rows. WS-4 must decide whether to add neutron rows to the user table (cleaner contract) or leave them schema-only (cleaner UX). WS-1 records the entries; WS-4 makes the call.

---

## Closing note on routing-lens conformance

Every code-bound decision in this synthesis answers the lens question "can we guarantee model-agnosticism?" with yes, evidenced. Specifically:

- The manifest itself carries no model-specific data. Field names are invariant under MSSM vs simplified-model; that's the producer's job.
- The contract test does string-presence and JSON-pointer validation only. No physics, no model-class bifurcation.
- Helpers WS-4 builds against the manifest are the four named in §7's code-side list, all of which the lens table explicitly lists as `Safe for code` (file existence, contract-between-tools, pinned schemas).
- Everything that *might* not be model-agnostic — MadDM stdout parsing, DRAKE Wolfram stdout extraction, multi-component DM comparison — stays in the LLM per the lens, and the manifest's `model_class_certification` field flags it explicitly so WS-4 doesn't accidentally promote.

The routing lens forces the same conclusion the critique pushed toward independently: the contract IS code, but the *enforcement* is loud-fail, not silent-fix. WS-4's job is to wire the helpers; WS-1's job is to make sure the helpers have a manifest to read that doesn't lie about what's actually in the producer skills today.
