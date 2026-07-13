# DESIGN-ITEM4-AMENDMENT — round-2 redirect ruling (post PR #35 review)

Amends DESIGN-ITEM4.md after pr35-review/REVIEW.md refuted the A-R2 velocity-gap
reading. Accepted as established: the A1 box expansion cures the Gram pole
(box max|c| 1.17e28 → 1.82; expanded-box C_scalar = −8.14e-8, and note
−1.283e-7 + (−8.14e-8) = −2.10e-7 = probe-1's full-amp fit — internally
consistent); the ~1.0 completeness residual is velocity-pinned (sixteen nines
across v → v/100) and COMMON to the triangle-only sector (1 − 3e-16,
REVIEW.md probe 2, already in VERIFY.md:45-46).

## Ruling 1 — Diagnosis: (ii)-dominant, (i) refuted as dominant BY PROBE 1; one
cheap prescribed test settles it and bounds contamination

**Decision.** The working diagnosis is hypothesis (ii): the residual is
predominantly **genuine physical Dirac content the 3-operator SI basis cannot
hold** — leading candidate the axial×axial (SD) structure, plus anapole/
pseudoscalar. Hypothesis (i) (frozen-coefficient vs off-axis-chain
inconsistency) is **refuted as the dominant source by probe 1 itself**: as
v → v/100 the sample configs approach the very kinematics the coefficients are
frozen at, so any mismatch-generated content must fall with v; the residual is
pinned. What survives at v→0 with O(1) matrix elements is exactly spin-spin
(axial×axial) content — velocity-independent, present in BOTH sectors (Z-/W-
mediated triangle and box pieces), and parametrically enormous relative to the
blind-spot-suppressed SI scalar. ‖SI‖/‖M‖ ~ 1e-8 in norm reproduces the
observed 1 − O(1e-16) residual arithmetic. [VERIFY: probe 3 below confirms the
A×A identification; do not hard-code it before the run.]

**Reconciliation (harmless vs contaminating).** Least squares extracts the
component of M along each basis column; a large orthogonal residual does not
corrupt C_scalar *if* the out-of-span content has small overlap with the basis
on the sample set. The stable, physical C_scalar (−1.28e-7 triangle, −8.1e-8
box, sum matching the full fit) is evidence the overlap is small — but probe
1's 15% C_scalar drift at v/100 (−2.10e-7 → −1.80e-7) is either genuine
contamination or twist-2-column ill-conditioning at small v, and MUST be
resolved, not assumed away.

**Prescribed test (probe 3; one kernel run, machinery exists from PR #33).**
Extend `$opRefs` with the Fierz-complete χ⊗q bilinear reference set
(S,P,V,A,T on each line, parity-odd included) and re-fit the CURED amplitude
(triangle-only, expanded-box-only, full):
- Residual collapses (< 1e-8): (ii) confirmed; record WHICH operators absorb
  it (expect A×A dominant) in the sidecar as diagnostics.
- Residual persists O(1): (i) is real after all (frozen-coefficient content is
  un-spannable by ANY local basis) → then and only then, move to per-config
  consistent kinematics (PV coefficients evaluated at each config's actual
  S,T — ~80 LoopTools evaluations, feasible).
- Contamination bound: |C_scalar(3-op) − C_scalar(full-basis)| / |C_scalar|
  reported; > 1% means the 3-op extraction was silently polluted and the
  full-basis fit becomes the production fit.

## Ruling 2 — Norms: reference operators YES, sampling blinding NO

Adding pseudoscalar/tensor/axial REFERENCE operators to the projection basis is
**measurement instrumentation, not an extension of the physical operator set**,
and is PERMITTED. The roadmap's "do NOT extend the operator set" (verified
precondition) forbade interpreting the Gram-poled residual as physics and
feeding new operators into σ_SI. The boundary, stated as a rule: only
{C_q scalar, C_q^(1,2) twist-2, C_G} may ever reach the nucleon matching;
every other fitted coefficient is a diagnostic, emitted in the sidecar
(`out_of_span_diagnostics`), never matched, never quoted as a cross-section.
(The A×A coefficients are real SD physics, but σ_SD matching is out of scope —
match_nucleon.py already hard-refuses SD couplings.)

Changing the SAMPLING to parity-even/q²→0 configs as the fix is **REJECTED**:
it manufactures a green completeness guard by choosing samples where unmodeled
content vanishes — the exact "false clean fit" `sd_projection.wl:194-198`
warns against. Sampling changes are allowed only for conditioning (e.g. a
second velocity scale to stabilise the twist-2 column), never to hide content.

## Ruling 3 — A6 completeness bar, amended (stronger guard, not looser)

The old bar ("3-op residual < 1e-4") assumed the amplitude is SI-only — wrong
in expectation for any amplitude with Z/W content, and it would NEVER go green.
Replace with three conjunctive criteria, all load-bearing:
1. **Full-basis completeness < 1e-8**: the Fierz-complete reference basis must
   span the cured amplitude to numerical precision. Residual above this =
   structural error (un-spannable content, hypothesis (i), or a projector bug)
  → loud `SD-PROJECTION-INCOMPLETE`, nothing ships. This is STRICTER than the
   old guard: nothing can hide as "expected residual".
2. **SI-extraction stability < 1%** between the 3-op fit and the full-basis fit
   (the contamination bound of Ruling 1).
3. **Velocity stability < 1%** for C_scalar and C_twist2 under v → v/10,
   evaluated on the FULL-basis fit (retained from A6; the probe-1 15% drift
   must be shown to be conditioning and cured, or it blocks shipping).
All other A6 criteria (UV/scale residues, A1-V, triangle continuity, Majorana
diagnostic, external anchors, sigma_provisional policy) stand unchanged.

## Ruling 4 — A4/A5 scope unchanged; ordering re-staged; O(v) motive dropped

Per-flavor u,d,s runs, the C^(1)/C^(2) split, and the nucleon contraction keep
their DESIGN-ITEM4 scope. Two changes:
- **Drop the O(v) twist-2 coefficient expansion as a residual fix** (REVIEW.md
  F1.1: twist-2 is already a basis direction; refining its coefficient cannot
  move an orthogonal residual). The C^(1)/C^(2) split survives only as its A5
  purpose: two twist-2 reference operators so the split is resolved for
  matching.
- **New stage 0 gates round 2.** Nothing in A4/A5 starts until, on the d-run:
  (0a) probe 3 run and Ruling-1 outcome recorded; (0b) projector basis
  completed per Ruling 2 with the three Ruling-3 criteria green; (0c) the
  review's debts fixed: F2 — A1-V must validate the PRODUCTION path
  (`ddIntU`/`ddBoxHead`) at the CONTRACTED level (Σ c_ij·components vs direct
  LoopTools at 3 points along a non-zero-Gram path with Gram/scale³ ∈
  [1e-3, 1e-1], convergence toward the reconstruction within a stated
  cancellation-error budget [VERIFY budget from the observed component
  magnitudes]), the Hisano pure-doublet anchor remaining the independent
  physics check; F5 — tensor-survivor guard moved to the SYMBOLIC amplitude
  (pre-mkNum) + a test that actually drives Exit[3]; F3 — triangle-continuity
  committed with a full-precision pinned fixture; F4 — EXCISE the dead
  mass-derivative branch and hard-error `SD-DD-DOUBLED-OFFSET-UNSUPPORTED` if
  a doubled offset is ever hit (a latent silent-zero derivative is worse than
  a loud unsupported case; reinstate only with its own LoopTools cross-check).
Order: stage 0 → per-flavor runs → nucleon contraction (A5) → anchors.
