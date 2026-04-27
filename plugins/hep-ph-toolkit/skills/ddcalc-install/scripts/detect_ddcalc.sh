#!/usr/bin/env bash
# Detect whether DDCalc is installed and configured.
# Usage: ./detect_ddcalc.sh
# Stdout: JSON {"status":"configured"|"found"|"missing", "path":"...", "version":"..."}
# Exit: 0 always (detect never fails, just reports)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$SHARED_COMMON"

_tag="ddcalc-detect"

# ── 1. Check config ────────────────────────────────────────────────────────────
ddcalc_path="$(config_get ddcalc_path)"
ddcalc_version="$(config_get ddcalc_version)"

_check_dir() {
  local d="$1"
  [ -d "$d" ] && \
    [ -f "$d/lib/libDDCalc.a" -o -f "$d/libDDCalc.a" ] && \
    return 0
  return 1
}

if [ -n "$ddcalc_path" ] && _check_dir "$ddcalc_path"; then
  printf '{"status":"configured","path":"%s","version":"%s"}\n' \
    "$ddcalc_path" "$ddcalc_version"
  exit 0
fi

# ── 2. Scan candidates ─────────────────────────────────────────────────────────
_scan_candidates() {
  local state_root="${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}"
  local candidates=(
    "$state_root/tools/DDCalc"
    "$state_root/tools/ddcalc"
    "$HOME/DDCalc"
    "$HOME/ddcalc"
    "/usr/local/lib/DDCalc"
  )
  for c in "${candidates[@]}"; do
    if _check_dir "$c"; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

found_path="$(_scan_candidates || true)"
if [ -n "$found_path" ]; then
  printf '{"status":"found","path":"%s"}\n' "$found_path"
  exit 0
fi

printf '{"status":"missing"}\n'
exit 0
