"""
check_state.py — probe model registration only.

Usage:
    python3 check_state.py
    python3 check_state.py --model <name>

Output (stdout): JSON object with key:
    model : {"status": "present" | "missing", "name": "<name-or-null>"}

Install state for SARAH / SPheno / Wolfram is no longer probed here; each
runner skill (`/sarah-build`, `/spheno-build`) carries its own preflight
that calls `_shared/installs/<tool>/detect.sh` and self-heals if missing.

Pure probe; no side effects on disk or config.

State and config roots obey HEPPH_STATE_ROOT and XDG_CONFIG_HOME for test
isolation (see phase2-plan-final.md §2.3).
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate config_helpers relative to this script's position in the tree.
# Script lives at:
#   plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py
# config_helpers.py lives at:
#   plugins/shared/install-helpers/config_helpers.py
# Relative path: ../../../../shared/install-helpers/
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_CONFIG_HELPERS_DIR = _SCRIPT_DIR / ".." / ".." / ".." / ".." / "shared" / "install-helpers"
sys.path.insert(0, str(_CONFIG_HELPERS_DIR.resolve()))

try:
    import config_helpers
except ModuleNotFoundError:
    # Fallback: try the _shared location (for testing without shared dir)
    _SHARED_DIR = _SCRIPT_DIR / ".." / ".." / "_shared"
    sys.path.insert(0, str(_SHARED_DIR.resolve()))
    import config_helpers


def _path_exists(path_str: str | None) -> bool:
    if not path_str:
        return False
    return Path(path_str).exists()


def check_model(cfg: dict, name: str | None) -> dict:
    """
    Return {"status": "present", "name": name} if the model is registered
    with at least a spec path, else {"status": "missing", "name": name_or_null}.
    """
    if name is None:
        return {"status": "missing", "name": None}
    models = cfg.get("models", {})
    entry = models.get(name)
    if entry and entry.get("spec") and _path_exists(entry.get("spec")):
        return {"status": "present", "name": name}
    return {"status": "missing", "name": name}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe model registration state."
    )
    parser.add_argument(
        "--model",
        metavar="NAME",
        default=None,
        help="Check registration status for this model name.",
    )
    args = parser.parse_args()

    # Re-compute roots in case env vars were set after module import.
    config_helpers._reload_roots()
    cfg = config_helpers.load_config()

    result = {
        "model": check_model(cfg, args.model),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
