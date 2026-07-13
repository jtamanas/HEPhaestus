# DESIGN-ITEM4-AMENDMENT2 — crossing-sector ruling (post PR #35 re-review)

Amends AMENDMENT.md after pr35-rereview/REVIEW.md. Accepted as established: the
committed 27-op basis was rank 12 (cond 4.1e5, D_Vq_Ac ≡ D_Aq_Vc, 7 null
pseudoscalar columns); a control-validated 256-op χ⊗q basis still leaves 0.206
because M carries mixed⊗mixed chain-product monomials (probe2-6). My
AMENDMENT.md probe-3 dichotomy is retracted: "persistence O(1) confirms (i)"
was invalid — persistence was only ever measured against incomplete bases, and
frozen coefficients cannot create content orthogonal to a genuinely complete
local basis. The (ii)-family diagnosis survives in corrected form: the residual
is projector basis-incompleteness (crossing sector), not kinematics.

## Ruling 1 — Fierz-rotate the mixed chains; do NOT add mixed⊗mixed columns

**Decision: rotation.** The decisive argument is not double-counting but
**guaranteed undercounting**: M's mixed⊗mixed monomials (F5*F6 etc., ~20% of
‖M‖, produced by FormCalc's own rearrangement of genuine box/triangle content)
contain SI-scalar strength under the exact Fierz identity. A fit with
mixed⊗mixed reference columns matches those monomials perfectly (constant
coefficients — they are M's own monomials), parks them there, and the physical
scalar content inside them NEVER reaches C_scalar → a finite, green-guarded,
systematically-low floor. Additionally the rotated images partially overlap the
direct columns, degrading conditioning. Rotation instead moves that content
into the χ⊗q sector where the scalar⊗scalar component lands in C_scalar, keeps
the basis interpretable, and leaves the SI extraction machinery unchanged.

**Realization (mechanical, self-verifying — no physics trusted from memory):**
in `sd_projection.wl`, rewrite each mixed⊗mixed monomial
(ū_χ A u_q)(ū_q B u_χ) into Σ_ij c_ij (ū_χ Γ_i u_χ)(ū_q Γ_j u_q) with c_ij
computed by 16-Γ trace completeness in Mathematica (an algebraic identity
evaluated by the machine, not a transcribed result — norms-clean by the A2
boundary). Momentum insertions ride along as part of A/B. **Rotation-exactness
guard (hard):** on every sample config, the rotated expression must equal the
original monomial's numeric value to < 1e-12 relative, else
`SD-FIERZ-ROTATION-INEXACT`, Exit 3. The identity is checked by evaluation
every run, never trusted.

**Conditioning requirements (hard guards, all pre-fit, all Exit 3):**
1. `SD-PROJECTION-BASIS-RANK-DEFICIENT`: numerical rank (SVD, tolerance
   σ_min/σ_max stated in the message) of the design matrix must equal the
   column count; on failure, name the null-space combinations (this alone
   would have caught rank-12-of-27 and the D_Vq_Ac ≡ D_Aq_Vc pair).
2. Null/collinear column detection: any ‖column‖ < 1e-12·‖matrix‖ or pairwise
   collinearity > 1−1e-10 is named and fatal (the 7 zero pseudoscalar columns
   are a sampling or construction defect to FIX, not silently drop).
3. Cond bound: cond(design matrix) < 1e4 on the retained basis. (Note 4.1e5
   would have passed a lax 1e6 bound — the rank test is the load-bearing
   guard; cond is secondary.)
4. **Per-column identifiability control:** for EVERY basis column, a synthetic
   amplitude with known coefficient in that direction must be recovered to
   < 1e-10 with cross-talk < 1e-10 (extends the R2 fixture to all columns). A
   rank-deficient basis can never silently measure again: it fails its own
   control before touching live data.

## Ruling 2 — Per-config kinematics: DEMOTED, not dead; two reopen triggers

Frozen coefficients are logically excluded as a source of *residual* (cannot
produce content outside a complete basis) — that work item is removed from
stage 0. But frozen-vs-config kinematics can still *bias coefficient values*
(the c_ab are DD-limit by design; the probes are finite-v). **Decision rule,
pre-registered:** reopen per-config kinematics if, AFTER the rotation + a
rank-verified basis, either (a) full-basis completeness residual > 1e-6
(something remains un-spannable), or (b) the v→v/10 drift of C_scalar exceeds
1% (value-bias, the probe-1 15% drift, survives the basis fix). Neither
trigger → the item stays closed.

## Ruling 3 — Pre-registered post-fix predictions and refutation bounds
(canonical point, d-run, rotated amplitude, rank-verified basis)

- **Completeness residual: predict < 1e-10.** M is a finite constant-
  coefficient combination of its monomials; rotation maps every monomial into
  the spanned sector exactly (guard-verified per config); the fit machinery
  recovers controls at 6.3e-14. **Refutes the basis-defect diagnosis:
  residual > 1e-6** with rotation-exactness and rank guards green → reopen
  hypothesis (i) per Ruling 2.
- **C_scalar: predict within [0.5, 5]×1e-7 in magnitude**, differing from the
  pre-rotation direct-sector −2.10e-7 by the mixed-sector Fierz contribution
  (sign not predicted — ~20% of ‖M‖ is mixed, but its scalar component is not
  pre-computable by hand under the norms). **Refutation: |C_scalar| > 1e-6 or
  < 1e-8**, or triangle-only no longer reproducing −1.2831509485455282e-7
  (the F3 fixture — rotation must not move the triangle sector's direct
  monomials), → construction error, stop.
- **si_shift (3-op vs full-basis C_scalar): predict < 1%.** Persistent
  shift > 10% → out-of-span overlap contamination is real and the 3-op fit is
  retired in favour of the full-basis fit as production.
- **v-drift: predict < 1%** if the probe-1 15% drift was defective-basis
  conditioning; > 1% → Ruling-2 trigger (b) fires.

## Ruling 4 — A6 bars survive; "full basis" re-derived; one bar added

Retained unchanged: full-basis completeness **< 1e-8**, si_shift **< 1%**,
v-drift **< 1%**, and all prior A6 criteria (UV/scale, A1-V, triangle fixture,
Majorana diagnostic, anchors, sigma_provisional). Re-derivation (RF2): "full
basis" now MEANS the rotated amplitude fitted against the rank-verified,
identifiability-controlled direct-sector basis — reachable by construction,
so the bar is a genuine guard, not an unreachable one; rename the label from
"Fierz-complete" to "rotated-complete" in code and sidecar. **Added bars:**
rotation-exactness < 1e-12 per config, and the Ruling-1 conditioning guards
green, as shipping preconditions. Honest carry-over (RF-minor-1): the rank-2
dd-expansion accuracy remains percent-level, acceptable against the ×3–5
anchor bands but must stay flagged in the sidecar until the Hisano anchor
adjudicates it. Reconcile the two contradictory committed texts on 0.669
(RF-minor-2) to this document's account: 0.669 was an instrument artifact of a
rank-12 basis; it carries no physics meaning.
