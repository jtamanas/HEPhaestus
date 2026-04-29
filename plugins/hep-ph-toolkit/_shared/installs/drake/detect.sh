#!/usr/bin/env bash
# Detect whether DRAKE is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: drake_path + drake_version match the pin.
#   2. Slow probe: existing probe_drake.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_DRAKE_VERSION:-1.0}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("drake_path",""))
except Exception: pass' "$cfg")"
fi

if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" drake "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

[ -n "$recorded_path" ] || exit 1
exec bash "$SCRIPT_DIR/probe_drake.sh" "$recorded_path"
