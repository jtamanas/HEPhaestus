# WS-1 Plan Draft — Output-contract verification

**Drafter:** plan-drafter agent
**Inputs consumed:**
- `.shift-manager/run-20260425-dmc/briefs/ROUTING_LENS.md`
- `.shift-manager/run-20260425-dmc/brainstorm/ws1_synthesis.md` (canonical design)
- `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (router, current state)
- `plugins/constraints/skills/micromegas/SKILL.md` (producer)
- `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (producer)
- `plugins/monte-carlo-tools/skills/drake/SKILL.md` (producer)
- `plugins/shared/schemas/scattering.schema.json` (only existing producer-side schema)
- `plugins/shared/schemas/tests/test_scattering_schema.py` (test convention to mirror)
- `plugins/constraints/skills/micromegas/tests/fixtures/` (existing producer fixture set — symlink targets)

---

## 1. Goal

Produce a **load-bearing, mechanically enforceable contract** between the `/dark-matter-constraints` router and its three producer skills (`/maddm`, `/micromegas`, `/drake`) by shipping (a) a JSON manifest that enumerates every cross-tool field/config-key/status-enum the router consumes, (b) an executable contract test that fails loudly on drift, (c) two fixture trees (synthetic for MadDM & DRAKE, symlinked for micrOMEGAs) that the test reads, (d) a permanent narrative `AUDIT.md` co-located with the manifest, and (e) a run-dir audit report capturing live findings. WS-1 does **not** author new schemas, modify producer SKILL.md prose, run real MadDM, or build any of the WS-4 helpers — it only ships the artifacts those downstream tasks consume. The synthesized design (Section 1 of `ws1_synthesis.md`) names every artifact; this plan only orders and gates them.

---

## 2. Inputs (design docs this plan consumes)

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Sets the model-agnosticism rule. Every code-bound choice in this plan must be invariant under BSM model class. |
| `brainstorm/ws1_synthesis.md` | Canonical spec. Tasks below derive directly from §1–§7 there. Do not re-decide synthesis decisions in implementation. |
| `dark-matter-constraints/SKILL.md` | Current router; source of the consumer-side field names (Step 4 table lines 136–141, Step 5 enum lines 198–207). |
| `maddm/SKILL.md` | Producer; lines 152–181 define the agent-parsed output. The `sigmav_xf` (line 164) vs `sigmav_total` (line 176) inconsistency is a logged finding. |
| `micromegas/SKILL.md` | Producer; lines 99–104 (per-run output table), 205–221 (stdout regex contract), 226–239 (`scattering/v1` example). |
| `drake/SKILL.md` | Producer; lines 76–86 (`detect` enum literals), lines 204–214 (result dict shape). |
| `scattering.schema.json` | Only producer-side schema today. Manifest `summary_json` rows reference it via JSON pointer; manifest does NOT duplicate it. |
| `shared/schemas/tests/test_scattering_schema.py` | Convention. The new contract test mirrors its `pytest`/`jsonschema.Draft202012Validator` patterns. |

---

## 3. Tasks (T1..T9)

Owner-class assignment follows the user's policy: 3 sonnet–opus cycles available, then opus–opus pairs. Mechanical authoring/JSON-shape work goes to `sonnet-implementer`; tasks needing physics or naming judgment go to `opus-implementer`.

---

### T1 — Author `router_contract.json` manifest skeleton (structure + section keys, no entries)

- **Owner class:** `sonnet-implementer`
- **Estimated cycles:** 1
- **Depends-on:** none
- **Inputs:** `ws1_synthesis.md` §1 (manifest shape example), §6.6 (manifest scope decision).
- **Outputs:**
  - `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` (NEW; create `contracts/` directory)
- **Acceptance gates** (all mechanically checkable):
  1. `test -d /Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts` → exit 0
  2. `jq -e '.schema_version == "router_contract/v1"' router_contract.json` → exit 0
  3. `jq -e '.router_skill == "plugins/constraints/skills/dark-matter-constraints/SKILL.md"' router_contract.json` → exit 0
  4. `jq -e 'has("output_fields") and has("config_keys") and has("status_enums")' router_contract.json` → exit 0
  5. `jq -e '.output_fields | type == "array"' router_contract.json` → exit 0
  6. `jq -e '.output_fields | length == 0' router_contract.json` → exit 0 (skeleton only; entries land in T3)
  7. `python -c 'import json; json.load(open(...))'` → exit 0 (parses as valid JSON)

---

### T2 — Author manifest **self-schema** (`router_contract.schema.json`) and add it to the schemas test suite

- **Owner class:** `opus-implementer` (judgment: chooses the locator-union JSON shape, decides which fields are required vs optional)
- **Estimated cycles:** 2
- **Depends-on:** T1
- **Inputs:**
  - `ws1_synthesis.md` §1 (manifest example with locator union `{kind: regex|schema_ref|stdout_regex|json_pointer}`).
  - `plugins/shared/schemas/scattering.schema.json` (style/convention).
  - `plugins/shared/schemas/tests/test_scattering_schema.py` (test pattern).
- **Outputs:**
  - `plugins/shared/schemas/router_contract.schema.json` (NEW)
  - `plugins/shared/schemas/tests/test_router_contract_schema.py` (NEW — mirrors `test_scattering_schema.py`)
- **Acceptance gates:**
  1. `jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' router_contract.schema.json` → exit 0
  2. `jq -e '.required | index("schema_version")' router_contract.schema.json` → exit 0
  3. `jq -e '.properties.output_fields.items.required | sort == ["audit_status","defined_in","downstream","field_name","fixture","model_class_certification","observable","produced_by","router_table_row","source_artifact","source_locator"] | sort' router_contract.schema.json` → exit 0 (every field from §1 example is required on every entry)
  4. `jq -e '.properties.output_fields.items.properties.produced_by.enum | sort == ["agent_parsed","install_detect_json","stdout_regex","summary_json"] | sort' router_contract.schema.json` → exit 0
  5. `jq -e '.properties.output_fields.items.properties.audit_status.enum | sort | index("pending_schema") != null' router_contract.schema.json` → exit 0 (per §7 risks #7, `pending_schema` literal MUST be allowed)
  6. `jq -e '.properties.output_fields.items.properties.audit_status.enum | index("verified_against_synthetic") != null and (.|index("schema_pinned") != null) and (.|index("documented_but_absent") != null)' router_contract.schema.json` → exit 0
  7. `jq -e '.properties.output_fields.items.properties.source_locator.oneOf | length >= 4' router_contract.schema.json` → exit 0 (locator union has ≥4 kinds: regex, schema_ref, stdout_regex, json_pointer)
  8. `pytest plugins/shared/schemas/tests/test_router_contract_schema.py` → exit 0 (self-validity + a positive sample document validates + a negative sample with extra top-level key fails — mirrors `test_scattering_schema.py` structure)

**Justification for opus-implementer:** §1 of synthesis sketches the manifest shape but does not pin the full required-field set, oneOf-locator schema, or which audit_status literals are mandatory. Implementer must read §3 (drift policy) to enumerate the audit_status enum, §6.4 to surface the `model_class_certification` enum (`unproven`, `scatter_subcommand_only`, …). Naming choices here propagate to every entry in T3 — judgment call.

---

### T3 — Populate `router_contract.json` with the 11 + 3 + 1 entries

- **Owner class:** `opus-implementer` (judgment: fills `model_class_certification` per §6.4, picks `audit_status` per row from §3 ladder)
- **Estimated cycles:** 2
- **Depends-on:** T1, T2 (manifest must validate against its self-schema)
- **Inputs:**
  - `ws1_synthesis.md` §2a (the 11 output_fields rows), §2b (3 config_keys), §2c (1 status_enum), §6.4 (model_class_certification rules), §3 (audit_status literals).
  - `dark-matter-constraints/SKILL.md` lines 136–141 (Step 4 cross-check table → router_table_row strings).
  - `maddm/SKILL.md` lines 152–181 (regex patterns for agent_parsed rows).
  - `micromegas/SKILL.md` lines 205–221 (stdout regex contract for `omega_h2`/`sigma_v_zero`).
  - `scattering.schema.json` (JSON pointers for `sigma_si_*` / `sigma_sd_*` rows).
- **Outputs:** updated `router_contract.json` (entries populated)
- **Acceptance gates:**
  1. `jq -e '.output_fields | length == 11' router_contract.json` → exit 0
  2. `jq -e '.config_keys | length == 3' router_contract.json` → exit 0
  3. `jq -e '.status_enums | length == 1' router_contract.json` → exit 0
  4. `jq -e '[.output_fields[] | .observable] | sort | unique | length == 5' router_contract.json` → exit 0 (Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩, σ_SI(n)/σ_SD(n) — 5 distinct observables across the 11 rows; entries 10 and 11 are neutron variants)
  5. `jq -e '[.output_fields[] | select(.downstream == "maddm")] | length == 5' router_contract.json` → exit 0 (rows 1, 3, 5, 7 in §2a table; verify count = 5 — Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩(v→0) — actually 4; if 4: assert 4. **Implementer reconciles §2a table count with this gate before commit.**)
  6. `jq -e '[.output_fields[] | select(.produced_by == "summary_json")] | length == 4' router_contract.json` → exit 0 (the four micrOMEGAs scatter rows: σ_SI(p,n), σ_SD(p,n))
  7. `jq -e '[.output_fields[] | select(.produced_by == "stdout_regex")] | length == 2' router_contract.json` → exit 0 (`omega_h2`, `sigma_v_zero` from micrOMEGAs stdout)
  8. `jq -e '[.output_fields[] | select(.produced_by == "agent_parsed")] | length >= 4' router_contract.json` → exit 0 (MadDM rows + DRAKE row)
  9. `jq -e '[.output_fields[] | select(.audit_status == "pending_schema")] | length == 2' router_contract.json` → exit 0 (per §7 risk #7: the two micrOMEGAs `omega_h2`/`sigma_v_zero` rows blocked on relic/v1 + annihilation/v1)
  10. `jq -e '[.output_fields[] | select(.downstream == "maddm") | .model_class_certification] | unique == ["unproven"]' router_contract.json` → exit 0 (per §6.4, every MadDM row is `unproven`)
  11. `jq -e '[.config_keys[] | .key] | sort == ["config.drake_path","config.maddm_path","config.micromegas_path"]' router_contract.json` → exit 0
  12. `jq -e '.status_enums[0].enum_name == "drake_install_detect_status"' router_contract.json` → exit 0
  13. `jq -e '.status_enums[0].literals | sort == ["activation_required","configured","found","missing"]' router_contract.json` → exit 0
  14. `python -c 'import json,jsonschema; m=json.load(open("...router_contract.json")); s=json.load(open("...router_contract.schema.json")); jsonschema.Draft202012Validator(s).validate(m)'` → exit 0 (manifest validates against T2's schema)

**Note on gate #5:** §2a's table lists 4 MadDM rows (Ωh²=1, σ_SI(p)=3, σ_SD(p)=5, ⟨σv⟩=7). The synthesis lists 11 total = 4 MadDM + 6 micrOMEGAs (4 summary_json scatter + 2 stdout_regex relic/annih) + 1 DRAKE. The implementer asserts these explicit counts.

---

### T4 — Author synthetic fixtures (MadDM + DRAKE) and symlinks (micrOMEGAs)

- **Owner class:** `sonnet-implementer` (mechanical: copy producer-documented format, add `STRUCTURED FAKE` header)
- **Estimated cycles:** 1
- **Depends-on:** T3 (must know which fields the manifest demands)
- **Inputs:**
  - `ws1_synthesis.md` §5 (fixture strategy, format details — case-strict, `STRUCTURED FAKE` header).
  - `maddm/SKILL.md` lines 152–181 (line shapes; `Omegah2 = 2.92e-01`, `sigma_SI_proton = ...`, etc.).
  - `drake/SKILL.md` lines 195–214 (DRAKE Wolfram stdout shape).
  - `plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json` (symlink target, exists).
  - `plugins/constraints/skills/micromegas/tests/fixtures/stdout_synthetic.txt` (symlink target, exists).
- **Outputs:**
  - `plugins/constraints/skills/dark-matter-constraints/tests/__init__.py` (NEW empty)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` (NEW; structured fake)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt` (NEW; structured fake)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json` (NEW; symlink → `../../../../../micromegas/tests/fixtures/summary_singletDM.json`)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/stdout_synthetic.txt` (NEW; symlink → `../../../../../micromegas/tests/fixtures/stdout_synthetic.txt`)
- **Acceptance gates:**
  1. `head -1 fixtures/maddm/MadDM_results_synthetic.txt | grep -F "STRUCTURED FAKE"` → exit 0
  2. `head -1 fixtures/drake/stdout_drake_synthetic.txt | grep -F "STRUCTURED FAKE"` → exit 0
  3. `grep -E '^Omegah2\s*=\s*[0-9]' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0
  4. `grep -E '^sigma_SI_proton\s*=' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0
  5. `grep -E '^sigma_SI_neutron\s*=' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0
  6. `grep -E '^sigma_SD_proton\s*=' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0
  7. `grep -E '^sigma_SD_neutron\s*=' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0
  8. `grep -Ei 'sigmav_total\s*=' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0 (canonical name per §4 doc-update list — synthetic must use `sigmav_total`, NOT `sigmav_xf`)
  9. `! grep -Ei 'sigmav_xf' fixtures/maddm/MadDM_results_synthetic.txt` → exit 0 (synthetic does not perpetuate the producer-doc inconsistency)
  10. `grep -Ei 'omega.{0,2}h.{0,2}\^?2' fixtures/drake/stdout_drake_synthetic.txt` → exit 0 (DRAKE Wolfram `Omega h^2` line)
  11. `test -L fixtures/micromegas/summary_singletDM.json && test -e fixtures/micromegas/summary_singletDM.json` → exit 0 (symlink exists and resolves)
  12. `test -L fixtures/micromegas/stdout_synthetic.txt && test -e fixtures/micromegas/stdout_synthetic.txt` → exit 0
  13. `python -c 'import json; json.load(open("fixtures/micromegas/summary_singletDM.json"))'` → exit 0 (symlinked JSON parses)

---

### T5 — Author executable contract test `test_router_contract.py`

- **Owner class:** `opus-implementer` (decides drift-classification mapping per §3 ladder; chooses how to xfail `pending_schema` rows)
- **Estimated cycles:** 2–3
- **Depends-on:** T2, T3, T4 (manifest schema, populated manifest, fixtures all required)
- **Inputs:**
  - `ws1_synthesis.md` §3 (drift rule ladder — every classification listed below maps to a test branch), §7 (helper consumer pattern), §8 risks #7 (`pending_schema` xfail).
  - `plugins/shared/schemas/tests/test_scattering_schema.py` (style template).
- **Outputs:**
  - `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (NEW)
- **Acceptance gates:**
  1. `pytest plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py -v` → exit 0 (all tests pass on the WS-1-shipped manifest + fixtures)
  2. `pytest -v ... | grep -c "PASSED"` ≥ 12 (every assertion in §5 below maps to ≥1 named test case)
  3. `pytest -v ... | grep -c "XFAIL"` == 2 (the two `pending_schema` rows xfail with explicit `reason="relic/v1 schema not yet delivered — see WS-4"`)
  4. **Negative-control gate:** an implementer-supplied `pytest -v` invocation with a deliberately mutated manifest copy (e.g. one row's `field_name` set to `WRONG_NAME`) must produce a FAILED result with the corresponding drift code in the failure message. Run via:
     - `cp router_contract.json /tmp/mutated.json && jq '.output_fields[0].field_name = "WRONG_NAME"' < router_contract.json > /tmp/mutated.json && ROUTER_CONTRACT_PATH=/tmp/mutated.json pytest test_router_contract.py` → exit non-zero AND stderr contains one of `DRIFT_PRODUCER_RENAMED|DRIFT_DOCUMENTED_BUT_ABSENT|DRIFT_ROUTER_INVENTED_NAME`
  5. Test imports only stdlib + `pytest` + `jsonschema` (no new dep): `! grep -E '^import (?!(json|pathlib|re|os|sys|subprocess|pytest|jsonschema))' test_router_contract.py`
  6. Test runs in <5s: `time pytest test_router_contract.py 2>&1 | grep -E 'real\s+0m[0-4]\.'`

(Section 5 below enumerates every assertion the test must make.)

---

### T6 — Author permanent `AUDIT.md` (committed contract narrative)

- **Owner class:** `opus-implementer` (judgment: which findings are permanent contract-narrative vs run-dir transient)
- **Estimated cycles:** 1–2
- **Depends-on:** T3 (manifest entries finalized), T5 (test results inform the audit narrative)
- **Inputs:**
  - `ws1_synthesis.md` §1 (artifact shape), §3 (drift codes), §4 (schema fix plan to be carried forward to WS-4), §6.7 (audit-doc permanence decision), §7 (handoff table), §8 (risks accepted).
  - `dark-matter-constraints/SKILL.md` (current Step 4 / Step 5 prose to reference).
- **Outputs:**
  - `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` (NEW)
- **Acceptance gates:**
  1. `test -f contracts/AUDIT.md` → exit 0
  2. `wc -l contracts/AUDIT.md` ≥ 80 (§6.7: this is the permanent narrative; not a stub)
  3. `grep -c "^## " contracts/AUDIT.md` ≥ 6 (must contain at least: Purpose, Manifest schema reference, Drift policy, Out-of-scope, Schema fix plan deferred to WS-4, Producer doc updates queued)
  4. `grep -F "router_contract.json" contracts/AUDIT.md` → exit 0
  5. `grep -F "DRIFT_PRODUCER_DOC_GAP" contracts/AUDIT.md` → exit 0 (every drift code from §3 is named)
  6. `grep -c -E "DRIFT_(PRODUCER_DOC_GAP|PRODUCER_RENAMED|ROUTER_INVENTED_NAME|DOCUMENTED_BUT_ABSENT|PRESENT_BUT_UNDOCUMENTED|INTERNAL_PRODUCER_DOC_INCONSISTENCY)" contracts/AUDIT.md` ≥ 6
  7. `grep -F "relic/v1" contracts/AUDIT.md && grep -F "annihilation/v1" contracts/AUDIT.md` → exit 0 (forward-pointer to WS-4 schema scope)
  8. `grep -F "WS-4" contracts/AUDIT.md` → exit 0 (explicit handoff named)
  9. `grep -Fi "sigmav_xf" contracts/AUDIT.md && grep -Fi "sigmav_total" contracts/AUDIT.md` → exit 0 (the producer-doc inconsistency is documented as a found drift)

---

### T7 — Author run-dir audit report `ws1_audit_report.md`

- **Owner class:** `opus-implementer` (judgment: captures live findings — what was discovered, what manager decided)
- **Estimated cycles:** 1
- **Depends-on:** T5 (test must run before findings are recorded)
- **Inputs:**
  - All artifacts produced T1–T6.
  - `MANAGER_DECISIONS.md` (run dir; if absent the report includes empty placeholder).
- **Outputs:**
  - `.shift-manager/run-20260425-dmc/state/ws1_audit_report.md` (NEW)
- **Acceptance gates:**
  1. `test -f .shift-manager/run-20260425-dmc/state/ws1_audit_report.md` → exit 0
  2. `wc -l ws1_audit_report.md` ≥ 50
  3. `grep -F "router_contract.json" ws1_audit_report.md` → exit 0
  4. `grep -F "test_router_contract.py" ws1_audit_report.md` → exit 0
  5. `grep -E "UNDOCUMENTED_OUTPUT_FIELD|DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY" ws1_audit_report.md` → exit 0 (the report must call out at least the documented producer inconsistencies — `sigmav_xf` vs `sigmav_total` per `maddm/SKILL.md`; `activation_required` topology per `drake/SKILL.md`)
  6. `grep -F "scan_index.csv" ws1_audit_report.md` → exit 0 (per §8 risk #4 — scan-mode column-name drift recorded but NOT gated)
  7. `grep -F "WS-3" ws1_audit_report.md` → exit 0 (real-MadDM-fixture gate handed forward)

---

### T8 — Author the four producer doc-update **scope notes** (NOT the edits)

- **Owner class:** `opus-implementer` (judgment on exact wording the WS-4 implementer should adopt)
- **Estimated cycles:** 1
- **Depends-on:** T6
- **Inputs:** `ws1_synthesis.md` §4 "Doc updates required (queued for WS-4, NOT WS-1)" — the four-item edit list.
- **Outputs:**
  - Section appended to `contracts/AUDIT.md` (or sub-file `contracts/WS4_DOC_EDITS.md`) named **"Producer doc edits queued for WS-4"** with one subsection per producer skill, each containing:
    - file path + target line numbers (from current SKILL.md)
    - exact `old text` block (verbatim from current file)
    - exact `new text` block (proposed)
- **Acceptance gates:**
  1. The doc has exactly four producer subsections: micromegas, maddm, dark-matter-constraints, drake. Verify: `grep -c "^### Producer:" contracts/AUDIT.md` (or WS4_DOC_EDITS.md) == 4
  2. For each subsection, the `old text` block must be greppable in the live producer SKILL.md today: `grep -F "$(extract old block)" plugins/.../SKILL.md` → exit 0 — verified for all 4
  3. For each subsection, the `new text` block must NOT yet appear in the live producer SKILL.md today (this is what WS-4 commits): `! grep -F "$(extract new block)" plugins/.../SKILL.md` → exit 0 — verified for all 4
  4. Each subsection names the WS-4 implementer-side gate that closes the edit: i.e. for each producer, an explicit gate line "WS-4 acceptance: `grep -c '<new wording>' SKILL.md == 1 AND grep -c '<old wording>' SKILL.md == 0`"
  5. `grep -c "WS-4 acceptance:" contracts/AUDIT.md` (or WS4_DOC_EDITS.md) ≥ 4

**Note:** WS-1 ships the *spec for the edits*, not the edits themselves. T8 is the bridge that prevents WS-4 from drifting from WS-1's findings.

---

### T9 — Plan-internal review pass (opus-reviewer)

- **Owner class:** `opus-reviewer`
- **Estimated cycles:** 1
- **Depends-on:** T1–T8
- **Inputs:** every artifact T1–T8 produced.
- **Outputs:**
  - `.shift-manager/run-20260425-dmc/state/ws1_review_signoff.md` (NEW; PASS/FAIL plus enumerated findings)
- **Acceptance gates:**
  1. Reviewer re-runs every gate in T1–T8 from a clean shell and pastes outputs into the signoff doc.
  2. Reviewer asserts `pytest plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` → exit 0
  3. Reviewer asserts the negative-control mutation (T5 gate #4) still fails loudly.
  4. Reviewer either signs off PASS (all gates green) or files findings the WS-1 implementer must address before WS-4 starts.

---

## 4. Sequencing diagram

```
T1 (skeleton manifest)
  └─→ T2 (manifest self-schema + schema test)
        └─→ T3 (populated manifest entries)
              └─→ T4 (fixtures: synthetic + symlinks)
                    └─→ T5 (executable contract test test_router_contract.py)
                          ├─→ T6 (permanent AUDIT.md)
                          │     └─→ T8 (queued WS-4 producer-doc edits)
                          │            └─→ T9 (review signoff)
                          └─→ T7 (run-dir audit report ws1_audit_report.md)
                                └─→ T9
```

**Why this order:**
1. The manifest is the pivot; everything reads from it. Skeleton (T1) lands first so T2 can write a schema *for* it without speculation about top-level keys.
2. T2 (self-schema) gates T3 — the populated manifest must validate against a committed schema, not a dynamic in-test schema. This is the lens-aligned move: the manifest is itself a contract about contracts (§8 risk #6).
3. T4 fixtures must exist before T5 (the test reads them). T4 depends on T3 because the manifest tells T4 which fields the synthetic fixtures must contain.
4. T5 is the teeth. Everything before it is data; T5 is the live check.
5. T6 narrative depends on T5 results (the audit cites real test outcomes).
6. T7 (run-dir) depends on T5 too but is independent of T6 and can run in parallel with T6 once T5 is green.
7. T8 (WS-4 doc-edit spec) depends on T6 because it cross-references the audit's own findings list.
8. T9 reviewer signs off the whole chain after every gate is green.

The ordering is *not* "fix the producer docs first" — that would be WS-1 doing producer-side work it has no mandate for (§6.2 of synthesis). T8 only *scopes* the edits; WS-4 commits them.

---

## 5. Gates — every assertion the contract test (`test_router_contract.py`) must make

This is the test's complete contract. Each assertion below maps to one or more `def test_*` cases in the file. The test reads `router_contract.json` and the fixtures and asserts:

### 5.1 Manifest structural assertions (4 tests)

1. `test_manifest_loads_and_validates_against_self_schema` — load `router_contract.json`, validate against `plugins/shared/schemas/router_contract.schema.json`. PASS = no `jsonschema.ValidationError`.
2. `test_manifest_schema_version_is_v1` — `manifest["schema_version"] == "router_contract/v1"`. Hard-pinned. Bumping is loud.
3. `test_manifest_has_three_required_sections` — `output_fields`, `config_keys`, `status_enums` all present and non-empty (per §6.6).
4. `test_manifest_section_counts_pinned` — `len(output_fields) == 11`, `len(config_keys) == 3`, `len(status_enums) == 1` (per §2). If WS-4 adds entries, these counts bump deliberately.

### 5.2 `output_fields` per-row assertions (5 tests, parametrized over rows)

5. `test_every_output_field_has_required_keys` — every entry has all keys listed in T2 gate #3 (observable, downstream, field_name, produced_by, source_artifact, source_locator, defined_in, fixture, audit_status, model_class_certification, router_table_row).
6. `test_every_summary_json_row_resolves_against_pinned_schema` — for each row with `produced_by == "summary_json"`:
   - load `source_locator.schema` (currently only `scattering/v1`); resolve `source_locator.json_pointer` against the schema's `properties`; assert the field exists and its type is `number`.
7. `test_every_agent_parsed_row_field_present_in_fixture` — for each row with `produced_by == "agent_parsed"`:
   - open `entry.fixture`; run `re.search(source_locator.pattern, fixture_text)`; assert match. **Drift code on failure: `DRIFT_DOCUMENTED_BUT_ABSENT`.**
8. `test_every_stdout_regex_row_field_present_in_fixture` — same as #7 but for `produced_by == "stdout_regex"` rows. Reads the linked `stdout_synthetic.txt`.
9. `test_router_skill_md_references_every_field_name` — for each row, `grep` the router SKILL.md for the literal `entry.field_name`; assert it appears at least once. **Drift code on failure: `DRIFT_ROUTER_INVENTED_NAME` if the field is in manifest but not in router; `DRIFT_PRODUCER_RENAMED` if reverse.**

### 5.3 `output_fields` cross-skill drift assertions (3 tests)

10. `test_every_field_name_appears_in_producer_skill_md` — for each row, `grep` the producer's SKILL.md (`entry.defined_in` minus the anchor) for the field name. **Drift codes: `DRIFT_PRODUCER_DOC_GAP` if absent.**
11. `test_pending_schema_rows_marked_xfail_with_explicit_reason` — rows with `audit_status == "pending_schema"` marked xfail; assert `len(pending_schema_rows) == 2` (omega_h2 micromegas-stdout, sigma_v_zero micromegas-stdout). xfail reason MUST contain string `"WS-4"` and `"relic/v1"` or `"annihilation/v1"`.
12. `test_no_undocumented_fields_in_fixtures` — for each fixture, scan for field-shaped patterns; for each one found that is NOT in the manifest, assert that the audit_report flags `UNDOCUMENTED_OUTPUT_FIELD`. (Soft check — this test xpasses if the audit_report mentions the finding.)

### 5.4 `config_keys` assertions (2 tests)

13. `test_config_keys_complete` — manifest lists exactly `config.maddm_path`, `config.micromegas_path`, `config.drake_path`. No more, no fewer.
14. `test_router_skill_md_reads_every_config_key` — for each `config_keys` entry, `grep -F entry.key` against `dark-matter-constraints/SKILL.md`; assert each key is read by the router.

### 5.5 `status_enums` assertions (3 tests)

15. `test_drake_status_enum_literals_pinned` — `status_enums[0].literals` is exactly `["activation_required", "configured", "found", "missing"]` (set equality, order-independent).
16. `test_router_skill_md_branches_on_every_status_literal` — for each literal, `grep -F` against `dark-matter-constraints/SKILL.md` Step 5 prose; assert each literal is named.
17. `test_drake_install_skill_md_documents_detect_subset` — per `drake/SKILL.md` lines 84–86, `detect` returns only `configured|found|missing`. The test records this in a soft-warn (not a hard fail) — `activation_required` belongs to `use-path` per producer doc; the manifest documents the topology, the test surfaces the inconsistency for WS-4 reconciliation. Assert: `entry.audit_status == "verified_in_writer_skill"` AND test logs a WARNING (visible in `pytest -v` capsys) naming the `activation_required` topology issue.

### 5.6 Manifest self-consistency (1 test)

18. `test_every_manifest_fixture_path_exists` — for every entry's `fixture` path, `pathlib.Path(...).exists()` is `True` (resolves through symlinks).

**Total assertions: ≥18 distinct test cases.** T5 acceptance gate #2 (`grep -c PASSED ≥ 12`) is a floor; the actual count should land at 16+ (18 minus the 2 xfailed pending_schema rows).

### 5.7 Negative-control gate (T5 gate #4)

A separate one-shot script in CI (or executed manually by the reviewer in T9) runs the test against a *mutated* manifest (e.g. one field renamed). The test must fail loudly with the right drift classification. This is the audit's teeth — without this proof, WS-1 has shipped a test that passes regardless of reality.

---

## 6. Pre-flight risks

These could block T1 or surface immediately when implementation starts. The implementer must confirm each is addressed before claiming T1 done.

1. **No collision: `contracts/` directory does not yet exist** — confirmed via `ls plugins/constraints/skills/dark-matter-constraints/` (only `SKILL.md` listed). T1 creates it fresh.
2. **No collision: `tests/` directory does not yet exist** — confirmed. T4 creates it fresh.
3. **Schema convention to mirror: `plugins/shared/schemas/scattering.schema.json`** uses Draft 2020-12, `additionalProperties: false`, `$id` URI of form `https://hep-ph-agents/schemas/<name>/v1`. T2's manifest schema MUST follow exactly the same conventions (no jsonschema.org draft mismatch, no `additionalProperties` left unset).
4. **Test convention to mirror: `plugins/shared/schemas/tests/test_scattering_schema.py`** uses module-scoped pytest fixtures + `jsonschema.Draft202012Validator`. T2's `test_router_contract_schema.py` MUST mirror.
5. **Tooling deps: jq + jsonschema (Python) + pytest** are the only required tools. All exist in the harness — `plugins/constraints/skills/micromegas/tests/test_summary_schema.py` already uses `jsonschema`. **No new dep introduced.**
6. **`relic/v1` and `annihilation/v1` schemas DO NOT yet exist** — T3 marks the relevant rows `audit_status: pending_schema` per §7 risk #7 and the test xfails them with explicit reason (T5 gate #3). WS-4 promotes them to `schema_pinned` after delivering the schemas.
7. **MadDM SKILL.md producer-doc inconsistency (`sigmav_xf` vs `sigmav_total`)** — synthesis §3 rule 6 (`DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`) — T8 stages the WS-4 fix; T7 records the live finding. Synthetic fixture in T4 uses `sigmav_total` (the canonical name the router reads) — **fixture drives one side of the contract, doc drives the other; test flags any divergence**.
8. **DRAKE `activation_required` topology** — per §8 risk #5 — manifest carries both literals, test records a soft-warn (T5 §5.5 #17), WS-4 reconciles.
9. **micrOMEGAs symlink target paths** — fixture symlinks at `dark-matter-constraints/tests/fixtures/micromegas/` resolve to `plugins/constraints/skills/micromegas/tests/fixtures/`. The relative-link form is `../../../../../micromegas/tests/fixtures/<file>`. **Implementer must confirm the relative path at T4 from the actual directory depth; recompute if the path tree differs.**
10. **Path stability across OS/CI** — symlinks are POSIX. Verified: this is a macOS/Linux project; no Windows CI listed. Symlinks safe.
11. **No new Python deps**: T5 uses only stdlib + pytest + jsonschema. **Do NOT introduce PyYAML, requests, or anything else.**

---

## 7. Out-of-scope

Explicit, so the implementer does not drift. Each item below is somebody else's work or deferred to a later run.

- **WS-1 does NOT author `relic.schema.json`** (relic/v1). That is WS-4's deliverable. WS-1 only specifies the shape (already written into `ws1_synthesis.md` §4).
- **WS-1 does NOT author `annihilation.schema.json`** (annihilation/v1). Same; WS-4.
- **WS-1 does NOT modify any producer SKILL.md** (`micromegas/SKILL.md`, `maddm/SKILL.md`, `drake/SKILL.md`, or the router's `dark-matter-constraints/SKILL.md`). T8 only *queues* the edits. WS-4 implementer applies them.
- **WS-1 does NOT touch the router's runtime SKILL.md prose.** No Step 4/Step 5 rewrites; that's WS-4.
- **WS-1 does NOT build any helpers.** No `verify_router_field_contract.py`, no `check_prereqs.py`, no `detect_drake.py`, no `extract_field.py`. WS-4.
- **WS-1 does NOT run real MadDM** to verify fixture parity. §6.4 explicit decision. WS-3 catches.
- **WS-1 does NOT add `omega_h2`/`sigma_v_zero` to `scattering.schema.json`.** §3 explicit: that schema is `additionalProperties: false` + `const: scattering/v1`; mutating it is an unannounced contract bump. WS-4 ships fresh schemas.
- **WS-1 does NOT add scan-mode CSV columns to the manifest.** §2d explicit: scan execution is v1.1-deferred; columns may be revisited. T7 audit report records the finding; manifest excludes them.
- **WS-1 does NOT add the router's blocker-code enum** (`MADDM_MISSING`, `DRAKE_MISSING`, etc.) to the `status_enums` section. §2d: these are router-internal, no cross-tool drift risk.
- **WS-1 does NOT wire the test into CI.** T9 runs it locally; CI wiring is WS-2.

---

## 8. Ready check — what must be true before T1 can start

The plan-critic should verify each of the following before signing off on WS-1 implementation:

1. `git status` shows no in-flight WS-1 changes from a prior failed run that could collide with T1's artifact paths. (Verify `plugins/constraints/skills/dark-matter-constraints/contracts/` does not exist; `plugins/constraints/skills/dark-matter-constraints/tests/` does not exist; `plugins/shared/schemas/router_contract.schema.json` does not exist.) → all confirmed via `ls` at draft time.
2. `python -c 'import jsonschema; import pytest'` returns exit 0 in the harness Python env. (Required by T2 + T5.)
3. `which jq` returns a path. (Required by every gate above.)
4. `ws1_synthesis.md` is committed or otherwise unmodified during implementation. (No moving target.)
5. The `MANAGER_DECISIONS.md` for run `20260425-dmc` is either absent (acceptable; T7 includes a placeholder) or present and pointing at this plan. (Not a blocker.)
6. The four producer SKILL.md files have not been modified since the synthesis was written. Verify via `git log -1 --format=%H plugins/constraints/skills/dark-matter-constraints/SKILL.md` matches the hash captured by the synthesizer. (If they have changed, T3's regex/JSON-pointer references and T8's `old text` blocks must be re-derived.)
7. The implementer has read the routing lens AND `ws1_synthesis.md` end-to-end. **No partial reads** — the synthesis's per-decision justifications drive specific implementation choices (especially the audit_status enum and the locator union shape).

If any of items 1–6 fail, the implementer must surface a blocker before starting T1 rather than improvising.

---

## Summary

- **9 tasks (T1–T9)**, total estimated cycles **≈12** (T1=1, T2=2, T3=2, T4=1, T5=2–3, T6=1–2, T7=1, T8=1, T9=1; midpoint = 12).
- **Critical path:** T1 → T2 → T3 → T4 → T5 → T9 (the test is the load-bearing artifact; everything hangs off T5).
- **Highest-judgment tasks:** T2 (manifest self-schema), T3 (entry population w/ model-class certification), T5 (drift-classification mapping in test), T8 (verbatim WS-4 producer-doc edits). All are `opus-implementer`.
- **Mechanical tasks:** T1 (skeleton), T4 (fixtures), T7 (run-dir narrative). `sonnet-implementer` first cycle.
