"""
Contract tests for install_spheno.sh verify.

Verifies that the JSON output from cmd_verify conforms to the schema
defined in design-final.md §2 (_schema.py).

Cases:
  - happy:  banner + version → ok, version extracted
  - dylib:  image-not-found output → installed_broken, shared_library_missing hint
  - garbage: unrecognized output → installed_broken
  - missing: non-existent path → missing, path_not_found hint
  - not_configured: no path + empty config → not_configured, exit 17
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure _schema is importable.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _schema import validate  # noqa: E402

# Path to install_spheno.sh relative to this test file.
# test_spheno.py is at: scripts/tests/test_verify_contract/test_spheno.py
# install_spheno.sh is at: scripts/install_spheno.sh
# So: parent (test_verify_contract) → parent (tests) → parent (scripts)
_SCRIPTS = Path(__file__).parent.parent.parent
_INSTALL_SPHENO = _SCRIPTS / "install_spheno.sh"


def run_verify(mock_bin: Path | None, extra_args: list[str] | None = None, env_extra: dict | None = None) -> tuple[int, dict]:
    """Run install_spheno.sh verify, return (returncode, parsed_json_payload)."""
    tmp_home = Path(pytest.importorskip("tempfile").mkdtemp())
    tmp_cfg = Path(pytest.importorskip("tempfile").mkdtemp())

    cmd = ["bash", str(_INSTALL_SPHENO), "verify"]
    if mock_bin is not None:
        cmd += ["--path", str(mock_bin)]
    if extra_args:
        cmd += extra_args

    env = os.environ.copy()
    env["HOME"] = str(tmp_home)
    env["XDG_CONFIG_HOME"] = str(tmp_cfg)
    if env_extra:
        env.update(env_extra)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = result.stdout.strip()
    assert stdout, f"stdout was empty (rc={result.returncode}, stderr={result.stderr!r})"
    payload = json.loads(stdout)
    return result.returncode, payload


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def happy_spheno(mock_script_factory) -> Path:
    """Mock SPheno that prints a banner with version and exits 1."""
    return mock_script_factory(
        "SPheno",
        exit_code=1,
        stdout="SPheno v4.0.5\nusage: SPheno <input file>\n",
    )


@pytest.fixture
def dylib_spheno(mock_script_factory) -> Path:
    """Mock SPheno that prints a dylib load failure and exits 1."""
    return mock_script_factory(
        "SPheno",
        exit_code=1,
        stdout=(
            "dyld: Library not loaded: @rpath/libifcore.dylib\n"
            "Reason: image not found\n"
        ),
    )


@pytest.fixture
def garbage_spheno(mock_script_factory) -> Path:
    """Mock SPheno that prints garbage (not a banner) and exits 1."""
    return mock_script_factory(
        "SPheno",
        exit_code=1,
        stdout="some unexpected error\n",
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHappy:
    def test_exit_code(self, happy_spheno):
        rc, _ = run_verify(happy_spheno)
        assert rc == 0

    def test_schema_valid(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\nPayload: {payload}"

    def test_ok_true(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert payload["ok"] is True

    def test_status_ok(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert payload["status"] == "ok"

    def test_tool_spheno(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert payload["tool"] == "spheno"

    def test_schema_version(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert payload["schema_version"] == 1

    def test_version_extracted(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert payload["version"] == "4.0.5"

    def test_no_probe_field(self, happy_spheno):
        _, payload = run_verify(happy_spheno)
        assert "probe" not in payload

    def test_one_stdout_line(self, happy_spheno):
        """stdout must be exactly one line (no stray log lines)."""
        tmp_home = Path(pytest.importorskip("tempfile").mkdtemp())
        tmp_cfg = Path(pytest.importorskip("tempfile").mkdtemp())
        env = os.environ.copy()
        env["HOME"] = str(tmp_home)
        env["XDG_CONFIG_HOME"] = str(tmp_cfg)
        result = subprocess.run(
            ["bash", str(_INSTALL_SPHENO), "verify", "--path", str(happy_spheno)],
            capture_output=True, text=True, env=env,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        assert len(lines) == 1, f"Expected 1 stdout line, got {len(lines)}: {result.stdout!r}"


class TestDylib:
    def test_exit_nonzero(self, dylib_spheno):
        rc, _ = run_verify(dylib_spheno)
        assert rc != 0

    def test_schema_valid(self, dylib_spheno):
        _, payload = run_verify(dylib_spheno)
        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\nPayload: {payload}"

    def test_ok_false(self, dylib_spheno):
        _, payload = run_verify(dylib_spheno)
        assert payload["ok"] is False

    def test_status_installed_broken(self, dylib_spheno):
        _, payload = run_verify(dylib_spheno)
        assert payload["status"] == "installed_broken"

    def test_hint_shared_library_missing(self, dylib_spheno):
        _, payload = run_verify(dylib_spheno)
        hints = payload.get("hints", [])
        codes = [h["code"] for h in hints]
        assert "shared_library_missing" in codes, (
            f"Expected shared_library_missing in hints, got: {codes}"
        )

    def test_no_probe_field(self, dylib_spheno):
        _, payload = run_verify(dylib_spheno)
        assert "probe" not in payload


class TestGarbage:
    def test_exit_nonzero(self, garbage_spheno):
        rc, _ = run_verify(garbage_spheno)
        assert rc != 0

    def test_schema_valid(self, garbage_spheno):
        _, payload = run_verify(garbage_spheno)
        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\nPayload: {payload}"

    def test_ok_false(self, garbage_spheno):
        _, payload = run_verify(garbage_spheno)
        assert payload["ok"] is False

    def test_status_installed_broken(self, garbage_spheno):
        _, payload = run_verify(garbage_spheno)
        assert payload["status"] == "installed_broken"

    def test_no_probe_field(self, garbage_spheno):
        _, payload = run_verify(garbage_spheno)
        assert "probe" not in payload


class TestMissing:
    def test_exit_16(self):
        rc, _ = run_verify(Path("/does/not/exist/SPheno"))
        assert rc == 16

    def test_schema_valid(self):
        _, payload = run_verify(Path("/does/not/exist/SPheno"))
        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\nPayload: {payload}"

    def test_status_missing(self):
        _, payload = run_verify(Path("/does/not/exist/SPheno"))
        assert payload["status"] == "missing"

    def test_hint_path_not_found(self):
        _, payload = run_verify(Path("/does/not/exist/SPheno"))
        hints = payload.get("hints", [])
        codes = [h["code"] for h in hints]
        assert "path_not_found" in codes, (
            f"Expected path_not_found in hints, got: {codes}"
        )


class TestNotConfigured:
    def test_exit_17(self):
        rc, _ = run_verify(None)
        assert rc == 17

    def test_schema_valid(self):
        _, payload = run_verify(None)
        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\nPayload: {payload}"

    def test_status_not_configured(self):
        _, payload = run_verify(None)
        assert payload["status"] == "not_configured"
