#!/usr/bin/env bash
# check_wolfram.sh — thin activation probe for drake-install.
#
# Reads wolfram_engine_path from config, runs `wolframscript -code '1+1'`,
# parses the combined stdout+stderr, and prints one of:
#   {"status":"ok"}
#   {"status":"activation_required","message":"...","user_instruction":"..."}
#   {"status":"missing"}
#   {"status":"error","detail":"..."}
#
# Follows sarah-install's pattern but does NOT copy its files — this is a
# standalone, dependency-free probe.
set -euo pipefail

_LOG_TAG="check_wolfram"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# resolve_wolfram: prefer wolfram_engine_path in config, fall back to PATH.
resolve_wolfram() {
  local path
  path="$(config_get wolfram_engine_path)"
  if [ -n "$path" ] && [ -x "$path" ]; then
    echo "$path"
    return 0
  fi
  local which_hit
  which_hit="$(command -v wolframscript || true)"
  if [ -n "$which_hit" ] && [ -x "$which_hit" ]; then
    echo "$which_hit"
    return 0
  fi
  echo ""
}

main() {
  local ws
  ws="$(resolve_wolfram)"
  if [ -z "$ws" ]; then
    printf '{"status":"missing"}\n'
    exit 0
  fi

  local probe_out probe_rc
  probe_out="$("$ws" -code '1+1' 2>&1)" && probe_rc=0 || probe_rc=$?

  # Parse inline — no external python module; keeps this file self-contained.
  python3 - "$probe_rc" <<PY
import json, sys
rc = int(sys.argv[1])
out = """$(printf '%s' "$probe_out" | sed 's/"/\\"/g')"""
low = out.lower()
if rc == 0 and out.strip() == "2":
    print(json.dumps({"status": "ok"}))
elif "activat" in low or "license" in low or "entitlement" in low:
    print(json.dumps({
        "status": "activation_required",
        "message": "Wolfram Engine is installed but needs activation.",
        "user_instruction": "Run \`wolframscript --activate\` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun _shared/installs/drake/install.sh.",
    }))
elif rc != 0:
    print(json.dumps({"status": "error", "detail": out[:500]}))
else:
    # Non-"2" stdout with rc 0 — weirdness, but not a fatal.
    print(json.dumps({"status": "error", "detail": out[:500]}))
PY
}

main "$@"
