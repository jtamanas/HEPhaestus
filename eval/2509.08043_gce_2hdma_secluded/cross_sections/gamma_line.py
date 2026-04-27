"""
Gamma-ray line cross-section for 2HDM+a: χχ̄ → γγ.
arXiv:2509.08043, Eqs. 54-55.

NOTE (S0 E4=NOT_FOUND): The paper does not state a numeric anchor for ⟨σv⟩_γγ
in the text. Fig. 12 shows γ-ray line constraints graphically without quoting
a specific value. Therefore this module ships for completeness but has NO grader
task (`t3_thdma_gamma_line_anchor` is NOT in the YAML file for Phase-1 delivery).

See README for details on the Phase-1 deferral.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import GEV2_TO_CM2, M_H, V_H
from models.two_hdm_plus_a import g_chi_a, g_chi_A


def sigma_v_gamma_line(
    m_chi: float,
    m_a: float,
    m_A: float,
    theta: float,
    g_chi: float,
    tan_beta: float,
) -> float:
    """Thermally-averaged ⟨σv⟩_γγ for 2HDM+a (Eqs. 54-55 of arXiv:2509.08043).

    The γ-ray line signal arises from χχ̄ → γγ via loop diagrams involving
    the 2HDM charged sector. The cross-section is proportional to:

        ⟨σv⟩_γγ ≈ α²_em g_{χa}² / (64π³) × |A(τ)|² / m_chi²

    where A(τ) is the loop amplitude summing over charged 2HDM particles,
    and τ = m_chi²/m_mediator².

    This is a stub implementation. The full loop sum over charged scalars
    requires the complete 2HDM+a spectrum (beyond current scope).
    A phase-space consistent estimate is returned.

    Parameters
    ----------
    m_chi    : float — DM mass [GeV]
    m_a      : float — light pseudoscalar mass [GeV]
    m_A      : float — heavy pseudoscalar mass [GeV]
    theta    : float — mixing angle [rad]
    g_chi    : float — overall DM Yukawa coupling
    tan_beta : float — tan(β)

    Returns
    -------
    float : ⟨σv⟩_γγ in cm³/s (estimate; no numeric pin from paper)
    """
    # S0 E4=NOT_FOUND: no numeric anchor from paper; module ships as stub only.
    # Raising NotImplementedError prevents accidental use as a real Eq. 54-55 evaluation.
    # Re-implement in a follow-up PR once a numeric anchor is extracted from Fig. 12.
    raise NotImplementedError(
        "gamma_line.sigma_v_gamma_line is a stub: S0 E4=NOT_FOUND — the paper "
        "gives no numeric ⟨σv⟩_γγ anchor in the text (only Fig. 12 graphically). "
        "No YAML grader task is wired for Phase-1 delivery. "
        "Re-implement when a digitized Fig. 12 value is available."
    )
