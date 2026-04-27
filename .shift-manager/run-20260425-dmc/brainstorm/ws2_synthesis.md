# WS-2 Synthesis — Router Test Harness (final design)

**Synthesizer:** ws2-brainstorm-synthesizer
**Inputs consumed end-to-end (in order):** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md`; `brainstorm/ws2_propose.md` (391 lines, ~53 cases proposed); `brainstorm/ws2_critique.md` (179 lines, ACCEPT-WITH-CHANGES, 10 items); `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (487 lines, WS-1 merged).

**Verdict on critique:** ACCEPT. All ten items are resolved below as binding decisions for the WS-2 plan-drafter — no "implementer reconciles" hedges. Final test count **42** (down from proposer's 53). Oracle script is test infra and stays that way (header forbids skill-code import). Conftest names are the canonical WS-1 trio (`_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST`); WS-4 T8 retrofit imports them from there. WS-2/WS-3 boundary is locked: any test that would invoke a real producer binary (MadDM/micrOMEGAs/DRAKE/Wolfram or a real `install.sh` shelling further) is WS-3.

---

## 1. Final test inventory per helper

Counts include named test functions. Parametrized cases collapse into a single function with N param rows; "(× N)" notes the row count.

### 1.1 `tests/test_check_prereqs.py` — 9 functions (12 cases of behavior)

Per `ws4_synthesis.md` §1.1. Exit-code grid: 0 / 1 / 2. Blocker codes per §1.1.

1. `test_check_prereqs_all_present_returns_ok_exit_zero` — happy path; `status:"ok"`, exit 0.
2. `test_check_prereqs_tool_path_missing_emits_blocker_exit_one` — **parametrize × 2**: `(maddm_path → MADDM_MISSING, /maddm-install)`, `(micromegas_path → MICROMEGAS_MISSING, /micromegas-install)`. Collapses proposer cases 2 + 3.
3. `test_check_prereqs_drake_path_blocker_exit_one` — **parametrize × 2**: `(unset → DRAKE_PATH_UNSET)`, `(bogus path → blocker code starts with "DRAKE_")`. Collapses proposer cases 4 + 5.
4. `test_check_prereqs_ufo_missing_emits_blocker_exit_one` — `models.<model>.ufo_path` nonexistent ⇒ `UFO_MISSING`, exit 1.
5. `test_check_prereqs_slha_missing_emits_hint_status_remains_ok` — `mssm_like` model lacks `latest_slha`; `SLHA_MISSING_HINT` in `blockers[]` but `status:"ok"`, exit 0 (LLM keeps the call).
6. `test_check_prereqs_unknown_model_documents_decision` — `--model nonexistent_in_config`. Docstring: "this assertion pins whatever WS-4 lands; if WS-4 changes behavior, this test must be intentionally rewritten." Asserts exit code in {1, 2} and a meaningful blocker/error code is emitted.
7. `test_check_prereqs_unparseable_manifest_exit_two` — `{not json` ⇒ exit 2, stderr `code:"PREREQ_HELPER_INTERNAL"`.
8. `test_check_prereqs_unreadable_config_exit_two` — `--config` is a directory ⇒ exit 2.
9. `test_check_prereqs_structural_outputs` — happy path: `len(checked) >= len(manifest.config_keys)`; each entry has `key`, `exists`, `path`. AND multi-blocker: two prereqs missing ⇒ both blocker codes present, exit 1. (Ordering NOT asserted — synthesis doesn't pin it; critic D1.)

### 1.2 `tests/test_detect_drake.py` — 8 functions

Per `ws4_synthesis.md` §1.2 + WS-4 plan T3. All eight distinct branches; no cuts.

1. `test_detect_drake_configured_emits_proceed`
2. `test_detect_drake_found_emits_proceed`
3. `test_detect_drake_missing_emits_DRAKE_MISSING`
4. `test_detect_drake_activation_required_emits_DRAKE_ACTIVATION_REQUIRED` — env-var stub strategy; see §3 fake.
5. `test_detect_drake_unparseable_json_emits_DRAKE_UNAVAILABLE` — non-JSON stub.
6. `test_detect_drake_unknown_status_literal_drift_to_unparseable` — valid JSON, `status:"frobbed"` not in manifest enum literals. Distinct from #5 (different code path).
7. `test_detect_drake_drake_path_set_short_circuit_documents_decision` — config has `drake_path:"/some/dir"` set; pin whichever branch WS-4 picks (decision-of-record). Stub touches sentinel; assert sentinel state matches branch chosen.
8. `test_detect_drake_default_command_with_stubbed_install_sh` — `HEPPH_DRAKE_DETECT_CMD` unset; **`install.sh` itself stubbed via `tmp_path / "bin" / "install.sh"` + `monkeypatch.setenv("PATH", ...)`** (critic N5: do NOT invoke the real `install.sh`). Asserts the documented fallback contract.

### 1.3 `tests/test_extract_field.py` — 9 functions

Per `ws4_synthesis.md` §1.3 (LOCKED 7-row grid) + WS-4 plan T4 (8th row added by critic). Drop proposer case 11 (default-schema-root resolution — already covered by WS-4 T4 acceptance gate; would mirror gate code per proposer §8.1's own rule). Keep proposer case 12 (nested-pointer pin) **with mandatory forward-compat docstring**.

1. `test_extract_field_present_number_returns_zero` — valid `relic.json`, `--key omega_h2`, exit 0.
2. `test_extract_field_present_null_returns_zero` — `omega_h2: null`, schema `oneOf [null, number]`, exit 0. Distinguishes from absent.
3. `test_extract_field_key_absent_exits_one_KEY_ABSENT`
4. `test_extract_field_schema_version_drift_in_data_exits_one_VERSION_DRIFT`
5. `test_extract_field_schema_id_drift_in_file_exits_one_VERSION_DRIFT` — tampered `$id`. Exercises §1.3 self-check ordering.
6. `test_extract_field_type_mismatch_exits_one_SCHEMA_MISMATCH`
7. `test_extract_field_unreadable_file_exits_two_internal`
8. `test_extract_field_malformed_json_exits_two_internal`
9. `test_extract_field_disallowed_null_on_scattering_v1_exits_one_SCHEMA_MISMATCH` — cross-validates `scattering.schema.json` (different schema family from #6).

**Plus** `test_extract_field_v1_does_not_support_nested_pointer_PIN` (case 12, conditional). Docstring (verbatim, mandatory): *"This pins v1 behavior: `--key channel_fractions.bb` is treated as a literal top-level key and exits with KEY_ABSENT. If a future v1.1 adds `--json-pointer`, this test MUST be intentionally rewritten, not deleted — the v1 contract still applies when `--json-pointer` is not passed."* Counted in the 9 only if the docstring is present.

Floats compared via `pytest.approx(value, rel=1e-9)` per critic D6.

### 1.4 `tests/test_verify_router_field_contract.py` — 10 functions

Per `ws4_synthesis.md` §1.4. Exercises the helper against MUTATED manifests; WS-1 already covers shipped-manifest behavior (and WS-4 T8 will retrofit that test to import this helper — that's WS-4's task, not WS-2).

1. `test_baseline_manifest_passes` — exit 0; `VerifyResult.fail == []`; `len(VerifyResult.xfail) == 4`.
2. `test_summary_line_format_matches_pattern` — final stdout line matches `^SUMMARY \d+/\d+/\d+$`.
3. `test_renamed_field_emits_DRIFT_PRODUCER_RENAMED_or_DOCUMENTED_BUT_ABSENT` — synthesis §1.4 enumerates both as candidates.
4. `test_invented_name_emits_DRIFT_ROUTER_INVENTED_NAME` — tmp router SKILL.md without the field name.
5. `test_documented_but_absent_emits_DRIFT_DOCUMENTED_BUT_ABSENT` — empty fixture file.
6. `test_undocumented_present_emits_DRIFT_PRESENT_BUT_UNDOCUMENTED` — `pytest.warns(UserWarning, match=r"DRIFT_PRESENT_BUT_UNDOCUMENTED")` per critic N3.
7. `test_internal_inconsistency_emits_DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY` — pending_producer_doc_fix row's xfail reason.
8. `test_unparseable_manifest_exits_two`
9. `test_importable_dataclass_surface` — `verify_router_field_contract`, `VerifyResult` import; `.ok`, `.xfail`, `.fail` lists exist.
10. `test_negative_control_workflow` — mutate-then-restore; pins WS-1 plan T3 acceptance gate #4 invariant survives the WS-4 extraction.

Manifest mutations are **inlined** per test (critic N6: drop `tmp_manifest` fixture). Each of tests 3, 4, 5, 6 does its own `tmp_path / "m.json"` write.

### 1.5 `tests/test_doc_vs_cli_parity.py` — 3 functions

Per critic D5. Capture `--help` once via session-scoped fixture (`conftest.helper_help_outputs`).

1. `test_doc_required_flags_present_in_help` — Direction A: every `--<flag>` in `--help` for a helper appears in ≥1 SKILL.md invocation block for that helper.
2. `test_doc_invocation_flags_exist_in_help` — Direction B: every `--<flag>` in a SKILL.md invocation block is real per `--help`.
3. `test_doc_references_each_helper_filename` — path-drift assertion: for every `scripts/*.py` helper, ≥1 SKILL.md invocation block references its filename. (Critic D5 third assertion.)

### 1.6 `tests/test_oracle_thresholds.py` — 4 functions (oracle, see §2)

Per critic D2: trim from 5 to 4. Drop "exactly at boundary" (the equality boundary lives in SKILL.md prose, not the oracle).

1. `test_oracle_threshold_above_fires` — `gap_fraction = 0.10001 ⇒ trigger=True`.
2. `test_oracle_threshold_below_does_not_fire` — `gap_fraction = 0.09999 ⇒ trigger=False`.
3. `test_oracle_resonance_5pct_above_fires` — `0.0501 ⇒ trigger=True`.
4. `test_oracle_resonance_5pct_below_does_not_fire` — `0.0499 ⇒ trigger=False`.

### 1.7 Total

`9 + 8 + 9 (+1 conditional) + 10 + 3 + 4 = 43` if the nested-pointer pin lands with its mandatory docstring; **42** if it's dropped. Plan-drafter targets **42 + 1 conditional** with the docstring requirement called out as a gate.

---

## 2. Oracle script spec

**Path:** `plugins/constraints/skills/dark-matter-constraints/tests/oracle/threshold_arithmetic.py`.

**File header (verbatim, mandatory — first 8 lines):**

```python
"""Test-only oracle for SKILL.md threshold prose.

This module is TEST INFRASTRUCTURE. Skill code MUST NOT import from it.
The /dark-matter-constraints router uses the LLM to apply heuristic thresholds
(10% spectrum gap, 5% near-resonance) per the routing lens. This oracle
encodes the same arithmetic as a lossy reference, used by tests to detect
SKILL.md prose drift. If oracle and prose disagree, prose wins (rewrite the
oracle, not the prose).
"""
```

**Verbatim SKILL.md sentences in docstring.** Every oracle function carries the exact SKILL.md sentence(s) it claims to encode in its docstring. Plan-drafter sources these from the rewritten SKILL.md (WS-4 T6); if not yet written at WS-2 implementation time, WS-2 sources from current `SKILL.md` Step 3 / Step 5b prose and notes "verbatim-as-of-WS-4-T6-pending."

**Tiebreaker rule (binding, in module docstring above):** SKILL.md prose is source of truth; oracle is the lossy encoding. WS-3 surfaces oracle-vs-prose disagreement ⇒ rewrite the oracle.

**4 cases (no equality-boundary case):** see §1.6.

**Lens-conformance reminder.** The oracle is a permitted exception to "no code-side threshold arithmetic" because (a) it lives at `tests/oracle/`, (b) the header forbids skill-code import, (c) it does not run at router invocation time. Any attempt to `from tests.oracle.threshold_arithmetic import ...` from skill code is a hard violation; WS-2 ships a `test_oracle_no_skill_imports` static check (covered by the path-drift parity test #3 above — `tests/oracle/` is not a `scripts/` path).

---

## 3. Conftest spec

**Path:** `plugins/constraints/skills/dark-matter-constraints/tests/conftest.py` (new — WS-2).

### 3.1 Canonical name table (LOAD-BEARING for WS-4 T8)

| Name | Type | Definition | Importer |
|---|---|---|---|
| `_HERE` | `pathlib.Path` (module-level constant) | `pathlib.Path(__file__).parent` (resolves to `tests/`) | WS-1 `test_router_contract.py` (post-WS-4-T8 retrofit), WS-2 test files |
| `_REPO_ROOT` | `pathlib.Path` (module-level constant) | `_HERE.parent.parent.parent.parent.parent` (5 levels up) | same |
| `_DEFAULT_MANIFEST` | `pathlib.Path` (module-level constant) | `_HERE.parent / "contracts" / "router_contract.json"` | same |

Names match WS-1's spelling exactly. WS-4 T8's retrofit replaces WS-1's module-level constants (currently lines 37–40 of `test_router_contract.py`) with `from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST`. Single source of truth; no shadowing.

### 3.2 WS-4 T8 import path (locked)

`from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST`

(Relative import; both `tests/__init__.py` and `tests/conftest.py` exist; pytest auto-discovers conftest fixtures across the same directory. The relative import is the cleanest since `tests/` is already a package.)

### 3.3 Other conftest entries

- `helper_loader(helper_name) -> module` — fixture wrapping `importlib.util.spec_from_file_location` for the four helpers under `scripts/`. Used by every helper-direct test.
- `helper_subprocess(helper_name, args, env={}) -> CompletedProcess` — fixture for CLI-mode tests.
- `helper_help_outputs` — **session-scoped** fixture (per critic N4). Captures `subprocess.run([sys.executable, helper_path, "--help"])` stdout once for all four helpers; returned as a `dict[str, str]`. Used by `test_doc_vs_cli_parity.py` to avoid 8× re-invocation.
- **No** `tmp_manifest` fixture (critic N6 + this synthesis): the four mutation tests inline their `tmp_path / "m.json"` writes. Less infrastructure; tests are easier to read at this scale.

---

## 4. Doc-vs-CLI parity spec

Three mechanical assertions, no LLM judgment.

### 4.1 Assertion 1 — Direction A (helper → doc)

**Code-fence parsing rule (LOCKED).** For each `python …/scripts/<helper>.py` invocation in SKILL.md:
1. Identify code fences delimited by ` ```bash ` / ` ``` ` (markdown convention). Treat each fence's contents as ONE string.
2. Tokenize that string on whitespace.
3. Collect every token starting with `--` as a flag mention.

Do NOT attempt to reason about line continuations (`\`), indentation, or quoted args. The whole-fence-as-one-string rule sidesteps the lot.

**Assertion:** for each helper, every required `--<flag>` (per its `--help`) appears as a token in ≥1 SKILL.md fence that also references the helper filename.

### 4.2 Assertion 2 — Direction B (doc → helper)

**Assertion:** every `--<flag>` token in any SKILL.md fence that references a helper filename must appear in that helper's `--help` flag set. Catches the case where SKILL.md teaches the LLM to call a flag that doesn't exist.

### 4.3 Assertion 3 — Path-drift

**Assertion:** for every `*.py` file in `plugins/constraints/skills/dark-matter-constraints/scripts/`, ≥1 SKILL.md code fence references its filename. Catches `check_prereq.py` typos vs `check_prereqs.py` reality.

**Sources:** primary doc is `plugins/constraints/skills/dark-matter-constraints/SKILL.md`. Secondary doc `contracts/AUDIT.md` is consulted only if it contains code fences referencing scripts (currently it doesn't; if it does post-WS-4-T1, parity extends).

**Helper `--help` capture:** session-scoped fixture (§3.3). One subprocess per helper per session. Skip exit-code parity entirely (argparse doesn't print exit codes; would require helper `--help` overload, out of scope).

---

## 5. Fixture inventory

### 5.1 Reused from WS-1 (no copies)

- `tests/fixtures/maddm/MadDM_results_synthetic.txt` — re-used by `test_verify_router_field_contract.py` baseline.
- `tests/fixtures/micromegas/summary_singletDM.json` (symlink) — re-used by `test_extract_field.py` happy-path rows.
- `tests/fixtures/drake/stdout_drake_synthetic.txt` — re-used by drift-injection.

### 5.2 New fixtures shipped by WS-2

Under `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/`:

**`helpers/check_prereqs/`:**
- `manifest_minimal.json` — 3 `config_keys` rows; empty `output_fields`/`status_enums`.
- `manifest_unparseable.json` — `{not json`.
- `config_all_present.json`, `config_maddm_missing.json`, `config_micromegas_missing.json`, `config_drake_unset.json`, `config_drake_nonexistent.json`, `config_no_ufo.json`, `config_mssm_like.json`.

**`helpers/detect_drake/`:**
- `stub_configured.sh`, `stub_found.sh`, `stub_missing.sh`, `stub_activation_required.sh`, `stub_unparseable.sh`, `stub_unknown_status.sh`.
- `stub_sentinel.sh` — touches sentinel file (proves stub was/wasn't invoked).
- **No** `stub_path_unavailable.sh` for the proposer's "real install.sh" path. Instead, test 8 ships `bin/install.sh` (a stub) under `tmp_path` and uses `monkeypatch.setenv("PATH", str(tmp_path/"bin") + ":" + os.environ["PATH"])`. Critic N5 boundary; WS-2 does not invoke the real `install.sh`.

**`helpers/extract_field/`:**
- `relic_present_number.json`, `relic_present_null.json`, `relic_no_xf.json`, `relic_schema_version_v2.json`, `relic_schema_mismatch.json`, `relic_malformed.json`.
- `summary_disallowed_null.json` — uses `scattering/v1` with `sigma_si_proton_cm2: null`.
- `tampered_schema_root/relic.schema.json` — `$id` mutated to `/relic/v2`.

**`spectra/`:** (per §2 + critic N2)
- `near_threshold_10pct.json` — `mass_gap_fraction: 0.10001`.
- `safe_above_10pct.json` — `mass_gap_fraction: 0.09999`.
- `near_resonance_5pct.json` — `mass_gap_to_resonance_fraction: 0.0501`.
- `safe_above_5pct.json` — `mass_gap_to_resonance_fraction: 0.0499`.
- **`README.md`** (3 lines, lowercase) — names each field and its meaning per critic N2. Verbatim shape:
  > Synthetic spectrum fixtures for the heuristic-trigger oracle.
  > `mass_gap_fraction` — Δm / m_DM, the spectrum gap (Step 3 trigger at 10%).
  > `mass_gap_to_resonance_fraction` — |m_DM − m_resonance/2| / m_DM (Step 5b at 5%).

**Future `spectrum/v1` schema** is out-of-scope for WS-2 and flagged as such.

### 5.3 No real-tool runs

Boundary holds: no MadDM, no micrOMEGAs, no DRAKE, no `wolframscript`, no real `drake-install/scripts/install.sh`. Test 8 of `detect_drake` is the only edge that previously leaked toward real-tool; the synthesis pins it inside the `tmp_path/bin/install.sh` stub.

---

## 6. WS-2 / WS-3 boundary

**One-sentence rule:** WS-2 owns helper-direct fixture-based tests with synthetic JSON/bash stubs and zero real producer binaries; everything that requires a real producer binary or LLM behavior on a fixture is WS-3.

**Concretely WS-3 (NOT WS-2):**
- Real-tool integration of `install.sh detect` ↔ `wolframscript` (Wolfram activation flow).
- LLM behavior on the four `spectra/` fixtures (whether the agent fires the threshold per SKILL.md prose).
- MadDM real-output parsing parity vs WS-1 manifest entries (per WS-1 §6.4 carry-over).
- `compare_dm` end-to-end (LLM-only; not testable mechanically).

**Concretely WS-2 (NOT WS-3):**
- Each helper as a Python module (importlib-loaded) and as a CLI (subprocess).
- Drift injection on the manifest with synthetic mutated copies.
- Doc-vs-CLI parity (mechanical).
- Oracle arithmetic (test infra).

**No overlap, no gaps.** WS-2 ships the `spectra/` fixtures; WS-3 consumes them.

---

## 7. 10-item adjudication table

| # | Critic item | Decision | Rationale |
|---|---|---|---|
| 1 | Test count cuts | **42 (+1 conditional).** Collapse `check_prereqs` 12→9 via parametrize for paired blocker codes (cases 2/3, 4/5). Drop `extract_field` case 11 (default-schema-root, mirrors WS-4 gate). Make case 12 (nested-pointer pin) conditional on the verbatim forward-compat docstring. | Critic D1 numbers verified against synthesis spec; padding is at parametrize-collapsible pairs, not load-bearing rows. |
| 2 | Oracle script | **4 cases; verbatim SKILL.md sentence in each docstring; prose-wins tiebreaker; no equality-boundary case.** Header forbids skill-code import. | Critic D2 + N1; the equality-boundary decision lives in SKILL.md prose (LLM territory per the lens). |
| 3 | `activation_required` fake | **Env var (`HEPPH_DRAKE_DETECT_CMD`) + bash stub. Reject `monkeypatch`/`subprocess.run` mock with rationale.** Re-verify after WS-4 T3 lands. | Critic D3; env var is the helper's documented test interface, tests CLI surface end-to-end, and decouples from the helper's internal `subprocess`-vs-`shutil.which` choice. |
| 4 | Conftest names | **Canonical (`_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST`) in `tests/conftest.py`. WS-4 T8 imports via `from .conftest import …`.** No renaming dodge. | Critic D4; one source of truth, prevents WS-1/WS-2 drift forever. |
| 5 | Doc-vs-CLI parity | **3 mechanical assertions: bidirectional flag set-equality + path-drift; whole-fence-as-one-string parsing; `--help` captured once via session fixture.** No exit-code parity. | Critic D5 + N4; pins parsing rule, catches typo path drift, avoids 8× subprocess overhead. |
| 6 | Punted unknowns (3 of them) | **Document-of-decision posture in test docstrings. Bind floats to `pytest.approx(rel=1e-9)`.** | Critic D6; WS-2 asserting behavior would create a phantom dependency on WS-4. Float approx is a binding decision WS-2 owns. |
| 7 | Spectrum fixtures | **Ship 3-line `tests/fixtures/spectra/README.md` naming the fields. Flag `spectrum/v1` schema as future (out-of-scope).** | Critic N2; README is sufficient at WS-2 scale; schema is post-WS-3 work if needed. |
| 8 | Undocumented-field test | **`pytest.warns(UserWarning, match=r"DRIFT_PRESENT_BUT_UNDOCUMENTED")`.** | Critic N3; WS-1's existing `warnings.warn` is silently passing without an assertion; WS-2 adds the assertion. |
| 9 | `detect_drake` test 8 | **Stub `install.sh` itself via `tmp_path/bin/install.sh` + `monkeypatch.setenv("PATH", …)`.** Do NOT drop. | Critic N5; the no-real-tool-runs boundary holds; the test still validates the default-cmd code path. |
| 10 | `tmp_manifest` fixture | **Drop. Inline mutations in the 4 needing tests.** | Critic N6; fixture machinery overshoots at scale of 4 tests; less infrastructure, more readable. |

---

## 8. Coordination with WS-1 (merged) and WS-4 (in flight)

### 8.1 WS-1 (merged)

WS-1's `tests/test_router_contract.py` is on `main` with module-level `_HERE`/`_REPO_ROOT`/`_DEFAULT_MANIFEST` constants at lines 37–40. WS-2 does NOT modify this file. WS-2 ships the `tests/conftest.py` with the same canonical names. WS-1's tests continue to pass unchanged because module-level constants and conftest module-level constants don't collide (tests resolve their constants from `_HERE = pathlib.Path(__file__).parent`, which is module-local).

The retrofit (replace WS-1's lines 37–40 with `from .conftest import …`) is **WS-4 T8's task**, not WS-2's. WS-2 simply ensures the canonical names exist in conftest at the moment WS-4 T8 lands.

### 8.2 WS-4 (in flight)

WS-2 writes tests against the `ws4_synthesis.md` spec, not `ws4_plan_final.md` gate code (per proposer §8.1 — WS-2 doesn't mirror WS-4 gates). When a WS-4 helper diverges from the synthesis, WS-2's tests fail and WS-4 gets the feedback signal. Three coordination points:

1. **`detect_drake` short-circuit branch label** when `drake_path` is set — synthesis §1.2 silent. WS-2 test 7 documents whichever WS-4 lands.
2. **`check_prereqs --model nonexistent_in_config` exit code** — synthesis §1.1 silent. WS-2 test 6 documents whichever WS-4 lands.
3. **`extract_field` float rendering precision** — synthesis §1.3 silent. WS-2 uses `pytest.approx(rel=1e-9)` (binding WS-2 decision per critic D6).

If any of these three surfaces a behavior WS-4 has NOT decided AND WS-4 cannot adjudicate at plan-draft time, that is a **WS-4 cycle re-dispatch trigger**. WS-2 plan-drafter surfaces these three to the manager as gates.

### 8.3 WS-3 hand-off

WS-2 ships `tests/fixtures/spectra/{near_threshold_10pct,safe_above_10pct,near_resonance_5pct,safe_above_5pct}.json` + the README. WS-3 consumes these to drive the LLM playtest on the rewritten SKILL.md. WS-2 does not run the LLM.

---

## 9. Out-of-scope for WS-2 (explicit)

- **Real producer binaries.** No MadDM / micrOMEGAs / DRAKE / Wolfram / real `install.sh` runs.
- **LLM behavior testing.** WS-3 owns it.
- **Modifying the four helpers.** WS-4 T2/T3/T4/T5 own them.
- **Rewriting `tests/test_router_contract.py`.** WS-4 T8 owns it.
- **`compare_dm` testing.** Prose-only per WS-4 synthesis §2; not testable mechanically.
- **`read_maddm_output` / `read_drake_output` testing.** Prose-only per WS-4 synthesis §1.5.
- **CI / GitHub Actions.** No-GitHub constraint per the lens "Non-goals." Ship `tests/run_tests.sh` only.
- **Manifest authoring.** WS-1's manifest is consumed; WS-2 mutates copies in `tmp_path`.
- **Schema authoring.** WS-4 T1 owns `relic.schema.json` / `annihilation.schema.json`; WS-2 references them via the WS-4 deliverable path.
- **Top-level Makefile.** WS-2 ships `run_tests.sh`; if the WS-2 implementer finds a Makefile convention in-repo, mirror; otherwise leave at script.
- **`spectrum/v1` schema.** Flagged as future post-WS-3; WS-2 ships only the README.
- **`compare_dm_single_component` v1.1 helper.** Out of scope for the entire run per WS-4 synthesis §2.2.

---

## Closing routing-lens conformance check

Every test in this synthesis exercises model-agnostic mechanical behavior. The oracle is allowed because (a) it lives at `tests/oracle/`, (b) the header forbids skill-code import, (c) the SKILL.md prose remains the source of truth (tiebreaker rule). The doc-vs-CLI parity test catches drift between two contract-bound artifacts. The four `spectra/` fixtures ship as test data for WS-3 to drive the LLM against; WS-2 does not assert LLM behavior. The WS-2/WS-3 boundary is locked at the "real producer binary or LLM" line. No physics in any assertion; no model-class branch in any helper test. Lens-conformant.

The 10 adjudications are tractable as a single WS-2 plan with no further brainstorm cycle. The three WS-4 coordination points (§8.2 items 1–3) are the only WS-4 cycle re-dispatch triggers; everything else is independent.
