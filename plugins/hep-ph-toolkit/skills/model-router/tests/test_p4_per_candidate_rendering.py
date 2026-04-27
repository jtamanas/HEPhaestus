"""
test_p4_per_candidate_rendering.py — S13t: per-candidate routing tests.

Per WS3 plan §S13 + synthesis Decision 1: when a model has multiple DM
candidates and the WS4 verdict is ROUTE_TO_ANALYTIC, each DM observable
gets a `per_candidate` array of PerCandidateRouting entries — one per
candidate — with the analytic_backend chain pinned per candidate.

Schema reference (manager D5 — see routing_report.schema.json):
    per_candidate.items.required = [candidate_name, active_chain,
                                    expected_observable_label]
    plus optional candidate_field_type, candidate_mediator_regime,
    candidate_uv_provenance.

Activated only when:
    - exception_verdict.verdict == "ROUTE_TO_ANALYTIC"
    - observable in {"relic", "dd", "id"}
"""
import pytest

compose_mod = pytest.importorskip(
    "model_router.stages.compose_rank",
    reason="stage_p4_compose_and_rank not yet implemented",
)
stage_p4_compose_and_rank = compose_mod.stage_p4_compose_and_rank


# ---------------------------------------------------------------------------
# Helpers (mirror test_p4_compose_rank.py)
# ---------------------------------------------------------------------------

def _make_axes(candidates=None):
    from model_router.types import AxisBundle, CandidateSpec
    return AxisBundle(
        A1="SM + extra SU(N)",
        A8="active",
        candidates=candidates if candidates is not None else [
            CandidateSpec(name="V", field_type="vector",
                          mediator_regime="tree-level-open",
                          uv_provenance="broken-generator-boson"),
            CandidateSpec(name="Psi", field_type="scalar",
                          mediator_regime="tree-level-blind-spot",
                          uv_provenance="elementary"),
        ],
        model_props={"analytic_module_status": "registered_active"},
    )


def _make_ctx(model_id="dark-su3", observables=("relic",)):
    from model_router.types import LoadedContext, RouterOptions
    return LoadedContext(
        model_id=model_id,
        observables=list(observables),
        options=RouterOptions(),
        model_meta={},
        model_spec={"name": model_id},
        prereqs={},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions={
            "exceptions": {
                "dsu3-002": {
                    "banner": "Dark SU(3) analytic backend disclosure.",
                }
            }
        },
        config={},
    )


def _make_matrix_verdicts(folds_by_obs):
    from model_router.types import MatrixVerdicts
    return MatrixVerdicts(by_observable=dict(folds_by_obs))


def _make_fold(prereq_id, role="primary", overall="blocked",
               blockers=None, priority_tiebreak=10):
    from model_router.types import PrereqFold
    return PrereqFold(
        prereq_id=prereq_id,
        overall_verdict=overall,
        blockers=blockers or ["MG5_DARK_COLOR_TENSOR_WALL"],
        blocker_classes=["fundamental-group-theory-gap"],
        caveats=[],
        role_for_observable=role,
        priority_tiebreak=priority_tiebreak,
    )


def _make_route_verdict(exception_id="dsu3-002"):
    import dataclasses
    from model_router.types import ExceptionVerdict
    field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    kwargs = {"verdict": "ROUTE_TO_ANALYTIC",
              "exception_id": exception_id,
              "disclosure_required": True}
    if "rationale" in field_names:
        kwargs["rationale"] = "dark color group requires analytic backend"
    if "reason_human" in field_names:
        kwargs["reason_human"] = "dark color group requires analytic backend"
    return ExceptionVerdict(**kwargs)


def _make_clear_verdict():
    import dataclasses
    from model_router.types import ExceptionVerdict
    field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    kwargs = {"verdict": "CLEAR", "exception_id": None,
              "disclosure_required": False}
    if "rationale" in field_names:
        kwargs["rationale"] = ""
    if "reason_human" in field_names:
        kwargs["reason_human"] = ""
    return ExceptionVerdict(**kwargs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPerCandidateRouting:
    """S13: per-candidate rows emit only for ROUTE_TO_ANALYTIC + DM observable."""

    def test_per_candidate_rows_emitted_for_dsu3_route_to_analytic_relic(self):
        """dark-su3 + ROUTE_TO_ANALYTIC + relic → 2 per_candidate entries (V, Psi)."""
        ctx = _make_ctx(model_id="dark-su3", observables=("relic",))
        axes = _make_axes()
        ev = _make_route_verdict()
        folds = [_make_fold("maddm")]
        mv = _make_matrix_verdicts({"relic": folds})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        assert len(relic.per_candidate) == 2
        names = [pc.candidate_name for pc in relic.per_candidate]
        assert names == ["V", "Psi"]

    def test_per_candidate_active_chain_pinned_to_analytic_backend(self):
        """Each per_candidate entry pins active_chain.prereq_id == analytic_backend."""
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_route_verdict()
        mv = _make_matrix_verdicts({"relic": [_make_fold("maddm")]})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        for pc in relic.per_candidate:
            assert pc.active_chain is not None
            assert pc.active_chain.prereq_id == "analytic_backend"

    def test_per_candidate_expected_observable_labels_per_candidate(self):
        """expected_observable_label uses Omega_<name>_h2 form for relic."""
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_route_verdict()
        mv = _make_matrix_verdicts({"relic": [_make_fold("maddm")]})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        labels = {pc.candidate_name: pc.expected_observable_label
                  for pc in relic.per_candidate}
        assert labels["V"] == "Omega_V_h2"
        assert labels["Psi"] == "Omega_Psi_h2"

    def test_per_candidate_carries_candidate_metadata(self):
        """candidate_field_type / mediator_regime / uv_provenance round-trip."""
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_route_verdict()
        mv = _make_matrix_verdicts({"relic": [_make_fold("maddm")]})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        v_pc = next(pc for pc in relic.per_candidate if pc.candidate_name == "V")
        assert v_pc.candidate_field_type == "vector"
        assert v_pc.candidate_mediator_regime == "tree-level-open"
        assert v_pc.candidate_uv_provenance == "broken-generator-boson"

    def test_per_candidate_empty_for_clear_verdict(self):
        """CLEAR verdict produces zero per_candidate entries even with DM observable."""
        ctx = _make_ctx(observables=("relic",))
        axes = _make_axes()
        ev = _make_clear_verdict()
        from model_router.types import PrereqFold
        good_fold = PrereqFold(
            prereq_id="maddm",
            overall_verdict="supported",
            blockers=[], blocker_classes=[], caveats=[],
            role_for_observable="primary",
            priority_tiebreak=10,
        )
        mv = _make_matrix_verdicts({"relic": [good_fold]})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        assert composed.per_observable["relic"].per_candidate == []
