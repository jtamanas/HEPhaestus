"""
Direct detection scaling identities for 2HDM+a σ_SI.
arXiv:2509.08043, Eqs. 36-40 (Tier-3 algebraic identities).

These helpers verify the power-law scaling of σ_SI (Eq. 50, G=1 limit) under
parameter rescaling. Both sides use sigma_SI_scaling (G=1 formula), so the ratios
are exact algebraic identities at Tier-3 level (Source C, tolerance 1e-8).

The expected_ratio is computed analytically from the sigma_SI_scaling formula
itself (not from leading-order approximations), ensuring ratio == expected_ratio
to floating-point precision. This is the plan's Source C intent.

Exact expected ratios from the sigma_SI_scaling formula (G=1):
    sigma ~ [A_loop]^2 * mu^2 * m_chi^2   (A_loop does NOT depend on m_chi alone)

    m_A:    A = (f*m_A)^2 - m_a^2)^2 / (m_A^2 - m_a^2)^2  [exact, not f^4]
    m_a:    A = (m_A^2 - (f*m_a)^2)^2 / (m_A^2 - m_a^2)^2  [exact]
    m_chi:  ratio = (mu_scaled/mu_base)^2 * factor^2         [exact; mu from A_loop * m_chi]
    theta:  ratio = (sin(2*f*t)/sin(2*t))^4                  [exact]
    g_chi:  ratio = factor^4                                  [exact, pure power law]
    sigma_q: ratio = factor^2                                 [exact, pure power law]
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import M_P, reduced_mass
from cross_sections.sigma_si_2hdma_scaling import sigma_SI_scaling


def scale_ratio_mA(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ (m_A² - m_a²)² scaling identity (exact, Source C).

    expected_ratio = [(factor*m_A)² - m_a²]² / [m_A² - m_a²]²
    Note: this is NOT exactly factor^4 because A_loop = (m_A² - m_a²)/...,
    not m_A^4 alone. The expected_ratio here is the exact algebraic value.

    Parameters
    ----------
    anchor : dict — anchor parameter point with keys m_chi, m_a, m_A, theta, g_chi, tan_beta
    factor : float — scaling factor for m_A

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': exact, 'axis': 'm_A', 'factor': factor}
    """
    m_A = anchor['m_A']
    m_a = anchor['m_a']
    s_base = sigma_SI_scaling(anchor['m_chi'], m_a, m_A,
                               anchor['theta'], anchor['g_chi'],
                               anchor.get('tan_beta', 1.0))
    s_scaled = sigma_SI_scaling(anchor['m_chi'], m_a, factor * m_A,
                                 anchor['theta'], anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0))
    # Exact expected ratio: sigma ~ A_loop^2 ~ (m_A^2 - m_a^2)^2
    numerator_sq   = ((factor * m_A)**2 - m_a**2)**2
    denominator_sq = (m_A**2 - m_a**2)**2
    expected = numerator_sq / denominator_sq
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': expected,
        'axis': 'm_A',
        'factor': factor,
    }


def scale_ratio_ma(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ (m_A² - m_a²)² / m_a⁴ scaling identity (exact, Source C).

    expected_ratio = [(m_A² - (f*m_a)²) / (f*m_a)²]² / [(m_A² - m_a²) / m_a²]²
    Exact algebraic value (not the leading-order factor^(-4) approximation).

    Parameters
    ----------
    anchor : dict — anchor parameters
    factor : float — scaling factor for m_a (use factor=0.5 for large increase)

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': exact, 'axis': 'm_a', 'factor': factor}
    """
    m_A = anchor['m_A']
    m_a = anchor['m_a']
    s_base = sigma_SI_scaling(anchor['m_chi'], m_a, m_A,
                               anchor['theta'], anchor['g_chi'],
                               anchor.get('tan_beta', 1.0))
    s_scaled = sigma_SI_scaling(anchor['m_chi'], factor * m_a, m_A,
                                 anchor['theta'], anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0))
    # Exact: sigma ~ [(m_A^2 - m_a^2) / m_a^2]^2
    # scaled: [(m_A^2 - (f*m_a)^2) / (f*m_a)^2]^2
    base_val   = (m_A**2 - m_a**2) / m_a**2
    scaled_val = (m_A**2 - (factor * m_a)**2) / (factor * m_a)**2
    expected   = (scaled_val / base_val)**2
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': expected,
        'axis': 'm_a',
        'factor': factor,
    }


def scale_ratio_mchi(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ μ² m_chi² scaling identity (exact, Source C).

    expected_ratio = (mu_scaled / mu_base)^2 * factor^2
    where mu = reduced_mass(m_chi, M_P). This is the exact algebraic value
    (not the approximation factor^2 which holds only for m_chi << M_P).

    Parameters
    ----------
    anchor : dict — anchor parameters
    factor : float — scaling factor for m_chi

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': exact, 'axis': 'm_chi', 'factor': factor}
    """
    m_chi = anchor['m_chi']
    s_base = sigma_SI_scaling(m_chi, anchor['m_a'], anchor['m_A'],
                               anchor['theta'], anchor['g_chi'],
                               anchor.get('tan_beta', 1.0))
    s_scaled = sigma_SI_scaling(factor * m_chi, anchor['m_a'], anchor['m_A'],
                                 anchor['theta'], anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0))
    # Exact: sigma ~ mu^2 * m_chi^2 (with G=1 and same A_loop since A_loop doesn't depend on m_chi)
    mu_base   = reduced_mass(m_chi, M_P)
    mu_scaled = reduced_mass(factor * m_chi, M_P)
    expected  = (mu_scaled / mu_base)**2 * factor**2
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': expected,
        'axis': 'm_chi',
        'factor': factor,
    }


def scale_ratio_theta(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ sin⁴(2θ) scaling identity.

    σ_SI(factor*θ) / σ_SI(θ) = [sin(2*factor*θ)/sin(2*θ)]⁴
    Leading order (small θ): ≈ factor⁴ = 16 at factor=2.

    Parameters
    ----------
    anchor : dict — anchor parameters
    factor : float — scaling factor for θ

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': (sin(2ft)/sin(2t))^4, 'axis': 'theta', 'factor': factor}
    """
    theta = anchor['theta']
    s_base = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                               theta, anchor['g_chi'],
                               anchor.get('tan_beta', 1.0))
    s_scaled = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                                 factor * theta, anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0))
    # Exact expected ratio from sin^4 scaling
    expected = (np.sin(2 * factor * theta) / np.sin(2 * theta))**4
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': expected,
        'axis': 'theta',
        'factor': factor,
    }


def scale_ratio_gchi(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ g_chi⁴ scaling identity.

    σ_SI(factor*g_chi) / σ_SI(g_chi) = factor⁴ = 16 at factor=2.

    Parameters
    ----------
    anchor : dict — anchor parameters
    factor : float — scaling factor for g_chi

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': factor**4, 'axis': 'g_chi', 'factor': factor}
    """
    s_base = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                               anchor['theta'], anchor['g_chi'],
                               anchor.get('tan_beta', 1.0))
    s_scaled = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                                 anchor['theta'], factor * anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0))
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': factor**4,
        'axis': 'g_chi',
        'factor': factor,
    }


def scale_ratio_sigmaq(anchor: dict, factor: float) -> dict:
    """Verify σ_SI ∝ σ_q² scaling identity.

    σ_SI(factor*σ_q) / σ_SI(σ_q) = factor² = 4 at factor=2.

    Parameters
    ----------
    anchor : dict — anchor parameters; must have 'sigma_mq' key
    factor : float — scaling factor for sigma_mq_qbarq

    Returns
    -------
    dict : {'ratio': computed, 'expected_ratio': factor**2, 'axis': 'sigma_q', 'factor': factor}
    """
    sigma_mq = anchor.get('sigma_mq', 0.330)
    s_base = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                               anchor['theta'], anchor['g_chi'],
                               anchor.get('tan_beta', 1.0),
                               sigma_mq_qbarq=sigma_mq)
    s_scaled = sigma_SI_scaling(anchor['m_chi'], anchor['m_a'], anchor['m_A'],
                                 anchor['theta'], anchor['g_chi'],
                                 anchor.get('tan_beta', 1.0),
                                 sigma_mq_qbarq=factor * sigma_mq)
    return {
        'ratio': s_scaled / s_base,
        'expected_ratio': factor**2,
        'axis': 'sigma_q',
        'factor': factor,
    }
