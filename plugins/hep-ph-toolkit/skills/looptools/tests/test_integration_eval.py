"""Tier-2 integration — full /looptools eval pipeline with a STUBBED driver.

The wolframscript subprocess is stubbed by the frozen eval_output.json fixture
(HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT).  Asserts the end-to-end chain produces a
schema-valid scattering/v1 that /ddcalc's validate_scattering.py accepts, with
source=looptools and the golden σ values.  No Wolfram / LoopTools needed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
DDCALC_SCRIPTS = SKILL_DIR.parent / "ddcalc" / "scripts"

GOLDEN = json.loads((FIXTURES_DIR / "scattering_golden.json").read_text())


def _run_eval(tmp_path: Path, extra_args=None, env_extra=None):
    """Run run_looptools.py eval as a subprocess with the stubbed driver."""
    work = tmp_path / "fc_out"
    work.mkdir()
    shutil.copy(FIXTURES_DIR / "amp_reduced.m", work / "amp_reduced.m")
    shutil.copy(FIXTURES_DIR / "amp_reduced.meta.json", work / "amp_reduced.meta.json")
    out_dir = tmp_path / "lt_out"

    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    env["HOME"] = str(tmp_path)
    env["HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT"] = str(FIXTURES_DIR / "eval_output.json")
    if env_extra:
        env.update(env_extra)

    args = [
        sys.executable, str(SCRIPTS_DIR / "run_looptools.py"), "eval",
        "--amp-reduced", str(work / "amp_reduced.m"),
        "--point", str(FIXTURES_DIR / "two_hdm_a_point.slha"),
        "--output-dir", str(out_dir),
    ]
    if extra_args:
        args += extra_args
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    return result, out_dir


def test_pipeline_emits_scattering(tmp_path):
    result, out_dir = _run_eval(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    scattering = out_dir / "scattering.json"
    assert scattering.exists()
    doc = json.loads(scattering.read_text())
    assert doc["schema_version"] == "scattering/v1"
    assert doc["source"] == "looptools"
    assert doc["source_run"]
    assert doc["m_dm_gev"] == pytest.approx(100.0)


def test_sigma_matches_golden(tmp_path):
    _, out_dir = _run_eval(tmp_path)
    doc = json.loads((out_dir / "scattering.json").read_text())
    assert doc["sigma_si_proton_cm2"] == pytest.approx(GOLDEN["sigma_si_proton_cm2"], rel=1e-9)
    assert doc["sigma_si_neutron_cm2"] == pytest.approx(GOLDEN["sigma_si_neutron_cm2"], rel=1e-9)
    assert doc["sigma_sd_proton_cm2"] is None
    assert doc["sigma_sd_neutron_cm2"] is None


def test_output_accepted_by_ddcalc_validator(tmp_path):
    pytest.importorskip("jsonschema")
    _, out_dir = _run_eval(tmp_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_scattering", str(DDCALC_SCRIPTS / "validate_scattering.py")
    )
    vs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vs)
    doc = json.loads((out_dir / "scattering.json").read_text())
    assert vs.validate_sigma_json(doc)["source"] == "looptools"


def test_run_receipt_summary_written(tmp_path):
    _, out_dir = _run_eval(tmp_path)
    runs = list((out_dir / "run").glob("*/summary.json"))
    assert runs, "no run/<ts>/summary.json receipt written"
    summary = json.loads(runs[0].read_text())
    for k in ("n_diagrams", "wall_clock_s", "cached", "looptools_version", "n_pv_calls", "point_id"):
        assert k in summary
    assert summary["cached"] is False


def test_cache_hit_on_rerun(tmp_path):
    r1, out_dir = _run_eval(tmp_path)
    assert r1.returncode == 0
    # Rerun against the SAME output dir → cache hit.
    work = tmp_path / "fc_out"
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    env["HOME"] = str(tmp_path)
    env["HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT"] = str(FIXTURES_DIR / "eval_output.json")
    args = [
        sys.executable, str(SCRIPTS_DIR / "run_looptools.py"), "eval",
        "--amp-reduced", str(work / "amp_reduced.m"),
        "--point", str(FIXTURES_DIR / "two_hdm_a_point.slha"),
        "--output-dir", str(out_dir),
    ]
    r2 = subprocess.run(args, capture_output=True, text=True, env=env)
    assert r2.returncode == 0
    assert json.loads(r2.stdout)["cached"] is True


def test_nonfinite_driver_output_blocks(tmp_path):
    """A driver output flagged non-finite → LOOPTOOLS_AMPLITUDE_NONFINITE (exit 2)."""
    bad = tmp_path / "bad_eval.json"
    d = json.loads((FIXTURES_DIR / "eval_output.json").read_text())
    d["amplitude"]["finite"] = False
    bad.write_text(json.dumps(d))
    result, _ = _run_eval(tmp_path, env_extra={"HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT": str(bad)})
    assert result.returncode == 2
    assert "LOOPTOOLS_AMPLITUDE_NONFINITE" in result.stderr


def test_missing_amp_input_blocks(tmp_path):
    """Missing amp_reduced.m → LOOPTOOLS_INPUT_MISSING (exit 1)."""
    out_dir = tmp_path / "lt_out"
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    env["HOME"] = str(tmp_path)
    env["HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT"] = str(FIXTURES_DIR / "eval_output.json")
    args = [
        sys.executable, str(SCRIPTS_DIR / "run_looptools.py"), "eval",
        "--amp-reduced", str(tmp_path / "nope" / "amp_reduced.m"),
        "--point", str(FIXTURES_DIR / "two_hdm_a_point.slha"),
        "--output-dir", str(out_dir),
    ]
    result = subprocess.run(args, capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert "LOOPTOOLS_INPUT_MISSING" in result.stderr
