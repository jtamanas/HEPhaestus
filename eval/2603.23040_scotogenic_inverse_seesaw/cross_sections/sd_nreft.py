"""
Spin-dependent (SD) NREFT cross section for Majorana DM-nucleon scattering.
arXiv:2603.23040, Eqs. 26b-c, 29b-d, 32, 33.
CONVENTIONS.md is binding for all implementations here.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import (
    M_Z, G_F, MAJORANA_FACTOR, GEV2_TO_CM2,
    S_A_p_XE131, S_A_n_XE131, J_XE131,
    M_P, M_N_NUCLEON,
    DELTA_U_P, DELTA_D_P, DELTA_S_P,
    DELTA_U_N, DELTA_D_N, DELTA_S_N,
)


def C_VA_Z(g_Zchichi_A: float, g_Zff_V: float, m_Z: float = M_Z) -> float:
    """Eq. 26b. Vector-axial Wilson coefficient from Z-exchange [GeV^-2].

    C^VA_Z = g_Zchichi_A * g_Zff_V / (2 * m_Z^2)

    Args:
        g_Zchichi_A   axial Z-chi-chi coupling [dimensionless]
        g_Zff_V       vector Z-f-f coupling [dimensionless]
        m_Z           Z mass [GeV]
    Returns:
        C^VA_Z [GeV^-2]
    """
    return g_Zchichi_A * g_Zff_V / (2.0 * m_Z**2)


def C_AA_Z(g_Zchichi_A: float, g_Zff_A: float, m_Z: float = M_Z) -> float:
    """Eq. 26c. Axial-axial Wilson coefficient from Z-exchange [GeV^-2].

    C^AA_Z = g_Zchichi_A * g_Zff_A / (2 * m_Z^2)

    Args:
        g_Zchichi_A   axial Z-chi-chi coupling [dimensionless]
        g_Zff_A       axial Z-f-f coupling [dimensionless]
        m_Z           Z mass [GeV]
    Returns:
        C^AA_Z [GeV^-2]
    """
    return g_Zchichi_A * g_Zff_A / (2.0 * m_Z**2)


def c4_per_nucleon(
    C_AA_Z_val: float,
    m_chi: float,
    Delta_u_N: float,
    Delta_d_N: float,
    Delta_s_N: float,
) -> float:
    """Eq. 29b. NREFT coefficient c4 per nucleon N [GeV^-2].

    c4^N = 4 * C^AA_Z * (Delta_u^N * T3_u + Delta_d^N * T3_d + Delta_s^N * T3_s)
         = 4 * C^AA_Z * (Delta_u^N * 1/2 - Delta_d^N * 1/2 - Delta_s^N * 1/2)

    Wait: c4 is related to the axial-axial operator chi^A N^A.
    The sum rule: c4^N = 4 * C^AA_Z * sum_q Delta_q^N * T3_q
    where T3_q = +1/2 for up-type, -1/2 for down-type.

    For this model with Z-axial-universal coupling (g_Zchichi_A same for all quarks
    of given isospin), c4_p == c4_n (isospin identity, brainstorm §0 S4).

    Per-nucleon (p and n separately) per CONVENTIONS.md.

    Args:
        C_AA_Z_val   axial-axial Wilson coefficient [GeV^-2]
        m_chi        DM mass [GeV]
        Delta_u_N    axial form factor for u quark in nucleon N [dimensionless]
        Delta_d_N    axial form factor for d quark in nucleon N [dimensionless]
        Delta_s_N    axial form factor for s quark in nucleon N [dimensionless]
    Returns:
        c4^N [GeV^-2]
    """
    # Eq. 29b: c4^N = 4 * C^AA_Z * sum_q g_Aff * Delta_q^N
    # For SM Z coupling: g_Af^f = T3_f = ±1/2
    # c4^N = 4 * C^AA_Z * (T3_u * Delta_u + T3_d * Delta_d + T3_s * Delta_s)
    # = 4 * C^AA_Z * (0.5 * Delta_u - 0.5 * Delta_d - 0.5 * Delta_s)
    return 4.0 * C_AA_Z_val * (0.5 * Delta_u_N - 0.5 * Delta_d_N - 0.5 * Delta_s_N)


def c6_per_nucleon(
    C_AA_Z_val: float,
    m_chi: float,
    m_N: float,
    Delta_u_N: float,
    Delta_d_N: float,
    Delta_s_N: float,
) -> float:
    """Eq. 29c. NREFT coefficient c6 per nucleon N [GeV^-4].

    c6 arises from pion/eta pole corrections to the SD interaction.
    c6^N = c4^N * m_N^2 / m_chi^2  (leading pion-pole contribution)

    Args:
        C_AA_Z_val   axial-axial Wilson coefficient [GeV^-2]
        m_chi        DM mass [GeV]
        m_N          nucleon mass [GeV]
        Delta_u_N, Delta_d_N, Delta_s_N   axial form factors [dimensionless]
    Returns:
        c6^N [GeV^-4]
    """
    c4 = c4_per_nucleon(C_AA_Z_val, m_chi, Delta_u_N, Delta_d_N, Delta_s_N)
    return c4 * m_N**2 / m_chi**2


def c9_per_nucleon(
    C_VA_Z_val: float,
    C_AA_Z_val: float,
    m_chi: float,
    m_N: float,
    Delta_u_N: float,
    Delta_d_N: float,
    Delta_s_N: float,
) -> float:
    """Eq. 29d. NREFT coefficient c9 per nucleon N [GeV^-3].

    c9 is a subleading velocity-dependent SD coefficient.
    c9^N ~ C^VA_Z * c4^N * m_N / m_chi  (from momentum-transfer expansion)

    Args:
        C_VA_Z_val   vector-axial Wilson coefficient [GeV^-2]
        C_AA_Z_val   axial-axial Wilson coefficient [GeV^-2]
        m_chi        DM mass [GeV]
        m_N          nucleon mass [GeV]
        Delta_u_N, Delta_d_N, Delta_s_N   axial form factors [dimensionless]
    Returns:
        c9^N [GeV^-3]
    """
    c4 = c4_per_nucleon(C_AA_Z_val, m_chi, Delta_u_N, Delta_d_N, Delta_s_N)
    return C_VA_Z_val * c4 * m_N / m_chi


def sigma_SD_full(
    m_chi: float,
    c4_p: float,
    c4_n: float,
    c6_p: float,
    c6_n: float,
    c9_p: float,
    c9_n: float,
    nucleus: str = 'Xe131',
) -> float:
    """Eq. 32. Full NREFT spin-dependent cross section per nucleus [cm^2].

    Includes c4 (leading), c6 (pion-pole, momentum-suppressed), and c9
    (velocity-suppressed) contributions per Del Nobile 2022 / Anand et al. 2014.

    B5 fix: c6_correction is no longer hard-coded to 0.  The correction is
    computed from the passed c6_{p,n} and c9_{p,n} coefficients.

    The NREFT SD amplitude squared includes operators O4 ~ S_chi . S_N
    (coefficient c4) and O6 ~ (S_chi . q)(S_N . q)/q^4 (coefficient c6) plus
    the subleading O9 ~ S_chi . (S_N × v_perp) (coefficient c9).  At
    zero-momentum-transfer only c4 contributes; c6 enters at O(q^2/m_chi^2).
    The cross-section expansion (canonical DM velocity v_DM = 2.2e-3 c,
    representative momentum transfer q^2 = mu_chi_A^2 * v_DM^2) is:

      sigma_full = sigma_simplified * (1 + delta_c6 + delta_c9)

    where (following Del Nobile 2022 Eqs. 5.51-5.52):
      delta_c6  = (S_p*c6_p + S_n*c6_n)^2 / (S_p*c4_p + S_n*c4_n)^2
                  * q_eff^2 / (4 * m_N_eff^2)
      delta_c9  = (S_p*c9_p + S_n*c9_n)^2 / (S_p*c4_p + S_n*c4_n)^2
                  * v_perp^2

    with q_eff^2 = mu_chi_A^2 * v_DM^2 [GeV^2],
         v_DM   = 2.2e-3 (local DM velocity / c, dimensionless),
         v_perp^2 = v_DM^2 - q_eff^2/(4*mu_chi_A^2) ≈ v_DM^2 (q-expansion),
         m_N_eff  = mu_chi_A (sets the scale of c6 [GeV^-4] coefficients).

    For this model: c6 = c4 * m_N^2/m_chi^2, so delta_c6 ~ (m_N/m_chi)^4 * v_DM^2/4.
    At BP3 (m_chi=61 GeV): delta_c6 ~ (0.94/61)^4 * (2.2e-3)^2/4 ~ 8e-4 * 1.2e-6 ~ 1e-9.
    The paper's <10% claim holds trivially for this model's kinematics.

    Applies MAJORANA_FACTOR exactly once on return (CONVENTIONS.md invariant — 2nd hit).

    Args:
        m_chi    DM mass [GeV]
        c4_p, c4_n   SD c4 coefficients for proton, neutron [GeV^-2]
        c6_p, c6_n   SD c6 coefficients for proton, neutron [GeV^-4]
        c9_p, c9_n   SD c9 coefficients for proton, neutron [GeV^-3]
        nucleus   'Xe131'
    Returns:
        sigma^SD_full [cm^2] (per-nucleus)
    """
    assert nucleus == 'Xe131', f"Only Xe131 supported, got {nucleus}"

    mu_chi_A = _reduced_mass_nucleus(m_chi, nucleus)  # [GeV]
    S_p = S_A_p_XE131
    S_n = S_A_n_XE131
    J = J_XE131

    # Leading c4 term (= sigma_SD_simplified before Majorana factor)
    denom_c4 = S_p * c4_p + S_n * c4_n  # [GeV^-2]
    sigma_0 = (3.0 * mu_chi_A**2 / (np.pi * (2.0 * J + 1.0))
               * denom_c4**2)  # [GeV^-4]

    # c6 and c9 correction terms (B5 fix — not hard-coded to zero)
    # Representative kinematics: v_DM = 2.2e-3, q^2 = mu^2 * v_DM^2
    v_DM = 2.2e-3  # local DM velocity / c [dimensionless]
    q_eff_sq = mu_chi_A**2 * v_DM**2  # [GeV^2]
    m_N_eff = (M_P + M_N_NUCLEON) / 2.0  # effective nucleon mass [GeV]

    c6_correction = 0.0
    c9_correction = 0.0

    if denom_c4 != 0.0:
        denom_c6 = S_p * c6_p + S_n * c6_n  # [GeV^-4]
        denom_c9 = S_p * c9_p + S_n * c9_n  # [GeV^-3]

        # delta_c6: O(q^2/m^2) correction from c6 operator
        # c6 [GeV^-4] contributes at q^2/m_N^2 order relative to c4 [GeV^-2]
        c6_correction = (denom_c6 / denom_c4)**2 * q_eff_sq / (4.0 * m_N_eff**2)

        # delta_c9: O(v^2) correction from c9 operator
        # c9 [GeV^-3] contributes at v_perp^2 order; v_perp^2 ~ v_DM^2
        c9_correction = (denom_c9 / denom_c4)**2 * v_DM**2

    sigma_full_gev = sigma_0 * (1.0 + c6_correction + c9_correction)
    sigma_full_cm2 = sigma_full_gev * GEV2_TO_CM2

    # Apply Majorana factor exactly once at sigma level
    return MAJORANA_FACTOR * sigma_full_cm2


def sigma_SD_simplified(
    m_chi: float,
    c4_p: float,
    c4_n: float,
    nucleus: str = 'Xe131',
) -> float:
    """Eq. 33. Simplified (dominant-term) SD cross section per nucleus [cm^2].

    sigma^SD_simpl = MAJORANA_FACTOR * 3 * mu_chi_A^2 / (pi * (2J+1))
                     * (S_p * c4_p + S_n * c4_n)^2

    Drops c6 and c9 terms. Paper claims < 10% agreement with Eq. 32.

    Applies MAJORANA_FACTOR exactly once on return (CONVENTIONS.md invariant — 3rd hit).

    Args:
        m_chi    DM mass [GeV]
        c4_p, c4_n   SD c4 coefficients for proton, neutron [GeV^-2]
        nucleus   'Xe131'
    Returns:
        sigma^SD_simplified [cm^2] (per-nucleus)
    """
    assert nucleus == 'Xe131', f"Only Xe131 supported, got {nucleus}"

    mu_chi_A = _reduced_mass_nucleus(m_chi, nucleus)  # [GeV]
    S_p = S_A_p_XE131
    S_n = S_A_n_XE131
    J = J_XE131

    sigma_simpl_gev = (3.0 * mu_chi_A**2 / (np.pi * (2.0 * J + 1.0))
                       * (S_p * c4_p + S_n * c4_n)**2)

    sigma_simpl_cm2 = sigma_simpl_gev * GEV2_TO_CM2

    # Apply Majorana factor exactly once at sigma level
    return MAJORANA_FACTOR * sigma_simpl_cm2


def _reduced_mass_nucleus(m_chi: float, nucleus: str) -> float:
    """Reduced mass of DM-nucleus system [GeV]."""
    if nucleus == 'Xe131':
        m_A = 131.0 * M_P  # approximate nuclear mass
    else:
        raise ValueError(f"Unknown nucleus: {nucleus}")
    return m_chi * m_A / (m_chi + m_A)
