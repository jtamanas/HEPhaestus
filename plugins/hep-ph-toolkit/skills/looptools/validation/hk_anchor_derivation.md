# Independent analytic anchor for the 2HDM+a loop-induced SI cross section

**Purpose.** An independent magnitude anchor for σ_SI(p), σ_SI(n) of the 2HDM+a
benchmark point, computed in closed form (one-loop box + heavy-quark gluon
matching) **without** FeynArts/FormCalc/LoopTools. It is meant to bound the
order of magnitude that the numerical chain (`run_eval.wls`) should reproduce —
**but read the COVERAGE section: this anchor and the LoopTools number are not
the same quantity.**

Artifacts:
- `hk_anchor.py` — the calculation (Feynman-parameter loop integral → f_N → σ).
- this file — derivation, conventions, inputs, intermediate numbers, coverage,
  uncertainty.

---

## 1. Result (headline)

| quantity | value |
|---|---|
| σ_SI(proton)  | **2.2 × 10⁻⁵⁴ cm²** (central), band **~5×10⁻⁵⁵ – 2×10⁻⁵⁴**, reliable to a factor ~5 |
| σ_SI(neutron) | **2.2 × 10⁻⁵⁴ cm²** (central), essentially equal to proton |
| f_p, f_n | 7.20×10⁻¹⁴, 7.18×10⁻¹⁴ GeV⁻² |
| dominant quark | **bottom** (tan²β-enhanced), top ~16× smaller (cotβ-suppressed) |

This is **far below the neutrino floor** (~10⁻⁴⁸–10⁻⁴⁹ cm²) and far below current
LZ/XENONnT sensitivity (~10⁻⁴⁷–10⁻⁴⁸ cm²). For this benchmark the
mediator-quark-loop SI signal is unobservable.

**Correction to the brief's premise.** The brief expected the *top* loop to
dominate. It does not: at tanβ=10 the down-type coupling carries tanβ=10 and the
up-type carries cotβ=0.1, so after the (correct, chirality-restoring) loop
structure the **bottom** box dominates the box contribution by ~16× over the top.

---

## 2. Model, conventions, inputs

Benchmark from `plugins/hep-ph-toolkit/skills/looptools/tests/fixtures/two_hdm_a_point.slha`:

| param | value | source |
|---|---|---|
| Mχ (Dirac singlet DM) | 100 GeV | MASS 9989932 |
| Ma (pseudoscalar mediator a) | 400 GeV | MASS 36 |
| MH± | 500 GeV | MASS 37 (EW box only) |
| MW | 80.379 GeV | MASS 24 |
| mt, mb | 173, 4.18 GeV | MASS 6, 5 |
| tanβ | 10 | HMIX 2 |
| α (CP-even mixing) | 1.0 | FRALPHA 1 — **does not enter** the pseudoscalar box |
| gχ | 1.0 | DMPORTAL 1 |
| v | 246 GeV | standard |
| mc, ms, md, mu | 1.27, 0.095, 4.7e-3, 2.2e-3 GeV | PDG (subdominant) |

**Coupling conventions** (identical to `2hdm-a/SKILL.md` reference Lagrangian and
the hand-crafted SARAH model vertices):

```
L ⊃ i gχ a (χ̄ γ5 χ)                         (DM–mediator, no 1/2)
L ⊃ i (m_q/v) ξ_q a (q̄ γ5 q)                (quark–mediator)
```

with the aligned Type-II 2HDM+a scaling
**ξ_up(u,c,t) = cotβ = 0.1**, **ξ_down(d,s,b) = tanβ = 10**.

*a–A⁰ mixing.* In the full 2HDM+a the physical light mediator is
a = cosθ·a₀ − sinθ·A⁰ and its couplings carry sinθ (to doublet-like states /
top: ξ_t^phys = −cotβ·sinθ) and cosθ (to DM). The benchmark SLHA fixes **neither
θ nor m_A⁰**. We therefore work in the **single-pseudoscalar simplified-model
limit** (sinθ→1, the a–A⁰ mixing folded into gχ and ξ_q), which is exactly what
the committed SARAH model encodes (`i gχ a χ̄χ`, `(m_q/v)ξ_q a q̄iγ5q`, no θ) and
what the brief's stated convention prescribes. Re-introducing a realistic
sinθ<1 would *reduce* the up-type (top) piece further; the bottom piece scales
with cosθ²·(coupling)² similarly. This is flagged as an assumption (§7).

**Cross-section convention** — matched to `scripts/match_nucleon.py` exactly:
σ_SI^N = (4/π) μ_N² f_N²  [GeV⁻²], σ[cm²]=σ[GeV⁻²]·(ħc)², ħc=0.1973269804 GeV·fm,
GEV2_TO_CM2 = 3.8937937×10⁻²⁸ cm²/GeV⁻², μ_N = Mχm_N/(Mχ+m_N).

**Nucleon form factors, preset `default_2018`.** The numeric values are *not*
committed in-repo (`run_eval.wls` defers them to micrOMEGAs built-ins). They are
the standard micrOMEGAs lattice defaults, identical to Abe–Fujiwara–Hisano
(arXiv:1810.01039) Table 4 — **flagged** as reconstructed-from-literature:

| | f_Tu | f_Td | f_Ts | f_TG = 1−Σf_Tq |
|---|---|---|---|---|
| proton  | 0.0153 | 0.0191 | 0.0447 | 0.9209 |
| neutron | 0.0110 | 0.0273 | 0.0447 | 0.9170 |

Because the dominant operator is the DM–gluon one (f_TG≈0.92), the result is
insensitive (~2%) to the light-quark σ-term choice; the `default_2018` vs `A1`
preset distinction is negligible here.

---

## 3. Why tree level vanishes and which loop dominates

The mediator a is CP-odd. The tree-level operator is
(gχ/Ma²)(m_q/v)ξ_q (χ̄iγ5χ)(q̄iγ5q): both bilinears are momentum-suppressed in
the non-relativistic limit ⇒ σ_SI^tree ≈ 0 (CP-forbidden). The leading SI signal
is loop-induced.

The **box** (two a-mediators, one SM quark in the loop; Fig. 1 of
arXiv:1711.02110) generates the *un*-suppressed scalar operator (χ̄χ)(q̄q). For
heavy quarks Q=c,b,t this is matched onto the DM–gluon operator via the
trace-anomaly / heavy-quark expansion. This is the
**Haisch–Kahlhoefer–type contribution** — see references in §6.

---

## 4. The box Wilson coefficient (full derivation)

Forward elastic χ(p)Q(k)→χ(p)Q(k), zero momentum transfer, p²=Mχ², k²=m_Q²,
p·k=Mχm_Q (both at rest at threshold). Vertices: −gχγ5 (DM), −c_Q γ5 (quark),
c_Q≡(m_Q/v)ξ_Q. Two diagrams: uncrossed and crossed.

**Numerators** (using p̸u=Mχu, k̸u=m_Q u, and ū(p)γ^μu(p)=2p^μ):
- DM line (both diagrams): ū_χ γ5(p̸−ℓ̸+Mχ)γ5 u_χ = ū_χ ℓ̸ u_χ = 2 p·ℓ.
- quark, uncrossed (internal k+ℓ): ū_Q γ5(k̸+ℓ̸+m_Q)γ5 u_Q = −2 k·ℓ.
- quark, crossed (internal k−ℓ): ū_Q γ5(k̸−ℓ̸+m_Q)γ5 u_Q = +2 k·ℓ.

The m_Q terms cancel in each numerator; the **opposite sign** between crossed and
uncrossed is the crucial point. It makes the two boxes *subtract*, so the scalar
coefficient ∝ (J_cross − J_uncross) → 0 as m_Q→0 — the **chirality flip** a
scalar quark bilinear must have. (Implemented and verified numerically.)

**Amplitudes** (i⁴=+1 from the four propagators; common factor gχ²c_Q²):
```
iM_uncross = −4 gχ²c_Q² ∫ d⁴ℓ/(2π)⁴ (p·ℓ)(k·ℓ)/[D_χ D_Q^+ D_a²]
iM_cross   = +4 gχ²c_Q² ∫ d⁴ℓ/(2π)⁴ (p·ℓ)(k·ℓ)/[D_χ D_Q^- D_a²]
```
D_χ=ℓ²−2p·ℓ, D_Q^±=ℓ²±2k·ℓ, D_a=ℓ²−ma².

**Feynman parameters** (n=4, doubled a-propagator; shift ℓ→ℓ+L; Wick rotation;
∫ℓ²/(ℓ²−Δ)⁴ and ∫1/(ℓ²−Δ)⁴ standard). The (z,w) parameters of the doubled
propagator collapse via the δ-function to a single factor s=1−x−y. Result:

```
α_Q = (gχ² c_Q² / 16π²) · J_total(Mχ, m_Q, ma)          [coeff of (χ̄χ)(Q̄Q)]

J_total = J_cross − J_uncross,
J_sign  = ∫₀¹dx ∫₀^{1−x}dy (1−x−y) [ (x Mχ ∓ y m_Q)² / Δ_∓²  −  1/(2Δ_∓) ],
Δ_∓     = (x Mχ ∓ y m_Q)² + (1−x−y) ma² ,
   uncrossed: sign −  (x Mχ − y m_Q);  crossed: sign +  (x Mχ + y m_Q).
```

Both integrals are UV-finite (box ~∫d⁴ℓ/ℓ⁶). Evaluated by `scipy.dblquad`.

**Heavy-quark → gluon / nucleon matching** (textbook, e.g. Hisano; SVZ):
```
f_N = m_N [ Σ_{q=u,d,s} f_Tq^N (α_q/m_q) + (2/27) f_TG^N Σ_{Q=c,b,t} (α_Q/m_Q) ]
```
This is exactly the matching `run_eval.wls` advertises (its lines 92–94), and the
2/27·f_TG appears identically in arXiv:1711.02110 Eq. (1.12).

**Cross-check of normalisation.** Writing σ=(1/π)μ²|C_N|² ⇔ σ=(4/π)μ²f_N² gives
f_N=C_N/2; matching our f_N to Arcadi et al. Eq. (1.11)–(1.12)
σ=(μ²/π)c_a⁴gχ⁴|F_l|², F_l=(2/27)f_TG Σ_q (m_q m_p/v²)C_{S,q}, yields
C_{S,Q} = −J_total/(8π²): our Feynman-parameter J_total **is** their (unquoted,
"lengthy") box function C_{S,q} up to the constant −1/(8π²). Structure and
normalisation therefore agree with the published formula.

---

## 5. Intermediate numbers (from `hk_anchor.py`)

Per-quark box (J_total in GeV⁻², α_Q = coeff of (χ̄χ)(Q̄Q) in GeV⁻²):

| q | m_Q | ξ | c_Q=(m_Q/v)ξ | J_total | α_Q |
|---|---|---|---|---|---|
| c | 1.27 | 0.1 | 5.16e-4 | 7.40e-9 | 1.25e-17 |
| b | 4.18 | 10  | 0.170   | 2.42e-8 | 4.43e-12 |
| t | 173  | 0.1 | 0.0703  | 3.68e-7 | 1.15e-11 |

Contributions to f_p [GeV⁻²]: b 6.78e-14, t 4.26e-15, s 2.31e-17, c 6.29e-19,
rest negligible ⇒ **f_p = 7.20e-14**, f_n = 7.18e-14.

σ_SI(p) = (4/π)(0.9296)²(7.20e-14)²·3.894e-28 = **2.22e-54 cm²**;
σ_SI(n) = **2.22e-54 cm²**.

---

## 6. References (cited equations)

1. **G. Arcadi, M. Lindner, F. S. Queiroz, W. Rodejohann, S. Vogl**,
   "Pseudoscalar Mediators: A WIMP model at the Neutrino Floor", arXiv:1711.02110.
   Eq. (1.10) heavy-quark gluon matching m_Q Q̄Q=−(α_s/12π)G²; Eq. (1.11)
   σ=(μ²/π)c_a⁴gχ⁴|F_l|²; Eq. (1.12) F_l=(2/27)f_TG Σ_q (m_q m_p/v²)C_{S,q}.
   **Primary structural reference for this anchor.**
2. **T. Abe, M. Fujiwara, J. Hisano**, "Loop corrections to dark matter direct
   detection in a pseudoscalar mediator dark matter model", JHEP 02 (2019) 028,
   arXiv:1810.01039. Box C_q^box (Eq. 3.40), DM-gluon two-loop C_G^box (3.45–46),
   triangle C_q^tri (3.35–36) [**finds the triangle DOMINANT**]; nucleon coupling
   C_N (3.29); σ_SI=(1/π)μ²|C_N|² (3.28); form factors **Table 4** (= our
   `default_2018`). Their two-loop C_G^box is the O(1) refinement of our naive
   2/27 matching ("top overestimated, charm/bottom underestimated").
3. **U. Haisch, F. Kahlhoefer (J. Unwin)**, arXiv:1208.4605 (JHEP 07 (2013) 125),
   "The impact of heavy-quark loops…": the heavy-quark-loop → DM-gluon mechanism
   the brief refers to as the "Haisch–Kahlhoefer calculation".
4. **M. Bauer, U. Haisch, F. Kahlhoefer**, "Simplified DM models with two Higgs
   doublets: I. Pseudoscalar mediators", JHEP 05 (2017) 138, arXiv:1701.07427:
   the 2HDM+a model and Type-II coupling ξ_t=−cotβ, DM coupling ∝cosθ (Eqs. 7–8).
5. **S. Ipek, D. McKeen, A. E. Nelson**, PRD 90 (2014) 055021, arXiv:1404.3716 —
   original pseudoscalar-mediator loop-SI box.

---

## 7. COVERAGE statement (read before comparing to LoopTools)

**This anchor computes ONLY the mediator(a) × quark-loop box → (gluon/quark scalar
operator).** It does **NOT** include, and the benchmark SLHA does **not pin
down**, two other pieces of the full 2HDM+a SI signal:

- **EW A⁰H±W∓ box** (charged Higgs + W). A genuinely electroweak contribution.
  Requires the a–A⁰ mixing θ and m_A⁰ (and uses MH±=500, MW=80.4) — θ and m_A⁰
  are absent from the SLHA. Crude dimensional estimate
  f_EW ~ (g₂²/16π²)·(gχ sinθ)·(m_N/M²) puts it in the same ballpark as, up to ~10²×
  larger than, the box-gluon piece, but still ≪ neutrino floor. **Not computable
  from this benchmark.**
- **Triangle** (effective hχχ/Hχχ vertex × Higgs Yukawa). Abe–Fujiwara–Hisano
  find this **DOMINATES** the SI rate. It needs the scalar trilinears g_haa,
  g_Haa (i.e. potential quartics c₁,c₂ / the SARAH `lamP` portal) and θ, m_A⁰ —
  **none in the SLHA**. **Not computable from this benchmark.**

**Fraction of total covered.** For the *full* 2HDM+a the triangle can be orders
of magnitude larger, so this box anchor may cover only a *small* fraction of the
true SI rate. For the **minimal single-pseudoscalar simplified model actually
encoded by the SLHA** (no trilinears, no θ, no m_A⁰), the box **is** the leading
well-defined piece, and this anchor covers it at leading order (missing only the
O(2–3) two-loop C_G^box refinement).

**Crucial for the LoopTools comparison.** `2hdm-a/SKILL.md` says the runtime chain
evaluates the **"charged-Higgs/W box + mediator triangle"** — i.e. *different*
contributions from this anchor. So this anchor is **not a like-for-like check** of
the LoopTools number unless LoopTools also includes the quark-loop→gluon box. If
the LoopTools number is much *larger* than 2×10⁻⁵⁴ cm², that is **expected** (it
would be the EW box and/or the trilinear-dependent triangle), not a discrepancy.
Use this anchor as a **lower-bound order-of-magnitude sanity check** on the
mediator-loop sector, not as the target value.

---

## 8. Uncertainty (no false precision)

- **Heavy-quark matching** (naive 2/27·f_TG of the box-induced Q̄Q vs the full
  two-loop C_G^box of AFH): factor ~2–3. The **dominant (bottom) term is exactly
  where this is least reliable** (AFH: charm/bottom underestimated by the naive
  approach) — **the single biggest flag.**
- **Renormalisation scale / quark mass scheme:** using m_b(MSbar, μ≈100 GeV)≈2.8
  GeV instead of 4.18 drops σ to 5.2e-55 (×0.23). Since bottom dominates and
  enters ~m_b²-like, this is a real factor ~4 swing.
- **Form-factor preset / σ-terms:** negligible (~2%, gluon-dominated).
- **a–A⁰ mixing sinθ→1 assumption (§2):** realistic sinθ<1 only *reduces* σ.
- **Velocity / momentum-transfer corrections:** negligible.

**Quoted band:** σ_SI(p) ≈ σ_SI(n) ≈ **2×10⁻⁵⁴ cm², reliable to a factor ~5**
(≈5×10⁻⁵⁵ – 1×10⁻⁵³). Order of magnitude (10⁻⁵⁴) is robust for the box piece.

---

## 9. Items for the adversarial reviewer to scrutinise

1. The **relative sign of crossed vs uncrossed box** (§4): it controls whether the
   boxes subtract (chirality-correct, J_total→0 as m_Q→0, our result) or add
   (would inflate σ by ~10⁶). Verified via γ5 algebra and the m_Q→0 limit.
2. The **Feynman-parameter J_total** is our own derivation standing in for the
   "lengthy" published C_{S,q}; the normalisation cross-check (C_{S,Q}=−J_total/8π²)
   is the main external validation but the absolute factor deserves a check.
3. **Naive 2/27 matching for the dominant bottom** quark (§8) — the largest
   normalisation uncertainty.
4. **default_2018 form-factor values reconstructed from AFH Table 4 /** micrOMEGAs,
   not from in-repo data (none exists).
5. The **coverage mismatch** (§7): anchor = quark-loop box; LoopTools (per SKILL) =
   EW box + triangle. Confirm what `run_eval.wls` actually sums before comparing.
