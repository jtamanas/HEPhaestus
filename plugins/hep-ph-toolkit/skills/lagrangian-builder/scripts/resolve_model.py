"""
resolve_model.py — look up a named model in config, return its registered paths.

Usage:
    python3 resolve_model.py <name>
    python3 resolve_model.py <name> --key {ufo,latest_slha,spheno_bin,spec}

Without --key, prints all registered fields as JSON.
With --key, prints the single value and exits 0; exits 1 if model not found,
exits 2 if the requested key is not set.

This is the W5-side convenience wrapper. The W6 /madgraph resolver uses its
own inline config read (resolve_named_model.py) — no cross-plugin import.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_CONFIG_HELPERS_DIR = (
    _SCRIPT_DIR / ".." / ".." / ".." / ".." / "shared" / "install-helpers"
)
sys.path.insert(0, str(_CONFIG_HELPERS_DIR.resolve()))

try:
    import config_helpers
except ModuleNotFoundError:
    _SHARED_DIR = _SCRIPT_DIR / ".." / ".." / "_shared"
    sys.path.insert(0, str(_SHARED_DIR.resolve()))
    import config_helpers

_VALID_KEYS = {"ufo", "latest_slha", "spheno_bin", "spec", "sarah_built_at", "spheno_built_at"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve a named model's registered paths from config."
    )
    parser.add_argument("name", help="Model name.")
    parser.add_argument(
        "--key",
        choices=sorted(_VALID_KEYS),
        default=None,
        help="Return only the value for this key.",
    )
    args = parser.parse_args()

    config_helpers._reload_roots()
    cfg = config_helpers.load_config()

    model = cfg.get("models", {}).get(args.name)
    if not model:
        print(f"model not registered: {args.name}", file=sys.stderr)
        sys.exit(1)

    if args.key is None:
        print(json.dumps(model, indent=2))
        return

    value = model.get(args.key)
    if not value:
        print(f"key {args.key!r} not set for model {args.name!r}", file=sys.stderr)
        sys.exit(2)

    print(value)


if __name__ == "__main__":
    main()
