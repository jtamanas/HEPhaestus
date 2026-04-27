"""
test_resolve_model.py — unit tests for scripts/resolve_model.py.

All tests run with isolated XDG_CONFIG_HOME + HEPPH_STATE_ROOT
(see phase2-plan-final.md §2.3).
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "resolve_model.py"
)
_CONFIG_HELPERS_DIR = (
    Path(__file__).resolve().parents[6] / "shared" / "install-helpers"
)


def _make_config(tmp_path: Path, models: dict) -> Path:
    """Write a minimal config.json under tmp_path; return its parent dir."""
    cfg_dir = tmp_path / "hephaestus"
    cfg_dir.mkdir(parents=True)
    cfg = {"models": models}
    (cfg_dir / "config.json").write_text(json.dumps(cfg))
    return tmp_path  # XDG_CONFIG_HOME


def _run_resolve(
    name: str,
    xdg_config: Path,
    state_root: Path,
    key: str | None = None,
) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_SCRIPT), name]
    if key:
        cmd += ["--key", key]
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(xdg_config)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestResolveModelHappyPath:
    def test_no_key_returns_json(self, tmp_path: Path) -> None:
        """Without --key, prints all fields as JSON."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        ufo_path = tmp_path / "ufo_dir"
        ufo_path.mkdir()
        spec_path = tmp_path / "spec.yaml"
        spec_path.write_text("spec_version: 1\n")

        xdg = _make_config(
            tmp_path / "cfg",
            {"dark_su3": {"spec": str(spec_path), "ufo": str(ufo_path)}},
        )
        result = _run_resolve("dark_su3", xdg, state_root)
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert parsed["ufo"] == str(ufo_path)

    def test_key_ufo_returns_path(self, tmp_path: Path) -> None:
        """--key ufo prints the UFO path."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        ufo_path = tmp_path / "ufo_dir"
        ufo_path.mkdir()
        spec_path = tmp_path / "spec.yaml"
        spec_path.write_text("spec_version: 1\n")

        xdg = _make_config(
            tmp_path / "cfg",
            {"dark_su3": {"spec": str(spec_path), "ufo": str(ufo_path)}},
        )
        result = _run_resolve("dark_su3", xdg, state_root, key="ufo")
        assert result.returncode == 0
        assert result.stdout.strip() == str(ufo_path)

    def test_key_latest_slha(self, tmp_path: Path) -> None:
        """--key latest_slha returns the SLHA path."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        slha_path = tmp_path / "SPheno.spc"
        slha_path.write_text("Block MASS\n")
        spec_path = tmp_path / "spec.yaml"
        spec_path.write_text("spec_version: 1\n")
        ufo_path = tmp_path / "ufo"
        ufo_path.mkdir()

        xdg = _make_config(
            tmp_path / "cfg",
            {
                "dark_su3": {
                    "spec": str(spec_path),
                    "ufo": str(ufo_path),
                    "latest_slha": str(slha_path),
                }
            },
        )
        result = _run_resolve("dark_su3", xdg, state_root, key="latest_slha")
        assert result.returncode == 0
        assert result.stdout.strip() == str(slha_path)


class TestResolveModelNotFound:
    def test_missing_model_exits_1(self, tmp_path: Path) -> None:
        """Model not in config → exit 1 with error on stderr."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        xdg = _make_config(tmp_path / "cfg", {})
        result = _run_resolve("nonexistent_model", xdg, state_root)
        assert result.returncode == 1
        assert "not registered" in result.stderr

    def test_empty_config_exits_1(self, tmp_path: Path) -> None:
        """Empty config → exit 1."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        xdg = _make_config(tmp_path / "cfg", {})
        result = _run_resolve("dark_su3", xdg, state_root)
        assert result.returncode == 1


class TestResolveModelMissingField:
    def test_missing_key_exits_2(self, tmp_path: Path) -> None:
        """Model registered but requested key absent → exit 2."""
        state_root = tmp_path / "state"
        state_root.mkdir()
        spec_path = tmp_path / "spec.yaml"
        spec_path.write_text("spec_version: 1\n")
        ufo_path = tmp_path / "ufo"
        ufo_path.mkdir()

        xdg = _make_config(
            tmp_path / "cfg",
            {"dark_su3": {"spec": str(spec_path), "ufo": str(ufo_path)}},
        )
        # latest_slha not set
        result = _run_resolve("dark_su3", xdg, state_root, key="latest_slha")
        assert result.returncode == 2
        assert "not set" in result.stderr
