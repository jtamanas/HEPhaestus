"""
test_p0_load.py — Phase 1: stage_p0_load tests (TDD scaffold; manager D7).

Tests are collected but SKIPPED until stage_p0_load impl lands (S6).
pytest.importorskip pattern: if the module is absent, all tests skip.
"""
import pytest

load_mod = pytest.importorskip(
    "model_router.stages.load",
    reason="stage_p0_load not yet implemented (awaiting S6)",
)
stage_p0_load = load_mod.stage_p0_load


class TestP0LoadBasic:
    """P0 happy-path tests."""

    def test_load_singlet_doublet_returns_loaded_context(
        self, mock_constraints_yaml, mock_blocker_catalog, mock_analytic_exceptions, tmp_path
    ):
        """singlet-doublet registered in mock registry → LoadedContext returned."""
        ctx = stage_p0_load(
            model_id="singlet-doublet",
            observables=["relic"],
            options=None,
            constraints_path=mock_constraints_yaml,
            blocker_catalog_path=None,
            analytic_exceptions_path=None,
        )
        assert ctx.model_id == "singlet-doublet"
        assert "relic" in ctx.observables

    def test_load_sets_default_observables_when_none_given(
        self, mock_constraints_yaml
    ):
        """When observables=None, P0 derives defaults from model meta."""
        ctx = stage_p0_load(
            model_id="singlet-doublet",
            observables=None,
            options=None,
            constraints_path=mock_constraints_yaml,
        )
        assert len(ctx.observables) > 0

    def test_load_absent_blocker_catalog_sets_absent_registries(
        self, mock_constraints_yaml, tmp_path
    ):
        """When blocker_catalog.yaml is absent, absent_registries is non-empty."""
        ctx = stage_p0_load(
            model_id="singlet-doublet",
            observables=["relic"],
            options=None,
            constraints_path=mock_constraints_yaml,
            blocker_catalog_path=tmp_path / "nonexistent_catalog.yaml",
        )
        assert "blocker_catalog" in ctx.absent_registries


class TestP0LoadErrors:
    """P0 error-path tests."""

    def test_load_unknown_model_raises_model_not_in_registry(
        self, mock_constraints_yaml
    ):
        """Unknown model_id → ModelNotInRegistry."""
        from model_router.types import ModelNotInRegistry
        with pytest.raises(ModelNotInRegistry):
            stage_p0_load(
                model_id="nonexistent-model-xyz",
                observables=["relic"],
                options=None,
                constraints_path=mock_constraints_yaml,
            )

    def test_load_ws2_not_merged_raises_ws2_not_merged(
        self, mock_constraints_yaml, monkeypatch
    ):
        """If ConstraintRow.capability_blockers is absent → WS2NotMerged at entry."""
        import time_budget
        # Simulate WS2 not merged by removing capability_blockers from ConstraintRow
        original_fields = time_budget.ConstraintRow.__dataclass_fields__.copy()

        from model_router.types import WS2NotMerged
        # We monkeypatch hasattr to return False for capability_blockers
        monkeypatch.setattr(
            "model_router.stages.load._has_capability_blockers",
            lambda: False,
        )
        with pytest.raises(WS2NotMerged):
            stage_p0_load(
                model_id="singlet-doublet",
                observables=["relic"],
                options=None,
                constraints_path=mock_constraints_yaml,
            )

    def test_load_corrupt_registry_raises_registry_corrupt(
        self, tmp_path
    ):
        """Malformed YAML in constraints_path → RegistryCorrupt."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("{ this: is: not: valid: yaml: :")
        from model_router.types import RegistryCorrupt
        with pytest.raises((RegistryCorrupt, Exception)):
            stage_p0_load(
                model_id="singlet-doublet",
                observables=["relic"],
                options=None,
                constraints_path=bad_yaml,
            )
