# W4 Review R1 — `/spheno-build`

**Branch:** `workstream/w4-spheno-build`
**Worktree:** `/Users/yianni/Projects/hep-ph-agents-worktrees/wt-w4-spheno-build`
**Reviewer:** Opus 4.7 (time-boxed, ~10 min)

## Verdict

**APPROVE with one minor branch-hygiene note.** W4 commit itself is scope-clean and spec-compliant; all spec-§5 invariants verified.

## Test count

`pytest plugins/hep-ph-toolkit/skills/spheno-build/tests/ -q` → **77 passed in 0.09s**. Matches implementer claim.

## Findings by severity

### None blocking

### Low — branch hygiene (not a W4 scope violation)

`git diff main..HEAD --stat` shows deletions of `sarah-build/*` and `monte-carlo-tools/skills/madgraph/*`, which at first glance looks like scope creep. Verified these come from ancestor commits on this branch (`merge-base = 949f484`, current `main = 1ff160d`): the branch diverged before W3's sarah-build lands and before a madgraph cleanup. The W4 commit itself (`be89e5f`) is exactly the claimed **20 files, all under `plugins/hep-ph-toolkit/skills/spheno-build/**`** (+2719/-4). **Recommend rebasing onto current main before merge** to avoid reintroducing deleted files.

### Verified spec-§5 invariants

1. **SPheno invocation signature** (`run_point.py:115`): `subprocess.run([str(spheno_bin), str(les_in), str(spc_out)], ...)` — exact two positional args `<bin> <LesHouches.in> <SPheno.spc>`. PASS.
2. **`os.cpu_count()` not `nproc`** (`compile_model.py:155-156`): `cpu_count = os.cpu_count() or 1; cmd = ["make", "-C", ..., f"-j{cpu_count}"]`. No shell-out. PASS.
3. **Cache key input-based** (`compile_model.py:76-80`): `sha256(spec.yaml) + "=" + sarah_version + "+" + spheno_version`. No output-tree hash. PASS.
4. **LesHouches blocks enumerated** (`leshouches_template.py`): MODSEL, SMINPUTS, MINPAR all present; SPHENOINPUT intentionally deferred to caller (comment at line 51, "callers must append from SARAH output"). Acceptable per §5 — SPHENOINPUT is model-dependent and best sourced from SARAH. NOTE.
5. **Recoverable test is deterministic** (`test_recoverable_handling.py`): uses synthetic `scan_recoverable_trigger.spc` fixture via monkeypatched `scan_worker`, asserts `exactly 1 recoverable row` at fixed index. No "at least one" wording. PASS.
6. **45-row assertion present** (`test_scan_determinism.py:100, 240`): `assert len(points) == 45` and row-count scan test. PASS.
7. **Test isolation**: all 5 test files use `tmp_path`/`monkeypatch`. PASS.
8. **Fixture size**: `sarah_output_darksu3.tar.gz` = 1394 B (1.4 KB) ≤ 10 MB. Placeholder rebuilt post-W3 via `regenerate_fixture.py` as documented. PASS.
9. **Blocker codes** (`compile_model.py:114,122,128,177`): `SPHENO_COMPILE_FAILED` emitted at all fatal paths. `run_point.py` emits `SPHENO_SPECTRUM_PROBLEM` / timeout codes. PASS.

## Recommendation

Merge after rebasing onto current `main` to drop the ancestor-commit deletions from the diff. W4 content itself is ready.
