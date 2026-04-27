"""
register_model.py — write config.models[<name>] atomically via config_helpers.

Usage:
    python3 register_model.py <name> \\
        --spec <path> \\
        --ufo  <path> \\
        [--latest-slha   <path>] \\
        [--spheno-bin    <path>] \\
        [--sarah-built-at  <iso8601>] \\
        [--spheno-built-at <iso8601>]

All path arguments must be absolute or will be resolved relative to cwd.
Exits 0 on success; exits 1 on model-name validation failure.

Config isolation is respected via HEPPH_STATE_ROOT and XDG_CONFIG_HOME
(see phase2-plan-final.md §2.3).
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
from pathlib import Path

# Locate config_helpers (same relative logic as check_state.py)
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register a model in the hephaestus config."
    )
    parser.add_argument("name", help="Model name (must match model-name regex).")
    parser.add_argument("--spec", required=True, help="Absolute path to spec YAML.")
    parser.add_argument("--ufo", required=True, help="Absolute path to UFO directory.")
    parser.add_argument("--latest-slha", default=None, help="Path to latest SPheno.spc.")
    parser.add_argument("--spheno-bin", default=None, help="Path to compiled SPheno binary.")
    parser.add_argument("--sarah-built-at", default=None, help="UTC ISO 8601 SARAH build timestamp.")
    parser.add_argument("--spheno-built-at", default=None, help="UTC ISO 8601 SPheno build timestamp.")
    args = parser.parse_args()

    # Validate model name against regex before writing
    if not config_helpers.MODEL_NAME_REGEX.match(args.name):
        print(
            f"error: model name {args.name!r} does not match ^[a-z][a-z0-9_]{{1,30}}$",
            file=sys.stderr,
        )
        sys.exit(1)

    # Re-compute roots in case env vars were set after import
    config_helpers._reload_roots()

    fields: dict = {
        "spec": str(Path(args.spec).resolve()),
        "ufo": str(Path(args.ufo).resolve()),
    }
    if args.latest_slha is not None:
        fields["latest_slha"] = str(Path(args.latest_slha).resolve())
    if args.spheno_bin is not None:
        fields["spheno_bin"] = str(Path(args.spheno_bin).resolve())
    if args.sarah_built_at is not None:
        fields["sarah_built_at"] = args.sarah_built_at
    if args.spheno_built_at is not None:
        fields["spheno_built_at"] = args.spheno_built_at

    config_helpers.register_model(args.name, **fields)
    print(f"Registered model {args.name!r} in config.")


if __name__ == "__main__":
    main()
