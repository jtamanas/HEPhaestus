"""
Validate a scattering JSON document against scattering.schema.json.
Emits a DDCALC_INPUT_INVALID blocker JSON to stderr on failure.

Usage:
    validate_scattering.py <sigma_json_path>
    → exits 0 if valid; exits non-zero with blocker on stderr if invalid.

Also importable: validate_sigma_json(path_or_dict) → dict (raises ValueError on invalid)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print(
        json.dumps({
            "code": "DDCALC_INPUT_INVALID",
            "mode": "fatal",
            "message": "jsonschema package not installed. Run: pip install jsonschema",
            "context": {},
        }),
        file=sys.stderr,
    )
    sys.exit(1)

# Schema path: ../../../../shared/schemas/scattering.schema.json
_SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent.parent
    / "shared"
    / "schemas"
    / "scattering.schema.json"
)


def load_schema() -> dict:
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def validate_sigma_json(data: dict | str | Path) -> dict:
    """
    Validate a scattering document.
    - data: dict, str (path), or Path
    Returns the validated dict on success.
    Raises ValueError with a message on validation failure.
    """
    if isinstance(data, (str, Path)):
        path = Path(data)
        with open(path) as f:
            doc = json.load(f)
    else:
        doc = data

    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: str(e.path))

    if errors:
        # Collect first few error messages
        msgs = [f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors[:3]]
        raise ValueError("; ".join(msgs))

    # Extra check: reject nreft_coefficients (v1 does not support NREFT)
    if "nreft_coefficients" in doc:
        raise ValueError(
            "nreft_coefficients: DDCALC_NREFT_NOT_SUPPORTED — "
            "NREFT inputs are not supported in v1."
        )

    return doc


def _blocker(message: str, context: dict | None = None) -> None:
    print(
        json.dumps({
            "code": "DDCALC_INPUT_INVALID",
            "mode": "fatal",
            "message": message,
            "context": context or {},
        }),
        file=sys.stderr,
    )


def main():
    if len(sys.argv) < 2:
        _blocker("Usage: validate_scattering.py <sigma_json_path>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        doc = validate_sigma_json(path)
    except FileNotFoundError as e:
        _blocker(str(e), {"path": path})
        sys.exit(1)
    except json.JSONDecodeError as e:
        _blocker(f"JSON parse error: {e}", {"path": path})
        sys.exit(1)
    except ValueError as e:
        _blocker(str(e), {"path": path, "error_tail": str(e)[:500]})
        sys.exit(1)

    # Echo back the validated document
    print(json.dumps(doc, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
