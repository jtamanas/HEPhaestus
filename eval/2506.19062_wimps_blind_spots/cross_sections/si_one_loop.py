"""
One-loop spin-independent DM-nucleon cross-sections.
arXiv:2506.19062, Eqs. (9), (14), (23).

These are the main results of the paper: the loop-corrected SI cross-sections
that set the effective detection floor when the tree-level cross-section is
suppressed (blind spot regions).

The full one-loop calculation involves:
  - Triangle diagrams (Higgs mediator with BSM particles in the loop)
  - Box diagrams (four-point DM-quark scattering)
  - Electroweak corrections (W/Z loops)

Wilson coefficients are matched onto the effective Lagrangian:
  L_eff = sum_q C_q * m_q * chi_bar chi * q_bar q
        + C_G * chi_bar chi * G^a_mu_nu G^a,mu_nu
        + sum_q (C_{1,q} chi_bar i d_mu gamma_nu chi + C_{5,q} chi_bar gamma_mu chi)
          * q_bar gamma^mu q    [twist-2 operators]
"""

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_P, V_H, M_H, M_Z, M_W,
    F_U_P, F_D_P, F_S_P, F_TG_P,
    Q2_U_P, Q2_D_P, QBAR2_U_P, QBAR2_D_P, Q2_S_P, Q2_C_P, Q2_B_P,
    GEV2_TO_CM2, reduced_mass,
)


def sigma_SI_one_loop_SD(
    m_chi1: float,
    C_triangle: float,
    C1_box: float,
    C5_box: float,
    C6_box: float,
    CG_box: float,
    C_q_EW: dict,
    G_q_EW: dict,
    CG_EW: float,
    m_target: float = M_P,
    v: float = V_H,
) -> float:
    """
    Full one-loop SI cross-section for the singlet-doublet model (Eq. 9).

    sigma_SI = (mu^2 / pi) * (m_p / v_h)^2 * |A|^2

    where A = sum_q f_q * [...] + twist-2 + gluon terms

    Parameters
    ----------
    C_triangle : float — triangle diagram coefficient (Eq. 31)
    C1_box, C5_box, C6_box : float — box diagram coefficients (Eq. 34)
    CG_box : float — gluon box coefficient (Eq. 34)
    C_q_EW : dict — {q: value} EW correction coefficients for each quark
    G_q_EW : dict — {q: value} EW twist-2 correction coefficients
    CG_EW  : float — EW gluon correction

    Returns
    -------
    sigma_SI : float [cm^2]
    """
    mu = reduced_mass(m_chi1, m_target)

    # Form factors for proton
    f_q = {"u": F_U_P, "d": F_D_P, "s": F_S_P}
    f_TG = F_TG_P

    # Quark PDF moments
    q2 = {
        "u": Q2_U_P, "d": Q2_D_P, "s": Q2_S_P,
        "c": Q2_C_P, "b": Q2_B_P
    }
    qbar2 = {
        "u": QBAR2_U_P, "d": QBAR2_D_P, "s": Q2_S_P,
        "c": Q2_C_P, "b": Q2_B_P
    }

    # Build the amplitude
    A = 0.0

    # Triangle + scalar form factor contributions
    for q in ["u", "d", "s"]:
        c_ew = C_q_EW.get(q, 0.0)
        A += f_q[q] * (C_triangle + c_ew)

    # Box contributions (twist-2 operators)
    for q in ["u", "d", "s", "c", "b"]:
        g_ew = G_q_EW.get(q, 0.0)
        A += (3.0 / 4.0) * (q2[q] + qbar2[q]) * (C1_box + m_chi1 * C5_box + g_ew)

    # Gluon contributions
    A += (2.0 / 27.0) * f_TG * (CG_box + CG_EW)

    sigma = (mu**2 / np.pi) * (m_target / v)**2 * A**2
    return sigma * GEV2_TO_CM2


def sigma_SI_one_loop_2HDMa(
    m_chi: float,
    C_q_triangle: dict,
    C_q_box: dict,
    C1_box: dict,
    C2_box: dict,
    CG_box: float,
    m_target: float = M_P,
    v: float = V_H,
) -> float:
    """
    Full one-loop SI cross-section for the 2HDM+a model (Eq. 23).

    sigma_SI = (mu^2/pi) * (m_p/v_h)^2 * |A|^2

    where A sums triangle, box, twist-2, and gluon contributions.

    Parameters
    ----------
    C_q_triangle : dict — {q: value} triangle coefficients for each quark
    C_q_box      : dict — {q: value} scalar box coefficients
    C1_box       : dict — {q: value} twist-2 box coefficient (momentum-independent)
    C2_box       : dict — {q: value} twist-2 box coefficient (momentum-dependent)
    CG_box       : float — gluon box coefficient

    Returns
    -------
    sigma_SI : float [cm^2]
    """
    mu = reduced_mass(m_chi, m_target)

    f_q = {"u": F_U_P, "d": F_D_P, "s": F_S_P}
    f_TG = F_TG_P
    q2 = {
        "u": Q2_U_P, "d": Q2_D_P, "s": Q2_S_P,
        "c": Q2_C_P, "b": Q2_B_P
    }
    qbar2 = {
        "u": QBAR2_U_P, "d": QBAR2_D_P, "s": Q2_S_P,
        "c": Q2_C_P, "b": Q2_B_P
    }

    A = 0.0

    # Triangle contributions (through Higgs mediator)
    for q in ["u", "d", "s"]:
        tri = C_q_triangle.get(q, 0.0)
        box = C_q_box.get(q, 0.0)
        A += f_q[q] * (tri + box)

    # Twist-2 (box) contributions
    for q in ["u", "d", "s", "c", "b"]:
        c1 = C1_box.get(q, 0.0)
        c2 = C2_box.get(q, 0.0)
        A += (3.0 / 4.0) * (q2[q] + qbar2[q]) * (c1 + m_chi * c2)

    # Gluon contribution
    A += (2.0 / 27.0) * f_TG * CG_box

    sigma = (mu**2 / np.pi) * (m_target / v)**2 * A**2
    return sigma * GEV2_TO_CM2


def triangle_coefficient_SD(
    y_h_chi_i_chi_j: float,
    y_h_chi_j_chi_1: float,
    m_chi_j: float,
    m_chi_1: float,
    m_h: float = M_H,
) -> float:
    """
    Triangle diagram contribution to C_triangle (Eq. 31).

    One triangle diagram with chi_j running in the loop, mediated by h.
    Sum over j = 1, 2, 3 for the full coefficient.

    C_triangle^{(j)} = (1/(16 pi^2)) * y_{h chi_j chi_1}^2 * m_chi_j
                        * C_0(m_chi_1^2, m_chi_j^2, m_h^2) + ...

    Returns the contribution from one internal fermion chi_j.
    """
    from ..loop_functions.passarino_veltman import C0, C2

    m1_sq = m_chi_1**2
    mj_sq = m_chi_j**2
    mh_sq = m_h**2

    # Leading contribution from scalar form factor
    c0 = C0(m1_sq, mj_sq, mh_sq)
    c2 = C2(m1_sq, mj_sq, mh_sq)

    coeff = y_h_chi_i_chi_j * y_h_chi_j_chi_1 / (16 * np.pi**2)
    return coeff * (m_chi_j * c0 + 2 * m_chi_1 * c2)


def triangle_coefficient_2HDMa(
    lambda_phi_aa: float,
    g_phi_qq: float,
    m_phi: float,
    m_a: float,
    m_chi: float,
    y_chi: float,
) -> float:
    """
    Triangle diagram contribution for 2HDM+a (Eq. 38).

    The triangle has a pseudoscalar a loop connecting the DM line
    to a scalar phi (= h or H) mediator, which then couples to quarks.

    C_{q,triangle}^{(phi)} = (y_chi^2 / (16 pi^2)) * lambda_{phi aa}
                              * g_{phi qq} * m_q / (v * m_phi^2)
                              * [loop integral]
    """
    from ..loop_functions.passarino_veltman import C2, B1

    m_a_sq = m_a**2
    m_chi_sq = m_chi**2

    # The loop integral involves C2 and B1 functions
    c2 = C2(m_chi_sq, m_a_sq, m_a_sq)
    b1 = B1(0, m_a_sq, m_chi_sq)

    coeff = y_chi**2 / (16 * np.pi**2)
    return coeff * lambda_phi_aa * (2 * c2 - b1)
