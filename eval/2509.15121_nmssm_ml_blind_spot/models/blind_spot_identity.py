"""
NMSSM bino/higgsino blind-spot identity.
arXiv:2509.15121, Eq. (7).

The blind-spot condition for vanishing DM-Higgs coupling in the bino/higgsino
system reads (approximately, neglecting wino and singlino admixture):

    [ m_chi1 + g1^2 v^2 / (M1 - m_chi1) ] / (mu_eff * sin(2 beta)) ~ 1

When this identity holds, the spin-independent direct detection cross section
is suppressed by destructive interference between bino and higgsino components.

Notes (binding):
  - m_chi1_signed is the SIGNED eigenvalue from diagonalize_neutralino,
    NOT |m_chi1|. The sign matters for the denominator (M1 - m_chi1).
  - g1 is SM-normalized (NOT GUT-normalized g' = g1 * sqrt(5/3)).
    constants.G1_SM is the only authoritative source.
  - The identity is approximate at O(Z_W + Z_S) corrections from wino/singlino
    admixture. On-blind-spot BPs: LHS ~ 1 to ~10%. Off-blind-spot: LHS != 1.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, G1_SM


def blind_spot_identity_lhs(
    m_chi1_signed: float,
    M1: float,
    mu_eff: float,
    tan_beta: float,
    v: float = V_H,
    g1: float = G1_SM,
) -> float:
    """
    LHS of the NMSSM bino/higgsino blind-spot identity, Eq. (7).
    arXiv:2509.15121, Eq. (7):

        LHS = [ m_chi1 + g1^2 v^2 / (M1 - m_chi1) ] / (mu_eff * sin(2*beta))

    On the blind spot, LHS ~ 1; clearly != 1 off the blind spot.

    Notes (binding):
      - m_chi1_signed is the SIGNED eigenvalue (SLHA-1 convention):
            m_chi1_signed = masses_abs[0] * signs[0]
        The sign enters the denominator (M1 - m_chi1_signed).
      - g1 MUST be SM-normalized (no sqrt(5/3) factor). Using G1_SM=0.3574.
      - sin(2*beta) = 2 sin(beta) cos(beta) = 2 tan_beta / (1 + tan_beta^2).
      - The denominator M1 - m_chi1_signed can be small if M1 ~ m_chi1 (bino
        limit). A conditioning guard |M1 - m_chi1| > 5 GeV is applied in tests.

    Parameters
    ----------
    m_chi1_signed : float — signed LSP mass eigenvalue [GeV] from SLHA-1 diag
    M1            : float — bino soft mass [GeV] (signed)
    mu_eff        : float — effective higgsino mass [GeV] (signed)
    tan_beta      : float — tan β > 0
    v             : float — Higgs VEV [GeV] (default V_H = 246.22)
    g1            : float — SM-normalized U(1)_Y coupling (default G1_SM = 0.3574)

    Returns
    -------
    float : LHS value; ~1 on blind spot; clearly != 1 off blind spot.

    Raises
    ------
    ZeroDivisionError : if M1 == m_chi1_signed (denominator exactly zero)
    """
    beta = np.arctan(tan_beta)
    sin_2beta = np.sin(2.0 * beta)

    denom_bino = M1 - m_chi1_signed
    numerator = m_chi1_signed + g1**2 * v**2 / denom_bino
    denominator = mu_eff * sin_2beta

    return numerator / denominator
