"""
Tree-level spin-independent DM-nucleon cross-sections.
arXiv:2506.19062, Eq. (5).

These are the standard Higgs-portal and Z-portal SI cross-sections
at leading order, before loop corrections.
"""

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_P, M_N, V_H, M_H, M_Z,
    F_U_P, F_D_P, F_S_P, F_TG_P,
    F_U_N, F_D_N, F_S_N, F_TG_N,
    GEV2_TO_CM2, reduced_mass,
)


def sigma_SI_higgs_portal(
    m_chi: float,
    y_h_chi_chi: float,
    m_h: float = M_H,
    m_target: float = M_P,
    v: float = V_H,
    f_u: float = F_U_P,
    f_d: float = F_D_P,
    f_s: float = F_S_P,
) -> float:
    """
    Tree-level SI cross-section from Higgs exchange (Eq. 5, first line).

    sigma_SI = (mu^2 / pi) * (m_N / v_h)^2 * |y_{h chi chi}|^2 / m_h^4
               * |sum_q f_q|^2

    The sum over quark form factors gives the effective Higgs-nucleon coupling:
      f_N = sum_{q=u,d,s} f_q + (2/27) * f_{TG} * sum_{q=c,b,t} 1
          = sum_{q=u,d,s} f_q + (2/27) * (1 - f_u - f_d - f_s) * 3

    Parameters
    ----------
    m_chi          : DM mass [GeV]
    y_h_chi_chi    : effective h-DM-DM coupling
    m_h            : Higgs mass [GeV]
    m_target       : target nucleon mass [GeV]
    v              : Higgs VEV [GeV]
    f_u, f_d, f_s  : nucleon scalar form factors

    Returns
    -------
    sigma_SI : float [cm^2]
    """
    mu = reduced_mass(m_chi, m_target)
    f_TG = 1.0 - f_u - f_d - f_s

    # Effective Higgs-nucleon coupling
    f_N = f_u + f_d + f_s + (2.0 / 27.0) * f_TG * 3

    sigma = (mu**2 / np.pi) * (m_target / v)**2 * y_h_chi_chi**2 / m_h**4 * f_N**2

    return sigma * GEV2_TO_CM2  # convert to cm^2


def sigma_SI_two_higgs(
    m_chi: float,
    y_h_chi_chi: float,
    y_H_chi_chi: float,
    m_h: float = M_H,
    m_H_heavy: float = 300.0,
    m_target: float = M_P,
    v: float = V_H,
    g_h_qq: float = 1.0,
    g_H_qq: float = 1.0,
    f_u: float = F_U_P,
    f_d: float = F_D_P,
    f_s: float = F_S_P,
) -> float:
    """
    Tree-level SI cross-section with two Higgs mediators (h and H).

    For the SD+2HDM model, both h and H contribute coherently:

    A ~ y_{h chi chi} * g_{h qq} / m_h^2 + y_{H chi chi} * g_{H qq} / m_H^2

    The blind spot occurs when A = 0.

    Parameters
    ----------
    g_h_qq  : h-quark coupling relative to SM (= 1 in alignment limit)
    g_H_qq  : H-quark coupling relative to SM (depends on 2HDM type)
    """
    mu = reduced_mass(m_chi, m_target)
    f_TG = 1.0 - f_u - f_d - f_s
    f_N = f_u + f_d + f_s + (2.0 / 27.0) * f_TG * 3

    # Combined amplitude from h and H exchange
    A = (y_h_chi_chi * g_h_qq / m_h**2
         + y_H_chi_chi * g_H_qq / m_H_heavy**2)

    sigma = (mu**2 / np.pi) * (m_target / v)**2 * A**2 * f_N**2

    return sigma * GEV2_TO_CM2


def sigma_SI_rescaled(sigma_SI: float, xi: float) -> float:
    """
    Rescale SI cross-section by relic density fraction.

    If the DM candidate does not saturate the observed relic density
    (Omega_chi < Omega_DM), the effective cross-section is:

    sigma_eff = xi * sigma_SI

    where xi = Omega_chi / Omega_DM.

    This is what experiments actually constrain.
    """
    return xi * sigma_SI


def blind_spot_amplitude_2h(
    y_h: float, y_H: float,
    m_h: float, m_H: float,
    g_h_qq: float = 1.0,
    g_H_qq: float = 1.0,
) -> float:
    """
    The scattering amplitude that vanishes at the blind spot.

    A = y_h * g_h_qq / m_h^2 + y_H * g_H_qq / m_H^2

    Returns A. The cross-section is proportional to A^2.
    """
    return y_h * g_h_qq / m_h**2 + y_H * g_H_qq / m_H**2
