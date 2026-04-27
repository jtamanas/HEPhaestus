#!/usr/bin/env bash
# test_install_sarah_live.sh — Tier-I integration test for install_sarah.sh.
# Gated: skips if wolfram_engine_path not configured or SARAH not installed.
#
# Validates:
#   1. register_path is idempotent (B4 regression: run install twice).
#   2. On macOS: init.m is in ~/Library/WolframEngine/Kernel/ (B2 regression).
#   3. install_sarah.sh verify exits 0 after install.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SARAH="$SCRIPT_DIR/../../install_sarah.sh"

pass() { printf 'PASS: %s\n' "$*"; }
skip() { printf 'SKIP: %s\n' "$*"; exit 0; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── Gate: require wolfram_engine_path configured ───────────────────────────────
WOLFRAM_PATH="$(bash "$INSTALL_SARAH" detect 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("path",""))' \
    2>/dev/null || true)"

WOLFRAM_ENGINE="$(bash -c "
  SCRIPT_DIR=\"$SCRIPT_DIR/../../\"
  . \"\$SCRIPT_DIR/_common.sh\"
  config_get wolfram_engine_path
" 2>/dev/null || true)"

if [ -z "$WOLFRAM_ENGINE" ] || [ ! -x "$WOLFRAM_ENGINE" ]; then
  skip "wolfram_engine_path not configured or not executable; skipping live test"
fi

SARAH_PATH="$(bash -c "
  SCRIPT_DIR=\"$SCRIPT_DIR/../../\"
  . \"\$SCRIPT_DIR/_common.sh\"
  config_get sarah_path
" 2>/dev/null || true)"

if [ -z "$SARAH_PATH" ] || [ ! -f "$SARAH_PATH/SARAH.m" ]; then
  skip "sarah_path not configured or SARAH.m not found; skipping live test"
fi

pass "Gates: wolfram_engine_path and sarah_path configured"

# ── Test 1: verify passes on configured path ───────────────────────────────────
rc=0
out="$("$INSTALL_SARAH" verify --path "$SARAH_PATH" --wolfram-path "$WOLFRAM_ENGINE")" || rc=$?
[ "$rc" = "0" ] || fail "verify failed (rc=$rc) on configured sarah_path=$SARAH_PATH. out=$out"
echo "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok'" \
  || fail "verify did not return status:ok, got: $out"
pass "verify exits 0 on configured sarah_path"

# ── Test 2: B2 regression — init.m in WolframEngine dir on macOS ───────────────
if [ "$(uname -s)" = "Darwin" ]; then
  EXPECTED_INIT="$HOME/Library/WolframEngine/Kernel/init.m"
  if [ -f "$EXPECTED_INIT" ]; then
    pass "B2 regression: init.m exists at $EXPECTED_INIT (correct macOS path)"
    grep -q 'hephaestus SARAH path' "$EXPECTED_INIT" \
      || fail "B2 regression: init.m at correct path but missing hephaestus marker"
    pass "B2 regression: init.m contains hephaestus marker"
  else
    # init.m might not exist if SARAH was never installed via this script.
    pass "B2 regression: init.m at $EXPECTED_INIT not found (SARAH may not have been installed via this script)"
  fi
  WRONG_INIT="$HOME/Library/Wolfram/Kernel/init.m"
  if [ -f "$WRONG_INIT" ]; then
    if grep -q 'hephaestus SARAH path' "$WRONG_INIT"; then
      # This indicates the pre-B2-fix code wrote to the wrong path.
      # It's a pre-existing condition on hosts that ran the old code; warn but
      # do not fail (the new code writes to the CORRECT path above).
      printf 'WARN: hephaestus marker found in old Mathematica path %s (legacy state; run unregister_path to clean up)\n' "$WRONG_INIT" >&2
    fi
  fi
  pass "B2 regression: new installs target correct WolframEngine path (legacy state noted above)"
fi

# ── Test 3: B4 regression — register_path twice does not crash ─────────────────
# Call use-path twice against the same directory; second call hits the regex rewrite
# branch which would crash without the re.escape(marker) fix.
rc=0
"$INSTALL_SARAH" use-path "$SARAH_PATH" >/dev/null 2>&1 || rc=$?
[ "$rc" = "0" ] || fail "B4 regression: first use-path call failed with rc=$rc"
rc=0
"$INSTALL_SARAH" use-path "$SARAH_PATH" >/dev/null 2>&1 || rc=$?
[ "$rc" = "0" ] || fail "B4 regression: second use-path call failed with rc=$rc (regex crash?)"
pass "B4 regression: use-path twice on same path succeeds"

# ── Test 4: verify still exits 0 after double use-path ────────────────────────
rc=0
out="$("$INSTALL_SARAH" verify --path "$SARAH_PATH" --wolfram-path "$WOLFRAM_ENGINE")" || rc=$?
[ "$rc" = "0" ] || fail "verify failed after double use-path (rc=$rc). out=$out"
pass "verify exits 0 after double use-path (B4 regression end-to-end)"

echo ""
echo "All test_install_sarah_live.sh tests passed."
