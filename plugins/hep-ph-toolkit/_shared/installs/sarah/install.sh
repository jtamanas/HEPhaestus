#!/usr/bin/env bash
# install.sh — detect / use-path / install SARAH for model-building skills.
#
# Subcommands:
#   detect              Print JSON state of existing SARAH install (no side-effects).
#   use-path <dir>      Register an existing SARAH package directory in config.
#   install [dir]       Full auto-install; default dir: ~/SARAH.
#
# Blockers are emitted as single-line JSON on stderr per blocker.schema.json.
# Status JSON (for detect / use-path success / activation_required) goes to stdout.
#
# TODO(post-refactor): plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh
# is a divergent variant carrying a `verify` subcommand, install_with_rollback,
# unregister_path, the VERSION:-marker probe, and HEPPH_SARAH_FORCE_SMOKE_FAIL
# test knob (with passing tests under that script's tests/ tree). When those
# features are absorbed here, the variant + its tests should be deleted.
set -euo pipefail

_LOG_TAG="install_sarah"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# shellcheck source=detect_wolfram.sh
. "$SCRIPT_DIR/detect_wolfram.sh"

# Version pin.  Override with HEPPH_SARAH_VERSION env var (see SHARED.md §Env-var overrides).
SARAH_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"
SARAH_URL="https://sarah.hepforge.org/downloads/SARAH-${SARAH_VERSION}.tar.gz"
SARAH_SHA256="TODO"  # TODO: compute real SHA256 before v1 release; verify_checksum warns-not-aborts for "TODO"

TARBALL="/tmp/sarah-${SARAH_VERSION}.tar.gz"

# ---------------------------------------------------------------------------
# probe_version: load SARAH in wolframscript and extract the version string.
# $Path gets the PARENT of pkg_dir so that `<<SARAH`` resolves.
# Preserving /.. is intentional: SARAH's loader requires the parent dir.
# ---------------------------------------------------------------------------
probe_version() {
  local pkg_dir="$1"
  local ws="${2:-}"
  [ -d "$pkg_dir" ] || return 1
  if [ -z "$ws" ]; then
    ws="$(config_get wolfram_engine_path)"
  fi
  [ -x "$ws" ] || return 1
  "$ws" -code "AppendTo[\$Path, \"$pkg_dir/..\"]; <<SARAH\`; Print[SARAH\`SA\`Version]" 2>/dev/null \
    | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1
}

# ---------------------------------------------------------------------------
# scan_candidates: look for a directory containing SARAH.m under common paths.
# ---------------------------------------------------------------------------
scan_candidates() {
  local roots=("$HOME/SARAH" "$HOME/software/SARAH" "/usr/local/SARAH")
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
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

# ---------------------------------------------------------------------------
# register_path: append SARAH's parent dir to Wolfram's $Path via init.m.
# Idempotent.
# ---------------------------------------------------------------------------
register_path() {
  local pkg_dir="$1"
  local parent
  parent="$(cd "$pkg_dir/.." && pwd)"
  # macOS WolframEngine init.m lives under ~/Library/WolframEngine/Kernel — NOT
  # ~/Library/Wolfram/Kernel (that's the Mathematica directory). B2 fix; see
  # install/scripts/install_sarah.sh:108 + tests/test_sarah_rollback.sh.
  local init_dir="$HOME/Library/WolframEngine/Kernel"  # macOS default
  [ "$(os_name)" = "linux" ] && init_dir="$HOME/.WolframEngine/Kernel"
  if [ -n "${HEPPH_WOLFRAM_USER_BASE:-}" ]; then
    init_dir="$HEPPH_WOLFRAM_USER_BASE/Kernel"
  fi
  mkdir -p "$init_dir"
  local init_file="$init_dir/init.m"
  local marker="(* hephaestus SARAH path *)"
  if [ -f "$init_file" ] && grep -q "hephaestus SARAH path" "$init_file"; then
    python3 - "$init_file" "$parent" "$marker" <<'PY'
import sys, re
path, parent, marker = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    src = f.read()
new = re.sub(
    re.escape(marker) + r".*\n.*\n",
    f"{marker}\nIf[!MemberQ[$Path, \"{parent}\"], AppendTo[$Path, \"{parent}\"]];\n",
    src,
)
with open(path, "w") as f:
    f.write(new)
PY
  else
    {
      echo ""
      echo "$marker"
      echo "If[!MemberQ[\$Path, \"$parent\"], AppendTo[\$Path, \"$parent\"]];"
    } >> "$init_file"
  fi
  log "Registered SARAH parent dir ($parent) in $init_file"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local path version ws
  path="$(config_get sarah_path)"
  ws="$(config_get wolfram_engine_path)"
  if [ -n "$path" ] && [ -d "$path" ] && [ -f "$path/SARAH.m" ]; then
    if [ -n "$ws" ] && [ -x "$ws" ] && version="$(probe_version "$path" "$ws")" && [ -n "$version" ]; then
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
      return 0
    fi
    # SARAH.m found at configured path but version probe unavailable (no wolframscript).
    # Report "found" so caller can decide whether to run use-path or install Wolfram.
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
  local path="$1"
  [ -n "$path" ] || {
    emit_blocker SARAH_PATH_INVALID fatal \
      "use-path requires a SARAH package dir argument." \
      "Provide the path to the directory containing SARAH.m."
    exit $EXIT_BAD_PATH
  }
  path="${path/#\~/$HOME}"

  if [ ! -d "$path" ] || [ ! -f "$path/SARAH.m" ]; then
    emit_blocker SARAH_PATH_INVALID fatal \
      "Not a SARAH package dir (missing SARAH.m): $path" \
      "Provide the path to the directory that contains SARAH.m (e.g. ~/SARAH/SARAH-4.15.3)."
    exit $EXIT_SARAH_PATH
  fi

  local ws
  ws="$(detect_wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "SARAH needs Wolfram Engine. No wolframscript binary found or configured." \
      "Run \`/install\` to install Wolfram Engine, or set wolfram_engine_path via \`/install use-path <path>\`."
    exit $EXIT_NO_WOLFRAM
  fi

  register_path "$path"
  local version
  version="$(probe_version "$path" "$ws" || true)"
  if [ -z "$version" ]; then
    warn "Version probe empty; re-registering \$Path and retrying once."
    register_path "$path"
    version="$(probe_version "$path" "$ws" || true)"
  fi
  if [ -z "$version" ]; then
    emit_blocker SARAH_SMOKE_TEST_FAILED fatal \
      "SARAH smoke test failed. wolframscript could not load SARAH and return a version." \
      "Ensure Wolfram Engine is activated (\`wolframscript --activate\`) and that $path contains a valid SARAH install."
    exit $EXIT_SMOKE
  fi

  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge sarah_path "$path" sarah_version "$version" sarah_installed_at "$installed_at"
  log "Configured SARAH at $path (v$version)"
  printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
}

# ---------------------------------------------------------------------------
# extract_and_register
# ---------------------------------------------------------------------------
extract_and_register() {
  local install_parent="$1"
  mkdir -p "$install_parent"
  log "Extracting SARAH to $install_parent ..."
  if ! tar -xzf "$TARBALL" -C "$install_parent"; then
    err "Extraction failed."
    df -h "$install_parent" >&2 || true
    exit $EXIT_EXTRACT
  fi
  local extracted
  extracted=$(tar -tzf "$TARBALL" 2>/dev/null | head -n1 | cut -d/ -f1)
  local pkg_dir="$install_parent/$extracted"
  if [ ! -f "$pkg_dir/SARAH.m" ]; then
    err "Extracted dir $pkg_dir does not contain SARAH.m."
    exit $EXIT_SARAH_PATH
  fi
  # Stable symlink so ~/SARAH always points at the active version.
  ln -sfn "$pkg_dir" "$install_parent/SARAH-current"
  echo "$pkg_dir"
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  local install_dir="${1:-$HOME/SARAH}"
  install_dir="${install_dir/#\~/$HOME}"

  local ws
  ws="$(detect_wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "SARAH needs Wolfram Engine configured first." \
      "Run \`/install\` to install Wolfram Engine, or \`bash _shared/installs/sarah/install.sh use-path\` after installing it manually."
    exit $EXIT_NO_WOLFRAM
  fi

  if ! command -v tar >/dev/null 2>&1; then
    err "tar not found on PATH."
    exit $EXIT_GENERIC
  fi

  log "SARAH version: $SARAH_VERSION"
  log "Install target: $install_dir"
  check_disk 1 2

  # Download.
  if ! download_with_retry "$SARAH_URL" "$TARBALL"; then
    emit_blocker SARAH_DOWNLOAD_FAILED fatal \
      "Download failed twice for $SARAH_URL" \
      "Check your network connection and retry. URL: $SARAH_URL"
    exit $EXIT_DOWNLOAD
  fi

  verify_checksum "$TARBALL" "$SARAH_SHA256"

  local pkg_dir
  pkg_dir="$(extract_and_register "$install_dir")"
  register_path "$pkg_dir"

  local version
  version="$(probe_version "$pkg_dir" "$ws" || true)"
  if [ -z "$version" ]; then
    warn "Version probe empty; re-registering \$Path and retrying once."
    register_path "$pkg_dir"
    version="$(probe_version "$pkg_dir" "$ws" || true)"
  fi
  if [ -z "$version" ]; then
    emit_blocker SARAH_SMOKE_TEST_FAILED fatal \
      "SARAH smoke test failed after install (wolframscript did not return a version)." \
      "Check that Wolfram Engine is activated: \`wolframscript --activate\`."
    exit $EXIT_SMOKE
  fi

  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge sarah_path "$pkg_dir" sarah_version "$version" sarah_installed_at "$installed_at"
  rm -f "$TARBALL"
  log "SARAH v$version installed at $pkg_dir."

  # Post-install activation check.
  local activation_status
  activation_status="$("$SCRIPT_DIR/check_wolfram_activation.sh" || true)"
  local act_state
  act_state="$(printf '%s' "$activation_status" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)"
  if [ "$act_state" = "activation_required" ]; then
    # Surface the user_instruction; exit 0 (not a blocker).
    printf '%s\n' "$activation_status"
    exit 0
  fi

  log "SARAH ready."
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<EOF
Usage: install.sh <command> [args]

Commands:
  detect              Print JSON state of existing SARAH install (no side-effects)
  use-path <dir>      Register an existing SARAH package dir (must contain SARAH.m)
  install [dir]       Full auto-install (default dir: ~/SARAH)

Environment overrides:
  HEPPH_SARAH_VERSION   Override pinned SARAH version (default: 4.15.3)
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
    *)        usage ;;
  esac
}

main "$@"
