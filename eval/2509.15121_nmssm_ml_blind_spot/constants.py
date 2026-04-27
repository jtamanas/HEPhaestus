"""
Physical constants used in arXiv:2509.15121.
"Shedding Light on Dark Matter at the LHC with Machine Learning"
Arganda et al., 2025.

All values in natural units (hbar = c = 1), masses in GeV.

References:
  - PDG 2022 for SM parameters
  - Planck 2018 for OMEGA_PLANCK_H2
"""

import numpy as np

# --------------------------------------------------------------------------
# Higgs sector
# --------------------------------------------------------------------------
V_H = 246.22       # Higgs VEV sqrt(vu^2 + vd^2) [GeV]; PDG 2022
M_H = 125.25       # SM Higgs boson mass [GeV]; PDG 2022
M_Z = 91.1876      # Z boson mass [GeV]; PDG 2022

# --------------------------------------------------------------------------
# Electroweak mixing
# --------------------------------------------------------------------------
SW2 = 0.23122      # sin^2(theta_W); PDG 2022 (MSbar, MZ scale)

# --------------------------------------------------------------------------
# Gauge couplings — SM normalization (NOT GUT-normalized).
#
# G1_SM is the SM U(1)_Y gauge coupling g1 (also written g' in some
# conventions), normalized so that the hypercharge-Higgs-Z vertex reads
#   M_Z = (1/2) sqrt(g1^2 + g2^2) * v .
#
# IMPORTANT: G1_SM is NOT the GUT-normalized coupling g_1^GUT = g1*sqrt(5/3).
# The NMSSM mass matrix Eq. (3) of arXiv:2509.15121 uses the SM-normalized
# g_1 (no sqrt(5/3) factor). See also the blind-spot Eq. (7).
#
# Numerical values:
#   g2 = 2*M_W/V_H     (tree-level relation; M_W ~ 80.377 GeV)
#   g1 = sqrt(4*pi*alpha_em / (1 - SW2)) but in practice we use:
#   SW2 = g1^2/(g1^2+g2^2)  -->  g1^2 = g2^2 * SW2/(1-SW2)
#   With g2 = 0.6517:  g1 = 0.6517 * sqrt(0.23122/0.76878) = 0.3574
# --------------------------------------------------------------------------
G2_SM = 0.6517     # SU(2)_L gauge coupling g2 [dimensionless]; SM-normalized
G1_SM = 0.3574     # U(1)_Y gauge coupling g1 [dimensionless]; SM-normalized

# --------------------------------------------------------------------------
# Cosmology
# --------------------------------------------------------------------------
OMEGA_PLANCK_H2 = 0.120   # Planck 2018: Omega_DM h^2 = 0.120 +/- 0.001


def reduced_mass(m1: float, m2: float) -> float:
    """
    Reduced mass of a two-body system.

    mu = m1 * m2 / (m1 + m2)

    Parameters
    ----------
    m1, m2 : float — masses [GeV]

    Returns
    -------
    float : reduced mass [GeV]
    """
    return m1 * m2 / (m1 + m2)
