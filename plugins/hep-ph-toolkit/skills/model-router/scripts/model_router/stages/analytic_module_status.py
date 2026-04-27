"""
model_router/stages/analytic_module_status.py — P1 adapter: analytic_module_status.

Manager D4: stub detection uses getattr(module, "STUB", False) — no AST walk.

Six-value closed enum per synthesis Decision 6:
  "registered_active" — module resolves AND registry entry exists with status: active
  "deprecated"        — module resolves AND registry entry exists with status: deprecated
  "retired"           — module resolves AND registry entry exists with status: retired
  "unregistered"      — module resolves AND no registry entry exists
  "stub"              — module resolves AND getattr(module, "STUB", False) is True
  "missing"           — module path does not resolve (None or import fails)
"""
from __future__ import annotations

import importlib
import pathlib
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Module resolution
# ---------------------------------------------------------------------------

def _analytic_models_root() -> pathlib.Path:
    """Return plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/."""
    _here = pathlib.Path(__file__).resolve()
    # parents[0] = stages/, [1] = model_router/, [2] = scripts/,
    # [3] = model-router/, [4] = skills/, [5] = workflow/, [6] = plugins/
    _plugins = _here.parents[6]
    return _plugins / "hep-ph-toolkit" / "skills" / "spheno-build" / "scripts" / "analytic_models"


def _resolve_module_path(analytic_module: Optional[str]) -> Optional[pathlib.Path]:
    """
    Map a dotted analytic_module string (e.g. 'analytic_models.dark_su3')
    to a filesystem path under the analytic_models root.
    Returns None if analytic_module is None.
    """
    if not analytic_module:
        return None
    root = _analytic_models_root()
    # Strip leading 'analytic_models.' prefix and convert dots to path separators
    module_part = analytic_module
    if module_part.startswith("analytic_models."):
        module_part = module_part[len("analytic_models."):]
    # Handle nested dotted paths
    parts = module_part.split(".")
    candidate = root / pathlib.Path(*parts).with_suffix(".py")
    return candidate


def _import_module(analytic_module: Optional[str]):
    """
    Import the analytic_models.* module.
    Returns the module object or None on ImportError.
    """
    if not analytic_module:
        return None
    _root_str = str(_analytic_models_root().parent)
    if _root_str not in sys.path:
        sys.path.insert(0, _root_str)
    try:
        return importlib.import_module(analytic_module)
    except ImportError:
        return None


def _is_stub_module(module) -> bool:
    """Return True iff the module declares STUB = True (manager D4)."""
    if module is None:
        return False
    return bool(getattr(module, "STUB", False))


def _find_registry_entry(model_id: str, registry: dict) -> Optional[dict]:
    """Return the registry entry for model_id, or None if not found.

    The analytic_exceptions registry has two known shapes in the wild:
      (a) dict keyed by exception id: ``exceptions: {dsu3-002: {model_id: dark-su3, ...}}``
          — used by WS3 test fixtures.
      (b) list of dicts: ``exceptions: [{id: dsu3-002, model: dark-su3, ...}, ...]``
          — used by the production registry under
          ``plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml``.

    Match against either ``model_id`` or ``model`` key for cross-shape compat.
    Returns the first matching entry (the registry is expected to have at most
    one active entry per model — if WS4 ever ships multiple, the loader should
    pre-filter by status).
    """
    exceptions = registry.get("exceptions", {})
    if isinstance(exceptions, dict):
        # Shape (a): dict keyed by exception id. Direct key match (legacy
        # fixture path), then fall back to scanning entries for model_id/model.
        if model_id in exceptions:
            return exceptions[model_id]
        for entry in exceptions.values():
            if not isinstance(entry, dict):
                continue
            if entry.get("model_id") == model_id or entry.get("model") == model_id:
                return entry
        return None
    if isinstance(exceptions, list):
        # Shape (b): list of dicts. Match by model_id or model field.
        for entry in exceptions:
            if not isinstance(entry, dict):
                continue
            if entry.get("model_id") == model_id or entry.get("model") == model_id:
                return entry
        return None
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _resolve_analytic_module_status(
    model_id: str,
    analytic_module: Optional[str],
    registry: dict,
) -> str:
    """
    Resolve the analytic_module_status for a model (six-value closed enum).

    Decision table (synthesis Decision 6, manager D4):
    1. analytic_module is None/empty → "missing"
    2. Module import fails → "missing"
    3. Module imports AND getattr(module, "STUB", False) → "stub"
    4. Module imports AND registry entry exists with status == "active" → "registered_active"
    5. Module imports AND registry entry exists with status == "deprecated" → "deprecated"
    6. Module imports AND registry entry exists with status == "retired" → "retired"
    7. Module imports AND no registry entry → "unregistered"
    """
    if not analytic_module:
        return "missing"

    module = _import_module(analytic_module)
    if module is None:
        return "missing"

    # Stub check (manager D4) — before registry lookup so a stub that accidentally
    # has a stale registry entry still returns "stub"
    if _is_stub_module(module):
        return "stub"

    # Registry lookup
    entry = _find_registry_entry(model_id, registry)
    if entry is None:
        return "unregistered"

    status = entry.get("status", "active")
    if status == "active":
        return "registered_active"
    elif status == "deprecated":
        return "deprecated"
    elif status == "retired":
        return "retired"
    else:
        # Unknown registry status; treat as unregistered
        return "unregistered"
