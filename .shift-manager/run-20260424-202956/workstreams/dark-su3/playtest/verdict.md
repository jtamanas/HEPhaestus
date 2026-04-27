VERDICT: FAIL
MODEL_SOURCE: analytic_compute_dark_su3
RENDERER_STATUS: n/a

## 5 Primary Criteria

1. PRIMARY-1 Pipeline connectivity: PASS — Omega_V=33.307>0, Omega_Psi=2995.557>0, relic_approx=False, sigmav_approx=True
2. PRIMARY-2 summary.json schema-valid: PASS — jsonschema validation against summary.schema.json: no errors
3. PRIMARY-3 BP1 bands at n=200: PASS — Omega_V=33.307 in [31.6,35.0], Omega_Psi=2995.557 in [2846,3146]
4. PRIMARY-4 Convergence baseline locked: PASS — n=200/400/800 all float64-identical, 0.00% drift
5. PRIMARY-5 iter-5 guard: PARTIAL — analytic compute functional; time_budget.py outputs BLOCKED (expected); plan G5 READY assertion is a spec mismatch (dsu3-003 minor)

## Banner Check: FAIL (MAJOR)

Banner absent: "NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Omega_tot h2 approx 0.12) is out of reach this run; values reported are regression-anchors, not physics targets."
Issue dsu3-002: blocker / docs / auto_fixable=true

## Drift Smoke Check: PASS

n=400/800 vs n=200: 0.00% drift (float64-identical; expected per dsu3-fix-scope.json weak_drift_gate_note)

## Paper-Fidelity Gap: MAJOR

Omega_naive=3029 vs paper 0.12: ~4 OoM. Cause: sigmav_approx=True.
Issue dsu3-004: major / physics / auto_fixable=false / NOT in Phase 2 docs-fix-loop scope.
Banner (dsu3-002) is the UX mitigation. Not conflated with banner issue.

## Issues Summary (see issues.json / issues.jsonl)

- dsu3-001: BLOCKER / docs / auto_fixable — stale "Confining dark sector" at SKILL.md:73, constraints.yaml:148, MANUAL_WALKTHROUGH.md:90
- dsu3-002: BLOCKER / docs / auto_fixable — banner template absent from all skill files
- dsu3-003: minor / docs — plan G5 READY assertion conflicts with time_budget.py output contract
- dsu3-004: major / physics / NOT auto_fixable — ~4 OoM paper-fidelity gap from sigmav_approx=True

## Phase 2 Disposition

Blockers dsu3-001 + dsu3-002 both have fix_scope=docs and auto_fixable=true.
No blockers with fix_scope in {physics, build, test, schema, cross_workstream}.
Phase 2 docs-only fix-loop: ELIGIBLE.
