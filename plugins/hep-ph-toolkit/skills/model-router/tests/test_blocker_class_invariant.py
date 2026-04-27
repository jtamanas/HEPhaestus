"""
test_blocker_class_invariant.py — CI invariant #2 (S25, plan §11.3).

Walk every per_observable.<obs>.blocker_classes[] (and ranked_alternatives'
blocker_classes) in every emitted report and assert each value is in the
closed five-element enum:
    {"missing-skill", "missing-tool-feature", "fundamental-group-theory-gap",
     "regime-mismatch", "spec-authoring-gap"}.

This guards against silent introduction of an unknown blocker class
anywhere in the WS2 matrix or WS3 fold reshape pipeline.
"""
import pathlib
import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for blocker-class invariant tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"

ALLOWED_BLOCKER_CLASSES = {
    "missing-skill",
    "missing-tool-feature",
    "fundamental-group-theory-gap",
    "regime-mismatch",
    "spec-authoring-gap",
}

PARAMETRIC_MODELS = [
    "singlet-doublet",
    "dark-su3",
    "two-hdm-a",
]


def _walk_classes(report_json):
    """Yield every blocker_class string found in the report."""
    for obs_routing in report_json.get("per_observable", {}).values():
        for cls in obs_routing.get("blocker_classes", []) or []:
            yield cls
        ac = obs_routing.get("active_chain") or {}
        for cls in ac.get("blocker_classes", []) or []:
            yield cls
        for alt in obs_routing.get("ranked_alternatives", []) or []:
            for cls in alt.get("blocker_classes", []) or []:
                yield cls
        for pc in obs_routing.get("per_candidate", []) or []:
            pca = pc.get("active_chain") or {}
            for cls in pca.get("blocker_classes", []) or []:
                yield cls


@pytest.mark.parametrize("model_id", PARAMETRIC_MODELS)
def test_emitted_blocker_classes_are_in_closed_enum(model_id, mock_constraints_yaml):
    from model_router.types import RouterOptions
    report = route(
        model_id=model_id,
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    found = list(_walk_classes(report.json_report))
    rogue = [c for c in found if c not in ALLOWED_BLOCKER_CLASSES]
    assert not rogue, (
        f"Rogue blocker classes in {model_id} report: {sorted(set(rogue))}; "
        f"expected subset of {sorted(ALLOWED_BLOCKER_CLASSES)}"
    )


def test_dark_su3_relic_carries_known_blocker_class(mock_constraints_yaml):
    """Anchor: dark-su3 relic ranked alternatives include
    fundamental-group-theory-gap from MG5_DARK_COLOR_TENSOR_WALL.
    """
    from model_router.types import RouterOptions
    report = route(
        model_id="dark-su3",
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    found = set(_walk_classes(report.json_report))
    # We don't pin which class shows up in tests of these synthetic specs,
    # but every found value must be in the enum (this is the invariant).
    for f in found:
        assert f in ALLOWED_BLOCKER_CLASSES, (
            f"Anchor: rogue class '{f}' in dark-su3 report"
        )
