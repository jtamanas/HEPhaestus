"""
test_orchestrator.py — Phase 7: full-pipeline integration scenarios (S23).

Six scenarios per WS3 plan §S23 (synthesis §11.2):
    1. singlet-doublet → CLEAR.
    2. dark-su3 → ROUTE_TO_ANALYTIC (analytic backend pinned for DM observables).
    3. two-hdm-a → HALT_FOR_SIGNOFF (via stub-adapter short-circuit; D6).
    4. archived spec → SpecArchivedError (clean error).
    5. unknown model → ModelNotInRegistry (clean error).
    6. dark-su3-confining synthetic → HARD_HALT (via stub fallback that injects HARD_HALT).

The orchestrator is a thin pipeline glue (P0..P5) with early-jump-to-P5 for
HARD_HALT and HALT_FOR_SIGNOFF (no matrix lookup needed for halts). All
observables, options, and registry paths can be overridden via kwargs to keep
tests hermetic.
"""
import pytest

orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route not yet implemented (awaiting S23)",
)
route = orch_mod.route


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _common_kwargs(mock_constraints_yaml):
    """Return kwargs that point P0 at the test fixture registry paths."""
    import pathlib
    fixtures = pathlib.Path(__file__).parent / "fixtures" / "registries"
    return dict(
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=fixtures / "blocker_catalog.yaml",
        analytic_exceptions_path=fixtures / "analytic_exceptions.yaml",
    )


# ---------------------------------------------------------------------------
# Scenario 1 — singlet-doublet → CLEAR
# ---------------------------------------------------------------------------

class TestOrchestratorClear:
    def test_singlet_doublet_returns_clear_routing_report(
        self, mock_constraints_yaml
    ):
        from model_router.types import RouterOptions
        report = route(
            model_id="singlet-doublet",
            observables=["relic"],
            options=RouterOptions(),
            **_common_kwargs(mock_constraints_yaml),
        )
        assert report.json_report["verdict"] == "CLEAR"
        assert report.exit_code == 0
        assert report.model_id == "singlet-doublet"
        assert "relic" in report.json_report["per_observable"]


# ---------------------------------------------------------------------------
# Scenario 2 — dark-su3 → ROUTE_TO_ANALYTIC
# ---------------------------------------------------------------------------

class TestOrchestratorRouteToAnalytic:
    def test_dark_su3_routes_to_analytic_backend_for_relic(
        self, mock_constraints_yaml
    ):
        from model_router.types import RouterOptions
        report = route(
            model_id="dark-su3",
            observables=["relic"],
            options=RouterOptions(),
            **_common_kwargs(mock_constraints_yaml),
        )
        assert report.json_report["verdict"] == "ROUTE_TO_ANALYTIC"
        assert report.exit_code == 0
        active = report.json_report["per_observable"]["relic"]["active_chain"]
        assert active is not None
        assert active["prereq_id"] == "analytic_backend"

    def test_dark_su3_emits_per_candidate_block_for_relic(
        self, mock_constraints_yaml
    ):
        from model_router.types import RouterOptions
        report = route(
            model_id="dark-su3",
            observables=["relic"],
            options=RouterOptions(),
            **_common_kwargs(mock_constraints_yaml),
        )
        per_cand = report.json_report["per_observable"]["relic"]["per_candidate"]
        assert len(per_cand) == 2
        labels = {pc["expected_observable_label"] for pc in per_cand}
        assert labels == {"Omega_V_h2", "Omega_Psi_h2"}


# ---------------------------------------------------------------------------
# Scenario 3 — 2HDM+a → HALT_FOR_SIGNOFF (stub adapter; D6)
# ---------------------------------------------------------------------------

class TestOrchestratorHaltForSignoff:
    def test_two_hdm_a_halts_for_signoff_via_stub_adapter(
        self, mock_constraints_yaml
    ):
        """The 2HDM+a registry entry pins analytic_module to
        analytic_models.stub_unimplemented (which carries STUB=True per D4).
        The P1 adapter should map this to status='stub'; P2 short-circuits
        to HALT_FOR_SIGNOFF (synthesis Decision 6).
        """
        from model_router.types import RouterOptions
        report = route(
            model_id="two-hdm-a",
            observables=["relic"],
            options=RouterOptions(),
            **_common_kwargs(mock_constraints_yaml),
        )
        assert report.json_report["verdict"] == "HALT_FOR_SIGNOFF"
        # Default mode: HALT_FOR_SIGNOFF still exits 0
        assert report.exit_code == 0
        # Per-observable status pinned to HALT
        assert report.json_report["per_observable"]["relic"]["status"] == "HALT"
        # Placements include both the halt notice and signoff prompt
        kinds = {p["kind"] for p in report.json_report["placements"]}
        assert "halt_notice" in kinds
        assert "signoff_prompt" in kinds

    def test_two_hdm_a_strict_mode_exits_5(
        self, mock_constraints_yaml
    ):
        from model_router.types import RouterOptions
        report = route(
            model_id="two-hdm-a",
            observables=["relic"],
            options=RouterOptions(strict=True),
            **_common_kwargs(mock_constraints_yaml),
        )
        assert report.exit_code == 5


# ---------------------------------------------------------------------------
# Scenario 4 — archived spec → SpecArchivedError
# ---------------------------------------------------------------------------

class TestOrchestratorArchivedSpec:
    def test_archived_a8_raises_spec_archived_error(
        self, mock_constraints_yaml, tmp_path, monkeypatch
    ):
        """When a model's WS1 A8 axis is 'archived', P1 raises SpecArchivedError."""
        from model_router.types import RouterOptions, SpecArchivedError
        # Patch the extract_axes module to return an archived A8 verdict.
        from model_router.stages import extract_axes as ea_mod

        def _archived_axes(ctx):
            from model_router.types import AxisBundle
            return AxisBundle(A1="SM only", A8="archived")

        monkeypatch.setattr(
            ea_mod, "stage_p1_validate_and_extract", _archived_axes
        )
        # The simple stub returns A8=archived without raising; the orchestrator
        # must detect this and raise SpecArchivedError before P2.
        with pytest.raises(SpecArchivedError):
            route(
                model_id="singlet-doublet",
                observables=["relic"],
                options=RouterOptions(),
                **_common_kwargs(mock_constraints_yaml),
            )


# ---------------------------------------------------------------------------
# Scenario 5 — unknown model → ModelNotInRegistry
# ---------------------------------------------------------------------------

class TestOrchestratorUnknownModel:
    def test_unknown_model_raises_model_not_in_registry(
        self, mock_constraints_yaml
    ):
        from model_router.types import RouterOptions, ModelNotInRegistry
        with pytest.raises(ModelNotInRegistry):
            route(
                model_id="nonexistent-model",
                observables=["relic"],
                options=RouterOptions(),
                **_common_kwargs(mock_constraints_yaml),
            )


# ---------------------------------------------------------------------------
# Scenario 6 — confining synthetic → HARD_HALT
# ---------------------------------------------------------------------------

class TestOrchestratorHardHalt:
    def test_confining_synthetic_routes_to_hard_halt(
        self, mock_constraints_yaml, monkeypatch
    ):
        """Confining synthetic models trigger HARD_HALT in WS4 (or fallback)."""
        from model_router.types import RouterOptions, ExceptionVerdict
        from model_router.stages import detect_exception as de_mod

        # Inject a HARD_HALT verdict to simulate WS4's response to the
        # confining gauge-group pattern. The orchestrator must short-circuit
        # P3+P4 ranking (no matrix lookup needed for halts) and dispatch
        # render with the HARD_HALT path.
        def _hard_halt_detect(axes, ctx):
            return ExceptionVerdict(
                verdict="HARD_HALT",
                exception_id=None,
                disclosure_required=False,
            )

        monkeypatch.setattr(
            de_mod, "stage_p2_detect_exception", _hard_halt_detect
        )
        # Use dark-su3 as a stand-in (the registry just provides a registered model;
        # the verdict is forced via the patched detector).
        report = route(
            model_id="dark-su3",
            observables=["relic"],
            options=RouterOptions(),
            **_common_kwargs(mock_constraints_yaml),
        )
        assert report.json_report["verdict"] == "HARD_HALT"
        assert report.exit_code == 0  # default mode
        # Hard-halt prompt placement at top
        kinds = {p["kind"] for p in report.json_report["placements"]}
        assert "hard_halt_prompt" in kinds
