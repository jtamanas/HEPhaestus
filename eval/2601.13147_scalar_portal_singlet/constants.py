"""
Physical constants used in arXiv:2601.13147 (Singlet Fermion DM + Scalar Portal).
All values in natural units (hbar = c = 1), masses in GeV.

These constants are shared verbatim with eval/2506.19062_wimps_blind_spots/constants.py.
The form factors follow Hoferichter et al. conventions.
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

# Conversion factors
GEV2_TO_CM2 = 0.3894e-27   # 1 GeV^-2 = 0.3894e-27 cm^2


def reduced_mass(m1: float, m2: float) -> float:
    """Reduced mass of a two-body system."""
    return m1 * m2 / (m1 + m2)


def sanity_check_vh() -> None:
    """Verify V_H is consistent with G_F via the tree-level relation V_H^2 * G_F * sqrt(2) ≈ 1.

    Note: V_H = 246.22 GeV is rounded to 2 decimal places; the exact value from G_F is
    246.2196 GeV. The identity holds to ~3e-6 (not 1e-6), so we use tol=5e-6 here.
    T36 in test_benchmarks.py documents this with tol=5e-6 as well.
    """
    assert abs(V_H**2 * G_F * np.sqrt(2.0) - 1.0) < 5e-6, "V_H–G_F identity violated"
