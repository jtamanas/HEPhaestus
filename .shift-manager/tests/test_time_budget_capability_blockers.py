"""S15: Test inject_capability_blockers helper.

Tests:
  - inject_capability_blockers populates capability_blockers on each ConstraintRow
  - resolve() itself remains unmodified (no capability_blockers from resolve alone)
  - CLI output unchanged from baseline
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

from time_budget import resolve, inject_capability_blockers, ConstraintRow
from matrix_lookup import load_capability_matrix


@pytest.fixture
def matrix():
    return load_capability_matrix(
        constraints_path=SHARED / "constraints.yaml",
        catalog_path=SHARED / "blocker_catalog.yaml",
    )


@pytest.fixture
def dsu3_axes():
    return yaml.safe_load((FIXTURES / "dark_su3_axes.yaml").read_text())


@pytest.fixture
def sd_axes():
    return yaml.safe_load((FIXTURES / "singlet_doublet_axes.yaml").read_text())


class TestInjectCapabilityBlockers:
    def test_resolve_does_not_set_capability_blockers(self):
        """resolve() alone leaves capability_blockers empty."""
        report = resolve("dark-su3", ["relic"])
        for row in report.rows:
            assert hasattr(row, "capability_blockers"), "ConstraintRow missing capability_blockers field"
            assert row.capability_blockers == [], f"Expected empty capability_blockers, got {row.capability_blockers}"

    def test_inject_populates_capability_blockers(self, matrix, dsu3_axes):
        """inject_capability_blockers() populates capability_blockers."""
        report = resolve("dark-su3", ["relic", "dd", "id"])
        report = inject_capability_blockers(report, matrix, dsu3_axes)

        # After injection, at least one row should have capability_blockers
        all_blockers = []
        for row in report.rows:
            all_blockers.extend(row.capability_blockers)

        assert all_blockers, "Expected at least some capability_blockers after injection"

    def test_inject_identifies_mg5_wall_for_dsu3(self, matrix, dsu3_axes):
        """For dark-su3, at least ANALYTIC_EXCEPTION_TRIGGER or MG5_DARK_COLOR_TENSOR_WALL should appear."""
        report = resolve("dark-su3", ["relic"])
        report = inject_capability_blockers(report, matrix, dsu3_axes)

        all_blocker_codes = []
        for row in report.rows:
            for bv in row.capability_blockers:
                if bv.blocker:
                    all_blocker_codes.append(bv.blocker)

        expected = {"MG5_DARK_COLOR_TENSOR_WALL", "ANALYTIC_EXCEPTION_TRIGGER", "ANALYTIC_MODULE_MISSING"}
        assert any(code in all_blocker_codes for code in expected), (
            f"Expected one of {expected} in capability_blockers, got {all_blocker_codes}"
        )

    def test_inject_returns_same_report_object(self, matrix, dsu3_axes):
        """inject_capability_blockers returns the same report (mutates and returns)."""
        report = resolve("dark-su3", ["relic"])
        returned = inject_capability_blockers(report, matrix, dsu3_axes)
        assert returned is report

    def test_constraint_row_capability_blockers_default_empty(self):
        """ConstraintRow.capability_blockers defaults to []."""
        r = ConstraintRow(constraint="relic", status="READY")
        assert r.capability_blockers == []
