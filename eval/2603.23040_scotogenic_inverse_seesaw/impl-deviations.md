# Implementation Deviations — arXiv:2603.23040

**Purpose:** Required by plan §0.5.2. Documents deviations discovered during Phase-1
re-read that exceeded the plan's 1% escalation threshold. In Round-2 the plan-binding
values are restored; this file records what changed and why.

---

## DEV-1: NuFIT version (plan 5.2 → NuFIT 6.0 unilateral switch — REVERSED in R2)

**Detected in:** Phase-1 re-read  
**Status:** REVERSED in Round-2. NuFIT 5.2 is now the binding default per plan §0.5.2.

| Parameter | NuFIT 5.2 (plan binding) | NuFIT 6.0 (paper) | Deviation |
|---|---|---|---|
| θ₂₃ | 49.1° | 46.9° | −4.5% (> 1% threshold) |
| δ_CP | 197.0° | 217.8° | +10.6% (> 1% threshold) |

**Impact on observables:** BR(μ→eγ) changes by ~factor 2 between the two NuFIT versions
due to the different PMNS mixing structure entering the Casas-Ibarra Yukawa matrix.

**Plan §0.5.2 verdict:** These deviations exceed the 1% threshold. The plan mandated
a halt and ping before Step 15. The Round-1 unilateral switch to NuFIT 6.0 without
a halt was out of bounds. Round-2 reverts to NuFIT 5.2 as the binding default and
re-pins T5–T7 accordingly.

**NuFIT 5.2 re-pinned BR values:**
- T5 (BP1): BR = 3.482e-32 (was 1.020e-31 with NuFIT 6.0)
- T6 (BP2): BR = 2.094e-32 (was 6.186e-32 with NuFIT 6.0)
- T7 (BP3): BR = 1.993e-32 (was 5.892e-32 with NuFIT 6.0)

---

## DEV-2: Lightest neutrino mass (plan m₁ = 1e-3 eV → 0.01 eV unilateral — REVERSED in R2)

**Detected in:** Phase-1 re-read  
**Status:** REVERSED in Round-2. m₁ = 1e-3 eV is the binding default per plan Step 3.

The plan (Step 3) specifies `m1_eV = 1e-3 eV` as the default for `M_NU_DIAG_NO`.
Round-1 switched to m₁ = 0.01 eV (×10), citing the paper's choice. The plan's
escalation criterion (>1% on any NuFIT angle) already mandated a halt; a ×10 mass
change compounds this. Round-2 reverts to m₁ = 1e-3 eV.

---

## Note on plan placeholder BR = 4.8e-14

The plan's §2 table T5 shows a placeholder target of 4.8e-14. This is approximately
the MEG-II experimental limit, not a computed value from the model. The actual
Casas-Ibarra chain with m₁ = 1e-3 eV and Λ_r ~ 3×10⁻³ GeV² gives
y_φ ~ 10⁻⁵, leading to BR ~ 10⁻³² — many orders of magnitude below the
experimental limit. This is physically expected (the scotogenic loop coupling
is small when m_ν is small). The plan placeholder 4.8e-14 was a rough order-of-magnitude
stand-in; the correct plan-compliant value pinned in Round-2 is 3.5e-32 at BP1.

---

## B5 context note: c6/c9 correction magnitude in this model (Round-3)

The paper's Eq. 32 (full SD cross section including c6 and c9 corrections) vs Eq. 33
(leading c4-only approximation) asserts "<10% agreement" as a cross-check. The
Round-2 implementation computes c6 and c9 correctly; however, in the scotogenic
inverse-seesaw model the axial structure naturally produces
c6^N = c4^N * m_N^2 / m_chi^2, which at BP3 (m_chi ≈ 61 GeV, m_N ≈ 0.939 GeV)
gives a suppression of order (m_N/m_chi)^2 * (m_N/m_chi)^2 ≈ (0.939/61)^4 ≈ 5×10^{-8},
and the combined c6+c9 correction to the ratio sigma_full/sigma_simplified is
numerically ~3×10^{-11} of the leading term.

Consequence: T14's ratio pin of 1.000000000032 is correct, and the paper's "<10%"
claim is over-satisfied by approximately 9 orders of magnitude in this model. The
test still serves as an implementation sanity check — it verifies that c6 and c9
enter sigma_SD_full through the correct formula and do not accidentally dominate —
but it cannot verify the paper's literal Eq.32-vs-Eq.33 statement in a physically
meaningful way. A tighter pin (e.g., rel=1e-10) would catch any future refactor that
accidentally inflates the correction by 4+ orders of magnitude.
