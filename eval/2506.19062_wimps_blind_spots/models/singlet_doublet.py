"""
Singlet-Doublet fermion dark matter model.
arXiv:2506.19062, Eqs. (1)-(11).

Lagrangian (Eq. 1):
  L = -1/2 m_S S^2 - m_D D_L D_R - y_1 D_L H S - y_2 D_R H~ S + h.c.

The neutral sector has a 3x3 mass matrix (Eq. 3) whose eigenstates are
chi_1 (DM), chi_2, chi_3. There is also a charged fermion psi^+/-.

Parameters:
  m_S    : singlet bare mass
  m_D    : doublet bare mass
  y_1    : Yukawa coupling 1
  y_2    : Yukawa coupling 2

Scan ranges (Eq. 11):
  m_S in [1, 5000] GeV
  m_D in [100, 5000] GeV
  y  in [1e-3, 10]        (with y_1 = y cos(theta), y_2 = y sin(theta))
  tan(theta) in [-20, 20]
"""

import numpy as np
from numpy.typing import NDArray

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_Z, M_H, M_W, SW2, A_U_Z, A_D_Z


def mass_matrix(m_S: float, m_D: float, y1: float, y2: float,
                v: float = V_H) -> NDArray:
    """
    Neutral fermion mass matrix (Eq. 3).

    Returns the 3x3 symmetric mass matrix M in the basis (S, D_L^0, D_R^0).
    Eigenvalues give physical masses m_chi1 < m_chi2 < m_chi3.
    The charged fermion mass is simply m_D.

    Parameters
    ----------
    m_S : float — singlet mass parameter [GeV]
    m_D : float — doublet mass parameter [GeV]
    y1  : float — Yukawa coupling y_1
    y2  : float — Yukawa coupling y_2
    v   : float — Higgs VEV [GeV]

    Returns
    -------
    M : ndarray, shape (3,3)
    """
    a = y1 * v / np.sqrt(2)
    b = y2 * v / np.sqrt(2)
    return np.array([
        [m_S, a,   b  ],
        [a,   0.0, m_D],
        [b,   m_D, 0.0],
    ])


def diagonalize(m_S: float, m_D: float, y1: float, y2: float,
                v: float = V_H) -> tuple[NDArray, NDArray]:
    """
    Diagonalize the neutral mass matrix.

    Returns
    -------
    masses : ndarray, shape (3,) — sorted physical masses (|eigenvalues|)
    U      : ndarray, shape (3,3) — unitary mixing matrix (columns = mass eigenstates)
    """
    M = mass_matrix(m_S, m_D, y1, y2, v)
    eigenvalues, U = np.linalg.eigh(M)
    # Sort by absolute value (lightest = DM candidate)
    idx = np.argsort(np.abs(eigenvalues))
    return np.abs(eigenvalues[idx]), U[:, idx]


def y1_y2_from_y_theta(y: float, theta: float) -> tuple[float, float]:
    """Convert (y, theta) parametrization to (y1, y2). Eq. (6)."""
    return y * np.cos(theta), y * np.sin(theta)


def coupling_h_chi1chi1(m_S: float, m_D: float, y: float, theta: float,
                        v: float = V_H) -> float:
    """
    Effective DM-Higgs coupling y_{h chi1 chi1} (Eq. 7, first expression).

    This is the coupling that enters the tree-level SI cross-section.
    The blind spot occurs when this coupling vanishes.

    Parameters
    ----------
    m_S, m_D : float — mass parameters [GeV]
    y        : float — overall Yukawa magnitude
    theta    : float — mixing angle [rad]
    v        : float — Higgs VEV [GeV]

    Returns
    -------
    y_h : float — effective h-chi1-chi1 coupling
    """
    y1, y2 = y1_y2_from_y_theta(y, theta)
    masses, U = diagonalize(m_S, m_D, y1, y2, v)
    m_chi1 = masses[0]

    # Numerator: -(sin(2theta) * m_D + m_chi1) * y^2 * v
    numerator = -(np.sin(2 * theta) * m_D + m_chi1) * y**2 * v

    # Denominator
    denominator = (m_D**2 + v**2 / 2.0 * y**2
                   + 2 * m_S * m_chi1 - 3 * m_chi1**2)

    if abs(denominator) < 1e-30:
        return 0.0
    return numerator / denominator


def coupling_Z_chi1chi1(m_S: float, m_D: float, y: float, theta: float,
                        v: float = V_H) -> float:
    """
    Effective DM-Z axial coupling y^A_{Z chi1 chi1} (Eq. 7, second expression).

    This enters the spin-dependent cross-section at tree level.

    Returns
    -------
    y_Z : float — effective Z-chi1-chi1 axial coupling
    """
    y1, y2 = y1_y2_from_y_theta(y, theta)
    masses, U = diagonalize(m_S, m_D, y1, y2, v)
    m_chi1 = masses[0]

    numerator = (-M_Z * v * y**2 * np.cos(2 * theta)
                 * (m_chi1**2 - m_D**2))

    denom_term1 = 2 * (m_chi1**2 - m_D**2)**2
    denom_term2 = v**2 * (2 * y**2 * np.sin(2 * theta) * m_chi1 * m_D
                          + y**2 * (m_chi1**2 + m_D**2))
    denominator = denom_term1 + denom_term2

    if abs(denominator) < 1e-30:
        return 0.0
    return numerator / denominator


def coupling_h_chi_ij_mixing(y1: float, y2: float,
                             U: NDArray, i: int, j: int) -> float:
    """
    DM-Higgs coupling via mixing matrix elements (Eq. 33 / Appendix A).

    y_{h N_i N_j} = (1/sqrt(2)) * (y1 * U[1,i]* U[0,j]* + y2 * U[2,j]* U[0,i]*)

    For real mixing matrix (symmetric M), this simplifies.
    """
    return (1.0 / np.sqrt(2)) * (y1 * U[1, i] * U[0, j]
                                  + y2 * U[2, j] * U[0, i])


def blind_spot_parameter(m_chi1: float, m_D: float, theta: float) -> float:
    """
    Blind spot condition parameter (Eq. 8).

    The tree-level SI cross-section vanishes when this equals zero:
      m_chi1 + m_D * sin(2*theta) = 0

    Returns the value of the blind-spot parameter.
    """
    return m_chi1 + m_D * np.sin(2 * theta)


def charged_fermion_mass(m_D: float) -> float:
    """Mass of the charged component psi^+/-. Equal to m_D at tree level."""
    return m_D


def scan_ranges() -> dict:
    """Parameter scan ranges from Eq. (11)."""
    return {
        "m_S": (1.0, 5000.0),          # GeV
        "m_D": (100.0, 5000.0),        # GeV
        "y": (1e-3, 10.0),
        "tan_theta": (-20.0, 20.0),
    }


def is_viable(m_chi1: float, m_D: float) -> bool:
    """
    Basic viability checks.
    - DM must be lightest neutral state (guaranteed by sorting)
    - Charged fermion (m_D) must be heavier than ~100 GeV (LEP bound)
    - Z/h invisible width: m_chi1 > ~45 GeV (approx)
    """
    return m_D > 100.0 and m_chi1 > 45.0
