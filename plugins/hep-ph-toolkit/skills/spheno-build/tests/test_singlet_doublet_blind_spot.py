"""test_singlet_doublet_blind_spot.py — WS-A §8.3 ship gate.

Independent physics gate: at the numerically precomputed reference point
(MS_zero found via eval/.../singlet_doublet.diagonalize + scipy.brentq),
our analytic module's m_chi1 must satisfy Eq. (8) of 2506.19062 to
machine precision.

The reference is computed from eval/ — a different codebase than our
analytic module — so a sign flip or basis mis-order in ours will surface
as a non-zero residual.

Regenerate MS_zero by running the script in /tmp/shift-manager/ws-a/05-impl-plan.md §4.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"

# Precomputed via scipy.optimize.brentq against eval/.../singlet_doublet.diagonalize.
# Parameters: MPsi=500, theta=-pi/6, y=1.0 → yh1=cos(-pi/6), yh2=sin(-pi/6).
# Residual tolerance checked at authoring: 1.137e-16.
_MS_ZERO = 433.01270189221924


def _load(name: str, p: Path):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_blind_spot_condition_at_MS_zero():
    sd = _load("sd", _SCRIPTS / "analytic_models" / "singlet_doublet.py")
    MPsi = 500.0
    theta = -np.pi / 6
    y = 1.0
    yh1 = y * np.cos(theta)
    yh2 = y * np.sin(theta)

    r = sd.compute(
        spec={},
        params={"MS": _MS_ZERO, "MPsi": MPsi, "yh1": yh1, "yh2": yh2},
    )
    m_chi1 = r["masses"][9958431]

    residual = m_chi1 + MPsi * np.sin(2 * theta)
    assert abs(residual) / MPsi < 1e-9, (
        f"Blind-spot condition violated (Eq. 8): m_chi1={m_chi1}, "
        f"MPsi={MPsi}, theta={theta}, |residual|/MPsi={abs(residual)/MPsi:.3e}"
    )


def test_matches_eval_diagonalize_bytewise():
    """Defence-in-depth: our m_chi1 must match eval's to 1e-10."""
    sd = _load("sd", _SCRIPTS / "analytic_models" / "singlet_doublet.py")

    import sys
    sys.path.insert(0, str(
        Path(__file__).resolve().parents[5] / "eval" / "2506.19062_wimps_blind_spots"
    ))
    sys.path.insert(0, str(
        Path(__file__).resolve().parents[5] / "eval" / "2506.19062_wimps_blind_spots" / "models"
    ))
    from singlet_doublet import diagonalize as eval_diag

    MPsi, theta, y = 500.0, -np.pi / 6, 1.0
    yh1, yh2 = y * np.cos(theta), y * np.sin(theta)
    eval_masses, _ = eval_diag(_MS_ZERO, MPsi, yh1, yh2)

    ours = sd.compute(spec={}, params={"MS": _MS_ZERO, "MPsi": MPsi,
                                       "yh1": yh1, "yh2": yh2})
    our_m_chi1 = ours["masses"][9958431]
    assert abs(our_m_chi1 - eval_masses[0]) < 1e-10, (
        f"m_chi1 drifts from eval: ours={our_m_chi1}, eval={eval_masses[0]}"
    )
