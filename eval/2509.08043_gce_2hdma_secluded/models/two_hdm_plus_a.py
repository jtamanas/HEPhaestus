"""
Two-Higgs-Doublet-Plus-Axion (2HDM+a) dark matter model.
arXiv:2509.08043, Eqs. 41-42, 47, 50.

The 2HDM+a model contains a Dirac DM fermion χ coupled to a pseudoscalar mediator a
(and the heavier pseudoscalar A) via a mixing angle θ. The DM-pseudoscalar couplings are:

    g_{χχa} = y_χ cos(θ)    (Eq. 41 — coupling to light pseudoscalar a)
    g_{χχA} = y_χ sin(θ)    (Eq. 41 — coupling to heavy pseudoscalar A)

Note: these satisfy g_{χa}² + g_{χA}² = y_χ², so y_χ is the overall coupling strength.

θ convention: Bauer-2017 mixing-angle convention; paper 2509.08043 uses same symbol.
θ in radians throughout.

A_loop is the amplitude factor (without the G loop function, which enters in sigma_SI_exact).
See sigma_si_2hdma_exact.py for the full σ_SI calculation (BL5 binding).
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def g_chi_a(y_chi: float, theta: float) -> float:
    """DM coupling to light pseudoscalar a: g_{χχa} = y_χ cos(θ).

    Eq. 41 of arXiv:2509.08043. θ in radians.

    Parameters
    ----------
    y_chi : float — overall DM Yukawa coupling
    theta : float — pseudoscalar mixing angle [rad]

    Returns
    -------
    float : g_{χχa} = y_χ cos(θ)
    """
    return y_chi * np.cos(theta)


def g_chi_A(y_chi: float, theta: float) -> float:
    """DM coupling to heavy pseudoscalar A: g_{χχA} = y_χ sin(θ).

    Eq. 41 of arXiv:2509.08043. θ in radians.

    Parameters
    ----------
    y_chi : float — overall DM Yukawa coupling
    theta : float — pseudoscalar mixing angle [rad]

    Returns
    -------
    float : g_{χχA} = y_χ sin(θ)
    """
    return y_chi * np.sin(theta)


def A_loop(
    m_chi: float,
    m_a: float,
    m_A: float,
    theta: float,
    g_chi: float,
    tan_beta: float,
    yukawa_type: str = 'II',
) -> complex:
    """Loop amplitude factor for the 2HDM+a triangle diagram (Eq. 47 of arXiv:2509.08043).

    IMPORTANT: This function does NOT include the loop function G(x, 0).
    G is applied separately in sigma_SI_exact (see cross_sections/sigma_si_2hdma_exact.py).
    This binding (BL5) ensures G enters exactly ONCE, squared, OUTSIDE A_loop.

    The amplitude factor A = (m_A² − m_a²) sin²(2θ) g_χ² / (64π² m_h² m_a²)
    encodes the coupling structure and heavy propagator suppression.
    The G loop function G(m_χ²/m_a², 0) enters in sigma_SI_exact.

    Parameters
    ----------
    m_chi : float — DM mass [GeV]
    m_a   : float — light pseudoscalar mass [GeV]
    m_A   : float — heavy pseudoscalar mass [GeV]
    theta : float — mixing angle [rad]
    g_chi : float — overall DM Yukawa coupling
    tan_beta : float — ratio of Higgs VEVs tan(β)
    yukawa_type : str — Yukawa type ('I', 'II', 'III', 'IV'), default 'II'

    Returns
    -------
    complex : amplitude factor A_loop (real at LO; complex type reserved for future width effects)

    Notes
    -----
    Return type is complex to leave room for future width effects.
    The G loop function is NOT included here (see sigma_si_2hdma_exact.py).
    """
    from constants import M_H
    sin2theta = np.sin(2.0 * theta)
    numerator = (m_A**2 - m_a**2) * sin2theta**2 * g_chi**2
    denominator = 64.0 * np.pi**2 * M_H**2 * m_a**2
    return complex(numerator / denominator, 0.0)
