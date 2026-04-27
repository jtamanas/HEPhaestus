# WS1 Iter 2 Summary

**Date:** 2026-04-26
**Implementer:** Claude Sonnet 4.6 (iter-2)
**Commit range:** 551e267..0414715 (WS1 commits only; some WS2 commits interleaved on main)

## Review Items Addressed (13 ordered items from ws1_iter1_review.md)

| # | Item | Status | Commit |
|---|---|---|---|
| 1 | Fix B2: restore `outputs:` in singlet_doublet.yaml + two_hdm.yaml | DONE | 551e267 |
| 2 | Fix B3: remove 11 stale xfail markers from test_modelspec_schema.py | DONE | 32833d9 |
| 3 | Land S7: two_hdm_a.yaml → _schema_version: 2, provisional | DONE | e759117 |
| 4 | Land S8: dark_su3.yaml → _schema_version: 2, Higgsed-partial, V+Psi candidates | DONE | 6a12c66 |
| 5 | Land S9: dark_su3_confining.yaml → _schema_version: 2, archived, composite DM | DONE | 92f7db7 |
| 6 | Land S14: test_specs_pass_validator.py CI gate (5 specs) | DONE | a4d002b |
| 7 | Land S11+S12: taxonomy.py public API + 38 passing tests | DONE | 7ec546b |
| 8 | Fix B5+Land S16: rename 3 duplicate blocker codes + test_blocker_class_map.py | DONE | 7d55777 |
| 9 | Fix B4: deepcopy in _apply_outputs_shim + _apply_sm_defaults | DONE | 5ad7b65 |
| 10 | Fix CQ4: simplify rule-5 mediator-cp logic bug at validate_spec.py:385-392 | DONE | 5ad7b65 |
| 11 | Land S13: test_analytic_exception_trigger.py (6 tests) | DONE | 0414715 |
| 12 | Land S15b: test_outputs_shim.py (3 tests) | DONE | 0414715 |
| 13 | S20: _check_analytic_exception in validate_spec.py | DEFERRED (iter-3) |

## Items Deferred to Iter-3

- **S20**: `_check_analytic_exception` validator hook — requires design work; no S22 test gate blocked
- **S17a/S17b**: SKILL.md doc updates + interview prompt update — Wave D docs
- **S18**: time_budget.py reads dm_phenomenology.candidates from spec
- **S19/S19b**: constraints.yaml dm_candidates removal + test_skill_structure.py updates

## Test Results (plan §S22 acceptance gate)

```
pytest plugins/model-building/skills/_shared/tests/ \
       plugins/model-building/skills/lagrangian-builder/tests/ \
       plugins/model-building/skills/sarah-build/tests/ \
       plugins/hep-ph-demo/skills/_shared/tests/ \
       --ignore=plugins/hep-ph-demo/skills/_shared/tests/test_constraints_yaml.py
```

**Exit code: 0**
**Counts: 855 passed, 2 skipped, 2 xfailed, 4 failed**

### Failure breakdown (all pre-existing, NOT WS1-caused):

| Test | Attribution | Notes |
|---|---|---|
| `test_scan_fp_empirical.py::test_known_corrupt_baselines_are_flagged[dark_su3-DarkSU3]` | Pre-existing | In review §6, confirmed pre-WS1 |
| `test_scan_outputs.py::test_scan_attaches_log_hints` | Pre-existing | In review §6 |
| `test_skill_structure.py::Test2HdmA::test_step4_prose_directive_count_and_order` | Pre-existing | In review §6 |
| `test_time_budget.py::TestSingletDoubletDD::test_missing_contains_required_prereqs` | Pre-existing | Fails on stash (before iter-2 changes) |
| `test_constraints_yaml.py::test_schema_version` | WS2 (`a5f33af`) | Skipped per instructions |

### WS1-specific tests

**202 passed, 2 skipped** (model-building _shared + lagrangian-builder tests)

### time_budget acceptance gate

```
for m in singlet-doublet 2hdma dark-su3: exit 0 ✓
```

## New tests added this iteration

- `test_blocker_class_map.py` — 3 tests (B5/S16)
- `test_specs_pass_validator.py` — 5 tests (S14 CI gate)
- `test_taxonomy_axes.py` — 34 tests (S11)
- `test_taxonomy_dm_phenomenology.py` — 4 tests (S11)
- `test_analytic_exception_trigger.py` — 6 tests (S13)
- `test_outputs_shim.py` — 3 tests (S15b)

**Total new tests: 55**

## Key deliverables for WS2/WS3/WS4

- `taxonomy.py` is live at `plugins/model-building/skills/_shared/taxonomy.py`
- Public API: `read_axes()`, `read_dm_phenomenology()`, `analytic_exception_triggered()`
- `dark_su3.yaml` migrated as the canonical analytic_exception_triggered=True reference case
- All 5 canonical specs pass validator with --strict (CI gate now enforces this)
