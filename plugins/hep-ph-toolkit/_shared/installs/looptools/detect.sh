#!/usr/bin/env bash
# Detect whether LoopTools is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: looptools_path + looptools_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."

# Pinned version. Bump in lockstep with INSTALL.md.
PINNED_VERSION="${HEPPH_LOOPTOOLS_VERSION:-2.16}"

# Read the recorded path from config without touching disk further.
cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("looptools_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" looptools "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: nothing in config, version drift, or HEPPH_FORCE_PROBE=1.
[ -n "$recorded_path" ] || exit 1
bash "$SCRIPT_DIR/probe_looptools.sh" "$recorded_path" >/dev/null 2>&1
