# Benchmark extraction TODO

Five new papers were accepted in the 2026-04-18 expansion round (see
`PAPER_CANDIDATES.md`). This document breaks down the work to turn each into a
benchmark in the same style as `2506.19062_wimps_blind_spots/`.

For the general extraction workflow, see `METHODOLOGY.md`. This document tracks
the per-paper specifics: which equations to pin, where the numbers live, and
the known risks before we start.

## Standard per-paper structure (from METHODOLOGY.md)

Every paper directory follows the layout:

```
eval/{arxiv_id}_{short_name}/
├── README.md              # Premise, what we benchmark, figure-to-equation map
├── paper_metadata.json    # Structured metadata
├── constants.py           # Physical constants used
├── models/                # One file per BSM model (mass matrix + couplings)
├── cross_sections/        # σ_SI, σ_SD, ⟨σv⟩ formulas
├── loop_functions/        # If needed
├── madgraph/              # proc/param/run cards + run_comparison.py
└── benchmarks/
    ├── benchmark_points.py  # Parameter points + expected outputs
    └── test_benchmarks.py   # The pin tests
```

Plus harness integration:
- Reference functions added to `eval/harness/refs.py`
- Tier-1/2/3 tasks added to `eval/tasks/*.yaml`
- Run `python -m eval.harness.run --runner reference --tier {1,2,3}` to verify
  the new tasks pass with our implementation before running Claude.

## Per-paper checklist (each paper repeats this skeleton)

For every paper below:

- [ ] **Phase 1 — Deep paper read.** Pass 1 structure (classify each numbered
      equation as closed-form / identity / definition / numerical-integration);
      Pass 2 numbers (extract every benchmark parameter point + every stated
      numerical observable + physical constants).
- [ ] **Phase 2 — Directory setup** (the layout above).
- [ ] **Phase 3 — Implement equations** as Python functions with equation-number
      docstrings and unit annotations.
- [ ] **Phase 4 — Write pin tests.** Hand-calculate at ≥3 BPs (or two-route
      cross-check). NO range tests (`assert sigma > 0` etc.) — every test must
      pin a specific number.
- [ ] **Phase 5 — MadGraph setup.** proc/param/run cards per model. UFO either
      pulled from public repo or built via FeynRules.
- [ ] **Phase 6 — Iterate.** Hunt convention factors (Majorana 2, identical-particle
      1/2, π normalizations) until tests pass.
- [ ] **Phase 7 — Harness integration.** Add reference functions to
      `eval/harness/refs.py`; add tier-1/2/3 tasks to `eval/tasks/*.yaml`;
      verify `python -m eval.harness.run --runner reference --tier {1,2,3}`
      passes before any Claude run.

---

## Paper 1 — arXiv:2601.13147 (singlet fermion + scalar portal)

**Suggested directory:** `eval/2601.13147_scalar_portal_singlet/`

**Why we accepted:** 9 fully-pinned BPs (BP1-BP9) with σ_SI(p), σ_SI(n),
Ωh², dominant annihilation channels in Tables 1+2. Blind-spot factor
(1/m_h₂² − 1/m_h₁²) is a clean algebraic identity. Bonus: GW/EWPT extension
(Tables 3+4) adds 9 more pinned points of (T_c, T_n, ξ_h, α_n, β/H_n).

### Equations to pin (Phase 3)

Core DM physics (Tier 2):
- [ ] Eq. 8 — CP-even mass matrix M²(v,0)
- [ ] Eqs. 11-12 — m²_{h₁,h₂} from M_hh, M_ss, M_hs (two routes: analytical + matrix diag)
- [ ] Eqs. 13-14 — inverse: λ_h, μ_hs, μ_s² in terms of physical inputs
- [ ] Eqs. 15-16 — vacuum stability + tree perturbative-unitarity bounds
- [ ] Eq. 18 — σ(pp→h₂) = sin²θ · σ_SM
- [ ] Eq. 22 — μ_sig = cos²θ; Eq. 24 — sinθ ≲ 0.24
- [ ] Eqs. 27-28 — Yukawa-rotated couplings g_{χχh₁,2}, g_{qqh₁,2}
- [ ] Eq. 29 — effective DM-quark Lagrangian (manifest blind-spot)
- [ ] **Eq. 31 — σ_SI** (headline, pinned at all 9 BPs)

Optional GW/EWPT extension (Tier 3 stretch):
- [ ] Eqs. 32-37 — field-dependent masses for V_eff
- [ ] Eq. 38 — Coleman-Weinberg V_CW
- [ ] Eqs. 41-44 — thermal J_B/J_F
- [ ] Eqs. 47-52 — Debye masses
- [ ] Eq. 56 — order parameters ξ_h, ξ_s
- [ ] Eqs. 57-59 — α_n, latent heat, β/H_n
- [ ] Eqs. 61-70 — full GW spectra

### Pinned numerics (BP1-BP9 from Tables 1-2)

Examples (full list: 9 BPs):
- BP1: m_h2=200, sinθ=0.001, λ_hs=2.2, λ_s=3.38, μ_3=−20, m_χ=222, g_χ=0.57 → Ωh²=0.119, σ_SI(p)=6.96×10⁻⁵⁰ cm², σ_SI(n)=7.10×10⁻⁵⁰ cm²
- BP4: m_h2=350, sinθ=0.001, λ_hs=4.3, λ_s=4.5, μ_3=20, m_χ=310, g_χ=0.87 → Ωh²=0.120, σ_SI(p)=3.26×10⁻⁴⁹
- BP9: m_h2=70, m_χ=78 → σ_SI(p)=1.26×10⁻⁴⁸, χχ→h₂h₂(100%); GW peak ~0.01 Hz

### Risks

- **No public UFO.** Authors built via FeynRules 2.3 + NLOCT. Need ~half-day to
  rebuild. Document the FeynRules model in `madgraph/feynrules/`.
- **No "agrees with X to 1%" validation statement** — criterion 4 fails. Use
  hand calculations + two-route cross-checks (mass-matrix vs analytical) for
  Tier-3 tests instead.
- EWPT extension requires **CosmoTransitions** or a numerical bounce solver.
  Defer GW chain to a Tier-3 stretch task; first cut should pin only Tier 2.

---

## Paper 2 — arXiv:2603.23040 (scotogenic inverse seesaw, light DM window)

**Suggested directory:** `eval/2603.23040_scotogenic_inverse_seesaw/`

> **A/B-test gated on UFO-generation skill.** No public UFO for this model.
> Under `--runner claude`, MG/MadDM observable tasks correctly trigger
> `BLOCKED_CORRECTLY` (see PR-A outcome-mode changes); under
> `--runner reference`, the closed-form Python oracle covers them. Promote to
> flagship end-to-end eval once the practitioner-authored-`.fr` →
> Mathematica-driven UFO workflow lands. Note: the flagship
> workflow assumes the practitioner supplies the `.fr` / `.m` file; generating
> the Lagrangian from prose is an explicit stretch goal, not a near-term
> target.

**Why we accepted:** Only paper in the new set that uses **MadDM directly** as
the relic engine, with explicit validation statement: "the analytical
calculation for ⟨σv_Møl⟩ matches the output of MadDM." Three named BPs (42,
59, 61 GeV) with full ILC cutflow tables. Higgs-funnel resonance regime.

### Equations to pin (Phase 3)

- [ ] Eq. 6 — cubic characteristic equation for χ masses
- [ ] Eqs. 7a-7c, 8 — closed-form roots X1,2,3 and angle θ
- [ ] Eqs. 10-11 — full 3×3 mixing matrix U_F with normalization
- [ ] Eq. 14a-b — neutrino mass M^ν = yφ Λ y^T_φ with one-loop function Λ_r
- [ ] Eq. 15 — Casas-Ibarra parameterization for y_φ
- [ ] Eqs. 16-17 — B(μ→eγ) with loop function F(x)
- [ ] Eqs. 19a-b — Γ(h→χχ), Γ(Z→χχ)
- [ ] Eqs. 22-24 — |M|² for χχ→ff̄ and σ
- [ ] Eq. 21 — Gondolo-Gelmini thermal averaging
- [ ] Eqs. 26a-c — matching coefficients C^SS_h, C^VA_Z, C^AA_Z
- [ ] Eqs. 29a-e — NREFT coefficients c1,4,6,8,9 (per nucleon)
- [ ] Eq. 30 — full σ̄^SI with isotopic sum and velocity term
- [ ] **Eqs. 32-33 — σ^SD** (full NREFT vs simplified dominant-term — Criterion 2 cross-check)
- [ ] Eq. 36 — statistical significance

### Pinned numerics

- Scalar masses fixed: m_φ1=1000, m_φ2=1200, m_φ3=1400 GeV
- PMNS inputs (Sec 2.1): Δm²21=7.5e-5 eV², Δm²23=2.45e-3 eV², sin²θ12=0.307,
  sin²θ23=0.534, sin²θ13=0.0216, δCP=1.21π, m_ν1=0.01 eV
- Constraints: B(μ→eγ)<3.1e-13, B(h→inv)<0.107, B(Z→inv)<0.008,
  0.115≤Ωh²≤0.125
- Nucleon form factors (Table 1): full f_Tq, F1, F2, GA, aπ, aη
- BP1 (42 GeV), BP2 (59 GeV), BP3 (61 GeV) at √s=1 TeV, L=4 ab⁻¹ — full cutflow
  in fb (BP2 e.g.: pre-selection 0.024 fb → after Cut 4: 0.0017 fb at 2.48σ)
- Table 3: five polarization configs

### Algebraic identities (Tier 3)

- σ_p^SD ≈ σ_n^SD (isospin-symmetric Majorana DM)
- SI velocity-suppression factor (Majorana: ~4 orders of magnitude vs SD)
- Eq. 32 vs Eq. 33 — full NREFT integral vs simplified dominant-term

### Risks

- **UFO not advertised public.** Built via FeynRules 2.0 + author chain. Ping
  authors first; if no luck, rebuild.
- **Per-BP σ_SI/σ_SD values live in Figs. 3-5, not tables.** Need to either
  digitize (fragile) or generate our own pinned numbers via the analytic chain
  + MadDM and treat consistency-with-paper as a Tier-3 figure-anchor task.
- Per-nucleus xenon isotope abundances in cited Del Nobile 2021, not in this
  paper — copy into `constants.py` once and document the source.

---

## Paper 3 — arXiv:2509.08043 (Hu/Cesarotti/Slatyer GCE 2HDM+a + secluded hypercharge)

**Suggested directory:** `eval/2509.08043_gce_2hdma_secluded/`

**Why we accepted (8/10 — strongest of the new set):** Eq. 50 is a textbook
closed-form 5-parameter scaling for σ_SI with explicit anchor 2.2×10⁻⁴⁹ cm².
Eq. 27 thermal relic anchor 4.4×10⁻²⁶ cm³/s. **Uses public Bauer 2HDM+a UFO**
(Bauer:2017ota) — zero UFO build cost. Two model classes (secluded hypercharge
+ 2HDM+a) cover natural diversity.

### Equations to pin (Phase 3)

- [ ] Eq. 24 — secluded ⟨σv⟩
- [ ] Eq. 27 — thermal relic anchor ⟨σv⟩_th ≃ 4.4×10⁻²⁶ cm³/s for Dirac DM
- [ ] Eqs. 36-40 — DD scalings
- [ ] Eqs. 41-42 — 2HDM+a ⟨σv⟩
- [ ] Eq. 44 — σ_SI exact (with loop function G(m_χ²/m_a², 0))
- [ ] **Eq. 50 — σ_SI scaling** with explicit anchor (the headline test)
- [ ] Eqs. 54-55 — gamma-ray line

### Pinned numerics

Eq. 50 anchor (the cleanest Tier-1/Tier-2 target in the new set):
```
σ_SI ≈ 2.2×10⁻⁴⁹ cm²
       × (m_A/800 GeV)⁴
       × (m_a/50 GeV)⁻⁴
       × (m_χ/30 GeV)²
       × (θ/0.1)⁴
       × (g_χ/0.5)⁴
       × (⟨N|Σm_q q̄q|N⟩/330 MeV)²
```

Generates infinite Tier-2 BPs by parameter rescale; pick ~5 anchor points to pin.

### Risks

- **No MadDM** — relic computed analytically. The MadGraph side is collider
  only (m_χχjj VBF or s-channel). Don't try to wedge MadDM in for this paper;
  scope the eval to algebraic-identity tests + public Bauer UFO MG cross-checks.
- **No per-BP table with paired (σ_SI, Ωh²)** — observables in exclusion plots
  (Figs. 9-12). The Eq. 50 scaling is enough for our purpose; don't fight it.
- **Bauer UFO** — pull from the public repo; document the version pin in
  `madgraph/README.md`.

---

## Paper 4 — arXiv:2511.21808 (Comprehensive WIMP study of Fermi-LAT GCE)

**Suggested directory:** `eval/2511.21808_gce_wimp_comprehensive/`

**Why we accepted:** ~10 portal classes (Higgs portals, scalar/pseudoscalar/
vector simplified mediators, ZZ portal, U(1)_Li−Lj, U(1)_B−L). Both
**MadDM and micrOMEGAs are used** in parallel — natural two-route check.
Table 2 has 4 BPs with (mDM, ⟨σv⟩, χ²); 14 closed-form equations across
portals.

**Scope discipline:** Don't try to cover all 10 models. **Pick the 4 with
Table 2 numerics** (Lμ-Le, Le-Lτ, Lμ-Lτ, B-L) plus one Higgs portal, and
ship that. The remaining 5 are stretch.

### Equations to pin (Phase 3)

- [ ] Eqs. 6, 7, 8 — Higgs-portal ⟨σv⟩
- [ ] Eqs. 13, 14 — simplified-mediator ⟨σv⟩
- [ ] Eq. 25, 38 — Z' portal ⟨σv⟩
- [ ] Eq. 9 — Higgs-portal σ_SI
- [ ] Eqs. 15, 17 — simplified-mediator σ_SI/σ_SD
- [ ] Eq. 26, 39, 44 — Z' portal σ_SI/σ_SD
- [ ] Eqs. 27, 28, 29 — mediator decay widths

### Pinned numerics (Table 2)

- Lμ-Le: mDM = 44.1 GeV, ⟨σv⟩ = 7.58×10⁻²⁶ cm³/s, χ² = 5.2
- Le-Lτ: mDM = 19.2 GeV, ⟨σv⟩ = 3.03×10⁻²⁶ cm³/s, χ² = 16.5
- Lμ-Lτ: mDM = 20.5 GeV, ⟨σv⟩ = 3.76×10⁻²⁶ cm³/s, χ² = 28.5
- B-L: mDM = 37.5 GeV, ⟨σv⟩ = 4.67×10⁻²⁶ cm³/s, χ² = 6.2

Plus per-model Higgs-portal/Z'-portal coupling values in body text:
mDM−mh/2 ≃ −0.025 GeV, λ ≃ 2×10⁻⁴ (scalar Higgs); λ ≃ 3.5×10⁻⁴ (vector Higgs);
Z' (mZ'=120 GeV, vector) λ ∼ 5×10⁻⁴; Z' axial λ ∼ 2.5×10⁻².

### Risks

- **UFO availability not stated.** May need to build per portal. Start with
  one portal (B-L is canonical) end-to-end before scaling to others.
- **No quantitative MadDM↔micrOMEGAs validation** — fails criterion 4 narrowly
  even though both tools are used.
- **σ_SI/σ_SD/Ωh² NOT tabulated per model** — only LZ-style contour plots.
  Pinning DD numbers requires running our closed-form Eqs. 9/15/17/26/39/44
  ourselves, not checking against published values.

---

## Paper 5 — arXiv:2509.15121 (Shedding Light on DM at the LHC with ML, NMSSM)

**Suggested directory:** `eval/2509.15121_nmssm_ml_blind_spot/`

**Why we accepted:** Tables 7-8 with **fully pinned BPs** (m_χ values to 0.1
GeV, σ_DD^SI=1.3e-48 and 4.2e-48 cm², Ωh²=0.1, production σ=105.1 fb).
**Eq. 7 NMSSM bino/higgsino blind-spot identity** confirmed exact:
(m_χ̃₁⁰ + g₁²v²/(M₁ − m_χ̃₁⁰)) · 1/(μ_eff sin 2β) ≃ 1.

### Equations to pin (Phase 3)

- [ ] Eqs. 3-5 — neutralino mass-matrix diagonalization
- [ ] Eq. 6 — compression parameter ε
- [ ] **Eq. 7 — NMSSM bino/higgsino blind-spot identity** (Tier 3 anchor)
- [ ] Eq. 15 — SI cross-section rescaling for sub-relic DM

### Pinned numerics (Tables 7-8)

- BP1-3: m_χ₁⁰ = 147.5 GeV, m_χ₂⁰ = 158.5 GeV, m_χ₃⁰ = 164.8 GeV;
  σ_DD^SI = 1.3×10⁻⁴⁸ cm²; Ω_χh² = 0.1; Z_BL = 6.29, Z_MLL = 6.67
- BP9-3: m_χ₁⁰ = 235.1 GeV, m_χ₂⁰ = 245.0 GeV, m_χ₃⁰ = 251.7 GeV;
  σ_DD^SI = 4.2×10⁻⁴⁸ cm²; Ω_χh² = 0.07
- Production: σ(pp → χ̃₁⁺χ̃₂⁰j) = 105.1 fb

### Risks

- **No MadDM** — micrOMEGAs/NMSSMTools are the DM-observable engines. The MG
  side is production cross sections only.
- **NMSSM UFO** — standard FeynRules NMSSM model. Should be straightforward
  pull from the FeynRules database. Document version pin.
- **ML scoring is out of scope.** We pin Eq. 7 + Tables 7-8 numerics, and
  reproduce the production σ via MG5+UFO. The ML "improvement over cut-and-
  count" claim is ungraded.
- **Many BPs (BP1-1 through BP9-3 pattern)** — pick 3-5 representative ones
  rather than all of them.

---

## Cross-cutting work

After all five papers are extracted:

- [ ] Update `eval/README.md` with the new paper table
- [ ] Add per-paper rows to `eval/tasks/tier1_setup.yaml`,
      `tier2_accuracy.yaml`, `tier3_advanced.yaml`
- [ ] Re-run `python -m eval.harness.run --runner reference` end-to-end —
      target 35 + N tasks all passing on the reference runner before any
      Claude run
- [ ] Run Claude with skills against tier 3 to actually close out the
      "tiers 1-3 working on Claude" claim from the 2026-04-18 status review
- [ ] Update `CASE_STUDY.md` if the expansion surfaces new bugs in our
      reference implementation (it probably will — every paper has factor-of-2
      conventions waiting to bite)

## Suggested execution order

1. **2509.08043 first** (Eq. 50 + public Bauer UFO is the lowest-effort win;
   gives us a clean 2HDM+a benchmark immediately).
2. **2509.15121 second** (Tables 7-8 + Eq. 7 blind-spot is a clean NMSSM
   benchmark; standard NMSSM UFO).
3. **2603.23040 third** (the only MadDM-using paper — strongest tool-fit
   evidence; but UFO build is heavier).
4. **2601.13147 fourth** (rich content but UFO build cost; defer GW/EWPT
   extension to Tier-3 stretch).
5. **2511.21808 last** (largest surface area; scope to 4 Table-2 portals
   first, treat the other 6 as stretch).
