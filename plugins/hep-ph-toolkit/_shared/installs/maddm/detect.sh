#!/usr/bin/env bash
# Detect whether MadDM is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: maddm_path + maddm_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = file-presence (DO NOT call MG5; that triggers a
#      multi-minute interactive install).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_MADDM_VERSION:-3.2.13}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("maddm_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" maddm "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: cheap file-presence probe (DO NOT invoke MG5 — would
# trigger a multi-minute interactive install).
[ -n "$recorded_path" ] || exit 1
[ -f "$recorded_path/maddm_run.py" ] || [ -f "$recorded_path/maddm.py" ] || exit 1
# Version-drift: MadDM has no canonical VERSION file at the plugin
# root, but installs may live under maddm-3.2.13/. Best-effort path
# match: rc=1 = drift, rc=0 = match, rc=2 = no version stamp parseable
# (file-presence stands).
set +e
bash "$SHARED/_detect_common.sh" path-version-match "$recorded_path" "$PINNED_VERSION"
rc=$?
set -e
[ $rc -eq 1 ] && exit 1
exit 0
