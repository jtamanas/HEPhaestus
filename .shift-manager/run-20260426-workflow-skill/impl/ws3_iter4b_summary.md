# WS3 iter-4b Summary (Opus implementer — CHUNK B)

## Verdict
- [x] CHUNK B acceptance met.
- [ ] CHUNK C (S23 orchestrator, S24 CLI, S25/S26 contract tests) pending dispatch.

## Tests
- Baseline (post iter-4a): **68 passed / 0 failed / 0 skipped**.
- Final: **101 passed / 0 failed / 0 skipped**.
- Net delta: **+33 passes, -0 fails, -0 skips**.

## Commits (all on main, ws3-iter4b prefix)
| SHA | Step | Description |
|---|---|---|
| `381474e` | S13 | Per-candidate routing for ROUTE_TO_ANALYTIC + DM observables. New `_build_per_candidate_chains` in compose_rank.py; PerCandidateRouting entries pin analytic_backend per CandidateSpec. 5 new tests. |
| `370e0d4` | S14 | chain_overrides + matrix_acknowledgement + strict-mode exit-4. New `_get_chain_overrides`, `_validate_matrix_acknowledgement`, `_build_active_chain_from_override`, `_build_observable_routing_overridden`. Strict mode raises MatrixAcknowledgementMissing on missing/incomplete acknowledgement. 5 new tests. |
| `180fa54` | S16+S17+S18+S22 | Replaced 4 render placeholder strings with real Markdown bodies consuming S15c helpers. ROUTE_TO_ANALYTIC raises DisclosureBannerMissing when disclosure_required=True but no analytic placement. Per-candidate sub-blocks under each DM observable. New tests/test_p5_render.py (14 tests) + tests/test_p5_placement_contract.py (9 tests). Drive-by: schema validator now constructs a referencing Registry so the relative $ref resolves. |

## Acceptance check (per dispatch brief)
- [x] **S13** per-candidate routing implemented; 5/5 tests GREEN.
- [x] **S14** chain_overrides + matrix_acknowledgement + strict-mode exit 4 implemented; 5/5 tests GREEN.
- [x] **S16/S17/S18** render-body placeholders replaced with real Markdown; 14 P5 render tests GREEN.
- [x] **S22** full P5 test coverage authored (test_p5_render.py 14 tests + test_p5_placement_contract.py 9 tests).
- [x] All previously-passing tests still pass (regression-free).
- [x] Stub render strings replaced (no more `placeholder` or `S16/S17/S18 not yet implemented` literals).
- [x] iter-4b log + summary saved.

## Discipline
- **TDD:** every new test file went RED-then-GREEN with documented RED count in each commit message.
- **Out-of-scope guard:** ZERO modifications to `plugins/constraints/skills/dark-matter-constraints/scripts/` (verified via `git diff --stat HEAD~3..HEAD -- plugins/constraints/skills/dark-matter-constraints/scripts/` — empty).
- **No model-name hardcoding** (no `if "dark_su3" in spec_name`); per-candidate routing is purely structural.
- **No physics reimplementation in Python**; per-candidate label is `Omega_<name>_h2` / `sigma_SI_<name>` / `Phi_id_<name>` — pure name composition driven by axes and registry.
- **Heredoc commits** with `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

## Test breakdown by file (final)
| File | Tests | Status |
|---|---:|---|
| test_p0_load.py | 6 | all pass |
| test_p1_extract_axes.py | 6 | all pass |
| test_p1_analytic_module_status_adapter.py | 6 | all pass |
| test_p2_detect_exception.py | 4 | all pass |
| test_p3_matrix_lookup.py | 6 | all pass |
| test_p4_compose_rank.py | 4 | all pass |
| test_p4_per_candidate_rendering.py | 5 | all pass (NEW) |
| test_p4_chain_overrides.py | 5 | all pass (NEW) |
| test_p4_ranking.py | 11 | all pass |
| test_p5_render_skeleton.py | 25 | all pass |
| test_p5_render.py | 14 | all pass (NEW) |
| test_p5_placement_contract.py | 9 | all pass (NEW) |
| **Total** | **101** | **all pass** |

## Remaining work (for CHUNK C dispatch)
- **S23** — `orchestrator.py` wiring P0..P5 with early-jump-to-P5 for HARD_HALT/HALT_FOR_SIGNOFF; 6 orchestrator scenario tests.
- **S24** — replace `router.py` skeleton with full argparse CLI per synthesis §4.2; flags `--observables`, `--strict`, `--output md|json|both`, `--output-dir`, `--config`, `--explain`.
- **S25** — 3 contract tests batch 1 (test_routing_report_schema.py, test_blocker_class_invariant.py, test_no_inference_by_stealth.py).
- **S26** — 3 contract tests batch 2 (test_strict_mode_exit_codes.py, test_upstream_absence.py, test_cross_plugin_dep_check.py).

## Latent footguns (still tracked)
- `py.py` at repo root and at `/tmp/py.py` shadow the `py` package, breaking pytest from those cwds. Workaround: use `/tmp/ws3-test-cwd/`. Not in chunk-B scope to fix.
- `referencing` module API is jsonschema-version-dependent. The drive-by adds a try/except fallback to `RefResolver`; further forward compatibility may need attention as jsonschema evolves past v4.18.

## Drive-by notes (no separate commit; folded into S16-S18+S22)
- The schema validator was previously fail-open against real (non-skeleton) reports because the `$ref: ranked_chain.schema.json` was unresolvable without a base URI. The skeleton contract tests did not trip this because they constructed minimal JSON with no `active_chain` populated; once the real renderer started emitting `ranked_alternatives`, every schema validation raised `Unresolvable`. Now properly resolved with a referencing Registry (with RefResolver fallback).
