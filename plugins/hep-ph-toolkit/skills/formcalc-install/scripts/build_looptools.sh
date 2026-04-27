#!/usr/bin/env bash
# build_looptools.sh — build LoopTools from the FormCalc-bundled source tree.
#
# Usage: build_looptools.sh <looptools_src_dir> <install_root> [looptools_version]
#
# The LoopTools source is bundled inside the FormCalc tarball under
# <formcalc_src>/LoopTools/.  This script runs ./configure && make
# inside that directory.
#
# Apple-Silicon branch:
#   uname -m == arm64 → probes gfortran at brew --prefix gcc@{13,14,15} and
#   brew --prefix gcc.  If libquadmath.dylib is absent → --without-quad.
#   Records looptools_quad: false in config.
#
# Exits EXIT_LOOPTOOLS_BUILD=29 on failure with blocker LOOPTOOLS_BUILD_FAILED.
set -euo pipefail

# ── Source shared helpers if not already sourced ─────────────────────────────
if ! declare -f log > /dev/null 2>&1; then
  _BLT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  _PLUGINS_DIR="$(cd "$_BLT_SCRIPT_DIR/../../../../.." && pwd)/plugins"
  _COMMON="$_PLUGINS_DIR/shared/install-helpers/_common.sh"
  _ATOMIC="$_PLUGINS_DIR/shared/install-helpers/atomic_write.sh"
  if [ ! -f "$_COMMON" ]; then
    echo "[build_looptools] ERROR: _common.sh not found at $_COMMON" >&2
    exit 1
  fi
  . "$_COMMON"
  . "$_ATOMIC"
fi

# ── Args ──────────────────────────────────────────────────────────────────────
LT_SRC_DIR="${1:?build_looptools.sh: LT_SRC_DIR required}"
INSTALL_ROOT="${2:?build_looptools.sh: INSTALL_ROOT required}"
LT_VERSION="${3:-10.0}"

_lt_fatal() {
  printf '{"code":"LOOPTOOLS_BUILD_FAILED","mode":"fatal","message":"%s","context":{"src_dir":"%s","install_root":"%s"}}\n' \
    "$1" "$LT_SRC_DIR" "$INSTALL_ROOT" >&2
  exit $EXIT_LOOPTOOLS_BUILD
}

# ── macOS SDK + quadmath probe ─────────────────────────────────────────────────
ARCH="$(uname -m)"
LOOPTOOLS_QUAD="true"
EXTRA_CONFIGURE_FLAGS=""
FC_OVERRIDE=""
LDFLAGS_EXTRA=""

if [ "$ARCH" = "arm64" ]; then
  log "Apple Silicon detected — probing gfortran + libquadmath..."

  # Probe brew prefixes for gcc@13, 14, 15, and plain gcc.
  GFORTRAN_CANDIDATES=()
  for slot in 13 14 15; do
    prefix=""
    prefix="$(brew --prefix "gcc@${slot}" 2>/dev/null || true)"
    if [ -n "$prefix" ] && [ -d "$prefix/bin" ]; then
      while IFS= read -r gf; do
        [ -x "$gf" ] && GFORTRAN_CANDIDATES+=("$gf")
      done < <(ls "$prefix/bin/gfortran"* 2>/dev/null || true)
    fi
  done
  prefix="$(brew --prefix gcc 2>/dev/null || true)"
  if [ -n "$prefix" ] && [ -d "$prefix/bin" ]; then
    while IFS= read -r gf; do
      [ -x "$gf" ] && GFORTRAN_CANDIDATES+=("$gf")
    done < <(ls "$prefix/bin/gfortran"* 2>/dev/null || true)
  fi

  # Also check standard gfortran.
  if command -v gfortran >/dev/null 2>&1; then
    GFORTRAN_CANDIDATES+=("$(command -v gfortran)")
  fi

  # Pick first candidate that has libquadmath, or record quad: false.
  FOUND_QUAD=false
  for gf in "${GFORTRAN_CANDIDATES[@]+"${GFORTRAN_CANDIDATES[@]}"}"; do
    quad_path="$("$gf" -print-file-name=libquadmath.dylib 2>/dev/null || true)"
    quad_path="${quad_path//[$'\r\n']/}"
    if [ -n "$quad_path" ] && [ "$quad_path" != "libquadmath.dylib" ] && [ -f "$quad_path" ]; then
      FOUND_QUAD=true
      FC_OVERRIDE="$gf"
      log "Found libquadmath.dylib via $gf → quad enabled"
      break
    fi
  done

  if [ "$FOUND_QUAD" = "false" ]; then
    LOOPTOOLS_QUAD="false"
    EXTRA_CONFIGURE_FLAGS="--without-quad"
    log "libquadmath.dylib absent — building LoopTools WITHOUT quad support"
  fi

  # macOS SDK ldflags.
  SDK_JSON=""
  _CHECK_SDK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  _SDK_SCRIPT="$(cd "$_CHECK_SDK/../../../../.." && pwd)/plugins/shared/install-helpers/check_macos_sdk.sh"
  if [ -f "$_SDK_SCRIPT" ]; then
    SDK_JSON="$(bash "$_SDK_SCRIPT" 2>/dev/null || true)"
    LDFLAGS_EXTRA="$(printf '%s' "$SDK_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('ldflags',''))" 2>/dev/null || true)"
  fi
fi

# ── Build ─────────────────────────────────────────────────────────────────────
if [ ! -d "$LT_SRC_DIR" ]; then
  _lt_fatal "LoopTools source directory not found: $LT_SRC_DIR"
fi

LT_INSTALL="$INSTALL_ROOT/looptools"
mkdir -p "$LT_INSTALL"

LOG_DIR="$LT_INSTALL"
mkdir -p "$LOG_DIR"

cd "$LT_SRC_DIR"

# Apply FC override if found.
CONFIGURE_ENV=()
if [ -n "$FC_OVERRIDE" ]; then
  CONFIGURE_ENV+=("FC=$FC_OVERRIDE")
fi
if [ -n "$LDFLAGS_EXTRA" ]; then
  CONFIGURE_ENV+=("LDFLAGS=$LDFLAGS_EXTRA")
fi

log "Configuring LoopTools ${LT_VERSION} (prefix=$LT_INSTALL)..."
if ! env "${CONFIGURE_ENV[@]+"${CONFIGURE_ENV[@]}"}" \
     ./configure --prefix="$LT_INSTALL" $EXTRA_CONFIGURE_FLAGS \
     >> "$LOG_DIR/looptools_configure.log" 2>&1; then
  _lt_fatal "LoopTools ./configure failed (see $LOG_DIR/looptools_configure.log)"
fi

log "Building LoopTools ${LT_VERSION}..."
if ! make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)" \
     >> "$LOG_DIR/looptools_make.log" 2>&1; then
  _lt_fatal "LoopTools make failed (see $LOG_DIR/looptools_make.log)"
fi

# Locate the built library.
LT_LIB=""
for candidate in \
    "$LT_SRC_DIR/build/libooptools.a" \
    "$LT_SRC_DIR/lib/libooptools.a" \
    "$LT_INSTALL/lib/libooptools.a"; do
  if [ -f "$candidate" ]; then
    LT_LIB="$candidate"
    break
  fi
done

# Also search inside build subdirs.
if [ -z "$LT_LIB" ]; then
  LT_LIB="$(find "$LT_SRC_DIR" -name "libooptools.a" 2>/dev/null | head -1 || true)"
fi

if [ -z "$LT_LIB" ]; then
  _lt_fatal "libooptools.a not found after make"
fi

log "LoopTools built: $LT_LIB (quad=$LOOPTOOLS_QUAD)"

# Emit results on stdout as key=value pairs for caller to parse.
printf 'looptools_lib=%s\n' "$LT_LIB"
printf 'looptools_quad=%s\n' "$LOOPTOOLS_QUAD"
printf 'looptools_version=%s\n' "$LT_VERSION"
