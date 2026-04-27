# WS5 Iteration 1 Log

**Date:** 2026-04-26
**Implementer:** Claude Sonnet 4.6 (ws5-iter1)
**Scope:** S0 (router-output spike) + S0.5 (fixture-registry repair)

---

## S0 — Router-output spike

### Actions taken

1. Created `tests/integration/__init__.py` (empty package marker)
2. Created `tests/integration/test_module_imports.py` (5-LOC permanent smoke)
3. Verified `pytest tests/integration/ -v` → 1 passed
4. Authored `impl/ws5_spike.py` — routes all 4 models × 2 modes via fixture registries
5. Ran initial spike → discovered 4 D-class findings and 1 R-class finding
6. Authored `intel/ws5_spike_findings.md` documenting all findings

### S0 discoveries (pre-S0.5 spike)

- D1: Fixture banner missing "25000"+"Planck target" (confirmed)
- D2: `dark-su3-confining-synthetic` not in fixture registry (confirmed)
- D3: Model ID `2hdm-a` vs `two-hdm-a` — fixture uses `two-hdm-a`; spike script corrected
- D4: `dark-su3` strict mode raised `MatrixAcknowledgementMissing` — fixture chain_overrides lacked `matrix_acknowledgement.accepted_blockers`
- R1: Real `_shared/analytic_exceptions.yaml` uses list shape; fixture uses dict shape (DEFERRED)

---

## S0.5 — Fixture-registry repair

### Actions taken

1. Rewrote `tests/fixtures/registries/analytic_exceptions.yaml` dsu3-002 banner verbatim from real registry (`banner: |` literal block; contains REGRESSION-ANCHOR, 25000, Planck target)
2. Added `matrix_acknowledgement.accepted_blockers` to dark-su3 `relic` and `dd` chain_overrides in fixture `constraints.yaml`
3. Added `dark-su3-confining-synthetic` entry to fixture `constraints.yaml` models block
4. Updated spike script model list from `2hdm-a` → `two-hdm-a`
5. Re-ran spike for all 4 models × 2 modes — all 8 outputs valid
6. Updated `intel/ws5_spike_findings.md` with "Resolved by S0.5" section

### S0.5 acceptance (all PASS)

- `dark-su3-confining-synthetic` in fixture constraints.yaml: OK
- `grep -E '25000|Planck target' analytic_exceptions.yaml`: MATCH
- All 8 spike JSON files exist: OK
- Synthetic strict: verdict=HARD_HALT, exit_code=6: OK
- dsu3 default banner: REGRESSION-ANCHOR + 25000 + Planck target all present: OK

---

## Final verification

- `pytest tests/integration/ -v` → 1 passed (smoke test still green)
- All OOS guards respected: zero edits to router source, canonical specs, or real shared registries

---

## Files created/modified

### New files
- `plugins/workflow/skills/model-router/tests/integration/__init__.py`
- `plugins/workflow/skills/model-router/tests/integration/test_module_imports.py`
- `.shift-manager/run-20260426-workflow-skill/impl/ws5_spike.py`
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_singlet_doublet_{default,strict}.{json,md}` (4)
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_two_hdm_a_{default,strict}.{json,md}` (4)
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_dark_su3_{default,strict}.{json,md}` (4)
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_dark_su3_confining_synthetic_{default,strict}.{json,md}` (4)
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_2hdm_a_{default,strict}.{json,md}` (4 error stubs from initial run)
- `.shift-manager/run-20260426-workflow-skill/intel/ws5_spike_findings.md`

### Modified files (fixture only — in scope per plan §Out-of-scope guards)
- `plugins/workflow/skills/model-router/tests/fixtures/registries/analytic_exceptions.yaml` — banner rewritten
- `plugins/workflow/skills/model-router/tests/fixtures/registries/constraints.yaml` — matrix_acknowledgement added; synthetic model registered

### No modifications to
- `plugins/workflow/skills/model-router/scripts/model_router/` (router source)
- `plugins/hep-ph-demo/skills/_shared/` (canonical registries)
- `plugins/hep-ph-demo/skills/_shared/assets/` (canonical specs)
