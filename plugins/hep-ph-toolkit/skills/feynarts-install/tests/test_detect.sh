#!/usr/bin/env bash
# test_detect.sh — unit tests for detect_feynarts.sh
#
# Tests all four status branches: configured, found, missing, ambiguous.
# All always-on (no Wolfram dependency; uses fake tmp HOMEs).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT_SCRIPT="$SCRIPT_DIR/../scripts/detect_feynarts.sh"

PASS=0
FAIL=0

_pass() { printf '  PASS: %s\n' "$1"; PASS=$((PASS + 1)); }
_fail() { printf '  FAIL: %s\n  Expected: %s\n  Got:      %s\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1)); }

# Helper: run detect with a fake HOME
_run_detect() {
  local fake_home="$1"
  local fake_config="${2:-}"
  HOME="$fake_home" \
    XDG_CONFIG_HOME="$fake_home/.config" \
    "${DETECT_SCRIPT}" detect 2>/dev/null
}

echo "=== test_detect.sh: detect_feynarts.sh unit tests ==="

# ------------------------------------------------------------------
# Test 1: missing — empty HOME, no config
# ------------------------------------------------------------------
FAKE_HOME="$(mktemp -d)"
trap 'rm -rf "$FAKE_HOME"' EXIT

OUT="$(_run_detect "$FAKE_HOME")"
if printf '%s' "$OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='missing'" 2>/dev/null; then
  _pass "missing: status==missing"
else
  _fail "missing: status==missing" '{"status":"missing"}' "$OUT"
fi

# ------------------------------------------------------------------
# Test 2: found — single FeynArts install in macOS Applications dir
# ------------------------------------------------------------------
FAKE_HOME2="$(mktemp -d)"
FEYNARTS_DIR="$FAKE_HOME2/Library/Wolfram/Applications/FeynArts-3.11"
mkdir -p "$FEYNARTS_DIR"
touch "$FEYNARTS_DIR/FeynArts.m"
trap 'rm -rf "$FAKE_HOME2"' EXIT

OUT2="$(HOME="$FAKE_HOME2" XDG_CONFIG_HOME="$FAKE_HOME2/.config" "${DETECT_SCRIPT}" detect 2>/dev/null)"
STATUS2="$(printf '%s' "$OUT2" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "PARSE_ERROR")"
if [ "$STATUS2" = "found" ]; then
  _pass "found: single macOS install → status==found"
else
  _fail "found: single macOS install → status==found" "found" "$STATUS2 ($OUT2)"
fi

# ------------------------------------------------------------------
# Test 3: ambiguous — two installs
# ------------------------------------------------------------------
FAKE_HOME3="$(mktemp -d)"
FEYNARTS_DIR3A="$FAKE_HOME3/Library/Wolfram/Applications/FeynArts-3.11"
FEYNARTS_DIR3B="$FAKE_HOME3/Library/Wolfram/Applications/FeynArts-3.10"
mkdir -p "$FEYNARTS_DIR3A" "$FEYNARTS_DIR3B"
touch "$FEYNARTS_DIR3A/FeynArts.m" "$FEYNARTS_DIR3B/FeynArts.m"
trap 'rm -rf "$FAKE_HOME3"' EXIT

OUT3="$(HOME="$FAKE_HOME3" XDG_CONFIG_HOME="$FAKE_HOME3/.config" "${DETECT_SCRIPT}" detect 2>/dev/null)"
STATUS3="$(printf '%s' "$OUT3" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "PARSE_ERROR")"
if [ "$STATUS3" = "ambiguous" ]; then
  _pass "ambiguous: two installs → status==ambiguous"
else
  _fail "ambiguous: two installs → status==ambiguous" "ambiguous" "$STATUS3 ($OUT3)"
fi

# ------------------------------------------------------------------
# Test 4: configured — config has valid feynarts_path
# ------------------------------------------------------------------
FAKE_HOME4="$(mktemp -d)"
FEYNARTS_DIR4="$FAKE_HOME4/Library/Wolfram/Applications/FeynArts-3.11"
mkdir -p "$FEYNARTS_DIR4"
touch "$FEYNARTS_DIR4/FeynArts.m"

CONFIG_DIR4="$FAKE_HOME4/.config/hephaestus"
mkdir -p "$CONFIG_DIR4"
python3 -c "
import json
d = {'feynarts_path': '$FEYNARTS_DIR4', 'feynarts_version': '3.11'}
with open('$CONFIG_DIR4/config.json', 'w') as f:
    json.dump(d, f)
"
trap 'rm -rf "$FAKE_HOME4"' EXIT

OUT4="$(HOME="$FAKE_HOME4" XDG_CONFIG_HOME="$FAKE_HOME4/.config" "${DETECT_SCRIPT}" detect 2>/dev/null)"
STATUS4="$(printf '%s' "$OUT4" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "PARSE_ERROR")"
if [ "$STATUS4" = "configured" ]; then
  _pass "configured: config has feynarts_path → status==configured"
else
  _fail "configured: config has feynarts_path → status==configured" "configured" "$STATUS4 ($OUT4)"
fi

# ------------------------------------------------------------------
# Test 5: found on Linux path ($HOME/.WolframEngine/Applications/)
# ------------------------------------------------------------------
FAKE_HOME5="$(mktemp -d)"
FEYNARTS_DIR5="$FAKE_HOME5/.WolframEngine/Applications/FeynArts-3.11"
mkdir -p "$FEYNARTS_DIR5"
touch "$FEYNARTS_DIR5/FeynArts.m"
trap 'rm -rf "$FAKE_HOME5"' EXIT

OUT5="$(HOME="$FAKE_HOME5" XDG_CONFIG_HOME="$FAKE_HOME5/.config" "${DETECT_SCRIPT}" detect 2>/dev/null)"
STATUS5="$(printf '%s' "$OUT5" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "PARSE_ERROR")"
if [ "$STATUS5" = "found" ]; then
  _pass "found: Linux WolframEngine path → status==found"
else
  _fail "found: Linux WolframEngine path → status==found" "found" "$STATUS5 ($OUT5)"
fi

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "Results: $PASS passed, $FAIL failed."
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
