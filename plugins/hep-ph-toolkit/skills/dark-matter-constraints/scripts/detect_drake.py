#!/usr/bin/env python3
"""detect_drake.py — WS-4 DRAKE installation state reporter for /dark-matter-constraints.

Usage:
    python <path>/scripts/detect_drake.py --config <path> [--manifest <path>]

Environment:
    HEPPH_DRAKE_DETECT_CMD  Override the default install.sh detect invocation (for tests).

Outputs a single-line JSON to stdout:
    {
        "branch": "branch1_unset"|"branch2_detect",
        "status": "configured"|"found"|"missing"|"activation_required"|"unparseable",
        "router_action": "proceed"|"emit_DRAKE_MISSING"|"emit_DRAKE_ACTIVATION_REQUIRED"|"emit_DRAKE_UNAVAILABLE",
        "raw_detect_output": "..."
    }

Exit codes:
    0 — always (state report, not a gate; router LLM uses router_action field)

Model-agnosticism: DRAKE installation state has zero model-class dependence.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Default manifest: contracts/router_contract.json relative to this helper
_DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "contracts" / "router_contract.json"

# Default install.sh path: relative to this file's location.
# Post-refactor (2026-04-29) the canonical drake install scripts live
# under `plugins/hep-ph-toolkit/_shared/installs/drake/`.
_DEFAULT_INSTALL_SH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "hep-ph-toolkit" / "_shared" / "installs" / "drake" / "install.sh"
)


def _load_json(path: str | Path) -> dict:
    with open(path) as fh:
        return json.load(fh)


def _router_action(status: str) -> str:
    """Map detect status to the router action code the LLM should use."""
    mapping = {
        "configured": "proceed",
        "found": "emit_DRAKE_MISSING",
        "missing": "emit_DRAKE_MISSING",
        "activation_required": "emit_DRAKE_ACTIVATION_REQUIRED",
        "unparseable": "emit_DRAKE_UNAVAILABLE",
    }
    return mapping.get(status, "emit_DRAKE_UNAVAILABLE")


def detect_drake(
    config_path: str | Path,
    manifest_path: str | Path | None = None,
) -> dict:
    """
    Detect DRAKE installation state.

    Returns a dict with keys: branch, status, router_action, raw_detect_output.
    Always exits 0 — this is a state report.
    """
    manifest_path = Path(manifest_path) if manifest_path else _DEFAULT_MANIFEST

    # Load manifest to validate known status literals
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError):
        manifest = {}

    known_literals: set[str] = set()
    for enum_entry in manifest.get("status_enums", []):
        if enum_entry.get("enum_name") == "drake_install_detect_status":
            known_literals = set(enum_entry.get("literals", []))
            break

    # Load config to check if drake_path is set
    try:
        config = _load_json(config_path)
    except (OSError, json.JSONDecodeError):
        config = {}

    drake_path = config.get("drake_path", "")

    if not drake_path:
        # Branch 1 — config.drake_path absent
        return {
            "branch": "branch1_unset",
            "status": "missing",
            "router_action": "emit_DRAKE_MISSING",
            "raw_detect_output": "",
        }

    # Branch 2 — config.drake_path set: invoke detect
    detect_cmd = os.environ.get("HEPPH_DRAKE_DETECT_CMD", "")
    if detect_cmd:
        cmd = [detect_cmd]
    else:
        cmd = ["bash", str(_DEFAULT_INSTALL_SH), "detect"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        raw_output = result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        raw_output = str(exc)
        return {
            "branch": "branch2_detect",
            "status": "unparseable",
            "router_action": "emit_DRAKE_UNAVAILABLE",
            "raw_detect_output": raw_output,
        }

    # Parse the JSON output from detect
    try:
        detect_json = json.loads(raw_output)
        status = detect_json.get("status", "")
    except (json.JSONDecodeError, ValueError):
        return {
            "branch": "branch2_detect",
            "status": "unparseable",
            "router_action": "emit_DRAKE_UNAVAILABLE",
            "raw_detect_output": raw_output,
        }

    # Validate status against manifest-known literals
    if known_literals and status not in known_literals:
        # Unknown status literal — treat as unparseable (schema drift)
        return {
            "branch": "branch2_detect",
            "status": "unparseable",
            "router_action": "emit_DRAKE_UNAVAILABLE",
            "raw_detect_output": raw_output,
        }

    return {
        "branch": "branch2_detect",
        "status": status,
        "router_action": _router_action(status),
        "raw_detect_output": raw_output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DRAKE installation state reporter for /dark-matter-constraints router.",
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to router_contract.json (default: auto-resolved).",
    )
    args = parser.parse_args()

    result = detect_drake(
        config_path=args.config,
        manifest_path=args.manifest,
    )

    print(json.dumps(result))
    sys.exit(0)  # Always 0 — state report, not a gate


if __name__ == "__main__":
    main()
