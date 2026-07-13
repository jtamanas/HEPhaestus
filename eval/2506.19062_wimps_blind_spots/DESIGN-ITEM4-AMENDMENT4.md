# DESIGN-ITEM4-AMENDMENT4 — falsifier STOP adjudication (post PR #36 round 2)

Amends AMENDMENT3.md after the Ruling-3 falsifier FAILED (PR #36 @ e5b1628).
Accepted: fixture half bit-identical (−1.2831509485455282e-7) at canonical;
|C_full|/|C_tri| = 7.32e-4 (θ=−0.076), 1.487e-3 (θ=−0.304), 7.9e-4 (canonical)
— the triangle-vs-box scalar cancellation is θ-INDEPENDENT, not blind-spot
physics; cross-instrument green at all points; SD-KINEMATICS-REOPEN-TRIGGERED
fired (twist-2 drift 11.5% at 11% |f_N| share, C_Q 2.1%, scalar abs 1.53e-8);
nothing shipped. The STOP clause is UPHELD: the production scalar extraction is
unvalidated. One correction to my own AMENDMENT3: its outcome dichotomy
(blind-spot physics vs instrument-made zero) was incomplete — a θ-independent
STRUCTURAL cancellation, physical or bookkeeping, fit neither branch. The
probes below close that hole.

**The deduction that ranks the hypotheses.** Rotation exactness (4.3e-16) means
the rotated amplitude IS M numerically; the fits therefore measured M
faithfully. threeOpFit(M_tri) = −1.28e-7 and threeOpFit(M_full) ≈ 1.7e-10
through the SAME arithmetic ⇒ the box sector of M carries scalar content
≈ −C_tri(θ) at every θ. Team-lead mechanisms (a) column leakage and (b) label
mismatch are thereby DEMOTED (not excluded — P1 still tests attribution): the
phenomenon is in M's box sector, i.e. amplitude assembly, DD expansion, or
genuine physics. The cross-instrument agreement is no mystery and no defense:
all three share M and the sample set, and at |C| ~ 1e-10 the 6e-10 absolute
floor makes agreement-at-noise trivially green (see Guard repairs). Corroborant
that the number is noise-floor residue: Im(C_scalar) ~ Re(C_scalar) at all
three θ — a below-threshold Wilson coefficient must be real.

## Ruling 1 — Ranked mechanisms, one pre-registered probe each (cheap first)

**H1 (leading) — box sector duplicates triangle content with opposite sign**
(assembly double-count or DD-expansion remnant ∝ triangle). Probe **P1**
(kernel-only, existing artifacts, existing triangle/box split): project the
BOX-only rotated sector on the 3-op basis AND on the 256-dictionary at all
three θ. Pre-registered: H1 alive iff C_scalar_box(θ) = −C_scalar_tri(θ)
within 1% at all θ with box-sector in-span completeness green. Then **P1b**:
split the box sector by loop-function head class (genuine-D0 vs C0/B0
reduction remnants) and re-project. H1 CONFIRMED iff the −C_tri piece is
carried by the non-D0 heads (duplicated triangle content — construction error
localized to assembly/reduction); if the genuine-D0 heads carry it, H1 is
falsified and H2/H3 adjudicate.
**H2 — the DD expansion manufactures the cancellation** (small-momentum
expansion of the crossed/direct box at the degenerate point creates a spurious
−triangle piece). Probe **P2, the genuinely independent fourth instrument**:
evaluate the UNEXPANDED box terms by direct LoopTools tensor evaluation at
|T| = 1 GeV² (Gram O(1), the A1-V-validated regime), project box-vs-triangle
scalar there. Pre-registered: cancellation ABSENT at |T|=1 (ratio > 0.1) →
H2 confirmed, the expansion is the bug; cancellation PRESENT → expansion
exonerated, H1 or H3.
**H3 — physical structural identity** (EW box scalar cancels the loop-induced
triangle at all θ). Probe **P3**: Hisano pure-doublet anchor, already
sanctioned (A2 validation path): transcribe gH (1104.0228) into
benchmarks/, run the pipeline at MS→large. Pre-registered: Hisano's total
scalar coefficient is NONZERO at generic size in the pure-doublet limit →
H3 REFUTED and the construction error stands; our C_scalar_full agreeing with
Hisano within ×5 while ~0 → H3 confirmed, AMENDMENT3's falsifier bar was
wrong physics and is retracted with a documented correction.
**H4 (demoted) — fit attribution (lead's a/b) / twist-2 entanglement (d).**
No separate probe: P1's dictionary-level box projection with completeness
green settles attribution; (d) is severed from the scalar question and handled
under Ruling 2. Order: P1 → P1b → P2 → P3. Each probe's verdict is committed
with its log before the next runs; no fix is coded before a mechanism is named.

## Ruling 2 — Kinematics reopen: STAYED behind the scalar mechanism; first
retest defined

The reopen trigger fired on instruments whose box sector is now under
construction-error investigation; adjudicating drift before the mechanism is
named would measure a suspect object. Decision: the reopen is LIVE but STAYED
until Ruling-1 probes conclude. First retest (pre-registered): one d-quark leg
with the DD-expansion coefficients re-derived at the v/10-matched kinematics
(S, sample momenta consistent), comparing C_twist2_sum against the frozen-
coefficient value. Bar: drift collapses < 1% → value-bias confirmed and the
cure is matched-kinematics evaluation (becomes production); drift persists ≥
1% → contracted-instrument sampling systematics, escalate to design. The STOP
freezes ALL production coefficient claims (twist-2 and C_Q included, since box
content feeds them), not only C_scalar.

## Ruling 3 — PR #36 MERGES as an honest-refusal record

The machinery worked: pre-registration executed, verdict recorded, nothing
shipped, guards runtime-verified. Same precedent as PR #35. Merge criteria:
(1) this AMENDMENT4 committed under eval/2506.19062_wimps_blind_spots/;
(2) the falsifier FAILED verdict + STOP recorded in a committed STATUS note
(Ruling 4), not only in the PR body; (3) no committed text presents
C_scalar = +1.66e-10, C_twist2_sum, C_Q, or the withheld σ_SI bracket as
validated physics (instrument readings under investigation only); (4) suite
green + protected-file byte-identity at merge SHA; (5) fresh-reviewer
confirmation of 1–4. Holding in draft is REJECTED: main should carry the
refusal record and the falsifier harness; the production path cannot ship a
number anyway (reopen trigger + this amendment).

## Ruling 4 — Round-1 canonical claim re-labeled: UNVALIDATED

The round-3 "+1.66e-10, conditionally physical" was gated on this falsifier;
the gate failed. Committed status (required for merge, in the driver history
note + eval STATUS file): "No validated blind-spot C_scalar exists.
−2.0973e-7 remains an instrument artifact (round 3); +1.66e-10 is an
unvalidated instrument reading of an amplitude whose box scalar sector is
under construction-error investigation (AMENDMENT4)." No σ_SI may be quoted
at any provenance level — sigma_provisional is insufficient; the bracket
arithmetic in handoffs stays labeled reviewer-orientation-only.

## Guard repairs (bind on the next leg)

1. SD-SI-CROSS-INSTRUMENT-DISAGREE is DEMOTED to report-only whenever
   |C| < 10× its absolute floor (6e-9): three same-M instruments agreeing at
   noise scale is not validation. Independence henceforth means a different
   evaluation path (P2) or different physics lineage (P3).
2. New shipped-coefficient diagnostic: |Im C|/|C| < 0.1 for any coefficient
   entering f_N, else named refusal SD-COEFF-IMAGINARY (a real Wilson
   coefficient with O(1) imaginary part is a noise-floor or assembly signal).

## Ruling 5 — Item-4 definition of done, updated

(a) Scalar mechanism adjudicated by P1–P3 with a named, committed verdict;
(b) if construction error: fixed, and the AMENDMENT3 falsifier RERUN passes
BOTH halves; if H3 (physical): the falsifier bar is formally retracted and
replaced by the Hisano-anchor agreement as the scalar validation;
(c) kinematics retest resolved per Ruling 2 (< 1% or mechanism named+bounded);
(d) per-flavor u/d/s; (e) σ_SI two-value bracket at canonical + 2 masses with
every guard green, Hisano ×5 and Fig.-1 ×3 anchors met — only then does
sigma_provisional drop. Item 4 is done at (e); merges before that are
milestone records (instruments or refusals), never numbers.
