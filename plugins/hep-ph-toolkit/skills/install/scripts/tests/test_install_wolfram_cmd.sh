#!/usr/bin/env bash
# test_install_wolfram_cmd.sh — assert all T2 acceptance criteria for install_wolfram.sh.
set -euo pipefail

# Change to the install/ directory (two levels up from this test file).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$INSTALL_DIR"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── 1. install → exit 0; stdout contains "walks you through" AND "use-path" ──
H1=$(mktemp -d); X1=$(mktemp -d)
err_tmp=$(mktemp)
# HEPPH_DISK_MIN_GB=1 bypasses the 20 GB gate; exercises banner-print path on any sandbox disk.
out1=$(HOME="$H1" XDG_CONFIG_HOME="$X1" HEPPH_DISK_MIN_GB=1 bash scripts/install_wolfram.sh install 2>"$err_tmp")
rc1=$?
[ "$rc1" -eq 0 ] || fail "install: expected exit 0, got $rc1"
pass "install: exit 0"

printf '%s' "$out1" | grep -qF 'walks you through' \
  || fail 'install: stdout missing "walks you through"'
pass 'install: stdout contains "walks you through"'

printf '%s' "$out1" | grep -qF 'use-path' \
  || fail 'install: stdout missing "use-path"'
pass 'install: stdout contains "use-path"'

# ── 2. install → stderr empty ─────────────────────────────────────────────────
err_size=$(wc -c < "$err_tmp" | tr -d ' ')
[ "$err_size" -eq 0 ] || fail "install: stderr not empty (got: $(cat "$err_tmp"))"
pass "install: stderr empty"
rm -f "$err_tmp"

# ── 3. detect with clean PATH → stdout equals {"status":"missing"} ───────────
H2=$(mktemp -d); X2=$(mktemp -d)
out2=$(HOME="$H2" XDG_CONFIG_HOME="$X2" PATH=/usr/bin:/bin bash scripts/install_wolfram.sh detect 2>/dev/null)
# Strip a single trailing newline for comparison.
out2_stripped=$(printf '%s' "$out2")
[ "$out2_stripped" = '{"status":"missing"}' ] \
  || fail 'detect: expected {"status":"missing"}, got: '"$out2_stripped"
pass 'detect: stdout == {"status":"missing"}'

# ── 4. use-path /does/not/exist → exit 16 ────────────────────────────────────
H3=$(mktemp -d); X3=$(mktemp -d)
rc4=0
HOME="$H3" XDG_CONFIG_HOME="$X3" bash scripts/install_wolfram.sh use-path /does/not/exist 2>/dev/null || rc4=$?
[ "$rc4" -eq 16 ] || fail "use-path /does/not/exist: expected exit 16, got $rc4"
pass "use-path /does/not/exist: exit 16"

# ── 5. EXIT_NO_WOLFRAM not referenced in install_wolfram.sh ──────────────────
count=$(grep -c 'EXIT_NO_WOLFRAM' scripts/install_wolfram.sh || true)
[ "$count" -eq 0 ] || fail "EXIT_NO_WOLFRAM found $count time(s) in install_wolfram.sh"
pass "EXIT_NO_WOLFRAM not referenced in install_wolfram.sh (count=0)"

# ── 6. Regression: test_exit_codes.sh still passes ────────────────────────────
bash "../../../shared/install-helpers/tests/test_exit_codes.sh" \
  || fail "plugins/shared/install-helpers/tests/test_exit_codes.sh exited non-zero"
pass "plugins/shared/install-helpers/tests/test_exit_codes.sh: exit 0"

# ── 7. Syntax check: bash -n scripts/install_wolfram.sh ──────────────────────
bash -n scripts/install_wolfram.sh || fail "bash -n scripts/install_wolfram.sh failed"
pass "bash -n scripts/install_wolfram.sh: exit 0"

echo "All install_wolfram command tests passed."
