#!/usr/bin/env bash
# use_path_feynarts.sh — register an existing FeynArts install and run smoke test.
#
# Usage: use_path_feynarts.sh <dir>
#
# Writes feynarts_path, feynarts_version, feynarts_installed_at,
# feynarts_generic_model_hash to config on success.
# Emits blocker on failure.

set -euo pipefail

_LOG_TAG="use_path_feynarts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

WOLFRAM_HELPERS="$SCRIPT_DIR/../../../../shared/install-helpers/wolfram"
DETECT_WOLFRAM="$WOLFRAM_HELPERS/detect_wolfram.sh"
. "$DETECT_WOLFRAM"
. "$SCRIPT_DIR/_blocker.sh"

TARGET_DIR="${1:-}"

if [ -z "$TARGET_DIR" ]; then
  echo "Usage: $(basename "$0") <feynarts-dir>" >&2
  exit 1
fi

# Normalize path
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd || echo "$TARGET_DIR")"

# Check FeynArts.m exists
if [ ! -f "$TARGET_DIR/FeynArts.m" ]; then
  emit_blocker "FEYNARTS_PATH_INVALID" "fatal" \
    "No FeynArts.m found at '$TARGET_DIR'." \
    "Provide the path to a valid FeynArts package directory."
  exit 27
fi

# Check wolframscript
WS="$(detect_wolfram_path)"
if [ -z "$WS" ]; then
  emit_blocker "WOLFRAM_KERNEL_ABSENT" "fatal" \
    "wolframscript binary not found or not configured." \
    "Run /install to install Wolfram Engine, then rerun /feynarts-install use-path."
  exit "$EXIT_NO_WOLFRAM"
fi

log "Registering FeynArts at $TARGET_DIR ..."

# Run smoke test
SMOKE_JSON="$("$SCRIPT_DIR/smoke_test_feynarts.sh" "$TARGET_DIR")"
SMOKE_STATUS="$(printf '%s' "$SMOKE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)"

case "$SMOKE_STATUS" in
  ok)
    VERSION="$(printf '%s' "$SMOKE_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('version','unknown'))" 2>/dev/null || true)"
    ;;
  activation_required)
    # Pass through to caller
    printf '%s\n' "$SMOKE_JSON"
    exit 0
    ;;
  *)
    # smoke_test_feynarts.sh already emitted a blocker
    exit 28
    ;;
esac

# Compute Lorentz.gen hash for cache-key input
LORENTZ_GEN="$TARGET_DIR/Models/Lorentz.gen"
LORENTZ_HASH=""
if [ -f "$LORENTZ_GEN" ]; then
  if command -v sha256sum >/dev/null 2>&1; then
    LORENTZ_HASH="$(sha256sum "$LORENTZ_GEN" | awk '{print $1}')"
  else
    LORENTZ_HASH="$(shasum -a 256 "$LORENTZ_GEN" | awk '{print $1}')"
  fi
fi

INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

config_merge \
  feynarts_path "$TARGET_DIR" \
  feynarts_version "$VERSION" \
  feynarts_installed_at "$INSTALLED_AT" \
  feynarts_generic_model_hash "$LORENTZ_HASH"

log "FeynArts $VERSION registered at $TARGET_DIR."
printf '{"status":"configured","path":"%s","version":"%s"}\n' "$TARGET_DIR" "$VERSION"
exit 0
