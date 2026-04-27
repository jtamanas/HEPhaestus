#!/usr/bin/env bash
# install_feynrules.sh — detect / use-path / install FeynRules for model-building skills.
#
# FeynRules is a pure Mathematica package (no native code, no compile step).
# Install pattern mirrors sarah-install: extract tarball → register package
# path in Wolfram's user init.m → verify via version probe.
#
# Subcommands:
#   detect              Print JSON state of existing FeynRules install (no side-effects).
#   use-path <dir>      Register an existing FeynRules package directory in config.
#   install [dir]       Full auto-install; default dir: ~/feynrules-current.
#   validate            Alias for detect (non-mutating health check).
#
# Blockers are emitted as single-line JSON on stderr per blocker.schema.json.
# Status JSON (for detect / use-path success / activation_required) goes to stdout.
set -euo pipefail

_LOG_TAG="install_feynrules"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# shellcheck source=detect_wolfram.sh
. "$SCRIPT_DIR/detect_wolfram.sh"

# shellcheck source=probe_feynrules.sh
. "$SCRIPT_DIR/probe_feynrules.sh"

# Version pin. Override with HEPPH_FEYNRULES_VERSION env var.
FEYNRULES_VERSION="${HEPPH_FEYNRULES_VERSION:-2.3.49}"
# Upstream serves a single rolling "current" tarball; version is hardcoded inside.
FEYNRULES_URL="${HEPPH_FEYNRULES_URL:-http://feynrules.irmp.ucl.ac.be/downloads/feynrules-current.tar.gz}"
FEYNRULES_SHA256="TODO"  # TODO: compute real SHA256 before v1 release; verify_checksum warns-not-aborts for "TODO"

TARBALL="/tmp/feynrules-${FEYNRULES_VERSION}.tar.gz"
INIT_MARKER_BEGIN="(* hephaestus:feynrules-install BEGIN *)"
INIT_MARKER_END="(* hephaestus:feynrules-install END *)"

# ---------------------------------------------------------------------------
# is_feynrules_dir: true if <dir> contains BOTH FeynRules.m and FeynRulesPackage.m.
# ---------------------------------------------------------------------------
is_feynrules_dir() {
  local d="$1"
  [ -d "$d" ] && [ -f "$d/FeynRules.m" ] && [ -f "$d/FeynRulesPackage.m" ]
}

# ---------------------------------------------------------------------------
# scan_candidates: look for a dir containing FeynRules.m + FeynRulesPackage.m.
# ---------------------------------------------------------------------------
scan_candidates() {
  local roots=(
    "$HOME/feynrules-current"
    "$HOME/FeynRules"
    "$HOME/feynrules"
    "$HOME/software/feynrules"
    "$HOME/software/FeynRules"
    "$HOME/feynrules-${FEYNRULES_VERSION}"
    "/usr/local/feynrules"
    "/usr/local/FeynRules"
    "/usr/local/feynrules-${FEYNRULES_VERSION}"
  )
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    if is_feynrules_dir "$root"; then
      echo "$root"; return 0
    fi
    # Search one level down (e.g. ~/feynrules-current/feynrules-2.3.49/).
    local sub
    sub=$(find "$root" -maxdepth 2 -name FeynRulesPackage.m -print 2>/dev/null | head -n1 || true)
    if [ -n "$sub" ]; then
      local candidate
      candidate="$(dirname "$sub")"
      if is_feynrules_dir "$candidate"; then
        echo "$candidate"; return 0
      fi
    fi
  done
  return 1
}

# ---------------------------------------------------------------------------
# user_base_dir: query $UserBaseDirectory from wolframscript; fallback to
# per-OS hardcoded default if query fails or wolframscript is not available.
# ---------------------------------------------------------------------------
user_base_dir() {
  local ws="$1"
  local probed=""
  if [ -n "$ws" ] && [ -x "$ws" ]; then
    probed="$("$ws" -code 'Print[$UserBaseDirectory]' 2>/dev/null \
      | grep -E '^/' | head -n1 || true)"
  fi
  if [ -n "$probed" ]; then
    echo "$probed"
    return 0
  fi
  # Fallback per-OS.
  if [ "$(os_name)" = "macos" ]; then
    # Prefer Wolfram Engine layout; fall back to Mathematica if present.
    if [ -d "$HOME/Library/Wolfram" ]; then
      echo "$HOME/Library/Wolfram"
    elif [ -d "$HOME/Library/Mathematica" ]; then
      echo "$HOME/Library/Mathematica"
    else
      echo "$HOME/Library/Wolfram"
    fi
  else
    if [ -d "$HOME/.WolframEngine" ]; then
      echo "$HOME/.WolframEngine"
    elif [ -d "$HOME/.Mathematica" ]; then
      echo "$HOME/.Mathematica"
    else
      echo "$HOME/.WolframEngine"
    fi
  fi
}

# ---------------------------------------------------------------------------
# register_path: idempotently append $FeynRulesPath + $Path entry to init.m.
# Guarded by BEGIN/END comment markers; rerunning replaces the block in place.
# ---------------------------------------------------------------------------
register_path() {
  local pkg_dir="$1"
  local ws="$2"
  local base
  base="$(user_base_dir "$ws")"
  local init_dir="$base/Kernel"
  mkdir -p "$init_dir"
  local init_file="$init_dir/init.m"
  touch "$init_file"

  python3 - "$init_file" "$pkg_dir" "$INIT_MARKER_BEGIN" "$INIT_MARKER_END" <<'PY'
import sys, re
path, pkg_dir, begin, end = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(path) as f:
    src = f.read()
block = (
    f"{begin}\n"
    f'$FeynRulesPath = "{pkg_dir}";\n'
    f'If[!MemberQ[$Path, $FeynRulesPath], AppendTo[$Path, $FeynRulesPath]];\n'
    f"{end}\n"
)
# Replace any existing marked block (greedy between markers, DOTALL).
pattern = re.compile(
    re.escape(begin) + r".*?" + re.escape(end) + r"\n?",
    re.DOTALL,
)
if pattern.search(src):
    new = pattern.sub(block, src)
else:
    # Append with a leading blank line for readability.
    sep = "" if src.endswith("\n") or src == "" else "\n"
    new = src + sep + "\n" + block
with open(path, "w") as f:
    f.write(new)
PY
  log "Registered FeynRules path ($pkg_dir) in $init_file"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local path version ws
  path="$(config_get feynrules_path)"
  ws="$(config_get wolfram_engine_path)"
  if [ -z "$ws" ] || [ ! -x "$ws" ]; then
    ws="$(detect_wolfram_path)"
  fi
  if [ -n "$path" ] && is_feynrules_dir "$path"; then
    if [ -n "$ws" ] && [ -x "$ws" ] && version="$(probe_feynrules_version "$path" "$ws")" && [ -n "$version" ]; then
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
      return 0
    fi
    # Files present but version probe unavailable.
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
    emit_blocker FEYNRULES_PATH_INVALID fatal \
      "use-path requires a FeynRules package dir argument." \
      "Provide the path to the directory containing FeynRules.m and FeynRulesPackage.m."
    exit $EXIT_BAD_PATH
  }
  path="${path/#\~/$HOME}"

  if ! is_feynrules_dir "$path"; then
    emit_blocker FEYNRULES_PATH_INVALID fatal \
      "Not a FeynRules package dir (missing FeynRules.m or FeynRulesPackage.m): $path" \
      "Provide the path to the dir that contains BOTH FeynRules.m and FeynRulesPackage.m (e.g. ~/feynrules-current)."
    exit $EXIT_BAD_PATH
  fi

  local ws
  ws="$(detect_wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "FeynRules needs Wolfram Engine. No wolframscript binary found or configured." \
      "Run \`/install\` to install Wolfram Engine, or set wolfram_engine_path via \`/install use-path <path>\`."
    exit $EXIT_NO_WOLFRAM
  fi

  register_path "$path" "$ws"
  local version
  version="$(probe_feynrules_version "$path" "$ws" || true)"
  if [ -z "$version" ]; then
    warn "Version probe empty; re-registering \$Path and retrying once."
    register_path "$path" "$ws"
    version="$(probe_feynrules_version "$path" "$ws" || true)"
  fi
  if [ -z "$version" ]; then
    emit_blocker FEYNRULES_SMOKE_TEST_FAILED fatal \
      "FeynRules smoke test failed. wolframscript could not load FeynRules and return a version." \
      "Ensure Wolfram Engine is activated (\`wolframscript --activate\`) and that $path contains a valid FeynRules install (FeynRules.m + FeynRulesPackage.m)."
    exit $EXIT_SMOKE
  fi

  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge feynrules_path "$path" feynrules_version "$version" feynrules_installed_at "$installed_at"
  log "Configured FeynRules at $path (v$version)"
  printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
}

# ---------------------------------------------------------------------------
# extract_tarball: extract to install_parent; return the resolved pkg_dir.
# ---------------------------------------------------------------------------
extract_tarball() {
  local install_parent="$1"
  mkdir -p "$install_parent"
  log "Extracting FeynRules to $install_parent ..."
  if ! tar -xzf "$TARBALL" -C "$install_parent"; then
    err "Extraction failed."
    df -h "$install_parent" >&2 || true
    exit $EXIT_EXTRACT
  fi
  # Top-level dir in the FeynRules tarball is typically `feynrules-current`
  # but may be versioned. Resolve by inspecting the tarball.
  local top
  top=$(tar -tzf "$TARBALL" 2>/dev/null | head -n1 | cut -d/ -f1)
  local pkg_dir="$install_parent/$top"
  if ! is_feynrules_dir "$pkg_dir"; then
    # Search one level deep just in case.
    local found
    found=$(find "$pkg_dir" -maxdepth 2 -name FeynRulesPackage.m -print 2>/dev/null | head -n1 || true)
    if [ -n "$found" ]; then
      pkg_dir="$(dirname "$found")"
    fi
  fi
  if ! is_feynrules_dir "$pkg_dir"; then
    err "Extracted dir $pkg_dir does not contain FeynRules.m + FeynRulesPackage.m."
    exit $EXIT_BAD_PATH
  fi
  # Stable symlink so ~/feynrules-current/current always points at the active build.
  ln -sfn "$pkg_dir" "$install_parent/current" 2>/dev/null || true
  echo "$pkg_dir"
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  local install_dir="${1:-$HOME/feynrules-current}"
  install_dir="${install_dir/#\~/$HOME}"

  local ws
  ws="$(detect_wolfram_path)"
  if [ -z "$ws" ]; then
    emit_blocker WOLFRAM_KERNEL_ABSENT fatal \
      "FeynRules needs Wolfram Engine configured first." \
      "Run \`/install\` to install Wolfram Engine, or \`/feynrules-install use-path\` after installing it manually."
    exit $EXIT_NO_WOLFRAM
  fi

  if ! command -v tar >/dev/null 2>&1; then
    err "tar not found on PATH."
    exit $EXIT_GENERIC
  fi

  log "FeynRules version (pin): $FEYNRULES_VERSION"
  log "Install target: $install_dir"
  # Tarball is ~590 KB; extracted tree ~50-200 MB with bundled models.
  # Require 1 GB free to leave room for user-generated UFO outputs.
  check_disk 1 2

  if ! download_with_retry "$FEYNRULES_URL" "$TARBALL"; then
    emit_blocker FEYNRULES_DOWNLOAD_FAILED fatal \
      "Download failed twice for $FEYNRULES_URL" \
      "Check your network connection and retry. URL: $FEYNRULES_URL"
    exit $EXIT_DOWNLOAD
  fi

  verify_checksum "$TARBALL" "$FEYNRULES_SHA256"

  local pkg_dir
  pkg_dir="$(extract_tarball "$install_dir")"
  register_path "$pkg_dir" "$ws"

  local version
  version="$(probe_feynrules_version "$pkg_dir" "$ws" || true)"
  if [ -z "$version" ]; then
    warn "Version probe empty; re-registering \$Path and retrying once."
    register_path "$pkg_dir" "$ws"
    version="$(probe_feynrules_version "$pkg_dir" "$ws" || true)"
  fi
  if [ -z "$version" ]; then
    # Emit a $Path diagnostic to help the user.
    warn "Current Wolfram \$Path:"
    "$ws" -code 'Print[$Path]' 2>&1 >&2 || true
    emit_blocker FEYNRULES_SMOKE_TEST_FAILED fatal \
      "FeynRules smoke test failed after install (wolframscript did not return a version)." \
      "Check that Wolfram Engine is activated: \`wolframscript --activate\`. On Mathematica 12.2+, ValueQ deprecation can block the load; FeynRules 2.3.49+ handles this."
    exit $EXIT_SMOKE
  fi

  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge feynrules_path "$pkg_dir" feynrules_version "$version" feynrules_installed_at "$installed_at"
  rm -f "$TARBALL"
  log "FeynRules v$version installed at $pkg_dir."

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

  log "FeynRules ready."
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<EOF
Usage: install_feynrules.sh <command> [args]

Commands:
  detect              Print JSON state of existing FeynRules install (no side-effects)
  use-path <dir>      Register an existing FeynRules package dir (must contain
                      FeynRules.m AND FeynRulesPackage.m)
  install [dir]       Full auto-install (default dir: ~/feynrules-current)
  validate            Alias for detect

Environment overrides:
  HEPPH_FEYNRULES_VERSION   Override pinned FeynRules version (default: 2.3.49)
  HEPPH_FEYNRULES_URL       Override tarball URL
                            (default: UCL feynrules-current.tar.gz)
  XDG_CONFIG_HOME           Override config directory (default: ~/.config)
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
    detect|validate) cmd_detect ;;
    use-path)        cmd_use_path "${1:-}" ;;
    install)         cmd_install "${1:-}" ;;
    *)               usage ;;
  esac
}

main "$@"
