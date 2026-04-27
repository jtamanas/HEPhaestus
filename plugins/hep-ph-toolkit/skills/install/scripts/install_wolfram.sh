#!/usr/bin/env bash
set -euo pipefail

_LOG_TAG="install_wolfram"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# _common.sh is a one-line shim that sources plugins/shared/install-helpers/_common.sh
# shellcheck source=_common.sh
. "$SCRIPT_DIR/_common.sh"

WOLFRAM_VERSION="14.1"
WOLFRAM_URL="https://www.wolfram.com/engine/"  # landing page; tarball requires login

probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  # wolframscript --version prints e.g. "WolframScript 1.11.0 for MacOSX-ARM64, built: ..."
  # The kernel version is what callers actually care about.
  "$bin" -code 'Print[$Version]' 2>/dev/null \
    | grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1
}

scan_candidates() {
  local candidates=(
    "/Applications/Wolfram.app/Contents/MacOS/wolframscript"
    "/Applications/Wolfram Engine.app/Contents/MacOS/wolframscript"
    "/Applications/Mathematica.app/Contents/MacOS/wolframscript"
    "/usr/local/bin/wolframscript"
    "/opt/Wolfram/WolframEngine/Executables/wolframscript"
  )
  # Also scan numbered installs under /usr/local/Wolfram/.
  if [ -d /usr/local/Wolfram/WolframEngine ]; then
    while IFS= read -r -d '' p; do candidates+=("$p"); done < <(
      find /usr/local/Wolfram/WolframEngine -maxdepth 3 -name wolframscript -print0 2>/dev/null || true
    )
  fi
  local which_hit
  which_hit="$(command -v wolframscript || true)"
  [ -n "$which_hit" ] && candidates+=("$which_hit")
  for c in "${candidates[@]}"; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

cmd_detect() {
  local path version
  path="$(config_get wolfram_engine_path)"
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

cmd_verify() {
  local path="" expected_version="" strict_version=0 timeout=15
  # Parse arguments
  while [ $# -gt 0 ]; do
    case "$1" in
      --path)            path="$2";             shift 2 ;;
      --expected-version) expected_version="$2"; shift 2 ;;
      --strict-version)  strict_version=1;      shift ;;
      --timeout)         timeout="$2";          shift 2 ;;
      --json)                                   shift ;;   # no-op; always JSON
      --wolfram-path)                           shift 2 ;; # ignored for uniformity
      *) err "Unknown argument: $1"; exit $EXIT_GENERIC ;;
    esac
  done

  # Kill any lingering child processes when this script exits.
  # Only kills the process group when we are the group leader (i.e. invoked
  # as a top-level script, not as a sourced function in a test shell).
  local _my_pgid
  _my_pgid="$(ps -o pgid= -p $$ 2>/dev/null | tr -d ' ' || true)"
  if [ "$$" = "$_my_pgid" ]; then
    trap 'kill -TERM 0 2>/dev/null || true' EXIT
  fi

  local start_ms
  start_ms=$(python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || echo 0)

  # Pre-probe: resolve path from config if not supplied via --path
  if [ -z "$path" ]; then
    path="$(config_get wolfram_engine_path)"
  fi
  if [ -z "$path" ]; then
    local duration_ms=0
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"not_configured","path":"","version":"","detail":"No path supplied and wolfram_engine_path not set in config. Use install_wolfram.sh use-path <path>.","hints":[],"duration_ms":%d}\n' "$duration_ms"
    exit $EXIT_NOT_CONFIGURED
  fi

  # Check path exists and is executable
  if [ ! -x "$path" ]; then
    local end_ms duration_ms
    end_ms=$(python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || echo 0)
    duration_ms=$(( end_ms - start_ms ))
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"missing","path":"%s","version":"","detail":"Path not found or not executable: %s","hints":[{"code":"path_not_found","message":"The wolframscript binary does not exist or is not executable at the given path"}],"duration_ms":%d}\n' \
      "$path" "$path" "$duration_ms"
    exit $EXIT_BAD_PATH
  fi

  # Probe: run wolframscript with two Print calls
  local tmpfile
  tmpfile="$(mktemp)"
  local probe_rc=0
  with_timeout "$timeout" "$path" -code 'Print[2+2]; Print[$Version]' >"$tmpfile" 2>&1 || probe_rc=$?

  local end_ms duration_ms
  end_ms=$(python3 -c 'import time; print(int(time.time()*1000))' 2>/dev/null || echo 0)
  duration_ms=$(( end_ms - start_ms ))

  # Handle timeout
  if [ "$probe_rc" = "124" ]; then
    rm -f "$tmpfile"
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"timeout","path":"%s","version":"","detail":"wolframscript probe timed out after %d seconds","hints":[],"duration_ms":%d}\n' \
      "$path" "$timeout" "$duration_ms"
    exit $EXIT_SMOKE
  fi

  # Handle probe failure (non-zero exit)
  local probe_stdout
  probe_stdout="$(cat "$tmpfile")"
  rm -f "$tmpfile"

  if [ "$probe_rc" -ne 0 ]; then
    local hint_json="[]"
    local detail
    detail="$(printf '%s' "$probe_stdout" | head -c 150 | tr '\n' ' ')"
    if printf '%s' "$probe_stdout" | grep -qi 'activation\|activate\|license\|sign in'; then
      hint_json='[{"code":"wolfram_not_activated","message":"Wolfram Engine is not activated. Run: wolframscript --activate"}]'
    fi
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"installed_broken","path":"%s","version":"","detail":"wolframscript exit %d: %s","hints":%s,"duration_ms":%d}\n' \
      "$path" "$probe_rc" "$detail" "$hint_json" "$duration_ms"
    exit $EXIT_SMOKE
  fi

  # Parse stdout: first line should be "4", second line should contain version
  local line1 line2
  line1="$(printf '%s' "$probe_stdout" | head -n1 | tr -d '[:space:]')"
  line2="$(printf '%s' "$probe_stdout" | sed -n '2p')"

  # Check first line == 4
  if [ "$line1" != "4" ]; then
    local hint_json="[]"
    if printf '%s' "$probe_stdout" | grep -qi 'activation\|activate\|license\|sign in'; then
      hint_json='[{"code":"wolfram_not_activated","message":"Wolfram Engine is not activated. Run: wolframscript --activate"}]'
    fi
    local detail
    detail="$(printf '%s' "$probe_stdout" | head -c 150 | tr '\n' ' ')"
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"installed_broken","path":"%s","version":"","detail":"Expected Print[2+2] == 4, got: %s","hints":%s,"duration_ms":%d}\n' \
      "$path" "$detail" "$hint_json" "$duration_ms"
    exit $EXIT_SMOKE
  fi

  # Extract version from second line
  local version
  version="$(printf '%s' "$line2" | { grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' || true; } | head -n1)"
  if [ -z "$version" ]; then
    printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"installed_broken","path":"%s","version":"","detail":"Could not parse version from $Version output: %s","hints":[],"duration_ms":%d}\n' \
      "$path" "$line2" "$duration_ms"
    exit $EXIT_SMOKE
  fi

  # Handle expected_version comparison
  if [ -n "$expected_version" ]; then
    if [ "$version" != "$expected_version" ]; then
      if [ "$strict_version" = "1" ]; then
        printf '{"schema_version":1,"tool":"wolfram","ok":false,"status":"version_mismatch","path":"%s","version":"%s","expected_version":"%s","detail":"Version mismatch: found %s, expected %s (strict)","hints":[],"duration_ms":%d}\n' \
          "$path" "$version" "$expected_version" "$version" "$expected_version" "$duration_ms"
        exit $EXIT_SMOKE
      else
        # Non-strict: ok=true but detail notes drift
        printf '{"schema_version":1,"tool":"wolfram","ok":true,"status":"ok","path":"%s","version":"%s","expected_version":"%s","detail":"Version drift: found %s, expected %s (non-strict; continuing)","hints":[],"duration_ms":%d}\n' \
          "$path" "$version" "$expected_version" "$version" "$expected_version" "$duration_ms"
        exit 0
      fi
    else
      # Versions match
      printf '{"schema_version":1,"tool":"wolfram","ok":true,"status":"ok","path":"%s","version":"%s","expected_version":"%s","detail":"","hints":[],"duration_ms":%d}\n' \
        "$path" "$version" "$expected_version" "$duration_ms"
      exit 0
    fi
  fi

  # No expected_version: happy path
  printf '{"schema_version":1,"tool":"wolfram","ok":true,"status":"ok","path":"%s","version":"%s","detail":"","hints":[],"duration_ms":%d}\n' \
    "$path" "$version" "$duration_ms"
  exit 0
}

cmd_use_path() {
  local path="$1"
  [ -n "$path" ] || { err "use-path requires a path"; exit $EXIT_BAD_PATH; }
  if [ ! -x "$path" ]; then
    err "Not executable: $path"
    exit $EXIT_BAD_PATH
  fi
  # Run verify as the smoke; propagate non-zero exit
  local verify_out verify_rc=0
  verify_out="$(cmd_verify --path "$path")" || verify_rc=$?
  if [ "$verify_rc" -ne 0 ]; then
    # Print the verify JSON to stderr for debugging and exit with verify's code
    printf '%s\n' "$verify_out" >&2
    exit "$verify_rc"
  fi
  local version
  version="$(printf '%s' "$verify_out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version",""))' 2>/dev/null || true)"
  config_merge wolfram_engine_path "$path" wolfram_engine_version "$version"
  log "Configured Wolfram Engine at $path (v$version)"
}

cmd_install() {
  cat <<EOF
Wolfram Engine activation can't be automated — it needs a browser and a free
Wolfram ID.

If you're running /install via the Claude skill, it walks you through
the full flow interactively. See SKILL.md §"Wolfram walkthrough" for the
step-by-step guide if you'd prefer to do it by hand:

  1. Visit $WOLFRAM_URL and download the free Wolfram Engine installer.
  2. Install it (macOS: drag Wolfram.app to /Applications;
     Linux: sudo bash WolframEngine_${WOLFRAM_VERSION}_LINUX.sh).
  3. Run \`wolframscript --activate\` yourself and sign in.
  4. Rerun this script with \`install_wolfram.sh use-path <path-to-wolframscript>\`.

Typical paths:
  macOS: /Applications/Wolfram.app/Contents/MacOS/wolframscript
  Linux: /usr/local/bin/wolframscript
EOF
  exit 0
}

usage() {
  cat >&2 <<EOF
Usage: install_wolfram.sh <command> [args]

Commands:
  detect              Print JSON state of existing Wolfram Engine install
  use-path <path>     Point config at an existing wolframscript binary
  install             Print a short pointer; see SKILL.md §Wolfram walkthrough for the interactive flow.
  verify              Probe the configured wolframscript and emit JSON status
                      Options: --path <p> --expected-version <v> --strict-version
                               --timeout <s> --json --wolfram-path <p>
EOF
  exit 2
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    detect)   cmd_detect ;;
    use-path) cmd_use_path "${1:-}" ;;
    install)  cmd_install ;;
    verify)   cmd_verify "$@" ;;
    *)        usage ;;
  esac
}

main "$@"
