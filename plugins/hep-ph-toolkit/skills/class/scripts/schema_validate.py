"""schema_validate.py — validate cosmology.json against cosmology/v1 schema.

Uses jsonschema.Draft202012Validator. The schema is read from
plugins/shared/schemas/cosmology.schema.json — never vendored here.

No NumPy, SciPy, or SymPy.
"""
from __future__ import annotations

import json
from pathlib import Path


class SchemaValidationError(Exception):
    """Raised when a document fails schema validation."""


def validate(document: dict, schema_path: Path) -> None:
    """Validate *document* against the JSON Schema at *schema_path*.

    Parameters
    ----------
    document:
        The dict to validate (e.g. the cosmology.json payload).
    schema_path:
        Absolute path to cosmology.schema.json.

    Raises
    ------
    SchemaValidationError
        If validation fails or jsonschema is not installed.
    """
    try:
        import jsonschema  # type: ignore[import]
    except ImportError as exc:
        raise SchemaValidationError(
            "jsonschema is required for output validation. "
            "Install it with: pip install jsonschema"
        ) from exc

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception as exc:
        raise SchemaValidationError(
            f"Failed to load schema from {schema_path}: {exc}"
        ) from exc

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(document))
    if errors:
        messages = [f"  - {e.json_path}: {e.message}" for e in errors[:5]]
        raise SchemaValidationError(
            f"cosmology.json does not conform to cosmology/v1 schema "
            f"({len(errors)} error(s)):\n" + "\n".join(messages)
        )
