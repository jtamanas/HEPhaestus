#!/usr/bin/env bash
# run_self_test.sh — Self-test suite for render-grep.sh harness
# Runs all fixture cases and records results to self_test.txt in same directory.
# Exit 0 if all tests pass, exit 1 if any test fails.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS="$SCRIPT_DIR/../render-grep.sh"
FIXTURES_DIR="$SCRIPT_DIR"
TRANSCRIPT="$SCRIPT_DIR/self_test.txt"
BANNER='dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets.'

PASS=0
FAIL=0

run_test() {
    local test_name="$1"
    local mdpath="$2"
    local needle="$3"
    local expected_exit="$4"

    echo "--- TEST: $test_name ---" >> "$TRANSCRIPT"
    echo "File: $mdpath" >> "$TRANSCRIPT"
    echo "Needle: $needle" >> "$TRANSCRIPT"
    echo "Expected exit: $expected_exit" >> "$TRANSCRIPT"

    bash "$HARNESS" "$mdpath" "$needle" >> "$TRANSCRIPT" 2>&1
    actual_exit=$?

    echo "Actual exit: $actual_exit" >> "$TRANSCRIPT"

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo "RESULT: PASS" >> "$TRANSCRIPT"
        PASS=$((PASS + 1))
    else
        echo "RESULT: FAIL (expected $expected_exit, got $actual_exit)" >> "$TRANSCRIPT"
        FAIL=$((FAIL + 1))
    fi
    echo "" >> "$TRANSCRIPT"
}

# Initialize transcript
{
    echo "render-grep.sh self-test transcript"
    echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Harness: $HARNESS"
    echo "=========================================="
    echo ""
} > "$TRANSCRIPT"

# Test 1: Positive case — token visible in blockquote (expected exit 0)
run_test "positive_visible" \
    "$FIXTURES_DIR/fixture_visible.md" \
    "banner-token-xyz" \
    0

# Test 2: Negative case — token only in HTML comment (expected exit 1)
run_test "negative_comment" \
    "$FIXTURES_DIR/fixture_comment.md" \
    "banner-token-xyz" \
    1

# Test 3: V1-shape blockquote with full banner string (expected exit 0)
run_test "positive_blockquote_v1" \
    "$FIXTURES_DIR/fixture_blockquote.md" \
    "$BANNER" \
    0

# Test 4: Unicode characters — Ω h² (G-RENDER-UTF8, expected exit 0)
run_test "positive_unicode" \
    "$FIXTURES_DIR/fixture_unicode.md" \
    "Ω h²" \
    0

# Summary
{
    echo "=========================================="
    echo "SUMMARY: PASS=$PASS FAIL=$FAIL TOTAL=$((PASS + FAIL))"
    if [ "$FAIL" -eq 0 ]; then
        echo "OVERALL: ALL_PASS"
    else
        echo "OVERALL: FAILURES_DETECTED"
    fi
} >> "$TRANSCRIPT"

echo "Self-test complete: PASS=$PASS FAIL=$FAIL (transcript: $TRANSCRIPT)"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
