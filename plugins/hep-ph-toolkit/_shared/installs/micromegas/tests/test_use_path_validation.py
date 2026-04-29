"""test_use_path_validation.py — unit tests for use_path.sh validation logic.

Runs use_path.sh on fake directories and asserts blocker codes
MICROMEGAS_PATH_INVALID and CALCHEP_PATH_INVALID are emitted on stderr.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent
_USE_PATH = _SCRIPTS / "use_path.sh"
_FAKE_TREE = _SCRIPT_DIR / "fixtures" / "fake_micromegas_tree"


def _run(args: list[str], env: dict | None = None) -> tuple[int, str, str]:
    """Run use_path.sh with given args. Returns (returncode, stdout, stderr)."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        ["bash", str(_USE_PATH)] + args,
        capture_output=True,
        text=True,
        env=merged_env,
    )
    return result.returncode, result.stdout, result.stderr


def _parse_blocker(stderr: str) -> dict | None:
    """Extract the first JSON blocker from stderr."""
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith("{") and "code" in line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


class TestMicrOMEGAsPathInvalid:
    def test_nonexistent_dir(self, tmp_path):
        rc, stdout, stderr = _run([str(tmp_path / "nonexistent")])
        assert rc != 0
        blocker = _parse_blocker(stderr)
        assert blocker is not None, f"No blocker in stderr: {stderr!r}"
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"
        assert blocker["mode"] == "fatal"

    def test_dir_missing_sources(self, tmp_path):
        # Create dir with CalcHEP_src but no sources/
        (tmp_path / "CalcHEP_src").mkdir()
        rc, stdout, stderr = _run([str(tmp_path)])
        assert rc != 0
        blocker = _parse_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"

    def test_dir_missing_calchep_src(self, tmp_path):
        # Create dir with sources/ but no CalcHEP_src/
        (tmp_path / "sources").mkdir()
        rc, stdout, stderr = _run([str(tmp_path)])
        assert rc != 0
        blocker = _parse_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "MICROMEGAS_PATH_INVALID"

    def test_valid_tree_without_smoke(self, tmp_path):
        """Valid tree structure should pass path validation even without smoke.

        use_path.sh should skip smoke if _smoke.sh not found in scripts/.
        We use a fake tree with a non-existent _smoke.sh location workaround:
        the fake tree has sources/ and CalcHEP_src/ so path validation passes.
        The smoke test may warn but should not cause a path-invalid error.
        """
        # use the fixture fake tree
        rc, stdout, stderr = _run(
            [str(_FAKE_TREE)],
            env={"XDG_CONFIG_HOME": str(tmp_path / "config"),
                 "HEPPH_STATE_ROOT": str(tmp_path / "state")},
        )
        # The test just checks we don't get MICROMEGAS_PATH_INVALID
        blocker = _parse_blocker(stderr)
        if blocker:
            assert blocker["code"] != "MICROMEGAS_PATH_INVALID", (
                f"Got MICROMEGAS_PATH_INVALID for valid tree: {blocker}"
            )


class TestCalcHEPPathInvalid:
    def test_calchep_path_missing_getFlags(self, tmp_path):
        # Valid micromegas dir, bad calchep dir
        (tmp_path / "micromegas" / "sources").mkdir(parents=True)
        (tmp_path / "micromegas" / "CalcHEP_src").mkdir(parents=True)
        calchep_bad = tmp_path / "calchep_bad"
        calchep_bad.mkdir()
        rc, stdout, stderr = _run(
            [str(tmp_path / "micromegas"), "--calchep-path", str(calchep_bad)]
        )
        assert rc != 0
        blocker = _parse_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "CALCHEP_PATH_INVALID"

    def test_calchep_path_has_getFlags_but_no_binary(self, tmp_path):
        # Valid micromegas dir, calchep has getFlags but no s_calchep binary
        (tmp_path / "micromegas" / "sources").mkdir(parents=True)
        (tmp_path / "micromegas" / "CalcHEP_src").mkdir(parents=True)
        calchep_src = tmp_path / "calchep" / "CalcHEP_src"
        calchep_src.mkdir(parents=True)
        (calchep_src / "getFlags").write_text("#!/bin/sh\n")
        (calchep_src / "getFlags").chmod(0o755)
        # No bin/s_calchep
        rc, stdout, stderr = _run(
            [str(tmp_path / "micromegas"), "--calchep-path", str(calchep_src)]
        )
        assert rc != 0
        blocker = _parse_blocker(stderr)
        assert blocker is not None
        assert blocker["code"] == "CALCHEP_PATH_INVALID"
