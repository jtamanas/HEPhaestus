# STATUS-ITEM4 — loop-floor scalar extraction (frozen at PR #36)

Status note required by DESIGN-ITEM4-AMENDMENT4.md Ruling 3 criterion (2)
and Ruling 4, finalized per DESIGN-ITEM4-AMENDMENT5R1.md (X CONFIRMED). This is the committed, load-bearing summary; the PR #36 body
carries the full measured-vs-predicted tables.

## Falsifier verdict (AMENDMENT3 Ruling 3 HARD GATE): FAILED

- Fixture half: PASSED — the canonical triangle fixture is bit-identical
  (C_scalar(tri) = -1.2831509485455282e-7, tri-runner reproduction).
- Growth half: FAILED at BOTH off-blind-spot points —
  |C_scalar_full|/|C_scalar_tri| = 7.32e-4 at theta = -0.076 and 1.487e-3
  at theta = -0.304 (canonical 7.9e-4), against the 0.1 bar. The
  triangle-vs-box scalar cancellation is theta-INDEPENDENT: not blind-spot
  physics. Cross-instrument was green at every point, which is NOT a
  defense (all three instruments share M and the sample set; agreement at
  |C| ~ 1e-10 under a 6e-10 absolute floor is trivially green).
- Adjudication: construction-error STOP clause, upheld through the probe
  ladder. FINAL DISPOSITION (AMENDMENT5R1): the FAILED verdict stands as an
  INSTRUMENT finding — it is what caught branch X. The falsifier's
  DENOMINATOR (C_tri = -1.28e-7) was itself the artifact, so growth-vs-theta
  is VOID as a physics test (both lineage readings are theta-flat); the
  measured ratios (7.3e-4 / 7.9e-4 / 1.5e-3) are artifact-vs-noise
  measurements. Scalar validation is re-posed as P3 (Hisano x5) plus the
  Fig.-1 x3 sigma_SI anchor (AMENDMENT5R1 R4).

## What is and is not a validated number (Ruling 4)

No validated blind-spot C_scalar exists. -2.0973e-7 remains an instrument
artifact (round 3). +1.66e-10 remains an UNVALIDATED instrument reading
until the P3 Hisano anchor adjudicates the physics scale (X does not
rehabilitate it by itself — AMENDMENT4 Ruling 4 / AMENDMENT5R1 R4).
C_Q = -2.75e-5 is VOID (see the C_Q section below). Production coefficient
claims stay frozen pending P3 + the R3 share re-measurement. NO sigma_SI
may be quoted at any provenance level: sigma_provisional is insufficient,
and the bracket arithmetic in handoffs stays labeled
reviewer-orientation-only.

## AMENDMENT5: the AMENDMENT4 H1 deduction is RETRACTED; the fork is X/Y

AMENDMENT4's load-bearing deduction ("the box sector carries -C_tri")
mixed a ROTATED numerator (+1.66e-10) with an UNROTATED denominator
(-1.28e-7) and is formally retracted (DESIGN-ITEM4-AMENDMENT5.md; the
implementer's P1 catch is credited there). H1 and H2 are CLOSED; P2 is
WITHDRAWN. The remaining fork is in the TRIANGLE sector, where the two
instrument lineages disagree by ~1e3:
- Branch X: the fixture -1.2831509485455282e-7 is a probeH-class
  unrotated-crossing artifact of M_tri's crossed-monomial weight; the
  rotated ~1e-10 is the honest reading.
- Branch Y: the rotated read-off destroys real scalar strength (the
  coefficient READ-OFF is the one step rotation-exactness and
  completeness never test on crossed content).
BINDING regardless of branch (AMENDMENT5 Ruling 1): rotation is
monomial-level and sector-blind; the unrotated tri-runner is re-labeled a
REGRESSION instrument — its bit-identity keeps gating merges, its VALUE
carries no physics weight pending the fork. Probe ladder v2: Q1
(rotated-3op on M_tri, three theta), Q2 (crossing split of M_tri; crossed
share of ||M_tri|| < 1e-3 refutes X and convicts Y on the spot), Q3
(synthetic-amplitude identifiability control through the crossed path,
recovery bar < 1e-10; failure convicts Y1 read-off), then P3 (Hisano)
if still ambiguous.

BRANCH VERDICT (designer-confirmed, DESIGN-ITEM4-AMENDMENT5R1.md):
**X CONFIRMED** against the pre-registered criteria. Evidence
(probe-box/q12/{canon,A,B}/probe.log, probe-box/q3/probe.log):
- Q1 — rotated-3op fit on M_tri alone: +1.6962e-10 (canonical),
  +8.2534e-11 (theta_A), -1.7422e-10 (theta_B); each matches
  full-minus-box linearity to 4-5 digits (rot_err <= 4.3e-16; the ~1
  rel_resid is the expected tiny-scalar-on-twist-2-norm signature).
- Q2 (decisive, quantitative) — crossing split of M_tri: 16 monomials,
  2 crossed, crossed share of ||M_tri|| = 0.7071 at ALL theta (>> the
  1e-3 X-refutation bar). Crossed part unrotated O_S leakage =
  -1.28485e-7 / -1.30052e-7 / -1.17260e-7 — and crossed+direct reproduces
  each theta's fixture EXACTLY (e.g. -1.28485e-7 + 1.696e-10 =
  -1.28315e-7). Crossed part ROTATED O_S = ~1e-15 at all theta. Direct
  part = the Q1 value on both lineages.
- Q3 — synthetic crossed-path identifiability control: known S(x)S
  content c_known = -1.6039386856819102e-8 (two independent
  determinations: exact Dirac-trace projection, config-constant; and
  256-dictionary LS, agreeing to 3e-14 with resid 4.4e-15; plus a
  built-in null pair with exactly zero S(x)S). Full
  rotate-then-read-off recovery: |transfer - c_known| = 1.77e-21,
  |threeop - c_known| = 2.25e-22 — eleven orders under the 1e-10 bar.
  Y1 (read-off) exonerated.
- Y2 — pre-answered green: the driver's cross-instrument triples compare
  the 80-forward-config rotated-3op against the 1104-config transfer at
  all three theta; agreement ~1e-12-1e-13, far under the 10% bar.
The fixture -1.2831509485455282e-7 is, quantitatively, the unrotated
crossing artifact. The honest tri-sector scalar reading is the ~1e-10
rotated value (physical status pending P3).

## Fixture re-label (AMENDMENT5R1 R1, verbatim)

"REGRESSION FIXTURE (instrument pin, NOT physics): -1.2831509485455282e-7
is the unrotated forward 3-op reading of M_tri. Measured (AMENDMENT5 Q2,
2026-07-13): this value is quantitatively the O_S leakage of M_tri's
unrotated Majorana-crossed monomials (crossed share 0.7071 of ||M_tri||;
crossed-part leakage -1.28485e-7; direct part +1.696e-10). It pins
bit-stability of the frozen unrotated code path; it is not a physical
coefficient. Physical scalar readings come from the rotated lineage
(AMENDMENT5R1)." Bit-identity REMAINS a merge criterion in this
regression role. Applied in-repo at: test_dd_triangle_continuity.py
(adjacent to the pin), run_dd_triangle_continuity.wls (header),
run_eval_sd.wls and sd_projection.wl (fixture-contract comments),
DESIGN-ITEM4.md (banner), STEP3-DESIGN.md (G1b note).

## C_Q: -2.75e-5 VOID; re-derivation (AMENDMENT5R1 R2)

C_Q = C_tri(unrotated)/m_q = -2.75e-5 is VOID as physics — its numerator
is the crossing artifact above. HISTORY: it fed the round-2 withheld
bracket arithmetic (gluon term -5.62e-6), the twist-2-vs-gluon
near-cancellation reading, and the 2.09% v-drift reopen row; all three
are re-labeled instrument findings of the regression lineage.
Re-derivation: C_Q(theta) := [rotated-3op S(x)S reading of M_tri(theta)]
/ m_q(flavor), carrying the +-6e-10/m_q band. Canonical: +1.696e-10 /
4.67e-3 = +3.63e-8 +- 1.28e-7 — CONSISTENT WITH ZERO (sidecar-flagged).
The two-value sigma_SI bracket is RETAINED as the honest band statement
(width ~ the C_Q-band's f_N weight, no longer a 100x spread); the floor
at this point is provisionally twist-2-dominated pending P3. Cross-flavor
C_Q equality guard re-scoped: the <1e-6 RELATIVE bar applies only when
|C_Q| > 10x its band; below that the bar is ABSOLUTE (<6e-10/m_q
difference). The re-derivation + guard re-scope bind on the next leg
(R3 share re-measurement, separate owner).

## Audit list (AMENDMENT5R1 R5, verbatim)

(a) F3 fixture + A6 triangle-continuity -> regression-only (R1 text).
(b) C_Q = -2.75e-5, its 2.09% v-drift row, and the round-2 withheld
bracket arithmetic (gluon -5.62e-6) -> VOID. (c) AMENDMENT3/4 falsifier
ratios (7.3e-4/7.9e-4/1.5e-3) -> measured artifact-vs-noise, void as
physics; the round-2 "FAILED falsifier" verdict stands as an INSTRUMENT
finding (it caught X). (d) Item-3/DESIGN-ITEM4 "triangle-only C_scalar
-1.28e-7 already stable" prose -> instrument-stable, not physics.
(e) G1b triangle-box interference-sign anchor -> must use rotated
readings. (f) run_dd_triangle_continuity.wls claims + si_shift history
entries -> re-labeled per this account. Unchanged verdicts: -2.0973e-7
artifact (round 3), Gram cure, all engineering guards.

## SD-COEFF-IMAGINARY disposition (AMENDMENT5 Ruling 5, design final)

The bar |Im C|/|C| < 0.1 applies to the SHIPPING instrument's reading
(rotated-3op / contracted): measured ~1e-9 at all three theta — GREEN.
The transfer instrument's |Im|/|C| up to 0.53 is a NAMED sampling
artifact, exempt from the bar, reported in the sidecar. An O(1) Im on the
shipping reading remains fatal.

## Mechanism probes (AMENDMENT4 Ruling 1; verdicts committed with logs)

- P1 (box-sector projection at three theta): H1 REFUTED at ALL THREE theta
  (probe-box/{canon,A,B}/probe.log). Measured: production instruments on
  the BOX sector agree tightly at NEGLIGIBLE values — canonical
  -4.1389e-12 (triple -4.0617e-12/-4.1389e-12/-4.0716e-12, maxdiff
  1.36e-13), theta_A -2.0150e-12 (maxdiff 1.43e-13), theta_B +3.8496e-12
  (maxdiff 1.32e-13); |ratio to C_tri| ~ 1.6e-5 - 3.3e-5 (box-sector
  dictionary completeness 1.95e-8/2.06e-8/2.27e-8, ~2x the 1e-8 full-amp
  bar — reported as measured). The box does NOT carry -C_tri on the
  production lineage at any theta. On the UNROTATED 3-op fit the box
  carries the SAME sign as C_tri (additive, not cancelling):
  C_box/(-C_tri) = -0.634 (canonical), -0.621 (theta_A), -0.579 (theta_B);
  and unrotated threeOpFit(M_full) = -2.09730e-7 / -2.10728e-7 /
  -1.85408e-7 (linearity exact to ~1e-16) — the round-3 artifact scale,
  near-theta-independent. AMENDMENT4's load-bearing deduction compared a
  ROTATED C_full (+1.66e-10) against an UNROTATED C_tri (-1.28e-7): the
  "theta-independent box cancellation" DISSOLVES into an instrument-lineage
  discrepancy (unrotated 3-op vs rotated production) concentrated in the
  TRIANGLE sector (by linearity, C_tri on the production lineage is
  ~ +1.70e-10). Since probeH (round 3) adjudicated unrotated Majorana
  crossings as projecting SPURIOUS scalar and the rotation is exact to
  4.3e-16, the -1.28e-7 falsifier denominator came under artifact
  suspicion — confirmed as branch X by Q1/Q2/Q3 (see BRANCH VERDICT above;
  AMENDMENT5 closed H1/H2 and withdrew P2; no fix coded before verdict).
- P1b (head-class split of the box sector, all three theta): the unrotated
  box scalar is carried ~98% by DIRECT C0/B0/A0 heads inside box-carrying
  terms (canonical -7.986e-8, theta_A -7.938e-8, theta_B -6.700e-8); the
  DD-expansion classes nearly cancel each other (pinch-remnant -1.198e-8/
  -1.097e-8/-9.294e-9 vs genuine-D0 +1.042e-8/+9.588e-9/+8.323e-9; class
  sums exact to ~1e-23). The
  H1-flavored "duplicated triangle content in the box assembly" reading is
  NOT supported as a cancellation mechanism (nothing cancels -C_tri); the
  direct triangle content in box terms is same-sign additive.
- Imaginary-part diagnostic (SD-COEFF-IMAGINARY motivation, refined): the
  O(1) Im/Re lives in the TRANSFER instrument only (|Im|/|C| = 0.31/0.53/
  0.22 at canonical/theta_A/theta_B), while the rotated-3op and unrotated
  fits on M give |Im|/|C| ~ 1e-9 — the imaginary part is a transfer-
  sampling artifact, not amplitude content.
- P2 (unexpanded box at |T| = 1 GeV^2): WITHDRAWN by AMENDMENT5 — it
  targeted a cancellation that P1 showed does not exist.
- P3 (Hisano pure-doublet anchor, benchmarks/ only): not yet run; the A2
  production-path ban is absolute.
- Kinematics reopen (twist-2 11.5% v-drift at 11% |f_N| share, C_Q 2.1%,
  scalar abs 1.53e-8): the stay is superseded by AMENDMENT5R1 R3 — the
  f_N shares must be RE-MEASURED with the re-derived C_Q (the old shares
  were computed against the void gluon term) before the v/10-matched
  retest runs. R3 is a separate leg with its own owner; prediction on
  record: gluon collapses, twist-2 dominates, its 11.5% drift still trips
  the trigger.

## Guard repairs bound on the next leg (pre-registered, not yet enforced)

1. SD-SI-CROSS-INSTRUMENT-DISAGREE demoted to report-only whenever
   |C| < 10x its absolute floor (6e-9); independence henceforth requires a
   different evaluation path or physics lineage (P3; the P2 path was
   withdrawn with H2).
2. SD-COEFF-IMAGINARY: |Im C|/|C| >= 0.1 on the SHIPPING instrument's
   reading of any coefficient entering f_N becomes a named refusal
   (design finalized in AMENDMENT5 Ruling 5: shipping reading ~1e-9 GREEN;
   the transfer instrument's 0.22-0.53 is a named exempt sampling
   artifact, sidecar-reported). Its catalog entry lands together with its
   emitter (no-emitterless-codes norm, test_derivative_blocker_retired
   precedent).

## Definition of done (Ruling 5)

Under the confirmed X branch (AMENDMENT5R1): P3 Hisano anchor adjudicates
the rotated lineage's physics scale (x5 band, both MS legs, same sign;
R4 protocol) -> R3 share re-measurement + kinematics retest resolution ->
per-flavor u/d/s -> sigma_SI two-value bracket at canonical + 2 masses
with every guard green and the Fig.-1 x3 anchor met. Merges before that
are milestone records (instruments or refusals), never numbers.
