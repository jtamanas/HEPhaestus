"""
test_p4_compose_rank.py — Phase 5: stage_p4_compose_and_rank tests (S11t).

Tests cover the per-constraint chain ranking using matrix_lookup verdicts +
the WS3 ranking layer (role > priority > user-memory > prereq_id).
"""
import pytest

compose_mod = pytest.importorskip(
    "model_router.stages.compose_rank",
    reason="stage_p4_compose_and_rank not yet implemented (awaiting S11)",
)
stage_p4_compose_and_rank = compose_mod.stage_p4_compose_and_rank


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_axes(a1="SM only", candidates=None, model_props=None):
    from model_router.types import AxisBundle, CandidateSpec
    return AxisBundle(
        A1=a1,
        A8="active",
        candidates=candidates if candidates is not None else [
            CandidateSpec(name="chi_1", field_type="Dirac fermion")
        ],
        model_props=model_props or {"analytic_module_status": "missing"},
    )


def _make_ctx(model_id="singlet-doublet", observables=("relic",), prereqs=None,
              user_preferences=None):
    from model_router.types import LoadedContext, RouterOptions
    return LoadedContext(
        model_id=model_id,
        observables=list(observables),
        options=RouterOptions(user_preferences=user_preferences),
        model_meta={},
        model_spec={"name": model_id},
        prereqs=prereqs or {},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions={},
        config={},
    )


def _make_matrix_verdicts(folds_by_obs):
    from model_router.types import MatrixVerdicts
    return MatrixVerdicts(by_observable=dict(folds_by_obs))


def _make_fold(prereq_id, role, overall="supported", priority_tiebreak=100,
               blockers=None):
    from model_router.types import PrereqFold
    return PrereqFold(
        prereq_id=prereq_id,
        overall_verdict=overall,
        blockers=blockers or [],
        blocker_classes=[],
        caveats=[],
        role_for_observable=role,
        priority_tiebreak=priority_tiebreak,
    )


def _make_exception_verdict(verdict="CLEAR"):
    import dataclasses
    from model_router.types import ExceptionVerdict
    field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    kwargs = {"verdict": verdict, "exception_id": None, "disclosure_required": False}
    if "rationale" in field_names:
        kwargs["rationale"] = ""
    if "reason_human" in field_names:
        kwargs["reason_human"] = ""
    return ExceptionVerdict(**kwargs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComposeRankRoleOrder:
    """Per plan §S11+S12: role primary < validator < specialty < escape_hatch < none."""

    def test_primary_outranks_validator_in_active_chain(self):
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_exception_verdict("CLEAR")
        folds = [
            _make_fold("micromegas", "validator", priority_tiebreak=20),
            _make_fold("maddm", "primary", priority_tiebreak=10),
        ]
        mv = _make_matrix_verdicts({"relic": folds})
        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        assert relic.active_chain is not None
        assert relic.active_chain.prereq_id == "maddm"
        assert relic.active_chain.role == "primary"
        # The validator should be in the alternatives
        alt_ids = [a.prereq_id for a in relic.ranked_alternatives]
        assert "micromegas" in alt_ids


class TestComposeRankUserMemory:
    """Per project_dm_tool_roles + plan §S12: user_preferences is tertiary tiebreak."""

    def test_user_memory_does_not_override_role(self):
        """Even if user prefers micromegas (1) over maddm (2), primary still wins."""
        ctx = _make_ctx(observables=("relic",),
                        user_preferences={"micromegas": 1, "maddm": 2})
        axes = _make_axes()
        ev = _make_exception_verdict("CLEAR")
        folds = [
            _make_fold("micromegas", "validator", priority_tiebreak=20),
            _make_fold("maddm", "primary", priority_tiebreak=10),
        ]
        mv = _make_matrix_verdicts({"relic": folds})
        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        # Role primary always beats role validator regardless of user_memory
        assert composed.per_observable["relic"].active_chain.prereq_id == "maddm"

    def test_user_memory_breaks_tie_within_same_role(self):
        """Two validators with same priority_tiebreak: user memory chooses winner."""
        ctx = _make_ctx(observables=("relic",),
                        user_preferences={"micromegas": 2, "drake": 3})
        axes = _make_axes()
        ev = _make_exception_verdict("CLEAR")
        # Both validators with same priority_tiebreak — user_memory should
        # tiebreak (lower wins).
        folds = [
            _make_fold("drake", "validator", priority_tiebreak=20),
            _make_fold("micromegas", "validator", priority_tiebreak=20),
        ]
        mv = _make_matrix_verdicts({"relic": folds})
        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        # micromegas (user_memory=2) ranks ahead of drake (user_memory=3)
        active = composed.per_observable["relic"].active_chain
        assert active.prereq_id == "micromegas"


class TestComposeRankBlockers:
    """Blocked folds should not be selected as active_chain."""

    def test_blocked_prereq_is_not_active_chain(self):
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_exception_verdict("CLEAR")
        folds = [
            _make_fold("maddm", "primary", overall="blocked",
                       blockers=["MG5_DARK_COLOR_TENSOR_WALL"]),
            _make_fold("micromegas", "validator", overall="supported",
                       priority_tiebreak=20),
        ]
        mv = _make_matrix_verdicts({"relic": folds})
        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        active = composed.per_observable["relic"].active_chain
        # When primary is blocked, validator should be selected
        assert active is not None
        assert active.prereq_id == "micromegas"
