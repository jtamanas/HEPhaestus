# WS5 iter-2 Summary

**Date:** 2026-04-26
**Implementer:** sonnet (iter-2)
**Scope:** S1 + S2 only
**Commit:** a90cb8e
**Status:** READY-FOR-REVIEW-2

---

## Deliverables

### S1 — 4 per-model expected YAML files + conftest scaffolding

| File | Status |
|---|---|
| `tests/integration/conftest.py` | CREATED |
| `tests/integration/expected/singlet_doublet.yaml` | CREATED |
| `tests/integration/expected/two_hdm_a.yaml` | CREATED |
| `tests/integration/expected/dark_su3.yaml` | CREATED |
| `tests/integration/expected/dark_su3_confining_synthetic.yaml` | CREATED |
| `tests/integration/snapshots/.gitkeep` | CREATED |

### S2 — parametrized test module

| File | Status |
|---|---|
| `tests/integration/test_validation.py` | CREATED |

---

## Test results

- S2 acceptance: `pytest -k 'verdict or status or active_chain or blockers_set'` → **40 passed**
- Full suite: `pytest tests/` → **176 passed** (135 WS3 + 41 WS5 integration)
- 0 failures, 0 regressions

---

## Deviations from plan

### D5 (NEW) — dark-su3 strict exit_code = 4, not 0

The plan said `exit_code.strict: 0` for dark-su3, based on the S0.5 D4 fix adding full `matrix_acknowledgement` to both `relic` and `dd` chain_overrides. However, that fix broke the WS3 test `test_dark_su3_strict_with_missing_acknowledgement_exits_4` which deliberately omits MATRIX_COVERAGE_GAP from `relic` to test the strict-mode raise contract.

**Resolution:** reverted `relic` chain_override to 6 blockers (sans MATRIX_COVERAGE_GAP), updated `dark_su3.yaml` to `exit_code.strict: 4`, updated `report_pair()` to catch `MatrixAcknowledgementMissing` → sentinel dict. All 176 tests pass.

**Impact:** S4's `test_exit_code_strict[dark-su3]` must assert `exit_code == 4` (not 0). The sentinel dict mechanism in `report_pair` makes this transparent.

---

## Iter-1 review recommendations (8 items — all consumed)

| Recommendation | Applied |
|---|---|
| 1. Use `two-hdm-a` as model_id everywhere | YES — all files use `two-hdm-a` |
| 2. singlet_doublet.yaml `dd.active_chain_prereq_id: ddcalc` | YES |
| 3. dark_su3 per_candidate labels per-observable | YES — all 3 observables encoded |
| 4. dark_su3_confining_synthetic.yaml HARD_HALT literal | YES |
| 5. two_hdm_a.yaml placements exception_id: null | YES |
| 6. `axis_snapshot: presence_only` in all 4 YAMLs | YES |
| 7. DRY guard for label assertion | YES — per_candidate encoded per-obs in YAML; conftest recompute_assertion_categories provides DRY helper |
| 8. S2 LOAD_BEARING test count = 40 | YES — 40 tests (4+12+12+12) |

---

READY-FOR-REVIEW-2
