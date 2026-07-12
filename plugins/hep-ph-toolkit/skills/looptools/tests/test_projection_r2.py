"""
test_projection_r2.py — R2 cross-talk fixture (STEP3-DESIGN.md Decision 6 R2).

Runs the SD chain-coefficient projector (sd_projection.wl via run_projection_sd.wls)
on fixtures built from the REAL FormCalc WeylChain definitions (copied verbatim
from the self-contained SD artifact) and asserts:

  * pure-scalar  -> C_scalar recovered, C_twist2 ~ 0  (no scalar->twist-2 leak)
  * pure-twist2  -> C_twist2 recovered, C_scalar ~ 0  (no twist-2->scalar leak;
                    the exact 2HDM+a static-collapse failure mode this guard exists
                    to catch)
  * mixed        -> BOTH recovered independently
  * adversarial  -> the completeness/structural guard FAILS LOUDLY (ok=False,
                    names the unrecognized rank-2 chain) instead of silently
                    dropping content (the PR #31 F2 silent-fall-through).

NON-CIRCULAR: the operator identity of each chain (F1,F4=chi-scalar; F2,F3=
quark-scalar; F15,F16=quark twist-2) is established by the ACTUAL spinor structure
via the numerical basis-vector solve (Decision 3.2), NOT by an assumed contiguous
index block — PR #31's fixtures were hand-built to obey the (wrong) block map, so
its R2 test was circular.  These fixtures would FAIL under the old {F5..F8}=twist-2
map because the real SD twist-2 chains are F15,F16.

The fixtures are pre-reduced (plain-number PV heads), so this needs only a Wolfram
kernel — NOT the LoopTools MathLink / HEPPH_RUN_WOLFRAM_TESTS gate.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES = TESTS_DIR / "fixtures" / "sd"
RUNNER = SCRIPTS_DIR / "run_projection_sd.wls"

_wolfram = shutil.which("wolframscript")
pytestmark = pytest.mark.skipif(_wolfram is None, reason="wolframscript not on PATH")

C_SCALAR_EXPECT = 19.0
C_TWIST2_EXPECT = 60.0
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
    assert d["ok"], f"projection failed: {d}"
    assert not d["residual_symbols"], f"unexpected residuals: {d['residual_symbols']}"
    assert d["completeness_ok"], f"completeness residual too large: {d['completeness_rel_residual']}"
    assert abs(d["C_scalar"] - C_SCALAR_EXPECT) / C_SCALAR_EXPECT < TOL
    # cross-talk: twist-2 must be < 1% of the scalar magnitude
    assert abs(d["C_twist2"]) < TOL * C_SCALAR_EXPECT, \
        f"scalar->twist-2 cross-talk {d['C_twist2']} (2HDM+a-collapse bug)"


def test_pure_twist2_projects_to_twist2_no_scalar(tmp_path):
    d = _project("pure_twist2", tmp_path)
    assert d["ok"], f"projection failed: {d}"
    assert not d["residual_symbols"], f"unexpected residuals: {d['residual_symbols']}"
    assert d["completeness_ok"], f"completeness residual too large: {d['completeness_rel_residual']}"
    assert abs(d["C_twist2"] - C_TWIST2_EXPECT) / C_TWIST2_EXPECT < TOL
    # cross-talk: scalar must be < 1% of the twist-2 magnitude — the load-bearing R2
    # check.  A static spin-summed collapse would fold this twist-2 into C_scalar.
    assert abs(d["C_scalar"]) < TOL * C_TWIST2_EXPECT, \
        f"twist-2->scalar cross-talk {d['C_scalar']} (2HDM+a-collapse bug)"


def test_mixed_recovers_both_independently(tmp_path):
    d = _project("mixed_scalar_twist2", tmp_path)
    assert d["ok"], f"projection failed: {d}"
    assert not d["residual_symbols"]
    assert d["completeness_ok"], f"completeness residual too large: {d['completeness_rel_residual']}"
    assert abs(d["C_scalar"] - C_SCALAR_EXPECT) / C_SCALAR_EXPECT < TOL
    assert abs(d["C_twist2"] - C_TWIST2_EXPECT) / C_TWIST2_EXPECT < TOL


def test_adversarial_unrecognized_chain_fails_loudly(tmp_path):
    """RED-FIRST (F2): a deliberately unrecognized rank-2 chain (F19) must make the
    projector fail loudly and NAME the offending chain — not silently drop it."""
    d = _project("adversarial_unrecognized", tmp_path)
    assert not d["ok"], "projector must REFUSE an unrecognized-structure amplitude"
    assert d["reason"] == "UNRECOGNIZED-CHAIN-STRUCTURE", f"wrong reason: {d}"
    assert any("F19" in c for c in d["unrecognized_chains"]), \
        f"the unrecognized chain must be named: {d['unrecognized_chains']}"
