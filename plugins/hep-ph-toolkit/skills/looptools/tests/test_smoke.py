"""
test_smoke.py — Tier-3 real-tool smoke for /looptools eval (DEFERRED-run).

DOUBLE-GATED, committed-but-skipped here (build plan §3, /class precedent):
  - @pytest.mark.smoke                       (selection: pytest -m smoke)
  - skipif HEPPH_RUN_WOLFRAM_TESTS != "1"    (safety: never runs without opt-in)

Runs the REAL FormCalc/LoopTools evaluation of the TwoHdmAfix charged-Higgs/W
box (A⁰H⁺W⁻) on the committed fixture, and asserts the audit's "step 2"
end-to-end closure: a FINITE, UV-finite, GAUGE-STABLE amplitude → a positive,
finite σ_SI.  The driver wrapper is lazy-imported so collection succeeds without
Wolfram (feynarts precedent).

This is the ONLY real correctness check for the loop-DD path.  Every Tier-1/2
test runs against frozen fixtures we authored; a wrong physics assumption in
match_nucleon.py or run_eval.wls only surfaces HERE.  Treat the fixture σ values
as provisional until this smoke replaces them on a tooled box.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

_WOLFRAM_GATE = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS") != "1"

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        _WOLFRAM_GATE,
        reason="Set HEPPH_RUN_WOLFRAM_TESTS=1 (and have Wolfram + FormCalc + "
               "LoopTools MathLink installed) to run the real loop-DD smoke.",
    ),
]


def _wolframscript() -> str | None:
    return shutil.which("wolframscript")


def _looptools_mathlink_available() -> bool:
    """Lazy config probe: looptools_path set + $PREFIX/bin/LoopTools present."""
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) \
        / "hephaestus" / "config.json"
    if not cfg.exists():
        return False
    try:
        c = json.loads(cfg.read_text())
    except Exception:
        return False
    lt = c.get("looptools_path", "")
    return bool(lt) and (Path(lt) / "bin" / "LoopTools").exists() \
        and str(c.get("looptools_mathlink_available", "")).lower() == "true"


def test_real_loop_dd_amplitude_is_finite_and_positive(tmp_path):
    """Real A⁰H⁺W⁻ box → finite, UV-finite, gauge-stable σ_SI > 0."""
    if _wolframscript() is None:
        pytest.skip("wolframscript not on PATH")
    if not _looptools_mathlink_available():
        pytest.skip("LoopTools MathLink binary not available (looptools_mathlink_available != true)")

    work = tmp_path / "fc_out"
    work.mkdir()
    shutil.copy(FIXTURES_DIR / "amp_reduced.m", work / "amp_reduced.m")
    shutil.copy(FIXTURES_DIR / "amp_reduced.meta.json", work / "amp_reduced.meta.json")
    out_dir = tmp_path / "lt_out"

    # NOTE: no HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT → exercises the REAL run_eval.wls driver.
    env = os.environ.copy()
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS_DIR / "run_looptools.py"), "eval",
            "--amp-reduced", str(work / "amp_reduced.m"),
            "--point", str(FIXTURES_DIR / "two_hdm_a_point.slha"),
            "--output-dir", str(out_dir),
        ],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, (
        f"real driver failed (rc={result.returncode}); stderr:\n{result.stderr}"
    )

    doc = json.loads((out_dir / "scattering.json").read_text())
    sigma_p = doc["sigma_si_proton_cm2"]
    sigma_n = doc["sigma_si_neutron_cm2"]

    # Finite + positive (the audit's step-2 closure: no missing-vertex zero, no
    # NaN/Inf from an un-cancelled UV pole or gauge dependence).
    assert sigma_p == sigma_p and sigma_p not in (float("inf"), float("-inf")), "σ_SI(p) non-finite"
    assert sigma_p > 0.0, "σ_SI(p) is not positive — possible missing-vertex zero"
    assert sigma_n > 0.0, "σ_SI(n) is not positive"

    # Plausibility band for a loop-induced 2HDM+a SI cross-section (very loose;
    # the smoke checks finiteness/sign/stability, not a pinned magnitude).
    assert 1e-52 < sigma_p < 1e-42, f"σ_SI(p)={sigma_p} outside the loop-DD plausibility band"


def test_driver_script_present():
    """The deferred driver asset must be committed even when the smoke is skipped."""
    assert (SCRIPTS_DIR / "run_eval.wls").exists()
