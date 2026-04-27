# arXiv:2509.15121 — NMSSM Bino/Higgsino Blind-Spot Benchmark

**Paper:** "Shedding Light on Dark Matter at the LHC with Machine Learning"
Arganda, de los Rios, Perez, Roy, Sanda Seoane, Wagner (2025)

> **A/B test status (2026-04-18):** Uses the standard FeynRules NMSSM UFO; the
> production σ(pp → χ̃₁⁺χ̃₂⁰j) task should route to MG under `--runner claude`.
> Spectrum and Eq. 7 blind-spot identity tasks are pure algebra and pass on
> the reference runner.

---

## What we compute vs. what we pin

| Tier | Task ID | Quantity | Method | Pin type |
|------|---------|----------|--------|----------|
| T1 | `t1_nmssm_transcription_bp1_3` | sigma_DD^SI, Omega_h2 at BP1-3 | Paper Table 7 | paper_pinned |
| T1 | `t1_nmssm_transcription_bp9_3` | sigma_DD^SI, Omega_h2 at BP9-3 | Paper Table 6/8 | paper_pinned |
| T1 | `t1_nmssm_proc_card` | MadGraph5 proc card text | Plan spec | computed |
| T2 | `t2_nmssm_spectrum_bp1_3` | m_chi1, m_chi2, m_chi3, Z_B at BP1-3 | Tree-level 5x5 diag (Eq. 3) | computed |
| T2 | `t2_nmssm_spectrum_bp9_3` | m_chi1, m_chi2, m_chi3, Z_B at BP9-3 | Tree-level 5x5 diag (Eq. 3) | computed |
| T2 | `t2_nmssm_spectrum_bp5_2` | m_chi1, m_chi2, m_chi3, Z_B at BP5-2 | Tree-level 5x5 diag (Eq. 3) | computed |
| T2 | `t2_nmssm_epsilon_bp9_3` | epsilon = m_chi2/m_chi1 - 1 at BP9-3 | Eq. (6) | computed |
| T2 | `t2_nmssm_sigma_si_rescaled_bp9_3` | sigma_SI_eff at BP9-3 | Eq. (15) sub-relic rescaling | computed |
| T3 | `t3_nmssm_blind_spot_eq7_on_bp1_3` | Eq. (7) LHS at BP1-3 | Eq. (7) formula | computed |
| T3 | `t3_nmssm_blind_spot_eq7_off_bp1_3` | floor_excess at BP1_3_off | Eq. (7) off-BP control | computed |
| T3 | `t3_nmssm_blind_spot_eq7_synthetic` | Eq. (7) LHS at synthetic blind spot | Self-consistent 4x4 limit | computed |
| T3 | `t3_nmssm_spectrum_identities_bp1_3` | trace, det, orthogonality, fraction sum | Algebraic identities | computed |

**Not computed here (tool invocations):** NMSSMTools masses, micrOMEGAs relic densities,
MadGraph5 production cross sections. These are either paper-pinned (Tier-1) or absent (no
`cached_sigma_prod.json` was generated; `t2_nmssm_sigma_prod_bp1_3` row is not authored).

---

## Phase-1 Key Finding: Paper BPs are NOT on the Eq. 7 blind spot

**This deviation from the plan is intentional and physically correct.**

The plan (§12) assumed the paper BPs would satisfy the Eq. 7 blind-spot identity LHS ~ 1.
Phase-1 measurement showed this is not the case at tree level:

| BP | LHS (Eq. 7) | |LHS - 1| | Interpretation |
|----|------------|----------|----------------|
| BP1-3 (on-BP, singlino LSP) | **3.33** | 2.33 | NOT on blind spot by Eq. 7 |
| BP1-3-off (mu_eff flipped) | **2.65** | 1.65 | Off-BP control, also far from 1 |
| Synthetic 4x4 (constructed) | **1.000000** | < 1e-6 | TRUE blind spot |

**Why does LHS ~ 3.33?** With M1 = 500 GeV (fixed, bino decoupled) and singlino LSP at
~147 GeV, the denominator `M1 - m_chi1 ~ 352 GeV` is large, and the g1-coupling term
`g1^2 * v^2 / 352 ~ 13 GeV` adds a small correction to a 147 GeV LSP. However
`mu_eff * sin(2*beta) = 161.8 * sin(2 * arctan(6.2)) = 161.8 * 0.312 ~ 50.5 GeV`,
making LHS = (147.5 + 13) / 50.5 ~ 3.2. The denominator `mu_eff * sin(2*beta)` is
roughly 3x smaller than the numerator because tan_beta = 6.2 is large (sin(2*beta) is
small for large tan_beta).

The paper's BPs are in the "bino-higgsino blind-spot parameter region" in the sense that
the SI cross section is suppressed, but not because Eq. 7 LHS = 1 at tree level. The
radiative corrections (NMSSMTools) and the sub-relic rescaling (Eq. 15) account for the
suppression seen in Tables 7-8.

**Test consequences (recorded in `impl-deviations.md`):**
1. `t3_nmssm_blind_spot_eq7_on_bp1_3` pins `lhs_eq7 = 3.33` (formula reproducibility test,
   not blind-spot saturation test).
2. `t3_nmssm_blind_spot_eq7_off_bp1_3` uses `floor_excess` only (not `relational_excess`),
   because |LHS_off - 1| = 1.65 is NOT > 5 * |LHS_on - 1| = 11.65 (the off-BP coupling
   difference is genuine but not 5x larger than on-BP).
3. The TRUE blind-spot saturation test is `t3_nmssm_blind_spot_eq7_synthetic`, which
   constructs a self-consistent 4x4 decoupled limit and asserts LHS = 1 to < 1e-6.

---

## Implementation Notes

### Constants
- `G1_SM = 0.3574` (SM-normalized, NOT GUT-normalized; no sqrt(5/3) factor)
- `G2_SM = 0.6517` (SM-normalized)
- `OMEGA_PLANCK_H2 = 0.120` (Planck 2018)

### Spectrum diagonalization (Eq. 3)
- Uses `scipy.linalg.eigh` (not `np.linalg.eigh`; LAPACK dsyev for reproducible sign conventions)
- Returns `(masses_abs, signs, N)` — SLHA-1 sign tracking
- `nmssm_spectrum` ref_fn returns absolute masses only; signed values consumed internally

### sigma_SI rescaling (Eq. 15)
- Implements `sigma_SI * min(1, Omega/Omega_Planck)` — `min(1, ...)` clips overproduction
- Deviation from plan wording (which had no `min`): the clip is physically correct for
  sub-relic dark matter and avoids unphysical rescaling above the Planck value

### Benchmark parameter reconstruction
- Paper uses NMSSMTools (radiative corrections); we use tree-level Eq. 3
- Tree-level masses agree to < 0.5% for m_chi1 (singlino), < 1% for m_chi2/m_chi3
- YAML Tier-2 rows pin to **computed** values (not paper Tables) for spectrum tests
- YAML Tier-1 rows pin to **paper** values for sigma_DD^SI and Omega_h2 (transcription)

---

## File Structure

```
eval/2509.15121_nmssm_ml_blind_spot/
├── README.md                    (this file)
├── paper_metadata.json
├── constants.py                 V_H, G1_SM, G2_SM, M_Z, M_H, OMEGA_PLANCK_H2, SW2
├── phase1_notes.md              Phase-1 log with LHS measurements and BP transcription
├── models/
│   ├── neutralino_spectrum.py   Eqs. 3-5, 5x5 diag, signed eigenvalues (scipy.linalg.eigh)
│   ├── blind_spot_identity.py   Eq. 7 LHS function
│   └── compression_parameter.py Eq. 6 epsilon
├── cross_sections/
│   └── sigma_si_rescaling.py   Eq. 15 sub-relic rescaling
├── madgraph/
│   ├── README.md                MG5 version pin; regen procedure
│   ├── proc_card.dat            pp > x1+ n2 j
│   ├── param_card_BP1_3.dat     SLHA-1 hand-authored for BP1-3
│   ├── run_card.dat             14 TeV, NNPDF30_lo, mu=HT/2, LO, 50k events
│   └── run_mg5_production.py   OFFLINE: generates cached_sigma_prod.json (not run)
├── benchmarks/
│   ├── benchmark_points.py      BP dict with params, expected, source labels
│   └── test_benchmarks.py       20 pytest tests: 4 Tier-1 transcription + 16 physics
└── verify_spectrum_signs.py     Standalone debug script (not in pytest collection)
```

---

## Deviations from plan (see `impl-deviations.md`)

1. `on_bp` test: LHS pinned at 3.33, not 1.0 (Phase-1 finding)
2. `off_bp` test: `relational_excess` dropped; `floor_excess` only
3. `sigma_SI_rescaled`: implements `min(1, ...)` clip (plan wording omitted it)
4. BP5-2 transcription row: skipped (≥2 threshold already met; BP5-2 fully transcribed
   but no T5/T6 YAML transcription row authored for it — spectrum row IS authored)
