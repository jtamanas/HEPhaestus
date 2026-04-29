#!/usr/bin/env bash
# _macos_env.sh — macOS-specific environment setup for micrOMEGAs build.
# Source into install_impl.sh on macOS. Sets SDKROOT, FFLAGS, LDFLAGS, DYLD_LIBRARY_PATH.
#
# Known limitation (v1.1 TODO): patch CalcHEP_src/getFlags for arm64.
# On clang 15+ arm64, the bundled getFlags emits x86_64 flags which cause
# build failures. Workaround: user passes a pre-patched CalcHEP via --calchep-path.
# See SKILL.md § macOS notes for details.

_macos_env_setup() {
  local path="$1"  # micrOMEGAs root

  if [ "$(uname -s)" != "Darwin" ]; then
    return 0
  fi

  # Phase-0 SDK helper
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SHARED_CHECK="$SCRIPT_DIR/../../../../shared/install-helpers/check_macos_sdk.sh"

  local sdk_json
  if [ -f "$SHARED_CHECK" ]; then
    sdk_json="$(bash "$SHARED_CHECK" 2>/dev/null || true)"
  else
    sdk_json='{"looptools_quad":true,"sdkroot":"","ldflags":""}'
  fi

  local sdkroot ldflags
  sdkroot="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('sdkroot',''))" "$sdk_json" 2>/dev/null || true)"
  ldflags="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('ldflags',''))" "$sdk_json" 2>/dev/null || true)"

  if [ -z "$sdkroot" ]; then
    # Try xcrun directly
    sdkroot="$(xcrun --show-sdk-path 2>/dev/null || true)"
  fi

  if [ -z "$sdkroot" ]; then
    SCRIPT_DIR_BLK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    . "$SCRIPT_DIR_BLK/_blocker.sh"
    emit_blocker MICROMEGAS_MACOS_SDK_MISMATCH fatal \
      "xcrun --show-sdk-path failed or returned empty. Install Xcode Command Line Tools." \
      "Run: xcode-select --install" \
      '{"sdkroot":""}'
    exit 31
  fi

  export SDKROOT="$sdkroot"

  # Homebrew gfortran → -ff2c + -ld_classic
  if command -v gfortran >/dev/null 2>&1 && gfortran --version 2>/dev/null | grep -qi homebrew; then
    export FFLAGS="${FFLAGS:+$FFLAGS }-ff2c"
    export LDFLAGS="${LDFLAGS:+$LDFLAGS }${ldflags:--Wl,-ld_classic}"
  elif [ -n "$ldflags" ]; then
    export LDFLAGS="${LDFLAGS:+$LDFLAGS }$ldflags"
  fi

  # DYLD_LIBRARY_PATH for smoke scope only (not written to user shell)
  export DYLD_LIBRARY_PATH="${path}/lib:${DYLD_LIBRARY_PATH:-}"
}
