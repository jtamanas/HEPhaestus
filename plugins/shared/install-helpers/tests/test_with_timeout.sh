#!/usr/bin/env bash
# test_with_timeout.sh — verify with_timeout helper: success, failure, timeout paths.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="$SCRIPT_DIR/../_common.sh"

# Source _common.sh to load with_timeout.
. "$COMMON_SH"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# ── Case (a): with_timeout 5 true → returns 0 ────────────────────────────────
rc=0
with_timeout 5 true || rc=$?
[ "$rc" -eq 0 ] || fail "with_timeout 5 true: expected exit 0, got $rc"
pass "with_timeout 5 true: exit 0"

# ── Case (b): with_timeout 5 false → returns 1 ───────────────────────────────
rc=0
with_timeout 5 false || rc=$?
[ "$rc" -eq 1 ] || fail "with_timeout 5 false: expected exit 1, got $rc"
pass "with_timeout 5 false: exit 1"

# ── Case (c): with_timeout 1 sleep 5 → returns 124 (timeout) ─────────────────
rc=0
with_timeout 1 sleep 5 || rc=$?
[ "$rc" -eq 124 ] || fail "with_timeout 1 sleep 5: expected exit 124 (timeout), got $rc"
pass "with_timeout 1 sleep 5: exit 124 (timeout)"

echo "All with_timeout tests passed."
