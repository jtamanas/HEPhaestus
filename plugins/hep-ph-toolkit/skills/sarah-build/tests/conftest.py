"""
conftest.py — pytest configuration for sarah-build tests.

Sets up sys.path so scripts can be imported without installation, and
registers the ``wolfram`` marker for tests that drive real wolframscript
against SARAH (end-to-end smoke and validate_goldens smoke).

Gotcha — if you hit ``AttributeError: module 'py' has no attribute 'path'``:
    MadGraph's ``ufo_expression_parsers.py`` uses PLY, which auto-generates
    a ``py.py`` parser table in the current working directory on first
    run.  When pytest is invoked from the marketplace repo root, that
    local ``py.py`` shadows the installed ``py`` package and pytest
    crashes during its own ``_pytest.compat`` import — *before* this
    conftest can emit a helpful error.  Fix: invoke pytest from any
    subdirectory (e.g. ``cd plugins/hep-ph-toolkit/skills/sarah-build
    && python -m pytest tests/``) so the repo root is no longer
    ``sys.path[0]``; or delete the stray ``py.py`` after it appears
    (it is gitignored and regenerated on demand).
"""

import sys
from pathlib import Path


# Defensive check: if we somehow reached conftest with a shadowed ``py``
# (rare — usually pytest crashes first), fail loudly with actionable
# text rather than a confusing downstream error.
try:
    import py as _py
    if not hasattr(_py, "path"):
        _origin = getattr(_py, "__file__", "<unknown>")
        raise RuntimeError(
            f"The 'py' module resolved to {_origin}, which is not the "
            "installed 'py' package (it lacks py.path).  Most likely a "
            "stray py.py file is shadowing the package — MadGraph's PLY "
            "parser auto-generates py.py in the cwd.  Run pytest from a "
            "subdirectory, or delete the stray py.py (see module-level "
            "docstring above)."
        )
except ImportError:
    pass

_TESTS_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _TESTS_DIR.parent
_SCRIPTS_DIR = _SKILL_DIR / "scripts"
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_SHARED_HELPERS_DIR = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers"

for _p in [str(_SCRIPTS_DIR), str(_SHARED_DIR), str(_SHARED_HELPERS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def pytest_configure(config):
    """Register custom markers used in this test suite."""
    config.addinivalue_line(
        "markers",
        "wolfram: tests that drive real wolframscript against SARAH "
        "(slow; skipped when SARAH/wolframscript are not installed).",
    )
