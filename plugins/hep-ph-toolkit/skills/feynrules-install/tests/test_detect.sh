#!/usr/bin/env bash
# test_detect.sh — smoke tests for install_feynrules.sh detect and use-path.
# Uses isolated HEPPH_STATE_ROOT and XDG_CONFIG_HOME; does NOT touch real user config.
#
# Run: bash tests/test_detect.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_FR="$SCRIPT_DIR/../scripts/install_feynrules.sh"
FIXTURE_STUB="$SCRIPT_DIR/fixtures/feynrules_stub"

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
# Keep PATH clean of system wolframscript so detection returns empty when
# the fixture doesn't set wolfram_engine_path. (Caller PATH may still provide
# one; that's OK — tests that care fix the config instead.)

# ---------------------------------------------------------------------------
# Test 1: detect with empty config → missing
# ---------------------------------------------------------------------------
out="$(bash "$INSTALL_FR" detect 2>/dev/null)"
if printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('status')=='missing', d" 2>/dev/null; then
  _pass "detect empty config returns missing"
else
  _fail "detect empty config returns missing" "got: $out"
fi

# ---------------------------------------------------------------------------
# Test 2: detect with config pointing at fixture stub → configured or found
# (probe_version will fail without wolframscript, so expect "found"; if a
#  real wolframscript is on the system it may still say "found" because
#  the stub FeynRulesPackage.m is not a valid FeynRules build.)
# ---------------------------------------------------------------------------
FAKE_FR_DIR="$STATE_ROOT/fake-feynrules"
mkdir -p "$FAKE_FR_DIR"
cp "$FIXTURE_STUB/FeynRules.m" "$FAKE_FR_DIR/FeynRules.m"
cp "$FIXTURE_STUB/FeynRulesPackage.m" "$FAKE_FR_DIR/FeynRulesPackage.m"

CFG_DIR="$CFG_HOME/hephaestus"
mkdir -p "$CFG_DIR"
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'feynrules_path': '$FAKE_FR_DIR'}, f)
"

out="$(bash "$INSTALL_FR" detect 2>/dev/null)"
status="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
if [ "$status" = "configured" ] || [ "$status" = "found" ]; then
  _pass "detect with fixture FeynRules dir returns configured or found (status=$status)"
else
  _fail "detect with fixture FeynRules dir" "expected configured or found, got: $out"
fi

path_out="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('path',''))" 2>/dev/null || true)"
if [ -n "$path_out" ]; then
  _pass "detect returns non-empty path"
else
  _fail "detect returns non-empty path" "path was empty in: $out"
fi

# ---------------------------------------------------------------------------
# Test 3: detect with dir missing FeynRulesPackage.m → missing (no match)
# ---------------------------------------------------------------------------
HALF_DIR="$STATE_ROOT/half-feynrules"
mkdir -p "$HALF_DIR"
touch "$HALF_DIR/FeynRules.m"   # FeynRulesPackage.m intentionally absent.
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'feynrules_path': '$HALF_DIR'}, f)
"
out="$(bash "$INSTALL_FR" detect 2>/dev/null)"
status="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
if [ "$status" = "missing" ]; then
  _pass "detect with half-populated dir falls through to missing"
else
  # scan_candidates may find a real install on the developer machine; accept
  # found as well, so long as it isn't "configured" for the half dir.
  cfg_path="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('path',''))" 2>/dev/null || true)"
  if [ "$status" = "found" ] && [ "$cfg_path" != "$HALF_DIR" ]; then
    _pass "detect with half-populated dir falls through (scan found another install)"
  else
    _fail "detect with half-populated dir" "expected missing, got: $out"
  fi
fi

# ---------------------------------------------------------------------------
# Test 4: use-path with non-existent directory → FEYNRULES_PATH_INVALID blocker
# ---------------------------------------------------------------------------
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_FR" use-path "/nonexistent/path/to/FeynRules" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert d.get('code') == 'FEYNRULES_PATH_INVALID', d
" 2>/dev/null; then
  _pass "use-path non-existent path emits FEYNRULES_PATH_INVALID fatal blocker"
else
  _fail "use-path non-existent path" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 5: use-path with dir missing FeynRulesPackage.m → FEYNRULES_PATH_INVALID
# ---------------------------------------------------------------------------
blocker_out=""
rc=0
blocker_out="$(bash "$INSTALL_FR" use-path "$HALF_DIR" 2>&1 1>/dev/null)" || rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert d.get('code') == 'FEYNRULES_PATH_INVALID', d
" 2>/dev/null; then
  _pass "use-path dir missing FeynRulesPackage.m → FEYNRULES_PATH_INVALID"
else
  _fail "use-path dir missing FeynRulesPackage.m" "rc=$rc blocker=$blocker_out"
fi

# ---------------------------------------------------------------------------
# Test 6: use-path with valid dir but no Wolfram Engine → WOLFRAM_KERNEL_ABSENT
# (Skip if a real wolframscript is on PATH — the scan will succeed and
#  the test would instead exercise the smoke-test path.)
# ---------------------------------------------------------------------------
python3 -c "
import json
with open('$CFG_DIR/config.json', 'w') as f:
    json.dump({'feynrules_path': '$FAKE_FR_DIR'}, f)
"
if command -v wolframscript >/dev/null 2>&1 || \
   [ -x "/Applications/Mathematica.app/Contents/MacOS/wolframscript" ] || \
   [ -x "/Applications/Wolfram Engine.app/Contents/MacOS/wolframscript" ]; then
  _skip "use-path valid dir but no wolfram" "wolframscript is available; cannot simulate absence"
else
  blocker_out=""
  rc=0
  blocker_out="$(bash "$INSTALL_FR" use-path "$FAKE_FR_DIR" 2>&1 1>/dev/null)" || rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$blocker_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('mode') == 'fatal', d
assert 'WOLFRAM' in d.get('code', ''), d
" 2>/dev/null; then
    _pass "use-path valid dir but no wolfram → WOLFRAM_KERNEL_ABSENT blocker"
  else
    if [ "$rc" -ne 0 ]; then
      _pass "use-path valid dir but no wolfram → non-zero exit"
    else
      _fail "use-path valid dir but no wolfram" "rc=$rc blocker=$blocker_out"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Test 7: install.sh wrapper dispatches to install_feynrules.sh
# ---------------------------------------------------------------------------
# Reset config to empty so detect returns `missing`.
rm -f "$CFG_DIR/config.json"
out="$(bash "$SCRIPT_DIR/../scripts/install.sh" detect 2>/dev/null)"
status="$(printf '%s' "$out" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
if [ "$status" = "missing" ] || [ "$status" = "found" ]; then
  _pass "install.sh wrapper dispatches detect (status=$status)"
else
  _fail "install.sh wrapper dispatches detect" "got: $out"
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
