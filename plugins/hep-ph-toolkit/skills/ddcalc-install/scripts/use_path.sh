#!/usr/bin/env bash
# Register an existing DDCalc installation directory.
# Usage: ./use_path.sh <dir>
# Stdout (success): {"status":"configured","path":"...","version":"..."}
# Exits non-zero on any fatal condition (blocker JSON on stderr).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$SHARED_COMMON"

_tag="ddcalc-use-path"

DIR="${1:-}"
if [ -z "$DIR" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_PATH_INVALID "No path provided." '{}' >&2
  exit "$EXIT_BAD_PATH"
fi

# Resolve to absolute path
DIR="$(cd "$DIR" 2>/dev/null && pwd)" || {
  "$SCRIPT_DIR/_blocker.sh" DDCALC_PATH_INVALID \
    "Directory does not exist: $1" "{\"given\":\"$1\"}" >&2
  exit "$EXIT_BAD_PATH"
}

# Check for libDDCalc.a
if [ ! -f "$DIR/lib/libDDCalc.a" ] && [ ! -f "$DIR/libDDCalc.a" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_PATH_INVALID \
    "libDDCalc.a not found in $DIR/lib/ or $DIR/" \
    "{\"path\":\"$DIR\"}" >&2
  exit "$EXIT_BAD_PATH"
fi

# Probe version string from the DDCalc binary/test if present
ddcalc_version="2.2.0"
if [ -x "$DIR/DDCalc_test" ]; then
  detected="$("$DIR/DDCalc_test" 2>/dev/null | grep -Eo 'DDCalc[[:space:]]+v?([0-9]+\.[0-9]+\.[0-9]+)' | head -1 | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' || true)"
  [ -n "$detected" ] && ddcalc_version="$detected"
fi

config_merge \
  ddcalc_path "$DIR" \
  ddcalc_version "$ddcalc_version" \
  ddcalc_installed_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

printf '{"status":"configured","path":"%s","version":"%s"}\n' \
  "$DIR" "$ddcalc_version"
