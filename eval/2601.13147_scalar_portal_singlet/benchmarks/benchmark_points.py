"""
Benchmark parameter points for arXiv:2601.13147 (Singlet Fermion DM + Scalar Portal).

BP1 extracted verbatim from paper Table 1 (source: BENCHMARK_TODO line 94):
  m_h2=200, sinθ=0.001, λ_hs=2.2, λ_s=3.38, μ_3=−20, m_χ=222, g_χ=0.57
  Ωh²=0.119, σ_SI(p)=6.96e-50, σ_SI(n)=7.10e-50

BP_mid is synthetic (source: plan brainstorm §B.3, "synthetic_control"):
  m_chi=200, g_chi=1.0, sin_theta=0.2, m_h1=125.25, m_h2=300, lambda_s=2.0, mu_3=-50
  Chosen to exercise sin_theta near the Eq. 24 bound (|sin_theta| <= 0.24)
  and sit away from blind-spot degeneracy. No paper observable.

BP9 numerics loaded from paper-1-numerics.md (extracted in S-01):
  m_chi=78.0, g_chi=0.34, sin_theta=0.002, m_h2=70.0, lambda_s=0.73, mu_3=20.0
  Note: m_h2=70 < m_h1=125.25 (singlet-like state is lighter than SM Higgs).

Naming convention:
  m_h1 = SM-like Higgs mass eigenstate
  m_h2 = singlet-like Higgs mass eigenstate
  For BP1 and BP_mid: m_h2 > m_h1 (singlet heavier)
  For BP9: m_h2 = 70 < m_h1 = 125.25 (singlet lighter)
"""

from dataclasses import dataclass
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import M_H


@dataclass(frozen=True)
class ScalarPortalBP:
    """Benchmark point for the scalar portal singlet DM model.

    Attributes
    ----------
    name           : str — benchmark identifier (e.g., 'BP1')
    m_chi          : float — DM mass [GeV]
    g_chi          : float — DM-singlet Yukawa coupling
    sin_theta      : float — mixing angle sine
    m_h1           : float — SM-like Higgs mass [GeV] (= 125.25 for all BPs)
    m_h2           : float — singlet-like Higgs mass [GeV]
    lambda_s       : float — singlet quartic coupling (from paper Table 1)
    mu_3           : float — singlet cubic coefficient [GeV]
    source         : str — data provenance ("paper_table_1", "synthetic_control", "paper_table_2")
    paper_omega_h2 : float | None — paper-quoted Ωh² (metadata only, not graded)
    paper_sigma_SI_p : float | None — paper-quoted σ_SI(proton) [cm²] (metadata only)
    paper_sigma_SI_n : float | None — paper-quoted σ_SI(neutron) [cm²] (metadata only)
    """
    name: str
    m_chi: float
    g_chi: float
    sin_theta: float
    m_h1: float
    m_h2: float
    lambda_s: float
    mu_3: float
    source: str
    paper_omega_h2: Optional[float]
    paper_sigma_SI_p: Optional[float]
    paper_sigma_SI_n: Optional[float]


# ------------------------------------------------------------------------------
# BP1 — from paper Table 1 (verbatim from BENCHMARK_TODO line 94)
# ------------------------------------------------------------------------------
BP1 = ScalarPortalBP(
    name="BP1",
    m_chi=222.0,
    g_chi=0.57,
    sin_theta=0.001,
    m_h1=125.25,    # = M_H (SM Higgs)
    m_h2=200.0,
    lambda_s=3.38,
    mu_3=-20.0,
    source="paper_table_1",
    paper_omega_h2=0.119,
    paper_sigma_SI_p=6.96e-50,   # paper value; our formula gives ~6.17e-50 (~11% gap)
    paper_sigma_SI_n=7.10e-50,   # paper value (see RECONCILIATION.md)
)

# ------------------------------------------------------------------------------
# BP_mid — synthetic control point (plan §B-1)
# Chosen to exercise sin_theta near the LHC bound (Eq. 24: |sin_theta| <= 0.24)
# and to have a non-trivial mixing for testing stability/unitarity.
# lambda_hs is NOT tabulated here; it is derived internally by
# lagrangian_params_from_physical when needed (B-6 fix).
# ------------------------------------------------------------------------------
BP_mid = ScalarPortalBP(
    name="BP_mid",
    m_chi=200.0,
    g_chi=1.0,
    sin_theta=0.2,
    m_h1=125.25,
    m_h2=300.0,
    lambda_s=2.0,
    mu_3=-50.0,
    source="synthetic_control",
    paper_omega_h2=None,
    paper_sigma_SI_p=None,
    paper_sigma_SI_n=None,
)

# ------------------------------------------------------------------------------
# BP9 — from paper Table 1 (extracted via S-01 paper re-read)
# Source: paper-1-numerics.md
# Note: m_h2=70 < m_h1=125.25 — the singlet is lighter than the SM Higgs here.
# The diagonalize_numerical function returns eigenvalues in ascending order (70, 125.25),
# so round-trip tests compare to sorted (min, max) = (70, 125.25).
# ------------------------------------------------------------------------------
BP9 = ScalarPortalBP(
    name="BP9",
    m_chi=78.0,
    g_chi=0.34,
    sin_theta=0.002,
    m_h1=125.25,    # = M_H (SM-like state)
    m_h2=70.0,      # singlet-like state, lighter than SM Higgs
    lambda_s=0.73,
    mu_3=20.0,
    source="paper_table_2",
    paper_omega_h2=None,
    paper_sigma_SI_p=1.26e-48,
    paper_sigma_SI_n=None,
)

# All graded benchmark points
PINNED_BPS = [BP1, BP_mid, BP9]

# Extended set (all paper BPs where we have enough parameters)
# These are for RECONCILIATION.md diagnostic only, not graded.
_BP2 = ScalarPortalBP(
    name="BP2", m_chi=242.0, g_chi=0.56, sin_theta=0.001,
    m_h1=125.25, m_h2=200.0, lambda_s=3.1, mu_3=100.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP3 = ScalarPortalBP(
    name="BP3", m_chi=180.0, g_chi=0.76, sin_theta=0.001,
    m_h1=125.25, m_h2=200.0, lambda_s=2.95, mu_3=-100.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP4 = ScalarPortalBP(
    name="BP4", m_chi=310.0, g_chi=0.87, sin_theta=0.001,
    m_h1=125.25, m_h2=200.0, lambda_s=4.5, mu_3=20.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP5 = ScalarPortalBP(
    name="BP5", m_chi=380.0, g_chi=0.73, sin_theta=0.001,
    m_h1=125.25, m_h2=350.0, lambda_s=4.0, mu_3=100.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP6 = ScalarPortalBP(
    name="BP6", m_chi=300.0, g_chi=0.87, sin_theta=0.001,
    m_h1=125.25, m_h2=350.0, lambda_s=4.1, mu_3=-100.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP7 = ScalarPortalBP(
    name="BP7", m_chi=167.4, g_chi=0.03, sin_theta=0.07,
    m_h1=125.25, m_h2=350.0, lambda_s=4.8, mu_3=20.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)
_BP8 = ScalarPortalBP(
    name="BP8", m_chi=94.75, g_chi=0.02, sin_theta=0.13,
    m_h1=125.25, m_h2=200.0, lambda_s=3.0, mu_3=20.0,
    source="paper_table_1",
    paper_omega_h2=None, paper_sigma_SI_p=None, paper_sigma_SI_n=None,
)

ALL_BPS = [BP1, _BP2, _BP3, _BP4, _BP5, _BP6, _BP7, _BP8, BP9, BP_mid]
