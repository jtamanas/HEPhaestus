"""
Invisible decay widths and branching ratios for h and Z in the scotogenic inverse seesaw.
arXiv:2603.23040, Eqs. 19a-b.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import M_H, M_Z, GAMMA_H_SM, GAMMA_Z_SM


def Gamma_h_to_chichi(
    m_chi: float,
    y_hchichi: float,
    m_h: float = M_H,
) -> float:
    """Eq. 19a. Partial width Gamma(h -> chi chi) [GeV].

    For a Majorana DM fermion chi1:
    Gamma(h -> chi chi) = y_hchichi^2 / (8 pi * m_h) * (1 - 4 m_chi^2 / m_h^2)^(3/2)

    Majorana factor note: identical-particle factor 1/2 and Majorana factor of 2
    from the Feynman rule combine to give net factor 1. No MAJORANA_FACTOR applied here.

    Returns 0 if m_h < 2*m_chi.

    Args:
        m_chi      DM mass [GeV]
        y_hchichi  effective h-chi-chi coupling [dimensionless]
        m_h        Higgs mass [GeV]
    Returns:
        Gamma(h -> chi chi) [GeV]
    """
    if m_h < 2.0 * m_chi:
        return 0.0
    phase_space = (1.0 - 4.0 * m_chi**2 / m_h**2)**1.5
    return y_hchichi**2 / (8.0 * np.pi * m_h) * phase_space


def Gamma_Z_to_chichi(
    m_chi: float,
    g_Zchichi_A: float,
    m_Z: float = M_Z,
) -> float:
    """Eq. 19b. Partial width Gamma(Z -> chi chi) [GeV].

    For a Majorana DM fermion chi1 with axial coupling g_Zchichi_A:
    Gamma(Z -> chi chi) = g_Zchichi_A^2 / (12 pi) * m_Z * (1 - 4 m_chi^2 / m_Z^2)^(3/2)

    Returns 0 exactly when 2*m_chi > m_Z (kinematically forbidden).

    Args:
        m_chi        DM mass [GeV]
        g_Zchichi_A  axial Z-chi-chi coupling [dimensionless]
        m_Z          Z boson mass [GeV]
    Returns:
        Gamma(Z -> chi chi) [GeV]
    """
    if 2.0 * m_chi > m_Z:
        return 0.0
    phase_space = (1.0 - 4.0 * m_chi**2 / m_Z**2)**1.5
    return g_Zchichi_A**2 / (12.0 * np.pi) * m_Z * phase_space


def BR_h_invisible(
    m_chi: float,
    y_hchichi: float,
    Gamma_h_SM: float = GAMMA_H_SM,
) -> float:
    """BR(h -> invisible) = Gamma(h -> chi chi) / (Gamma_h_SM + Gamma(h -> chi chi)).

    Experimental constraint: BR(h -> inv) < 0.107 (ATLAS).

    Args:
        m_chi       DM mass [GeV]
        y_hchichi   h-chi-chi coupling [dimensionless]
        Gamma_h_SM  SM Higgs total width [GeV]
    Returns:
        BR(h -> invisible) [dimensionless]
    """
    gamma_inv = Gamma_h_to_chichi(m_chi, y_hchichi)
    return gamma_inv / (Gamma_h_SM + gamma_inv)


def BR_Z_invisible(
    m_chi: float,
    g_Zchichi_A: float,
    Gamma_Z_SM: float = GAMMA_Z_SM,
) -> float:
    """BR(Z -> chi chi) contribution to invisible Z width.

    Args:
        m_chi         DM mass [GeV]
        g_Zchichi_A   axial Z-chi-chi coupling [dimensionless]
        Gamma_Z_SM    SM Z total width [GeV]
    Returns:
        BR(Z -> chi chi) [dimensionless]
    """
    gamma_z = Gamma_Z_to_chichi(m_chi, g_Zchichi_A)
    return gamma_z / (Gamma_Z_SM + gamma_z)
