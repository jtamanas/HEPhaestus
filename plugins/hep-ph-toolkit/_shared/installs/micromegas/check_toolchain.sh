#!/usr/bin/env bash
# check_toolchain.sh — Toolchain precondition check for /micromegas-install.
#
# Verifies, in order:
#   1. C compiler:  gcc or clang on PATH  → CC_ABSENT if missing
#   2. gfortran:    gfortran on PATH      → GFORTRAN_ABSENT if missing
#   3. GNU make:    gmake, or `make` that is GNU make → GNU_MAKE_ABSENT if missing
#
# Also warns (not blocks) when X11 development headers are absent — they are
# only needed for the CalcHEP interactive GUI, not for batch-mode DM
# observables (relic density, direct detection, indirect detection).
#
# Origin: this script was migrated from the v0 monte-carlo-tools version of
# /micromegas-install when the two skills were consolidated. It is sourced by
# install_impl.sh at stage 0 (before disk-check) to catch toolchain gaps with
# a friendly, per-OS install hint rather than letting `make` fail opaquely.
#
# Exit codes on failure are drawn from shared _common.sh:
#   EXIT_NO_GFORTRAN (10) for GFORTRAN_ABSENT
#   EXIT_NO_LAPACK   (25) for CC_ABSENT and GNU_MAKE_ABSENT (reused)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared helpers
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Source blocker helper
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="check_toolchain"

# ---------------------------------------------------------------------------
# Per-OS install-hint helpers
# ---------------------------------------------------------------------------

cc_hint() {
  case "$(os_name)" in
    macos)
      echo "Install Xcode Command Line Tools: xcode-select --install  (or install a Homebrew gcc: brew install gcc)"
      ;;
    linux)
      echo "Install a C compiler: sudo apt-get install -y build-essential  (Debian/Ubuntu) or sudo yum install -y gcc  (RHEL/CentOS)"
      ;;
    *)
      echo "Install a C compiler (gcc or clang) for your OS before retrying."
      ;;
  esac
}

gfortran_hint() {
  case "$(os_name)" in
    macos)
      echo "Install gfortran with Homebrew: brew install gcc"
      ;;
    linux)
      echo "Install gfortran with: sudo apt-get install -y gfortran  (Debian/Ubuntu) or sudo yum install -y gcc-gfortran  (RHEL/CentOS)"
      ;;
    *)
      echo "Install a Fortran compiler (gfortran) for your OS before retrying."
      ;;
  esac
}

gnu_make_hint() {
  case "$(os_name)" in
    macos)
      echo "Install GNU make with Homebrew: brew install make  (installs as gmake)"
      ;;
    linux)
      echo "Install GNU make with: sudo apt-get install -y make  (Debian/Ubuntu) or sudo yum install -y make  (RHEL/CentOS)"
      ;;
    *)
      echo "Install GNU make for your OS before retrying."
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

check_cc() {
  if command -v gcc >/dev/null 2>&1; then
    log "C compiler found: gcc ($(command -v gcc))"
    return 0
  fi
  if command -v clang >/dev/null 2>&1; then
    log "C compiler found: clang ($(command -v clang))"
    return 0
  fi
  emit_blocker "CC_ABSENT" "fatal" \
    "A C compiler (gcc or clang) is required to build micrOMEGAs but was not found on PATH." \
    "$(cc_hint)"
  exit "$EXIT_NO_LAPACK"  # 25 — reused per SKILL.md exit-code table
}

check_gfortran() {
  if command -v gfortran >/dev/null 2>&1; then
    log "gfortran found: $(command -v gfortran)"
    return 0
  fi
  emit_blocker "GFORTRAN_ABSENT" "fatal" \
    "gfortran is required to build micrOMEGAs but was not found on PATH." \
    "$(gfortran_hint)"
  exit "$EXIT_NO_GFORTRAN"
}

check_gnu_make() {
  # Prefer gmake; else accept `make` if it reports itself as GNU make.
  if command -v gmake >/dev/null 2>&1; then
    log "GNU make found: gmake ($(command -v gmake))"
    return 0
  fi
  if command -v make >/dev/null 2>&1; then
    if make --version 2>/dev/null | head -n1 | grep -qi 'gnu make'; then
      log "GNU make found: make ($(command -v make))"
      return 0
    fi
  fi
  emit_blocker "GNU_MAKE_ABSENT" "fatal" \
    "GNU make (gmake, or a GNU-compatible make) is required to build micrOMEGAs but was not found on PATH." \
    "$(gnu_make_hint)"
  exit "$EXIT_NO_LAPACK"  # 25 — reused per SKILL.md exit-code table
}

check_x11_optional() {
  # Best-effort: look for a common X11 header. Absence is a WARNING, not a blocker.
  local hdr_candidates=(
    "/usr/include/X11/Xlib.h"
    "/usr/local/include/X11/Xlib.h"
    "/opt/X11/include/X11/Xlib.h"          # XQuartz (macOS)
    "/opt/homebrew/include/X11/Xlib.h"     # Apple Silicon Homebrew
  )
  local hdr
  for hdr in "${hdr_candidates[@]}"; do
    if [ -f "$hdr" ]; then
      log "X11 headers found: $hdr"
      return 0
    fi
  done
  warn "X11 development headers not found — CalcHEP's interactive GUI (s_calchep) will not launch."
  warn "Batch-mode DM observables (relic density, direct/indirect detection) do not need X11 and will still work."
  case "$(os_name)" in
    macos)
      warn "To enable the GUI, install XQuartz: brew install --cask xquartz"
      ;;
    linux)
      warn "To enable the GUI, install X11 dev headers: sudo apt-get install -y libx11-dev  (Debian/Ubuntu) or sudo yum install -y libX11-devel  (RHEL/Fedora)"
      ;;
  esac
  return 0
}

# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------
check_toolchain_present() {
  check_cc
  check_gfortran
  check_gnu_make
  check_x11_optional
  log "Toolchain OK (C compiler + gfortran + GNU make all present)."
}

# Run check when executed directly (not sourced).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  check_toolchain_present
fi
