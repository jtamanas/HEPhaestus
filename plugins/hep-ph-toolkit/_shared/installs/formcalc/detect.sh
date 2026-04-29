#!/usr/bin/env bash
# Detect whether FormCalc is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: formcalc_path + formcalc_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = wolframscript probe_formcalc.wls.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FORMCALC_VERSION:-9.10}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("formcalc_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" formcalc "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: Wolfram-driven probe via probe_formcalc.wls.
[ -n "$recorded_path" ] || exit 1
command -v wolframscript >/dev/null 2>&1 || exit 1
wolframscript -file "$SCRIPT_DIR/probe_formcalc.wls" "$recorded_path" >/dev/null 2>&1
