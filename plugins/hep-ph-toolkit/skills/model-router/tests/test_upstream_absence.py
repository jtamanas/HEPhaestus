"""
test_upstream_absence.py — CI invariant: upstream WS1/WS2/WS4 absent (S26).

Per plan §S26 + manager D1/D2/D9:
  - WS1 absent (taxonomy.read_axes import fails) -> WS1NotMerged, exit 1.
  - WS2 absent (ConstraintRow.capability_blockers field missing) -> WS2NotMerged, exit 3.
  - WS4 absent (detect_analytic_exception module missing) -> CLEAR stub
    verdict + detector_unavailable: true diagnostic, exit 0.

The hard-gate behaviors are pinned by simulating each absence via module
patching. The WS4 absent case is the single-tier fail-open path; WS1 and
WS2 are fail-closed.
"""
import pathlib
import pytest

# These tests import model_router internals so the module must load.
orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for upstream-absence tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"


def _kwargs(constraints):
    return dict(
        constraints_path=constraints,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )


# ---------------------------------------------------------------------------
# WS1 absent — taxonomy.read_axes import fails -> WS1NotMerged (exit 1)
# ---------------------------------------------------------------------------

class TestWS1Absent:
    def test_ws1_unavailable_raises_ws1_not_merged(
        self, mock_constraints_yaml, monkeypatch
    ):
        from model_router.types import RouterOptions, WS1NotMerged
        from model_router.stages import extract_axes as ea_mod

        # Simulate WS1 absent by setting the module-level availability flag.
        monkeypatch.setattr(ea_mod, "_read_axes_available", False)
        monkeypatch.setattr(ea_mod, "_read_axes_fn", None)

        with pytest.raises(WS1NotMerged):
            route(
                model_id="singlet-doublet",
                observables=["relic"],
                options=RouterOptions(),
                **_kwargs(mock_constraints_yaml),
            )

    def test_ws1_not_merged_carries_exit_code_1(self):
        """Class-level invariant: WS1NotMerged.exit_code == 1."""
        from model_router.types import WS1NotMerged
        assert WS1NotMerged.exit_code == 1


# ---------------------------------------------------------------------------
# WS2 absent — ConstraintRow.capability_blockers missing -> WS2NotMerged (exit 3)
# ---------------------------------------------------------------------------

class TestWS2Absent:
    def test_ws2_capability_blockers_missing_raises_ws2_not_merged(
        self, mock_constraints_yaml, monkeypatch
    ):
        from model_router.types import RouterOptions, WS2NotMerged
        from model_router.stages import load as load_mod

        monkeypatch.setattr(load_mod, "_has_capability_blockers", lambda: False)

        with pytest.raises(WS2NotMerged):
            route(
                model_id="singlet-doublet",
                observables=["relic"],
                options=RouterOptions(),
                **_kwargs(mock_constraints_yaml),
            )

    def test_ws2_not_merged_carries_exit_code_3(self):
        """Class-level invariant: WS2NotMerged.exit_code == 3."""
        from model_router.types import WS2NotMerged
        assert WS2NotMerged.exit_code == 3


# ---------------------------------------------------------------------------
# WS4 absent — detector module unavailable -> CLEAR + detector_unavailable
# ---------------------------------------------------------------------------

class TestWS4Absent:
    def test_ws4_detector_unavailable_returns_clear_verdict(
        self, mock_constraints_yaml, monkeypatch
    ):
        """When WS4 is unavailable, the detect_exception stage falls back
        to a CLEAR stub verdict with detector_unavailable=True diagnostic.
        """
        from model_router.types import RouterOptions
        from model_router.stages import detect_exception as de_mod

        monkeypatch.setattr(de_mod, "_WS4_DETECTOR_AVAILABLE", False)
        monkeypatch.setattr(de_mod, "_ws4_detect", None)

        report = route(
            model_id="singlet-doublet",
            observables=["relic"],
            options=RouterOptions(),
            **_kwargs(mock_constraints_yaml),
        )
        assert report.json_report["verdict"] == "CLEAR"
        assert report.exit_code == 0
        # detector_unavailable diagnostic surfaced
        assert report.json_report["diagnostics"].get("detector_unavailable") is True

    def test_ws4_absent_default_mode_exits_0(
        self, mock_constraints_yaml, monkeypatch
    ):
        """WS4 absent does NOT escalate — fail-open is intentional (D9 differs from
        D1/D2 fail-closed posture). Exit code stays 0 in default mode."""
        from model_router.types import RouterOptions
        from model_router.stages import detect_exception as de_mod

        monkeypatch.setattr(de_mod, "_WS4_DETECTOR_AVAILABLE", False)
        monkeypatch.setattr(de_mod, "_ws4_detect", None)

        report = route(
            model_id="singlet-doublet",
            observables=["relic"],
            options=RouterOptions(),
            **_kwargs(mock_constraints_yaml),
        )
        assert report.exit_code == 0
