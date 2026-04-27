#!/usr/bin/env bash
# build_project.sh — run `make main` inside a micrOMEGAs model project directory.
#
# Usage: build_project.sh <project_dir>
#
# Exit codes:
#   0  — success
#   2  — MICROMEGAS_PROJECT_BUILD_FAILED (blocker on stderr with make_log_tail)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

_LOG_TAG="micromegas-build"

EXIT_BUILD_FAILED=2

if [ $# -lt 1 ]; then
  err "Usage: build_project.sh <project_dir>"
  exit $EXIT_BUILD_FAILED
fi

project_dir="$1"

if [ ! -d "$project_dir" ]; then
  printf '{"code":"MICROMEGAS_PROJECT_BUILD_FAILED","mode":"fatal","message":"Project dir not found: %s"}\n' \
    "$project_dir" >&2
  exit $EXIT_BUILD_FAILED
fi

if [ ! -f "$project_dir/Makefile" ]; then
  printf '{"code":"MICROMEGAS_PROJECT_BUILD_FAILED","mode":"fatal","message":"No Makefile in project dir: %s"}\n' \
    "$project_dir" >&2
  exit $EXIT_BUILD_FAILED
fi

NCPUS="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)"
make_log="$project_dir/make.log"

log "Building micrOMEGAs project in $project_dir with make -j${NCPUS}..."
make_rc=0
make -C "$project_dir" main -j"$NCPUS" >"$make_log" 2>&1 || make_rc=$?

if [ $make_rc -ne 0 ]; then
  make_tail="$(python3 -c "
import sys
sys.path.insert(0, '$(dirname "$SCRIPT_DIR")/scripts')
try:
    from _make_log_parse import make_log_tail_json_safe
    with open('$make_log') as f:
        print(make_log_tail_json_safe(f.read(), 40))
except Exception as e:
    print(str(e))
" 2>/dev/null || tail -40 "$make_log" | tr '\n' '|' | sed 's/"/\\"/g')"

  printf '{"code":"MICROMEGAS_PROJECT_BUILD_FAILED","mode":"fatal","message":"make main failed (exit %d)","context":{"make_log_tail":"%s"}}\n' \
    "$make_rc" "$make_tail" >&2
  exit $EXIT_BUILD_FAILED
fi

log "Project built successfully: $project_dir"
echo "$project_dir/main"
exit 0
