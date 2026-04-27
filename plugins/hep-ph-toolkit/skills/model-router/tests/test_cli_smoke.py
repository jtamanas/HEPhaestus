"""
test_cli_smoke.py — WS3 iter-5 smoke test for the canonical /model-router demo.

Per ws3_iter4_review.md Blocker 1: SKILL.md's `## Usage > Basic usage`
example is `/model-router dark-su3`, but at iter-4 it failed end-to-end
against the production registry because `models.dark-su3` had no
`spec_path` field, causing `extract_axes` to wrap a SchemaVersionError
as RegistryCorrupt.

This test runs the orchestrator in-process against the **production**
constraints.yaml (NOT a fixture) and asserts the canonical demo path
produces a valid routing report end-to-end, without RegistryCorrupt.

Also asserts the same for `2hdm-a` so any future spec_path regression
on that model is caught here as well.

Out-of-scope (per review-4): `singlet-doublet` is intentionally NOT
covered here — its canonical asset (`singlet_doublet.yaml`) is missing
under `_shared/assets/`. That model's fate is documented inline in
constraints.yaml (gap-finding, not back-fill).
"""
import pathlib

import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for CLI smoke test",
)
route = orch_mod.route

# Production registry path — resolved from this file's location, NOT cwd.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
_PROD_SHARED = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared"
_PROD_CONSTRAINTS = _PROD_SHARED / "constraints.yaml"
_PROD_BLOCKER_CATALOG = _PROD_SHARED / "blocker_catalog.yaml"
_PROD_ANALYTIC_EXCEPTIONS = _PROD_SHARED / "analytic_exceptions.yaml"


def _prod_kwargs():
    return dict(
        constraints_path=_PROD_CONSTRAINTS,
        blocker_catalog_path=_PROD_BLOCKER_CATALOG,
        analytic_exceptions_path=_PROD_ANALYTIC_EXCEPTIONS,
    )


@pytest.mark.parametrize("model_id", ["dark-su3", "2hdm-a"])
def test_cli_smoke_runs_against_production_registry(model_id):
    """The canonical SKILL.md demo invocation must complete end-to-end.

    Asserts:
      - No RegistryCorrupt raised (the iter-4 failure mode).
      - report.json_report['axis_snapshot']['A1'] is populated (truthy).
      - report.json_report['verdict'] is one of the 4 documented verdicts.
    """
    assert _PROD_CONSTRAINTS.exists(), (
        f"Production constraints.yaml missing at {_PROD_CONSTRAINTS}"
    )

    from model_router.types import RegistryCorrupt, RouterOptions

    try:
        report = route(
            model_id=model_id,
            observables=None,
            options=RouterOptions(),
            **_prod_kwargs(),
        )
    except RegistryCorrupt as exc:
        pytest.fail(
            f"RegistryCorrupt raised for {model_id!r} against production "
            f"registry — likely a missing/wrong `spec_path` in "
            f"constraints.yaml `models.{model_id}`. Original error: {exc}"
        )

    snapshot = report.json_report.get("axis_snapshot", {})
    assert snapshot.get("A1"), (
        f"axis_snapshot.A1 is empty for {model_id!r}; spec did not load."
    )
    assert report.json_report.get("verdict") in {
        "CLEAR",
        "ROUTE_TO_ANALYTIC",
        "HALT_FOR_SIGNOFF",
        "HARD_HALT",
    }
