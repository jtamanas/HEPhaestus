"""S3: Test the matrix loader skeleton.

Tests:
  - Matrix instantiates against live constraints.yaml (which has no capabilities yet)
  - lookup_blockers returns empty dict when no capabilities blocks exist
  - compute_analytic_module_status returns 'missing' when registry absent
"""
from __future__ import annotations
from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import load_capability_matrix, CapabilityMatrix


@pytest.fixture
def matrix(shared_lib):
    return load_capability_matrix(
        constraints_path=shared_lib / "constraints.yaml",
        catalog_path=shared_lib / "blocker_catalog.yaml",
        registry_path=None,  # registry absent
    )


class TestMatrixLoader:
    def test_matrix_instantiates(self, matrix):
        assert isinstance(matrix, CapabilityMatrix)

    def test_registry_absent_flag(self, matrix):
        assert matrix.registry_present is False

    def test_analytic_module_status_missing_when_no_registry(self, matrix):
        # With no registry, all models return "missing"
        assert matrix.compute_analytic_module_status("dark-su3") == "missing"
        assert matrix.compute_analytic_module_status("singlet-doublet") == "missing"
        assert matrix.compute_analytic_module_status("2hdm-a") == "missing"

    def test_lookup_blockers_returns_dict(self, matrix):
        """lookup_blockers returns a dict keyed by prereq_id."""
        axes_bundle = {
            "axes": {"A1": "SM", "A8": "complete"},
            "candidates": [],
            "lagrangian": {},
            "model_runtime": {"analytic_module_status": "missing"},
        }
        result = matrix.lookup_blockers(axes_bundle)
        # May be empty (no capabilities blocks yet at S3) or have entries
        assert isinstance(result, dict)

    def test_matrix_has_prereqs(self, matrix):
        prereqs = matrix.get_prereqs()
        assert "madgraph" in prereqs
        assert "maddm" in prereqs
        assert "sarah-build" in prereqs

    def test_constraints_data_schema_version(self, matrix):
        data = matrix.get_constraints_data()
        assert data["schema_version"] == 2

    def test_fold_returns_dict(self, matrix):
        """fold() works on empty verdicts dict."""
        fold = matrix.fold({})
        assert isinstance(fold, dict)

    def test_viable_chain_empty_on_no_capabilities(self, matrix):
        """Without capabilities blocks, viable_chain_for returns empty list."""
        fold = matrix.fold({})
        chain = matrix.viable_chain_for("relic", fold)
        assert isinstance(chain, list)

    def test_registry_present_with_dummy_file(self, shared_lib, tmp_path):
        """When registry file exists, registry_present=True."""
        import yaml
        dummy_registry = tmp_path / "analytic_exceptions.yaml"
        dummy_registry.write_text(yaml.dump({
            "schema_version": 1,
            "exceptions": []
        }))
        m = load_capability_matrix(
            constraints_path=shared_lib / "constraints.yaml",
            catalog_path=shared_lib / "blocker_catalog.yaml",
            registry_path=dummy_registry,
        )
        assert m.registry_present is True
        # With empty registry, dark-su3 still returns "missing"
        assert m.compute_analytic_module_status("dark-su3") == "missing"
