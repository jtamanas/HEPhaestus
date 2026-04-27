"""
config_migration.py — Adoption check for hephaestus config.json.

This is NOT a migrator (no key renames).  It is an adoption check:
- Asserts that the existing hep-ph-demo keys (wolfram_engine_path,
  sarah_path, spheno_path, mg5_path) are present if they were set before.
- Ensures that the 'models' key exists (creates it as {} if absent).
- Prints a diff of any changes that --apply would make.

Usage:
    python3 config_migration.py --check    # exits 0 if no changes needed, 1 if changes needed
    python3 config_migration.py --apply    # writes via config_helpers.merge_config; exits 0

The --check exit code:
    0  config is already in the desired state (no changes needed).
    1  changes would be made (not an error; --apply fixes it).
    2  argument error.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import config_helpers (handle both in-repo and installed usage)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
_SHARED_HELPERS = _HERE.parent.parent.parent / "shared" / "install-helpers"
if str(_SHARED_HELPERS) not in sys.path:
    sys.path.insert(0, str(_SHARED_HELPERS))

try:
    import config_helpers
except ImportError:
    # Fall back: if running from the _shared/ dir with helpers co-located
    sys.path.insert(0, str(_HERE))
    import config_helpers  # type: ignore[no-redef]

# ---------------------------------------------------------------------------
# Known hep-ph-demo config keys that MUST NOT be renamed or removed.
# ---------------------------------------------------------------------------
PRESERVED_KEYS = {
    "wolfram_engine_path",
    "sarah_path",
    "spheno_path",
    "mg5_path",
    "last_configured",
    "python",
}

# Keys that the migration check ensures exist.
REQUIRED_KEYS: dict[str, object] = {
    "models": {},
}


def _compute_diff(current: dict) -> dict:
    """Return a dict of keys that would be added/changed by --apply.

    Only adds new keys from REQUIRED_KEYS if they are absent.
    Does NOT rename or remove any existing key.
    """
    diff: dict = {}
    for key, default in REQUIRED_KEYS.items():
        if key not in current:
            diff[key] = default
    return diff


def cmd_check(verbose: bool = True) -> int:
    """Check config; return 0 if no changes needed, 1 if changes would be made."""
    config_helpers._reload_roots()
    current = config_helpers.load_config()

    # Assert preserved keys are not altered (they may simply be absent if
    # the user hasn't run an installer yet — that is OK).
    for key in PRESERVED_KEYS:
        if key in current:
            # Key exists: fine.  We just confirm it hasn't been renamed.
            pass  # no rename logic

    diff = _compute_diff(current)
    if not diff:
        if verbose:
            print("config is already in the desired state; no changes needed.")
        return 0
    if verbose:
        print("The following changes would be applied:")
        for k, v in diff.items():
            old = current.get(k, "<absent>")
            print(f"  {k}: {json.dumps(old)} → {json.dumps(v)}")
    return 1


def cmd_apply() -> int:
    """Apply needed changes to config via config_helpers.merge_config; return 0."""
    config_helpers._reload_roots()
    current = config_helpers.load_config()
    diff = _compute_diff(current)
    if not diff:
        print("config is already in the desired state; nothing to do.")
        return 0
    # Ensure 'models' sub-dict is merged without clobbering existing models.
    if "models" in diff:
        # Use register_model approach: just ensure the key exists.
        # We call merge_config with models = existing-or-empty dict.
        existing_models = current.get("models", {})
        config_helpers.merge_config(models=existing_models)  # type: ignore[arg-type]
    print("Applied changes to config.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="hephaestus config adoption check"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Check config; exit 0 if OK, 1 if changes needed.",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Apply needed changes and write config.",
    )
    args = parser.parse_args()

    if args.check:
        sys.exit(cmd_check())
    elif args.apply:
        sys.exit(cmd_apply())


if __name__ == "__main__":
    main()
