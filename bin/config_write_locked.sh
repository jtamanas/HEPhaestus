#!/usr/bin/env bash
# bin/config_write_locked.sh — wave-mutex wrapper for config.json writes.
# Refactored ws3-iter1: delegates locking to bin/flock_run.sh.
#
# Usage:
#   bin/config_write_locked.sh key1 val1 [key2 val2 ...]
#
# Lock file: ${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus/.config.lock
#   NOTE: this lock retains the XDG_CONFIG_HOME convention (NOT $HEPPH_STATE_ROOT).
#   WS3 does not migrate this path; the config-lock has its own historical home.
# Timeout:   30 s per attempt; retry once (60 s total max), zero-sleep between.
# Exit 0:    config written successfully under lock.
# Exit 1:    lock acquisition failed after both attempts, or config_merge failed.
#
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SHARED_COMMON="$REPO_ROOT/plugins/shared/install-helpers/_common.sh"
[ -f "$SHARED_COMMON" ] || { printf '[config_write_locked] ERROR: _common.sh not found at %s\n' "$SHARED_COMMON" >&2; exit 1; }
# shellcheck source=../plugins/shared/install-helpers/_common.sh
. "$SHARED_COMMON"

_LOG_TAG="config-write-locked"
CONFIG_LOCK_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus/.config.lock"
LOCK_TIMEOUT=30

mkdir -p "$(dirname "$CONFIG_LOCK_FILE")"
touch "$CONFIG_LOCK_FILE"

if [ $# -lt 2 ]; then
  printf '[config_write_locked] Usage: %s key1 val1 [key2 val2 ...]\n' "$0" >&2
  exit 1
fi

# Defeat nested fcntl.flock in config_merge's inner Python (see _common.sh:190).
export HEPPH_CONFIG_LOCK_HELD=1
# Export SHARED_COMMON so the child bash invocation can source _common.sh
# (bash 3.2 on macOS does not support export -f, so we re-source in child).
export SHARED_COMMON

STDERR_BUF="$(mktemp)"
cleanup() { rm -f "$STDERR_BUF"; }
trap cleanup EXIT

# Attempt 1: capture helper stderr so we can discard FLOCK_TIMEOUT JSON on retry
# (decision #13 — exactly one JSON blocker per timeout, not two).
rc=0
"$REPO_ROOT/bin/flock_run.sh" "$CONFIG_LOCK_FILE" "$LOCK_TIMEOUT" -- \
  bash -c '. "$SHARED_COMMON"; config_merge "$@"' _ "$@" 2>"$STDERR_BUF" || rc=$?

if [ "$rc" -eq 124 ]; then
  warn "Lock timeout on attempt 1; retrying once..."
  # Attempt 2: stderr passes through directly (first-attempt JSON discarded).
  rc=0
  "$REPO_ROOT/bin/flock_run.sh" "$CONFIG_LOCK_FILE" "$LOCK_TIMEOUT" -- \
    bash -c '. "$SHARED_COMMON"; config_merge "$@"' _ "$@" || rc=$?
  if [ "$rc" -eq 124 ]; then
    printf '{"code":"CONFIG_LOCK_TIMEOUT","mode":"fatal","message":"config_write_locked.sh: lock timeout after 2 attempts","context":{"lock_file":"%s"}}\n' \
      "$CONFIG_LOCK_FILE" >&2
    exit 1
  fi
fi

if [ "$rc" -ne 0 ]; then
  # Surface captured attempt-1 stderr so unexpected errors are visible.
  cat "$STDERR_BUF" >&2 || true
  err "config_merge exited with code $rc"
  exit "$rc"
fi

log "config_merge completed under fcntl.flock (lock: $CONFIG_LOCK_FILE)"
exit 0
