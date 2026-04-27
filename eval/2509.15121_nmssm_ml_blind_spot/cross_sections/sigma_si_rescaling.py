"""
Sub-relic DM rescaling of the spin-independent direct detection cross section.
arXiv:2509.15121, Eq. (15).

When the neutralino LSP underproduces the observed DM relic density
(Omega_chi h^2 < Omega_Planck h^2), the effective direct detection rate is
suppressed by the fraction of DM that the neutralino actually constitutes.
The effective cross section is:

    sigma_SI_eff = sigma_SI * min(1, Omega_chi h^2 / Omega_Planck h^2)

This rescaling is applied when comparing to experimental limits that assume
100% DM composition. For BPs with Omega < 0.12, the effective sigma is
reduced accordingly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import OMEGA_PLANCK_H2


def sigma_SI_rescaled(
    sigma_SI_nominal: float,
    omega_h2_computed: float,
    omega_h2_planck: float = OMEGA_PLANCK_H2,
) -> float:
    """
    Sub-relic-DM rescaling of the SI direct detection cross section.
    arXiv:2509.15121, Eq. (15):

        sigma_SI_eff = sigma_SI * min(1, Omega_chi h^2 / Omega_Planck h^2)

    Used when the NMSSM neutralino underproduces DM (Omega < Planck value),
    so the local dark matter density entering the direct detection rate is
    suppressed by the relic fraction.

    Monotonicity: sigma_SI_eff is linear in omega_h2_computed (when the
    ratio is below 1). Doubling omega_h2_computed doubles sigma_SI_eff
    exactly (verified in tests). When omega_h2_computed >= omega_h2_planck,
    the min clips at 1 and sigma_SI_eff = sigma_SI_nominal.

    Parameters
    ----------
    sigma_SI_nominal   : float — nominal SI cross section [cm^2]
    omega_h2_computed  : float — computed relic density Omega_chi h^2
    omega_h2_planck    : float — Planck 2018 reference value (default 0.120)

    Returns
    -------
    float : effective SI cross section [cm^2]; units same as sigma_SI_nominal
    """
    rescaling = min(1.0, omega_h2_computed / omega_h2_planck)
    return sigma_SI_nominal * rescaling
