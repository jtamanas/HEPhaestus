# WS-2 Plan Draft — Router Test Harness

**Plan-drafter:** ws2-plan-drafter
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws2_synthesis.md` (design canon, 42 + 1 conditional tests, 10 decisions resolved); `plan/ws4_plan_final.md` (helper paths, CLI shapes, T8 contract); `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (WS-1 merged convention).

This is a draft. The synthesis adjudications are binding; this plan transcribes them as ordered tasks T1..T9 with mechanical gates. No re-decisions.

`$REPO=/Users/yianni/Projects/hep-ph-agents`
`$DMC=$REPO/plugins/constraints/skills/dark-matter-constraints`
`$RUN=$REPO/.shift-manager/run-20260425-dmc`

---

## 1. Goal

Decompose synthesis §1 (6 test files, 42 cases + 1 conditional), §2 (oracle script with verbatim header), §3 (conftest with canonical WS-1 trio), §4 (3-assertion doc-vs-CLI parity), §5 (fixture inventory), §6 (WS-2/WS-3 boundary check) into 9 ordered tasks with runnable gates. Ship exactly the test files, fixtures, conftest, oracle, and run-tests script the synthesis specifies; do not test helper internals (WS-4), do not invoke real producer binaries or the LLM (WS-3).

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint: WS-2 tests model-agnostic mechanical behavior; oracle is permitted exception (test infra, no skill-code import). |
| `$RUN/brainstorm/ws2_synthesis.md` | Design canon. §1 inventory (42+1), §2 oracle, §3 conftest, §4 doc-vs-CLI, §5 fixtures, §6 WS-2/WS-3 boundary, §8 coordination, §9 out-of-scope, §7 10-item adjudication. |
| `$RUN/plan/ws4_plan_final.md` | Helper paths + CLI shapes. T2/T3/T4/T5 acceptance gates pin the surfaces WS-2 tests. T8 retrofit pattern is the importlib loader template. |
| `$DMC/tests/test_router_contract.py` (WS-1, merged main) | Convention: `_HERE` / `_REPO_ROOT` / `_DEFAULT_MANIFEST` module-level constants. WS-2 conftest must use these exact names (synthesis §3.1). |
| `$DMC/SKILL.md` (POST-T7-rewrite) | Doc-vs-CLI parity test source. Read after WS-4 T7 lands. |

**Pre-flight critical fact:** WS-4 is in flight. WS-2 cannot truly start a per-helper test file until the helper exists on disk. Each task pre-flight (§7) runs `test -f` on its WS-4 dependency before authoring begins.

---

## 3. Tasks

Nine tasks. Owner classes per synthesis §7 row 1 (mechanical authoring → sonnet; load-bearing contract authoring → opus; review of any single-source-of-truth artifact → opus-reviewer). Cycle estimate: each task is 1 cycle except T9 (review pass).

---

### T1 — `tests/conftest.py` (canonical WS-1 trio + helper-loader fixtures)

- **Owner:** `opus-implementer` (single source of truth for WS-1/WS-2/WS-4-T8).
- **Cycles:** 1. **Depends-on:** none.
- **Inputs:** `ws2_synthesis.md` §3.1 (names `_HERE`/`_REPO_ROOT`/`_DEFAULT_MANIFEST`), §3.2 (`from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST`), §3.3 (`helper_loader`, `helper_subprocess`, **session-scoped** `helper_help_outputs`; NO `tmp_manifest`); WS-1 `test_router_contract.py` lines 37–40.
- **Outputs:** `$DMC/tests/conftest.py` (NEW).

**Acceptance gates:**

```bash
C=$DMC/tests/conftest.py
test -f "$C"
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('cf', pathlib.Path('$C'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert isinstance(m._HERE, pathlib.Path) and m._HERE.name == 'tests'
assert isinstance(m._REPO_ROOT, pathlib.Path)
assert m._DEFAULT_MANIFEST.name == 'router_contract.json'
assert m._DEFAULT_MANIFEST.parent.name == 'contracts'
"
cd "$DMC" && python -c "from tests.conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST"
pytest "$DMC/tests/test_router_contract.py" -v; test $? -eq 0   # WS-1 non-regression
grep -F "def helper_loader" "$C"
grep -F "def helper_subprocess" "$C"
grep -E 'scope\s*=\s*"session"' "$C"   # critic N4
grep -F "helper_help_outputs" "$C"
! grep -F "def tmp_manifest" "$C"      # critic N6
```

---

### T2 — `tests/oracle/threshold_arithmetic.py` (test infra; verbatim header)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** none.
- **Inputs:** `ws2_synthesis.md` §2 (verbatim 8-line header; tiebreaker "prose wins"). Current `$DMC/SKILL.md` Step 3 (10%) and Step 5b (5%). If T7 not landed, tag each function docstring `verbatim-as-of-WS-4-T6-pending`.
- **Outputs:** `$DMC/tests/oracle/__init__.py` (empty); `$DMC/tests/oracle/threshold_arithmetic.py` (NEW).

**Acceptance gates:**

```bash
O=$DMC/tests/oracle/threshold_arithmetic.py
test -f "$O" && test -f "$DMC/tests/oracle/__init__.py"
python -c "
src = open('$O').read()
for s in ['Test-only oracle for SKILL.md threshold prose',
          'TEST INFRASTRUCTURE. Skill code MUST NOT import from it',
          '10% spectrum gap, 5% near-resonance',
          'lossy reference',
          'prose wins (rewrite the oracle, not the prose)']:
    assert s in src, s
"
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('o', pathlib.Path('$O'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert callable(getattr(m,'spectrum_gap_trigger',None))
assert callable(getattr(m,'near_resonance_trigger',None))
"
! grep -E "from.*scripts\.|import.*scripts\." "$O"
```

---

### T3 — Fixtures: `tests/fixtures/spectra/` (4 JSON + README)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** none.
- **Inputs:** `ws2_synthesis.md` §5.2 spectra block.
- **Outputs:** `$DMC/tests/fixtures/spectra/{near_threshold_10pct,safe_above_10pct,near_resonance_5pct,safe_above_5pct}.json` + `README.md` (verbatim 3-line).

**Acceptance gates:**

```bash
F=$DMC/tests/fixtures/spectra
for n in near_threshold_10pct safe_above_10pct near_resonance_5pct safe_above_5pct; do
  test -f "$F/$n.json" && python -c "import json; json.load(open('$F/$n.json'))"
done
test -f "$F/README.md"
grep -F "Synthetic spectrum fixtures for the heuristic-trigger oracle" "$F/README.md"
grep -F "Step 3 trigger at 10%" "$F/README.md"
grep -F "Step 5b at 5%" "$F/README.md"
python -c "
import json
assert json.load(open('$F/near_threshold_10pct.json'))['mass_gap_fraction'] == 0.10001
assert json.load(open('$F/safe_above_10pct.json'))['mass_gap_fraction'] == 0.09999
assert json.load(open('$F/near_resonance_5pct.json'))['mass_gap_to_resonance_fraction'] == 0.0501
assert json.load(open('$F/safe_above_5pct.json'))['mass_gap_to_resonance_fraction'] == 0.0499
"
! test -f "$REPO/plugins/shared/schemas/spectrum.schema.json"   # future, out-of-scope
```

---

### T4 — `tests/test_oracle_thresholds.py` (4 cases consuming oracle)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T2, T3.
- **Inputs:** `ws2_synthesis.md` §1.6 (4 cases, no equality-boundary); T2 verbatim sentences mirrored in test docstrings per §2.
- **Outputs:** `$DMC/tests/test_oracle_thresholds.py` (NEW).

**Acceptance gates:**

```bash
T=$DMC/tests/test_oracle_thresholds.py
test -f "$T"
for fn in test_oracle_threshold_above_fires test_oracle_threshold_below_does_not_fire \
          test_oracle_resonance_5pct_above_fires test_oracle_resonance_5pct_below_does_not_fire; do
  grep -F "def $fn" "$T"
done
! grep -E "def test_oracle.*(boundary|equality|exact_at)" "$T"   # critic D2
grep -F "Skill code MUST NOT" "$T"     # module header forbids skill-code import
python -c "
import re; src=open('$T').read()
for fn in ['test_oracle_threshold_above_fires','test_oracle_threshold_below_does_not_fire',
          'test_oracle_resonance_5pct_above_fires','test_oracle_resonance_5pct_below_does_not_fire']:
    body=re.search(rf'def {fn}.*?(?=\ndef |\Z)', src, re.DOTALL).group(0)
    assert '\"\"\"' in body, fn
"
pytest "$T" -v; test $? -eq 0
```

---

### T5 — `tests/test_check_prereqs.py` (9 functions, 12 behaviors via parametrize)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T2 helper.
- **Inputs:** `ws2_synthesis.md` §1.1 (parametrize collapses pairs 2/3 and 4/5); `ws4_plan_final.md` T2 (`--config`, `--model`, `--manifest`).
- **Outputs:** `$DMC/tests/fixtures/helpers/check_prereqs/` (10 fixtures per synthesis §5.2: `manifest_minimal.json`, `manifest_unparseable.json`, `config_{all_present,maddm_missing,micromegas_missing,drake_unset,drake_nonexistent,no_ufo,mssm_like}.json`); `$DMC/tests/test_check_prereqs.py` (NEW).

**Acceptance gates:**

```bash
H=$DMC/scripts/check_prereqs.py
T=$DMC/tests/test_check_prereqs.py
F=$DMC/tests/fixtures/helpers/check_prereqs
test -f "$H" || { echo "BLOCK: WS-4 T2 not landed"; exit 1; }
test -f "$T" && test -d "$F"
COUNT=$(grep -cE "^def test_check_prereqs_" "$T")
test "$COUNT" -eq 9
for fn in \
  test_check_prereqs_all_present_returns_ok_exit_zero \
  test_check_prereqs_tool_path_missing_emits_blocker_exit_one \
  test_check_prereqs_drake_path_blocker_exit_one \
  test_check_prereqs_ufo_missing_emits_blocker_exit_one \
  test_check_prereqs_slha_missing_emits_hint_status_remains_ok \
  test_check_prereqs_unknown_model_documents_decision \
  test_check_prereqs_unparseable_manifest_exit_two \
  test_check_prereqs_unreadable_config_exit_two \
  test_check_prereqs_structural_outputs; do
  grep -F "def $fn" "$T"
done
grep -F "@pytest.mark.parametrize" "$T"
grep -F "decision pending" "$T"
grep -F "WS-4 cycle 1 behavior" "$T"
pytest "$T" -v; test $? -eq 0
```

---

### T6 — `tests/test_detect_drake.py` (8 functions, env-var bash stub strategy)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T3 helper.
- **Inputs:** `ws2_synthesis.md` §1.2 (env-var `HEPPH_DRAKE_DETECT_CMD`; test 8 stubs `install.sh` via `tmp_path/bin`); `ws4_plan_final.md` T3.
- **Outputs:** `$DMC/tests/fixtures/helpers/detect_drake/` (7 stubs per §5.2: `stub_{configured,found,missing,activation_required,unparseable,unknown_status,sentinel}.sh`); `$DMC/tests/test_detect_drake.py` (NEW).

**Acceptance gates:**

```bash
H=$DMC/scripts/detect_drake.py
T=$DMC/tests/test_detect_drake.py
F=$DMC/tests/fixtures/helpers/detect_drake
test -f "$H" || { echo "BLOCK: WS-4 T3 not landed"; exit 1; }
test -f "$T" && test -d "$F"

# All 7 stub scripts exist + executable
for s in stub_configured stub_found stub_missing stub_activation_required stub_unparseable stub_unknown_status stub_sentinel; do
  test -x "$F/$s.sh"
done

# stub_path_unavailable.sh deliberately ABSENT (synthesis §5.2 critic N5: real install.sh path
# replaced by tmp_path/bin/install.sh stub inside test 8 — boundary check)
! test -e "$F/stub_path_unavailable.sh"

# Exactly the 8 functions per synthesis §1.2
for fn in \
  test_detect_drake_configured_emits_proceed \
  test_detect_drake_found_emits_proceed \
  test_detect_drake_missing_emits_DRAKE_MISSING \
  test_detect_drake_activation_required_emits_DRAKE_ACTIVATION_REQUIRED \
  test_detect_drake_unparseable_json_emits_DRAKE_UNAVAILABLE \
  test_detect_drake_unknown_status_literal_drift_to_unparseable \
  test_detect_drake_drake_path_set_short_circuit_documents_decision \
  test_detect_drake_default_command_with_stubbed_install_sh; do
  grep -F "def $fn" "$T"
done

# env-var stub strategy used (HEPPH_DRAKE_DETECT_CMD)
grep -F "HEPPH_DRAKE_DETECT_CMD" "$T"

# Test 8 stubs install.sh in tmp_path/bin (NOT real /drake-install/scripts/install.sh)
grep -F 'tmp_path' "$T" | grep -F "bin"
grep -F 'install.sh' "$T"
! grep -F '/drake-install/scripts/install.sh' "$T"  # never reach into real tree

# Document-of-decision for short-circuit branch (synthesis §8.2 item 1)
grep -F "decision pending" "$T"
grep -F "WS-4 cycle 1 behavior" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T7 — `tests/test_extract_field.py` (9 functions + 1 conditional pin)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T1 schemas; WS-4 T4 helper.
- **Inputs:** `ws2_synthesis.md` §1.3 (9 + 1 conditional with mandatory verbatim docstring); `ws4_plan_final.md` T4 (8-row exit grid).
- **Outputs:** `$DMC/tests/fixtures/helpers/extract_field/` (8 fixtures per §5.2: `relic_{present_number,present_null,no_xf,schema_version_v2,schema_mismatch,malformed}.json`, `summary_disallowed_null.json`, `tampered_schema_root/relic.schema.json`); `$DMC/tests/test_extract_field.py` (NEW).

**Acceptance gates:**

```bash
H=$DMC/scripts/extract_field.py
T=$DMC/tests/test_extract_field.py
F=$DMC/tests/fixtures/helpers/extract_field
RS=$REPO/plugins/shared/schemas/relic.schema.json
AS=$REPO/plugins/shared/schemas/annihilation.schema.json
test -f "$H" || { echo "BLOCK: WS-4 T4 not landed"; exit 1; }
test -f "$RS" || { echo "BLOCK: WS-4 T1 schemas not landed"; exit 1; }
test -f "$T" && test -d "$F"

# Required fixtures exist
for n in relic_present_number relic_present_null relic_no_xf relic_schema_version_v2 \
         relic_schema_mismatch relic_malformed summary_disallowed_null; do
  test -f "$F/$n.json"
done
test -f "$F/tampered_schema_root/relic.schema.json"

# 9 named functions (synthesis §1.3, case 11 dropped)
for fn in \
  test_extract_field_present_number_returns_zero \
  test_extract_field_present_null_returns_zero \
  test_extract_field_key_absent_exits_one_KEY_ABSENT \
  test_extract_field_schema_version_drift_in_data_exits_one_VERSION_DRIFT \
  test_extract_field_schema_id_drift_in_file_exits_one_VERSION_DRIFT \
  test_extract_field_type_mismatch_exits_one_SCHEMA_MISMATCH \
  test_extract_field_unreadable_file_exits_two_internal \
  test_extract_field_malformed_json_exits_two_internal \
  test_extract_field_disallowed_null_on_scattering_v1_exits_one_SCHEMA_MISMATCH; do
  grep -F "def $fn" "$T"
done

# Conditional 10th pin function with mandatory verbatim docstring (synthesis §1.3)
if grep -F "def test_extract_field_v1_does_not_support_nested_pointer_PIN" "$T"; then
  grep -F "channel_fractions.bb" "$T"
  grep -F "literal top-level key" "$T"
  grep -F "future v1.1 adds" "$T"
  grep -F "MUST be intentionally rewritten, not deleted" "$T"
fi

# pytest.approx with rel=1e-9 used for float comparisons (critic D6)
grep -E "pytest\.approx\([^)]*rel\s*=\s*1e-9" "$T"

# Document-of-decision for float precision (synthesis §8.2 item 3)
grep -F "decision pending" "$T"

# Dropped case 11 (default-schema-root resolution) — must NOT be a test (synthesis §1.3 + §7 row 1)
! grep -F "test_extract_field_default_schema_root" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T8 — `tests/test_verify_router_field_contract.py` (10 functions, mutated manifests)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T5 helper; WS-1 fixtures.
- **Inputs:** `ws2_synthesis.md` §1.4 (mutations inlined; no `tmp_manifest`); `ws4_plan_final.md` T5 (`VerifyResult` dataclass with `.ok`/`.xfail`/`.fail`).
- **Outputs:** `$DMC/tests/test_verify_router_field_contract.py` (NEW).

**Acceptance gates:**

```bash
H=$DMC/scripts/verify_router_field_contract.py
T=$DMC/tests/test_verify_router_field_contract.py
M=$DMC/contracts/router_contract.json
test -f "$H" || { echo "BLOCK: WS-4 T5 not landed"; exit 1; }
test -f "$M"
test -f "$T"

# 10 named functions per synthesis §1.4
for fn in \
  test_baseline_manifest_passes \
  test_summary_line_format_matches_pattern \
  test_renamed_field_emits_DRIFT_PRODUCER_RENAMED_or_DOCUMENTED_BUT_ABSENT \
  test_invented_name_emits_DRIFT_ROUTER_INVENTED_NAME \
  test_documented_but_absent_emits_DRIFT_DOCUMENTED_BUT_ABSENT \
  test_undocumented_present_emits_DRIFT_PRESENT_BUT_UNDOCUMENTED \
  test_internal_inconsistency_emits_DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY \
  test_unparseable_manifest_exits_two \
  test_importable_dataclass_surface \
  test_negative_control_workflow; do
  grep -F "def $fn" "$T"
done

# critic N3: pytest.warns assertion on undocumented-present
grep -E "pytest\.warns\(UserWarning,\s*match=r['\"]DRIFT_PRESENT_BUT_UNDOCUMENTED" "$T"

# critic N6: mutations inlined (no shared tmp_manifest fixture)
! grep -F "def tmp_manifest" "$T"
! grep -F "def tmp_manifest" "$DMC/tests/conftest.py"
# Each mutation test writes to tmp_path / 'm.json'
COUNT=$(grep -c "tmp_path / [\"']m.json[\"']" "$T")
test "$COUNT" -ge 4

# Summary regex pattern enforced
grep -F "^SUMMARY " "$T"
grep -E '\\d\+/\\d\+/\\d\+' "$T"

# baseline pinned: 4 xfails
grep -F "len(VerifyResult.xfail) == 4" "$T" || grep -F 'xfail) == 4' "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T9 — `tests/test_doc_vs_cli_parity.py` (3 mechanical assertions)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1 (session fixture); WS-4 T2/T3/T4/T5 helpers; WS-4 T7 router SKILL.md rewrite.
- **Inputs:** `ws2_synthesis.md` §4 (whole-fence-as-one-string parsing LOCKED; no exit-code parity).
- **Outputs:** `$DMC/tests/test_doc_vs_cli_parity.py` (NEW).

**Acceptance gates:**

```bash
S=$DMC/SKILL.md
SCR=$DMC/scripts
T=$DMC/tests/test_doc_vs_cli_parity.py
test -f "$S" && test -d "$SCR" && test -f "$T"

# Pre-flight: all 4 helpers present (WS-4 T2/T3/T4/T5)
for n in check_prereqs detect_drake extract_field verify_router_field_contract; do
  test -f "$SCR/$n.py" || { echo "BLOCK: $n.py missing"; exit 1; }
done
# Pre-flight: T7 router SKILL.md rewrite has direct-path invocations
grep -E 'python.*scripts/.*\.py' "$S" >/dev/null || { echo "BLOCK: T7 not landed"; exit 1; }

# 3 named functions per synthesis §4
for fn in \
  test_doc_required_flags_present_in_help \
  test_doc_invocation_flags_exist_in_help \
  test_doc_references_each_helper_filename; do
  grep -F "def $fn" "$T"
done

# whole-fence-as-one-string parsing rule LOCKED — implementer uses fence-block logic
grep -E "(```bash|```)" "$T"
grep -F "split" "$T"   # tokenize on whitespace per §4.1

# uses session-scoped helper_help_outputs fixture (avoid 8x re-invocation)
grep -F "helper_help_outputs" "$T"

# No exit-code parity test (synthesis §4: "Skip exit-code parity entirely")
! grep -F "exit_code_parity" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T10 — WS-2/WS-3 boundary check + `run_tests.sh`

- **Owner:** `opus-reviewer` (final lens-conformance audit + boundary grep). **Cycles:** 1. **Depends-on:** T1–T9.
- **Inputs:** `ws2_synthesis.md` §6 (boundary rule), §9 (out-of-scope).
- **Outputs:** `$DMC/tests/run_tests.sh` (NEW); audit log `$RUN/state/ws2_boundary_audit.txt`.

**Acceptance gates:**

```bash
TESTS=$DMC/tests
RUN=$DMC/tests/run_tests.sh
LOG=$RUN/state/ws2_boundary_audit.txt   # uses $RUN passed by manager OR shift-manager run dir

test -f "$RUN/run_tests.sh" 2>/dev/null || test -f "$RUN" || { echo "INFO: run_tests.sh path"; }
# (Conventionally the script lives at $DMC/tests/run_tests.sh.)

# 1. No real-tool runs anywhere in WS-2 tests
! grep -rE "subprocess\.run\([^)]*['\"](maddm|micromegas|wolframscript|drake)['\"]" "$TESTS" --include="*.py"
! grep -rE "(check_call|run|Popen)\([^)]*['\"]/.*/(MadDM|micromegas|drake)" "$TESTS" --include="*.py"
# Real install.sh under drake-install never invoked
! grep -rE "drake-install/scripts/install\.sh" "$TESTS" --include="*.py"

# 2. No LLM-behavior tests
! grep -rE "(claude|anthropic|openai|llm)" "$TESTS" --include="*.py" -i

# 3. Conftest single source of truth — no parallel _HERE/_REPO_ROOT redefinitions in WS-2 test files
for f in $TESTS/test_check_prereqs.py $TESTS/test_detect_drake.py $TESTS/test_extract_field.py \
         $TESTS/test_verify_router_field_contract.py $TESTS/test_doc_vs_cli_parity.py \
         $TESTS/test_oracle_thresholds.py; do
  test -f "$f" || continue
  ! grep -E "^_HERE\s*=" "$f"
  ! grep -E "^_REPO_ROOT\s*=" "$f"
done

# 4. Oracle import boundary holds — no skill-code module imports oracle
! grep -rE "from tests\.oracle" "$DMC/scripts" 2>/dev/null
! grep -rE "import tests\.oracle" "$DMC/scripts" 2>/dev/null

# 5. Total test count = 42 (+1 conditional)
COUNT=$(pytest "$TESTS" --collect-only -q 2>/dev/null | grep -E "^$DMC" | wc -l | tr -d ' ')
test "$COUNT" -ge 42 && test "$COUNT" -le 43

# 6. Whole-suite green
pytest "$TESTS" -v; test $? -eq 0

# 7. run_tests.sh exists, executable, exits 0
test -x "$DMC/tests/run_tests.sh"
"$DMC/tests/run_tests.sh"; test $? -eq 0
```

---

## 4. Sequencing diagram

```
Cycle 1 (parallel, no WS-4 deps):
  T1 (opus, conftest)
  T2 (sonnet, oracle module)
  T3 (sonnet, spectra fixtures)
  T4 (sonnet, oracle thresholds test) — depends on T2+T3 mid-cycle

Cycle 2 (gated on WS-4 T2/T3/T4/T5 landed):
  T5 (sonnet, test_check_prereqs) — gated on WS-4 T2
  T6 (sonnet, test_detect_drake) — gated on WS-4 T3
  T7 (sonnet, test_extract_field) — gated on WS-4 T1+T4
  T8 (sonnet, test_verify_router_field_contract) — gated on WS-4 T5

Cycle 3 (gated on WS-4 T7 router SKILL.md rewrite landed):
  T9 (sonnet, doc-vs-CLI parity) — gated on WS-4 T7

Cycle 4: T10 (opus-reviewer, boundary audit + run_tests.sh)
```

**Critical path:** T1 → (WS-4 T2..T5) → T8 → T9 → T10 (4 cycles WS-2-side; total wall-clock depends on WS-4 cadence).

**Cycle envelope:** **4 binding, 5 ceiling** (1 retry slot for any per-helper test if WS-4 lands a behavior the synthesis didn't pin and forces a doc-of-decision rewrite).

---

## 5. Gates summary (mechanical sub-gate counts)

T1 ~7, T2 ~6, T3 ~10, T4 ~6, T5 ~12, T6 ~14, T7 ~14, T8 ~10, T9 ~9, T10 ~12. **~100 mechanical sub-gates total.** No `wc -l > 0`, no bare `test -f` claims of done — every gate carries a content assertion or pytest run.

---

## 6. Coordination

### 6.1 With WS-1 (MERGED)

- WS-2 conftest (T1) defines `_HERE` / `_REPO_ROOT` / `_DEFAULT_MANIFEST` with the **exact** WS-1 names. WS-1 `test_router_contract.py` keeps its module-level constants (no shadow); it continues to pass unchanged. T1 acceptance gate runs `pytest test_router_contract.py` to prove non-regression.
- WS-2 does NOT modify WS-1 test files. WS-4 T8 owns the retrofit that rewrites WS-1 to import from conftest.

### 6.2 With WS-4 (in flight)

| WS-2 task | Required WS-4 deliverable on disk | Pre-flight `test -f` |
|---|---|---|
| T1 | none — conftest is independent | (none) |
| T2 | none | (none) |
| T3 | none | (none) |
| T4 | T2 + T3 outputs (within WS-2) | tests/oracle/threshold_arithmetic.py + spectra/*.json |
| T5 | WS-4 T2 (`check_prereqs.py`) | `$DMC/scripts/check_prereqs.py` |
| T6 | WS-4 T3 (`detect_drake.py`) | `$DMC/scripts/detect_drake.py` |
| T7 | WS-4 T1 schemas + T4 (`extract_field.py`) | `$DMC/scripts/extract_field.py` + `$REPO/plugins/shared/schemas/relic.schema.json` |
| T8 | WS-4 T5 (`verify_router_field_contract.py`) | `$DMC/scripts/verify_router_field_contract.py` |
| T9 | WS-4 T2/T3/T4/T5 helpers + T7 SKILL.md rewrite | all 4 scripts/*.py + grep `python.*scripts/` in SKILL.md |
| T10 | T1–T9 in WS-2 | (whole-suite) |

### 6.3 Three documented-decision unknowns (synthesis §8.2)

WS-2 does NOT block on these; tests pin whichever WS-4 cycle-1 behavior lands and document the punt:

1. `detect_drake` short-circuit when `drake_path` is set — T6 test 7 docstring: "decision pending — currently asserts <branch label> per WS-4 cycle 1 behavior."
2. `check_prereqs --model nonexistent_in_config` exit code (1 vs 2) — T5 test 6 docstring same form, asserts exit code in {1, 2}.
3. `extract_field` float rendering precision — T7 uses `pytest.approx(rel=1e-9)` (binding WS-2 decision per critic D6); docstring records the binding.

**Trigger condition:** if at WS-2 task-start time WS-4 has NOT landed a behavior for any of the three, the WS-2 implementer writes the doc-of-decision skeleton with the synthesis's expected default (e.g. exit 1 for unknown model) and surfaces a manager note. **Not a WS-4 re-dispatch trigger from WS-2 side** — the synthesis already adjudicated this as document-of-decision posture.

### 6.4 With WS-3

- WS-2 ships the 4 spectra fixtures + README; WS-3 consumes them for LLM playtest.
- WS-2 does NOT run the LLM; WS-2 does NOT invoke real producer binaries.

---

## 7. Pre-flight risks

Implementer verifies before opening each task.

1. **Conftest name collision.** T1 must use the WS-1 names verbatim. Run `pytest test_router_contract.py` after T1 lands; if it breaks, T1 is wrong.
2. **WS-4 helper presence.** Each per-helper test pre-flights with `test -f` on its WS-4 deliverable. If absent, BLOCK and surface a manager blocker.
3. **WS-4 T7 router SKILL.md rewrite.** T9 (doc-vs-CLI parity) cannot start until T7 lands; pre-flight greps SKILL.md for `python.*scripts/.*\.py`.
4. **Oracle no-skill-code-import.** T2 + T4 + T10 all assert this boundary. If any skill-code path imports `tests.oracle`, hard violation.
5. **Real-tool boundary.** T6 test 8 stubs `install.sh` via `tmp_path/bin`; never reaches into `/drake-install/scripts/install.sh`. T10 boundary audit greps for the real path and asserts absence.
6. **No `tmp_manifest` fixture.** Critic N6: each of the 4 mutation tests in T8 inlines its `tmp_path / "m.json"` write. T8 gate asserts the fixture is NOT defined.
7. **Document-of-decision posture.** T5 test 6, T6 test 7, T7 float-precision: each docstring must contain "decision pending" + "WS-4 cycle 1 behavior" tag.
8. **Conditional 10th `extract_field` test.** T7 ships either 9 or 10 functions; if 10, the verbatim mandatory docstring (synthesis §1.3) is grep-asserted.
9. **Session-scoped `--help` capture.** T1 conftest must declare `helper_help_outputs` with `scope="session"` (critic N4); T9 imports it. If T1 forgets `scope`, 8× subprocess overhead is the symptom.
10. **`spectrum/v1` schema.** Out-of-scope. T3 gate asserts the schema file does NOT exist (catch over-eager implementer).
11. **No GitHub Actions / CI / Makefile.** Synthesis §9. T10 ships `run_tests.sh` only.
12. **No real producer binaries.** T10 boundary audit greps for `subprocess.run` against MadDM/micromegas/drake/wolframscript binaries; absence required.

---

## 8. Out-of-scope (explicit, mirrors synthesis §9)

- Real producer binaries (MadDM/micrOMEGAs/DRAKE/Wolfram/`install.sh`) — WS-3.
- LLM behavior testing — WS-3.
- Modifying any of the four helpers — WS-4.
- Rewriting `tests/test_router_contract.py` — WS-4 T8.
- `compare_dm` / `read_maddm_output` / `read_drake_output` testing — prose-only per WS-4 synthesis.
- CI / GitHub Actions.
- Manifest authoring — WS-1.
- Schema authoring — WS-4 T1.
- Top-level Makefile.
- `spectrum/v1` schema — flagged future.
- `compare_dm_single_component` v1.1 helper — out of scope for the run.

---

## 9. Ready check

Predicates that must hold before T1 starts.

1. `test -f $DMC/tests/test_router_contract.py` (WS-1 merged on main).
2. `test -f $DMC/contracts/router_contract.json`.
3. `test -d $DMC/tests/fixtures` (WS-1 fixtures present).
4. `test ! -f $DMC/tests/conftest.py` (T1 first to create — must NOT pre-exist).
5. `python -c 'import jsonschema, pytest'` exits 0.
6. Implementer has read `briefs/ROUTING_LENS.md`, `ws2_synthesis.md`, `ws4_plan_final.md`, AND this plan end-to-end. No partial reads.

For per-task ready checks, see §6.2 table.

---

## Summary

10 tasks (T1..T10); cycle envelope **4 binding, 5 ceiling**; opus on T1 (conftest contract) and T10 (boundary review); sonnet on T2–T9; critical path T1 → WS-4 helpers → T8 → T9 → T10; 42 + 1 conditional tests target; ~100 mechanical sub-gates; document-of-decision posture for the 3 punted unknowns; WS-2/WS-3 boundary held by T10's grep audit.
