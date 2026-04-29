#!/usr/bin/env bash
# probe_looptools.sh — smoke test for a LoopTools install prefix.
#
# Usage:
#   probe_looptools.sh <prefix>                 # light mode: file presence only
#   probe_looptools.sh --full-smoke <prefix>    # full mode: compile + run b0_test.F
#
# Light mode checks (exit 0 all pass, exit 15 on any failure):
#   - $prefix/lib/libooptools.a       (Fortran library, required)
#   - $prefix/bin/lt                  (CLI, required)
#   - $prefix/include/looptools.h     (Fortran header, required)
#   - $prefix/include/clooptools.h    (C/C++ header, required)
#
# Full mode additionally:
#   - Compiles scripts/b0_test.F against $prefix (needs gfortran)
#   - Runs the binary and parses stdout for "B0_SMOKE -4.4059328 2.7041431"
#   - Tolerates floating-point differences to 4 decimal places
#
# Prints a single-line JSON result to stdout on success:
#   {"status":"ok","mode":"light"|"full","prefix":"..."}
# Emits LOOPTOOLS_SMOKE_TEST_FAILED blocker to stderr + exits 15 on failure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="probe_looptools"

# Local exit code (matches SKILL.md blocker table).
EXIT_SMOKE_LT=15

light_probe() {
  local prefix="$1"
  local missing=()

  [ -f "$prefix/lib/libooptools.a" ] || missing+=("lib/libooptools.a")
  [ -x "$prefix/bin/lt" ]            || missing+=("bin/lt")
  [ -r "$prefix/include/looptools.h" ]  || missing+=("include/looptools.h")
  [ -r "$prefix/include/clooptools.h" ] || missing+=("include/clooptools.h")

  if [ ${#missing[@]} -gt 0 ]; then
    local joined
    joined="$(IFS=', '; echo "${missing[*]}")"
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "LoopTools prefix $prefix failed light smoke test; missing: $joined" \
      "Verify the prefix points to a completed 'make install' tree (not the source root)."
    exit "$EXIT_SMOKE_LT"
  fi

  log "Light smoke OK for $prefix."
}

full_probe() {
  local prefix="$1"

  # Need gfortran to build the B0 test.
  if ! command -v gfortran >/dev/null 2>&1 && [ -z "${FC:-}" ]; then
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "Full smoke test requires gfortran but none was found on PATH." \
      "Install gfortran or use light mode: probe_looptools.sh <prefix>"
    exit "$EXIT_SMOKE_LT"
  fi
  local fc="${FC:-gfortran}"

  local src="$SCRIPT_DIR/b0_test.F"
  if [ ! -f "$src" ]; then
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "b0_test.F test program not found at $src."
    exit "$EXIT_SMOKE_LT"
  fi

  local tmpdir
  tmpdir="$(mktemp -d -t looptools-smoke-XXXXXX)"
  trap 'rm -rf "$tmpdir"' RETURN

  local bin="$tmpdir/b0_test"
  local buildlog="$tmpdir/build.log"

  log "Compiling B0 smoke test against $prefix ..."
  if ! "$fc" -I"$prefix/include" "$src" -L"$prefix/lib" -looptools -o "$bin" \
       >"$buildlog" 2>&1; then
    local tail_txt
    tail_txt="$(tail -n 20 "$buildlog" 2>/dev/null || echo "")"
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "Failed to compile b0_test.F against LoopTools prefix $prefix. Build log tail: $tail_txt" \
      "Check that lib/libooptools.a was built with the same gfortran you are using now ($fc)."
    exit "$EXIT_SMOKE_LT"
  fi

  log "Running B0 smoke test ..."
  local out
  if ! out="$("$bin" 2>&1)"; then
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "B0 smoke binary ran but exited non-zero. Output: $out"
    exit "$EXIT_SMOKE_LT"
  fi

  # Expected values from LT 2.16 manual p. 26: (-4.40593283, 2.7041431)
  # Match to 4 decimal places: -4.4059 and 2.7041.
  local parsed
  parsed="$(printf '%s' "$out" | python3 - <<'PY' || echo "FAIL"
import sys, re
data = sys.stdin.read()
m = re.search(r'B0_SMOKE\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)', data)
if not m:
    print("FAIL")
    sys.exit(0)
re_part = float(m.group(1))
im_part = float(m.group(2))
# Tolerate 4 decimal places -> abs error < 5e-5.
ok_re = abs(re_part - (-4.40593283)) < 5e-4
ok_im = abs(im_part - ( 2.7041431 )) < 5e-4
print(f"OK re={re_part} im={im_part}" if (ok_re and ok_im) else f"FAIL re={re_part} im={im_part}")
PY
)"

  case "$parsed" in
    OK*)
      log "Full smoke OK: $parsed"
      ;;
    *)
      emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
        "B0 smoke test produced unexpected output. Parsed: $parsed. Raw: $out" \
        "Expected B0(1000,50,80) ≈ (-4.40593283, 2.7041431). Check LoopTools build integrity."
      exit "$EXIT_SMOKE_LT"
      ;;
  esac
}

main() {
  local mode="light"
  local prefix=""

  case "${1:-}" in
    --full-smoke) mode="full"; prefix="${2:-}" ;;
    "") echo "Usage: probe_looptools.sh [--full-smoke] <prefix>" >&2; exit 2 ;;
    *) prefix="$1" ;;
  esac

  [ -n "$prefix" ] || { echo "Usage: probe_looptools.sh [--full-smoke] <prefix>" >&2; exit 2; }
  prefix="${prefix/#\~/$HOME}"

  if [ ! -d "$prefix" ]; then
    emit_blocker "LOOPTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "Prefix $prefix is not a directory."
    exit "$EXIT_SMOKE_LT"
  fi

  light_probe "$prefix"
  if [ "$mode" = "full" ]; then
    full_probe "$prefix"
  fi

  printf '{"status":"ok","mode":"%s","prefix":"%s"}\n' "$mode" "$prefix"
}

main "$@"
