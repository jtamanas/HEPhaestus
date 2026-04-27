"""Negative-control suite — 4 sabotaged SKILL.md files.

Each test parameterizes over a sabotage_id and an expected_fail_assertion.
In normal mode: assert the named assertion IS in hard_failures (sabotage fired).
In WS3_FORCE_LIVE=1 mode: assert it is NOT in hard_failures (live SKILL.md clean).

NC-3 is retargeted to crosscheck_disagreement_blocker_present (structural: verifies the
CROSSCHECK_DISAGREEMENT literal is emitted when Point A's 14.4% rel-diff fixture
is loaded). See plan-final §9 item 6 for the rationale.
"""

from __future__ import annotations

import os
import pathlib

import pytest

from tests.dark_su3_playtest.conftest import (
    NC_DIR,
    RetryResult,
    run_playtest,
    run_with_retry_budget,
)


@pytest.mark.parametrize("sabotage_id,expected_fail_assertion", [
    ("NC-1", "extract_field_schema_version_arg"),
    ("NC-2", "extract_field_sigma_v_zero_invocation"),
    ("NC-3", "crosscheck_disagreement_blocker_present"),   # retargeted (plan-final §9 #6)
    ("NC-4", "spec_flag_preflight"),
])
def test_negative_control(sabotage_id, expected_fail_assertion, monkeypatch):
    """Assert each sabotage deterministically fires its expected hard assertion.

    In WS3_FORCE_LIVE=1 mode: the test inverts — live SKILL.md should NOT
    trigger the assertion (verifies live SKILL.md is not accidentally sabotaged).

    Uses the `in` form (plan-final §9 #7): sabotage overlap is acceptable as
    long as the named assertion appears somewhere in the failure set.
    """
    force_live = os.environ.get("WS3_FORCE_LIVE") == "1"

    if not force_live:
        # Normal mode: load the sabotaged SKILL.md
        broken_path = NC_DIR / f"SKILL.md.broken_{sabotage_id}"
        assert broken_path.exists(), f"Sabotage file missing: {broken_path}"
        monkeypatch.setenv("WS3_SKILL_OVERRIDE_PATH", str(broken_path))
    else:
        # Force-live mode: unset override, use real SKILL.md
        monkeypatch.delenv("WS3_SKILL_OVERRIDE_PATH", raising=False)

    # Run Point A with DRAKE configured (exercises all assertion paths)
    result: RetryResult = run_playtest(point="A", drake_branch="configured", tier="tier1")

    if force_live:
        # Inversion: assert the expected assertion does NOT fire on live SKILL.md
        assert expected_fail_assertion not in [hf.assertion_id for hf in result.hard_failures], (
            f"LIVE SKILL.md accidentally triggers '{expected_fail_assertion}'. "
            f"hard_failures: {[hf.assertion_id for hf in result.hard_failures]}. "
            f"The live SKILL.md may be sabotaged."
        )
    else:
        # Normal mode: the `in` form — named assertion must appear in failures.
        # Sabotage overlap is acceptable as long as the named assertion appears
        # in the failure set (plan-final §9 #7: `in` not `==`).
        assert expected_fail_assertion in [hf.assertion_id for hf in result.hard_failures], (
            f"Sabotage {sabotage_id} did NOT fire '{expected_fail_assertion}'. "
            f"hard_failures: {[hf.assertion_id for hf in result.hard_failures]}. "
            f"The sabotage may not be effective or the assertion check is broken."
        )
