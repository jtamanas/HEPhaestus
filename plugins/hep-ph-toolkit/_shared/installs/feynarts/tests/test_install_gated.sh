#!/usr/bin/env bash
# test_install_gated.sh — end-to-end FeynArts install test.
#
# GATED: requires HEPPH_RUN_WOLFRAM_TESTS=1 AND HEPPH_RUN_NETWORK_TESTS=1.
# CI skips this test. Run locally with:
#
#   HEPPH_RUN_WOLFRAM_TESTS=1 HEPPH_RUN_NETWORK_TESTS=1 \
#     bash plugins/hep-ph-toolkit/skills_shared/installs/feynarts/tests/test_install_gated.sh
#
# The test:
#   1. Installs FeynArts 3.11 to a temp directory.
#   2. Verifies FeynArts.m is present.
#   3. Runs smoke test.
#   4. Reports pass/fail; does NOT clean up the install (leave for /feynarts tests).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/../install.sh"

# Gate check
if [ "${HEPPH_RUN_WOLFRAM_TESTS:-0}" != "1" ] || [ "${HEPPH_RUN_NETWORK_TESTS:-0}" != "1" ]; then
  echo "SKIP: test_install_gated.sh requires HEPPH_RUN_WOLFRAM_TESTS=1 AND HEPPH_RUN_NETWORK_TESTS=1"
  exit 0
fi

echo "=== test_install_gated.sh: end-to-end FeynArts install ==="

TMPDIR_INSTALL="$(mktemp -d)"
echo "Install target: $TMPDIR_INSTALL/FeynArts-3.11"

INSTALL_DIR="$TMPDIR_INSTALL/FeynArts-3.11"

# Run install to temp dir
if bash "$INSTALL_SCRIPT" "$INSTALL_DIR"; then
  echo "PASS: install_feynarts.sh exited 0"
else
  RC=$?
  echo "FAIL: install_feynarts.sh exited $RC"
  exit 1
fi

# Verify FeynArts.m present
if [ -f "$INSTALL_DIR/FeynArts.m" ]; then
  echo "PASS: FeynArts.m present at $INSTALL_DIR"
else
  echo "FAIL: FeynArts.m not found at $INSTALL_DIR"
  exit 1
fi

# Run smoke test directly
SMOKE_OUT="$("$SCRIPT_DIR/../smoke_test_feynarts.sh" "$INSTALL_DIR" 2>/dev/null)"
SMOKE_STATUS="$(printf '%s' "$SMOKE_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "parse_error")"

case "$SMOKE_STATUS" in
  ok)
    VERSION="$(printf '%s' "$SMOKE_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null || echo "?")"
    echo "PASS: smoke test passed, version=$VERSION"
    ;;
  activation_required)
    echo "SKIP: Wolfram Engine not activated — smoke test skipped."
    echo "PASS (partial): install completed, activation pending."
    ;;
  *)
    echo "FAIL: smoke test returned status=$SMOKE_STATUS ($SMOKE_OUT)"
    exit 1
    ;;
esac

echo ""
echo "Results: install integration test PASSED."
exit 0
