#!/usr/bin/env bash
# Unit test: offline cache mode in install_ddcalc.sh via HEPPH_NO_NETWORK=1
# Usage: HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/cache bash test_offline_cache.sh
# Or just: bash test_offline_cache.sh (sets up its own cache)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"

PASS=0
FAIL=0

_assert() {
  local desc="$1" expr="$2"
  if eval "$expr"; then
    echo "PASS: $desc"
    PASS=$((PASS+1))
  else
    echo "FAIL: $desc"
    FAIL=$((FAIL+1))
  fi
}

# ── Setup: isolated tmp environment ──────────────────────────────────────────
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CACHE_DIR="$TMP/cache"
STATE_DIR="$TMP/state"
CONFIG_DIR="$TMP/config/hephaestus"
mkdir -p "$CACHE_DIR" "$STATE_DIR" "$CONFIG_DIR"

# ── Test 1: cache miss → EXIT_DOWNLOAD ───────────────────────────────────────
# Source _common.sh to get EXIT_DOWNLOAD value
EXIT_DOWNLOAD_VAL="$(bash -c ". '$SHARED_COMMON'; echo \$EXIT_DOWNLOAD")"

(
  export HEPPH_NO_NETWORK=1
  export HEPPH_OFFLINE_CACHE_DIR="$CACHE_DIR"
  export HEPPH_STATE_ROOT="$STATE_DIR"
  export XDG_CONFIG_HOME="$TMP/config"
  result="$(. "$SHARED_COMMON"; download_with_retry "https://example.com/foo.tgz" "$TMP/out.tgz" "DDCALC" 2>&1; echo "exit:$?")" || true
  exit_code=$?
  echo "$result"
  exit $exit_code
) 2>&1 | grep -q "DDCALC_OFFLINE_CACHE_MISS" && \
  _assert "offline cache miss emits DDCALC_OFFLINE_CACHE_MISS blocker" "true" || \
  _assert "offline cache miss emits DDCALC_OFFLINE_CACHE_MISS blocker" "false"

# ── Test 2: cache hit → exit 0 ───────────────────────────────────────────────
# The offline cache is keyed by basename($dest), not URL basename.
# We request dest="$TMP/myfile.tgz", so cache must have "$CACHE_DIR/myfile.tgz".
echo "fake_tarball_content" > "$CACHE_DIR/myfile.tgz"

set +e
(
  export HEPPH_NO_NETWORK=1
  export HEPPH_OFFLINE_CACHE_DIR="$CACHE_DIR"
  export HEPPH_STATE_ROOT="$STATE_DIR"
  export XDG_CONFIG_HOME="$TMP/config"
  . "$SHARED_COMMON"
  download_with_retry "https://example.com/ddcalc.tgz" "$TMP/myfile.tgz" "DDCALC"
)
RC=$?
set -e

_assert "offline cache hit exits 0" "[ $RC -eq 0 ]"
_assert "offline cache hit copies file" "[ -f '$TMP/myfile.tgz' ]"
_assert "offline cache hit content matches" "cmp -s '$CACHE_DIR/myfile.tgz' '$TMP/myfile.tgz'"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
