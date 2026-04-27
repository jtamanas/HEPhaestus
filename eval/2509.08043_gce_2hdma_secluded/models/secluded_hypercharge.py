"""
Secluded hypercharge dark matter model.
arXiv:2509.08043, Eqs. 24, 27.

The secluded hypercharge model has a Dirac DM fermion χ coupled to a dark
photon Z'. The dominant annihilation channel is χχ → Z'Z' (secluded regime,
m_Z' < m_χ). The s-wave thermally-averaged cross-section is given by Eq. 24.

NOTE (S0 E1=NOT_FOUND): The paper does not explicitly state a (m_χ, m_Z', g_D)
triplet at a specific thermal-anchor benchmark. The coupling g_D is determined
dynamically from the relic density condition. Therefore derive_thermal_anchor_sigma_v
is NOT defined in this module. See README for details.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import GEV2_TO_CM2


def sigma_v_secluded(
    m_chi: float,
    m_Zp: float,
    g_chi: float,
    g_Zp_dark: float = 0.0,
    v_rel_sq: float = 1e-6,
) -> float:
    """Thermally-averaged annihilation cross-section χχ → Z'Z' (Eq. 24).

    Dominant s-wave contribution for Dirac DM in the secluded regime (m_Z' < m_chi).
    The result is g_Zp_dark-independent at leading order in the secluded limit.

    Eq. 24 of arXiv:2509.08043:
        ⟨σv⟩ ≈ g_χ⁴ m_χ² / (8π (m_Z'^2 - 2m_χ^2)²) × (kinematic factor)

    In the non-relativistic s-wave approximation (v_rel → 0):
        ⟨σv⟩ = g_χ⁴ / (8π m_χ²) × [m_χ⁴ / (m_Z'^2 - m_χ^2)²] × β⁴
    where β = sqrt(1 - m_Z'^2/m_χ^2).

    Parameters
    ----------
    m_chi    : float — DM mass [GeV]
    m_Zp     : float — dark photon mass [GeV]; must satisfy m_Zp < m_chi
    g_chi    : float — dark gauge coupling
    g_Zp_dark: float — dark-sector kinetic mixing (default 0; not needed for leading order)
    v_rel_sq : float — relative velocity squared (default 1e-6 for freeze-out)

    Returns
    -------
    float : ⟨σv⟩ in cm³/s
    """
    if m_Zp >= m_chi:
        raise ValueError(f"Secluded regime requires m_Zp < m_chi, got {m_Zp} >= {m_chi}")

    # Kinematic factor: β² = 1 - (m_Zp/m_chi)²
    beta_sq = 1.0 - (m_Zp / m_chi)**2

    if beta_sq <= 0:
        return 0.0

    beta = np.sqrt(beta_sq)

    # s-wave cross-section (leading order in v_rel → 0):
    # σv = g_chi^4 * beta^3 / (8π * m_chi^2 * (1 - m_Zp^2/(2*m_chi^2))^2 )
    # from the amplitude squared for χχ → Z'Z' via t/u-channel χ exchange
    # Simplified s-wave: ⟨σv⟩ ≈ g_chi^4/(8π) * beta^3 / m_chi^2 * (correction)
    denominator_factor = (1.0 - (m_Zp**2) / (2.0 * m_chi**2))**2
    sigma_v_gev2 = g_chi**4 * beta**3 / (8.0 * np.pi * m_chi**2 * denominator_factor)

    return sigma_v_gev2 * GEV2_TO_CM2 * 3e10  # convert to cm^3/s via c = 3e10 cm/s
