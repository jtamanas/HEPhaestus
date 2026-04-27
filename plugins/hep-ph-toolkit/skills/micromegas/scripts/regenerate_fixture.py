"""regenerate_fixture.py — regenerate the singletDM golden fixture.

GATED: requires HEPPH_RUN_NETWORK_TESTS=1 and a configured micrOMEGAs installation.

Runs the micrOMEGAs-shipped Singlet_DM/ benchmark project with its default inputs
(unmodified). Captures stdout and writes:
  - tests/fixtures/stdout_singletDM.txt  (raw stdout from real Singlet_DM/main)

The golden JSON (summary_singletDM.json) is produced separately by the agent:
  1. Run this script to update stdout_singletDM.txt.
  2. The agent reads stdout_singletDM.txt per the SKILL.md §"Reading micrOMEGAs output
     (agent-driven)" patterns and writes summary_singletDM.json.
  3. Commit both files together.

This script does NOT extract scalar fields — that is the agent's job, not a
regex function in a committed script.

Usage:
    HEPPH_RUN_NETWORK_TESTS=1 python3 regenerate_fixture.py
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import os
import subprocess
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _SCRIPT_DIR.parent / "tests" / "fixtures"


def _load_config() -> dict:
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {}


def main():
    if os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") != "1":
        print("SKIP: HEPPH_RUN_NETWORK_TESTS not set to 1", file=sys.stderr)
        sys.exit(0)

    config = _load_config()
    micromegas_path = config.get("micromegas_path", "")
    if not micromegas_path:
        print("ERROR: micromegas_path not configured. Run /micromegas-install first.", file=sys.stderr)
        sys.exit(1)

    singletdm_dir = Path(micromegas_path) / "Singlet_DM"
    if not singletdm_dir.exists():
        # Try alternate shipped name
        for candidate in Path(micromegas_path).iterdir():
            if candidate.is_dir() and "singlet" in candidate.name.lower():
                singletdm_dir = candidate
                break
        else:
            print(f"ERROR: Singlet_DM/ not found under {micromegas_path}", file=sys.stderr)
            sys.exit(1)

    print(f"Using Singlet_DM dir: {singletdm_dir}")

    # Build if needed
    if not (singletdm_dir / "main").exists():
        print("Building Singlet_DM/main...")
        result = subprocess.run(
            ["make", "main"],
            cwd=str(singletdm_dir),
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: make failed: {result.stderr[:500]}", file=sys.stderr)
            sys.exit(1)

    # Run the shipped benchmark with default inputs
    print("Running Singlet_DM benchmark...")
    result = subprocess.run(
        ["./main"],
        cwd=str(singletdm_dir),
        capture_output=True, text=True,
        env={**os.environ, "HEPPH_MICROMEGAS_SEED": "42"},
        timeout=120,
    )

    if result.returncode != 0:
        print(f"WARNING: Singlet_DM/main exited {result.returncode}", file=sys.stderr)
        print(f"stderr: {result.stderr[:500]}", file=sys.stderr)

    # Write raw stdout fixture — pure capture, no extraction
    stdout_fixture = _FIXTURES_DIR / "stdout_singletDM.txt"
    stdout_fixture.write_text(result.stdout)
    print(f"Written: {stdout_fixture}")
    print()
    print("Next step: have the agent read stdout_singletDM.txt per SKILL.md")
    print("§'Reading micrOMEGAs output (agent-driven)' and write summary_singletDM.json.")
    print("Then commit both files.")


if __name__ == "__main__":
    main()
