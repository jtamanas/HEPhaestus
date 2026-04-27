# WS4 iter-2 summary

**Agent:** second sonnet implementer  
**Commit range:** 862a215 .. 67bacdb (5 commits)  
**Branch:** worktree-agent-a856544d9fb5357b4

---

## Review items addressed

### Blockers (all 4 resolved)

| Blocker | Review item | Status | Commit |
|---------|-------------|--------|--------|
| B4 | Combined-run conftest collision (`ImportPathMismatchError`) | Fixed | 862a215 |
| B3 | proxy_run static test `warnings.warn` → `assert` (TDD: RED then GREEN) | Fixed | 3df63b4 |
| B2 | Paraphrased-banner fallback in renderer → `RuntimeError` | Fixed | c03379c |
| B1 | Runtime emission test self-authorized rescope → formal `pytest.skip` + FOLLOWUPS.md | Fixed | 4f8fdd3 |

**Blocker 4 fix detail:** Both test dirs had `tests/__init__.py` making pytest register
both conftest files as `tests.conftest` → collision. Fix: removed `__init__.py` from the
workflow tests dir (safe — no `from tests.conftest import` usage there), changed `from .conftest import`
in workflow `test_exceptions_registry.py` (was relative, now inlined path constants),
and converted 6 DMC test files from `from tests.conftest import` to `from .conftest import`.

**Blocker 3 fix detail:** TDD confirmed: assertion change made test RED (AssertionError on
both P1 and P2 for `micromegas-singlet-doublet-proxy-001`). Then added verbatim PROXY-RUN
DISCLOSURE banner from registry to `dark-matter-constraints/SKILL.md` (P1) and
`micromegas/SKILL.md` (P2). Test now GREEN with hard assert, no warnings.

**Blocker 2 fix detail:** Removed the `else` branch that emitted a paraphrased banner when
`entry is None`. Replaced with `raise RuntimeError("Disclosure registry entry missing required
\`banner\` field — registry must be edited to add it; no template fallback exists")`.
All 15 workflow tests pass.

**Blocker 1 fix detail:** Replaced tautological `test_dsu3_002_emitted_before_results_table`
with `test_dmc_runtime_emission_dsu3_002` that calls `pytest.skip("Tracked: FU-WS4-RUNTIME-001
— DMC renderer does not yet expose Python API; runtime emission test deferred")`. Created
`decisions/FOLLOWUPS.md` with 3 FU entries (FU-WS4-RUNTIME-001 open, FU-WS4-PROXY-RUNTIME-001
open, FU-WS4-PROXY-RUN-PLACEMENTS closed by B3). Cleaned up unused imports.

### Minor recommendations addressed

| Rec | Review item | Status | Commit |
|-----|-------------|--------|--------|
| 5 | Write decisions/FOLLOWUPS.md | Done | 4f8fdd3 |
| 6 | Document `_dm_not_in_uv_fields` dark-gauge gate provisionality | Done | 67bacdb |
| 8 | Remove basename fallback in loader path-matching | Done | 67bacdb |

### Minor recommendations left for iter-3

| Rec | Review item | Reason deferred |
|-----|-------------|-----------------|
| 7 | Move `test_status_filtering` to `test_exceptions_registry.py` | Non-blocking; context budget |
| 9 | Extract `_REPO_ROOT` repetition to `_paths.py` | Non-blocking; context budget |
| 10 | Note S3a/S3b/S3c TDD discipline in iter-1 log | Retrospective; non-blocking |

---

## Test results (final)

**Command:** `pytest plugins/workflow/skills/analytic-exception-detector/tests/ plugins/constraints/skills/dark-matter-constraints/tests/ -v`

**Exit code:** 0

| Category | Count |
|----------|-------|
| passed | 87 |
| skipped | 1 (test_dmc_runtime_emission_dsu3_002 — FU-WS4-RUNTIME-001) |
| xfailed | 3 (pre-existing) |
| xpassed | 3 (pre-existing, unrelated to WS4) |
| warnings | 1 (pre-existing DRIFT_PRESENT_BUT_UNDOCUMENTED) |
| failed | 0 |

Improvement from iter-1: proxy_run warnings (2) eliminated; combined-run collection error eliminated.

---

## Commit range

```
862a215  ws4-iter2(blocker-4): fix combined-run conftest collision
3df63b4  ws4-iter2(blocker-3): convert proxy_run warn to assert; add banners to SKILL.md files
c03379c  ws4-iter2(blocker-2): replace paraphrased-banner fallback with RuntimeError
4f8fdd3  ws4-iter2(blocker-1): formal descope of runtime emission test + FOLLOWUPS.md
67bacdb  ws4-iter2(rec-6+8): document dark-gauge guard + remove basename path fallback
```
