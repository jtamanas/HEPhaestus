"""Singlet-doublet fermion DM — analytic spectrum module.

Basis: (s0, PsiDd0, PsiDu0), matching the SARAH ordering declared in the
modelspec yaml (ewsb.mixings.weyls). The yh1 Yukawa (conj[H].FS.PsiDu) couples
s0↔PsiDu0; yh2 (H.FS.PsiDd) couples s0↔PsiDd0.

Mass matrix (SARAH's CalculateMFChi, in this basis — NOT the paper's Eq. 3,
which has all-plus off-diagonals; see _mass_matrix for the sign provenance):
    M = [[MS,  -b,    a    ],
         [-b,   0,   -MPsi ],
         [a,  -MPsi,  0    ]]
where a = yh1 * v / sqrt(2), b = yh2 * v / sqrt(2). Same eigenvalues as the
paper's matrix; eigenvector component signs differ, and the UFO vertices
require SARAH's.

Charged Dirac sector: m_chi± = |MPsi|, UMMIX = UPMIX = [[1]].

PDG IDs are fixed by SARAH's assignment (see
~/.local/share/hephaestus/models/singlet_doublet/sarah_output/UFO/SingletDoublet/particles.py):
    Chi1=9958431, Chi2=9956206, Chi3=9979223, ChiM=9984071.
"""

from __future__ import annotations

import numpy as np

# _common is loaded dynamically: the analytic_models package is loaded via
# spec_from_file_location, so `analytic_models/` is not on sys.path and
# ``from _common import V_H`` does not resolve. This mirrors the pattern in
# compile_model._load_config_helpers and every sibling spheno-build script.
import importlib.util as _ilu
from pathlib import Path as _P
_here = _P(__file__).resolve().parent
_spec = _ilu.spec_from_file_location("_common", _here / "_common.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
V_H = _mod.V_H

# SARAH-assigned PDG IDs (frozen; a test re-reads particles.py and asserts match).
SINGLET_DOUBLET_PDG_IDS = {
    "Chi1": 9958431,
    "Chi2": 9956206,
    "Chi3": 9979223,
    "ChiM": 9984071,
}

# SM PDG IDs we echo for downstream consumers.
_SM_MASS_BLOCK = {
    23: 91.1876,      # Z
    24: 80.377,       # W
    25: 125.25,       # h
}


def _mass_matrix(MS: float, MPsi: float, yh1: float, yh2: float,
                 v: float = V_H) -> np.ndarray:
    # Sign convention: this is SARAH's OWN matrix, transcribed from the
    # generated CalculateMFChi (TreeLevelMasses_SingletDoublet.f90:767-775,
    # PhaseFS = 1):
    #     mat(1,2) = -yh2*v/sqrt(2)   (H.FS.PsiDd through the SU(2) epsilon)
    #     mat(1,3) = +yh1*v/sqrt(2)   (conj[H].FS.PsiDu, direct contraction)
    #     mat(2,3) = -MPsi            (PsiDu.PsiDd through the epsilon)
    # The UFO vertices (e.g. GC_99 ~ yh2*ZN12 - yh1*ZN13) were generated
    # from the same Lagrangian, so ZNMIX must diagonalise THIS matrix.
    # Diagonalising the paper-style all-plus matrix instead (the pre-2026-07
    # behaviour) yields eigenvector rows whose 2nd component has the wrong
    # sign — an internally inconsistent card whose symptom is a spurious
    # sigma_SI blind spot at theta = +/- pi/4 (where yh1 = +/- yh2) instead
    # of the true theta = -0.152. Eigenvalues equal the paper matrix's
    # (similar via diag(1,-1,1)), so masses and paper Eq. 8 are unchanged.
    a = yh1 * v / np.sqrt(2.0)
    b = yh2 * v / np.sqrt(2.0)
    return np.array([
        [MS,  -b,    a    ],
        [-b,  0.0,  -MPsi ],
        [a,  -MPsi,  0.0  ],
    ], dtype=float)


def compute(spec: dict, params: dict) -> dict:
    """Run the analytic spectrum for singlet-doublet.

    Raises
    ------
    ValueError : invalid parameter (e.g. MPsi < 0).
    numpy.linalg.LinAlgError : diagonalisation failed.
    """
    MS   = float(params["MS"])
    MPsi = float(params["MPsi"])
    yh1  = float(params["yh1"])
    yh2  = float(params["yh2"])
    if MPsi < 0.0:
        raise ValueError(f"MPsi must be >= 0, got {MPsi}")

    M = _mass_matrix(MS, MPsi, yh1, yh2)
    eigvals, U = np.linalg.eigh(M)
    idx = np.argsort(np.abs(eigvals))
    signed = eigvals[idx]
    masses = np.abs(signed)
    U_sorted = U[:, idx]
    ZN = U_sorted.T  # rows=mass eigenstate, cols=interaction (SARAH convention)

    # Majorana phase: the SLHA carries |m| in MASS, so ZN must satisfy
    # ZN . M . ZN^T = diag(+|m|). A real orthogonal ZN can only produce the
    # SIGNED eigenvalue on the diagonal; a negative-eigenvalue row must be
    # multiplied by i (then (i z) M (i z)^T = -z M z^T = +|m|), i.e. that
    # row belongs in IMZNMIX with the ZNMIX row zero. This is exactly what
    # SARAH's own SPheno code does (TreeLevelMasses CalculateMFChi:
    # ``ZN(i1,:) = (0,1)*ZNa(i1,:)`` for Eig < 0). Emitting |m| with a
    # purely real ZN gives every vertex linear in that row a wrong phase:
    # it corrupted the chi2-exchange interference in chi1 chi1 -> Zh
    # (Omega h^2 = 0.0717 instead of 0.2916 at the canonical benchmark).
    is_neg = signed < 0.0

    masses_out = {
        SINGLET_DOUBLET_PDG_IDS["Chi1"]: float(masses[0]),
        SINGLET_DOUBLET_PDG_IDS["Chi2"]: float(masses[1]),
        SINGLET_DOUBLET_PDG_IDS["Chi3"]: float(masses[2]),
        SINGLET_DOUBLET_PDG_IDS["ChiM"]: float(abs(MPsi)),
    }
    masses_out.update(_SM_MASS_BLOCK)

    mixing: dict[str, dict] = {}
    mixing["ZNMIX"]   = {(i + 1, j + 1): 0.0 if is_neg[i] else float(ZN[i, j])
                         for i in range(3) for j in range(3)}
    mixing["IMZNMIX"] = {(i + 1, j + 1): float(ZN[i, j]) if is_neg[i] else 0.0
                         for i in range(3) for j in range(3)}
    mixing["UMMIX"]   = {(1, 1): 1.0}
    mixing["UPMIX"]   = {(1, 1): 1.0}
    mixing["IMUMMIX"] = {(1, 1): 0.0}
    mixing["IMUPMIX"] = {(1, 1): 0.0}

    return {
        "masses": masses_out,
        "mixing": mixing,
        "problem": [],
        "diagnostics": {
            # Eq. 8 of 2506.19062: m_chi1 + MPsi sin(2 theta) = 0 with
            # theta = arctan2(yh2, yh1) — SARAH's matrix has the same
            # spectrum as the paper's, so paper coordinates apply directly.
            # Uses the SIGNED lightest eigenvalue: with |m| the residual
            # tracks the wrong branch when m_chi1 < 0.
            "blind_spot_residual":
                float(signed[0] + abs(MPsi) * np.sin(
                    2.0 * np.arctan2(yh2, yh1)
                )),
            "m_chi1_signed": float(signed[0]),
        },
    }
