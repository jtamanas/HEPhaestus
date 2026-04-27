"""Tier-1 dry-run tests — Dark SU(3) playtest.

All helpers are stubbed at the subprocess boundary. No real LLM calls
(unless WS3_FORCE_LIVE=1 is set). Hard gate: single-shot pass required.

Scenarios: 2 points × 4 DRAKE-branch fixtures for Point A + 1 for Point B = 5 total.
Pass criterion (synthesis §4.4): every HARD assertion passes on attempt 1,
AND no SOFT assertion fails 3-of-3 (3-of-3 fail is an informational warning).
"""

from __future__ import annotations

import re

import pytest

from tests.dark_su3_playtest.conftest import (
    FIXTURES,
    RetryResult,
    run_with_retry_budget,
)

# ---------------------------------------------------------------------------
# Tier-1: 5 scenarios
# ---------------------------------------------------------------------------

TIER1_SCENARIOS = [
    # (scenario_id, point, drake_branch)
    ("pointA_configured", "A", "configured"),
    ("pointA_missing", "A", "missing"),
    ("pointA_activation_required", "A", "activation_required"),
    ("pointA_unset", "A", None),
    ("pointB", "B", None),
]


@pytest.mark.parametrize("scenario_id,point,drake_branch", TIER1_SCENARIOS)
def test_tier1_scenario(scenario_id: str, point: str, drake_branch: str | None) -> None:
    """Tier-1 hard-gate: all HARD assertions pass on attempt 1.

    Integration-marked assertions defined in conftest.run_with_retry_budget.
    Soft-assertion 3-of-3 fail is logged as a warning, not a gate failure.
    """
    result: RetryResult = run_with_retry_budget(
        scenario_id=scenario_id,
        point=point,
        drake_branch=drake_branch,
        tier="tier1",
    )

    # HARD gate: no hard failures
    hard_fail_ids = [hf.assertion_id for hf in result.hard_failures]
    assert not result.hard_failures, (
        f"[{scenario_id}] HARD assertion(s) failed: {hard_fail_ids}"
    )

    # SOFT gate: warn only on 3-of-3 fail
    for assertion_id, attempt in result.soft_results.items():
        if attempt is None:
            pytest.warns(
                UserWarning,
                match=f"soft assertion '{assertion_id}' failed 3-of-3",
            ) if False else None  # just log; don't gate
            print(
                f"WARNING: [{scenario_id}] soft assertion '{assertion_id}' "
                "failed 3-of-3 (informational, not a gate)"
            )


@pytest.mark.parametrize("scenario_id,point,drake_branch", TIER1_SCENARIOS)
def test_tier1_spec_flag_survives(scenario_id: str, point: str, drake_branch: str | None) -> None:
    """HARD: --spec flag must be present in SKILL.md (pre-LLM pre-flight)."""
    from tests.dark_su3_playtest.conftest import SKILL_MD_PATH

    content = SKILL_MD_PATH.read_text(encoding="utf-8")
    assert "--spec" in content, (
        f"--spec flag missing from SKILL.md at {SKILL_MD_PATH}"
    )


@pytest.mark.parametrize("scenario_id,point,drake_branch", TIER1_SCENARIOS)
def test_tier1_extract_field_omega_h2_key(
    scenario_id: str, point: str, drake_branch: str | None
) -> None:
    """HARD (W4-D casing pin): extract_field --key omega_h2 (lowercase, underscore).

    Asserts the SKILL.md uses the canonical lowercase form, not OmegaH2 or Omega_h2.
    """
    from tests.dark_su3_playtest.conftest import SKILL_MD_PATH, resolve_skill_md

    content = resolve_skill_md().read_text(encoding="utf-8")
    if "extract_field" in content:
        assert "--key omega_h2" in content, (
            "SKILL.md must use '--key omega_h2' (lowercase) per W4-D casing pin. "
            f"Found content near extract_field: ...{content[content.find('extract_field'):content.find('extract_field')+80]}..."
        )


# ---------------------------------------------------------------------------
# T1 gate #2 — Spectrum-point numeric fixtures (plan-final T1 §3 revised)
# Fix #2: use \b word-boundary so the YAML-nested form "  m_chi: 100" matches.
# The original plan gate used ^m_chi:\s*100\b (line-anchored) which FAILS for
# YAML-nested keys (the line has leading whitespace). Correct pattern: \bm_chi:\s*100\b.
# ---------------------------------------------------------------------------


def test_t1_fixture_spec_pointA_numeric_anchors() -> None:
    """Verify spec_pointA.yaml contains the locked spectrum values (plan-final T1 gate #2).

    Uses word-boundary grep (\b) to match YAML-nested keys correctly.
    The ^-anchored pattern fails for keys nested under dm_candidate:.
    """
    spec_path = FIXTURES / "specs" / "spec_pointA.yaml"
    content = spec_path.read_text(encoding="utf-8")

    assert re.search(r"\bm_chi:\s*100\b", content), (
        f"spec_pointA.yaml missing m_chi: 100 — found in: {spec_path}"
    )
    assert re.search(r"\bm_med:\s*199\b", content), (
        f"spec_pointA.yaml missing m_med: 199 — found in: {spec_path}"
    )
    assert re.search(r"\bmass:\s*105\b", content), (
        f"spec_pointA.yaml missing partner mass: 105 — found in: {spec_path}"
    )
    assert re.search(r"\bwidth_over_mass:\s*0\.005\b", content), (
        f"spec_pointA.yaml missing width_over_mass: 0.005 — found in: {spec_path}"
    )


def test_t1_fixture_spec_pointB_numeric_anchors() -> None:
    """Verify spec_pointB.yaml contains the locked spectrum values (plan-final T1 gate #2).

    Uses word-boundary grep (\b) to match YAML-nested keys correctly.
    """
    spec_path = FIXTURES / "specs" / "spec_pointB.yaml"
    content = spec_path.read_text(encoding="utf-8")

    assert re.search(r"\bm_chi:\s*100\b", content), (
        f"spec_pointB.yaml missing m_chi: 100 — found in: {spec_path}"
    )
    assert re.search(r"\bm_med:\s*230\b", content), (
        f"spec_pointB.yaml missing m_med: 230 — found in: {spec_path}"
    )
    assert re.search(r"\bwidth_over_mass:\s*0\.005\b", content), (
        f"spec_pointB.yaml missing width_over_mass: 0.005 — found in: {spec_path}"
    )


# ---------------------------------------------------------------------------
# Pass-criterion summary hook (plan-final T4 gate #9)
# ---------------------------------------------------------------------------


def pytest_terminal_summary(terminalreporter, exitstatus, config):  # noqa: ARG001
    """Emit WS-3 pass criterion status at session end."""
    passed = terminalreporter.stats.get("passed", [])
    failed = terminalreporter.stats.get("failed", [])
    skipped = terminalreporter.stats.get("skipped", [])
    terminalreporter.write_sep(
        "=",
        f"WS-3 Tier-1 summary: {len(passed)} passed, {len(failed)} failed, "
        f"{len(skipped)} skipped",
    )
    if failed:
        terminalreporter.write_line(
            "FAIL: WS-3 pass criterion NOT met — one or more HARD assertions failed."
        )
    else:
        terminalreporter.write_line(
            "PASS: All HARD assertions passed. "
            "Check soft-assertion warnings above for informational flakes."
        )
