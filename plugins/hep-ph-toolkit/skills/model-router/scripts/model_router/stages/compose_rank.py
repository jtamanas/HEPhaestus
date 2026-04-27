"""
model_router/stages/compose_rank.py — Stage P4: compose ranked routing per observable.

Per WS3 plan §S11+S12+S14:
  - Combine per-observable matrix folds + the WS4 exception verdict into
    `ComposedRouting`.
  - Per-observable ranking uses the three-layer sort (role > priority >
    user_memory > prereq_id) from `model_router.ranking`.
  - The selected `active_chain` is the top-ranked, non-blocked fold; the
    rest go into `ranked_alternatives`.
  - Verdict short-circuits:
      HARD_HALT          — no chain selected; status=HARD_HALT.
      HALT_FOR_SIGNOFF   — no chain selected; status=HALT.
      ROUTE_TO_ANALYTIC  — analytic_backend pinned for DM observables.
      CLEAR              — normal ranked routing.

This module does NOT compute observables; it only orders / combines
verdicts (per `feedback_augment_not_replace`).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from model_router.ranking import (
    _apply_user_memory_tiebreak,
    rank_by_role,
)
from model_router.types import (
    ActiveChain,
    AxisBundle,
    ComposedRouting,
    ExceptionVerdict,
    LoadedContext,
    MatrixAcknowledgementMissing,
    MatrixVerdicts,
    ObservableRouting,
    PerCandidateRouting,
    PrereqFold,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DM_OBSERVABLES = {"relic", "dd", "id"}


def _is_dm_observable(observable: str) -> bool:
    return observable in _DM_OBSERVABLES


def _verdict_str(ev: Optional[ExceptionVerdict]) -> str:
    if ev is None:
        return "CLEAR"
    return getattr(ev, "verdict", "CLEAR") or "CLEAR"


def _exception_id(ev: Optional[ExceptionVerdict]) -> Optional[str]:
    if ev is None:
        return None
    return getattr(ev, "exception_id", None)


def _fold_to_active_chain(fold: PrereqFold, status: str = "ROUTED") -> ActiveChain:
    """Convert a PrereqFold to an ActiveChain (status defaults to ROUTED)."""
    return ActiveChain(
        prereq_id=fold.prereq_id,
        role=fold.role_for_observable,
        status=status,
        blockers=list(fold.blockers),
        blocker_classes=list(fold.blocker_classes),
        caveats=list(fold.caveats),
        runtime_install_required=fold.runtime_install_required,
        matrix_acknowledgement_missing=False,
    )


def _select_active_and_alternatives(
    folds: List[PrereqFold],
    user_memory: Optional[Dict[str, int]],
) -> tuple[Optional[PrereqFold], List[PrereqFold]]:
    """Apply role/priority/user-memory ranking; return (top_unblocked, alternatives).

    The "active" is the top-ranked fold whose overall_verdict is NOT 'blocked'.
    All other folds (including any blocked top-rankers and below-active folds)
    become alternatives, preserving rank order.
    """
    ranked = rank_by_role(folds, observable="")  # observable arg reserved
    ranked = _apply_user_memory_tiebreak(ranked, user_memory)

    active: Optional[PrereqFold] = None
    alternatives: List[PrereqFold] = []
    for fold in ranked:
        if active is None and fold.overall_verdict != "blocked":
            active = fold
        else:
            alternatives.append(fold)
    return active, alternatives


def _build_observable_routing_clear(
    observable: str,
    folds: List[PrereqFold],
    user_memory: Optional[Dict[str, int]],
) -> ObservableRouting:
    """CLEAR-path observable routing: normal ranked chain selection."""
    active_fold, alt_folds = _select_active_and_alternatives(folds, user_memory)

    if active_fold is None:
        # All folds are blocked OR no folds at all: status=BLOCKED
        return ObservableRouting(
            observable=observable,
            status="BLOCKED",
            active_chain=None,
            ranked_alternatives=[_fold_to_active_chain(f, status="BLOCKED") for f in alt_folds],
            blockers=sorted({b for f in folds for b in f.blockers}),
            blocker_classes=sorted({c for f in folds for c in f.blocker_classes}),
        )

    return ObservableRouting(
        observable=observable,
        status="ROUTED",
        active_chain=_fold_to_active_chain(active_fold, status="ROUTED"),
        ranked_alternatives=[
            _fold_to_active_chain(
                f,
                status=("BLOCKED" if f.overall_verdict == "blocked" else "ROUTED"),
            )
            for f in alt_folds
        ],
        blockers=list(active_fold.blockers),
        blocker_classes=list(active_fold.blocker_classes),
        caveats=list(active_fold.caveats),
    )


def _label_for_candidate(candidate, observable: str) -> str:
    """Compose the per-candidate observable label.

    Per WS3 plan §S13 + synthesis §5.1: relic → Omega_<name>_h2;
    dd → sigma_SI_<name>; id → Phi_id_<name>. The candidate_name comes
    from CandidateSpec.name; observable selects the prefix/suffix shape.
    """
    name = getattr(candidate, "name", "")
    if observable == "relic":
        return f"Omega_{name}_h2"
    if observable == "dd":
        return f"sigma_SI_{name}"
    if observable == "id":
        return f"Phi_id_{name}"
    return f"{observable}_{name}"


def _build_per_candidate_chains(
    observable: str,
    axes: AxisBundle,
    exception_verdict: Optional[ExceptionVerdict],
) -> List[PerCandidateRouting]:
    """Build per-candidate routing list for ROUTE_TO_ANALYTIC + DM observables.

    Per WS3 plan §S13 + synthesis Decision 1: when a model has multiple DM
    candidates (e.g. dark-su3's V + Psi) and the WS4 verdict is
    ROUTE_TO_ANALYTIC, route each candidate independently to its own
    analytic chain. Activated only when:
        - exception_verdict.verdict == "ROUTE_TO_ANALYTIC"
        - observable in {relic, dd, id}
    Otherwise returns [].

    Per-candidate active_chain is always pinned to analytic_backend with
    role=escape_hatch, since per-candidate v1 only fires inside
    ROUTE_TO_ANALYTIC.
    """
    if exception_verdict is None:
        return []
    if getattr(exception_verdict, "verdict", "CLEAR") != "ROUTE_TO_ANALYTIC":
        return []
    if not _is_dm_observable(observable):
        return []

    candidates = list(axes.candidates or [])
    if not candidates:
        return []

    out: List[PerCandidateRouting] = []
    for cand in candidates:
        analytic_chain = ActiveChain(
            prereq_id="analytic_backend",
            role="escape_hatch",
            status="ROUTED",
            blockers=[],
            blocker_classes=[],
            caveats=[],
            runtime_install_required=False,
            matrix_acknowledgement_missing=False,
        )
        out.append(PerCandidateRouting(
            candidate_name=getattr(cand, "name", ""),
            candidate_field_type=getattr(cand, "field_type", None),
            candidate_mediator_regime=getattr(cand, "mediator_regime", None),
            candidate_uv_provenance=getattr(cand, "uv_provenance", None),
            active_chain=analytic_chain,
            expected_observable_label=_label_for_candidate(cand, observable),
        ))
    return out


def _build_observable_routing_route_to_analytic(
    observable: str,
    folds: List[PrereqFold],
    user_memory: Optional[Dict[str, int]],
    exception_id: Optional[str],
    axes: Optional[AxisBundle] = None,
    exception_verdict: Optional[ExceptionVerdict] = None,
) -> ObservableRouting:
    """ROUTE_TO_ANALYTIC: pin analytic_backend for DM observables; otherwise
    fall back to normal CLEAR-path routing for non-DM observables.

    For DM observables, also emits per_candidate routing (S13 / Decision 1)
    when axes.candidates is non-empty.
    """
    if not _is_dm_observable(observable):
        return _build_observable_routing_clear(observable, folds, user_memory)

    analytic_chain = ActiveChain(
        prereq_id="analytic_backend",
        role="escape_hatch",
        status="ROUTED",
        blockers=[],
        blocker_classes=[],
        caveats=[],
        runtime_install_required=False,
        matrix_acknowledgement_missing=False,
    )
    # All matrix folds become "Blockers on alternative chains" — every
    # matrix prereq for this observable is what would have been routed.
    alt_chains = [
        _fold_to_active_chain(
            f,
            status=("BLOCKED" if f.overall_verdict == "blocked" else "ROUTED"),
        )
        for f in folds
    ]

    per_candidate: List[PerCandidateRouting] = []
    if axes is not None:
        per_candidate = _build_per_candidate_chains(observable, axes, exception_verdict)

    return ObservableRouting(
        observable=observable,
        status="ROUTED",
        active_chain=analytic_chain,
        ranked_alternatives=alt_chains,
        per_candidate=per_candidate,
    )


def _get_chain_overrides(ctx: LoadedContext, observable: str) -> Optional[Dict]:
    """Return the chain_overrides.<observable> block for ctx, or None."""
    if not ctx.model_meta:
        return None
    overrides = ctx.model_meta.get("chain_overrides")
    if not isinstance(overrides, dict):
        return None
    block = overrides.get(observable)
    if not isinstance(block, dict):
        return None
    return block


def _matrix_blockers_for_observable(folds: List[PrereqFold]) -> List[str]:
    """Aggregate all matrix-fold blockers for the observable (deduped, ordered)."""
    seen: List[str] = []
    for f in folds:
        if f.overall_verdict != "blocked":
            continue
        for b in f.blockers:
            if b not in seen:
                seen.append(b)
    return seen


def _validate_matrix_acknowledgement(
    override_block: Dict,
    matrix_blockers: List[str],
) -> bool:
    """Check whether the override's matrix_acknowledgement covers every
    matrix-fold blocker for this observable.

    Returns True iff the override carries a matrix_acknowledgement block
    AND every matrix blocker appears in accepted_blockers. Per WS3 plan
    §S14, missing or incomplete acknowledgement is the only contradiction
    the renderer/strict-mode treat as exit-code 4.
    """
    if not matrix_blockers:
        # Nothing to acknowledge → trivially satisfied.
        return True
    ack = override_block.get("matrix_acknowledgement")
    if not isinstance(ack, dict):
        return False
    accepted = ack.get("accepted_blockers") or []
    if not isinstance(accepted, list):
        return False
    accepted_set = set(accepted)
    return all(b in accepted_set for b in matrix_blockers)


def _build_active_chain_from_override(
    override_block: Dict,
    matrix_blockers: List[str],
) -> ActiveChain:
    """Build an ActiveChain from a chain_overrides block.

    The override.chain[0] is treated as the pinned active prereq (typically
    "analytic_backend"). The matrix_acknowledgement_missing flag is set
    when the override fails _validate_matrix_acknowledgement.
    """
    chain = override_block.get("chain") or []
    pinned_id = chain[0] if chain else "analytic_backend"
    backend_hint = override_block.get("backend_hint")
    role = "escape_hatch" if backend_hint == "analytic" else "primary"

    ack_ok = _validate_matrix_acknowledgement(override_block, matrix_blockers)
    caveats: List[str] = []
    reason = override_block.get("reason")
    if reason:
        caveats.append(f"chain_override: {reason}")

    return ActiveChain(
        prereq_id=pinned_id,
        role=role,
        status="ROUTED",
        blockers=[],
        blocker_classes=[],
        caveats=caveats,
        runtime_install_required=False,
        matrix_acknowledgement_missing=not ack_ok,
    )


def _build_observable_routing_overridden(
    observable: str,
    folds: List[PrereqFold],
    override_block: Dict,
    axes: Optional[AxisBundle] = None,
    exception_verdict: Optional[ExceptionVerdict] = None,
) -> ObservableRouting:
    """Build ObservableRouting using a chain_override (skip the matrix ranking)."""
    matrix_blockers = _matrix_blockers_for_observable(folds)
    active_chain = _build_active_chain_from_override(override_block, matrix_blockers)

    # Matrix folds become "Blockers on alternative chains" — the override
    # explicitly bypasses them, so they're surfaced as alternatives.
    alt_chains = [
        _fold_to_active_chain(
            f,
            status=("BLOCKED" if f.overall_verdict == "blocked" else "ROUTED"),
        )
        for f in folds
    ]

    per_candidate: List[PerCandidateRouting] = []
    if axes is not None:
        per_candidate = _build_per_candidate_chains(observable, axes, exception_verdict)

    warnings: List[str] = []
    if active_chain.matrix_acknowledgement_missing:
        warnings.append(
            "chain_override drops matrix-blocked prereqs without complete "
            "matrix_acknowledgement; results unverified."
        )

    return ObservableRouting(
        observable=observable,
        status="ROUTED",
        active_chain=active_chain,
        ranked_alternatives=alt_chains,
        per_candidate=per_candidate,
        matrix_acknowledgement_warnings=warnings,
    )


def _build_observable_routing_halted(
    observable: str,
    folds: List[PrereqFold],
    status: str,
) -> ObservableRouting:
    """HARD_HALT or HALT_FOR_SIGNOFF: emit per-observable rows with no active
    chain; preserve fold information in ranked_alternatives for diagnostic UI.
    """
    return ObservableRouting(
        observable=observable,
        status=status,
        active_chain=None,
        ranked_alternatives=[
            _fold_to_active_chain(f, status=status) for f in folds
        ],
        blockers=sorted({b for f in folds for b in f.blockers}),
        blocker_classes=sorted({c for f in folds for c in f.blocker_classes}),
    )


# ---------------------------------------------------------------------------
# Public API — Stage P4
# ---------------------------------------------------------------------------

def stage_p4_compose_and_rank(
    axes: AxisBundle,
    ctx: LoadedContext,
    exception_verdict: Optional[ExceptionVerdict],
    matrix_verdicts: MatrixVerdicts,
) -> ComposedRouting:
    """Stage P4: compose ranked per-observable routing.

    Routing branches on `exception_verdict.verdict`:
      HARD_HALT          → all observables HARD_HALT.
      HALT_FOR_SIGNOFF   → all observables HALT.
      ROUTE_TO_ANALYTIC  → DM observables pinned to analytic_backend; non-DM
                           observables follow the normal ranked path.
      CLEAR              → normal ranked path.

    Per-observable ranking is sourced from `MatrixVerdicts.by_observable`
    using `model_router.ranking.rank_by_role` followed by user-memory
    tertiary tiebreak (manager Decision 5; SKILL.md `## Ranking policy`).
    """
    verdict = _verdict_str(exception_verdict)
    exc_id = _exception_id(exception_verdict)

    user_memory = None
    if ctx.options is not None:
        user_memory = ctx.options.user_preferences

    per_observable: Dict[str, ObservableRouting] = {}
    exception_verdict_by_observable: Dict[str, ExceptionVerdict] = {}

    strict_mode = bool(getattr(ctx.options, "strict", False)) if ctx.options else False

    for observable in (ctx.observables or []):
        folds = (matrix_verdicts.by_observable.get(observable, []) if matrix_verdicts else [])

        # S14: chain_overrides take precedence over matrix ranking for
        # CLEAR / ROUTE_TO_ANALYTIC verdicts. HARD_HALT and HALT_FOR_SIGNOFF
        # always halt regardless of overrides.
        override_block = _get_chain_overrides(ctx, observable)

        if verdict == "HARD_HALT":
            per_observable[observable] = _build_observable_routing_halted(
                observable, folds, status="HARD_HALT"
            )
        elif verdict == "HALT_FOR_SIGNOFF":
            per_observable[observable] = _build_observable_routing_halted(
                observable, folds, status="HALT"
            )
        elif override_block is not None:
            # S14: chain_override path. Strict mode raises on missing/incomplete
            # matrix_acknowledgement (synthesis Decision 4 → exit code 4).
            matrix_blockers = _matrix_blockers_for_observable(folds)
            ack_ok = _validate_matrix_acknowledgement(override_block, matrix_blockers)
            if strict_mode and not ack_ok:
                raise MatrixAcknowledgementMissing(
                    f"chain_override for observable '{observable}' on model "
                    f"'{ctx.model_id}' drops matrix-blocked prereqs without "
                    f"complete matrix_acknowledgement. Missing acknowledgement "
                    f"for: {[b for b in matrix_blockers if b not in (override_block.get('matrix_acknowledgement') or {}).get('accepted_blockers', [])]}. "
                    f"Strict mode → exit code 4."
                )
            per_observable[observable] = _build_observable_routing_overridden(
                observable, folds, override_block,
                axes=axes,
                exception_verdict=exception_verdict,
            )
        elif verdict == "ROUTE_TO_ANALYTIC":
            per_observable[observable] = _build_observable_routing_route_to_analytic(
                observable, folds, user_memory,
                exception_id=exc_id,
                axes=axes,
                exception_verdict=exception_verdict,
            )
        else:
            per_observable[observable] = _build_observable_routing_clear(
                observable, folds, user_memory
            )

        if exception_verdict is not None:
            exception_verdict_by_observable[observable] = exception_verdict

    return ComposedRouting(
        model_id=ctx.model_id,
        observables=list(ctx.observables or []),
        exception_verdict=exception_verdict,
        exception_verdict_by_observable=exception_verdict_by_observable,
        per_observable=per_observable,
        diagnostics={
            **(dict(ctx.diagnostics) if (ctx and ctx.diagnostics) else {}),
            **(dict(matrix_verdicts.diagnostics) if matrix_verdicts and matrix_verdicts.diagnostics else {}),
        },
        axes_snapshot=axes,
    )
