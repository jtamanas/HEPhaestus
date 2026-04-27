#!/usr/bin/env bash
# test_atomic_write.sh — verify atomic_write and atomic_write_stdin helpers.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATOMIC_SH="$SCRIPT_DIR/../atomic_write.sh"
COMMON_SH="$SCRIPT_DIR/../_common.sh"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# Source _common.sh first so log/err/warn exist, then atomic_write.sh.
. "$COMMON_SH"
. "$ATOMIC_SH"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# ── Test 1: atomic_write basic correctness ───────────────────────────────────
DEST="$TMP_DIR/dest.txt"
SRC="$TMP_DIR/src.txt"
echo "hello world" > "$SRC"
atomic_write "$DEST" "$SRC"
diff "$SRC" "$DEST" > /dev/null || fail "atomic_write: dest content differs from src"
pass "atomic_write: basic write"

# ── Test 2: atomic_write_stdin basic correctness ─────────────────────────────
DEST2="$TMP_DIR/dest2.txt"
echo "stdin content" | atomic_write_stdin "$DEST2"
[ "$(cat "$DEST2")" = "stdin content" ] || fail "atomic_write_stdin: wrong content"
pass "atomic_write_stdin: basic write"

# ── Test 3: Atomicity — dest is either old or new, never partial ─────────────
# Write initial content.
DEST3="$TMP_DIR/dest3.txt"
OLD_CONTENT="$TMP_DIR/old.txt"
NEW_CONTENT="$TMP_DIR/new.txt"
printf 'OLD_CONTENT_LINE\n' > "$OLD_CONTENT"
# Write a 10 KB new file so fsync has meaningful work to do.
python3 -c "print('X' * 10240)" > "$NEW_CONTENT"

atomic_write "$DEST3" "$OLD_CONTENT"

# Race: attempt ~20 interrupted writes; tolerate any that succeed or get killed.
OBSERVED_PARTIAL=0
for i in $(seq 1 20); do
  (
    . "$COMMON_SH"
    . "$ATOMIC_SH"
    timeout 0.01 bash -c ". \"$COMMON_SH\"; . \"$ATOMIC_SH\"; atomic_write \"$DEST3\" \"$NEW_CONTENT\"" || true
  ) 2>/dev/null || true

  # After each attempt, read dest and check it matches either old or new fully.
  if [ -f "$DEST3" ]; then
    if diff "$DEST3" "$OLD_CONTENT" >/dev/null 2>&1 || diff "$DEST3" "$NEW_CONTENT" >/dev/null 2>&1; then
      : # ok
    else
      OBSERVED_PARTIAL=1
      fail "Partial write detected at iteration $i"
    fi
  fi
done

[ "$OBSERVED_PARTIAL" -eq 0 ] || fail "Partial write observed"
pass "Atomicity: no partial writes in 20 racing iterations"

# ── Test 4: Error case — missing src ─────────────────────────────────────────
set +e
atomic_write "$TMP_DIR/nonexistent_dest.txt" "/does/not/exist/src.txt" 2>/dev/null
rc=$?
set -e
[ "$rc" -ne 0 ] || fail "Expected non-zero exit for missing content_file"
pass "atomic_write: non-zero exit for missing src"

echo "All atomic_write tests passed."
