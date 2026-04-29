#!/usr/bin/env bash
# Detect whether MadGraph5_aMC@NLO is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: madgraph_path + madgraph_version match the pin
#      and the binary exists on disk.
#   2. Slow probe: defer to the canonical install_mg5.sh detect command
#      (parses --help banner; cold call ~1s).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_MG5_VERSION:-3.5.6}"

# Resolve install_mg5.sh — historically lives under skills/install/scripts/.
INSTALL_MG5="$SCRIPT_DIR/../../../skills/install/scripts/install_mg5.sh"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("madgraph_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path: madgraph_path is the absolute path to the mg5_aMC binary;
# _detect_common.sh checks file existence + recorded version match.
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" madgraph "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi

# Slow path: defer to install_mg5.sh detect (parses --help banner).
if [ -x "$INSTALL_MG5" ]; then
  out="$(bash "$INSTALL_MG5" detect 2>/dev/null || true)"
  status="$(printf '%s' "$out" | python3 -c "import json,sys
try:
  d=json.loads(sys.stdin.read())
  print(d.get('status',''))
except Exception: pass" 2>/dev/null || true)"
  [ "$status" = "configured" ] && exit 0
fi
exit 1
