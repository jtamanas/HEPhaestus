# EVIDENCE NOTE — Pairing-vs-diagram mechanism for the FeynArts ordering signature

**Leg:** AMENDMENT9 precondition, item 1 (source-locator; code-read only, no kernel).
**Question:** Does the FeynArts external-fermion-ordering sign (the D3 toy's explicit
leading minus) attach PER-PAIRING (so scalar-class chains could carry it while
twist-2-class chains do not — mechanistically explaining a uniform scalar-sector-only
flip) or PER-DIAGRAM (all chains in a diagram share it — leaving the scalar-only
pattern unexplained by this candidate)?

**Artifact examined (production, raw, pre-FormCalc):**
`/Users/yianni/.claude/jobs/c703354a/tmp/loopset-step2/loop1_full_chi1/FeynAmpList.m`
(FeynArts 3.11, model `singlet_doublet`, model_hash `ffb97ad2…`, process
`{F[5,{1}], F[4]} -> {F[5,{1}], F[4]}` = chi1 d -> chi1 d, AmplitudeLevel
{Generic, Classes}, 164 FeynAmps across 15 topologies, including both box
orderings T1/T2). Analysis is pure text-parsing of the FeynAmp structures
(balanced-bracket extraction; parser inline in the git log / reproducible from
this note).

## Finding 1 — External pairing is UNIFORM across all 164 diagrams

Every FeynAmp contains exactly **two external FermionChains** with the **same
pairing and the same spinor order**:

```
FermionChain[ MajoranaSpinor[ FourMomentum[Outgoing,1] …], …, MajoranaSpinor[ FourMomentum[Incoming,1] …] ]
* FermionChain[ DiracSpinor[ FourMomentum[Outgoing,2] …], …, DiracSpinor[ FourMomentum[Incoming,2] …] ]
```

i.e. (chibar_out … chi_in)(qbar_out … q_in) — the identical (chi̅ chi)(q̄ q)
pairing of the D3 tree toy. Census over all 164 FeynAmps:

- pairing {(Out1,Inc1), (Out2,Inc2)}: **164 / 164**
- crossed pairings (e.g. Out1 with Inc2): **0**
- reversed-flow external spinors (negative FourMomentum): **0**

This holds in particular for BOTH box topologies (T1 and T2, 12 generics each —
the direct and crossed boxes): the external chains read (chi̅ chi)(q̄ q) in both;
the "crossing" lives entirely in the loop-momentum routing, and no relative
external-ordering sign distinguishes them (same prefactor pattern by generic,
verified below). The Majorana-crossed monomials (F5·F6 / F7·F8) seen in
`amp_reduced` are produced downstream by FormCalc's Weyl-chain reduction, not by
crossed external pairing at the FeynArts level.

## Finding 2 — The sign attaches as a single per-diagram prefactor on the product of BOTH chains

Each FeynAmp has the form

```
FeynAmp[GraphID[Topology == 1, Generic == 1], Integral[FourMomentum[Internal, 1]],
  ((I/16)*RelativeCF*FermionChain[…]*FermionChain[…]*…)]
```

The sign is a scalar constant multiplying the product FermionChain × FermionChain.
There is **no per-chain sign slot**: nothing at the FeynAmp level can give the
chi-chain and the q-chain (or, a fortiori, the scalar vs twist-2 Dirac content
INSIDE those chains, which only separates after FormCalc reduction) different
signs. Attachment is **per-diagram, operator-blind**.

## Finding 3 — The per-generic sign variation is generic-model loop bookkeeping, not ordering

Prefactor signs vary across generics within a topology (e.g. T1: +I/16 for
G{1,2,6,9,10,11}, −I/16 for G{3,4,5,7,8,12}). This variation is fully attributed:

- law tested: prefactor sign = (−1)^(#vector loop fields + closed-fermion-loop + ghost-loop)
- result: **162 / 164 FeynAmps match**
- the 2 residuals (T7 G12, G13) are 4-point-vertex generics with a distinct
  1/16-vs-1/32 normalization; their prefactors are still single diagram-global
  constants, so they do not affect the attachment conclusion.

This is standard generic-model propagator/loop-sign bookkeeping and is
independent of the external-fermion-ordering question.

## Finding 4 — The ordering signature is therefore a PROCESS-GLOBAL constant

Because the external ordering, the chain pairing, and the spinor order are
identical in every diagram, whatever ordering signature FeynArts assigns to the
(chi̅ chi)(q̄ q) two-distinct-line pairing (measured as an explicit −1 in the D3
tree toy, `toy_feynamps_raw.m` in this directory) is the SAME constant for all
164 diagrams — and hence identical for scalar-class and twist-2-class content,
since both live inside the same two chains of the same diagrams.

## VERDICT (pre-registered branch)

**PER-DIAGRAM** (indeed per-process). A uniform SCALAR-SECTOR-ONLY sign flip is
**NOT mechanistically explained** by the FeynArts external-fermion-ordering
signature: this candidate flips scalar and twist-2 together or not at all.
Per the AMENDMENT9 precondition branch, the sequencing flips — twist-2
re-verification becomes a BEFORE-conviction gate.

Companion leg (item 2, kernel): a single-fermion-chain known-sign FormCalc toy
(`toy2_*` in this directory) that closes the reviewer's overall-i/normalization
residual independently of the two-chain ordering boundary; pre-registered signs
in the script headers.
