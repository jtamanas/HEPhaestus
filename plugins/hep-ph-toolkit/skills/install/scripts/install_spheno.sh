#!/usr/bin/env bash
# DIVERGENT VARIANT — pending consolidation into _shared/installs/spheno/install.sh.
#
# This script is invoked by the legacy demo-install.sh dispatcher. It carries
# features the canonical _shared/installs/spheno/install.sh does not yet have:
#   - `verify` subcommand with structured JSON contract (see test_verify_spheno.sh)
#   - spheno_probe_banner with dylib-vs-banner-vs-unknown classification under
#     a with_timeout guard
#   - HEPPH_F90_COMPILER override on compile path
# The canonical version, in turn, has features this one lacks:
#   - emit_blocker JSON-on-stderr contract via _blocker.sh
#   - HEPPH_SPHENO_VERSION env override
#   - spheno_src_path tracking + version-mismatch policy
# Until the two are reconciled, both are kept. New install paths go through
# `bundle_install.sh` -> `_shared/installs/spheno/install.sh`. The legacy
# demo-install.sh harness still uses this script.
set -euo pipefail

_LOG_TAG="install_spheno"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# _common.sh is a one-line shim that sources plugins/shared/install-helpers/_common.sh
# shellcheck source=_common.sh
. "$SCRIPT_DIR/_common.sh"

SPHENO_VERSION="4.0.5"
SPHENO_URL="https://spheno.hepforge.org/downloads/SPheno-${SPHENO_VERSION}.tar.gz"
SPHENO_SHA256="TODO"  # TODO: verify SHA256 before v1

TARBALL="/tmp/spheno.tar.gz"

# SPheno's version isn't exposed cleanly via a flag. Parse the Makefile /
# source dir name where possible; fall back to the pinned version string.
probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  local dir
  dir="$(cd "$(dirname "$bin")/.." && pwd)"
  # The source dir is named e.g. SPheno-4.0.5; extract the version if so.
  local base
  base="$(basename "$dir")"
  local v
  v="$(printf '%s' "$base" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  # Fallback: run binary with no args and grep the banner.
  v="$("$bin" 2>&1 | grep -Eo 'SPheno[[:space:]]v?[0-9]+\.[0-9]+\.[0-9]+' | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  return 1
}

# spheno_probe_banner <bin> [<timeout_seconds>]
#
# Runs the SPheno binary with no args under with_timeout, captures
# combined stdout+stderr (up to 200 lines), and returns a two-line
# status block to stdout:
#
#   CODE:<DYLIB|BANNER|UNKNOWN>
#   VERSION:<x.y.z or empty>
#
# Priority-1 (dylib load failures): case-insensitive match on
#   "image not found", "Symbol not found", "cannot open shared object"
# Priority-2 (banner present): case-insensitive match on
#   "usage", "input file", "leshouches"
# Else: UNKNOWN.
#
# Version extraction (when BANNER): tries SPheno v<N>.<N>.<N> in output,
# then falls back to directory-name of the binary parent.
spheno_probe_banner() {
  local bin="$1"
  local timeout_s="${2:-20}"
  local combined
  combined="$(with_timeout "$timeout_s" "$bin" 2>&1 | head -n 200 || true)"
  # Priority-1: dylib / shared-library load failures.
  if printf '%s' "$combined" | grep -qiE '(image not found|Symbol not found|cannot open shared object)'; then
    printf 'CODE:DYLIB\nVERSION:\n'
    return 0
  fi
  # Priority-2: banner present (usage/input file/leshouches).
  if printf '%s' "$combined" | grep -qiE '(usage|input file|leshouches)'; then
    local v
    v="$(printf '%s' "$combined" | grep -Eo 'SPheno[[:space:]]v?[0-9]+\.[0-9]+\.[0-9]+' | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
    if [ -z "$v" ]; then
      local dir base
      dir="$(cd "$(dirname "$bin")/.." && pwd 2>/dev/null || true)"
      base="$(basename "$dir")"
      v="$(printf '%s' "$base" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
    fi
    printf 'CODE:BANNER\nVERSION:%s\n' "$v"
    return 0
  fi
  # Else: unknown output.
  printf 'CODE:UNKNOWN\nVERSION:\n'
  return 0
}

smoke_test() {
  local bin="$1"
  local out
  out="$(with_timeout 20 "$bin" 2>&1 | head -n 200 || true)"
  # Check for dylib failures first — surface a useful error message.
  if printf '%s' "$out" | grep -qiE '(image not found|Symbol not found|cannot open shared object)'; then
    err "SPheno smoke test: dylib load failure. Try 'otool -L $bin' (macOS) or 'ldd $bin' (linux)."
    exit $EXIT_SMOKE
  fi
  # SPheno with no args prints a usage banner to stderr/stdout.
  if printf '%s' "$out" | grep -qiE '(usage|input file|LesHouches)'; then
    log "SPheno smoke test passed."
    return 0
  fi
  err "SPheno smoke test failed. Output:"
  printf '%s\n' "$out" | tail -n 30 >&2
  exit $EXIT_SMOKE
}

scan_candidates() {
  local roots=("$HOME/SPheno" "$HOME/software/SPheno" "/usr/local/SPheno")
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    if [ -x "$root/bin/SPheno" ]; then echo "$root/bin/SPheno"; return 0; fi
    local hit
    hit=$(find "$root" -maxdepth 3 -type f -name SPheno -perm -u+x 2>/dev/null | head -n1 || true)
    [ -n "$hit" ] && { echo "$hit"; return 0; }
  done
  local which_hit
  which_hit="$(command -v SPheno || true)"
  [ -n "$which_hit" ] && { echo "$which_hit"; return 0; }
  return 1
}

cmd_detect() {
  local path version
  path="$(config_get spheno_path)"
  if [ -n "$path" ] && version="$(probe_version "$path")"; then
    printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
    return 0
  fi
  local found
  if found="$(scan_candidates)"; then
    printf '{"status":"found","path":"%s"}\n' "$found"
    return 0
  fi
  printf '{"status":"missing"}\n'
}

# cmd_verify [--path <bin>] [--timeout <seconds>] [--expected-version <v>]
#
# Emits one line of JSON to stdout conforming to design-final §2 schema.
# Exit codes: 0=ok, 15=installed_broken or timeout, 16=missing, 17=not_configured.
cmd_verify() {
  local path="" timeout_s=20 expected_version=""
  # Parse args.
  while [ $# -gt 0 ]; do
    case "$1" in
      --path)             path="$2";             shift 2 ;;
      --timeout)          timeout_s="$2";        shift 2 ;;
      --expected-version) expected_version="$2"; shift 2 ;;
      --json)             shift ;;
      *) err "cmd_verify: unknown arg $1"; exit 2 ;;
    esac
  done

  # Resolve path: arg > config.
  if [ -z "$path" ]; then
    path="$(config_get spheno_path)"
  fi

  # No path anywhere → not_configured / 17.
  if [ -z "$path" ]; then
    local ev_field=""
    [ -n "$expected_version" ] && ev_field=", \"expected_version\": \"$expected_version\""
    printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "not_configured", "path": "", "version": "", "detail": "no path supplied and no config entry found", "hints": []%s}\n' "$ev_field"
    exit $EXIT_NOT_CONFIGURED
  fi

  # Path not executable → missing / 16.
  if [ ! -x "$path" ]; then
    local ev_field=""
    [ -n "$expected_version" ] && ev_field=", \"expected_version\": \"$expected_version\""
    printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "missing", "path": "%s", "version": "", "detail": "path not found or not executable", "hints": [{"code": "path_not_found", "message": "Check that the SPheno binary exists at the configured path."}]%s}\n' "$path" "$ev_field"
    exit $EXIT_BAD_PATH
  fi

  # Probe the binary.
  # Capture output to a tmp file so we can also capture with_timeout's exit code.
  # A pipe (... | head -n 200) loses the left-hand exit code in bash.
  local probe_out probe_out_file probe_rc
  probe_out_file="$(mktemp)"
  probe_rc=0
  ( with_timeout "$timeout_s" "$path" >"$probe_out_file" 2>&1 ) || probe_rc=$?
  probe_out="$(head -n 200 "$probe_out_file" 2>/dev/null || true)"
  rm -f "$probe_out_file"

  # with_timeout returns 124 on timeout.
  if [ "$probe_rc" -eq 124 ]; then
    local ev_field=""
    [ -n "$expected_version" ] && ev_field=", \"expected_version\": \"$expected_version\""
    printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "timeout", "path": "%s", "version": "", "detail": "binary did not respond within %s seconds", "hints": []%s}\n' "$path" "$timeout_s" "$ev_field"
    exit $EXIT_SMOKE
  fi

  local ev_field=""
  [ -n "$expected_version" ] && ev_field=", \"expected_version\": \"$expected_version\""

  # Priority-1: dylib / shared-library load failures.
  if printf '%s' "$probe_out" | grep -qiE '(image not found|Symbol not found|cannot open shared object)'; then
    printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "installed_broken", "path": "%s", "version": "", "detail": "dylib/shared-library load failure detected", "hints": [{"code": "shared_library_missing", "message": "Try '"'"'otool -L %s'"'"' (macOS) or '"'"'ldd %s'"'"' (linux) to identify the missing library."}]%s}\n' "$path" "$path" "$path" "$ev_field"
    exit $EXIT_SMOKE
  fi

  # Priority-2: banner present.
  if printf '%s' "$probe_out" | grep -qiE '(usage|input file|leshouches)'; then
    local v
    v="$(printf '%s' "$probe_out" | grep -Eo 'SPheno[[:space:]]v?[0-9]+\.[0-9]+\.[0-9]+' | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
    if [ -z "$v" ]; then
      local dir base
      dir="$(cd "$(dirname "$path")/.." && pwd 2>/dev/null || true)"
      base="$(basename "$dir")"
      v="$(printf '%s' "$base" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
    fi
    local detail="banner found"
    [ -z "$v" ] && detail="banner found; version could not be extracted from output or directory name"
    # Check expected_version if supplied.
    if [ -n "$expected_version" ] && [ -n "$v" ] && [ "$v" != "$expected_version" ]; then
      printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "version_mismatch", "path": "%s", "version": "%s", "detail": "expected %s but found %s", "hints": []%s}\n' "$path" "$v" "$expected_version" "$v" "$ev_field"
      exit $EXIT_SMOKE
    fi
    printf '{"schema_version": 1, "tool": "spheno", "ok": true, "status": "ok", "path": "%s", "version": "%s", "detail": "%s", "hints": []%s}\n' "$path" "$v" "$detail" "$ev_field"
    exit 0
  fi

  # Else: unknown output → installed_broken.
  printf '{"schema_version": 1, "tool": "spheno", "ok": false, "status": "installed_broken", "path": "%s", "version": "", "detail": "binary ran but produced unrecognized output (not a SPheno banner)", "hints": []%s}\n' "$path" "$ev_field"
  exit $EXIT_SMOKE
}

cmd_use_path() {
  local path="$1"
  [ -n "$path" ] || { err "use-path requires a SPheno binary path"; exit $EXIT_BAD_PATH; }
  path="${path/#\~/$HOME}"
  if [ ! -x "$path" ]; then
    err "Not executable: $path"
    exit $EXIT_BAD_PATH
  fi
  smoke_test "$path"
  local version
  version="$(probe_version "$path" || echo "$SPHENO_VERSION")"
  config_merge spheno_path "$path" spheno_version "$version"
  log "Configured SPheno at $path (v$version)"
  # Final gate: verify confirms the binary is healthy after config_merge.
  cmd_verify --path "$path" >/dev/null
}

check_gfortran() {
  if ! command -v gfortran >/dev/null 2>&1; then
    case "$(os_name)" in
      macos) err "gfortran not found. Install with: brew install gcc" ;;
      linux) err "gfortran not found. Install with: sudo apt install gfortran" ;;
      *)     err "gfortran not found. Install a Fortran compiler for your OS." ;;
    esac
    exit $EXIT_NO_GFORTRAN
  fi
}

compile() {
  local src_dir="$1"
  log "Compiling SPheno in $src_dir (may take 5-10 minutes)..."
  local log_file="/tmp/spheno_make.log"
  # B5 fix: probe ifort for functionality, not just PATH-presence.
  # A broken Intel oneAPI shim may be on PATH but exit non-zero on --version.
  local make_args=""
  if ifort --version >/dev/null 2>&1; then
    :
  else
    make_args="F90=gfortran"
    log "ifort probe failed (not installed or non-functional); building with gfortran."
  fi
  # HEPPH_F90_COMPILER env override wins over auto-detection.
  if [ -n "${HEPPH_F90_COMPILER:-}" ]; then
    make_args="F90=$HEPPH_F90_COMPILER"
    log "HEPPH_F90_COMPILER set; using $HEPPH_F90_COMPILER"
  fi
  if ! ( cd "$src_dir" && make $make_args ) >"$log_file" 2>&1; then
    err "make failed. Last 40 lines of $log_file:"
    tail -n 40 "$log_file" >&2 || true
    if grep -qiE '(lapack|liblapack|-llapack)' "$log_file"; then
      case "$(os_name)" in
        macos) err "Missing LAPACK. Install with: brew install lapack" ;;
        linux) err "Missing LAPACK. Install with: sudo apt install liblapack-dev" ;;
      esac
      exit $EXIT_NO_LAPACK
    fi
    err "Full build log: $log_file"
    exit $EXIT_SPHENO_MAKE
  fi
  log "SPheno compiled successfully."
}

cmd_install() {
  local install_dir="${1:-$HOME/SPheno}"
  install_dir="${install_dir/#\~/$HOME}"

  log "Install target: $install_dir"
  check_gfortran
  check_disk 1 2
  mkdir -p "$install_dir"
  download_with_retry "$SPHENO_URL" "$TARBALL"
  verify_checksum "$TARBALL" "$SPHENO_SHA256"

  log "Extracting SPheno to $install_dir ..."
  if ! tar -xzf "$TARBALL" -C "$install_dir"; then
    err "Extraction failed."
    exit $EXIT_EXTRACT
  fi
  local extracted
  extracted=$(tar -tzf "$TARBALL" | head -n1 | cut -d/ -f1)
  local src_dir="$install_dir/$extracted"
  if [ ! -d "$src_dir" ]; then
    err "Expected source dir $src_dir not found after extraction."
    exit $EXIT_EXTRACT
  fi

  compile "$src_dir"

  local bin="$src_dir/bin/SPheno"
  if [ ! -x "$bin" ]; then
    err "Build finished but $bin is missing or not executable."
    exit $EXIT_SPHENO_MAKE
  fi
  smoke_test "$bin"
  local version
  version="$(probe_version "$bin" || echo "$SPHENO_VERSION")"
  config_merge spheno_path "$bin" spheno_version "$version"
  rm -f "$TARBALL"
  log "SPheno v$version installed at $bin."
  # Chain install → verify.
  cmd_verify --path "$bin" >/dev/null
}

usage() {
  cat >&2 <<EOF
Usage: install_spheno.sh <command> [args]

Commands:
  detect              Print JSON state of existing SPheno install
  use-path <path>     Point config at an existing SPheno binary
  install [dir]       Full auto-install (default parent dir: ~/SPheno)
  verify [opts]       Verify an installed SPheno binary; emit JSON to stdout
                        --path <bin>               path to SPheno binary
                        --timeout <s>              probe timeout in seconds (default: 20)
                        --expected-version <v>     fail if version != v
EOF
  exit 2
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    detect)   cmd_detect ;;
    use-path) cmd_use_path "${1:-}" ;;
    install)  cmd_install "${1:-}" ;;
    verify)   cmd_verify "$@" ;;
    *)        usage ;;
  esac
}

main "$@"
