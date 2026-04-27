# WS-2 Proposal — Router Test Harness

**Proposer:** ws2-brainstorm-proposer
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md` (the design canon for the 4 helpers WS-2 tests); `plan/ws4_plan_final.md` (helper paths, CLI shapes, schema-dispatch rule, the 7-row exit-code grid for `extract_field`, the 4-state machine for `detect_drake`); WS-1's MERGED `tests/test_router_contract.py` (style reference); WS-1's MERGED `contracts/router_contract.json` (the manifest that `verify_router_field_contract` consumes); the existing `tests/fixtures/` tree (`maddm/MadDM_results_synthetic.txt`, `drake/stdout_drake_synthetic.txt`, `micromegas/stdout_synthetic.txt` + `summary_singletDM.json` symlinks).

This is a proposal, not an implementation. Scope is fixture-based unit-style tests for the 4 helpers WS-4 ships, plus a doc-vs-CLI parity invariant. Real-tool runs and LLM behavior are out of scope (WS-3 owns those).

---

## 1. Test inventory

For each of the 4 helpers, an explicit list of named test cases with imperative names. Numbers are implementer-targets, not floors.

### 1.1 `tests/test_check_prereqs.py` — ~12 cases

Per `ws4_synthesis.md` §1.1: blocker codes `MADDM_MISSING`, `MICROMEGAS_MISSING`, `DRAKE_PATH_UNSET`, `UFO_MISSING`, `SLHA_MISSING_HINT`. Exit codes 0 / 1 / 2.

1. `test_check_prereqs_all_present_returns_ok_exit_zero` — all three tool paths exist, model UFO exists ⇒ `status:"ok"`, exit 0.
2. `test_check_prereqs_maddm_missing_emits_blocker_exit_one` — `maddm_path` set to nonexistent ⇒ blocker code `MADDM_MISSING`, `fixit_skill:"/maddm-install"`, exit 1.
3. `test_check_prereqs_micromegas_missing_emits_blocker_exit_one` — same shape for micrOMEGAs.
4. `test_check_prereqs_drake_path_unset_emits_blocker_exit_one` — `drake_path` absent (key not present) ⇒ `DRAKE_PATH_UNSET`, exit 1.
5. `test_check_prereqs_drake_path_nonexistent_emits_blocker_exit_one` — `drake_path` set to a bogus path ⇒ blocker present (helper choice — the synthesis doesn't enumerate; assert blocker code starts with `DRAKE_`).
6. `test_check_prereqs_ufo_missing_emits_blocker_exit_one` — `models.<model>.ufo_path` nonexistent ⇒ `UFO_MISSING`, exit 1.
7. `test_check_prereqs_slha_missing_emits_hint_status_remains_ok` — model lacks `latest_slha`; helper surfaces `SLHA_MISSING_HINT` in `blockers[]` but `status:"ok"`, exit 0 (LLM keeps the call per the lens).
8. `test_check_prereqs_unknown_model_exit_two` — `--model nonexistent_in_config` ⇒ exit 2 (internal: model interpolation fails) OR exit 1 with a config-level blocker — assert against whatever WS-4 lands; pin the case so behavior is documented.
9. `test_check_prereqs_unparseable_manifest_exit_two` — manifest is not valid JSON ⇒ exit 2 with stderr `code:"PREREQ_HELPER_INTERNAL"`.
10. `test_check_prereqs_unreadable_config_exit_two` — `--config` points at a directory ⇒ exit 2.
11. `test_check_prereqs_checked_array_lists_every_dispatched_key` — happy path: assert `len(checked) >= len(manifest.config_keys)`; each entry has `key`, `exists`, `path`.
12. `test_check_prereqs_multiple_blockers_aggregated` — two prereqs missing simultaneously ⇒ both blockers present, exit 1, ordering deterministic (assert against a sorted-by-code expectation).

### 1.2 `tests/test_detect_drake.py` — ~8 cases

Per `ws4_synthesis.md` §1.2 + `ws4_plan_final.md` T3: 5 status branches (`configured` / `found` / `missing` / `activation_required` / `unparseable`); exit code is always 0; `router_action` switches downstream behavior; the `HEPPH_DRAKE_DETECT_CMD` env var injects a stub `install.sh detect` for testing.

1. `test_detect_drake_configured_emits_proceed` — stubbed detect returns `{"status":"configured","path":"/x","version":"1.0"}` ⇒ helper emits `branch:"branch1_unset"` or `"branch2_detect"` (whichever the impl picks; assert on `status:"configured"`, `router_action:"proceed"`), exit 0.
2. `test_detect_drake_found_emits_proceed` — stub returns `status:"found"` ⇒ `router_action:"proceed"`, exit 0.
3. `test_detect_drake_missing_emits_DRAKE_MISSING` — stub returns `status:"missing"` ⇒ `router_action:"emit_DRAKE_MISSING"`, exit 0.
4. `test_detect_drake_activation_required_emits_DRAKE_ACTIVATION_REQUIRED` — stub returns `status:"activation_required"` ⇒ `router_action:"emit_DRAKE_ACTIVATION_REQUIRED"`, exit 0. (See §4.1 for the fake — this is the hardest fixture.)
5. `test_detect_drake_unparseable_emits_DRAKE_UNAVAILABLE` — stub emits non-JSON ("not json at all") ⇒ helper emits `status:"unparseable"`, `router_action:"emit_DRAKE_UNAVAILABLE"`, `raw_detect_output` populated, exit 0.
6. `test_detect_drake_unknown_status_drift_to_unparseable` — stub emits valid JSON with `status:"frobbed"` (not in manifest's enum literals) ⇒ helper detects manifest-drift on the literal set and emits `status:"unparseable"`, exit 0.
7. `test_detect_drake_drake_path_set_takes_branch1_unset_short_circuit` — config has `drake_path:"/some/dir"` set ⇒ helper does NOT invoke the detect stub at all (assert via a stub that touches a sentinel file; assert sentinel absent), emits `branch:"branch1_unset"` or whichever branch synthesis defines as the "already configured" path. (Edge case the synthesis names but does not fully spec — pin behavior.)
8. `test_detect_drake_default_command_invokes_install_sh` — `HEPPH_DRAKE_DETECT_CMD` unset ⇒ helper invokes the real `drake-install/scripts/install.sh detect` path, but with a fake `$PATH` so the binary is unavailable; assert helper falls back to `status:"unparseable"` or surfaces a documented error (whichever the impl chooses; pin the contract).

### 1.3 `tests/test_extract_field.py` — ~12 cases

Per `ws4_synthesis.md` §1.3 (LOCKED 7-row exit-code grid) + `ws4_plan_final.md` T4 (8th critic-added row).

1. `test_extract_field_present_number_returns_zero` — valid `relic_singletDM_synthetic.json`, `--key omega_h2 --schema-version relic/v1` ⇒ stdout JSON with `value:<float>`, exit 0.
2. `test_extract_field_present_null_returns_zero` — hand-rolled relic JSON with `omega_h2: null` ⇒ stdout `value: null`, exit 0. Distinguishes from absent.
3. `test_extract_field_key_absent_exits_with_token` — valid relic JSON with no `xf` key, `--key xf` ⇒ exit 1, stderr `code:"KEY_ABSENT"`.
4. `test_extract_field_schema_version_drift_exits_with_token` — JSON's `schema_version:"relic/v2"` ⇒ exit 1, stderr `code:"VERSION_DRIFT"`.
5. `test_extract_field_schema_id_drift_exits_with_token` — `--schema-root` points at a tampered file with `$id` ending `/relic/v2` ⇒ exit 1, stderr `code:"VERSION_DRIFT"`. Tests the §1.3 self-check ordering (must fire BEFORE jsonschema validation).
6. `test_extract_field_schema_mismatch_exits_with_token` — `m_dm_gev:"oops"` (string, not number) ⇒ exit 1, stderr `code:"SCHEMA_MISMATCH"`.
7. `test_extract_field_unreadable_file_exits_two` — nonexistent JSON path ⇒ exit 2, stderr `code:"EXTRACT_FIELD_INTERNAL"`.
8. `test_extract_field_malformed_json_exits_two` — JSON file containing `{not json` ⇒ exit 2, stderr `code:"EXTRACT_FIELD_INTERNAL"`.
9. `test_extract_field_disallowed_null_on_non_nullable_key_schema_mismatch` — critic §2 T4 row: `summary.json` with `sigma_si_proton_cm2: null` against `scattering/v1` (no `oneOf [null, ...]` for that key) ⇒ exit 1, `SCHEMA_MISMATCH`.
10. `test_extract_field_emits_source_file_in_stdout` — happy path: stdout JSON includes `source_file: <abs path>`, `key`, `schema_version`. Pins the output contract.
11. `test_extract_field_default_schema_root_resolves` — omit `--schema-root`; helper resolves the default per §1.3 (`plugins/shared/schemas/`) ⇒ exit 0. Tests the path-resolution branch.
12. `test_extract_field_does_not_support_nested_pointer` — synthesis §1.3 says nested access (`channel_fractions.bb`) is OUT OF SCOPE for v1. Pass `--key channel_fractions.bb` ⇒ helper treats the literal string as a top-level key ⇒ `KEY_ABSENT`, exit 1. Pins the "no nested pointer in v1" contract so a future `--json-pointer` flag doesn't silently break this.

**Stdout-regex mode.** Per the synthesis (§1.5 final paragraph + §1.3 "Mode" line), `extract_field.py` is **JSON-only in v1**. There is no stdout-regex mode in the helper. So this proposer drops the "stdout-regex mode" sub-bullet from the task statement. The stdout-regex extraction stays in the LLM (per the lens) until W4-A/W4-B's `relic.json` and `annihilation.json` close it out.

### 1.4 `tests/test_verify_router_field_contract.py` — ~10 cases

Per `ws4_synthesis.md` §1.4 + `ws4_plan_final.md` T5. The drift-code ladder: `DRIFT_PRODUCER_DOC_GAP`, `DRIFT_PRODUCER_RENAMED`, `DRIFT_ROUTER_INVENTED_NAME`, `DRIFT_DOCUMENTED_BUT_ABSENT`, `DRIFT_PRESENT_BUT_UNDOCUMENTED`, `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY`. WS-1 already covers the manifest-vs-fixture surface in `test_router_contract.py`; WS-2 here covers the **helper itself** (T8 retrofits the WS-1 test to call the helper, but that's a WS-4 deliverable, not WS-2).

1. `test_verify_router_field_contract_baseline_manifest_passes` — shipped manifest + shipped fixtures ⇒ helper exit 0; `VerifyResult.fail == []`; `len(VerifyResult.xfail) == 4` (per WS-1's pinned count).
2. `test_verify_router_field_contract_summary_line_format` — stdout final line matches `^SUMMARY \d+/\d+/\d+$`. Pins the line shape so WS-3's grep doesn't break.
3. `test_verify_router_field_contract_renamed_field_emits_drift_producer_renamed` — mutate manifest `output_fields[0].field_name` to a name that doesn't appear in the producer SKILL.md ⇒ exit 1, `FAIL` line containing `DRIFT_PRODUCER_RENAMED` or `DRIFT_DOCUMENTED_BUT_ABSENT` (assert one of the two — synthesis §1.4 enumerates both as candidates for this case).
4. `test_verify_router_field_contract_invented_name_emits_drift_router_invented` — temporarily replace router SKILL.md text in a tmp dir so a manifest field name is NOT in the rendered router prose ⇒ exit 1, `DRIFT_ROUTER_INVENTED_NAME`.
5. `test_verify_router_field_contract_documented_but_absent_emits_drift` — point a manifest entry's `fixture` at an empty tmp file ⇒ `DRIFT_DOCUMENTED_BUT_ABSENT` for that row.
6. `test_verify_router_field_contract_undocumented_present_emits_drift` — append a `frobnicator = 0.5` line to a copy of `MadDM_results_synthetic.txt` ⇒ `DRIFT_PRESENT_BUT_UNDOCUMENTED` (warning, not failure, per WS-1's softpass policy; assert via the `xfail`/warnings channel).
7. `test_verify_router_field_contract_internal_inconsistency_emits_drift` — for the `pending_producer_doc_fix` row, ensure `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY` appears in the xfail reason.
8. `test_verify_router_field_contract_unparseable_manifest_exits_two` — `{not json` ⇒ exit 2.
9. `test_verify_router_field_contract_importable_dataclass_surface` — `from <helper> import verify_router_field_contract, VerifyResult`; assert `VerifyResult` is a dataclass with `.ok`, `.xfail`, `.fail` lists. Pins the surface T8 retrofit imports.
10. `test_verify_router_field_contract_negative_control_workflow` — copy of WS-1 plan T3 acceptance gate #4: mutate manifest, run helper, assert non-zero exit, then restore manifest, assert zero exit. The negative-control invariant survives the WS-4 extraction.

**Note on WS-1 retrofit:** WS-4 task T8 rewrites `tests/test_router_contract.py` to import from `verify_router_field_contract`. WS-2 does NOT re-implement that test (it's WS-4's). WS-2 owns only the **direct unit tests** of the helper (this §1.4 list).

---

## 2. Trigger-boundary tests

The lens is unambiguous: the 10% (Step 3) and 5% (Step 5) thresholds are heuristic-with-default + expert-overridable. They live in the LLM. **There is no helper to test for the trigger arithmetic itself.**

But the user's question is correct: a fixture spectrum at `10.001%` should fire and `9.999%` should not. WS-2 cannot test the LLM's behavior. So we have three options:

**Option A — Omit.** Argue this category falls entirely on WS-3's integration playtest. WS-3 produces a Profumo Fig. 8 spectrum and exercises the rewritten SKILL.md prose; if the LLM fails to fire on a near-resonance spectrum, that's a SKILL.md-prose bug that surfaces there.

**Option B — Thin "oracle" Python script.** Write a non-helper, NOT-shipped-in-skill arithmetic script (`tests/oracle_threshold.py`) that mirrors the LLM's trigger arithmetic verbatim and is testable. The script is documentation-by-code: it shows what the LLM *should* compute. Tests assert: at 10.001% it fires; at 9.999% it does not; at exactly 10.0% the contract is open and a default-fire is acceptable.

**Option C — Synthesize the spectrum into a synthetic fixture and add a WS-3 hand-off note.** Ship a fixture file `tests/fixtures/spectra/near_threshold_10pct.json` with a documented `gap_fraction` of 0.10001 and a sibling `safe_above_10pct.json` at 0.09999. WS-2 does not test these; they are WS-3's playtest material.

**This proposer's recommendation: Option B + Option C combined.**

Reasoning. Option A leaves a gap: the SKILL.md prose may drift the threshold during the rewrite (e.g. say "10%" in one place and "10 percent" with a different rounding in another), and there is no mechanical guard. Option B provides a *contract document* — the oracle script encodes "this is what '10% trigger' means in arithmetic" — and gives WS-3 fixtures to drive the LLM against. The oracle script is NOT shipped in the skill; it lives at `tests/oracle/threshold_arithmetic.py` with a header comment that says: "This script is a test-only reference for what the SKILL.md threshold prose means. Do NOT import from skill code; the LLM does the arithmetic in prose."

Tests for the oracle:

- `test_oracle_threshold_above_fires` — `gap_fraction=0.10001 ⇒ trigger=True`.
- `test_oracle_threshold_below_does_not_fire` — `gap_fraction=0.09999 ⇒ trigger=False`.
- `test_oracle_threshold_exactly_at_default_fires` — pin the default behavior at 0.10 exactly (open contract; argue ≥ vs >, document the choice).
- `test_oracle_resonance_5pct_above_fires` — `mass_gap_to_resonance / m_DM = 0.0501 ⇒ trigger=True`.
- `test_oracle_resonance_5pct_below_does_not_fire` — `0.0499 ⇒ trigger=False`.

Plus 2 synthetic spectrum fixtures shipped to `tests/fixtures/spectra/` for WS-3 to consume. WS-3 will run the rewritten SKILL.md prose (LLM-driven) against them and the WS-3 playtest report logs whether the LLM fires correctly. **WS-2 does not run the LLM; WS-2 ships the oracle and the fixtures.**

This is the cleanest split: deterministic arithmetic captured in code (and tested mechanically); LLM behavior tested at WS-3.

---

## 3. Test framework, layout, and discovery

### 3.1 Where new tests live

**Recommendation: same directory as WS-1's tests.** `plugins/constraints/skills/dark-matter-constraints/tests/`. Reasons:

- Single discovery root for `pytest`. Running `pytest plugins/constraints/skills/dark-matter-constraints/tests/` runs everything.
- WS-1 already sites `tests/__init__.py` there; reuse.
- A sibling `tests_helpers/` would create a second discovery root and bifurcate the conftest surface. No payoff.

**Layout:**

```
plugins/constraints/skills/dark-matter-constraints/tests/
├── __init__.py                                  (WS-1, exists)
├── conftest.py                                  (NEW — WS-2)
├── test_router_contract.py                      (WS-1, retrofitted by WS-4 T8)
├── test_check_prereqs.py                        (NEW — WS-2)
├── test_detect_drake.py                         (NEW — WS-2)
├── test_extract_field.py                        (NEW — WS-2)
├── test_verify_router_field_contract.py         (NEW — WS-2)
├── test_doc_vs_cli_parity.py                    (NEW — WS-2; §6)
├── oracle/
│   └── threshold_arithmetic.py                  (NEW — WS-2; §2)
├── test_oracle_thresholds.py                    (NEW — WS-2; §2)
└── fixtures/
    ├── maddm/                                   (WS-1, exists)
    ├── micromegas/                              (WS-1, symlinked)
    ├── drake/                                   (WS-1, exists)
    ├── helpers/                                 (NEW — WS-2; see §4)
    │   ├── check_prereqs/                       (synthetic configs + manifests)
    │   ├── detect_drake/                        (stub install.sh scripts emitting each branch)
    │   └── extract_field/                       (hand-rolled JSONs covering the exit-code grid)
    └── spectra/                                  (NEW — WS-2; §2)
        ├── near_threshold_10pct.json
        ├── safe_above_10pct.json
        ├── near_resonance_5pct.json
        └── safe_above_5pct.json
```

### 3.2 Naming convention

`test_<helper_basename>.py`. Mirror the WS-1 file's per-test imperative names.

### 3.3 Conftest

Yes — one `conftest.py` consolidating:

- `_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST` constants (lifted from WS-1's `test_router_contract.py`; WS-4 T8 retrofit replaces those constants with imports from conftest, reducing churn).
- A `helper_loader(helper_name) -> module` fixture that wraps `importlib.util.spec_from_file_location` for each of the 4 helpers. This is the canonical "load a helper as a Python module" boilerplate; without it every test file repeats 5 lines of importlib code.
- A `tmp_manifest(monkeypatch, request)` fixture that copies the shipped manifest to a tmp dir, applies a `jq`-style mutation passed via parametrize, and returns the path. Used by `test_verify_router_field_contract.py` for drift-injection tests.
- A `helper_subprocess(helper_name, args, env={}) -> CompletedProcess` fixture for CLI-mode tests (running the helper via `subprocess.run`).

### 3.4 Discovery

Standard `pytest` + `conftest.py`. No special markers needed beyond `@pytest.mark.xfail` (already used by WS-1).

---

## 4. Fixture strategy

### 4.1 Reuse from WS-1

Direct reuse:
- `tests/fixtures/maddm/MadDM_results_synthetic.txt` — re-used by `test_verify_router_field_contract.py` in baseline tests.
- `tests/fixtures/micromegas/summary_singletDM.json` (symlink) — re-used by `test_extract_field.py` row 1, row 9.
- `tests/fixtures/drake/stdout_drake_synthetic.txt` — re-used by drift-injection tests.

### 4.2 New fixtures WS-2 must ship

Under `tests/fixtures/helpers/`:

**`check_prereqs/`:**
- `manifest_minimal.json` — manifest with the 3 `config_keys` entries + empty `output_fields` and `status_enums`.
- `manifest_unparseable.json` — `{not json`.
- `config_all_present.json` — config interpolating to all-existent paths (paths point at the test harness's tmp dir or the fixture dir itself).
- `config_maddm_missing.json` — `maddm_path:"/nonexistent/maddm"`.
- `config_micromegas_missing.json` — same shape for micrOMEGAs.
- `config_drake_unset.json` — drake_path key absent.
- `config_drake_nonexistent.json` — drake_path set to a bogus path.
- `config_no_ufo.json` — `models.dummy.ufo_path` nonexistent.
- `config_mssm_like.json` — model named `mssm_like` to drive the SLHA-hint branch.

**`detect_drake/`:**
- `stub_configured.sh`, `stub_found.sh`, `stub_missing.sh`, `stub_activation_required.sh`, `stub_unparseable.sh`, `stub_unknown_status.sh` — bash one-liners emitting the canned JSON outputs (per WS-4 plan T3 acceptance gates).
- `stub_sentinel.sh` — touches a sentinel file; used by test 7 (drake_path-set short-circuit) to assert the stub was NOT invoked.
- `stub_path_unavailable.sh` — exits non-zero with no output; used by test 8.

**`extract_field/`:**
- `relic_present_number.json` — passes schema, omega_h2 is a positive number.
- `relic_present_null.json` — omega_h2 explicitly `null` (schema's `oneOf` allows).
- `relic_no_xf.json` — valid but `xf` key absent.
- `relic_schema_version_v2.json` — `schema_version:"relic/v2"`.
- `relic_schema_mismatch.json` — `m_dm_gev: "oops"`.
- `relic_malformed.json` — literally `{not json`.
- `relic_summary_disallowed_null.json` — uses `scattering/v1` schema with `sigma_si_proton_cm2: null` (critic row 8).
- `tampered_schema_root/relic.schema.json` — copy of `relic.schema.json` with `$id` mutated to `/relic/v2`. Used by row 5.
- `relic_with_extra_undocumented_key.json` — for use in conftest tests of `additionalProperties: false`.

**`spectra/`:** (per §2)
- `near_threshold_10pct.json` — synthetic spectrum with `mass_gap_fraction: 0.10001`.
- `safe_above_10pct.json` — `0.09999`.
- `near_resonance_5pct.json` — `mass_gap_to_resonance_fraction: 0.0501`.
- `safe_above_5pct.json` — `0.0499`.

These spectrum fixtures are minimal-shaped — they are NOT bound to a real MadDM/micrOMEGAs format. They are oracle-input JSONs documenting the threshold contract. WS-3 may also synthesize real spectrum fixtures from its Profumo replay; those are WS-3 fixtures, not WS-2's.

### 4.3 No real-tool runs

The lens (and synthesis §8) is explicit: WS-2 runs no MadDM, micrOMEGAs, DRAKE. All fixtures are synthetic, hand-crafted, or symlinked from WS-1's set. WS-3 covers real-tool integration.

---

## 5. CLI parity test

The drift surface this catches: SKILL.md says `python …/scripts/check_prereqs.py --config X --model Y` but the helper's `--help` only shows `--cfg` and `--model`. WS-2 must catch that.

### 5.1 Approach — structured, not pure-grep

A pure grep would be brittle: SKILL.md formatting (code fences, line breaks, `\` continuations) varies. Instead:

**`tests/test_doc_vs_cli_parity.py`:**

```python
import re, subprocess, pathlib, pytest

HELPERS = [
    ("check_prereqs.py",                    {"--config", "--model", "--manifest"}),
    ("detect_drake.py",                     {"--config", "--manifest"}),
    ("extract_field.py",                    {"--json", "--key", "--schema-version", "--schema-root"}),
    ("verify_router_field_contract.py",     {"--manifest", "--fixtures-root"}),
]

# For each helper, assert that:
#   1. helper --help lists every flag in the expected set (and no more, modulo --help/-h).
#   2. SKILL.md prose mentions the helper at least once with a direct-path invocation
#      including at least the required-flag subset.
```

Specifically:

1. **Run `--help`.** `subprocess.run([sys.executable, str(helper_path), "--help"], capture_output=True)`. Parse the output via a regex lifting argparse's `--<flag>` tokens.
2. **Compare to expected set.** Assert set-equality (modulo `--help`/`-h`). This catches helper-side drift (a flag renamed or removed).
3. **Read SKILL.md.** Extract every line matching `python .*/scripts/<helper_basename>` (or a multi-line variant; allow trailing `\` continuation).
4. **For each invocation block, parse out the `--<flag>` tokens.** Assert the helper's required flags are all mentioned at least once (per helper) in SKILL.md.

This is structured (`set` operations), not pure-grep, so we can give clean failure messages: `"check_prereqs.py --help has flags {--cfg,--model,--manifest} but SKILL.md uses --config — drift"`.

### 5.2 Exit codes parity

Synthesis §1 pins exit-code semantics per helper. SKILL.md prose mentions exit codes in only some places (where relevant to error handling). The doc-vs-CLI parity test does NOT enforce exit-code parity in prose — that's documented at the helper level (`--help` may print exit codes; if so, parity test asserts the documented codes match the synthesis grid). If `--help` doesn't enumerate exit codes (most argparse helpers don't by default), the test skips that check with a documented reason.

---

## 6. Doc-vs-CLI grep test

Per synthesis §6: WS-2 ships a "doc-vs-CLI grep test." Specification:

### 6.1 Which docs

Two:
- `plugins/constraints/skills/dark-matter-constraints/SKILL.md` — primary. Every helper invocation mentioned in prose must match the helper's CLI surface.
- `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` — secondary. The AUDIT.md is permanent provenance from WS-1; it may reference helpers in the "what was deferred to WS-4" section. If it does, those references must also parse cleanly.

### 6.2 Which CLI surfaces

All four helpers' `--help` output. Per-helper running of `python <path>/scripts/<helper>.py --help`.

### 6.3 What the test asserts

Two directions:

**Direction A (helper → doc): "every required flag in `--help` appears in SKILL.md."** If the helper requires `--config`, `--model`, `--manifest`, then SKILL.md must mention all three, in at least one invocation block, for that helper. This catches the case where SKILL.md prose stale-references an old API.

**Direction B (doc → helper): "every flag SKILL.md mentions in an invocation block is a real flag."** If SKILL.md says `python .../scripts/extract_field.py --json X --key Y --schema-version Z --output Q`, then `--output` must be in the helper's `--help`. Otherwise SKILL.md is teaching the LLM to call a flag that doesn't exist — the worst kind of drift because the LLM will hit it at runtime.

Both directions ship as named tests:
- `test_doc_required_flags_present_in_help` (A)
- `test_doc_invocation_flags_exist_in_help` (B)

This proposer prefers BOTH directions over the converse-or-converse choice in the task statement. The two checks catch different drift; together they pin the contract bidirectionally.

---

## 7. CI integration

### 7.1 Constraints

- User has a no-GitHub constraint per the lens "Non-goals." → No GitHub Actions YAML.
- Repo doesn't have an existing top-level Makefile (verify before authoring; if absent, don't introduce a new top-level discipline for a single skill's tests).

### 7.2 Recommendation: a `tests/run_tests.sh` script + a per-skill Makefile target if the convention exists

Minimum viable:
- **`plugins/constraints/skills/dark-matter-constraints/tests/run_tests.sh`** — a one-liner that does `cd $(dirname "$0")/.. && python -m pytest tests/ -v "$@"`. Documented in the rewritten SKILL.md "How to test the router" section (one paragraph).

Optional additions (gated on existing repo conventions; check before authoring):
- If a top-level `Makefile` exists, add `test-dark-matter-constraints:` target that calls the shell script.
- If other skills have per-skill `Makefile`s (this proposer hasn't checked; verify in WS-2 implementation), mirror that convention.

Argument against doing more: the test surface is small (4 helpers + ~50 cases), and `pytest tests/` is already the obvious runner. Over-engineering CI for a 50-test suite is unjustified.

**Final decision:** ship `run_tests.sh`. If the WS-2 implementer finds a Makefile convention in-repo, add a target; otherwise leave at script. Do NOT add GitHub Actions.

---

## 8. Risks + scope

### 8.1 Helper-API drift between WS-4 cycles

Risk. WS-4's plan envelopes 5 cycles (6 ceiling). T2/T3/T4/T5 are cycle-1; T7 is cycles 2–3; T8 is cycle 4. WS-2 must not block on T7/T8 finalizing — but the helper APIs (T2/T3/T4/T5) are cycle-1 and locked by the synthesis. So:

- **Mitigation:** WS-2 writes tests against the **synthesis spec** (`ws4_synthesis.md` §1.1–1.4 + plan §3 acceptance gates). If a WS-4 helper diverges from the synthesis (e.g. T4's exit-code grid changes), WS-2's tests fail and WS-4 gets a feedback signal — that's correct behavior, not a WS-2 bug.
- **Mitigation:** WS-2 does NOT mirror the WS-4 plan's gate code. Tests are independent: they exercise the helper as a library + as a CLI, with synthetic fixtures, and assert observed behavior matches the spec. No copy-paste from WS-4 plan gates.

### 8.2 WS-3's playtest may surface a helper bug

If WS-3 runs the rewritten SKILL.md against Profumo Fig. 8 and a helper misbehaves, WS-2's fixtures may need updating (e.g. a real `summary.json` shape WS-1 didn't anticipate). **Posture:** WS-2 ships the v1 test surface; WS-3 may file follow-up fixture additions. WS-2 does not block on WS-3.

### 8.3 The hardest fixture: `activation_required` for `detect_drake`

Wolfram Engine activation behavior is real. The smoke test in `drake-install/scripts/install.sh` returns `status:"activation_required"` only when a real `wolframscript` invocation hits the activation prompt. We cannot reproduce that in CI, by design.

**Fake strategy (clean):**

The helper consumes `install.sh detect`'s **JSON stdout**. The helper does NOT itself talk to Wolfram. So the fake is at the JSON-stdout boundary, NOT at the Wolfram boundary.

`HEPPH_DRAKE_DETECT_CMD` (per `ws4_synthesis.md` §1.2) is the env var that overrides the default `install.sh detect` invocation. WS-2's stub for `activation_required`:

```bash
#!/bin/bash
# tests/fixtures/helpers/detect_drake/stub_activation_required.sh
cat <<'END'
{"status":"activation_required","path":"/fake/wolfram/path"}
END
```

The test sets `HEPPH_DRAKE_DETECT_CMD=$PWD/stub_activation_required.sh`, runs the helper, asserts `router_action:"emit_DRAKE_ACTIVATION_REQUIRED"`. **No Wolfram, no activation flow, no real `install.sh`.**

This is clean because it tests exactly what the helper's contract says: "I consume the JSON `install.sh detect` emits and dispatch on `status`." The end-to-end integration of `install.sh` ↔ `wolframscript` is WS-4 T8's territory (the bash-test of `cmd_detect` itself); WS-2 trusts that test and stubs at the boundary above.

### 8.4 WS-1's `test_router_contract.py` retrofit (WS-4 T8) overlaps WS-2

WS-4 T8 rewrites WS-1's test to import from `verify_router_field_contract.py`. WS-2 also tests that helper directly. These don't conflict — the WS-1 test exercises the helper's behavior on the real shipped manifest (with the 4 xfails); WS-2's tests exercise the helper on synthetic mutated manifests (drift-injection). Both are needed.

**Ordering:** WS-2 should NOT touch `test_router_contract.py`. If WS-4 T8 hasn't landed when WS-2 starts implementation, WS-2 still writes `test_verify_router_field_contract.py` against the helper module path (via `importlib.util.spec_from_file_location`) and treats the helper's module as the source of truth.

### 8.5 Conftest collisions with WS-1's test

WS-1's `test_router_contract.py` defines `_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST` as module-level constants (not in a conftest). WS-2's conftest will define the same names as fixtures or constants. To avoid colliding on rename:

- WS-2's conftest names them `_TESTS_DIR`, `_REPO`, `_MANIFEST_PATH` (different prefixes).
- The WS-4 T8 retrofit can use either set; not WS-2's problem to coordinate.

### 8.6 What WS-2 needs from WS-4 that the synthesis doesn't yet specify

Three items the WS-2 implementer should pin during the WS-2 plan-draft phase (or surface as a blocker if WS-4's plan-final doesn't resolve them):

1. **`detect_drake` short-circuit semantics when `drake_path` is set.** Synthesis §1.2 says `branch:"branch1_unset"|"branch2_detect"`. If `drake_path` is set, does the helper still call detect, or short-circuit? Test 7 in §1.2 pins this — WS-2 needs WS-4 to confirm one branch.
2. **`check_prereqs` model-not-in-config behavior.** Synthesis §1.1 doesn't say what happens if `--model nonexistent_in_config` is passed. Exit 2 (internal — couldn't resolve model)? Or exit 1 (config-level blocker)? WS-2 case 8 documents whichever WS-4 picks; needs WS-4 to confirm.
3. **`extract_field` value rendering for very large/very small floats.** A relic-density value of 1.2e-38 in JSON: does the helper round-trip the float exactly via `json.dumps(value)`, or use a fixed precision? Tests for `extract_field` will assert exact equality on the round-tripped value; if WS-4 picks fixed precision, WS-2 must adapt.

These are open at the synthesis level. WS-2 plan-draft surfaces them; WS-2 implementation pins behavior to whatever WS-4 ships and writes the test as a documentation-of-decision.

### 8.7 Out-of-scope confirmations

WS-2 does NOT:
- Modify any of the 4 helper scripts (WS-4 T2/T3/T4/T5 own them).
- Re-implement WS-1's `test_router_contract.py` body (WS-4 T8 retrofit owns; WS-2 ships the **direct unit tests** for the helper at §1.4).
- Run real MadDM / micrOMEGAs / DRAKE (WS-3).
- Test the LLM (untestable; WS-3 integration playtest).
- Touch the manifest, schemas, or contracts (WS-1 / WS-4 T1 own).

---

## 9. Closing routing-lens conformance check

WS-2 tests are mechanically verifiable behavioral assertions about model-agnostic helpers. Each helper (per the lens) is provably model-agnostic; WS-2's tests reinforce that by covering every documented exit code with synthetic fixtures that don't presume any model class. The trigger-boundary tests (§2) are split clean: the **arithmetic** is in the oracle (testable); the **judgment of when to trigger** stays with the LLM (untestable, WS-3 plays it). The doc-vs-CLI parity test (§5/§6) catches the SKILL.md-vs-CLI drift surface the synthesis explicitly calls out as a WS-2 deliverable.

This proposal is consistent with: the lens hard constraint on model-agnosticism; synthesis §7.2's WS-2 import boundary (`importlib.util.spec_from_file_location`); synthesis §1's helper inventory; the plan §6.2's hand-off shape; and WS-1's test-file conventions in `tests/test_router_contract.py`.
