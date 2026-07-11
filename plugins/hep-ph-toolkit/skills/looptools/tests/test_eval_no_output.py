"""
test_eval_no_output.py — loud-failure hardening for the /looptools eval leg.

Regression coverage for the step-2 (STEP2.md, subtask 3a) friction: run_eval.wls
could exit 0 (or abort via MathLink::MLException) leaving eval_output.json
empty/absent, and run_looptools.py's run_driver then crashed with a raw Python
JSONDecodeError instead of a structured blocker.  These tests pin:

  (a) a run whose eval_output.json is missing / empty / garbage → a structured
      LOOPTOOLS_EVAL_NO_OUTPUT blocker on stderr, nonzero exit, NO traceback;
  (b) the JSONDecodeError path specifically (garbage bytes on disk);
  (c) unbound-model-parameter detection: the driver's UNBOUND-MODEL-PARAMETERS
      marker is classified and the offending symbol names are surfaced in the
      blocker context (the singlet-doublet symptom → guided step-3 error).

All hermetic: a fake "wolframscript" shell/py stub stands in for the real driver,
so no Wolfram / LoopTools is needed.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

import run_looptools  # noqa: E402  (conftest puts scripts/ on sys.path)


# ── Unit: log classification helpers ────────────────────────────────────────

def test_diagnose_unbound_model_parameters():
    log = 'run_eval: UNBOUND-MODEL-PARAMETERS {"Masshh[2](H,35)", "gchi(DMSECTOR:2)"}'
    assert run_looptools._diagnose_eval_failure(log, 3) == "unbound_model_parameters"


def test_diagnose_mathlink_abort():
    log = "MathLink::MLException: ...\nlibc++abi: terminating\n"
    assert run_looptools._diagnose_eval_failure(log, 0) == "mathlink_aborted"


def test_diagnose_selftest_and_unknown():
    assert run_looptools._diagnose_eval_failure(
        "run_eval: LoopTools C0i self-test failed (got $Failed)", 1
    ) == "looptools_selftest_failed"
    assert run_looptools._diagnose_eval_failure("", 0) == "unknown"


def test_extract_unbound_symbols():
    log = 'run_eval: UNBOUND-MODEL-PARAMETERS {"Masshh[2](H,35)", "gchi(DMSECTOR:2)", "ZAMIX(ZAMIX:i,j)"}'
    got = run_looptools._extract_unbound(log)
    assert got == ["Masshh[2](H,35)", "gchi(DMSECTOR:2)", "ZAMIX(ZAMIX:i,j)"]


def test_extract_unbound_none_when_absent():
    assert run_looptools._extract_unbound("nothing to see here") == []


# ── Unit: run_driver against a fake driver binary ───────────────────────────

def _fake_bin(tmp_path: Path, mode: str) -> Path:
    """Write a fake wolframscript (used AS the wolfram binary) that mimics
    run_eval.wls failure modes.

    run_driver invokes ``[wolfram_bin, -script, driver, amp, point, ff, eval_out, lt]``;
    with this stub standing in for wolfram_bin, its own argv is
    ``[stub, -script, driver, amp, point, ff, eval_out, lt]`` → eval_out is argv[6].
    """
    p = tmp_path / f"fake_wolfram_{mode}.py"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"mode = {mode!r}\n"
        "eval_out = sys.argv[6]\n"
        "if mode == 'empty':\n"
        "    open(eval_out, 'w').close(); sys.exit(0)\n"
        "if mode == 'garbage':\n"
        "    open(eval_out, 'w').write('this is not json <<<'); sys.exit(0)\n"
        "if mode == 'missing':\n"
        "    sys.exit(0)\n"
        "if mode == 'unbound':\n"
        "    sys.stderr.write('run_eval: UNBOUND-MODEL-PARAMETERS "
        "{\"Masshh[2](H,35)\", \"gchi(DMSECTOR:2)\"}\\n'); sys.exit(3)\n"
    )
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _call_run_driver(tmp_path: Path, mode: str):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    amp = tmp_path / "amp_reduced.m"
    amp.write_text("{amp -> 0}\n")
    return run_looptools.run_driver(
        wolfram_bin=str(_fake_bin(tmp_path, mode)),
        amp_reduced_path=amp,
        point={"dm_pdg": 9989932, "m_dm_gev": 100.0},
        form_factor_preset="default_2018",
        output_dir=tmp_path,
        run_dir=run_dir,
        looptools_path=str(tmp_path),
    )


@pytest.mark.parametrize("mode", ["empty", "missing", "garbage"])
def test_run_driver_no_output_raises_evalnooutput(tmp_path, mode):
    with pytest.raises(run_looptools.EvalNoOutput) as ei:
        _call_run_driver(tmp_path, mode)
    # Not a bare RuntimeError message about JSON — a structured, classified failure.
    assert ei.value.cause in ("unknown", "mathlink_aborted", "unbound_model_parameters")
    assert isinstance(ei.value.unbound, list)


def test_run_driver_garbage_is_not_a_jsondecode_traceback(tmp_path):
    # The JSONDecodeError path must be caught and re-raised as EvalNoOutput.
    with pytest.raises(run_looptools.EvalNoOutput):
        _call_run_driver(tmp_path, "garbage")


def test_run_driver_unbound_names_symbols(tmp_path):
    with pytest.raises(run_looptools.EvalNoOutput) as ei:
        _call_run_driver(tmp_path, "unbound")
    assert ei.value.cause == "unbound_model_parameters"
    assert "Masshh[2](H,35)" in ei.value.unbound
    assert "gchi(DMSECTOR:2)" in ei.value.unbound


# ── End-to-end: the CLI emits the blocker, never a raw traceback ────────────

def _run_cli(tmp_path: Path, mode: str):
    cfg_home = tmp_path / "cfg"
    (cfg_home / "hephaestus").mkdir(parents=True)
    lt_dir = tmp_path / "lt"
    lt_dir.mkdir()
    fake = _fake_bin(tmp_path, mode)
    (cfg_home / "hephaestus" / "config.json").write_text(json.dumps({
        "wolfram_engine_path": str(fake),
        "looptools_path": str(lt_dir),
        "looptools_mathlink_available": "true",
        "looptools_version": "2.16",
    }))
    work = tmp_path / "fc_out"
    work.mkdir()
    import shutil
    shutil.copy(FIXTURES_DIR / "amp_reduced.m", work / "amp_reduced.m")
    shutil.copy(FIXTURES_DIR / "amp_reduced.meta.json", work / "amp_reduced.meta.json")

    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(cfg_home)
    env["HOME"] = str(tmp_path)
    args = [
        sys.executable, str(SCRIPTS_DIR / "run_looptools.py"), "eval",
        "--amp-reduced", str(work / "amp_reduced.m"),
        "--point", str(FIXTURES_DIR / "two_hdm_a_point.slha"),
        "--output-dir", str(tmp_path / "lt_out"),
    ]
    return subprocess.run(args, capture_output=True, text=True, env=env)


@pytest.mark.parametrize("mode", ["empty", "garbage", "unbound"])
def test_cli_emits_blocker_not_traceback(tmp_path, mode):
    result = _run_cli(tmp_path, mode)
    assert result.returncode != 0
    assert "LOOPTOOLS_EVAL_NO_OUTPUT" in result.stderr, result.stderr
    assert "Traceback (most recent call last)" not in result.stderr, result.stderr
    assert "JSONDecodeError" not in result.stderr, result.stderr


def test_cli_unbound_surfaces_symbol_names(tmp_path):
    result = _run_cli(tmp_path, "unbound")
    # The blocker JSON is the last stderr line.
    blocker = json.loads([ln for ln in result.stderr.splitlines() if ln.strip().startswith("{")][-1])
    assert blocker["code"] == "LOOPTOOLS_EVAL_NO_OUTPUT"
    assert blocker["context"]["cause"] == "unbound_model_parameters"
    assert "Masshh[2](H,35)" in blocker["context"]["unbound_symbols"]
