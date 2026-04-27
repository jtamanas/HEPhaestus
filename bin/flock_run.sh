#!/usr/bin/env bash
# bin/flock_run.sh — portable Python-fcntl.flock file-lock runner.
#
# Usage:
#   bin/flock_run.sh [--fd <N>] <lock_file> <timeout_sec> -- <cmd> [args...]
#
# Exit codes:
#   0          Lock acquired; wrapped command exited 0 (process replaced by exec).
#   1-123,     Wrapped command's exit code, transparently propagated.
#   125-127
#   124        Lock acquisition timed out (matches GNU timeout(1); differs from
#              flock(1)'s exit-1-on-timeout). Emits FLOCK_TIMEOUT JSON to stderr.
#   125        Helper internal error before exec: bad args (FLOCK_USAGE),
#              mkdir -p failed (FLOCK_LOCKDIR_DENIED), --fd N not open
#              (FLOCK_FD_INVALID), python3 missing (FLOCK_PYTHON_MISSING).
#
# Lock-file convention (path-form):
#   Helper runs mkdir -p on the lock file's parent dir; touch creates the file.
#   Lock survives exec: the flock is on an open file description; exec replaces
#   the bash process but the fd is inherited by the wrapped command.
#
# Fd-form (--fd N):
#   Caller has already opened fd N (e.g. exec 200>"$lock_file"). Helper acquires
#   flock on fd N and exec-s the wrapped command. Caller must NOT close fd N
#   before calling this helper. mkdir -p is NOT called in fd-form.
#
# NFS caveat: fcntl.flock on NFS is advisory-only on many kernel/NFS versions;
#   lock semantics may not hold cross-host. For single-machine use, behavior is
#   correct on both macOS (10.15+) and Linux.
#
# SCOPE.md line 38 override: SCOPE.md calls for fcntl.lockf (POSIX record locks,
#   fcntl F_SETLK). We use fcntl.flock (the flock(2) syscall) instead.
#   Rationale documented in bin/README.md. Helper does NOT read HEPPH_STATE_ROOT;
#   caller resolves the lock path; helper accepts an arbitrary path.
#
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── argument parsing ───────────────────────────────────────────────────────────

fd_mode=0
fd_num=9
lock_file=""
timeout_sec=""

_usage() {
  printf '{"code":"FLOCK_USAGE","mode":"fatal","message":"flock_run.sh: %s","context":{}}\n' "$1" >&2
  exit 125
}

if [ $# -lt 4 ]; then
  _usage "too few arguments: bin/flock_run.sh [--fd N] <lock_file> <timeout_sec> -- <cmd> [args...]"
fi

# Optional --fd N
if [ "${1:-}" = "--fd" ]; then
  shift
  fd_num="${1:-}"
  [ -n "$fd_num" ] || _usage "--fd requires an argument"
  shift
  fd_mode=1
fi

lock_file="${1:-}"
[ -n "$lock_file" ] || _usage "<lock_file> is required"
shift

timeout_sec="${1:-}"
[ -n "$timeout_sec" ] || _usage "<timeout_sec> is required"
# Validate: must be a non-negative integer
case "$timeout_sec" in
  ''|*[!0-9]*) _usage "<timeout_sec> must be a non-negative integer, got: $timeout_sec" ;;
esac
shift

# Expect the -- separator
if [ "${1:-}" != "--" ]; then
  _usage "expected '--' separator before command, got: ${1:-}"
fi
shift

if [ $# -lt 1 ]; then
  _usage "no command specified after '--'"
fi

# ── check python3 ──────────────────────────────────────────────────────────────

if ! command -v python3 >/dev/null 2>&1; then
  printf '{"code":"FLOCK_PYTHON_MISSING","mode":"fatal","message":"flock_run.sh: python3 not on PATH","context":{}}\n' >&2
  exit 125
fi

# ── path-form: prepare the lock file ──────────────────────────────────────────

if [ "$fd_mode" -eq 0 ]; then
  lock_dir="$(dirname "$lock_file")"
  if ! mkdir -p "$lock_dir" 2>/dev/null; then
    _errno="$?"
    printf '{"code":"FLOCK_LOCKDIR_DENIED","mode":"fatal","message":"flock_run.sh: cannot create lock dir","context":{"lock_dir":"%s","errno":"%s"}}\n' \
      "$lock_dir" "$_errno" >&2
    exit 125
  fi
  touch "$lock_file"
  # Open lock file on fd 9 in append mode to avoid truncation races.
  exec 9>>"$lock_file"
  fd_num=9
fi

# ── fd-form: validate the fd is open ──────────────────────────────────────────

if [ "$fd_mode" -eq 1 ]; then
  # Try to probe the fd — use /dev/fd/N if available, otherwise test with a read probe.
  fd_valid=0
  if [ -e "/dev/fd/$fd_num" ] 2>/dev/null; then
    fd_valid=1
  else
    # Fallback probe: use read with timeout; if fd is not open this will fail
    if { : <&"$fd_num"; } 2>/dev/null || { : >&"$fd_num"; } 2>/dev/null; then
      fd_valid=1
    fi
  fi
  if [ "$fd_valid" -eq 0 ]; then
    printf '{"code":"FLOCK_FD_INVALID","mode":"fatal","message":"flock_run.sh: fd %s not open","context":{"fd":%s}}\n' \
      "$fd_num" "$fd_num" >&2
    exit 125
  fi
fi

# ── acquire the flock via Python heredoc ──────────────────────────────────────
# Mirror the pattern from bin/config_write_locked.sh:57 for set-e safety.

rc=0
python3 - "$fd_num" "$timeout_sec" <<'PY' || rc=$?
import fcntl, sys, time

fd_num  = int(sys.argv[1])
timeout = int(sys.argv[2])
deadline = time.monotonic() + timeout

while True:
    try:
        fcntl.flock(fd_num, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sys.exit(0)
    except BlockingIOError:
        if time.monotonic() >= deadline:
            sys.exit(99)
        time.sleep(0.05)
    except Exception:
        sys.exit(98)
PY

# ── interpret Python exit code ─────────────────────────────────────────────────

if [ "$rc" -eq 99 ]; then
  printf '{"code":"FLOCK_TIMEOUT","mode":"fatal","message":"flock_run.sh: lock timeout","context":{"lock_file":"%s","timeout_sec":%s}}\n' \
    "$lock_file" "$timeout_sec" >&2
  exit 124
fi

if [ "$rc" -ne 0 ]; then
  printf '{"code":"FLOCK_PYTHON_MISSING","mode":"fatal","message":"flock_run.sh: python3 flock acquisition failed (exit %s)","context":{}}\n' \
    "$rc" >&2
  exit 125
fi

# Lock acquired — exec the wrapped command.
# Lock follows the open file description through exec to the wrapped process.
exec "$@"
