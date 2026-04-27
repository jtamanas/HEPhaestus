"""
test_p2_detect_exception.py — Phase 3: stage_p2_detect_exception tests (TDD scaffold).

Tests collected but SKIPPED until detect_exception impl lands (S9).
"""
import pytest

detect_mod = pytest.importorskip(
    "model_router.stages.detect_exception",
    reason="stage_p2_detect_exception not yet implemented (awaiting S9)",
)
stage_p2_detect_exception = detect_mod.stage_p2_detect_exception


class TestP2DetectException:
    """P2 WS4 wrapper tests."""

    def test_detect_clear_for_singlet_doublet(
        self, mock_constraints_yaml, spec_singlet_doublet
    ):
        """singlet-doublet (no analytic exception) → CLEAR verdict."""
        from model_router.types import AxisBundle, LoadedContext, RouterOptions

        axes = _make_axes_singlet_doublet()
        ctx = _make_ctx("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        verdict = stage_p2_detect_exception(axes, ctx)
        assert verdict.verdict == "CLEAR"

    def test_detect_route_to_analytic_for_dark_su3(
        self, mock_constraints_yaml, spec_dark_su3, mock_analytic_exceptions
    ):
        """dark-su3 with active analytic exception → ROUTE_TO_ANALYTIC verdict."""
        axes = _make_axes_dark_su3()
        ctx = _make_ctx("dark-su3", spec_dark_su3, mock_constraints_yaml)
        ctx.analytic_exceptions = mock_analytic_exceptions
        verdict = stage_p2_detect_exception(axes, ctx)
        assert verdict.verdict == "ROUTE_TO_ANALYTIC"

    def test_detect_halt_for_signoff_for_2hdma_stub(
        self, mock_constraints_yaml, spec_two_hdm_a
    ):
        """2HDM+a with stub analytic module → HALT_FOR_SIGNOFF (stub adapter)."""
        axes = _make_axes_two_hdm_a()
        ctx = _make_ctx("two-hdm-a", spec_two_hdm_a, mock_constraints_yaml)
        verdict = stage_p2_detect_exception(axes, ctx)
        assert verdict.verdict == "HALT_FOR_SIGNOFF"

    def test_detect_ws4_absent_returns_clear_stub_with_diagnostic(
        self, mock_constraints_yaml, spec_singlet_doublet, monkeypatch
    ):
        """When WS4 detector module is absent → CLEAR stub + detector_unavailable diagnostic."""
        import sys
        # Simulate WS4 absent
        monkeypatch.setattr(
            "model_router.stages.detect_exception._WS4_DETECTOR_AVAILABLE",
            False,
        )
        axes = _make_axes_singlet_doublet()
        ctx = _make_ctx("singlet-doublet", spec_singlet_doublet, mock_constraints_yaml)
        verdict = stage_p2_detect_exception(axes, ctx)
        assert verdict.verdict == "CLEAR"
        # detector_unavailable should be in ctx.diagnostics or verdict
        assert getattr(verdict, "detector_unavailable", False) or \
               ctx.diagnostics.get("detector_unavailable", False)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_axes_singlet_doublet():
    from model_router.types import AxisBundle, CandidateSpec
    # uv_provenance is non-None so WS4 takes the axis-based path in
    # _compute_signal_dm_not_in_uv (instead of falling back to direct spec
    # inspection, which assumes display.dm_candidates is a dict).
    return AxisBundle(
        A1="SM only",
        A8="active",
        candidates=[
            CandidateSpec(
                name="chi_1",
                field_type="Dirac fermion",
                uv_provenance="tree-level portal",
            )
        ],
        model_props={"analytic_module_status": "missing"},
    )


def _make_axes_dark_su3():
    from model_router.types import AxisBundle, CandidateSpec
    return AxisBundle(
        A1="SM + extra SU(N)",
        A8="active",
        candidates=[
            CandidateSpec(name="V", field_type="vector", uv_provenance="analytic-only"),
            CandidateSpec(name="Psi", field_type="Dirac fermion", uv_provenance="analytic-only"),
        ],
        model_props={"analytic_module_status": "registered_active"},
    )


def _make_axes_two_hdm_a():
    from model_router.types import AxisBundle, CandidateSpec
    return AxisBundle(
        A1="SM only",
        A8="active",
        candidates=[CandidateSpec(name="chi", field_type="Majorana fermion")],
        model_props={"analytic_module_status": "stub"},
    )


def _make_ctx(model_id, spec, constraints_path, model_meta=None):
    import yaml
    from model_router.types import LoadedContext, RouterOptions

    raw = yaml.safe_load(open(constraints_path))
    meta = model_meta or raw.get("models", {}).get(model_id, {})
    return LoadedContext(
        model_id=model_id,
        observables=["relic"],
        options=RouterOptions(),
        model_meta=meta,
        model_spec=spec,
        prereqs=raw.get("prereqs", {}),
        constraints_raw=raw,
        blocker_catalog={},
        analytic_exceptions={},
        config={},
    )
