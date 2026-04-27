"""Resolve a named hephaestus model to its registered paths.

CLI usage:
    python3 resolve_named_model.py <name>                    # print full JSON dict
    python3 resolve_named_model.py <name> --key <keyname>    # print single value

Exit codes:
    0  success
    1  model not registered (or config file not found)
    2  key not set for this model (or unrecognised key)
    3  bad arguments
"""
import json
import os
import sys
from pathlib import Path

# Inline config read — no cross-plugin import (judgment-call #6).
CONFIG_PATH = (
    Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    / "hephaestus"
    / "config.json"
)

KNOWN_KEYS = {"ufo", "latest_slha", "spheno_bin", "latest_run", "spec",
              "sarah_built_at", "spheno_built_at"}


def resolve(name: str) -> dict | None:
    """Return the config.models[name] dict, or None if not found."""
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except FileNotFoundError:
        return None
    return cfg.get("models", {}).get(name) or None


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(
            "usage: resolve_named_model.py <name> [--key {ufo,latest_slha,spheno_bin,...}]",
            file=sys.stderr,
        )
        sys.exit(0 if args and args[0] in ("-h", "--help") else 3)

    name = args[0]

    # Parse optional --key
    key: str | None = None
    if len(args) == 3 and args[1] == "--key":
        key = args[2]
    elif len(args) == 2 and args[1] == "--key":
        print("--key requires an argument", file=sys.stderr)
        sys.exit(3)
    elif len(args) != 1:
        print(
            "usage: resolve_named_model.py <name> [--key {ufo,latest_slha,spheno_bin,...}]",
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except FileNotFoundError:
        print(f"config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    model = cfg.get("models", {}).get(name)
    if not model:
        print(f"model not registered: {name}", file=sys.stderr)
        sys.exit(1)

    if key is None:
        # Print full dict as JSON
        print(json.dumps(model))
        return

    value = model.get(key)
    if not value:
        print(f"key {key!r} not set for {name}", file=sys.stderr)
        sys.exit(2)

    print(value)


if __name__ == "__main__":
    main()
