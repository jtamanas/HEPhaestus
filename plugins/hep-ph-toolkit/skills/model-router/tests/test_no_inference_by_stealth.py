"""
test_no_inference_by_stealth.py — CI invariant #3 (S25, plan §11.3).

The router must NOT silently infer/coerce missing axes. Every absent
axis must surface either as a `None` value in the AxisBundle (and thus
in the emitted axis_snapshot), or via a diagnostic. The router never
substitutes a default value or guesses when an axis is missing from the
spec.

Per critique R refinement: parametric over the AxisBundle attribute
interface, not implementation internals.
"""
import pathlib
import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for no-inference invariant tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"

AXIS_FIELDS = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]


def test_axisbundle_exposes_all_eight_axis_fields():
    """The AxisBundle dataclass must expose every A1..A8 attribute."""
    from model_router.types import AxisBundle
    ab = AxisBundle()
    for axis in AXIS_FIELDS:
        assert hasattr(ab, axis), f"AxisBundle missing attribute {axis}"


def test_emitted_axis_snapshot_carries_all_eight_or_none(mock_constraints_yaml):
    """The emitted axis_snapshot must carry every A1..A8 (value or None);
    no axis is silently dropped or auto-defaulted."""
    from model_router.types import RouterOptions
    report = route(
        model_id="singlet-doublet",
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    snap = report.json_report.get("axis_snapshot")
    assert snap is not None, "axis_snapshot missing from report"
    for axis in AXIS_FIELDS:
        assert axis in snap, f"axis_snapshot missing key {axis}"


def test_router_does_not_inject_default_observables_silently(mock_constraints_yaml):
    """If the user provides observables, the router does not extend the list."""
    from model_router.types import RouterOptions
    report = route(
        model_id="dark-su3",
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    # observables in the report must be exactly what the caller asked for.
    assert report.json_report["observables"] == ["relic"]
    assert list(report.json_report["per_observable"].keys()) == ["relic"]


def test_router_uses_default_observables_only_when_none_given(mock_constraints_yaml):
    """When observables is None, defaults derive from registry (not silent guess)."""
    from model_router.types import RouterOptions
    report = route(
        model_id="dark-su3",
        observables=None,
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    obs = set(report.json_report["observables"])
    # Default observables come from the constraints fixture (relic, dd, id).
    assert obs.issubset({"relic", "dd", "id"})
    assert len(obs) > 0
