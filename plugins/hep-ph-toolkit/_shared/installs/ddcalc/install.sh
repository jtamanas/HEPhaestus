#!/usr/bin/env bash
# install.sh — _shared/installs/ddcalc entry point.
# Install DDCalc 2.2.0 from source.
# Usage: install.sh [<install_dir>] [--with-overlay <name>]
# Exit: 0 on success; non-zero with blocker JSON on stderr on failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
CHECK_SDK="$SCRIPT_DIR/../../../../shared/install-helpers/check_macos_sdk.sh"
. "$SHARED_COMMON"

_tag="ddcalc-install"

SKILL_ENV="$SCRIPT_DIR/../skill_env.yaml"

# Parse skill_env.yaml
_yaml_get() {
  python3 - "$SKILL_ENV" "$1" <<'PY'
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
print(data.get(sys.argv[2], ""))
PY
}

DDCALC_VERSION="$(_yaml_get HEPPH_DDCALC_VERSION)"
DDCALC_SHA256="$(_yaml_get HEPPH_DDCALC_SHA256)"
DDCALC_FFLAGS="$(_yaml_get HEPPH_DDCALC_FFLAGS)"
DDCALC_CFLAGS="$(_yaml_get HEPPH_DDCALC_CFLAGS)"

# ── Parse arguments ─────────────────────────────────────────────────────────
INSTALL_DIR=""
OVERLAY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --with-overlay)
      OVERLAY="${2:?overlay name required}"
      shift 2
      ;;
    --*)
      err "Unknown option: $1"; exit 1
      ;;
    *)
      INSTALL_DIR="$1"
      shift
      ;;
  esac
done

STATE_ROOT="${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}"
INSTALL_DIR="${INSTALL_DIR:-$STATE_ROOT/tools/DDCalc}"

# ── Prerequisites ────────────────────────────────────────────────────────────
if ! command -v gfortran >/dev/null 2>&1; then
  "$SCRIPT_DIR/_blocker.sh" GFORTRAN_ABSENT \
    "gfortran not found in PATH. Install gfortran (e.g. brew install gcc)." \
    '{}' >&2
  exit "$EXIT_NO_GFORTRAN"
fi

check_disk 2 4

# ── macOS SDK flags ───────────────────────────────────────────────────────────
SDK_JSON="{}"
if [ -x "$CHECK_SDK" ]; then
  SDK_JSON="$(bash "$CHECK_SDK" 2>/dev/null || echo '{}')"
fi
LDFLAGS="$(echo "$SDK_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ldflags',''))" 2>/dev/null || echo "")"
SDKROOT="$(echo "$SDK_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sdkroot',''))" 2>/dev/null || echo "")"

log "SDK flags: LDFLAGS='$LDFLAGS' SDKROOT='$SDKROOT'"

# ── Download ───────────────────────────────────────────────────────────────────
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TARBALL="$TMP_DIR/ddcalc.tgz"
DDCALC_URL="$(bash "$SCRIPT_DIR/_probe_url.sh" 2>/dev/null || true)"
if [ -z "$DDCALC_URL" ]; then
  # Fallback to configured primary URL
  DDCALC_URL="$(_yaml_get HEPPH_DDCALC_URL)"
fi

log "Downloading DDCalc $DDCALC_VERSION from $DDCALC_URL"
download_with_retry "$DDCALC_URL" "$TARBALL" DDCALC

verify_checksum "$TARBALL" "$DDCALC_SHA256"

# ── Extract ────────────────────────────────────────────────────────────────────
SRC_DIR="$TMP_DIR/src"
mkdir -p "$SRC_DIR"
tar -xzf "$TARBALL" -C "$SRC_DIR" --strip-components=1 2>&1 | \
  head -5 || { err "Failed to extract DDCalc tarball"; exit "$EXIT_EXTRACT"; }
log "Extracted DDCalc source."

# ── Apply version banner patch ─────────────────────────────────────────────────
BANNER_PATCH="$SCRIPT_DIR/patches/version_banner.patch"
if [ -f "$BANNER_PATCH" ]; then
  log "Applying version banner patch..."
  (cd "$SRC_DIR" && git apply --ignore-whitespace "$BANNER_PATCH" 2>&1) || \
  (cd "$SRC_DIR" && patch -p1 < "$BANNER_PATCH" 2>&1) || \
    warn "Version banner patch did not apply cleanly (non-fatal)."
fi

# ── Apply overlay (native-only v1: overlays deferred to v1.1) ─────────────────
if [ -n "$OVERLAY" ]; then
  log "Overlay requested: $OVERLAY"
  bash "$SCRIPT_DIR/apply_overlay.sh" "$SRC_DIR" "$OVERLAY" || {
    exit $?
  }
fi

# ── Build ──────────────────────────────────────────────────────────────────────
log "Building DDCalc..."
BUILD_LOG="$TMP_DIR/build.log"

BUILD_ENV=""
[ -n "$SDKROOT" ] && BUILD_ENV="SDKROOT=$SDKROOT "
[ -n "$LDFLAGS" ] && BUILD_ENV="${BUILD_ENV}LDFLAGS=$LDFLAGS "

set +e
eval "env ${BUILD_ENV}FFLAGS='$DDCALC_FFLAGS' CFLAGS='$DDCALC_CFLAGS' \
  make -C '$SRC_DIR' lib FC=gfortran 2>&1" > "$BUILD_LOG"
MAKE_RC=$?
set -e

if [ $MAKE_RC -ne 0 ]; then
  BUILD_LOG_TAIL="$(tail -40 "$BUILD_LOG" | python3 -c "
import sys, json
lines = sys.stdin.read()
print(json.dumps(lines))" 2>/dev/null || echo '""')"
  "$SCRIPT_DIR/_blocker.sh" DDCALC_BUILD_FAILED \
    "DDCalc make failed (exit $MAKE_RC). See build_log_tail in context." \
    "{\"build_log_tail\":$BUILD_LOG_TAIL}" >&2
  exit 1
fi
log "Build succeeded."

# ── Install ────────────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR/lib" "$INSTALL_DIR/include" "$INSTALL_DIR/data"
cp "$SRC_DIR/lib/libDDCalc.a" "$INSTALL_DIR/lib/"
cp "$SRC_DIR/include/"*.hpp "$INSTALL_DIR/include/" 2>/dev/null || true
cp -r "$SRC_DIR/data/" "$INSTALL_DIR/" 2>/dev/null || true

# Copy test binary if built
for prog in DDCalc_test DDCalc_exampleC; do
  [ -x "$SRC_DIR/$prog" ] && cp "$SRC_DIR/$prog" "$INSTALL_DIR/" || true
done

# ── Smoke test ────────────────────────────────────────────────────────────────
DETECTED_VERSION="$(bash "$SCRIPT_DIR/_smoke_test.sh" "$INSTALL_DIR" 2>&1)" || {
  exit "$EXIT_SMOKE"
}
log "Smoke test passed. DDCalc version: $DETECTED_VERSION"

# ── Record in config ──────────────────────────────────────────────────────────
UPSTREAM_COMMIT="$(_yaml_get HEPPH_DDCALC_UPSTREAM_COMMIT)"
config_merge \
  ddcalc_path "$INSTALL_DIR" \
  ddcalc_version "$DETECTED_VERSION" \
  ddcalc_installed_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  ddcalc_upstream_url "$DDCALC_URL" \
  ddcalc_upstream_commit "$UPSTREAM_COMMIT" \
  ddcalc_experiment_set "native"

log "DDCalc $DETECTED_VERSION installed to $INSTALL_DIR"
printf '{"status":"installed","path":"%s","version":"%s"}\n' \
  "$INSTALL_DIR" "$DETECTED_VERSION"
