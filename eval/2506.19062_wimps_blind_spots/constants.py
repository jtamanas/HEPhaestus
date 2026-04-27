"""
Physical constants used in arXiv:2506.19062.
All values in natural units (hbar = c = 1), masses in GeV.
"""

import numpy as np

# Electroweak parameters
M_W = 80.377          # W boson mass [GeV]
M_Z = 91.1876         # Z boson mass [GeV]
M_H = 125.25          # SM Higgs mass [GeV]
V_H = 246.22          # Higgs VEV [GeV]
G_F = 1.1663788e-5    # Fermi constant [GeV^-2]
ALPHA_EM = 1.0 / 137.036  # fine structure constant
SW2 = 0.23122         # sin^2(theta_W)
CW2 = 1.0 - SW2
G_WEAK = np.sqrt(4 * np.pi * ALPHA_EM / SW2)  # SU(2) gauge coupling

# Quark masses (MSbar at 2 GeV unless noted)
M_U = 2.16e-3         # up quark [GeV]
M_D = 4.67e-3         # down quark [GeV]
M_S = 93.4e-3         # strange quark [GeV]
M_C = 1.27            # charm quark [GeV]
M_B = 4.18            # bottom quark [GeV]
M_T = 172.69          # top quark [GeV]

# Nucleon parameters
M_P = 0.93827         # proton mass [GeV]
M_N = 0.93957         # neutron mass [GeV]

# Nucleon form factors for SI scattering (Hoferichter et al.)
# f_q^N = <N|m_q qbar q|N> / m_N
F_U_P = 0.0153        # f_u^p
F_D_P = 0.0191        # f_d^p
F_S_P = 0.0447        # f_s^p
F_U_N = 0.0110        # f_u^n
F_D_N = 0.0273        # f_d^n
F_S_N = 0.0447        # f_s^n

# Gluon form factor: f_TG = 1 - sum_q f_q
F_TG_P = 1.0 - F_U_P - F_D_P - F_S_P
F_TG_N = 1.0 - F_U_N - F_D_N - F_S_N

# Nucleon spin fractions for SD scattering
DELTA_U_P = 0.842     # Delta_u^p
DELTA_D_P = -0.427    # Delta_d^p
DELTA_S_P = -0.085    # Delta_s^p

# Quark PDFs at mu = 2 GeV (for twist-2 contributions)
# q(2) = <N|(1/2) qbar {gamma_mu D_nu} q|N> (second moment)
Q2_U_P = 0.22         # u(2) for proton
Q2_D_P = 0.11         # d(2) for proton
QBAR2_U_P = 0.034     # ubar(2) for proton
QBAR2_D_P = 0.036     # dbar(2) for proton
Q2_S_P = 0.026        # s(2) = sbar(2) for proton
Q2_C_P = 0.019        # c(2) = cbar(2) for proton
Q2_B_P = 0.012        # b(2) = bbar(2) for proton

# Z-boson couplings to quarks: A_q^Z = T3_q
A_U_Z = 0.5           # up-type T3
A_D_Z = -0.5          # down-type T3

# Cosmological parameters
OMEGA_DM_H2 = 0.1200  # Planck 2018 DM relic density
OMEGA_DM_H2_SIGMA = 0.0012
SIGMA_V_THERMAL = 3.0e-26  # thermal <sigma v> [cm^3/s]

# Conversion factors
GEV2_TO_CM2 = 0.3894e-27   # 1 GeV^-2 = 0.3894e-27 cm^2
GEV2_TO_PB = 0.3894e6      # 1 GeV^-2 = 0.3894e6 pb
CM2_TO_PB = 1.0e36          # 1 cm^2 = 1e36 pb


def reduced_mass(m1: float, m2: float) -> float:
    """Reduced mass of a two-body system."""
    return m1 * m2 / (m1 + m2)
