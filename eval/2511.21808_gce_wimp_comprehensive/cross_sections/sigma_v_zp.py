"""
Thermally averaged DM annihilation cross section via Z' mediator.
arXiv:2511.21808, Eqs. 25, 38 (plan v1 numbering).

Convention: <σv> Taylor expansion truncated at s+p wave (Gondolo-Gelmini
1991 standard). Off-resonance this agrees with the full GG integral to O(v^4).
Near resonance (|s - m_Zp^2| < m_Zp * Γ_Zp), the BW-augmented formula is
used; truncation order does not apply there.

Truncation order: s-wave + p-wave only (a + b*x^{-1} in the non-relativistic
expansion, standard Gondolo-Gelmini result at O(x^{-1})). Higher-order
corrections (O(v^4)) not included.

Module-level function `thermal_average_gg` provides a second route via
scipy Bessel-function integration (Gondolo-Gelmini 1991 formula). This
function is a convention spot-check only — both routes share the same
|M|^2, so their agreement does not validate the matrix element; it only
checks the thermal-average integral convention (K_1/K_2 Bessel indices,
x_fo choice). For independent |M|^2 validation, see the MadGraph
cross-check (Plan C: deferred to future work).
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import GEV2_TO_CM2
from cross_sections.z_prime_decays import (
    gamma_zprime_total,
    gamma_zprime_to_ff,
    gamma_zprime_to_nu,
)
from models.charges import QUARK_FLAVORS, LEPTON_FLAVORS, NEUTRINO_FLAVORS


def _sigma_v_channel_s_wave(mediator, flavor: str, *, dm_type: str) -> float:
    """
    s-wave coefficient `a` for χχ̄ → ff̄ via Z' exchange.

    a = (N_c Q_V^2 g_chi^2 g_Zp^2) / (4π) × m_DM^2 / ((4m_DM^2 - m_Zp^2)^2 + m_Zp^2 Γ^2)
        × 2 (if β_f > 0 kinematic factor ~ 1 near threshold for heavy DM)

    Simplified non-relativistic limit (m_DM >> m_f, s-wave):
      a ≈ N_c g_chi^2 Q_V[f]^2 g_Zp^2 m_DM^2 / (π D_BW)

    Returns float in GeV^-2.
    """
    from models.charges import QUARK_FLAVORS as QF
    g_V, g_A = mediator.coupling_to_fermion(flavor)
    # s-wave for vector coupling: a ∝ g_V^2 (β_f factor → 1 when m_f << m_DM)
    N_c = 3 if flavor in QF else 1
    m_DM = mediator.m_DM
    m_Zp = mediator.m_Zp
    Gamma = gamma_zprime_total(mediator, dm_type=dm_type)
    s0 = 4.0 * m_DM**2
    D_BW = (s0 - m_Zp**2)**2 + (m_Zp * Gamma)**2
    # s-wave coefficient (leading in v^2 expansion)
    a = N_c * g_V**2 * mediator.g_chi**2 * m_DM**2 / (math.pi * D_BW)
    return a


def sigma_v_zprime(mediator, *, dm_type: str, final_state: str = "sum") -> float:
    """
    Thermally averaged annihilation <σv> for χχ̄ → SM via Z' exchange.
    arXiv:2511.21808, Eqs. 25 (plan-38, BW) and 13-14 (plan, |M|^2 structure).

    Implements the s-wave + p-wave Taylor expansion:
      <σv> = a + b * <v^2>

    At freeze-out, <v^2> ≈ 6/x_fo ≈ 6 * T_fo / m_DM ≈ 0.24 (x_fo ~ 25).
    For relic density and GCE comparison, <σv> is evaluated at v → 0
    (indirect detection limit), so <σv>_ID ≈ a (s-wave dominates for
    vector coupling).

    Near resonance (4m_DM^2 ≈ m_Zp^2), the BW denominator is enhanced.
    The formula is identical — the BW denominator D_BW naturally captures
    the resonance enhancement.

    Truncation: s-wave term only (a) for the default v→0 evaluation.
    The p-wave (b) is suppressed by v^2 ≈ 0 in the indirect-detection limit.

    Channels summed:
      - χχ̄ → qq̄ (all quarks with non-zero coupling)
      - χχ̄ → ll̄ (charged leptons with non-zero coupling)
      - χχ̄ → νν̄ (neutrinos with non-zero coupling)

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        "Dirac" or "Majorana". Mandatory kwarg.
    final_state : str
        Channel selector. "sum" (default) sums all channels.
        Can also specify a single flavor, e.g. "mu", "b".

    Returns
    -------
    float : <σv> in cm^3/s.
    """
    m_DM = mediator.m_DM
    m_Zp = mediator.m_Zp
    Gamma = gamma_zprime_total(mediator, dm_type=dm_type)

    s0 = 4.0 * m_DM**2
    D_BW = (s0 - m_Zp**2)**2 + (m_Zp * Gamma)**2

    total_a = 0.0  # s-wave coefficient [GeV^-2]

    if final_state == "sum":
        channels_to_sum = list(QUARK_FLAVORS) + list(LEPTON_FLAVORS)
    else:
        channels_to_sum = [final_state]

    for flavor in channels_to_sum:
        if flavor not in QUARK_FLAVORS and flavor not in LEPTON_FLAVORS:
            continue
        g_V, g_A = mediator.coupling_to_fermion(flavor)
        from models.charges import QUARK_FLAVORS as QF
        N_c = 3 if flavor in QF else 1
        # s-wave coefficient per channel (v→0 limit, m_f → 0 approximation)
        a_ch = N_c * g_V**2 * mediator.g_chi**2 * m_DM**2 / (math.pi * D_BW)
        total_a += a_ch

    # Neutrino channels (massless)
    for nu_f in NEUTRINO_FLAVORS:
        Q_nu = mediator.charges.Q_V[nu_f]
        if Q_nu == 0.0:
            continue
        g_nu_V = mediator.g_Zp * Q_nu
        # N_c = 1 for leptons; s-wave coefficient
        a_nu = g_nu_V**2 * mediator.g_chi**2 * m_DM**2 / (math.pi * D_BW)
        total_a += a_nu

    # Majorana DM has additional 1/2 from identical-particle averaging
    if dm_type == "Majorana":
        total_a *= 0.5

    # Convert GeV^-2 to cm^3/s (natural units: <σv> has units [GeV^-2] * c)
    sigma_v_cm3s = total_a * GEV2_TO_CM2

    return sigma_v_cm3s


def thermal_average_gg(mediator, x_fo: float, *, dm_type: str) -> float:
    """
    Gondolo-Gelmini thermal average of σv via scipy Bessel-function integral.
    arXiv:2511.21808 supplementary route; Gondolo & Gelmini (1991).

    This is a CONVENTION SPOT-CHECK ONLY. Both this function and
    sigma_v_zprime() share the same |M|^2 (the BW s-wave coefficient).
    Their agreement therefore does NOT validate the underlying matrix
    element — it only verifies the thermal-average integral convention
    (K_1/K_2 Bessel indices, x_fo choice).

    Formula (GG 1991):
      <σv> = (x_fo / 8 m_DM^5 K_2^2(x_fo)) ∫ σ̂(s) (s - 4m_DM^2) √s K_1(x_fo √s / m_DM) ds

    where σ̂(s) = s-channel Z' cross section (sum over final states).

    Parameters
    ----------
    mediator : ZPrimeMediator
    x_fo : float
        Inverse freeze-out temperature x_fo = m_DM / T_fo (typically ~25).
    dm_type : str
        Mandatory kwarg.

    Returns
    -------
    float : <σv> in cm^3/s.
    """
    # scipy import local to function (plan §7 spec)
    from scipy.special import kv as scipy_kv
    import numpy as np

    m_DM = mediator.m_DM
    m_Zp = mediator.m_Zp
    Gamma = gamma_zprime_total(mediator, dm_type=dm_type)

    # s-channel 2->2 cross section sigma(s) [GeV^-2]
    # For s-wave: sigma(s) = a(m_DM) / beta_DM where beta_DM = sqrt(1 - 4m^2/s)
    # This is the correct Mandelstam-s-dependent cross section (NR limit, m_f=0).
    def integrand(s_val):
        if s_val <= 4.0 * m_DM**2:
            return 0.0
        D_BW = (s_val - m_Zp**2)**2 + (m_Zp * Gamma)**2
        beta_DM = math.sqrt(1.0 - 4.0 * m_DM**2 / s_val)
        if beta_DM == 0.0:
            return 0.0

        # sigma(s) = Σ_f N_c g_chi^2 g_V[f]^2 m_DM^2 / (pi D_BW beta_DM)
        sigma_s = 0.0
        for flavor in list(QUARK_FLAVORS) + list(LEPTON_FLAVORS):
            g_V, _ = mediator.coupling_to_fermion(flavor)
            from models.charges import QUARK_FLAVORS as QF
            N_c = 3 if flavor in QF else 1
            sigma_s += N_c * g_V**2 * mediator.g_chi**2 * m_DM**2 / (math.pi * D_BW * beta_DM)
        # Neutrinos
        for nu_f in NEUTRINO_FLAVORS:
            Q_nu = mediator.charges.Q_V[nu_f]
            if Q_nu == 0.0:
                continue
            g_nu_V = mediator.g_Zp * Q_nu
            sigma_s += g_nu_V**2 * mediator.g_chi**2 * m_DM**2 / (math.pi * D_BW * beta_DM)
        if dm_type == "Majorana":
            sigma_s *= 0.5
        # GG integrand: σ(s) * (s - 4 m_DM^2) * sqrt(s) * K_1(x_fo * sqrt(s) / m_DM)
        sqrt_s = math.sqrt(s_val)
        K1_arg = x_fo * sqrt_s / m_DM
        K1_val = float(scipy_kv(1, K1_arg))
        return sigma_s * (s_val - 4.0 * m_DM**2) * sqrt_s * K1_val

    # K_2(x_fo) for normalization
    K2_xfo = float(scipy_kv(2, x_fo))

    # Numerical integration from s_min = 4 m_DM^2 to s_max (upper limit cutoff)
    from scipy.integrate import quad
    s_min = 4.0 * m_DM**2
    s_max = (10.0 * m_DM)**2  # generous upper cutoff

    integral_val, _ = quad(integrand, s_min, s_max, limit=200)

    # GG formula prefactor: x_fo / (8 m_DM^5 K_2^2(x_fo))
    prefactor = x_fo / (8.0 * m_DM**5 * K2_xfo**2)

    sigma_v_gev2 = prefactor * integral_val

    return sigma_v_gev2 * GEV2_TO_CM2
