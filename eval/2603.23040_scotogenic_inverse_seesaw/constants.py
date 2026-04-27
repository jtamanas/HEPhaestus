"""
Physical constants used in arXiv:2603.23040 (Scotogenic Inverse Seesaw).
All values in natural units (hbar = c = 1), masses in GeV unless noted.

Sources:
  - EW parameters: PDG 2022
  - Scalar form factors: Hoferichter, Ruiz de Elvira, Kubis, Meissner 2015
    (Phys. Rev. Lett. 115, 092301).
    Derivation: sigma_piN = 59.1(3.5) MeV, sigma_s = 41.3(7.7) MeV (proton).
    f_Tq = m_q <N|q-bar q|N> / m_N.
    Quark mass ratios used: m_u/m_d = 0.553, m_s/m_l = 27.5 (FLAG 2019)
    to split sigma_piN into f_Tu and f_Td separately for p and n.
  - Axial form factors: FLAG 2021 g_A averages (Nf=2+1+1 lattice).
  - Xenon abundances: Del Nobile 2022, Table B.1.
  - MAJORANA_FACTOR docstring: applied exactly once per sigma-level function.
"""

import numpy as np
from numpy.typing import NDArray

# ======================================================================
# Electroweak parameters
# ======================================================================
M_W = 80.377          # W boson mass [GeV]
M_Z = 91.1876         # Z boson mass [GeV]
M_H = 125.25          # SM Higgs mass [GeV]
V_H = 246.22          # Higgs VEV [GeV]
G_F = 1.1663788e-5    # Fermi constant [GeV^-2]
ALPHA_EM = 1.0 / 137.036  # fine structure constant (dimensionless)
SW2 = 0.23122         # sin^2(theta_W) [dimensionless]
ALPHA_S_MZ = 0.1179   # strong coupling at M_Z (dimensionless)

# Decay widths
GAMMA_H_SM = 4.07e-3   # SM Higgs total width [GeV]
GAMMA_Z_SM = 2.4952    # SM Z total width [GeV]

# ======================================================================
# Lepton masses
# ======================================================================
M_E_LEPTON = 0.510999e-3   # electron mass [GeV]
M_MU = 0.10566             # muon mass [GeV]
M_TAU = 1.77686            # tau mass [GeV]

# ======================================================================
# Quark masses (MSbar, appropriate scale)
# ======================================================================
M_U = 2.16e-3         # up quark [GeV]
M_D = 4.67e-3         # down quark [GeV]
M_S = 93.4e-3         # strange quark [GeV]
M_C = 1.27            # charm quark [GeV]
M_B = 4.18            # bottom quark [GeV]
M_T = 172.69          # top quark [GeV]

# ======================================================================
# Nucleon masses
# ======================================================================
M_P = 0.93827         # proton mass [GeV]
M_N_NUCLEON = 0.93957  # neutron mass [GeV] (renamed to avoid clash with M_N param)

# ======================================================================
# Scalar (SI) nucleon form factors — Hoferichter et al. 2015
# f_Tq^N defined via f_Tq = m_q <N|q-bar q|N> / m_N
# Proton
# ======================================================================
F_TU_P = 0.0153       # f_Tu^proton
F_TD_P = 0.0191       # f_Td^proton
F_TS_P = 0.0447       # f_Ts^proton
# Neutron (isospin rotation: u <-> d, s same)
F_TU_N = 0.0110       # f_Tu^neutron
F_TD_N = 0.0273       # f_Td^neutron
F_TS_N = 0.0447       # f_Ts^neutron


def f_TG(f_Tu_N: float, f_Td_N: float, f_Ts_N: float) -> float:
    """Gluon form factor. f_TG = 2/27 * (1 - f_Tu - f_Td - f_Ts). [dimensionless]"""
    return (2.0 / 27.0) * (1.0 - f_Tu_N - f_Td_N - f_Ts_N)


# Precomputed gluon form factors
F_TG_P = f_TG(F_TU_P, F_TD_P, F_TS_P)
F_TG_N = f_TG(F_TU_N, F_TD_N, F_TS_N)

# ======================================================================
# Axial (SD) nucleon form factors — FLAG 2021 g_A averages
# Nf=2+1+1 lattice QCD
# ======================================================================
# Proton axial couplings
DELTA_U_P = 0.842     # Delta_u^proton (dimensionless)
DELTA_D_P = -0.427    # Delta_d^proton (dimensionless)
DELTA_S_P = -0.085    # Delta_s^proton (dimensionless)
# Neutron axial couplings (isospin rotation: u <-> d, s same)
DELTA_U_N = DELTA_D_P    # -0.427 (dimensionless)
DELTA_D_N = DELTA_U_P    #  0.842 (dimensionless)
DELTA_S_N = DELTA_S_P    # -0.085 (dimensionless)

# ======================================================================
# Xenon parameters — Del Nobile 2022, Table B.1
# ======================================================================
XENON_Z = 54  # atomic number of xenon (constant; N6 resolution)

# Isotopic abundances (mass number: fractional abundance)
XENON_ABUNDANCES = {
    124: 0.0009,
    126: 0.0009,
    128: 0.0192,
    129: 0.2644,
    130: 0.0408,
    131: 0.2118,
    132: 0.2689,
    134: 0.1044,
    136: 0.0887,
}

# Xe-131 spin matrix elements (dominant odd-neutron isotope)
S_A_p_XE131 = 0.010   # proton spin matrix element for Xe-131 [dimensionless]
S_A_n_XE131 = 0.329   # neutron spin matrix element for Xe-131 [dimensionless]
J_XE131 = 1.5         # total spin of Xe-131 nucleus [dimensionless]

# ======================================================================
# Conversion factors
# ======================================================================
GEV2_TO_CM2 = 0.3894e-27      # 1 GeV^-2 = 0.3894e-27 cm^2
GEV_TO_CMCUBEDSEC = 1.1673e-17  # 1 GeV^-2 natural units -> cm^3/s for <sigma v>

# ======================================================================
# MAJORANA_FACTOR
# ======================================================================
MAJORANA_FACTOR = 2.0
"""Factor from identical-particle statistics in the outgoing DM line.
Applied exactly once per sigma-level function (`sigma_bar_SI`,
`sigma_SD_full`, `sigma_SD_simplified`). Never at |M|^2 or
Wilson-coefficient layer. Cross-checked against Del Nobile 2022 Eq. 5.38."""


# ======================================================================
# Helper
# ======================================================================
def reduced_mass(m1: float, m2: float) -> float:
    """Reduced mass of a two-body system [same units as inputs]."""
    return m1 * m2 / (m1 + m2)
