"""
test_projection_r2.py — R2 cross-talk fixture (STEP3-DESIGN.md Decision 6 R2).

Runs the SD chain-coefficient projector (sd_projection.wl via run_projection_sd.wls)
on hand-built PRE-REDUCED fixtures with known pure-scalar / pure-twist-2 /
mixed content, and asserts the projector recovers each operator coefficient to
<1% with cross-talk <1% — the exact failure mode (scalar<->twist-2 folding of the
2HDM+a static spin-summed collapse) this guard is built to catch.

The fixtures are pre-reduced (plain-number PV heads), so this needs only a
Wolfram kernel — NOT the LoopTools MathLink / HEPPH_RUN_WOLFRAM_TESTS gate.  It
is skipped only when wolframscript is absent (the hermetic disjointness invariant
in test_sd_binding.py covers the same guard without any kernel).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES = TESTS_DIR / "fixtures" / "sd"
RUNNER = SCRIPTS_DIR / "run_projection_sd.wls"

_wolfram = shutil.which("wolframscript")
pytestmark = pytest.mark.skipif(_wolfram is None, reason="wolframscript not on PATH")

C_SCALAR_EXPECT = 19.0   # F1(4) + F4(3) + F2(5) + F3(7)
C_TWIST2_EXPECT = 60.0   # F5(11) + F6(13) + F7(17) + F8(19)
TOL = 0.01               # 1% recovery + cross-talk band (Decision 6 R2)


def _project(fixture_name: str, tmp_path: Path) -> dict:
    out = tmp_path / f"{fixture_name}.json"
    res = subprocess.run(
        [_wolfram, "-script", str(RUNNER), str(FIXTURES / f"{fixture_name}.m"), str(out)],
        capture_output=True, text=True, timeout=600,
    )
    assert out.exists(), f"projector produced no output:\n{res.stdout}\n{res.stderr}"
    return json.loads(out.read_text())


def test_pure_scalar_projects_to_scalar_no_twist2(tmp_path):
    d = _project("pure_scalar", tmp_path)
    assert not d["residual_symbols"], f"unexpected residuals: {d['residual_symbols']}"
    assert abs(d["C_scalar"] - C_SCALAR_EXPECT) / C_SCALAR_EXPECT < TOL
    # cross-talk: twist-2 must be < 1% of the scalar magnitude
    assert abs(d["C_twist2"]) < TOL * C_SCALAR_EXPECT, \
        f"scalar->twist-2 cross-talk {d['C_twist2']} (2HDM+a-collapse bug)"


def test_pure_twist2_projects_to_twist2_no_scalar(tmp_path):
    d = _project("pure_twist2", tmp_path)
    assert not d["residual_symbols"], f"unexpected residuals: {d['residual_symbols']}"
    assert abs(d["C_twist2"] - C_TWIST2_EXPECT) / C_TWIST2_EXPECT < TOL
    # cross-talk: scalar must be < 1% of the twist-2 magnitude — the load-bearing R2
    # check.  A static spin-summed collapse would fold this twist-2 into C_scalar.
    assert abs(d["C_scalar"]) < TOL * C_TWIST2_EXPECT, \
        f"twist-2->scalar cross-talk {d['C_scalar']} (2HDM+a-collapse bug)"


def test_mixed_recovers_both_independently(tmp_path):
    d = _project("mixed_scalar_twist2", tmp_path)
    assert not d["residual_symbols"]
    assert abs(d["C_scalar"] - C_SCALAR_EXPECT) / C_SCALAR_EXPECT < TOL
    assert abs(d["C_twist2"] - C_TWIST2_EXPECT) / C_TWIST2_EXPECT < TOL


def test_twist2_c1_c2_subsplit_sums_to_block(tmp_path):
    """The C^(1)/C^(2) sub-split must sum to the twist-2 block total."""
    d = _project("pure_twist2", tmp_path)
    assert abs((d["C_twist2_1"] + d["C_twist2_2"]) - d["C_twist2"]) < 1e-6
