"""validate_spec.py — Validate a ModelSpec v3 YAML.

Thin wrapper around :mod:`modelspec_v3.validate`. The CLI prints
diagnostics in the v3 pretty format on stderr and exits non-zero on
errors. The library entry point :func:`validate` returns the loaded
spec dict (raising :class:`SystemExit(1)` on validation errors), to
preserve the call shape used by ``build.py`` and friends.

Usage:
    python3 validate_spec.py <spec.yaml>
"""
from __future__ import annotations

import pathlib
import sys

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_SHARED_DIR = _SCRIPT_DIR.parent.parent / "_shared"

if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from modelspec_v3.loader import load_spec, SpecLoadError  # noqa: E402
from modelspec_v3.validate import validate as _v3_validate  # noqa: E402
from modelspec_v3.emit import emit_pretty  # noqa: E402


def validate(spec_path: "pathlib.Path | str") -> dict:
    """Load *spec_path*, run v3 validation, and return the spec dict.

    On any validation error this exits with status 1 after writing
    pretty-formatted diagnostics to stderr (matching the legacy
    ``MODELSPEC_INVALID`` exit semantics).
    """
    try:
        spec = load_spec(spec_path)
    except SpecLoadError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    result = _v3_validate(spec)
    if result.warnings:
        print(emit_pretty(result.warnings), file=sys.stderr)
    if result.errors:
        print(emit_pretty(result.errors), file=sys.stderr)
        sys.exit(1)
    return spec


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <spec.yaml>", file=sys.stderr)
        sys.exit(2)
    spec = validate(pathlib.Path(sys.argv[1]))
    name = spec.get("model", {}).get("name", "<unknown>")
    print(f'{{"status": "valid", "name": "{name}"}}')


if __name__ == "__main__":
    main()
