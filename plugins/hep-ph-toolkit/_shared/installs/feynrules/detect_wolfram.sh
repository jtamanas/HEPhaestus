#!/usr/bin/env bash
# detect_wolfram.sh — standalone Wolfram Engine detection for feynrules-install.
# Decoupled from hep-ph-demo/install_wolfram.sh and sarah-install (self-contained copy).
# Sources _common.sh for config_get.
#
# Usage (internal; sourced or called by install_feynrules.sh):
#   detect_wolfram_path    — prints wolframscript path if found, empty if not
set -euo pipefail

_LOG_TAG="detect_wolfram"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

wolfram_probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  "$bin" -code 'Print[$Version]' 2>/dev/null \
    | grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1
}

wolfram_scan_candidates() {
  local candidates=(
    "/Applications/Wolfram.app/Contents/MacOS/wolframscript"
    "/Applications/Wolfram Engine.app/Contents/MacOS/wolframscript"
    "/Applications/Mathematica.app/Contents/MacOS/wolframscript"
    "/usr/local/bin/wolframscript"
    "/opt/Wolfram/WolframEngine/Executables/wolframscript"
  )
  if [ -d /usr/local/Wolfram/WolframEngine ]; then
    while IFS= read -r -d '' p; do candidates+=("$p"); done < <(
      find /usr/local/Wolfram/WolframEngine -maxdepth 3 -name wolframscript -print0 2>/dev/null || true
    )
  fi
  local which_hit
  which_hit="$(command -v wolframscript || true)"
  [ -n "$which_hit" ] && candidates+=("$which_hit")

  for c in "${candidates[@]}"; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

# detect_wolfram_path: prints the wolframscript path from config or scan; empty if absent.
detect_wolfram_path() {
  local path
  path="$(config_get wolfram_engine_path)"
  if [ -n "$path" ] && [ -x "$path" ]; then
    echo "$path"
    return 0
  fi
  local found
  if found="$(wolfram_scan_candidates)"; then
    echo "$found"
    return 0
  fi
  echo ""
}

# If executed directly (not sourced), run a detect and print JSON.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  path="$(detect_wolfram_path)"
  if [ -n "$path" ]; then
    version="$(wolfram_probe_version "$path" || true)"
    printf '{"status":"found","path":"%s","version":"%s"}\n' "$path" "$version"
  else
    printf '{"status":"missing"}\n'
  fi
fi
