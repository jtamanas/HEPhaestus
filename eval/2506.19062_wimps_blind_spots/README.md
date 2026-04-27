# 2506.19062 — WIMPs Below the Radar

**Title:** WIMPs Below the Radar: Blind Spots and Benchmarks Beyond the Neutrino Floor
**Authors:** Giorgio Arcadi, Stefano Profumo
**arXiv:** [2506.19062](https://arxiv.org/abs/2506.19062) [hep-ph], June 2025

## Premise

This paper investigates WIMP dark matter scenarios that naturally evade direct
detection constraints through "blind spots" — parameter-space regions where the
tree-level spin-independent (SI) DM-nucleon scattering cross-section vanishes due
to cancellations in the couplings. Loop corrections then set the effective floor.

Three BSM models are studied:

1. **Singlet-Doublet fermion model** — A Dirac singlet S mixes with a vector-like
   doublet (D_L, D_R) via Yukawa couplings to the Higgs. The 3x3 mass matrix admits
   blind spots where the effective Higgs-DM coupling vanishes.

2. **2HDM+a** — Two-Higgs-Doublet Model extended with a pseudoscalar singlet a^0
   that couples to fermionic DM. SI scattering is loop-suppressed (CP symmetry
   forbids tree-level SI scattering via pseudoscalar exchange).

3. **Dark SU(3)** — A confining dark gauge sector with vector and scalar DM
   candidates. The scalar component has an exact (parameter-independent) blind spot
   due to a cancellation between the two Higgs mediators.

## What We Benchmark

### Analytically evaluable equations (Python implementations)
- Mass matrix diagonalization (Eq. 3)
- DM-Higgs and DM-Z couplings (Eqs. 7, 15-18, 28)
- Blind spot conditions (Eqs. 8, 29)
- Tree-level SI/SD cross-sections (Eq. 5)
- Pseudoscalar mixing angle (Eq. 21)
- Trilinear scalar couplings (Eq. 25)
- One-loop SI cross-sections via Passarino-Veltman integrals (Eqs. 9, 14, 23)

### MadGraph comparison
- Tree-level DM-nucleon scattering cross-sections
- DM pair annihilation cross-sections (for relic density)
- Mass spectra validation against analytical diagonalization

### Models required
- Singlet-Doublet: available as custom UFO or via FeynRules
- 2HDM+a: official LHC DM WG UFO model (DMPseudo_2HDM)
- Dark SU(3): requires custom UFO model via FeynRules

## Figures to Reproduce

| Figure | Content | Key equation |
|--------|---------|--------------|
| 1 | SI cross-section vs m_chi1 (singlet-doublet) | Eq. 9 |
| 2 | SI cross-section vs tan(theta) (SD+2HDM benchmarks) | Eqs. 14-18 |
| 3 | Full parameter scan SD+2HDM | Eq. 14 |
| 4 | SI cross-section vs m_chi (2HDM+a benchmarks) | Eq. 23 |
| 5 | Full parameter scan 2HDM+a | Eq. 23 |
| 6 | Collider-stable pseudoscalar regime | Eq. 23 |
| 7 | Relic density evolution (Dark SU(3)) | Eq. 27 |
| 8 | SI cross-section vs m_V (Dark SU(3)) | Eq. 28 |
