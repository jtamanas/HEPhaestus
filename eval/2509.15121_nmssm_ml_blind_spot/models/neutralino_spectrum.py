"""
NMSSM neutralino mass matrix and diagonalization.
arXiv:2509.15121, Eqs. (3)-(5).

The 5×5 neutralino mass matrix is written in the weak eigenstate basis
    psi^0 = (B~, W~^3, H~_d^0, H~_u^0, S~)
(Bino, neutral Wino, down-Higgsino, up-Higgsino, Singlino).

SLHA-1 convention (binding per plan):
  - scipy.linalg.eigh is used (NOT np.linalg.eigh); eigh returns real
    eigenvalues in ascending algebraic order and a real orthogonal matrix O
    such that M = O diag(lambda_i) O^T.
  - Physical masses are |lambda_i|.
  - Signs of lambda_i ARE tracked and propagated into couplings.
    The signed m_chi1 enters the Eq. (7) denominator (see blind_spot_identity.py).
  - Returned arrays are sorted by |lambda_i| ascending, carrying signs.

Note on scipy.linalg.eigh vs np.linalg.eigh:
  scipy.linalg.eigh is used (overrides brainstorm §3 docstring text that
  mentioned np.linalg.eigh) because scipy.linalg.eigh guarantees the
  LAPACK dsyev driver on all platforms, giving reproducible sign conventions.
"""

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eigh
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, G1_SM, G2_SM


def neutralino_mass_matrix(
    M1: float,
    M2: float,
    mu_eff: float,
    tan_beta: float,
    lambda_: float,
    kappa: float,
    vS: float,
    v: float = V_H,
    g1: float = G1_SM,
    g2: float = G2_SM,
) -> NDArray:
    """
    NMSSM neutralino 5×5 mass matrix in the basis (B~, W~^3, H~_d^0, H~_u^0, S~).
    arXiv:2509.15121, Eq. (3).

    The symmetric real matrix M_chi is:

        M_chi = [ M1           0        -cβ sW mZ   sβ sW mZ    0         ]
                [ 0            M2        cβ cW mZ   -sβ cW mZ   0         ]
                [ -cβ sW mZ   cβ cW mZ    0          -μ_eff     -λ vu      ]
                [ sβ sW mZ   -sβ cW mZ   -μ_eff       0         -λ vd      ]
                [ 0            0         -λ vu        -λ vd      2κ vS      ]

    where  sW = sin θ_W,  cW = cos θ_W,  sβ = sin β,  cβ = cos β,
           vu = v sin β,  vd = v cos β,  mZ = M_Z/2 (off-diagonal element).

    Entries follow from the NMSSM superpotential W ⊃ λ S H_u H_d + κ/3 S³
    and the soft-breaking sector; see Eq. (3) and surrounding text.

    Parameters
    ----------
    M1        : float — bino soft mass [GeV], signed per SLHA-1
    M2        : float — wino soft mass [GeV], signed per SLHA-1
    mu_eff    : float — effective higgsino mass λ vS [GeV], signed
    tan_beta  : float — tan β = vu/vd > 0 (dimensionless)
    lambda_   : float — NMSSM superpotential coupling λ (dimensionless)
    kappa     : float — NMSSM self-coupling κ (dimensionless)
    vS        : float — singlet VEV [GeV] (related to mu_eff by μ_eff = λ vS)
    v         : float — Higgs VEV v = sqrt(vu²+vd²) [GeV] (default V_H=246.22)
    g1        : float — SM-normalized U(1)_Y coupling g1 (default G1_SM=0.3574)
    g2        : float — SM-normalized SU(2)_L coupling g2 (default G2_SM=0.6517)

    Returns
    -------
    M : ndarray (5,5) — real-symmetric neutralino mass matrix [GeV]
    """
    beta = np.arctan(tan_beta)
    sin_beta = np.sin(beta)
    cos_beta = np.cos(beta)

    # Higgs component VEVs
    vu = v * sin_beta   # up-type Higgs VEV [GeV]
    vd = v * cos_beta   # down-type Higgs VEV [GeV]

    # Weinberg angle from gauge couplings (tree-level)
    # sin^2(theta_W) = g1^2 / (g1^2 + g2^2)
    g_sq = g1**2 + g2**2
    sW = g1 / np.sqrt(g_sq)   # sin theta_W
    cW = g2 / np.sqrt(g_sq)   # cos theta_W

    # Z-mass off-diagonal structure: mZ_entry = (g/2) * v * ...
    # The off-diagonal Bino-Higgsino entries are -(1/2)*g1*vd and +(1/2)*g1*vu
    # The off-diagonal Wino-Higgsino entries are +(1/2)*g2*vd and -(1/2)*g2*vu
    # These match the form: -mZ*sin(theta_W)*cos(beta), etc.
    half_g1_vd = -0.5 * g1 * vd   # M_{13}: Bino–Hd entry
    half_g1_vu = +0.5 * g1 * vu   # M_{14}: Bino–Hu entry
    half_g2_vd = +0.5 * g2 * vd   # M_{23}: Wino–Hd entry
    half_g2_vu = -0.5 * g2 * vu   # M_{24}: Wino–Hu entry

    # Higgsino–Singlino off-diagonal entries: -lambda * vu and -lambda * vd
    lam_vu = -lambda_ * vu   # M_{35}: Hd–Singlino
    lam_vd = -lambda_ * vd   # M_{45}: Hu–Singlino (note: different sign per NMSSM convention)

    # Singlino mass: 2 kappa vS
    m_singlino = 2.0 * kappa * vS

    M = np.array([
        [M1,          0.0,       half_g1_vd, half_g1_vu, 0.0      ],
        [0.0,         M2,        half_g2_vd, half_g2_vu, 0.0      ],
        [half_g1_vd,  half_g2_vd, 0.0,       -mu_eff,    lam_vu   ],
        [half_g1_vu,  half_g2_vu, -mu_eff,    0.0,        lam_vd   ],
        [0.0,         0.0,        lam_vu,     lam_vd,     m_singlino],
    ], dtype=float)

    return M


def diagonalize_neutralino(
    M1: float,
    M2: float,
    mu_eff: float,
    tan_beta: float,
    lambda_: float,
    kappa: float,
    vS: float,
    v: float = V_H,
    g1: float = G1_SM,
    g2: float = G2_SM,
) -> tuple:
    """
    Diagonalize the NMSSM neutralino mass matrix in SLHA-1 convention.
    arXiv:2509.15121, Eqs. (3)-(5).

    Uses scipy.linalg.eigh (NOT np.linalg.eigh; see module docstring for
    rationale). eigh returns signed real eigenvalues in ascending algebraic
    order and a real orthogonal matrix N such that M = N diag(lambda_i) N^T.

    SLHA-1 sign-tracking convention (binding):
      - Physical masses are |lambda_i|, sorted ascending.
      - signs[i] = sign(lambda_i) tracks the signed eigenvalue.
      - Signed mass: m_chi_i_signed = masses_abs[i] * signs[i]
      - The signed m_chi1 is used in Eq. (7) via:
            m_chi1_signed = masses_abs[0] * signs[0]
      - The mixing matrix N is real orthogonal; its columns are reordered
        to match the ascending-|eigenvalue| sorting.

    Parameters
    ----------
    M1, M2    : float — bino/wino soft masses [GeV], signed
    mu_eff    : float — effective higgsino mass [GeV], signed
    tan_beta  : float — tan β > 0
    lambda_   : float — NMSSM superpotential coupling λ
    kappa     : float — NMSSM self-coupling κ
    vS        : float — singlet VEV [GeV]
    v         : float — Higgs VEV [GeV] (default V_H)
    g1        : float — SM-normalized U(1)_Y coupling (default G1_SM)
    g2        : float — SM-normalized SU(2)_L coupling (default G2_SM)

    Returns
    -------
    masses_abs : ndarray (5,) — |m_chi_i| in ascending order [GeV]
    signs      : ndarray (5,) int — sign(lambda_i) in {+1, -1} for each state
    N          : ndarray (5,5) — real orthogonal mixing matrix; column i
                 is the mass eigenstate corresponding to masses_abs[i]
    """
    M = neutralino_mass_matrix(M1, M2, mu_eff, tan_beta, lambda_, kappa, vS,
                                v=v, g1=g1, g2=g2)

    # eigh returns eigenvalues in ascending algebraic order (NOT by |eigenvalue|)
    # and eigenvectors as columns.
    eigenvalues, eigenvectors = eigh(M)

    # Sort by |eigenvalue| ascending to get mass ordering
    abs_evals = np.abs(eigenvalues)
    sort_idx = np.argsort(abs_evals)

    masses_abs = abs_evals[sort_idx]
    signs = np.sign(eigenvalues[sort_idx]).astype(int)
    # Handle exact zero eigenvalues (shouldn't occur in physical spectrum)
    signs[signs == 0] = 1
    N = eigenvectors[:, sort_idx]

    return masses_abs, signs, N


def bino_higgsino_fractions(N: NDArray, i: int = 0) -> dict:
    """
    Bino, wino, higgsino, singlino composition fractions of the i-th neutralino.
    arXiv:2509.15121, notation of Sec. III.

    In the (B~, W~^3, H~_d^0, H~_u^0, S~) basis:
        Z_B = |N[0, i]|^2             (bino fraction)
        Z_W = |N[1, i]|^2             (wino fraction)
        Z_H = |N[2, i]|^2 + |N[3, i]|^2  (higgsino fraction = Hd + Hu)
        Z_S = |N[4, i]|^2             (singlino fraction)

    The sum Z_B + Z_W + Z_H + Z_S = 1 to machine precision (orthonormality of N).

    Parameters
    ----------
    N : ndarray (5,5) — orthogonal mixing matrix from diagonalize_neutralino
    i : int — mass eigenstate index (0 = LSP)

    Returns
    -------
    dict with keys 'Z_B', 'Z_W', 'Z_H', 'Z_S', all in [0, 1]
    """
    col = N[:, i]
    Z_B = float(col[0] ** 2)
    Z_W = float(col[1] ** 2)
    Z_H = float(col[2] ** 2 + col[3] ** 2)
    Z_S = float(col[4] ** 2)
    return {"Z_B": Z_B, "Z_W": Z_W, "Z_H": Z_H, "Z_S": Z_S}
