#!/usr/bin/env bash
# Detect whether HiggsTools (HiggsBounds + HiggsSignals) is installed and
# registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: higgsbounds_path + hb_version match the pin.
#      (Note: this skill registers higgsbounds_path / higgssignals_path;
#      the canonical "main" path is higgsbounds_path.)
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = HBwithSPheno binary present in HB build dir.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_HB_VERSION:-5.10.2}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
recorded_version=""
if [ -f "$cfg" ]; then
  read -r recorded_path recorded_version < <(python3 -c '
import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("higgsbounds_path",""), d.get("hb_version",""))
except Exception:
  print(" ")
' "$cfg")
fi

# Fast path: use config.higgsbounds_path + config.hb_version (note: keys
# are higgsbounds_path/hb_version, not higgstools_path/_version, so we
# bypass _detect_common.sh's tool-prefix scheme and check directly.
if [ -n "$recorded_path" ] && [ "$recorded_version" = "$PINNED_VERSION" ] && [ -e "$recorded_path" ]; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: HBwithSPheno binary check.
[ -n "$recorded_path" ] || exit 1
[ -x "$recorded_path/HBwithSPheno" ] || [ -x "$recorded_path/HiggsBounds" ] || exit 1
