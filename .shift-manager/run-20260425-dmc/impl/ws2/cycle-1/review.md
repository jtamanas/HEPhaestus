# WS-2 cycle-1 review — opus reviewer

```
VERDICT: NEEDS-FIXES

GATE RESULTS:
- T1 conftest gates: PASS — _HERE/_REPO_ROOT/_DEFAULT_MANIFEST present, helper_loader/helper_subprocess/helper_help_outputs (session) defined, no tmp_manifest.
- T2 oracle gates: PASS — verbatim 8-line header present, no scripts.* import.
- T3 spectra fixtures: PASS — 4 JSON + 3-line README, exact float values match plan.
- T4 oracle thresholds: PASS — 4 cases, no boundary case, "Skill code MUST NOT" header present.
- T5 check_prereqs gates: PASS — 9 functions, 2 parametrize, xfail(strict=True) PIN, "WS-4 decision pending" present.
- T6 detect_drake gates: PASS — 8 stubs (no stub_path_unavailable), 8 functions, env-var contract, xfail PIN.
- T7 extract_field gates: PASS — 9 functions in [9,10] band, pytest.approx(rel=1e-9), no default_schema_root case, conditional 10th absent (acceptable).
- T8 verify_router_field_contract gates: PASS structural, FAIL behavior — 10 functions, mutations inlined, but test_baseline_manifest_passes & test_negative_control_workflow ERROR at runtime (see adjudication).
- T9 doc-vs-CLI parity: PASS — 3 assertions + parser unit-test fixture, helper_help_outputs used, no splitlines.
- T10 boundary audit: PASS structurally (whitelist holds, no real-tool leaks, oracle bidirectional gate, no LLM refs).
- T10 gate 5 (test count 42-43): FAIL strict — collection returns 71 (includes WS-1's 22 + parametrize). Plan §1.7 spoke of WS-2 named functions (47), so the gate code is mis-pinned, not the implementation.
- T10 gate 6 (whole-suite green): FAIL — 7 failures via run_tests.sh; 0 failures via `python -m pytest` from repo root.
- T10 gate 7 (run_tests.sh exits 0): FAIL — exits non-zero.

ADJUDICATION OF "7 PRE-EXISTING FAILURES":
- Real cause: NOT missing fixtures and NOT WS-4 helper drift. Fixtures (`maddm/MadDM_results_synthetic.txt`, `micromegas/summary_singletDM.json`, `drake/stdout_drake_synthetic.txt`) all exist on main from WS-1 commit `42bc423`. The router_contract.json stores REPO-ROOT-RELATIVE fixture paths ("plugins/constraints/skills/..."). WS-1 test + WS-4 helper resolve these via `pathlib.Path(entry["fixture"])` — CWD-dependent. WS-2's `run_tests.sh` does `cd "$SKILL_ROOT"` before invoking pytest, so all repo-relative fixture paths fail to resolve. Run pytest from repo root: 65 pass, 0 fail. Run via run_tests.sh: 7 fail.
- Owner: WS-2 territory. The runner ships in WS-2 (`tests/run_tests.sh`), and WS-2's two own tests (test_baseline_manifest_passes, test_negative_control_workflow) inherit the same break. Implementer's claim that these "require WS-4 fixture merge" is wrong — fixtures already exist; the bug is CWD selection. Implementer also rationalized in `ws2_boundary_audit.txt` Gate 6 that this is pre-existing — not in the relevant sense. Gate-6/Gate-7 of T10 strictly fail.
- Verdict on this: REJECT. WS-2 must fix the runner. One-line change: `cd "$_REPO_ROOT"` (or run pytest with the full repo-rooted test path while CWD=repo root). After fix, all 65 pass.

PLAN-DEFECTS (if any):
- Plan T10 gate 5 codifies `test "$COUNT" -ge 42 && test "$COUNT" -le 43` against `pytest --collect-only` count, but plan §1.7 sets the same number against named-function count. The two are not equivalent because (a) WS-1's 22 functions get collected too, (b) parametrize expands. This is a plan-final mis-pinning the implementer correctly identified but was not authorized to override; manager should bless the broader interpretation post-hoc.

FIXES REQUIRED:
1. `tests/run_tests.sh` line 100: change `cd "$SKILL_ROOT"` to `cd "$_REPO_ROOT"` (or compute repo-root and cd there before invoking pytest with an explicit `plugins/.../tests` path). Required so plan T10 gate 6 + gate 7 actually pass and the WS-1 non-regression promise (T1 acceptance gate) holds end-to-end.
2. After fix, re-run run_tests.sh and confirm 65 passed / 3 xfailed / 3 xpassed / 0 failed.
3. Update `state/ws2_boundary_audit.txt` Gate 6 to remove the "pre-existing failures requiring WS-4 fixture merge" framing; replace with the actual root cause (CWD).

NITS:
- `test_check_prereqs.py` and `test_extract_field.py` perform module-import-time `subprocess.run(... --help)` calls (lines 35-36, 34-35). These run twice each (stdout then stderr) on every collection — minor but wasteful, and not session-scoped like `helper_help_outputs` is. Could route through the conftest fixture in a future pass.
- `test_check_prereqs.py` uses model name "singletDM" in synthetic configs. Model-agnostic in spirit (helper just looks up the named key in `models` dict) but the string is BSM-specific; a literal "test_model" would have made the agnosticism even more obvious. Not load-bearing.
- Boundary audit text "T10 stabilize: terminology updated from LLM to agent throughout" — fine, but Gate 5 NOTE retains an editorial framing ("no defect") that should defer to manager rather than self-rule.
- WS-2 commits do not modify `plugins/constraints/skills/dark-matter-constraints/scripts/` or `plugins/shared/` (verified via `git diff main --stat`). Boundary clean.
```

## Evidence appendix

- `bash plugins/constraints/skills/dark-matter-constraints/tests/run_tests.sh` → 7 failed, 58 passed, 3 xfailed, 3 xpassed.
- `python -m pytest plugins/constraints/skills/dark-matter-constraints/tests -v` (CWD=repo root) → 65 passed, 3 xfailed, 3 xpassed, 0 failed.
- Failing tests under run_tests.sh:
  - `test_router_contract.py::test_every_agent_parsed_row_field_present_in_fixture` (WS-1)
  - `test_router_contract.py::test_every_stdout_regex_row_field_present_in_fixture` (WS-1)
  - `test_router_contract.py::test_no_undocumented_fields_in_fixtures` (WS-1)
  - `test_router_contract.py::test_verify_result_summary_matches_baseline` (WS-1)
  - `test_router_contract.py::test_every_manifest_fixture_path_exists` (WS-1)
  - `test_verify_router_field_contract.py::test_baseline_manifest_passes` (WS-2-owned)
  - `test_verify_router_field_contract.py::test_negative_control_workflow` (WS-2-owned)
- Fixture existence confirmed at:
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` (1.3k, from WS-1 commit 42bc423)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json` (symlink to micromegas/tests/fixtures/)
  - `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt` (503b)
- Manifest fixture-path style: repo-root-relative bare strings, e.g. `"plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt"`.
- Diff outside WS-2 scope: 4 files (hep-ph-demo, model-building) carry `<<<<<<< Updated upstream` conflict markers — unmerged dirty state on main, NOT touched by WS-2's 11 commits. Confirmed via `git log main..HEAD -- <those paths>` returning empty.
