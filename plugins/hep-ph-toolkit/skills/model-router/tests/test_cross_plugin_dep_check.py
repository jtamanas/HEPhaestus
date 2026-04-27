"""
test_cross_plugin_dep_check.py — CI invariant: cross-plugin dep (S26, manager D2).

Per plan §S26 + D2:
  - Missing hep-ph-demo._shared.matrix_lookup raises
    WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO with exit code 3.
  - The remediation message contains "install hep-ph-demo plugin".
  - The exit-code attribute on the exception class is 3.

The dep is exercised by patching the import site inside stages/matrix_lookup.py.
"""
import pathlib
import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for cross-plugin dep tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"


def _kwargs(constraints):
    return dict(
        constraints_path=constraints,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )


def test_missing_hep_ph_demo_raises_with_remediation(
    mock_constraints_yaml, monkeypatch
):
    """Patch _load_matrix to simulate matrix_lookup ImportError -> raise the
    WS3 cross-plugin error.
    """
    from model_router.types import (
        RouterOptions,
        WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO,
    )
    from model_router.stages import matrix_lookup as ml_mod

    def _failing_load(*args, **kwargs):
        raise WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO(
            "plugins/hep-ph-toolkit/skills/_shared/matrix_lookup.py not importable; "
            "install hep-ph-demo plugin"
        )

    monkeypatch.setattr(ml_mod, "_load_matrix", _failing_load)

    with pytest.raises(WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO) as excinfo:
        route(
            model_id="singlet-doublet",
            observables=["relic"],
            options=RouterOptions(),
            **_kwargs(mock_constraints_yaml),
        )
    assert "install hep-ph-demo plugin" in str(excinfo.value)


def test_workflow_plugin_missing_dep_carries_exit_code_3():
    """Class-level invariant: the exception's exit_code is 3."""
    from model_router.types import WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO
    assert WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO.exit_code == 3


def test_dep_check_fires_inside_matrix_lookup_stage(
    mock_constraints_yaml, monkeypatch
):
    """Verify the dep check fires at the stage_p3_matrix_lookup boundary
    (not at module import time) — so the orchestrator can short-circuit
    without crashing on import for HARD_HALT/HALT_FOR_SIGNOFF paths.
    """
    from model_router.types import (
        ExceptionVerdict,
        RouterOptions,
        WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO,
    )
    from model_router.stages import matrix_lookup as ml_mod
    from model_router.stages import detect_exception as de_mod

    # Force HARD_HALT verdict so P3 is short-circuited.
    def _hard_halt(axes, ctx):
        return ExceptionVerdict(verdict="HARD_HALT")

    def _failing_load(*args, **kwargs):
        raise WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO(
            "should not be reached"
        )

    monkeypatch.setattr(de_mod, "stage_p2_detect_exception", _hard_halt)
    monkeypatch.setattr(ml_mod, "_load_matrix", _failing_load)

    # Should NOT raise — P3 is skipped on HARD_HALT.
    report = route(
        model_id="singlet-doublet",
        observables=["relic"],
        options=RouterOptions(),
        **_kwargs(mock_constraints_yaml),
    )
    assert report.json_report["verdict"] == "HARD_HALT"
