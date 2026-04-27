"""
Tree-level spin-dependent DM-nucleon cross-sections.
arXiv:2506.19062, Eq. (5), second expression.
"""

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_P, M_Z,
    A_U_Z, A_D_Z,
    DELTA_U_P, DELTA_D_P, DELTA_S_P,
    GEV2_TO_CM2, reduced_mass,
)


def sigma_SD_Z_exchange(
    m_chi: float,
    y_Z_chi_chi: float,
    m_target: float = M_P,
    m_Z: float = M_Z,
) -> float:
    """
    Tree-level SD cross-section from Z exchange (Eq. 5, second line).

    sigma_SD = (3 * mu^2 / (pi * m_Z^4)) * |y^A_{Z chi chi}|^2
               * [A_u^Z * Delta_u^p + A_d^Z * (Delta_d^p + Delta_s^p)]^2

    Parameters
    ----------
    m_chi       : DM mass [GeV]
    y_Z_chi_chi : axial Z-DM-DM coupling

    Returns
    -------
    sigma_SD : float [cm^2]
    """
    mu = reduced_mass(m_chi, m_target)

    # Nucleon spin content from Z coupling
    spin_factor = (A_U_Z * DELTA_U_P
                   + A_D_Z * (DELTA_D_P + DELTA_S_P))

    sigma = (3.0 * mu**2 / (np.pi * m_Z**4)) * y_Z_chi_chi**2 * spin_factor**2

    return sigma * GEV2_TO_CM2
