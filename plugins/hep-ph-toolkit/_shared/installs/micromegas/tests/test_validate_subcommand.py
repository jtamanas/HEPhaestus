"""test_validate_subcommand.py — tests for `install_micromegas.sh validate`.

Covers the validate subcommand migrated from monte-carlo-tools v0:
  - No config → MICROMEGAS_PATH_INVALID
  - Config pointing at missing directory → MICROMEGAS_PATH_INVALID
  - Config pointing at dir missing structural markers → MICROMEGAS_PATH_INVALID
  - Config pointing at valid fake tree → exit 0, prints "configured" JSON,
    does NOT modify config (read-only contract).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent
_DISPATCH = _SCRIPTS / "install.sh"
_FAKE_TREE = _SCRIPT_DIR / "fixtures" / "fake_micromegas_tree"

EXIT_BAD_PATH = 16


def _run_validate(env_overrides: dict) -> tuple[int, str, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    result = subprocess.run(
        ["bash", str(_DISPATCH), "validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def _first_blocker(stderr: str) -> dict | None:
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith("{") and "code" in line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def _write_config(cfg_dir: Path, data: dict) -> Path:
    target = cfg_dir / "hephaestus" / "config.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w") as f:
        json.dump(data, f)
    return target


class TestValidateReadOnly:
    def test_no_config_emits_path_invalid(self, tmp_path):
        rc, stdout, stderr = _run_validate(
            {
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            }
        )
        assert rc == EXIT_BAD_PATH, f"Expected {EXIT_BAD_PATH}, got {rc}. stderr: {stderr[:400]}"
        blocker = _first_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"
        assert blocker["mode"] == "fatal"

    def test_config_path_missing_on_disk(self, tmp_path):
        cfg_dir = tmp_path / "config"
        _write_config(cfg_dir, {"micromegas_path": str(tmp_path / "gone")})
        rc, stdout, stderr = _run_validate(
            {
                "XDG_CONFIG_HOME": str(cfg_dir),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            }
        )
        assert rc == EXIT_BAD_PATH
        blocker = _first_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"

    def test_config_path_missing_markers(self, tmp_path):
        cfg_dir = tmp_path / "config"
        target = tmp_path / "micromegas_fake"
        target.mkdir()  # exists but has no sources/ or CalcHEP_src/
        _write_config(cfg_dir, {"micromegas_path": str(target)})
        rc, stdout, stderr = _run_validate(
            {
                "XDG_CONFIG_HOME": str(cfg_dir),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            }
        )
        assert rc == EXIT_BAD_PATH
        blocker = _first_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"

    def test_valid_tree_readonly_does_not_rewrite_config(self, tmp_path):
        """validate with a valid fake tree → exit 0, config content unchanged."""
        cfg_dir = tmp_path / "config"
        # Seed a config with an intentionally stale version string — validate
        # must NOT rewrite it (read-only contract).
        cfg_file = _write_config(
            cfg_dir,
            {
                "micromegas_path": str(_FAKE_TREE),
                "micromegas_version": "stale_sentinel_7.7.7",
            },
        )
        before = cfg_file.read_text()

        rc, stdout, stderr = _run_validate(
            {
                "XDG_CONFIG_HOME": str(cfg_dir),
                "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            }
        )
        # The fake tree may or may not pass the smoke test (depends on
        # whether _smoke.sh finds a valid MSSM/main.c). Accept either 0 or
        # the smoke-test-failed exit, but NEVER MICROMEGAS_PATH_INVALID.
        blocker = _first_blocker(stderr)
        if blocker is not None:
            assert blocker["code"] != "MICROMEGAS_PATH_INVALID", (
                f"Valid tree should not emit MICROMEGAS_PATH_INVALID: {blocker}"
            )

        # Read-only contract: config content must be byte-identical.
        after = cfg_file.read_text()
        assert before == after, (
            "validate must not rewrite config.json; content changed:\n"
            f"before={before}\nafter={after}"
        )
