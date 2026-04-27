"""
Thermally-averaged DM annihilation cross-section for 2HDM+a.
arXiv:2509.08043, Eqs. 41-42.

The DM pair-annihilation χχ̄ → ff̄ proceeds via s-channel pseudoscalar mediator (a or A).
The dominant channel is typically χχ̄ → bb̄ (bottom quarks) at the GCE-fit benchmark.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import GEV2_TO_CM2, M_B, M_T, M_C, M_S


# Quark Yukawa couplings for type-II 2HDM (tan_beta enhancement for down-type)
_YUKAWA_QUARKS = {
    'b': M_B,
    't': M_T,
    'c': M_C,
    's': M_S,
}


def sigma_v_2hdma_xx_ff(
    m_chi: float,
    m_a: float,
    g_chi: float,
    theta: float,
    tan_beta: float,
    final_state: str = 'b',
) -> float:
    """Thermally-averaged χχ̄ → ff̄ cross-section via pseudoscalar mediator (Eqs. 41-42).

    Dominant s-wave (p-wave suppressed for pseudoscalar) contribution:
        ⟨σv⟩ = Nc * m_f² * g_chi_a² * g_f_a² / (8π) * (s - 4m_f²)^{1/2} * β_f / (s - m_a²)² + Γ_a²)
    In the non-relativistic DM limit (s ~ 4*m_chi²):

        σv ≈ g_{χχa}² * g_{fa}² * Nc * m_f² / (8π m_chi² [(4m_chi² - m_a²)² + Γ_a²])
             * sqrt(1 - m_f²/m_chi²)

    where g_{χχa} = g_chi * cos(θ) (Eq. 41) and g_{fa} = m_f/(v*tan_β) for type-II.

    Parameters
    ----------
    m_chi      : float — DM mass [GeV]
    m_a        : float — light pseudoscalar mass [GeV]
    g_chi      : float — overall DM Yukawa coupling
    theta      : float — mixing angle [rad]
    tan_beta   : float — tan(β) (ratio of Higgs VEVs)
    final_state: str   — quark flavor ('b', 't', 'c', 's'; default 'b')

    Returns
    -------
    float : ⟨σv⟩ in cm³/s
    """
    from models.two_hdm_plus_a import g_chi_a as _g_chi_a

    if final_state not in _YUKAWA_QUARKS:
        raise ValueError(f"Unknown final state '{final_state}'. Use: {list(_YUKAWA_QUARKS.keys())}")

    m_f = _YUKAWA_QUARKS[final_state]

    if m_chi < m_f:
        return 0.0  # kinematically forbidden

    Nc = 3  # color factor for quarks

    # DM-a coupling
    gca = _g_chi_a(g_chi, theta)

    # Type-II Yukawa: down-type quarks get tan_beta enhancement
    if final_state in ('b', 's'):
        g_f = m_f / (246.22 * tan_beta)  # down-type: 1/tan_beta suppression in v_SM
    else:
        g_f = m_f / 246.22  # up-type: standard Yukawa

    # Center-of-mass energy squared at threshold (NR DM)
    s = 4.0 * m_chi**2

    # Propagator: 1/((s - m_a^2)^2) (neglect width for simplicity)
    prop_sq = 1.0 / (s - m_a**2)**2

    # Phase space factor
    if m_f >= m_chi:
        return 0.0
    beta_f = np.sqrt(1.0 - m_f**2 / m_chi**2)

    # σv in GeV^{-2}
    sigma_v_gev2 = (Nc * m_f**2 * gca**2 * g_f**2 / (8.0 * np.pi)
                    * prop_sq * s * beta_f)

    # Convert to cm³/s
    return sigma_v_gev2 * GEV2_TO_CM2 * 3e10
