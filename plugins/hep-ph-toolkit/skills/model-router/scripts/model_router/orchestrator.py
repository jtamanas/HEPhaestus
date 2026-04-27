"""
model_router/orchestrator.py — top-level pipeline glue (S23).

The orchestrator wires the six WS3 stages (P0..P5) into a single `route()`
call:

    P0 load            -> LoadedContext
    P1 extract_axes    -> AxisBundle  (raises SpecArchivedError on A8=archived)
    P2 detect_exception -> ExceptionVerdict
        | HARD_HALT or HALT_FOR_SIGNOFF -> short-circuit; skip P3 and produce
        | empty MatrixVerdicts before P4 (per WS3 plan §S23 + synthesis §3 P5
        | early-jump path).
    P3 matrix_lookup   -> MatrixVerdicts
    P4 compose_rank    -> ComposedRouting
    P5 render          -> RoutingReport

`route()` is a pure pipeline function — it does NOT compute observables, run
tools, or call out to physics backends. It only orchestrates structural
stages.

Public API:
    route(model_id, observables=None, options=None,
          *, constraints_path=None, blocker_catalog_path=None,
          analytic_exceptions_path=None) -> RoutingReport

Errors propagate (P0 ModelNotInRegistry / WS2NotMerged, P1 SpecArchivedError /
WS1NotMerged, etc.).  The CLI in router.py maps exceptions to exit codes; the
in-process API just re-raises.
"""
from __future__ import annotations

import pathlib
from typing import List, Optional

from model_router.types import (
    LoadedContext,
    MatrixVerdicts,
    RouterOptions,
    RoutingReport,
    SpecArchivedError,
)


def route(
    model_id: str,
    observables: Optional[List[str]] = None,
    options: Optional[RouterOptions] = None,
    *,
    constraints_path: Optional[pathlib.Path] = None,
    blocker_catalog_path: Optional[pathlib.Path] = None,
    analytic_exceptions_path: Optional[pathlib.Path] = None,
) -> RoutingReport:
    """Route a registered BSM model through the WS3 pipeline.

    Args:
        model_id: registered model identifier (in constraints.yaml `models`).
        observables: optional list (e.g. ["relic", "dd"]); defaults to model defaults.
        options: optional RouterOptions (strict, output, user_preferences, ...).
        constraints_path/blocker_catalog_path/analytic_exceptions_path: optional
            registry-path overrides (for tests / non-default registries).

    Returns:
        RoutingReport with json_report, markdown_report, placements, exit_code.

    Raises:
        ModelNotInRegistry, ModelSpecMissing, RegistryCorrupt — from P0.
        WS2NotMerged — from P0 (manager D1 hard-gate).
        WS1NotMerged — from P1 (manager D9 hard-gate).
        SpecArchivedError — from P1 (A8 == 'archived').
        WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO — from P3 (manager D2).
        DetectorInternalError — from P2 (WS4 raised unexpectedly).
        SchemaValidationError — from P5 (emitted JSON failed schema).
        DisclosureBannerMissing — from P5 (ROUTE_TO_ANALYTIC + missing banner).
        MatrixAcknowledgementMissing — from P4 (--strict + bad chain_override).
    """
    # Late imports so test monkeypatches on stage modules take effect.
    from model_router.stages import load as _load_mod
    from model_router.stages import extract_axes as _axes_mod
    from model_router.stages import detect_exception as _exc_mod
    from model_router.stages import matrix_lookup as _matrix_mod
    from model_router.stages import compose_rank as _compose_mod
    from model_router.stages import render as _render_mod

    if options is None:
        options = RouterOptions()

    # --- P0: load registries + spec ---
    ctx: LoadedContext = _load_mod.stage_p0_load(
        model_id=model_id,
        observables=observables,
        options=options,
        constraints_path=constraints_path,
        blocker_catalog_path=blocker_catalog_path,
        analytic_exceptions_path=analytic_exceptions_path,
    )

    # --- P1: extract axes (early halt on archived) ---
    axes = _axes_mod.stage_p1_validate_and_extract(ctx)

    # Defensive: if extract_axes returned an A8=archived bundle without raising,
    # surface the SpecArchivedError at the orchestrator boundary.  The
    # extract_axes module also raises this; the duplicate check makes the
    # orchestrator robust against monkeypatched / partial implementations.
    if getattr(axes, "A8", None) == "archived":
        raise SpecArchivedError(
            f"Model '{model_id}' is archived (A8 == 'archived'); "
            "routing halted before exception detection."
        )

    # --- P2: detect analytic exception ---
    exception_verdict = _exc_mod.stage_p2_detect_exception(axes, ctx)
    verdict = getattr(exception_verdict, "verdict", "CLEAR") or "CLEAR"

    # --- P3: matrix lookup (skip on hard halts; short-circuit per plan §S23) ---
    if verdict in ("HARD_HALT", "HALT_FOR_SIGNOFF"):
        # Empty matrix verdicts: composer will emit per-observable rows from
        # exception_verdict only.  This avoids an unnecessary cross-plugin
        # matrix call when no chain selection is possible.
        matrix_verdicts = MatrixVerdicts(by_observable={obs: [] for obs in ctx.observables})
    else:
        matrix_verdicts = _matrix_mod.stage_p3_matrix_lookup(
            axes, ctx, exception_verdict
        )

    # --- P4: compose + rank ---
    composed = _compose_mod.stage_p4_compose_and_rank(
        axes, ctx, exception_verdict, matrix_verdicts
    )

    # --- P5: render to JSON + Markdown ---
    report = _render_mod.stage_p5_render(composed, ctx, options)
    return report
