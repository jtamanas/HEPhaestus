#!/usr/bin/env bash
# build_form.sh — download + build FORM 4.3.1.
#
# Usage: build_form.sh <install_root> <form_version>
# Can be called as a standalone script or sourced by install_formcalc_full.sh.
#
# Installs FORM binary at: <install_root>/form/<arch>-<os>/form
# No $PATH symlinks. No shell rc modifications.
# Exits EXIT_FORM_BUILD=28 on failure with blocker FORM_BUILD_FAILED.
set -euo pipefail

# ── Source shared helpers if not already sourced ─────────────────────────────
if ! declare -f log > /dev/null 2>&1; then
  _BUILD_FORM_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  _PLUGINS_DIR="$(cd "$_BUILD_FORM_SCRIPT_DIR/../../../../.." && pwd)/plugins"
  _COMMON="$_PLUGINS_DIR/shared/install-helpers/_common.sh"
  _ATOMIC="$_PLUGINS_DIR/shared/install-helpers/atomic_write.sh"
  if [ ! -f "$_COMMON" ]; then
    echo "[build_form] ERROR: _common.sh not found at $_COMMON" >&2
    exit 1
  fi
  . "$_COMMON"
  . "$_ATOMIC"
fi

# ── Args ─────────────────────────────────────────────────────────────────────
INSTALL_ROOT="${1:?build_form.sh: INSTALL_ROOT required}"
FORM_VERSION="${2:?build_form.sh: FORM_VERSION required}"

# ── Arch / OS detection ───────────────────────────────────────────────────────
ARCH="$(uname -m)"
OS_SYS="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$OS_SYS" in
  darwin) OS_TAG="macos" ;;
  linux*)  OS_TAG="linux" ;;
  *)       OS_TAG="$OS_SYS" ;;
esac

FORM_DEST_DIR="$INSTALL_ROOT/form/${ARCH}-${OS_TAG}"
FORM_BINARY="$FORM_DEST_DIR/form"

# ── Source URL ────────────────────────────────────────────────────────────────
# FORM source releases on GitHub (form-dev/form), with vermaseren/form redirect.
# Verified live: HTTP 200 via github.com/vermaseren/form → github.com/form-dev/form
FORM_URL="https://github.com/vermaseren/form/releases/download/v${FORM_VERSION}/form-${FORM_VERSION}.tar.gz"
FORM_SHA256="${HEPPH_FORM_SHA256:-f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce}"

# ── Build ─────────────────────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

_form_fatal() {
  printf '{"code":"FORM_BUILD_FAILED","mode":"fatal","message":"%s","context":{"install_root":"%s","form_version":"%s"}}\n' \
    "$1" "$INSTALL_ROOT" "$FORM_VERSION" >&2
  exit $EXIT_FORM_BUILD
}

log "Downloading FORM ${FORM_VERSION}..."
TARBALL="$WORK_DIR/form-${FORM_VERSION}.tar.gz"
if ! download_with_retry "$FORM_URL" "$TARBALL" "FORM"; then
  _form_fatal "FORM tarball download failed"
fi

verify_checksum "$TARBALL" "$FORM_SHA256"

log "Extracting FORM ${FORM_VERSION}..."
if ! tar -xzf "$TARBALL" -C "$WORK_DIR"; then
  _form_fatal "FORM tarball extraction failed"
fi

# Find the source directory.
FORM_SRC_DIR=""
for d in "$WORK_DIR"/form-*; do
  if [ -d "$d" ]; then
    FORM_SRC_DIR="$d"
    break
  fi
done
if [ -z "$FORM_SRC_DIR" ]; then
  _form_fatal "FORM source directory not found after extraction"
fi

log "Configuring FORM ${FORM_VERSION} (prefix=$FORM_DEST_DIR)..."
mkdir -p "$FORM_DEST_DIR"
cd "$FORM_SRC_DIR"

# FORM's configure is pre-generated (no autoreconf needed).
if [ ! -x "./configure" ]; then
  _form_fatal "FORM configure script not found — unexpected tarball structure"
fi

if ! ./configure --prefix="$FORM_DEST_DIR" >> "$FORM_DEST_DIR/form_configure.log" 2>&1; then
  _form_fatal "FORM ./configure failed (see $FORM_DEST_DIR/form_configure.log)"
fi

log "Building FORM ${FORM_VERSION}..."
if ! make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)" \
     >> "$FORM_DEST_DIR/form_make.log" 2>&1; then
  _form_fatal "FORM make failed (see $FORM_DEST_DIR/form_make.log)"
fi

# Install just the binary (no 'make install' to avoid writing to system paths).
BUILT_BINARY=""
for f in "$FORM_SRC_DIR/src/form" "$FORM_SRC_DIR/form" "$FORM_SRC_DIR/bin/form"; do
  if [ -x "$f" ]; then
    BUILT_BINARY="$f"
    break
  fi
done
if [ -z "$BUILT_BINARY" ]; then
  _form_fatal "FORM binary not found after make — looked in $FORM_SRC_DIR"
fi

cp "$BUILT_BINARY" "$FORM_BINARY"
chmod +x "$FORM_BINARY"
log "FORM binary installed at $FORM_BINARY"

# Emit the binary path on stdout for callers.
echo "$FORM_BINARY"
