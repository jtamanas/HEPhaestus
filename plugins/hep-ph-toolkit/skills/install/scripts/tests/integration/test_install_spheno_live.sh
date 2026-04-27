#!/usr/bin/env bash
# test_install_spheno_live.sh — tier-I (gated) integration test for SPheno.
#
# Gating: skip unless HEPPH_SKIP_INTEGRATION is unset AND gfortran is present
# AND at least 3 GB free in /tmp.
#
# Usage:
#   bash test_install_spheno_live.sh                # runs full install + verify
#   HEPPH_SKIP_INTEGRATION=1 bash test_install...   # exits 0 immediately (CI skip)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
skip() { printf 'SKIP: %s\n' "$*"; exit 0; }

# ── Gate 1: HEPPH_SKIP_INTEGRATION ───────────────────────────────────────────
if [ -n "${HEPPH_SKIP_INTEGRATION:-}" ]; then
  skip "HEPPH_SKIP_INTEGRATION is set; skipping live integration test."
fi

# ── Gate 2: gfortran must be available ───────────────────────────────────────
if ! command -v gfortran >/dev/null 2>&1; then
  skip "gfortran not found; skipping live integration test."
fi

# ── Gate 3: at least 3 GB free in /tmp ───────────────────────────────────────
avail_kb=$(df -k /tmp | awk 'NR==2 {print $4}')
avail_gb=$(( avail_kb / 1024 / 1024 ))
if [ "$avail_gb" -lt 3 ]; then
  skip "Less than 3 GB free in /tmp (have ${avail_gb} GB); skipping."
fi

# ── Setup ─────────────────────────────────────────────────────────────────────
TEST_HOME=$(mktemp -d)
TEST_CFG=$(mktemp -d)
INSTALL_TARGET="$TEST_HOME/SPheno-test-$$"

cleanup() {
  rm -rf "$TEST_HOME" "$TEST_CFG" "$INSTALL_TARGET" 2>/dev/null || true
}
trap cleanup EXIT

# ── Run install ───────────────────────────────────────────────────────────────
printf 'Running: install_spheno.sh install %s\n' "$INSTALL_TARGET"
HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_CFG" \
  HEPPH_DISK_MIN_GB=1 \
  bash "$INSTALL_DIR/scripts/install_spheno.sh" install "$INSTALL_TARGET" \
  || fail "install_spheno.sh install exited non-zero"

pass "install completed"

# ── Check config has spheno_path ──────────────────────────────────────────────
cfg_file="$TEST_CFG/hephaestus/config.json"
[ -f "$cfg_file" ] || fail "config.json not found at $cfg_file"
spheno_path=$(python3 -c "import json; d=json.load(open('$cfg_file')); print(d.get('spheno_path',''))")
[ -n "$spheno_path" ] || fail "spheno_path not set in config.json"
pass "config.json has spheno_path: $spheno_path"

# ── Check config has spheno_version ──────────────────────────────────────────
spheno_version=$(python3 -c "import json; d=json.load(open('$cfg_file')); print(d.get('spheno_version',''))")
[ -n "$spheno_version" ] || fail "spheno_version not set in config.json"
pass "config.json has spheno_version: $spheno_version"

# ── Run verify against the installed path ─────────────────────────────────────
verify_out=$(HOME="$TEST_HOME" XDG_CONFIG_HOME="$TEST_CFG" \
  bash "$INSTALL_DIR/scripts/install_spheno.sh" verify --path "$spheno_path")
verify_rc=$?

[ "$verify_rc" -eq 0 ] || fail "verify exited $verify_rc; output: $verify_out"

printf '%s' "$verify_out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['ok'] is True, f'ok not True: {d}'
assert d['status'] == 'ok', f'status not ok: {d}'
assert d['version'], f'version empty: {d}'
print(f'verify ok: version={d[\"version\"]}')
" || fail "verify JSON assertion failed: $verify_out"

pass "verify --path \$spheno_path exits 0 and JSON ok=true"

echo ""
echo "All live integration tests passed."
