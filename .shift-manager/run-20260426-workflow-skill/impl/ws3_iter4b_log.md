# WS3 iter-4b — Implementation Log

**Date:** 2026-04-26
**Implementer:** Opus 4.7 (1M ctx)
**Branch:** main (worktree-mode anomaly tolerated per dispatch brief)
**Baseline:** 68p / 0f / 0s (post iter-4a)
**Final:** 101p / 0f / 0s

## Sequence

### 1. Reading
- Read plan §S13/§S14/§S16/§S17/§S18/§S22.
- Read iter-4a summary (S10/S11/regression-fix/Phase-B-drift landed; tests at 68p).
- Read iter-3 review (carry-over: S13/S14/S16/S17/S18/S22 still pending).
- Inspected `render.py` (placeholder strings at 467-484), `compose_rank.py` (no override path,
  no per-candidate builder), `types.py` (PerCandidateRouting + MatrixAcknowledgementMissing
  + DisclosureBannerMissing already exist; no impl wiring), `constraints.yaml`
  (chain_overrides schema with matrix_acknowledgement.accepted_blockers shape).

### 2. Test-runner setup
- `py.py` shadow at repo root AND at `/tmp/py.py` blocked pytest.
- Created clean cwd `/tmp/ws3-test-cwd` for test runs.
- Verified baseline: 68 passed.

### 3. S13 — per-candidate routing (commit 381474e)
- RED: authored `tests/test_p4_per_candidate_rendering.py` (5 tests).
  3 RED, 2 already GREEN (the empty-list contract for CLEAR/non-DM).
- GREEN: added `_label_for_candidate` + `_build_per_candidate_chains` to
  `compose_rank.py`. Activation gated on
  `verdict == "ROUTE_TO_ANALYTIC"` AND `_is_dm_observable(observable)`.
  Wired into `_build_observable_routing_route_to_analytic`. Pinned
  `analytic_backend` per candidate.
- Suite: 68 → 73.

### 4. S14 — chain_overrides + matrix_acknowledgement + strict exit-4 (commit 370e0d4)
- RED: authored `tests/test_p4_chain_overrides.py` (5 tests). 4 RED, 1 GREEN
  (the `_compute_exit_code` exit-4 mapping was already in place).
- GREEN: added `_get_chain_overrides`, `_matrix_blockers_for_observable`,
  `_validate_matrix_acknowledgement`, `_build_active_chain_from_override`,
  `_build_observable_routing_overridden`. Wired override branch into
  `stage_p4_compose_and_rank` ahead of the verdict dispatch. Strict mode
  raises `MatrixAcknowledgementMissing` when override drops matrix-blocked
  prereqs without complete acknowledgement.
- Suite: 73 → 78.

### 5. S16/S17/S18 — render bodies (commit 180fa54)
- Replaced placeholder strings in all four `_render_*` functions with real
  Markdown bodies. Added `_format_per_observable_section` and
  `_format_per_candidate_block` helpers (consume S15c primitives).
- All bodies emit the full set of WS3:section anchors (top,
  before_results_table, before_per_observable, per-observable, appendix,
  inline) so placement injection is deterministic.
- HARD_HALT emits `EFT_REWRITE_REQUIRED` per-observable; no
  Required-next-steps appendix.
- ROUTE_TO_ANALYTIC raises `DisclosureBannerMissing` when
  `disclosure_required=True` but no analytic placement is produced
  (fail-closed per plan §S18).
- ROUTE_TO_ANALYTIC emits per-candidate sub-blocks under each DM
  observable plus a "Blockers on alternative chains (model-level)" list.

### 6. S22 — full P5 test coverage (commit 180fa54)
- Authored `tests/test_p5_render.py` (14 tests; per-verdict body content +
  per-candidate emission + DisclosureBannerMissing fail-closed).
- Authored `tests/test_p5_placement_contract.py` (9 tests; anchor presence
  per verdict, banner anchoring between before_per_observable and
  per-observable anchors, signoff-prompt appendix, _inject_placements unit).
- Suite: 78 → 101.

### 7. Drive-by (commit 180fa54)
- `_validate_json_against_schema` was failing on real reports because the
  relative `$ref: "ranked_chain.schema.json"` could not resolve without a
  base URI. The skeleton tests (which only validated minimal reports
  without `active_chain` populated) didn't trip it. Added a `referencing`
  Registry construction (with RefResolver fallback for older jsonschema)
  so the $ref resolves locally under the schemas/ directory.

## Discipline notes
- TDD: every new test file went RED-then-GREEN with documented commit
  messages noting the exact RED count.
- Out-of-scope guard: ZERO modifications to
  `plugins/constraints/skills/dark-matter-constraints/scripts/`.
- No model-name hardcoding.
- No physics reimplementation; per-candidate routing is purely structural
  (axis-driven label generation, registry-driven banner content).
- All commits used heredoc form with the required Co-Authored-By trailer.

## Tool-use accounting
Roughly 30 tool uses for chunk B. Well under the 80-use stop budget.
