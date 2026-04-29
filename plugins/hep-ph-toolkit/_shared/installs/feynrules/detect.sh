#!/usr/bin/env bash
# Detect whether FeynRules is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: feynrules_path + feynrules_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = $feynrules_path/FeynRules.m present (cheap; no
#      wolframscript invocation).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FEYNRULES_VERSION:-2.3.49}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("feynrules_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" feynrules "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: file-presence + version-drift check.
[ -n "$recorded_path" ] || exit 1
[ -f "$recorded_path/FeynRules.m" ] || exit 1
# Version-drift: FeynRules ships under FeynRules-2.3.49/ — match the path.
set +e
bash "$SHARED/_detect_common.sh" path-version-match "$recorded_path" "$PINNED_VERSION"
rc=$?
set -e
[ $rc -eq 1 ] && exit 1
exit 0
