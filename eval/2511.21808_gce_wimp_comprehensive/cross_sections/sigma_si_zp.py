"""
Spin-independent DM-nucleon cross section via Z' exchange.
arXiv:2511.21808, Eq. 39 (plan v1 numbering); actual paper Eq. 15.

CASE A nuclear form factor convention (Phase-0.5 D3 decision):
  The paper uses VALENCE QUARK COUNTING for vector Z' SI cross section:
    f_p = 2 Q_V[u] g_Zp + Q_V[d] g_Zp   (proton = 2u + 1d valence quarks)
    f_n = Q_V[u] g_Zp + 2 Q_V[d] g_Zp   (neutron = 1u + 2d valence quarks)

  This is NOT the Hoferichter scalar sigma-term form factor; it is the
  coherent vector charge of the nucleon.

  Source: arXiv:2511.21808, Section II.1/II.5, text below Eq. 15:
  "f_p = 2V_u + V_d, f_n = V_u + 2V_d" where V_q = Q_V[q] g_Zp.

Formula:
  σ_SI = (μ²/π) × (g_χ × f_N)² / m_Zp⁴ × GEV2_TO_CM2

where f_N = g_Zp × (2 Q_V[u] + Q_V[d]) for proton.

B-L portal: Q_V[u] = Q_V[d] = 1/3 → f_p = g_Zp × 1 → σ_SI = (μ²/π)(g_χ g_Zp)²/m_Zp⁴
Lᵢ-Lⱼ portals: Q_V[u] = Q_V[d] = 0 → f_p = 0 → σ_SI = 0 (by arithmetic, no branch)

Identity: Lᵢ-Lⱼ gives exactly zero by arithmetic (Q_V[q]=0 for quarks).
No special-case `return 0.0` branch — zeros fall out from multiplication.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import M_P, M_N, GEV2_TO_CM2, reduced_mass


def sigma_SI_zprime(mediator, *, dm_type: str, target: str = "proton") -> float:
    """
    Spin-independent DM-nucleon cross section via Z' vector exchange.
    arXiv:2511.21808, Eq. 39 (plan v1) / Eq. 15 (paper v2).

    Implementation uses VALENCE QUARK COUNTING (Case A, Phase-0.5 D3):
      f_p = g_Zp × (2 Q_V[u] + Q_V[d])
      f_n = g_Zp × (Q_V[u] + 2 Q_V[d])

    Full formula:
      σ_SI = (μ²/π) × (g_χ × f_N)² / m_Zp⁴

    where μ = m_DM × m_N / (m_DM + m_N) is the DM-nucleon reduced mass.

    Lᵢ-Lⱼ portals: Q_V[u] = Q_V[d] = 0 → f_N = 0 → σ_SI = 0.0 (arithmetic).
    B-L portal: Q_V[u] = Q_V[d] = 1/3 → f_p = f_n = g_Zp → σ_SI = (μ²/π)(g_χ g_Zp)²/m_Zp⁴.

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        Mandatory kwarg (guardrail). For Dirac DM, no symmetry factor difference
        in σ_SI (unlike σv). Retained for uniform call-site signature.
    target : str
        "proton" (default) or "neutron".

    Returns
    -------
    float : σ_SI in cm².
    """
    _ = dm_type  # mandatory kwarg; no sigma_SI dependence on dm_type for vector Z'

    charges = mediator.charges
    g_Zp = mediator.g_Zp
    g_chi = mediator.g_chi
    m_Zp = mediator.m_Zp
    m_DM = mediator.m_DM

    # Nucleon mass for reduced mass calculation
    if target == "proton":
        m_N = M_P
    elif target == "neutron":
        m_N = M_N
    else:
        raise ValueError(f"target must be 'proton' or 'neutron', got '{target}'")

    # Nucleon coupling via valence quark counting (Case A)
    # Proton = 2u + 1d, Neutron = 1u + 2d
    Q_V_u = charges.Q_V["u"]
    Q_V_d = charges.Q_V["d"]

    if target == "proton":
        # f_p = g_Zp × (2 Q_V[u] + Q_V[d])
        # Factor 2 for valence up-quarks in proton, 1 for down-quarks
        f_N = g_Zp * (2.0 * Q_V_u + 1.0 * Q_V_d)
    else:
        # f_n = g_Zp × (Q_V[u] + 2 Q_V[d])
        f_N = g_Zp * (1.0 * Q_V_u + 2.0 * Q_V_d)

    # DM-nucleon reduced mass
    mu = reduced_mass(m_DM, m_N)

    # σ_SI = (μ²/π) × (g_χ f_N)² / m_Zp⁴
    sigma_gev2 = (mu**2 / math.pi) * (g_chi * f_N)**2 / m_Zp**4

    # Convert to cm²
    return sigma_gev2 * GEV2_TO_CM2
