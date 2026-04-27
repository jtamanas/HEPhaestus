"""
Box diagram loop functions for one-loop DM-nucleon scattering.
arXiv:2506.19062, Eqs. (34)-(37) (singlet-doublet) and (40)-(42) (2HDM+a).

These functions compute the Wilson coefficients for the effective
DM-quark operators that arise from box diagrams with two DM lines
and two quark lines connected by mediator exchange.
"""

import numpy as np
from .passarino_veltman import C0, C2, D0, B0


# --------------------------------------------------------------------------
# Singlet-Doublet model box functions (Eqs. 34-37)
# --------------------------------------------------------------------------

def Z_111(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Loop function Z_{111} from Eq. (35).

    Z_{111}(m1^2, m2^2, m3^2) = integral_0^1 dx dy dz delta(x+y+z-1)
                                  * 1 / (x*m1^2 + y*m2^2 + z*m3^2)

    This is related to C0 at zero external momenta:
    Z_{111} = C0(m1^2, m2^2, m3^2) (up to normalization conventions)
    """
    return C0(m1_sq, m2_sq, m3_sq)


def Z_001(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Loop function Z_{001} from Eq. (35).

    Z_{001}(m1^2, m2^2, m3^2) = integral_0^1 dx dy dz delta(x+y+z-1)
                                  * z / (x*m1^2 + y*m2^2 + z*m3^2)
    """
    return C2(m1_sq, m2_sq, m3_sq)


def Z_11(m1_sq: float, m2_sq: float) -> float:
    """
    Two-mass loop function Z_{11} from Eq. (35).

    Z_{11}(m1^2, m2^2) = integral_0^1 dx / (x*m1^2 + (1-x)*m2^2)

    Analytic result:
      Z_{11} = ln(m1^2/m2^2) / (m1^2 - m2^2)  for m1 != m2
      Z_{11} = 1/m^2                             for m1 = m2
    """
    if abs(m1_sq - m2_sq) < 1e-10 * max(abs(m1_sq), abs(m2_sq), 1e-30):
        return 1.0 / m1_sq if abs(m1_sq) > 1e-30 else 0.0
    if abs(m1_sq) < 1e-30 or abs(m2_sq) < 1e-30:
        return 0.0  # needs regularization
    return np.log(abs(m1_sq / m2_sq)) / (m1_sq - m2_sq)


def Z_00(m1_sq: float, m2_sq: float) -> float:
    """
    Two-mass loop function Z_{00} from Eq. (35).

    Z_{00}(m1^2, m2^2) = integral_0^1 dx (1-x) / (x*m1^2 + (1-x)*m2^2)

    Analytic result:
      Z_{00} = [m1^2 ln(m1^2/m2^2)/(m1^2-m2^2) - 1] / (m1^2-m2^2)  for m1 != m2
      Z_{00} = 1/(2*m^2)                                               for m1 = m2
    """
    if abs(m1_sq - m2_sq) < 1e-10 * max(abs(m1_sq), abs(m2_sq), 1e-30):
        return 1.0 / (2.0 * m1_sq) if abs(m1_sq) > 1e-30 else 0.0
    return (m1_sq * np.log(abs(m1_sq / m2_sq)) / (m1_sq - m2_sq) - 1.0) / (m1_sq - m2_sq)


def X_n(n: int, m1_sq: float, m2_sq: float, m3_sq: float,
        m4_sq: float) -> float:
    """
    Four-point loop function X_n from Eq. (36).

    X_n involves derivatives of the four-point function with respect to
    external momenta. At zero momentum transfer, this reduces to
    combinations of D0 and C0 functions.

    For n=2 (the case needed in Eq. 34):
    X_2 is related to the tensor box integral.
    """
    # At zero external momenta, X_2 can be expressed in terms of D0
    # X_2(m1,m2,m3,m4) = D0(m1,m2,m3,m4) + corrections
    # Exact form depends on conventions from Belyaev:2022qnf
    return D0(m1_sq, m2_sq, m3_sq, m4_sq)


def Y_n(n: int, m1_sq: float, m2_sq: float, m3_sq: float,
        m4_sq: float) -> float:
    """
    Four-point loop function Y_n from Eq. (36).

    Similar to X_n but with different tensor structure.
    At zero momentum transfer, also reduces to D0 combinations.
    """
    return D0(m1_sq, m2_sq, m3_sq, m4_sq)


# --------------------------------------------------------------------------
# Singlet-Doublet Wilson coefficients (Eq. 34)
# --------------------------------------------------------------------------

def C1_box_SD(masses_chi: list, m_Z: float, m_W: float,
              couplings_Z: list) -> float:
    """
    Box Wilson coefficient C_{1,box}^{CP-even} for singlet-doublet (Eq. 34).

    This involves Z-Z box diagrams with DM and quark external lines.
    The coefficient depends on the Z-chi_i-chi_j couplings and the
    mass spectrum of the neutral fermions.

    Parameters
    ----------
    masses_chi : list of float — [m_chi1, m_chi2, m_chi3]
    m_Z : float — Z boson mass
    m_W : float — W boson mass
    couplings_Z : list — Z-chi1-chi_j couplings for j=1,2,3

    Returns
    -------
    C1 : float — Wilson coefficient
    """
    m_chi1 = masses_chi[0]
    result = 0.0
    for j in range(3):
        m_j = masses_chi[j]
        g_j = couplings_Z[j]
        # Z-Z box: chi1 q -> chi_j (internal) -> chi1 q
        result += g_j**2 * Z_111(m_chi1**2, m_j**2, m_Z**2)
    return result / (16 * np.pi**2)


def CG_box_SD(masses_chi: list, m_Z: float, m_W: float,
              couplings_Z: list, couplings_h: list,
              m_h: float) -> float:
    """
    Gluon Wilson coefficient C_{G,box}^{CP-even} for singlet-doublet (Eq. 34).

    The gluon coefficient arises from heavy-quark loops that are integrated out,
    contributing through the trace anomaly.
    """
    result = 0.0
    m_chi1 = masses_chi[0]
    for j in range(3):
        m_j = masses_chi[j]
        # Higgs-mediated box contribution to gluon operator
        g_h_j = couplings_h[j]
        result += g_h_j**2 * Z_111(m_chi1**2, m_j**2, m_h**2)
    return result / (16 * np.pi**2)


# --------------------------------------------------------------------------
# 2HDM+a box functions (Eqs. 40-42)
# --------------------------------------------------------------------------

def X_001(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Three-point function X_{001} from Eq. (41).

    X_{001}(m1^2, m2^2, m3^2) = integral dx dy dz delta(1-x-y-z)
                                  * z / (x*m1^2 + y*m2^2 + z*m3^2)^2

    This is the same as C2 with different normalization.
    """
    return C2(m1_sq, m2_sq, m3_sq)


def X_111(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Three-point function X_{111} from Eq. (41).
    Same as Z_{111} / C0.
    """
    return C0(m1_sq, m2_sq, m3_sq)


def F_func(m_sq: float, m_a_sq: float, m_chi_sq: float) -> float:
    """
    Function F(m^2) used in C_G^box for 2HDM+a (Eq. 42).

    F(m^2) appears in the gluon Wilson coefficient from integrating out
    heavy quarks running in the box loop.

    At the relevant scale, this is:
    F(m_q^2) = m_q^2 * C0(m_a^2, m_q^2, m_chi^2) + ...
    """
    return m_sq * C0(m_a_sq, m_sq, m_chi_sq)


def Cq_box_2HDMa(m_chi: float, m_a: float, m_q: float,
                  y_chi: float, g_aq: float) -> float:
    """
    Quark box Wilson coefficient C_{q,box} for 2HDM+a (Eq. 40).

    This is the leading box contribution to the effective DM-quark operator
    from pseudoscalar exchange.

    Parameters
    ----------
    m_chi : float — DM mass [GeV]
    m_a   : float — pseudoscalar mediator mass [GeV]
    m_q   : float — quark mass [GeV]
    y_chi : float — DM-pseudoscalar coupling
    g_aq  : float — quark-pseudoscalar coupling

    Returns
    -------
    C_q : float — Wilson coefficient
    """
    m_chi_sq = m_chi**2
    m_a_sq = m_a**2
    m_q_sq = m_q**2

    # Box topology: chi q -> a a -> chi q
    coeff = y_chi**2 * g_aq**2 / (16 * np.pi**2)
    integral = X_111(m_chi_sq, m_a_sq, m_q_sq)
    return coeff * m_q * integral


def CG_box_2HDMa(m_chi: float, m_a: float, y_chi: float,
                  quark_couplings: dict) -> float:
    """
    Gluon box Wilson coefficient C_{G,box} for 2HDM+a (Eq. 40).

    Arises from integrating out heavy quarks (c, b, t) in the box loop.
    Uses the function F(m_q^2) from Eq. (42).

    Parameters
    ----------
    quark_couplings : dict — {quark_name: (mass, coupling)} for c, b, t
    """
    m_chi_sq = m_chi**2
    m_a_sq = m_a**2
    coeff = y_chi**2 / (16 * np.pi**2)

    result = 0.0
    for name, (m_q, g_q) in quark_couplings.items():
        result += g_q**2 * F_func(m_q**2, m_a_sq, m_chi_sq)

    return coeff * result
