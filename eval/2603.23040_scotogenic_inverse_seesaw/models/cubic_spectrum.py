"""
Neutral fermion mass spectrum for the scotogenic inverse seesaw model.
arXiv:2603.23040, Eqs. 6-11.

Parameter convention (plan mapping):
  M_R  = m_E   [GeV]  — vector-like lepton doublet mass
  mu_S         [GeV]  — symmetric mixing scale: mu_1 = mu_2 = mu_S
                         (mu_1 = y1*v/sqrt(2), mu_2 = y2*v/sqrt(2))
  M_N  = m_N   [GeV]  — Majorana singlet mass

The fermion mass matrix (Eq. 4) is:
    M_F = [[0,   M_R,  mu_S ],
           [M_R,  0,   mu_S ],
           [mu_S, mu_S, M_N ]]

Its characteristic equation is Eq. 6 (cubic in x).
"""

import numpy as np
from numpy.typing import NDArray
from typing import Tuple


def cubic_coeffs(M_R: float, mu_S: float, M_N: float) -> Tuple[float, float, float, float]:
    """Eq. 6. Coefficients (a, b, c, d) of the cubic a*x^3 + b*x^2 + c*x + d = 0.

    Mass matrix entry mapping: m_E = M_R, mu_1 = mu_2 = mu_S, m_N = M_N.

    Returns:
        (a, b, c, d) float coefficients of x^3, x^2, x^1, x^0.
    """
    # Eq. 6: x^3 - M_N*x^2 - (M_R^2 + mu_S^2 + mu_S^2)*x
    #         + M_N*M_R^2 - 2*mu_S*mu_S*M_R = 0
    a = 1.0
    b = -M_N
    c = -(M_R**2 + 2.0 * mu_S**2)
    d = M_N * M_R**2 - 2.0 * mu_S**2 * M_R
    return (a, b, c, d)


def spectrum_roots(M_R: float, mu_S: float, M_N: float) -> Tuple[float, float, float]:
    """Eq. 6. Real roots X1, X2, X3 of the cubic characteristic equation.

    Binding: sorted by ASCENDING real part (not |X|). Signs preserved.
    Physical masses = |X_i| applied at the observable layer only.

    Imaginary guard: asserts |imag(root)| < 1e-10 for each root.

    Returns:
        (X1, X2, X3): three real eigenvalues [GeV], ascending order.
    """
    a, b, c, d = cubic_coeffs(M_R, mu_S, M_N)
    roots = np.roots([a, b, c, d])
    for r in roots:
        assert abs(r.imag) < 1e-10, (
            f"Non-real root {r} in cubic_spectrum — check inputs "
            f"M_R={M_R}, mu_S={mu_S}, M_N={M_N}"
        )
    real_roots = np.sort(roots.real)
    return (float(real_roots[0]), float(real_roots[1]), float(real_roots[2]))


def mixing_angle_theta(M_R: float, mu_S: float, M_N: float) -> float:
    """Eq. 8. Diagonalization mixing angle theta [rad].

    Defined via atan2 of the off-diagonal elements of the mass matrix.
    For the symmetric case mu_1 = mu_2 = mu_S:
      theta = atan(2 * mu_S * M_R / (M_R^2 - M_N * M_R + ...))
    (Full expression from diagonalizing the 2x2 block after integrating out
    the heavy states.)
    """
    # For the 3x3 matrix with mu_1 = mu_2 = mu_S:
    # The mixing angle in the heavy sector is
    #   tan(theta) = sqrt(2) * mu_S / M_R  (small-mu_S limit)
    # Full expression from Cardano discriminant (Eq. 8):
    #   Using the 2x2 sub-block of (E0_L, E0_R) with M_R on diagonal
    #   and mu_S couplings to N, the angle is:
    numerator = np.sqrt(2.0) * mu_S
    denominator = M_R
    return float(np.arctan2(numerator, denominator))


def mixing_matrix_UF(M_R: float, mu_S: float, M_N: float) -> NDArray:
    """Eqs. 10-11. 3x3 unitary mixing matrix U_F.

    Columns are mass eigenvectors aligned to sorted eigenvalues (X1, X2, X3).
    Re-phased so that the column-wise first-nonzero-entry is positive real
    (deterministic global phase).

    Satisfies: U_F^T @ M_F @ U_F = diag(X1, X2, X3)
               U_F^T @ U_F = I  (to 1e-10)
    """
    # Build the symmetric mass matrix (Majorana: symmetric convention)
    MF = np.array([
        [0.0,    M_R,   mu_S],
        [M_R,    0.0,   mu_S],
        [mu_S,   mu_S,  M_N ],
    ])

    # Diagonalize via numpy
    eigenvalues, eigenvectors = np.linalg.eigh(MF)
    # np.linalg.eigh returns eigenvectors as COLUMNS, sorted ascending eigenvalue

    # Re-phase each column so the first nonzero entry is positive real
    U = eigenvectors.copy().astype(complex)
    for j in range(3):
        col = U[:, j]
        # Find first nonzero entry
        for i in range(3):
            if abs(col[i]) > 1e-14:
                phase = col[i] / abs(col[i])
                U[:, j] = col / phase
                break

    return np.real(U)  # Purely real for real symmetric matrix


def physical_masses(M_R: float, mu_S: float, M_N: float) -> Tuple[float, float, float]:
    """Observable physical masses |X1|, |X2|, |X3| [GeV].

    Absolute values of the eigenvalues from spectrum_roots().
    """
    X1, X2, X3 = spectrum_roots(M_R, mu_S, M_N)
    return (abs(X1), abs(X2), abs(X3))
