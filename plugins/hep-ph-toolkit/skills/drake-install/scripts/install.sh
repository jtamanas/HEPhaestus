#!/usr/bin/env bash
# install.sh — detect / use-path / install / validate DRAKE.
#
# Subcommands:
#   detect              Print JSON state of existing DRAKE install (no side-effects).
#   use-path <dir>      Register an existing unpacked DRAKE directory in config.
#   install [dir]       Attempt auto-install; on hepforge Anubis gate, emit
#                       {"status":"manual_download_required",...} and exit 0
#                       so the caller can route the user through use-path.
#   validate            Re-run the WIMP smoke test against the configured drake_path.
#
# Blockers are emitted as single-line JSON on stderr per blocker.schema.json.
# Status JSON (configured / found / missing / activation_required /
# manual_download_required) goes to stdout.
set -euo pipefail

_LOG_TAG="install_drake"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# Local exit code for Anubis-gated download (above 20, per _common.sh convention).
EXIT_HEPFORGE_GATED=18

# Version pin. Override with HEPPH_DRAKE_VERSION env var.
DRAKE_VERSION="${HEPPH_DRAKE_VERSION:-1.0}"
DRAKE_URL_BASE="${HEPPH_DRAKE_URL:-https://drake.hepforge.org/downloads/drake.zip}"

ZIPBALL="/tmp/drake-${DRAKE_VERSION}.zip"

# ---------------------------------------------------------------------------
# wolfram_path: resolve wolframscript via config or PATH. Empty if absent.
# ---------------------------------------------------------------------------
wolfram_path() {
  local path
  path="$(config_get wolfram_engine_path)"
  if [ -n "$path" ] && [ -x "$path" ]; then
    echo "$path"; return 0
  fi
  local which_hit
  which_hit="$(command -v wolframscript || true)"
  if [ -n "$which_hit" ] && [ -x "$which_hit" ]; then
    echo "$which_hit"; return 0
  fi
  echo ""
}

# ---------------------------------------------------------------------------
# is_drake_dir: a plausible DRAKE root contains test/test.wls.
# ---------------------------------------------------------------------------
is_drake_dir() {
  local dir="$1"
  [ -d "$dir" ] && [ -f "$dir/test/test.wls" ]
}

# ---------------------------------------------------------------------------
# scan_candidates: common locations for an unpacked DRAKE tree.
# ---------------------------------------------------------------------------
scan_candidates() {
  local roots=("$HOME/drake" "$HOME/DRAKE" "$HOME/hep/drake" "$HOME/software/drake")
  for root in "${roots[@]}"; do
    if is_drake_dir "$root"; then
      echo "$root"; return 0
    fi
    # One level of nesting (e.g. ~/drake/drake-1.0/).
    if [ -d "$root" ]; then
      local sub
      sub=$(find "$root" -maxdepth 2 -type f -name test.wls -path '*/test/test.wls' -print 2>/dev/null | head -n1 || true)
      if [ -n "$sub" ]; then
        echo "$(dirname "$(dirname "$sub")")"; return 0
      fi
    fi
  done
  return 1
}

# ---------------------------------------------------------------------------
# looks_like_anubis_challenge: detect hepforge's bot-protection HTML.
# Returns 0 if the file looks like an Anubis challenge page, non-zero otherwise.
# ---------------------------------------------------------------------------
looks_like_anubis_challenge() {
  local file="$1"
  [ -f "$file" ] || return 1
  # Anubis pages are small HTML with telltale strings. A real drake.zip is
  # multi-MB and binary. Check both size (<200 KB is suspicious) and content.
  local size
  size=$(wc -c <"$file" | tr -d ' ')
  if [ "$size" -lt 204800 ]; then
    if head -c 4096 "$file" 2>/dev/null | grep -qiE 'anubis|proof.of.work|challenge|cloudflare|<!doctype html|<html' ; then
      return 0
    fi
  fi
  return 1
}

# ---------------------------------------------------------------------------
# run_smoke: invoke probe_drake.sh and echo its JSON on stdout.
# ---------------------------------------------------------------------------
run_smoke() {
  local drake_dir="$1"
  local ws="${2:-}"
  "$SCRIPT_DIR/probe_drake.sh" "$drake_dir" "$ws"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local path ws
  path="$(config_get drake_path)"
  ws="$(wolfram_path)"

  if [ -n "$path" ] && is_drake_dir "$path"; then
    if [ -n "$ws" ]; then
      local smoke status
      smoke="$(run_smoke "$path" "$ws")"
      status="$(printf '%s' "$smoke" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
      if [ "$status" = "ok" ]; then
        local version
        version="$(printf '%s' "$smoke" | python3 -c "import json,sys; print(json.load(sys.stdin).get('version',''))" 2>/dev/null || true)"
        printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
        return 0
      fi
      # Smoke test did not pass — distinguish activation vs other failure
      if [ "$status" = "activation_required" ]; then
        printf '{"status":"activation_required","path":"%s"}\n' "$path"
        return 0
      fi
      # Other smoke failures fall through to "found".
    fi
    printf '{"status":"found","path":"%s"}\n' "$path"
    return 0
  fi

  local found
  if found="$(scan_candidates)"; then
    printf '{"status":"found","path":"%s"}\n' "$found"
    return 0
  fi

  printf '{"status":"missing"}\n'
}

# ---------------------------------------------------------------------------
# cmd_use_path
# ---------------------------------------------------------------------------
cmd_use_path() {
  local path="${1:-}"
  if [ -z "$path" ]; then
    emit_blocker DRAKE_PATH_INVALID fatal \
      "use-path requires a DRAKE directory argument." \
      "Provide the path to the unpacked DRAKE root (the directory that contains test/test.wls)."
    exit $EXIT_BAD_PATH
  fi
  path="${path/#\~/$HOME}"

  if ! is_drake_dir "$path"; then
    emit_blocker DRAKE_PATH_INVALID fatal \
      "Not a DRAKE tree (missing test/test.wls): $path" \
      "Download the zipball from https://drake.hepforge.org/, unpack it, and point use-path at the directory containing test/test.wls."
    exit $EXIT_BAD_PATH
  fi

  local ws
  ws="$(wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "DRAKE needs Wolfram Engine. No wolframscript binary found or configured." \
      "Run \`/install\` to install Wolfram Engine, or set wolfram_engine_path via \`/install use-path <path>\`."
    exit $EXIT_NO_WOLFRAM
  fi

  log "Running DRAKE WIMP smoke test at $path ..."
  local smoke status
  smoke="$(run_smoke "$path" "$ws")"
  status="$(printf '%s' "$smoke" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"

  case "$status" in
    ok)
      local version installed_at
      version="$(printf '%s' "$smoke" | python3 -c "import json,sys; print(json.load(sys.stdin).get('version',''))" 2>/dev/null || true)"
      [ -n "$version" ] || version="1.0 (assumed)"
      installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      config_merge drake_path "$path" drake_version "$version" drake_installed_at "$installed_at"
      log "Configured DRAKE at $path (v$version)"
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
      ;;
    activation_required)
      # Surface as status, not a blocker. Still record the path so the user
      # can re-run `/drake-install detect` after activation.
      local installed_at
      installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      config_merge drake_path "$path" drake_version "1.0 (assumed, unverified)" drake_installed_at "$installed_at"
      printf '%s\n' "$smoke"
      ;;
    *)
      emit_blocker DRAKE_SMOKE_TEST_FAILED fatal \
        "DRAKE WIMP smoke test failed. See /tmp/drake_smoke.log for details." \
        "Ensure Wolfram Engine is activated (\`wolframscript --activate\`) and that $path/test/test.wls is intact."
      exit $EXIT_SMOKE
      ;;
  esac
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  local install_dir="${1:-$HOME/drake}"
  install_dir="${install_dir/#\~/$HOME}"

  local ws
  ws="$(wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "DRAKE needs Wolfram Engine configured first." \
      "Run \`/install\` to install Wolfram Engine, or \`/drake-install use-path\` after unpacking DRAKE manually."
    exit $EXIT_NO_WOLFRAM
  fi

  if ! command -v unzip >/dev/null 2>&1; then
    err "unzip not found on PATH."
    exit $EXIT_NO_UNZIP
  fi

  log "DRAKE version: $DRAKE_VERSION"
  log "Install target: $install_dir"
  check_disk 1 2

  # Attempt download. We deliberately do NOT use download_with_retry's
  # hard-exit path here — the Anubis gate is a first-class outcome and we
  # want to route the user, not abort.
  rm -f "$ZIPBALL"
  local dl_rc=0
  log "Download attempt: $DRAKE_URL_BASE"
  curl -L --fail --silent --show-error -o "$ZIPBALL" "$DRAKE_URL_BASE" || dl_rc=$?

  if [ "$dl_rc" -ne 0 ] || [ ! -s "$ZIPBALL" ]; then
    warn "Download failed (curl rc=$dl_rc). hepforge's Anubis bot-challenge is the usual cause."
    cat <<JSON
{"status":"manual_download_required","message":"Automated download from hepforge was blocked (curl rc=$dl_rc). The hepforge site uses Anubis bot-protection that curl/wget cannot solve.","user_instruction":"Open https://drake.hepforge.org/ in a browser, click Downloads, save the zipball, unpack it (e.g. to ~/drake), then rerun \`/drake-install use-path ~/drake\`."}
JSON
    exit 0
  fi

  if looks_like_anubis_challenge "$ZIPBALL"; then
    warn "Downloaded file looks like an Anubis challenge page, not a zipball."
    rm -f "$ZIPBALL"
    cat <<JSON
{"status":"manual_download_required","message":"hepforge returned an Anubis bot-challenge page instead of the zipball.","user_instruction":"Open https://drake.hepforge.org/ in a browser, click Downloads, save the zipball, unpack it (e.g. to ~/drake), then rerun \`/drake-install use-path ~/drake\`."}
JSON
    exit 0
  fi

  # Optional checksum (will warn on placeholder).
  local drake_sha256="${HEPPH_DRAKE_SHA256:-TODO}"
  verify_checksum "$ZIPBALL" "$drake_sha256"

  mkdir -p "$install_dir"
  log "Extracting DRAKE to $install_dir ..."
  if ! unzip -q -o "$ZIPBALL" -d "$install_dir"; then
    err "Extraction failed."
    exit $EXIT_EXTRACT
  fi

  # Find the unpacked root (either install_dir itself or a single top-level child).
  local pkg_dir=""
  if is_drake_dir "$install_dir"; then
    pkg_dir="$install_dir"
  else
    local candidate
    candidate=$(find "$install_dir" -maxdepth 2 -type f -name test.wls -path '*/test/test.wls' -print 2>/dev/null | head -n1 || true)
    if [ -n "$candidate" ]; then
      pkg_dir="$(dirname "$(dirname "$candidate")")"
    fi
  fi

  if [ -z "$pkg_dir" ] || ! is_drake_dir "$pkg_dir"; then
    emit_blocker DRAKE_PATH_INVALID fatal \
      "Extracted archive did not contain test/test.wls under $install_dir." \
      "Inspect $install_dir manually, or download the zipball via browser and use \`/drake-install use-path\`."
    exit $EXIT_BAD_PATH
  fi

  # Delegate the rest to use-path (which runs smoke test + writes config).
  cmd_use_path "$pkg_dir"
  rm -f "$ZIPBALL"
}

# ---------------------------------------------------------------------------
# cmd_validate: re-run smoke test against the configured path.
# ---------------------------------------------------------------------------
cmd_validate() {
  local path ws
  path="$(config_get drake_path)"
  if [ -z "$path" ] || ! is_drake_dir "$path"; then
    emit_blocker DRAKE_PATH_INVALID fatal \
      "No drake_path configured, or path is invalid." \
      "Run \`/drake-install detect\` or \`/drake-install use-path <dir>\` first."
    exit $EXIT_BAD_PATH
  fi
  ws="$(wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "DRAKE needs Wolfram Engine." \
      "Run \`/install\` or set wolfram_engine_path."
    exit $EXIT_NO_WOLFRAM
  fi

  local smoke status
  smoke="$(run_smoke "$path" "$ws")"
  status="$(printf '%s' "$smoke" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
  case "$status" in
    ok)
      printf '%s\n' "$smoke"
      ;;
    activation_required)
      printf '%s\n' "$smoke"
      ;;
    *)
      emit_blocker DRAKE_SMOKE_TEST_FAILED fatal \
        "DRAKE smoke test failed. See /tmp/drake_smoke.log." \
        "Check Wolfram Engine activation and the DRAKE install at $path."
      exit $EXIT_SMOKE
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<EOF
Usage: install.sh <command> [args]

Commands:
  detect              Print JSON state of existing DRAKE install (no side-effects)
  use-path <dir>      Register an existing unpacked DRAKE directory (must contain test/test.wls)
  install [dir]       Attempt auto-install (default dir: ~/drake).
                      If hepforge's Anubis bot-challenge blocks the download, emits
                      {"status":"manual_download_required",...} and exits 0.
  validate            Re-run the WIMP smoke test against the configured drake_path

Environment overrides:
  HEPPH_DRAKE_VERSION   Override pinned DRAKE version (default: 1.0)
  HEPPH_DRAKE_URL       Override download URL (default: https://drake.hepforge.org/downloads/drake.zip)
  HEPPH_DRAKE_SHA256    Override expected SHA256 (default: TODO)
  XDG_CONFIG_HOME       Override config directory (default: ~/.config)
EOF
  exit 2
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    detect)   cmd_detect ;;
    use-path) cmd_use_path "${1:-}" ;;
    install)  cmd_install "${1:-}" ;;
    validate) cmd_validate ;;
    *)        usage ;;
  esac
}

main "$@"
