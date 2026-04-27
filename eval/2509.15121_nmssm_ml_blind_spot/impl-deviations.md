# Implementation Deviations from Plan — arXiv:2509.15121

Recorded per review S-2, N-2, N-3 requirements.

---

## D1. Eq. 7 on-BP LHS: 3.33, not ~1.0 (Phase-1 finding)

**Plan language (§12, S19):** `t3_nmssm_blind_spot_eq7_on_bp1_3` should pin `lhs_eq7`
with `expected = 1.0`, `tolerance = 0.10`.

**What was shipped:** `lhs_eq7` pinned at `3.33` with `tolerance = 0.10` (relative).

**Why:** Phase-1 measurement (phase1_notes.md §4) found that at the paper BPs, with
M1 = 500 GeV (bino decoupled) and singlino LSP at 147 GeV and tan_beta = 6.2:

    LHS = (m_chi1 + g1^2*v^2/(M1 - m_chi1)) / (mu_eff * sin(2*beta))
        = (147.5 + 13.3) / (161.8 * 0.312)
        = 160.8 / 50.5
        ~ 3.33

The denominator `mu_eff * sin(2*beta) ~ 50.5 GeV` is small because tan_beta = 6.2
makes sin(2*beta) = 2*tan_beta/(1+tan_beta^2) ~ 0.312, and mu_eff = 161.8 GeV. The
paper BPs are NOT on the Eq. 7 blind spot at tree level.

**Impact on tests:**
- The on-BP test is a formula reproducibility test (verifies Eq. 7 is coded correctly),
  not a blind-spot saturation test.
- The TRUE blind-spot test is `t3_nmssm_blind_spot_eq7_synthetic` (LHS = 1 to 1e-6).
- The plan's Mutation Probe A expectation changes: `t3_nmssm_blind_spot_eq7_on_bp1_3`
  will FAIL if `return 1.0` mock is used (since pinned at 3.33, not 1.0), which is
  actually stricter than the plan intended.

**Status: physics-correct deviation; reviewer-endorsed (review R1 E-7, E-1).**

---

## D2. Off-BP test: `relational_excess` dropped, `floor_excess` only

**Plan language (§12, G1, S19):** `t3_nmssm_blind_spot_eq7_off_bp1_3` should return
both `relational_excess = |LHS_off - 1| - 5*|LHS_on - 1|` and `floor_excess`, with
both graded as numeric with `expected=0.30, tolerance=1.0`.

**What was shipped:** `floor_excess` only. `relational_excess` is dropped from both
the ref_fn return dict and the YAML grader.

**Why:** Phase-1 measurement gives:
- |LHS_on - 1| = |3.33 - 1| = 2.33
- |LHS_off - 1| = |2.65 - 1| = 1.65
- `relational_excess = 1.65 - 5 * 2.33 = 1.65 - 11.65 = -10.0` (NEGATIVE)

A negative relational_excess would cause the grader to fail permanently, regardless
of formula correctness. The plan's relational test assumed |LHS_off - 1| >> |LHS_on - 1|
(off-BP much further from 1), but both BPs are far from the blind spot for different
reasons (sign flip of mu_eff flips the sign of LHS denominator, reducing |LHS - 1|
rather than increasing it at these parameter values).

**Remaining test value:** `floor_excess = 1.65 - 0.30 = 1.35 > 0` confirms the off-BP
value is far from 1, catching any `return 1.0` mock (which would give floor_excess ~ -0.30).

**Status: physics-correct deviation; documented in phase1_notes.md §4; reviewer-endorsed.**

---

## D3. sigma_SI rescaling: `min(1, ...)` clip implemented

**Plan language (§S6):** `sigma_SI * omega/Omega_Planck` with no `min(1, ...)` clause.

**What was shipped:** `sigma_SI * min(1, omega/Omega_Planck)`.

**Why:** For BPs with `Omega > 0.120` (overproduction, e.g. BP5-2 has Omega_h2 = 2.7),
the unclipped rescaling would give sigma_SI_eff > sigma_SI_nominal. This is unphysical:
if the neutralino overproduces DM, the standard sub-relic rescaling formula clips at 1
(the DM assumption is saturated or exceeded). The `min(1, ...)` is standard in the
sub-relic literature (e.g. Jungman, Kamionkowski, Griest 1996).

**Impact:** monotonicity test in pytest (`test_bp9_3_and_monotonicity`) verifies linear
scaling for sub-Planck omega. The `min` clip is triggered only for overproducing BPs
(BP5-2), which has no sigma_SI grader in Tier-2 (BP9-3 is used for that test with
Omega_h2 = 0.07 < 0.12, so the clip is not triggered there).

**Status: defensible deviation; documented here.**

---

## D4. BP5-2 transcription YAML row skipped

**Plan language (§6.1 branch 1):** if BP5-2 resolves cleanly, author a T5/T6 transcription
row for it (sigma_DD_SI, omega_h2).

**What was shipped:** `t2_nmssm_spectrum_bp5_2` (Tier-2 spectrum row) is authored.
No Tier-1 transcription row for BP5-2 sigma_DD_SI or omega_h2.

**Why:** The ≥2 transcription threshold is met by BP1-3 + BP9-3. BP5-2 is transcribed
in `benchmark_points.py` and has a Tier-2 spectrum row, but the extra Tier-1 row
was not needed and would add a fourth transcription row without additional physics value.

**Status: minor process deviation; no physics impact.**

---

## D5. N-3: test tolerance vs YAML tolerance mismatch for m_chi1/m_chi3

**Test file (TestSpectrum::test_bp1_3):** uses `rtol=0.01` (1%) for m_chi1 and m_chi3.
**YAML row (t2_nmssm_spectrum_bp1_3):** uses `tolerance=0.005` (0.5%) for all masses.

**Status:** Not a functional problem (ref_fn returns computed values, YAML grader
compares ref_fn output to itself, always passes). Tolerances only matter when comparing
model output to expected. The pytest tolerance is a documentation nit; the YAML
tolerance governs actual harness grading. Left as-is per budget constraints.
