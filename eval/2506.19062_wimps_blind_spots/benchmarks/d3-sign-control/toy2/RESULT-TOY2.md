# RESULT — toy2 known-sign FormCalc overall-i/normalization confirmation

**Pre-registration:** ToyDiracH2.mod / toy2_gen.wls headers (committed before the run).
Process: chi phi -> chi phi, t-channel h, single fermion chain, one diagram.
A-priori: M_phys = − gchi·mu/(t − Mhh²)·(ūu) = − gchi·mu·Den[T,Mhh²]·(ūu).

**Measured (gen on WE 13.3 FeynArts kernel, reduce via production
run_calcfeynamp.wls, weyl/D, same invocation as D3):**

- Raw CreateFeynAmp output (`toy2_amps.m`):
  `FeynAmp[GraphID[...], Integral[], I*mu*FermionChain[ū, I*gchi*(ω−+ω+), u]*PropagatorDenominator[k4−k2, Mhh]]`
  — **NO leading minus** on the single-chain amplitude.
- Reduced (`out/amp_reduced.m`):
  `Amp[...][ -((F1 + F2)*gchi*mu*Den[T, Mhh^2]) ]`, F1/F2 = ū ω₆/ω₇ u
  — Den-coefficient **NEGATIVE = −gchi·mu**, i.e. Amp ≡ M_phys exactly.

**Verdict: prediction (a) CONFIRMED — branch (b) (global −1) REFUTED.**
FormCalc's CalcFeynAmp normalization is sign-faithful (Amp ≡ M_phys; vertex i's
as stored, PropagatorDenominator → Den[T,m²] = 1/(T−m²) with no extra i, no
overall constant). This closes the reviewer's one un-closable residual DIRECTLY
(measured, not artifact-inferred).

**Cross-toy algebra (both toys, same toolchain):**
- toy2 (1 chain):  raw = (i·mu)(i·gchi)(chain)·PD           → reduced = −g·mu·chain·Den   = M_phys ✓
- D3   (2 chains): raw = **−**(i·gchi)(i·gq)(chains)·PD     → reduced = +g·g·chains·Den   = −M_phys ✗
CalcFeynAmp maps raw→reduced with constant +1 in both cases. The ONLY anomalous
constant in the toolchain is the explicit −1 that CreateFeynAmp attaches to the
two-distinct-fermion-line (chi̅ chi)(q̄ q) FermionChain pairing.

**Interaction with item 1 (EVIDENCE-PAIRING-VS-DIAGRAM.md):** the −1 is
two-chain-pairing-specific but, per the item-1 census, that pairing is shared by
ALL 164 production diagrams — so on the production process it acts as a
process-global constant that would flip scalar AND twist-2 together. Toy2 rules
out "global on all amplitudes" (single-chain is clean) but does not rescue a
scalar-sector-only mechanism; the twist-2 before-conviction gate from item 1
stands.
