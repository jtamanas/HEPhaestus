#!/usr/bin/env python3
"""check_prereqs.py — WS-4 prerequisite guard for /dark-matter-constraints.

Usage:
    python <path>/scripts/check_prereqs.py --config <path> --model <name> [--manifest <path>]

Outputs a single-line JSON to stdout:
    {"status": "ok"|"blocked", "blockers": [...], "checked": [...]}

Exit codes:
    0 — status is "ok" (all required paths exist and prerequisites met)
    1 — status is "blocked" (helper ran fine; contract failed)
    2 — internal error (manifest unparseable, config unreadable)

Model-agnosticism: checks only file/dir existence. SLHA_MISSING_HINT is
informational; LLM decides per model class whether to honor it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover — pyyaml is part of the dev env
    yaml = None  # noqa: F841 — fallback handled in _load_model_spec

# Default manifest: contracts/router_contract.json relative to this helper
_DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "contracts" / "router_contract.json"


def _load_json(path: str | Path) -> dict:
    """Load and parse a JSON file; raises on failure."""
    with open(path) as fh:
        return json.load(fh)


def _load_config_file(path: str | Path) -> dict:
    """Load a config file, accepting either JSON or YAML.

    The SKILL.md documents configs under a "## Config (YAML)" heading, and the
    live playtest fixtures ship `.yaml` configs, yet historically this helper
    only accepted JSON. We try JSON first (a strict superset-friendly fast path
    that also keeps existing `.json` fixtures byte-identical) and fall back to
    `yaml.safe_load` on a JSON parse error.

    Raises:
        OSError            — file unreadable (propagated to the exit-2 path).
        json.JSONDecodeError — content is neither valid JSON nor a YAML mapping
                               (normalised so the caller's existing except clause
                               reports PREREQ_HELPER_INTERNAL / exit 2).
    """
    with open(path) as fh:
        text = fh.read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:  # pragma: no cover — pyyaml is part of the dev env
            raise
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise json.JSONDecodeError(f"config is neither JSON nor YAML: {exc}", text, 0)
    if not isinstance(data, dict):
        raise json.JSONDecodeError("config did not parse to a mapping/object", text, 0)
    return data


def _blocker(code: str, message: str, fixit_skill: str | None = None) -> dict:
    return {"code": code, "message": message, "fixit_skill": fixit_skill}


def _notice(code: str, message: str) -> dict:
    """Recoverable, informational notice. Mirrors _blocker shape but does not flip status."""
    return {"code": code, "message": message, "fixit_skill": None}


def _load_model_spec(spec_path: str | Path) -> dict:
    """Load a ModelSpec YAML (used to detect analytic-only branch eligibility).

    Returns {} on any failure (missing file, parse error, missing pyyaml).
    The caller treats {} as "no analytic-only signal" — fail-closed: an
    unreadable spec must NOT silently demote UFO_MISSING.
    """
    if yaml is None:
        return {}
    try:
        with open(spec_path) as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


_CONSTRAINTS_YAML = (
    Path(__file__).resolve().parents[4]
    / "hep-ph-toolkit" / "skills" / "_shared" / "constraints.yaml"
)


def _model_is_multi_component(model: str) -> bool:
    """Read `models.<model>.multi_component` from `_shared/constraints.yaml`.

    This file is the canonical source for the multi_component flag (per
    /dark-matter-constraints SKILL.md Step 2 analytic-only branch wording).
    Returns False on any read/parse failure — fail-closed.
    """
    if yaml is None or not _CONSTRAINTS_YAML.is_file():
        return False
    try:
        with open(_CONSTRAINTS_YAML) as fh:
            data = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return False
    models = data.get("models", {}) if isinstance(data, dict) else {}
    entry = models.get(model, {}) if isinstance(models, dict) else {}
    return bool(entry.get("multi_component", False))


def _is_analytic_only_branch(model: str, model_cfg: dict) -> tuple[bool, str | None]:
    """Determine whether the analytic-only branch fires for this model.

    Conditions (mirrors `dark-matter-constraints` SKILL.md Step 2 branch):
      1. `_shared/constraints.yaml` `models.<model>.multi_component` is true.
      2. ModelSpec at `config.models[<model>].spec_yaml` has
         `backends.spectrum == "analytic"`.

    Returns (eligible, spec_yaml_path_or_None). The path is returned so the
    caller can record it in `checked[]` regardless of outcome.
    """
    spec_yaml = model_cfg.get("spec_yaml")
    if not spec_yaml:
        return False, None
    spec = _load_model_spec(spec_yaml)
    if not spec:
        return False, str(spec_yaml)
    backends = spec.get("backends", {})
    spectrum = backends.get("spectrum") if isinstance(backends, dict) else None
    multi = _model_is_multi_component(model)
    return (multi and spectrum == "analytic"), str(spec_yaml)


def _dig(obj: object, dotted: str) -> object:
    """Navigate a dotted path into nested dicts; return None if any level absent."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _spec_field_values(spec: dict, field: str) -> list:
    """Resolve a manifest condition ``spec_field`` to a list of concrete values.

    Supports exactly the two shapes the manifest uses:
      * a dotted path — ``cosmology.kind`` → the value at that path
      * a single ``[?]`` wildcard — ``candidates[?].mediator_regime`` → the
        sub-value for *every* element of the (top-level) list.

    An absent field (or absent container) resolves to an empty list, so a
    conditional key guarded by it is treated as inactive (not required). This
    is the desired behaviour: a plain spec that never mentions ``cosmology`` or
    ``candidates`` must not be forced to supply class/looptools paths.
    """
    if "[?]" in field:
        before, after = field.split("[?]", 1)
        before = before.rstrip(".")
        container = _dig(spec, before) if before else spec
        if not isinstance(container, list):
            return []
        rest = after.lstrip(".")
        out = []
        for item in container:
            val = _dig(item, rest) if rest else item
            if val is not None:
                out.append(val)
        return out
    val = _dig(spec, field)
    return [] if val is None else [val]


def _condition_active(spec: dict, condition: dict) -> bool:
    """Decide whether a conditional config key must be enforced for ``spec``.

    Implements only the operators the manifest declares (``in`` / ``not_in``):
      * ``{"spec_field": F, "in": [...]}``     → active if any value ∈ list
      * ``{"spec_field": F, "not_in": [...]}`` → active if any value ∉ list

    An absent field yields no values, so both operators evaluate to inactive —
    the key is skipped. Malformed/opaque conditions fall through to "active"
    (enforced) rather than silently dropping a real gate.
    """
    if not isinstance(condition, dict):
        return True
    field = condition.get("spec_field")
    if not field:
        return True
    values = _spec_field_values(spec, field)
    if "in" in condition:
        allowed = condition["in"]
        return any(v in allowed for v in values)
    if "not_in" in condition:
        excluded = condition["not_in"]
        return any(v not in excluded for v in values)
    return True


def check_prereqs(
    config_path: str | Path,
    model: str,
    manifest_path: str | Path | None = None,
) -> tuple[dict, int]:
    """
    Check prerequisites for the dark-matter-constraints router.

    Returns (result_dict, exit_code) where exit_code is 0, 1, or 2.
    result_dict is the JSON-serialisable output payload.
    """
    manifest_path = Path(manifest_path) if manifest_path else _DEFAULT_MANIFEST

    # --- load manifest ---
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        err = {"error": str(exc), "code": "PREREQ_HELPER_INTERNAL"}
        return err, 2

    # --- load config (JSON, or YAML fallback) ---
    try:
        config = _load_config_file(config_path)
    except (OSError, json.JSONDecodeError) as exc:
        err = {"error": str(exc), "code": "PREREQ_HELPER_INTERNAL"}
        return err, 2

    config_keys = manifest.get("config_keys", [])
    blockers: list[dict] = []
    checked: list[dict] = []

    # Resolve the model's ModelSpec once, up front, so config-key `condition`
    # fields can be evaluated against it. Absent/unreadable spec → {} → every
    # conditional key is treated as inactive (skipped), which is the safe
    # non-blocking behaviour for the two recoverable conditional keys
    # (class_path / looptools_path).
    models_section = config.get("models", {})
    model_cfg = models_section.get(model, {}) if isinstance(models_section, dict) else {}
    _spec_yaml = model_cfg.get("spec_yaml")
    model_spec = _load_model_spec(_spec_yaml) if _spec_yaml else {}

    # Map well-known config key → blocker code + fixit skill
    _KEY_META = {
        "config.maddm_path": ("MADDM_MISSING", "_shared/installs/maddm"),
        "config.micromegas_path": ("MICROMEGAS_MISSING", "_shared/installs/micromegas"),
        "config.drake_path": ("DRAKE_PATH_UNSET", "_shared/installs/drake"),
    }

    for entry in config_keys:
        key = entry.get("key", "")
        # Conditional keys (class_path / looptools_path) carry a `condition`.
        # Skip the key entirely when its condition does not match this spec —
        # a standard-thermal, non-loop spec must NOT require these paths.
        condition = entry.get("condition")
        if condition is not None and not _condition_active(model_spec, condition):
            continue
        # Strip "config." prefix to get the field name in config dict
        field = key.removeprefix("config.")
        value = config.get(field)
        entry_type = entry.get("type", "")

        exists = False
        if entry_type == "path_or_bool":
            if value is None:
                exists = False
                path_str = None
            elif isinstance(value, bool):
                exists = bool(value)
                path_str = None
            else:
                path_str = str(value)
                exists = os.path.exists(path_str)
        else:
            # Unknown type — treat presence of a non-None value as "exists"
            exists = value is not None
            path_str = str(value) if value is not None else None

        checked.append({"key": key, "exists": exists, "path": path_str})

        if not exists:
            code, fixit = _KEY_META.get(key, (f"{field.upper()}_MISSING", None))
            blockers.append(_blocker(
                code,
                f"Prerequisite not met: {key} is absent or path does not exist.",
                fixit,
            ))

    # --- UFO path check (model-specific, but always required) ---
    # (models_section / model_cfg resolved up front for condition evaluation.)

    # Detect analytic-only branch (multi_component + backends.spectrum=analytic).
    # When it fires we demote UFO_MISSING from fatal to a recoverable
    # ANALYTIC_BACKEND_PATH notice, mirroring the SKILL.md Step 2 branch — the
    # router will skip /maddm and consume <spheno_run>/diagnostics.json directly,
    # so a missing UFO is not a real prereq failure.
    analytic_branch, spec_yaml_path = _is_analytic_only_branch(model, model_cfg)
    if spec_yaml_path is not None:
        checked.append({
            "key": f"config.models[{model}].spec_yaml",
            "exists": os.path.exists(spec_yaml_path),
            "path": spec_yaml_path,
        })

    ufo_path = model_cfg.get("ufo_path")
    if not ufo_path or not os.path.exists(str(ufo_path)):
        if analytic_branch:
            # Demoted: not a blocker. Record an informational notice instead.
            blockers.append(_notice(
                "ANALYTIC_BACKEND_PATH",
                f"config.models[{model!r}].ufo_path absent, but analytic-only "
                "branch is eligible (multi_component=true AND "
                "backends.spectrum=='analytic'). MadDM will be skipped; relic "
                "numbers come from the analytic backend's diagnostics.json. "
                "UFO is not required on this branch.",
            ))
        else:
            blockers.append(_blocker(
                "UFO_MISSING",
                f"config.models[{model!r}].ufo_path is absent or path does not exist.",
                "/sarah-build",
            ))
        ufo_exists = False
    else:
        ufo_exists = True
    checked.append({"key": f"config.models[{model}].ufo_path", "exists": ufo_exists, "path": str(ufo_path) if ufo_path else None})

    # --- SLHA hint (informational only — LLM decides per model class) ---
    latest_slha = model_cfg.get("latest_slha")
    if latest_slha and not os.path.exists(str(latest_slha)):
        blockers.append(_blocker(
            "SLHA_MISSING_HINT",
            f"config.models[{model!r}].latest_slha is set but file does not exist. "
            "For simplified-model UFOs this is not fatal; for MSSM-class models it may be. "
            "LLM adjudicates.",
            "/spheno-build",
        ))

    # Determine overall status.  SLHA_MISSING_HINT and ANALYTIC_BACKEND_PATH do
    # NOT flip status to blocked — they are informational notices. Only real
    # blockers (codes not in this allow-list) do.
    _RECOVERABLE = {"SLHA_MISSING_HINT", "ANALYTIC_BACKEND_PATH"}
    hard_blockers = [b for b in blockers if b["code"] not in _RECOVERABLE]
    status = "ok" if not hard_blockers else "blocked"

    # Split blockers vs notices: callers (LLM and tests) want a clear
    # structural separation for the analytic-only / hint codes that intentionally
    # do NOT flip status to blocked.
    notices = [b for b in blockers if b["code"] in _RECOVERABLE]
    real_blockers = [b for b in blockers if b["code"] not in _RECOVERABLE]
    # Keep `blockers` field in the legacy shape (everything, both real and
    # informational, including SLHA_MISSING_HINT) so existing tests that scan
    # codes from `blockers` continue to pass; add `notices` as the canonical
    # surface for ANALYTIC_BACKEND_PATH-style demotions.
    result = {
        "status": status,
        "blockers": blockers,           # legacy: real + informational
        "real_blockers": real_blockers, # only fatal codes (would flip status)
        "notices": notices,             # informational / recoverable demotions
        "checked": checked,
    }
    exit_code = 0 if status == "ok" else 1
    return result, exit_code


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prerequisite guard for /dark-matter-constraints router.",
    )
    parser.add_argument("--config", required=True, help="Path to config JSON/YAML.")
    parser.add_argument("--model", required=True, help="BSM model name (key in config.models).")
    parser.add_argument("--manifest", default=None, help="Path to router_contract.json (default: auto-resolved).")
    args = parser.parse_args()

    result, exit_code = check_prereqs(
        config_path=args.config,
        model=args.model,
        manifest_path=args.manifest,
    )

    if exit_code == 2:
        # Internal error: write to stderr
        print(json.dumps(result), file=sys.stderr)
    else:
        print(json.dumps(result))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
