#!/usr/bin/env bash
# Detect whether SPheno is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: spheno_path + spheno_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = bin/SPheno exists and is executable.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_SPHENO_VERSION:-4.0.5}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("spheno_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" spheno "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: SPheno binary present + version-drift check.
[ -n "$recorded_path" ] || exit 1
[ -x "$recorded_path" ] || exit 1
# SPheno installs typically live under SPheno-4.0.5/ with a versioned
# dir name. rc=1 = drift, rc=0 = match, rc=2 = no version stamp parseable.
set +e
bash "$SHARED/_detect_common.sh" path-version-match "$recorded_path" "$PINNED_VERSION"
rc=$?
set -e
[ $rc -eq 1 ] && exit 1
exit 0
