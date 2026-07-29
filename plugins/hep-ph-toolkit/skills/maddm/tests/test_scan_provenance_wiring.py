"""test_scan_provenance_wiring.py — wire check_slha_provenance into
scan_sarah_dd.run_point's per-point direct_detection path.

Every scan point is intentionally produced via SPheno's ``--no-register``
(scan_sarah_dd.py's own design note), so "nothing registered for this model"
is the expected steady state for a scan, not a signal — calling
``check_slha_provenance`` naively would print one WARNING per point, pure
noise. ``run_point`` therefore calls it with ``quiet_when_unregistered=True``:

  * a genuine sha256 mismatch against something a user actually registered
    (e.g. a real spheno-build point run before also running a scan) still
    prints the loud WARNING — that is still a meaningful "wrong card" signal
    even inside a scan;
  * the "nothing registered" case is silenced;
  * either way the guard is diagnostic-only: it must never change a point's
    ``status`` (never ``fatal=True`` from this call site).

Uses only temp dirs + env-isolated config + a fully stubbed subprocess
pipeline (spheno / mg5 setup / mg5 launch / gamlike parse) — no real MadDM /
SPheno / MG5 is ever invoked. Uses the same importlib ``_load`` convention as
``test_scan_sarah_dd.py`` (there is deliberately no ``tests/__init__.py`` in
this dir — see docs/testing.md — so a plain package-relative import would
collide with other skills' ``tests`` packages under `prepend` mode).
"""
from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path

import pytest

import config_helpers

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    path = _SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = _load("scan_sarah_dd")
maddm_run = _load("maddm_run")


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))
    config_helpers._reload_roots()
    yield
    config_helpers._reload_roots()


def _dummy_args(tmp_path):
    return types.SimpleNamespace(
        out_dir=str(tmp_path), param=[], model="singlet_doublet",
        dm_candidate="chi1", prune=False, scan_drives_only=False,
    )


def _write_slha(tmp_path, name, mass=123.0):
    p = tmp_path / name
    p.write_text(f"BLOCK MASS\n 999 {mass}\nBLOCK BSMPARAMS\n 1 1.0\n")
    return p


def _stub_pipeline(per_point_slha):
    """Fake ``subprocess.run`` covering the whole run_point pipeline (spheno /
    mg5 setup / mg5 launch / gamlike parse), enough for run_point to reach
    status='ok' while serving *per_point_slha* as the point's produced SLHA.
    """
    def fake_run(cmd, *a, **k):
        cmd = list(cmd)
        head = str(cmd[1]) if len(cmd) > 1 else ""
        if "run_spheno.py" in head:
            out = {"status": "ok", "slha_path": str(per_point_slha)}
            return types.SimpleNamespace(
                returncode=0, stdout=json.dumps(out) + "\n", stderr="")
        if len(cmd) > 2 and str(cmd[2]).endswith("setup.mg5"):
            cwd = Path(k["cwd"])
            card_dir = cwd / "maddm_run_dd" / "Cards"
            card_dir.mkdir(parents=True, exist_ok=True)
            (card_dir / "param_card.dat").write_text("placeholder\n")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if len(cmd) > 2 and str(cmd[2]).endswith("launch.mg5"):
            cwd = Path(k["cwd"])
            results_dir = cwd / "maddm_run_dd" / "output" / "run_01"
            results_dir.mkdir(parents=True, exist_ok=True)
            (results_dir / "MadDM_results.txt").write_text("dummy\n")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        if "parse_maddm_results.py" in head:
            out_path = Path(cmd[cmd.index("--out") + 1])
            out_path.write_text(json.dumps({"direct": {
                "sigma_si_proton_cm2": 1e-45, "sigma_si_neutron_cm2": 1e-45,
                "sigma_sd_proton_cm2": 1e-40, "sigma_sd_neutron_cm2": 1e-40,
            }}))
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected subprocess.run call: {cmd}")
    return fake_run


_SLHA_COMPLETE_STUB = types.SimpleNamespace(
    complete_sarah_param_card=lambda card, ufo: ["BSMPARAMS"],
)


# ── (a) a registered-but-different spectrum: mismatch still warns ──────────

def test_run_point_provenance_mismatch_warns(tmp_path, monkeypatch, isolated_config, capsys):
    registered = _write_slha(tmp_path, "registered.spc", mass=200.0)
    config_helpers.register_latest_slha("singlet_doublet", str(registered), point="BP1")

    per_point = _write_slha(tmp_path, "point.spc", mass=999.0)  # different sha256
    monkeypatch.setattr(scan, "subprocess",
                        types.SimpleNamespace(run=_stub_pipeline(per_point)))

    r = scan.run_point(
        _dummy_args(tmp_path / "out"), maddm_run, _SLHA_COMPLETE_STUB,
        "mg5_stub", str(tmp_path / "ufo"), 999, "MS", 200.0, "pt0",
    )
    err = capsys.readouterr().err
    assert "WARNING" in err and "does NOT match" in err
    # Diagnostic only: the mismatch must never fail the point.
    assert r["status"] == "ok"
    assert r["provenance"]["ok"] is False
    assert r["provenance"]["reason"] == "sha256_mismatch"


# ── (b) nothing registered (the normal scan case): silent ──────────────────
#
# NOTE: `config_helpers.read_latest_slha` (called *by* check_slha_provenance)
# prints its own separate "convenience cache: model not found / no cached
# SLHA" WARNING whenever the model has no registration at all — that is a
# distinct, lower-level warning that `quiet_when_unregistered` deliberately
# does not touch (it is in scope for `config_helpers`, not this guard, and
# other callers of `read_latest_slha` rely on it). What `quiet_when_unregistered`
# silences is specifically `check_slha_provenance`'s OWN "MadDM DD
# provenance[...]" WARNING line for the `reason="no_registration"` case — the
# one this per-scan-point call site would otherwise print once per point.

def test_run_point_no_registration_is_silent(tmp_path, monkeypatch, isolated_config, capsys):
    per_point = _write_slha(tmp_path, "point.spc", mass=321.0)
    monkeypatch.setattr(scan, "subprocess",
                        types.SimpleNamespace(run=_stub_pipeline(per_point)))

    r = scan.run_point(
        _dummy_args(tmp_path / "out"), maddm_run, _SLHA_COMPLETE_STUB,
        "mg5_stub", str(tmp_path / "ufo"), 999, "MS", 321.0, "pt0",
    )
    err = capsys.readouterr().err
    assert "MadDM DD provenance" not in err, (
        "quiet_when_unregistered must silence check_slha_provenance's own "
        "no_registration WARNING"
    )
    assert r["status"] == "ok"
    assert r["provenance"]["ok"] is False
    assert r["provenance"]["reason"] == "no_registration"


# ── CLI entrypoint ──────────────────────────────────────────────────────────

def _run_cli_check(tmp_path, *extra_args):
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(tmp_path / "state")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    return subprocess.run(
        [sys.executable, str(_SCRIPTS / "maddm_run.py"), "check-provenance",
         *extra_args],
        env=env, capture_output=True, text=True,
    )


def test_cli_check_provenance_match_exits_zero(tmp_path):
    import config_helpers as ch
    slha = _write_slha(tmp_path, "spec.spc")
    # Register against the SAME isolated config the subprocess will read.
    import os
    env = {"HEPPH_STATE_ROOT": str(tmp_path / "state"),
           "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    ch._reload_roots()
    try:
        ch.register_latest_slha("singlet_doublet", str(slha), point="BP1")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        ch._reload_roots()

    proc = _run_cli_check(tmp_path, "singlet_doublet", str(slha),
                          "--observables", "direct_detection")
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out["reason"] is None


def test_cli_check_provenance_mismatch_exits_nonzero(tmp_path):
    import os
    import config_helpers as ch
    registered = _write_slha(tmp_path, "registered.spc", mass=1.0)
    other = _write_slha(tmp_path, "other.spc", mass=2.0)
    env = {"HEPPH_STATE_ROOT": str(tmp_path / "state"),
           "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    ch._reload_roots()
    try:
        ch.register_latest_slha("singlet_doublet", str(registered), point="BP1")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        ch._reload_roots()

    proc = _run_cli_check(tmp_path, "singlet_doublet", str(other),
                          "--observables", "direct_detection")
    assert proc.returncode == 1
    assert "WARNING" in proc.stderr and "does NOT match" in proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is False
    assert out["reason"] == "sha256_mismatch"


def test_cli_check_provenance_quiet_when_unregistered(tmp_path):
    slha = _write_slha(tmp_path, "spec.spc")
    proc = _run_cli_check(tmp_path, "singlet_doublet", str(slha),
                          "--observables", "direct_detection",
                          "--quiet-when-unregistered")
    assert proc.returncode == 1  # ok=False still, just quiet
    # check_slha_provenance's own WARNING is silenced; config_helpers.
    # read_latest_slha's separate "no cached SLHA" warning is out of this
    # flag's scope (see NOTE above test_run_point_no_registration_is_silent).
    assert "MadDM DD provenance" not in proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is False
    assert out["reason"] == "no_registration"
