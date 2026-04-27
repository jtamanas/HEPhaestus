"""
check_state.py — probe SARAH/SPheno/Wolfram install state + model registration.

Usage:
    python3 check_state.py
    python3 check_state.py --model <name>

Output (stdout): JSON object with keys:
    sarah_install   : "configured" | "missing"
    spheno_install  : "configured" | "missing"
    wolfram_install : "configured" | "missing"
    model           : {"status": "present" | "missing", "name": "<name-or-null>"}

Pure probe; no side effects on disk or config.

State and config roots obey HEPPH_STATE_ROOT and XDG_CONFIG_HOME for test
isolation (see phase2-plan-final.md §2.3).
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import os
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
    """Return True if the path string is non-empty and the path exists on disk."""
    if not path_str:
        return False
    return Path(path_str).exists()


def check_sarah(cfg: dict) -> str:
    """Return 'configured' if SARAH is ready, else 'missing'."""
    sarah_path = cfg.get("sarah_path")
    if not sarah_path:
        return "missing"
    p = Path(sarah_path)
    if p.is_dir() and (p / "SARAH.m").exists():
        return "configured"
    return "missing"


def check_spheno(cfg: dict) -> str:
    """Return 'configured' if SPheno binary is reachable, else 'missing'."""
    spheno_path = cfg.get("spheno_path")
    if not spheno_path:
        return "missing"
    p = Path(spheno_path)
    if p.is_file() and os.access(p, os.X_OK):
        return "configured"
    return "missing"


def check_wolfram(cfg: dict) -> str:
    """Return 'configured' if wolframscript is reachable, else 'missing'."""
    wolfram_path = cfg.get("wolfram_engine_path")
    if not wolfram_path:
        return "missing"
    p = Path(wolfram_path)
    if p.is_file() and os.access(p, os.X_OK):
        return "configured"
    return "missing"


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
        description="Probe SARAH/SPheno/Wolfram install state."
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
        "sarah_install": check_sarah(cfg),
        "spheno_install": check_spheno(cfg),
        "wolfram_install": check_wolfram(cfg),
        "model": check_model(cfg, args.model),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
