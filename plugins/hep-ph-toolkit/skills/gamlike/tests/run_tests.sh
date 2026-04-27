#!/usr/bin/env bash
# run_tests.sh — gamlike skill test runner.
# Mirrors dark-matter-constraints/tests/run_tests.sh structure.
# Usage: bash plugins/hep-ph-toolkit/skills/gamlike/tests/run_tests.sh
# from the repo root.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Use git rev-parse for worktree-compatible root detection (.git may be a file, not a dir)
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
    # Fallback: walk up looking for plugins/ directory
    REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
    while [[ "$REPO_ROOT" != "/" ]] && [[ ! -e "$REPO_ROOT/.git" ]]; do
        REPO_ROOT="$(dirname "$REPO_ROOT")"
    done
fi

echo "=== gamlike v0 test suite ==="
echo "REPO_ROOT: $REPO_ROOT"
echo ""

# ── Gate 1: no real-tool subprocess calls in tests ────────────────────────────
echo "--- Gate 1: no real-tool subprocess calls ---"
if grep -rE "subprocess.*['\"]?(maddm|micromegas|wolframscript|drake|mg5_aMC)['\"]?" \
    "$SCRIPT_DIR/"*.py 2>/dev/null | grep -v '^#'; then
    echo "FAIL Gate 1: real-tool subprocess call found in tests"
    exit 1
fi
echo "Gate 1 OK: no real-tool subprocess calls"

# ── Gate 2: no LLM-behavior tests ────────────────────────────────────────────
echo "--- Gate 2: no LLM-behavior tests ---"
if grep -rEi "(claude|anthropic|openai|llm)" \
    "$SCRIPT_DIR/"*.py 2>/dev/null | grep -v '^#'; then
    echo "FAIL Gate 2: LLM-behavior test found"
    exit 1
fi
echo "Gate 2 OK: no LLM-behavior tests"

echo ""

# ── Run pytest ────────────────────────────────────────────────────────────────
echo "--- Running pytest ---"
cd "$REPO_ROOT"
python -m pytest \
    plugins/hep-ph-toolkit/skills/gamlike/tests \
    -v \
    -W error \
    --strict-markers \
    -p no:warnings 2>&1 | head -200 || \
python -m pytest \
    plugins/hep-ph-toolkit/skills/gamlike/tests \
    -v \
    --strict-markers \
    "$@"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=== gamlike suite: ALL PASSED ==="
else
    echo ""
    echo "=== gamlike suite: FAILED (exit $EXIT_CODE) ==="
fi
exit $EXIT_CODE
