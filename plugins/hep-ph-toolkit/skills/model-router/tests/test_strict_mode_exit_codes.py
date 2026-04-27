"""
test_strict_mode_exit_codes.py — CI invariant: --strict exit-code mapping (S26).

Per plan §S26 + synthesis Decision 4 / §10:
  - dark-su3 --strict (chain_override missing matrix_acknowledgement) -> exit 4.
  - two-hdm-a --strict (HALT_FOR_SIGNOFF via stub adapter)             -> exit 5.
  - confining synthetic --strict (HARD_HALT)                           -> exit 6.

Tests run the orchestrator in-process (not subprocess) so the test runner
can monkeypatch the WS4 stub-detection branch where needed; the CLI
exit-code mapping is exercised separately at the router.py level.
"""
import pathlib
import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for strict-mode exit-code tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"


def _kwargs(constraints):
    return dict(
        constraints_path=constraints,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )


def test_dark_su3_strict_with_missing_acknowledgement_exits_4(mock_constraints_yaml):
    """Strict mode raises MatrixAcknowledgementMissing when chain_override
    drops matrix-blocked prereqs without acknowledgement.
    """
    from model_router.types import RouterOptions, MatrixAcknowledgementMissing
    with pytest.raises(MatrixAcknowledgementMissing):
        route(
            model_id="dark-su3",
            observables=["relic"],
            options=RouterOptions(strict=True),
            **_kwargs(mock_constraints_yaml),
        )


def test_two_hdm_a_strict_halt_for_signoff_exits_5(mock_constraints_yaml):
    """Strict mode + HALT_FOR_SIGNOFF -> exit_code == 5 (synthesis §10)."""
    from model_router.types import RouterOptions
    report = route(
        model_id="two-hdm-a",
        observables=["relic"],
        options=RouterOptions(strict=True),
        **_kwargs(mock_constraints_yaml),
    )
    assert report.exit_code == 5
    assert report.json_report["verdict"] == "HALT_FOR_SIGNOFF"


def test_hard_halt_strict_exits_6(mock_constraints_yaml, monkeypatch):
    """Strict mode + HARD_HALT -> exit_code == 6 (synthesis §10)."""
    from model_router.types import RouterOptions, ExceptionVerdict
    from model_router.stages import detect_exception as de_mod

    def _hard_halt_detect(axes, ctx):
        return ExceptionVerdict(
            verdict="HARD_HALT",
            exception_id=None,
            disclosure_required=False,
        )

    monkeypatch.setattr(de_mod, "stage_p2_detect_exception", _hard_halt_detect)
    report = route(
        model_id="dark-su3",
        observables=["relic"],
        options=RouterOptions(strict=True),
        **_kwargs(mock_constraints_yaml),
    )
    assert report.exit_code == 6
    assert report.json_report["verdict"] == "HARD_HALT"
