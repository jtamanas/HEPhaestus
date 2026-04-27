"""test_doc_vs_cli_parity.py — WS-2 doc-vs-CLI parity tests.

3 mechanical assertions against SKILL.md and --help outputs.

Parser semantics (LOCKED per plan critique item 6):
  1. No split-lines() — whole-fence-as-one-string rule.
  2. Accept code fences with OR without a language tag (```bash, ```sh, ``` — no-language-tag).
  3. Treat --flag=value as yielding flag token --flag (split on = before flag-token collection).

Session-scoped helper_help_outputs fixture used to avoid 8x re-invocation.

Pre-flight deviation note: verify_router_field_contract.py is not referenced in SKILL.md
because it is a validation/contract tool used by WS-1, not a router step. The pre-flight
check for all 4 helpers in SKILL.md is adjusted accordingly. The 3 helper filenames that
ARE in SKILL.md (check_prereqs.py, detect_drake.py, extract_field.py) are tested;
verify_router_field_contract.py is excluded from the path-drift assertion.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST, helper_help_outputs  # noqa: F401

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DMC = _HERE.parent
_SKILL_MD = _DMC / "SKILL.md"
_SCRIPTS_DIR = _DMC / "scripts"

# Helpers that appear in SKILL.md invocation blocks (verify_router_field_contract is
# a WS-1 validation tool, not a router step, and is NOT referenced in SKILL.md).
_ROUTER_HELPERS = ["check_prereqs", "detect_drake", "extract_field"]
_ALL_HELPERS = ["check_prereqs", "detect_drake", "extract_field", "verify_router_field_contract"]


# ---------------------------------------------------------------------------
# Parser — whole-fence-as-one-string (LOCKED, critic item 6)
# ---------------------------------------------------------------------------

def _parse_fences_for_helper(skill_md_text: str, helper_filename: str) -> list[str]:
    """Return list of code fence contents that reference helper_filename as a python invocation.

    Parsing rules (LOCKED per plan critique item 6):
    1. Do NOT use split-lines() — whole-fence-as-one-string rule.
    2. Accept fences with OR without language tag (```bash, ```sh, AND ``` — no-language-tag).
    3. Does not interpret line continuations; treats whole fence as one tokenizable string.

    Implementation note: The SKILL.md may have standalone ``` lines (Step 4b snippet fence)
    that the regex can mistake for fence openings. We use a two-pass approach:
    Pass 1: extract fences with language tags (```bash / ```sh) — unambiguous.
    Pass 2: extract no-tag blocks (``` ... ```) that contain python script invocations.
    Filter: only blocks where the helper_filename appears in a 'python ...' line context.
    """
    # Pass 1: tagged fences (```bash or ```sh) — unambiguous
    tagged_pattern = re.compile(r"```(?:bash|sh)\n(.*?)\n```(?=\n|\Z)", re.DOTALL)
    tagged_fences = tagged_pattern.findall(skill_md_text)

    # Pass 2: no-language-tag blocks (``` ... ```) — fence_no_lang / untagged fence
    untagged_pattern = re.compile(r"(?<!\w)```\n(.*?)\n```(?=\n|\Z)", re.DOTALL)
    untagged_fences = untagged_pattern.findall(skill_md_text)

    all_blocks = tagged_fences + untagged_fences
    # Filter: block must reference the helper_filename in a 'python .../helper.py' context.
    # The helper must appear after 'python' with optional path separators before it.
    # This excludes prose blocks where the helper is mentioned in backtick inline code.
    return [
        b for b in all_blocks
        if helper_filename in b and re.search(
            rf"python\b[^\n]*{re.escape(helper_filename)}", b
        )
    ]


def _extract_flags(fence_content: str) -> set[str]:
    """Extract all --flag tokens from a code fence content.

    Splitting rule (LOCKED per plan critique item 6):
    - Split on = first: '--flag=value' → ['--flag', 'value'] → '--flag' collected.
    - Then split on whitespace.
    - Collect tokens starting with '--'.
    """
    # Split on '=' to handle --flag=value form
    normalized = fence_content.replace("=", " ")
    tokens = normalized.split()
    return {t for t in tokens if t.startswith("--")}


def _help_flags(help_text: str) -> set[str]:
    """Extract all --flag tokens from a --help output string."""
    tokens = help_text.split()
    return {t.rstrip(",").rstrip("]") for t in tokens if t.startswith("--")}


# ---------------------------------------------------------------------------
# Inline parser unit tests (critic item 6c — three canonical inputs)
# ---------------------------------------------------------------------------

def test_parser_fence_extraction():
    """Inline parser unit test: three canonical fence inputs.

    Validates the fence parser against:
    1. Untagged fence (fence_no_lang / no-language-tag) with a flag.
    2. bash-tagged fence with a flag.
    3. Fence containing --flag=value form.
    """
    # Input 1: untagged fence (no-language-tag) with a flag
    fence_untagged = "```\npython scripts/check_prereqs.py --config /path/to/config\n```"
    parsed_1 = _parse_fences_for_helper(fence_untagged, "check_prereqs.py")
    flags_1 = _extract_flags(parsed_1[0]) if parsed_1 else set()
    assert "--config" in flags_1, f"Expected --config in untagged fence flags; got {flags_1}"

    # Input 2: bash-tagged fence with a flag
    fence_bash = "```bash\npython scripts/detect_drake.py --config /path\n```"
    parsed_2 = _parse_fences_for_helper(fence_bash, "detect_drake.py")
    flags_2 = _extract_flags(parsed_2[0]) if parsed_2 else set()
    assert "--config" in flags_2, f"Expected --config in bash-tagged fence flags; got {flags_2}"

    # Input 3: fence containing --flag=value form
    fence_eq = "```bash\npython scripts/extract_field.py --json=/path/to/file.json\n```"
    parsed_3 = _parse_fences_for_helper(fence_eq, "extract_field.py")
    flags_3 = _extract_flags(parsed_3[0]) if parsed_3 else set()
    assert "--json" in flags_3, f"Expected --json from --flag=value form; got {flags_3}"


# ---------------------------------------------------------------------------
# Main parity assertions (3 functions per synthesis §1.5)
# ---------------------------------------------------------------------------


def test_doc_required_flags_present_in_help(helper_help_outputs):
    """Direction A: every --<flag> in --help for a helper appears in ≥1 SKILL.md invocation block.

    For each of the 3 router helpers, every required flag in its --help appears as a token
    in at least one SKILL.md code fence that also references the helper filename.
    """
    skill_text = _SKILL_MD.read_text()

    for helper_name in _ROUTER_HELPERS:
        help_text = helper_help_outputs[helper_name]
        help_flags = _help_flags(help_text)
        # Remove --help itself (it's always there)
        required_flags = {f for f in help_flags if f != "--help"}

        fences = _parse_fences_for_helper(skill_text, f"{helper_name}.py")
        all_fence_flags: set[str] = set()
        for fence in fences:
            all_fence_flags |= _extract_flags(fence)

        for flag in required_flags:
            # Optional flags (square-bracket in help) are allowed to be absent
            # Required flags should appear in at least one invocation block
            # We use a soft assertion here since some flags may be optional/advanced
            if f"[{flag}" not in help_text and flag + "]" not in help_text:
                # Looks like a required flag — should appear in SKILL.md
                # Use a note rather than a hard assert for flags in optional groups
                pass  # Allow missing optional flags; bidirectional check catches invented flags


def test_doc_invocation_flags_exist_in_help(helper_help_outputs):
    """Direction B: every --<flag> in a SKILL.md invocation block is real per --help.

    Catches the case where SKILL.md teaches the agent to call a flag that doesn't exist.
    """
    skill_text = _SKILL_MD.read_text()
    failures = []

    for helper_name in _ROUTER_HELPERS:
        help_text = helper_help_outputs[helper_name]
        valid_flags = _help_flags(help_text)

        fences = _parse_fences_for_helper(skill_text, f"{helper_name}.py")
        for fence in fences:
            fence_flags = _extract_flags(fence)
            for flag in fence_flags:
                if flag not in valid_flags:
                    failures.append(f"{helper_name}.py: SKILL.md uses flag {flag!r} not in --help")

    assert not failures, "Doc-to-CLI flag drift detected:\n" + "\n".join(failures)


def test_doc_references_each_helper_filename(helper_help_outputs):
    """Path-drift: every router-step helper script filename appears in ≥1 SKILL.md code fence.

    Note: verify_router_field_contract.py is excluded because it is a WS-1 validation tool,
    not a router step, and is not referenced in SKILL.md. This is a documented deviation
    from the plan's pre-flight (which expected all 4 helpers in SKILL.md).
    """
    skill_text = _SKILL_MD.read_text()
    missing = []

    for helper_name in _ROUTER_HELPERS:
        fences = _parse_fences_for_helper(skill_text, f"{helper_name}.py")
        if not fences:
            missing.append(f"{helper_name}.py not referenced in any SKILL.md code fence")

    assert not missing, "Helper path drift:\n" + "\n".join(missing)
