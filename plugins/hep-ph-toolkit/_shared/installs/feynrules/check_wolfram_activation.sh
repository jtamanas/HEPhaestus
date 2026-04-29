#!/usr/bin/env bash
# check_wolfram_activation.sh — probe wolframscript for activation status.
# Reads wolfram_engine_path from config (or scans); runs `wolframscript -code '1+1'`;
# pipes stdout+stderr to _activation_parse.py and prints the resulting JSON.
# Always exits 0 — activation status is encoded in the JSON, not the exit code.
#
# JSON output:
#   {"status":"ok"}
#   {"status":"activation_required","message":"...","user_instruction":"..."}
#   {"status":"error","detail":"..."}
#   {"status":"missing"}   — wolframscript binary not found/configured
set -euo pipefail

_LOG_TAG="check_wolfram_activation"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Source detect_wolfram.sh to get detect_wolfram_path().
# shellcheck source=detect_wolfram.sh
. "$SCRIPT_DIR/detect_wolfram.sh"

main() {
  local ws
  ws="$(detect_wolfram_path)"

  if [ -z "$ws" ]; then
    printf '{"status":"missing"}\n'
    exit 0
  fi

  local probe_out probe_rc
  probe_out="$("$ws" -code '1+1' 2>&1)" && probe_rc=0 || probe_rc=$?

  printf '%s' "$probe_out" \
    | python3 "$SCRIPT_DIR/_activation_parse.py" "$probe_rc"
}

main "$@"
