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


def test_eval_params_rejects_non_finite():
    # inf (via an overflowing literal) and nan must be rejected loudly.
    with pytest.raises(ValueError, match="non-finite"):
        scan.eval_params(["x=1e400"], "t", 0.0)
    with pytest.raises(ValueError, match="non-finite"):
        scan.eval_params(["x=1e400 - 1e400"], "t", 0.0)  # inf - inf = nan


@pytest.mark.parametrize("name", ["nan", "inf", "e", "gamma", "tau"])
def test_eval_params_hazard_names_removed(name):
    # Collision-prone math names are stripped from the namespace: a bare
    # reference raises NameError instead of silently computing garbage.
    with pytest.raises(NameError):
        scan.eval_params([f"x={name}"], "t", 0.0)


def test_eval_params_pi_kept():
    p = scan.eval_params(["x=pi"], "t", 0.0)
    assert p["x"] == pytest.approx(3.14159265358979)


def test_param_names_no_evaluation():
    assert scan.param_names(["MS=150", "yh1=cos(theta)"]) == ["MS", "yh1"]
    with pytest.raises(ValueError):
        scan.param_names(["MS150"])


# ── run_point: EXPR failure marks the POINT failed, scan continues ─────────

def _dummy_args(tmp_path, params):
    import types
    return types.SimpleNamespace(out_dir=str(tmp_path), param=params,
                                 model="singlet_doublet", dm_candidate="chi1",
                                 prune=True)


def test_run_point_marks_expr_failure_as_failed_point(tmp_path):
    """A per-value EXPR error returns a marked-failed dict (stage=param_eval)
    instead of raising and aborting the whole scan. No downstream tool is
    touched (module args are None and must never be reached)."""
    r = scan.run_point(_dummy_args(tmp_path, ["yh2=badname"]),
                       None, None, None, None, None, "theta", -0.15, "pt_bad")
    assert r["status"] == "failed"
    assert r["stage"] == "param_eval"
    assert "NameError" in r["stderr"]
    # No result.json → a resumed scan retries this point.
    assert not (tmp_path / "pt_bad" / "result.json").exists()


def test_run_point_marks_non_finite_as_failed_point(tmp_path):
    r = scan.run_point(_dummy_args(tmp_path, ["x=1e400"]),
                       None, None, None, None, None, "theta", 0.0, "pt_inf")
    assert r["status"] == "failed"
    assert r["stage"] == "param_eval"
    assert "non-finite" in r["stderr"]


# ── validate_ufo_path: the read-time guard (item 2) ────────────────────────

def test_validate_ufo_path_clean(capsys):
    warns = maddm_run.validate_ufo_path("/abs/state/models/singlet_doublet/SingletDoublet")
    assert warns == []
    assert capsys.readouterr().err == ""


def test_validate_ufo_path_relative_unresolvable(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)  # guarantee the path does not resolve
    warns = maddm_run.validate_ufo_path("demo_output/SingletDoublet")
    assert any("RELATIVE" in w for w in warns)
    assert "WARNING" in capsys.readouterr().err


def test_validate_ufo_path_relative_resolving_is_clean(tmp_path, monkeypatch, capsys):
    """A relative path that resolves from the CWD is legitimate — no warning."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "models" / "SingletDoublet").mkdir(parents=True)
    warns = maddm_run.validate_ufo_path("models/SingletDoublet")
    assert warns == []
    assert capsys.readouterr().err == ""


def test_validate_ufo_path_hyphenated(capsys):
    warns = maddm_run.validate_ufo_path("/abs/demo_output/singlet-doublet/SingletDoublet")
    assert any("hyphen" in w.lower() for w in warns)
    assert "WARNING" in capsys.readouterr().err


# ── CLI: --param name colliding with the scan variable is refused ──────────

def test_cli_rejects_param_shadowing_scan_var(tmp_path):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(tmp_path / "state")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS / "scan_sarah_dd.py"), "singlet_doublet",
         "--scan", "theta=-0.1:0.1:2", "--param", "theta=2.0",
         "--out-dir", str(tmp_path / "out")],
        env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 2  # argparse error
    assert "collides with the --scan variable" in proc.stderr
    assert not (tmp_path / "out").exists()  # refused before doing anything
