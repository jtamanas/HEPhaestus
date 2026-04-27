"""
Thermally averaged DM annihilation cross section via Higgs portal.
arXiv:2511.21808, Eqs. 6-8 (plan v1 numbering).

Scalar DM with Lagrangian: L ⊃ -(1/2)λ χ² H†H
Effective h-χ-χ coupling: y_{hχχ} = λ v_h  (D2 decision)

Formula (Eq. 6, plan):
  <σv> = y_{hχχ}² / (4π) × Σ_f N_c y_f² m_f² β_f / [(4m_χ² - m_h²)² + m_h² Γ_h²]
       × (1 + p-wave correction)

In the narrow-width approximation off the funnel:
  <σv> ≈ N_c y_f² y_{hχχ}² m_f² β_f / [4π m_DM² ((4m_DM² - m_h²)² + m_h²Γ_h²)]
        × 4 m_DM²

The full formula at leading order (s-wave, m_χ² << m_h²):
  <σv> = (y_{hχχ})² Σ_{f} N_c m_f² β_f^3 / [8π m_DM² |D_BW|^2]

where D_BW = 4m_DM² - m_h² + i m_h Γ_h and β_f = sqrt(1 - m_f²/m_DM²).

Notes:
  - Vector portal deferred in v1 (docstring note).
  - dm_type="scalar" sentinel for this module.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import (
    M_H, V_H, GEV2_TO_CM2,
    M_U, M_D, M_S, M_C, M_B, M_T,
    M_E, M_MU, M_TAU,
)

# SM Yukawa-type: fermion mass → coupling via y_f = m_f / v_h
# (this gives the Higgs-to-ff coupling in the SM)
_FERMION_MASS_YUKAWA = {
    "u": M_U, "d": M_D, "s": M_S, "c": M_C, "b": M_B, "t": M_T,
    "e": M_E, "mu": M_MU, "tau": M_TAU,
}
_QUARK_FLAVORS = frozenset({"u", "d", "s", "c", "b", "t"})

# Channels available for σv calculation
HIGGS_PORTAL_CHANNELS = list(_FERMION_MASS_YUKAWA.keys())

# SM Higgs total width [GeV] — PDG 2024
GAMMA_H_SM = 4.07e-3


def sigma_v_higgs_portal(portal, *, dm_type: str = "scalar", channel: str) -> float:
    """
    Thermally averaged <σv> for scalar DM via Higgs portal.
    arXiv:2511.21808, Eqs. 6-8 (plan v1 numbering).

    NOTE: Vector portal deferred in v1. Only scalar DM supported.

    Formula (s-wave, off-funnel approximation):
      <σv> = y_{hχχ}² × Σ_f [N_c m_f² β_f^3 / (8π v_h²)] / |D_BW|²

    where:
      y_{hχχ} = λ v_h  (effective h-χ-χ coupling, D2 convention)
      D_BW = 4 m_DM² - m_h² + i m_h Γ_h
      β_f = sqrt(1 - m_f²/m_DM²)  (kinematic factor)
      y_f = m_f / v_h  (SM Yukawa coupling)

    Rewriting:
      <σv> = (λ v_h)² / (8π v_h²) × N_c × m_f² / m_DM² × β_f^3 / |D_BW|²
           = λ² / (8π) × N_c m_f² β_f^3 / (m_DM² |D_BW|²)

    This is the leading s-wave term; p-wave and BW off-funnel formula.

    Parameters
    ----------
    portal : HiggsPortalScalar
    dm_type : str
        Must be "scalar" (guardrail; vector deferred).
    channel : str
        SM fermion channel, e.g. "bb", "b", "tau", "mu".
        Accepts "b", "bb" → bottom quark.
        Single flavor string; "sum" sums all kinematically open channels.

    Returns
    -------
    float : <σv> in cm^3/s.
    """
    if dm_type != "scalar":
        raise ValueError(
            "sigma_v_higgs_portal only supports dm_type='scalar'. "
            "Vector portal is deferred in v1."
        )

    m_DM = portal.m_DM
    lam = portal.lam
    m_h = portal.m_h
    y_hchichi = portal.effective_h_DM_DM_coupling()  # = lam * v_h

    # BW denominator |D_BW|²
    s0 = 4.0 * m_DM**2
    D_BW_sq = (s0 - m_h**2)**2 + (m_h * GAMMA_H_SM)**2

    # Normalize channel string
    ch = channel.rstrip("~").rstrip("b") + channel[len(channel.rstrip("~b")):]
    # Simple mapping
    if channel in ("bb", "b b~", "b"):
        flavors_to_sum = ["b"]
    elif channel in ("tau", "tautau", "tau+ tau-"):
        flavors_to_sum = ["tau"]
    elif channel in ("cc", "c"):
        flavors_to_sum = ["c"]
    elif channel in ("tt", "t"):
        flavors_to_sum = ["t"]
    elif channel == "sum":
        flavors_to_sum = list(_FERMION_MASS_YUKAWA.keys())
    else:
        # Try direct lookup
        flavors_to_sum = [channel] if channel in _FERMION_MASS_YUKAWA else []
        if not flavors_to_sum:
            raise ValueError(
                f"Unknown channel '{channel}'. Use 'b', 'tau', 'c', 't', 'sum', etc."
            )

    total_sigma_v_gev2 = 0.0

    for flavor in flavors_to_sum:
        m_f = _FERMION_MASS_YUKAWA[flavor]

        # Kinematic check: DM must be heavier than final-state fermion
        if m_DM <= m_f:
            continue

        beta_f = math.sqrt(1.0 - m_f**2 / m_DM**2)
        N_c = 3 if flavor in _QUARK_FLAVORS else 1

        # <σv> contribution from this channel
        # Formula: N_c * y_{hχχ}^2 * m_f^2 * β_f^3 / (8π * v_h^2 * |D_BW|^2)
        # Equivalently: N_c * λ^2 * m_f^2 * β_f^3 / (8π * |D_BW|^2)
        sigma_v_ch = (N_c * y_hchichi**2 * m_f**2 * beta_f**3
                      / (8.0 * math.pi * V_H**2 * D_BW_sq))
        total_sigma_v_gev2 += sigma_v_ch

    return total_sigma_v_gev2 * GEV2_TO_CM2
