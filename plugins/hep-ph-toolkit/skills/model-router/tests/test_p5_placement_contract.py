"""
test_p5_placement_contract.py — S22: placement-contract tests (Decision 2).

Per WS3 plan §S22 + R10 mitigation: assert against renderer-emitted
anchor comments (`<!-- WS3:section=<position> -->`) injected by the S15c
`_inject_placements` helper. Substring fallback retained for double-coverage.

The 5 placement positions per the schema closed enum:
    top | before_results_table | before_per_observable | appendix | inline
"""
import pytest

render_mod = pytest.importorskip(
    "model_router.stages.render",
    reason="render module not yet implemented",
)
stage_p5_render = render_mod.stage_p5_render
_inject_placements = render_mod._inject_placements


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


def _make_composed(verdict, exception_id=None):
    from model_router.types import (
        ActiveChain, ComposedRouting, ObservableRouting,
    )
    return ComposedRouting(
        model_id="placement-test",
        observables=["relic"],
        exception_verdict=_make_exception_verdict(verdict, exception_id),
        per_observable={
            "relic": ObservableRouting(
                observable="relic", status="ROUTED",
                active_chain=ActiveChain(
                    prereq_id="analytic_backend" if verdict == "ROUTE_TO_ANALYTIC" else "maddm",
                    role="escape_hatch" if verdict == "ROUTE_TO_ANALYTIC" else "primary",
                    status="ROUTED",
                ),
            ),
        },
    )


def _make_ctx(analytic_exceptions=None):
    from model_router.types import LoadedContext, RouterOptions
    return LoadedContext(
        model_id="placement-test",
        observables=["relic"],
        options=RouterOptions(),
        model_meta={"analytic_module_status": "unregistered"},
        model_spec={"name": "placement-test"},
        prereqs={},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions=analytic_exceptions or {
            "exceptions": {
                "dsu3-002": {"banner": "Banner content for placement contract."},
            }
        },
        config={},
    )


def _make_options():
    from model_router.types import RouterOptions
    return RouterOptions()


# ---------------------------------------------------------------------------
# Anchor presence per verdict
# ---------------------------------------------------------------------------

class TestAnchorPresence:
    """Each render path emits the WS3 section anchor comments."""

    @pytest.mark.parametrize("verdict,expected_anchors", [
        ("CLEAR", ["top", "before_results_table", "before_per_observable",
                   "appendix", "inline"]),
        ("HARD_HALT", ["top", "before_results_table", "before_per_observable",
                       "appendix", "inline"]),
        ("HALT_FOR_SIGNOFF", ["top", "before_results_table",
                                "before_per_observable", "appendix", "inline"]),
        ("ROUTE_TO_ANALYTIC", ["top", "before_results_table",
                                "before_per_observable", "appendix", "inline"]),
    ])
    def test_render_emits_required_anchors(self, verdict, expected_anchors):
        """The render body emits a WS3:section anchor comment for each position."""
        composed = _make_composed(verdict, exception_id="dsu3-002")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        for pos in expected_anchors:
            assert f"<!-- WS3:section={pos} -->" in md, \
                f"Anchor for {pos} missing in {verdict} body"


# ---------------------------------------------------------------------------
# Disclosure banner anchoring (Decision 2; R10 mitigation)
# ---------------------------------------------------------------------------

class TestDisclosureBannerAnchor:
    """ROUTE_TO_ANALYTIC banner appears between before_per_observable and per-observable anchors."""

    def test_banner_appears_after_before_per_observable_anchor(self):
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        anchor = "<!-- WS3:section=before_per_observable -->"
        assert anchor in md
        idx = md.index(anchor)
        after = md[idx:]
        assert "Banner content for placement contract." in after, \
            f"Banner content not present after anchor; tail: {after[:300]!r}"

    def test_banner_appears_before_per_observable_section_anchor(self):
        """Per-observable section anchor follows the before_per_observable anchor."""
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        anchor_before = "<!-- WS3:section=before_per_observable -->"
        anchor_per = "<!-- WS3:section=per-observable -->"
        # Banner content must be between these anchors
        idx_before = md.index(anchor_before)
        idx_per = md.index(anchor_per)
        assert idx_before < idx_per
        between = md[idx_before:idx_per]
        assert "Banner content for placement contract." in between


# ---------------------------------------------------------------------------
# HALT_FOR_SIGNOFF placement contract (signoff prompt at appendix)
# ---------------------------------------------------------------------------

class TestSignoffPromptPlacement:
    """HALT_FOR_SIGNOFF: signoff prompt placed in the appendix section."""

    def test_signoff_prompt_appears_after_appendix_anchor(self):
        composed = _make_composed("HALT_FOR_SIGNOFF")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        anchor = "<!-- WS3:section=appendix -->"
        assert anchor in md
        idx = md.index(anchor)
        after = md[idx:]
        assert "Required next steps" in after or "sign-off" in after.lower()


# ---------------------------------------------------------------------------
# _inject_placements unit tests
# ---------------------------------------------------------------------------

class TestInjectPlacementsUnit:
    """_inject_placements honors anchor presence and falls back to append."""

    def test_inject_when_anchor_present(self):
        from model_router.types import Placement
        md = "Header\n<!-- WS3:section=top -->\nFooter"
        placements = [Placement(position="top", content="INJECTED", kind="halt_notice")]
        out = _inject_placements(md, placements, "top")
        assert "INJECTED" in out
        idx_anchor = out.index("<!-- WS3:section=top -->")
        idx_inj = out.index("INJECTED")
        assert idx_inj > idx_anchor

    def test_inject_appends_when_anchor_missing(self):
        from model_router.types import Placement
        md = "Header without anchor"
        placements = [Placement(position="top", content="INJECTED", kind="halt_notice")]
        out = _inject_placements(md, placements, "top")
        assert "INJECTED" in out
        # Should be appended at end
        assert out.rstrip().endswith("INJECTED")
