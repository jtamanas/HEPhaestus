"""Shared constants for analytic modules.

Prefer importing from eval/2506.19062_wimps_blind_spots/constants.py when the
sibling eval/ tree is present; fall back to hardcoded values otherwise.
A CI test (tests/test_analytic_singlet_doublet.py) asserts byte-equivalence.
"""

from __future__ import annotations

import importlib.util as _ilu
from pathlib import Path

# Default PDG 2020 values — must match eval/ constants.py.
V_H = 246.22
M_Z = 91.1876
M_W = 80.377
M_H = 125.25
G_F = 1.1663788e-5
ALPHA_EM = 1.0 / 137.036
SW2 = 0.23122


def _try_eval_constants():
    """Attempt to pull constants from eval/ tree; return a dict or None."""
    here = Path(__file__).resolve()
    # plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/_common.py
    # -> parents[5] = repo root.
    repo_root = here.parents[5]
    ev = repo_root / "eval" / "2506.19062_wimps_blind_spots" / "constants.py"
    if not ev.exists():
        return None
    spec = _ilu.spec_from_file_location("eval_constants", ev)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {k: getattr(mod, k) for k in ("V_H", "M_Z", "M_W", "M_H",
                                         "G_F", "ALPHA_EM", "SW2")
            if hasattr(mod, k)}


_eval = _try_eval_constants()
if _eval is not None:
    # Override hardcoded defaults from eval/ when present.
    V_H = _eval.get("V_H", V_H)
    M_Z = _eval.get("M_Z", M_Z)
    M_W = _eval.get("M_W", M_W)
    M_H = _eval.get("M_H", M_H)
    G_F = _eval.get("G_F", G_F)
    ALPHA_EM = _eval.get("ALPHA_EM", ALPHA_EM)
    SW2 = _eval.get("SW2", SW2)
