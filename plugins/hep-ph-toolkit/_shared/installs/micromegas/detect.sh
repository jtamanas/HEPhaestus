#!/usr/bin/env bash
# Detect whether micrOMEGAs is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: micromegas_path + micromegas_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = sources/ + CalcHEP_src/ markers via _probe.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_MICROMEGAS_VERSION:-6.0.5}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("micromegas_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" micromegas "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: tool-specific binary check.
[ -n "$recorded_path" ] || exit 1
[ -d "$recorded_path/sources" ] || exit 1
[ -d "$recorded_path/CalcHEP_src" ] || exit 1
