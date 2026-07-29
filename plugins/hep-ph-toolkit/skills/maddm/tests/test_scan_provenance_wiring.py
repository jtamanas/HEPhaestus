"""test_scan_provenance_wiring.py — wire check_slha_provenance into
scan_sarah_dd.run_point's per-point direct_detection path, and prove the
guard is actually reachable from the real (non-pytest) production process.

Design recap (see maddm/SKILL.md "SLHA provenance check" and
scan_sarah_dd.py's in-code comment at the call site):

  * `check_slha_provenance` defaults to **guarding**: loud, fail-visible,
    meant for a single pre-DD call site (the CLI, or a future one-off
    analysis-point run) where a wrong-card mistake is a real hazard.
  * `record_only=True` switches to **recording**: compute and return the
    same result dict, but suppress every WARNING this function (and the
    `config_helpers.read_latest_slha` call it makes) would otherwise print.
    `run_point` uses this mode, because at that call site the check is
    tautological (the checked file IS the file about to be copied onto the
    card) and a "mismatch" against the model's single global `latest_slha`
    pointer is the *expected* shape of every point of a healthy `--no-register`
    scan, not a signal — warning on it would be guaranteed per-point noise.
  * Either way the guard is diagnostic-only at the scan call site: it must
    never change a point's `status` (never `fatal=True` from `run_point`),
    and an exception from the guard call must never abort the point.

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
import os
import subprocess
import sys
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


# ── (a) a registered-but-different spectrum: recorded silently, not warned ──
#
# The scan call site uses record_only=True: a scan point's SLHA differs from
# the model's single global latest_slha pointer BY CONSTRUCTION on every
# point of a healthy scan (each point is produced via --no-register), so this
# is NOT a "wrong card" signal the way a mismatch at a real pre-DD call site
# (the CLI) would be — it must stay silent. The dict is still computed
# correctly and attached to the point's result for later inspection.

def test_run_point_provenance_mismatch_recorded_silently(
    tmp_path, monkeypatch, isolated_config, capsys,
):
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
    assert "MadDM DD provenance" not in err, (
        "record_only=True must suppress the mismatch WARNING at the scan "
        "call site — a scan point differing from the global latest_slha "
        "pointer is expected, not a signal"
    )
    # But the guard still actually ran and computed the real answer — the
    # dict is recorded, just not printed.
    assert r["status"] == "ok"
    assert r["provenance"]["ok"] is False
    assert r["provenance"]["reason"] == "sha256_mismatch"


# ── (b) nothing registered (the normal scan case): also recorded silently ──
#
# record_only=True suppresses check_slha_provenance's own WARNING AND the
# separate one config_helpers.read_latest_slha prints on its own account for
# the same call (captured via contextlib.redirect_stderr inside
# check_slha_provenance) — so stderr is fully clean here, not just missing
# the "MadDM DD provenance" substring.

def test_run_point_no_registration_recorded_silently(
    tmp_path, monkeypatch, isolated_config, capsys,
):
    per_point = _write_slha(tmp_path, "point.spc", mass=321.0)
    monkeypatch.setattr(scan, "subprocess",
                        types.SimpleNamespace(run=_stub_pipeline(per_point)))

    r = scan.run_point(
        _dummy_args(tmp_path / "out"), maddm_run, _SLHA_COMPLETE_STUB,
        "mg5_stub", str(tmp_path / "ufo"), 999, "MS", 321.0, "pt0",
    )
    err = capsys.readouterr().err
    # (generate_maddm_script's unrelated UFO-path WARNING is expected here —
    # tmp_path always contains a hyphenated pytest tempdir component — and is
    # not part of the provenance check at all; assert on the absence of BOTH
    # provenance warnings specifically, not a blanket empty stderr.)
    assert "MadDM DD provenance" not in err
    assert "convenience cache" not in err, (
        "record_only=True must suppress config_helpers.read_latest_slha's "
        "own 'no cached SLHA' warning too, not just check_slha_provenance's "
        "own line"
    )
    assert r["status"] == "ok"
    assert r["provenance"]["ok"] is False
    assert r["provenance"]["reason"] == "no_registration"


# ── Exception isolation: a guard failure must never abort the point ────────

def test_run_point_survives_guard_exception(tmp_path, monkeypatch, isolated_config):
    per_point = _write_slha(tmp_path, "point.spc", mass=42.0)
    monkeypatch.setattr(scan, "subprocess",
                        types.SimpleNamespace(run=_stub_pipeline(per_point)))

    class _ExplodingMaddmRun:
        def __getattr__(self, name):
            if name == "check_slha_provenance":
                def boom(*a, **k):
                    raise RuntimeError("guard exploded")
                return boom
            return getattr(maddm_run, name)

    r = scan.run_point(
        _dummy_args(tmp_path / "out"), _ExplodingMaddmRun(), _SLHA_COMPLETE_STUB,
        "mg5_stub", str(tmp_path / "ufo"), 999, "MS", 42.0, "pt0",
    )
    assert r["status"] == "ok"
    assert r["provenance"]["ok"] is None
    assert "guard exploded" in r["provenance"]["error"]


# ── Production-path proof: config_helpers must be importable WITHOUT a
#    pytest process pre-seeding sys.modules ─────────────────────────────────
#
# Every other test above imports config_helpers at module scope (line ~40),
# which seeds sys.modules["config_helpers"] for the whole pytest process —
# so none of them can distinguish the wired guard from the inert one that
# silently falls back to reason="unverifiable". This test runs in a genuinely
# separate subprocess that never imports config_helpers directly and never
# runs under maddm/tests/conftest.py, reproducing exactly how scan_sarah_dd.py
# loads maddm_run.py in real (non-test) use: importlib.util.spec_from_file_
# location, no sys.path insertion, no pre-seeded sys.modules entry.

_PROBE_SCRIPT = """
import importlib.util, json, sys
from pathlib import Path

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

maddm_run = load("maddm_run", sys.argv[1])
result = maddm_run.check_slha_provenance(
    sys.argv[2], sys.argv[3], observables=["direct_detection"],
)
print(json.dumps(result))
"""


def test_check_slha_provenance_importable_in_production_process(tmp_path):
    """The guard must not silently degrade to reason='unverifiable' just
    because it was loaded the way scan_sarah_dd.py loads it (by file path,
    no sys.path setup, fresh interpreter with nothing pre-imported)."""
    slha = _write_slha(tmp_path, "spec.spc")
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(tmp_path / "state")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    # Deliberately do NOT put install-helpers on PYTHONPATH / sys.path here —
    # that would defeat the point of the test (self-locate must do the work).
    env.pop("PYTHONPATH", None)

    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT,
         str(_SCRIPTS / "maddm_run.py"), "singlet_doublet", str(slha)],
        env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert result["reason"] != "unverifiable", (
        "check_slha_provenance fell back to 'unverifiable' — config_helpers "
        "was not importable in a process that loaded maddm_run.py by file "
        "path the way scan_sarah_dd.py does; the self-locate fix is not "
        "working. Got: " + json.dumps(result)
    )
    # Nothing was registered for this model in the fresh isolated config, so
    # the guard should have gotten far enough to correctly report that —
    # the specific, meaningful failure mode, not a generic "can't tell".
    assert result["reason"] == "no_registration"


# ── CLI entrypoint ──────────────────────────────────────────────────────────

def _run_cli_check(tmp_path, *extra_args):
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(tmp_path / "state")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    return subprocess.run(
        [sys.executable, str(_SCRIPTS / "maddm_run.py"), "check-provenance",
         *extra_args],
        env=env, capture_output=True, text=True,
    )


def _register_in_env(tmp_path, model, slha_path, **kw):
    """Register *slha_path* for *model* against the SAME isolated
    HEPPH_STATE_ROOT/XDG_CONFIG_HOME a subprocess CLI invocation with those
    same env vars will read."""
    env = {"HEPPH_STATE_ROOT": str(tmp_path / "state"),
           "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    config_helpers._reload_roots()
    try:
        config_helpers.register_latest_slha(model, str(slha_path), **kw)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        config_helpers._reload_roots()


def test_cli_check_provenance_match_exits_zero(tmp_path):
    slha = _write_slha(tmp_path, "spec.spc")
    _register_in_env(tmp_path, "singlet_doublet", slha, point="BP1")

    proc = _run_cli_check(tmp_path, "singlet_doublet", str(slha),
                          "--observables", "direct_detection")
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out["reason"] is None


def test_cli_check_provenance_mismatch_exits_one(tmp_path):
    registered = _write_slha(tmp_path, "registered.spc", mass=1.0)
    other = _write_slha(tmp_path, "other.spc", mass=2.0)
    _register_in_env(tmp_path, "singlet_doublet", registered, point="BP1")

    proc = _run_cli_check(tmp_path, "singlet_doublet", str(other),
                          "--observables", "direct_detection")
    assert proc.returncode == 1
    assert "WARNING" in proc.stderr and "does NOT match" in proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is False
    assert out["reason"] == "sha256_mismatch"


def test_cli_check_provenance_unverifiable_exits_two(tmp_path):
    """A pre-guard registration (pointer with no recorded fingerprint) is
    ok=True/reason=unverifiable in the result dict, but must NOT exit 0 —
    an agent gating on exit code alone must not read "couldn't check" as
    "checked and clean"."""
    slha = _write_slha(tmp_path, "spec.spc")
    _register_in_env_plain(tmp_path, "singlet_doublet", str(slha))

    proc = _run_cli_check(tmp_path, "singlet_doublet", str(slha),
                          "--observables", "direct_detection")
    assert proc.returncode == 2, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is True
    assert out["reason"] == "unverifiable"


def _register_in_env_plain(tmp_path, model, slha_path):
    """Like _register_in_env but via plain register_model (pre-guard style:
    a latest_slha pointer with no latest_slha_provenance fingerprint)."""
    env = {"HEPPH_STATE_ROOT": str(tmp_path / "state"),
           "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    config_helpers._reload_roots()
    try:
        config_helpers.register_model(model, latest_slha=str(slha_path))
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        config_helpers._reload_roots()


def test_cli_check_provenance_record_only_suppresses_warning(tmp_path):
    slha = _write_slha(tmp_path, "spec.spc")
    proc = _run_cli_check(tmp_path, "singlet_doublet", str(slha),
                          "--observables", "direct_detection",
                          "--record-only")
    # record_only doesn't change the exit-code logic, only the WARNING output:
    # reason=no_registration is ok=False, same as any other mismatch -> 1.
    assert proc.returncode == 1
    assert proc.stderr.strip() == "", (
        "--record-only must suppress ALL warnings, including the separate "
        "one config_helpers.read_latest_slha prints for the same call"
    )
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["ok"] is False
    assert out["reason"] == "no_registration"
