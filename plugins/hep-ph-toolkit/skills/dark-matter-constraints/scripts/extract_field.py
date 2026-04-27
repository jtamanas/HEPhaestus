#!/usr/bin/env python3
"""extract_field.py — WS-4 schema-pinned field extractor for /dark-matter-constraints.

Usage:
    python <path>/scripts/extract_field.py --json <path> --key <name> --schema-version <id> [--schema-root <dir>]

Outputs on clean extract (stdout):
    {"value": <number|null>, "key": "<name>", "schema_version": "<id>", "source_file": "<abs-path>"}

Outputs on error (stderr):
    {"error": "...", "code": "<see grid>"}

Exit-code grid (LOCKED — synthesis §1.3):
    0 — key present, value matches a schema branch (number)
    0 — key present, value is null AND schema permits oneOf [null, ...]
    1 — key absent from JSON entirely (KEY_ABSENT)
    1 — JSON parses but schema_version field doesn't match --schema-version (VERSION_DRIFT)
    1 — Schema file's $id does not end with /<schema-version> (VERSION_DRIFT)
    1 — JSON validates but value type doesn't match schema's branch (SCHEMA_MISMATCH)
    2 — file unreadable / unparseable / schema file missing (EXTRACT_FIELD_INTERNAL)

Schema dispatch (LOCKED — plan §9 item 2):
    schema_file = <schema-root> / "<basename>.schema.json"
    where <basename> = <schema-version>.split("/")[0]
    Default <schema-root> = $REPO/plugins/shared/schemas/ (resolved from helper location).

Model-agnosticism: schema pinned with additionalProperties:false; field exists with a
typed value, exists as null, or is absent. No physics, no model-class branch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

# Default schema root: plugins/shared/schemas/ relative to this helper's location
# Path(__file__) → scripts/ → dark-matter-constraints/ → skills/ → constraints/ → plugins/
_DEFAULT_SCHEMA_ROOT = Path(__file__).resolve().parents[4] / "shared" / "schemas"


def _emit_error(code: str, message: str) -> None:
    """Write error JSON to stderr."""
    print(json.dumps({"error": message, "code": code}), file=sys.stderr)


def extract_field(
    json_path: str | Path,
    key: str,
    schema_version: str,
    schema_root: str | Path | None = None,
) -> tuple[dict | None, int]:
    """
    Extract a single top-level field from a schema-pinned JSON file.

    Returns (result_dict, exit_code):
        - On success: ({"value": ..., "key": ..., "schema_version": ..., "source_file": ...}, 0)
        - On recoverable contract failure: (None, 1) — error already written to stderr
        - On internal error: (None, 2) — error already written to stderr
    """
    schema_root = Path(schema_root) if schema_root else _DEFAULT_SCHEMA_ROOT
    json_path = Path(json_path).resolve()

    # --- load JSON file ---
    try:
        with open(json_path) as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _emit_error("EXTRACT_FIELD_INTERNAL", f"Cannot read or parse JSON file: {exc}")
        return None, 2

    # --- schema dispatch: <schema-root>/<basename>.schema.json ---
    basename = schema_version.split("/")[0]
    schema_file = schema_root / f"{basename}.schema.json"

    try:
        with open(schema_file) as fh:
            schema = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _emit_error("EXTRACT_FIELD_INTERNAL", f"Cannot read or parse schema file {schema_file}: {exc}")
        return None, 2

    # --- schema $id self-check BEFORE validation (synthesis §1.3, plan §7 item 5) ---
    schema_id = schema.get("$id", "")
    if not schema_id.endswith("/" + schema_version):
        _emit_error(
            "VERSION_DRIFT",
            f"Schema file $id '{schema_id}' does not end with '/{schema_version}'. "
            f"Shadow-loading of a different schema version detected.",
        )
        return None, 1

    # --- JSON schema_version field check ---
    data_sv = data.get("schema_version", "")
    if data_sv != schema_version:
        _emit_error(
            "VERSION_DRIFT",
            f"JSON schema_version '{data_sv}' does not match expected '{schema_version}'.",
        )
        return None, 1

    # --- validate full JSON against schema ---
    try:
        jsonschema.Draft202012Validator(schema).validate(data)
    except jsonschema.ValidationError as exc:
        _emit_error(
            "SCHEMA_MISMATCH",
            f"JSON failed schema validation: {exc.message}",
        )
        return None, 1

    # --- extract the requested key ---
    if key not in data:
        _emit_error(
            "KEY_ABSENT",
            f"Key '{key}' is absent from the JSON (not the same as null — key does not exist).",
        )
        return None, 1

    value = data[key]

    # Value present (null or number) — return it
    result = {
        "value": value,
        "key": key,
        "schema_version": schema_version,
        "source_file": str(json_path),
    }
    return result, 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Schema-pinned field extractor for /dark-matter-constraints router.",
    )
    parser.add_argument("--json", required=True, dest="json_path", help="Path to schema-pinned JSON file.")
    parser.add_argument("--key", required=True, help="Top-level key name to extract.")
    parser.add_argument(
        "--schema-version",
        required=True,
        help="Schema version id (e.g. 'relic/v1', 'annihilation/v1', 'scattering/v1').",
    )
    parser.add_argument(
        "--schema-root",
        default=None,
        help="Directory containing schema files (default: auto-resolved to plugins/shared/schemas/).",
    )
    args = parser.parse_args()

    result, exit_code = extract_field(
        json_path=args.json_path,
        key=args.key,
        schema_version=args.schema_version,
        schema_root=args.schema_root,
    )

    if result is not None:
        print(json.dumps(result))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
