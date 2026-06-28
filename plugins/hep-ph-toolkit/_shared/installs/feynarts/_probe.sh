#!/usr/bin/env bash
# detect_feynarts.sh — scan for FeynArts installations.
#
# Usage:
#   detect_feynarts.sh detect   — JSON status to stdout
#   (or source and call detect_feynarts_path / detect_feynarts_status)
#
# Outputs one of:
#   {"status":"configured","path":"...","version":"3.11"}
#   {"status":"found","path":"..."}
#   {"status":"ambiguous","paths":["...",  "..."]}
#   {"status":"missing"}
#
# Exit codes: always 0 (status encoded in JSON).

set -euo pipefail

_LOG_TAG="detect_feynarts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 4 levels up from this file lands at plugins/:
# plugins/hep-ph-toolkit/_shared/installs/feynarts/_probe.sh → plugins/shared/
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Candidate directories to scan for FeynArts.m
# find returns full file paths; we take dirname to get the containing directory.
_feynarts_candidate_dirs() {
  local candidates=()

  # $UserBaseDirectory/Applications roots, across products and OSes. The
  # directory name differs by product/version:
  #   - macOS Wolfram Engine:      ~/Library/WolframEngine/Applications  (real
  #                                install location on this machine)
  #   - macOS Mathematica/Wolfram: ~/Library/Wolfram/Applications
  #   - macOS Mathematica (legacy):~/Library/Mathematica/Applications
  #   - Linux Wolfram Engine:      ~/.WolframEngine/Applications
  #   - Linux Mathematica:         ~/.Mathematica/Applications
  # Scanning the wrong sibling (e.g. Wolfram vs WolframEngine) is the classic
  # false-"missing": detect.sh resolves $UserBaseDirectory live, but this
  # standalone scanner must enumerate all known roots explicitly.
  local app_roots=(
    "$HOME/Library/WolframEngine/Applications"
    "$HOME/Library/Wolfram/Applications"
    "$HOME/Library/Mathematica/Applications"
    "$HOME/.WolframEngine/Applications"
    "$HOME/.Mathematica/Applications"
  )
  local apps
  for apps in "${app_roots[@]}"; do
    [ -d "$apps" ] || continue
    while IFS= read -r -d '' f; do
      local d
      d="$(dirname "$f")"
      candidates+=("$d")
    done < <(find "$apps" -maxdepth 2 -name "FeynArts.m" -print0 2>/dev/null || true)
  done

  # Additional common paths
  local extra_paths=(
    "/usr/local/share/FeynArts"
    "$HOME/FeynArts"
  )
  for p in "${extra_paths[@]}"; do
    [ -f "$p/FeynArts.m" ] && candidates+=("$p")
  done

  # Deduplicate (handle empty array safely)
  if [ "${#candidates[@]}" -gt 0 ]; then
    printf '%s\n' "${candidates[@]}" | sort -u
  fi
}

# detect_feynarts_path: returns configured path from config, or "" if not set
detect_feynarts_configured() {
  local path
  path="$(config_get feynarts_path)"
  if [ -n "$path" ] && [ -f "$path/FeynArts.m" ]; then
    echo "$path"
    return 0
  fi
  echo ""
}

# Main detect logic — prints JSON status
detect_feynarts_status() {
  # 1. Check config first
  local configured_path
  configured_path="$(detect_feynarts_configured)"
  if [ -n "$configured_path" ]; then
    local version
    version="$(config_get feynarts_version || true)"
    printf '{"status":"configured","path":"%s","version":"%s"}\n' \
      "$configured_path" "${version:-unknown}"
    return 0
  fi

  # 2. Scan candidates
  local found_paths=()
  while IFS= read -r p; do
    [ -n "$p" ] && found_paths+=("$p")
  done < <(_feynarts_candidate_dirs)

  local n="${#found_paths[@]}"
  if [ "$n" -eq 0 ]; then
    printf '{"status":"missing"}\n'
    return 0
  fi

  if [ "$n" -eq 1 ]; then
    printf '{"status":"found","path":"%s"}\n' "${found_paths[0]}"
    return 0
  fi

  # Multiple found — ambiguous
  python3 - "${found_paths[@]}" <<'PY'
import json, sys
paths = sys.argv[1:]
print(json.dumps({"status": "ambiguous", "paths": paths}, separators=(",", ":")))
PY
}

# If executed directly, run detect
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  subcmd="${1:-detect}"
  case "$subcmd" in
    detect) detect_feynarts_status ;;
    *) echo "Usage: $0 detect" >&2; exit 1 ;;
  esac
fi
