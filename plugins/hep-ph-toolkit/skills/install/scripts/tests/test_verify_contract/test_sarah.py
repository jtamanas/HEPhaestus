"""
test_sarah.py — verify-contract tests for install_sarah.sh.

Tests that install_sarah.sh verify outputs JSON conforming to the schema
defined in _schema.py (design-final.md §2.2 / §2.3 / §2.4).

Cases:
  1. happy path: VERSION:4.15.3 → status ok, version 4.15.3.
  2. no VERSION line → status installed_broken, hint kernel_init_m_path.
  3. wolframscript absent → status installed_broken, hint wolfram_engine_missing.

Runs the real install_sarah.sh with mock wolframscript executables.
Wolfram Engine not required.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Ensure _schema.py is importable.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _schema import validate  # noqa: E402

INSTALL_SARAH = (
    Path(__file__).parents[2] / "install_sarah.sh"
)


@pytest.fixture
def sarah_pkg(tmp_path: Path) -> Path:
    """Create a minimal SARAH package directory containing SARAH.m."""
    pkg = tmp_path / "sarah-pkg"
    pkg.mkdir()
    (pkg / "SARAH.m").touch()
    return pkg


@pytest.fixture
def mock_wolframscript_factory(tmp_path: Path):
    """Return a factory that creates mock wolframscript executables."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    def factory(
        name: str = "wolframscript",
        *,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
    ) -> Path:
        script = bin_dir / name
        # Write stdout/stderr to companion files so the mock script can cat them.
        # This avoids any quoting/escaping issues with special characters in content.
        stdout_file = bin_dir / f"{name}.stdout"
        stderr_file = bin_dir / f"{name}.stderr"
        stdout_file.write_text(stdout)
        stderr_file.write_text(stderr)
        body = textwrap.dedent(f"""\
            #!/usr/bin/env bash
            cat {str(stdout_file)!r}
            cat {str(stderr_file)!r} >&2
            exit {exit_code}
        """)
        script.write_text(body)
        script.chmod(
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        )
        return script

    return factory


def run_verify(
    sarah_pkg: Path,
    wolfram_path: str | None,
    *,
    env: dict | None = None,
    extra_args: list[str] | None = None,
    timeout: int = 10,
) -> tuple[int, dict]:
    """Run install_sarah.sh verify and return (returncode, parsed_json_payload)."""
    cmd = [str(INSTALL_SARAH), "verify", "--path", str(sarah_pkg)]
    if wolfram_path is not None:
        cmd += ["--wolfram-path", wolfram_path]
    if extra_args:
        cmd += extra_args

    run_env = os.environ.copy()
    run_env.pop("WOLFRAM_PATH", None)  # Don't inherit any real wolframscript env.
    if env:
        run_env.update(env)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )

    try:
        payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        pytest.fail(
            f"install_sarah.sh verify produced non-JSON stdout.\n"
            f"returncode={result.returncode}\n"
            f"stdout={result.stdout!r}\n"
            f"stderr={result.stderr!r}\n"
            f"parse error: {e}"
        )

    return result.returncode, payload


# ── Test cases ─────────────────────────────────────────────────────────────────


class TestSarahVerifyContract:
    """Schema-compliance tests for install_sarah.sh verify JSON output."""

    def test_happy_path(self, sarah_pkg, mock_wolframscript_factory):
        """Happy path: VERSION:4.15.3 in output → status ok, version 4.15.3."""
        mock = mock_wolframscript_factory(
            stdout="SARAH 4.15.3 loaded\nVERSION:4.15.3\n",
            exit_code=0,
        )
        rc, payload = run_verify(sarah_pkg, str(mock))

        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\npayload={payload}"

        assert rc == 0, f"Expected exit 0, got {rc}"
        assert payload["status"] == "ok"
        assert payload["ok"] is True
        assert payload["version"] == "4.15.3"
        assert payload["tool"] == "sarah"
        assert payload.get("schema_version") == 1

        # 'probe' field must be absent (design-final §2.2 forbidden keys).
        assert "probe" not in payload, "Forbidden key 'probe' present in payload"

    def test_no_version_line_installed_broken(self, sarah_pkg, mock_wolframscript_factory):
        """No VERSION: line → installed_broken with hint kernel_init_m_path."""
        mock = mock_wolframscript_factory(
            stdout="SARAH banner only\nNo version line here\n",
            exit_code=0,
        )
        rc, payload = run_verify(sarah_pkg, str(mock))

        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\npayload={payload}"

        assert rc == 15, f"Expected exit 15, got {rc}"
        assert payload["status"] == "installed_broken"
        assert payload["ok"] is False

        hint_codes = [h["code"] for h in payload.get("hints", [])]
        assert "kernel_init_m_path" in hint_codes, (
            f"Expected hint 'kernel_init_m_path', got hints: {payload.get('hints')}"
        )
        # Forbidden key check.
        assert "probe" not in payload

    def test_no_wolframscript_wolfram_engine_missing(
        self, sarah_pkg, tmp_path: Path
    ):
        """No --wolfram-path and no wolframscript on PATH → wolfram_engine_missing hint."""
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()

        rc, payload = run_verify(
            sarah_pkg,
            wolfram_path=None,  # No --wolfram-path.
            env={
                "PATH": f"{empty_bin}:/usr/bin:/bin",
                "HOME": str(fake_home),
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "HEPPH_WOLFRAM_USER_BASE": str(tmp_path / "wolfram-base"),
            },
        )

        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\npayload={payload}"

        assert rc == 15, f"Expected exit 15, got {rc}"
        assert payload["status"] == "installed_broken"
        assert payload["ok"] is False

        hint_codes = [h["code"] for h in payload.get("hints", [])]
        assert "wolfram_engine_missing" in hint_codes, (
            f"Expected hint 'wolfram_engine_missing', got hints: {payload.get('hints')}"
        )
        # Forbidden key check.
        assert "probe" not in payload

    def test_missing_sarah_path(self, tmp_path: Path, mock_wolframscript_factory):
        """Path exists but no SARAH.m → status missing, exit 16."""
        empty_dir = tmp_path / "empty-pkg"
        empty_dir.mkdir()
        mock = mock_wolframscript_factory(stdout="", exit_code=0)

        rc, payload = run_verify(empty_dir, str(mock))

        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\npayload={payload}"

        assert rc == 16, f"Expected exit 16, got {rc}"
        assert payload["status"] == "missing"
        assert payload["ok"] is False
        assert "probe" not in payload

    def test_expected_version_present_when_flag_supplied(
        self, sarah_pkg, mock_wolframscript_factory
    ):
        """When --expected-version is supplied, expected_version appears in payload."""
        mock = mock_wolframscript_factory(
            stdout="SARAH 4.15.3 loaded\nVERSION:4.15.3\n",
            exit_code=0,
        )
        rc, payload = run_verify(
            sarah_pkg, str(mock), extra_args=["--expected-version", "4.15.3"]
        )
        assert "expected_version" in payload, (
            f"expected_version should be present when --expected-version flag used"
        )
        assert payload["expected_version"] == "4.15.3"

        errors = validate(payload)
        assert errors == [], f"Schema errors: {errors}\npayload={payload}"

    def test_expected_version_absent_when_flag_omitted(
        self, sarah_pkg, mock_wolframscript_factory
    ):
        """When --expected-version is omitted, expected_version absent from payload."""
        mock = mock_wolframscript_factory(
            stdout="SARAH 4.15.3 loaded\nVERSION:4.15.3\n",
            exit_code=0,
        )
        rc, payload = run_verify(sarah_pkg, str(mock))
        assert "expected_version" not in payload, (
            f"expected_version should be absent when --expected-version flag not used"
        )

    def test_schema_version_always_present(
        self, sarah_pkg, mock_wolframscript_factory
    ):
        """schema_version=1 must be present in all responses."""
        mock = mock_wolframscript_factory(
            stdout="SARAH 4.15.3 loaded\nVERSION:4.15.3\n",
            exit_code=0,
        )
        _, payload = run_verify(sarah_pkg, str(mock))
        assert payload.get("schema_version") == 1
