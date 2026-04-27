#!/usr/bin/env bash
# test_no_network_mode.sh — verify HEPPH_NO_NETWORK=1 offline-cache behaviour
# in download_with_retry.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="$SCRIPT_DIR/../_common.sh"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# ── Setup temp dirs ──────────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d)"
TMP_CACHE="$TMP_DIR/cache"
TMP_OUT="$TMP_DIR/out"
mkdir -p "$TMP_CACHE" "$TMP_OUT"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# Stub curl so any network call would fail.
mkdir -p "$TMP_DIR/bin"
cat > "$TMP_DIR/bin/curl" <<'CURL'
#!/usr/bin/env bash
echo "STUB CURL — should not be called in offline mode" >&2
exit 1
CURL
chmod +x "$TMP_DIR/bin/curl"
export PATH="$TMP_DIR/bin:$PATH"

# ── Test 1: Cache hit ────────────────────────────────────────────────────────
CACHE_FILE="$TMP_CACHE/foo.tar.gz"
DEST_FILE="$TMP_OUT/foo.tar.gz"
echo "original content" > "$CACHE_FILE"

(
  . "$COMMON_SH"
  export HEPPH_NO_NETWORK=1
  export HEPPH_OFFLINE_CACHE_DIR="$TMP_CACHE"
  download_with_retry "https://example.com/foo.tar.gz" "$DEST_FILE" "TEST"
)
rc=$?

[ "$rc" -eq 0 ] || fail "Cache-hit: expected exit 0, got $rc"
[ -f "$DEST_FILE" ] || fail "Cache-hit: dest file not created"
diff "$CACHE_FILE" "$DEST_FILE" > /dev/null || fail "Cache-hit: dest differs from cached file"
pass "Cache hit: exit 0 and byte-equal copy"

# ── Test 2: Cache miss ───────────────────────────────────────────────────────
DEST_FILE2="$TMP_OUT/bar.tar.gz"
STDERR_FILE="$TMP_DIR/stderr.txt"

set +e
(
  . "$COMMON_SH"
  export HEPPH_NO_NETWORK=1
  export HEPPH_OFFLINE_CACHE_DIR="$TMP_CACHE"
  download_with_retry "https://example.com/bar.tar.gz" "$DEST_FILE2" "TEST"
) 2>"$STDERR_FILE"
rc=$?
set -e

[ "$rc" -eq 12 ] || fail "Cache miss: expected exit 12 (EXIT_DOWNLOAD), got $rc"

grep -q "TEST_OFFLINE_CACHE_MISS" "$STDERR_FILE" \
  || fail "Cache miss: expected TEST_OFFLINE_CACHE_MISS in stderr. Got: $(cat "$STDERR_FILE")"
pass "Cache miss: exit 12 and TEST_OFFLINE_CACHE_MISS in stderr"

echo "All no-network mode tests passed."
