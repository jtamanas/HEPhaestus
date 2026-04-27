"""
test_p5_render_skeleton.py — S15d: renderer skeleton contract test.

Tests dispatch, schema validation, exit-code mapping, placement vocabulary,
and placement counts per verdict.

Uses hand-built ComposedRouting + LoadedContext fixtures (no WS2 required).
"""
import pytest

render_mod = pytest.importorskip(
    "model_router.stages.render",
    reason="render module not yet implemented (awaiting S15a)",
)

stage_p5_render = render_mod.stage_p5_render
_build_json_report = render_mod._build_json_report
_compute_exit_code = render_mod._compute_exit_code
_build_placements = render_mod._build_placements
_inject_placements = render_mod._inject_placements


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_exception_verdict(verdict: str, exception_id: str = None):
    """Build a minimal ExceptionVerdict stub for testing.

    Compatible with both the WS4 Verdict class (uses reason_human) and the
    local stub fallback (uses rationale). Only passes fields that exist on the class.
    """
    import dataclasses
    from model_router.types import ExceptionVerdict
    try:
        field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    except TypeError:
        field_names = set()

    kwargs = {"verdict": verdict, "exception_id": exception_id, "disclosure_required": False}
    if "rationale" in field_names:
        kwargs["rationale"] = None
    if "detector_unavailable" in field_names:
        kwargs["detector_unavailable"] = False
    if "reason_human" in field_names:
        kwargs["reason_human"] = ""
    return ExceptionVerdict(**kwargs)


def _make_composed(verdict: str, exception_id: str = None):
    """Build a minimal ComposedRouting with the given verdict."""
    from model_router.types import ComposedRouting
    return ComposedRouting(
        model_id="test-model",
        observables=["relic"],
        exception_verdict=_make_exception_verdict(verdict, exception_id),
        per_observable={},
        diagnostics={},
    )


def _make_ctx():
    """Build a minimal LoadedContext for render tests."""
    from model_router.types import LoadedContext, RouterOptions
    return LoadedContext(
        model_id="test-model",
        observables=["relic"],
        options=RouterOptions(),
        model_meta={"analytic_module_status": "unregistered"},
        model_spec={"name": "test-model"},
        prereqs={},
        constraints_raw={},
        blocker_catalog={},
        analytic_exceptions={},
        config={},
    )


def _make_options(strict: bool = False):
    from model_router.types import RouterOptions
    return RouterOptions(strict=strict)


# ---------------------------------------------------------------------------
# S15d test 1: dispatch on verdict
# ---------------------------------------------------------------------------

class TestRenderDispatch:
    """stage_p5_render dispatches to distinct code paths per verdict."""

    def test_clear_verdict_produces_routing_report(self):
        """CLEAR verdict produces a RoutingReport with exit_code 0."""
        from model_router.types import RoutingReport
        composed = _make_composed("CLEAR")
        ctx = _make_ctx()
        opts = _make_options()
        report = stage_p5_render(composed, ctx, opts)
        assert isinstance(report, RoutingReport)
        assert report.exit_code == 0

    def test_route_to_analytic_verdict_produces_routing_report(self):
        """ROUTE_TO_ANALYTIC verdict produces a RoutingReport."""
        from model_router.types import RoutingReport
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx()
        opts = _make_options()
        report = stage_p5_render(composed, ctx, opts)
        assert isinstance(report, RoutingReport)
        assert report.exit_code == 0

    def test_halt_for_signoff_verdict_exit_code(self):
        """HALT_FOR_SIGNOFF with strict=True → exit_code 5."""
        composed = _make_composed("HALT_FOR_SIGNOFF")
        ctx = _make_ctx()
        opts = _make_options(strict=True)
        report = stage_p5_render(composed, ctx, opts)
        assert report.exit_code == 5

    def test_hard_halt_verdict_exit_code(self):
        """HARD_HALT with strict=True → exit_code 6."""
        composed = _make_composed("HARD_HALT")
        ctx = _make_ctx()
        opts = _make_options(strict=True)
        report = stage_p5_render(composed, ctx, opts)
        assert report.exit_code == 6


# ---------------------------------------------------------------------------
# S15d test 2: schema validation raises on malformed JSON
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    """_validate_json_against_schema raises SchemaValidationError on bad input."""

    def test_schema_validation_raises_on_missing_required_field(self):
        """Malformed JSON (missing required field) raises SchemaValidationError."""
        from model_router.types import SchemaValidationError
        from model_router.stages.render import _validate_json_against_schema
        try:
            import jsonschema  # type: ignore  # noqa
        except ImportError:
            pytest.skip("jsonschema not installed — schema validation skipped")

        # Missing required 'verdict' field
        bad_report = {
            "schema_version": 1,
            "model_id": "test",
            "observables": [],
            # "verdict" is missing — required by schema
            "model_props": {"analytic_module_status": "unregistered"},
            "per_observable": {},
            "placements": [],
            "diagnostics": {},
        }
        with pytest.raises(SchemaValidationError):
            _validate_json_against_schema(bad_report)

    def test_valid_json_passes_schema_validation(self):
        """A valid minimal report passes schema validation."""
        from model_router.stages.render import _validate_json_against_schema
        try:
            import jsonschema  # type: ignore  # noqa
        except ImportError:
            pytest.skip("jsonschema not installed — schema validation skipped")

        valid_report = {
            "schema_version": 1,
            "model_id": "test-model",
            "observables": ["relic"],
            "verdict": "CLEAR",
            "model_props": {"analytic_module_status": "unregistered"},
            "per_observable": {},
            "placements": [],
            "diagnostics": {},
        }
        # Should not raise
        _validate_json_against_schema(valid_report)


# ---------------------------------------------------------------------------
# S15d test 3: exit code mapping table
# ---------------------------------------------------------------------------

class TestExitCodeMapping:
    """_compute_exit_code honors synthesis §10 table."""

    @pytest.mark.parametrize("verdict,strict,expected", [
        ("CLEAR", False, 0),
        ("ROUTE_TO_ANALYTIC", False, 0),
        ("HALT_FOR_SIGNOFF", False, 0),
        ("HARD_HALT", False, 0),
        ("CLEAR", True, 0),
        ("ROUTE_TO_ANALYTIC", True, 0),
        ("HALT_FOR_SIGNOFF", True, 5),
        ("HARD_HALT", True, 6),
    ])
    def test_exit_code_table(self, verdict, strict, expected):
        """Exit code matches synthesis §10 table."""
        composed = _make_composed(verdict)
        opts = _make_options(strict=strict)
        code = _compute_exit_code(composed, opts)
        assert code == expected


# ---------------------------------------------------------------------------
# S15d test 4: placement vocabulary closed enum
# ---------------------------------------------------------------------------

class TestPlacementVocabulary:
    """Placements built by _build_placements honor the schema closed enums."""

    VALID_POSITIONS = {"top", "before_results_table", "before_per_observable", "appendix", "inline"}
    VALID_KINDS = {"analytic", "proxy_run", "halt_notice", "signoff_prompt", "hard_halt_prompt"}

    @pytest.mark.parametrize("verdict", ["CLEAR", "ROUTE_TO_ANALYTIC", "HALT_FOR_SIGNOFF", "HARD_HALT"])
    def test_placement_fields_are_valid_enum_values(self, verdict):
        """All placement fields use closed-enum values from schema."""
        composed = _make_composed(verdict)
        ctx = _make_ctx()
        placements = _build_placements(composed, ctx)
        for p in placements:
            assert p.position in self.VALID_POSITIONS, f"Invalid position: {p.position!r}"
            assert p.kind in self.VALID_KINDS, f"Invalid kind: {p.kind!r}"


# ---------------------------------------------------------------------------
# S15d test 5: placement counts per verdict
# ---------------------------------------------------------------------------

class TestPlacementCounts:
    """_build_placements emits the correct number of placements per verdict."""

    def test_clear_has_zero_placements(self):
        """CLEAR verdict → 0 placements."""
        composed = _make_composed("CLEAR")
        placements = _build_placements(composed, _make_ctx())
        assert placements == []

    def test_route_to_analytic_has_one_placement(self):
        """ROUTE_TO_ANALYTIC verdict → 1 placement."""
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        placements = _build_placements(composed, _make_ctx())
        assert len(placements) == 1
        assert placements[0].position == "before_per_observable"
        assert placements[0].kind == "analytic"

    def test_halt_for_signoff_has_two_placements(self):
        """HALT_FOR_SIGNOFF verdict → 2 placements (halt_notice + signoff_prompt)."""
        composed = _make_composed("HALT_FOR_SIGNOFF")
        placements = _build_placements(composed, _make_ctx())
        assert len(placements) == 2
        kinds = {p.kind for p in placements}
        assert "halt_notice" in kinds
        assert "signoff_prompt" in kinds

    def test_hard_halt_has_one_placement(self):
        """HARD_HALT verdict → 1 placement."""
        composed = _make_composed("HARD_HALT")
        placements = _build_placements(composed, _make_ctx())
        assert len(placements) == 1
        assert placements[0].position == "top"
        assert placements[0].kind == "hard_halt_prompt"

    def test_json_report_includes_exit_code_field(self):
        """JSON report emits exit_code per SKILL.md docs (Phase B drift fix)."""
        composed = _make_composed("CLEAR")
        ctx = _make_ctx()
        opts = _make_options()
        report = stage_p5_render(composed, ctx, opts)
        assert "exit_code" in report.json_report, \
            f"json_report missing exit_code field; keys={list(report.json_report.keys())}"
        assert isinstance(report.json_report["exit_code"], int)
        assert report.json_report["exit_code"] == report.exit_code

    def test_json_report_includes_axis_snapshot_field(self):
        """JSON report emits axis_snapshot per SKILL.md docs (Phase B drift fix)."""
        from model_router.types import AxisBundle
        composed = _make_composed("CLEAR")
        # Carry an AxisBundle on ComposedRouting per iter-3 review recommendation
        composed.axes_snapshot = AxisBundle(
            A1="SM only",
            A8="active",
        )
        ctx = _make_ctx()
        opts = _make_options()
        report = stage_p5_render(composed, ctx, opts)
        assert "axis_snapshot" in report.json_report, \
            f"json_report missing axis_snapshot; keys={list(report.json_report.keys())}"
        snap = report.json_report["axis_snapshot"]
        assert isinstance(snap, dict)
        assert snap.get("A1") == "SM only"
        assert snap.get("A8") == "active"

    def test_disclosure_banner_position_before_per_observable(self):
        """ROUTE_TO_ANALYTIC disclosure banner appears between WS3 section anchors."""
        composed = _make_composed("ROUTE_TO_ANALYTIC", exception_id="dsu3-002")
        ctx = _make_ctx()
        report = stage_p5_render(composed, ctx, _make_options())
        md = report.markdown_report
        # The before_per_observable anchor and banner content should both appear
        assert "<!-- WS3:section=before_per_observable -->" in md
        # Banner content appears after the anchor
        anchor_pos = md.index("<!-- WS3:section=before_per_observable -->")
        after_anchor = md[anchor_pos:]
        # The analytic placement content should follow
        assert "Analytic backend active" in after_anchor or "analytic" in after_anchor.lower()
