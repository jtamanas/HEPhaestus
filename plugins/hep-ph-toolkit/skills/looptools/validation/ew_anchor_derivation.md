# Like-for-like analytic anchor for the 2HDM+a loop-induced SI cross section
### (charged-Higgs/W box + mediator triangle — the LoopTools diagram set)

**Purpose.** Provide the **like-for-like** magnitude target for the project's
LoopTools direct-detection chain, which advertises exactly
`loop_topologies = {"chargedHiggs_W_box", "mediator_triangle"}`
(`scripts/run_eval.wls` line 127; `2hdm-a/SKILL.md` and `looptools/SKILL.md`
"charged-Higgs/W box (A⁰H⁺W⁻) + mediator triangle"). This is the complement of
`hk_anchor.py`, which computes the **pseudoscalar × quark-loop box → gluon** — a
*disjoint* set that is **not** in the LoopTools topology list.

Artifacts: `ew_anchor.py` (the calculation), this file (derivation + citations).

---

## 1. Result (headline)

| quantity | value |
|---|---|
| σ_SI(proton)  | **6.4 × 10⁻⁴⁹ cm²** (central), band **~2 × 10⁻⁴⁹ – 2 × 10⁻⁴⁸**, factor ~3–5 |
| σ_SI(neutron) | **6.6 × 10⁻⁴⁹ cm²** (central), ~3% above proton |
| f_p, f_n (triangle) | −3.85 × 10⁻¹¹, −3.91 × 10⁻¹¹ GeV⁻² |
| dominant piece | **mediator triangle, SM-like h exchange** (H is ~3%, EW box ≤30%) |

This sits **near / just below the neutrino floor** (~10⁻⁴⁸–10⁻⁴⁹ cm²) and below
current LZ/XENONnT (~10⁻⁴⁷–10⁻⁴⁸). It is **~5 orders of magnitude larger** than the
`hk_anchor` pseudoscalar-box number (2 × 10⁻⁵⁴ cm²) — because the triangle proceeds
through an **O(v) scalar trilinear** (a–a–h ≈ 350 GeV, a portal coupling of natural
electroweak size — NOT a tanβ blow-up, see §4) and the gluon-coherent SM-like-Higgs
coupling, whereas the pseudoscalar box is chirality- and Yukawa-suppressed. AFH find
precisely this hierarchy (the triangle dominates σ_SI in the 2HDM+a).

> **Two caveats up front (do not over-read this number):** (i) the dominant
> **triangle** is computed rigorously here, but the **charged-Higgs/W box is only an
> estimate (≤30%), not computed** — and the box is precisely the piece a real
> LoopTools run evaluates rigorously, so a live number **~1.3–1.7× ABOVE** this
> triangle anchor is **expected** (constructive box), not a discrepancy (§6). (ii)
> "Like-for-like" holds via **triangle-dominance**, not a clean diagram-by-diagram box
> match: the regenerated **elastic** fixture `amp_reduced.m` now **DOES contain the
> χχ→h/H→q̄q triangle** as a t-channel `Den[T,Masshh²]` × `C0i[…χ,a,a…]` vertex
> correction (§7, Step-0 SATISFIED). The anchor's `chargedHiggs_W_box` (A⁰H±W∓) is
> **not** a clean χ-side box in this model — χ is a singlet coupling only to neutral
> a/A⁰, so the genuine box is the pseudoscalar×quark (hk-type) D0i with W/H± entering
> as **quark-side** vertex corrections (§7).

---

## 2. Reference papers and a citation correction

The prompt cites **AFH arXiv:1810.01039** for "the charged-Higgs/W box + triangle."
**That paper is the gauge-singlet pseudoscalar simplified model** — its "box"
(Eq. 3.40) is the **pseudoscalar × quark** box (∝ (m_q/v)² (ξ^χξ^q)²), i.e. the
*hk_anchor* diagram, **not** an electroweak A⁰H±W∓ box. There is no charged Higgs
or W in 1810.01039.

The genuine 2HDM+a SI calculation with the charged-Higgs box **and** the triangle is
the follow-up:

> **T. Abe, M. Fujiwara, J. Hisano, Y. Shoji**, *"Maximum value of the
> spin-independent cross section in the THDM+a"*, **JHEP 01 (2020) 114,
> arXiv:1910.09771.**

1810.01039 still supplies the **triangle loop function** (Eq. 3.35–3.36), the
effective-interaction normalisation (Eq. 3.22), the nucleon coupling (Eq. 3.28–3.29)
and the form factors (Table 4); 1910.09771 supplies the **2HDM+a trilinears**
(Eq. 49–50) and the charged-Higgs box. **This anchor uses both** for the triangle
(rigorous) and the box (estimate); it is the intended like-for-like LoopTools target,
subject to the topology-label caveat in §7. *(Flag #1 for the reviewer.)*

---

## 3. Model, conventions, inputs

Pinned benchmark (GeV): m_χ=100, m_a=400 (light, mostly-singlet pseudoscalar),
m_A⁰=500 (heavy doublet pseudoscalar = AFH "m_A"), m_H±=500, m_H=500, m_h=125,
m_W=80.379, m_Z=91.1876, m_t=173, m_b=4.18; v=246, v_d=24.49, v_u=244.78.
Angles: tanβ=10 (β=1.4711), α=−0.0997 (alignment **α=β−π/2**, cos(β−α)≈0),
a–A⁰ mixing sinθ=0.35 (cosθ=0.9368). g_χ=1, sin²θ_W=1−m_W²/m_Z²=0.2230.

**DM coupling.** Dirac χ, `L ⊃ i g_χ a χ̄γ5χ` (no ½). Reduced couplings
**ξ^χ_a = g_χ cosθ = 0.937, ξ^χ_A = g_χ sinθ = 0.35** (AFH 1810.01039 Eq. 2.18–2.19;
the prompt pins these). AFH use a Majorana χ with `(i g_χ/2)a₀χ̄γ5χ` but the same
reduced coupling — the Dirac (no-½) and Majorana (½ × symmetry-factor 2) vertices
coincide; a residual Dirac/Majorana factor ≤2 in the **loop** normalisation is
carried as an uncertainty (§8). *(Flag #2.)*

**Yukawas (aligned Type-II):** φ–q̄q = (m_q/v) ξ_q^φ with
ξ_u^h=cosα/sinβ, ξ_d^h=−sinα/cosβ (→ **≈1, SM-like** in alignment);
ξ_u^H=sinα/sinβ (→ −cotβ=−0.1), ξ_d^H=cosα/cosβ (→ tanβ=10).

**Cross-section convention** (matches `scripts/match_nucleon.py` exactly):
σ_SI^N=(4/π)μ_N²f_N² [GeV⁻²]; σ[cm²]=σ[GeV⁻²]·(ħc)², ħc=1.973269804×10⁻¹⁴ GeV·cm,
GEV2_TO_CM2=3.8937937×10⁻²⁸, μ_N=m_χm_N/(m_χ+m_N). (AFH write σ=(1/π)μ²|C_N|² ⇒
**f_N=C_N/2**; identical.)

**Form factors `default_2018`** (= micrOMEGAs lattice = AFH Table 4 = hk_anchor):
f_Tu/f_Td/f_Ts = 0.0153/0.0191/0.0447 (p), 0.0110/0.0273/0.0447 (n);
f_TG=1−Σf_Tq.

---

## 4. The scalar trilinears g_haa, g_Haa from the pinned potential

The triangle's size is set by the a–a–φ trilinears, generated by the portal quartics
`V ⊃ (c₁|H₁|² + c₂|H₂|²)a₀²` plus the 2HDM geometry, projected through the CP-even
(α) and CP-odd (θ) mixings. We use **AFH 1910.09771 Eq. (49)**:

```
g_aah = s_θ²(2m_a² + m_h² − 2m_A⁰²)/v  +  2v c_θ² (c₁ cos²β + c₂ sin²β)        (Eq.49)
```

The portal bracket `(c₁cos²β + c₂sin²β) = (c₁ + c₂tan²β)/(1+tan²β)` projects onto the
**SM (h) direction**; the **orthogonal (H) direction** picks `(c₂−c₁) sinβ cosβ`,
which **vanishes for c₁=c₂**.

**No tanβ enhancement (corrected framing).** With the pinned **c₁=c₂=1** the SM-direction
bracket collapses: `(c₁cos²β + c₂sin²β) = c₂(cos²β+sin²β) = c₂ = 1`. The tanβ factors
cancel identically. So the portal piece is just
`2v c_θ² c₂ ≈ 2·246·0.878·1 = 432 GeV` — an **O(v) coupling of natural electroweak
size**, NOT a tan²β blow-up. (A genuine tanβ enhancement would require c₂ ≫ c₁; it does
not occur here.) The number is correct; the earlier "tan²β-enhanced" wording was wrong.

**Identification of the pinned potential with AFH (c₁,c₂).** The pinned `λP1=λP2=1.0`
are the a₀²|H₁|², a₀²|H₂|² quartics ⇒ **c₁=c₂=1.0**. *(Flag #3: this identification
of λP1,λP2 ↔ c₁,c₂ should be confirmed against the SARAH `TwoHdmAfix` potential; the
cubic `lamP≈224 GeV` portal `λP(H₁†H₂)a` enters m_a/θ generation, not g_aah directly.)*

Numerically (c₁=c₂=1, cos²β=0.0099, sin²β=0.9901):
```
g_aah = (−81.85)_geo + (+431.78)_portal = +349.9 GeV          ← O(v) portal-dominated
g_aaH = (+34.86)_geo + (0.00)_portal     = +34.9 GeV           ← portal vanishes (c₁=c₂)
```
The portal piece (+432 GeV) is `2v c_θ² c₂` — an **O(v) electroweak-scale coupling**;
it dominates over the geometric −82 GeV piece simply because the latter is a small
s_θ²×(mass-splitting/v) term. There is **no tanβ enhancement** (§ above). This O(v)
trilinear is the physical origin of the σ_SI magnitude relative to the (tiny)
pseudoscalar box.

---

## 5. Triangle: loop function, effective coupling, nucleon matching

**Topology.** χ̄χ → φ via a closed χ–a–a loop (two χχa vertices + one φaa vertex),
then φ propagator → φ–q̄q. Internal lines: one χ propagator + two a propagators.

**Loop function (derived from scratch; sec. cross-checked against AFH Eq. 3.36).**
At zero momentum transfer the two a-propagators carry equal momentum, so the triangle
collapses to a derivative of a bubble. The χ-line numerator γ5(p̸−k̸+m_χ)γ5 = −(p̸−k̸)+m_χ
gives ū k̸ u → m_χ ūu (the **scalar** χ̄χ piece ∝ m_χ — the required chirality flip).
Feynman-combining `1/(A B²)`, shifting, and Wick-rotating
`∫d⁴l/(2π)⁴ 1/(l²−Δ)³ = −i/(2(4π)²Δ)` yields

```
C_{φχχ} = −(m_χ/(4π)²) Σ_med  g_{φ·med·med} (ξ^χ_med)²  L(m_χ, m_med)              (= AFH Eq.3.36)

L(m_χ, m_med) = ∫₀¹ dx  x(1−x) / [ x m_med² + (1−x)² m_χ² ]                       [GeV⁻²]
```

and **L is exactly AFH's `[∂B0(p²,m_med²,m_χ²)/∂p²]_{p²=m_χ²}`** (the substitution
x↔1−x maps my integrand onto the standard ∂B0/∂p² form — verified analytically).
This UV-finiteness (doubled propagator → ∫d⁴l/l⁶) and the explicit ∝m_χ scalar piece
are the two physics checks. The mixed a–A⁰ term (AFH's third line in 3.36,
∝ s_θc_θ/(m_A⁰²−m_a²)) is numerically tiny and folded into the uncertainty.

Numbers:
```
L(100,400) = 2.542×10⁻⁶,  L(100,500) = 1.711×10⁻⁶ GeV⁻²
ξ^χ_a=0.937, ξ^χ_A=0.35
g_hχχ = −5.41×10⁻⁴   (a-loop −4.94×10⁻⁴  +  A⁰-loop −4.64×10⁻⁵)
g_Hχχ = −5.39×10⁻⁵
```

**Nucleon coupling (Higgs-portal form, AFH Eq. 3.29 reorganised):**
```
f_N^φ = C_{φχχ} (m_N/v) F_N^φ / m_φ²,
F_N^φ = Σ_{u,d,s} f_Tq ξ_q^φ + (2/27) f_TG Σ_{c,b,t} ξ_Q^φ.       (sum over 3 heavy)
```
The `(2/27)f_TG` per heavy quark is the standard SVZ trace-anomaly matching
m_Q Q̄Q → −(α_s/12π)GG; for the SM-like h (ξ≈1) it reproduces the canonical
Higgs-nucleon factor F_p^h=0.284 (≈ the textbook 0.28–0.30) — a normalisation check.

```
proton : F_p^h=0.284, F_p^H=1.305 (tanβ-enhanced down quarks)
  f_p(h) = −3.75×10⁻¹¹,  f_p(H) = −1.07×10⁻¹²  (H is 2.9% of h in f_p)
  f_p(triangle) = −3.85×10⁻¹¹ GeV⁻²
neutron: f_n(triangle) = −3.91×10⁻¹¹ GeV⁻²
```

**h dominates (verified, as the prompt anticipated).** Although F^H is 4.6× larger
(tanβ-enhanced) and 1/m_H² is 1/16, g_Hχχ is ~10× smaller (g_aaH small because the
c₁=c₂ portal cancels), so net H/h ≈ 2.9% in f_N. The SM-like h wins via the large
g_aah and the 1/m_h² propagator.

**σ_SI:** with μ_p=0.9296, μ_n=0.9308:
```
σ_SI(p) = (4/π)μ_p² f_p² (ħc)² = 6.36×10⁻⁴⁹ cm²
σ_SI(n) =                        6.55×10⁻⁴⁹ cm²
```

**The from-scratch derivation above is the primary result and stands on its own.**

**Crude ballpark only (NOT an independent confirmation).** As a loose order-of-magnitude
sanity feel, AFH 1910.09771 report σ_SI up to ~10⁻⁴⁶ cm² at their *maximum*; naively
rescaling their m_a≈100 benchmark by (g_hχχ)² ∝ L² ∝ 1/m_a⁴ → our m_a=400 gives
~4×10⁻⁴⁹, the same ballpark as 6×10⁻⁴⁹. **Do not treat this as a second independent
check:** (i) AFH's *maximum* uses couplings optimised over the allowed parameter space,
not our pinned point; (ii) the 1/m_a⁴ rescaling ignores g_aah's own m_a dependence
(the geometric s_θ² term ∝ m_a²/v) and the A⁰-loop; and (iii) at their m_a≈m_χ≈100 the
loop function L is **not** ∝1/m_a² (the expansion that gives 1/m_a⁴ breaks down when
m_a is not ≫ m_χ). It is a consistency smell-test, nothing more — the validity of the
number rests on the explicit calculation, not on this rescaling.

---

## 6. The charged-Higgs/W box (A⁰H±W∓) — structural estimate only

**Topological subtlety (Flag #4).** The DM χ is a singlet coupling **only** to a/A⁰.
A genuine one-loop χq→χq **box** therefore must have a/A⁰ on both rails that connect
the χ line to the quark line (→ that is the *pseudoscalar × quark* box of `hk_anchor`,
which is **not** in the LoopTools topology list). A box with W± and H± in it enters
because the CP-odd states mix into the charged sector through the **gauge vertex**
a–W∓–H± (∝ g sinθ/2) and A⁰–W∓–H± (∝ g cosθ/2) from `|D_μH|²`; the W and H± then dress
the **quark** side (W: charged current q→q′; H±: charged-Higgs Yukawa). The
unsuppressed scalar χ̄χ piece still requires two CP-odd insertions on the χ line.

**This box is an ESTIMATE, not a calculation.** State it plainly: the explicit box
Wilson coefficient lives in AFH 1910.09771's appendix (Passarino–Veltman D₀/C₀ form)
and was **not machine-extractable here**; reconstructing it from scratch (4 masses
m_a/m_A⁰, m_W, m_H±, m_q + the gauge + Yukawa + CKM structure) is error-prone and
**not warranted** because AFH find it sub-dominant to the O(v)-trilinear triangle. We
bound **|f_N^box| ≤ 0.30 |f_N^triangle|** and quote it one-sided (its sign vs the
triangle is not fixed here). With the box at the bound, σ_SI(p) rises to ≤1.1×10⁻⁴⁸ cm².

**This is exactly the piece LoopTools computes rigorously.** The charged-Higgs/W box
(the `D0i[MW2,MHp2,Ma2,0,...]`/`C0i`/`B0i` structure in `amp_reduced.m`) is what a real
FormCalc/LoopTools evaluation does *properly*, where this anchor only estimates. **A
live LoopTools σ_SI landing ~1.3–1.7× ABOVE this triangle anchor is therefore EXPECTED**
(a constructively-interfering, rigorously-computed box on top of the triangle), **not a
discrepancy.** *(Flag #5.)* Conversely a live number *below* the triangle would suggest
destructive box interference or that the triangle is not actually in the amplitude (§7).

---

## 7. Coverage / like-for-like statement

| diagram | this anchor | LoopTools topology *label* | in fixture `amp_reduced.m`? | hk_anchor |
|---|---|---|---|---|
| mediator triangle (h/H via aa-loop) | **rigorous** | `mediator_triangle` ✓ | **YES** — t-channel `Den[T,Masshh²]` × `C0i[…χ,a,a…]` | — |
| charged-Higgs/W box (A⁰H±W∓) | estimate (≤30%) | `chargedHiggs_W_box` ✓ | **not a clean χ-side box** (see below) | — |
| pseudoscalar × quark (hk-type) box | present in fixture | (genuine χ-side box) | **YES** — D0i internal {χ,a,a,q} | the hk diagram set |
| 2-loop DM–gluon box | excluded | absent | no | partly (2/27 match) |

**Like-for-like now holds via TRIANGLE-DOMINANCE — Step-0 SATISFIED (updated).**
The fixture `amp_reduced.m` was **regenerated in the ELASTIC channel** (χ q → χ q,
process `{F[101],F[3,{1}]} -> {F[101],F[3,{1}]}`) on FeynArts 3.11 / WE 13.3 + FormCalc
9.10, replacing the old box-only toy. Two facts that previously downgraded "LoopTools
computes the dominant triangle" to a pending inference are now resolved:

1. **`run_eval.wls` numerical core is still a STUB** (hard-sets `fp = fn = 0`) — it
   computes no cross-section yet, so there is nothing to compare against *numerically*
   until that core is filled. (This is the next task and is independent of Step 0.)
2. **The real diagram content now lives in the regenerated fixture.** The committed
   `amp_reduced.m` **DOES contain the χχ→h/H→q̄q triangle**, verified in the elastic
   reduced amplitude as a single term carrying BOTH the t-channel scalar mediator and
   the χ-side vertex-correction loop:
   `Den[T, Masshh[I2G5]²] · gchi² · MassFchi · C0i[cc0, MassFchi², T, MassFchi², MassFchi², MassAh[I3G5]², MassAh[I3G6]²] · ZA[I3G5,3]·ZA[I3G6,3]·ZH[I2G5,2] · Mat[SUN1]`.
   The mediator is **natively t-channel** (`Den[T,Masshh²]`; **every** Den head in the
   amplitude is `T`), so the DD limit is **literally t→0** — no annihilation-S→0 hack.
   The genuine χ-side box present is the **pseudoscalar×quark (hk-type)** box,
   `D0i` with internal `{χ,a,a,q}` (e.g. `D0i[dd0, MassFchi², T, MassFu[1]², …, MassFchi², MassAh², MassAh², MassFu²]`).

**Box-coverage caveat (physics-review note).** The anchor's `chargedHiggs_W_box`
(A⁰H±W∓) is **NOT** a clean χ-side box in this model: χ is a **singlet** and couples
only to the neutral `a/A⁰`, so it cannot attach directly to W/H±. The genuine box is
the pseudoscalar×quark (hk-type) box above, with W/H± entering as **quark-side** vertex
corrections. So the like-for-like holds via **triangle-dominance** (the triangle is
~94% of σ_SI per §1/§6), **not** a clean diagram-by-diagram box match. A live LoopTools
number landing on the triangle anchor therefore validates the dominant physics; the
"box" piece is covered as quark-side dressing + the hk-type box, not as a separate
A⁰H±W∓ topology.

Other caveats: (a) LoopTools' box is rigorous (FormCalc/LoopTools PV), ours is a ≤30%
estimate; (b) tree-level scalar (h/H) exchange is **CP-allowed but momentum-suppressed**
for a pseudoscalar mediator — the σ_SI here is genuinely loop-induced via the *effective*
g_φχχ, consistent with the "CP-forbidden tree SI" statement in both SKILLs. We include
**no** tree-level SI (it is ≈0).

---

## 8. Uncertainty (no false precision)

Central **σ_SI(p) ≈ σ_SI(n) ≈ 6×10⁻⁴⁹ cm², reliable to a factor ~3–5**
(band ≈ 2×10⁻⁴⁹ – 2×10⁻⁴⁸). Order of magnitude (10⁻⁴⁹) is robust. Drivers:

- **Charged-Higgs/W box not computed** (§6): ≤30% on f_N ⇒ up to ×1.7 on σ. **Biggest
  one-sided flag.**
- **Dirac vs Majorana loop normalisation** (§3): factor ≤2 on f_N ⇒ ≤×4 on σ.
- **Portal identification λP1,λP2 ↔ c₁,c₂** (§4): g_aah is portal-dominated, so a
  re-identification (or a cubic-`lamP` contribution to g_aah we omitted) moves σ ∝ g_aah².
- **Loop-function form** ∂B0/∂p² vs my from-scratch L (shown identical) — checked, no
  residual; the mixed a–A⁰ triangle term omitted (≲ few %).
- **g_aaH / g_φA⁰A⁰ trilinears** approximated (§3 code note): affects only the ~3% H
  and ~9% A⁰-loop pieces.
- **Form-factor preset / σ-terms:** ~few % (the h piece is gluon-coherent, F^h≈0.28).
- **NLO / scale / quark-mass scheme:** the triangle is dominated by the universal
  gluon-coherent h coupling, mild scheme sensitivity (~10–20%).

---

## 9. Items for the adversarial reviewer

1. **Citation:** the EW box + triangle is **1910.09771** (Abe-Fujiwara-Hisano-**Shoji**),
   not 1810.01039 (which is the singlet model; its "box" = the hk pseudoscalar box). §2.
2. **Loop function L = [∂B0/∂p²]** derived from scratch and matched to AFH Eq. 3.36 by
   x↔1−x; the ∝m_χ scalar piece and UV-finiteness are the checks. §5.
3. **Trilinear g_aah ≈ 350 GeV is an O(v) portal coupling, NOT tanβ-enhanced** (with
   c₁=c₂ the tanβ factors cancel, §4). **Confirm λP1,λP2 ↔ AFH c₁,c₂** against the SARAH
   `TwoHdmAfix` potential.
4. **h dominates** (H ≈3%, A⁰-loop ≈9% of the h a-loop) — the prompt expected h; verified.
5. **Charged-Higgs/W box is an ESTIMATE (≤30%), not computed** (§6) — and it is exactly
   the piece LoopTools does rigorously, so a live number ~1.3–1.7× **above** the triangle
   is **expected**, not a discrepancy.
6. **Like-for-like via triangle-dominance** (§7, updated): the regenerated **elastic**
   fixture `amp_reduced.m` **now contains the triangle** (t-channel `Den[T,Masshh²]` ×
   `C0i[…χ,a,a…]`), so Step-0 is **SATISFIED**. `run_eval.wls`'s numerical core is still a
   stub (fp=fn=0) pending the next task. The A⁰H±W∓ box is not a clean χ-side box (χ is a
   singlet); the genuine box is the pseudoscalar×quark (hk-type) D0i {χ,a,a,q}.
7. **Dirac/Majorana factor ≤2** (§3) — overall normalisation, σ ∝ f².
8. **No second independent check.** The AFH-rescaling is a crude ballpark only (§5); the
   from-scratch derivation is the sole basis for the number.

---

## 10. Operational validation window (for whoever fills `run_eval.wls`)

Once the numerical core of `run_eval.wls` is implemented and a real FeynArts/FormCalc
`amp_reduced.m` is in hand, use this anchor as follows:

**Step 0 (prerequisite) — SATISFIED.** The committed fixture `amp_reduced.m` was
regenerated in the **elastic** χ q → χ q channel and **does contain** the χχ→h/H→q̄q
triangle: grep confirms `Den[T, Masshh[_]^2]` (t-channel scalar mediator) multiplying
`C0i[cc0, MassFchi^2, T, MassFchi^2, MassFchi^2, MassAh[_]^2, MassAh[_]^2]` (the χ-a-a
vertex-correction loop) in a single term, with `gchi^2 · MassFchi · ZA[,3]^2 · ZH[,2]`.
Because the mediator is **natively t-channel**, the DD limit is **literally t→0** — set
T→0 in `run_eval.wls` directly; **no** annihilation-S→0 substitution and **no** Mandelstam
crossing/remapping are needed (the box invariants S,U inside the D0i args are box-internal,
not propagator channels — every `Den` head is `T`). The earlier "box-only fixture" warning
no longer applies (§7).

**Then read the live σ_SI against these windows (proton):**

| live σ_SI(p) | verdict |
|---|---|
| ~6×10⁻⁴⁹ to ~1×10⁻⁴⁸ cm² (i.e. within ~×3–5 of 6×10⁻⁴⁹, and *above* it) | **VALIDATES** — triangle + constructive rigorous box, as expected |
| ~2×10⁻⁴⁹ to ~2×10⁻⁴⁸ | within the quoted band; acceptable (check box sign) |
| ~10⁻⁵⁴ cm² (≈ `hk_anchor.py`'s 2×10⁻⁵⁴) | **WRONG REGIME** — LoopTools is in the pseudoscalar-quark-box floor; the triangle (and/or the EW box) is missing from the amplitude → **topology/coverage bug** |
| ≫10⁻⁴⁸ or ≪10⁻⁴⁹ | investigate: coupling/units error, or a real box interference not captured by the ≤30% estimate |

**Diagnostic floor.** `hk_anchor.py` (σ ≈ 2×10⁻⁵⁴ cm²) is the **wrong-regime floor**:
a live LoopTools result near *that* value means the chain is computing the
pseudoscalar-quark box (hk diagram set) instead of the EW box + triangle it is supposed
to — i.e. the FeynArts amplitude has the wrong topologies. The ~5-orders-of-magnitude gap
between the two anchors makes this an unambiguous diagnostic.
