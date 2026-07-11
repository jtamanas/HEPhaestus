"""Tier-2 hybrid tests — Dark SU(3) playtest.

Real helpers (invoked via SKILL.md subprocess strings) + canned fixture files.
Run with: HEPPH_RUN_LIVE_PLAYTESTS=1 pytest -m integration tests/dark_su3_playtest/test_playtest_tier2.py

Same scenario matrix and pass criterion as Tier-1. Difference: helpers are
invoked for real; only physics tool outputs (MadDM stdout, etc.) are stubbed
via the canned fixture directory.

These tests invoke the real `claude` CLI (live LLM calls against the Sonnet
model) once per scenario — non-deterministic, ~20 minutes and real API spend
PER scenario. They are gated behind HEPPH_RUN_LIVE_PLAYTESTS=1 (see the
skipif below) so a bare `python -m pytest` from the repo root never triggers
live LLM calls or API spend.
"""

from __future__ import annotations

import os

import pytest

from tests.dark_su3_playtest.conftest import (
    RetryResult,
    run_with_retry_budget,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("HEPPH_RUN_LIVE_PLAYTESTS") != "1",
        reason=(
            "Tier-2 playtest scenarios invoke the real `claude` CLI (live LLM "
            "calls, ~20 min and real API spend PER scenario). Opt in with "
            "HEPPH_RUN_LIVE_PLAYTESTS=1 pytest tests/dark_su3_playtest/test_playtest_tier2.py"
        ),
    ),
]

TIER2_SCENARIOS = [
    ("pointA_configured", "A", "configured"),
    ("pointA_missing", "A", "missing"),
    ("pointA_activation_required", "A", "activation_required"),
    ("pointA_unset", "A", None),
    ("pointB", "B", None),
]


@pytest.mark.parametrize("scenario_id,point,drake_branch", TIER2_SCENARIOS)
def test_tier2_scenario(scenario_id: str, point: str, drake_branch: str | None) -> None:
    """Tier-2 hard-gate with real helper subprocesses."""
    result: RetryResult = run_with_retry_budget(
        scenario_id=scenario_id,
        point=point,
        drake_branch=drake_branch,
        tier="tier2",
    )
    hard_fail_ids = [hf.assertion_id for hf in result.hard_failures]
    assert not result.hard_failures, (
        f"[{scenario_id}] Tier-2 HARD assertion(s) failed: {hard_fail_ids}"
    )
    for assertion_id, attempt in result.soft_results.items():
        if attempt is None:
            print(
                f"WARNING: [{scenario_id}] soft assertion '{assertion_id}' "
                "failed 3-of-3 (informational)"
            )
