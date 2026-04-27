#!/usr/bin/env bash
# check_gfortran.sh — Check for gfortran; emit GFORTRAN_ABSENT fatal blocker if absent.
# Exit 0 if gfortran found; exit $EXIT_NO_GFORTRAN (10) if absent.
#
# Sourced or called directly by install_spheno.sh.
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

_LOG_TAG="check_gfortran"

check_gfortran_present() {
  if command -v gfortran >/dev/null 2>&1; then
    log "gfortran found: $(command -v gfortran)"
    return 0
  fi

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
    "gfortran is required to compile SPheno but was not found on PATH." \
    "$user_instruction"
  exit "$EXIT_NO_GFORTRAN"
}

# Run check when executed directly (not sourced).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  check_gfortran_present
fi
