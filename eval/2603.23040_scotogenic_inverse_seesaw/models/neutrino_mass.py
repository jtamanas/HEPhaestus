"""
One-loop neutrino mass in the scotogenic inverse seesaw model.
arXiv:2603.23040, Eqs. 14a-b and 15.
"""

import numpy as np
from numpy.typing import NDArray
from typing import Optional, Tuple


def loop_lambda_r(m_phi: float, m_chi_r: float) -> float:
    """Eq. 14b. Loop factor Lambda_r [GeV^2].

    Lambda_r = m_chi_r^3 / (m_phi^2 - m_chi_r^2) * ln(m_phi^2 / m_chi_r^2) / (16 pi^2)

    (Sum over all UF,k2 mixing elements is handled in lambda_vector.)

    Args:
        m_phi   [GeV]: scalar singlet mass m_phi_r
        m_chi_r [GeV]: mass eigenvalue m_chi_r (physical |X_r|)
    Returns:
        Lambda_r [GeV^2] (dimensionless combination; actual units depend on convention)
    """
    # Eq. 14b: Lambda_r = (1/(16 pi^2)) * m_chi^3 / (m_phi^2 - m_chi^2) * ln(m_phi^2/m_chi^2)
    prefactor = 1.0 / (16.0 * np.pi**2)
    m_chi_sq = m_chi_r**2
    m_phi_sq = m_phi**2
    if abs(m_phi_sq - m_chi_sq) < 1e-30:
        # L'Hopital limit (mass degenerate)
        return prefactor * (1.0 / m_chi_r)
    log_term = np.log(m_phi_sq / m_chi_sq)
    return prefactor * m_chi_r**3 / (m_phi_sq - m_chi_sq) * log_term


def lambda_vector(
    m_phi_triplet: Tuple[float, float, float],
    physical_masses_chi: Tuple[float, float, float],
    UF: NDArray,
) -> NDArray:
    """Vector of effective loop factors Lambda_r for r = 1,2,3 [GeV^2].

    Eq. 14b summed over fermion mass eigenstates k:
      Lambda_r = (1/(16 pi^2)) * sum_k |U_F,k2|^2 * m_chi_k^3 / (m_phi_r^2 - m_chi_k^2)
                 * ln(m_phi_r^2 / m_chi_k^2)

    Here |U_F,k2|^2 is the |second-column| mixing element (k=row, column 1 in 0-indexed).

    Args:
        m_phi_triplet       (m_phi1, m_phi2, m_phi3) [GeV]
        physical_masses_chi (m_chi1, m_chi2, m_chi3) [GeV]
        UF                  3x3 mixing matrix from mixing_matrix_UF
    Returns:
        Lambda [GeV^2] of shape (3,)
    """
    Lambda = np.zeros(3)
    prefactor = 1.0 / (16.0 * np.pi**2)
    for r, m_phi in enumerate(m_phi_triplet):
        m_phi_sq = m_phi**2
        total = 0.0
        for k, m_chi in enumerate(physical_masses_chi):
            u_k2_sq = UF[k, 1]**2   # column index 1 = second mass eigenstate (0-indexed)
            m_chi_sq = m_chi**2
            denom = m_phi_sq - m_chi_sq
            if abs(denom) < 1e-30:
                total += u_k2_sq / m_chi
            else:
                total += u_k2_sq * m_chi**3 / denom * np.log(m_phi_sq / m_chi_sq)
        Lambda[r] = prefactor * total
    return Lambda


def neutrino_mass_matrix(y_phi: NDArray, Lambda: NDArray) -> NDArray:
    """Eq. 14a. Neutrino mass matrix M^nu [eV].

    M^nu_ij = sum_r y_phi_ir * Lambda_r * y_phi_jr

    In matrix form: M^nu = y_phi @ diag(Lambda) @ y_phi^T

    Args:
        y_phi   (3,3) complex Yukawa coupling matrix [dimensionless]
        Lambda  (3,) loop factor vector [GeV^2]
    Returns:
        M_nu (3,3) complex matrix [eV] (note: Lambda in GeV^2, y_phi dim-less,
        so M_nu ~ GeV^2 — caller must apply eV conversion if needed)
    """
    return y_phi @ np.diag(Lambda) @ y_phi.T


def casas_ibarra_yukawa(
    m_nu_diag: NDArray,
    U_PMNS: NDArray,
    Lambda: NDArray,
    R: Optional[NDArray] = None,
) -> NDArray:
    """Eq. 15. Casas-Ibarra Yukawa coupling matrix y_phi.

    y_phi = U_PMNS^* @ sqrt(diag(m_nu)) @ R^T @ sqrt(diag(1/Lambda))

    R=I_3 is binding for all three BPs (brainstorm §0 S1).
    Any override must be documented in the caller.

    Args:
        m_nu_diag  (3,) neutrino mass eigenvalues [same units as Lambda^-1/2 * m_nu^1/2]
        U_PMNS     (3,3) complex PMNS matrix
        Lambda     (3,) loop factors [GeV^2]
        R          (3,3) complex rotation matrix; defaults to I_3
    Returns:
        y_phi  (3,3) complex Yukawa matrix [dimensionless if units consistent]
    """
    if R is None:
        R = np.eye(3, dtype=complex)

    # sqrt(diag(m_nu)) — handle zero masses
    sqrt_m_nu = np.diag(np.sqrt(np.abs(m_nu_diag)).astype(complex))

    # sqrt(diag(1/Lambda))
    sqrt_inv_Lambda = np.diag(1.0 / np.sqrt(np.abs(Lambda)).astype(complex))

    y_phi = U_PMNS.conj() @ sqrt_m_nu @ R.T @ sqrt_inv_Lambda
    return y_phi
