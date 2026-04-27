"""
2HDM+a (Two-Higgs-Doublet Model + pseudoscalar mediator) dark matter model.
arXiv:2506.19062, Eqs. (20)-(25).

The DM chi is a Dirac fermion that couples to a gauge-singlet pseudoscalar a^0,
which mixes with the 2HDM pseudoscalar A through a portal coupling kappa.
SI scattering is loop-suppressed: tree-level SI vanishes by CP symmetry
(pseudoscalar mediator cannot generate a scalar-type nucleon operator).

Parameters:
  m_chi    : DM mass [GeV]
  m_a      : light pseudoscalar mass [GeV]
  m_H      : heavy scalar mass [GeV]
  m_A      : heavy pseudoscalar mass [GeV]
  m_Hpm    : charged Higgs mass [GeV]
  y_chi    : DM Yukawa coupling to pseudoscalar
  sin_theta: pseudoscalar mixing angle sin(theta)
  tan_beta : ratio of Higgs VEVs
  lambda_3 : 2HDM quartic coupling
  lambda_1P: portal coupling (Phi_1-a^0)
  lambda_2P: portal coupling (Phi_2-a^0)

Scan ranges (Eq. 24):
  m_chi in [1, 1000] GeV
  m_a in [10, 600] GeV
  m_H, m_Hpm, m_A in [m_h, 1500] GeV
  y_chi in [1e-3, 10]
  sin_theta in [-sin(pi/4), sin(pi/4)]
  tan_beta in [1, 60]
  lambda_3, lambda_1P, lambda_2P in [-4*pi, 4*pi]
"""

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_H as M_h


def pseudoscalar_mixing_angle(kappa: float, m_A: float, m_a0: float,
                               v: float = V_H) -> float:
    """
    Pseudoscalar mixing angle theta from Eq. (21).

    tan(2*theta) = 2 * kappa * v / (m_A^2 - m_a0^2)

    Parameters
    ----------
    kappa : float — portal coupling [GeV]
    m_A   : float — heavy pseudoscalar mass [GeV]
    m_a0  : float — bare singlet pseudoscalar mass [GeV]
    v     : float — Higgs VEV [GeV]

    Returns
    -------
    theta : float — mixing angle [rad]
    """
    if abs(m_A**2 - m_a0**2) < 1e-30:
        return np.pi / 4.0 * np.sign(kappa)
    return 0.5 * np.arctan2(2 * kappa * v, m_A**2 - m_a0**2)


def physical_pseudoscalar_masses(m_A: float, m_a0: float,
                                  kappa: float, v: float = V_H
                                  ) -> tuple[float, float]:
    """
    Physical pseudoscalar masses after mixing.

    The mass-squared matrix in the (A, a^0) basis:
      [[m_A^2, kappa*v], [kappa*v, m_a0^2]]

    Returns (m_light, m_heavy).
    """
    avg = 0.5 * (m_A**2 + m_a0**2)
    diff = 0.5 * (m_A**2 - m_a0**2)
    off = kappa * v
    discriminant = np.sqrt(diff**2 + off**2)
    m_light = np.sqrt(max(0, avg - discriminant))
    m_heavy = np.sqrt(avg + discriminant)
    return m_light, m_heavy


def trilinear_haa(lambda_1P: float, lambda_2P: float, tan_beta: float,
                  v: float = V_H, m_h: float = M_h) -> float:
    """
    Trilinear coupling lambda_{haa} in the sin(theta) -> 0 limit (Eq. 25).

    lambda_{haa} = -(2 * v / m_h) * (lambda_1P * cos^2(beta) + lambda_2P * sin^2(beta))

    This enters the triangle diagram contribution to the SI cross-section.

    Returns
    -------
    lambda_haa : float [GeV]
    """
    beta = np.arctan(tan_beta)
    cb2 = np.cos(beta)**2
    sb2 = np.sin(beta)**2
    return -(2 * v / m_h) * (lambda_1P * cb2 + lambda_2P * sb2)


def trilinear_Haa(lambda_1P: float, lambda_2P: float, tan_beta: float,
                  m_H: float, v: float = V_H) -> float:
    """
    Trilinear coupling lambda_{Haa} in the sin(theta) -> 0 limit (Eq. 25).

    lambda_{Haa} = (v / m_H) * sin(2*beta) * (lambda_1P - lambda_2P)

    Returns
    -------
    lambda_Haa : float [GeV]
    """
    beta = np.arctan(tan_beta)
    return (v / m_H) * np.sin(2 * beta) * (lambda_1P - lambda_2P)


def dm_pseudoscalar_coupling(y_chi: float, sin_theta: float) -> tuple[float, float]:
    """
    DM coupling to physical pseudoscalar mass eigenstates (Eq. 22).

    L contains: i * y_chi * chi_bar * gamma_5 * chi * (a * cos(theta) + A * sin(theta))

    Returns
    -------
    (g_chi_a, g_chi_A) : DM coupling to light a and heavy A
    """
    cos_theta = np.sqrt(1 - sin_theta**2)
    return y_chi * cos_theta, y_chi * sin_theta


def quark_pseudoscalar_couplings_type_I(tan_beta: float, sin_theta: float,
                                         m_q: float, v: float = V_H
                                         ) -> tuple[float, float]:
    """
    Quark coupling to pseudoscalars in Type-I 2HDM.

    All quarks couple to Phi_2, so:
      g_{a qq} = (m_q / v) * sin(theta) / tan(beta)
      g_{A qq} = (m_q / v) * cos(theta) / tan(beta)

    Returns (g_a_qq, g_A_qq).
    """
    cos_theta = np.sqrt(1 - sin_theta**2)
    base = m_q / (v * tan_beta)
    return base * sin_theta, base * cos_theta


def quark_pseudoscalar_couplings_type_II(tan_beta: float, sin_theta: float,
                                          m_q: float, is_up_type: bool,
                                          v: float = V_H
                                          ) -> tuple[float, float]:
    """
    Quark coupling to pseudoscalars in Type-II 2HDM.

    Up-type: g ~ m_q / (v * tan_beta)
    Down-type: g ~ m_q * tan_beta / v

    Returns (g_a_qq, g_A_qq).
    """
    cos_theta = np.sqrt(1 - sin_theta**2)
    if is_up_type:
        base = m_q / (v * tan_beta)
    else:
        base = m_q * tan_beta / v
    return base * sin_theta, base * cos_theta


def scan_ranges() -> dict:
    """Parameter scan ranges from Eq. (24)."""
    return {
        "m_chi": (1.0, 1000.0),
        "m_a": (10.0, 600.0),
        "m_H": (M_h, 1500.0),
        "m_Hpm": (M_h, 1500.0),
        "m_A": (M_h, 1500.0),
        "y_chi": (1e-3, 10.0),
        "sin_theta": (-np.sin(np.pi / 4), np.sin(np.pi / 4)),
        "tan_beta": (1.0, 60.0),
        "lambda_3": (-4 * np.pi, 4 * np.pi),
        "lambda_1P": (-4 * np.pi, 4 * np.pi),
        "lambda_2P": (-4 * np.pi, 4 * np.pi),
    }
