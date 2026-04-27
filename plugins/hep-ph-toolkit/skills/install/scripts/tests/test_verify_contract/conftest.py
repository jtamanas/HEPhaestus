"""
Shared fixtures for verify-contract tests.

WS0 provides the minimal scaffold; WS1-WS4 append tool-specific fixtures.
"""

from __future__ import annotations

import os
import stat
import sys
import textwrap
from pathlib import Path

import pytest

# Ensure this package directory is importable so _schema.py resolves.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


@pytest.fixture
def mock_script_factory(tmp_path: Path):
    """Return a factory that creates executable mock scripts in a tmp dir.

    Usage:
        script = mock_script_factory("wolframscript", exit_code=0, stdout="4\\n14.1.0\\n")
        # script is an absolute path to an executable file in tmp_path/bin/

    The factory places each script in ``tmp_path / "bin"`` so callers can
    prepend that directory to PATH:
        monkeypatch.setenv("PATH", str(tmp_path / "bin") + ":" + os.environ["PATH"])
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    def factory(
        name: str,
        *,
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> Path:
        """Create a mock executable named *name* in tmp_path/bin/.

        Args:
            name:      Filename of the mock script (e.g. ``"wolframscript"``).
            exit_code: The script's exit status.
            stdout:    Text written to stdout before exiting.
            stderr:    Text written to stderr before exiting.

        Returns:
            Absolute ``Path`` to the created script.
        """
        script_path = bin_dir / name
        stdout_escaped = stdout.replace("'", "'\\''")
        stderr_escaped = stderr.replace("'", "'\\''")
        body = textwrap.dedent(f"""\
            #!/usr/bin/env bash
            printf '%s' '{stdout_escaped}'
            printf '%s' '{stderr_escaped}' >&2
            exit {exit_code}
        """)
        script_path.write_text(body)
        script_path.chmod(
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        )
        return script_path

    return factory
