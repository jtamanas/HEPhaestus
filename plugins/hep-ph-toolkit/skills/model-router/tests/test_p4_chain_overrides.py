"""
test_p4_chain_overrides.py — S14: chain_overrides + matrix_acknowledgement +
strict-mode exit-4 path.

Per WS3 plan §S14 + synthesis Decision 4: when constraints.yaml supplies a
`chain_overrides.<observable>` block that drops matrix-blocked prereqs,
the override MUST carry a `matrix_acknowledgement` block listing the
accepted blockers. Strict mode raises `MatrixAcknowledgementMissing`
when the acknowledgement is absent or incomplete; non-strict mode
records the issue on the active chain (matrix_acknowledgement_missing=True)
and continues.
"""
import pytest

compose_mod = pytest.importorskip(
    "model_router.stages.compose_rank",
    reason="stage_p4_compose_and_rank not yet implemented",
)
stage_p4_compose_and_rank = compose_mod.stage_p4_compose_and_rank


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_axes():
    from model_router.types import AxisBundle, CandidateSpec
    return AxisBundle(
        A1="SM + extra SU(N)",
        A8="active",
        candidates=[
            CandidateSpec(name="V", field_type="vector"),
        ],
        model_props={"analytic_module_status": "registered_active"},
    )


def _make_ctx(model_id="dark-su3", observables=("relic",), strict=False,
              chain_overrides=None):
    """Build LoadedContext with optional chain_overrides on the model_meta."""
    from model_router.types import LoadedContext, RouterOptions
    model_meta: dict = {}
    if chain_overrides is not None:
        model_meta["chain_overrides"] = chain_overrides
    return LoadedContext(
        model_id=model_id,
        observables=list(observables),
        options=RouterOptions(strict=strict),
        model_meta=model_meta,
        model_spec={"name": model_id},
        prereqs={},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions={},
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

class TestChainOverrideHonored:
    """When chain_overrides is present, the override prereq becomes the active chain."""

    def test_override_pins_analytic_backend(self):
        """chain_overrides.relic.chain == [analytic_backend] → active_chain.prereq_id pinned."""
        ev = _make_clear_verdict()
        ctx = _make_ctx(
            chain_overrides={
                "relic": {
                    "chain": ["analytic_backend"],
                    "reason": "MG5 dt1 dark-color tensor wall",
                    "backend_hint": "analytic",
                    "matrix_acknowledgement": {
                        "accepted_blockers": ["MG5_DARK_COLOR_TENSOR_WALL"],
                        "accepted_workaround": "ANALYTIC_BACKEND_PATH",
                        "authority": "WS4 dsu3-002 disclosure",
                        "last_audited": "2026-04-26",
                    },
                },
            },
        )
        axes = _make_axes()
        folds = [_make_fold("maddm")]
        mv = _make_matrix_verdicts({"relic": folds})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        assert relic.active_chain is not None
        assert relic.active_chain.prereq_id == "analytic_backend"
        assert relic.active_chain.matrix_acknowledgement_missing is False


class TestMatrixAcknowledgementMissing:
    """Override that drops matrix-blocked prereqs without acknowledgement."""

    def test_missing_acknowledgement_marks_chain_in_non_strict(self):
        """Override without matrix_acknowledgement → active chain flagged, no raise."""
        ev = _make_clear_verdict()
        ctx = _make_ctx(
            strict=False,
            chain_overrides={
                "relic": {
                    "chain": ["analytic_backend"],
                    "reason": "MG5 wall",
                    # NO matrix_acknowledgement block
                },
            },
        )
        axes = _make_axes()
        folds = [_make_fold("maddm", blockers=["MG5_DARK_COLOR_TENSOR_WALL"])]
        mv = _make_matrix_verdicts({"relic": folds})

        composed = stage_p4_compose_and_rank(axes, ctx, ev, mv)
        relic = composed.per_observable["relic"]
        assert relic.active_chain is not None
        assert relic.active_chain.matrix_acknowledgement_missing is True

    def test_strict_mode_raises_matrix_acknowledgement_missing(self):
        """Strict mode + missing acknowledgement → MatrixAcknowledgementMissing raised."""
        from model_router.types import MatrixAcknowledgementMissing
        ev = _make_clear_verdict()
        ctx = _make_ctx(
            strict=True,
            chain_overrides={
                "relic": {
                    "chain": ["analytic_backend"],
                    "reason": "MG5 wall",
                },
            },
        )
        axes = _make_axes()
        folds = [_make_fold("maddm", blockers=["MG5_DARK_COLOR_TENSOR_WALL"])]
        mv = _make_matrix_verdicts({"relic": folds})

        with pytest.raises(MatrixAcknowledgementMissing):
            stage_p4_compose_and_rank(axes, ctx, ev, mv)

    def test_incomplete_acknowledgement_misses_blocker_in_strict(self):
        """Strict mode: ack present but missing the actual blocker → raises."""
        from model_router.types import MatrixAcknowledgementMissing
        ev = _make_clear_verdict()
        ctx = _make_ctx(
            strict=True,
            chain_overrides={
                "relic": {
                    "chain": ["analytic_backend"],
                    "reason": "MG5 wall",
                    "matrix_acknowledgement": {
                        # Acknowledges UFO_MISSING but the actual matrix blocker
                        # is MG5_DARK_COLOR_TENSOR_WALL → contradiction
                        "accepted_blockers": ["UFO_MISSING"],
                        "accepted_workaround": "ANALYTIC_BACKEND_PATH",
                        "authority": "stale ack",
                        "last_audited": "2026-04-26",
                    },
                },
            },
        )
        axes = _make_axes()
        folds = [_make_fold("maddm", blockers=["MG5_DARK_COLOR_TENSOR_WALL"])]
        mv = _make_matrix_verdicts({"relic": folds})

        with pytest.raises(MatrixAcknowledgementMissing):
            stage_p4_compose_and_rank(axes, ctx, ev, mv)


class TestChainOverrideExitCode:
    """Strict-mode exit code 4 from missing acknowledgement contradiction."""

    def test_exit_code_4_when_strict_with_missing_ack(self):
        """Compute exit code from a ComposedRouting whose active chain is flagged."""
        from model_router.stages.render import _compute_exit_code
        from model_router.types import (
            ActiveChain, ComposedRouting, ObservableRouting, RouterOptions,
        )
        flagged_chain = ActiveChain(
            prereq_id="analytic_backend",
            role="escape_hatch",
            status="ROUTED",
            matrix_acknowledgement_missing=True,
        )
        composed = ComposedRouting(
            model_id="dark-su3",
            observables=["relic"],
            exception_verdict=_make_clear_verdict(),
            per_observable={
                "relic": ObservableRouting(
                    observable="relic",
                    status="ROUTED",
                    active_chain=flagged_chain,
                ),
            },
        )
        opts = RouterOptions(strict=True)
        assert _compute_exit_code(composed, opts) == 4
