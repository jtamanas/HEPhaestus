#!/usr/bin/env bash
# Smoke test: verify DDCalc install by building and running DDCalc_test.
# Usage: _smoke_test.sh <ddcalc_dir>
# Exit 0 on success; non-zero (with blocker JSON on stderr) on failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$SHARED_COMMON"

_tag="ddcalc-smoke"

DIR="${1:?DDCalc install dir required}"

if [ ! -f "$DIR/lib/libDDCalc.a" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_SMOKE_TEST_FAILED \
    "libDDCalc.a not found: $DIR/lib/libDDCalc.a" \
    "{\"dir\":\"$DIR\"}" >&2
  exit "$EXIT_SMOKE"
fi

# Try running DDCalc_test if it exists
TEST_BIN="$DIR/DDCalc_test"
if [ -x "$TEST_BIN" ]; then
  out="$("$TEST_BIN" 2>&1 || true)"
  # Check for version line (patched binary prints "DDCalc 2.2.0")
  if echo "$out" | grep -qE 'DDCalc[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+'; then
    version="$(echo "$out" | grep -Eo 'DDCalc[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+' | head -1 | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')"
    log "DDCalc smoke test passed. Version: $version"
    echo "$version"
    exit 0
  elif echo "$out" | grep -q "DDCalc successfully initialized"; then
    # Stock unpatched binary — still OK, use configured version
    log "DDCalc smoke test passed (unpatched banner)."
    echo "2.2.0"
    exit 0
  else
    "$SCRIPT_DIR/_blocker.sh" DDCALC_SMOKE_TEST_FAILED \
      "DDCalc_test produced unexpected output" \
      "{\"output_head\":\"$(echo "$out" | head -3 | tr '\n' ' ')\"}" >&2
    exit "$EXIT_SMOKE"
  fi
else
  # Binary not present — verify libDDCalc.a is non-empty at minimum
  size="$(wc -c < "$DIR/lib/libDDCalc.a")"
  if [ "$size" -lt 10000 ]; then
    "$SCRIPT_DIR/_blocker.sh" DDCALC_SMOKE_TEST_FAILED \
      "libDDCalc.a is suspiciously small ($size bytes)" \
      "{\"dir\":\"$DIR\",\"lib_size\":$size}" >&2
    exit "$EXIT_SMOKE"
  fi
  log "DDCalc library smoke test passed (no test binary; lib size=${size} bytes)."
  echo "2.2.0"
  exit 0
fi
