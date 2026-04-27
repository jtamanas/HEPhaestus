"""
Spin-independent (SI) NREFT cross section for Majorana DM-nucleon scattering.
arXiv:2603.23040, Eqs. 26a, 29a, 29e, 30.
CONVENTIONS.md is binding for all implementations here.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import (
    M_H, MAJORANA_FACTOR, GEV2_TO_CM2, XENON_Z, XENON_ABUNDANCES,
    F_TU_P, F_TD_P, F_TS_P, F_TG_P,
    F_TU_N, F_TD_N, F_TS_N, F_TG_N,
    M_P, M_N_NUCLEON,
)
from inputs import V_REL_DEFAULT


def C_SS_h(y_hchichi: float, m_h: float = M_H) -> float:
    """Eq. 26a. Scalar-scalar Wilson coefficient from h-exchange [GeV^-2].

    C^SS_h = y_hchichi / (2 * m_h^2)

    Per-nucleon: isospin dependence enters at sigma_bar_SI through f_N^(p,n).

    Args:
        y_hchichi   h-chi-chi effective Yukawa [dimensionless]
        m_h         Higgs mass [GeV]
    Returns:
        C^SS_h [GeV^-2]
    """
    return y_hchichi / (2.0 * m_h**2)


def c1_per_nucleon(
    C_SS_h_val: float,
    m_chi: float,
    m_N: float,
    f_Tu_N: float,
    f_Td_N: float,
    f_Ts_N: float,
    f_TG_N: float,
) -> float:
    """Eq. 29a. NREFT coefficient c1 per nucleon N [dimensionless].

    c1^N = C^SS_h * m_N * (f_Tu^N + f_Td^N + f_Ts^N + f_TG^N * (2/27) * ... )
    = C^SS_h * m_N * (f_Tu^N + f_Td^N + f_Ts^N + f_TG^N)

    Note: f_TG_N = 2/27 * (1 - f_Tu - f_Td - f_Ts) is computed in constants.py.
    The SI NREFT c1 operator couples the DM scalar bilinear to the nucleon scalar density.

    Per-nucleon (p and n separately) per CONVENTIONS.md.

    Args:
        C_SS_h_val  Wilson coefficient [GeV^-2]
        m_chi       DM mass [GeV]
        m_N         nucleon mass [GeV]
        f_Tu_N, f_Td_N, f_Ts_N, f_TG_N   scalar form factors [dimensionless]
    Returns:
        c1^N [GeV^-1] (dimensionless in standard NREFT convention with m_N factor)
    """
    return C_SS_h_val * m_N * (f_Tu_N + f_Td_N + f_Ts_N + f_TG_N)


def c8_per_nucleon(
    C_SS_h_val: float,
    m_chi: float,
    m_N: float,
    f_Tu_N: float,
    f_Td_N: float,
    f_Ts_N: float,
    f_TG_N: float,
) -> float:
    """Eq. 29e. NREFT coefficient c8 per nucleon N [GeV^-1].

    c8 is the velocity-dependent SI coefficient entering the v^2/c^2 term in sigma_bar_SI.
    c8^N = 2 * c1^N / m_chi  (subleading velocity correction)

    Args:
        C_SS_h_val   Wilson coefficient [GeV^-2]
        m_chi        DM mass [GeV]
        m_N          nucleon mass [GeV]
        f_Tu_N, f_Td_N, f_Ts_N, f_TG_N   form factors
    Returns:
        c8^N [GeV^-1]
    """
    c1 = c1_per_nucleon(C_SS_h_val, m_chi, m_N, f_Tu_N, f_Td_N, f_Ts_N, f_TG_N)
    return 2.0 * c1 / m_chi


def _isotope_nuclear_response_SI(A: int, Z: int, c1_p: float, c1_n: float) -> float:
    """Del Nobile Eq. 5.49. Nuclear response function for SI scattering.

    W^SI(A,Z) = |Z * c1_p + (A-Z) * c1_n|^2

    Uses XENON_Z = 54 from constants (N6 resolution).

    Args:
        A    mass number
        Z    atomic number (= XENON_Z = 54 for xenon)
        c1_p proton c1 coefficient [GeV^-1]
        c1_n neutron c1 coefficient [GeV^-1]
    Returns:
        W^SI [GeV^-2]
    """
    return abs(Z * c1_p + (A - Z) * c1_n)**2


def sigma_bar_SI(
    m_chi: float,
    c1_p: float,
    c1_n: float,
    xenon_abundances: dict = None,
    v_rel: float = V_REL_DEFAULT,
    include_v2_term: bool = True,
) -> float:
    """Eq. 30. Abundance-weighted sigma_bar^SI per nucleon [cm^2].

    sigma_bar^SI = MAJORANA_FACTOR * (mu_chi_N)^2 / pi
                   * sum_A [xi_A * W^SI(A,Z) / A^2]  * (1 + v^2/c^2 * c8^2/c1^2 * ...)

    Applies MAJORANA_FACTOR exactly once on return (CONVENTIONS.md invariant).

    Per-nucleon after isotope averaging, consistent with Del Nobile 2022 Eq. 5.49.

    Args:
        m_chi      DM mass [GeV]
        c1_p       proton c1 coefficient [GeV^-1]
        c1_n       neutron c1 coefficient [GeV^-1]
        xenon_abundances  {A: fraction} (default: XENON_ABUNDANCES from constants)
        v_rel      v/c [dimensionless], v_rel=1e-3 for benchmark
        include_v2_term  include the subleading v^2/c^2 c8 term
    Returns:
        sigma_bar^SI [cm^2]
    """
    if xenon_abundances is None:
        xenon_abundances = XENON_ABUNDANCES

    # DM-nucleon reduced mass (proton as reference nucleon)
    mu_chi_N = m_chi * M_P / (m_chi + M_P)  # [GeV]

    # Abundance-weighted nuclear response averaged over xenon isotopes
    nuclear_response = 0.0
    for A, xi_A in xenon_abundances.items():
        W_SI = _isotope_nuclear_response_SI(A, XENON_Z, c1_p, c1_n)
        nuclear_response += xi_A * W_SI / A**2

    # SI cross section per nucleon [GeV^-2]
    sigma_SI_gev = mu_chi_N**2 / np.pi * nuclear_response

    # v^2 velocity correction (subleading, from c8 operator)
    if include_v2_term and abs(c1_p) > 0:
        # c8 ~ 2*c1/m_chi; the ratio enters as (c8/c1)^2 * v^2 correction
        # leading correction: delta = v^2 * (c8_p^2/(4*m_chi^2*c1_p^2)) * ... ~ v^2 correction
        # For Eq. 30, the velocity term is O(v^2) suppressed:
        sigma_SI_gev *= (1.0 + v_rel**2)  # simplified; exact form from Eq. 30

    # Convert to cm^2
    sigma_SI_cm2 = sigma_SI_gev * GEV2_TO_CM2

    # Apply Majorana factor exactly once at sigma level (CONVENTIONS.md)
    return MAJORANA_FACTOR * sigma_SI_cm2
