#!/usr/bin/env bash
# Detect whether HiggsTools (HiggsBounds + HiggsSignals) is installed and
# registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: keys vary by backend.
#      Legacy backend  → higgsbounds_path + higgsbounds_version
#      Unified backend → higgstools_path  + higgstools_version
#      For backwards compatibility, hb_version is also accepted as a
#      synonym for higgsbounds_version (older configs).
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = HBwithSPheno / HiggsBounds binary present in build dir.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_HB_VERSION="${HEPPH_HB_VERSION:-5.10.2}"
PINNED_HT_VERSION="${HEPPH_HT_VERSION:-1.2}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
backend=""
legacy_path=""; legacy_version=""
unified_path=""; unified_version=""
if [ -f "$cfg" ]; then
  # Read all relevant fields in one shot. Lines: backend, hb_path,
  # hb_version (preferring higgsbounds_version then hb_version),
  # ht_path, ht_version.
  raw="$(python3 - "$cfg" <<'PY' 2>/dev/null || true
import json, sys
try:
  with open(sys.argv[1]) as f: d = json.load(f)
except Exception:
  print(); print(); print(); print(); print(); sys.exit(0)
print(d.get("higgstools_backend", ""))
print(d.get("higgsbounds_path", ""))
print(d.get("higgsbounds_version", "") or d.get("hb_version", ""))
print(d.get("higgstools_path", ""))
print(d.get("higgstools_version", ""))
PY
  )"
  backend="$(printf '%s\n' "$raw" | sed -n '1p')"
  legacy_path="$(printf '%s\n' "$raw" | sed -n '2p')"
  legacy_version="$(printf '%s\n' "$raw" | sed -n '3p')"
  unified_path="$(printf '%s\n' "$raw" | sed -n '4p')"
  unified_version="$(printf '%s\n' "$raw" | sed -n '5p')"
fi

# Fast path. Backend may be unset on older configs; default to legacy.
case "${backend:-legacy}" in
  unified)
    if [ -n "$unified_path" ] && [ "$unified_version" = "$PINNED_HT_VERSION" ] && [ -e "$unified_path" ]; then
      [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
    fi
    recorded_path="$unified_path"
    ;;
  *)
    if [ -n "$legacy_path" ] && [ "$legacy_version" = "$PINNED_HB_VERSION" ] && [ -e "$legacy_path" ]; then
      [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
    fi
    recorded_path="$legacy_path"
    ;;
esac

# Slow path: HBwithSPheno / HiggsBounds binary check.
[ -n "$recorded_path" ] || exit 1
[ -x "$recorded_path/HBwithSPheno" ] || [ -x "$recorded_path/HiggsBounds" ] || exit 1
