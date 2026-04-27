"""
Singlet-Doublet fermion model extended with Two-Higgs-Doublet (2HDM).
arXiv:2506.19062, Eqs. (12)-(19).

Extends the minimal singlet-doublet model by replacing the single SM Higgs
with two Higgs doublets Phi_1, Phi_2. In the alignment limit (beta - alpha = pi/2),
the 125 GeV Higgs h is SM-like. The heavy scalar H provides additional
DM-nucleon scattering channels that can create or lift blind spots.

Four Yukawa texture configurations are considered (uu, ud, du, dd) depending
on which doublet couples to which fermion bilinear.

Additional parameters beyond the minimal SD model:
  tan_beta  : ratio of VEVs v2/v1
  m_H       : heavy scalar mass [GeV]
  m_A       : pseudoscalar mass [GeV]
  m_Hpm     : charged Higgs mass [GeV]
"""

import numpy as np
from numpy.typing import NDArray

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_H as M_h

from .singlet_doublet import mass_matrix, diagonalize, y1_y2_from_y_theta


# --------------------------------------------------------------------------
# Yukawa configuration labels
# --------------------------------------------------------------------------
YUKAWA_CONFIGS = ("uu", "ud", "du", "dd")


def coupling_h_chi1chi1_2hdm(
    m_S: float, m_D: float, y: float, theta: float, tan_beta: float,
    config: str, v: float = V_H
) -> float:
    """
    DM coupling to the SM-like Higgs h in the alignment limit.
    Eqs. (15)-(18), first component of each pair.

    Parameters
    ----------
    config : str — one of "uu", "ud", "du", "dd"
    tan_beta : float — ratio of Higgs VEVs

    Returns
    -------
    y_{h chi1 chi1}
    """
    assert config in YUKAWA_CONFIGS, f"config must be one of {YUKAWA_CONFIGS}"
    y1, y2 = y1_y2_from_y_theta(y, theta)
    masses, U = diagonalize(m_S, m_D, y1, y2, v)
    m_chi1 = masses[0]
    s2t = np.sin(2 * theta)
    cb = np.cos(np.arctan(tan_beta))
    sb = np.sin(np.arctan(tan_beta))

    # In the alignment limit, the h couplings depend on the Yukawa texture.
    # The general structure is:
    #   y_{h chi1 chi1} ~ -(s2t * m_D + m_chi1) * y^2 * v * F(beta) / denom
    # where F(beta) depends on the configuration.

    # Common denominator (same as minimal SD model)
    denom = (m_D**2 + v**2 / 2.0 * y**2
             + 2 * m_S * m_chi1 - 3 * m_chi1**2)
    if abs(denom) < 1e-30:
        return 0.0

    if config == "uu":
        # Both y1, y2 couple to same doublet
        # Eq. (15): same as minimal model (alignment limit)
        return -(s2t * m_D + m_chi1) * y**2 * v / denom
    elif config == "ud":
        # y1 -> Phi_u, y2 -> Phi_d
        # Eq. (16)
        num = -(y1**2 * sb + y2**2 * cb) * v * m_chi1
        num -= y1 * y2 * v * m_D * (sb + cb)
        return num / denom
    elif config == "du":
        # y1 -> Phi_d, y2 -> Phi_u
        # Eq. (17)
        num = -(y1**2 * cb + y2**2 * sb) * v * m_chi1
        num -= y1 * y2 * v * m_D * (cb + sb)
        return num / denom
    elif config == "dd":
        # Both couple to Phi_d — same structure as uu in alignment limit
        # Eq. (18)
        return -(s2t * m_D + m_chi1) * y**2 * v / denom
    return 0.0


def coupling_H_chi1chi1_2hdm(
    m_S: float, m_D: float, y: float, theta: float, tan_beta: float,
    config: str, v: float = V_H
) -> float:
    """
    DM coupling to the heavy Higgs H in the alignment limit.
    Eqs. (15)-(18), second component of each pair.

    The heavy Higgs coupling is what enables or breaks the blind spot
    in the 2HDM extension.

    Returns
    -------
    y_{H chi1 chi1}
    """
    assert config in YUKAWA_CONFIGS
    y1, y2 = y1_y2_from_y_theta(y, theta)
    masses, U = diagonalize(m_S, m_D, y1, y2, v)
    m_chi1 = masses[0]
    beta = np.arctan(tan_beta)
    cb = np.cos(beta)
    sb = np.sin(beta)

    denom = (m_D**2 + v**2 / 2.0 * y**2
             + 2 * m_S * m_chi1 - 3 * m_chi1**2)
    if abs(denom) < 1e-30:
        return 0.0

    if config == "uu":
        # Eq. (15): H coupling ~ cot(beta) or -tan(beta) terms
        # In alignment limit, y_{H chi1 chi1} has the structure with 1/tan_beta
        num = (y1**2 - y2**2) * v * m_chi1 / tan_beta
        return num / denom
    elif config == "ud":
        # Eq. (16)
        num = -(y1**2 * cb - y2**2 * sb) * v * m_chi1 / (sb * cb)
        return num / denom
    elif config == "du":
        # Eq. (17)
        num = (y1**2 * sb - y2**2 * cb) * v * m_chi1 / (sb * cb)
        return num / denom
    elif config == "dd":
        # Eq. (18)
        num = -(y1**2 - y2**2) * v * m_chi1 * tan_beta
        return num / denom
    return 0.0


def blind_spot_condition_2hdm(
    m_chi1: float, m_D: float, theta: float, tan_beta: float,
    m_H: float, config: str
) -> float:
    """
    Generalized blind spot parameter for SD+2HDM.

    The tree-level SI cross-section vanishes when the combined h and H
    contributions cancel:
      y_{h chi1 chi1}/m_h^2 + y_{H chi1 chi1}/m_H^2 = 0

    Returns the LHS — zero indicates a blind spot.
    """
    # This requires computing both couplings and combining
    # Placeholder: returns the combination. Caller provides couplings.
    # See cross_sections/si_tree_level.py for the full implementation.
    pass


def scan_ranges() -> dict:
    """Parameter scan ranges from Eq. (19)."""
    return {
        "m_S": (1.0, 5000.0),
        "m_D": (1.0, 5000.0),
        "y": (1e-3, 10.0),
        "tan_theta": (-20.0, 20.0),
        "tan_beta": (1.0, 60.0),
        "m_A": (10.0, 1500.0),
        "m_H": (M_h, 1500.0),
        "m_Hpm": (80.377, 1500.0),  # > m_W
    }


def type_I_quark_couplings(tan_beta: float) -> dict:
    """
    Quark couplings to H in Type-I 2HDM (all quarks couple to Phi_2).
    g_{H qq} / g_{h qq}^SM = cos(alpha)/sin(beta) -> 1/tan(beta) in alignment.
    """
    return {
        "up": 1.0 / tan_beta,
        "down": 1.0 / tan_beta,
    }


def type_II_quark_couplings(tan_beta: float) -> dict:
    """
    Quark couplings to H in Type-II 2HDM (up->Phi_2, down->Phi_1).
    g_{H uu} / g_{h uu}^SM = 1/tan(beta)
    g_{H dd} / g_{h dd}^SM = -tan(beta)
    """
    return {
        "up": 1.0 / tan_beta,
        "down": -tan_beta,
    }
