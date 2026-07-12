"""
test_dd_expansion_a1v.py — A1-V head-level cross-check for the box small-momentum
(DD-limit) expansion (DESIGN-ITEM4.md Decision A1-V), plus the DD-point finiteness
demonstration (the payoff mechanism).

DOUBLE-GATED (same discipline as test_smoke.py):
  * skipif wolframscript not on PATH
  * skipif HEPPH_RUN_WOLFRAM_TESTS != "1"  (real LoopTools MathLink required)
  * skip if the LoopTools MathLink binary is not configured

What it asserts (drives scripts/run_dd_expansion_check.wls):
  1. A1-V: the expansion's EXACT reduction primitives (the rank-1 vector reduction
     and the trace reduction) reproduce LoopTools' OWN box tensor coefficients at
     3 non-degenerate kinematic points (Gram = O(1)) to < 1e-6 relative — "same
     integrals, tool-precision agreement, not a physics band" (Decision A1-V).
     These are exact PV identities (true at all kinematics); the DD application is
     their Gram-stable collinear specialisation.
  2. DD finiteness (the cure): at the degenerate DD point the collinear reduction
     ddBoxHead[dd11,..] stays FINITE (O(1e-10)) while LoopTools' own D0i[dd11,..]
     rides the Gram-determinant pole (~1e8) — the verified item-4 blocker
     (kinematics-invest/FINDINGS.md + kinvest-verify/VERIFY.md).  The ratio is the
     ~1e-18 headline demonstrating the pole is gone.

RED-FIRST against base: this file + scripts/run_dd_expansion_check.wls +
scripts/sd_dd_expansion.wl do not exist at origin/main@5619b6d, so the A1-V check
had nothing to run.  The mechanism it validates (the box DD expansion) is the
item-4 deliverable.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
RUNNER = SCRIPTS_DIR / "run_dd_expansion_check.wls"

_WOLFRAM_GATE = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS") != "1"

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        _WOLFRAM_GATE,
        reason="Set HEPPH_RUN_WOLFRAM_TESTS=1 (and have Wolfram + FormCalc + "
               "LoopTools MathLink) to run the box DD-expansion A1-V cross-check.",
    ),
]


def _looptools_prefix() -> str | None:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) \
        / "hephaestus" / "config.json"
    if not cfg.exists():
        return None
    try:
        c = json.loads(cfg.read_text())
    except Exception:
        return None
    lt = c.get("looptools_path", "")
    if lt and (Path(lt) / "bin" / "LoopTools").exists() \
            and str(c.get("looptools_mathlink_available", "")).lower() == "true":
        return lt
    return None


@pytest.fixture(scope="module")
def check_result(tmp_path_factory) -> dict:
    if shutil.which("wolframscript") is None:
        pytest.skip("wolframscript not on PATH")
    prefix = _looptools_prefix()
    if prefix is None:
        pytest.skip("LoopTools MathLink binary not available (looptools_mathlink_available != true)")
    out = tmp_path_factory.mktemp("dd_a1v") / "a1v.json"
    res = subprocess.run(
        ["wolframscript", "-script", str(RUNNER), str(out), prefix],
        capture_output=True, text=True, timeout=900,
    )
    assert out.exists(), f"A1-V runner produced no output:\n{res.stdout}\n{res.stderr}"
    return json.loads(out.read_text())


def test_a1v_exact_primitives_match_looptools_tensors(check_result):
    """Decision A1-V: rank-1 vector + trace reductions == LoopTools box tensor
    coefficients at 3 non-degenerate points, to < 1e-6 relative."""
    d = check_result
    assert d["a1v_ok"], f"A1-V failed: max reldiff {d['a1v_max_reldiff']} >= 1e-6"
    assert d["a1v_max_reldiff"] < 1e-6, d["a1v_max_reldiff"]
    # each of the 3 points must individually pass (no averaging over a failure)
    assert all(r < 1e-6 for r in d["a1v_reldiffs"]), d["a1v_reldiffs"]


def test_dd_point_reduction_is_finite_while_looptools_blows_up(check_result):
    """The cure: at the degenerate DD point the collinear reduction is finite while
    LoopTools' own dd11 rides the Gram pole (~1e8)."""
    d = check_result
    assert d["dd_box_dd11_finite"], \
        f"DD-reduced dd11 not finite/small: {d['dd_finite_box_dd11_abs']}"
    # LoopTools' own tensor coefficient IS Gram-poled at the DD point (the blocker)
    assert d["lt_gram_poled_dd11_abs"] > 1e5, \
        f"expected LoopTools dd11 to be Gram-poled (>1e5), got {d['lt_gram_poled_dd11_abs']}"
    # the pole is gone from the reduction: ratio is astronomically small
    assert d["dd_over_lt_ratio"] < 1e-10, d["dd_over_lt_ratio"]


def test_gram_monitor_reports_rank1_degeneracy(check_result):
    """The Gram/degeneracy monitor must flag the DD box signature as (near-)rank-1
    (det/scale^3 ~ 0, rank-1 residual ~ 0) — that is WHY the collinear reduction is
    exact there and LoopTools' tensor reduction is not."""
    d = check_result
    assert abs(d["gram_det_over_scale3"]) < 1e-12, d["gram_det_over_scale3"]
    assert d["rank1_residual"] < 1e-6, d["rank1_residual"]
