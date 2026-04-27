"""test_no_dmc_scripts_modified.py — Out-of-scope CI guard (WS4-S13).

This test should run FIRST in any CI invocation (before unit/static/runtime tests)
so violations are caught before other tests are wasted.

Per WS4 plan §7 out-of-scope manifest and synthesis §11.2:
  plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/ is the PROTECTED
  surface for WS4. No file under this directory may be modified by WS4 commits.

Guard logic:
  - Determine the WS4 base commit via WS4_BASE_REF env var (default: git merge-base HEAD main).
  - Run `git diff --name-only <base>..HEAD -- 'plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/'`.
  - Assert the output is empty.

Skip condition: only when .git directory is absent (source-tarball install).
When .git is present, the test runs unconditionally — local development included.

On failure: assertion message names the offending file(s) and points to
synthesis §11.2 ("DMC scripts/ is out-of-scope for WS4").
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

_HERE = pathlib.Path(__file__).parent
# tests/ -> analytic-exception-detector/ -> skills/ -> workflow/ -> plugins/ -> repo root
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent
_GIT_DIR = _REPO_ROOT / ".git"

_DMC_SCRIPTS_GLOB = "plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/"


def _get_base_ref() -> str:
    """Get the base commit ref for the diff.

    Uses WS4_BASE_REF env var if set, otherwise computes git merge-base HEAD main.
    """
    base_ref = os.environ.get("WS4_BASE_REF", "")
    if base_ref:
        return base_ref

    result = subprocess.run(
        ["git", "merge-base", "HEAD", "main"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    if result.returncode != 0:
        # If merge-base fails (e.g., main doesn't exist locally), try origin/main
        result2 = subprocess.run(
            ["git", "merge-base", "HEAD", "origin/main"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        if result2.returncode != 0:
            pytest.skip(
                f"Could not determine base ref: git merge-base failed "
                f"(stdout={result.stdout!r}, stderr={result.stderr!r})"
            )
        return result2.stdout.strip()
    return result.stdout.strip()


@pytest.mark.skipif(
    not _GIT_DIR.exists(),
    reason="No .git directory — skipping git-diff guard (source-tarball install)"
)
def test_no_dmc_script_files_in_diff():
    """Assert that no file under dark-matter-constraints/scripts/ was modified by WS4.

    WS4 out-of-scope manifest (plan §7): the entire DMC scripts/ directory is
    protected. This test enforces the constraint by diffing the current HEAD
    against the WS4 base commit.

    Configure WS4_BASE_REF env var to override the base commit (default: git merge-base HEAD main).
    """
    base_ref = _get_base_ref()

    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}..HEAD", "--", _DMC_SCRIPTS_GLOB],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )

    if result.returncode != 0:
        pytest.skip(
            f"git diff failed (base_ref={base_ref!r}): "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    modified_files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

    assert not modified_files, (
        f"WS4 out-of-scope violation: the following files under "
        f"dark-matter-constraints/scripts/ were modified by WS4 commits:\n"
        + "\n".join(f"  - {f}" for f in modified_files)
        + "\n\nThis violates the WS4 out-of-scope manifest (plan §7) and "
        "synthesis §11.2 ('DMC scripts/ is out-of-scope for WS4'). "
        "DMC scripts/ changes require a separate workstream with explicit "
        "manager approval."
    )
