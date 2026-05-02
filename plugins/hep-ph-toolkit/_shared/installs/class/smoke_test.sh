#!/usr/bin/env bash
# smoke_test.sh — run CLASS Planck18 default-precision background and assert c.age().
#
# Usage: smoke_test.sh <class_src_dir>
#
# Asserts c.age() within 0.5% of 13.797 Gyr (reference recorded on Ubuntu 22.04
# with system gcc; see INSTALL.md §macOS notes for fixture provenance).
#
# Exit 0 = smoke passed.
# Exit $EXIT_SMOKE (15) = assertion failed.
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../../shared/install-helpers/_common.sh"
if [ ! -f "$COMMON" ]; then
  COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
fi
. "$COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="class-smoke"

CLASS_SRC="${1:-}"

if [ -z "$CLASS_SRC" ]; then
  err "Usage: smoke_test.sh <class_src_dir>"
  exit 1
fi

CONFIG_PYTHON="$(config_get python 2>/dev/null || true)"
PYTHON_BIN="${CONFIG_PYTHON:-python3}"

log "Running CLASS smoke test: classy c.age() assertion"
log "Python: $PYTHON_BIN"

# Run with a 60-second timeout
SMOKE_RC=0
with_timeout 60 "$PYTHON_BIN" - <<'PY' || SMOKE_RC=$?
import sys, math

try:
    from classy import Class
except ImportError as e:
    print(f"CLASSY_IMPORT_FAILED: {e}", file=sys.stderr)
    sys.exit(15)

# Planck18 default-precision LCDM
c = Class()
c.set({
    'output': 'tCl,mPk',
    'l_max_scalars': 2000,
    'P_k_max_1/Mpc': 3.0,
    'H0': 67.32,
    'Omega_b': 0.02238,
    'Omega_cdm': 0.1201,
    'A_s': 2.100e-9,
    'n_s': 0.9660,
    'tau_reio': 0.0543,
})
c.compute()

age_gyr = c.age()
c.struct_cleanup()
c.empty()

# Reference: 13.797 Gyr (Planck 2018, Table 2; reproduced on Ubuntu 22.04 LTS
# with system gcc + CLASS v3.3.4 at 60-s default precision).
# Tolerance: 0.5% (6x tighter than compiler-induced drift).
REFERENCE_AGE = 13.797
TOLERANCE = 0.005  # 0.5%

rel_err = abs(age_gyr - REFERENCE_AGE) / REFERENCE_AGE
if rel_err > TOLERANCE:
    print(
        f"CLASS_SMOKE_FAILED: c.age()={age_gyr:.6f} deviates from reference "
        f"{REFERENCE_AGE} by {rel_err*100:.3f}% (tolerance {TOLERANCE*100:.1f}%)",
        file=sys.stderr,
    )
    sys.exit(15)

print(f"[class-smoke] c.age()={age_gyr:.6f} Gyr — within {TOLERANCE*100:.1f}% of {REFERENCE_AGE} PASS")
sys.exit(0)
PY

if [ $SMOKE_RC -eq 124 ]; then
  emit_blocker "CLASS_SMOKE_FAILED" "fatal" \
    "Smoke test timed out after 60 s" \
    "Check CLASS build and classy installation. Try: $PYTHON_BIN -c 'from classy import Class; c=Class(); c.set({\"output\":\"\"}); c.compute()'"
  exit "$EXIT_SMOKE"
fi

if [ $SMOKE_RC -ne 0 ]; then
  emit_blocker "CLASS_SMOKE_FAILED" "fatal" \
    "Smoke test failed (exit $SMOKE_RC)" \
    "Check classy installation: $PYTHON_BIN -c 'from classy import Class'"
  exit "$EXIT_SMOKE"
fi

log "Smoke test passed."
exit 0
