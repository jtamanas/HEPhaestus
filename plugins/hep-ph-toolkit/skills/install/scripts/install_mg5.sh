#!/usr/bin/env bash
set -euo pipefail

_LOG_TAG="install_mg5"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# _common.sh is a one-line shim that sources plugins/shared/install-helpers/_common.sh
# shellcheck source=_common.sh
. "$SCRIPT_DIR/_common.sh"

MG5_VERSION="3.5.6"
MG5_VERSIONED_DIR="MG5_aMC_v3_5_6"
MG5_URL="https://launchpad.net/mg5amcnlo/3.0/3.5.x/+download/MG5_aMC_v3.5.6.tar.gz"
MG5_SHA256="TODO"  # TODO: verify SHA256 before v1

TARBALL="/tmp/mg5.tar.gz"
SMOKE_DIR="/tmp/mg5_smoke"

check_gfortran() {
  if ! command -v gfortran >/dev/null 2>&1; then
    case "$(os_name)" in
      macos) err "gfortran not found. Install with: brew install gcc" ;;
      linux) err "gfortran not found. Install with: sudo apt install gfortran  (or: sudo dnf install gcc-gfortran)" ;;
      *)     err "gfortran not found. Install a Fortran compiler for your OS." ;;
    esac
    exit $EXIT_NO_GFORTRAN
  fi
  log "gfortran: $(gfortran -dumpfullversion -dumpversion 2>/dev/null | head -n1 || gfortran -v 2>&1 | head -n1)"
}

# mg5_probe_version — two-tier version probe; B6 fix.
# Tier 1 (required): parse version from --help banner.
# Tier 2 (enrichment only): read <root>/VERSION if path is <root>/bin/mg5_aMC.
# B6 rationale: --version was removed in MG5 3.5.6; --help is stable across 3.5.x.
# Returns non-zero (and prints nothing) if both tiers fail.
mg5_probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1

  # Tier 1: banner from --help
  local tier1
  tier1=$(
    "$bin" --help 2>&1 | head -n 20 \
      | grep -Eo 'MadGraph5_aMC@NLO[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+' \
      | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' \
      | head -n1 || true
  )

  if [ -n "$tier1" ]; then
    echo "$tier1"
    return 0
  fi

  # Tier 2: filesystem VERSION file (enrichment; only when path layout allows)
  if [[ "$bin" == */bin/mg5_aMC ]]; then
    local root
    root="$(dirname "$(dirname "$bin")")"
    if [ -f "$root/VERSION" ]; then
      local tier2
      tier2=$(head -n1 "$root/VERSION" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)
      if [ -n "$tier2" ]; then
        echo "$tier2"
        return 0
      fi
    fi
  fi

  return 1
}

# probe_version — thin wrapper for backwards compat with cmd_detect, cmd_use_path, cmd_install.
probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  mg5_probe_version "$bin"
}

scan_candidates() {
  local candidates=(
    "$HOME/MG5_aMC/bin/mg5_aMC"
    "$HOME/software/MG5_aMC/bin/mg5_aMC"
    "/usr/local/bin/mg5_aMC"
  )
  local which_hit
  which_hit="$(command -v mg5_aMC || true)"
  [ -n "$which_hit" ] && candidates+=("$which_hit")
  for c in "${candidates[@]}"; do
    if [ -x "$c" ]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

cmd_detect() {
  local path version
  path="$(config_get madgraph_path)"
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

cmd_use_path() {
  local path="$1"
  [ -n "$path" ] || { err "use-path requires a path"; exit $EXIT_BAD_PATH; }
  if [ ! -x "$path" ]; then
    err "Not executable: $path"
    exit $EXIT_BAD_PATH
  fi
  local version
  if ! version="$(probe_version "$path")"; then
    err "Could not determine version for: $path"
    exit $EXIT_BAD_PATH
  fi
  config_merge madgraph_path "$path" madgraph_version "$version"
  log "Configured MG5 at $path (v$version)"
}

extract_and_link() {
  local install_parent="$1"
  local target="$install_parent/$MG5_VERSIONED_DIR"
  local link="$install_parent/MG5_aMC"
  mkdir -p "$install_parent"
  log "Extracting to $install_parent ..."
  if ! tar -xzf "$TARBALL" -C "$install_parent"; then
    err "Extraction failed. Disk state:"
    df -h "$install_parent" >&2 || true
    rm -rf "$target"
    exit $EXIT_EXTRACT
  fi
  local extracted
  extracted=$(tar -tzf "$TARBALL" | head -n1 | cut -d/ -f1)
  if [ "$extracted" != "$MG5_VERSIONED_DIR" ] && [ -d "$install_parent/$extracted" ]; then
    mv "$install_parent/$extracted" "$target"
  fi
  ln -sfn "$target" "$link"
  log "Linked $link -> $target"
  echo "$link/bin/mg5_aMC"
}

smoke_test() {
  local bin="$1"
  log "Smoke test: e+ e- > mu+ mu- ..."
  rm -rf "$SMOKE_DIR"
  local out
  if ! out=$(printf 'generate e+ e- > mu+ mu-\noutput %s\nexit\n' "$SMOKE_DIR" | "$bin" 2>&1); then
    err "MG5 exited non-zero during smoke test."
    printf '%s\n' "$out" | tail -n 30 >&2
    if printf '%s' "$out" | grep -q 'gfortran: command not found'; then
      err "MG5 lost gfortran from PATH. Current PATH: $PATH"
      err "Re-run in a shell where 'gfortran' is on PATH (check ~/.zshrc, ~/.bashrc)."
    fi
    exit $EXIT_SMOKE
  fi
  if [ ! -d "$SMOKE_DIR/SubProcesses/P1_epem_mupmum" ]; then
    err "Smoke test did not produce expected SubProcess directory."
    printf '%s\n' "$out" | tail -n 30 >&2
    exit $EXIT_SMOKE
  fi
  rm -rf "$SMOKE_DIR"
  log "Smoke test passed."
}

cmd_install() {
  local install_dir="${1:-$HOME/MG5_aMC}"
  install_dir="${install_dir/#\~/$HOME}"
  local install_parent
  install_parent="$(dirname "$install_dir")"

  log "Install target: $install_dir (parent: $install_parent)"
  check_gfortran
  check_disk 2 4
  download_with_retry "$MG5_URL" "$TARBALL"
  verify_checksum "$TARBALL" "$MG5_SHA256"
  local bin
  bin="$(extract_and_link "$install_parent")"
  smoke_test "$bin"
  local version
  version="$(probe_version "$bin" || echo "$MG5_VERSION")"
  config_merge madgraph_path "$bin" madgraph_version "$version"
  rm -f "$TARBALL"
  log "MadGraph5_aMC@NLO v$version installed at $install_dir."
  log "Config written to $CONFIG_FILE."
}

# cmd_verify — verify an existing MG5 installation.
# Design-final §3.4 + §2 (contract). B6 fix: uses --help banner, not --version.
cmd_verify() {
  # Install EXIT trap per design-final §2.6: clean up child processes on unexpected exit.
  # _verify_clean=1 is set just before normal exits so the trap is a no-op on clean paths.
  local _verify_clean=0
  trap '[ "$_verify_clean" = "0" ] && kill -TERM 0 2>/dev/null || true' EXIT

  local path="" expected_version="" strict_version=0 timeout=10

  # Parse argv
  while [ $# -gt 0 ]; do
    case "$1" in
      --path)              path="$2";             shift 2 ;;
      --expected-version)  expected_version="$2"; shift 2 ;;
      --strict-version)    strict_version=1;      shift ;;
      --timeout)           timeout="$2";          shift 2 ;;
      --json)              shift ;;           # default; accept for symmetry
      --wolfram-path)      shift 2 ;;         # silently ignored for mg5
      *) err "Unknown option: $1"; exit 32 ;;
    esac
  done

  # Fall back to config if --path not supplied
  if [ -z "$path" ]; then
    path="$(config_get madgraph_path)"
  fi

  local t_start
  # Portable millisecond timestamp: use python3 if available, else fall back to seconds.
  _ms_now() {
    python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || \
      awk 'BEGIN{srand(); print int(systime()*1000)}' 2>/dev/null || \
      echo "0"
  }
  t_start="$(_ms_now)"

  # Helper: emit JSON and exit
  _emit_json() {
    local status="$1" ok="$2" version="${3:-}" detail="${4:-}" hints="${5:-}"
    local t_end duration_ms
    t_end="$(_ms_now)"
    duration_ms=$(( t_end - t_start ))
    local ev_field=""
    [ -n "$expected_version" ] && ev_field=",\"expected_version\":\"$expected_version\""
    local hints_field=""
    [ -n "$hints" ] && hints_field=",\"hints\":[$hints]"
    printf '{"schema_version":1,"tool":"mg5","ok":%s,"status":"%s","path":"%s","version":"%s","detail":"%s"%s%s,"duration_ms":%d}\n' \
      "$ok" "$status" "$path" "$version" "$detail" "$ev_field" "$hints_field" "$duration_ms"
  }

  # Pre-probe: not_configured
  if [ -z "$path" ]; then
    _emit_json "not_configured" "false" "" "No --path supplied and madgraph_path not in config"
    _verify_clean=1; exit $EXIT_NOT_CONFIGURED
  fi

  # Pre-probe: missing / not executable
  if [ ! -x "$path" ]; then
    _emit_json "missing" "false" "" "Not executable: $path" \
      '{"code":"path_not_found","message":"Path does not exist or is not executable"}'
    _verify_clean=1; exit $EXIT_BAD_PATH
  fi

  # Probe: run --help with timeout
  local probe_rc=0
  local probe_tmp
  probe_tmp="$(mktemp)"
  with_timeout "$timeout" bash -c '"$1" --help >"$2" 2>&1' _ "$path" "$probe_tmp" || probe_rc=$?

  if [ "$probe_rc" = "124" ]; then
    rm -f "$probe_tmp"
    _emit_json "timeout" "false" "" "--help exceeded ${timeout}s timeout"
    _verify_clean=1; exit $EXIT_SMOKE
  fi

  local probe_out
  probe_out="$(cat "$probe_tmp")"
  rm -f "$probe_tmp"

  if [ "$probe_rc" -ne 0 ]; then
    local detail_esc
    detail_esc="$(printf '%s' "$probe_out" | head -n3 | tr '\n' ' ' | cut -c1-180)"
    _emit_json "installed_broken" "false" "" "--help exited $probe_rc: $detail_esc"
    _verify_clean=1; exit $EXIT_SMOKE
  fi

  # Extract version via mg5_probe_version (tier-1: banner, tier-2: VERSION file).
  # MG5 3.5.6 dropped the version string from --help, so tier-2 is now the live
  # path. Routing through mg5_probe_version keeps both tiers in one place.
  local version="" detail=""
  version="$(mg5_probe_version "$path" || true)"

  if [ -z "$version" ]; then
    _emit_json "installed_broken" "false" "" \
      "Could not extract version from --help banner or VERSION file" \
      '{"code":"mg5_version_probe_stale","message":"Banner format may have changed; update mg5_probe_version regex"}'
    _verify_clean=1; exit $EXIT_SMOKE
  fi

  # Note when the banner was silent and the VERSION file was the source.
  case "$path" in
    */bin/mg5_aMC)
      local root
      root="$(dirname "$(dirname "$path")")"
      local banner_ver
      banner_ver="$(printf '%s' "$probe_out" \
        | grep -Eo 'MadGraph5_aMC@NLO[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+' \
        | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
      if [ -z "$banner_ver" ]; then
        detail="version from VERSION file (--help banner has no version string)"
      elif [ "$banner_ver" != "$version" ]; then
        detail="VERSION file disagrees: $version on disk, $banner_ver in banner"
        warn "$detail"
      fi
      ;;
  esac

  # Optional: version mismatch check
  if [ -n "$expected_version" ] && [ "$version" != "$expected_version" ]; then
    if [ "$strict_version" = "1" ]; then
      _emit_json "version_mismatch" "false" "$version" \
        "version $version on disk, expected $expected_version"
      _verify_clean=1; exit $EXIT_SMOKE
    else
      if [ -z "$detail" ]; then
        detail="version $version on disk, expected $expected_version"
      else
        detail="$detail; expected $expected_version"
      fi
      warn "Version drift: $detail"
    fi
  fi

  _emit_json "ok" "true" "$version" "$detail"
  _verify_clean=1; exit 0
}

usage() {
  cat >&2 <<EOF
Usage: install_mg5.sh <command> [args]

Commands:
  detect                 Print JSON state of existing MG5 install
  use-path <path>        Point config at an existing mg5_aMC binary
  install [dir]          Full auto-install (default dir: ~/MG5_aMC)
  verify [--path <p>] [--expected-version <v>] [--strict-version]
         [--timeout <s>]  Verify an existing MG5 installation
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
