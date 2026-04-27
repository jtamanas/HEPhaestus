# WS5 iter-3 Log

**Date:** 2026-04-26
**Implementer:** sonnet (iter-3)
**Scope:** S3, S4, S5, S6
**Commit:** f6ac15d
**Pattern:** abbreviated 1-sonnet+1-opus (per plan §Iron-sharps-iron PARTIAL PRESERVATION)

---

## Required reading order (consumed)

1. `plan/ws5_plan_final.md` — sections S3-S6 READ IN FULL.
2. `reviews/ws5_iter2_review.md` — 7 recommendations consumed:
   - R#1: sentinel-dict + S7 snapshot risk — DOCUMENTED, S7 will skip dark-su3-strict snapshot.
   - R#2: dict-access for exit_code — APPLIED (all S4 tests use `report["exit_code"]`).
   - R#3: matrix_acknowledgement_missing_observables field — DIAGNOSTIC test added (S3).
   - R#4: per_candidate labels per-observable (dsu3) — APPLIED in S3 per expected YAML.
   - R#5: recompute_assertion_categories DRY cross-check — APPLIED in S3 banner test.
   - R#6: exception_id + kind + position assertions — APPLIED in S3 banner test.
   - R#7: lru_cache on _get_reports — APPLIED (functools.lru_cache added).
3. `impl/ws5_iter2_summary.md` — understood iter-2 state; D5 (dsu3 strict exit_code=4) consumed.
4. `tests/integration/conftest.py` — route_for, report_pair, recompute_assertion_categories read.
5. `tests/integration/test_validation.py` — existing 40-test structure read.
6. Expected YAML files (all 4) — data values read for assertions.

---

## Steps completed

### S3 — dsu3 LOAD-BEARING assertions

**File:** `tests/integration/test_validation.py` (extended)

4 tests added to the existing module:

1. `test_dsu3_per_candidate_pair_emitted` — LOAD_BEARING. Loops all 3 observables;
   asserts `len(per_candidate) == 2`, `names == {V, Psi}`, labels per-observable
   (relic→{Omega_V_h2,Omega_Psi_h2}, dd→{sigma_SI_V,sigma_SI_Psi}, id→{Phi_id_V,Phi_id_Psi}).
   Driven by `expected/dark_su3.yaml` per_candidate section.

2. `test_dsu3_dark_color_wall_surfaces_in_disclosure_banner` — LOAD_BEARING.
   Asserts `placements[0].kind == "analytic"`, `exception_id == "dsu3-002"`,
   `position == "before_per_observable"`, and three content substrings
   ("REGRESSION-ANCHOR", "25000", "Planck target").
   Also calls `recompute_assertion_categories("dark-su3", ...)["dsu3_banner_triple_substring"]`
   for DRY cross-check (Recommendation #5, #6).

3. `test_dsu3_matrix_acknowledgement_intact` — DIAGNOSTIC. Asserts that only `relic`
   has `matrix_acknowledgement_missing=True` in default mode (relic chain_override
   deliberately omits MATRIX_COVERAGE_GAP per WS3 contract). Fails if unexpected
   observables have the flag set.

4. `test_dsu3_active_chain_is_analytic_backend` — LOAD_BEARING. Asserts all 3
   observables have `active_chain.prereq_id == "analytic_backend"` and
   `active_chain.role == "escape_hatch"`.

### S4 — Strict-mode + exit-code assertions

**File:** `tests/integration/test_validation.py` (extended)

8 tests added:

- `test_exit_code_default[<model_id>]` × 4 — LOAD_BEARING. All 4 models exit 0 in default mode.
- `test_exit_code_strict[<model_id>]` × 4 — LOAD_BEARING. Expected values:
  - singlet-doublet: 0
  - two-hdm-a: 5 (HALT_FOR_SIGNOFF)
  - dark-su3: 4 (MatrixAcknowledgementMissing sentinel, per D5 from iter-2)
  - dark-su3-confining-synthetic: 6 (HARD_HALT)
  Uses dict-access `report["exit_code"]` per Recommendation #2.

### S5 — Markdown 3-substring + HARD_HALT no-signoff negative

**File:** `tests/integration/test_validation.py` (extended)

5 tests added (all LOAD_BEARING):

1. `test_dsu3_markdown_contains_regression_anchor_phrase`: full phrase check.
2. `test_two_hdm_a_markdown_contains_signoff_section_header`: section header in 2hdm-a markdown.
3. `test_dark_su3_confining_markdown_contains_eft_rewrite_phrase`: EFT REWRITE REQUIRED in synthetic markdown.
4. `test_dark_su3_confining_markdown_no_signoff_section`: negative assertion — no "## Required next steps".
5. `test_hard_halt_no_signoff_placement`: JSON placements have no `signoff_prompt` kind for synthetic.

### S6 — validation_report.py CLI + smoke test

**Files created:**
- `scripts/validation_report.py` (new)
- `tests/integration/test_validation_report_smoke.py` (new)

`validation_report.py`:
- `argparse` CLI with `--config <dir>` and `--no-color` flags.
- Routes all 4 models (default + strict) using production `route()` with fixture registry paths.
- Outputs one `## <model_id>` markdown section per model.
- Imports `recompute_assertion_categories` from `tests/integration/conftest.py` for DRY (plan R7).
- No numpy/scipy/mpmath imports (verified by `grep` and runtime self-check in `__main__`).
- Exit 0 always — formatter, not a regression gate.
- Handles MatrixAcknowledgementMissing sentinel (same as report_pair).

`test_validation_report_smoke.py`:
- 1 test: `test_validation_report_emits_section_per_model`.
- Runs `validation_report.py --no-color` via subprocess; asserts `## <model_id>` for all 4.

---

## Test counts

| Step | Tests | Marker | Status |
|---|---|---|---|
| S3 dsu3 per_candidate | 1 | LOAD_BEARING | GREEN |
| S3 dsu3 banner | 1 | LOAD_BEARING | GREEN |
| S3 dsu3 matrix_ack | 1 | DIAGNOSTIC | GREEN |
| S3 dsu3 active_chain | 1 | LOAD_BEARING | GREEN |
| S4 exit_code_default | 4 | LOAD_BEARING | GREEN |
| S4 exit_code_strict | 4 | LOAD_BEARING | GREEN |
| S5 markdown (5) | 5 | LOAD_BEARING | GREEN |
| S6 smoke | 1 | (none) | GREEN |
| **S3-S6 subtotal** | **18** | | |

Full suite (integration): **59 passed / 0 failed**
Full suite (all router tests): **194 passed / 0 failed**

RED count: 0 (all tests written GREEN against post-S0.5 spike output; no RED-then-GREEN
cycle was needed because spike output was authoritative from iter-1/iter-2).

---

## Iter-2 recommendations consumption

| # | Recommendation | Applied |
|---|---|---|
| 1 | sentinel-dict won't survive S7 schema-validation for dark-su3-strict | NOTED — S7 will handle (skip dark-su3-strict snapshot or separate code path). |
| 2 | dict-access for exit_code in S4 | YES — all S4 tests use `report["exit_code"]`. |
| 3 | matrix_acknowledgement_missing_observables field | YES — DIAGNOSTIC test added in S3. |
| 4 | per_candidate loop all 3 obs in S3 | YES — test_dsu3_per_candidate_pair_emitted iterates all 3. |
| 5 | DRY via recompute_assertion_categories | YES — banner test cross-checks the helper. |
| 6 | exception_id + kind + position assertions | YES — banner test asserts all 3 fields. |
| 7 | lru_cache on _get_reports | YES — functools.lru_cache applied. |

---

## OOS discipline

Zero edits to:
- `plugins/constraints/skills/dark-matter-constraints/scripts/`
- `plugins/workflow/skills/model-router/scripts/model_router/` (router source)
- `plugins/hep-ph-demo/skills/_shared/` (real registries)
- `CLAUDE.md`

Only files touched:
- `plugins/workflow/skills/model-router/tests/integration/test_validation.py` (extended)
- `plugins/workflow/skills/model-router/scripts/validation_report.py` (new)
- `plugins/workflow/skills/model-router/tests/integration/test_validation_report_smoke.py` (new)
