"""
conftest.py — WS5 integration test fixtures for the model-router.

Inherits parent tests/conftest.py sys.path shim (executed at collection time).

Provides:
  - route_for(model_id, observables, strict=False) -> RoutingReport
  - report_pair(model_id) -> tuple[dict, dict]  (default, strict json_report)
  - load_expected(model_id) -> dict
  - recompute_assertion_categories(model_id, report) -> dict[str, bool]
  - pytest_configure: registers load_bearing + diagnostic markers
"""
from __future__ import annotations

import pathlib
import yaml
import pytest

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------
_INTEGRATION_DIR = pathlib.Path(__file__).resolve().parent
_EXPECTED_DIR = _INTEGRATION_DIR / "expected"
_SNAPSHOTS_DIR = _INTEGRATION_DIR / "snapshots"

# Parent tests/ dir (for registry file access)
_TESTS_DIR = _INTEGRATION_DIR.parent
_REGISTRY_DIR = _TESTS_DIR / "fixtures" / "registries"


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "load_bearing: assertion is LOAD_BEARING; failure HOLDS WS5 unconditionally",
    )
    config.addinivalue_line(
        "markers",
        "diagnostic: assertion is DIAGNOSTIC; failure ships with finding in WS5_FINDINGS.md",
    )


# ---------------------------------------------------------------------------
# Registry paths (fixture registries — NOT the real _shared/ registries)
# ---------------------------------------------------------------------------
_FIXTURE_CONSTRAINTS_PATH = _REGISTRY_DIR / "constraints.yaml"
_FIXTURE_BLOCKER_CATALOG_PATH = _REGISTRY_DIR / "blocker_catalog.yaml"
_FIXTURE_ANALYTIC_EXCEPTIONS_PATH = _REGISTRY_DIR / "analytic_exceptions.yaml"


# ---------------------------------------------------------------------------
# route_for helper — calls production route() with fixture registry paths
# ---------------------------------------------------------------------------
def route_for(model_id: str, observables: list[str], strict: bool = False):
    """Call production route() with fixture registry overrides.

    Returns a RoutingReport (full object, not dict).
    Uses the fixture registries at tests/fixtures/registries/ per WS3 D6.
    """
    from model_router.orchestrator import route, RouterOptions  # noqa: imported late

    options = RouterOptions(strict=strict)
    return route(
        model_id,
        observables,
        options,
        constraints_path=_FIXTURE_CONSTRAINTS_PATH,
        blocker_catalog_path=_FIXTURE_BLOCKER_CATALOG_PATH,
        analytic_exceptions_path=_FIXTURE_ANALYTIC_EXCEPTIONS_PATH,
    )


# ---------------------------------------------------------------------------
# report_pair — returns (default json_report dict, strict json_report dict)
# ---------------------------------------------------------------------------
def report_pair(model_id: str) -> tuple[dict, dict]:
    """Route model in both default and strict modes; return json_report dicts.

    Strict mode may raise MatrixAcknowledgementMissing (exit code 4) for
    models where the fixture chain_override deliberately omits blockers.
    In that case a sentinel dict {"exit_code": 4, "verdict": "_EXCEPTION_",
    "_exception_type": "MatrixAcknowledgementMissing"} is returned as the
    strict json_report so that test_exit_code_strict can assert exit_code == 4.
    """
    from model_router.types import MatrixAcknowledgementMissing  # noqa: late import

    observables = ["relic", "dd", "id"]
    default_report = route_for(model_id, observables, strict=False)

    try:
        strict_routing = route_for(model_id, observables, strict=True)
        strict_report = strict_routing.json_report
    except MatrixAcknowledgementMissing:
        strict_report = {
            "exit_code": 4,
            "verdict": "_EXCEPTION_",
            "_exception_type": "MatrixAcknowledgementMissing",
        }

    return (default_report.json_report, strict_report)


# ---------------------------------------------------------------------------
# load_expected — load per-model expected YAML
# ---------------------------------------------------------------------------
def load_expected(model_id: str) -> dict:
    """Load the per-model expected YAML from expected/<slug>.yaml."""
    slug = model_id.replace("-", "_")
    path = _EXPECTED_DIR / f"{slug}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# recompute_assertion_categories — DRY assertion logic (R7)
# Used by both test_validation.py and validation_report.py.
# ---------------------------------------------------------------------------
def recompute_assertion_categories(model_id: str, report: dict) -> dict[str, bool]:
    """Run all assertion categories against a json_report dict.

    Returns a dict mapping assertion_name -> bool (True = PASS, False = FAIL).
    Keys:
        verdict, per_observable_status_<obs>, per_observable_active_chain_<obs>,
        per_observable_blockers_set_<obs>, placements_count,
        dsu3_banner_triple_substring (only for dark-su3),
        hard_halt_no_signoff (only for dark-su3-confining-synthetic).
    """
    expected = load_expected(model_id)
    results: dict[str, bool] = {}

    # --- verdict ---
    results["verdict"] = report.get("verdict") == expected.get("verdict")

    # --- per_observable ---
    for obs in ["relic", "dd", "id"]:
        po = report.get("per_observable", {}).get(obs, {})
        exp_po = expected.get("per_observable", {}).get(obs, {})

        # status
        results[f"per_observable_status_{obs}"] = (
            po.get("status") == exp_po.get("status")
        )

        # active_chain prereq_id
        expected_prereq = exp_po.get("active_chain_prereq_id")
        actual_chain = po.get("active_chain")
        if expected_prereq is None:
            results[f"per_observable_active_chain_{obs}"] = actual_chain is None
        else:
            results[f"per_observable_active_chain_{obs}"] = (
                actual_chain is not None
                and actual_chain.get("prereq_id") == expected_prereq
            )

        # blockers set
        expected_blockers = set(exp_po.get("blockers_set", []))
        actual_blockers = set(po.get("blockers", []))
        results[f"per_observable_blockers_set_{obs}"] = (
            actual_blockers == expected_blockers
        )

    # --- dsu3 banner triple substring ---
    if model_id == "dark-su3":
        placements = report.get("placements", [])
        if placements:
            content = placements[0].get("content", "")
            results["dsu3_banner_triple_substring"] = all(
                sub in content
                for sub in ["REGRESSION-ANCHOR", "25000", "Planck target"]
            )
        else:
            results["dsu3_banner_triple_substring"] = False

    # --- hard_halt_no_signoff ---
    if model_id == "dark-su3-confining-synthetic":
        placements = report.get("placements", [])
        results["hard_halt_no_signoff"] = not any(
            p.get("kind") == "signoff_prompt" for p in placements
        )

    return results
