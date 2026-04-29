#!/usr/bin/env bash
# _probe.sh — probe micrOMEGAs installation state.
#
# Emits one-line JSON to stdout:
#   {"status":"configured","path":"...","version":"..."}
#   {"status":"found","path":"...","version":"..."}  (path valid but not in config)
#   {"status":"missing"}
#
# Exit 0 in all three cases.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
    SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
. "$SHARED_COMMON"

_LOG_TAG="micromegas-detect"

_parse_version() {
  # Parse version from $path/include/VERSION, fallback to man/*.txt
  local path="$1"
  local ver=""
  if [ -f "$path/include/VERSION" ]; then
    ver="$(head -1 "$path/include/VERSION" | tr -d '[:space:]')"
  fi
  if [ -z "$ver" ] && ls "$path"/man/*.txt >/dev/null 2>&1; then
    ver="$(grep -h 'version' "$path"/man/*.txt 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  fi
  echo "${ver:-unknown}"
}

_probe_path() {
  local path="$1"
  [ -d "$path/sources" ] && [ -d "$path/CalcHEP_src" ] && return 0
  return 1
}

# ── Configured path from config ──────────────────────────────────────────────
configured_path="$(config_get micromegas_path 2>/dev/null || true)"

if [ -n "$configured_path" ]; then
  if _probe_path "$configured_path"; then
    ver="$(_parse_version "$configured_path")"
    printf '{"status":"configured","path":"%s","version":"%s"}\n' \
      "$configured_path" "$ver"
    exit 0
  else
    warn "Config has micromegas_path=$configured_path but path is invalid; treating as missing."
  fi
fi

# ── Well-known fallback locations ─────────────────────────────────────────────
for candidate in \
    "$HOME/micrOMEGAs/micromegas_6.0.5" \
    "$HOME/micromegas_6.0.5" \
    "/opt/micromegas_6.0.5" \
    "/usr/local/micromegas_6.0.5"
do
  if _probe_path "$candidate" 2>/dev/null; then
    ver="$(_parse_version "$candidate")"
    printf '{"status":"found","path":"%s","version":"%s"}\n' \
      "$candidate" "$ver"
    exit 0
  fi
done

printf '{"status":"missing"}\n'
exit 0
