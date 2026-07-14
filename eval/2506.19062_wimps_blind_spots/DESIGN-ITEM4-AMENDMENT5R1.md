# DESIGN-ITEM4-AMENDMENT5R1 — X CONFIRMED; execution order for the consequences

Amends AMENDMENT5.md. Verdict against the pre-registered criteria: **branch X
CONFIRMED.** Q1: rotated-3op on M_tri = +1.696e-10/+8.25e-11/−1.742e-10,
matching full-minus-box linearity. Q2 (decisive, quantitative): crossed share
of ‖M_tri‖ = 0.7071; crossed-part unrotated O_S leakage −1.2848e-7 with
crossed+direct reproducing the fixture EXACTLY at every θ; rotated crossed
~1e-15. Q3: synthetic crossed S⊗S (c_known = −1.6039386856819102e-8, two
independent determinations) recovered to 1.77e-21/2.25e-22 — Y1 exonerated by
eleven orders. Y2 pre-answered green (80-cfg vs 1104-cfg ~1e-12). The fixture
is, quantitatively, the unrotated crossing artifact.

## R1 — Fixture re-label (committed verbatim, adjacent to the pinned value)
"REGRESSION FIXTURE (instrument pin, NOT physics): −1.2831509485455282e-7 is
the unrotated forward 3-op reading of M_tri. Measured (AMENDMENT5 Q2,
2026-07-13): this value is quantitatively the O_S leakage of M_tri's unrotated
Majorana-crossed monomials (crossed share 0.7071 of ‖M_tri‖; crossed-part
leakage −1.28485e-7; direct part +1.696e-10). It pins bit-stability of the
frozen unrotated code path; it is not a physical coefficient. Physical scalar
readings come from the rotated lineage (AMENDMENT5R1)." Bit-identity REMAINS a
merge criterion in this regression role.

## R2 — C_Q re-derivation and the bracket
C_Q(θ) := [rotated-3op S⊗S reading of M_tri(θ)] / m_q(flavor), carrying the
±6e-10/m_q band. Canonical: +1.696e-10/4.67e-3 ≈ +3.63e-8 ± 1.28e-7 —
CONSISTENT WITH ZERO; the sidecar flags it so, and −2.75e-5 is VOID with a
history note. The two-value σ_SI bracket is RETAINED (it is now the honest
band statement: width ≈ the C_Q-band's f_N weight, no longer a 100× spread);
the floor at this point is provisionally twist-2-dominated pending P3.
Cross-flavor C_Q equality guard re-scoped: the <1e-6 RELATIVE bar is
meaningless at noise scale — it applies only when |C_Q| > 10× its band;
below that the bar is ABSOLUTE (<6e-10/m_q difference).

## R3 — Reopen-trigger share re-measurement: runs NOW, before/parallel to P3
One kernel leg: recompute f_N terms with the re-derived C_Q and rotated
readings; re-evaluate the trigger on the new shares. Prediction (falsifiable):
the gluon term collapses, twist-2 becomes the dominant share, and its 11.5%
v-drift STILL trips the trigger → the stayed v/10-matched-kinematics retest
(AMENDMENT4 Ruling 2) proceeds as pre-registered. If no >1%-share coefficient
drifts >1%, the trigger clears and the retest is cancelled with the
measurement cited. P3 has no dependency on this leg and may run in parallel
(different owner, different files).

## R4 — Falsifier re-pose: P3 protocol and bars
Growth-vs-θ is VOID (both lineage readings θ-flat; the old denominator was the
artifact). Scalar validation = P3: transcribe Hisano 1104.0228 gH (and gT1+gT2
for a free second axis) into eval benchmarks/ (A2 validation path ONLY, cited
by equation), evaluate at OUR parameters in the pure-doublet limit; run the
pipeline at MS = 3 TeV and 10 TeV (m_χ → MPsi = 500, d-quark, same y).
Pre-registered bars: |C_scalar_ours/C_Hisano| ∈ [0.2, 5] at BOTH legs, same
sign, AND twist-2 within the same band → the rotated ~1e-10-scale lineage is
CONFIRMED physical and +1.66e-10 is promoted to a validated reading. Note the
denominator is valid here: Hisano's pure-doublet gH is definitively nonzero —
if our rotated C_scalar sits at noise scale at MS=10 TeV too, P3 FAILS →
the amplitude M itself is missing real content (assembly-level, NOT the
read-off — Q3 stands); that outcome reopens the FormCalc/DD-expansion chain
as a construction error with a fresh design round. Fig.-1 ×3 remains the
σ_SI-level anchor for shipping.

## R5 — Audit list (named in the committed STATUS note)
(a) F3 fixture + A6 triangle-continuity → regression-only (R1 text).
(b) C_Q = −2.75e-5, its 2.09% v-drift row, and the round-2 withheld bracket
arithmetic (gluon −5.62e-6) → VOID. (c) AMENDMENT3/4 falsifier ratios
(7.3e-4/7.9e-4/1.5e-3) → measured artifact-vs-noise, void as physics; the
round-2 "FAILED falsifier" verdict stands as an INSTRUMENT finding (it caught
X). (d) Item-3/DESIGN-ITEM4 "triangle-only C_scalar −1.28e-7 already stable"
prose → instrument-stable, not physics. (e) G1b triangle–box interference-sign
anchor → must use rotated readings. (f) run_dd_triangle_continuity.wls claims
+ si_shift history entries → re-labeled per this account. Unchanged verdicts:
−2.0973e-7 artifact (round 3), Gram cure, all engineering guards.

## R6 — PR #36 proceeds to merge-prep NOW
STATUS note states X CONFIRMED with the Q1/Q2/Q3 evidence, R1 re-label, R5
audit list, and the AMENDMENT4-deduction retraction. Merge criteria otherwise
per AMENDMENT4 Ruling 3, with "AMENDMENT4 committed" extended to amendments
4, 5, and 5R1. Fresh reviewer confirms; no self-grading; the R3 leg and P3
are round-3 work on new branches, not merge blockers.
