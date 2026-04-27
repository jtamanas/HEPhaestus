"""
Contract tests for install_wolfram.sh verify.

Invokes the real install_wolfram.sh verify subcommand with mock wolframscript
binaries provided by the mock_script_factory fixture, then validates the JSON
output against _schema.validate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure _schema.py is importable from this package directory.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _schema import validate  # noqa: E402

# Absolute path to install_wolfram.sh
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent.parent.parent  # ws1-wolfram root
_INSTALL_SCRIPT = (
    _HERE.parent.parent / "install_wolfram.sh"
)


def _run_verify(args: list[str], env: dict | None = None) -> tuple[int, dict]:
    """Run install_wolfram.sh verify with given extra args.

    Returns (exit_code, parsed_json_dict).
    Raises if stdout is not valid JSON.
    """
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(
        ["bash", str(_INSTALL_SCRIPT), "verify", *args],
        capture_output=True,
        text=True,
        env=merged_env,
    )
    stdout = result.stdout.strip()
    if not stdout:
        pytest.fail(
            f"install_wolfram.sh verify produced no stdout.\n"
            f"exit={result.returncode}\nstderr={result.stderr[:500]}"
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"stdout is not valid JSON: {exc}\nstdout={stdout!r}")
    return result.returncode, payload


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_happy_path_validates(mock_script_factory, tmp_path):
    """Happy-path mock: Print[2+2] → 4, Print[$Version] → 14.1 line."""
    mock_ws = mock_script_factory(
        "wolframscript",
        exit_code=0,
        stdout="4\n14.1 for MacOSX-ARM64\n",
    )
    # Redirect config home to a temp dir with no config file
    env = {"XDG_CONFIG_HOME": str(tmp_path / "config")}
    rc, payload = _run_verify(["--path", str(mock_ws)], env=env)

    assert rc == 0, f"Expected exit 0, got {rc}. payload={payload}"
    errors = validate(payload)
    assert errors == [], f"Schema validation errors: {errors}"
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["tool"] == "wolfram"
    assert payload["schema_version"] == 1
    assert payload["version"] == "14.1"
    # expected_version must be absent when not supplied
    assert "expected_version" not in payload, "expected_version should be absent when not supplied"
    # probe must be absent
    assert "probe" not in payload, "forbidden key 'probe' must not appear"


def test_activation_banner_validates(mock_script_factory, tmp_path):
    """Activation-banner mock: stdout has 'activate' text, exit 1."""
    mock_ws = mock_script_factory(
        "wolframscript",
        exit_code=1,
        stdout="Wolfram Engine requires activation. Please activate your license.\n",
    )
    env = {"XDG_CONFIG_HOME": str(tmp_path / "config")}
    rc, payload = _run_verify(["--path", str(mock_ws)], env=env)

    assert rc != 0, f"Expected non-zero exit for broken install, got {rc}"
    errors = validate(payload)
    assert errors == [], f"Schema validation errors: {errors}"
    assert payload["ok"] is False
    assert payload["status"] == "installed_broken"
    assert payload["tool"] == "wolfram"
    assert payload["schema_version"] == 1
    # hint code must be wolfram_not_activated
    hints = payload.get("hints", [])
    assert len(hints) >= 1, "Expected at least one hint for activation banner"
    assert hints[0]["code"] == "wolfram_not_activated", (
        f"Expected hint code 'wolfram_not_activated', got {hints[0]['code']!r}"
    )
    # schema validates the hint code too
    errors2 = validate(payload)
    assert errors2 == [], f"Schema re-validation errors: {errors2}"
