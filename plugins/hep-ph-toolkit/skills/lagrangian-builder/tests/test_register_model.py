"""
test_register_model.py — unit tests for scripts/register_model.py.

Tests use isolated XDG_CONFIG_HOME + HEPPH_STATE_ROOT.
No real tools required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "register_model.py"
)


def _run_register(
    args: list[str],
    cfg_root: Path,
    state_root: Path,
) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_SCRIPT)] + args
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(cfg_root)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _load_config(cfg_root: Path) -> dict:
    cfg_file = cfg_root / "hephaestus" / "config.json"
    if not cfg_file.exists():
        return {}
    return json.loads(cfg_file.read_text())


class TestRegisterModelHappyPath:
    def test_basic_registration(self, tmp_path: Path) -> None:
        """Registering with spec + ufo creates the models entry."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")
        ufo = tmp_path / "ufo_dir"
        ufo.mkdir()

        result = _run_register(
            ["dark_su3", "--spec", str(spec), "--ufo", str(ufo)],
            cfg, state,
        )
        assert result.returncode == 0, result.stderr

        config = _load_config(cfg)
        assert "models" in config
        model = config["models"]["dark_su3"]
        assert model["spec"] == str(spec.resolve())
        assert model["ufo"] == str(ufo.resolve())

    def test_optional_keys_written(self, tmp_path: Path) -> None:
        """Optional flags --latest-slha, --spheno-bin, etc. are written."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")
        ufo = tmp_path / "ufo"
        ufo.mkdir()
        slha = tmp_path / "SPheno.spc"
        slha.write_text("Block MASS\n")
        sbin = tmp_path / "SphenoDarkSU3"
        sbin.write_text("#!/bin/sh\n")

        result = _run_register(
            [
                "dark_su3",
                "--spec", str(spec),
                "--ufo", str(ufo),
                "--latest-slha", str(slha),
                "--spheno-bin", str(sbin),
                "--sarah-built-at", "2026-04-18T12:00:00Z",
                "--spheno-built-at", "2026-04-18T13:00:00Z",
            ],
            cfg, state,
        )
        assert result.returncode == 0, result.stderr

        config = _load_config(cfg)
        model = config["models"]["dark_su3"]
        assert model["latest_slha"] == str(slha.resolve())
        assert model["spheno_bin"] == str(sbin.resolve())
        assert model["sarah_built_at"] == "2026-04-18T12:00:00Z"
        assert model["spheno_built_at"] == "2026-04-18T13:00:00Z"

    def test_idempotent_update(self, tmp_path: Path) -> None:
        """Registering the same model twice merges fields; existing keys preserved."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")
        ufo = tmp_path / "ufo"
        ufo.mkdir()

        # First registration
        _run_register(
            ["dark_su3", "--spec", str(spec), "--ufo", str(ufo)],
            cfg, state,
        )
        # Second registration adds latest_slha
        slha = tmp_path / "SPheno.spc"
        slha.write_text("Block MASS\n")
        _run_register(
            ["dark_su3", "--spec", str(spec), "--ufo", str(ufo),
             "--latest-slha", str(slha)],
            cfg, state,
        )

        config = _load_config(cfg)
        model = config["models"]["dark_su3"]
        assert model["ufo"] == str(ufo.resolve())
        assert model["latest_slha"] == str(slha.resolve())


class TestRegisterModelInvalidName:
    def test_invalid_name_exits_1(self, tmp_path: Path) -> None:
        """A name that fails the model-name regex causes exit 1."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")
        ufo = tmp_path / "ufo"
        ufo.mkdir()

        result = _run_register(
            ["2hdm_bad_start", "--spec", str(spec), "--ufo", str(ufo)],
            cfg, state,
        )
        assert result.returncode == 1
        assert "2hdm_bad_start" in result.stderr

    def test_name_with_uppercase_rejected(self, tmp_path: Path) -> None:
        """Uppercase names are rejected."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")
        ufo = tmp_path / "ufo"
        ufo.mkdir()

        result = _run_register(
            ["DarkSU3", "--spec", str(spec), "--ufo", str(ufo)],
            cfg, state,
        )
        assert result.returncode == 1
