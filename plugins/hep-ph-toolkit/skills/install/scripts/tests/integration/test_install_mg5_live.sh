#!/usr/bin/env bash
# test_install_mg5_live.sh — Tier-I live integration test for install_mg5.sh.
# Gated off by default; only runs when HEPPH_SKIP_INTEGRATION and
# HEPPH_SKIP_INTEGRATION_MG5 are both unset (or not "1").
#
# Plan-final.md §2.2 WS2-T1 item 4.
set -euo pipefail

# ── Skip gates ────────────────────────────────────────────────────────────────
: "${HEPPH_SKIP_INTEGRATION:=}"
: "${HEPPH_SKIP_INTEGRATION_MG5:=}"
if [ "${HEPPH_SKIP_INTEGRATION}" = "1" ] || [ "${HEPPH_SKIP_INTEGRATION_MG5}" = "1" ]; then
  echo "[integration_mg5] skipped (HEPPH_SKIP_INTEGRATION)"
  exit 0
fi

# Skip if gfortran is unavailable (pragmatic, not a failure).
if ! command -v gfortran >/dev/null 2>&1; then
  echo "[integration_mg5] skipped: gfortran not found"
  exit 0
fi

# Skip if < 3 GB free in /tmp.
_free_gb=$(df -k /tmp | awk 'NR==2 {print int($4/1024/1024)}')
if [ "${_free_gb}" -lt 3 ]; then
  echo "[integration_mg5] skipped: only ${_free_gb} GB free in /tmp (need 3)"
  exit 0
fi

# ── Locate install script ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MG5_SCRIPT="$INSTALL_DIR/scripts/install_mg5.sh"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

TEST_DIR="/tmp/hepph-mg5-test"
rm -rf "$TEST_DIR"

# ── Run install ───────────────────────────────────────────────────────────────
echo "[integration_mg5] Running install to $TEST_DIR ..."
XDG_CONFIG_HOME="$TEST_DIR/cfg" bash "$MG5_SCRIPT" install "$TEST_DIR/mg5" \
  || fail "install exited non-zero"
pass "install: exited 0"

# ── Locate the installed binary from config ───────────────────────────────────
cfg_json="$TEST_DIR/cfg/hephaestus/config.json"
[ -f "$cfg_json" ] || fail "config.json not found at $cfg_json"

mg5_path=$(python3 -c "import json; d=json.load(open('$cfg_json')); print(d.get('madgraph_path',''))")
[ -n "$mg5_path" ] || fail "madgraph_path not set in config.json"
pass "config: madgraph_path=$mg5_path"

# ── Run verify ────────────────────────────────────────────────────────────────
echo "[integration_mg5] Running verify --path $mg5_path ..."
out=$(XDG_CONFIG_HOME="$TEST_DIR/cfg" bash "$MG5_SCRIPT" verify --path "$mg5_path" 2>/dev/null) \
  || fail "verify exited non-zero"

python3 -c "
import json, sys
d = json.loads('$out')
assert d['status'] == 'ok', f'status={d[\"status\"]}'
assert d['ok'] is True, d
print('verify JSON ok, version=' + d.get('version', ''))
" || fail "verify JSON check failed"
pass "verify: exit 0 and status=ok"

echo "[integration_mg5] All integration tests passed."
