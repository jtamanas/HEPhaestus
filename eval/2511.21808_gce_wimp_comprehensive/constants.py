"""
Physical constants used in arXiv:2511.21808.
All values in natural units (hbar = c = 1), masses in GeV.

References:
  PDG 2024: https://pdg.lbl.gov/
  Hoferichter et al. 2017: arXiv:1708.02245 (scalar nucleon form factors)
  Belanger et al. 2020: micrOMEGAs (SD axial form factors)
"""

import math

# ===========================================================================
# Electroweak parameters  [PDG 2024]
# ===========================================================================
M_W = 80.377          # W boson mass [GeV]
M_Z = 91.1876         # Z boson mass [GeV]
M_H = 125.25          # SM Higgs mass [GeV]
V_H = 246.22          # Higgs VEV [GeV]
G_F = 1.1663788e-5    # Fermi constant [GeV^-2]
ALPHA_EM = 1.0 / 137.036  # fine structure constant at q^2=0
SW2 = 0.23122         # sin^2(theta_W) [PDG 2024]
CW2 = 1.0 - SW2       # cos^2(theta_W)

# ===========================================================================
# Quark masses — MSbar at 2 GeV (used in form factor context, D1 decision)
# Kinematic thresholds in decay widths use pole masses.
# ===========================================================================
M_U = 2.16e-3         # up quark MSbar at 2 GeV [GeV]  PDG 2024
M_D = 4.67e-3         # down quark MSbar at 2 GeV [GeV]  PDG 2024
M_S = 93.4e-3         # strange quark MSbar at 2 GeV [GeV]  PDG 2024
M_C = 1.27            # charm quark MSbar at m_c [GeV]  PDG 2024
M_B = 4.18            # bottom quark MSbar at m_b [GeV]  PDG 2024
M_T = 172.69          # top quark pole mass [GeV]  PDG 2024

# Quark pole masses (for kinematic thresholds in Z' decay widths)
M_U_POLE = 2.16e-3    # up quark pole (approx MSbar, negligible for threshold)
M_D_POLE = 4.67e-3    # down quark pole
M_S_POLE = 93.4e-3    # strange pole
M_C_POLE = 1.67       # charm pole  PDG 2024
M_B_POLE = 4.78       # bottom pole  PDG 2024
M_T_POLE = 172.69     # top pole

# ===========================================================================
# Lepton masses  [PDG 2024]
# ===========================================================================
M_E   = 0.51099895e-3  # electron mass [GeV]
M_MU  = 105.6583755e-3 # muon mass [GeV]
M_TAU = 1776.86e-3     # tau mass [GeV]

# ===========================================================================
# Nucleon masses  [PDG 2024]
# ===========================================================================
M_P = 0.93827208816   # proton mass [GeV]
M_N = 0.93956542052   # neutron mass [GeV]

# ===========================================================================
# Nucleon SCALAR form factors  (Hoferichter et al. 2017, arXiv:1708.02245)
# Used for Higgs portal σ_SI; NOT used for vector Z' SI (valence quark counting used there).
# f_q^N = <N|m_q qq̄|N> / M_N
# ===========================================================================
F_U_P = 0.0153        # f_u^p  [Hoferichter 2017]
F_D_P = 0.0191        # f_d^p  [Hoferichter 2017]
F_S_P = 0.0447        # f_s^p  [Hoferichter 2017]
F_TG_P = 1.0 - F_U_P - F_D_P - F_S_P   # gluon trace (proton): ~0.9209

F_U_N = 0.0110        # f_u^n  [Hoferichter 2017]
F_D_N = 0.0273        # f_d^n  [Hoferichter 2017]
F_S_N = 0.0447        # f_s^n  (same as proton; strange-quark contribution isoscalar)
F_TG_N = 1.0 - F_U_N - F_D_N - F_S_N   # gluon trace (neutron): ~0.9170

# Total scalar nucleon factor (Higgs portal): f_N = sum_q f_q + (2/9) F_TG
# f_N^p = F_U_P + F_D_P + F_S_P + (2/9)*F_TG_P
F_N_SCALAR_P = F_U_P + F_D_P + F_S_P + (2.0/9.0)*F_TG_P  # ≈ 0.2838
F_N_SCALAR_N = F_U_N + F_D_N + F_S_N + (2.0/9.0)*F_TG_N  # ≈ 0.2838

# ===========================================================================
# SD axial nucleon form factors  (Belanger et al. 2020, micrOMEGAs; Ellis et al.)
# Delta_q^N = <N|q-bar gamma_mu gamma_5 q|N> (spin content)
# ===========================================================================
DELTA_U_P =  0.842    # Delta_u^p   [PDG/Belanger]
DELTA_D_P = -0.427    # Delta_d^p
DELTA_S_P = -0.085    # Delta_s^p

DELTA_U_N = -0.427    # Delta_u^n = Delta_d^p (isospin)
DELTA_D_N =  0.842    # Delta_d^n = Delta_u^p
DELTA_S_N = -0.085    # Delta_s^n = Delta_s^p

# ===========================================================================
# Conversion factors
# ===========================================================================
GEV2_TO_CM2 = 0.3894e-27   # 1 GeV^-2 = 0.3894e-27 cm^2  [PDG]
# Note: CM3S_PER_GEV_MINUS_2 = GEV2_TO_CM2 * c (c=1 in natural units)
# <sigma*v> in cm^3/s = <sigma*v> in GeV^-2 * GEV2_TO_CM2
# (natural units: hbar*c = 0.197327 GeV·fm; (hbar*c)^2 = 3.894e-4 GeV^2·mb)


# ===========================================================================
# Helper functions
# ===========================================================================

def reduced_mass(m1: float, m2: float) -> float:
    """Reduced mass of a two-body system in GeV."""
    return m1 * m2 / (m1 + m2)


def beta(m_f: float, m_V: float) -> float:
    """Relativistic velocity factor sqrt(1 - 4*m_f^2/m_V^2) for V->ff decay."""
    x = 4.0 * m_f**2 / m_V**2
    if x >= 1.0:
        return 0.0
    return math.sqrt(1.0 - x)
