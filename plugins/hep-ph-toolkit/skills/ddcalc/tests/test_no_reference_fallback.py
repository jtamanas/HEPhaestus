"""
Grep gate: verify that no reference/analytic fallback exists in the
plugins/hep-ph-toolkit/skills/ddcalc/ and plugins/hep-ph-toolkit/_shared/installs/ddcalc/ subtrees.

These terms are FORBIDDEN per plan §5 and brainstorm §5:
- HEPPH_ALLOW_REFERENCE
- DDCALC_REFERENCE_ONLY
- reference_only (as a status or variable name, not in comments)
- allow-analytic-fallback

This test is a unit-level enforcement: if any of these strings appear in
non-test, non-SKILL.md, non-NOTICE source files, the test fails.

The SKILL.md files explicitly list these as "forbidden blockers" for
documentation purposes — they are excluded from the grep scan.
The test files themselves mention the terms — also excluded.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# Root of the worktree (repo root: go up 6 levels from this test file)
# tests/ -> ddcalc/ -> skills/ -> constraints/ -> plugins/ -> (repo root)
CONSTRAINTS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent

# Files excluded from the grep (docs, SKILL.md, NOTICE, this test file itself)
EXCLUDED_PATTERNS = [
    "SKILL.md",
    "NOTICE",
    "ATTRIBUTIONS.md",
    "test_no_reference_fallback.py",
    "verifications.md",
    ".pyc",
]

FORBIDDEN_TERMS = [
    "HEPPH_ALLOW_REFERENCE",
    "DDCALC_REFERENCE_ONLY",
    "allow-analytic-fallback",
]

# "reference_only" is trickier — it appears in the brainstorm docs and SKILL.md
# We gate on it only in .py and .sh source files
REFERENCE_ONLY_EXTENSIONS = {".py", ".sh", ".c", ".hpp", ".f90"}


def _should_exclude(path: Path) -> bool:
    for pat in EXCLUDED_PATTERNS:
        if pat in path.name:
            return True
    return False


def _scan_for_term(term: str, extensions: set[str] | None = None) -> list[str]:
    """
    Return list of '<file>:<line_num>: <content>' matches for forbidden term.

    Scope is intentionally limited to the ddcalc and ddcalc-install skill
    subtrees so that sibling workstreams (higgstools, micromegas, …) don't
    produce false positives for ddcalc-specific enforcement rules.
    """
    result = subprocess.run(
        [
            "git", "grep", "-n", "--", term,
            "plugins/hep-ph-toolkit/skills/ddcalc/",
            "plugins/hep-ph-toolkit/_shared/installs/ddcalc/",
        ],
        cwd=CONSTRAINTS_DIR,
        capture_output=True,
        text=True,
    )
    hits = []
    for line in result.stdout.splitlines():
        # line format: plugins/hep-ph-toolkit/skills/ddcalc/foo.py:42:content
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        file_path = Path(parts[0])
        if _should_exclude(file_path):
            continue
        if extensions is not None and file_path.suffix not in extensions:
            continue
        hits.append(line)
    return hits


class TestNoReferenceFallback:
    def test_no_hepph_allow_reference(self):
        """HEPPH_ALLOW_REFERENCE must not appear in any constraints source file."""
        hits = _scan_for_term("HEPPH_ALLOW_REFERENCE")
        assert not hits, (
            "HEPPH_ALLOW_REFERENCE found in constraints source (forbidden):\n"
            + "\n".join(hits)
        )

    def test_no_ddcalc_reference_only(self):
        """DDCALC_REFERENCE_ONLY must not appear in any constraints source file."""
        hits = _scan_for_term("DDCALC_REFERENCE_ONLY")
        assert not hits, (
            "DDCALC_REFERENCE_ONLY found in constraints source (forbidden):\n"
            + "\n".join(hits)
        )

    def test_no_allow_analytic_fallback(self):
        """allow-analytic-fallback must not appear in any constraints source file."""
        hits = _scan_for_term("allow-analytic-fallback")
        assert not hits, (
            "allow-analytic-fallback found in constraints source (forbidden):\n"
            + "\n".join(hits)
        )

    def test_no_reference_only_in_source(self):
        """
        'reference_only' must not appear as a status string in .py/.sh/.c source files.
        (Allowed in docs, SKILL.md, NOTICE, this test file.)
        """
        hits = _scan_for_term(
            "reference_only",
            extensions=REFERENCE_ONLY_EXTENSIONS,
        )
        assert not hits, (
            "'reference_only' found as status/variable in constraints source (forbidden):\n"
            + "\n".join(hits)
        )

    def test_overlay_not_supported_v1_present(self):
        """
        DDCALC_OVERLAY_NOT_SUPPORTED_V1 must be present in apply_overlay.sh
        as the machine-readable gate marker.
        """
        hits = _scan_for_term("DDCALC_OVERLAY_NOT_SUPPORTED_V1")
        assert hits, (
            "DDCALC_OVERLAY_NOT_SUPPORTED_V1 not found in constraints source. "
            "apply_overlay.sh must contain this gate marker."
        )
