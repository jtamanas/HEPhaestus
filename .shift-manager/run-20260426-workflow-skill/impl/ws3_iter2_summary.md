# WS3 iter-2 Summary

**Branch:** `worktree-agent-af06d4ba6edcdfe94`
**Commit range (iter-2 only):** `6c35d1e..b181eda` (4 commits)
**Date:** 2026-04-26

---

## Items addressed

### Fix #1 (HIGH) — D9 violation: local axis fallback deleted
- `extract_axes.py` lines 161-173 fallback removed. `SchemaVersionError` → `RegistryCorrupt`.
- All 5 fixture specs migrated to `_schema_version: 2` with `kind:` gauge fields and
  `authoring_status`, so `taxonomy.read_axes` succeeds without any local fallback.

### Fix #2 (MEDIUM) — Fake test restored to real assertion
- `test_extract_archived_model_raises_spec_archived_error`: `assert True` → `with pytest.raises(SpecArchivedError)`.
- Spec patch changed from `spec["_lifecycle"]` to `spec["authoring_status"] = "archived"` —
  the correct field for `taxonomy.read_axes` to return `A8 == 'archived'`.

### S12 — ranking.py + user_memory.py (WS2-independent)
- `rank_by_role()`: three-layer sort (role_index < priority_tiebreak < prereq_id).
- `_apply_user_memory_tiebreak()`: tertiary user-memory sort; absent prereq → 999.
- `load_user_memory()`: stub returning `options.user_preferences` (parser deferred per D11).
- TDD: 11 tests in `test_p4_ranking.py`; confirmed skipped before impl, all pass after.

### S15a-d — render.py skeleton + placements + formatting helpers + contract test
- `stage_p5_render()`: dispatches to verdict-specific render functions (S16-S18 stubbed).
- `_build_json_report()`: serializes `ComposedRouting` → schema-valid JSON dict.
- `_compute_exit_code()`: synthesis §10 table (strict→5/6; default→0).
- `_validate_json_against_schema()`: raises `SchemaValidationError` via jsonschema.
- `_build_placements()`: verdict dispatch → closed-enum placements (ROUTE_TO_ANALYTIC=1,
  HALT_FOR_SIGNOFF=2, HARD_HALT=1, CLEAR=0).
- `_inject_placements()`: `<!-- WS3:section=<position> -->` anchors.
- Formatting helpers: `_format_status_line`, `_format_axis_snapshot_table`,
  `_format_methodology_footnote`, `_format_ranked_chain_table`, `_format_diagnostics_section`.
- `test_p5_render_skeleton.py`: 23 tests — all pass.

### S27 — Full SKILL.md prose
- Populated all TODO sections: usage (Step 0 registration, basic/strict/explain CLI),
  pipeline stage table, ranking policy (3-layer sort), ROUTE_TO_ANALYTIC per-candidate,
  strict mode exit code table, JSON report structure, placement positions, schema versioning,
  plugin-home override note, upstream dependency table.

---

## Items deferred (WS2-dependent, await iter-3 after WS2 merge)

- **S6 happy-path** — needs `ConstraintRow.capability_blockers`. Gate correctly fires.
- **S10** — matrix_lookup needs WS2 bulk API.
- **S11** — compose_rank needs WS2 `ConstraintRow.capability_blockers`.
- **S13** — per-candidate routing (needs S11).
- **S14** — chain overrides + strict fallthrough (needs S11).
- **S19-S23** — test skip-flips + orchestrator (needs S6, S10-S14).
- **S24** — CLI entrypoint (needs S23 orchestrator).
- **S25-S26** — full contract test batches (need S23).
- **S16-S18** — render verdict functions (stubbed; full impl deferred — S15d contract passes).

---

## Test results (final)

```
Command: python3 -m pytest plugins/workflow/skills/model-router/tests/ -v --tb=short
Exit code: 1 (4 expected failures — WS2NotMerged gate correct behavior)
Counts: 52 passed / 4 failed / 1 skipped — 57 collected
```

**Failing tests (all expected, WS2NotMerged gate):**
- `test_load_singlet_doublet_returns_loaded_context`
- `test_load_sets_default_observables_when_none_given`
- `test_load_absent_blocker_catalog_sets_absent_registries`
- `test_load_unknown_model_raises_model_not_in_registry`

**Skipped:** 1 — `test_p3_matrix_lookup.py` whole-file skip (S10 not yet implemented; correct per D7).

---

## Commit range

| Commit | Message |
|--------|---------|
| 6c35d1e | ws3-iter2(fix1+fix2): remove D9 fallback + restore real archived-model assertion |
| bc9279f | ws3-iter2(S12): ranking.py + user_memory.py — WS2-independent pure functions |
| 5b6dc2f | ws3-iter2(S15a-d): render.py skeleton + placements + formatting helpers + contract test |
| b181eda | ws3-iter2(S27): full SKILL.md prose — usage, ranking policy, exit codes, report structure |

(Plus cherry-picks of 9 iter-1 commits: f508eab..c0ba7c5)
