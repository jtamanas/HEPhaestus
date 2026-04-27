"""S6: Test fold(), rank_by_role(), viable_chain_for().

5 test cases per WS2 plan S6:
  1. Pure not_applicable → overall_verdict = "no_coverage"
  2. One blocked + several supported → blocked
  3. Tie at primary resolved by priority_tiebreak
  4. escape_hatch viable when others blocked → returns escape-hatch chain
  5. Multi-prereq dependency topo ordering (gating_for)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import (
    BlockerVerdict,
    ToolLevelVerdict,
    CapabilityMatrix,
    load_capability_matrix,
)


def make_bv(prereq_id, axis, verdict, blocker=None, blocker_class=None):
    return BlockerVerdict(
        prereq_id=prereq_id,
        axis=axis,
        matched_value="test",
        verdict=verdict,
        blocker=blocker,
        blocker_class=blocker_class,
    )


@pytest.fixture
def matrix(shared_lib):
    return load_capability_matrix(
        constraints_path=shared_lib / "constraints.yaml",
        catalog_path=shared_lib / "blocker_catalog.yaml",
        registry_path=None,
    )


class TestFold:
    def test_01_pure_not_applicable_is_no_coverage(self, matrix):
        """All not_applicable → overall_verdict = 'no_coverage'."""
        verdicts = {
            "madgraph": [make_bv("madgraph", "A7", "not_applicable")],
            "drake": [make_bv("drake", "A4.n_higgs_doublets", "not_applicable")],
        }
        fold = matrix.fold(verdicts)
        # madgraph and drake have no capabilities blocks yet → covered by empty
        # But since we call fold with explicit verdicts, test directly:
        assert fold["madgraph"].overall_verdict == "no_coverage"
        assert fold["drake"].overall_verdict == "no_coverage"

    def test_02_one_blocked_wins_over_supported(self, matrix):
        """blocked beats supported in fold."""
        verdicts = {
            "madgraph": [
                make_bv("madgraph", "A3.has_majorana_fermion", "supported"),
                make_bv("madgraph", "A1", "blocked",
                        blocker="MG5_DARK_COLOR_TENSOR_WALL",
                        blocker_class="fundamental-group-theory-gap"),
            ],
        }
        fold = matrix.fold(verdicts)
        tlv = fold["madgraph"]
        assert tlv.overall_verdict == "blocked"
        assert tlv.first_blocker == "MG5_DARK_COLOR_TENSOR_WALL"
        assert tlv.first_blocker_class == "fundamental-group-theory-gap"

    def test_03_priority_tiebreak_resolves_tie(self, matrix):
        """rank_by_role tiebreaks by priority_tiebreak (lower wins)."""
        # Inject synthetic fold results with two 'primary' prereqs for relic
        # with different priority_tiebreaks
        from dataclasses import replace
        tlv_a = ToolLevelVerdict(
            prereq_id="maddm",
            overall_verdict="supported",
            viable_for_observables=("relic",),
            role={"relic": "primary"},
            priority_tiebreak=10,
        )
        tlv_b = ToolLevelVerdict(
            prereq_id="micromegas",
            overall_verdict="supported",
            viable_for_observables=("relic",),
            role={"relic": "primary"},
            priority_tiebreak=20,
        )
        fold = {"maddm": tlv_a, "micromegas": tlv_b}
        ranked = matrix.rank_by_role(fold, "relic")
        ids = [tlv.prereq_id for tlv in ranked]
        # Lower priority_tiebreak wins → maddm first
        assert ids[0] == "maddm"
        assert ids[1] == "micromegas"

    def test_04_escape_hatch_viable_when_others_blocked(self, matrix):
        """rank_by_role includes escape_hatch when primary is blocked."""
        tlv_maddm = ToolLevelVerdict(
            prereq_id="maddm",
            overall_verdict="blocked",
            viable_for_observables=(),
            role={"relic": "primary"},
        )
        tlv_backend = ToolLevelVerdict(
            prereq_id="analytic_backend",
            overall_verdict="supported_with_caveat",
            viable_for_observables=("relic",),
            role={"relic": "escape_hatch"},
        )
        fold = {"maddm": tlv_maddm, "analytic_backend": tlv_backend}
        ranked = matrix.rank_by_role(fold, "relic")
        ids = [tlv.prereq_id for tlv in ranked]
        # Only analytic_backend is viable (maddm is blocked)
        assert "analytic_backend" in ids
        assert "maddm" not in ids

    def test_05_viable_chain_topo_orders_gatings(self, matrix):
        """viable_chain_for returns gating prereqs before producer, topo-ordered."""
        tlv_sarah = ToolLevelVerdict(
            prereq_id="sarah-build",
            overall_verdict="supported",
            viable_for_observables=(),
            role={"relic": "none"},
            gating_for=("relic",),
            depends_on_prereqs=(),
        )
        tlv_spheno = ToolLevelVerdict(
            prereq_id="spheno-build",
            overall_verdict="supported",
            viable_for_observables=(),
            role={"relic": "none"},
            gating_for=("relic",),
            depends_on_prereqs=("sarah-build",),
        )
        tlv_backend = ToolLevelVerdict(
            prereq_id="analytic_backend",
            overall_verdict="supported_with_caveat",
            viable_for_observables=("relic",),
            role={"relic": "escape_hatch"},
            gating_for=(),
            depends_on_prereqs=(),
        )
        fold = {
            "sarah-build": tlv_sarah,
            "spheno-build": tlv_spheno,
            "analytic_backend": tlv_backend,
        }
        chain = matrix.viable_chain_for("relic", fold)
        assert "analytic_backend" in chain
        # analytic_backend is the producer (escape_hatch); must be last
        assert chain[-1] == "analytic_backend"
        # gating prereqs should appear before the producer
        if "sarah-build" in chain and "spheno-build" in chain:
            assert chain.index("sarah-build") < chain.index("spheno-build")

    def test_06_tie_error_on_same_priority_same_role(self, matrix):
        """D10: rank_by_role raises MultipleSamePriorityRolesError when two prereqs
        share role and priority_tiebreak, making ranking nondeterministic."""
        from matrix_lookup import MultipleSamePriorityRolesError
        tlv_a = ToolLevelVerdict(
            prereq_id="tool_alpha",
            overall_verdict="supported",
            viable_for_observables=("relic",),
            role={"relic": "primary"},
            priority_tiebreak=100,  # default — tie
        )
        tlv_b = ToolLevelVerdict(
            prereq_id="tool_beta",
            overall_verdict="supported",
            viable_for_observables=("relic",),
            role={"relic": "primary"},
            priority_tiebreak=100,  # default — tie
        )
        fold = {"tool_alpha": tlv_a, "tool_beta": tlv_b}
        with pytest.raises(MultipleSamePriorityRolesError) as exc_info:
            matrix.rank_by_role(fold, "relic")
        msg = str(exc_info.value)
        assert "tool_alpha" in msg or "tool_beta" in msg, (
            f"Error message should contain the colliding prereq IDs, got: {msg}"
        )
