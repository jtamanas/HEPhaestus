"""
Scalar dark matter via Higgs portal.
arXiv:2511.21808, Section II.2; Equations 6-9 (plan numbering).

Lagrangian convention (paper explicit, D2 decision):
  L ⊃ - (1/2) λ_{hχ} χ² H†H

When H acquires its VEV v_h, the effective h-χ-χ vertex is:
  y_{hχχ} = λ v_h

(From: -(1/2)λ χ² (v_h + h)² → cross term -(1/2)λ χ² 2 v_h h = -λ v_h h χ²
→ vertex factor = λ v_h in the Feynman rule for h-χ-χ.)

The Breit-Wigner correction is relevant near m_χ ≈ m_h / 2 (the "funnel").
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import M_H, V_H


class HiggsPortalScalar:
    """
    Scalar DM coupled via Higgs portal.
    arXiv:2511.21808, Section II.2.

    Attributes
    ----------
    m_DM : float
        DM mass [GeV].
    lam : float
        Quartic coupling λ in (1/2)λ χ² H†H.
    m_h : float
        Higgs mass [GeV] (default 125.25 GeV).
    """

    def __init__(self, m_DM: float, lam: float, m_h: float = M_H):
        self.m_DM = m_DM
        self.lam = lam
        self.m_h = m_h

    def effective_h_DM_DM_coupling(self) -> float:
        """
        Effective h-χ-χ coupling from (1/2)λ|H|²S².
        arXiv:2511.21808, Section II.2 (D2 convention).

        y_{hχχ} = λ · v_h

        This arises because:
          (1/2)λ χ² |H|² ⊃ (1/2)λ χ² · (v_h + h)²
          → (1/2)λ χ² (2 v_h h) at linear order in h
          → vertex = λ v_h   (the 1/2 cancels against the 2 from expansion)

        Returns
        -------
        float : coupling y_{hχχ} [dimensionless]
        """
        return self.lam * V_H

    def breit_wigner_factor(self, s: float) -> complex:
        """
        Breit-Wigner propagator factor for h-exchange.
        arXiv:2511.21808 Eq. 8 (plan numbering).

        F_BW(s) = 1 / (s - m_h^2 + i * m_h * Γ_h)

        where Γ_h is the SM Higgs total width (~4.07 MeV = 4.07e-3 GeV).

        Parameters
        ----------
        s : float
            Mandelstam s [GeV^2].

        Returns
        -------
        complex : Breit-Wigner propagator [GeV^-2]
        """
        # SM Higgs total width (PDG 2024)
        gamma_h_sm = 4.07e-3  # GeV
        denom = complex(s - self.m_h**2, self.m_h * gamma_h_sm)
        return 1.0 / denom
