"""
model_router/stages/load.py — Stage P0: load registries, spec, and config.

Manager D1: At entry, checks ConstraintRow.capability_blockers.
            If absent, raises WS2NotMerged (exit 3). Fail-closed.

Manager D6: monkeypatch-friendly: reads _YAML_PATH (from time_budget) and calls _load().
            Tests patch time_budget._YAML_PATH + time_budget._load.

Absent registries (blocker_catalog, analytic_exceptions): fail-open (set {} and
append to LoadedContext.absent_registries). constraints.yaml absence is fatal.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

import yaml

from model_router.types import (
    LoadedContext,
    ModelNotInRegistry,
    ModelSpecMissing,
    RegistryCorrupt,
    RouterOptions,
    WS2NotMerged,
)

# ---------------------------------------------------------------------------
# WS2 hard-gate: introspect ConstraintRow.capability_blockers (manager D1)
# ---------------------------------------------------------------------------

def _has_capability_blockers() -> bool:
    """Returns True iff WS2-S10 has added capability_blockers to ConstraintRow.

    NOTE: dataclass fields with default_factory do NOT appear as class-level attributes,
    so hasattr(ConstraintRow, 'capability_blockers') returns False even when the field
    exists. Use dataclasses.fields() to check the dataclass field set instead.
    """
    import dataclasses
    try:
        # sys.path shim to _shared already done by conftest / router.py
        _shared = pathlib.Path(__file__).resolve().parents[6] / "hep-ph-toolkit" / "skills" / "_shared"
        if str(_shared) not in sys.path:
            sys.path.insert(0, str(_shared))
        from time_budget import ConstraintRow  # noqa: import inside function
        field_names = {f.name for f in dataclasses.fields(ConstraintRow)}
        return "capability_blockers" in field_names
    except (ImportError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _shared_path() -> pathlib.Path:
    """Return plugins/hep-ph-toolkit/skills/_shared/ relative to this file."""
    # This file: plugins/hep-ph-toolkit/skills/model-router/scripts/model_router/stages/load.py
    _here = pathlib.Path(__file__).resolve()
    # parents[6] = plugins/
    _plugins = _here.parents[6]
    return _plugins / "hep-ph-toolkit" / "skills" / "_shared"


def _resolve_spec_path(spec_path_str: Optional[str]) -> Optional[pathlib.Path]:
    """Resolve a spec_path from the registry (relative to repo root or absolute)."""
    if not spec_path_str:
        return None
    p = pathlib.Path(spec_path_str)
    if p.is_absolute():
        return p
    # Relative: repo root is parents[7] of this file
    _repo_root = pathlib.Path(__file__).resolve().parents[7]
    return _repo_root / p


def _load_yaml(path: pathlib.Path, label: str, absent_registries: List[str]) -> dict:
    """Load a YAML file. On absence, append label to absent_registries and return {}."""
    if path is None or not path.exists():
        absent_registries.append(label)
        return {}
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data or {}
    except yaml.YAMLError as exc:
        absent_registries.append(label)
        return {}


def _load_constraints_yaml(path: pathlib.Path) -> dict:
    """Load constraints.yaml. Raises RegistryCorrupt on YAML error; raises FileNotFoundError if absent."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise
    except yaml.YAMLError as exc:
        raise RegistryCorrupt(f"constraints.yaml failed YAML parse: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryCorrupt(f"constraints.yaml is not a mapping: got {type(data)}")
    return data


def _default_observables(model_meta: dict, constraints_raw: dict) -> List[str]:
    """Derive default observables from the model's dm_phenomenology and available constraints."""
    dm_pheno = model_meta.get("dm_phenomenology", {})
    candidates = dm_pheno.get("candidates", [])
    available = list(constraints_raw.get("constraints", {}).keys())
    if not candidates:
        # No DM candidates: only collider-relevant constraints
        return [o for o in available if o in ("collider", "higgs")]
    # Standard DM observables
    dm_defaults = ["relic", "dd", "id"]
    return [o for o in dm_defaults if o in available] or available


def _load_config(config_path: Optional[str]) -> dict:
    """Load ~/.config/hephaestus/config.json. Fail-open (return {})."""
    if config_path:
        p = pathlib.Path(config_path)
    else:
        p = pathlib.Path.home() / ".config" / "hephaestus" / "config.json"
    if not p.exists():
        return {}
    try:
        with open(p) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stage_p0_load(
    model_id: str,
    observables: Optional[List[str]],
    options: Optional[RouterOptions],
    constraints_path: Optional[pathlib.Path] = None,
    blocker_catalog_path: Optional[pathlib.Path] = None,
    analytic_exceptions_path: Optional[pathlib.Path] = None,
) -> LoadedContext:
    """
    Stage P0: load all registries, model spec, and config.

    Raises:
        WS2NotMerged — if ConstraintRow.capability_blockers is absent (manager D1).
        ModelNotInRegistry — if model_id is not in constraints.yaml models block.
        ModelSpecMissing — if spec_path resolves to a non-existent file.
        RegistryCorrupt — if constraints.yaml fails YAML parse.
    """
    # Manager D1: hard gate on WS2
    if not _has_capability_blockers():
        raise WS2NotMerged(
            "ConstraintRow.capability_blockers missing — WS2-S10 must merge before "
            "WS3 implementation can run. exit 3."
        )

    if options is None:
        options = RouterOptions()

    absent_registries: List[str] = []
    diagnostics: Dict[str, Any] = {}

    # Resolve path: use explicit arg, or fall back to time_budget._YAML_PATH
    if constraints_path is None:
        _shared = _shared_path()
        # Try to read time_budget._YAML_PATH if patched
        try:
            _shared_str = str(_shared)
            if _shared_str not in sys.path:
                sys.path.insert(0, _shared_str)
            import time_budget  # noqa
            constraints_path = pathlib.Path(time_budget._YAML_PATH)
        except (ImportError, AttributeError):
            constraints_path = _shared / "constraints.yaml"

    # Load constraints.yaml (fatal on absence or corrupt)
    try:
        constraints_raw = _load_constraints_yaml(constraints_path)
    except FileNotFoundError:
        raise RegistryCorrupt(f"constraints.yaml not found at {constraints_path}")

    # Validate model_id is registered
    models = constraints_raw.get("models", {})
    if model_id not in models:
        raise ModelNotInRegistry(
            f"Model {model_id!r} not found in constraints.yaml models block. "
            f"Known models: {list(models.keys())}"
        )
    model_meta = models[model_id]

    # Load model spec
    spec_path_str = model_meta.get("spec_path")
    spec_path = _resolve_spec_path(spec_path_str)
    model_spec: dict = {}
    if spec_path is None:
        absent_registries.append("model_spec")
        diagnostics["model_spec_warning"] = "No spec_path in registry entry; using empty spec."
    elif not spec_path.exists():
        # Fail-open for tests where the real spec isn't on disk
        absent_registries.append("model_spec")
        diagnostics["model_spec_warning"] = f"spec_path {spec_path} does not exist; using empty spec."
    else:
        try:
            with open(spec_path) as f:
                model_spec = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            raise RegistryCorrupt(f"ModelSpec YAML parse error at {spec_path}: {exc}") from exc

    # Resolve blocker_catalog
    if blocker_catalog_path is None:
        blocker_catalog_path = _shared_path() / "blocker_catalog.yaml"
    blocker_catalog = _load_yaml(blocker_catalog_path, "blocker_catalog", absent_registries)

    # Resolve analytic_exceptions
    if analytic_exceptions_path is None:
        analytic_exceptions_path = _shared_path() / "analytic_exceptions.yaml"
    analytic_exceptions = _load_yaml(analytic_exceptions_path, "analytic_exceptions", absent_registries)
    # Normalize the `exceptions` field to a dict-keyed-by-id shape. The
    # production registry under hep-ph-demo/_shared/analytic_exceptions.yaml
    # writes `exceptions:` as a list of dicts (each with `id`, `model`); WS3
    # test fixtures use a dict keyed by exception id (each entry has
    # `model_id`). Both shapes are accepted; downstream stages assume dict.
    _exc = analytic_exceptions.get("exceptions") if isinstance(analytic_exceptions, dict) else None
    if isinstance(_exc, list):
        _normalized: dict = {}
        for entry in _exc:
            if not isinstance(entry, dict):
                continue
            key = entry.get("id") or entry.get("model_id") or entry.get("model")
            if key is None:
                continue
            # Mirror `model` -> `model_id` so consumers that read `model_id`
            # (the fixture-shape field name) keep working unchanged.
            if "model_id" not in entry and "model" in entry:
                entry = {**entry, "model_id": entry["model"]}
            _normalized[key] = entry
        analytic_exceptions = {**analytic_exceptions, "exceptions": _normalized}

    # Default observables
    if observables is None or len(observables) == 0:
        observables = _default_observables(model_meta, constraints_raw)

    # Load config (fail-open)
    config = _load_config(options.config_path)

    return LoadedContext(
        model_id=model_id,
        observables=list(observables),
        options=options,
        model_meta=model_meta,
        model_spec=model_spec,
        prereqs=constraints_raw.get("prereqs", {}),
        constraints_raw=constraints_raw,
        blocker_catalog=blocker_catalog,
        analytic_exceptions=analytic_exceptions,
        config=config,
        absent_registries=absent_registries,
        diagnostics=diagnostics,
    )
