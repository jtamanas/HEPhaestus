#!/usr/bin/env bash
# test_exit_codes.sh — verify the four new exit code constants exist and have
# the expected values, and that no two EXIT_ constants collide.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_SH="$SCRIPT_DIR/../_common.sh"

# Source _common.sh to load constants.
. "$COMMON_SH"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# ── 1. New constants exist and have correct values ───────────────────────────
[ "${EXIT_NO_CMAKE:-}" = "26" ]       || fail "EXIT_NO_CMAKE expected 26, got '${EXIT_NO_CMAKE:-unset}'"
pass "EXIT_NO_CMAKE=26"

[ "${EXIT_NO_PYBIND:-}" = "27" ]      || fail "EXIT_NO_PYBIND expected 27, got '${EXIT_NO_PYBIND:-unset}'"
pass "EXIT_NO_PYBIND=27"

[ "${EXIT_FORM_BUILD:-}" = "28" ]     || fail "EXIT_FORM_BUILD expected 28, got '${EXIT_FORM_BUILD:-unset}'"
pass "EXIT_FORM_BUILD=28"

[ "${EXIT_LOOPTOOLS_BUILD:-}" = "29" ] || fail "EXIT_LOOPTOOLS_BUILD expected 29, got '${EXIT_LOOPTOOLS_BUILD:-unset}'"
pass "EXIT_LOOPTOOLS_BUILD=29"
[ "${EXIT_NOT_CONFIGURED:-}" = "17" ] || fail "EXIT_NOT_CONFIGURED expected 17, got '${EXIT_NOT_CONFIGURED:-unset}'"
pass "EXIT_NOT_CONFIGURED=17"

# ── 2. No two EXIT_ constants share the same numeric value ──────────────────
# Extract all EXIT_VARNAME=N assignments from _common.sh (only bare integer assignments).
duplicate_values=$(grep -E '^EXIT_[A-Z_]+=[0-9]+$' "$COMMON_SH" \
  | awk -F= '{print $2}' \
  | sort \
  | uniq -d)

if [ -n "$duplicate_values" ]; then
  fail "Duplicate exit code values found: $duplicate_values"
fi
pass "No duplicate EXIT_ values"

# ── 3. Expected codes from pre-existing set are still present ────────────────
[ "${EXIT_OK:-}" = "0" ]              || fail "EXIT_OK missing or wrong"
[ "${EXIT_NO_WOLFRAM:-}" = "20" ]     || fail "EXIT_NO_WOLFRAM missing or wrong"
[ "${EXIT_NO_LAPACK:-}" = "25" ]      || fail "EXIT_NO_LAPACK missing or wrong"
pass "Pre-existing exit codes intact"

echo "All exit code tests passed."
