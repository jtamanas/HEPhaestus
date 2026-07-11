"""Unit tests for the SARAH-model DD scan driver's pure helpers and the
UFO-path read-time validation guard."""
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    path = _SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = _load("scan_sarah_dd")
maddm_run = _load("maddm_run")


# ── parse_scan_spec ────────────────────────────────────────────────────────

def test_parse_scan_spec_linear():
    var, vals = scan.parse_scan_spec("theta=-0.17:-0.135:8")
    assert var == "theta"
    assert len(vals) == 8
    assert vals[0] == pytest.approx(-0.17)
    assert vals[-1] == pytest.approx(-0.135)


def test_parse_scan_spec_single_point():
    var, vals = scan.parse_scan_spec("x=1.5:9.0:1")
    assert vals == [1.5]


def test_parse_scan_spec_bad():
    with pytest.raises(ValueError):
        scan.parse_scan_spec("theta=-0.17:-0.135")  # missing N


# ── eval_params: the scan variable drives derived params ───────────────────

def test_eval_params_derived():
    import math
    p = scan.eval_params(
        ["MS=150", "MPsi=500", "yh1=cos(theta)", "yh2=sin(theta)"],
        "theta", -0.152,
    )
    assert p["MS"] == 150.0
    assert p["MPsi"] == 500.0
    assert p["yh1"] == pytest.approx(math.cos(-0.152))
    assert p["yh2"] == pytest.approx(math.sin(-0.152))


def test_eval_params_no_builtins():
    # eval namespace strips builtins — an attempt to reach them fails, not
    # silently returns something dangerous.
    with pytest.raises(Exception):
        scan.eval_params(["x=__import__('os').getcwd()"], "t", 0.0)


# ── validate_ufo_path: the read-time guard (item 2) ────────────────────────

def test_validate_ufo_path_clean(capsys):
    warns = maddm_run.validate_ufo_path("/abs/state/models/singlet_doublet/SingletDoublet")
    assert warns == []
    assert capsys.readouterr().err == ""


def test_validate_ufo_path_relative(capsys):
    warns = maddm_run.validate_ufo_path("demo_output/SingletDoublet")
    assert any("RELATIVE" in w for w in warns)
    assert "WARNING" in capsys.readouterr().err


def test_validate_ufo_path_hyphenated(capsys):
    warns = maddm_run.validate_ufo_path("/abs/demo_output/singlet-doublet/SingletDoublet")
    assert any("hyphen" in w.lower() for w in warns)
    assert "WARNING" in capsys.readouterr().err
