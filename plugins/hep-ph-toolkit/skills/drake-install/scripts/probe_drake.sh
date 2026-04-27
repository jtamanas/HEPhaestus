#!/usr/bin/env bash
# probe_drake.sh — run the WIMP benchmark smoke test against a DRAKE tree.
#
# Usage: probe_drake.sh <drake_dir> [<wolframscript_path>]
#
# Output (stdout, JSON):
#   {"status":"ok","version":"1.0 (assumed)"}
#   {"status":"activation_required",...}
#   {"status":"failed","detail":"..."}
#
# Always exits 0 — the status is encoded in the JSON. Callers that need a
# non-zero exit on failure should inspect the JSON.
#
# Log: combined stdout+stderr from wolframscript is written to /tmp/drake_smoke.log.
set -euo pipefail

_LOG_TAG="probe_drake"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

SMOKE_LOG="/tmp/drake_smoke.log"

main() {
  local drake_dir="${1:-}"
  local ws="${2:-}"

  if [ -z "$drake_dir" ] || [ ! -d "$drake_dir" ]; then
    printf '{"status":"failed","detail":"drake_dir not a directory"}\n'
    exit 0
  fi

  local test_script="$drake_dir/test/test.wls"
  if [ ! -f "$test_script" ]; then
    printf '{"status":"failed","detail":"test/test.wls missing in %s"}\n' "$drake_dir"
    exit 0
  fi

  if [ -z "$ws" ]; then
    ws="$(config_get wolfram_engine_path)"
  fi
  if [ -z "$ws" ] || [ ! -x "$ws" ]; then
    ws="$(command -v wolframscript || true)"
  fi
  if [ -z "$ws" ] || [ ! -x "$ws" ]; then
    printf '{"status":"failed","detail":"wolframscript not available"}\n'
    exit 0
  fi

  # Run the canonical WIMP benchmark from the paper appendix A.3.
  # cd into the drake dir so relative paths inside test.wls resolve.
  local rc=0
  ( cd "$drake_dir/test" && "$ws" test.wls WIMP bm_WIMP settings_WIMP ) \
    >"$SMOKE_LOG" 2>&1 || rc=$?

  local out
  out="$(cat "$SMOKE_LOG" 2>/dev/null || true)"

  python3 - "$rc" "$SMOKE_LOG" <<'PY'
import json, sys, os
rc = int(sys.argv[1])
log_path = sys.argv[2]
try:
    with open(log_path) as f:
        out = f.read()
except Exception:
    out = ""
low = out.lower()
# DRAKE has no formal version string in its source; report assumed.
version = "1.0 (assumed)"
if "activat" in low or "license required" in low or "entitlement" in low:
    print(json.dumps({
        "status": "activation_required",
        "message": "Wolfram Engine is installed but needs activation.",
        "user_instruction": "Run `wolframscript --activate` and rerun /drake-install.",
    }))
elif rc == 0 and out.strip():
    print(json.dumps({"status": "ok", "version": version}))
else:
    detail = (out[-400:] or f"exit={rc}").replace("\n", " ")
    print(json.dumps({"status": "failed", "detail": detail}))
PY
}

main "$@"
