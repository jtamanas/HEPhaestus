# WS5 iter-3 Summary

**Date:** 2026-04-26
**Implementer:** sonnet (iter-3)
**Scope:** S3, S4, S5, S6
**Commit:** f6ac15d
**Status:** READY-FOR-REVIEW-3

---

## Deliverables

### S3 — dsu3 LOAD-BEARING assertions

| File | Status |
|---|---|
| `tests/integration/test_validation.py` (extended) | DONE |

4 tests added:
- `test_dsu3_per_candidate_pair_emitted` — LOAD_BEARING
- `test_dsu3_dark_color_wall_surfaces_in_disclosure_banner` — LOAD_BEARING
- `test_dsu3_matrix_acknowledgement_intact` — DIAGNOSTIC
- `test_dsu3_active_chain_is_analytic_backend` — LOAD_BEARING

### S4 — Strict-mode + exit-code assertions

8 tests added (all LOAD_BEARING):
- `test_exit_code_default[<model_id>]` × 4
- `test_exit_code_strict[<model_id>]` × 4

### S5 — Markdown 3-substring + HARD_HALT no-signoff negative

5 tests added (all LOAD_BEARING):
- `test_dsu3_markdown_contains_regression_anchor_phrase`
- `test_two_hdm_a_markdown_contains_signoff_section_header`
- `test_dark_su3_confining_markdown_contains_eft_rewrite_phrase`
- `test_dark_su3_confining_markdown_no_signoff_section`
- `test_hard_halt_no_signoff_placement`

### S6 — validation_report.py + smoke test

| File | Status |
|---|---|
| `scripts/validation_report.py` | CREATED |
| `tests/integration/test_validation_report_smoke.py` | CREATED |

---

## Test results

- S3 acceptance: `pytest -k 'dsu3' -m load_bearing` → 3 LOAD_BEARING tests PASS
- S4 acceptance: `pytest -k 'exit_code'` → 8 tests PASS
- S5 acceptance: `pytest -k 'markdown or no_signoff_placement'` → 5 tests PASS
- S6 acceptance: `pytest test_validation_report_smoke.py` → 1 test PASS
- Full integration suite: **59 passed / 0 failed**
- Full router suite: **194 passed / 0 failed**

---

## Iter-2 recommendations consumption (all 7)

| # | Status |
|---|---|
| 1 sentinel-dict S7 risk | NOTED — S7 will skip dark-su3-strict or use separate code path |
| 2 dict-access for exit_code | APPLIED |
| 3 matrix_ack DIAGNOSTIC test | APPLIED |
| 4 per_candidate all 3 obs | APPLIED |
| 5 DRY via recompute helper | APPLIED |
| 6 exception_id + kind + position | APPLIED |
| 7 lru_cache on _get_reports | APPLIED |

---

## Open items for S7-S10

- S7: regenerate_snapshots.py + 8 (or 7) snapshots + 16 (or 14) snapshot tests.
  Key decision: sentinel-dict (Recommendation #1) means dark-su3-strict snapshot
  will not validate against schema. Either skip that snapshot or use a separate approach.
- S8: WS5_FINDINGS.md with ≥ 2 pre-populated findings.
- S9: test_oos_guards.py.
- S10: SKILL.md ## Validation section + RUN_REPORT.md summary.

---

READY-FOR-REVIEW-3
