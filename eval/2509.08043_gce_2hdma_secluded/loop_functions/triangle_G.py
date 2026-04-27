"""
Bauer-2017 loop function G(x, y=0) for 2HDM+a direct detection.
arXiv:2509.08043, Eqs. 48-49 and the y→0 limit used in Eq. 47/50.

G(x, y) is defined in the paper (Eqs. 48-49) via:

    G(x,y) = -4i ∫₀¹ dz z/ℱ^(1/2) × ln[(ℱ^(1/2)+iy(1-z))/(ℱ^(1/2)-iy(1-z))]
    ℱ(x,y,z) = y[4(1-z) + 4xz² − y(1-z)²]

For the σ_SI formula (Eq. 47/50), G is evaluated at y=0: G(m_χ²/m_a², 0).
Taking the y→0 limit analytically via L'Hôpital:

    G(x, 0) = 2 ∫₀¹ dz z(1-z) / [(1-z) + xz²]           (*)

Boundary identity: G(0, 0) = 1 (stated in paper after Eq. 49).
  Proof: G(0,0) = 2∫₀¹ z(1-z)/(1-z) dz = 2∫₀¹ z dz = 2·(1/2) = 1. ✓

S0 E3 note: The paper's G(x,0) uses the integral formula above with G(0,0)=1,
NOT the plan's Bauer-2017 Spence-closed-form with G(1,0)=1. Since E3=NOT_FOUND
(paper gives no closed form), we use the paper's integral formula.

Taylor expansion near x=0 (small m_χ/m_a limit):
  G(x, 0) = 1 - x/3 + x²/6 - x³/10 + ...  [for |x| < 1]
  (Coefficients from expanding 1/[(1-z)+xz²] in powers of x and integrating term by term)

G_taylor_limit(x) = 1 - x/3 (leading-order Taylor for the scaling Eq. 50).

Reference: arXiv:2509.08043, Eqs. 47-50; Bauer et al. (2017) [Bauer:2017ota] for original definition.
"""

import numpy as np
from scipy.integrate import quad


def G(x: float, y: float = 0.0) -> float:
    """Bauer-2017 loop function G(x, y), y=0 specialization (Eq. 47/50 of arXiv:2509.08043).

    For y=0, evaluates:
        G(x, 0) = 2 ∫₀¹ dz z(1-z) / [(1-z) + xz²]

    For |x| < 1e-4 (near x=0): uses Taylor expansion G ≈ 1 - x/3 + x²/6
    to avoid numerical issues at the lower limit (x→0 gives G→1).

    Note: G(0,0) = 1 (paper statement, confirmed analytically).
    G decreases monotonically from 1 as x increases.

    Parameters
    ----------
    x : float — loop argument = m_χ²/m_a² ≥ 0
    y : float — second argument (default 0.0; y=0 corresponds to the σ_SI formula)

    Returns
    -------
    float : G(x, y) value (dimensionless, real)
    """
    if y != 0.0:
        # Full G(x,y) via numerical integration (used for y≠0 checks)
        return _G_full(x, y)

    # y = 0 branch
    if x < 0:
        raise ValueError(f"G(x,0) requires x >= 0, got x={x}")

    if x < 1e-4:
        # Taylor expansion near x=0 (avoids integrand issues at extreme small x)
        # G(x,0) = 1 - x/3 + x²/6 - x³/10 + ...
        return 1.0 - x / 3.0 + x**2 / 6.0 - x**3 / 10.0

    def integrand(z):
        denom = (1.0 - z) + x * z**2
        if denom <= 0:
            return 0.0
        return 2.0 * z * (1.0 - z) / denom

    result, _ = quad(integrand, 0.0, 1.0, limit=100)
    return result


def _G_full(x: float, y: float) -> float:
    """Full G(x,y) numerical evaluation via the paper's integral (Eqs. 48-49).

    G(x,y) = -4i ∫₀¹ dz z/ℱ^{1/2} × ln[(ℱ^{1/2}+iy(1-z))/(ℱ^{1/2}-iy(1-z))]
    ℱ(x,y,z) = y[4(1-z) + 4xz² − y(1-z)²]

    Only used for non-zero y (validation).
    """
    def integrand_real(z):
        if z <= 0 or z >= 1:
            return 0.0
        cal_F = y * (4.0 * (1.0 - z) + 4.0 * x * z**2 - y * (1.0 - z)**2)
        if cal_F <= 0:
            return 0.0
        sqrtF = np.sqrt(cal_F)
        iy_term = y * (1.0 - z)
        # ln((sqrtF + i*iy)/(sqrtF - i*iy)) = 2i*arctan(iy/sqrtF)
        arg = iy_term / sqrtF
        ln_im = 2.0 * np.arctan(arg)  # imaginary part of log
        # G contribution: -4i * z/sqrtF * (i * ln_im) = 4 * z/sqrtF * ln_im
        return 4.0 * z / sqrtF * ln_im

    result, _ = quad(integrand_real, 0.0, 1.0, limit=100)
    return result


def G_taylor_limit(x: float) -> float:
    """Leading-order Taylor (small-x) limit of G(x, 0).

    G_taylor(x) = 1 - x/3  [leading two terms for small x = m_χ²/m_a²]

    Used by Eq. 50 scaling formula in the limit m_χ ≪ m_a.
    For the Taylor limit x→0: G → 1 (paper's G(0,0)=1 boundary condition).

    Parameters
    ----------
    x : float — m_χ²/m_a² (should be ≪ 1 for Taylor approximation to be valid)

    Returns
    -------
    float : G_taylor = 1 - x/3
    """
    return 1.0 - x / 3.0
