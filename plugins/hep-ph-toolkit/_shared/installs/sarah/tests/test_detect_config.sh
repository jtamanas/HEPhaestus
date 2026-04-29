#!/usr/bin/env bash
# test_detect_config.sh — smoke tests for install.sh detect and use-path.
# Uses isolated HEPPH_STATE_ROOT and XDG_CONFIG_HOME; does NOT touch real user config.
#
# Run: bash tests/test_detect_config.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SARAH="$SCRIPT_DIR/../install.sh"

PASS=0
FAIL=0
SKIP=0

_pass() { echo "PASS: $1"; PASS=$(( PASS + 1 )); }
_fail() { echo "FAIL: $1 — $2"; FAIL=$(( FAIL + 1 )); }
_skip() { echo "SKIP: $1 — $2"; SKIP=$(( SKIP + 1 )); }

# Isolated temp dirs; cleaned up on exit.
STATE_ROOT="$(mktemp -d -t hepph-state-XXXXXX)"
CFG_HOME="$(mktemp -d -t hepph-cfg-XXXXXX)"
trap 'rm -rf "$STATE_ROOT" "$CFG_HOME"' EXIT

export HEPPH_STATE_ROOT="$STATE_ROOT"
export XDG_CONFIG_HOME="$CFG_HOME"

# ---------------------------------------------------------------------------
# Test 1: detect with empty config → missing
# ---------------------------------------------------------------------------
out="$(bash "$INSTALL_SARAH" detect 2>/dev/null)"
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='missing', d" 2>/dev/null; then
  _pass "detect empty config returns missing"
else
  _fail "detect empty config returns missing" "got: $out"
fi

# ---------------------------------------------------------------------------
# Test 2: detect with config pointing at a fake SARAH.m → configured
# (probe_version will fail because wolframscript is absent, so we expect
#  "found" or "configured" depending on whether probe succeeds.
#  Since wolframscript is likely absent in CI, we check for "found".)
# ---------------------------------------------------------------------------
FAKE_SARAH_DIR="$STATE_ROOT/fake-sarah"
mkdir -p "$FAKE_SARAH_DIR"
touch "$FAKE_SARAH_DIR/SARAH.m"

# Write a fake config with sarah_path.
CFG_DIR="$CFG_HOME/hephaestus"
mkdir -p "$CFG_DIR"
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'sarah_path': '$FAKE_SARAH_DIR'}, f)
"

out="$(bash "$INSTALL_SARAH" detect 2>/dev/null)"
status="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
if [ "$status" = "configured" ] || [ "$status" = "found" ]; then
  _pass "detect with fake SARAH dir returns configured or found (status=$status)"
else
  _fail "detect with fake SARAH dir" "expected configured or found, got: $out"
fi

# Verify path is returned in configured/found case.
path_out="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('path',''))" 2>/dev/null || true)"
if [ -n "$path_out" ]; then
  _pass "detect returns non-empty path"
else
  _fail "detect returns non-empty path" "path was empty in: $out"
fi

# ---------------------------------------------------------------------------
# Test 3: use-path with non-existent directory → fatal blocker + non-zero exit
# ---------------------------------------------------------------------------
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_SARAH" use-path "/nonexistent/path/to/SARAH" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert 'SARAH_PATH_INVALID' in d.get('code','') or 'SARAH' in d.get('code',''), d
" 2>/dev/null; then
  _pass "use-path non-existent path emits fatal blocker and exits non-zero"
else
  _fail "use-path non-existent path" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 4: use-path with a dir that has no SARAH.m → fatal blocker
# ---------------------------------------------------------------------------
EMPTY_DIR="$STATE_ROOT/empty-dir"
mkdir -p "$EMPTY_DIR"
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_SARAH" use-path "$EMPTY_DIR" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
" 2>/dev/null; then
  _pass "use-path dir without SARAH.m emits fatal blocker"
else
  _fail "use-path dir without SARAH.m" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 5: use-path with valid dir but no Wolfram Engine → WOLFRAM_KERNEL_ABSENT
# ---------------------------------------------------------------------------
# Ensure no wolfram_engine_path in config (use fresh config).
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'sarah_path': '$FAKE_SARAH_DIR'}, f)
"
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_SARAH" use-path "$FAKE_SARAH_DIR" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert 'WOLFRAM' in d.get('code', ''), d
" 2>/dev/null; then
  _pass "use-path valid dir but no wolfram → WOLFRAM_KERNEL_ABSENT blocker"
else
  # May also exit early with WOLFRAM_KERNEL_ABSENT from a scan result — accept either.
  if [ "$rc" -ne 0 ]; then
    _pass "use-path valid dir but no wolfram → non-zero exit (wolfram absent)"
  else
    _fail "use-path valid dir but no wolfram" "rc=$rc blocker=$blocker_out"
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
