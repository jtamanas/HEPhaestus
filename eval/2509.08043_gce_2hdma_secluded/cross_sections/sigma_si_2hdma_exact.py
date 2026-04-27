"""
Exact one-loop spin-independent DM-nucleon cross-section for 2HDM+a.
arXiv:2509.08043, Eqs. 47/50 (triangle diagram + full σ_SI).

Equation-numbering note: the plan's earlier label "Eq. 44" was incorrect.
Eq. 44 in the paper is the box-diagram contribution (loop function F, subleading).
The triangle diagram amplitude is Eq. 47; the resulting σ_SI is Eq. 50 (first line).
This module implements Eq. 47/50 (the primary Tier-2 target).

PRIMARY Tier-2 implementation. Uses the G(m_χ²/m_a², 0) loop function from triangle_G.py.

BL5 binding: G enters exactly ONCE, squared, OUTSIDE A_loop.
The structure is:
    A = A_loop(...)           [from models/two_hdm_plus_a.py, does NOT include G]
    x = m_chi² / m_a²
    g = G(x, 0.0)             [from loop_functions/triangle_G.py]
    sigma = prefactor * |A|² * g²
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_H, M_P, SIGMA_MQ_QBARQ, GEV2_TO_CM2, reduced_mass
from loop_functions.triangle_G import G
from models.two_hdm_plus_a import A_loop


def sigma_SI_exact(
    m_chi: float,
    m_a: float,
    m_A: float,
    theta: float,
    g_chi: float,
    tan_beta: float = 1.0,
    sigma_mq_qbarq: float = SIGMA_MQ_QBARQ,
    yukawa_type: str = "II",
) -> float:
    """Exact one-loop σ_SI for 2HDM+a (Eqs. 47/50 of arXiv:2509.08043).

    Equation-numbering note: Eq. 47 gives the triangle-diagram effective Lagrangian
    with loop function G(m_χ²/m_a², 0); Eq. 50 (first line) gives the resulting σ_SI.
    The plan's earlier label "Eq. 44" referred to a different equation in the paper
    (the box diagram using loop function F). This module implements the Eq. 47/50 route.

    Structure (BL5 binding — G applied ONCE, OUTSIDE A_loop):
        A = A_loop(m_chi, m_a, m_A, theta, g_chi, tan_beta, yukawa_type)
        x = m_chi² / m_a²
        g = G(x, 0.0)
        sigma_gev2 = prefactor(sigma_mq_qbarq, reduced_mass(m_chi, M_P)) * |A|² * g²
        return sigma_gev2 * GEV2_TO_CM2   [in cm²]

    Physical formula (from Eq. 47 effective Lagrangian + standard σ_SI):
        f_N = A_loop * G(x,0) * m_chi / V_H² * σ_{mq}        [dim: GeV⁻²]
        σ_SI = 4 μ²/π × f_N²     [dim: GeV⁻²]
        → convert to cm² via GEV2_TO_CM2

    where A_loop = (m_A² - m_a²) sin²(2θ) g_χ² / (64π² m_h² m_a²) [dim: GeV⁻²]

    Note on G(0,0)=1 convention: the paper states G(0,0)=1, so in the small-x (Taylor)
    limit σ_SI recovers the scaling formula Eq. 50.

    Parameters
    ----------
    m_chi         : float — DM mass [GeV]
    m_a           : float — light pseudoscalar mass [GeV]
    m_A           : float — heavy pseudoscalar mass [GeV]
    theta         : float — mixing angle [rad]
    g_chi         : float — overall DM Yukawa coupling
    tan_beta      : float — tan(β) (default 1.0)
    sigma_mq_qbarq: float — nucleon matrix element ⟨N|Σ m_q q̄q|N⟩ [GeV] (default 0.330)
    yukawa_type   : str   — Yukawa type (default 'II')

    Returns
    -------
    float : σ_SI in cm²
    """
    # Reduced mass
    mu = reduced_mass(m_chi, M_P)

    # A_loop amplitude factor (does NOT include G — BL5 binding)
    A = A_loop(m_chi, m_a, m_A, theta, g_chi, tan_beta, yukawa_type)

    # Loop argument and G function (enters ONCE, squared)
    x = m_chi**2 / m_a**2
    g = G(x, 0.0)

    # Coupling to nucleon: f_N = A * G * m_chi / V_H^2 * sigma_mq_qbarq [GeV^-2]
    f_N = abs(A) * g * m_chi / V_H**2 * sigma_mq_qbarq

    # σ_SI = 4 μ²/π * f_N² [GeV^-2]
    sigma_gev2 = 4.0 * mu**2 / np.pi * f_N**2

    return sigma_gev2 * GEV2_TO_CM2
