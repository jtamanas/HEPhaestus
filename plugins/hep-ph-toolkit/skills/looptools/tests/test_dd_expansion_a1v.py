"""
test_dd_expansion_a1v.py — A1-V head-level cross-check for the box small-momentum
(DD-limit) expansion (DESIGN-ITEM4.md Decision A1-V), plus the DD-point finiteness
demonstration (the payoff mechanism).

DOUBLE-GATED (same discipline as test_smoke.py):
  * skipif wolframscript not on PATH
  * skipif HEPPH_RUN_WOLFRAM_TESTS != "1"  (real LoopTools MathLink required)
  * skip if the LoopTools MathLink binary is not configured

What it asserts (drives scripts/run_dd_expansion_check.wls):
  1. EXACT primitives (validation-side; ddIntOffsetExact + ddTraceScalar vs
     LoopTools tensors at 3 Gram-O(1) points, < 1e-6).  These certify
     ddScalarInt (shared with production) + the numerator-identity machinery;
     ddIntOffsetExact itself is NOT on the production path (PR #35 review F2 —
     stated, not implied away).
  2. PRODUCTION path, contracted level (DESIGN-ITEM4-AMENDMENT.md stage-0c F2):
     ddIntU / ddBasisComponents (which feed ddBoxHead) vs LoopTools' own tensor
     u-contractions along the physical SD signature's non-zero-Gram T-path:
       * rank-1 contraction: machine precision at every point (1e-6 bar literal);
       * rank-2: deviation falls toward the DD point with the budget power laws
         (fitted log-log slopes);
       * extrapolated T->0 LoopTools reference vs production at T=-TEPS, within
         the stated budgets.  HONESTY NOTE (live A-R1 risk, bounded): the rank-2
         contracted check is limited to ~1e-2 by the extrapolation reference
         itself (threshold kinematics; a sqrt-adapted basis is ill-conditioned
         and does worse).  The rank-2 production accuracy is therefore bounded
         at the PERCENT level by this check, not 1e-6; the independent physics
         check for rank-2 content is the Hisano pure-doublet anchor (stage 1).
  3. DD finiteness (the cure): at the degenerate DD point the reduction stays
     FINITE (O(1e-10)) while LoopTools' own D0i[dd11,..] rides the Gram pole
     (~1e8) — the verified item-4 blocker (kinematics-invest/FINDINGS.md +
     kinvest-verify/VERIFY.md).

RED-FIRST against base: this file + scripts/run_dd_expansion_check.wls +
scripts/sd_dd_expansion.wl do not exist at origin/main@5619b6d, so the A1-V check
had nothing to run.  The production-path section (2) was added against PR #35's
first commit, whose committed test validated only the exact primitives (review
finding F2).
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
    """Section 1: exact vector + trace primitives == LoopTools box tensor
    coefficients at 3 non-degenerate points, to < 1e-6 relative (validation-side;
    certifies ddScalarInt + the numerator machinery)."""
    d = check_result
    assert d["a1v_ok"], f"A1-V failed: max reldiff {d['a1v_max_reldiff']} >= 1e-6"
    assert d["a1v_max_reldiff"] < 1e-6, d["a1v_max_reldiff"]
    # each of the 3 points must individually pass (no averaging over a failure)
    assert all(r < 1e-6 for r in d["a1v_reldiffs"]), d["a1v_reldiffs"]


def test_production_rank1_contraction_is_exact(check_result):
    """Section 2a (amendment-0c F2): the PRODUCTION telescoper ddIntU's rank-1
    contraction equals LoopTools' own Sum_i b_i D_i at every point of the
    non-zero-Gram T-path — the 1e-6 bar met literally (measured ~1e-15)."""
    d = check_result
    assert d["prod_u1_max_rel"] < 1e-6, d["prod_u1_max_rel"]
    # per-point (no averaging)
    assert all(row["u1_rel"] < 1e-6 for row in d["prod_sameT"]), d["prod_sameT"]


def test_production_rank2_converges_toward_dd_point(check_result):
    """Section 2a: the rank-2 deviation between the production reduction and
    LoopTools' contractions must FALL toward the DD point with a positive power
    (measured slope ~1.0 in |T| over T=-100..-1).  A flat or growing deviation
    would mean the collinear reconstruction does not approach LoopTools' tensors
    in the limit it is designed for."""
    d = check_result
    assert 0.4 <= d["prod_u2_conv_slope"] <= 1.3, d["prod_u2_conv_slope"]
    assert 0.6 <= d["prod_d00_conv_slope"] <= 1.3, d["prod_d00_conv_slope"]
    # deviations must be monotonically decreasing as |T| decreases
    u2 = [row["u2_rel"] for row in d["prod_sameT"]]      # T = -100, -10, -1
    d00 = [row["D00_rel"] for row in d["prod_sameT"]]
    assert u2[0] > u2[1] > u2[2], u2
    assert d00[0] > d00[1] > d00[2], d00


def test_production_matches_extrapolated_looptools_within_budget(check_result):
    """Section 2b: LoopTools contractions extrapolated T->0 vs the PRODUCTION
    values at T=-TEPS.  Budgets (stated, measured): rank-1 1e-6 (measured 1.4e-9),
    D00 1e-3 (measured 4.8e-5), u2/Duu 2.5e-2 (measured ~1.2e-2 — limited by the
    extrapolation reference itself; percent-level bound, Hisano anchor is the
    tighter independent check)."""
    d = check_result
    assert d["prod_u1_extrap_rel"] < 1e-6, d["prod_u1_extrap_rel"]
    assert d["prod_d00_extrap_rel"] < 1e-3, d["prod_d00_extrap_rel"]
    assert d["prod_u2_extrap_rel"] < 2.5e-2, d["prod_u2_extrap_rel"]
    assert d["prod_duu_extrap_rel"] < 2.5e-2, d["prod_duu_extrap_rel"]


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
