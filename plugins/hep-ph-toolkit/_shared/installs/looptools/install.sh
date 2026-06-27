#!/usr/bin/env bash
# install.sh — _shared/installs/looptools entry point.
#
# Subcommands:
#   detect                  Print JSON state of existing LoopTools install.
#   use-path <prefix>       Accept an existing install prefix; validate and record.
#   install [prefix]        Full auto-install from feynarts.de.
#                           Default: $HOME/LoopTools/LoopTools-<version>
#   validate                Re-run light smoke test on the configured prefix.
#
# Version: HEPPH_LOOPTOOLS_VERSION (default 2.16).
# Compiler pin: FC=/path/to/gfortran-XX (records full version in config).
#
# Blocker codes (see SKILL.md):
#   GFORTRAN_ABSENT (25), CC_ABSENT (25), LOOPTOOLS_DOWNLOAD_FAILED (12),
#   LOOPTOOLS_CONFIGURE_FAILED (11), LOOPTOOLS_BUILD_FAILED (13),
#   LOOPTOOLS_SMOKE_TEST_FAILED (15), LOOPTOOLS_PATH_INVALID (16).
set -euo pipefail

_LOG_TAG="install_looptools"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# ---------------------------------------------------------------------------
# Local exit codes (match SKILL.md blocker table). Shared codes from
# _common.sh: EXIT_DOWNLOAD=12, EXIT_SMOKE=15, EXIT_BAD_PATH=16.
# Local codes:
# ---------------------------------------------------------------------------
EXIT_LT_CONFIGURE=11
EXIT_LT_BUILD=13
EXIT_LT_GFORTRAN=25

# ---------------------------------------------------------------------------
# Version / URL configuration.
# ---------------------------------------------------------------------------
LOOPTOOLS_VERSION="${HEPPH_LOOPTOOLS_VERSION:-2.16}"
LOOPTOOLS_URL="https://feynarts.de/looptools/LoopTools-${LOOPTOOLS_VERSION}.tar.gz"
LOOPTOOLS_SHA256="TODO"  # verify_checksum warns-not-aborts; update pre-v1

TARBALL="/tmp/looptools-${LOOPTOOLS_VERSION}.tar.gz"
BUILD_LOG="/tmp/looptools_build.log"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Parse version from an existing prefix.
# Strategy 1: source tree name inside prefix (LoopTools-2.16/).
# Strategy 2: strings from libooptools.a (unreliable, skipped).
# Strategy 3: fall back to HEPPH_LOOPTOOLS_VERSION.
probe_version() {
  local prefix="$1"
  [ -d "$prefix" ] || return 1
  # Walk up looking for an ancestor named LoopTools-x.y.
  local dir="$prefix"
  local v=""
  for _i in 1 2 3; do
    v="$(basename "$dir" | grep -Eo '[0-9]+\.[0-9]+' | head -n1 || true)"
    if [ -n "$v" ]; then echo "$v"; return 0; fi
    dir="$(dirname "$dir")"
    [ "$dir" = "/" ] && break
  done
  echo "$LOOPTOOLS_VERSION"
}

# Check whether a prefix looks like a LoopTools install (has libooptools.a).
is_valid_prefix() {
  local p="$1"
  [ -f "$p/lib/libooptools.a" ]
}

# Scan well-known locations for an existing LoopTools install prefix.
scan_candidates() {
  local roots=(
    "$HOME/LoopTools"
    "$HOME/software/LoopTools"
    "$HOME/looptools"
    "/usr/local"
    "/opt/LoopTools"
  )
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    # Direct hit: $root itself is a prefix.
    if is_valid_prefix "$root"; then echo "$root"; return 0; fi
    # Versioned subdirs: $root/LoopTools-x.y.
    local hit
    hit="$(find "$root" -maxdepth 3 -type f -name libooptools.a 2>/dev/null | head -n1 || true)"
    if [ -n "$hit" ]; then
      local prefix
      prefix="$(cd "$(dirname "$hit")/.." && pwd)"
      echo "$prefix"
      return 0
    fi
  done
  return 1
}

# Record all config keys for a validated install.
# Usage: record_install <prefix> <src_path> <version> <gfortran_version> <gfortran_path> <mathlink_available>
record_install() {
  local prefix="$1"
  local src="$2"
  local version="$3"
  local gf_version="$4"
  local gf_path="$5"
  local mathlink="$6"
  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge \
    looptools_path "$prefix" \
    looptools_src_path "$src" \
    looptools_version "$version" \
    looptools_gfortran_version "$gf_version" \
    looptools_gfortran_path "$gf_path" \
    looptools_mathlink_available "$mathlink" \
    looptools_installed_at "$installed_at"
  log "Recorded looptools_path=$prefix version=$version gfortran=$gf_path"
}

# ---------------------------------------------------------------------------
# Locate Wolfram's MathLink template compiler `mcc` so the optional
# Mathematica/Wolfram frontend (`bin/LoopTools`) can be built.
#
# Wolfram Engine ships NO kernel binary (`math`/`MathKernel`/`WolframKernel`)
# on PATH and NO `mcc` on PATH — only `wolframscript`. So we cannot rely on
# `command -v mcc`; we must dig `mcc` out of the app bundle / install tree.
#
# Returns (on stdout) an `mcc` path that is SAFE TO INVOKE — i.e. contains no
# spaces in any directory component. `mcc` is an old /bin/sh script that uses
# its own dir ($0) unquoted to find `mprep`, headers and `libMLi*.a`; a path
# like ".../Wolfram Engine.app/..." breaks it ("/Applications/Wolfram: No such
# file or directory"). When the real path has spaces we expose its
# CompilerAdditions dir through a space-free symlink and return the mcc inside.
#
# Echoes nothing and returns 1 if no usable mcc is found.
locate_mcc() {
  # Respect an explicit override.
  if [ -n "${MCC:-}" ] && [ -x "${MCC:-}" ]; then printf '%s\n' "$MCC"; return 0; fi
  if command -v mcc >/dev/null 2>&1; then command -v mcc; return 0; fi

  # Platform dir inside SystemFiles/Links/MathLink/DeveloperKit/<platform>/.
  local uname_s uname_m platform
  uname_s="$(uname -s)"; uname_m="$(uname -m)"
  case "$uname_s" in
    Darwin) case "$uname_m" in
              arm64)  platform="MacOSX-ARM64" ;;
              x86_64) platform="MacOSX-x86-64" ;;
              *)      platform="MacOSX-ARM64" ;;
            esac ;;
    Linux)  case "$uname_m" in
              aarch64|arm64) platform="Linux-ARM64" ;;
              *)             platform="Linux-x86-64" ;;
            esac ;;
    *) platform="" ;;
  esac

  local found=""
  # Fast path on macOS: Spotlight.
  if command -v mdfind >/dev/null 2>&1; then
    found="$(mdfind -name mcc 2>/dev/null \
              | grep -E "CompilerAdditions/mcc$" \
              | grep -E "(MathLink|WSTP)/DeveloperKit/${platform}/" \
              | head -n1)"
  fi
  # Fallback: scan well-known app/install roots.
  if [ -z "$found" ]; then
    local roots=(
      "/Applications/Wolfram Engine.app"
      "/Applications/Mathematica.app"
      "/Applications/Wolfram.app"
      "/Applications/Wolfram Desktop.app"
      "$HOME/Wolfram" "/opt/Wolfram" "/usr/local/Wolfram"
      "/usr/local/Mathematica" "/opt/mathematica"
    )
    local r
    for r in "${roots[@]}"; do
      [ -d "$r" ] || continue
      found="$(find "$r" -type f -path "*${platform}/CompilerAdditions/mcc" 2>/dev/null | head -n1)"
      [ -n "$found" ] && break
    done
  fi
  [ -n "$found" ] || return 1

  # Make the path space-free if necessary (see header).
  case "$found" in
    *" "*)
      local ca link
      ca="$(dirname "$found")"                 # .../CompilerAdditions
      link="${TMPDIR:-/tmp}/hephaestus-wolfram-mldk-${platform}"
      ln -sfn "$ca" "$link" 2>/dev/null || return 1
      found="$link/mcc"
      ;;
  esac
  [ -x "$found" ] && printf '%s\n' "$found"
}

# Emit a {"status":"configured", ...} line from a prefix in config.
emit_configured_json() {
  local prefix="$1"
  local version gf_version
  version="$(config_get looptools_version)"
  [ -n "$version" ] || version="$(probe_version "$prefix")"
  gf_version="$(config_get looptools_gfortran_version)"
  printf '{"status":"configured","path":"%s","version":"%s","gfortran_version":"%s"}\n' \
    "$prefix" "$version" "$gf_version"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local prefix
  prefix="$(config_get looptools_path)"

  if [ -n "$prefix" ] && is_valid_prefix "$prefix"; then
    emit_configured_json "$prefix"
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
# cmd_validate
# ---------------------------------------------------------------------------
cmd_validate() {
  local prefix
  prefix="$(config_get looptools_path)"
  if [ -z "$prefix" ]; then
    emit_blocker "LOOPTOOLS_PATH_INVALID" "fatal" \
      "No looptools_path in config; cannot validate." \
      "Run 'install.sh install' or 'install.sh use-path <prefix>' first."
    exit "$EXIT_BAD_PATH"
  fi
  bash "$SCRIPT_DIR/probe_looptools.sh" "$prefix"
}

# ---------------------------------------------------------------------------
# cmd_use_path
# ---------------------------------------------------------------------------
cmd_use_path() {
  local path="${1:-}"
  [ -n "$path" ] || {
    emit_blocker "LOOPTOOLS_PATH_INVALID" "fatal" \
      "use-path requires a prefix argument."
    exit "$EXIT_BAD_PATH"
  }
  path="${path/#\~/$HOME}"

  if [ ! -d "$path" ]; then
    emit_blocker "LOOPTOOLS_PATH_INVALID" "fatal" \
      "Prefix $path is not a directory." \
      "Provide the absolute path to a directory containing lib/libooptools.a."
    exit "$EXIT_BAD_PATH"
  fi

  if ! is_valid_prefix "$path"; then
    emit_blocker "LOOPTOOLS_PATH_INVALID" "fatal" \
      "Prefix $path does not contain lib/libooptools.a." \
      "Provide the prefix used for --prefix=, not the source root."
    exit "$EXIT_BAD_PATH"
  fi

  # Light smoke test.
  bash "$SCRIPT_DIR/probe_looptools.sh" "$path" >/dev/null

  # Detect gfortran (required so we can record its version for coherence).
  # shellcheck source=check_gfortran.sh
  . "$SCRIPT_DIR/check_gfortran.sh"
  check_gfortran_present
  local gf_version="$HEPPH_LOOPTOOLS_GFORTRAN_VERSION"
  local gf_path="$HEPPH_LOOPTOOLS_GFORTRAN_PATH"

  # Derive src tree heuristically (parent of prefix if named LoopTools-x.y).
  local src="$path"
  if [ ! -f "$path/Makefile" ] && [ -f "$(dirname "$path")/LoopTools-${LOOPTOOLS_VERSION}/Makefile" ]; then
    src="$(dirname "$path")/LoopTools-${LOOPTOOLS_VERSION}"
  fi

  local mathlink="false"
  [ -x "$path/bin/LoopTools" ] && mathlink="true"

  local version
  version="$(probe_version "$path")"

  record_install "$path" "$src" "$version" "$gf_version" "$gf_path" "$mathlink"
  printf '{"status":"configured","path":"%s","version":"%s","gfortran_version":"%s","mathlink_available":%s}\n' \
    "$path" "$version" "$gf_version" "$mathlink"
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  local install_root="${1:-$HOME/LoopTools}"
  install_root="${install_root/#\~/$HOME}"

  # Precondition: gfortran (records version + path into env).
  # shellcheck source=check_gfortran.sh
  . "$SCRIPT_DIR/check_gfortran.sh"
  check_gfortran_present
  check_cc_present
  local gf_version="$HEPPH_LOOPTOOLS_GFORTRAN_VERSION"
  local gf_path="$HEPPH_LOOPTOOLS_GFORTRAN_PATH"

  # Idempotency: if already installed at the pinned version, exit early.
  local existing_prefix existing_version
  existing_prefix="$(config_get looptools_path)"
  if [ -n "$existing_prefix" ] && is_valid_prefix "$existing_prefix"; then
    existing_version="$(config_get looptools_version)"
    if [ "$existing_version" = "$LOOPTOOLS_VERSION" ]; then
      log "LoopTools $LOOPTOOLS_VERSION already installed at $existing_prefix; skipping."
      emit_configured_json "$existing_prefix"
      return 0
    fi
    log "Existing LoopTools at $existing_prefix (v$existing_version) differs from pin ($LOOPTOOLS_VERSION); installing fresh."
  fi

  check_disk 1 2
  mkdir -p "$install_root"

  # Download.
  log "Downloading LoopTools ${LOOPTOOLS_VERSION} from $LOOPTOOLS_URL ..."
  if ! download_with_retry "$LOOPTOOLS_URL" "$TARBALL"; then
    emit_blocker "LOOPTOOLS_DOWNLOAD_FAILED" "fatal" \
      "Failed to download LoopTools ${LOOPTOOLS_VERSION} from $LOOPTOOLS_URL after 2 attempts." \
      "Check your internet connection. URL: $LOOPTOOLS_URL"
    exit "$EXIT_DOWNLOAD"
  fi

  verify_checksum "$TARBALL" "$LOOPTOOLS_SHA256"

  log "Extracting LoopTools to $install_root ..."
  if ! tar -xzf "$TARBALL" -C "$install_root"; then
    emit_blocker "LOOPTOOLS_DOWNLOAD_FAILED" "fatal" \
      "Extraction of LoopTools tarball to $install_root failed."
    exit "$EXIT_EXTRACT"
  fi

  local extracted_name
  extracted_name="$(tar -tzf "$TARBALL" 2>/dev/null | head -n1 | cut -d/ -f1)"
  local src_dir="$install_root/$extracted_name"

  if [ ! -d "$src_dir" ]; then
    emit_blocker "LOOPTOOLS_DOWNLOAD_FAILED" "fatal" \
      "Expected source directory $src_dir not found after extraction."
    exit "$EXIT_EXTRACT"
  fi

  rm -f "$TARBALL"

  # Prefix = same as source dir (LoopTools installs in-tree by default when
  # --prefix is set to $src_dir).
  local prefix="$src_dir"

  # Detect the Wolfram MathLink template compiler `mcc` so we can build the
  # optional Mathematica frontend (`bin/LoopTools`). Note: Wolfram Engine puts
  # NO kernel binary on PATH, so the historical `command -v math` check below
  # always failed under Wolfram Engine and silently disabled MathLink. We now
  # search the app bundle directly (see locate_mcc). Override with MCC=/path,
  # or force library-only with HEPPH_LOOPTOOLS_NO_MATHLINK=1.
  local want_mathlink="no"
  local mathlink_available="false"
  local mcc_path=""
  if [ "${HEPPH_LOOPTOOLS_NO_MATHLINK:-0}" != "1" ]; then
    if mcc_path="$(locate_mcc)" && [ -n "$mcc_path" ]; then
      want_mathlink="yes"
      log "Found Wolfram mcc at $mcc_path; will build MathLink frontend (bin/LoopTools)."
    else
      log "No Wolfram mcc found (no Mathematica/Wolfram Engine dev kit); building library only (make lib)."
    fi
  fi

  # Configure. Pass MCC so configure's MathLink probe (which calls \${MCC:-mcc})
  # succeeds and sets ML=1 in the generated makefile.
  log "Configuring LoopTools in $src_dir (FC=$gf_path) ..."
  : > "$BUILD_LOG"
  if ! (
    cd "$src_dir"
    FC="$gf_path" ${mcc_path:+MCC="$mcc_path"} ./configure --prefix="$prefix"
  ) >>"$BUILD_LOG" 2>&1; then
    local tail_txt
    tail_txt="$(tail -n 30 "$BUILD_LOG" 2>/dev/null || echo "")"
    emit_blocker "LOOPTOOLS_CONFIGURE_FAILED" "fatal" \
      "LoopTools ./configure failed. Build log tail: $tail_txt" \
      "See full log at $BUILD_LOG."
    exit "$EXIT_LT_CONFIGURE"
  fi

  # Build. With mcc present use 'make all' (library + lt + LoopTools frontend);
  # otherwise 'make lib' (core static library only). We pass MCC on the make
  # command line too (overrides the makefile value) for robustness.
  #
  # Graceful degradation: the MathLink frontend is OPTIONAL. If 'make all'
  # fails (e.g. a broken/incompatible mcc toolchain on some other machine), we
  # must NOT sink the core libooptools.a deliverable — retry 'make lib' and, if
  # the core library builds, downgrade to library-only (mathlink_available stays
  # "false") and continue. Only a failed CORE 'make lib' is a fatal blocker.
  local make_target="all"
  [ "$want_mathlink" = "no" ] && make_target="lib"
  log "Compiling LoopTools (make $make_target) ..."
  if ! ( cd "$src_dir" && FC="$gf_path" make "$make_target" ${mcc_path:+MCC="$mcc_path"} ) >>"$BUILD_LOG" 2>&1; then
    if [ "$make_target" = "all" ]; then
      local frontend_tail
      frontend_tail="$(tail -n 15 "$BUILD_LOG" 2>/dev/null || echo "")"
      log "WARNING: 'make all' (MathLink frontend) failed; retrying core 'make lib' only. Frontend log tail: $frontend_tail"
      want_mathlink="no"
      make_target="lib"
      if ! ( cd "$src_dir" && FC="$gf_path" make lib ) >>"$BUILD_LOG" 2>&1; then
        local tail_txt
        tail_txt="$(tail -n 40 "$BUILD_LOG" 2>/dev/null || echo "")"
        emit_blocker "LOOPTOOLS_BUILD_FAILED" "fatal" \
          "LoopTools 'make lib' (core library) failed. Build log tail: $tail_txt" \
          "See full log at $BUILD_LOG. Common causes: gfortran version skew, missing libstdc++."
        exit "$EXIT_LT_BUILD"
      fi
      log "Core libooptools.a built; continuing without the MathLink frontend (mathlink_available=false)."
    else
      local tail_txt
      tail_txt="$(tail -n 40 "$BUILD_LOG" 2>/dev/null || echo "")"
      emit_blocker "LOOPTOOLS_BUILD_FAILED" "fatal" \
        "LoopTools 'make $make_target' failed. Build log tail: $tail_txt" \
        "See full log at $BUILD_LOG. Common causes: gfortran version skew, missing libstdc++."
      exit "$EXIT_LT_BUILD"
    fi
  fi

  # make install (places lib/, bin/, include/ under --prefix).
  log "Installing LoopTools to $prefix ..."
  if ! ( cd "$src_dir" && FC="$gf_path" make install ) >>"$BUILD_LOG" 2>&1; then
    local tail_txt
    tail_txt="$(tail -n 40 "$BUILD_LOG" 2>/dev/null || echo "")"
    emit_blocker "LOOPTOOLS_BUILD_FAILED" "fatal" \
      "LoopTools 'make install' failed. Build log tail: $tail_txt" \
      "See full log at $BUILD_LOG."
    exit "$EXIT_LT_BUILD"
  fi

  log "LoopTools compiled successfully."

  if ! is_valid_prefix "$prefix"; then
    emit_blocker "LOOPTOOLS_BUILD_FAILED" "fatal" \
      "Build finished but $prefix/lib/libooptools.a is missing." \
      "See full log at $BUILD_LOG."
    exit "$EXIT_LT_BUILD"
  fi

  # Smoke test (light by default; full if HEPPH_LOOPTOOLS_FULL_SMOKE=1).
  if [ "${HEPPH_LOOPTOOLS_FULL_SMOKE:-0}" = "1" ]; then
    bash "$SCRIPT_DIR/probe_looptools.sh" --full-smoke "$prefix" >/dev/null
  else
    bash "$SCRIPT_DIR/probe_looptools.sh" "$prefix" >/dev/null
  fi

  # Record MathLink availability as "true" ONLY if the frontend binary both
  # exists and genuinely evaluates an integral. Use ToExpression so B0/A0 bind
  # to the LoopTools` context (bare symbols would shadow as Global` at parse
  # time). A finite number = pass. If wolframscript is unavailable we fall back
  # to a presence check (the binary built, but could not be verified here).
  if [ -x "$prefix/bin/LoopTools" ]; then
    if command -v wolframscript >/dev/null 2>&1; then
      local ml_out
      ml_out="$(wolframscript -code \
        'link = Install["'"$prefix"'/bin/LoopTools"]; r = ToExpression["B0[0, 100^2, 100^2]"]; Print["RESULT:", NumberQ[r], ":", r]; Uninstall[link]' \
        2>/dev/null || true)"
      if printf '%s' "$ml_out" | grep -q "RESULT:True:"; then
        mathlink_available="true"
        config_merge looptools_mathlink_path "$prefix/bin/LoopTools" \
          looptools_mathlink_verified "true"
        log "MathLink frontend verified: B0(0,100^2,100^2) returned a finite number."
      else
        log "WARNING: bin/LoopTools built but B0 verification did not return a number; recording mathlink_available=false."
      fi
    else
      # Binary present but could not run the B0 check here (no wolframscript on
      # PATH). Record availability on presence, but flag it as unverified so a
      # downstream caller knows the runtime check was skipped, not passed.
      mathlink_available="true"
      config_merge looptools_mathlink_path "$prefix/bin/LoopTools" \
        looptools_mathlink_verified "unverified"
      log "bin/LoopTools present; wolframscript not on PATH, skipped runtime verification (looptools_mathlink_verified=unverified)."
    fi
  fi

  record_install "$prefix" "$src_dir" "$LOOPTOOLS_VERSION" "$gf_version" "$gf_path" "$mathlink_available"
  log "LoopTools v${LOOPTOOLS_VERSION} installed at $prefix (gfortran=$gf_path)."
  printf '{"status":"installed","path":"%s","version":"%s","gfortran_version":"%s","mathlink_available":%s}\n' \
    "$prefix" "$LOOPTOOLS_VERSION" "$gf_version" "$mathlink_available"
}

# ---------------------------------------------------------------------------
# usage / main
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<'EOF'
Usage: install.sh <command> [args]

Commands:
  detect              Print JSON state of existing LoopTools install.
  use-path <prefix>   Accept a prefix directory containing lib/libooptools.a.
  install [dir]       Full auto-install from feynarts.de.
                      Default parent: ~/LoopTools
                      Override version: HEPPH_LOOPTOOLS_VERSION=x.y
                      Pin compiler:    FC=/path/to/gfortran-XX
  validate            Re-run the light smoke test on the configured prefix.

Env overrides:
  HEPPH_LOOPTOOLS_VERSION     Pin a specific LoopTools release (default: 2.16)
  HEPPH_LOOPTOOLS_FULL_SMOKE  Set to 1 to require B0 numerical test on install
  FC                          Pin a specific gfortran binary (recorded in config)
  XDG_CONFIG_HOME             Override config directory (test isolation)
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
    validate) cmd_validate ;;
    *)        usage ;;
  esac
}

main "$@"
