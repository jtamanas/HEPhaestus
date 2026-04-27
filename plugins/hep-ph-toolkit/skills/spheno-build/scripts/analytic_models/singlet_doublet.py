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
    masses = np.abs(eigvals[idx])
    U_sorted = U[:, idx]
    ZN = U_sorted.T  # rows=mass eigenstate, cols=interaction (SARAH convention)

    masses_out = {
        SINGLET_DOUBLET_PDG_IDS["Chi1"]: float(masses[0]),
        SINGLET_DOUBLET_PDG_IDS["Chi2"]: float(masses[1]),
        SINGLET_DOUBLET_PDG_IDS["Chi3"]: float(masses[2]),
        SINGLET_DOUBLET_PDG_IDS["ChiM"]: float(abs(MPsi)),
    }
    masses_out.update(_SM_MASS_BLOCK)

    mixing: dict[str, dict] = {}
    mixing["ZNMIX"]   = {(i + 1, j + 1): float(ZN[i, j]) for i in range(3) for j in range(3)}
    mixing["IMZNMIX"] = {(i + 1, j + 1): 0.0            for i in range(3) for j in range(3)}
    mixing["UMMIX"]   = {(1, 1): 1.0}
    mixing["UPMIX"]   = {(1, 1): 1.0}
    mixing["IMUMMIX"] = {(1, 1): 0.0}
    mixing["IMUPMIX"] = {(1, 1): 0.0}

    return {
        "masses": masses_out,
        "mixing": mixing,
        "problem": [],
        "diagnostics": {
            "blind_spot_residual":
                float(masses[0] + abs(MPsi) * np.sin(
                    2.0 * np.arctan2(yh2, yh1)
                )),
        },
    }
