"""
test_check_state.py — unit tests for scripts/check_state.py.

Each test uses isolated XDG_CONFIG_HOME and HEPPH_STATE_ROOT directories.
No real tools required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "check_state.py"
)


def _write_config(cfg_root: Path, data: dict) -> None:
    hep_dir = cfg_root / "hephaestus"
    hep_dir.mkdir(parents=True, exist_ok=True)
    (hep_dir / "config.json").write_text(json.dumps(data))


def _run_check_state(
    cfg_root: Path,
    state_root: Path,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_SCRIPT)] + (extra_args or [])
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(cfg_root)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestEmptyConfig:
    def test_all_missing(self, tmp_path: Path) -> None:
        """Empty config → all statuses missing."""
        cfg = tmp_path / "cfg"
        cfg.mkdir()
        state = tmp_path / "state"
        state.mkdir()
        result = _run_check_state(cfg, state)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        assert out["sarah_install"] == "missing"
        assert out["spheno_install"] == "missing"
        assert out["wolfram_install"] == "missing"
        assert out["model"]["status"] == "missing"
        assert out["model"]["name"] is None


class TestSARAHConfigured:
    def test_sarah_configured_when_dir_and_sarah_m_exist(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        # Create a fake SARAH package dir with SARAH.m
        sarah_dir = tmp_path / "SARAH"
        sarah_dir.mkdir()
        (sarah_dir / "SARAH.m").write_text("(* fake *)")

        _write_config(cfg, {"sarah_path": str(sarah_dir)})
        result = _run_check_state(cfg, state)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        assert out["sarah_install"] == "configured"

    def test_sarah_missing_when_sarah_m_absent(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()
        # Dir exists but no SARAH.m
        sarah_dir = tmp_path / "SARAH"
        sarah_dir.mkdir()
        _write_config(cfg, {"sarah_path": str(sarah_dir)})
        result = _run_check_state(cfg, state)
        out = json.loads(result.stdout)
        assert out["sarah_install"] == "missing"


class TestSphenoConfigured:
    def test_spheno_configured_when_binary_executable(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spheno_bin = tmp_path / "SPheno"
        spheno_bin.write_text("#!/bin/sh\necho SPheno\n")
        spheno_bin.chmod(0o755)

        _write_config(cfg, {"spheno_path": str(spheno_bin)})
        result = _run_check_state(cfg, state)
        out = json.loads(result.stdout)
        assert out["spheno_install"] == "configured"

    def test_spheno_missing_when_not_executable(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spheno_bin = tmp_path / "SPheno"
        spheno_bin.write_text("#!/bin/sh\n")
        spheno_bin.chmod(0o644)  # not executable

        _write_config(cfg, {"spheno_path": str(spheno_bin)})
        result = _run_check_state(cfg, state)
        out = json.loads(result.stdout)
        assert out["spheno_install"] == "missing"


class TestModelFlag:
    def test_model_present_when_spec_path_exists(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")

        _write_config(
            cfg,
            {"models": {"dark_su3": {"spec": str(spec), "ufo": "/some/path"}}},
        )
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "present"
        assert out["model"]["name"] == "dark_su3"

    def test_model_missing_when_not_registered(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()
        _write_config(cfg, {})
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "missing"

    def test_model_missing_when_spec_file_absent(self, tmp_path: Path) -> None:
        """Registered but spec file deleted → status missing."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        _write_config(
            cfg,
            {"models": {"dark_su3": {"spec": "/nonexistent/spec.yaml"}}},
        )
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "missing"
