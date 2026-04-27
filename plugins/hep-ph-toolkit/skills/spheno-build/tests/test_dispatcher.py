"""test_dispatcher.py — Unit tests for dispatcher.dispatch (WS-A §8.1)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"


def _load(name: str, p: Path):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def dispatcher_mod():
    return _load("dispatcher", _SCRIPTS / "dispatcher.py")


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    (tmp_path / "state").mkdir()
    (tmp_path / "cfg").mkdir()


class TestDefaultBackend:
    def test_default_backend_is_spheno_when_outputs_has_spheno(self, dispatcher_mod, tmp_path):
        spec = {"outputs": ["ufo", "spheno"]}
        assert dispatcher_mod._resolve_backend_name(spec) == "spheno"

    def test_explicit_analytic_overrides(self, dispatcher_mod):
        spec = {"outputs": ["ufo", "spheno"], "backends": {"spectrum": "analytic"}}
        assert dispatcher_mod._resolve_backend_name(spec) == "analytic"

    def test_default_falls_back_to_analytic_when_no_spheno(self, dispatcher_mod):
        spec = {"outputs": ["ufo"]}
        assert dispatcher_mod._resolve_backend_name(spec) == "analytic"


class TestAnalyticMissingModule:
    def test_unregistered_model_emits_ANALYTIC_MODULE_MISSING(self, dispatcher_mod, tmp_path, capsys):
        spec = {"outputs": ["ufo"], "backends": {"spectrum": "analytic"}}
        r = dispatcher_mod.dispatch(
            model_name="no_such_model",
            spec=spec,
            params={},
            out_dir=tmp_path / "run",
            config={},
        )
        assert r["status"] == "fatal"
        assert r["blocker_code"] == "ANALYTIC_MODULE_MISSING"


class TestAnalyticSingletDoublet:
    def test_singlet_doublet_analytic_runs_cleanly(self, dispatcher_mod, tmp_path):
        spec = {"outputs": ["ufo"], "backends": {"spectrum": "analytic"}}
        r = dispatcher_mod.dispatch(
            model_name="singlet_doublet",
            spec=spec,
            params={"MS": 150.0, "MPsi": 500.0, "yh1": 0.5, "yh2": 0.3},
            out_dir=tmp_path / "run",
            config={},
        )
        assert r["status"] == "ok"
        assert r["backend"] == "analytic"
        assert "9958431" in r["summary"]["masses"] or 9958431 in r["summary"]["masses"]


class TestSphenoDelegation:
    def test_missing_leshouches_returns_fatal(self, dispatcher_mod, tmp_path):
        spec = {"outputs": ["ufo", "spheno"]}  # spheno is default
        r = dispatcher_mod.dispatch(
            model_name="anything",
            spec=spec,
            params={},
            out_dir=tmp_path / "nolh",
            config={},
        )
        assert r["backend"] == "spheno"
        assert r["status"] == "fatal"
        assert r["blocker_code"] == "SPHENO_NO_OUTPUT"
