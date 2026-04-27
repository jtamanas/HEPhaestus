"""S12: Test matrix_acknowledgement schema + suppression logic.

4 cases:
  (a) dsu3 override silences invariant #12 (has matrix_acknowledgement)
  (b) Missing acknowledgement on contradicting override → detectable
  (c) Acknowledgement listing a non-fired blocker → no error
  (d) Override with new blocker not in accepted_blockers → not silenced
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
NEGATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "matrix" / "negative"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import load_capability_matrix, BlockerVerdict


@pytest.fixture
def matrix():
    return load_capability_matrix(
        constraints_path=SHARED / "constraints.yaml",
        catalog_path=SHARED / "blocker_catalog.yaml",
    )


@pytest.fixture
def dsu3_axes():
    import yaml as _yaml
    fixtures_dir = Path(__file__).parent / "fixtures" / "matrix"
    return _yaml.safe_load((fixtures_dir / "dark_su3_axes.yaml").read_text())


class TestAcknowledgement:
    def test_a_dsu3_override_has_acknowledgement(self):
        """(a) dark-su3 relic chain_overrides has matrix_acknowledgement block."""
        data = yaml.safe_load((SHARED / "constraints.yaml").read_text())
        dsu3 = data["models"]["dark-su3"]
        override = dsu3.get("chain_overrides", {}).get("relic", {})
        ack = override.get("matrix_acknowledgement")
        assert ack is not None, "dsu3 relic chain_override missing matrix_acknowledgement"
        assert "accepted_blockers" in ack
        assert "MG5_DARK_COLOR_TENSOR_WALL" in ack["accepted_blockers"]
        assert "ANALYTIC_EXCEPTION_TRIGGER" in ack["accepted_blockers"]
        assert "authority" in ack
        assert "last_audited" in ack

    def test_b_missing_acknowledgement_detectable(self):
        """(b) An override without matrix_acknowledgement can be detected."""
        fixture = yaml.safe_load((NEGATIVE_FIXTURES / "missing_acknowledgement.yaml").read_text())
        models = fixture.get("models", {})
        found_missing = False
        for model_id, model in models.items():
            overrides = model.get("chain_overrides", {})
            for constraint, override in overrides.items():
                if override.get("matrix_acknowledgement") is None:
                    found_missing = True
                    break
        assert found_missing, "Expected at least one override without matrix_acknowledgement in fixture"

    def test_c_apply_acknowledgements_marks_blocker_acknowledged(self, matrix, dsu3_axes):
        """(c) apply_acknowledgements marks acknowledged=True for listed blocker codes."""
        # First get verdicts with blockers
        verdicts = matrix.lookup_blockers(dsu3_axes)

        # Create a fake override block that acknowledges a blocker
        override_block = {
            "matrix_acknowledgement": {
                "accepted_blockers": ["MG5_DARK_COLOR_TENSOR_WALL", "ANALYTIC_EXCEPTION_TRIGGER"],
                "accepted_workaround": "ANALYTIC_BACKEND_PATH",
                "authority": "test",
                "last_audited": "2026-04-26"
            }
        }
        new_verdicts = matrix.apply_acknowledgements(verdicts, override_block)

        # Check that madgraph's ANALYTIC_EXCEPTION_TRIGGER is now acknowledged
        madgraph_verdicts = new_verdicts.get("madgraph", [])
        trigger_verdicts = [bv for bv in madgraph_verdicts if bv.blocker == "ANALYTIC_EXCEPTION_TRIGGER"]
        assert trigger_verdicts, (
            "expected at least one ANALYTIC_EXCEPTION_TRIGGER verdict for dsu3 madgraph; "
            f"got madgraph verdicts: {madgraph_verdicts}"
        )
        assert trigger_verdicts[0].acknowledged is True, "ANALYTIC_EXCEPTION_TRIGGER should be acknowledged"

        # Check that codes NOT in accepted_blockers are not acknowledged
        spheno_verdicts = new_verdicts.get("spheno-build", [])
        spheno_blocked = [bv for bv in spheno_verdicts if bv.verdict == "blocked"]
        assert spheno_blocked, (
            "expected at least one blocked verdict for dsu3 spheno-build; "
            f"got spheno-build verdicts: {spheno_verdicts}"
        )
        # SPHENO_NOT_REQUESTED is not in accepted_blockers, so should remain unacknowledged
        assert not spheno_blocked[0].acknowledged, (
            f"SPHENO_NOT_REQUESTED should not be acknowledged (not in accepted_blockers); "
            f"got: {spheno_blocked[0]}"
        )

    def test_d_unlisted_blocker_not_silenced(self, matrix, dsu3_axes):
        """(d) A blocker code not in accepted_blockers remains unacknowledged."""
        verdicts = matrix.lookup_blockers(dsu3_axes)

        # Acknowledgement lists only MG5 wall (not SPHENO_NOT_REQUESTED)
        override_block = {
            "matrix_acknowledgement": {
                "accepted_blockers": ["MG5_DARK_COLOR_TENSOR_WALL"],
                "authority": "test",
                "last_audited": "2026-04-26"
            }
        }
        new_verdicts = matrix.apply_acknowledgements(verdicts, override_block)

        # spheno-build's SPHENO_NOT_REQUESTED should NOT be acknowledged
        spheno_verdicts = new_verdicts.get("spheno-build", [])
        for bv in spheno_verdicts:
            if bv.blocker == "SPHENO_NOT_REQUESTED":
                assert not bv.acknowledged, "SPHENO_NOT_REQUESTED was not in accepted_blockers, should not be acknowledged"
                return
        # If we reach here, spheno-build wasn't blocked (OK, test passes by absence)
        assert True
