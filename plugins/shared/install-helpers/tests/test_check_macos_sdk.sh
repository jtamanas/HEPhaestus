#!/usr/bin/env bash
# test_check_macos_sdk.sh — verify check_macos_sdk JSON output under shim uname.
# On non-Darwin CI, all subtests are skipped (exit 0).
set -euo pipefail

[ "$(uname -s)" = "Darwin" ] || { echo "SKIP: non-Darwin platform"; exit 0; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="$SCRIPT_DIR/../_common.sh"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# ── Test 1: arm64 uname shim → ldflags contains -Wl,-ld_classic ─────────────
mkdir -p "$TMP_DIR/bin_arm64"
cat > "$TMP_DIR/bin_arm64/uname" <<'SHIM'
#!/usr/bin/env bash
if [ "${1:-}" = "-m" ]; then echo "arm64"; elif [ "${1:-}" = "-s" ]; then echo "Darwin"; else /usr/bin/uname "$@"; fi
SHIM
chmod +x "$TMP_DIR/bin_arm64/uname"

result=$(
  export PATH="$TMP_DIR/bin_arm64:$PATH"
  . "$COMMON_SH"
  check_macos_sdk
)

echo "arm64 result: $result"
# On arm64 + Clang>=15 machine, ldflags should be -Wl,-ld_classic.
# We test the JSON field is present and non-empty for ldflags key.
# Accept either value since the actual clang version determines it.
echo "$result" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'ldflags' in d, 'missing ldflags key'
assert 'looptools_quad' in d, 'missing looptools_quad key'
assert 'sdkroot' in d, 'missing sdkroot key'
# On arm64 + clang>=15 expected -Wl,-ld_classic
if d['ldflags']:
    assert d['ldflags'] == '-Wl,-ld_classic', f'unexpected ldflags: {d[\"ldflags\"]}'
print('arm64 JSON is well-formed')
" || fail "arm64 JSON parse failed"
pass "arm64 shim: JSON output is valid"

# ── Test 2: x86_64 uname shim → ldflags is empty string ─────────────────────
mkdir -p "$TMP_DIR/bin_x86"
cat > "$TMP_DIR/bin_x86/uname" <<'SHIM'
#!/usr/bin/env bash
if [ "${1:-}" = "-m" ]; then echo "x86_64"; elif [ "${1:-}" = "-s" ]; then echo "Darwin"; else /usr/bin/uname "$@"; fi
SHIM
chmod +x "$TMP_DIR/bin_x86/uname"

result2=$(
  export PATH="$TMP_DIR/bin_x86:$PATH"
  . "$COMMON_SH"
  check_macos_sdk
)

echo "x86_64 result: $result2"
echo "$result2" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'ldflags' in d, 'missing ldflags key'
assert d['ldflags'] == '', f'expected empty ldflags for x86_64, got {d[\"ldflags\"]!r}'
print('x86_64 JSON is well-formed with empty ldflags')
" || fail "x86_64 JSON parse failed"
pass "x86_64 shim: ldflags is empty string"

echo "All check_macos_sdk tests passed."
