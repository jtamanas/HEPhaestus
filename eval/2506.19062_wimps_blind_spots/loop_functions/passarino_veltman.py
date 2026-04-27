"""
Passarino-Veltman scalar integrals for one-loop DM-nucleon scattering.
arXiv:2506.19062, Eqs. (31)-(32), (38)-(39).

These are the standard PV integrals in the zero-momentum-transfer limit
(q^2 -> 0), which is appropriate for non-relativistic DM-nucleon scattering.

Reference implementations should be cross-checked against LoopTools
(Hahn & Perez-Victoria 1999).
"""

import numpy as np
from functools import lru_cache


def B0(m1_sq: float, m2_sq: float, mu_sq: float = None) -> float:
    """
    Scalar two-point function B_0(0; m1^2, m2^2) at zero external momentum.

    B_0(0; m1^2, m2^2) = -ln(m1*m2/mu^2) + ... (UV divergent)

    In the DM-nucleon context, we only need finite combinations of B0's,
    so the divergence cancels. We return the finite part in MSbar with
    mu = sqrt(m1*m2) by default.

    For the cross-section formulas, only differences B0(m1,m2) - B0(m3,m4)
    appear, making the result scheme-independent.
    """
    if mu_sq is None:
        mu_sq = np.sqrt(abs(m1_sq * m2_sq)) if m1_sq * m2_sq > 0 else 1.0

    # At q^2 = 0:
    # B0(0; m1^2, m2^2) = 1 - ln(m2^2/mu^2) + m1^2/(m1^2 - m2^2) * ln(m2^2/m1^2)
    if abs(m1_sq - m2_sq) < 1e-10 * max(abs(m1_sq), abs(m2_sq), 1e-30):
        # Degenerate case
        if abs(m1_sq) < 1e-30:
            return 0.0
        return 1.0 - np.log(abs(m1_sq) / mu_sq)
    if abs(m1_sq) < 1e-30:
        return 1.0 - np.log(abs(m2_sq) / mu_sq)
    if abs(m2_sq) < 1e-30:
        return 1.0 - np.log(abs(m1_sq) / mu_sq)

    return (1.0 - np.log(abs(m2_sq) / mu_sq)
            + m1_sq / (m1_sq - m2_sq) * np.log(abs(m2_sq / m1_sq)))


def B1(p_sq: float, m1_sq: float, m2_sq: float) -> float:
    """
    Scalar two-point tensor integral B_1 (Eq. 39).

    B_1(p^2; m1^2, m2^2) = integral representation from Eq. (39).
    At p^2 = 0 (zero momentum transfer):

    B_1(0; m1^2, m2^2) = -1/2 * B0(m1^2, m2^2) + (m1^2 - m2^2)/(2*p^2) * [B0(m1^2,m2^2) - B0(m1^2,m1^2)]

    In the limit p^2 -> 0, we use the Feynman parameter representation:
    B_1(0; m1^2, m2^2) = integral_0^1 dx x / (x*m2^2 + (1-x)*m1^2 - x(1-x)*0)
    """
    # Numerical integration for general case
    from scipy.integrate import quad

    def integrand(x):
        denom = x * m2_sq + (1.0 - x) * m1_sq - x * (1.0 - x) * p_sq
        if abs(denom) < 1e-30:
            return 0.0
        return -x / denom

    result, _ = quad(integrand, 0, 1)
    return result


def C0(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Scalar three-point function C_0(0,0,0; m1^2, m2^2, m3^2) (Eq. 32).

    At zero external momenta:

    C_0 = integral_0^1 dx integral_0^{1-x} dy / [x*m1^2 + y*m2^2 + (1-x-y)*m3^2]^2

    This is the triangle integral that appears in the one-loop SI cross-section.
    """
    from scipy.integrate import dblquad

    def integrand(y, x):
        denom = x * m1_sq + y * m2_sq + (1.0 - x - y) * m3_sq
        if abs(denom) < 1e-30:
            return 0.0
        return 1.0 / denom**2

    result, _ = dblquad(integrand, 0, 1, 0, lambda x: 1.0 - x)
    return result


def C0_analytic(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Analytic form of C_0(0,0,0; m1^2, m2^2, m3^2) for distinct masses.

    C_0 = sum_i [ln(m_i^2) / product_{j!=i}(m_i^2 - m_j^2)]

    For degenerate masses, use limiting forms.
    """
    masses_sq = [m1_sq, m2_sq, m3_sq]

    # Check for degeneracies
    tol = 1e-6 * max(abs(m) for m in masses_sq if abs(m) > 0)

    # All three equal
    if (abs(m1_sq - m2_sq) < tol and abs(m2_sq - m3_sq) < tol):
        if abs(m1_sq) < 1e-30:
            return 0.0
        return 1.0 / (2.0 * m1_sq)

    # Two equal
    for i in range(3):
        j = (i + 1) % 3
        k = (i + 2) % 3
        if abs(masses_sq[j] - masses_sq[k]) < tol:
            m_a = masses_sq[i]
            m_b = masses_sq[j]
            if abs(m_a - m_b) < tol:
                return 1.0 / (2.0 * m_a) if abs(m_a) > 1e-30 else 0.0
            return (1.0 / (m_a - m_b)
                    * (m_a * np.log(m_a) - m_b * np.log(m_b)) / (m_a - m_b)
                    - 1.0 / (m_a - m_b)) if abs(m_a) > 1e-30 else 0.0

    # All distinct
    result = 0.0
    for i in range(3):
        if abs(masses_sq[i]) < 1e-30:
            continue
        prod = 1.0
        for j in range(3):
            if j != i:
                prod *= (masses_sq[i] - masses_sq[j])
        if abs(prod) > 1e-30:
            result += np.log(abs(masses_sq[i])) / prod
    return result


def C2(m1_sq: float, m2_sq: float, m3_sq: float) -> float:
    """
    Tensor three-point function C_2(0,0,0; m1^2, m2^2, m3^2) (Eq. 32).

    Related to C_0 by tensor reduction. At zero external momenta:

    C_2 = integral_0^1 dx integral_0^{1-x} dy * y / [x*m1^2 + y*m2^2 + (1-x-y)*m3^2]^2
    """
    from scipy.integrate import dblquad

    def integrand(y, x):
        denom = x * m1_sq + y * m2_sq + (1.0 - x - y) * m3_sq
        if abs(denom) < 1e-30:
            return 0.0
        return y / denom**2

    result, _ = dblquad(integrand, 0, 1, 0, lambda x: 1.0 - x)
    return result


def D0(m1_sq: float, m2_sq: float, m3_sq: float, m4_sq: float) -> float:
    """
    Scalar four-point function D_0(0,...,0; m1^2, m2^2, m3^2, m4^2).

    At zero external momenta, this is the box integral:

    D_0 = integral dx dy dz / [x*m1^2 + y*m2^2 + z*m3^2 + (1-x-y-z)*m4^2]^3
        * 2   (from the Feynman parametrization normalization)

    where 0 <= x, y, z, x+y+z <= 1.
    """
    from scipy.integrate import tplquad

    def integrand(z, y, x):
        denom = (x * m1_sq + y * m2_sq + z * m3_sq
                 + (1.0 - x - y - z) * m4_sq)
        if abs(denom) < 1e-30:
            return 0.0
        return 2.0 / denom**3

    result, _ = tplquad(
        integrand,
        0, 1,                          # x
        0, lambda x: 1.0 - x,          # y
        0, lambda x, y: 1.0 - x - y,   # z
    )
    return result
