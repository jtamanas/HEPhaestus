"""
test_p1_analytic_module_status_adapter.py — Decision 6 + manager D4 (STUB marker).

Tests collected but SKIPPED until analytic_module_status impl lands (S8).
"""
import pytest

ams_mod = pytest.importorskip(
    "model_router.stages.analytic_module_status",
    reason="analytic_module_status not yet implemented (awaiting S8)",
)
_resolve_analytic_module_status = ams_mod._resolve_analytic_module_status


MOCK_REGISTRY = {
    "exceptions": {
        "dark-su3": {
            "analytic_module": "analytic_models.dark_su3",
            "status": "active",
        }
    }
}


class TestAnalyticModuleStatusAdapter:
    """Decision 6 six-value enum tests."""

    def test_status_registered_active_for_dsu3(self):
        """dark-su3 with active registry entry → 'registered_active'."""
        result = _resolve_analytic_module_status(
            model_id="dark-su3",
            analytic_module="analytic_models.dark_su3",
            registry=MOCK_REGISTRY,
        )
        assert result == "registered_active"

    def test_status_stub_for_2hdma(self):
        """
        2HDM+a uses analytic_models.stub_unimplemented → 'stub'.
        This test requires the STUB = True constant to be present in stub_unimplemented.py
        (added by S8 first action per manager D4).
        """
        result = _resolve_analytic_module_status(
            model_id="two-hdm-a",
            analytic_module="analytic_models.stub_unimplemented",
            registry={"exceptions": {}},  # no registry entry for 2HDM+a
        )
        assert result == "stub"

    def test_status_missing_when_no_module(self):
        """No analytic_module in spec → 'missing'."""
        result = _resolve_analytic_module_status(
            model_id="singlet-doublet",
            analytic_module=None,
            registry={"exceptions": {}},
        )
        assert result == "missing"

    def test_status_unregistered_when_module_present_but_no_registry_entry(self):
        """Module path resolves but no registry entry → 'unregistered'."""
        # Use a real module that exists (dark_su3) but with no registry entry
        result = _resolve_analytic_module_status(
            model_id="mystery-model",
            analytic_module="analytic_models.dark_su3",
            registry={"exceptions": {}},
        )
        assert result == "unregistered"

    def test_status_deprecated_for_deprecated_registry_entry(self):
        """Registry entry with status='deprecated' → 'deprecated'."""
        registry = {
            "exceptions": {
                "old-model": {
                    "analytic_module": "analytic_models.dark_su3",
                    "status": "deprecated",
                }
            }
        }
        result = _resolve_analytic_module_status(
            model_id="old-model",
            analytic_module="analytic_models.dark_su3",
            registry=registry,
        )
        assert result == "deprecated"

    def test_status_returns_string_from_closed_enum(self):
        """Return value is always from the six-value closed enum."""
        VALID = {"registered_active", "deprecated", "retired", "unregistered", "stub", "missing"}
        for module, model, reg in [
            (None, "x", {"exceptions": {}}),
            ("analytic_models.stub_unimplemented", "y", {"exceptions": {}}),
            ("analytic_models.dark_su3", "dark-su3", MOCK_REGISTRY),
        ]:
            result = _resolve_analytic_module_status(
                model_id=model,
                analytic_module=module,
                registry=reg,
            )
            assert result in VALID, f"Got {result!r} not in {VALID}"
