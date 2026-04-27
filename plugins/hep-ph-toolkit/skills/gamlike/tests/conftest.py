"""
conftest.py — shared fixtures for gamlike test suite.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent.resolve()
_REPO_ROOT = _HERE
while _REPO_ROOT.name and not (_REPO_ROOT / ".git").exists():
    _REPO_ROOT = _REPO_ROOT.parent

_FIXTURES_DIR = _HERE / "fixtures"
_SCRIPT_PATH = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "gamlike" / "scripts" / "parse_maddm_results.py"


# ── Pytest fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def repo_root():
    return _REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir():
    return _FIXTURES_DIR


@pytest.fixture(scope="session")
def script_path():
    return _SCRIPT_PATH


@pytest.fixture
def fixture_path():
    """Returns callable: fixture_path(name) → Path"""
    def _fp(name: str) -> Path:
        return _FIXTURES_DIR / name
    return _fp


@pytest.fixture
def parser_subprocess(tmp_path):
    """
    Returns callable: run_parser(fixture_name, extra_args=[]) → (CompletedProcess, out_path)
    Runs parse_maddm_results.py via subprocess on the named fixture.
    out_path is the JSON output path.
    """
    def _run(fixture_name: str, extra_args=None):
        input_path = _FIXTURES_DIR / fixture_name
        out_path = tmp_path / (fixture_name + ".gamlike.json")
        cmd = [sys.executable, str(_SCRIPT_PATH), str(input_path), "--out", str(out_path)]
        if extra_args:
            cmd.extend(extra_args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result, out_path
    return _run


@pytest.fixture
def parser_module():
    """
    Imports parse_maddm_results.py as a module (in-process).
    Returns the module object.
    """
    spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def parse_fixture(parser_module, tmp_path):
    """
    Returns callable: parse_fixture(name) → parsed dict
    Parses the named fixture in-process via parse_file().
    """
    def _p(name: str) -> dict:
        path = _FIXTURES_DIR / name
        return parser_module.parse_file(path)
    return _p
