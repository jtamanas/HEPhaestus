# WS5 Iteration 1 Summary

**Date:** 2026-04-26
**Implementer:** Claude Sonnet 4.6
**Steps completed:** S0 (router-output spike) + S0.5 (fixture-registry repair)

READY-FOR-REVIEW-1

---

## What was done

### S0: Router-output spike
- Created `tests/integration/__init__.py` + permanent 5-LOC smoke test (`test_module_imports.py`)
- Authored and ran `impl/ws5_spike.py` routing all 4 models × 2 modes through fixture registries
- Discovered 4 D-class findings and 1 R-class finding
- Documented all findings in `intel/ws5_spike_findings.md`

### S0.5: Fixture-registry repair
- Rewrote dsu3-002 banner in fixture `analytic_exceptions.yaml` verbatim from real `_shared/` registry (now contains REGRESSION-ANCHOR, "25000× the Planck target")
- Added `matrix_acknowledgement.accepted_blockers` to dark-su3 `relic` + `dd` chain_overrides (7 blockers; enables strict=0)
- Registered `dark-su3-confining-synthetic` in fixture `constraints.yaml`
- Re-ran spike: all 8 outputs (4 models × 2 modes) valid

---

## Key findings for S1 (expected YAML authoring)

| Finding | Impact on S1 |
|---|---|
| Model ID is `two-hdm-a` (not `2hdm-a`) | Use `two-hdm-a` everywhere |
| singlet-doublet `dd.active_chain.prereq_id = "ddcalc"` (not `maddm`) | Set `dd.active_chain_prereq_id: ddcalc` in expected YAML |
| dark-su3 per_candidate labels differ by observable | Labels are per-observable: relic=Omega_V/Psi_h2, dd=sigma_SI_V/Psi, id=Phi_id_V/Psi |
| dark-su3-confining-synthetic per_observable status = "HARD_HALT" | Set `status: HARD_HALT` for all observables |
| R-class: real analytic_exceptions.yaml uses list shape; fixture uses dict | DEFERRED; no WS5 action |

---

## Post-spike ground-truth table (authoritative for S1)

| Model (canonical ID) | Mode | Verdict | Exit |
|---|---|---|---|
| singlet-doublet | default | CLEAR | 0 |
| singlet-doublet | strict | CLEAR | 0 |
| two-hdm-a | default | HALT_FOR_SIGNOFF | 0 |
| two-hdm-a | strict | HALT_FOR_SIGNOFF | 5 |
| dark-su3 | default | ROUTE_TO_ANALYTIC | 0 |
| dark-su3 | strict | ROUTE_TO_ANALYTIC | 0 |
| dark-su3-confining-synthetic | default | HARD_HALT | 0 |
| dark-su3-confining-synthetic | strict | HARD_HALT | 6 |

---

## Acceptance criteria status

- [x] `pytest tests/integration/ -v` exits 0; 1 passed (smoke test)
- [x] `ls intel/ws5_spike_*.json | wc -l` >= 6 (actual: 10; 8 current + 2 error stubs)
- [x] `intel/ws5_spike_findings.md` exists with D-class and R-class findings
- [x] Fixture banner contains REGRESSION-ANCHOR, 25000, Planck target
- [x] `dark-su3-confining-synthetic` in fixture constraints.yaml
- [x] All 8 current spike outputs exist and are valid
- [x] Synthetic strict: verdict=HARD_HALT, exit_code=6
- [x] dsu3 default banner: three-substring assertion passes

---

## OOS guard verification

Zero edits to:
- `plugins/workflow/skills/model-router/scripts/model_router/` (router source)
- `plugins/hep-ph-demo/skills/_shared/{constraints,analytic_exceptions,blocker_catalog}.yaml`
- `plugins/hep-ph-demo/skills/_shared/assets/{singlet_doublet,2hdm_a,dark_su3}.yaml`
- `plugins/constraints/skills/dark-matter-constraints/` (any file)

Only fixture files edited (in scope per plan):
- `tests/fixtures/registries/analytic_exceptions.yaml`
- `tests/fixtures/registries/constraints.yaml`
