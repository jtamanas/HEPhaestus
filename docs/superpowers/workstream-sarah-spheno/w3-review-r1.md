## Verdict: APPROVE

## Test count
34 passed in 0.41s (pytest, worktree `wt-w3-sarah-build`).

## Findings

### Blocker
_None._

### Major
_None._

### Minor
- **Scope audit caveat (not a defect).** `git diff main..HEAD --stat` shows `plugins/hep-ph-toolkit/skills/madgraph/**` deletions, but `git log main..HEAD -- plugins/monte-carlo-tools/` is empty. Those deletions live on `main` post-branch; against the actual merge-base `949f484`, the diff is 100% under `plugins/hep-ph-toolkit/skills/sarah-build/**` (27 files, +2168/-4). Scope is clean. Worth a rebase on `main` before merge to avoid reviewer confusion, but not a blocker here.
- `parse_sarah_log.py` uses Python `warnings.warn` for unknown log patterns (line comment, not surfaced in grep). Non-fatal per plan, but consider a structured `unknown_pattern` code later so the harness can aggregate.

### Nit
- `run_sarah.py:169` — `AppendTo[$Path, "{sarah_path}/.."]` is correct (matches hep-ph-demo precedent). Please add a one-line comment in-situ noting "`/..` suffix required; see §2.X" so a future contributor doesn't strip it during cleanup.
- `SKILL.md:224` self-references "§2.10: `str.format` only, no Jinja2" — good. Consider tagging the render function docstring the same way.

## Check-by-check evidence
1. **Tests pass.** 34/34, 0.41s.
2. **Scope.** Clean against merge-base; see Minor above.
3. **No Jinja2.** Zero `{%` / `{{` hits in `templates/` or rendered goldens. The four `.format(**tokens_*)` calls at `render_templates.py:322-325` are standard Python `str.format`. Test `test_no_jinja2_syntax` enforces this on rendered output.
4. **`str.format` usage.** Confirmed at lines 322-325; f-strings used elsewhere for per-line row construction (lines 94, 155, 190, 208, 264, 266) — appropriate, no Jinja.
5. **`AppendTo[..., "/.."]`.** Present at `run_sarah.py:169`: `f'AppendTo[$Path, "{sarah_path}/.."]; '`. Phase-2 contract honored.
6. **Cache key shape.** `_compute_cache_key(spec_bytes, sarah_version)` returns `f"{sha}={sarah_version}"` (line 74-77). Stored at `.sarah_build_key`. No output-tree hashing. Matches §2.9.
7. **Blocker emission.** `ANOMALY_CANCELLATION_FAILED` (fatal), `MODELSPEC_INVALID` (fatal), and a separate `warnings` entry for non-fatal warning lines. Schema-conformant.
8. **Test isolation.** All four test files use `monkeypatch` / `tmp_path`. Confirmed via grep.
9. **Goldens sane.** 4 `.m` files present (`DarkSU3.m`, `SPheno.m`, `parameters.m`, `particles.m`). `MpsiD`, `gD`, `psiDL`, `psiDR`, `SU3` all present with plausible formatting.
10. **`build.py --help`** runs cleanly; `--force` flag surfaced.

Reviewed time-boxed in ~8 min against the 10-check list. SARAH integration itself is implicit-skipped (no `wolframscript` on reviewer machine) — unavoidable and called out by implementer.
