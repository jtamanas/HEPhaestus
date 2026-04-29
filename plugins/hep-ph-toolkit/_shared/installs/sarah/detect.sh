#!/usr/bin/env bash
# SARAH detect: composes config-read + Wolfram reachability + activation
# parse + version probe into a single binary exit code.
#
# Exit 0 iff:
#   - sarah_path is registered in config and matches the pinned version, OR
#   - the path on disk holds a SARAH tree, AND
#   - Wolfram is reachable (detect_wolfram.sh → "configured"), AND
#   - Wolfram is activated (check_wolfram_activation.sh → not "activation_required").
# Otherwise exit 1.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("sarah_path",""))
except Exception: pass' "$cfg")"
fi

# Tier 1: config fast path (config + path on disk + version match).
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" sarah "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Tier 2a: Wolfram reachable.
wolfram_status="$(bash "$SCRIPT_DIR/detect_wolfram.sh" 2>/dev/null \
  | python3 -c 'import json,sys
try:
  print(json.load(sys.stdin).get("status",""))
except Exception: pass' || true)"
[ "$wolfram_status" = "configured" ] || exit 1

# Tier 2b: Wolfram activated.
activation_status="$(bash "$SCRIPT_DIR/check_wolfram_activation.sh" 2>/dev/null \
  | python3 -c 'import json,sys
try:
  print(json.load(sys.stdin).get("status",""))
except Exception: pass' || true)"
[ "$activation_status" != "activation_required" ] || exit 1

# Tier 2c: SARAH tree exists at recorded_path.
[ -n "$recorded_path" ] || exit 1
[ -d "$recorded_path" ] || exit 1
# SARAH installs land at <prefix>/SARAH-<version>/SARAH.m; check both shapes.
[ -f "$recorded_path/SARAH.m" ] || [ -f "$recorded_path/SARAH-$PINNED_VERSION/SARAH.m" ] || exit 1
