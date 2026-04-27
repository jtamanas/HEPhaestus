"""
Tree-level spin-independent DM-nucleon cross-section for the scalar portal singlet model.
arXiv:2601.13147, Eq. (31).

The cross-section involves exchange of h1 and h2 with blind-spot cancellation:

  sigma_SI = (mu^2 / pi) * (m_N/v)^2 * g_chi^2 * sin^2(theta) * cos^2(theta)
             * [(m_h2^2 - m_h1^2) / (m_h1^2 * m_h2^2)]^2
             * f_N^2 * GEV2_TO_CM2

where the blind-spot factor is written in the numerator-first form (S5):
  blind_spot = (m_h2^2 - m_h1^2) / (m_h1^2 * m_h2^2)

This gives bit-exact 0.0 when m_h1 == m_h2 (float subtraction of equal values).

Derivation:
  The amplitude A = sum_q (y_{chi chi h_k} * y_{qq h_k} / m_hk^2) sums over h1, h2:
    A = [g_chi * sin_theta * (m_q/v) * cos_theta] / m_h1^2
      + [g_chi * cos_theta * (-(m_q/v) * sin_theta)] / m_h2^2
    = g_chi * (m_q/v) * sin_theta * cos_theta * (1/m_h1^2 - 1/m_h2^2)
    = g_chi * (m_q/v) * sin_theta * cos_theta * (m_h2^2 - m_h1^2)/(m_h1^2 * m_h2^2)

  sigma = (mu^2/pi) * m_N^2 * (sum_q A * f_q)^2 * GEV2_TO_CM2
  where sum_q A * f_q = A * f_N (with f_N using (2/9)*f_TG form)
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_H, M_P, V_H, GEV2_TO_CM2, reduced_mass,
    F_U_P, F_D_P, F_S_P,
)
from models.scalar_portal_singlet import f_N_proton, f_N_neutron


def sigma_SI_scalar_portal(
    m_chi: float,
    g_chi: float,
    sin_theta: float,
    m_h1: float = M_H,
    m_h2: float = 200.0,
    m_target: float = M_P,
    v: float = V_H,
    f_u: float = F_U_P,
    f_d: float = F_D_P,
    f_s: float = F_S_P,
) -> float:
    """
    Tree-level spin-independent DM-nucleon cross-section (Eq. 31).

    Blind-spot factor uses the numerator-first form:
      blind_spot_factor = (m_h2^2 - m_h1^2) / (m_h1^2 * m_h2^2)
    so m_h1 == m_h2 gives bit-exact 0.0 (S5 requirement).

    Formula:
      sigma_SI = (mu^2 / pi) * (m_N/v)^2 * g_chi^2 * sin^2(theta) * cos^2(theta)
                 * blind_spot_factor^2 * f_N^2 * GEV2_TO_CM2

    where:
      mu = reduced_mass(m_chi, m_N) [GeV]
      f_N = f_u + f_d + f_s + (2/9)*(1 - f_u - f_d - f_s)  [(2/9)*f_TG convention]

    Parameters
    ----------
    m_chi    : float — DM mass [GeV]
    g_chi    : float — DM-singlet Yukawa coupling
    sin_theta: float — mixing angle sine
    m_h1     : float — lighter/SM-like Higgs mass [GeV] (default M_H = 125.25)
    m_h2     : float — heavier/singlet-like Higgs mass [GeV] (default 200.0)
    m_target : float — target nucleon mass [GeV] (default M_P = proton)
    v        : float — Higgs VEV [GeV] (default V_H = 246.22)
    f_u, f_d, f_s : float — nucleon scalar form factors (default proton values)

    Returns
    -------
    float : cross-section in cm^2 (bit-exact 0.0 at degeneracy m_h1 == m_h2)
    """
    mu = reduced_mass(m_chi, m_target)
    cos_theta_sq = 1.0 - sin_theta**2

    # Blind-spot factor: numerator-first form ensures bit-exact 0 at degeneracy
    blind_spot_factor = (m_h2**2 - m_h1**2) / (m_h1**2 * m_h2**2)

    # Nucleon form factor f_N (2/9 * f_TG convention)
    f_light = f_u + f_d + f_s
    f_N = f_light + (2.0 / 9.0) * (1.0 - f_light)

    # Cross-section
    sigma_gev2 = (
        (mu**2 / np.pi)
        * (m_target / v)**2
        * g_chi**2
        * sin_theta**2
        * cos_theta_sq
        * blind_spot_factor**2
        * f_N**2
    )
    return sigma_gev2 * GEV2_TO_CM2


def _reduce_eq31_to_single_higgs_limit(
    m_chi: float,
    g_chi: float,
    sin_theta: float,
    m_h1: float,
) -> float:
    """
    Helper demonstrating that Eq. 31 reduces to 2506.19062's sigma_SI_higgs_portal
    in the heavy second scalar limit m_h2 -> infinity (B-2 lock).

    Derivation (6-line algebraic derivation):
      1. Start with Eq. 31 blind-spot factor: (m_h2^2 - m_h1^2)/(m_h1^2 * m_h2^2)
      2. As m_h2 -> inf: = m_h2^2 / (m_h1^2 * m_h2^2) = 1 / m_h1^2
      3. So sigma_SI -> (mu^2/pi) * (m_N/v)^2 * g_chi^2 * sin^2*cos^2 / m_h1^4 * f_N^2
      4. This is sigma_SI_higgs_portal(m_chi, y_h_eff, m_h=m_h1)
         with y_h_eff = g_chi * sin_theta * sqrt(1 - sin_theta^2)  [B-2 LOCKED FORM]
      5. Because sigma_SI_higgs_portal = (mu^2/pi)*(m_N/v)^2 * y_h_eff^2 / m_h1^4 * f_N^2
      6. Substituting: y_h_eff^2 = g_chi^2 * sin^2 * cos^2 -- QED.

    y_h_eff formula is LOCKED to: g_chi * sin_theta * sqrt(1 - sin_theta^2)
    This is derived from the amplitude structure, not a free parameter.

    Parameters
    ----------
    m_chi     : float — DM mass [GeV]
    g_chi     : float — DM-singlet Yukawa coupling
    sin_theta : float — mixing angle sine
    m_h1      : float — lighter Higgs mass [GeV]

    Returns
    -------
    float : sigma_SI in cm^2 in the single-Higgs limit
    """
    # B-2 LOCKED: y_h_eff = g_chi * sin_theta * sqrt(1 - sin_theta^2)
    y_h_eff = g_chi * sin_theta * np.sqrt(1.0 - sin_theta**2)

    mu = reduced_mass(m_chi, M_P)
    f_N = f_N_proton()

    sigma_gev2 = (
        (mu**2 / np.pi)
        * (M_P / V_H)**2
        * y_h_eff**2
        / m_h1**4
        * f_N**2
    )
    return sigma_gev2 * GEV2_TO_CM2


if __name__ == "__main__":
    # Smoke tests
    import numpy as np

    # Test bit-exact zero at degeneracy (S5)
    sigma_degen = sigma_SI_scalar_portal(222.0, 0.57, 0.001, 125.25, 125.25)
    assert sigma_degen == 0.0, f"Degeneracy test failed: {sigma_degen}"
    print(f"sigma_SI at degeneracy = {sigma_degen} (exact 0.0) OK")

    # Test BP1 value (should be near 6.17e-50)
    sigma_bp1 = sigma_SI_scalar_portal(222.0, 0.57, 0.001, 125.25, 200.0)
    print(f"sigma_SI at BP1 = {sigma_bp1:.3e}")
    assert abs(sigma_bp1 / 6.17e-50 - 1.0) < 0.01, f"BP1 value off: {sigma_bp1:.3e} vs 6.17e-50"
    print(f"sigma_SI within 1% of 6.17e-50 OK")

    # Test heavy m_h2 reduction (B-2 consistency)
    sigma_heavy = sigma_SI_scalar_portal(222.0, 0.57, 0.001, 125.25, 1.0e6)
    sigma_single = _reduce_eq31_to_single_higgs_limit(222.0, 0.57, 0.001, 125.25)
    ratio = sigma_heavy / sigma_single
    assert abs(ratio - 1.0) < 1e-6, f"Heavy limit reduction off: ratio = {ratio:.10f}"
    print(f"Heavy m_h2 limit matches single-Higgs to {abs(ratio-1):.2e} (within 1e-6) OK")

    print("All si_tree_level self-tests passed.")
