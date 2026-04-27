"""conftest.py — WS-2 shared fixtures for /dark-matter-constraints test harness.

Canonical path constants (WS-1 naming; WS-4 T8 imports via `from .conftest import`):
  _HERE             — pathlib.Path resolving to this tests/ directory
  _REPO_ROOT        — pathlib.Path resolving to the repository root
  _DEFAULT_MANIFEST — pathlib.Path resolving to contracts/router_contract.json
"""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Module-level path constants (WS-1 canonical names — do NOT rename).
# ---------------------------------------------------------------------------

_HERE: pathlib.Path = pathlib.Path(__file__).parent
_REPO_ROOT: pathlib.Path = _HERE.parent.parent.parent.parent.parent  # 5 levels up to repo root
_DEFAULT_MANIFEST: pathlib.Path = _HERE.parent / "contracts" / "router_contract.json"

_SCRIPTS_DIR: pathlib.Path = _HERE.parent / "scripts"

_HELPER_NAMES = [
    "check_prereqs",
    "detect_drake",
    "extract_field",
    "verify_router_field_contract",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def helper_loader():
    """Return a callable that importlib-loads a helper by name.

    Usage::

        def test_foo(helper_loader):
            m = helper_loader("check_prereqs")
            result, code = m.check_prereqs(config_path=..., model=..., manifest_path=...)
    """
    def _load(helper_name: str):
        helper_path = _SCRIPTS_DIR / f"{helper_name}.py"
        spec = importlib.util.spec_from_file_location(helper_name, helper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load


@pytest.fixture
def helper_subprocess():
    """Return a callable that runs a helper as a CLI subprocess.

    Usage::

        def test_foo(helper_subprocess):
            cp = helper_subprocess("check_prereqs", ["--config", "...", "--model", "foo"])
            assert cp.returncode == 0
    """
    def _run(helper_name: str, args: list[str], env: dict | None = None):
        import os
        helper_path = str(_SCRIPTS_DIR / f"{helper_name}.py")
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        cmd = [sys.executable, helper_path] + args
        return subprocess.run(cmd, capture_output=True, text=True, env=run_env)  # sys.executable

    return _run


@pytest.fixture(scope="session")
def helper_help_outputs() -> dict[str, str]:
    """Session-scoped fixture: capture --help stdout for all four helpers once.

    Returns a dict mapping helper name → help text string.
    Avoids 8× re-invocation across test_doc_vs_cli_parity tests.
    """
    result: dict[str, str] = {}
    for name in _HELPER_NAMES:
        helper_path = str(_SCRIPTS_DIR / f"{name}.py")
        cp = subprocess.run([sys.executable, helper_path, "--help"], capture_output=True, text=True)  # sys.executable
        result[name] = cp.stdout + cp.stderr  # argparse writes to stdout; keep stderr too
    return result
