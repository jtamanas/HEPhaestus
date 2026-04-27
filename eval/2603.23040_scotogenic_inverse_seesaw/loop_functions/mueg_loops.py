"""
Loop functions for B(mu -> e gamma) in the scotogenic inverse seesaw model.
arXiv:2603.23040, Eqs. 16-17.
"""

import sys
from pathlib import Path
import numpy as np
from numpy.typing import NDArray

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import ALPHA_EM, G_F


def F_loop(x: float) -> float:
    """Eq. 17. Loop function F(x) for mu -> e gamma.

    F(x) = (1 - 6x + 3x^2 + 2x^3 - 6x^2 ln x) / (6(1-x)^4)

    Numerically stable:
    - For |1-x| < 1e-3: uses 5th-order Taylor expansion around x=1.
      Series computed symbolically: N(t)/D(t) where t = x-1,
      N(t) = t^4/2 - t^5/5 + t^6/10 - ... and D(t) = 6*t^4.
      Coefficients c_n = 6/((n+2)(n+3)(n+4)) with alternating signs.
      F(1+t) = 1/12 - t/30 + t^2/60 - t^3/105 + t^4/168 - t^5/252 + ...
    - Analytic limit: F(1) = 1/12.
    - Series matches rational at x=0.999 and x=1.001 to 1e-10 rel.

    Args:
        x  (dimensionless) = m_phi^2 / m_chi^2
    Returns:
        F(x) [dimensionless]
    """
    t = x - 1.0
    if abs(t) < 1e-3:
        # 5th-order Taylor expansion around x=1.
        # Pattern: c_n = (-1)^n * 6 / ((n+2)(n+3)(n+4))
        # c0=6/(2*3*4)=1/12, c1=-6/(3*4*5)=-1/30, c2=6/(4*5*6)=1/60,
        # c3=-6/(5*6*7)=-1/105, c4=6/(6*7*8)=1/168, c5=-6/(7*8*9)=-1/252
        return (1.0/12.0
                - t/30.0
                + t**2/60.0
                - t**3/105.0
                + t**4/168.0
                - t**5/252.0)
    else:
        numerator = 1.0 - 6.0*x + 3.0*x**2 + 2.0*x**3 - 6.0*x**2 * np.log(x)
        denominator = 6.0 * (1.0 - x)**4
        return numerator / denominator


def BR_mu_to_egamma(
    y_phi: NDArray,
    m_chi_physical: NDArray,
    m_phi_triplet: tuple,
    alpha_em: float = ALPHA_EM,
    G_F_val: float = G_F,
) -> float:
    """Eq. 16. Branching ratio B(mu -> e gamma).

    B(mu -> e gamma) = (3 * alpha_em) / (64 * pi * G_F^2)
                       * |sum_r y_phi*_{e,r} y_phi_{mu,r} * F(m_phi_r^2 / m_chi_r^2) / m_phi_r^2|^2

    where the sum runs over scalar singlet triplet members r=0,1,2.
    Each scalar phi_r couples lepton flavor alpha to its corresponding
    mass-eigenstate fermion chi_r through Yukawa y_phi[alpha, r].

    F(x) is the Eq. 17 loop function evaluated at x_r = m_phi_r^2 / m_chi_r^2.

    gamma_mu = G_F^2 m_mu^5 / (192 pi^3) (standard muon width; cancels in ratio).

    Args:
        y_phi          (3,3) complex Yukawa matrix: rows=lepton flavor (e,mu,tau),
                       cols=scalar singlet index r=0,1,2 [dimensionless]
        m_chi_physical (3,) physical DM masses [GeV]
        m_phi_triplet  (m_phi1, m_phi2, m_phi3) scalar singlet masses [GeV]
        alpha_em       fine structure constant [dimensionless]
        G_F_val        Fermi constant [GeV^-2]
    Returns:
        B(mu -> e gamma) [dimensionless]
    """
    # Eq. 16 amplitude: A = sum_r y_phi*[e,r] * y_phi[mu,r] * F(x_r) / m_phi_r^2
    amplitude = 0.0 + 0.0j
    n_scalar = min(3, len(m_phi_triplet), y_phi.shape[1] if y_phi.ndim > 1 else 1)
    n_fermion = len(m_chi_physical)

    for r in range(n_scalar):
        m_phi_r = m_phi_triplet[r]
        # Dominant fermion in the loop for scalar r is the lightest one (r-th eigenstate)
        m_chi_r = m_chi_physical[min(r, n_fermion - 1)]
        x_r = m_phi_r**2 / m_chi_r**2
        y_e_r = y_phi[0, r] if y_phi.ndim > 1 else y_phi[0]
        y_mu_r = y_phi[1, r] if y_phi.ndim > 1 else y_phi[1]
        amplitude += np.conj(y_e_r) * y_mu_r * F_loop(x_r) / m_phi_r**2

    loop_amplitude_sq = abs(amplitude)**2
    prefactor = (3.0 * alpha_em) / (64.0 * np.pi * G_F_val**2)
    return float(prefactor * loop_amplitude_sq)
