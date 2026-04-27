# WS3 iter-2 log

**Implementer:** claude-sonnet-4-6 (second sonnet implementer)
**Worktree:** `/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-af06d4ba6edcdfe94`
**Branch:** `worktree-agent-af06d4ba6edcdfe94`
**Started:** 2026-04-26

## Setup

Cherry-picked iter-1's 9 commits (d73675e..a07887f → f508eab..c0ba7c5) into this worktree.
Baseline: 18 passed / 4 failed (WS2NotMerged gate, expected) / 1 skipped.

---

## Fix #1 (HIGH) — D9 violation: local axis fallback in extract_axes.py

**Review finding:** extract_axes.py:131-173 had a `_extract_A1`/`_extract_A8` fallback
that violated D9 ("No local fallback … implemented").

**Root cause:** Fixture specs were v1-format (no `_schema_version: 2`, used `dark: true/false`
on gauge groups instead of `kind:`, no `authoring_status` field), causing `taxonomy.read_axes`
to raise `SchemaVersionError`. Iter-1 silently caught the exception and fell back to local
extraction.

**Fix applied:**
1. Updated all 5 fixture specs to `_schema_version: 2` with proper `kind:` fields:
   - `singlet_doublet.yaml` → authoring_status: active
   - `dark_su3.yaml` → authoring_status: complete, kind: dark on SU3_D
   - `two_hdm_a.yaml` → authoring_status: provisional
   - `leptoquark_synthetic.yaml` → authoring_status: active
   - `dark_su3_confining_synthetic.yaml` → authoring_status: active
2. Rewrote extract_axes.py:
   - Removed the fallback branch (lines 161-173 deleted)
   - Catch `SchemaVersionError` specifically → re-raise as `RegistryCorrupt`
   - All other exceptions from read_axes propagate unmodified
   - Import `SchemaVersionError` from taxonomy at module load

---

## Fix #2 (MEDIUM) — fake test: test_extract_archived_model_raises_spec_archived_error

**Review finding:** test body was `assert True` — a fake test masking a design defect.

**Fix applied:**
- Replaced `assert True` with `with pytest.raises(SpecArchivedError):`
- Changed spec patch from `spec["_lifecycle"] = "archived"` to
  `spec["authoring_status"] = "archived"` — correct field for taxonomy.read_axes to
  return A8='archived', which triggers the SpecArchivedError hard-halt.
- Real assertion passes because implementation is correct.

**TDD note:** The `assert True` always passed (fake). The real assertion now passes because
the implementation is correct — the fallback removal makes the flow deterministic.

---

## S12 — ranking.py + user_memory.py

TDD scaffold (test_p4_ranking.py, 11 tests) written first, confirmed skipped.
Implementation: `rank_by_role()` — 3-layer sort (role_index, priority_tiebreak, prereq_id).
`_apply_user_memory_tiebreak()` — adds user-memory as tertiary sort key (absent prereq → 999).
`load_user_memory()` — stub returning options.user_preferences (parser deferred per D11/OQ-2).
All 11 tests pass.

## S15a+S15b+S15c+S15d — render.py skeleton + contract test

S15a: stage_p5_render dispatch + _build_json_report + _compute_exit_code (§10 table:
strict→5/6; default→0) + _validate_json_against_schema (SchemaValidationError via jsonschema).
Schema path fix: parents[1] not parents[2] for schema in stages/render.py.

S15b: _build_placements — verdict dispatch: ROUTE_TO_ANALYTIC→1 (before_per_observable,
analytic); HALT_FOR_SIGNOFF→2 (halt_notice top + signoff_prompt appendix); HARD_HALT→1
(hard_halt_prompt top); CLEAR→[].

S15c: formatting helpers — _format_status_line, _format_axis_snapshot_table,
_format_methodology_footnote, _format_ranked_chain_table, _format_diagnostics_section,
_inject_placements (with <!-- WS3:section=<position> --> anchors).

S15d: test_p5_render_skeleton.py (23 tests) — dispatch/verdict/schema/exit-code/placement.

## Commits so far

- (cherry-picks of iter-1 work, not counted as iter-2 commits)
- 6c35d1e ws3-iter2(fix1+fix2): remove D9 fallback + restore real archived-model assertion
- bc9279f ws3-iter2(S12): ranking.py + user_memory.py — WS2-independent pure functions
- 5b6dc2f ws3-iter2(S15a-d): render.py skeleton + placements + formatting helpers + contract test
- (S27 SKILL.md pending)

Test status after S15d: 52 passed / 4 failed (WS2NotMerged) / 1 skipped.

---
