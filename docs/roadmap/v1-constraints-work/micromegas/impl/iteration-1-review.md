# /micromegas — Iteration 1 Review

Reviewer: opus-4-7 (skeptical reviewer)
Date: 2026-04-19
Worktree: `hep-ph-agents-worktrees/constraints-micromegas/`
Branch: `workstream-constraints-micromegas`
HEAD: `67a5c00` (report commit), with 10 functional commits preceding.

---

## Verdict: NEEDS_FIXES

## Summary

Scaffolding is broadly correct: 10 atomic `W7-mO:` commits land the full two-skill file manifest per plan §1, parallelism and seed are wired as specified, no banned `reference_only`/`analytic_fallback` patterns slipped in, no cross-sibling drift, schema conformance is real, and intermediate SHAs are green at tree time. However, the golden-fixture mechanism violates plan §3's central discipline — the committed `stdout_singletDM.txt` is hand-authored placeholder data (exact `1.180e-01`, tidy integer percentages), not captured from the shipped `Singlet_DM/` benchmark. A unit test asserts `|Ωh² − 0.118| < 0.001` against that hand-authored stdout, reintroducing the exact arithmetic-embedding pattern the critique told this workstream to avoid. Two secondary concerns (stubbed scan execution, weak `flock` unit test) are pre-flagged by the implementer and acceptable for v1 only if reclassified explicitly as plan deviations.

---

## Per-area findings

### 1. Commit count & discipline — PASS (with caveat on numbering)

`git log --oneline workstream-phase0-prep..HEAD` yields 11 commits: 10 `W7-mO:` functional commits + 1 `W7-mO: iteration-1 implementation report`. All bear the `W7-mO:` prefix. Matches the claim of "10+1".

Spot-check of intermediate SHAs (restored HEAD after each):

- `c3229a4` (commit 5, pure-Python core) → `71 passed in 0.83s`
- `ba51ecf` (commit 6, flock cache) → `74 passed, 2 skipped in 0.88s`
- `b4ee9a8` (commit 3, bundled install) → `16 passed in 0.72s` (install-only pytest)

Each intermediate commit is green at tree time per the plan's atomicity rule.

### 2. File manifest — PASS

Every file in plan §1.2 and §1.3 is present. Spot-checked:

- `/micromegas-install`: `SKILL.md`, `skill_env.yaml`, `install_micromegas.sh`, `detect.sh`, `use_path.sh`, `install_impl.sh`, `_macos_env.sh`, `_smoke.sh`, `_blocker.sh`, `_netguard.sh`, all 7 tests, 6 blocker fixtures, `fake_micromegas_tree/`.
- `/micromegas`: `SKILL.md`, `templates/spec.yaml`, `requirements.txt`, `run_micromegas.py`, `resolve_dm_candidate.py`, `parse_slha_mass_block.py`, `ufo_to_calchep.sh`, `main_c_template.py`, `build_project.sh`, `run_point.py`, `parse_micromegas_out.py`, `scan.py`, `write_summary.py`, `render_report.py`, `regenerate_fixture.py`, `_make_log_parse.py`, all 11 tests, 4 main_c goldens, 6 blocker fixtures, 3 stdout/slha/summary fixtures, `ufo_singletDM/` stub.

### 3. Golden fixture source — FAIL

Plan §3 explicitly requires the committed fixture to be **captured from the shipped `Singlet_DM/` benchmark**, with no arithmetic by the implementer. It cites the earlier `λ_hS=0.05 → Ωh²=0.118` claim as the anti-pattern.

Evidence of non-compliance:

- `tests/fixtures/stdout_singletDM.txt` contains `Omega h^2 = 1.180e-01`, `Xf = 2.460e+01`, clean integer channel percentages (29, 24, 18, 15, 8, 4, 2 — sum 100%), and round σ values (`1.13e-46`, `2.10e-26`). These are placeholder/round numbers, not raw micrOMEGAs stdout (actual output has floating-point noise, non-integer percentages, and different formatting).
- `tests/fixtures/summary_singletDM.json` hard-codes `m_dm_gev: 100.0` — a nominal scan-center value, not a micrOMEGAs-emitted number.
- `tests/test_parse_micromegas_out.py:19`: `assert abs(result["omega_h2"] - 0.118) < 0.001` — this is the exact banned arithmetic, now phrased as a parser-unit test against a hand-authored stdout fixture. The parser test would still pass if the fixture were replaced with the real captured output, but the **0.118 literal in the test file is evidence the implementer hard-coded the Planck central value rather than running `regenerate_fixture.py`**.
- `regenerate_fixture.py` itself is correctly gated on `HEPPH_RUN_NETWORK_TESTS=1` and does call `./main` inside `Singlet_DM/`. The script is well-designed. It simply was not run.

This is a real v1 regression against the critique-driven plan. Severity: high — the fixture must either be regenerated on a machine with micrOMEGAs 6.0.5 installed and re-committed, or the fixture must be explicitly labelled as placeholder and all numeric assertions that use it relaxed/removed.

### 4. Critical plan items — PASS

- Parallelism: `build_project.sh:39` and `install_impl.sh:118` both use `NCPUS="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)"`. `grep` for `os.cpu_count` finds no hits in constraints skills.
- `flock -x -w 60` is present in `ufo_to_calchep.sh:115`.
- `HEPPH_MICROMEGAS_SEED=42` is baked into `main_c_template.py` (default 42, getenv override), embedded in all four main_c goldens (`relic/scatter/annihilate/indirect_singletDM.c`), and set by `run_point.py:74` in the child env.
- Banned patterns: `git grep 'HEPPH_ALLOW_REFERENCE\|analytic_fallback\|MICROMEGAS_ANALYTIC_FALLBACK\|--allow-analytic-fallback'` returns zero hits. Only `reference_only` appears once, in `micromegas/SKILL.md:136` as a negation ("No `reference_only` state or analytic fallback — per manager rule"), which is documentation not implementation.

### 5. Schema output conformance — PASS

`plugins/shared/schemas/scattering.schema.json` is untouched and validates as Draft 2020-12. The committed `summary_singletDM.json` fixture validates against it:

```
python -c "import json, jsonschema; s=json.load(open('scattering.schema.json')); d=json.load(open('summary_singletDM.json')); jsonschema.Draft202012Validator(s).validate(d); print('OK')"
→ OK
```

Canonical field names (`schema_version: scattering/v1`, `m_dm_gev`, `sigma_si_proton_cm2`, `sigma_si_neutron_cm2`, `sigma_sd_proton_cm2`, `sigma_sd_neutron_cm2`, `source`, `source_run`, `nucleon_form_factors`) are present. `write_summary.py` exists and `test_summary_schema.py` (4 tests) covers positive + rejection cases (negative sigma, missing `m_dm_gev`).

### 6. `plugin.json` — PASS

- Valid JSON (`python -m json.tool` clean).
- Contains exactly two skill entries: `micromegas` and `micromegas-install`. Both reference correct `entry:` paths. Not lexically sorted (`micromegas` listed before `micromegas-install`), but sibling workstreams have not landed yet so this will resolve at merge time.
- Preserves Phase-0's `name/description/version` keys and `skills: [...]` shape. No replacement of Phase-0 scaffold.

### 7. Integration-test gating — PASS

`pytest plugins/hep-ph-toolkit/skills/ -q` with no env vars → `95 passed, 4 skipped in 0.89s` (4 skipped = `test_ufo_conversion.py` x 2, `test_singletdm_golden.py` x 2). All four integration tests gate on `HEPPH_RUN_NETWORK_TESTS=1`; skip messages are clean ("HEPPH_RUN_NETWORK_TESTS not set"). Offline-install shell test is gated at the `.sh` level and not collected by pytest. Unit tier is fully hermetic: no network calls, no `make`, no binary execution.

Note: with `HEPPH_RUN_NETWORK_TESTS=1` the skipped tests would still short-circuit because they require `micromegas_path` in config, which is not set on this machine. This is correct behavior.

### 8. Apple Silicon — PASS

`_macos_env.sh:17-19` computes `SHARED_CHECK` path to `plugins/shared/install-helpers/check_macos_sdk.sh` (Phase-0 helper) and sources it via `bash`. On SDK-empty it falls back to direct `xcrun --show-sdk-path`, and emits `MICROMEGAS_MACOS_SDK_MISMATCH` + exit 31 if both fail. `SDKROOT`, `FFLAGS` (Homebrew-gfortran guarded), `LDFLAGS`, and `DYLD_LIBRARY_PATH` are all exported per plan.

### 9. CalcHEP arm64 TODO — PASS

- `_macos_env.sh:5-8` documents "Known limitation (v1.1 TODO): patch CalcHEP_src/getFlags for arm64."
- `SKILL.md:156-158` documents the same as a known-limitation note with `--calchep-path` workaround.

### 10. Non-goals respected — PASS

- `git diff workstream-phase0-prep..HEAD -- plugins/model-building/` → empty.
- `git diff workstream-phase0-prep..HEAD -- plugins/hep-ph-toolkit/skills/ddcalc plugins/hep-ph-toolkit/skills/higgstools` → empty.
- No touch on `marketplace.json`, `CLAUDE.md`, or `_common.sh` per diff stat.

### 11. 95 unit + 4 skipped — PASS (after correcting glob)

My first pytest invocation used a glob that under-counted (`micromegas*` conflicts with pytest file-collection rules), yielding 90 passed. Running `pytest plugins/hep-ph-toolkit/skills/ -q` (the glob the report implicitly used) gives the advertised `95 passed, 4 skipped`. Test collection confirms 99 tests total.

### 12. `build_key` cache atomicity + `_netguard.sh` — CONCERN

`_netguard.sh` is fully tested: `test_netguard.sh` exercises clean-make, curl-capture, wget-capture, git-capture, and blocker emission. All 5 assertions pass on re-run.

`flock` coverage is weaker. `test_flock_cache.py::test_cache_populated_once` launches two parallel subprocesses but asserts only `len(complete_dirs) <= 1`, with an inline comment "May be 0 if newProject stub didn't work (that's OK for unit test)." A test that passes when nothing happens is not a test of `flock`. The other two tests in this file check hash-key independence, not locking. The implementer's Deviation #4 acknowledges "the unit test does not exercise the actual flock path." This is a v1-acceptable gap if clearly framed as integration-only, but the plan §1.3 explicitly calls for a unit test of "two parallel invocations on same hash; only one populates." As written, the test does not confirm that behavior.

### 13. Implementer-flagged risks — assessment

| Implementer risk | Severity |
|------------------|----------|
| 1. PPPC path (`Data/AtProduction_gammas.dat`) | Low; reviewer can verify during v1 install smoke. |
| 2. CalcHEP arm64 FFLAGS interference | Low–Medium; documented TODO. |
| 3. macOS `flock` requires Homebrew util-linux | Medium; will surface as `flock: command not found` on plain macOS. Worth a runtime-present check with a clear blocker code. |
| 4. `newProject` may not exist pre-build | Low; error path emits `UFO_CONVERT_FAILED` with location; OK. |
| 5. `test_use_path_validation.py` path isolation | Low; behavior is correct. |
| 6. CalcHEP Monte Carlo may not honour `srand` seed | Medium–High for scan reproducibility, but cannot be validated in v1 without a real install. Accept as v1.1 investigation. |
| 7. Channel regex format | Medium; will be resolved when real fixture is captured (cross-listed with §3 FAIL). |

### Additional finding — verification command fragility

The plan §4 command
```
HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/empty bash install_micromegas.sh install 2>&1 | grep -q MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY
```
fails on this machine (2 GB free ≤ 3 GB check-disk threshold) without `HEPPH_SKIP_DISK_CHECK=1` — the disk check fires before the network check. The implementer added `HEPPH_SKIP_DISK_CHECK` as a test-only env var (Deviation #2) and the python no-network test uses it, so coverage is fine, but the plan's literal command won't run as written on constrained dev boxes. Minor; suggest the plan's next revision add the skip flag to the verification script or re-order stages so network policy is evaluated before disk.

### Additional finding — scan.py does not execute points

`scan.py:155-160` writes `status: "queued"` stub rows with empty `omega_h2`/σ columns. Plan §1.3 states: `run_point.py` is called per grid point; columns are populated. Implementer Deviation #5 acknowledges this but frames it as "connect when binary is available." This leaves the `scan` subcommand non-functional even with a real micrOMEGAs install — the user gets a CSV of "queued" rows. Severity: Medium. At minimum `scan.py` should attempt `run_point.run()` and fall back to "queued" with a reason, or refuse to run without a binary.

---

## Required fixes

1. **Regenerate the golden fixture from the shipped benchmark.** Run `regenerate_fixture.py` on a machine with micrOMEGAs 6.0.5 installed, commit the captured `stdout_singletDM.txt` and `summary_singletDM.json`. Remove the literal `0.118` from `test_parse_micromegas_out.py:19` — either assert the value read is finite+positive, or assert it equals whatever the regenerated fixture contains (loaded from the fixture, not typed in). This is the central plan discipline.
2. **Wire `scan.py` to `run_point.run()`.** Even if the binary is absent, the scan should invoke `run_point.run()` and classify the resulting `MICROMEGAS_RUNTIME_FAILURE` per-row rather than writing a blanket "queued". Alternatively: refuse to run with a clear `MICROMEGAS_BINARY_MISSING` blocker.
3. **Strengthen `test_flock_cache.py::test_cache_populated_once`.** The assertion `<= 1` trivially passes on 0. Change to require exactly 1 complete directory (fail the test if the mocked pipeline doesn't produce any), or relocate the test to the integration tier and replace the unit test with something that actually exercises the `flock` syscall (e.g. two raw `flock -x` subshells on a shared lockfile).

## Nice-to-haves

- Explicit `command -v flock` check in `ufo_to_calchep.sh` with a clear blocker code on macOS systems missing `util-linux`.
- Plan §4 verification command revised to include `HEPPH_SKIP_DISK_CHECK=1`, or stage ordering in `install_impl.sh` swapped so network policy is evaluated before disk.
- `plugin.json` skills array lexically sorted (plan §1.1 specifies this; sibling-merge will likely re-sort, but doing it now reduces diff noise).
- PPPC table path (`Data/AtProduction_gammas.dat` vs. `Data/pppc4dmid/...`) verified against the real 6.0.5 tarball before the first v1 install smoke.

## Re-verification requested

After the required fixes land:

- Re-run `pytest plugins/hep-ph-toolkit/skills/ -q` → expect `≥95 passed, 4 skipped`.
- Diff `tests/fixtures/stdout_singletDM.txt` vs. its previous hand-authored form — confirm it contains non-integer percentages, float noise, and a header consistent with `Singlet_DM/main` output.
- `grep -n '0\.118\|0\.05' plugins/hep-ph-toolkit/skills/micromegas/tests/` → should not find any literal in test assertions (fixture contents are acceptable).
- Re-run `scan.py` with `--scan lhs=0.05:0.15:step=0.05` against a stub binary; each row should have a `status` other than `queued` (either `ok`, `recoverable`, or `MICROMEGAS_BINARY_MISSING`).
- Re-run `test_flock_cache.py`; the populated-once test should fail if the mock fails to populate, not silently pass.

No code changes made by reviewer.
