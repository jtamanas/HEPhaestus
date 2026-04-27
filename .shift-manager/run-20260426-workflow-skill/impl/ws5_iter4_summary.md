# WS5 iter-4 Summary

**Date:** 2026-04-26
**Implementer:** sonnet (iter-4)
**Scope:** S7, S8, S9, S10
**Commits:** 6c3631a (S7), 61b1b67 (S8-S10)
**Status:** READY-FOR-FINAL-REVIEW

---

## Deliverables

### S7 — Snapshot tripwires

| File | Status |
|---|---|
| `scripts/regenerate_snapshots.py` | CREATED |
| `snapshots/singlet_doublet.json` | CREATED |
| `snapshots/singlet_doublet.strict.json` | CREATED |
| `snapshots/two_hdm_a.json` | CREATED |
| `snapshots/two_hdm_a.strict.json` | CREATED |
| `snapshots/dark_su3.json` | CREATED |
| `snapshots/dark_su3_confining_synthetic.json` | CREATED |
| `snapshots/dark_su3_confining_synthetic.strict.json` | CREATED |
| `test_validation.py` (extended with 14 snapshot tests) | DONE |

7 snapshots (not 8): dark-su3-strict skipped per iter-2 Recommendation #1
(MatrixAcknowledgementMissing; sentinel dict not schema-valid). Documented in
WS5_FINDINGS.md Finding 4.

14 snapshot tests: 7 `test_snapshot_matches` (DIAGNOSTIC) + 7
`test_snapshot_validates_against_schema` (LOAD_BEARING). All GREEN.

Key fix: schema validation mirrors render.py exactly — `Resource(contents=...,
specification=DRAFT7)` + `with_resource("ranked_chain.schema.json", ...)`.

### S8 — WS5_FINDINGS.md

6 findings (2 DEFERRED, 2 OPEN, 2 RESOLVED-IN-WS5). Satisfies ≥ 2 pre-populated
requirement.

### S9 — test_oos_guards.py

2 OOS guard tests. Graceful skip (no origin/main). PASS in CI.

### S10 — SKILL.md + RUN_REPORT.md

- SKILL.md: `## Validation` section added (grep -c == 1).
- RUN_REPORT.md: created and populated with WS5 validation summary.

---

## Test results

- Integration suite: **73 passed / 2 skipped / 0 failed**
- Full router suite: **208 passed / 2 skipped / 0 failed**

---

## Ship-readiness checklist

1. [x] Integration suite exits 0; 73 passed, 2 expected skips.
2. [x] `validation_report.py` exits 0; 4 model sections in output.
3. [x] `ls snapshots/*.json | wc -l` returns 7 (documented gap: Finding 4).
4. [x] 7 snapshots validate against `routing_report.schema.json`.
5. [x] `grep -c '^## Validation' SKILL.md` == 1.
6. [x] `grep -c '^## WS5 validation summary' RUN_REPORT.md` == 1.
7. [x] WS5_FINDINGS.md has 6 findings (≥ 2 requirement met).
8. [x] OOS guard test passes or skips gracefully.
9. [x] No `pytest.mark.skip` outside documented gaps.
10. [x] No `pytest.mark.xfail` anywhere.
11. [x] No numpy/scipy/mpmath imports in validation_report.py or regenerate_snapshots.py.
12. [x] WS5 OOS discipline maintained (no forbidden-path edits).
13. [x] dsu3 LOAD_BEARING banner assertion (3 substrings) PASSES.

---

READY-FOR-FINAL-REVIEW
