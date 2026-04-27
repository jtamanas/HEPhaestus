"""
model_router/stages/detect_exception.py — Stage P2: WS4 exception detector wrapper.

Tries to import and call WS4's detect() function.
On ImportError: sets detector_unavailable=True diagnostic; returns CLEAR stub verdict.
On detector runtime exception: raises DetectorInternalError.

WS4 public API (per ws4_plan_final.md D9 + S3b):
  detect(spec: dict, *, signal_inputs: SignalInputs | None = None,
         registry: RegistryView | None = None) -> Verdict

The analytic_module_status from P1 is passed via signal_inputs.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Optional

from model_router.types import (
    AxisBundle,
    DetectorInternalError,
    ExceptionVerdict,
    LoadedContext,
    SignalInputs,
)

# ---------------------------------------------------------------------------
# WS4 availability flag (module-level; monkeypatch-friendly for tests)
# ---------------------------------------------------------------------------

def _setup_ws4_path():
    """Add analytic-exception-detector/scripts to sys.path for WS4 import."""
    _here = pathlib.Path(__file__).resolve()
    # parents[6] = plugins/
    _plugins = _here.parents[6]
    _ws4_scripts = _plugins / "hep-ph-toolkit" / "skills" / "analytic-exception-detector" / "scripts"
    _ws4_str = str(_ws4_scripts)
    if _ws4_str not in sys.path:
        sys.path.insert(0, _ws4_str)


_setup_ws4_path()

try:
    from detect_analytic_exception import detect as _ws4_detect  # type: ignore
    _WS4_DETECTOR_AVAILABLE = True
except ImportError:
    _WS4_DETECTOR_AVAILABLE = False
    _ws4_detect = None


# ---------------------------------------------------------------------------
# Stub verdict builder
# ---------------------------------------------------------------------------

def _build_exception_verdict(verdict: str, rationale: str = "", **kwargs) -> ExceptionVerdict:
    """Build an ExceptionVerdict compatible with both the WS4 Verdict and the local stub.

    WS4 Verdict uses 'reason_human' for the rationale string.
    The local stub class uses 'rationale'.
    This builder dispatches to the correct field name.
    """
    import dataclasses
    try:
        field_names = {f.name for f in dataclasses.fields(ExceptionVerdict)}
    except TypeError:
        field_names = set()

    if "reason_human" in field_names:
        kwargs["reason_human"] = rationale
    elif "rationale" in field_names:
        kwargs["rationale"] = rationale

    return ExceptionVerdict(verdict=verdict, **kwargs)


def _build_clear_stub(detector_unavailable: bool = False) -> ExceptionVerdict:
    """Return a CLEAR stub ExceptionVerdict."""
    v = _build_exception_verdict(
        verdict="CLEAR",
        rationale="No analytic exception detected.",
        exception_id=None,
        disclosure_required=False,
    )
    if hasattr(v, "detector_unavailable"):
        v.detector_unavailable = detector_unavailable
    return v


def _build_halt_for_signoff_stub() -> ExceptionVerdict:
    """Return a HALT_FOR_SIGNOFF stub for the stub-module path."""
    return _build_exception_verdict(
        verdict="HALT_FOR_SIGNOFF",
        rationale="analytic_module_status == 'stub'; sign-off required before proceeding.",
        exception_id=None,
        disclosure_required=False,
    )


# ---------------------------------------------------------------------------
# Signal inputs builder
# ---------------------------------------------------------------------------

def _build_signal_inputs(axes: AxisBundle, ctx: LoadedContext) -> SignalInputs:
    """Build WS4 SignalInputs from the P1 AxisBundle.

    WS4's real SignalInputs dataclass declares only four fields (see
    plugins/hep-ph-toolkit/skills/analytic-exception-detector/scripts/detect_analytic_exception.py:76-82):
        gauge_extension_class, dm_candidate_uv_provenance, stabilizing_symmetry, raw_modelspec.

    The router's analytic_module_status (P1 adapter output) is NOT a WS4 kwarg.
    To keep it available to downstream code without violating the WS4 contract,
    stash it in raw_modelspec under the sentinel key "__analytic_module_status".
    The stub short-circuit `_apply_stub_short_circuit` already operates on the
    AxisBundle directly, so it does not need this stash; the field is preserved
    here only for diagnostic / extension use.
    """
    a4 = axes.A4 or {}
    raw_spec = dict(ctx.model_spec) if isinstance(ctx.model_spec, dict) else {}
    raw_spec["__analytic_module_status"] = axes.model_props.get(
        "analytic_module_status", "missing"
    )
    return SignalInputs(
        gauge_extension_class=axes.A1,
        dm_candidate_uv_provenance=(
            axes.candidates[0].uv_provenance if axes.candidates else None
        ),
        stabilizing_symmetry=a4.get("stabilizing_symmetry") if isinstance(a4, dict) else None,
        raw_modelspec=raw_spec,
    )


# ---------------------------------------------------------------------------
# Short-circuit: stub analytic module → HALT_FOR_SIGNOFF (synthesis Decision 6)
# ---------------------------------------------------------------------------

def _apply_stub_short_circuit(axes: AxisBundle, ctx: LoadedContext) -> Optional[ExceptionVerdict]:
    """
    If analytic_module_status == 'stub', short-circuit to HALT_FOR_SIGNOFF.
    This prevents a stale/empty module from being treated as ROUTE_TO_ANALYTIC.
    Per synthesis Decision 6 + manager D4: SC_ANALYTIC_MODULE_WIRED returns False
    for stub status; WS4 truth table maps this to HALT_FOR_SIGNOFF.
    """
    status = axes.model_props.get("analytic_module_status", "missing")
    if status == "stub":
        ctx.diagnostics["analytic_stub_short_circuit"] = True
        return _build_halt_for_signoff_stub()
    return None


def _apply_analytic_active_detection(axes: AxisBundle, ctx: LoadedContext) -> Optional[ExceptionVerdict]:
    """
    If analytic_module_status == 'registered_active', check if the analytic_exceptions
    registry has a matching entry (keyed by exception_id, model_id field inside entry).
    If found active, return ROUTE_TO_ANALYTIC.
    This is the WS3-internal path for when WS4 detector is unavailable.
    """
    status = axes.model_props.get("analytic_module_status", "missing")
    if status not in ("registered_active", "deprecated"):
        return None
    # Search registry entries by model_id field (entries are keyed by exception_id)
    exceptions = ctx.analytic_exceptions.get("exceptions", {})
    matched_exception_id = None
    matched_entry = None
    for exc_id, entry in exceptions.items():
        if entry.get("model_id") == ctx.model_id:
            if entry.get("status", "active") in ("active", "deprecated"):
                matched_exception_id = exc_id
                matched_entry = entry
                break
    if matched_exception_id:
        return _build_exception_verdict(
            verdict="ROUTE_TO_ANALYTIC",
            rationale=f"Active analytic exception {matched_exception_id!r} registered for {ctx.model_id}.",
            exception_id=matched_exception_id,
            disclosure_required=True,
        )
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stage_p2_detect_exception(axes: AxisBundle, ctx: LoadedContext) -> ExceptionVerdict:
    """
    Stage P2: invoke WS4 exception detector.

    Returns:
        ExceptionVerdict with verdict in {CLEAR, ROUTE_TO_ANALYTIC, HALT_FOR_SIGNOFF, HARD_HALT}.

    Raises:
        DetectorInternalError — if WS4 detect() raises an unexpected exception.
    """
    # Short-circuit 1: stub module → HALT_FOR_SIGNOFF (synthesis D6; WS4-independent)
    stub_verdict = _apply_stub_short_circuit(axes, ctx)
    if stub_verdict is not None:
        return stub_verdict

    # If WS4 is not available, apply WS3-internal detection logic
    if not _WS4_DETECTOR_AVAILABLE:
        ctx.diagnostics["detector_unavailable"] = True

        # WS3-internal ROUTE_TO_ANALYTIC detection (registered_active with registry entry)
        analytic_verdict = _apply_analytic_active_detection(axes, ctx)
        if analytic_verdict is not None:
            return analytic_verdict

        # Default: CLEAR stub
        return _build_clear_stub(detector_unavailable=True)

    # WS4 available: call detect()
    signal_inputs = _build_signal_inputs(axes, ctx)

    try:
        verdict = _ws4_detect(ctx.model_spec, signal_inputs=signal_inputs)
    except Exception as exc:
        raise DetectorInternalError(
            f"WS4 detect() raised an unexpected exception: {exc}"
        ) from exc

    return verdict
