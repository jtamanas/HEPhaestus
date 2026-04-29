#!/usr/bin/env bash
# check_gfortran.sh — Check for gfortran AND record its version + absolute
# binary path for later compiler-coherence checks. Adapted from
# spheno-install/scripts/check_gfortran.sh.
#
# Unlike the spheno version, this script *also* exports:
#   HEPPH_LOOPTOOLS_GFORTRAN_VERSION   full first line of `gfortran --version`
#   HEPPH_LOOPTOOLS_GFORTRAN_PATH      absolute path to the binary picked
#
# so that install.sh can persist those into config.
#
# Respects FC env var as an override (lets macOS/Homebrew users with multiple
# gfortran installs pin a specific one, e.g. FC=/opt/homebrew/bin/gfortran-13).
#
# Exit 0 if gfortran found; exit $EXIT_NO_GFORTRAN (25) if absent.
# (Note: uses LOOPTOOLS-local exit code 25 instead of shared 10 — matches the
#  LOOPTOOLS blocker code table in SKILL.md.)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared helpers (4 levels up from this skill's scripts/).
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Source blocker helper.
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="check_gfortran_lt"

# Local exit code for gfortran absence (matches blocker table in SKILL.md).
EXIT_GFORTRAN_LT=25

check_gfortran_present() {
  local fc_bin=""

  # Respect FC if user has pinned it; otherwise use command -v gfortran.
  if [ -n "${FC:-}" ]; then
    if [ -x "$FC" ]; then
      fc_bin="$FC"
    elif command -v "$FC" >/dev/null 2>&1; then
      fc_bin="$(command -v "$FC")"
    fi
  fi

  if [ -z "$fc_bin" ] && command -v gfortran >/dev/null 2>&1; then
    fc_bin="$(command -v gfortran)"
  fi

  if [ -z "$fc_bin" ] || [ ! -x "$fc_bin" ]; then
    local user_instruction
    case "$(os_name)" in
      macos)
        user_instruction="Install gfortran with Homebrew: brew install gcc"
        ;;
      linux)
        user_instruction="Install gfortran with: sudo apt-get install -y gfortran  (Debian/Ubuntu) or sudo yum install -y gcc-gfortran  (RHEL/CentOS)"
        ;;
      *)
        user_instruction="Install a Fortran compiler (gfortran) for your OS before retrying."
        ;;
    esac

    emit_blocker "GFORTRAN_ABSENT" "fatal" \
      "gfortran is required to compile LoopTools but was not found on PATH (FC=${FC:-unset})." \
      "$user_instruction"
    exit "$EXIT_GFORTRAN_LT"
  fi

  # Capture first line of version output (the canonical "GNU Fortran ..." line).
  local version_line
  version_line="$("$fc_bin" --version 2>/dev/null | head -n1 || echo "")"
  if [ -z "$version_line" ]; then
    version_line="unknown"
  fi

  log "gfortran found: $fc_bin"
  log "gfortran version: $version_line"

  # Export for install.sh to pick up and persist.
  export HEPPH_LOOPTOOLS_GFORTRAN_PATH="$fc_bin"
  export HEPPH_LOOPTOOLS_GFORTRAN_VERSION="$version_line"

  return 0
}

check_cc_present() {
  # LoopTools needs a C compiler for the fcc wrapper and a few utilities.
  if command -v gcc >/dev/null 2>&1; then
    log "C compiler found: $(command -v gcc)"
    return 0
  fi
  if command -v clang >/dev/null 2>&1; then
    log "C compiler found: $(command -v clang)"
    return 0
  fi

  local user_instruction
  case "$(os_name)" in
    macos)
      user_instruction="Install Xcode Command Line Tools: xcode-select --install  (or: brew install gcc)"
      ;;
    linux)
      user_instruction="Install gcc: sudo apt-get install -y gcc  (Debian/Ubuntu) or sudo yum install -y gcc  (RHEL/CentOS)"
      ;;
    *)
      user_instruction="Install a C compiler (gcc or clang) for your OS before retrying."
      ;;
  esac

  emit_blocker "CC_ABSENT" "fatal" \
    "A C compiler (gcc or clang) is required to build LoopTools but none was found on PATH." \
    "$user_instruction"
  exit "$EXIT_GFORTRAN_LT"
}

# Run checks when executed directly (not sourced).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  check_gfortran_present
  check_cc_present
  printf '{"gfortran_path":"%s","gfortran_version":"%s"}\n' \
    "$HEPPH_LOOPTOOLS_GFORTRAN_PATH" "$HEPPH_LOOPTOOLS_GFORTRAN_VERSION"
fi
