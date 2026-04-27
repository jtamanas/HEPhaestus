#!/usr/bin/env bash
# test_skill_sections.sh — verify SKILL.md section structure, anti-assertions,
# and contract/SKILL cross-check for the install skill Wolfram UX.
set -euo pipefail

cd "$(dirname "$0")/.."

SKILL_MD="SKILL.md"
CONTRACT_MD="docs/wolfram-ux-contract.md"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# ── Duty 1 — Section-header presence (each grep -cE MUST equal 1) ────────────

count=$(grep -cE '^## Bundle flow$' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'## Bundle flow' header: expected 1 match in $SKILL_MD, got $count"
pass "header '## Bundle flow' present (count=1)"

count=$(grep -cE '^## Wolfram walkthrough$' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'## Wolfram walkthrough' header: expected 1 match in $SKILL_MD, got $count"
pass "header '## Wolfram walkthrough' present (count=1)"

count=$(grep -cE '^## Deferred Wolfram path$' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'## Deferred Wolfram path' header: expected 1 match in $SKILL_MD, got $count"
pass "header '## Deferred Wolfram path' present (count=1)"

count=$(grep -cE '^### 1\. Wolfram Engine \(manual\)$' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'### 1. Wolfram Engine (manual)' header: expected 1 match in $SKILL_MD, got $count"
pass "header '### 1. Wolfram Engine (manual)' present (count=1)"

count=$(grep -cE '^### Bundle warning$' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'### Bundle warning' header: expected 1 match in $SKILL_MD, got $count"
pass "header '### Bundle warning' present (count=1)"

count=$(grep -cE '^### Phase 1 of 2' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'### Phase 1 of 2' header: expected 1 match in $SKILL_MD, got $count"
pass "header '### Phase 1 of 2' present (count=1)"

count=$(grep -cE '^### Phase 2 of 2' "$SKILL_MD") || count=0
[ "$count" -eq 1 ] || fail "'### Phase 2 of 2' header: expected 1 match in $SKILL_MD, got $count"
pass "header '### Phase 2 of 2' present (count=1)"

# ── Duty 2 — Anti-assertions (each grep -c MUST equal 0) ─────────────────────

count=$(grep -c -F "Ready to run the minimal demo" "$SKILL_MD") || count=0
[ "$count" -eq 0 ] || fail "spec-era text 'Ready to run the minimal demo' must NOT appear in $SKILL_MD (found $count times)"
pass "anti-assertion 'Ready to run the minimal demo' absent from SKILL.md"

count=$(grep -c -F '"error":"unknown bundle:' "$SKILL_MD") || count=0
[ "$count" -eq 0 ] || fail "internal error JSON '\"error\":\"unknown bundle:' must NOT appear in $SKILL_MD (found $count times)"
pass "anti-assertion '\"error\":\"unknown bundle:' absent from SKILL.md"

# ── Duty 3 — Contract/SKILL cross-check ──────────────────────────────────────
# For each substring: must appear at least once in BOTH files.

check_both() {
  local substr="$1"
  local skill_count contract_count
  skill_count=$(grep -c -F "$substr" "$SKILL_MD") || skill_count=0
  contract_count=$(grep -c -F "$substr" "$CONTRACT_MD") || contract_count=0

  if [ "$skill_count" -eq 0 ] && [ "$contract_count" -eq 0 ]; then
    fail "substring '$substr' missing from BOTH $SKILL_MD AND $CONTRACT_MD"
  elif [ "$skill_count" -eq 0 ]; then
    fail "substring '$substr' missing from $SKILL_MD (present in $CONTRACT_MD)"
  elif [ "$contract_count" -eq 0 ]; then
    fail "substring '$substr' missing from $CONTRACT_MD (present in $SKILL_MD)"
  fi
  pass "cross-check '$substr' present in both $SKILL_MD and $CONTRACT_MD"
}

check_both "Heads up — this bundle needs Wolfram Engine"
check_both "Phase 1 of 2"
check_both "Phase 2 of 2"
check_both "wolframscript --activate"
check_both "Paused. Your config has"
check_both "Installed: SPheno"
check_both "attempt 2 wait 20s"

echo "All section tests passed."
