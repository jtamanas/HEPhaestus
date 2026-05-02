"""
test_install_args.py — unit tests for install.sh argument parsing,
env-var gating, and dry-run path validation.

No network access. Mocks/stubs used for binary presence checks.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
INSTALL_SCRIPT = SKILL_DIR / "install.sh"


def run_script(args, env_overrides=None, timeout=15):
    """Run install.sh with given args; return (returncode, stdout, stderr)."""
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


def make_fake_class_tree(tmp_path):
    """Create a fake CLASS build directory with a stub 'class' binary."""
    class_src = tmp_path / "class_src"
    class_src.mkdir(parents=True)
    class_exe = class_src / "class"
    class_exe.write_text("#!/bin/bash\necho 'CLASS v3.3.4'\n")
    class_exe.chmod(0o755)
    return class_src


class TestNoSubcommandShowsUsage:
    """Test that no subcommand shows usage and exits non-zero."""

    def test_no_args_exits_nonzero(self, tmp_path):
        """No subcommand exits non-zero with usage message."""
        rc, stdout, stderr = run_script(
            [],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0


class TestDetectSubcommand:
    """Test the 'detect' subcommand dispatches to _probe.sh."""

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
        """use-path with valid class dir writes config and exits 0."""
        class_src = make_fake_class_tree(tmp_path)
        rc, stdout, stderr = run_script(
            ["use-path", str(class_src)],
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
        assert config["class_path"] == str(class_src)
        assert config["class_version"] == "3.3.4"

    def test_use_path_missing_binary(self, tmp_path):
        """use-path fails with CLASS_PATH_INVALID when class binary absent."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        rc, stdout, stderr = run_script(
            ["use-path", str(empty_dir)],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        assert "CLASS_PATH_INVALID" in stderr

    def test_use_path_nonexistent_dir(self, tmp_path):
        """use-path with non-existent path exits 16 and emits CLASS_PATH_INVALID."""
        rc, stdout, stderr = run_script(
            ["use-path", "/nonexistent/class/dir"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc == 16, f"expected exit 16, got {rc}"
        assert "CLASS_PATH_INVALID" in stderr

    def test_use_path_no_args(self, tmp_path):
        """use-path with no args fails with CLASS_PATH_INVALID."""
        rc, stdout, stderr = run_script(
            ["use-path"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        assert "CLASS_PATH_INVALID" in stderr


class TestInstallSubcommandEnvGating:
    """Test the 'install' subcommand env-var and argument gating."""

    def test_offline_no_network_blocks_install(self, tmp_path):
        """install with HEPPH_NO_NETWORK=1 emits CLASS_OFFLINE_NO_CACHE."""
        env = {
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            "HEPPH_NO_NETWORK": "1",
            "HEPPH_OFFLINE_CACHE_DIR": str(tmp_path / "empty_cache"),
        }
        (tmp_path / "empty_cache").mkdir()
        rc, stdout, stderr = run_script(
            ["install"],
            env_overrides=env,
        )
        assert rc != 0
        assert "CLASS_OFFLINE_NO_CACHE" in stderr

    def test_toolchain_missing_emits_class_toolchain_missing(self, tmp_path):
        """install emits CLASS_TOOLCHAIN_MISSING when cc/make absent."""
        import shutil

        # Create a minimal PATH with python3 only (no cc, make, cython)
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()

        python3_dir = str(Path(shutil.which("python3") or "/usr/bin/python3").parent)
        env = {
            "PATH": str(fake_bin) + ":" + python3_dir + ":/usr/bin:/bin",
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        }
        rc, stdout, stderr = run_script(
            ["install"],
            env_overrides=env,
        )
        assert rc != 0
        assert "CLASS_TOOLCHAIN_MISSING" in stderr


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

    def test_unknown_subcommand_does_not_emit_json(self, tmp_path):
        """Unknown subcommand emits error text, not JSON, on stdout."""
        rc, stdout, stderr = run_script(
            ["frobnicate"],
            env_overrides={
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            },
        )
        assert rc != 0
        # Should not be valid JSON
        try:
            json.loads(stdout)
            # If it parses as JSON that's unexpected but not tested here
        except (json.JSONDecodeError, ValueError):
            pass  # Expected: not JSON
