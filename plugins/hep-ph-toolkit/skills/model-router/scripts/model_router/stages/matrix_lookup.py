"""
model_router/stages/matrix_lookup.py — Stage P3: capability matrix lookup wrapper.

Per WS3 plan §S10:
  - Wraps WS2's `from matrix_lookup import load_capability_matrix` /
    `CapabilityMatrix` with a manager-D2 cross-plugin dep check.
  - Translates the WS3 `AxisBundle` into the WS2 axes-bundle dict shape
    expected by `CapabilityMatrix.lookup_blockers`.
  - Folds per-prereq blocker verdicts into per-observable
    `PrereqFold` lists (output `MatrixVerdicts`).

Manager D2: ImportError on the hep-ph-demo `matrix_lookup` module raises
`WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO` (exit code 3) with a remediation
message containing `"install hep-ph-demo plugin"`.

The router does NOT compute observables (per `feedback_augment_not_replace`).
This module only translates inputs, calls WS2 APIs, and reshapes outputs.
"""
from __future__ import annotations

import dataclasses
import pathlib
import sys
from typing import Any, Dict, List, Optional

from model_router.types import (
    AxisBundle,
    ExceptionVerdict,
    LoadedContext,
    MatrixVerdicts,
    PrereqFold,
    WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO,
)

# ---------------------------------------------------------------------------
# Cross-plugin dep check (manager D2)
# ---------------------------------------------------------------------------

def _setup_hep_ph_demo_path() -> None:
    """Insert plugins/hep-ph-toolkit/skills/_shared into sys.path."""
    _here = pathlib.Path(__file__).resolve()
    # parents: stages/ -> model_router/ -> scripts/ -> model-router/ -> skills/ -> workflow/ -> plugins/
    _plugins = _here.parents[6]
    _shared = _plugins / "hep-ph-toolkit" / "skills" / "_shared"
    if str(_shared) not in sys.path:
        sys.path.insert(0, str(_shared))


def _load_matrix(constraints_path: Optional[pathlib.Path] = None,
                 catalog_path: Optional[pathlib.Path] = None,
                 registry_path: Optional[pathlib.Path] = None):
    """Import and call hep-ph-demo's load_capability_matrix; raise the WS3
    cross-plugin error on ImportError (manager D2).
    """
    _setup_hep_ph_demo_path()
    try:
        from matrix_lookup import load_capability_matrix  # type: ignore
    except ImportError as exc:
        raise WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO(
            "plugins/hep-ph-toolkit/skills/_shared/matrix_lookup.py not importable; "
            "install hep-ph-demo plugin"
        ) from exc
    return load_capability_matrix(
        constraints_path=constraints_path,
        catalog_path=catalog_path,
        registry_path=registry_path,
    )


# ---------------------------------------------------------------------------
# AxisBundle -> WS2 axes-bundle dict translation
# ---------------------------------------------------------------------------

def _axes_to_bundle_dict(axes: AxisBundle, ctx: LoadedContext) -> Dict[str, Any]:
    """Translate WS3 AxisBundle into the WS2 axes-bundle dict shape.

    WS2 CapabilityMatrix.lookup_blockers expects:
        {
          "axes": {"A1": ..., "A2": ..., ..., "A8": ...},
          "candidates": [{"name": ..., "field_type": ..., "uv_provenance": ...}, ...],
          "lagrangian": {...},        # from spec
          "model_runtime": {"analytic_module_status": ..., ...},
        }

    No physics inference: pure structural copy.
    """
    axes_dict: Dict[str, Any] = {}
    for axis_id in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"):
        axes_dict[axis_id] = getattr(axes, axis_id, None)

    candidates = []
    for cand in (axes.candidates or []):
        # CandidateSpec is a dataclass; convert to dict for WS2 consumption.
        if dataclasses.is_dataclass(cand):
            candidates.append(dataclasses.asdict(cand))
        elif isinstance(cand, dict):
            candidates.append(cand)
        else:
            candidates.append({"name": str(cand)})

    # Pass through lagrangian section verbatim from spec (WS2 reads
    # lagrangian.* axis paths in some rules).
    spec = ctx.model_spec or {}
    lagrangian = spec.get("lagrangian", {}) if isinstance(spec, dict) else {}

    model_runtime: Dict[str, Any] = {}
    model_runtime["analytic_module_status"] = (axes.model_props or {}).get(
        "analytic_module_status", "missing"
    )

    return {
        "axes": axes_dict,
        "candidates": candidates,
        "lagrangian": lagrangian,
        "model_runtime": model_runtime,
    }


# ---------------------------------------------------------------------------
# WS2 BlockerVerdict / ToolLevelVerdict -> WS3 PrereqFold reshape
# ---------------------------------------------------------------------------

def _build_prereq_fold(
    prereq_id: str,
    bvlist: list,
    tool_level,
    observable: str,
) -> PrereqFold:
    """Construct one WS3 PrereqFold from WS2 (BlockerVerdict list, ToolLevelVerdict)
    for a single observable.
    """
    # Collect blocker codes + classes from the BlockerVerdict list, deduping
    # while preserving insertion order.
    seen_codes: List[str] = []
    seen_classes: List[str] = []
    seen_caveats: List[str] = []
    for bv in bvlist:
        code = getattr(bv, "blocker", None)
        cls = getattr(bv, "blocker_class", None)
        cav = getattr(bv, "caveat", None)
        if code and code not in seen_codes:
            seen_codes.append(code)
        if cls and cls not in seen_classes:
            seen_classes.append(cls)
        if cav and cav not in seen_caveats:
            seen_caveats.append(cav)

    role_for_observable = "none"
    priority_tiebreak = 100
    overall = "not_applicable"
    if tool_level is not None:
        roles = getattr(tool_level, "role", {}) or {}
        role_for_observable = roles.get(observable, "none")
        priority_tiebreak = getattr(tool_level, "priority_tiebreak", 100)
        overall = getattr(tool_level, "overall_verdict", "not_applicable")

    no_coverage = (overall == "no_coverage")
    if no_coverage:
        # Surface the spec-authoring-gap blocker code per plan S10.
        if "MATRIX_COVERAGE_GAP" not in seen_codes:
            seen_codes.append("MATRIX_COVERAGE_GAP")
        if "spec-authoring-gap" not in seen_classes:
            seen_classes.append("spec-authoring-gap")

    return PrereqFold(
        prereq_id=prereq_id,
        overall_verdict=overall if not no_coverage else "blocked",
        blockers=seen_codes,
        blocker_classes=seen_classes,
        caveats=seen_caveats,
        role_for_observable=role_for_observable,
        priority_tiebreak=priority_tiebreak,
        runtime_install_required=False,
        no_coverage=no_coverage,
    )


# ---------------------------------------------------------------------------
# Public API — Stage P3
# ---------------------------------------------------------------------------

def stage_p3_matrix_lookup(
    axes: AxisBundle,
    ctx: LoadedContext,
    exception_verdict: Optional[ExceptionVerdict] = None,
) -> MatrixVerdicts:
    """Stage P3: capability-matrix lookup for the model's axes across observables.

    Returns:
        MatrixVerdicts with `by_observable: {observable: [PrereqFold, ...]}`.

    Raises:
        WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO when hep-ph-demo's matrix_lookup
        module is not importable (manager D2).
    """
    # Resolve constraints/catalog paths from LoadedContext when available;
    # fall back to library defaults otherwise.
    constraints_path = None
    catalog_path = None
    registry_path = None

    # Allow explicit override via diagnostics for tests; else use defaults.
    cfg_paths = (ctx.diagnostics or {}).get("matrix_paths", {}) if ctx else {}
    if isinstance(cfg_paths, dict):
        if cfg_paths.get("constraints"):
            constraints_path = pathlib.Path(cfg_paths["constraints"])
        if cfg_paths.get("catalog"):
            catalog_path = pathlib.Path(cfg_paths["catalog"])
        if cfg_paths.get("registry"):
            registry_path = pathlib.Path(cfg_paths["registry"])

    matrix = _load_matrix(
        constraints_path=constraints_path,
        catalog_path=catalog_path,
        registry_path=registry_path,
    )

    bundle = _axes_to_bundle_dict(axes, ctx)
    verdicts_by_prereq = matrix.lookup_blockers(bundle)
    fold_by_prereq = matrix.fold(verdicts_by_prereq)

    by_observable: Dict[str, List[PrereqFold]] = {}
    diagnostics: Dict[str, Any] = {}

    for observable in (ctx.observables or []):
        folds: List[PrereqFold] = []
        for prereq_id in fold_by_prereq.keys():
            bvlist = verdicts_by_prereq.get(prereq_id, [])
            tool_level = fold_by_prereq.get(prereq_id)
            try:
                folds.append(
                    _build_prereq_fold(prereq_id, bvlist, tool_level, observable)
                )
            except Exception as exc:  # pragma: no cover — single-prereq fail-open per S10
                diagnostics.setdefault(
                    "single_prereq_lookup_failures", []
                ).append({"prereq_id": prereq_id, "error": str(exc)})
        by_observable[observable] = folds

    return MatrixVerdicts(
        by_observable=by_observable,
        diagnostics=diagnostics,
    )
