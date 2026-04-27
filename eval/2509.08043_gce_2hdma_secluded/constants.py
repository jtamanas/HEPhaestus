"""
Physical constants for arXiv:2509.08043.
All values in natural units (hbar = c = 1), masses in GeV.

θ here = Bauer-2017 mixing-angle convention; paper 2509.08043 uses same symbol.
"""

import numpy as np

# Electroweak parameters
V_H = 246.22           # Higgs VEV [GeV]
M_H = 125.25           # SM Higgs mass [GeV]
M_Z = 91.1876          # Z boson mass [GeV]
M_W = 80.377           # W boson mass [GeV]
SW2 = 0.23122          # sin²(θ_W)
ALPHA_EM = 1.0 / 137.036  # fine structure constant
G_F = 1.1663788e-5     # Fermi constant [GeV^-2]

# Quark masses (MSbar at 2 GeV unless noted)
M_U = 2.16e-3          # up quark [GeV]
M_D = 4.67e-3          # down quark [GeV]
M_S = 0.093            # strange quark [GeV]
M_C = 1.27             # charm quark [GeV]
M_B = 4.18             # bottom quark [GeV]
M_T = 172.69           # top quark [GeV]

# Nucleon masses
M_P = 0.93827          # proton mass [GeV]
M_N = 0.93957          # neutron mass [GeV]

# Nucleon form factors (scalar, SI scattering via Higgs portal)
# Proton: f_q^p = <p|m_q q-bar q|p> / m_p
F_U_P = 0.0153
F_D_P = 0.0191
F_S_P = 0.0447
F_TG_P = 1.0 - F_U_P - F_D_P - F_S_P   # heavy quark contribution (trace anomaly)

# Neutron
F_U_N = 0.0110
F_D_N = 0.0273
F_S_N = 0.0447
F_TG_N = 1.0 - F_U_N - F_D_N - F_S_N

# Nucleon sigma term (mass-dimensioned scalar form factor):
# SIGMA_MQ_QBARQ = <N|Σ_q m_q q̄q|N>  [GeV]
# This is MASS-DIMENSIONED (not a dimensionless form factor — see plan N4).
# Value: 330 MeV = 0.330 GeV from lattice QCD / ChPT fits.
# Used in Eq. 50 (arXiv:2509.08043) as the nucleon matrix element for σ_SI.
SIGMA_MQ_QBARQ = 0.330  # GeV; <N|Σ_q m_q q̄q|N>, MASS-DIMENSIONED (not a dimensionless form factor)

# Conversion factors
GEV2_TO_CM2 = 0.3894e-27   # 1 GeV^-2 = 0.3894e-27 cm^2


def reduced_mass(m1: float, m2: float) -> float:
    """Reduced mass of a two-body system [GeV].

    Parameters
    ----------
    m1 : float — first particle mass [GeV]
    m2 : float — second particle mass [GeV]

    Returns
    -------
    float : reduced mass m1*m2/(m1+m2) [GeV]
    """
    return m1 * m2 / (m1 + m2)
