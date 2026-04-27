VERDICT: FAIL
MODEL_SOURCE: hand_crafted_sarah_model_fixture
RENDERER_STATUS: debt

## Summary

PT1 completed with Omega h^2 = 10.494 (target band [9.95, 10.36]); deviation +3.4% above upper bound.
Dominant annihilation channel: chichibar_wphp + chichibar_wmhm (gauge, 99.2%) rather than chichibar_bbx (0.65%).

### Gate Evaluation (G1-G10)

| Gate | Status | Evidence |
|------|--------|----------|
| G1: omega_in_band [9.95,10.36] | FAIL | Omega h^2 = 10.494 (+3.4% outside band) |
| G2: bbx >= 30% | FAIL | chichibar_bbx = 0.65% (dominant channel is gauge W+H-) |
| G3: Wchi=0.0 | PASS | DECAY 9989932 0.000000e+00 confirmed |
| G4: PHASES[1]=1.0 sentinel | PASS | Line 214: rpchiR = 1.000000e+00 |
| G5: .patched marker | PASS | demo_output/2hdm-a/playtest_log/.patched present |
| G6: mtime sentinel | PASS | param_card.dat newer than .output_marker |
| G7: finite Omega h^2 | PASS | 10.494 (not -1.0 sentinel) |
| G8: MadDM ran | PASS | run_04 complete, MadDM_results.txt written |
| G9: SARAH MakeUFO | PASS | TwoHdmAfix UFO at SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/ |
| G10: schema validates | PASS | test_summary_schema.py: [PASS] 2hdm-a |

### Root Cause

Blocker 2hdma-001: patch_paramcard.py regex bug prevents updating positive-valued DMSECTOR/PHASES/ZAMIX entries on first-run fresh MG5 cards (regex `(?!\d)` lookahead fails for values starting with digits). Required manual param_card fixes. After fixing: PHASES[1]=1.0, DMSECTOR gchi=1.0, ZAMIX analytically set.

Warning 2hdma-003: With correct ZA mixing (singlet-dominated Ah2 at theta_a=0.1), the b-quark Yukawa coupling to Ah2 is suppressed by factor sin(theta_a)*cos(beta) ~ 0.010. The Ah2-W-H gauge coupling dominates. Expected bbx~60% channel breakdown incompatible with current ZAMIX parametrization.

### Recommendation

Fix patcher regex (2hdma-001) before re-playtest. Investigate whether iter-8's 10.15 result required different ZAMIX (possibly theta_a closer to pi/2 or different Ah2 mass assignment). The pipeline infrastructure (SARAH->UFO->MadDM) is confirmed working end-to-end.
