"""
Spin-dependent DM-nucleon cross section via Z' exchange.
arXiv:2511.21808, Eq. 44 (plan v1 numbering); actual paper Eq. 17.

Formula (Eq. 17 of paper, plan's "Eq. 44"):
  σ_SD = (4 μ²/π) × (g_χ g_Zp / m_Zp²)² × [C_A^N]²

where C_A^N is the nucleon axial charge:
  C_A^p = Δu^p Q_A[u] + Δd^p Q_A[d] + Δs^p Q_A[s]
  C_A^n = Δu^n Q_A[u] + Δd^n Q_A[d] + Δs^n Q_A[s]

and Δq^N are the nucleon spin fractions (axial form factors).

NOTE: The paper's Eq. 17 has a v² factor (p-wave suppression), making
σ_SD velocity-suppressed at low v. In the non-relativistic limit,
σ_SD(v→0) = 0 for p-wave. However, for the benchmark function here we
compute the v-independent prefactor (the coefficient of v²), which
gives σ_SD at finite v. The test T2.7 checks σ_SD=0 for purely vector
portals (Q_A=0 for Lᵢ-Lⱼ) which is exact regardless of p-wave suppression.

All portal charges in this paper have Q_A = 0 (pure vector coupling).
σ_SD therefore evaluates to exactly 0.0 by arithmetic for all physical portals.

The two TEST_AXIAL_CHARGES_A/B in test_benchmarks.py fabricate non-zero
axial charges to verify the arithmetic path is correct.

Identity: Q_A=0 → C_A^N=0 → σ_SD=0 falls out by arithmetic.
No special-case `return 0.0` branch — zeros emerge from multiplication.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_P, M_N, GEV2_TO_CM2, reduced_mass,
    DELTA_U_P, DELTA_D_P, DELTA_S_P,
    DELTA_U_N, DELTA_D_N, DELTA_S_N,
)


def sigma_SD_zprime(mediator, *, dm_type: str, target: str = "proton") -> float:
    """
    Spin-dependent DM-nucleon cross section via Z' axial exchange.
    arXiv:2511.21808, Eq. 44 (plan v1) / Eq. 17 (paper v2).

    Formula (v-independent coefficient of the v² term; equal to the
    non-relativistic coefficient used in standard direct-detection limits):
      σ_SD = (4 μ²/π) × (g_χ g_Zp / m_Zp²)² × [C_A^N]²

    where:
      C_A^p = Δu^p Q_A[u] + Δd^p Q_A[d] + Δs^p Q_A[s]
      C_A^n = Δu^n Q_A[u] + Δd^n Q_A[d] + Δs^n Q_A[s]

    Nucleon axial form factors (Belanger/PDG):
      Δu^p =  0.842,  Δd^p = -0.427,  Δs^p = -0.085
      Δu^n = -0.427,  Δd^n =  0.842,  Δs^n = -0.085

    For all physical portals in arXiv:2511.21808, Q_A = 0 for all quarks,
    so C_A^N = 0 and σ_SD = 0.0 (exact, by arithmetic).

    For fabricated axial charges (used in tests T3.5/T3.6), the formula
    evaluates to non-zero values correctly.

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        Mandatory kwarg (guardrail). No symmetry-factor difference in
        σ_SD for Dirac vs Majorana at this level of approximation.
    target : str
        "proton" (default) or "neutron".

    Returns
    -------
    float : σ_SD (v-independent coefficient) in cm².
    """
    _ = dm_type  # mandatory kwarg; σ_SD convention same for Dirac/Majorana here

    charges = mediator.charges
    g_Zp = mediator.g_Zp
    g_chi = mediator.g_chi
    m_Zp = mediator.m_Zp
    m_DM = mediator.m_DM

    # Nucleon mass
    if target == "proton":
        m_N = M_P
        delta_u = DELTA_U_P
        delta_d = DELTA_D_P
        delta_s = DELTA_S_P
    elif target == "neutron":
        m_N = M_N
        delta_u = DELTA_U_N
        delta_d = DELTA_D_N
        delta_s = DELTA_S_N
    else:
        raise ValueError(f"target must be 'proton' or 'neutron', got '{target}'")

    # Axial nucleon charge C_A^N = Σ_{q∈{u,d,s}} Δq^N × Q_A[q]
    # Only u, d, s contribute to nucleon spin content (heavy quarks negligible).
    Q_A_u = charges.Q_A["u"]
    Q_A_d = charges.Q_A["d"]
    Q_A_s = charges.Q_A["s"]

    C_A_N = delta_u * Q_A_u + delta_d * Q_A_d + delta_s * Q_A_s

    # DM-nucleon reduced mass
    mu = reduced_mass(m_DM, m_N)

    # σ_SD = (4 μ²/π) × (g_χ g_Zp / m_Zp²)² × C_A^N²
    sigma_gev2 = (4.0 * mu**2 / math.pi) * (g_chi * g_Zp / m_Zp**2)**2 * C_A_N**2

    return sigma_gev2 * GEV2_TO_CM2
