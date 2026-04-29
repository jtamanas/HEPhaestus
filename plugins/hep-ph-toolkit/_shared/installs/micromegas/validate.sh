#!/usr/bin/env bash
# validate.sh — re-validate the currently configured micrOMEGAs install.
#
# Usage: validate.sh
#
# Reads config.micromegas_path and re-runs the light smoke test
# (sources/micromegas.a, CalcHEP_src/bin/s_calchep, MSSM/main.c). Does NOT
# write to config on success — this subcommand is read-only with respect to
# config state.
#
# Emits MICROMEGAS_PATH_INVALID if:
#   - config.micromegas_path is not set
#   - the path no longer exists on disk
#   - the path is missing expected structural markers
#
# Emits MICROMEGAS_SMOKE_TEST_FAILED if the smoke test fails.
#
# Origin: migrated from the v0 monte-carlo-tools/micromegas-install skill into
# _shared/installs/micromegas as part of
# the consolidation with the v1 constraints skill. Complements `detect`
# (which emits {status:configured|found|missing}) by eagerly running the
# smoke test — useful for CI or post-install verification.
#
# Exit codes:
#   0  — validated OK (prints {"status":"configured",...})
#   16 — MICROMEGAS_PATH_INVALID
#   32 — MICROMEGAS_SMOKE_TEST_FAILED
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="micromegas-validate"

EXIT_MICROMEGAS_SMOKE=32

path="$(config_get micromegas_path 2>/dev/null || true)"
if [ -z "$path" ]; then
  emit_blocker MICROMEGAS_PATH_INVALID fatal \
    "No micromegas_path recorded in config." \
    "Run 'bash _shared/installs/micromegas/install.sh install' or 'bash _shared/installs/micromegas/install.sh use-path <dir>' first."
  exit $EXIT_BAD_PATH
fi

if [ ! -d "$path" ]; then
  emit_blocker MICROMEGAS_PATH_INVALID fatal \
    "Configured micromegas_path=$path does not exist on disk." \
    "Re-run 'bash _shared/installs/micromegas/install.sh install' to reinstall, or 'bash _shared/installs/micromegas/install.sh use-path <dir>' to point to a working tree."
  exit $EXIT_BAD_PATH
fi

# Structural markers check (always-present).
if [ ! -d "$path/sources" ] || [ ! -d "$path/CalcHEP_src" ]; then
  emit_blocker MICROMEGAS_PATH_INVALID fatal \
    "Configured micromegas_path=$path no longer contains required markers (sources/ and/or CalcHEP_src/)." \
    "Re-run 'bash _shared/installs/micromegas/install.sh install' or 'bash _shared/installs/micromegas/install.sh use-path <dir>' to point to a valid tree."
  exit $EXIT_BAD_PATH
fi

# Light smoke (compiles+runs MSSM/main.c stub; emits blocker on failure).
if ! bash "$SCRIPT_DIR/_smoke.sh" "$path"; then
  exit $EXIT_MICROMEGAS_SMOKE
fi

# Success — re-print the {configured,...} status without modifying config.
ver=""
if [ -f "$path/include/VERSION" ]; then
  ver="$(head -1 "$path/include/VERSION" | tr -d '[:space:]')"
fi
printf '{"status":"configured","path":"%s","version":"%s"}\n' \
  "$path" "${ver:-unknown}"
exit 0
