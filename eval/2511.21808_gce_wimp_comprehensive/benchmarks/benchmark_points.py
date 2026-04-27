"""
Benchmark parameter points for arXiv:2511.21808 GCE WIMP study.

Tier-2 hand-picked BPs (T2.1 – T2.9):
  Selected by implementer at physically motivated parameter values.
  Expected values computed from hand-calculations; tolerances set conservatively.

Table-2 BPs (Tier-3 self-consistency only):
  From paper Table 2 best-fit values.
  m_Zp = 120.0 GeV (stated in paper body), g_chi = 1.0, Dirac DM.
  These are used ONLY for inversion round-trip tests (self-consistency).
  They do NOT externally validate our formula.

Test axial charges (T3.5, T3.6 -- non-trivial SD tests):
  Fabricated Charges objects with non-zero Q_A to test sigma_SD is non-trivial.
  The physical portals all have Q_A=0; these test the arithmetic path.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    M_MU, M_E, M_TAU,
    DELTA_U_P, DELTA_D_P, DELTA_S_P,
    M_P, GEV2_TO_CM2,
)
from models.charges import Charges, SM_FLAVORS, B_MINUS_L, LMU_MINUS_LE


# ===========================================================================
# Tier-2 hand-picked benchmark points (T2.1 – T2.9)
# ===========================================================================

TIER2_HANDPICKED_BPS = {
    # -----------------------------------------------------------------------
    # T2.1 — Γ(Z' → μ⁺μ⁻), Lμ-Le, m_Zp=200, g_Zp=0.01
    # Eq. 27 (plan v1) = closed-form partial width, massless limit
    # Γ = N_c Q_V[mu]^2 g_Zp^2 m_Zp / (12π) × (1 + 2m_μ²/m_Zp²) β_μ
    #   = (0.01)^2 × 200 / (12π) × (1 + 2×(0.1057)^2/200^2) × √(1 - 4×(0.1057)^2/200^2)
    #   ≈ 1e-4 × 200 / 37.699 × 1.0 × 1.0
    #   = 2e-2 / 37.699 = 5.305e-4 GeV
    # -----------------------------------------------------------------------
    "T2.1": {
        "description": "Gamma(Z'->mu+mu-) at Lmu-Le, m_Zp=200, g_Zp=0.01",
        "portal": "Lmu_Le",
        "m_Zp": 200.0, "g_Zp": 0.01, "g_chi": 0.1, "m_DM": 50.0,
        "dm_type": "Dirac",
        "flavor": "mu",
        "expected_gamma": 5.305e-4,  # GeV
        "tolerance": 0.01,           # 1%
        "source": "A (hand-calc)",
        "equation": "Eq. 27 (plan v1)",
    },
    # -----------------------------------------------------------------------
    # T2.2 — Γ(Z' → ν_μ ν̄_μ), Lμ-Le, same BP
    # Eq. 29 (plan v1): massless-ν limit
    # Γ = Q_nu_mu^2 g_Zp^2 m_Zp / (24π) = (0.01)^2 × 200 / (24π)
    #   = 2e-4 / (24 × 3.14159) = 2e-4 / 75.398 = 2.653e-6 GeV
    # Wait -- this is per active-ν, but nu_mu has Q=+1 in Lmu-Le:
    # Γ(Z'->nu_mu nu_bar_mu) = (0.01*1)^2 × 200 / (24π)
    #                        = 1e-4 × 200 / (24π) = 2e-2/75.398 = 2.653e-4 GeV
    # -----------------------------------------------------------------------
    "T2.2": {
        "description": "Gamma(Z'->nu_mu nu_bar_mu) at Lmu-Le, m_Zp=200, g_Zp=0.01",
        "portal": "Lmu_Le",
        "m_Zp": 200.0, "g_Zp": 0.01, "g_chi": 0.1, "m_DM": 50.0,
        "dm_type": "Dirac",
        "nu_flavor": "nu_mu",
        "expected_gamma_nu_mu": 2.653e-4,  # GeV (one active ν species)
        "tolerance": 0.01,
        "source": "A (hand-calc)",
        "equation": "Eq. 29 (plan v1)",
    },
    # -----------------------------------------------------------------------
    # T2.3 — Γ(Z' → χ χ̄), B-L, m_Zp=200, m_DM=50, g_chi=0.1, Dirac
    # Eq. 28 (plan v1):
    # Γ = g_chi^2 m_Zp / (12π) × (1 + 2m_DM^2/m_Zp^2) × β_DM
    # β_DM = sqrt(1 - 4×50²/200²) = sqrt(1 - 0.25) = sqrt(0.75) = 0.86603
    # Γ = (0.1)^2 × 200 / (12π) × (1 + 2×50²/200²) × 0.86603
    #   = 0.01 × 200 / 37.699 × (1 + 0.125) × 0.86603
    #   = 2 / 37.699 × 1.125 × 0.86603
    #   = 0.053050 × 1.125 × 0.86603
    #   = 0.05175 GeV
    # -----------------------------------------------------------------------
    "T2.3": {
        "description": "Gamma(Z'->chi chi_bar) at B-L, m_Zp=200, m_DM=50, g_chi=0.1, Dirac",
        "portal": "BminusL",
        "m_Zp": 200.0, "g_Zp": 0.01, "g_chi": 0.1, "m_DM": 50.0,
        "dm_type": "Dirac",
        # β_DM = sqrt(1 - 4*50^2/200^2) = sqrt(0.75) = 0.866025
        # Γ = (0.1)^2 × 200/(12π) × (1+2×(50/200)^2) × 0.866025
        #   = 0.01 × 200/(12π) × 1.125 × 0.866025
        #   = 0.01 × 5.3052 × 1.125 × 0.866025 = 0.05174 GeV
        "expected_gamma_DM": 5.169e-2,  # GeV (numerical: 5.168708e-02)
        "tolerance": 0.01,
        "source": "A (hand-calc)",
        "equation": "Eq. 28 (plan v1)",
    },
    # -----------------------------------------------------------------------
    # T2.4 — Γ_total identity: sum of partials == gamma_zprime_total
    # Tested at 3 random points × 4 portals in test code.
    # (No single expected value; abs diff < 1e-10.)
    # -----------------------------------------------------------------------
    "T2.4": {
        "description": "Gamma_total = sum of partials (identity)",
        "tolerance_abs": 1e-10,
        "source": "C (algebraic identity)",
        "equation": "identity",
    },
    # -----------------------------------------------------------------------
    # T2.5 — σ_SI B-L at (m_DM=50, m_Zp=200, g_chi=0.1, g_Zp=0.01, Dirac)
    # Eq. 39 (plan v1) / Eq. 15 (paper v2); Case A valence quark counting.
    # See paper-extracted.md for full arithmetic.
    # Expected: 6.571e-44 cm² (calculated above)
    # -----------------------------------------------------------------------
    "T2.5": {
        "description": "sigma_SI(B-L proton) at m_DM=50, m_Zp=200, g_chi=0.1, g_Zp=0.01",
        "portal": "BminusL",
        "m_DM": 50.0, "m_Zp": 200.0, "g_chi": 0.1, "g_Zp": 0.01,
        "dm_type": "Dirac",
        "target": "proton",
        # Hand-calc (Case A, valence quark counting):
        # μ = 50×0.93827/(50+0.93827) = 0.92099 GeV; μ²/π = 0.26999 GeV²
        # f_p = g_Zp × (2×Q_V[u] + Q_V[d]) = 0.01 × (2×1/3 + 1/3) = 0.01 × 1 = 0.01
        # σ = 0.26999 × (0.1×0.01)² / (200⁴) × 0.3894e-27
        #   = 0.26999 × 1e-6 × 6.25e-10 × 0.3894e-27
        #   = 0.26999 × 6.25e-16 × 0.3894e-27 = 6.572e-44 cm²
        "expected_sigma_SI": 6.571e-44,  # cm² (from numerical verification)
        "tolerance": 0.05,   # 5% (Case A)
        "source": "A (hand-calc, Case A valence quark counting)",
        "equation": "Eq. 39 (plan v1) / Eq. 15 (paper v2)",
    },
    # -----------------------------------------------------------------------
    # T2.6 — σ_SI Lμ-Le = 0 (exact by arithmetic; Q_V[q]=0 for quarks)
    # -----------------------------------------------------------------------
    "T2.6": {
        "description": "sigma_SI(Lmu-Le) = 0 exactly (no quark coupling)",
        "portal": "Lmu_Le",
        "m_DM": 50.0, "m_Zp": 200.0, "g_chi": 0.1, "g_Zp": 0.01,
        "dm_type": "Dirac",
        "target": "proton",
        "tolerance_abs": 1e-60,
        "source": "C (algebraic identity)",
        "equation": "Eq. 26 (plan v1)",
    },
    # -----------------------------------------------------------------------
    # T2.7 — σ_SD Lμ-Le = 0 (exact by arithmetic; Q_A=0 for all flavors)
    # -----------------------------------------------------------------------
    "T2.7": {
        "description": "sigma_SD(Lmu-Le) = 0 exactly (no axial coupling)",
        "portal": "Lmu_Le",
        "m_DM": 50.0, "m_Zp": 200.0, "g_chi": 0.1, "g_Zp": 0.01,
        "dm_type": "Dirac",
        "target": "proton",
        "tolerance_abs": 1e-60,
        "source": "C (algebraic identity)",
        "equation": "Eq. 44 (plan v1) / Eq. 17 (paper v2)",
    },
    # -----------------------------------------------------------------------
    # T2.8 — Higgs-portal σv off-funnel at (m_DM=100, λ=0.1, channel="b")
    # Eq. 6-8 (plan v1)
    # Off-funnel (m_DM >> m_h/2 = 62.6): BW correction ≈ 1 at denominator
    # Formula: <σv> = λ² N_c m_b² β_b^3 / (8π V_H² |D_BW|²) × GEV2_TO_CM2
    # m_DM=100, m_h=125.25, m_b=4.18 (pole mass):
    # s0 = 4×100² = 40000 GeV²
    # D_BW² = (40000 - 125.25²)² + (125.25 × 4.07e-3)² ≈ (40000 - 15688)² + tiny²
    #       = (24312)² ≈ 5.910e8 (Γ_h contribution negligible)
    # β_b = sqrt(1 - 4.18²/100²) = sqrt(1 - 0.001745) ≈ 0.99913
    # <σv> = (0.1)² × 3 × (4.18)² × (0.99913)^3 / (8π × (246.22)² × 5.910e8) × 0.3894e-27
    # Numerator: 0.01 × 3 × 17.47 × 0.9974 = 0.01 × 3 × 17.43 = 0.5228
    # Denominator: 8π × 60604 × 5.910e8 = 25.133 × 60604 × 5.910e8
    #            = 25.133 × 3.582e13 = 9.004e14
    # <σv>_gev2 = 0.5228 / 9.004e14 = 5.806e-16 GeV^-2
    # <σv>_cm3s = 5.806e-16 × 3.894e-28 = 2.261e-43 cm³/s ... let me verify numerically
    # -----------------------------------------------------------------------
    "T2.8": {
        "description": "sigma_v Higgs portal off-funnel at m_DM=100, lam=0.1, channel=b",
        "m_DM": 100.0, "lam": 0.1,
        "dm_type": "scalar",
        "channel": "b",
        # Hand-calc: y_hchi = lam*V_H = 24.622; D_BW^2 = (4*100^2 - 125.25^2)^2 = 5.911e8
        # sigma_v = 3*(24.622)^2*(4.18)^2*(0.999)^3 / (8pi*(246.22)^2*5.911e8) * GEV2_TO_CM2
        # = 3*606.2*17.47*0.997 / (25.133*60624*5.911e8) * 0.3894e-27
        # = 31689 / 9.009e14 * 0.3894e-27 = 3.517e-11 * 0.3894e-27 = 1.370e-38 cm^3/s
        "expected_sigma_v": 1.370e-38,  # cm^3/s
        "tolerance": 0.05,
        "source": "A (hand-calc)",
        "equation": "Eq. 6-8 (plan v1)",
    },
    # -----------------------------------------------------------------------
    # T2.9 — Higgs-portal σ_SI at funnel: m_DM=62.60, λ=2e-4
    # Eq. 9 (plan v1); complete arithmetic in constants.py docstring.
    # Expected: 2.012e-50 cm²
    # -----------------------------------------------------------------------
    "T2.9": {
        "description": "sigma_SI Higgs portal at funnel m_DM=62.60, lam=2e-4",
        "m_DM": 62.60, "lam": 2e-4,
        "dm_type": "scalar",
        "target": "proton",
        "expected_sigma_SI": 2.012e-50,  # cm²
        "tolerance": 0.05,
        "source": "A (hand-calc)",
        "equation": "Eq. 9 (plan v1)",
    },
}

# ===========================================================================
# Table-2 BPs (Tier-3 self-consistency only)
# ===========================================================================

TABLE_2_BPS = {
    # m_Zp = 120 GeV (paper body text), g_chi = 1.0, Dirac
    "Lmu_Le": {
        "m_DM": 44.1, "m_Zp": 120.0, "g_chi": 1.0, "dm_type": "Dirac",
        "sigma_v_target": 7.58e-26,  # cm³/s
        "note": "Table 2, Lmu-Le portal best fit",
    },
    "Le_Ltau": {
        "m_DM": 19.2, "m_Zp": 120.0, "g_chi": 1.0, "dm_type": "Dirac",
        "sigma_v_target": 3.03e-26,
        "note": "Table 2, Le-Ltau portal best fit",
    },
    "Lmu_Ltau": {
        "m_DM": 20.5, "m_Zp": 120.0, "g_chi": 1.0, "dm_type": "Dirac",
        "sigma_v_target": 3.76e-26,
        "note": "Table 2, Lmu-Ltau portal best fit",
    },
    "BminusL": {
        "m_DM": 37.5, "m_Zp": 120.0, "g_chi": 1.0, "dm_type": "Dirac",
        "sigma_v_target": 4.67e-26,
        "note": "Table 2, B-L portal best fit",
    },
}

# ===========================================================================
# Non-trivial axial charge assignments (B4 fix: SD tests)
# ===========================================================================

# TEST_AXIAL_CHARGES_A: isovector axial assignment
# Q_A[u]=+1, Q_A[d]=-1, all others 0
TEST_AXIAL_CHARGES_A = Charges(
    name="test_axial_isovector",
    Q_V={f: 0.0 for f in SM_FLAVORS},
    Q_A={
        "u": +1.0, "d": -1.0, "c": 0.0, "s": 0.0, "t": 0.0, "b": 0.0,
        "e": 0.0, "mu": 0.0, "tau": 0.0,
        "nu_e": 0.0, "nu_mu": 0.0, "nu_tau": 0.0,
    },
    N_nu_active=0,
    N_nu_sterile=0,
)

# Hand-calc for σ_SD(proton) with TEST_AXIAL_CHARGES_A at (m_DM=50, m_Zp=200, g_chi=0.1, g_Zp=0.01):
# C_A^p = Δu^p × Q_A[u] + Δd^p × Q_A[d] + Δs^p × Q_A[s]
#       = 0.842 × (+1) + (-0.427) × (-1) + (-0.085) × 0
#       = 0.842 + 0.427 = 1.269
# σ_SD = (4 μ²/π) × (g_chi g_Zp / m_Zp²)² × (C_A^p)²
# μ = 50×0.93827/(50+0.93827) = 0.92099 GeV
# σ_SD_gev2 = (4×0.92099²/π) × (0.1×0.01/200²)² × 1.269²
#           = (4×0.84822/π) × (1e-3/40000)² × 1.610
#           = (3.39287/π) × (2.5e-8)² × 1.610
#           = 1.07990 × 6.25e-16 × 1.610
#           = 1.07990 × 1.006e-15 = 1.086e-15 GeV^-2
# σ_SD_cm2 = 1.086e-15 × 3.894e-28 = 4.228e-43 cm²
TEST_AXIAL_A_EXPECTED_SIGMA_SD = 4.233e-43  # cm² (T3.5 pin; numerical: 4.232691e-43)
TEST_AXIAL_A_TOLERANCE = 0.05

# TEST_AXIAL_CHARGES_B: isoscalar axial assignment
# Q_A[u]=+1/2, Q_A[d]=+1/2, all others 0
TEST_AXIAL_CHARGES_B = Charges(
    name="test_axial_isoscalar",
    Q_V={f: 0.0 for f in SM_FLAVORS},
    Q_A={
        "u": +0.5, "d": +0.5, "c": 0.0, "s": 0.0, "t": 0.0, "b": 0.0,
        "e": 0.0, "mu": 0.0, "tau": 0.0,
        "nu_e": 0.0, "nu_mu": 0.0, "nu_tau": 0.0,
    },
    N_nu_active=0,
    N_nu_sterile=0,
)

# Hand-calc for σ_SD(proton) with TEST_AXIAL_CHARGES_B at same BP:
# C_A^p = 0.842×0.5 + (-0.427)×0.5 + 0 = 0.421 - 0.2135 = 0.2075
# σ_SD_gev2 = 1.07990 × (0.1×0.01/200²)² × 0.2075²
#           = 1.07990 × 6.25e-16 × 0.04306
#           = 1.07990 × 2.691e-17 = 2.906e-17 GeV^-2
# σ_SD_cm2 = 2.906e-17 × 3.894e-28 = 1.131e-44 cm²
TEST_AXIAL_B_EXPECTED_SIGMA_SD = 1.132e-44  # cm² (T3.6 pin; numerical: 1.131695e-44)
TEST_AXIAL_B_TOLERANCE = 0.05

# MG5 benchmark point (for future use when UFO is vendored)
MG5_BP = {
    "portal": "BminusL",
    "m_DM": 50.0, "m_Zp": 200.0, "g_chi": 0.1, "g_Zp": 0.01,
    "dm_type": "Dirac",
    "note": "Plan C: MG tasks not present in v1 (no UFO vendored)",
}
