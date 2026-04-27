"""
test_install_args.py — unit tests for install_higgstools.sh argument parsing,
env-var gating, and dry-run path validation.

No network access. Mocks/stubs used for binary presence checks.
"""
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
INSTALL_SCRIPT = SCRIPTS_DIR / "install_higgstools.sh"


def run_script(args, env_overrides=None, timeout=15):
    """Run install_higgstools.sh with given args; return (returncode, stdout, stderr)."""
    env = {**os.environ}
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        ["bash", str(INSTALL_SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def make_fake_tree(tmp_path, with_hb=True, with_hs=True):
    """Create fake HB/HS build directories with stub binaries."""
    hb_bin = tmp_path / "hb" / "build" / "bin"
    hs_bin = tmp_path / "hs" / "build" / "bin"
    hb_bin.mkdir(parents=True)
    hs_bin.mkdir(parents=True)

    if with_hb:
        hb_exe = hb_bin / "HiggsBounds"
        hb_exe.write_text("#!/bin/bash\n")
        hb_exe.chmod(0o755)

    if with_hs:
        hs_exe = hs_bin / "HiggsSignals"
        hs_exe.write_text("#!/bin/bash\n")
        hs_exe.chmod(0o755)

    return tmp_path / "hb" / "build", tmp_path / "hs" / "build"


class TestDetectSubcommand:
    """Test the 'detect' subcommand dispatches to detect_higgstools.sh."""

    def test_detect_returns_json(self, tmp_path):
        """detect subcommand returns valid JSON with a status field."""
        rc, stdout, stderr = run_script(
            ["detect"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc == 0, f"detect failed: {stderr}"
        data = json.loads(stdout)
        assert "status" in data

    def test_detect_missing_when_no_config(self, tmp_path):
        """detect returns missing when no config or tools present."""
        rc, stdout, stderr = run_script(
            ["detect"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc == 0
        data = json.loads(stdout)
        assert data["status"] == "missing"


class TestUsePathSubcommand:
    """Test the 'use-path' subcommand."""

    def test_use_path_success(self, tmp_path):
        """use-path with valid HB+HS dirs writes config and exits 0."""
        hb_dir, hs_dir = make_fake_tree(tmp_path)
        rc, stdout, stderr = run_script(
            ["use-path", str(hb_dir), str(hs_dir)],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc == 0, f"use-path failed: {stderr}"
        # Config should be written
        cfg_file = tmp_path / "cfg" / "hephaestus" / "config.json"
        assert cfg_file.exists(), "config.json was not created"
        config = json.loads(cfg_file.read_text())
        assert config["higgstools_backend"] == "legacy"
        assert config["higgsbounds_path"] == str(hb_dir)
        assert config["higgssignals_path"] == str(hs_dir)

    def test_use_path_missing_hb_binary(self, tmp_path):
        """use-path fails with HIGGSTOOLS_PATH_INVALID when HB binary absent."""
        _, hs_dir = make_fake_tree(tmp_path, with_hb=False)
        hb_dir = tmp_path / "hb" / "build"
        hb_dir.mkdir(parents=True, exist_ok=True)
        rc, stdout, stderr = run_script(
            ["use-path", str(hb_dir), str(hs_dir)],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        assert "HIGGSTOOLS_PATH_INVALID" in stderr

    def test_use_path_missing_hs_binary(self, tmp_path):
        """use-path fails with HIGGSTOOLS_PATH_INVALID when HS binary absent."""
        hb_dir, _ = make_fake_tree(tmp_path, with_hs=False)
        hs_dir = tmp_path / "hs" / "build"
        hs_dir.mkdir(parents=True, exist_ok=True)
        rc, stdout, stderr = run_script(
            ["use-path", str(hb_dir), str(hs_dir)],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        assert "HIGGSTOOLS_PATH_INVALID" in stderr

    def test_use_path_no_args(self, tmp_path):
        """use-path with no args fails with HIGGSTOOLS_PATH_INVALID."""
        rc, stdout, stderr = run_script(
            ["use-path"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        assert "HIGGSTOOLS_PATH_INVALID" in stderr


class TestInstallSubcommandEnvGating:
    """Test the 'install' subcommand env-var and argument gating."""

    def test_unified_backend_requires_env_var(self, tmp_path):
        """install --backend=unified without HEPPH_HIGGSTOOLS_BACKEND=unified fails with recoverable blocker."""
        env = {
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            "HEPPH_NO_NETWORK": "1",  # prevent any actual network access
            "HEPPH_OFFLINE_CACHE_DIR": str(tmp_path / "cache"),
        }
        # Ensure HEPPH_HIGGSTOOLS_BACKEND is not set
        env.pop("HEPPH_HIGGSTOOLS_BACKEND", None)
        rc, stdout, stderr = run_script(
            ["install", "--backend=unified"],
            env_overrides=env,
        )
        assert rc != 0
        assert "HIGGSTOOLS_BACKEND_UNAVAILABLE" in stderr

    def test_offline_no_network_blocks_install(self, tmp_path):
        """install with HEPPH_NO_NETWORK=1 emits HIGGSTOOLS_OFFLINE_NO_CACHE."""
        env = {
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            "HEPPH_NO_NETWORK": "1",
            "HEPPH_OFFLINE_CACHE_DIR": str(tmp_path / "empty_cache"),
        }
        (tmp_path / "empty_cache").mkdir()
        rc, stdout, stderr = run_script(
            ["install", "--backend=legacy"],
            env_overrides=env,
        )
        assert rc != 0
        assert "HIGGSTOOLS_OFFLINE_NO_CACHE" in stderr

    def test_install_no_gfortran_emits_toolchain_blocker(self, tmp_path):
        """install emits HIGGSTOOLS_TOOLCHAIN_MISSING when gfortran absent."""
        import shutil
        # Create a PATH with cmake but no gfortran; preserve python3 location
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        cmake_stub = fake_bin / "cmake"
        cmake_stub.write_text("#!/bin/bash\necho 'cmake 3.20'\n")
        cmake_stub.chmod(0o755)

        # Build a PATH that has python3 but not gfortran
        python3_dir = str(Path(shutil.which("python3") or "/usr/bin/python3").parent)
        env = {
            "PATH": str(fake_bin) + ":" + python3_dir + ":/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        }
        rc, stdout, stderr = run_script(
            ["install", "--backend=legacy"],
            env_overrides=env,
        )
        assert rc != 0
        assert "HIGGSTOOLS_TOOLCHAIN_MISSING" in stderr

    def test_install_no_cmake_emits_toolchain_blocker(self, tmp_path):
        """install emits HIGGSTOOLS_TOOLCHAIN_MISSING when cmake absent."""
        import shutil
        # Create a PATH with gfortran but no cmake; preserve python3 location
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        gfortran_stub = fake_bin / "gfortran"
        gfortran_stub.write_text("#!/bin/bash\necho 'gfortran 12'\n")
        gfortran_stub.chmod(0o755)

        python3_dir = str(Path(shutil.which("python3") or "/usr/bin/python3").parent)
        env = {
            "PATH": str(fake_bin) + ":" + python3_dir + ":/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        }
        rc, stdout, stderr = run_script(
            ["install", "--backend=legacy"],
            env_overrides=env,
        )
        assert rc != 0
        assert "HIGGSTOOLS_TOOLCHAIN_MISSING" in stderr


class TestUnknownSubcommand:
    """Test unknown subcommands."""

    def test_unknown_subcommand_exits_nonzero(self, tmp_path):
        """Unknown subcommand exits with non-zero."""
        rc, stdout, stderr = run_script(
            ["frobnicate"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
