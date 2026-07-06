"""Singlet-doublet fermion DM — analytic spectrum module.

Basis: (s0, PsiDd0, PsiDu0), matching the SARAH ordering declared in the
modelspec yaml (ewsb.mixings.weyls). The yh1 Yukawa (conj[H].FS.PsiDu) couples
s0↔PsiDu0; yh2 (H.FS.PsiDd) couples s0↔PsiDd0.

Mass matrix (Eq. 3, in this basis):
    M = [[MS,  b,    a   ],
         [b,   0,    MPsi],
         [a,   MPsi, 0   ]]
where a = yh1 * v / sqrt(2), b = yh2 * v / sqrt(2).

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
    a = yh1 * v / np.sqrt(2.0)
    b = yh2 * v / np.sqrt(2.0)
    return np.array([
        [MS, b,    a   ],
        [b,  0.0,  MPsi],
        [a,  MPsi, 0.0 ],
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
    # row belongs in IMZNMIX with the ZNMIX row zero. Emitting |m| with a
    # purely real ZN gives every vertex linear in that row a wrong phase:
    # it corrupted the chi2-exchange interference in chi1 chi1 -> Zh
    # (Omega h^2 = 0.0717 instead of 0.242 at the canonical benchmark) and
    # displaced the sigma_SI blind spot from the true theta = -0.152
    # (m_chi1 + MPsi sin 2theta = 0, paper Eq. 8) to a spurious +0.79.
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
            # Eq. 8 of 2506.19062 uses the SIGNED lightest eigenvalue: with
            # |m| the residual can never vanish for theta > 0 yet spuriously
            # tracks the wrong branch when m_chi1 < 0.
            "blind_spot_residual":
                float(signed[0] + abs(MPsi) * np.sin(
                    2.0 * np.arctan2(yh2, yh1)
                )),
            "m_chi1_signed": float(signed[0]),
        },
    }
