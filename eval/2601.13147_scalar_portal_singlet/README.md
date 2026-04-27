# arXiv:2601.13147 — Singlet Fermion DM + Scalar Portal

**Paper:** "Revisiting Singlet Fermion Dark Matter with a Scalar Portal: Connecting Higgs Phenomenology and Strong Electroweak Phase Transition"  
**Authors:** Jaydeb Das, Saurabh Niyogi, Tripurari Srivastava  
**arXiv:** https://arxiv.org/abs/2601.13147  
**Version:** v3

> **A/B test status (2026-04-18):** UFO not public for this model; expect
> `BLOCKED_CORRECTLY` on σ_SI tier-2 tasks under `--runner claude` until
> UFO-generation support lands. Mass-spectrum tier-2 and blind-spot tier-3
> tasks are pure algebra and should pass.

## Premise

This paper studies a singlet fermion dark matter model with a real scalar Higgs portal.
The SM is extended with a gauge-singlet real scalar S and a Dirac fermion χ coupled via
`L_portal = g_chi * S * chi_bar * chi`. The scalar S mixes with the SM Higgs via the
portal coupling, producing two CP-even mass eigenstates h1 (SM-like) and h2 (singlet-like)
with mixing angle θ.

The paper:
1. Computes spin-independent DM-nucleon cross-sections via h1/h2 exchange (Eq. 31)
2. Applies LHC constraints (Eq. 18/22: signal strength) and vacuum stability/unitarity (Eqs. 15-16)
3. Identifies a "blind spot" when m_h1 = m_h2 (exact cancellation in the SI amplitude)
4. Connects to strong electroweak phase transition (out-of-scope for this benchmark)

## What We Benchmark

### Analytically evaluable equations (Python implementations)

| Module | Functions | Equations |
|--------|-----------|-----------|
| `models/scalar_portal_singlet.py` | `mass_matrix_CPeven` | Eq. 8 |
| | `m_h1_h2_analytical`, `diagonalize_numerical` | Eqs. 11-12 |
| | `lagrangian_params_from_physical` | Eqs. 13-14 (inverse) |
| | `vacuum_stability_lhs`, `perturbative_unitarity_lhs` | Eqs. 15-16 |
| | `sigma_pp_h2`, `mu_signal` | Eqs. 18, 22 |
| | `coupling_chichi_h1/h2`, `coupling_qq_h1/h2` | Eqs. 27-28 |
| | `amplitude_SI`, `f_N_proton/neutron` | Eq. 29 |
| `cross_sections/si_tree_level.py` | `sigma_SI_scalar_portal` | Eq. 31 |

### Benchmark points (Table 1)

| BP | m_chi [GeV] | g_chi | sin_theta | m_h2 [GeV] | Source |
|----|-------------|-------|-----------|-----------|--------|
| BP1 | 222 | 0.57 | 0.001 | 200 | Paper Table 1 |
| BP_mid | 200 | 1.0 | 0.2 | 300 | Synthetic control |
| BP9 | 78 | 0.34 | 0.002 | 70 | Paper Table 1 |

### Key cross-sections (internal hand-calc, not paper-match)

| BP | sigma_SI (proton) | Note |
|----|------------------|------|
| BP1 | ~6.17e-50 cm² | Paper gives 6.96e-50; ~11% gap documented in RECONCILIATION.md |

## Figures to Reproduce

| Figure | Content | Key equation |
|--------|---------|-------------|
| Fig. 1 | Scalar potential and mass spectrum | Eqs. 8, 11-12 |
| Fig. 2 | sigma_SI vs m_chi (LZ limits) | Eq. 31 |
| Fig. 3 | Signal strength mu vs sin_theta | Eq. 22 |
| Fig. 4 | Stability/unitarity constraints | Eqs. 15-16 |

## Running Tests

```bash
cd eval/2601.13147_scalar_portal_singlet
python -m pytest benchmarks/test_benchmarks.py -v
# Expected: 38 passed (37 from plan + 1 amplitude sign variant)
```

## Notes

- V_H = 246.22 GeV (same as 2506.19062; PDG value rounded to 2 decimal places)
- Form factors: Hoferichter et al. (same as 2506.19062)
- sigma_SI gap of ~11% vs paper: tracked in RECONCILIATION.md; due to form factor/VEV convention differences
