# DESIGN-ITEM4-AMENDMENT5 — H1 refuted; the fork is the triangle sector (X/Y)

Amends AMENDMENT4.md after P1/P1b (probe-box/{canon,A,B}). Accepted: on the
UNROTATED 3-op instrument the box is additive, C_box ≈ +0.6×C_tri, same sign,
at all three θ (−1.28e-7 + −0.81e-7 = −2.10e-7, linearity exact ~1e-16); on
the production lineage C_box ≈ ±4e-12; the DD-expansion head classes self-
cancel to 1e-23 — no duplicated-triangle mechanism. **RETRACTION (mine):**
AMENDMENT4's deduction "the box sector carries −C_tri" mixed a ROTATED
numerator (+1.66e-10) with an UNROTATED denominator (−1.28e-7); the
implementer's catch is correct and credited. **P2 (unexpanded box at |T|=1) is
WITHDRAWN** — it targeted a cancellation that does not exist. H1 and H2 are
CLOSED. What remains: the two lineages disagree by ~1e3 IN THE TRIANGLE
SECTOR (unrotated fixture −1.28315085e-7 vs rotated production ≈ +1.7e-10),
and exactly one of them is the physical scalar coefficient.

## Ruling 1 — The fork, and the design ruling on rotation vs the triangle

**Branch X:** the fixture −1.2831509485455282e-7 is itself a probeH-class
artifact — M_tri carries weight on the Majorana-crossed monomials (same χ
legs, same FormCalc rearrangement), whose UNROTATED out-of-span leakage into
O_S is the fixture's value; the rotated ~1e-10 is the honest reading.
**Branch Y:** the rotated production lineage destroys real scalar strength in
a way rotation-exactness and completeness cannot see (both check M's VALUES,
not the coefficient READ-OFF — the read-off of the rotated algebraic
decomposition is the one step those guards never test on crossed content).
**Design ruling (binding, both branches):** the rotation rule is
monomial-level and sector-blind — any M_tri weight on F5*F6/F7*F8 must be
rotated by the identical rule; the tri-runner's unrotated path is hereby
re-labeled a REGRESSION instrument (bit-stability of the frozen code path),
never a physics reading. Physical claims come only from rotated readings —
which under Y must first be repaired. The fixture's bit-identity remains a
merge criterion as regression; its VALUE carries no validation weight
pending the fork.

## Ruling 2 — Probe ladder v2 (pre-registered; verdict committed before next)

**Q1** (kernel, implementer's (i)): rotated-3op fit on M_tri alone, all three
θ, with residual reported. Predict under X: ≈ +1.7e-10-scale, consistent with
full-minus-box by linearity.
**Q2** (kernel, implementer's (ii), THE instrument-level discriminator):
probeH-style crossing split on M_tri. Predict under X: M_tri's crossed
monomials carry ≈ −1.28e-7 O_S leakage unrotated and ~0 rotated, direct
monomials ~1e-10. **Sharp branch:** if M_tri has NO material crossed-monomial
weight (crossed share of ‖M_tri‖ < 1e-3), X is REFUTED on the spot and Y is
convicted — rotation then cannot explain the tri-sector gap.
**Q3** (kernel, closes a genuine control gap): synthetic-amplitude
identifiability control THROUGH the crossed path — build a synthetic M from
crossed-type monomials with KNOWN S⊗S content (known because constructed from
in-span structures then re-expressed in crossed form via the same C-identity),
run the full rotate-then-read-off pipeline. Recovery to < 1e-10 exonerates
the read-off; failure convicts Y and localizes it. (Existing identifiability
controls cover direct columns only — this is the hole Y lives in.)
**P3** (decisive independent lineage, unchanged from AMENDMENT4): Hisano
pure-doublet gH transcription (benchmarks/ only), pipeline at MS→large.
Whichever scale Hisano's functions produce, ours must match within ×5:
−1.28e-7-scale → Y confirmed at the physics level; ~1e-10-scale → X
confirmed. No leaning pre-registered — the two instrument readings differ by
1e3 and Hisano adjudicates which is physical.
Order: Q1+Q2 (one kernel session) → Q3 → P3. No production-code fix before a
committed verdict.

## Ruling 3 — X-branch consequences (pre-registered, fire only on X verdict)

(1) Fixture re-labeled in-repo: "pinned regression value of the unrotated
forward 3-op instrument; a crossing artifact, not a physical coefficient."
(2) C_Q = C_tri/m_q = −2.75e-5 is VOID; C_Q re-derived from the ROTATED
triangle reading (Q1 value) — this collapses the gluon term by ~1e3, undoes
the twist-2-vs-gluon near-cancellation, and therefore the kinematics
reopen-trigger mechanics (AMENDMENT4 Ruling 2) must be RE-MEASURED on the
re-derived f_N shares before the stayed retest runs. (3) The falsifier is
re-posed with a valid denominator: growth-vs-θ is VOID as a test (both
lineage readings are θ-flat); scalar validation becomes P3 (Hisano ×5) plus
the Fig.-1 ×3 σ_SI anchor. (4) Validation audit: everything that leaned on
−1.28e-7 as physics loses weight and is named in the STATUS note — item-3
"triangle-only stable" narrative (re-label: instrument-stable), A6
triangle-continuity (regression-only), AMENDMENT3/4 falsifier denominators
(void), round-2 C_Q row (void). Round-3's "+1.66e-10" stays UNVALIDATED until
P3 — X does not rehabilitate it by itself.

## Ruling 4 — Y-branch consequences (pre-registered, fire only on Y verdict)

Named candidate mechanisms, each with its probe: **Y1** — read-off
normalization/convention error in mapping the rotated decomposition's S⊗S
coefficient to O_S (shared by all three cross-instruments, hence invisible to
their agreement): convicted/cleared by Q3 directly. **Y2** — sample-set
dependence (transfer-enriched rows re-attribute scalar strength): probe = the
rotated production fit re-run on the ORIGINAL 80 forward configs only; a
material shift (> 10%) convicts Y2. On Y conviction: fix the named mechanism,
re-run Q1–Q3 green, then RE-RUN the AMENDMENT3 falsifier as posed (its
denominator is valid under Y) — both halves must pass before any coefficient
claim. C_Q and the fixture keep their current status under Y.

## Ruling 5 — PR #36 merge timing, and the Im/Re fold-in

Merge-prep stays PARKED until the Q1/Q2/Q3 verdict (kernel-only, hours) —
NOT until P3: the committed STATUS note must state the right branch (under X
it must carry the fixture re-label; merging before the verdict risks
committing a narrative we re-label days later, which is how this arc's debts
were made). P1 verdicts and the AMENDMENT4-deduction retraction go into the
PR body and STATUS note now, staged with the X/Y outcome slot. Merge criteria
otherwise unchanged from AMENDMENT4 Ruling 3.
**SD-COEFF-IMAGINARY (design finalized):** the bar |Im C|/|C| < 0.1 applies
to the SHIPPING instrument's reading (rotated-3op / contracted), measured
~1e-9 — green; the transfer instrument's |Im|/|C| up to 0.53 is a named
sampling artifact, exempt from the bar, reported in the sidecar. An O(1)
Im on the shipping reading remains fatal.
