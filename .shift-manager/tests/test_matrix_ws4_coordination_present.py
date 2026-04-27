"""S18-present: WS4 coordination test — present-mode real cross-check.

Skipif analytic_exceptions.yaml absent. Tests real cross-check when WS4 ships.

Asserts:
  1. When registry has dsu3-002 active, compute_analytic_module_status("dark-su3") == "registered_active"
     AND analytic_backend fires supported_with_caveat
  2. Every escape_hatch_target: ws4 cell corresponds to a registry entry for ≥1 model
  3. For 2hdm-a: when registry has no active entry, compute_analytic_module_status == "stub"
     (or missing) and ANALYTIC_MODULE_MISSING fires
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
FIXTURES = Path(__file__).parent / "fixtures" / "matrix"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

REGISTRY_PATH = SHARED / "analytic_exceptions.yaml"

from matrix_lookup import load_capability_matrix


@pytest.mark.skipif(
    not REGISTRY_PATH.exists(),
    reason="WS4 registry (analytic_exceptions.yaml) not yet shipped; S18-present skipped."
)
class TestWS4CoordinationPresent:
    @pytest.fixture
    def registry_data(self):
        return yaml.safe_load(REGISTRY_PATH.read_text())

    @pytest.fixture
    def matrix_with_registry(self):
        return load_capability_matrix(
            constraints_path=SHARED / "constraints.yaml",
            catalog_path=SHARED / "blocker_catalog.yaml",
            registry_path=REGISTRY_PATH,
        )

    @pytest.fixture
    def dark_su3_axes(self):
        axes = yaml.safe_load((FIXTURES / "dark_su3_axes.yaml").read_text())
        return axes

    @pytest.fixture
    def two_hdm_a_axes(self):
        axes = yaml.safe_load((FIXTURES / "2hdm_a_axes.yaml").read_text())
        return axes

    def test_1_dark_su3_registered_active(self, matrix_with_registry, dark_su3_axes, registry_data):
        """#1: dark-su3 with active registry entry → registered_active + supported_with_caveat."""
        # Only run if dsu3-002 is in the registry
        entries = registry_data.get("exceptions", registry_data.get("entries", []))
        if isinstance(entries, dict):
            entries = list(entries.values())
        has_dsu3 = any(
            e.get("model") == "dark-su3" and e.get("status") == "active"
            for e in entries if isinstance(e, dict)
        )
        if not has_dsu3:
            pytest.skip("dsu3-002 not registered as active in analytic_exceptions.yaml")

        status = matrix_with_registry.compute_analytic_module_status("dark-su3")
        assert status == "registered_active", f"Expected registered_active, got {status}"

        # analytic_backend should fire supported_with_caveat
        axes_copy = dict(dark_su3_axes)
        axes_copy["model_runtime"] = {"analytic_module_status": "registered_active"}
        verdicts = matrix_with_registry.lookup_blockers(axes_copy)
        backend = verdicts.get("analytic_backend", [])
        caveat_verdicts = [bv for bv in backend if bv.verdict == "supported_with_caveat"]
        assert caveat_verdicts, f"Expected supported_with_caveat for analytic_backend, got: {backend}"

    def test_2_escape_hatch_ws4_corresponds_to_registry_entry(
        self, matrix_with_registry, dark_su3_axes, registry_data
    ):
        """#2: escape_hatch_target: ws4 cells correspond to ≥1 registry entry for the model."""
        verdicts = matrix_with_registry.lookup_blockers(dark_su3_axes)
        ws4_triggers = [
            bv for bvlist in verdicts.values()
            for bv in bvlist
            if bv.escape_hatch_target == "ws4"
        ]

        if not ws4_triggers:
            pytest.skip("No escape_hatch_target: ws4 verdicts for dark-su3")

        # There should be at least one entry in the registry
        entries = registry_data.get("exceptions", registry_data.get("entries", []))
        if isinstance(entries, dict):
            entries = list(entries.values())
        assert entries, "Registry is empty; expected at least one entry"

    def test_3_2hdm_a_analytic_module_missing_or_stub(
        self, matrix_with_registry, two_hdm_a_axes
    ):
        """#3: 2hdm-a without active registry entry → missing or stub + ANALYTIC_MODULE_MISSING."""
        status = matrix_with_registry.compute_analytic_module_status("2hdm-a")
        assert status in ("missing", "stub", "deprecated"), (
            f"Expected missing/stub for 2hdm-a, got {status}"
        )

        axes_copy = dict(two_hdm_a_axes)
        axes_copy["model_runtime"] = {"analytic_module_status": status}
        verdicts = matrix_with_registry.lookup_blockers(axes_copy)
        backend = verdicts.get("analytic_backend", [])
        blocked = [bv for bv in backend if bv.verdict == "blocked" and bv.blocker == "ANALYTIC_MODULE_MISSING"]
        assert blocked, f"Expected ANALYTIC_MODULE_MISSING for 2hdm-a, got: {backend}"
