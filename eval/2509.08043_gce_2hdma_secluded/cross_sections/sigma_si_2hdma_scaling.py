"""
Scaling approximation (G=1 limit) for σ_SI in the 2HDM+a model.
arXiv:2509.08043, Eq. 50 (second line — pure power-law scaling formula).

In the small-x limit (m_χ ≪ m_a), G(x,0) → G(0,0) = 1, and the exact formula
reduces to the scaling approximation:

    σ_SI ≈ 2.2×10⁻⁴⁹ cm² × (m_A/800)⁴ × (m_a/50)⁻⁴ × (m_χ/30)² × (θ/0.1)⁴ × (g_χ/0.5)⁴

where the anchor values (800, 50, 30, 0.1, 0.5) correspond to BP-A.

This module implements sigma_SI_scaling using G=1 (zeroth-order Taylor, G(0,0)=1),
making the formula a pure power law in all parameters. This is the G→1 approximation
from Eq. 50 second line, equivalent to the paper's scaling formula.

G=1 (not G_taylor = 1-x/3) is used so that the Tier-3 scaling identities
(T16-T21 in test_benchmarks.py) are exact algebraic identities to 1e-8 precision.
For G_taylor = 1-x/3 agreement with sigma_SI_exact in the small-x limit, see T25.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_H, M_P, SIGMA_MQ_QBARQ, GEV2_TO_CM2, reduced_mass
from models.two_hdm_plus_a import A_loop


def sigma_SI_scaling(
    m_chi: float,
    m_a: float,
    m_A: float,
    theta: float,
    g_chi: float,
    tan_beta: float = 1.0,
    sigma_mq_qbarq: float = SIGMA_MQ_QBARQ,
) -> float:
    """Scaling approximation for σ_SI with G=1 (Eq. 50 power-law of arXiv:2509.08043).

    Uses G=1.0 (the G(0,0)=1 limit, zeroth-order Taylor approximation).
    This is the paper's Eq. 50 second line: a pure power law in (m_A, m_a, m_chi, theta, g_chi).

    Valid in the limit x = m_χ²/m_a² → 0 (light DM or heavy pseudoscalar).
    Ratio sigma_SI_scaling / sigma_SI_exact → 1 as x → 0 (verified by T25 at x=1e-4).

    Note: Using G=1 (not G_taylor=1-x/3) ensures the Tier-3 power-law identities
    T16-T21 are exact to 1e-8 absolute tolerance.

    Parameters
    ----------
    m_chi         : float — DM mass [GeV]
    m_a           : float — light pseudoscalar mass [GeV]
    m_A           : float — heavy pseudoscalar mass [GeV]
    theta         : float — mixing angle [rad]
    g_chi         : float — overall DM Yukawa coupling
    tan_beta      : float — tan(β) (default 1.0)
    sigma_mq_qbarq: float — nucleon matrix element [GeV] (default 0.330)

    Returns
    -------
    float : σ_SI scaling approximation in cm² (pure power law, G=1)
    """
    # Reduced mass
    mu = reduced_mass(m_chi, M_P)

    # A_loop amplitude factor
    A = A_loop(m_chi, m_a, m_A, theta, g_chi, tan_beta)

    # G = 1.0 (zeroth-order Taylor, paper's G(0,0)=1 limit for Eq. 50 scaling formula)
    g = 1.0

    # Coupling to nucleon: f_N = A * G * m_chi / V_H^2 * sigma_mq [GeV^-2]
    f_N = abs(A) * g * m_chi / V_H**2 * sigma_mq_qbarq

    # σ_SI = 4 μ²/π * f_N² [GeV^-2]
    sigma_gev2 = 4.0 * mu**2 / np.pi * f_N**2

    return sigma_gev2 * GEV2_TO_CM2
