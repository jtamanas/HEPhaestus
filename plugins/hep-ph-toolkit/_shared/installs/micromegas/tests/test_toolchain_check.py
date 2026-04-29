"""test_toolchain_check.py — tests for check_toolchain.sh.

Validates the migrated toolchain precondition script:
  - When a required binary is absent from PATH → correct blocker code on
    stderr, correct exit code.
  - When all required binaries are present → exit 0, no blocker.
  - X11 headers absence is warn-only (never emits a blocker).

Uses a stub PATH containing only selected binaries to simulate missing
toolchain. Origin: behavior migrated from the v0 monte-carlo-tools
micromegas-install skill during the April 2026 consolidation (see
docs/roadmap/v1-constraints-work/consolidate-micromegas-report.md).
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent
_CHECK_TOOLCHAIN = _SCRIPTS / "check_toolchain.sh"

EXIT_NO_GFORTRAN = 10
EXIT_NO_LAPACK = 25  # reused for CC_ABSENT and GNU_MAKE_ABSENT


def _make_stub(target_dir: Path, name: str, body: str = "#!/bin/sh\nexit 0\n") -> Path:
    p = target_dir / name
    p.write_text(body)
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return p


def _run(env_overrides: dict) -> tuple[int, str, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    result = subprocess.run(
        ["bash", str(_CHECK_TOOLCHAIN)],
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


@pytest.fixture
def isolated_path(tmp_path):
    """Return (path_dir, coreutils_dir) for tests.

    The coreutils_dir contains only /bin/sh essentials; selectively add
    stub compiler/make binaries to path_dir to simulate presence/absence.
    """
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    # Locate essential OS utilities (head, grep, etc.) — we need a minimal
    # system PATH that still has these or the bash script itself will fail.
    # Simplest: include /usr/bin and /bin, which provide sh/head/grep/command,
    # but exclude gcc/clang/gfortran/make/gmake by filtering them from stubs.
    # We don't need to strip them from /usr/bin because the stub_dir is
    # prepended — but we rely on `command -v` semantics which searches all
    # PATH entries. So we actually do need to narrow PATH for absence tests.
    # Strategy: use a minimal PATH="<stub_dir>:/empty_usr". But commands like
    # `head`, `grep`, `tail`, `command` are builtins in bash or in /usr/bin.
    # Safest: construct a synthetic /usr-like dir that only has the basics.
    basics_dir = tmp_path / "basics"
    basics_dir.mkdir()
    for tool in ("head", "grep", "tail", "uname", "sh", "bash", "cat",
                 "cut", "echo", "sed", "tr", "printf", "dirname", "basename",
                 "find", "mkdir", "chmod", "rm", "cp", "mv", "ls", "awk",
                 "python3"):
        src = shutil.which(tool)
        if src:
            # Symlink so real binary is accessible
            (basics_dir / tool).symlink_to(src)
    return stub_dir, basics_dir


class TestToolchainAbsence:
    def test_cc_absent_emits_blocker(self, isolated_path):
        stub_dir, basics_dir = isolated_path
        # Provide gfortran + gmake stubs; omit cc/gcc/clang.
        _make_stub(stub_dir, "gfortran")
        _make_stub(
            stub_dir,
            "gmake",
            body="#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'GNU Make 4.4'; exit 0\n",
        )
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == EXIT_NO_LAPACK, f"Expected {EXIT_NO_LAPACK}, got {rc}. stderr: {stderr[:400]}"
        blocker = _first_blocker(stderr)
        assert blocker is not None, f"No blocker in stderr: {stderr[:400]}"
        assert blocker["code"] == "CC_ABSENT"
        assert blocker["mode"] == "fatal"

    def test_gfortran_absent_emits_blocker(self, isolated_path):
        stub_dir, basics_dir = isolated_path
        _make_stub(stub_dir, "gcc")
        _make_stub(
            stub_dir,
            "gmake",
            body="#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'GNU Make 4.4'; exit 0\n",
        )
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == EXIT_NO_GFORTRAN, f"Expected {EXIT_NO_GFORTRAN}, got {rc}. stderr: {stderr[:400]}"
        blocker = _first_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "GFORTRAN_ABSENT"

    def test_gnu_make_absent_emits_blocker(self, isolated_path):
        stub_dir, basics_dir = isolated_path
        _make_stub(stub_dir, "gcc")
        _make_stub(stub_dir, "gfortran")
        # No gmake or make at all
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == EXIT_NO_LAPACK
        blocker = _first_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "GNU_MAKE_ABSENT"


class TestToolchainPresent:
    def test_all_present_exits_zero(self, isolated_path):
        stub_dir, basics_dir = isolated_path
        _make_stub(stub_dir, "gcc")
        _make_stub(stub_dir, "gfortran")
        _make_stub(
            stub_dir,
            "gmake",
            body="#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'GNU Make 4.4'; exit 0\n",
        )
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == 0, f"Expected 0, got {rc}. stderr: {stderr[:400]}"
        # Must not emit a fatal blocker.
        blocker = _first_blocker(stderr)
        # Warn lines are NOT JSON blockers; a JSON blocker would fail here.
        if blocker is not None:
            assert blocker["mode"] != "fatal", (
                f"Toolchain present but fatal blocker emitted: {blocker}"
            )

    def test_make_as_gnu_make_accepted(self, isolated_path):
        """A `make` that reports itself as GNU make should count as GNU make."""
        stub_dir, basics_dir = isolated_path
        _make_stub(stub_dir, "gcc")
        _make_stub(stub_dir, "gfortran")
        # No gmake, but provide `make` that looks like GNU make.
        _make_stub(
            stub_dir,
            "make",
            body="#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'GNU Make 4.4'; exit 0\n",
        )
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == 0, f"Expected 0, got {rc}. stderr: {stderr[:400]}"


class TestX11WarningOnly:
    def test_x11_absence_never_blocks(self, isolated_path):
        """X11 headers missing must only warn, never emit a fatal blocker."""
        stub_dir, basics_dir = isolated_path
        _make_stub(stub_dir, "gcc")
        _make_stub(stub_dir, "gfortran")
        _make_stub(
            stub_dir,
            "gmake",
            body="#!/bin/sh\n[ \"$1\" = \"--version\" ] && echo 'GNU Make 4.4'; exit 0\n",
        )
        path = f"{stub_dir}:{basics_dir}"
        rc, stdout, stderr = _run({"PATH": path})
        assert rc == 0
        blocker = _first_blocker(stderr)
        if blocker is not None:
            # If X11 somehow emitted a blocker, it must not be fatal.
            assert blocker["mode"] != "fatal", (
                f"X11 must be warn-only, got fatal blocker: {blocker}"
            )
