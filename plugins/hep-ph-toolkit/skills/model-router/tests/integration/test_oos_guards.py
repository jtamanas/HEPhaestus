"""
test_oos_guards.py — WS5 out-of-scope verification tests.

Asserts that no WS5 commits modified forbidden paths or ground-truth registry
files. Uses `git merge-base HEAD origin/main` as the base ref (per plan §S9 +
WS4-S13 verbatim pattern).

Gracefully skips if git is not available or origin/main cannot be resolved.

OOS guard paths (per plan §S9.Do + WS5 discipline):
  FORBIDDEN_PATHS  — directory prefixes that must not be touched.
  FORBIDDEN_FILES  — specific ground-truth registry files that must not be
                     modified.
"""
from __future__ import annotations

import subprocess

import pytest

# ---------------------------------------------------------------------------
# Forbidden path prefixes — ZERO WS5 modifications allowed.
# ---------------------------------------------------------------------------
FORBIDDEN_PATHS = [
    "plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/",
    "plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/",
    "plugins/hep-ph-toolkit/skills/model-router/scripts/model_router/",
    "plugins/hep-ph-toolkit/skills/analytic-exception-detector/scripts/",
]

# ---------------------------------------------------------------------------
# Forbidden files — ground-truth registries and canonical assets.
# ---------------------------------------------------------------------------
FORBIDDEN_FILES = [
    "plugins/hep-ph-toolkit/skills/_shared/constraints.yaml",
    "plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml",
    "plugins/hep-ph-toolkit/skills/_shared/blocker_catalog.yaml",
    "plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml",
    "plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/2hdm_a.yaml",
    "plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/dark_su3.yaml",
]


# ---------------------------------------------------------------------------
# Helper — get list of changed paths since branching from origin/main.
# ---------------------------------------------------------------------------
def _git_diff_paths() -> list[str]:
    """Return list of paths changed since git merge-base HEAD origin/main.

    Calls pytest.skip() if git is unavailable or origin/main cannot be
    resolved (e.g. no remote configured, fresh clone without fetch).
    """
    try:
        base_result = subprocess.run(
            ["git", "merge-base", "HEAD", "origin/main"],
            capture_output=True,
            text=True,
            check=True,
        )
        base = base_result.stdout.strip()
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return diff_result.stdout.splitlines()
    except FileNotFoundError as exc:
        pytest.skip(f"git not available: {exc}")
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"git not available or no origin/main: {exc}")


# ---------------------------------------------------------------------------
# OOS guard tests
# ---------------------------------------------------------------------------

def test_no_oos_path_modified() -> None:
    """Assert no forbidden directory prefix was modified between base and HEAD.

    FORBIDDEN_PATHS: router source, DM-constraints scripts/tests, WS4 AED scripts.
    Gracefully skips if git/origin/main unavailable.
    """
    changed = _git_diff_paths()
    offending = [
        p for p in changed
        if any(p.startswith(prefix) for prefix in FORBIDDEN_PATHS)
    ]
    assert not offending, (
        f"WS5 violation: out-of-scope directory paths modified:\n"
        + "\n".join(f"  {p}" for p in offending)
    )


def test_no_oos_file_modified() -> None:
    """Assert no ground-truth registry or canonical asset file was modified.

    FORBIDDEN_FILES: real _shared/ registries and canonical spec assets.
    Gracefully skips if git/origin/main unavailable.
    """
    changed = _git_diff_paths()
    offending = [p for p in changed if p in FORBIDDEN_FILES]
    assert not offending, (
        f"WS5 violation: ground-truth registry files modified:\n"
        + "\n".join(f"  {p}" for p in offending)
    )
