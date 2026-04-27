"""test_analytic_exception_disclosure_emission.py — Runtime emission test (S5/S6).

WS4 v1 — Manager-approved descope (iter-2).

Spike result (WS4 S5 30-min spike, 2026-04-26):
    The DMC merged-report renderer is a Claude Code SKILL.md-driven agent action,
    NOT a Python function or subprocess. There is no Python-callable renderer in
    plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/.

The original test_dsu3_002_emitted_before_results_table test was self-authorized
by iter-1 as a rescope targeting render_disclosure.py (the workflow-skill upstream
renderer) — a tautological assertion (registry → wrap → unwrap → assertEqual).
Iter-2 manager decision: formally descope to pytest.skip with tracking.

Tracked gap: FU-WS4-RUNTIME-001 — see .shift-manager/run-20260426-workflow-skill/decisions/FOLLOWUPS.md

The workflow-renderer test (workflow-skill upstream surface) is also skipped
because it asserts a tautological pipeline; the load-bearing WS4 contract for
the DMC side is enforced by the static placement test
(test_analytic_exception_disclosure_static.py), which hard-asserts banner
verbatim-presence at every registered placement path (P1 = DMC SKILL.md,
P2 = micromegas SKILL.md, P3 = dark_su3.py).

test_dsu3_002_fixture_has_analytic_meta is preserved as a non-emission fixture
sanity check — it does not assert emission semantics.
"""
from __future__ import annotations

import json
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.disclosure_contract

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
_FIXTURE_SUMMARY = _HERE / "fixtures" / "disclosure_emission" / "dsu3_stubbed_summary.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dsu3_stubbed_summary():
    return json.loads(_FIXTURE_SUMMARY.read_text())


# ---------------------------------------------------------------------------
# Test (b) — runtime emission test for dsu3-002
# ---------------------------------------------------------------------------


def test_dmc_runtime_emission_dsu3_002():
    """DMC merged-report runtime emission test — formally deferred.

    The DMC merged-report renderer is a Claude Code SKILL.md-driven agent
    action (Step 6 prose), NOT a Python function or subprocess. There is no
    Python-callable renderer in dark-matter-constraints/scripts/ that can be
    imported and invoked to capture emitted bytes.

    Iter-1 self-authorized a rescope targeting render_disclosure.py (the
    workflow-skill upstream renderer) — a tautological assertion. Iter-2
    manager decision: descope to pytest.skip with explicit tracking.

    Unblock criterion: DMC ships a Python `render_merged_report()` function
    in dark-matter-constraints/scripts/ that accepts a model spec + registry
    entry and returns the merged report bytes. That function can then be
    imported here and asserted to contain the verbatim banner before the
    Results table.

    See: FU-WS4-RUNTIME-001 in
         .shift-manager/run-20260426-workflow-skill/decisions/FOLLOWUPS.md
    """
    pytest.skip(
        "Tracked: FU-WS4-RUNTIME-001 — DMC renderer does not yet expose "
        "Python API; runtime emission test deferred"
    )


def test_dsu3_002_fixture_has_analytic_meta(dsu3_stubbed_summary):
    """Stubbed summary fixture carries _meta.backend == 'analytic' and sigmav_approx: true."""
    assert dsu3_stubbed_summary.get("_meta", {}).get("backend") == "analytic"
    assert dsu3_stubbed_summary.get("sigmav_approx") is True
    assert "Omega_V_h2" in dsu3_stubbed_summary
    assert "Omega_Psi_h2" in dsu3_stubbed_summary
