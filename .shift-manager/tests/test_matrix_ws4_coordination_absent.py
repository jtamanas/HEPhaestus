"""S18-absent: WS4 coordination test — absent-mode fallback.

Always runs. Tests the behavior when analytic_exceptions.yaml is absent.

Asserts:
  1. compute_analytic_module_status returns 'missing' for all 3 demo models
  2. analytic_backend row's ANALYTIC_MODULE_MISSING rule fires for every demo model
  3. escape_hatch_target: ws4 cells exist in the matrix shape
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

from matrix_lookup import load_capability_matrix

# Confirm registry is absent (always-absent mode)
REGISTRY_PATH = SHARED / "analytic_exceptions.yaml"


@pytest.fixture
def matrix_no_registry():
    """Load matrix without WS4 registry."""
    return load_capability_matrix(
        constraints_path=SHARED / "constraints.yaml",
        catalog_path=SHARED / "blocker_catalog.yaml",
        registry_path=None,  # force absent even if file exists
    )


@pytest.fixture
def dark_su3_axes():
    return yaml.safe_load((FIXTURES / "dark_su3_axes.yaml").read_text())


@pytest.fixture
def singlet_doublet_axes():
    return yaml.safe_load((FIXTURES / "singlet_doublet_axes.yaml").read_text())


@pytest.fixture
def two_hdm_a_axes():
    return yaml.safe_load((FIXTURES / "2hdm_a_axes.yaml").read_text())


class TestWS4CoordinationAbsent:
    def test_1_analytic_module_status_missing_all_models(self, matrix_no_registry):
        """#1: Without registry, compute_analytic_module_status returns 'missing' for all models."""
        assert matrix_no_registry.compute_analytic_module_status("dark-su3") == "missing"
        assert matrix_no_registry.compute_analytic_module_status("singlet-doublet") == "missing"
        assert matrix_no_registry.compute_analytic_module_status("2hdm-a") == "missing"
        # Also test an arbitrary model
        assert matrix_no_registry.compute_analytic_module_status("nonexistent-model") == "missing"

    def test_2_analytic_backend_blocked_for_all_models(
        self, matrix_no_registry, dark_su3_axes, singlet_doublet_axes, two_hdm_a_axes
    ):
        """#2: Without registry, analytic_backend fires ANALYTIC_MODULE_MISSING for every model."""
        for axes_bundle, model_name in [
            (dark_su3_axes, "dark-su3"),
            (singlet_doublet_axes, "singlet-doublet"),
            (two_hdm_a_axes, "2hdm-a"),
        ]:
            # Ensure analytic_module_status is "missing"
            axes_copy = dict(axes_bundle)
            axes_copy["model_runtime"] = {"analytic_module_status": "missing"}

            verdicts = matrix_no_registry.lookup_blockers(axes_copy)
            backend_verdicts = verdicts.get("analytic_backend", [])
            blocked = [bv for bv in backend_verdicts if bv.verdict == "blocked"]
            assert blocked, (
                f"Expected ANALYTIC_MODULE_MISSING for {model_name} but got no blocked verdicts. "
                f"Verdicts: {backend_verdicts}"
            )
            assert any(bv.blocker == "ANALYTIC_MODULE_MISSING" for bv in blocked), (
                f"Expected ANALYTIC_MODULE_MISSING blocker for {model_name}, got: "
                f"{[bv.blocker for bv in blocked]}"
            )

    def test_3_escape_hatch_target_ws4_declared(self, matrix_no_registry, dark_su3_axes):
        """#3: escape_hatch_target: ws4 cells exist in the matrix for dark-su3."""
        verdicts = matrix_no_registry.lookup_blockers(dark_su3_axes)
        ws4_referrers = []
        for prereq_id, bvlist in verdicts.items():
            for bv in bvlist:
                if bv.escape_hatch_target == "ws4":
                    ws4_referrers.append(f"{prereq_id}: {bv.blocker}")

        assert ws4_referrers, (
            "Expected at least one verdict with escape_hatch_target='ws4' for dark-su3. "
            f"Got verdicts: {[(p, [b.verdict for b in vl]) for p, vl in verdicts.items()]}"
        )
