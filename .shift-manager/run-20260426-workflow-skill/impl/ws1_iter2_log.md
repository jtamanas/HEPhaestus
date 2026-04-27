# WS1 Iter 2 Log

B2: restored outputs: field in singlet_doublet.yaml + two_hdm.yaml — 6 starter-template tests now PASS (551e267)
B3/S10: removed 11 stale xfail markers from test_modelspec_schema.py — all 22 tests now PASS (32833d9)
B4/CQ4: _apply_outputs_shim+_apply_sm_defaults return deep-copies; rule-5 logic bug fixed (5ad7b65)
B5/S16: renamed 3 duplicate blocker codes; test_blocker_class_map.py added (3 tests pass) (7d55777)
S7: two_hdm_a.yaml migrated — v2, provisional, loop-only-CP-forbidden DM, exit 0 --strict (e759117)
S8: dark_su3.yaml migrated — v2, Higgsed-partial, V+Psi candidates, analytic_exception ref case (6a12c66)
S9: dark_su3_confining.yaml migrated — v2, archived, unbroken-confining, composite DM (92f7db7)
S14: test_specs_pass_validator.py added — 5 specs CI gate, all pass (a4d002b)
S11/S12: taxonomy.py + 38 tests — read_axes, read_dm_phenomenology, analytic_exception_triggered (7ec546b)
S13/S15b: analytic-exception trigger + outputs-shim tests — 9 tests (0414715)
FULL SUITE: 855 passed, 4 pre-existing failures, 0 WS1 failures; time_budget exit 0 all 3 models
