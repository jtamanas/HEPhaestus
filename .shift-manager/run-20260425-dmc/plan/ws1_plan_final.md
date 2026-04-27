# WS-1 Plan Final — Output-contract verification

**Synthesizer:** plan-synthesizer
**Verdict on critique:** Adopted. Drafter chain rebuilt to 6 tasks / 7-cycle budget.
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`, `brainstorm/ws1_synthesis.md`, `plan/ws1_plan_draft.md`, `plan/ws1_plan_critique.md`, `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (Step 4 cross-check table at lines 136–141, Step 5 enum literals at lines 198–207), `plugins/constraints/skills/micromegas/SKILL.md` (lines 99–104, 205–221, 226–239), `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (lines 152–181), `plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 76–86), `plugins/shared/schemas/scattering.schema.json`, `plugins/shared/schemas/tests/test_scattering_schema.py`.

This plan is the canonical instruction set for WS-1 implementers. Where the synthesis (`ws1_synthesis.md`) and the drafter (`ws1_plan_draft.md`) disagree with the critic (`ws1_plan_critique.md`), this document picks one and explains why. **No "implementer reconciles" hedges remain.**

---

## 1. Goal

Produce a **load-bearing, mechanically enforceable contract** between the `/dark-matter-constraints` router and its three producer skills (`/maddm`, `/micromegas`, `/drake`) by shipping (a) a JSON manifest enumerating every cross-tool field, config key, and status enum the router consumes, (b) a self-schema for that manifest co-located with it, (c) an executable contract test that fails loudly on drift and provides a working negative-control, (d) two synthetic fixtures plus two symlinks pointing at producer-side fixtures, (e) a permanent narrative `AUDIT.md` co-located with the manifest, and (f) a run-dir audit report capturing live findings. WS-1 does **not** author new physics schemas, modify any producer SKILL.md prose, run real MadDM, or build any of the WS-4 helpers — it only ships the artifacts those downstream tasks consume.

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Sets the model-agnosticism rule. Every code-bound choice must hold under any BSM model class. |
| `brainstorm/ws1_synthesis.md` | Canonical design. Section anchors below cite it. |
| `plan/ws1_plan_critique.md` | Twelve adjudications inherited and resolved (§9 of this doc). |
| `dark-matter-constraints/SKILL.md` | Source of router-consumed field names (Step 4 table lines 136–141; Step 5 lines 198–207). |
| `maddm/SKILL.md` | Producer; lines 152–181. **Internal inconsistency** between line 164 (`sigmav_xf`) and line 176 (`sigmav_total`) is a logged finding. |
| `micromegas/SKILL.md` | Producer; lines 99–104, 205–221 (stdout regex), 226–239 (`scattering/v1` example). |
| `drake/SKILL.md` | Producer; lines 76–86 (`detect` enum is `configured|found|missing`; `activation_required` is `use-path`-only). |
| `scattering.schema.json` | Only existing producer-side schema; manifest references via JSON pointer, never duplicates. |
| `tests/test_scattering_schema.py` | Test convention to mirror (Draft 2020-12 + module-scoped fixtures). |

---

## 3. Tasks

Six tasks. Owner classes: `sonnet-implementer` for mechanical authoring, `opus-implementer` for judgment, `opus-reviewer` for the final gate. No `sonnet-reviewer`.

All paths in this section are absolute. Acceptance gates are runnable bash/python — not prose. Replace `$REPO=/Users/yianni/Projects/hep-ph-agents` mentally; gates use absolute paths verbatim.

---

### T1 — Author manifest + co-located self-schema (populated, not skeleton)

- **Owner class:** `opus-implementer`
- **Cycle estimate:** 2
- **Depends-on:** none

**Inputs:**
- `ws1_synthesis.md` §1 (manifest example), §2a/§2b/§2c (entry counts), §3 (drift codes ⇒ `audit_status` enum), §6.4 (`model_class_certification` enum), §6.6 (single-file three-section decision).
- `dark-matter-constraints/SKILL.md` lines 136–141 (4 router-surfaced observables × 2 producers), lines 198–207 (DRAKE branch literals).
- `maddm/SKILL.md` lines 152–181 (regex shapes; `sigmav_total` is the canonical name, see §9 row 3).
- `micromegas/SKILL.md` lines 205–221 (stdout regex contract for `omega_h2`, `sigma_v_zero`).
- `scattering.schema.json` (JSON pointers for the four micrOMEGAs scatter rows).

**Outputs (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json` (NEW — co-located with the manifest, NOT in `plugins/shared/schemas/`; see §9 row 4)

**Manifest content (pinned, no ambiguity):**

`output_fields` has **9 entries** (decision §9 row 1):

| # | Observable | Downstream | Field name | produced_by | source_artifact | audit_status |
|---|---|---|---|---|---|---|
| 1 | Ωh² | maddm | `Omegah2` | `agent_parsed` | `MadDM_results.txt` | `verified_against_synthetic` |
| 2 | σ_SI(p) | maddm | `sigma_si_proton` | `agent_parsed` | `MadDM_results.txt` | `verified_against_synthetic` |
| 3 | σ_SD(p) | maddm | `sigma_sd_proton` | `agent_parsed` | `MadDM_results.txt` | `verified_against_synthetic` |
| 4 | ⟨σv⟩(v→0) | maddm | `sigmav_total` | `agent_parsed` | `MadDM_results.txt` | `pending_producer_doc_fix` |
| 5 | Ωh² | micromegas | `omega_h2` | `stdout_regex` | `stdout.log` | `pending_schema` |
| 6 | σ_SI(p) | micromegas | `sigma_si_proton_cm2` | `summary_json` | `summary.json` (`scattering/v1`) | `schema_pinned` |
| 7 | σ_SD(p) | micromegas | `sigma_sd_proton_cm2` | `summary_json` | `summary.json` (`scattering/v1`) | `schema_pinned` |
| 8 | ⟨σv⟩(v→0) | micromegas | `sigma_v_zero` | `stdout_regex` | `stdout.log` | `pending_schema` |
| 9 | Ωh² | drake | `omega_h2` | `agent_parsed` | DRAKE stdout | `verified_against_synthetic` |

`config_keys` has **3 entries**: `config.maddm_path`, `config.micromegas_path`, `config.drake_path`.

`status_enums` has **1 entry** named `drake_install_detect_status` with `literals: ["configured","found","missing","activation_required"]` and `audit_status: "pending_producer_topology_fix"` (decision §9 row 2 — drake's `detect` only emits 3 of these 4 today).

**Self-schema (`router_contract.schema.json`) MUST:**
- `$schema = "https://json-schema.org/draft/2020-12/schema"`, `$id = "https://hep-ph-agents/schemas/router_contract/v1"` (mirrors `scattering.schema.json`).
- `additionalProperties: false` at every object level.
- `output_fields.items.properties.produced_by.enum` is **exactly** `["agent_parsed","install_detect_json","stdout_regex","summary_json"]` (sorted).
- `output_fields.items.properties.audit_status.enum` is **exactly** `["documented_but_absent","pending_producer_doc_fix","pending_producer_topology_fix","pending_schema","schema_pinned","verified_against_synthetic","verified_in_writer_skill"]` (sorted; closed enum — decision §9 row 11).
- `output_fields.items.properties.model_class_certification.enum` is **exactly** `["scatter_subcommand_only","stdout_regex_brittle","unproven","wolfram_unstructured"]` (sorted).
- `source_locator` is a `oneOf` with four branches: `{kind:"regex",pattern:string}`, `{kind:"stdout_regex",pattern:string}`, `{kind:"schema_ref",schema:string,json_pointer:string}`, `{kind:"json_pointer",json_pointer:string}`.
- Required keys on every `output_fields` entry: `observable, downstream, field_name, produced_by, source_artifact, source_locator, defined_in, fixture, audit_status, model_class_certification, router_table_row`.

**Acceptance gates (run from repo root):**

```bash
# Files exist
test -f /Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
test -f /Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json

# JSON parse + version pin
M=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
S=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json
python -c "import json; json.load(open('$M')); json.load(open('$S'))"
jq -e '.schema_version == "router_contract/v1"' "$M"
jq -e '."$id" == "https://hep-ph-agents/schemas/router_contract/v1"' "$S"
jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' "$S"

# Section counts pinned to 9 / 3 / 1
jq -e '.output_fields | length == 9' "$M"
jq -e '.config_keys   | length == 3' "$M"
jq -e '.status_enums  | length == 1' "$M"

# Producer split: 4 maddm + 4 micromegas + 1 drake
jq -e '[.output_fields[] | select(.downstream=="maddm")]      | length == 4' "$M"
jq -e '[.output_fields[] | select(.downstream=="micromegas")] | length == 4' "$M"
jq -e '[.output_fields[] | select(.downstream=="drake")]      | length == 1' "$M"

# produced_by split (cross-check from another angle)
jq -e '[.output_fields[] | select(.produced_by=="summary_json")]  | length == 2' "$M"  # only the two scatter rows
jq -e '[.output_fields[] | select(.produced_by=="stdout_regex")]  | length == 2' "$M"
jq -e '[.output_fields[] | select(.produced_by=="agent_parsed")]  | length == 5' "$M"

# audit_status pin: 2 pending_schema, 1 pending_producer_doc_fix
jq -e '[.output_fields[] | select(.audit_status=="pending_schema")]              | length == 2' "$M"
jq -e '[.output_fields[] | select(.audit_status=="pending_producer_doc_fix")]    | length == 1' "$M"

# config_keys & status_enums content
jq -e '([.config_keys[].key] | sort) == ["config.drake_path","config.maddm_path","config.micromegas_path"]' "$M"
jq -e '.status_enums[0].enum_name == "drake_install_detect_status"' "$M"
jq -e '(.status_enums[0].literals | sort) == ["activation_required","configured","found","missing"]' "$M"
jq -e '.status_enums[0].audit_status == "pending_producer_topology_fix"' "$M"

# Self-schema validates the manifest
python -c "
import json, jsonschema
m=json.load(open('$M')); s=json.load(open('$S'))
jsonschema.Draft202012Validator(s).validate(m)
print('OK')
"

# Self-schema closed enums (audit_status, produced_by, model_class_certification)
jq -e '(.properties.output_fields.items.properties.audit_status.enum | sort) == ["documented_but_absent","pending_producer_doc_fix","pending_producer_topology_fix","pending_schema","schema_pinned","verified_against_synthetic","verified_in_writer_skill"]' "$S"
jq -e '(.properties.output_fields.items.properties.produced_by.enum | sort) == ["agent_parsed","install_detect_json","stdout_regex","summary_json"]' "$S"
jq -e '.properties.output_fields.items.properties.source_locator.oneOf | length == 4' "$S"
jq -e '.additionalProperties == false' "$S"
```

**Justification for opus owner:** picking the `audit_status` enum literal set (closed list of 7), composing the locator `oneOf`, and assigning each row's `model_class_certification` per §6.4 is judgment, not transcription. T1 also commits to the row count adjudication (§9 row 1).

---

### T2 — Author synthetic fixtures and producer-side symlinks

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** T1

**Inputs:**
- `ws1_synthesis.md` §5 (fixture strategy + `STRUCTURED FAKE` header convention).
- `maddm/SKILL.md` lines 152–181 (line shapes — synthetic must use canonical `sigmav_total`, NOT `sigmav_xf`; this is decision §9 row 3 in action).
- `drake/SKILL.md` lines 195–214 (Wolfram stdout shape).
- Existing producer fixtures at `plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json` and `stdout_synthetic.txt`.

**Outputs (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/__init__.py` (NEW empty)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` (NEW; structured fake)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt` (NEW; structured fake)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json` (NEW; symlink → `../../../../micromegas/tests/fixtures/summary_singletDM.json`)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/stdout_synthetic.txt` (NEW; symlink → `../../../../micromegas/tests/fixtures/stdout_synthetic.txt`)

**Symlink path note.** The two skills share a parent at `plugins/constraints/skills/`. From `…/dark-matter-constraints/tests/fixtures/micromegas/<file>`, the relative target is `../../../../micromegas/tests/fixtures/<file>` (4 levels of `../`, NOT 5). Implementer MUST create the symlink with this exact relative path, not absolute, so the link survives worktree relocation.

**Acceptance gates:**

```bash
F=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/fixtures

# Synthetic fixtures exist with STRUCTURED FAKE header
head -1 "$F/maddm/MadDM_results_synthetic.txt"  | grep -F "STRUCTURED FAKE"
head -1 "$F/drake/stdout_drake_synthetic.txt"   | grep -F "STRUCTURED FAKE"

# MadDM synthetic carries each canonical field name
grep -E '^Omegah2[[:space:]]*=[[:space:]]*[0-9]'           "$F/maddm/MadDM_results_synthetic.txt"
grep -E '^sigma_SI_proton[[:space:]]*='                    "$F/maddm/MadDM_results_synthetic.txt"
grep -E '^sigma_SI_neutron[[:space:]]*='                   "$F/maddm/MadDM_results_synthetic.txt"
grep -E '^sigma_SD_proton[[:space:]]*='                    "$F/maddm/MadDM_results_synthetic.txt"
grep -E '^sigma_SD_neutron[[:space:]]*='                   "$F/maddm/MadDM_results_synthetic.txt"
grep -E '^sigmav_total[[:space:]]*='                       "$F/maddm/MadDM_results_synthetic.txt"
# Synthetic must NOT perpetuate the producer-doc inconsistency:
! grep -E 'sigmav_xf' "$F/maddm/MadDM_results_synthetic.txt"

# DRAKE synthetic carries an Omega h^2 line in Wolfram stdout shape
grep -Ei 'Omega[[:space:]]*h\^?2' "$F/drake/stdout_drake_synthetic.txt"

# Symlinks resolve (portability check — decision §9 row 9)
test -L "$F/micromegas/summary_singletDM.json"
test -e "$F/micromegas/summary_singletDM.json"   # follows symlink
test -L "$F/micromegas/stdout_synthetic.txt"
test -e "$F/micromegas/stdout_synthetic.txt"

# Symlinks are RELATIVE (not absolute) — required for worktree portability
readlink "$F/micromegas/summary_singletDM.json" | grep -q '^\.\./\.\./'
readlink "$F/micromegas/stdout_synthetic.txt"   | grep -q '^\.\./\.\./'

# Symlinked JSON parses (proves resolution + integrity)
python -c "import json; json.load(open('$F/micromegas/summary_singletDM.json'))"

# Worktree portability gate (decision §9 row 9): the realpath must point inside the repo, not outside
python -c "
import os
real = os.path.realpath('$F/micromegas/summary_singletDM.json')
assert real.startswith('/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/micromegas/tests/fixtures/'), real
print('OK', real)
"
```

---

### T3 — Author executable contract test `test_router_contract.py`

- **Owner class:** `opus-implementer`
- **Cycle estimate:** 2
- **Depends-on:** T1, T2

**Inputs:**
- `ws1_synthesis.md` §3 (drift code ladder), §7 (helper consumer shape), §8 risk #7 (`pending_*` xfail policy).
- `tests/test_scattering_schema.py` (style template).
- `T1/router_contract.json` and `router_contract.schema.json` (live).
- All five fixture files from T2.

**Outputs (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (NEW)

**The test must implement every assertion in §5 of this plan** (gate enumeration). The xfail policy is uniform: any row whose `audit_status` starts with `pending_` is xfailed using `pytest.mark.xfail(reason=…)` where the reason cites the specific WS-4 deliverable (e.g. `"WS-4: relic/v1 schema not yet delivered"`, `"WS-4: producer SKILL.md edit — sigmav_xf → sigmav_total"`, `"WS-4: drake-install detect must emit activation_required"`). The xfail count is computed dynamically from the manifest, not hard-coded.

The test reads the manifest path from env var `ROUTER_CONTRACT_PATH` if set, otherwise from the absolute default `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json`. This indirection is what makes the negative-control gate possible.

**Acceptance gates:**

```bash
T=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
M=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json

# 1. Baseline pass on the shipped manifest
pytest "$T" -v
test $? -eq 0

# 2. PASSED + XFAIL counts derived dynamically from manifest, not literals
PENDING=$(jq '[.output_fields[] | select(.audit_status | startswith("pending_"))] | length' "$M")
PENDING_ENUM=$(jq '[.status_enums[] | select(.audit_status | startswith("pending_"))] | length' "$M")
EXPECTED_XFAIL=$((PENDING + PENDING_ENUM))
ACTUAL_XFAIL=$(pytest "$T" -v 2>&1 | grep -c "XFAIL")
test "$ACTUAL_XFAIL" -eq "$EXPECTED_XFAIL"

# 3. NEGATIVE-CONTROL GATE (decision §9 + critic note explicitly addressed):
#    a) clone the manifest, b) mutate the clone, c) point the test at the clone,
#    d) assert exit nonzero with DRIFT_* in the output,
#    e) re-run against the original and assert exit zero.
TMP=$(mktemp -d)
CLONE="$TMP/router_contract_mutated.json"
cp "$M" "$CLONE"                                  # (a) clone
jq '.output_fields[0].field_name = "WRONG_NAME_DELIBERATE"' "$CLONE" > "$CLONE.tmp" && mv "$CLONE.tmp" "$CLONE"   # (b) mutate clone
ROUTER_CONTRACT_PATH="$CLONE" pytest "$T" -v > "$TMP/mutated.log" 2>&1   # (c) point test at clone
MUTATED_RC=$?
grep -E 'DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME|PRODUCER_DOC_GAP)' "$TMP/mutated.log"   # (d) drift code surfaces
test $MUTATED_RC -ne 0                            # (d cont.) exit nonzero
pytest "$T" -v                                    # (e) re-run against original
test $? -eq 0
rm -rf "$TMP"

# 4. Fixture-path resolution: every entry's fixture path must exist
python -c "
import json, pathlib, os
m = json.load(open('$M'))
for e in m['output_fields']:
    p = pathlib.Path(e['fixture'])
    assert p.exists(), f'missing {p}'
print('OK')
"
```

The negative-control gate is the audit's teeth. **The implementer MUST run it before claiming T3 done; the reviewer (T6) re-runs it.** No `time` budget, no PCRE forbidden-import grep, no machine-dependent gates.

---

### T4 — Author permanent `AUDIT.md`

- **Owner class:** `opus-implementer`
- **Cycle estimate:** 1
- **Depends-on:** T3 (audit narrative cites real test outcomes)

**Inputs:**
- `ws1_synthesis.md` §1, §3, §4, §6.7, §7, §8.
- `dark-matter-constraints/SKILL.md` (Step 4 / Step 5 prose to reference).
- T1's manifest, T3's test results.

**Output (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` (NEW)

**Required sections (each must contain a non-empty paragraph, not a heading-only stub):**
1. **Purpose.** Names `router_contract.json` and explains why the router needs a contract manifest.
2. **Scope (9 entries).** Names the 4 + 4 + 1 split. Explicitly notes the neutron rows are *out of scope today* — covered by `test_scattering_schema.py` already, promote here if WS-4 surfaces them in the router (decision §9 row 1).
3. **Drift policy.** Names every code from synthesis §3: `DRIFT_PRODUCER_DOC_GAP`, `DRIFT_PRODUCER_RENAMED`, `DRIFT_ROUTER_INVENTED_NAME`, `DRIFT_DOCUMENTED_BUT_ABSENT`, `DRIFT_PRESENT_BUT_UNDOCUMENTED`, `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`. Each named in a sentence, not a list item.
4. **Pending rows (xfail policy).** Lists the 3 xfail rows + 1 xfail enum (4 xfails total): two `pending_schema` (omega_h2 / sigma_v_zero from micrOMEGAs stdout — blocked on WS-4 `relic/v1` and `annihilation/v1`), one `pending_producer_doc_fix` (`sigmav_total` row blocked on WS-4 producer doc edit), one `pending_producer_topology_fix` (`drake_install_detect_status` blocked on WS-4 producer topology change).
5. **Schema fix plan deferred to WS-4.** Names `relic/v1` and `annihilation/v1` and explains why a `scattering/v2` is the wrong shape (synthesis §4).
6. **Symlink convention.** One paragraph per decision §9 row 9: relative cross-skill symlinks are the convention from WS-1 forward; if a future platform breaks them, switch to git-tracked copies and accept the duplication.
7. **Out-of-scope and WS-4 hand-off.** Cross-references §8 of this plan (one-line bullets pointing into the producer SKILL.md edits queued for WS-4).

**Acceptance gates:**

```bash
A=/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md
test -f "$A"

# Each named section header is present
for sec in "Purpose" "Scope" "Drift policy" "Pending rows" "Schema fix plan" "Symlink convention" "Out-of-scope"; do
  grep -F "$sec" "$A" || { echo "MISSING SECTION: $sec"; exit 1; }
done

# Every drift code appears in a sentence (lowercased "the" within 80 chars before/after the code; replaces wc-l ≥ 80 + heading-count gates)
for code in DRIFT_PRODUCER_DOC_GAP DRIFT_PRODUCER_RENAMED DRIFT_ROUTER_INVENTED_NAME DRIFT_DOCUMENTED_BUT_ABSENT DRIFT_PRESENT_BUT_UNDOCUMENTED DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY; do
  grep -E "[A-Za-z][^.]{0,200}${code}[^.]{0,200}\." "$A" || { echo "DRIFT CODE NOT IN SENTENCE: $code"; exit 1; }
done

# Forward-pointers to WS-4 land
grep -F "relic/v1"        "$A"
grep -F "annihilation/v1" "$A"
grep -F "WS-4"            "$A"

# Producer-doc inconsistency named (sigmav_xf vs sigmav_total)
grep -F "sigmav_xf"    "$A"
grep -F "sigmav_total" "$A"

# Manifest filename appears
grep -F "router_contract.json" "$A"

# Symlink convention paragraph present
grep -E "symlink.*relative|relative.*symlink" -i "$A"
```

---

### T5 — Author run-dir audit report `ws1_audit_report.md`

- **Owner class:** `sonnet-implementer` (mechanical narration of T1–T4 outputs; was opus in draft, demoted per critic recommendation)
- **Cycle estimate:** 1
- **Depends-on:** T3, T4

**Output (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-dmc/state/ws1_audit_report.md` (NEW)

**Required content (token-grep gates, not line floor):** the report names every artifact T1–T4 shipped, records the negative-control gate outcome, calls out the live producer-doc inconsistencies (`sigmav_xf` / `sigmav_total`, drake `activation_required` topology), records the scan-mode column-name finding (`scan_index.csv`) without gating it, and explicitly hands the real-MadDM fixture replacement forward to WS-3.

**Acceptance gates:**

```bash
R=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-dmc/state/ws1_audit_report.md
test -f "$R"

# Artifacts named
grep -F "router_contract.json"        "$R"
grep -F "router_contract.schema.json" "$R"
grep -F "test_router_contract.py"     "$R"
grep -F "AUDIT.md"                    "$R"

# Live findings recorded (no line-count gate)
grep -F "sigmav_xf"                                  "$R"
grep -F "sigmav_total"                               "$R"
grep -E "activation_required.*detect|detect.*activation_required" "$R"
grep -F "scan_index.csv"                             "$R"

# Forward gates to WS-3 / WS-4
grep -F "WS-3" "$R"
grep -F "WS-4" "$R"

# Negative-control outcome recorded
grep -E "negative.control|DRIFT_(PRODUCER|ROUTER|DOCUMENTED)" "$R"
```

---

### T6 — Plan-internal review pass

- **Owner class:** `opus-reviewer` (decision §9 row 8 — keep opus, accept the cycle cost; review is the audit's last line of defense)
- **Cycle estimate:** 1
- **Depends-on:** T1–T5

**Output (absolute):**
- `/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-dmc/state/ws1_review_signoff.md` (NEW; PASS/FAIL + enumerated findings)

**Acceptance gates:**

```bash
SO=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-dmc/state/ws1_review_signoff.md
test -f "$SO"

# Reviewer re-ran every T1-T5 gate from a clean shell and pasted output
grep -F "T1 gates" "$SO"
grep -F "T2 gates" "$SO"
grep -F "T3 gates" "$SO"
grep -F "T4 gates" "$SO"
grep -F "T5 gates" "$SO"

# Reviewer ran the contract test and the negative-control
grep -F "pytest" "$SO"
grep -F "negative-control" "$SO"

# Verdict line present
grep -E '^(PASS|FAIL):' "$SO"
```

---

## 4. Sequencing

```
T1 (manifest + self-schema, populated)
  └─→ T2 (fixtures + symlinks)
        └─→ T3 (executable contract test)
              ├─→ T4 (permanent AUDIT.md)
              └─→ T5 (run-dir audit report)        [T4 ∥ T5]
                    └─→ T6 (review signoff)
```

**Critical path:** T1 → T2 → T3 → T6.
**Parallelism:** T4 and T5 can run in the same cycle if a single implementer holds both (sonnet for T5, opus for T4 — different owner classes, so they run as a parallel pair).

**Cycle envelope:** T1 (2) + T2 (1) + T3 (2) + max(T4, T5) (1) + T6 (1) = **7 cycles**. Decision §9 row 12.

---

## 5. Gate enumeration — every assertion `test_router_contract.py` makes

Each numbered item is one or more `def test_*` cases. Drift codes in **bold** are the failure-mode names that must surface in stderr on a failed assertion (so the negative-control gate can grep for them).

### 5.1 Manifest structural assertions (4)

1. `test_manifest_loads_and_validates_against_self_schema` — load both files, run `jsonschema.Draft202012Validator(schema).validate(manifest)`. PASS = no `ValidationError`.
2. `test_manifest_schema_version_is_v1` — `manifest["schema_version"] == "router_contract/v1"`.
3. `test_manifest_has_three_required_sections` — `output_fields`, `config_keys`, `status_enums` present and non-empty.
4. `test_manifest_section_counts_pinned` — `len(output_fields) == 9`, `len(config_keys) == 3`, `len(status_enums) == 1`.

### 5.2 `output_fields` per-row assertions (5, parametrized)

5. `test_every_output_field_has_required_keys` — every entry has all 11 required keys.
6. `test_every_summary_json_row_resolves_against_pinned_schema` — for `produced_by == "summary_json"`: load `source_locator.schema` (resolves to `plugins/shared/schemas/scattering.schema.json`), resolve `json_pointer` against the schema's `properties`, assert field exists with type `number`. **`DRIFT_PRODUCER_DOC_GAP` on failure.**
7. `test_every_agent_parsed_row_field_present_in_fixture` — open `entry.fixture`, run `re.search(source_locator.pattern, fixture_text)`, assert match. **`DRIFT_DOCUMENTED_BUT_ABSENT` on failure.**
8. `test_every_stdout_regex_row_field_present_in_fixture` — same pattern as #7 but reads the symlinked `stdout_synthetic.txt`.
9. `test_router_skill_md_references_every_field_name` — for each row, `re.search(rf"\b{re.escape(entry['field_name'])}\b", router_skill_md)` must match. **`DRIFT_ROUTER_INVENTED_NAME` on failure.**

### 5.3 `output_fields` cross-skill drift assertions (3)

10. `test_every_field_name_appears_in_producer_skill_md` — for each row, grep producer SKILL.md (path from `entry.defined_in`) for the literal `field_name`. **`DRIFT_PRODUCER_DOC_GAP` on failure** for non-pending rows; `pending_*` rows are xfailed with explicit reason.
11. `test_pending_rows_xfailed_with_explicit_reason` — count rows with `audit_status` starting `pending_` and assert each was xfailed at runtime; xfail reasons must contain the string `"WS-4"`. The expected xfail count is computed from the manifest at test-collection time, not hard-coded.
12. `test_no_undocumented_fields_in_fixtures` — for the MadDM synthetic, parse field-shaped patterns (`^\w+\s*=`) and assert each is either present in the manifest OR named in the run-dir audit report under `DRIFT_PRESENT_BUT_UNDOCUMENTED`. (Soft-pass via audit-report token grep — ensures every fixture-side field is accounted for.)

### 5.4 `config_keys` assertions (2)

13. `test_config_keys_complete` — exactly `{config.maddm_path, config.micromegas_path, config.drake_path}` (set equality).
14. `test_router_skill_md_reads_every_config_key` — for each, `grep -F entry.key` against router SKILL.md.

### 5.5 `status_enums` assertions (3)

15. `test_drake_status_enum_literals_pinned` — `set(status_enums[0].literals) == {"configured","found","missing","activation_required"}`.
16. `test_router_skill_md_branches_on_every_status_literal` — for each literal, `grep -F` against router SKILL.md Step 5 region.
17. `test_drake_install_detect_documents_subset` — `xfail(reason="WS-4: drake-install detect must emit activation_required (currently use-path only — drake/SKILL.md lines 84–86)")`. **This is the topology xfail — decision §9 row 2.** Until WS-4 reconciles, this test xfails loudly; it does NOT warn-and-pass.

### 5.6 Manifest self-consistency (1)

18. `test_every_manifest_fixture_path_exists` — `pathlib.Path(entry["fixture"]).exists()` resolves through symlinks.

### 5.7 Negative-control (separate gate, T3 acceptance gate #3)

External shell snippet (not a pytest case): clone manifest → mutate clone → run pytest against clone via `ROUTER_CONTRACT_PATH` env var → assert exit nonzero AND a `DRIFT_*` code appears in stderr → re-run against original → assert exit zero.

**Total in-pytest cases: 18. Expected runtime outcomes: 14 PASS + 4 XFAIL** (rows 4, 5, 8 are xfail per `audit_status`; case 17 is xfail per the topology decision).

---

## 6. Pre-flight risks

Implementer MUST verify each before declaring T1 done.

1. **Directory collision check.** Confirm `contracts/` and `tests/` do not yet exist under `plugins/constraints/skills/dark-matter-constraints/`. **Verified at synthesis time:** `ls` shows only `SKILL.md`. T1/T2 create both fresh.
2. **`pytest` config.** Repo has no top-level `pytest.ini` / `pyproject.toml` — pytest uses default discovery. Verify `pytest plugins/shared/schemas/tests/test_scattering_schema.py` runs from repo root in the harness env before T3. If not, T3 must include a `conftest.py` next to the new test that pins `rootdir`.
3. **`jq` availability.** Every gate above uses `jq`. Verify `which jq` in the harness env before T1; if absent, surface as blocker, do not improvise with `python -c "import json; ..."`.
4. **Schema convention.** `scattering.schema.json` uses Draft 2020-12, `additionalProperties: false`, `$id = https://hep-ph-agents/schemas/<name>/v1`. T1's self-schema mirrors exactly. **No drafting deviation — `plugins/shared/schemas/router_contract.schema.json` is NOT created (decision §9 row 4).**
5. **No new Python deps.** T3 imports only `json`, `pathlib`, `re`, `os`, `subprocess`, `pytest`, `jsonschema`. All exist (`test_scattering_schema.py` uses jsonschema). Do NOT add PyYAML, requests, etc.
6. **Symlink portability.** macOS / Linux only; no Windows CI. Relative symlinks (4 levels of `../`) work across worktrees. **Gate at T2** (decision §9 row 9) verifies resolution; AUDIT.md (T4) documents the convention.
7. **Producer SKILL.md hashes.** Verify `git log -1 --format=%H plugins/.../SKILL.md` for the four producer skills hasn't changed between synthesis-time and T1-start. If a hash has shifted, T1 implementer re-reads the affected file end-to-end before authoring entries (regex shapes / field names may have moved).
8. **MadDM `sigmav_xf` vs `sigmav_total` (live).** Decision: synthetic uses `sigmav_total`; manifest row 4's `audit_status` is `pending_producer_doc_fix`; test xfails it. WS-4 reconciles producer doc.
9. **DRAKE `activation_required` topology (live).** Decision: manifest carries all four literals; status_enums entry's `audit_status` is `pending_producer_topology_fix`; test xfails (case #17). WS-4 reconciles.

---

## 7. Out-of-scope

Explicit list of things WS-1 does NOT do, so the implementer does not drift.

- WS-1 does NOT author `relic.schema.json` or `annihilation.schema.json` — WS-4 deliverable.
- WS-1 does NOT modify any producer SKILL.md (`micromegas`, `maddm`, `drake`, `dark-matter-constraints` itself).
- WS-1 does NOT rewrite the router's Step 4 / Step 5 prose.
- WS-1 does NOT build any helpers (`verify_router_field_contract`, `check_prereqs`, `detect_drake`, `extract_field`).
- WS-1 does NOT run real MadDM (synthesis §6.4; WS-3 catches).
- WS-1 does NOT add fields to `scattering.schema.json` (would silently bump `scattering/v1`).
- WS-1 does NOT add scan-mode CSV columns to the manifest (v1.1-deferred per `micromegas/SKILL.md` line 108).
- WS-1 does NOT add the router-internal blocker enum (`MADDM_MISSING`, etc.) to `status_enums` (synthesis §2d).
- WS-1 does NOT wire the test into CI (WS-2).
- WS-1 does NOT author T8 from the drafter's plan — verbatim producer-doc edits queued for WS-4. **Replaced by §8 below** (decision §9 row 7).

---

## 8. WS-4 hand-off (concrete file/line targets)

T8 from the drafter is **dropped** (decision §9 row 7). Synthesis §4 already pins these edits; WS-4's plan-drafter re-derives verbatim against the live worktree at WS-4 start. WS-1 only commits to *naming* them so WS-4 cannot miss any. AUDIT.md (T4 §7 "Out-of-scope and WS-4 hand-off") references this list.

| # | File | Line(s) | Edit summary | Closes which xfail |
|---|---|---|---|---|
| W4-A | `plugins/constraints/skills/micromegas/SKILL.md` | 99, 226 | Add `relic.json` + `annihilation.json` to per-run output table; add schema examples mirroring the existing `summary.json` example block | `pending_schema` rows 5, 8 (after `relic/v1`, `annihilation/v1` ship) |
| W4-B | `plugins/constraints/skills/micromegas/SKILL.md` | (header includes) | Add new schema files: `plugins/shared/schemas/relic.schema.json`, `plugins/shared/schemas/annihilation.schema.json` per synthesis §4 | Same as W4-A |
| W4-C | `plugins/monte-carlo-tools/skills/maddm/SKILL.md` | 164 | Reconcile `sigmav_xf` (line 164) → `sigmav_total` (matches line 176 and the router consumer) | `pending_producer_doc_fix` row 4 |
| W4-D | `plugins/constraints/skills/dark-matter-constraints/SKILL.md` | ~213 (Step 5 Branch 2) | Make DRAKE's Ωh² field name explicit (`omega_h2`, lowercase, matching `drake/SKILL.md` line 207's emitted dict) | (no xfail — clarity edit) |
| W4-E | `plugins/monte-carlo-tools/skills/drake/SKILL.md` | 84–86 | Either extend `detect` to emit `activation_required` (preferred), OR change router Step 5 Branch 2 to read `activation_required` from `use-path` rather than `detect` | `pending_producer_topology_fix` (status_enums entry) |
| W4-F | (no doc edit; helper authoring) | n/a | Author `verify_router_field_contract`, `check_prereqs`, `detect_drake`, `extract_field` per synthesis §7 helper boundary | (none — these consume the manifest) |
| W4-G | (deferred enrichment) | n/a | If WS-4 surfaces neutron rows in the router's Step 4 cross-check table, extend manifest to 11 entries (4+6+1) and re-run T1's gate suite | (none — promotion path) |

---

## 9. Twelve-item adjudication table

One row per critic item. Decision is binding.

| # | Critic item | Decision | Rationale |
|---|---|---|---|
| 1 | Entry count: 9 vs 11 | **9** (4 MadDM + 4 micrOMEGAs + 1 DRAKE) | The router's actual Step 4 cross-check table (`dark-matter-constraints/SKILL.md` lines 136–141) surfaces only proton rows; neutron rows are covered by `test_scattering_schema.py` already. Adding them here conflates router-contract with schema-completeness. AUDIT.md notes the promotion path (WS-4 W4-G). |
| 2 | DRAKE `activation_required` policy | **xfail** with new literal `pending_producer_topology_fix` | The lens demands loud contracts. A `pytest` WARNING is filtered by default and silently passes — forbidden by the "silent-pass-in-disguise" constraint. xfail forces WS-4 to land a fix to clear it. |
| 3 | `sigmav_xf` vs `sigmav_total` in synthetic | **`sigmav_total`** in synthetic; manifest row 4 carries `audit_status: pending_producer_doc_fix`; producer-doc fix queued as WS-4 W4-C | Router code already reads `sigmav_total` (see `dark-matter-constraints/SKILL.md` line 141); making the synthetic match canonical usage and xfailing the producer-doc gap is the lens-aligned move. |
| 4 | Manifest-schema location | **`plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json`** (co-located with manifest) | Existing `plugins/shared/schemas/` holds *cross-tool physics* schemas (`scattering`, `processspec`, `amp_reduced.meta`). The router contract manifest is router-internal; placing its schema in `shared/` would dilute the convention. |
| 5 | Merge T1 → T3 (skeleton + populate) | **Yes — collapsed** | Empty skeleton has zero risk to land separately and zero parallelism unblocked. T1 of this plan ships the populated manifest in one cycle pair. |
| 6 | Merge T2 + T3 (self-schema + populate) | **Yes — collapsed into T1 of this plan** | Same opus-implementer, same file family, mutually informing. Authoring schema and entries together prevents shape-vs-content drift. |
| 7 | T8 fate | **Drop entirely.** Synthesis §4 is the source of truth; WS-4 plan-drafter re-derives against live worktree. AUDIT.md §7 references the W4-A…W4-E list above. | Re-deriving verbatim edits against possibly-drifted hashes is brittle and duplicates synthesis §4 (single-source-of-truth violation). WS-4 does its own grep-and-fix. |
| 8 | T9 owner class | **`opus-reviewer`, 1 cycle** (no split) | The review IS the audit's last line of defense. Splitting into sonnet-mechanical + opus-interpretive doubles overhead. Accepting the gate-replay cost is correct — every gate is mechanically checkable, but the *interpretation* of a failure is opus work. |
| 9 | Symlink portability | **Hard gate.** T2 acceptance gate verifies relative-symlink form (`^\.\./\.\./`) AND realpath resolution into the producer fixtures dir. AUDIT.md §6 documents the convention as a recoverable failure mode. | Symlinks are a new convention in this repo; gating now prevents a silent break later. |
| 10 | Loose-gate replacement policy | **Replace every `wc -l ≥ N` and `grep -c heading-count` with content-token grep.** AUDIT.md and audit_report.md gates verify named sections AND that drift codes appear in sentences (regex with `[^.]{0,200}` window before/after). | Line-count gates pass on empty files of the right length. Content-token gates pass only when the named claim is actually written. |
| 11 | `audit_status` enum literals | **Closed enum, exactly 7 literals (sorted):** `documented_but_absent`, `pending_producer_doc_fix`, `pending_producer_topology_fix`, `pending_schema`, `schema_pinned`, `verified_against_synthetic`, `verified_in_writer_skill` | The drafter's hedged list is implementer drift waiting to happen. Closed enum + `additionalProperties: false` makes adding a literal a deliberate, reviewed act. |
| 12 | Cycle budget | **7 cycles.** T1 (2) + T2 (1) + T3 (2) + max(T4, T5) (1) + T6 (1) | Achieved by collapsing T1+T2+T3-skeleton into a single populated-manifest task and dropping T8. The drafter's 12-cycle budget reflected the unmerged shape, not extra work. |

---

## 10. Ready check — predicates that must hold before T1 starts

All checked at draft-time; implementer re-verifies before opening T1.

1. `git status` clean for `plugins/constraints/skills/dark-matter-constraints/contracts/`, `plugins/constraints/skills/dark-matter-constraints/tests/`, `plugins/shared/schemas/router_contract.schema.json` — none should exist.
2. `python -c 'import jsonschema, pytest'` exits 0 in harness env.
3. `which jq` returns a path.
4. `pytest plugins/shared/schemas/tests/test_scattering_schema.py` exits 0 from repo root (proves harness pytest works without extra config).
5. `ws1_synthesis.md` and this final plan are unmodified during implementation.
6. The four producer SKILL.md files at the hashes captured in §6 risk #7 — if any has changed, re-read end-to-end before T1.
7. Implementer has read `briefs/ROUTING_LENS.md`, `ws1_synthesis.md`, `ws1_plan_critique.md`, AND this plan end-to-end. No partial reads.

If any of items 1–6 fails, raise a blocker before starting T1. Item 7 is verified by the implementer's own discipline.

---

## Summary

- **6 tasks (T1–T6).** Total cycle estimate **7**.
- **Critical path:** T1 → T2 → T3 → T6. T4 ∥ T5 in cycle 5.
- **Highest-judgment tasks:** T1 (manifest + self-schema, locator union + closed enums), T3 (drift-classification mapping + working negative-control), T4 (audit narrative).
- **Mechanical tasks:** T2 (fixtures), T5 (run-dir narrative — sonnet, demoted from opus per critic).
- **Adjudications binding** per §9. The implementer does NOT re-decide any item there.
- **Negative-control gate is teeth.** T3 acceptance gate #3 must pass before T3 is declared done; T6 reviewer re-runs it. Without it, the contract test silently passes.
