"""validate_runner_spec.py — Step 1 runner-spec schema validator (D2).

Validates a runner-spec YAML against
``plugins/shared/schemas/runner_spec.schema.json`` using Draft7Validator.

On failure: prints a JSON error object to stderr and exits 1::

    {"code": "RUNNER_SPEC_INVALID", "mode": "recoverable",
     "detail": "<human-readable message>", "json_path": "<path string>"}

On success: prints the normalised spec as JSON to stdout and exits 0.

Usage::

    python validate_runner_spec.py --spec path/to/spec.yaml
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

import jsonschema

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
# scripts/ → dark-matter-constraints/ → skills/ → hep-ph-toolkit/ → plugins/ → repo
_REPO_ROOT = _HERE.parents[4]
_SCHEMA_PATH = _REPO_ROOT / "plugins" / "shared" / "schemas" / "runner_spec.schema.json"
_LOADER_PATH = _REPO_ROOT / "plugins" / "shared" / "runner_spec_loader.py"


def _load_loader_module():
    """Dynamically import runner_spec_loader from the shared plugins directory."""
    spec = importlib.util.spec_from_file_location("runner_spec_loader", _LOADER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate_runner_spec(spec_path: pathlib.Path) -> dict:
    """Load and validate a runner-spec YAML.

    Returns the normalised spec dict on success.
    Raises ``SystemExit(1)`` on validation failure (emitting structured JSON
    to stderr).

    Parameters
    ----------
    spec_path:
        Path to the runner-spec YAML file.

    Returns
    -------
    dict
        Normalised spec dict (cosmology scalar form promoted to object).
    """
    # Load spec via shared loader (normalises legacy scalar cosmology)
    loader_mod = _load_loader_module()
    try:
        spec = loader_mod.load_runner_spec(spec_path)
    except Exception as exc:
        _fail(f"Cannot load YAML: {exc}", json_path="")

    # Load schema
    try:
        with open(_SCHEMA_PATH) as fh:
            schema = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"Cannot load runner_spec schema: {exc}", json_path="")

    # Validate
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(spec))
    if errors:
        # Report the first (most relevant) error
        err = errors[0]
        path_str = "/" + "/".join(str(p) for p in err.absolute_path) if err.absolute_path else ""
        _fail(err.message, json_path=path_str)

    return spec


def _fail(detail: str, json_path: str) -> None:
    """Print structured RUNNER_SPEC_INVALID error to stderr and exit 1."""
    payload = {
        "code": "RUNNER_SPEC_INVALID",
        "mode": "recoverable",
        "detail": detail,
        "json_path": json_path,
    }
    print(json.dumps(payload), file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a runner-spec YAML against runner_spec/v1 schema.",
    )
    parser.add_argument("--spec", required=True, help="Path to the runner-spec YAML file.")
    args = parser.parse_args()

    spec_path = pathlib.Path(args.spec)
    if not spec_path.exists():
        _fail(f"Spec file not found: {spec_path}", json_path="")

    spec = validate_runner_spec(spec_path)
    print(json.dumps(spec))


if __name__ == "__main__":
    main()
