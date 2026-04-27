# WS3 iter-4c Summary (Opus implementer — CHUNK C / final)

## Verdict
- [x] CHUNK C acceptance met. WS3 ship-ready.
- READY-FOR-INTEGRATION

## Tests
- Baseline (post iter-4b): **101 passed / 0 failed / 0 skipped**.
- Final: **133 passed / 0 failed / 0 skipped**.
- Net delta: **+32 passes, -0 fails, -0 skips**.

## Commits (all on main, ws3-iter4c prefix)
| SHA | Step | Description |
|---|---|---|
| `7ef85ae` | S23 | Orchestrator: route(model_id, observables, options, *paths) wires P0..P5 with HARD_HALT/HALT_FOR_SIGNOFF early jump-to-P5. 8 scenario tests. Schema A2..A7 loosened to accept any (real WS1 axes are dicts/lists). Test fixture spec_paths repointed at fixture specs for hermetic runs. |
| `e8fa0be` | S24 | Replace router.py skeleton with full argparse CLI: --observables, --strict, --output, --output-dir, --config, --explain, plus three registry-path overrides. Exception-to-exit-code mapping per SKILL.md table. --explain appends per-prereq trace section. Smoke-tested end-to-end on dark-su3. |
| `61f4119` | S25 | Three contract test files batch 1 (12 tests): routing_report_schema (parametric over fixture models), blocker_class_invariant (5-element closed enum), no_inference_by_stealth (AxisBundle interface + observable defaults discipline). |
| `32adedf` | S26 | Three contract test files batch 2 (12 tests): strict_mode_exit_codes (4/5/6), upstream_absence (WS1/WS2/WS4 each absent), cross_plugin_dep_check (D2). Drive-by fix: composer now folds ctx.diagnostics into composed.diagnostics (was dropping detector_unavailable from JSON report). |

## Acceptance check (per dispatch brief)
- [x] **S23** orchestrator implemented; 8 scenario tests GREEN (the brief asked
      for 6 — the count grew because ROUTE_TO_ANALYTIC and HALT_FOR_SIGNOFF
      each split into a pair to cover both default-mode behavior and
      a load-bearing assertion (per-candidate emission, strict exit 5)).
- [x] **S24** CLI implemented; argparse covers every plan-listed flag plus
      registry-path overrides; smoke-tested.
- [x] **S25** 3 contract test files batch 1 authored (12 tests GREEN).
- [x] **S26** 3 contract test files batch 2 authored (12 tests GREEN).
- [x] Orchestrator + CLI work end-to-end on at least 1 demo model
      (dark-su3 ROUTE_TO_ANALYTIC smoke test).
- [x] All 6 contract test files pass (12 + 12 = 24 contract tests, all GREEN).
- [x] Full suite stays green or grows (101 -> 133, +32 net).
- [x] SKILL.md aligns with shipped behavior (no stale field references; audit
      confirmed no edits required).
- [x] Out-of-scope guard verified clean across all chunk-A/B/C commits
      (`git diff --stat 7ef85ae~1..HEAD -- plugins/constraints/` -> empty).
- [x] iter-4c summary + log saved at
      `.shift-manager/run-20260426-workflow-skill/impl/ws3_iter4c_{summary,log}.md`.
- [x] READY-FOR-INTEGRATION line included.

## Discipline
- **TDD:** every new test file went RED-then-GREEN with documented RED count
  in the commit messages.
- **Out-of-scope guard:** ZERO modifications to
  `plugins/constraints/skills/dark-matter-constraints/scripts/` or `tests/`
  across the entire iter-4 sequence.
- **No model-name hardcoding** (no `if "dark_su3" in model_id` patterns);
  the orchestrator is pure pipeline glue.
- **No physics reimplementation in Python**; the router only routes.
- **Heredoc commits** with `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

## Test breakdown by file (final 133)
See `ws3_iter4c_log.md` for the full per-file table. New in chunk C:
test_orchestrator (8), test_routing_report_schema (4),
test_blocker_class_invariant (4), test_no_inference_by_stealth (4),
test_strict_mode_exit_codes (3), test_upstream_absence (6),
test_cross_plugin_dep_check (3). Total new = 32.

## Latent footguns (still tracked; not in chunk-C scope)
- `py.py` at repo root and at `/tmp/py.py` shadow the `py` package, breaking
  pytest from those cwds. Workaround: `cd /tmp/ws3-test-cwd && pytest …`.
  Documented in iter-4a and iter-4b summaries; still applies.
- `referencing` Registry vs RefResolver compat: the renderer falls back from
  the newer `referencing` package to `RefResolver` for older jsonschema. Both
  paths exercised by the schema-invariant tests; no action needed today.

## Drive-by changes (folded into chunk-C commits, no separate commit)
- AxisSnapshot schema A2..A7 type relaxed to `{}` (any) — was `["string","null"]`,
  but real WS1 axes are dicts and lists. Necessary for the orchestrator end-to-
  end path to validate.
- Test fixture constraints.yaml `models.<id>.spec_path` now points at the
  fixture spec files under `tests/fixtures/specs/` instead of hep-ph-demo
  asset paths. Hermetic; survives a missing singlet_doublet asset.
- Composer folds ctx.diagnostics into composed.diagnostics so WS4
  detector_unavailable surfaces in the JSON report.

## What's next (after WS3 ships)
- WS4 remaining work (per the WS4 plan).
- WS5 (real tool integration tests / harness) — out of WS3 scope per plan §11.4.
- A future MEMORY.md parser for `RouterOptions.user_preferences` (deferred per D11/OQ-2).

## READY-FOR-INTEGRATION
All chunk-C acceptance gates green. Suite at 133p / 0f / 0s. CLI smoke-tested
end-to-end. Out-of-scope guard clean. WS3 is ship-ready.
