#!/usr/bin/env bash
# test_netguard.sh — unit tests for _netguard.sh.
# Wraps a fake make that calls curl; asserts log entry + MICROMEGAS_BUILD_NEEDS_NETWORK.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETGUARD_SH="$SCRIPT_DIR/../_netguard.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

. "$NETGUARD_SH"

# ── Test 1: clean make (no network) → netguard_check passes ──────────────────
LOG1="$TMP_DIR/clean.log"
netguard_setup "$LOG1"
# Simulate make that does NOT call curl
(
  PATH="$NETGUARD_STUB_DIR:$PATH"
  echo "Building without network..."
)
netguard_check "$LOG1" && pass "clean make → netguard_check passes" \
  || fail "clean make should not trigger MICROMEGAS_BUILD_NEEDS_NETWORK"
netguard_cleanup

# ── Test 2: make that calls curl → log entry + MICROMEGAS_BUILD_NEEDS_NETWORK ─
LOG2="$TMP_DIR/net.log"
netguard_setup "$LOG2"
# Simulate make that calls curl
(
  PATH="$NETGUARD_STUB_DIR:$PATH"
  curl https://example.com/package.tgz >/dev/null 2>&1 || true
)
# Now check: should fail and emit blocker
net_stderr="$(netguard_check "$LOG2" 2>&1 || true)"
if [ -s "$LOG2" ]; then
  pass "netguard log captured curl attempt"
else
  fail "netguard log is empty after curl call"
fi

if echo "$net_stderr" | grep -q "MICROMEGAS_BUILD_NEEDS_NETWORK"; then
  pass "MICROMEGAS_BUILD_NEEDS_NETWORK emitted"
else
  fail "Expected MICROMEGAS_BUILD_NEEDS_NETWORK in stderr: $net_stderr"
fi
netguard_cleanup

# ── Test 3: wget stub ────────────────────────────────────────────────────────
LOG3="$TMP_DIR/wget.log"
netguard_setup "$LOG3"
(
  PATH="$NETGUARD_STUB_DIR:$PATH"
  wget https://other.example/data.zip >/dev/null 2>&1 || true
)
if [ -s "$LOG3" ] && grep -q "NETGUARD: wget" "$LOG3"; then
  pass "netguard captures wget"
else
  fail "netguard did not capture wget: $(cat "$LOG3")"
fi
netguard_cleanup

# ── Test 4: git stub ─────────────────────────────────────────────────────────
LOG4="$TMP_DIR/git.log"
netguard_setup "$LOG4"
(
  PATH="$NETGUARD_STUB_DIR:$PATH"
  git clone https://github.com/example/repo >/dev/null 2>&1 || true
)
if [ -s "$LOG4" ] && grep -q "NETGUARD: git" "$LOG4"; then
  pass "netguard captures git"
else
  fail "netguard did not capture git: $(cat "$LOG4")"
fi
netguard_cleanup

echo "All netguard tests passed."
