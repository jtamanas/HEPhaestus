#!/usr/bin/env bash
# run_tests.sh — WS-2 test suite driver
# Runs the dark-matter-constraints skill test harness.
# Exits 0 on suite-green (or expected xfail/xpass), non-zero on unexpected failures.
#
# Usage:
#   ./tests/run_tests.sh              # from dark-matter-constraints/ root
#   bash plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/run_tests.sh  # from repo root
set -euo pipefail

# Resolve the skill root (parent of this script's directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TESTS_DIR="$SKILL_ROOT/tests"

echo "=== WS-2 dark-matter-constraints test suite ==="
echo "Skill root: $SKILL_ROOT"
echo "Tests dir:  $TESTS_DIR"
echo

# ---------------------------------------------------------------------------
# Boundary pre-check (gates 1–4b from ws2_plan_final.md T10)
# ---------------------------------------------------------------------------
echo "--- Boundary pre-check ---"

# Gate 1: no subprocess calls to real tools (must use sys.executable / stub_ / tmp_path)
LEAKS=$(grep -rE "(subprocess\.(run|call|check_call|check_output|Popen)|os\.system|os\.popen|os\.exec)" \
  "$TESTS_DIR" --include="*.py" | \
  grep -vE "(sys\.executable|tmp_path|fixtures/.*\.sh|stub_)" || true)
if [ -n "$LEAKS" ]; then
  echo "BOUNDARY FAIL (gate 1): real-tool subprocess calls detected:"
  echo "$LEAKS"
  exit 1
fi
echo "Gate 1 PASS — no real-tool subprocess leaks"

# Gate 1b: real producer binary names not in subprocess args
if grep -rE "(subprocess|os\.(system|popen|exec))[^#]*['\"](maddm|micromegas|wolframscript|drake)['\"]" \
     "$TESTS_DIR" --include="*.py" 2>/dev/null | grep -q .; then
  echo "BOUNDARY FAIL (gate 1b): real producer name in subprocess call"
  exit 1
fi
echo "Gate 1b PASS"

# Gate 2: no LLM-behavior tests
if grep -rElI "(claude|anthropic|openai|llm)" "$TESTS_DIR" --include="*.py" 2>/dev/null | grep -q .; then
  echo "BOUNDARY FAIL (gate 2): LLM references found in test files"
  exit 1
fi
echo "Gate 2 PASS — no LLM-behavior tests"

# Gate 3: no _HERE/_REPO_ROOT top-level redefinitions in WS-2 test files
for f in \
  "$TESTS_DIR/test_check_prereqs.py" \
  "$TESTS_DIR/test_detect_drake.py" \
  "$TESTS_DIR/test_extract_field.py" \
  "$TESTS_DIR/test_verify_router_field_contract.py" \
  "$TESTS_DIR/test_doc_vs_cli_parity.py" \
  "$TESTS_DIR/test_oracle_thresholds.py"; do
  [ -f "$f" ] || continue
  if grep -qE "^_HERE\s*=" "$f"; then
    echo "BOUNDARY FAIL (gate 3): _HERE redefined in $(basename "$f")"
    exit 1
  fi
  if grep -qE "^_REPO_ROOT\s*=" "$f"; then
    echo "BOUNDARY FAIL (gate 3): _REPO_ROOT redefined in $(basename "$f")"
    exit 1
  fi
done
echo "Gate 3 PASS — conftest is single source of truth for _HERE/_REPO_ROOT"

# Gate 4a: skill scripts do not import oracle
if [ -d "$SKILL_ROOT/scripts" ]; then
  if grep -rE "(from\s+tests\.oracle|import\s+tests\.oracle)" "$SKILL_ROOT/scripts" 2>/dev/null | grep -q .; then
    echo "BOUNDARY FAIL (gate 4a): skill/scripts imports test oracle"
    exit 1
  fi
fi
echo "Gate 4a PASS — skill code does not import oracle"

# Gate 4b: only test_oracle_thresholds.py imports oracle
for f in "$TESTS_DIR"/test_*.py; do
  fname="$(basename "$f")"
  [ "$fname" = "test_oracle_thresholds.py" ] && continue
  if grep -qF "tests.oracle" "$f" 2>/dev/null || grep -qE "from\s+\.oracle" "$f" 2>/dev/null; then
    echo "BOUNDARY FAIL (gate 4b): oracle import in $fname"
    exit 1
  fi
done
echo "Gate 4b PASS — oracle imported only by test_oracle_thresholds.py"

echo
echo "--- Boundary pre-check PASSED ---"
echo

# ---------------------------------------------------------------------------
# Run pytest
# ---------------------------------------------------------------------------
# Compute repo root: tests → dark-matter-constraints → skills → constraints
#                         → plugins → repo-root  (five levels up from SCRIPT_DIR)
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"

echo "--- Running pytest ---"
echo "Repo root: $REPO_ROOT"
cd "$REPO_ROOT"
python -m pytest "plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests" -v
EXIT=$?

echo
if [ $EXIT -eq 0 ]; then
  echo "=== WS-2 suite: ALL PASSED ==="
else
  echo "=== WS-2 suite: $EXIT failures (see above) ==="
fi
exit $EXIT
