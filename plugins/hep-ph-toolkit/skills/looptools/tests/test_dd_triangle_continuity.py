"""
test_dd_triangle_continuity.py — triangle-continuity fixture (PR #35 review F3).

The box DD expansion rewrites ONLY D0i heads, so the triangle/bubble sector of
the canonical singlet-doublet amplitude must reproduce the item-3 baseline
C_scalar EXACTLY.  This test drives scripts/run_dd_triangle_continuity.wls on
the canonical reduced amplitude + point and compares against the pinned
FULL-PRECISION fixture (independently measured by the PR #35 reviewer, then
reproduced by this runner).

TRIPLE-GATED: wolframscript + HEPPH_RUN_WOLFRAM_TESTS=1 + the canonical
artifacts.  The reduced amplitude and point are job-scratch artifacts (too big
/ too point-specific to commit), so their locations come from env vars:

    HEPPH_SD_CANONICAL_AMP    -> amp_reduced.m  (wrapped amp/subexpr/abbr assoc)
    HEPPH_SD_CANONICAL_POINT  -> point.json     (SD SPheno spectrum point)

Skipped (not failed) when either is unset or missing — but when they ARE
present, the fixture comparison is exact-tolerance (1e-10 relative), so any
drift in the binding pattern, the projection, or the term split is loud.
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
RUNNER = SCRIPTS_DIR / "run_dd_triangle_continuity.wls"

# Pinned full-precision fixture: triangle-only C_scalar at the canonical SD
# point (mchi1 = 132.69 GeV, external down quark, setdelta 0 / setmudim 1), as
# produced by run_dd_triangle_continuity.wls (this runner is deterministic for
# a given kernel/LoopTools build, so the comparison below is exact-tolerance).
# The PR #35 adversarial review measured -1.2831508511406324e-7 with its own
# ad-hoc split script (REVIEW.md F3); this runner agrees with that independent
# measurement to 7.6e-8 RELATIVE (float noise through a different evaluation
# order + LeastSquares path), which is the honest cross-check statement — the
# two are NOT bit-identical.
TRIANGLE_C_SCALAR = -1.2831509485455282e-7
REVIEWER_C_SCALAR = -1.2831508511406324e-7

_WOLFRAM_GATE = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS") != "1"

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        _WOLFRAM_GATE,
        reason="Set HEPPH_RUN_WOLFRAM_TESTS=1 (and have Wolfram + FormCalc + "
               "LoopTools MathLink) to run the triangle-continuity fixture.",
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
def continuity_result(tmp_path_factory) -> dict:
    if shutil.which("wolframscript") is None:
        pytest.skip("wolframscript not on PATH")
    prefix = _looptools_prefix()
    if prefix is None:
        pytest.skip("LoopTools MathLink binary not available")
    amp = os.environ.get("HEPPH_SD_CANONICAL_AMP", "")
    pt = os.environ.get("HEPPH_SD_CANONICAL_POINT", "")
    if not (amp and Path(amp).exists() and pt and Path(pt).exists()):
        pytest.skip("canonical artifacts not available "
                    "(set HEPPH_SD_CANONICAL_AMP / HEPPH_SD_CANONICAL_POINT)")
    out = tmp_path_factory.mktemp("dd_tri") / "tri.json"
    res = subprocess.run(
        ["wolframscript", "-script", str(RUNNER), amp, pt, "default",
         str(out), prefix],
        capture_output=True, text=True, timeout=3600,
    )
    assert out.exists(), \
        f"continuity runner produced no output:\n{res.stdout}\n{res.stderr}"
    return json.loads(out.read_text())


def test_triangle_sector_c_scalar_matches_pinned_fixture(continuity_result):
    """The DD expansion must not move the triangle sector AT ALL: exact
    continuity with the item-3 baseline, compared at 1e-10 relative."""
    got = continuity_result["triangle_only"]["C_scalar_re"]
    rel = abs(got - TRIANGLE_C_SCALAR) / abs(TRIANGLE_C_SCALAR)
    assert rel < 1e-10, (
        f"triangle-only C_scalar drifted: got {got!r}, "
        f"fixture {TRIANGLE_C_SCALAR!r}, rel {rel:.3e}"
    )


def test_triangle_sector_agrees_with_independent_review_measurement(continuity_result):
    """Cross-check against the reviewer's independently-scripted measurement:
    agreement to 1e-6 relative (measured 7.6e-8) — loose enough for a different
    evaluation order, tight enough that a physics-level drift cannot hide."""
    got = continuity_result["triangle_only"]["C_scalar_re"]
    rel = abs(got - REVIEWER_C_SCALAR) / abs(REVIEWER_C_SCALAR)
    assert rel < 1e-6, (
        f"triangle-only C_scalar disagrees with the review measurement: "
        f"got {got!r}, review {REVIEWER_C_SCALAR!r}, rel {rel:.3e}"
    )


def test_split_is_nondegenerate(continuity_result):
    d = continuity_result
    assert d["n_triangle_terms"] > 0
    assert d["n_box_terms"] > 0
    assert d["n_triangle_terms"] + d["n_box_terms"] == d["n_terms"]
