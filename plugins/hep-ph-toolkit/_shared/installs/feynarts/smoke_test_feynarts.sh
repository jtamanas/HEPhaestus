#!/usr/bin/env bash
# smoke_test_feynarts.sh — run a minimal FeynArts smoke test via wolframscript.
#
# Usage: smoke_test_feynarts.sh <feynarts_path>
#
# Exits 0 if FeynArts loads and $FeynArtsVersion is non-empty.
# Exits EXIT_FEYNARTS_SMOKE (28) on failure.
# Emits {"status":"activation_required",...} to stdout when Wolfram needs activation.
#
# Reads wolfram_engine_path from config.

set -euo pipefail

_LOG_TAG="smoke_test_feynarts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

WOLFRAM_HELPERS="$SCRIPT_DIR/../../../../shared/install-helpers/wolfram"
CHECK_ACTIVATION="$WOLFRAM_HELPERS/check_wolfram_activation.sh"
DETECT_WOLFRAM="$WOLFRAM_HELPERS/detect_wolfram.sh"

# Source blocker helper
. "$SCRIPT_DIR/_blocker.sh"

FEYNARTS_PATH="${1:-}"

if [ -z "$FEYNARTS_PATH" ]; then
  # Try to get from config
  FEYNARTS_PATH="$(config_get feynarts_path || true)"
fi

if [ -z "$FEYNARTS_PATH" ] || [ ! -f "$FEYNARTS_PATH/FeynArts.m" ]; then
  emit_blocker "FEYNARTS_PATH_INVALID" "fatal" \
    "FeynArts.m not found at '$FEYNARTS_PATH'." \
    "Provide a valid FeynArts directory via bash _shared/installs/feynarts/install.sh use-path <dir>."
  exit 27
fi

# Get wolframscript path
. "$DETECT_WOLFRAM"
WS="$(detect_wolfram_path)"
if [ -z "$WS" ]; then
  emit_blocker "WOLFRAM_KERNEL_ABSENT" "fatal" \
    "wolframscript binary not found." \
    "Run /install to install Wolfram Engine first."
  exit "$EXIT_NO_WOLFRAM"
fi

log "Running FeynArts smoke test (path=$FEYNARTS_PATH)..."

# Run the smoke test
SMOKE_OUT="$("$WS" -code "AppendTo[\$Path,\"$FEYNARTS_PATH\"]; Needs[\"FeynArts\`\"]; Print[\$FeynArtsVersion]" 2>&1)" \
  && SMOKE_RC=0 || SMOKE_RC=$?

# Check for activation requirement via shared helper
ACTIVATION_JSON="$(printf '%s' "$SMOKE_OUT" | python3 "$WOLFRAM_HELPERS/_activation_parse.py" "$SMOKE_RC" 2>/dev/null || true)"
ACTIVATION_STATUS="$(printf '%s' "$ACTIVATION_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)"

if [ "$ACTIVATION_STATUS" = "activation_required" ]; then
  log "Wolfram Engine requires activation."
  printf '%s\n' "$ACTIVATION_JSON"
  exit 0
fi

# Extract version from output
VERSION="$(printf '%s' "$SMOKE_OUT" | grep -Eo '[0-9]+\.[0-9]+' | head -n1 || true)"

if [ -z "$VERSION" ]; then
  emit_blocker "FEYNARTS_SMOKE_TEST" "fatal" \
    "FeynArts smoke test failed: no version string in output." \
    "Check Wolfram Engine activation and FeynArts installation."
  exit 28
fi

log "FeynArts smoke test passed: version=$VERSION"
printf '{"status":"ok","version":"%s"}\n' "$VERSION"
exit 0
