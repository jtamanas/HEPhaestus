#!/usr/bin/env bash
# install.sh — _shared/installs/spheno entry point (W2).
#
# Subcommands:
#   detect                  Print JSON state of existing SPheno install.
#   use-path <path>         Accept a binary OR a source-tree path; record both
#                           spheno_path (binary) and spheno_src_path (source root).
#   install [dir]           Full auto-install from source (default: $HOME/SPheno/SPheno-<version>).
#
# Version-mismatch policy: if an existing spheno_src_path has a version that
# does not match the current pin, install fresh alongside in a new versioned
# subdirectory; update both keys to the fresh install.
#
# HEPPH_SPHENO_VERSION env override respected (defaults to 4.0.5).
#
# TODO(post-refactor): plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh
# is a divergent variant carrying a `verify` subcommand, spheno_probe_banner
# (dylib-vs-banner classification under with_timeout), and the
# HEPPH_F90_COMPILER override (with passing tests under that script's tests/
# tree). When those features are absorbed here, the variant + its tests
# should be deleted.
set -euo pipefail

_LOG_TAG="install_spheno"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared helpers (W0 pattern for model-building skills, 4 levels up).
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Source blocker helper.
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# ---------------------------------------------------------------------------
# Version / URL configuration (HEPPH_SPHENO_VERSION override per §2.4).
# ---------------------------------------------------------------------------
SPHENO_VERSION="${HEPPH_SPHENO_VERSION:-4.0.5}"
SPHENO_URL="https://spheno.hepforge.org/downloads/SPheno-${SPHENO_VERSION}.tar.gz"
SPHENO_SHA256="TODO"  # verify_checksum warns-not-aborts for TODO; update pre-v1

TARBALL="/tmp/spheno-${SPHENO_VERSION}.tar.gz"
MAKE_LOG="/tmp/spheno_make.log"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Probe the version from a SPheno binary.
# Strategy 1: parse the version from the source directory name (SPheno-x.y.z).
# Strategy 2: run the binary with no args and grep the banner.
probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  local dir
  dir="$(cd "$(dirname "$bin")/.." && pwd)"
  local base
  base="$(basename "$dir")"
  local v
  v="$(printf '%s' "$base" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  v="$("$bin" 2>&1 | grep -Eo 'SPheno[[:space:]]v?[0-9]+\.[0-9]+\.[0-9]+' \
        | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  return 1
}

smoke_test() {
  local bin="$1"
  local out
  out="$("$bin" 2>&1 || true)"
  if printf '%s' "$out" | grep -qiE '(usage|input file|LesHouches)'; then
    log "SPheno smoke test passed."
    return 0
  fi
  emit_blocker "SPHENO_BASE_BUILD_FAILED" "fatal" \
    "SPheno binary at $bin failed smoke test (expected usage/LesHouches banner)."
  exit "$EXIT_SMOKE"
}

# Scan well-known locations for an existing SPheno binary.
scan_candidates() {
  local roots=("$HOME/SPheno" "$HOME/software/SPheno" "/usr/local/SPheno")
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    # Versioned sub-dirs, e.g. $HOME/SPheno/SPheno-4.0.5/bin/SPheno
    local hit
    hit=$(find "$root" -maxdepth 4 -type f -name SPheno -perm -u+x 2>/dev/null | head -n1 || true)
    [ -n "$hit" ] && { echo "$hit"; return 0; }
  done
  local which_hit
  which_hit="$(command -v SPheno || true)"
  [ -n "$which_hit" ] && { echo "$which_hit"; return 0; }
  return 1
}

# Derive spheno_src_path from a binary path: go two levels up (bin/SPheno → root).
derive_src_from_bin() {
  local bin="$1"
  local dir
  dir="$(cd "$(dirname "$bin")/.." && pwd)"
  echo "$dir"
}

# Record both spheno_path and spheno_src_path in config, plus version and timestamp.
record_both_keys() {
  local bin="$1"
  local src="$2"
  local version="$3"
  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge \
    spheno_path "$bin" \
    spheno_src_path "$src" \
    spheno_version "$version" \
    spheno_installed_at "$installed_at"
  log "Recorded spheno_path=$bin spheno_src_path=$src version=$version"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local path
  path="$(config_get spheno_path)"

  if [ -n "$path" ] && [ -x "$path" ]; then
    local version
    version="$(probe_version "$path" || echo "")"
    local src_path src_was_derived=0
    src_path="$(config_get spheno_src_path)"

    # Re-validate a configured src_path against the filesystem: if the
    # recorded path no longer has a Makefile (user rm -rf'd the tree,
    # relocated it, etc.), treat as missing and fall through to derive.
    if [ -n "$src_path" ] && [ ! -f "$src_path/Makefile" ]; then
      src_path=""
    fi

    # If spheno_src_path not in config (or stale), derive it.
    if [ -z "$src_path" ]; then
      src_path="$(derive_src_from_bin "$path")"
      if [ ! -f "$src_path/Makefile" ]; then
        src_path=""
      else
        src_was_derived=1
      fi
    fi

    # Persist a freshly-derived src_path so downstream skills like
    # /spheno-build can read it from config without requiring the user
    # to run `use-path`. The value is trivially recomputable from
    # spheno_path, so writing it is a caching promotion, not new
    # information. We deliberately do NOT persist spheno_version here:
    # probe_version reads the directory basename, and persisting that
    # would poison cmd_install's version-mismatch branch for users whose
    # dir name is stale relative to the actual binary.
    if [ "$src_was_derived" = "1" ] && [ -n "$src_path" ]; then
      config_merge spheno_src_path "$src_path"
    fi

    if [ -n "$src_path" ]; then
      printf '{"status":"configured","path":"%s","src_path":"%s","version":"%s"}\n' \
        "$path" "$src_path" "$version"
    else
      printf '{"status":"configured","path":"%s","version":"%s"}\n' \
        "$path" "$version"
    fi
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
  [ -n "$path" ] || {
    emit_blocker "SPHENO_PATH_INVALID" "fatal" \
      "use-path requires a path argument (binary or source tree)."
    exit "$EXIT_BAD_PATH"
  }

  # Expand ~ to $HOME.
  path="${path/#\~/$HOME}"

  local bin src version

  # Case 1: path is an executable file named SPheno → treat as binary.
  if [ -f "$path" ] && [ -x "$path" ] && [ "$(basename "$path")" = "SPheno" ]; then
    bin="$path"
    src="$(derive_src_from_bin "$bin")"
    if [ ! -f "$src/Makefile" ]; then
      emit_blocker "SPHENO_PATH_INVALID" "fatal" \
        "Binary at $bin accepted, but source tree Makefile not found at $src/Makefile. Cannot record spheno_src_path." \
        "Provide the source tree root instead, or ensure the SPheno source is present alongside the binary."
      exit "$EXIT_BAD_PATH"
    fi
    if [ ! -x "$bin" ]; then
      emit_blocker "SPHENO_PATH_INVALID" "fatal" \
        "Path $bin is not executable."
      exit "$EXIT_BAD_PATH"
    fi
    version="$(probe_version "$bin" || echo "$SPHENO_VERSION")"
    smoke_test "$bin"
    record_both_keys "$bin" "$src" "$version"
    printf '{"status":"configured","path":"%s","src_path":"%s","version":"%s"}\n' \
      "$bin" "$src" "$version"
    return 0
  fi

  # Case 2: path is a directory with a Makefile → treat as source tree.
  if [ -d "$path" ] && [ -f "$path/Makefile" ]; then
    src="$path"
    bin="$src/bin/SPheno"
    if [ ! -x "$bin" ]; then
      emit_blocker "SPHENO_PATH_INVALID" "fatal" \
        "Source tree at $src accepted (Makefile present), but binary $bin is missing or not executable." \
        "Run 'make' inside $src first, then retry use-path."
      exit "$EXIT_BAD_PATH"
    fi
    version="$(probe_version "$bin" || echo "$SPHENO_VERSION")"
    smoke_test "$bin"
    record_both_keys "$bin" "$src" "$version"
    printf '{"status":"configured","path":"%s","src_path":"%s","version":"%s"}\n' \
      "$bin" "$src" "$version"
    return 0
  fi

  # Neither case matched.
  emit_blocker "SPHENO_PATH_INVALID" "fatal" \
    "Path $path is not a valid SPheno binary (executable named SPheno) nor a source tree (directory with Makefile)." \
    "Provide either: the absolute path to the SPheno binary (e.g. ~/SPheno/SPheno-4.0.5/bin/SPheno), or the source tree root directory (e.g. ~/SPheno/SPheno-4.0.5/)."
  exit "$EXIT_BAD_PATH"
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  local install_root="${1:-$HOME/SPheno}"
  install_root="${install_root/#\~/$HOME}"

  # Version-mismatch check: if an existing install is present, compare versions.
  local existing_path existing_src existing_version
  existing_path="$(config_get spheno_path)"
  existing_src="$(config_get spheno_src_path)"
  if [ -z "$existing_src" ] && [ -n "$existing_path" ] && [ -x "$existing_path" ]; then
    existing_src="$(derive_src_from_bin "$existing_path")"
    [ -f "$existing_src/Makefile" ] || existing_src=""
  fi

  if [ -n "$existing_path" ] && [ -x "$existing_path" ]; then
    existing_version="$(probe_version "$existing_path" || echo "")"
    if [ -n "$existing_version" ] && [ "$existing_version" != "$SPHENO_VERSION" ]; then
      log "Version mismatch: existing=$existing_version pin=$SPHENO_VERSION. Installing fresh alongside."
      printf '{"status":"version_mismatch","existing_path":"%s","existing_version":"%s","pin":"%s","action":"installing_fresh_alongside"}\n' \
        "$existing_path" "$existing_version" "$SPHENO_VERSION"
      # Override install root to a versioned subdirectory so we never overwrite.
      install_root="$HOME/SPheno-${SPHENO_VERSION}"
    fi
  fi

  # gfortran precondition check.
  # shellcheck source=check_gfortran.sh
  . "$SCRIPT_DIR/check_gfortran.sh"
  check_gfortran_present

  check_disk 1 2
  mkdir -p "$install_root"

  # Download SPheno tarball.
  log "Downloading SPheno ${SPHENO_VERSION} from $SPHENO_URL ..."
  if ! download_with_retry "$SPHENO_URL" "$TARBALL"; then
    emit_blocker "SPHENO_DOWNLOAD_FAILED" "fatal" \
      "Failed to download SPheno ${SPHENO_VERSION} from $SPHENO_URL after 2 attempts." \
      "Check your internet connection. URL: $SPHENO_URL"
    exit "$EXIT_DOWNLOAD"
  fi

  verify_checksum "$TARBALL" "$SPHENO_SHA256"

  log "Extracting SPheno to $install_root ..."
  if ! tar -xzf "$TARBALL" -C "$install_root"; then
    emit_blocker "SPHENO_DOWNLOAD_FAILED" "fatal" \
      "Extraction of SPheno tarball to $install_root failed."
    exit "$EXIT_EXTRACT"
  fi

  # Determine the extracted source directory (e.g. SPheno-4.0.5).
  local extracted_name
  extracted_name="$(tar -tzf "$TARBALL" 2>/dev/null | head -n1 | cut -d/ -f1)"
  local src_dir="$install_root/$extracted_name"

  if [ ! -d "$src_dir" ]; then
    emit_blocker "SPHENO_DOWNLOAD_FAILED" "fatal" \
      "Expected source directory $src_dir not found after extraction."
    exit "$EXIT_EXTRACT"
  fi

  rm -f "$TARBALL"

  # Compile SPheno. Honor HEPPH_F90_COMPILER override (default gfortran)
  # so base-install and model-compile (compile_model.py) use the same
  # compiler — mismatched Fortran compilers produce unreadable .mod files.
  local f90_compiler="${HEPPH_F90_COMPILER:-gfortran}"
  log "Compiling SPheno in $src_dir with F90=$f90_compiler (may take 5-15 minutes) ..."
  if ! ( cd "$src_dir" && make "F90=$f90_compiler" ) >"$MAKE_LOG" 2>&1; then
    local blocker_json
    blocker_json="$(python3 "$SCRIPT_DIR/_make_log_parse.py" < "$MAKE_LOG")"
    # Emit as a blocker on stderr.
    printf '%s\n' "$blocker_json" >&2
    log "Full build log: $MAKE_LOG"
    exit "$EXIT_SPHENO_MAKE"
  fi
  log "SPheno compiled successfully."

  local bin="$src_dir/bin/SPheno"
  if [ ! -x "$bin" ]; then
    emit_blocker "SPHENO_BASE_BUILD_FAILED" "fatal" \
      "Build finished but $bin is missing or not executable."
    exit "$EXIT_SPHENO_MAKE"
  fi

  smoke_test "$bin"

  local version
  version="$(probe_version "$bin" || echo "$SPHENO_VERSION")"
  # Source tree is retained (not deleted) — record both keys.
  record_both_keys "$bin" "$src_dir" "$version"
  log "SPheno v${version} installed at $bin (source retained at $src_dir)."
  printf '{"status":"installed","path":"%s","src_path":"%s","version":"%s"}\n' \
    "$bin" "$src_dir" "$version"
}

# ---------------------------------------------------------------------------
# usage / main
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<'EOF'
Usage: install.sh <command> [args]

Commands:
  detect              Print JSON state of existing SPheno install.
  use-path <path>     Accept a binary OR source-tree path; record both
                      spheno_path (binary) and spheno_src_path (source root).
  install [dir]       Full auto-install from source.
                      Default parent: ~/SPheno/SPheno-<version>
                      Override version: HEPPH_SPHENO_VERSION=x.y.z

Env overrides:
  HEPPH_SPHENO_VERSION   Pin a specific SPheno release (default: 4.0.5)
  XDG_CONFIG_HOME        Override config directory (test isolation)
  HEPPH_STATE_ROOT       Override per-model state root (test isolation)
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
    *)        usage ;;
  esac
}

main "$@"
