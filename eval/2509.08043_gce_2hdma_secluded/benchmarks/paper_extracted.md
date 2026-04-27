# Paper S0 Extraction — arXiv:2509.08043

**Paper:** "Testing Viability of Benchmark Dark Matter Models for the Galactic Center Excess"
**Authors:** Yongao Hu, Cari Cesarotti, Tracy R. Slatyer
**Submitted:** September 9, 2025
**URL:** https://arxiv.org/abs/2509.08043

---

## E1 — Secluded-Hypercharge Benchmark Point (m_χ, m_Z', g_χ)

**Status: NOT_FOUND**

The paper does not explicitly state a single (m_χ, m_Z', g_χ) triplet that reproduces the
thermal anchor ⟨σv⟩ = 4.4×10⁻²⁶ cm³/s. Instead, Section 2.3.1 states that g_D is
*determined dynamically* by requiring the annihilation produces the correct DM thermal relic
density from Eq. 24. The parameter space scan ranges are:
- m_χ ∈ [10, 100] GeV
- m_Z' < m_χ (secluded regime)
- ε ∈ [10⁻⁹, 10⁻⁴] (kinetic mixing)

Results are presented as exclusion plots (Section 4), not explicit triplets in the text.

**Fallback decision:** Drop `derive_thermal_anchor_sigma_v`, `t1_sechyp_param_card_anchor`,
and `t2_sechyp_thermal_anchor` from the harness. Keep `sigma_v_secluded` as an unpinned
function. Document in README that sechyp tasks are deferred pending explicit BP extraction
from result figures.

---

## E2 — Eq. 44 Full Expression (σ_SI prefactor)

**Status: FOUND (partial — labeled Eq. 44 is the box diagram, Eq. 50 is full σ_SI)**

The paper uses two diagrams for σ_SI in the 2HDM+a model:

**Eq. 44 (box diagram):**
```
ℒ_(a) = Σ_q [ m_q² g_χ² tan²β sin²(2θ) / (128π² m_a²(m_χ²−m_q²)) ]
          × [F(m_χ²/m_a²) − F(m_q²/m_a²)] × (m_χ m_q / v²) χχ̄qq̄
```
Uses loop function F (not G). This is the box contribution.

**Eq. 47 (triangle diagram effective Lagrangian — the PRIMARY term for σ_SI):**
```
ℒ_(b) = (m_A² − m_a²) sin²(2θ) g_χ² / (64π² m_h² m_a²) × G(m_χ²/m_a², 0) × (m_χ m_q / v²) χχ̄qq̄
```
Uses G function. This is the triangle contribution.

**Eq. 50 (full σ_SI combining all contributions, with scaling formula):**
```
σ_SI = (μ²_χN/π) × [(m_A² − m_a²) sin²(2θ) g_χ² / (64π² m_h² m_a²) × G(m_χ²/m_a², 0) × sigma_mq / v²]²

σ_SI ≈ 2.2×10⁻⁴⁹ cm² × (m_A/800)⁴ × (m_a/50)⁻⁴ × (m_χ/30)² × (θ/0.1)⁴ × (g_χ/0.5)⁴
```
(Second line is Taylor/scaling approximation for small x = m_χ²/m_a².)

**Implementation note:** The plan's "Eq. 44" corresponds to the paper's Eq. 50 (the full σ_SI).
The prefactor structure is: σ_SI = (μ²/π) × f_N² where f_N = A_loop × G × m_χ/v² × σ_mq,
and A_loop = (m_A²−m_a²) × sin²(2θ) × g_χ² / (64π² × m_h² × m_a²).

---

## E3 — G(x, y) Definition and Branch Choice

**Status: NOT_FOUND (paper gives integral form, not closed Spence form)**

The paper defines G(x,y) via Eqs. 48-49:
```
G(x,y) = -4i ∫₀¹ dz z/ℱ^(1/2)(x,y,z) × ln[(ℱ^(1/2) + iy(1-z)) / (ℱ^(1/2) - iy(1-z))]
ℱ(x,y,z) = y[4(1-z) + 4xz² − y(1-z)²]
```
The paper states: "Note that G(0,0) = 1."

At y→0 (the limit needed for σ_SI via Eq. 50 / 47), the integral yields:
```
G(x, 0) = 2 ∫₀¹ dz z(1-z) / [(1-z) + xz²]
```
This is computed via mpmath.quad (NOT scipy.special.spence).
Verified: G(0, 0) = 1 analytically (since ∫₀¹ z dz = 1/2, the factor of 2 gives 1). ✓

**DEVIATION from plan:** The plan's 5 literal G values (0.590150, 1.0, 0.606706, 0.2125, 0.0433605)
assumed G(1,0) = 1. The paper's formula gives G(1,0) = 0.41840 (NOT 1). The plan's values are
from a Bauer-2017 formula that could not be independently verified. Per E3 NOT_FOUND fallback
rule: use the paper's integral formula (y→0 limit) with G(0,0) = 1 as the threshold identity.

**Updated 5 G literals (from paper formula, computed via mpmath):**
| x | G(x, 0) | Notes |
|---|---|---|
| 0.5 | **0.527887** | computed via integral |
| 1.0 | **0.418399** | computed via integral |
| 2.0 | **0.316090** | computed via integral |
| 10.0 | **0.138373** | computed via integral |
| 100.0 | **0.030144** | computed via integral |
| 0.0 | **1.000000** | analytic: G(0,0)=1 identity |

**Threshold identity:** G(0, 0) = 1 (not G(1,0)=1 as in plan).
Tests T1-T5 updated to use these literals.

---

## E4 — Fig. 12 γ-ray Line Numeric Anchor

**Status: NOT_FOUND**

The paper's Section 4 results show Fig. 12 (γ-ray line constraints) graphically, but no
numeric value for ⟨σv⟩_γγ at the 2HDM+a anchor BP is stated in the text. The comparison uses
the Foster et al. (2023) analysis without quoting a specific cross-section threshold.

**Fallback decision:** Drop `t3_thdma_gamma_line_anchor` from YAML. Module `gamma_line.py`
ships as a stub for completeness but has no grader pin. Documented in README.

---

## E5 — Bauer UFO Version Statement

**Status: NOT_FOUND**

Section 3.2.6 states: "using the 2HDM Universal FeynRules Output (UFO) from Ref. [Bauer:2017ota]"
No SHA, FeynRules version tag, or specific identifier is given.

**Fallback decision:** Proceed with vendored stub using LHC DM WG 2HDM+a parameter names
(BL7 route 2). `PINNED_SHA` = SHA-256 of committed stub `parameters.py`. Documented in
`madgraph/README.md`.
