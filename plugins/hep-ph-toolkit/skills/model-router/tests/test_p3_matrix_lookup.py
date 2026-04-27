"""
test_p3_matrix_lookup.py — Phase 4: stage_p3_matrix_lookup tests (TDD scaffold).

Tests collected but SKIPPED until matrix_lookup impl lands (S10).
"""
import pytest

matrix_mod = pytest.importorskip(
    "model_router.stages.matrix_lookup",
    reason="stage_p3_matrix_lookup not yet implemented (awaiting S10)",
)
stage_p3_matrix_lookup = matrix_mod.stage_p3_matrix_lookup


class TestP3MatrixLookup:
    """P3 matrix lookup tests."""

    def test_lookup_singlet_doublet_maddm_supported(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """singlet-doublet with SM-only gauge group → maddm: supported for relic."""
        axes, ctx, verdict = _setup("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        result = stage_p3_matrix_lookup(axes, ctx, verdict)
        relic_folds = result.by_observable.get("relic", [])
        maddm_fold = next((f for f in relic_folds if f.prereq_id == "maddm"), None)
        assert maddm_fold is not None
        assert maddm_fold.overall_verdict in ("supported", "supported_with_caveat")

    def test_lookup_dark_su3_maddm_blocked(
        self, mock_constraints_yaml, spec_dark_su3
    ):
        """dark-su3 with SU(N) gauge group → maddm: blocked (MG5_DARK_COLOR_TENSOR_WALL)."""
        axes, ctx, verdict = _setup("dark-su3", spec_dark_su3, mock_constraints_yaml,
                                    a1="SM + extra SU(N)")
        result = stage_p3_matrix_lookup(axes, ctx, verdict)
        relic_folds = result.by_observable.get("relic", [])
        maddm_fold = next((f for f in relic_folds if f.prereq_id == "maddm"), None)
        assert maddm_fold is not None
        assert maddm_fold.overall_verdict == "blocked"
        assert "MG5_DARK_COLOR_TENSOR_WALL" in maddm_fold.blockers

    def test_lookup_missing_hep_ph_demo_raises(
        self, mock_constraints_yaml, spec_singlet_doublet, absent_hep_ph_demo
    ):
        """When hep-ph-demo matrix_lookup is absent → WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO."""
        from model_router.types import WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO
        axes, ctx, verdict = _setup("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        with pytest.raises((WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO, ImportError)):
            stage_p3_matrix_lookup(axes, ctx, verdict)

    def test_lookup_returns_role_assignments(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """Each fold has role_for_observable populated from capabilities.role."""
        axes, ctx, verdict = _setup("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        result = stage_p3_matrix_lookup(axes, ctx, verdict)
        relic_folds = result.by_observable.get("relic", [])
        maddm_fold = next((f for f in relic_folds if f.prereq_id == "maddm"), None)
        assert maddm_fold is not None
        assert maddm_fold.role_for_observable in (
            "primary", "validator", "specialty", "escape_hatch", "none"
        )

    def test_lookup_blocker_classes_from_closed_enum(
        self, mock_constraints_yaml, spec_dark_su3
    ):
        """All blocker_classes in folds are from the five-value closed enum."""
        VALID = {
            "missing-skill", "missing-tool-feature", "fundamental-group-theory-gap",
            "regime-mismatch", "spec-authoring-gap"
        }
        axes, ctx, verdict = _setup("dark-su3", spec_dark_su3, mock_constraints_yaml,
                                    a1="SM + extra SU(N)")
        result = stage_p3_matrix_lookup(axes, ctx, verdict)
        for folds in result.by_observable.values():
            for fold in folds:
                for cls in fold.blocker_classes:
                    assert cls in VALID, f"Invalid blocker_class: {cls!r}"

    def test_lookup_micromegas_validator_role(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """micromegas has role=validator for relic in mock registry."""
        axes, ctx, verdict = _setup("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        result = stage_p3_matrix_lookup(axes, ctx, verdict)
        relic_folds = result.by_observable.get("relic", [])
        mm_fold = next((f for f in relic_folds if f.prereq_id == "micromegas"), None)
        assert mm_fold is not None
        assert mm_fold.role_for_observable == "validator"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(model_id, spec, constraints_path, a1="SM only"):
    import yaml
    from model_router.types import (
        LoadedContext, RouterOptions, AxisBundle, CandidateSpec, ExceptionVerdict
    )
    raw = yaml.safe_load(open(constraints_path))
    meta = raw.get("models", {}).get(model_id, {})
    ctx = LoadedContext(
        model_id=model_id,
        observables=["relic"],
        options=RouterOptions(),
        model_meta=meta,
        model_spec=spec,
        prereqs=raw.get("prereqs", {}),
        constraints_raw=raw,
        blocker_catalog={},
        analytic_exceptions={},
        config={},
    )
    axes = AxisBundle(
        A1=a1,
        A8="active",
        candidates=[CandidateSpec(name="chi_1")],
        model_props={"analytic_module_status": "missing"},
    )
    verdict = ExceptionVerdict(verdict="CLEAR")
    return axes, ctx, verdict
