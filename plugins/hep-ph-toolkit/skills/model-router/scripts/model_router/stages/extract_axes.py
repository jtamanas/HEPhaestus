"""
model_router/stages/extract_axes.py — Stage P1: validate and extract axes.

Manager D9 hard-gate on WS1: imports from taxonomy.read_axes; raises WS1NotMerged
(exit 1) if taxonomy is absent or read_axes is missing. No local fallback.

If read_axes raises SchemaVersionError (spec not at _schema_version: 2), re-raises
as RegistryCorrupt — specs must be migrated before routing can proceed.

Calls analytic_module_status adapter (S8) to compute model_props.analytic_module_status.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Dict, List

from model_router.types import (
    AxisBundle,
    CandidateSpec,
    LoadedContext,
    RegistryCorrupt,
    SpecArchivedError,
    WS1NotMerged,
)
from model_router.stages.analytic_module_status import _resolve_analytic_module_status

# ---------------------------------------------------------------------------
# WS1 hard-gate: import taxonomy.read_axes (manager D9)
# ---------------------------------------------------------------------------

def _setup_taxonomy_path():
    """Add plugins/hep-ph-toolkit/skills/_shared to sys.path for taxonomy import."""
    _here = pathlib.Path(__file__).resolve()
    # parents[6] = plugins/
    _plugins = _here.parents[6]
    _shared = _plugins / "hep-ph-toolkit" / "skills" / "_shared"
    _shared_str = str(_shared)
    if _shared_str not in sys.path:
        sys.path.insert(0, _shared_str)


_setup_taxonomy_path()

try:
    from taxonomy import read_axes as _read_axes_fn  # type: ignore
    _read_axes_available = True
except ImportError:
    _read_axes_available = False
    _read_axes_fn = None

# Capture SchemaVersionError type if taxonomy is available; else None.
try:
    from taxonomy import SchemaVersionError as _SchemaVersionError  # type: ignore
except (ImportError, AttributeError):
    _SchemaVersionError = None


# ---------------------------------------------------------------------------
# Candidate extraction
# ---------------------------------------------------------------------------

def _extract_candidates(model_spec: dict, model_meta: dict) -> List[CandidateSpec]:
    """
    Extract DM candidates from model_spec.dm_phenomenology.candidates or
    model_meta.dm_phenomenology.candidates (registry wins over spec if both present).
    """
    # Prefer registry metadata (model_meta) as it carries the routing-relevant fields
    meta_pheno = model_meta.get("dm_phenomenology", {})
    spec_pheno = model_spec.get("dm_phenomenology", {})

    # Registry candidates take priority (they're explicitly curated for routing)
    raw_candidates = meta_pheno.get("candidates") or spec_pheno.get("candidates") or []

    candidates = []
    for c in raw_candidates:
        if isinstance(c, dict):
            candidates.append(CandidateSpec(
                name=c.get("name", "unknown"),
                field_type=c.get("field_type"),
                mediator_regime=c.get("mediator_regime"),
                uv_provenance=c.get("uv_provenance"),
            ))
    return candidates


# ---------------------------------------------------------------------------
# Model props computation
# ---------------------------------------------------------------------------

def _compute_model_props(ctx: LoadedContext) -> Dict[str, Any]:
    """
    Compute the derived model_props dict including analytic_module_status.
    Reads analytic_module from model_meta or model_spec backends block.
    """
    # analytic_module may be in model_meta or spec.backends
    analytic_module = (
        ctx.model_meta.get("analytic_module")
        or ctx.model_spec.get("backends", {}).get("analytic_module")
    )

    status = _resolve_analytic_module_status(
        model_id=ctx.model_id,
        analytic_module=analytic_module,
        registry=ctx.analytic_exceptions,
    )

    return {
        "analytic_module_status": status,
        "analytic_module": analytic_module,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stage_p1_validate_and_extract(ctx: LoadedContext) -> AxisBundle:
    """
    Stage P1: validate the ModelSpec and extract WS1 taxonomy axes.

    Raises:
        WS1NotMerged    — if taxonomy.read_axes is not importable (manager D9, exit 1).
        RegistryCorrupt — if spec is not at _schema_version: 2 (SchemaVersionError from
                          taxonomy). Specs must be migrated; no local fallback (D9).
        SpecArchivedError — if A8 axis == 'archived'.
    """
    if not _read_axes_available:
        raise WS1NotMerged(
            "plugins/hep-ph-toolkit/skills/_shared/taxonomy.py not present or "
            "read_axes not exported — WS1-S12 must merge before WS3 can run. exit 1"
        )

    diagnostics: Dict[str, Any] = {}

    # D9: call taxonomy.read_axes — no local fallback.
    # SchemaVersionError → RegistryCorrupt (spec must be migrated to v2).
    # Any other taxonomy exception propagates as-is (unexpected; let it surface).
    try:
        axis_report = _read_axes_fn(ctx.model_spec)
    except Exception as exc:
        if _SchemaVersionError is not None and isinstance(exc, _SchemaVersionError):
            raise RegistryCorrupt(
                f"Model spec for {ctx.model_id!r} is not at _schema_version: 2 — "
                f"migrate the spec before running /model-router. "
                f"(taxonomy.SchemaVersionError: {exc})"
            ) from exc
        raise

    # Extract candidates
    candidates = _extract_candidates(ctx.model_spec, ctx.model_meta)

    # Compute model props (analytic_module_status)
    model_props = _compute_model_props(ctx)

    # Build AxisBundle from taxonomy AxisReport (re-export from _shared/taxonomy.read_axes only)
    bundle = AxisBundle(
        A1=axis_report.a1,
        A2=str(axis_report.a2) if axis_report.a2 else None,
        A3=axis_report.a3 if isinstance(axis_report.a3, dict) else None,
        A4=axis_report.a4 if isinstance(axis_report.a4, dict) else None,
        A5=str(axis_report.a5) if axis_report.a5 else None,
        A6=str(axis_report.a6) if axis_report.a6 else None,
        A7=axis_report.a7 if isinstance(axis_report.a7, dict) else None,
        A8=axis_report.a8,
        candidates=candidates,
        model_props=model_props,
        diagnostics=diagnostics,
    )

    # Hard-halt on archived lifecycle (A8 == 'archived')
    if bundle.A8 == "archived":
        raise SpecArchivedError(
            f"Model {ctx.model_id!r} is archived (A8 == 'archived'). Routing halted. "
            "Use an active model or restore the spec to proceed."
        )

    return bundle
