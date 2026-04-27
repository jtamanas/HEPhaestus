# WS-2 Plan Final — Router Test Harness

**Plan-synthesizer:** ws2-plan-synthesizer
**Verdict on critique:** ACCEPT (all 7 items resolved as binding decisions below).
**Status:** FINAL. Implementer must not re-decide; surfaces blockers to manager only.
**Inputs consumed end-to-end (in order):** `briefs/ROUTING_LENS.md`; `brainstorm/ws2_synthesis.md` (design canon, 42+1 tests, 10 brainstorm-cycle adjudications); `plan/ws2_plan_draft.md` (10-task decomposition); `plan/ws2_plan_critique.md` (7 items for synthesizer); `plan/ws4_plan_final.md` (helper paths, CLI shapes, T8 retrofit pattern); `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (WS-1 merged convention).

`$REPO=/Users/yianni/Projects/hep-ph-agents`
`$DMC=$REPO/plugins/constraints/skills/dark-matter-constraints`
`$RUN=$REPO/.shift-manager/run-20260425-dmc`

---

## 1. Goal

Decompose synthesis §1 (6 test files, 42 cases + 1 conditional), §2 (oracle script with verbatim header), §3 (conftest with canonical WS-1 trio), §4 (3-assertion doc-vs-CLI parity), §5 (fixture inventory), §6 (WS-2/WS-3 boundary check) into **10 ordered tasks** with mechanical sub-gates. Ship exactly the test files, fixtures, conftest, oracle, and run-tests script the synthesis specifies; do not test helper internals (WS-4-owned), do not invoke real producer binaries or the LLM (WS-3-owned).

**WS-4 dependency posture:** WS-4 cycle 1 has just completed (T1–T8 committed; T7 had a line-count gate failure under adjudication, reviewer is verifying). The helpers are on the WS-4 branch and have NOT yet merged to main. **WS-2 implementation cannot start until WS-4 merges to main.** Plan-finalization completes now.

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint: WS-2 tests model-agnostic mechanical behavior; oracle is permitted exception (test infra, no skill-code import). |
| `$RUN/brainstorm/ws2_synthesis.md` | Design canon. §1 inventory (42+1), §2 oracle, §3 conftest, §4 doc-vs-CLI, §5 fixtures, §6 WS-2/WS-3 boundary, §8 coordination, §9 out-of-scope, §7 10-item adjudication. |
| `$RUN/plan/ws4_plan_final.md` | Helper paths + CLI shapes. T2/T3/T4/T5 acceptance gates pin the surfaces WS-2 tests. T8 retrofit pattern is the importlib loader template. |
| `$RUN/plan/ws2_plan_critique.md` | 7-item adjudication mandate for this final document. |
| `$DMC/tests/test_router_contract.py` (WS-1, merged main) | Convention: `_HERE` / `_REPO_ROOT` / `_DEFAULT_MANIFEST` module-level constants. WS-2 conftest must use these exact names (synthesis §3.1). |
| `$DMC/SKILL.md` (POST-WS-4-T7-rewrite) | Doc-vs-CLI parity test source. Read after WS-4 T7 lands and merges. |

---

## 3. Tasks

Ten tasks (T1..T10). Owner classes resolved per critique §3 (T1 sonnet, not opus). Cycle estimate: each task is one cycle except T10 which absorbs final review and `run_tests.sh`.

---

### T1 — `tests/conftest.py` (canonical WS-1 trio + helper-loader fixtures)

- **Owner:** `sonnet-implementer` (downgraded from opus per critic item 2; spec is precise, no judgment).
- **Cycles:** 1. **Depends-on:** WS-4 merged to main (for `tests/__init__.py` presence and non-regression run).
- **Inputs:** `ws2_synthesis.md` §3.1 (names `_HERE`/`_REPO_ROOT`/`_DEFAULT_MANIFEST`), §3.2 (`from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST`), §3.3 (`helper_loader`, `helper_subprocess`, **session-scoped** `helper_help_outputs`; NO `tmp_manifest`); WS-1 `test_router_contract.py` lines 37–40.
- **Outputs:** `$DMC/tests/conftest.py` (NEW).

**Acceptance gates:**

```bash
C=$DMC/tests/conftest.py
test -f "$C"
test -f "$DMC/tests/__init__.py"   # required for relative import (synthesis §3.2)
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

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** none (independent of WS-4).
- **Inputs:** `ws2_synthesis.md` §2 (verbatim 8-line header; tiebreaker "prose wins"). Current `$DMC/SKILL.md` Step 3 (10%) and Step 5b (5%). **If WS-4 T7 (router SKILL.md rewrite) not merged, tag each function docstring `verbatim-as-of-WS-4-T7-pending`** (corrects the synthesis "T6" typo per critic gate audit on T2).
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
# Scope guard (remove only when spectrum/v1 lands in a future run):
! test -f "$REPO/plugins/shared/schemas/spectrum.schema.json"
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

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T2 helper merged to main.
- **Inputs:** `ws2_synthesis.md` §1.1 (parametrize collapses pairs 2/3 and 4/5); `ws4_plan_final.md` T2 (`--config`, `--model`, `--manifest`).
- **Outputs:** `$DMC/tests/fixtures/helpers/check_prereqs/` (10 fixtures per synthesis §5.2: `manifest_minimal.json`, `manifest_unparseable.json`, `config_{all_present,maddm_missing,micromegas_missing,drake_unset,drake_nonexistent,no_ufo,mssm_like}.json`); `$DMC/tests/test_check_prereqs.py` (NEW).

**Pre-flight (CLI-shape; per critic item 5):**

```bash
H=$DMC/scripts/check_prereqs.py
test -f "$H" || { echo "BLOCK: WS-4 T2 not merged to main"; exit 1; }
for f in --config --model --manifest; do
  python "$H" --help 2>&1 | grep -F -- "$f" >/dev/null || \
    { echo "BLOCK: WS-4 T2 CLI drift — missing $f"; exit 1; }
done
```

**Acceptance gates:**

```bash
H=$DMC/scripts/check_prereqs.py
T=$DMC/tests/test_check_prereqs.py
F=$DMC/tests/fixtures/helpers/check_prereqs
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
# parametrize is used at least twice (collapsing the 2/3 and 4/5 pairs)
test "$(grep -c '@pytest.mark.parametrize' "$T")" -ge 2

# WS-4-owned unknown (#2: nonexistent-model exit code) — xfail(strict=True) per critic item 3
grep -E "pytest\.mark\.xfail\(strict\s*=\s*True" "$T"
grep -F "WS-4 decision pending" "$T"
grep -F "ws2_synthesis.md §8.2" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T6 — `tests/test_detect_drake.py` (8 functions, env-var bash stub strategy)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T3 helper merged to main.
- **Inputs:** `ws2_synthesis.md` §1.2 (env-var `HEPPH_DRAKE_DETECT_CMD`; test 8 stubs `install.sh` via `tmp_path/bin`); `ws4_plan_final.md` T3.
- **Outputs:** `$DMC/tests/fixtures/helpers/detect_drake/` (7 stubs per §5.2: `stub_{configured,found,missing,activation_required,unparseable,unknown_status,sentinel}.sh`); `$DMC/tests/test_detect_drake.py` (NEW).

**Pre-flight (CLI-shape; per critic item 5):**

```bash
H=$DMC/scripts/detect_drake.py
test -f "$H" || { echo "BLOCK: WS-4 T3 not merged to main"; exit 1; }
for f in --config --manifest; do
  python "$H" --help 2>&1 | grep -F -- "$f" >/dev/null || \
    { echo "BLOCK: WS-4 T3 CLI drift — missing $f"; exit 1; }
done
# env-var contract documented in --help
python "$H" --help 2>&1 | grep -F "HEPPH_DRAKE_DETECT_CMD" >/dev/null || \
  { echo "BLOCK: WS-4 T3 missing env-var contract"; exit 1; }
```

**Acceptance gates:**

```bash
T=$DMC/tests/test_detect_drake.py
F=$DMC/tests/fixtures/helpers/detect_drake
test -f "$T" && test -d "$F"

for s in stub_configured stub_found stub_missing stub_activation_required stub_unparseable stub_unknown_status stub_sentinel; do
  test -x "$F/$s.sh"
done

# stub_path_unavailable.sh deliberately ABSENT (synthesis §5.2 critic N5)
! test -e "$F/stub_path_unavailable.sh"

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

grep -F "HEPPH_DRAKE_DETECT_CMD" "$T"
grep -F 'tmp_path' "$T" | grep -F "bin"
grep -F 'install.sh' "$T"
! grep -F '/drake-install/scripts/install.sh' "$T"  # never reach into real tree

# WS-4-owned unknown (#1: drake_path-set short-circuit branch) — xfail(strict=True) per critic item 3 + item 4
grep -E "pytest\.mark\.xfail\(strict\s*=\s*True" "$T"
grep -F "WS-4 decision pending" "$T"
grep -F "ws2_synthesis.md §8.2" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T7 — `tests/test_extract_field.py` (9 functions + 1 conditional pin)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T1 schemas + T4 helper merged to main.
- **Inputs:** `ws2_synthesis.md` §1.3 (9 + 1 conditional with mandatory verbatim docstring); `ws4_plan_final.md` T4 (8-row exit grid).
- **Outputs:** `$DMC/tests/fixtures/helpers/extract_field/` (8 fixtures per §5.2: `relic_{present_number,present_null,no_xf,schema_version_v2,schema_mismatch,malformed}.json`, `summary_disallowed_null.json`, `tampered_schema_root/relic.schema.json`); `$DMC/tests/test_extract_field.py` (NEW).

**Pre-flight (CLI-shape; per critic item 5):**

```bash
H=$DMC/scripts/extract_field.py
RS=$REPO/plugins/shared/schemas/relic.schema.json
test -f "$H" || { echo "BLOCK: WS-4 T4 not merged to main"; exit 1; }
test -f "$RS" || { echo "BLOCK: WS-4 T1 schemas not merged to main"; exit 1; }
for f in --json --key --schema-version; do
  python "$H" --help 2>&1 | grep -F -- "$f" >/dev/null || \
    { echo "BLOCK: WS-4 T4 CLI drift — missing $f"; exit 1; }
done
```

**Acceptance gates:**

```bash
T=$DMC/tests/test_extract_field.py
F=$DMC/tests/fixtures/helpers/extract_field
test -f "$T" && test -d "$F"

for n in relic_present_number relic_present_null relic_no_xf relic_schema_version_v2 \
         relic_schema_mismatch relic_malformed summary_disallowed_null; do
  test -f "$F/$n.json"
done
test -f "$F/tampered_schema_root/relic.schema.json"

# Function-count band [9, 10] per critic gate audit on T7
COUNT=$(grep -cE "^def test_extract_field_" "$T")
test "$COUNT" -ge 9 && test "$COUNT" -le 10

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

# pytest.approx with rel=1e-9 (WS-2-owned binding decision per critic D6 — keep, NOT xfail)
grep -E "pytest\.approx\([^)]*rel\s*=\s*1e-9" "$T"

# Dropped case 11 must NOT appear
! grep -F "test_extract_field_default_schema_root" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T8 — `tests/test_verify_router_field_contract.py` (10 functions, mutated manifests)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1; WS-4 T5 helper merged to main; WS-1 fixtures.
- **Inputs:** `ws2_synthesis.md` §1.4 (mutations inlined; no `tmp_manifest`); `ws4_plan_final.md` T5 (`VerifyResult` dataclass with `.ok`/`.xfail`/`.fail`).
- **Outputs:** `$DMC/tests/test_verify_router_field_contract.py` (NEW).

**Pre-flight:**

```bash
H=$DMC/scripts/verify_router_field_contract.py
M=$DMC/contracts/router_contract.json
test -f "$H" || { echo "BLOCK: WS-4 T5 not merged to main"; exit 1; }
test -f "$M"
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('vc', pathlib.Path('$H'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert hasattr(m, 'verify_router_field_contract')
assert hasattr(m, 'VerifyResult')
" || { echo "BLOCK: WS-4 T5 module surface drift"; exit 1; }
```

**Acceptance gates:**

```bash
T=$DMC/tests/test_verify_router_field_contract.py
test -f "$T"

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

grep -E "pytest\.warns\(UserWarning,\s*match=r['\"]DRIFT_PRESENT_BUT_UNDOCUMENTED" "$T"

# critic N6: mutations inlined (no shared tmp_manifest fixture)
! grep -F "def tmp_manifest" "$T"
! grep -F "def tmp_manifest" "$DMC/tests/conftest.py"
COUNT=$(grep -c "tmp_path / [\"']m.json[\"']" "$T")
test "$COUNT" -ge 4

grep -F "^SUMMARY " "$T"
grep -E '\\d\+/\\d\+/\\d\+' "$T"

grep -F 'xfail) == 4' "$T" || grep -F "len(VerifyResult.xfail) == 4" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T9 — `tests/test_doc_vs_cli_parity.py` (3 mechanical assertions)

- **Owner:** `sonnet-implementer`. **Cycles:** 1. **Depends-on:** T1 (session fixture); WS-4 T2/T3/T4/T5 helpers + T7 router SKILL.md rewrite all merged to main.
- **Inputs:** `ws2_synthesis.md` §4 (whole-fence-as-one-string parsing LOCKED; no exit-code parity).
- **Outputs:** `$DMC/tests/test_doc_vs_cli_parity.py` (NEW).

**Pre-flight (CLI-shape + SKILL.md content; per critic items 5 + 6):**

```bash
S=$DMC/SKILL.md
SCR=$DMC/scripts
test -f "$S" && test -d "$SCR"

# All 4 helpers present AND each name appears in SKILL.md (broader than the draft's single grep)
for n in check_prereqs detect_drake extract_field verify_router_field_contract; do
  test -f "$SCR/$n.py" || { echo "BLOCK: $n.py not merged to main"; exit 1; }
  grep -F "$n.py" "$S" >/dev/null || { echo "BLOCK: WS-4 T7 SKILL.md missing $n.py"; exit 1; }
done

# At least one direct-path helper invocation in SKILL.md
grep -E 'python.*scripts/.*\.py' "$S" >/dev/null || { echo "BLOCK: T7 not finalized"; exit 1; }
```

**Parser semantics (LOCKED per critic item 6):**

The parser MUST:
1. NOT use `splitlines()` (would break the whole-fence-as-one-string rule when invocations span line continuations).
2. Accept code fences with OR without a language tag (i.e. ```` ```bash ````, ```` ```sh ````, AND ```` ``` ````).
3. Treat `--flag=value` as yielding the flag token `--flag` (split on `=` before flag-token collection).

The implementer MUST ship an inline parser-test fixture that exercises three canonical inputs (untagged fence with a flag; bash-tagged fence with a flag; fence containing `--flag=value`) and asserts the expected flag set on each.

**Acceptance gates:**

```bash
T=$DMC/tests/test_doc_vs_cli_parity.py
test -f "$T"

for fn in \
  test_doc_required_flags_present_in_help \
  test_doc_invocation_flags_exist_in_help \
  test_doc_references_each_helper_filename; do
  grep -F "def $fn" "$T"
done

# whole-fence-as-one-string parsing LOCKED
grep -E "(\`\`\`bash|\`\`\`)" "$T"
grep -F "split" "$T"
! grep -F "splitlines" "$T"        # critic item 6 (a)

# Untagged fence handling — parser must reference the no-language-tag case in a comment or fixture
grep -E "(no.?language.?tag|untagged.?fence|fence_no_lang|^[\"']\`\`\`$)" "$T"  # critic item 6 (b)

# Inline parser-test fixture present (a function whose name signals parser unit test)
grep -E "def test_(parser|fence_parser|flag_extraction)" "$T"  # critic item 6 (c)

# uses session-scoped helper_help_outputs fixture (avoid 8x re-invocation)
grep -F "helper_help_outputs" "$T"

# No exit-code parity test (synthesis §4)
! grep -F "exit_code_parity" "$T"

pytest "$T" -v; test $? -eq 0
```

---

### T10 — WS-2/WS-3 boundary check + `run_tests.sh`

- **Owner:** `opus-reviewer` (final lens-conformance audit + boundary grep). **Cycles:** 1. **Depends-on:** T1–T9.
- **Inputs:** `ws2_synthesis.md` §6 (boundary rule), §9 (out-of-scope); critic item 7 (broaden subprocess regex; add oracle-leak-from-tests guard).
- **Outputs:** `$DMC/tests/run_tests.sh` (NEW); audit log `$RUN/state/ws2_boundary_audit.txt`.

**Acceptance gates:**

```bash
TESTS=$DMC/tests
RUN_SH=$DMC/tests/run_tests.sh

# 1. Real-tool runs — POSITIVE WHITELIST (critic item 7)
# All subprocess.* and os.system/popen calls in tests MUST go via sys.executable, tmp_path,
# fixtures/*.sh, or stub_* paths. Anything else is a real-tool invocation.
LEAKS=$(grep -rE "(subprocess\.(run|call|check_call|check_output|Popen)|os\.system|os\.popen|os\.exec)" \
  "$TESTS" --include="*.py" | \
  grep -vE "(sys\.executable|tmp_path|fixtures/.*\.sh|stub_)" || true)
test -z "$LEAKS" || { echo "BOUNDARY LEAK: $LEAKS"; exit 1; }

# Real producer binaries by name — defense in depth
! grep -rE "(subprocess|os\.(system|popen|exec))[^#]*['\"](maddm|micromegas|wolframscript|drake)['\"]" "$TESTS" --include="*.py"
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

# 4. Oracle import boundary — TWO directions (critic item 7)
# 4a. Skill code does NOT import oracle
! grep -rE "(from\s+tests\.oracle|import\s+tests\.oracle)" "$DMC/scripts" 2>/dev/null
# 4b. Only test_oracle_thresholds.py imports oracle from tests/
for f in $(ls "$TESTS"/test_*.py 2>/dev/null | grep -v test_oracle_thresholds); do
  ! grep -F "tests.oracle" "$f"
  ! grep -E "from\s+\.oracle" "$f"
done

# 5. Total test count = 42 (+1 conditional)
COUNT=$(cd "$DMC" && pytest tests --collect-only -q 2>/dev/null | grep -E "^tests/" | wc -l | tr -d ' ')
test "$COUNT" -ge 42 && test "$COUNT" -le 43

# 6. Whole-suite green (including WS-1 non-regression)
pytest "$TESTS" -v; test $? -eq 0

# 7. run_tests.sh exists, executable, exits 0
test -x "$RUN_SH"
"$RUN_SH"; test $? -eq 0
```

---

## 4. Sequencing

```
Pre-condition: WS-4 cycle 1 reviewer signs off and WS-4 branch merges to main.
               Helpers: check_prereqs.py, detect_drake.py, extract_field.py,
               verify_router_field_contract.py + relic/annihilation schemas + T7
               SKILL.md rewrite all on main.

Cycle 1 (parallel, no WS-4 helper deps; opens once WS-4 merge lands):
  T1 (sonnet, conftest)
  T2 (sonnet, oracle module)
  T3 (sonnet, spectra fixtures)
  T4 (sonnet, oracle-thresholds test) — depends on T2+T3 mid-cycle

Cycle 2 (each gated on its WS-4 helper now on main):
  T5 (sonnet, test_check_prereqs)
  T6 (sonnet, test_detect_drake)
  T7 (sonnet, test_extract_field)
  T8 (sonnet, test_verify_router_field_contract)

Cycle 3 (gated on WS-4 T7 router SKILL.md rewrite on main):
  T9 (sonnet, doc-vs-CLI parity)

Cycle 4: T10 (opus-reviewer, boundary audit + run_tests.sh)
```

**Critical path:** T1 → (WS-4 helpers on main) → T8 / T7 → T9 → T10 (4 cycles WS-2-side; total wall-clock depends on whether WS-4 retries).

**Cycle envelope (FINAL):** **4 binding, 6 ceiling.** (Per critic item 1: 4 ceiling claimed by drafter is over-tight; if WS-4 hits its 6-cycle ceiling, WS-2 envelope extends one cycle. The 6-cycle ceiling explicitly absorbs: one WS-4 retry rippling into WS-2, plus one WS-2 retry slot for any per-helper test if WS-4 lands a behavior the synthesis didn't pin and forces a new xfail authoring.)

---

## 5. Gates summary

T1 ~8, T2 ~6, T3 ~10, T4 ~6, T5 ~14 (incl. CLI-shape pre-flight and xfail), T6 ~17 (incl. CLI-shape pre-flight and xfail), T7 ~16 (incl. CLI-shape pre-flight and count band), T8 ~11, T9 ~11 (incl. parser-semantics sub-gates), T10 ~14 (incl. positive whitelist + bidirectional oracle boundary). **~113 mechanical sub-gates total.** No `wc -l > 0` style claims-of-done; every gate carries a content assertion or pytest run.

---

## 6. Coordination

### 6.1 With WS-1 (MERGED)

- WS-2 conftest (T1) defines `_HERE` / `_REPO_ROOT` / `_DEFAULT_MANIFEST` with the **exact** WS-1 names. WS-1 `test_router_contract.py` keeps its module-level constants (no shadow); it continues to pass unchanged. T1 acceptance gate runs `pytest test_router_contract.py` to prove non-regression.
- WS-2 does NOT modify WS-1 test files. WS-4 T8 owns the retrofit that rewrites WS-1 to import from conftest.

### 6.2 With WS-4 (cycle 1 just completed)

| WS-2 task | Required WS-4 deliverable on main | Pre-flight beyond `test -f` |
|---|---|---|
| T1 | none — conftest is independent | `test -f tests/__init__.py` |
| T2 | none | (none) |
| T3 | none | (none) |
| T4 | T2 + T3 outputs (within WS-2) | (none) |
| T5 | WS-4 T2 (`check_prereqs.py`) | `--help` greps for `--config`, `--model`, `--manifest` |
| T6 | WS-4 T3 (`detect_drake.py`) | `--help` greps for `--config`, `--manifest`, `HEPPH_DRAKE_DETECT_CMD` |
| T7 | WS-4 T1 schemas + T4 (`extract_field.py`) | `--help` greps for `--json`, `--key`, `--schema-version` |
| T8 | WS-4 T5 (`verify_router_field_contract.py`) | importable surface check (`verify_router_field_contract`, `VerifyResult`) |
| T9 | WS-4 T2/T3/T4/T5 helpers + T7 SKILL.md rewrite | all 4 `scripts/*.py` filenames grep-present in `SKILL.md` |
| T10 | T1–T9 in WS-2 | (whole-suite + run_tests.sh) |

### 6.3 Three documented-decision unknowns (synthesis §8.2 — RESOLVED per critic items 3 + 4)

The three "punted unknowns" are NOT WS-4 cycle re-dispatch triggers (critic item 4 favors §8.2's "wins" reading at the test-codification level; the §6.3-vs-§8.2 ambiguity is resolved here as: at WS-2 plan-finalize time these are NOT triggers, because WS-4 cycle 1 has already landed; the cycle-1 behavior is the decision-of-record). For the **two WS-4-owned** decisions, WS-2 uses `pytest.mark.xfail(strict=True)` until a manager-level decision-of-record exists in `state/MANAGER_DECISIONS.md`. For the **WS-2-owned** float-precision decision, WS-2 binds `pytest.approx(rel=1e-9)`.

| # | Unknown | Posture |
|---|---|---|
| 1 | `detect_drake` short-circuit when `drake_path` is set | T6 test 7 → `pytest.mark.xfail(strict=True, reason="WS-4 decision pending — see ws2_synthesis.md §8.2")`. When manager records the decision, flip xfail to a normal test with docstring referencing the decision-of-record. |
| 2 | `check_prereqs --model nonexistent_in_config` exit code (1 vs 2) | T5 test 6 → same xfail(strict=True) posture. |
| 3 | `extract_field` float rendering precision | T7 → `pytest.approx(rel=1e-9)` (binding WS-2 decision per critic D6); docstring records the binding. **NOT xfail** — this is WS-2-owned. |

**Re-dispatch trigger condition:** if WS-2 implementation discovers WS-4 cycle-1 cannot be made to satisfy the xfail expectation (i.e. the helper's behavior is internally inconsistent with synthesis §1.1 / §1.2 in a way that breaks even xfail authoring), surface to manager — that IS a WS-4 re-dispatch trigger from the WS-2 side.

### 6.4 With WS-3

- WS-2 ships the 4 spectra fixtures + README; WS-3 consumes them for LLM playtest.
- WS-2 does NOT run the LLM; WS-2 does NOT invoke real producer binaries.

---

## 7. Pre-flight (CLI-shape, per critic item 5)

Beyond the per-task pre-flights inlined under T5/T6/T7/T9 above, the implementer at task-start time runs:

1. **WS-4 merge confirmation.** `git -C $REPO log main --oneline -- $DMC/scripts/check_prereqs.py` returns at least one commit; same for the other three helpers and the schemas.
2. **Conftest name collision.** T1 must use the WS-1 names verbatim. Run `pytest test_router_contract.py` after T1 lands; if it breaks, T1 is wrong.
3. **CLI-shape pre-flights** (T5/T6/T7/T9): `--help` greps for required flags. Three lines of bash per task; catches WS-4 helper-CLI drift cleanly.
4. **WS-4 T7 router SKILL.md rewrite.** T9 cannot start until T7 lands on main; pre-flight greps SKILL.md for all 4 helper filenames.
5. **Oracle no-skill-code-import.** T2 + T4 + T10 all assert this boundary. Any skill-code path importing `tests.oracle` is a hard violation.
6. **Real-tool boundary.** T6 test 8 stubs `install.sh` via `tmp_path/bin`; never reaches into `/drake-install/scripts/install.sh`. T10 boundary audit greps for the real path and asserts absence.
7. **No `tmp_manifest` fixture.** Critic N6: each of the 4 mutation tests in T8 inlines its `tmp_path / "m.json"` write. T8 gate asserts the fixture is NOT defined.
8. **xfail(strict=True) posture.** T5 test 6 and T6 test 7: each carries `pytest.mark.xfail(strict=True, reason="WS-4 decision pending — see ws2_synthesis.md §8.2")`.
9. **Conditional 10th `extract_field` test.** T7 ships either 9 or 10 functions; if 10, the verbatim mandatory docstring (synthesis §1.3) is grep-asserted. T7 also asserts function-count is in [9, 10].
10. **Session-scoped `--help` capture.** T1 conftest must declare `helper_help_outputs` with `scope="session"` (critic N4); T9 imports it.
11. **`spectrum/v1` schema.** Out-of-scope for this run. T3 gate asserts the schema file does NOT exist.
12. **No GitHub Actions / CI / Makefile.** Synthesis §9. T10 ships `run_tests.sh` only.

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

## 9. 7-item adjudication (critique → final-plan binding)

| # | Critic item | Decision (binding for implementer) | Where applied in this plan |
|---|---|---|---|
| 1 | Cycle envelope (4/5 vs 4/6) | **4 binding, 6 ceiling.** Drafter's 5-ceiling claim was over-optimistic; if WS-4 retries, WS-2 absorbs the slip. | §4 Sequencing (cycle envelope clause). |
| 2 | T1 owner downgrade opus → sonnet | **Sonnet.** Synthesis §3.1 spec is precise; no judgment. Saves opus budget for T10. | T1 owner line. |
| 3 | Document-of-decision → `xfail(strict=True)` | **Adopt `xfail(strict=True)` for the two WS-4-owned decisions** (`detect_drake` short-circuit; `check_prereqs --model nonexistent_in_config` exit code). **Keep float-precision binding** (`pytest.approx(rel=1e-9)`) — that's WS-2-owned. Flip xfail when manager records decision-of-record. | T5 + T6 acceptance gates; §6.3 table. |
| 4 | Plan §6.3 vs synthesis §8.2 contradiction | **§8.2 wins at the test-codification level — these are NOT re-dispatch triggers from WS-2 side at plan-finalize time** (WS-4 cycle 1 has just landed; cycle-1 behavior is the decision-of-record). However, if WS-2 implementation discovers cycle-1 behavior cannot satisfy even xfail authoring, that DOES become a re-dispatch trigger. | §6.3 (final language). |
| 5 | CLI-shape pre-flights for T5/T6/T7/T9 | **Adopt.** Each task adds 3-4 lines of `--help` grep before authoring. Catches WS-4 CLI drift cleanly. | T5/T6/T7/T9 each have a `Pre-flight (CLI-shape; per critic item 5)` block. |
| 6 | T9 parser semantics pinning | **Pin three rules:** (a) `splitlines` forbidden, (b) untagged fences must be accepted, (c) inline parser-test fixture validates the expected flag set on three canonical inputs (untagged fence; bash-tagged fence; `--flag=value` form). | T9 parser-semantics block + acceptance gates. |
| 7 | T10 boundary audit broadening | **Adopt:** positive whitelist for `subprocess.*`/`os.*` calls (only `sys.executable` / `tmp_path` / `fixtures/*.sh` / `stub_*` permitted); add oracle-leak-from-tests guard (only `test_oracle_thresholds.py` imports `tests.oracle`). | T10 acceptance gate 1 (LEAKS variable) + gate 4b (per-test-file oracle import check). |

---

## 10. Ready check

Predicates that must hold before T1 starts.

1. WS-4 cycle 1 reviewer has signed off; WS-4 branch has merged to main.
2. `test -f $DMC/scripts/check_prereqs.py` (and the other three helpers) on the main worktree.
3. `test -f $REPO/plugins/shared/schemas/relic.schema.json` and `annihilation.schema.json`.
4. `test -f $DMC/tests/test_router_contract.py` (WS-1 already on main).
5. `test -f $DMC/contracts/router_contract.json`.
6. `test -d $DMC/tests/fixtures` (WS-1 fixtures present).
7. `test -f $DMC/tests/__init__.py` (required for the relative import in T1).
8. `test ! -f $DMC/tests/conftest.py` (T1 first to create — must NOT pre-exist).
9. `python -c 'import jsonschema, pytest'` exits 0.
10. Implementer has read `briefs/ROUTING_LENS.md`, `ws2_synthesis.md`, `ws2_plan_critique.md`, AND this plan end-to-end. No partial reads.

For per-task ready checks, see §6.2 table.

**Worktree branch name (proposed):** `ws2-test-harness` rooted at the post-WS-4-merge main commit.

---

## Closing routing-lens conformance check

The plan respects the lens: WS-2 tests model-agnostic mechanical behavior; oracle is permitted exception (test infra, no skill-code import; bidirectional boundary enforced by T10); doc-vs-CLI parity is mechanical; the four `spectra/` fixtures are data, not assertions. WS-2 does NOT invoke real producer binaries; does NOT exercise LLM behavior; does NOT modify helpers. The 7-item critique mandate is fully adjudicated. **Plan is lens-conformant and ready for the manager's go-decision pending WS-4 merge to main.**
