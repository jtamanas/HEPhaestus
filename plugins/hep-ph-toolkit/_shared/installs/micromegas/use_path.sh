#!/usr/bin/env bash
# use_path.sh — configure micrOMEGAs from an existing installation directory.
#
# Usage: use_path.sh <dir> [--calchep-path <dir>]
#
# Exit codes:
#   0  — configured OK
#   16 — MICROMEGAS_PATH_INVALID (dir lacks sources/ or CalcHEP_src/)
#   30 — CALCHEP_PATH_INVALID (--calchep-path given but invalid)
#   32 — MICROMEGAS_SMOKE_TEST_FAILED
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="micromegas-use-path"

EXIT_CALCHEP_BAD=30
EXIT_MICROMEGAS_SMOKE=32

if [ $# -lt 1 ]; then
  err "Usage: use_path.sh <dir> [--calchep-path <dir>]"
  exit $EXIT_BAD_PATH
fi

micromegas_dir="$1"; shift

# Parse optional --calchep-path
calchep_path=""
while [ $# -gt 0 ]; do
  case "$1" in
    --calchep-path)
      calchep_path="$2"
      shift 2
      ;;
    *)
      err "Unknown argument: $1"
      exit $EXIT_BAD_PATH
      ;;
  esac
done

# ── Validate micromegas_dir ───────────────────────────────────────────────────
if [ ! -d "$micromegas_dir/sources" ]; then
  emit_blocker MICROMEGAS_PATH_INVALID fatal \
    "micrOMEGAs path '$micromegas_dir' lacks sources/ directory." \
    "Run /micromegas-install install to obtain a valid installation."
  exit $EXIT_BAD_PATH
fi

if [ -z "$calchep_path" ] && [ ! -d "$micromegas_dir/CalcHEP_src" ]; then
  emit_blocker MICROMEGAS_PATH_INVALID fatal \
    "micrOMEGAs path '$micromegas_dir' lacks CalcHEP_src/ directory (bundled CalcHEP required)." \
    "Provide --calchep-path if CalcHEP is installed separately."
  exit $EXIT_BAD_PATH
fi

# ── Validate calchep_path if provided ────────────────────────────────────────
if [ -n "$calchep_path" ]; then
  if [ ! -f "$calchep_path/getFlags" ]; then
    emit_blocker CALCHEP_PATH_INVALID fatal \
      "CalcHEP path '$calchep_path' lacks getFlags script." \
      "Provide the CalcHEP_src/ subdirectory of a valid CalcHEP installation."
    exit $EXIT_CALCHEP_BAD
  fi
  calchep_bin="${calchep_path%/CalcHEP_src}"
  if [ ! -f "$calchep_bin/bin/s_calchep" ] && [ ! -f "$calchep_path/../bin/s_calchep" ]; then
    emit_blocker CALCHEP_PATH_INVALID fatal \
      "CalcHEP path '$calchep_path': s_calchep binary not found." \
      "Ensure CalcHEP is fully compiled before using --calchep-path."
    exit $EXIT_CALCHEP_BAD
  fi
fi

# ── Determine resolved calchep_path ─────────────────────────────────────────
if [ -z "$calchep_path" ]; then
  effective_calchep="$micromegas_dir/CalcHEP_src"
  calchep_bundled="true"
else
  effective_calchep="$calchep_path"
  calchep_bundled="false"
fi

# ── Smoke test ───────────────────────────────────────────────────────────────
if [ -f "$SCRIPT_DIR/_smoke.sh" ]; then
  if ! bash "$SCRIPT_DIR/_smoke.sh" "$micromegas_dir"; then
    emit_blocker MICROMEGAS_SMOKE_TEST_FAILED fatal \
      "micrOMEGAs smoke test failed for path '$micromegas_dir'." \
      "Ensure micrOMEGAs is fully compiled (cd '$micromegas_dir' && make)."
    exit $EXIT_MICROMEGAS_SMOKE
  fi
else
  warn "Smoke test script not found; skipping smoke test."
fi

# ── Write config ─────────────────────────────────────────────────────────────
# Parse version
ver=""
if [ -f "$micromegas_dir/include/VERSION" ]; then
  ver="$(head -1 "$micromegas_dir/include/VERSION" | tr -d '[:space:]')"
fi

ts="$(python3 -c "import datetime; print(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")"

config_merge \
  micromegas_path "$micromegas_dir" \
  micromegas_version "${ver:-6.0.5}" \
  calchep_path "$effective_calchep" \
  calchep_bundled "$calchep_bundled" \
  micromegas_installed_at "$ts"

log "micrOMEGAs configured at $micromegas_dir (version: ${ver:-unknown})"
printf '{"status":"configured","path":"%s","version":"%s"}\n' \
  "$micromegas_dir" "${ver:-unknown}"
exit 0
