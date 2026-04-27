"""
test_p5_render.py — S22: full P5 render body tests.

Per WS3 plan §S22: tests cover each verdict's Markdown body for the
real (S16/S17/S18) impl. Replaces the placeholder-string assertions
with real-content assertions.
"""
import pytest

render_mod = pytest.importorskip(
    "model_router.stages.render",
    reason="render module not yet implemented",
)
stage_p5_render = render_mod.stage_p5_render


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_exception_verdict(verdict: str, exception_id: str = None,
                             disclosure_required: bool = False):
    import dataclasses
    from model_router.types import ExceptionVerdict
    field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    kwargs = {"verdict": verdict, "exception_id": exception_id,
              "disclosure_required": disclosure_required}
    if "rationale" in field_names:
        kwargs["rationale"] = ""
    if "detector_unavailable" in field_names:
        kwargs["detector_unavailable"] = False
    if "reason_human" in field_names:
        kwargs["reason_human"] = ""
    return ExceptionVerdict(**kwargs)


def _make_active_chain(prereq_id="maddm", role="primary", status="ROUTED",
                        blockers=None):
    from model_router.types import ActiveChain
    return ActiveChain(
        prereq_id=prereq_id,
        role=role,
        status=status,
        blockers=blockers or [],
        blocker_classes=[],
        caveats=[],
    )


def _make_obs_routing(observable="relic", status="ROUTED",
                       active_chain=None, ranked_alternatives=None,
                       per_candidate=None):
    from model_router.types import ObservableRouting
    return ObservableRouting(
        observable=observable,
        status=status,
        active_chain=active_chain,
        ranked_alternatives=ranked_alternatives or [],
        per_candidate=per_candidate or [],
    )


def _make_axes(A1="SM only", A8="active"):
    from model_router.types import AxisBundle
    return AxisBundle(A1=A1, A8=A8)


def _make_composed(verdict, model_id="test-model", per_observable=None,
                    axes=None, exception_id=None,
                    disclosure_required=False):
    from model_router.types import ComposedRouting
    if per_observable is None:
        per_observable = {"relic": _make_obs_routing(
            active_chain=_make_active_chain(),
        )}
    return ComposedRouting(
        model_id=model_id,
        observables=list(per_observable.keys()),
        exception_verdict=_make_exception_verdict(
            verdict, exception_id=exception_id,
            disclosure_required=disclosure_required,
        ),
        per_observable=per_observable,
        axes_snapshot=axes,
    )


def _make_ctx(model_id="test-model", analytic_exceptions=None):
    from model_router.types import LoadedContext, RouterOptions
    return LoadedContext(
        model_id=model_id,
        observables=["relic"],
        options=RouterOptions(),
        model_meta={"analytic_module_status": "unregistered"},
        model_spec={"name": model_id},
        prereqs={},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions=analytic_exceptions or {},
        config={},
    )


def _make_options(strict=False):
    from model_router.types import RouterOptions
    return RouterOptions(strict=strict)


# ---------------------------------------------------------------------------
# CLEAR render tests
# ---------------------------------------------------------------------------

class TestRenderClear:
    """S16: _render_clear emits real Markdown body."""

    def test_clear_no_placeholder_string(self):
        """CLEAR body never contains the old `<CLEAR placeholder ...>` literal."""
        composed = _make_composed("CLEAR", axes=_make_axes())
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "placeholder" not in md.lower(), \
            f"CLEAR body still contains placeholder text:\n{md[:500]}"
        assert "S16 not yet implemented" not in md

    def test_clear_includes_header_and_status(self):
        """CLEAR body has the model_id header and a Status: line."""
        composed = _make_composed("CLEAR")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "# Routing Report" in md
        assert "test-model" in md
        assert "**Status:**" in md
        assert "CLEAR" in md

    def test_clear_includes_per_observable_section(self):
        """CLEAR body emits the per-observable section for each observable."""
        composed = _make_composed("CLEAR")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "Observable: `relic`" in md or "observable: `relic`" in md.lower()
        # Ranked-chain table header
        assert "| Rank |" in md
        assert "maddm" in md

    def test_clear_includes_axis_snapshot_when_present(self):
        """CLEAR body renders the axis snapshot table when axes_snapshot is set."""
        composed = _make_composed("CLEAR", axes=_make_axes(A1="SM only", A8="active"))
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "Axis snapshot" in md
        assert "A1" in md
        assert "SM only" in md


# ---------------------------------------------------------------------------
# HARD_HALT render tests
# ---------------------------------------------------------------------------

class TestRenderHardHalt:
    """S16: _render_hard_halt emits real Markdown body with EFT_REWRITE_REQUIRED rows."""

    def test_hard_halt_no_placeholder_string(self):
        composed = _make_composed("HARD_HALT")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "placeholder" not in md.lower()
        assert "S16 not yet implemented" not in md

    def test_hard_halt_includes_eft_rewrite_required(self):
        """HARD_HALT body emits EFT_REWRITE_REQUIRED per-observable."""
        composed = _make_composed("HARD_HALT")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        assert "EFT_REWRITE_REQUIRED" in report.markdown_report

    def test_hard_halt_no_required_next_steps_section(self):
        """HARD_HALT does NOT include the `Required next steps` section."""
        composed = _make_composed("HARD_HALT")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        # The signoff prompt is HALT_FOR_SIGNOFF only; HARD_HALT must not
        # contain the required-next-steps signoff appendix.
        md = report.markdown_report
        assert "Required next steps (analytic exception sign-off)" not in md


# ---------------------------------------------------------------------------
# HALT_FOR_SIGNOFF render tests
# ---------------------------------------------------------------------------

class TestRenderHaltForSignoff:
    """S17: _render_halt_for_signoff emits halt notice + signoff appendix."""

    def test_halt_for_signoff_no_placeholder_string(self):
        composed = _make_composed("HALT_FOR_SIGNOFF")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "placeholder" not in md.lower()
        assert "S17 not yet implemented" not in md

    def test_halt_for_signoff_includes_signoff_prompt_in_appendix(self):
        """HALT_FOR_SIGNOFF body has the signoff prompt placement injected."""
        composed = _make_composed("HALT_FOR_SIGNOFF")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "Required next steps" in md or "sign-off" in md.lower()


# ---------------------------------------------------------------------------
# ROUTE_TO_ANALYTIC render tests
# ---------------------------------------------------------------------------

class TestRenderRouteToAnalytic:
    """S18: _render_route_to_analytic emits banner + per_candidate."""

    def test_route_no_placeholder_string(self):
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx(analytic_exceptions={
            "exceptions": {"dsu3-002": {"banner": "DSU3 analytic banner."}},
        })
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "placeholder" not in md.lower()
        assert "S18 not yet implemented" not in md

    def test_route_includes_disclosure_banner(self):
        """ROUTE_TO_ANALYTIC body contains the banner text from the registry."""
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx(analytic_exceptions={
            "exceptions": {"dsu3-002": {"banner": "DSU3 analytic banner verbatim."}},
        })
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "DSU3 analytic banner verbatim" in md

    def test_route_includes_blockers_on_alternative_chains(self):
        """ROUTE_TO_ANALYTIC body has the model-level alternative-blockers section."""
        from model_router.types import ActiveChain, ObservableRouting
        alt = ActiveChain(
            prereq_id="maddm", role="primary", status="BLOCKED",
            blockers=["MG5_DARK_COLOR_TENSOR_WALL"],
        )
        composed = _make_composed(
            "ROUTE_TO_ANALYTIC",
            exception_id="dsu3-002",
            per_observable={
                "relic": ObservableRouting(
                    observable="relic", status="ROUTED",
                    active_chain=ActiveChain(prereq_id="analytic_backend",
                                              role="escape_hatch",
                                              status="ROUTED"),
                    ranked_alternatives=[alt],
                ),
            },
        )
        ctx = _make_ctx(analytic_exceptions={
            "exceptions": {"dsu3-002": {"banner": "DSU3 banner."}},
        })
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "Blockers on alternative chains" in md
        assert "MG5_DARK_COLOR_TENSOR_WALL" in md

    def test_route_disclosure_banner_missing_raises(self):
        """ROUTE_TO_ANALYTIC + disclosure_required=True + no banner → DisclosureBannerMissing."""
        from model_router.types import DisclosureBannerMissing
        composed = _make_composed(
            "ROUTE_TO_ANALYTIC",
            exception_id="unknown-exception-id",
            disclosure_required=True,
        )
        # ctx.analytic_exceptions has NO entry for unknown-exception-id, so
        # _build_placements falls back; but the entry has no banner field
        # AND disclosure is required → fail-closed.
        ctx = _make_ctx(analytic_exceptions={"exceptions": {}})
        # Stub _build_placements to return [] to simulate truly missing placement.
        # The current impl always creates a synthetic placement when no banner;
        # however the fail-closed only fires when the analytic placement is
        # ABSENT. We achieve that by patching _build_placements briefly.
        import model_router.stages.render as rmod
        orig = rmod._build_placements
        try:
            rmod._build_placements = lambda c, x: []
            with pytest.raises(DisclosureBannerMissing):
                stage_p5_render(composed, ctx, _make_options())
        finally:
            rmod._build_placements = orig


# ---------------------------------------------------------------------------
# Per-candidate rendering inside ROUTE_TO_ANALYTIC
# ---------------------------------------------------------------------------

class TestRenderPerCandidate:
    """S18 + Decision 1: per_candidate sub-blocks emitted under DM observables."""

    def test_per_candidate_blocks_emitted(self):
        from model_router.types import (
            ActiveChain, ObservableRouting, PerCandidateRouting,
        )
        per_cand = [
            PerCandidateRouting(
                candidate_name="V",
                candidate_field_type="vector",
                candidate_mediator_regime="tree-level-open",
                candidate_uv_provenance="broken-generator-boson",
                active_chain=ActiveChain(
                    prereq_id="analytic_backend", role="escape_hatch",
                    status="ROUTED",
                ),
                expected_observable_label="Omega_V_h2",
            ),
            PerCandidateRouting(
                candidate_name="Psi",
                candidate_field_type="scalar",
                candidate_mediator_regime="tree-level-blind-spot",
                candidate_uv_provenance="elementary",
                active_chain=ActiveChain(
                    prereq_id="analytic_backend", role="escape_hatch",
                    status="ROUTED",
                ),
                expected_observable_label="Omega_Psi_h2",
            ),
        ]
        composed = _make_composed(
            "ROUTE_TO_ANALYTIC",
            exception_id="dsu3-002",
            per_observable={
                "relic": ObservableRouting(
                    observable="relic", status="ROUTED",
                    active_chain=ActiveChain(prereq_id="analytic_backend",
                                              role="escape_hatch",
                                              status="ROUTED"),
                    per_candidate=per_cand,
                ),
            },
        )
        ctx = _make_ctx(analytic_exceptions={
            "exceptions": {"dsu3-002": {"banner": "DSU3 banner."}},
        })
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        assert "Candidate `V`" in md
        assert "Candidate `Psi`" in md
        assert "Omega_V_h2" in md
        assert "Omega_Psi_h2" in md
        assert "tree-level-open" in md
        assert "tree-level-blind-spot" in md
