"""
test_p1_extract_axes.py — Phase 2: stage_p1_validate_and_extract tests (TDD scaffold).

Tests collected but SKIPPED until extract_axes impl lands (S7).
"""
import pytest

extract_mod = pytest.importorskip(
    "model_router.stages.extract_axes",
    reason="stage_p1_validate_and_extract not yet implemented (awaiting S7)",
)
stage_p1_validate_and_extract = extract_mod.stage_p1_validate_and_extract


class TestP1ExtractAxesBasic:
    """P1 happy-path tests."""

    def test_extract_singlet_doublet_returns_axis_bundle(
        self, mock_constraints_yaml, spec_singlet_doublet, tmp_path
    ):
        """singlet-doublet spec → AxisBundle with populated axes."""
        from model_router.types import LoadedContext, RouterOptions
        ctx = _make_ctx("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        axes = stage_p1_validate_and_extract(ctx)
        assert axes is not None
        assert axes.A1 is not None  # gauge extension class must be set

    def test_extract_dark_su3_multi_component_candidates(
        self, mock_constraints_yaml, spec_dark_su3, tmp_path
    ):
        """dark-su3 has two DM candidates (V, Psi)."""
        ctx = _make_ctx("dark-su3", spec_dark_su3, mock_constraints_yaml)
        axes = stage_p1_validate_and_extract(ctx)
        assert len(axes.candidates) == 2
        names = [c.name for c in axes.candidates]
        assert "V" in names and "Psi" in names

    def test_extract_archived_model_raises_spec_archived_error(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """When A8 == 'archived', SpecArchivedError is raised."""
        from model_router.types import SpecArchivedError
        # Set authoring_status to archived — taxonomy.read_axes returns A8='archived',
        # which triggers the hard-halt check in stage_p1_validate_and_extract.
        spec = dict(spec_singlet_doublet)
        spec["authoring_status"] = "archived"
        ctx = _make_ctx("singlet-doublet", spec, mock_constraints_yaml)
        with pytest.raises(SpecArchivedError):
            stage_p1_validate_and_extract(ctx)


class TestP1ExtractAxesErrors:
    """P1 error / WS1 hard-gate tests."""

    def test_extract_ws1_absent_raises_ws1_not_merged(
        self, mock_constraints_yaml, spec_singlet_doublet, monkeypatch
    ):
        """When taxonomy.read_axes import fails → WS1NotMerged (exit 1)."""
        import sys
        # Simulate WS1 absent by making taxonomy un-importable
        saved = sys.modules.pop("taxonomy", None)
        try:
            # monkeypatch the import guard in extract_axes
            monkeypatch.setattr(
                "model_router.stages.extract_axes._read_axes_available",
                False,
            )
            from model_router.types import WS1NotMerged
            ctx = _make_ctx("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
            with pytest.raises(WS1NotMerged):
                stage_p1_validate_and_extract(ctx)
        finally:
            if saved is not None:
                sys.modules["taxonomy"] = saved

    def test_extract_leptoquark_has_empty_candidates(
        self, mock_constraints_yaml, spec_leptoquark_synthetic
    ):
        """Leptoquark synthetic has dm_phenomenology.candidates == []."""
        ctx = _make_ctx("leptoquark-synthetic", spec_leptoquark_synthetic, mock_constraints_yaml,
                        model_meta={"dm_phenomenology": {"candidates": []}})
        axes = stage_p1_validate_and_extract(ctx)
        assert axes.candidates == []

    def test_extract_returns_model_props_with_analytic_module_status(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """model_props["analytic_module_status"] is present in the AxisBundle."""
        ctx = _make_ctx("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        axes = stage_p1_validate_and_extract(ctx)
        assert "analytic_module_status" in axes.model_props


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_ctx(model_id, spec, constraints_path, model_meta=None):
    """Build a minimal LoadedContext for testing extract_axes in isolation."""
    import yaml
    from model_router.types import LoadedContext, RouterOptions

    raw = yaml.safe_load(open(constraints_path))
    meta = model_meta or raw.get("models", {}).get(model_id, {})
    return LoadedContext(
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
