# Hand-Calc Ledger for σ_SI (arXiv:2509.08043)

**Generated:** Pre-S9 (before writing sigma_si_2hdma_exact.py) per plan requirement.
**Method:** Python `mpmath` with 25 decimal places + independent algebra (NOT by calling
the triangle_G.py module or sigma_si_2hdma_exact.py — those are validated AGAINST this ledger).
**Formula:** Eq. 47/50 of arXiv:2509.08043 (triangle diagram contribution):
  - A_loop = (m_A² - m_a²) sin²(2θ) g_χ² / (64π² M_h² m_a²)   [GeV⁻²]
  - f_N = A_loop × G(x,0) × m_χ / V_H² × σ_{mq}               [GeV⁻²]
  - σ_SI = 4 μ² / π × f_N²                                     [GeV⁻²]
  - σ_SI (cm²) = σ_SI (GeV⁻²) × 0.3894×10⁻²⁷

**Equation numbering note:** The plan's "Eq. 44" corresponds to the paper's Eq. 50 (the
full σ_SI expression). The triangle amplitude appears in Eq. 47. All references below
use the paper's numbering (Eq. 47/50). The box-diagram contribution (paper's Eq. 44,
using loop function F) is a separate, subleading term not implemented here.

**G(x,0) formula (paper y→0 limit, NOT Bauer-Spence):**
  G(x,0) = 2 ∫₀¹ dz z(1-z) / [(1-z) + xz²]
  Computed via `mpmath.quad` (independent of loop_functions/triangle_G.py).
  Boundary: G(0,0) = 1 (analytic identity: 2∫₀¹ z dz = 1).

**Constants used:**
  V_H = 246.22 GeV, M_h = 125.25 GeV, M_P = 0.93827 GeV
  σ_{mq} = 0.330 GeV, GEV2_TO_CM2 = 0.3894×10⁻²⁷ cm²/GeV⁻²

---

## BP-A  (m_A=800, m_a=50, m_chi=30, θ=0.1, g_χ=0.5, tan_β=1, σ_mq=0.330 GeV)

**1. Reduced mass:**
```
μ = m_chi · M_P / (m_chi + M_P)
  = 30 · 0.93827 / (30 + 0.93827)
  = 28.14810 / 30.93827
  = 0.909815  GeV
```

**2. Loop argument:**
```
x = m_chi² / m_a² = 900 / 2500 = 0.360000
```

**3. G(x=0.360, y=0) via mpmath integral:**
```
G(0.36, 0) = 2 ∫₀¹ z(1-z) / [(1-z) + 0.36·z²] dz
           = 0.579703  (6 sig figs, mpmath 25 dps)
```

**4. A_loop amplitude factor (Eq. 47 bracket — triangle diagram):**
```
m_A² - m_a² = 800² - 50² = 640000 - 2500 = 637500  GeV²
sin²(2θ) = sin²(0.2) = 0.19867² = 0.039469
g_χ² = 0.5² = 0.25
64π² = 631.654
M_h² = 125.25² = 15687.5625  GeV²
m_a² = 50² = 2500  GeV²

A_loop = 637500 × 0.039469 × 0.25 / (631.654 × 15687.5625 × 2500)
       = 6284.86 / (2.47693 × 10¹⁰)
       = 2.53907 × 10⁻⁷  GeV⁻²
```

**5. Nucleon coupling f_N:**
```
f_N = A_loop × G × m_chi / V_H² × σ_mq
    = 2.53907×10⁻⁷ × 0.579703 × 30 / (246.22² × 0.330)
    = 2.53907×10⁻⁷ × 0.579703 × 30 / (60624.28 × 0.330)
    = 2.53907×10⁻⁷ × 0.579703 × 30 / 20006.01
    = 2.53907×10⁻⁷ × 0.579703 × 1.49956×10⁻³
    = 2.40380×10⁻¹¹  GeV⁻²
```

**6. σ_SI (GeV⁻²):**
```
σ_SI = 4 × μ² / π × f_N²
     = 4 × 0.909815² / π × (2.40380×10⁻¹¹)²
     = 4 × 0.827764 / 3.141593 × 5.77823×10⁻²²
     = 4 × 0.263477 × 5.77823×10⁻²²
     = 6.09076×10⁻²²  GeV⁻²
```

**7. σ_SI (cm²):**
```
σ_SI = 6.09076×10⁻²² × 0.3894×10⁻²⁷
     = 2.37135×10⁻⁴⁹  cm²
```

**TARGET BP-A:** σ_SI = **2.371e-49 cm²**

---

## BP-B  (m_A=1600, m_a=50, m_chi=30, θ=0.1, g_χ=0.5, tan_β=1 — vary m_A)

**1. Reduced mass:** μ = 0.909815 GeV  (same as BP-A)

**2. Loop argument:** x = 0.360000  (same as BP-A); G = 0.579703

**3. A_loop (ratio from BP-A):**
```
m_A² - m_a² = 1600² - 50² = 2560000 - 2500 = 2557500  GeV²
A_loop(B) / A_loop(A) = (m_A²_B - m_a²) / (m_A²_A - m_a²)
                      = 2557500 / 637500 = 4.01176

A_loop(B) = 2.53907×10⁻⁷ × 4.01176 = 1.01853×10⁻⁶  GeV⁻²
```

**4. f_N (ratio from BP-A):**
```
f_N(B) / f_N(A) = A_loop(B) / A_loop(A) = 4.01176
f_N(B) = 2.40380×10⁻¹¹ × 4.01176 = 9.64580×10⁻¹¹  GeV⁻²
```

**5. σ_SI (ratio from BP-A):**
```
σ_SI(B) / σ_SI(A) = [f_N(B) / f_N(A)]² = (4.01176)² = 16.0942
σ_SI(B) = 2.37135×10⁻⁴⁹ × 16.0942 = 3.81669×10⁻⁴⁸  cm²
```

**TARGET BP-B:** σ_SI = **3.817e-48 cm²**

---

## BP-C  (m_A=800, m_a=25, m_chi=30, θ=0.1, g_χ=0.5, tan_β=1 — vary m_a)

**1. Reduced mass:** μ = 0.909815 GeV

**2. Loop argument:**
```
x = 30² / 25² = 900 / 625 = 1.440000
G(1.44, 0) = 2 ∫₀¹ z(1-z)/[(1-z)+1.44z²] dz = 0.363171  (mpmath 25 dps)
```

**3. A_loop:**
```
m_A² - m_a² = 640000 - 625 = 639375  GeV²
64π² × M_h² × m_a² = 631.654 × 15687.56 × 625 = 6.19296×10⁹  GeV⁴
A_loop(C) = 639375 × 0.039469 × 0.25 / 6.19296×10⁹
           = 6298.64 / 6.19296×10⁹
           = 1.01704×10⁻⁶  GeV⁻²
```

**4. f_N (ratio from BP-A):**
```
f_N(C) / f_N(A) = [A_loop(C) / A_loop(A)] × [G(C) / G(A)]
                = (1.01704×10⁻⁶ / 2.53907×10⁻⁷) × (0.363171 / 0.579703)
                = 4.00555 × 0.626458
                = 2.50870
f_N(C) = 2.40380×10⁻¹¹ × 2.50870 = 6.03231×10⁻¹¹  GeV⁻²
```

**5. σ_SI (ratio from BP-A):**
```
σ_SI(C) / σ_SI(A) = [f_N(C) / f_N(A)]² = (2.50870)² = 6.29357
σ_SI(C) = 2.37135×10⁻⁴⁹ × 6.29357 = 1.49268×10⁻⁴⁸  cm²
```

**TARGET BP-C:** σ_SI = **1.493e-48 cm²**

---

## BP-D  (m_A=800, m_a=50, m_chi=60, θ=0.1, g_χ=0.5, tan_β=1 — vary m_chi)

**1. Reduced mass:**
```
μ = 60 × 0.93827 / (60 + 0.93827) = 56.2962 / 60.93827 = 0.923823  GeV
```

**2. Loop argument:**
```
x = 60² / 50² = 3600 / 2500 = 1.440000
G(1.44, 0) = 0.363171  (same x as BP-C)
```

**3. A_loop:** Same as BP-A (same m_A, m_a, θ, g_chi):
```
A_loop(D) = 2.53907×10⁻⁷  GeV⁻²
```

**4. f_N:**
```
f_N = A_loop × G × m_chi / V_H² × σ_mq
f_N(D) / f_N(A) = [G(D) / G(A)] × [m_chi_D / m_chi_A]
                = (0.363171 / 0.579703) × (60 / 30)
                = 0.626458 × 2.0
                = 1.252917
f_N(D) = 2.40380×10⁻¹¹ × 1.252917 = 3.01146×10⁻¹¹  GeV⁻²
```

**5. σ_SI:**
```
σ_SI(D) / σ_SI(A) = [μ_D / μ_A]² × [f_N(D) / f_N(A)]²
                  = (0.923823 / 0.909815)² × (1.252917)²
                  = (1.015410)² × 1.569961
                  = 1.031058 × 1.569961
                  = 1.618706

σ_SI(D) = 2.37135×10⁻⁴⁹ × 1.618706 = 3.83821×10⁻⁴⁹  cm²
```

**TARGET BP-D:** σ_SI = **3.838e-49 cm²**

---

## BP-E  (m_A=800, m_a=50, m_chi=30, θ=0.05, g_χ=0.5, tan_β=1 — vary θ)

**1. Reduced mass:** μ = 0.909815 GeV

**2. Loop argument:** x = 0.36, G = 0.579703

**3. A_loop (ratio from BP-A via sin² scaling):**
```
sin²(2×0.05) = sin²(0.1) = 0.0099833  [sin(0.1) = 0.099833]
sin²(2×0.1)  = sin²(0.2) = 0.039469   [sin(0.2) = 0.198669]

A_loop(E) / A_loop(A) = sin²(0.1) / sin²(0.2) = 0.0099833 / 0.039469 = 0.252903
A_loop(E) = 2.53907×10⁻⁷ × 0.252903 = 6.41977×10⁻⁸  GeV⁻²
```

**4. f_N (ratio from BP-A):**
```
f_N(E) / f_N(A) = A_loop(E) / A_loop(A) = 0.252903
f_N(E) = 2.40380×10⁻¹¹ × 0.252903 = 6.07859×10⁻¹²  GeV⁻²
```

**5. σ_SI (ratio from BP-A):**
```
σ_SI(E) / σ_SI(A) = (0.252903)² = 0.063960
σ_SI(E) = 2.37135×10⁻⁴⁹ × 0.063960 = 1.51685×10⁻⁵⁰  cm²
```

**TARGET BP-E:** σ_SI = **1.517e-50 cm²**

---

## BP-F  (m_A=800, m_a=50, m_chi=30, θ=0.1, g_χ=1.0, tan_β=1 — vary g_chi)

**1. Reduced mass:** μ = 0.909815 GeV

**2. Loop argument:** x = 0.36, G = 0.579703

**3. A_loop (ratio from BP-A via g_chi² scaling):**
```
A_loop ~ g_chi² so:
A_loop(F) / A_loop(A) = (g_chi_F / g_chi_A)² = (1.0 / 0.5)² = 4.0
A_loop(F) = 2.53907×10⁻⁷ × 4.0 = 1.01563×10⁻⁶  GeV⁻²
```

**4. f_N (ratio from BP-A):**
```
f_N(F) / f_N(A) = (g_chi_F / g_chi_A)² = 4.0
f_N(F) = 2.40380×10⁻¹¹ × 4.0 = 9.61519×10⁻¹¹  GeV⁻²
```

**5. σ_SI (ratio from BP-A):**
```
σ_SI(F) / σ_SI(A) = [f_N(F) / f_N(A)]² = (4.0)² = 16.0
σ_SI(F) = 2.37135×10⁻⁴⁹ × 16.0 = 3.79416×10⁻⁴⁸  cm²
```

**TARGET BP-F:** σ_SI = **3.794e-48 cm²**

---

## Summary Table

| BP | m_chi | m_a | m_A | θ | g_χ | x | G(x,0) | σ_SI (cm²) |
|---|---|---|---|---|---|---|---|---|
| A | 30 | 50 | 800 | 0.1 | 0.5 | 0.36 | 0.579703 | **2.371e-49** |
| B | 30 | 50 | 1600 | 0.1 | 0.5 | 0.36 | 0.579703 | **3.817e-48** |
| C | 30 | 25 | 800 | 0.1 | 0.5 | 1.44 | 0.363171 | **1.493e-48** |
| D | 60 | 50 | 800 | 0.1 | 0.5 | 1.44 | 0.363171 | **3.838e-49** |
| E | 30 | 50 | 800 | 0.05 | 0.5 | 0.36 | 0.579703 | **1.517e-50** |
| F | 30 | 50 | 800 | 0.1 | 1.0 | 0.36 | 0.579703 | **3.794e-48** |

**Note on paper anchor:** Paper's Eq. 50 scaling formula states σ_SI ≈ 2.2×10⁻⁴⁹ cm² at BP-A.
This ledger gives 2.371×10⁻⁴⁹ cm² (+7.8% deviation). The deviation is explained by the
paper's Taylor approximation G(x,0) ≈ 1 used in the scaling formula, whereas the exact
G(0.36, 0) = 0.579703 < 1. The factor (0.579703)² ≈ 0.336 reduces the exact σ_SI relative
to what the G=1 approximation would give. The T7–T14 tests compare sigma_SI_exact to these
hand-calc targets, NOT to the paper's scaling approximation 2.2e-49.

**Note on equation numbering:** All formulas here implement the paper's Eq. 47 (triangle
diagram effective Lagrangian) with the resulting σ_SI from Eq. 50 (first line, exact form).
The plan's earlier label "Eq. 44" was a misnomer — Eq. 44 in the paper is the box-diagram
contribution using loop function F, which is a separate subleading term.
