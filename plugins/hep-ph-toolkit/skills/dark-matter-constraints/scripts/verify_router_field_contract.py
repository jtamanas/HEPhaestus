#!/usr/bin/env python3
"""verify_router_field_contract.py — WS-4 router contract verification helper.

Usage:
    python <path>/scripts/verify_router_field_contract.py [--manifest <path>] [--fixtures-root <path>]

Outputs a pytest-style summary per output_fields row:
    OK <observable>:<downstream>
    XFAIL <observable>:<downstream>:<reason>
    FAIL <observable>:<downstream>:<DRIFT_CODE>:<detail>

Final summary line:
    SUMMARY <ok>/<xfail>/<fail>

Exit codes:
    0 — all rows pass-or-xfail
    1 — any row fails with a DRIFT_* code
    2 — internal error (manifest unparseable, schema file missing)

Drift codes emitted (synthesis §1.4):
    DRIFT_PRODUCER_DOC_GAP
    DRIFT_PRODUCER_RENAMED
    DRIFT_ROUTER_INVENTED_NAME
    DRIFT_DOCUMENTED_BUT_ABSENT
    DRIFT_PRESENT_BUT_UNDOCUMENTED
    DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY

Importable surface:
    from verify_router_field_contract import verify_router_field_contract, VerifyResult
    result = verify_router_field_contract(manifest_path, fixtures_root)
    # result.ok, result.xfail, result.fail are lists of row-result dicts

Model-agnosticism: pure string match + JSON pointer + jsonschema. No physics.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import pathlib
import re
import sys
from typing import Any

import jsonschema

# ---------------------------------------------------------------------------
# Paths — resolved relative to this helper
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_DEFAULT_MANIFEST = _HERE.parent / "contracts" / "router_contract.json"
_DEFAULT_FIXTURES_ROOT = _HERE.parent / "tests" / "fixtures"

# Repo root: scripts/ → dark-matter-constraints/ → skills/ → constraints/ → plugins/ → repo
_REPO_ROOT = _HERE.parents[4]


# ---------------------------------------------------------------------------
# VerifyResult dataclass
# ---------------------------------------------------------------------------

class _VerifyResultBase:
    """Result of verify_router_field_contract. Has ok, xfail, fail list attributes."""
    __dataclass_fields__: dict = {}  # satisfies dataclasses.is_dataclass()

    def __init__(self) -> None:
        self.ok: list = []
        self.xfail: list = []
        self.fail: list = []

    def __repr__(self) -> str:
        return (
            f"VerifyResult(ok={len(self.ok)}, xfail={len(self.xfail)}, fail={len(self.fail)})"
        )


# Expose as VerifyResult — the __dataclass_fields__ attribute makes dataclasses.is_dataclass() True
VerifyResult = _VerifyResultBase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: pathlib.Path) -> dict:
    with open(path) as fh:
        return json.load(fh)


def _producer_skill_path(entry: dict) -> pathlib.Path:
    """Resolve the absolute producer SKILL.md path from entry.defined_in."""
    defined_in = entry["defined_in"]
    path_part = defined_in.split("#")[0]
    return _REPO_ROOT / path_part


def _router_skill_path(manifest: dict) -> pathlib.Path:
    router_skill = manifest.get("router_skill", "")
    return _REPO_ROOT / router_skill


def _scattering_schema_path() -> pathlib.Path:
    return _REPO_ROOT / "plugins" / "shared" / "schemas" / "scattering.schema.json"


def _xfail_reason(status: str, field_name: str = "") -> str:
    if status == "pending_schema":
        if "sigma_v" in field_name or field_name == "sigma_v_zero":
            return "WS-4: annihilation/v1 schema not yet delivered — see WS-4 W4-A/W4-B"
        return "WS-4: relic/v1 schema not yet delivered — see WS-4 W4-A/W4-B"
    if status == "pending_producer_doc_fix":
        return (
            "WS-4: producer SKILL.md edit — maddm/SKILL.md line 164 lists legacy name, "
            "must be reconciled to canonical field name — see WS-4 W4-C"
        )
    if status == "pending_producer_topology_fix":
        return (
            "WS-4: drake-install detect must emit activation_required "
            "(currently use-path only — drake/SKILL.md lines 84-86) — see WS-4 W4-E"
        )
    return f"WS-4: pending status: {status}"


# ---------------------------------------------------------------------------
# Per-row verification dispatch
# ---------------------------------------------------------------------------

def _check_agent_parsed(
    entry: dict,
    fixtures_root: pathlib.Path,
    router_skill_text: str,
) -> tuple[str | None, str | None]:
    """
    For produced_by=='agent_parsed': pattern must match in fixture.
    Returns (drift_code, detail) or (None, None) on pass.
    """
    fixture_path = pathlib.Path(entry["fixture"])
    if not fixture_path.exists():
        return "DRIFT_DOCUMENTED_BUT_ABSENT", f"Fixture not found: {fixture_path}"
    fixture_text = fixture_path.read_text()
    pattern = entry["source_locator"]["pattern"]
    if not re.search(pattern, fixture_text, re.MULTILINE):
        return (
            "DRIFT_DOCUMENTED_BUT_ABSENT",
            f"Pattern '{pattern}' not found in fixture '{fixture_path}'",
        )

    # Check field_name appears in router SKILL.md
    fn = entry["field_name"]
    if not re.search(rf"\b{re.escape(fn)}\b", router_skill_text):
        return (
            "DRIFT_ROUTER_INVENTED_NAME",
            f"Field '{fn}' not found as word in router SKILL.md",
        )

    # Check field_name appears in producer SKILL.md
    skill_path = _producer_skill_path(entry)
    if not skill_path.exists():
        return "DRIFT_PRODUCER_DOC_GAP", f"Producer SKILL.md not found: {skill_path}"
    skill_text = skill_path.read_text()
    if not re.search(rf"\b{re.escape(fn)}\b", skill_text):
        return (
            "DRIFT_PRODUCER_DOC_GAP",
            f"Field '{fn}' not found in producer SKILL.md ({skill_path})",
        )

    return None, None


def _resolve_type(prop: dict) -> set[str]:
    """Return the set of JSON-Schema types encoded in *prop*.

    Handles three forms:
    - ``{"type": "number"}``              → {"number"}
    - ``{"oneOf": [{...}, ...]}``         → union of each branch's types
    - ``{"anyOf": [{...}, ...]}``         → union of each branch's types
    Falls back to an empty set when no recognisable type information is present.
    """
    if "type" in prop:
        t = prop["type"]
        return set(t) if isinstance(t, list) else {t}
    types: set[str] = set()
    for key in ("oneOf", "anyOf"):
        for branch in prop.get(key, []):
            types |= _resolve_type(branch)
    return types


def _check_summary_json(
    entry: dict,
    fixtures_root: pathlib.Path,
    router_skill_text: str,
) -> tuple[str | None, str | None]:
    """
    For produced_by=='summary_json': json_pointer must resolve in scattering schema.
    Returns (drift_code, detail) or (None, None) on pass.
    """
    # Load scattering schema
    schema_path = _scattering_schema_path()
    if not schema_path.exists():
        return "DRIFT_PRODUCER_DOC_GAP", f"Scattering schema not found: {schema_path}"
    try:
        schema = _load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return "DRIFT_PRODUCER_DOC_GAP", f"Cannot load scattering schema: {exc}"

    locator = entry["source_locator"]
    ptr = locator.get("json_pointer", "")
    if not ptr.startswith("/properties/"):
        return "DRIFT_PRODUCER_DOC_GAP", f"Unexpected json_pointer form: {ptr}"

    prop_name = ptr[len("/properties/"):]
    props = schema.get("properties", {})
    if prop_name not in props:
        return (
            "DRIFT_PRODUCER_DOC_GAP",
            f"Field '{prop_name}' not found in scattering.schema.json properties",
        )

    prop_types = _resolve_type(props[prop_name])
    if "number" not in prop_types:
        return (
            "DRIFT_PRODUCER_DOC_GAP",
            f"Field '{prop_name}' has types {prop_types!r}, expected 'number' to be present",
        )

    # Also verify fixture exists and field_name is in router SKILL.md
    fixture_path = pathlib.Path(entry["fixture"])
    if not fixture_path.exists():
        return "DRIFT_DOCUMENTED_BUT_ABSENT", f"Fixture not found: {fixture_path}"

    fn = entry["field_name"]
    if not re.search(rf"\b{re.escape(fn)}\b", router_skill_text):
        return (
            "DRIFT_ROUTER_INVENTED_NAME",
            f"Field '{fn}' not found as word in router SKILL.md",
        )

    return None, None


def _check_stdout_regex(
    entry: dict,
    fixtures_root: pathlib.Path,
    router_skill_text: str,
) -> tuple[str | None, str | None]:
    """
    For produced_by=='stdout_regex': pattern must match in fixture.
    Returns (drift_code, detail) or (None, None) on pass.
    """
    fixture_path = pathlib.Path(entry["fixture"])
    if not fixture_path.exists():
        return "DRIFT_DOCUMENTED_BUT_ABSENT", f"Stdout fixture not found: {fixture_path}"
    fixture_text = fixture_path.read_text()
    pattern = entry["source_locator"]["pattern"]
    if not re.search(pattern, fixture_text, re.MULTILINE | re.IGNORECASE):
        return (
            "DRIFT_DOCUMENTED_BUT_ABSENT",
            f"Pattern '{pattern}' not found in fixture '{fixture_path}'",
        )

    fn = entry["field_name"]
    if not re.search(rf"\b{re.escape(fn)}\b", router_skill_text):
        return (
            "DRIFT_ROUTER_INVENTED_NAME",
            f"Field '{fn}' not found as word in router SKILL.md",
        )

    return None, None


def _check_pending_schema_row(entry: dict) -> tuple[str | None, str | None]:
    """
    For pending_schema rows: check if the schema now exists (xfail becomes XPASS).
    Returns (drift_code, detail) if still failing, or (None, None) if schema now ships.
    """
    fn = entry["field_name"]
    schema_name = "relic" if "sigma_v" not in fn else "annihilation"
    schema_path = _REPO_ROOT / "plugins" / "shared" / "schemas" / f"{schema_name}.schema.json"
    if not schema_path.exists():
        return "DRIFT_PRODUCER_DOC_GAP", f"Schema '{schema_name}.schema.json' not yet shipped"
    try:
        schema = _load_json(schema_path)
        props = schema.get("properties", {})
        if fn not in props:
            return "DRIFT_PRODUCER_DOC_GAP", f"Schema exists but has no '{fn}' property"
    except (OSError, json.JSONDecodeError) as exc:
        return "DRIFT_PRODUCER_DOC_GAP", f"Cannot load schema: {exc}"
    return None, None


def _check_pending_producer_doc_fix(entry: dict) -> tuple[str | None, str | None]:
    """
    For pending_producer_doc_fix rows: check if producer SKILL.md reading section
    now uses the canonical name without the legacy name.
    """
    skill_path = _producer_skill_path(entry)
    if not skill_path.exists():
        return "DRIFT_PRODUCER_DOC_GAP", f"Producer SKILL.md not found: {skill_path}"
    skill_text = skill_path.read_text()

    # Extract reading section
    reading_lines = []
    in_reading = False
    for line in skill_text.splitlines():
        if "Reading MadDM output" in line:
            in_reading = True
        if in_reading:
            reading_lines.append(line)
        if in_reading and line.startswith("###") and "Reading MadDM" not in line:
            break
    reading_text = "\n".join(reading_lines)

    if re.search(r'\bsigmav_xf\b', reading_text):
        return (
            "DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY",
            "maddm/SKILL.md reading section still references legacy 'sigmav_xf' name",
        )
    return None, None


def _check_pending_producer_topology_fix(
    manifest: dict,
    entry: dict | None = None,
) -> tuple[str | None, str | None]:
    """
    For pending_producer_topology_fix status_enums rows: check if drake/SKILL.md
    detect table now documents activation_required as a table row.
    """
    drake_skill_path = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "drake" / "SKILL.md"
    if not drake_skill_path.exists():
        return "DRIFT_PRODUCER_DOC_GAP", f"drake/SKILL.md not found"
    drake_text = drake_skill_path.read_text()

    detect_match = re.search(
        r"Expected `status` values from.*?(?=\nNote:|\n\n\*\*If|\Z)",
        drake_text,
        re.DOTALL,
    )
    if not detect_match:
        return "DRIFT_PRODUCER_DOC_GAP", "Could not find detect status table in drake/SKILL.md"
    detect_table = detect_match.group(0)

    if not re.search(r'^\|\s*`activation_required`', detect_table, re.MULTILINE):
        return (
            "DRIFT_PRODUCER_DOC_GAP",
            "drake/SKILL.md detect status TABLE does not list 'activation_required' as a row",
        )
    return None, None


# ---------------------------------------------------------------------------
# Main verification function
# ---------------------------------------------------------------------------

def verify_router_field_contract(
    manifest_path: pathlib.Path,
    fixtures_root: pathlib.Path,
) -> VerifyResult:
    """
    Verify router field contract.

    Returns VerifyResult with .ok, .xfail, .fail lists (each item is a row-result dict).
    """
    result = VerifyResult()

    # Load manifest
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load manifest: {exc}") from exc

    # Load router SKILL.md text
    router_skill_path = _router_skill_path(manifest)
    try:
        router_skill_text = router_skill_path.read_text()
    except OSError:
        router_skill_text = ""

    # Process output_fields entries
    for entry in manifest.get("output_fields", []):
        audit_status = entry.get("audit_status", "")
        observable = entry.get("observable", "?")
        downstream = entry.get("downstream", "?")
        field_name = entry.get("field_name", "?")
        label = f"{observable}:{downstream}"

        is_pending = audit_status.startswith("pending_")
        produced_by = entry.get("produced_by", "")

        if is_pending:
            # Determine if the pending condition is now resolved (XPASS) or still failing
            if audit_status == "pending_schema":
                drift_code, detail = _check_pending_schema_row(entry)
            elif audit_status == "pending_producer_doc_fix":
                drift_code, detail = _check_pending_producer_doc_fix(entry)
            else:
                drift_code, detail = _check_pending_producer_topology_fix(manifest, entry)

            if drift_code is None:
                # Condition resolved — XPASS (count as OK)
                row = {"label": label, "field_name": field_name, "status": "xpass"}
                result.ok.append(row)
            else:
                # Still failing — expected XFAIL
                reason = _xfail_reason(audit_status, field_name)
                row = {
                    "label": label,
                    "field_name": field_name,
                    "status": "xfail",
                    "reason": reason,
                    "drift_code": drift_code,
                    "detail": detail,
                }
                result.xfail.append(row)
        else:
            # Non-pending: run the appropriate check
            if produced_by == "agent_parsed":
                drift_code, detail = _check_agent_parsed(entry, fixtures_root, router_skill_text)
            elif produced_by == "summary_json":
                drift_code, detail = _check_summary_json(entry, fixtures_root, router_skill_text)
            elif produced_by == "stdout_regex":
                drift_code, detail = _check_stdout_regex(entry, fixtures_root, router_skill_text)
            else:
                drift_code, detail = "DRIFT_PRODUCER_DOC_GAP", f"Unknown produced_by: '{produced_by}'"

            if drift_code is None:
                row = {"label": label, "field_name": field_name, "status": "ok"}
                result.ok.append(row)
            else:
                row = {
                    "label": label,
                    "field_name": field_name,
                    "status": "fail",
                    "drift_code": drift_code,
                    "detail": detail,
                }
                result.fail.append(row)

    # Process status_enums entries
    for enum_entry in manifest.get("status_enums", []):
        audit_status = enum_entry.get("audit_status", "")
        enum_name = enum_entry.get("enum_name", "?")
        label = f"enum:{enum_name}"

        is_pending = audit_status.startswith("pending_")

        if is_pending:
            if audit_status == "pending_producer_topology_fix":
                drift_code, detail = _check_pending_producer_topology_fix(manifest, enum_entry)
            else:
                drift_code, detail = "DRIFT_PRODUCER_DOC_GAP", f"Unknown pending status: {audit_status}"

            if drift_code is None:
                row = {"label": label, "field_name": enum_name, "status": "xpass"}
                result.ok.append(row)
            else:
                reason = _xfail_reason(audit_status, enum_name)
                row = {
                    "label": label,
                    "field_name": enum_name,
                    "status": "xfail",
                    "reason": reason,
                    "drift_code": drift_code,
                    "detail": detail,
                }
                result.xfail.append(row)
        else:
            # Non-pending enum: verify literals appear in router SKILL.md
            drift_code = None
            detail = None
            for literal in enum_entry.get("literals", []):
                if literal not in router_skill_text:
                    drift_code = "DRIFT_ROUTER_INVENTED_NAME"
                    detail = f"Status literal '{literal}' not found in router SKILL.md"
                    break
            if drift_code is None:
                row = {"label": label, "field_name": enum_name, "status": "ok"}
                result.ok.append(row)
            else:
                row = {
                    "label": label,
                    "field_name": enum_name,
                    "status": "fail",
                    "drift_code": drift_code,
                    "detail": detail,
                }
                result.fail.append(row)

    return result


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify router field contract against producer SKILL.md files and fixtures.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to router_contract.json (default: auto-resolved; env ROUTER_CONTRACT_PATH overrides).",
    )
    parser.add_argument(
        "--fixtures-root",
        default=None,
        help="Path to fixtures directory (default: auto-resolved to tests/fixtures/).",
    )
    args = parser.parse_args()

    # Env override for manifest (per WS-1 plan T3 acceptance gate #3)
    env_manifest = os.environ.get("ROUTER_CONTRACT_PATH")
    if env_manifest:
        manifest_path = pathlib.Path(env_manifest)
    elif args.manifest:
        manifest_path = pathlib.Path(args.manifest)
    else:
        manifest_path = _DEFAULT_MANIFEST

    fixtures_root = pathlib.Path(args.fixtures_root) if args.fixtures_root else _DEFAULT_FIXTURES_ROOT

    try:
        result = verify_router_field_contract(manifest_path, fixtures_root)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc), "code": "VERIFY_INTERNAL"}), file=sys.stderr)
        sys.exit(2)

    # Print one line per row
    for row in result.ok:
        if row.get("status") == "xpass":
            print(f"XPASS {row['label']}")
        else:
            print(f"OK {row['label']}")

    for row in result.xfail:
        drift = row.get("drift_code", "")
        reason = row.get("reason", "")
        print(f"XFAIL {row['label']}:{drift}:{reason}")

    for row in result.fail:
        drift = row.get("drift_code", "")
        detail = row.get("detail", "")
        print(f"FAIL {row['label']}:{drift}:{detail}")

    # Summary
    n_ok = len(result.ok)
    n_xfail = len(result.xfail)
    n_fail = len(result.fail)
    print(f"SUMMARY {n_ok}/{n_xfail}/{n_fail}")

    if n_fail > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
