#!/usr/bin/env bash
# test_detect.sh — smoke tests for drake-install detect and use-path.
# Uses isolated XDG_CONFIG_HOME; does NOT touch real user config.
#
# Run: bash tests/test_detect.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$SCRIPT_DIR/../scripts/install.sh"
FIXTURE_DIR="$SCRIPT_DIR/fixtures/drake_stub"

PASS=0
FAIL=0
SKIP=0

_pass() { echo "PASS: $1"; PASS=$(( PASS + 1 )); }
_fail() { echo "FAIL: $1 — $2"; FAIL=$(( FAIL + 1 )); }
_skip() { echo "SKIP: $1 — $2"; SKIP=$(( SKIP + 1 )); }

# Isolated temp dirs; cleaned up on exit.
CFG_HOME="$(mktemp -d -t hepph-drake-cfg-XXXXXX)"
trap 'rm -rf "$CFG_HOME"' EXIT

export XDG_CONFIG_HOME="$CFG_HOME"
CFG_DIR="$CFG_HOME/hephaestus"
mkdir -p "$CFG_DIR"

# ---------------------------------------------------------------------------
# Test 1: detect with empty config → missing
# ---------------------------------------------------------------------------
out="$(bash "$INSTALL_SH" detect 2>/dev/null)"
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='missing', d" 2>/dev/null; then
  _pass "detect empty config returns missing"
else
  _fail "detect empty config returns missing" "got: $out"
fi

# ---------------------------------------------------------------------------
# Test 2: detect with config pointing at the fixture → found or configured
# (wolframscript is almost certainly absent / unactivated in CI, so smoke
#  test will fail and we fall back to "found".)
# ---------------------------------------------------------------------------
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'drake_path': '$FIXTURE_DIR'}, f)
"

out="$(bash "$INSTALL_SH" detect 2>/dev/null)"
status="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
if [ "$status" = "configured" ] || [ "$status" = "found" ]; then
  _pass "detect with fixture returns configured or found (status=$status)"
else
  _fail "detect with fixture" "expected configured or found, got: $out"
fi

path_out="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('path',''))" 2>/dev/null || true)"
if [ -n "$path_out" ]; then
  _pass "detect returns non-empty path"
else
  _fail "detect returns non-empty path" "path was empty in: $out"
fi

# ---------------------------------------------------------------------------
# Test 3: use-path with non-existent dir → fatal blocker + non-zero exit
# ---------------------------------------------------------------------------
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_SH" use-path "/nonexistent/drake/path" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert 'DRAKE' in d.get('code','') or 'WOLFRAM' in d.get('code',''), d
" 2>/dev/null; then
  _pass "use-path non-existent path emits fatal blocker and exits non-zero"
else
  _fail "use-path non-existent path" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 4: use-path with dir missing test/test.wls → fatal DRAKE_PATH_INVALID
# ---------------------------------------------------------------------------
EMPTY_DIR="$(mktemp -d -t drake-empty-XXXXXX)"
trap 'rm -rf "$CFG_HOME" "$EMPTY_DIR"' EXIT
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_SH" use-path "$EMPTY_DIR" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert d.get('code') == 'DRAKE_PATH_INVALID', d
" 2>/dev/null; then
  _pass "use-path dir without test/test.wls emits DRAKE_PATH_INVALID blocker"
else
  _fail "use-path dir without test/test.wls" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 5: use-path with valid fixture but no wolfram_engine_path →
# WOLFRAM_KERNEL_ABSENT (unless wolframscript happens to be on PATH)
# ---------------------------------------------------------------------------
# Clear config so wolfram_engine_path is empty.
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({}, f)
"
# Neutralize PATH so wolframscript is genuinely absent. Keep python3 reachable
# by prepending its parent dir (install.sh requires python3 >= 3.10).
PY3_DIR="$(dirname "$(command -v python3)")"
SAFE_PATH="$PY3_DIR:/usr/bin:/bin"
blocker_out=""
rc=0
blocker_out="$(PATH="$SAFE_PATH" bash "$INSTALL_SH" use-path "$FIXTURE_DIR" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert d.get('code') == 'WOLFRAM_KERNEL_ABSENT', d
" 2>/dev/null; then
  _pass "use-path valid fixture but no wolfram → WOLFRAM_KERNEL_ABSENT"
else
  # If wolframscript is present in /usr/bin (unlikely), the test will take
  # a different path. Accept any non-zero exit with a fatal blocker.
  if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('mode')=='fatal'" 2>/dev/null; then
    _pass "use-path valid fixture but no wolfram → fatal blocker (non-standard path)"
  else
    _fail "use-path valid fixture but no wolfram" "rc=$rc blocker=$blocker_out"
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "Results: PASS=$PASS FAIL=$FAIL SKIP=$SKIP"
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
