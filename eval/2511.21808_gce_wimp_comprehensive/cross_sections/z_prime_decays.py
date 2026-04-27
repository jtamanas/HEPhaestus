"""
Z' mediator partial and total decay widths.
arXiv:2511.21808, Eqs. 27, 28, 29 (plan v1 numbering).

Physics:
  Γ(Z' → f f̄) = N_c Q_f² g_Zp² m_Zp / (12π) × (1 + 2m_f²/m_Zp²) β_f
  Γ(Z' → χ χ̄) = g_χ² m_Zp / (12π) × (1 + 2m_χ²/m_Zp²) β_χ    [Dirac]
               = g_χ² m_Zp / (24π) × (1 - 4m_χ²/m_Zp²)^{3/2}   [Majorana]
  Γ(Z' → ν ν̄) = Q_ν² g_Zp² m_Zp / (24π) × N_ν             [massless ν]

where β_f = sqrt(1 - 4m_f²/m_Zp²) is the relativistic velocity factor.

Notes on dm_type:
  - dm_type is mandatory on all public functions (guardrail).
  - For gamma_zprime_to_ff and gamma_zprime_to_nu, dm_type is unused but
    required for uniform call-site safety.
  - For gamma_zprime_to_DM, dm_type determines the Majorana/Dirac factor.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_U_POLE, M_D_POLE, M_S_POLE, M_C_POLE, M_B_POLE, M_T_POLE,
    M_E, M_MU, M_TAU,
)

# Quark color factor
N_C_QUARK = 3
N_C_LEPTON = 1

# Fermion masses by flavor (pole masses for kinematic thresholds)
_FERMION_MASS = {
    "u": M_U_POLE, "d": M_D_POLE, "c": M_C_POLE,
    "s": M_S_POLE, "b": M_B_POLE, "t": M_T_POLE,
    "e": M_E, "mu": M_MU, "tau": M_TAU,
}

_QUARK_FLAVORS = frozenset({"u", "d", "c", "s", "b", "t"})
_LEPTON_FLAVORS = frozenset({"e", "mu", "tau"})
_CHARGED_FERMIONS = frozenset(_QUARK_FLAVORS | _LEPTON_FLAVORS)


def gamma_zprime_to_ff(mediator, flavor: str, *, dm_type: str) -> float:
    """
    Partial width Γ(Z' → f f̄) for one charged SM fermion flavor.
    arXiv:2511.21808, Eq. 27 (plan v1 numbering).

    Formula:
      Γ = N_c Q_V[f]² g_Zp² m_Zp / (12π) × (1 + 2m_f²/m_Zp²) β_f

    where β_f = sqrt(1 - 4m_f²/m_Zp²) and N_c=3 (quarks), 1 (leptons).

    Parameters
    ----------
    mediator : ZPrimeMediator
    flavor : str
        SM fermion flavor key (e.g. "mu", "b", "u").
    dm_type : str
        Mandatory kwarg (guardrail); unused for this decay channel.

    Returns
    -------
    float : partial width [GeV]. Zero if kinematically forbidden (m_Zp < 2m_f).
    """
    _ = dm_type  # required kwarg, unused here

    if flavor not in _CHARGED_FERMIONS:
        raise ValueError(f"flavor '{flavor}' not in charged SM fermions")

    g_V, g_A = mediator.coupling_to_fermion(flavor)
    # For pure vector coupling (Q_A=0 for all portals in this paper), g_A=0.
    # Width formula for vector current:
    #   Γ = N_c/(12π) * m_Zp * g_V² * (1 + 2m_f²/m_Zp²) * β_f
    # (The g_A contribution would be Γ_A = N_c/(12π) * m_Zp * g_A² * (1 - 4m_f²/m_Zp²)^{3/2})

    m_f = _FERMION_MASS[flavor]
    m_Zp = mediator.m_Zp

    # Kinematic check
    if m_Zp < 2.0 * m_f:
        return 0.0

    beta_f = math.sqrt(1.0 - 4.0 * m_f**2 / m_Zp**2)
    N_c = N_C_QUARK if flavor in _QUARK_FLAVORS else N_C_LEPTON

    # Vector coupling contribution
    width_V = (N_c * g_V**2 * m_Zp / (12.0 * math.pi)
               * (1.0 + 2.0 * m_f**2 / m_Zp**2) * beta_f)

    # Axial coupling contribution (g_A = 0 in this paper, but computed for correctness)
    width_A = (N_c * g_A**2 * m_Zp / (12.0 * math.pi)
               * (1.0 - 4.0 * m_f**2 / m_Zp**2)**(3.0/2.0))

    return width_V + width_A


def gamma_zprime_to_nu(mediator, *, dm_type: str) -> float:
    """
    Total partial width Γ(Z' → ν ν̄) summed over all active + sterile neutrino species.
    arXiv:2511.21808, Eq. 29 (plan v1 numbering).

    Formula (massless neutrinos):
      Γ = Q_ν² g_Zp² m_Zp / (24π) × N_nu_total

    where N_nu_total = N_nu_active + N_nu_sterile.
    For Lᵢ-Lⱼ portals, two neutrino species have ±1 charges (one +1, one -1),
    so we sum Q_ν[ν_i]² over species with non-zero charge.

    For B-L: Q_ν = -1 for all 3 active ν; sterile ν also have Q_{B-L} = -1.

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        Mandatory kwarg (guardrail); unused for this decay channel.

    Returns
    -------
    float : total neutrino partial width [GeV].
    """
    _ = dm_type  # required kwarg, unused here

    m_Zp = mediator.m_Zp

    # Active neutrinos — sum over those with non-zero charge
    nu_flavors = ("nu_e", "nu_mu", "nu_tau")
    width_active = 0.0
    for nu_f in nu_flavors:
        Q_nu = mediator.charges.Q_V[nu_f]
        if Q_nu == 0.0:
            continue
        g_nu = mediator.g_Zp * Q_nu
        # Massless neutrino: (1 + 2m²/m_Z'²) β → 1, β → 1
        width_active += g_nu**2 * m_Zp / (24.0 * math.pi)

    # Sterile neutrinos (B-L case): all have Q_{B-L} = -1
    # Coupling = g_Zp * (-1) → |g|² = g_Zp²
    n_sterile = mediator.charges.N_nu_sterile
    if n_sterile > 0:
        # Sterile neutrinos for B-L: charge = -1
        # For other portals, N_nu_sterile=0 so this loop doesn't run.
        g_sterile = mediator.g_Zp * (-1.0)  # Q_{B-L}(RH ν) = -1
        width_sterile = n_sterile * g_sterile**2 * m_Zp / (24.0 * math.pi)
    else:
        width_sterile = 0.0

    return width_active + width_sterile


def gamma_zprime_to_DM(mediator, *, dm_type: str) -> float:
    """
    Partial width Γ(Z' → χ χ̄) for DM pair.
    arXiv:2511.21808, Eq. 28 (plan v1 numbering).

    Dirac DM:
      Γ = g_χ² m_Zp / (12π) × (1 + 2m_χ²/m_Zp²) × β_χ

    Majorana DM:
      Γ = g_χ² m_Zp / (24π) × (1 - 4m_χ²/m_Zp²)^{3/2}
      (axial-only coupling; factor 1/2 for identical particles)

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        "Dirac" or "Majorana". Materially affects the result.

    Returns
    -------
    float : partial width [GeV]. Zero if kinematically forbidden (m_Zp < 2*m_DM).
    """
    m_DM = mediator.m_DM
    m_Zp = mediator.m_Zp
    g_chi = mediator.g_chi

    if m_Zp < 2.0 * m_DM:
        return 0.0

    beta_chi = math.sqrt(1.0 - 4.0 * m_DM**2 / m_Zp**2)

    if dm_type == "Dirac":
        # Vector coupling to Dirac DM: same formula as fermion (N_c=1)
        width = (g_chi**2 * m_Zp / (12.0 * math.pi)
                 * (1.0 + 2.0 * m_DM**2 / m_Zp**2) * beta_chi)
    elif dm_type == "Majorana":
        # Axial coupling to Majorana DM (self-conjugate): 1/2 factor
        width = (g_chi**2 * m_Zp / (24.0 * math.pi)
                 * (1.0 - 4.0 * m_DM**2 / m_Zp**2)**(3.0/2.0))
    else:
        raise ValueError(f"dm_type must be 'Dirac' or 'Majorana', got '{dm_type}'")

    return width


def gamma_zprime_total(mediator, *, dm_type: str) -> float:
    """
    Total Z' decay width summed over all kinematically allowed channels.
    arXiv:2511.21808 (identity: Γ_total = Σ Γ_partial).

    Channels included:
      - All SM charged fermions (u, d, c, s, b, t, e, mu, tau)
      - All active + sterile neutrinos
      - DM pair (χ χ̄) if m_Zp > 2 m_DM

    Parameters
    ----------
    mediator : ZPrimeMediator
    dm_type : str
        Mandatory kwarg; passed to gamma_zprime_to_DM.

    Returns
    -------
    float : total width [GeV].
    """
    width = 0.0

    # SM charged fermions
    for flavor in _CHARGED_FERMIONS:
        width += gamma_zprime_to_ff(mediator, flavor, dm_type=dm_type)

    # Neutrinos (active + sterile)
    width += gamma_zprime_to_nu(mediator, dm_type=dm_type)

    # DM pair
    width += gamma_zprime_to_DM(mediator, dm_type=dm_type)

    return width
