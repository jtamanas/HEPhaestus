#!/usr/bin/env bash
# install_feynarts.sh — download, extract, and register FeynArts 3.11.
#
# Usage: install_feynarts.sh [install_dir]
#
# Installs to $UserBaseDirectory/Applications/FeynArts-{version}/ by default.
# The UserBaseDirectory is resolved via wolframscript.
# All steps are atomic; partial downloads are cleaned up on failure.

set -euo pipefail

_LOG_TAG="install_feynarts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

WOLFRAM_HELPERS="$SCRIPT_DIR/../../../../shared/install-helpers/wolfram"
DETECT_WOLFRAM="$WOLFRAM_HELPERS/detect_wolfram.sh"
CHECK_ACTIVATION="$WOLFRAM_HELPERS/check_wolfram_activation.sh"
. "$DETECT_WOLFRAM"
. "$SCRIPT_DIR/_blocker.sh"

# Version can be overridden via environment
FEYNARTS_VERSION="${HEPPH_FEYNARTS_VERSION:-3.11}"
TARBALL_URL="https://www.feynarts.de/FeynArts-${FEYNARTS_VERSION}.tar.gz"
EXPECTED_SHA256="TODO"  # Must be replaced before v1.0 release with real checksum

# 1. Check wolframscript
WS="$(detect_wolfram_path)"
if [ -z "$WS" ]; then
  emit_blocker "WOLFRAM_KERNEL_ABSENT" "fatal" \
    "wolframscript binary not found." \
    "Run /install to install Wolfram Engine first."
  exit "$EXIT_NO_WOLFRAM"
fi

# 2. Disk check
check_disk 1 2

# 3. Resolve install directory
INSTALL_DIR="${1:-}"
if [ -z "$INSTALL_DIR" ]; then
  # Resolve $UserBaseDirectory via wolframscript
  USER_BASE_DIR="$("$WS" -code 'Print[$UserBaseDirectory]' 2>/dev/null | tr -d '\n\r' || true)"
  if [ -z "$USER_BASE_DIR" ]; then
    # Fallback heuristics
    if [ "$(uname -s)" = "Darwin" ]; then
      USER_BASE_DIR="$HOME/Library/Wolfram"
    else
      USER_BASE_DIR="$HOME/.WolframEngine"
    fi
  fi
  INSTALL_DIR="$USER_BASE_DIR/Applications/FeynArts-${FEYNARTS_VERSION}"
fi

log "Install target: $INSTALL_DIR"

# Skip if already installed
if [ -f "$INSTALL_DIR/FeynArts.m" ]; then
  log "FeynArts already present at $INSTALL_DIR — re-registering."
  "$SCRIPT_DIR/use_path_feynarts.sh" "$INSTALL_DIR"
  exit $?
fi

# 4. Download
TMPDIR_WORK="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_WORK"' EXIT

TARBALL="$TMPDIR_WORK/FeynArts-${FEYNARTS_VERSION}.tar.gz"
log "Downloading FeynArts $FEYNARTS_VERSION from $TARBALL_URL ..."
download_with_retry "$TARBALL_URL" "$TARBALL" "FEYNARTS"

# 5. Checksum
# If HEPPH_FEYNARTS_SKIP_SHA256=1 is set, skip verification with a warning
# (useful in development environments before the real checksum is pinned).
# If EXPECTED_SHA256 is still "TODO" and the bypass is NOT set, emit a
# fatal blocker: FEYNARTS_SHA256_NOT_PINNED.
if [ "${HEPPH_FEYNARTS_SKIP_SHA256:-0}" = "1" ]; then
  warn "HEPPH_FEYNARTS_SKIP_SHA256=1 — skipping SHA256 checksum verification."
  warn "This is insecure. Compute the real checksum and set sha256 in skill_env.yaml before release."
elif [ "$EXPECTED_SHA256" = "TODO" ]; then
  emit_blocker "FEYNARTS_SHA256_NOT_PINNED" "fatal" \
    "SHA256 checksum for FeynArts-${FEYNARTS_VERSION}.tar.gz is not pinned (value: TODO)." \
    "Compute the real checksum with: sha256sum FeynArts-${FEYNARTS_VERSION}.tar.gz, update sha256 in skill_env.yaml, then retry. To bypass in dev only: HEPPH_FEYNARTS_SKIP_SHA256=1"
  exit 30
else
  verify_checksum "$TARBALL" "$EXPECTED_SHA256"
fi

# 6. Extract
log "Extracting $TARBALL ..."
mkdir -p "$INSTALL_DIR"
if tar -tzf "$TARBALL" 2>/dev/null | head -n1 | grep -q '^FeynArts'; then
  # tarball has a top-level FeynArts directory — strip one level
  tar -xzf "$TARBALL" -C "$INSTALL_DIR" --strip-components=1 2>/dev/null \
    || tar -xzf "$TARBALL" -C "$(dirname "$INSTALL_DIR")" 2>/dev/null
else
  tar -xzf "$TARBALL" -C "$INSTALL_DIR" 2>/dev/null
fi

if [ ! -f "$INSTALL_DIR/FeynArts.m" ]; then
  err "Extraction failed: FeynArts.m not found at $INSTALL_DIR."
  emit_blocker "FEYNARTS_SMOKE_TEST" "fatal" \
    "FeynArts extraction produced no FeynArts.m." \
    "Check tarball integrity and retry /feynarts-install install."
  exit 28
fi

# 7. Register via use_path (runs smoke test + writes config)
"$SCRIPT_DIR/use_path_feynarts.sh" "$INSTALL_DIR"
