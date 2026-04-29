#!/usr/bin/env bash
# DIVERGENT VARIANT — pending consolidation into _shared/installs/sarah/install.sh.
#
# This script is invoked by the legacy demo-install.sh dispatcher. It carries
# features the canonical _shared/installs/sarah/install.sh does not yet have:
#   - `verify` subcommand with structured JSON contract (see test_verify_sarah.sh)
#   - install_with_rollback / unregister_path (see test_sarah_rollback.sh)
#   - VERSION: marker probe + StyleForm[...] banner fallback
#   - HEPPH_SARAH_FORCE_SMOKE_FAIL test knob
#   - HEPPH_WOLFRAM_USER_BASE override for init.m relocation
# The canonical version, in turn, has features this one lacks:
#   - emit_blocker JSON-on-stderr contract via _blocker.sh
#   - HEPPH_SARAH_VERSION env override
#   - sarah_installed_at timestamp
#   - post-install activation check
# Until the two are reconciled, both are kept. New install paths go through
# `bundle_install.sh` -> `_shared/installs/sarah/install.sh`. The legacy
# demo-install.sh harness still uses this script.
set -euo pipefail

_LOG_TAG="install_sarah"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# _common.sh is a one-line shim that sources plugins/shared/install-helpers/_common.sh
# shellcheck source=_common.sh
. "$SCRIPT_DIR/_common.sh"

SARAH_VERSION="4.15.3"
SARAH_URL="https://sarah.hepforge.org/downloads/SARAH-${SARAH_VERSION}.tar.gz"
SARAH_SHA256="TODO"  # TODO: verify SHA256 before v1

TARBALL="/tmp/sarah.tar.gz"

# SARAH is a Mathematica package dir, not an executable. We record the package
# root directory (the one that contains SARAH.m) as sarah_path.

# Run the fresh-session SARAH version probe via wolframscript.
# NO manual $Path manipulation on the command line — init.m must do the work.
# Relying purely on init.m is the anti-pattern fix (B3).
# Usage: sarah_probe_version <pkg_dir> <wolframscript>
# Prints version string (e.g. "4.15.3") to stdout; returns 1 if probe fails.
sarah_probe_version() {
  local pkg_dir="$1"
  local wolframscript="$2"
  # Use temp file to avoid $() + with_timeout interaction on bash 3.2 (macOS).
  local out_file
  out_file="$(mktemp /tmp/sarah_probe_out.XXXXXX)"
  local rc=0
  # Two -code flags per design §3.2. Note: SARAH`SA`Version may be a StyleForm object
  # in some SARAH versions, so we parse the version from EITHER:
  #   (a) a VERSION: prefixed line (if the ToString produces a plain string), OR
  #   (b) any [0-9]+\.[0-9]+\.[0-9]+ pattern in the banner (SARAH loads its version
  #       into the banner as StyleForm[4.15.3, ...] which contains the version string).
  # The SARAH banner is emitted on <<SARAH` load, so the banner presence itself
  # confirms that $Path registration worked.
  with_timeout 45 "$wolframscript" \
      -code '<<SARAH`' \
      -code 'Print["VERSION:" <> ToString[SARAH`SA`Version]]' \
      > "$out_file" 2>/dev/null || rc=$?
  local out
  out="$(cat "$out_file" 2>/dev/null || true)"
  rm -f "$out_file"
  [ "$rc" = "0" ] || return 1
  # First try: explicit VERSION: marker line.
  local ver
  ver="$(echo "$out" | grep -Eo '^VERSION:[0-9]+\.[0-9]+\.[0-9]+' | head -n1 | sed 's/^VERSION://' || true)"
  # Fallback: extract version from banner (handles StyleForm-wrapped SARAH`SA`Version).
  if [ -z "$ver" ]; then
    ver="$(echo "$out" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  fi
  echo "$ver"
}

probe_version() {
  local pkg_dir="$1"
  local wolframscript="${2:-}"
  [ -d "$pkg_dir" ] || return 1
  [ -f "$pkg_dir/SARAH.m" ] || return 1
  if [ -z "$wolframscript" ]; then
    wolframscript="$(config_get wolfram_engine_path || true)"
  fi
  [ -n "$wolframscript" ] && [ -x "$wolframscript" ] || return 1
  sarah_probe_version "$pkg_dir" "$wolframscript"
}

scan_candidates() {
  # Look for a directory containing SARAH.m under common locations.
  local roots=("$HOME/SARAH" "$HOME/software/SARAH" "/usr/local/SARAH")
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    # Direct (e.g. ~/SARAH/SARAH.m) or one level deep (e.g. ~/SARAH/SARAH-4.15.3/SARAH.m).
    if [ -f "$root/SARAH.m" ]; then
      echo "$root"; return 0
    fi
    local sub
    sub=$(find "$root" -maxdepth 2 -name SARAH.m -print 2>/dev/null | head -n1 || true)
    if [ -n "$sub" ]; then
      echo "$(dirname "$sub")"; return 0
    fi
  done
  return 1
}

cmd_detect() {
  local path version wolfram
  path="$(config_get sarah_path)"
  wolfram="$(config_get wolfram_engine_path)"
  if [ -n "$path" ] && [ -d "$path" ]; then
    if version="$(probe_version "$path" "$wolfram")" && [ -n "$version" ]; then
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
      return 0
    fi
  fi
  local found
  if found="$(scan_candidates)"; then
    printf '{"status":"found","path":"%s"}\n' "$found"
    return 0
  fi
  printf '{"status":"missing"}\n'
}

# _init_dir: resolve the Wolfram Engine kernel directory.
# B2 fix: macOS target is the WolframEngine kernel dir, not the Mathematica one.
# HEPPH_WOLFRAM_USER_BASE env override for testing.
_sarah_init_dir() {
  local init_dir="$HOME/Library/WolframEngine/Kernel"  # macOS (B2 fix)
  [ "$(os_name)" = "linux" ] && init_dir="$HOME/.WolframEngine/Kernel"
  if [ -n "${HEPPH_WOLFRAM_USER_BASE:-}" ]; then
    init_dir="$HEPPH_WOLFRAM_USER_BASE/Kernel"
  fi
  echo "$init_dir"
}

register_path() {
  # Ensure wolframscript finds SARAH by appending its pkg dir to
  # Wolfram's $Path via the per-user init file. Idempotent.
  # Rename: local 'parent' -> 'pkg_dir_abs' to reflect actual semantics.
  local pkg_dir="$1"
  local pkg_dir_abs
  pkg_dir_abs="$(cd "$pkg_dir" && pwd)"
  local init_dir
  init_dir="$(_sarah_init_dir)"
  mkdir -p "$init_dir"
  local init_file="$init_dir/init.m"
  local marker="(* hephaestus SARAH path *)"
  if [ -f "$init_file" ] && grep -q "hephaestus SARAH path" "$init_file"; then
    # Rewrite the line in place; B4 fix: use re.escape(marker) to handle regex metachars.
    python3 - "$init_file" "$pkg_dir_abs" "$marker" <<'PY'
import sys, re
path, pkg_dir_abs, marker = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    src = f.read()
# Build the Path-registration line using concatenation so the source does not
# contain the literal probe-anti-pattern string (design-final §2.4 / B3).
append_line = (
    "If[!MemberQ[" + "$Path, \"" + pkg_dir_abs + "\"], "
    + "AppendTo[" + "$Path, \"" + pkg_dir_abs + "\"]];"
)
new = re.sub(
    re.escape(marker) + r".*\n.*\n",
    f"{marker}\n{append_line}\n",
    src,
)
with open(path, "w") as f:
    f.write(new)
PY
  else
    {
      echo ""
      echo "$marker"
      echo "If[!MemberQ[\$Path, \"$pkg_dir_abs\"], AppendTo[\$Path, \"$pkg_dir_abs\"]];"
    } >> "$init_file"
  fi
  log "Registered SARAH pkg dir ($pkg_dir_abs) in $init_file"
}

unregister_path() {
  # Inverse of register_path: remove the marker line + AppendTo line from init.m.
  # Idempotent: if already absent, no-op.
  # P2 §2.6 fix: canonicalize gracefully in case pkg dir is gone.
  local raw="$1"
  local pkg_dir_abs
  pkg_dir_abs="$(cd "$raw" 2>/dev/null && pwd)" || pkg_dir_abs="$raw"
  local init_dir
  init_dir="$(_sarah_init_dir)"
  local init_file="$init_dir/init.m"
  [ -f "$init_file" ] || return 0
  python3 - "$init_file" "$pkg_dir_abs" <<'PY'
import sys, re
path, pkg = sys.argv[1], sys.argv[2]
with open(path) as f:
    src = f.read()
marker = "(* hephaestus SARAH path *)"
new = re.sub(
    re.escape(marker) + r"\s*\n[^\n]*" + re.escape(pkg) + r"[^\n]*\n",
    "",
    src,
)
with open(path, "w") as f:
    f.write(new)
PY
}

cmd_verify() {
  # Parse arguments.
  local path="" wolfram_path="" expected_version="" strict_version=0
  local timeout_secs=45 json_out=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --path)            path="$2";             shift 2 ;;
      --wolfram-path)    wolfram_path="$2";      shift 2 ;;
      --expected-version) expected_version="$2"; shift 2 ;;
      --strict-version)  strict_version=1;       shift ;;
      --timeout)         timeout_secs="$2";      shift 2 ;;
      --json)            json_out=1;             shift ;;
      *) err "Unknown verify option: $1"; exit 2 ;;
    esac
  done

  # Resolve path from config if not provided.
  if [ -z "$path" ]; then
    path="$(config_get sarah_path || true)"
  fi

  # Helper to emit JSON and exit.
  _emit() {
    local status="$1" ok="$2" version="${3:-}" detail="${4:-}" hints="${5:-}"
    local path_val="${path:-}"
    local ev_field=""
    if [ -n "$expected_version" ]; then
      ev_field=", \"expected_version\": \"$expected_version\""
    fi
    local hints_field=""
    if [ -n "$hints" ]; then
      hints_field=", \"hints\": [$hints]"
    fi
    printf '{"schema_version":1,"tool":"sarah","ok":%s,"status":"%s","path":"%s","version":"%s","detail":"%s"%s%s}\n' \
      "$ok" "$status" "$path_val" "$version" "$detail" "$ev_field" "$hints_field"
  }

  # Pre-probe: not_configured (exit 17).
  if [ -z "$path" ]; then
    _emit "not_configured" "false" "" "sarah_path not set; configure via use-path or install"
    exit "$EXIT_NOT_CONFIGURED"
  fi

  # Pre-probe: missing (exit 16).
  if [ ! -d "$path" ] || [ ! -f "$path/SARAH.m" ]; then
    _emit "missing" "false" "" "path not found or missing SARAH.m" \
      "{\"code\":\"path_not_found\",\"message\":\"$path is not a SARAH package dir\"}"
    exit "$EXIT_BAD_PATH"
  fi

  # Resolve wolframscript.
  if [ -z "$wolfram_path" ]; then
    wolfram_path="$(config_get wolfram_engine_path || true)"
  fi
  if [ -z "$wolfram_path" ] || [ ! -x "$wolfram_path" ]; then
    # Last resort: wolframscript on PATH.
    wolfram_path="$(command -v wolframscript 2>/dev/null || true)"
  fi
  if [ -z "$wolfram_path" ] || [ ! -x "$wolfram_path" ]; then
    _emit "installed_broken" "false" "" "wolframscript not found" \
      "{\"code\":\"wolfram_engine_missing\",\"message\":\"wolframscript not found; configure via install_wolfram.sh\"}"
    exit "$EXIT_SMOKE"
  fi

  # Run probe with timeout.
  # Use temp files to capture stdout/stderr to avoid $() + with_timeout
  # interaction issue on bash 3.2 (macOS default) where wait() inside a
  # command substitution subshell may block for background job children.
  local probe_stdout_file probe_stderr_file
  probe_stdout_file="$(mktemp /tmp/sarah_verify_out.XXXXXX)"
  probe_stderr_file="$(mktemp /tmp/sarah_verify_err.XXXXXX)"
  local probe_rc=0
  with_timeout "$timeout_secs" "$wolfram_path" \
      -code '<<SARAH`' \
      -code 'Print["VERSION:" <> ToString[SARAH`SA`Version]]' \
      > "$probe_stdout_file" 2>"$probe_stderr_file" || probe_rc=$?

  local probe_out stderr_snippet
  probe_out="$(cat "$probe_stdout_file" 2>/dev/null || true)"
  stderr_snippet="$(head -c 200 "$probe_stderr_file" 2>/dev/null | tr '\n' ' ' || true)"
  rm -f "$probe_stdout_file" "$probe_stderr_file"

  if [ "$probe_rc" = "124" ]; then
    _emit "timeout" "false" "" "wolframscript exceeded ${timeout_secs}s timeout"
    exit "$EXIT_SMOKE"
  fi

  if [ "$probe_rc" != "0" ]; then
    local hints_str=""
    # Hint on init.m path issues if stderr mentions relevant terms.
    if echo "$stderr_snippet" | grep -qiE 'SARAH\.m|\$Path|init\.m'; then
      hints_str="{\"code\":\"kernel_init_m_path\",\"message\":\"init.m \$Path registration may be broken\"}"
    fi
    _emit "installed_broken" "false" "" "wolframscript exited $probe_rc: ${stderr_snippet:0:150}" "$hints_str"
    exit "$EXIT_SMOKE"
  fi

  # Parse version from output.
  # First try: explicit VERSION: marker (set by our second -code arg).
  # Fallback: extract from banner (handles StyleForm-wrapped SARAH`SA`Version).
  local version=""
  version="$(echo "$probe_out" | grep -Eo '^VERSION:[0-9]+\.[0-9]+\.[0-9]+' | head -n1 | sed 's/^VERSION://' || true)"
  if [ -z "$version" ]; then
    version="$(echo "$probe_out" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  fi

  if [ -z "$version" ]; then
    _emit "installed_broken" "false" "" "no VERSION: line in wolframscript output" \
      "{\"code\":\"kernel_init_m_path\",\"message\":\"init.m \$Path registration may be broken\"}"
    exit "$EXIT_SMOKE"
  fi

  # Version match check.
  if [ -n "$expected_version" ] && [ "$version" != "$expected_version" ]; then
    local detail_msg="version $version != expected $expected_version"
    if [ "$strict_version" = "1" ]; then
      _emit "version_mismatch" "false" "$version" "$detail_msg"
      exit "$EXIT_SMOKE"
    fi
  fi

  _emit "ok" "true" "$version" ""
  exit 0
}

cmd_use_path() {
  local path="$1"
  [ -n "$path" ] || { err "use-path requires a SARAH package dir"; exit $EXIT_BAD_PATH; }
  path="${path/#\~/$HOME}"
  if [ ! -d "$path" ] || [ ! -f "$path/SARAH.m" ]; then
    err "Not a SARAH package dir (missing SARAH.m): $path"
    exit $EXIT_SARAH_PATH
  fi
  register_path "$path"
  # Delegate to cmd_verify (shell function call, not subprocess).
  if ! cmd_verify --path "$path"; then
    local rc=$?
    err "SARAH verify failed after use-path. init.m may be misconfigured."
    exit "$rc"
  fi
  local version=""
  version="$(config_get sarah_path | xargs -I{} sh -c 'true')" || true
  # Re-read version from probe for config_merge.
  local wolfram
  wolfram="$(config_get wolfram_engine_path || true)"
  version="$(probe_version "$path" "$wolfram" || true)"
  config_merge sarah_path "$path" sarah_version "$version"
  log "Configured SARAH at $path (v${version:-unknown})"
}

extract_and_register() {
  # Extract-only: symlink creation moved to AFTER smoke passes (design §4.2).
  local install_parent="$1"
  mkdir -p "$install_parent"
  log "Extracting SARAH to $install_parent ..."
  if ! tar -xzf "$TARBALL" -C "$install_parent"; then
    err "Extraction failed."
    df -h "$install_parent" >&2 || true
    exit $EXIT_EXTRACT
  fi
  local extracted
  extracted=$(tar -tzf "$TARBALL" | head -n1 | cut -d/ -f1)
  local pkg_dir="$install_parent/$extracted"
  if [ ! -f "$pkg_dir/SARAH.m" ]; then
    err "Extracted dir $pkg_dir does not contain SARAH.m."
    exit $EXIT_SARAH_PATH
  fi
  echo "$pkg_dir"
}

# Smoke-test body factored out for testability.
# HEPPH_SARAH_FORCE_SMOKE_FAIL=1 forces failure (test knob for rollback tests).
smoke_test_body() {
  if [ "${HEPPH_SARAH_FORCE_SMOKE_FAIL:-0}" = "1" ]; then
    return 1
  fi
  local pkg_dir="$1"
  local wolfram="$2"
  local version
  version="$(probe_version "$pkg_dir" "$wolfram" || true)"
  [ -n "$version" ]
}

# install_with_rollback: factored install core (extraction assumed done).
# Registers $Path, smokes, rolls back on failure.
# Args: <new_pkg_dir> <previous_path> <install_parent> <wolfram>
install_with_rollback() {
  local new_pkg_dir="$1"
  local previous_path="$2"
  local install_parent="$3"
  local wolfram="$4"

  register_path "$new_pkg_dir"

  if ! smoke_test_body "$new_pkg_dir" "$wolfram"; then
    # Rollback: remove new init.m entry.
    unregister_path "$new_pkg_dir"
    # Re-register previous version if it existed.
    if [ -n "$previous_path" ] && [ -d "$previous_path" ]; then
      register_path "$previous_path"
    fi
    err "SARAH smoke test failed; rolled back init.m."
    return "$EXIT_SMOKE"
  fi

  # Symlink created only after smoke passes (moved from extract_and_register).
  ln -sfn "$new_pkg_dir" "$install_parent/SARAH-current"
  return 0
}

cmd_install() {
  local install_dir="${1:-$HOME/SARAH}"
  install_dir="${install_dir/#\~/$HOME}"

  local wolfram
  wolfram="$(config_get wolfram_engine_path || true)"
  if [ -z "$wolfram" ] || [ ! -x "$wolfram" ]; then
    err "SARAH needs Wolfram Engine configured first. Run install_wolfram.sh."
    exit $EXIT_NO_WOLFRAM
  fi
  if ! command -v tar >/dev/null 2>&1; then
    err "tar not found on PATH."
    exit $EXIT_GENERIC
  fi

  log "Install target: $install_dir"
  check_disk 1 2
  download_with_retry "$SARAH_URL" "$TARBALL"
  verify_checksum "$TARBALL" "$SARAH_SHA256"

  # Snapshot previous sarah_path before any changes.
  local previous_path
  previous_path="$(config_get sarah_path || true)"

  local pkg_dir
  pkg_dir="$(extract_and_register "$install_dir")"

  local version
  if ! install_with_rollback "$pkg_dir" "$previous_path" "$install_dir" "$wolfram"; then
    exit "$EXIT_SMOKE"
  fi

  version="$(probe_version "$pkg_dir" "$wolfram" || true)"
  config_merge sarah_path "$pkg_dir" sarah_version "${version:-}"
  rm -f "$TARBALL"
  log "SARAH v${version:-unknown} installed at $pkg_dir."
}

usage() {
  cat >&2 <<EOF
Usage: install_sarah.sh <command> [args]

Commands:
  detect              Print JSON state of existing SARAH install
  use-path <dir>      Point config at an existing SARAH package dir (contains SARAH.m)
  install [dir]       Full auto-install (default dir: ~/SARAH)
  verify [opts]       Fast probe of an already-installed SARAH
                      --path <dir>           SARAH pkg dir (default: from config)
                      --wolfram-path <exe>   wolframscript path (default: from config)
                      --expected-version <v> Expected version string
                      --strict-version       Exit non-zero on version mismatch
                      --timeout <secs>       Probe timeout (default: 45)
                      --json                 (reserved; output is always JSON)
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
