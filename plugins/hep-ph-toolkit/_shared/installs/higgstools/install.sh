#!/usr/bin/env bash
# install.sh — _shared/installs/higgstools entry point.
# Install HiggsBounds-5 + HiggsSignals-2 (legacy Fortran default)
# or the unified HiggsTools C++ library (opt-in via HEPPH_HIGGSTOOLS_BACKEND=unified).
#
# Usage:
#   install.sh detect
#   install.sh use-path <hb_dir> <hs_dir>
#   install.sh install [--backend=legacy|unified]
#   install.sh install --force
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="higgstools-install"

SKILL_ENV="$SCRIPT_DIR/skill_env.yaml"

# ── Parse skill_env.yaml (pure Python, no PyYAML dependency) ─────────────────
_read_yaml() {
  python3 - "$SKILL_ENV" "$1" <<'PY'
import sys, re
path, key = sys.argv[1], sys.argv[2]
with open(path) as f:
    for line in f:
        m = re.match(r'^' + re.escape(key) + r'\s*:\s*"?([^"#\n]+)"?', line)
        if m:
            print(m.group(1).strip())
            sys.exit(0)
print("")
PY
}

HB_VERSION="$(_read_yaml HB_VERSION)"
HS_VERSION="$(_read_yaml HS_VERSION)"
HB_REPO="$(_read_yaml hb_repo)"
HB_TAG="$(_read_yaml hb_tag)"
HB_COMMIT="$(_read_yaml hb_commit)"
HS_REPO="$(_read_yaml hs_repo)"
HS_TAG="$(_read_yaml hs_tag)"
HS_COMMIT="$(_read_yaml hs_commit)"

SUBCOMMAND="${1:-detect}"
shift || true

# ── Subcommand: detect ────────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "detect" ]; then
  exec bash "$SCRIPT_DIR/_probe.sh"
fi

# ── Subcommand: use-path ──────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "use-path" ]; then
  HB_DIR="${1:-}"
  HS_DIR="${2:-}"

  if [ -z "$HB_DIR" ] || [ -z "$HS_DIR" ]; then
    emit_blocker "HIGGSTOOLS_PATH_INVALID" "fatal" \
      "use-path requires two arguments: <hb_dir> <hs_dir>" \
      "Provide paths to the HiggsBounds and HiggsSignals build directories."
    exit "$EXIT_BAD_PATH"
  fi

  # Check HB binary
  if [ ! -x "$HB_DIR/bin/HiggsBounds" ] && [ ! -x "$HB_DIR/HiggsBounds" ]; then
    emit_blocker "HIGGSTOOLS_PATH_INVALID" "fatal" \
      "HiggsBounds binary not found in $HB_DIR" \
      "Provide a valid HiggsBounds build directory with the HiggsBounds executable."
    exit "$EXIT_BAD_PATH"
  fi

  # Check HS binary
  if [ ! -x "$HS_DIR/bin/HiggsSignals" ] && [ ! -x "$HS_DIR/HiggsSignals" ]; then
    emit_blocker "HIGGSTOOLS_PATH_INVALID" "fatal" \
      "HiggsSignals binary not found in $HS_DIR" \
      "Provide a valid HiggsSignals build directory with the HiggsSignals executable."
    exit "$EXIT_BAD_PATH"
  fi

  log "Registering HiggsBounds at $HB_DIR"
  log "Registering HiggsSignals at $HS_DIR"

  config_merge \
    "higgstools_backend" "legacy" \
    "higgsbounds_path" "$HB_DIR" \
    "higgsbounds_version" "$HB_VERSION" \
    "higgssignals_path" "$HS_DIR" \
    "higgssignals_version" "$HS_VERSION" \
    "higgstools_installed_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  log "use-path: configuration written successfully."
  python3 -c "import json; print(json.dumps({'status': 'configured', 'backend': 'legacy'}))"
  exit 0
fi

# ── Unified backend installer ────────────────────────────────────────────────
# Called after legacy install succeeds when BACKEND=unified.
# RECOVERABLE-BLOCKER on macOS arm64 build failure — never fatal.
_install_unified_backend() {
  # shellcheck disable=SC2034  # commit vars used for SHA verification
  local HT_VERSION ht_repo ht_tag ht_commit hbds_repo hbds_tag hbds_commit hsds_repo hsds_tag hsds_commit
  HT_VERSION="$(_read_yaml HT_VERSION)"
  ht_repo="$(_read_yaml ht_repo)"
  ht_tag="$(_read_yaml ht_tag)"
  ht_commit="$(_read_yaml ht_commit)"; : "${ht_commit}"  # used for SHA verification
  local HBDATASET_TAG HSDATASET_TAG
  HBDATASET_TAG="$(_read_yaml HBDATASET_TAG)"
  HSDATASET_TAG="$(_read_yaml HSDATASET_TAG)"
  hbds_repo="$(_read_yaml hbdataset_repo)"
  hbds_tag="$(_read_yaml hbdataset_tag)"
  hbds_commit="$(_read_yaml hbdataset_commit)"; : "${hbds_commit}"  # SHA verification
  hsds_repo="$(_read_yaml hsdataset_repo)"
  hsds_tag="$(_read_yaml hsdataset_tag)"
  hsds_commit="$(_read_yaml hsdataset_commit)"; : "${hsds_commit}"  # SHA verification

  local INSTALL_ROOT="${HEPPH_INSTALL_ROOT:-$HOME}"
  local HT_SRC="$INSTALL_ROOT/HiggsTools-$HT_VERSION"
  local HBDS_DIR="$INSTALL_ROOT/hbdataset-$HBDATASET_TAG"
  local HSDS_DIR="$INSTALL_ROOT/hsdataset-$HSDATASET_TAG"

  log "--- Unified backend install (opt-in) ---"

  # Toolchain check for unified
  local missing_tools=""
  for tool in cmake g++ python3; do
    command -v "$tool" >/dev/null 2>&1 || missing_tools="$missing_tools $tool"
  done
  if [ -n "$missing_tools" ]; then
    emit_blocker "HIGGSTOOLS_TOOLCHAIN_MISSING" "recoverable" \
      "Unified backend toolchain missing:$missing_tools" \
      "Install missing tools. Unified backend skipped; legacy backend is active."
    warn "Unified backend skipped due to missing tools:$missing_tools"
    return 0
  fi

  # Check cmake version >= 3.16
  local cmake_ver
  cmake_ver=$(cmake --version 2>/dev/null | head -1 | grep -Eo '[0-9]+\.[0-9]+' | head -1 || echo "0.0")
  local cmake_major cmake_minor
  cmake_major=$(echo "$cmake_ver" | cut -d. -f1)
  cmake_minor=$(echo "$cmake_ver" | cut -d. -f2)
  if [ "$cmake_major" -lt 3 ] || { [ "$cmake_major" -eq 3 ] && [ "$cmake_minor" -lt 16 ]; }; then
    emit_blocker "HIGGSTOOLS_TOOLCHAIN_MISSING" "recoverable" \
      "cmake >= 3.16 required for unified backend; found $cmake_ver" \
      "Upgrade cmake. Unified backend skipped."
    warn "Unified backend skipped: cmake $cmake_ver < 3.16"
    return 0
  fi

  # Check pybind11
  if ! python3 -c "import pybind11" 2>/dev/null; then
    emit_blocker "HIGGSTOOLS_TOOLCHAIN_MISSING" "recoverable" \
      "pybind11 Python package not found (required for unified backend)" \
      "Install pybind11: pip install pybind11. Unified backend skipped."
    warn "Unified backend skipped: pybind11 not found"
    return 0
  fi

  # Clone datasets
  log "Cloning hbdataset $hbds_tag..."
  if ! git clone --depth 1 --branch "$hbds_tag" "$hbds_repo" "$HBDS_DIR" 2>&1; then
    emit_blocker "HIGGSTOOLS_DOWNLOAD_FAILED" "recoverable" \
      "git clone failed for hbdataset $hbds_tag" \
      "Check network. Unified backend skipped; legacy backend is active."
    return 0
  fi

  log "Cloning hsdataset $hsds_tag..."
  if ! git clone --depth 1 --branch "$hsds_tag" "$hsds_repo" "$HSDS_DIR" 2>&1; then
    emit_blocker "HIGGSTOOLS_DOWNLOAD_FAILED" "recoverable" \
      "git clone failed for hsdataset $hsds_tag" \
      "Check network. Unified backend skipped; legacy backend is active."
    return 0
  fi

  # Clone HiggsTools
  log "Cloning HiggsTools $ht_tag..."
  if ! git clone --depth 1 --branch "$ht_tag" "$ht_repo" "$HT_SRC" 2>&1; then
    emit_blocker "HIGGSTOOLS_DOWNLOAD_FAILED" "recoverable" \
      "git clone failed for HiggsTools $ht_tag" \
      "Check network. Unified backend skipped; legacy backend is active."
    return 0
  fi

  # Build HiggsTools with Python bindings
  local HT_BUILD="$HT_SRC/build"
  mkdir -p "$HT_BUILD"

  # macOS arm64 graceful-skip on build failure
  local IS_MACOS_ARM64=0
  if [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    IS_MACOS_ARM64=1
  fi

  local build_rc=0
  cmake -S "$HT_SRC" -B "$HT_BUILD" \
    -DCMAKE_BUILD_TYPE=Release \
    -DHiggsTools_BUILD_PYTHON=ON \
    -DHiggsBoundsData_DIR="$HBDS_DIR" \
    -DHiggsSignalsData_DIR="$HSDS_DIR" \
    2>&1 | tee "$HT_BUILD/cmake.log" >&2 || build_rc=$?

  if [ $build_rc -ne 0 ]; then
    if [ $IS_MACOS_ARM64 -eq 1 ]; then
      emit_blocker "HIGGSTOOLS_BUILD_FAILED" "recoverable" \
        "HiggsTools unified backend build failed on macOS arm64 (known ABI issue)" \
        "Unified C++ backend is unverified on macOS arm64. Use legacy backend (default)."
    else
      emit_blocker "HIGGSTOOLS_BUILD_FAILED" "recoverable" \
        "HiggsTools unified backend CMake configure failed" \
        "Check $HT_BUILD/cmake.log. Unified backend skipped; legacy backend is active."
    fi
    warn "Unified backend build failed — legacy backend remains active."
    return 0
  fi

  cmake --build "$HT_BUILD" \
    -j "$(python3 -c 'import os; print(os.cpu_count() or 2)')" \
    2>&1 | tee "$HT_BUILD/build.log" >&2 || build_rc=$?

  if [ $build_rc -ne 0 ]; then
    if [ $IS_MACOS_ARM64 -eq 1 ]; then
      emit_blocker "HIGGSTOOLS_BUILD_FAILED" "recoverable" \
        "HiggsTools unified backend build failed on macOS arm64" \
        "Unified C++ backend is unverified on macOS arm64. Use legacy backend (default)."
    else
      emit_blocker "HIGGSTOOLS_BUILD_FAILED" "recoverable" \
        "HiggsTools unified backend cmake --build failed" \
        "Check $HT_BUILD/build.log. Unified backend skipped."
    fi
    warn "Unified backend build failed — legacy backend remains active."
    return 0
  fi

  # Python smoke test
  if ! python3 -c "import Higgs.bounds, Higgs.signals" 2>/dev/null; then
    emit_blocker "HIGGSTOOLS_BACKEND_UNAVAILABLE" "recoverable" \
      "HiggsTools Python module import failed after build" \
      "Check PYTHONPATH includes $HT_BUILD. Unified backend skipped."
    warn "Unified backend Python import failed — legacy backend remains active."
    return 0
  fi

  # Verify dataset SHAs
  local actual_hbds_sha actual_hsds_sha
  actual_hbds_sha=$(git -C "$HBDS_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")
  actual_hsds_sha=$(git -C "$HSDS_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")

  # Write unified config keys (additive — legacy keys already written).
  # higgstools_version pins the unified C++ HiggsTools release; legacy
  # higgsbounds_version + higgssignals_version remain the source of
  # truth for the legacy backend.
  config_merge \
    "higgstools_backend" "unified" \
    "higgstools_path" "$HT_BUILD" \
    "higgstools_version" "$HT_VERSION" \
    "hbdataset_path" "$HBDS_DIR" \
    "hbdataset_commit" "$actual_hbds_sha" \
    "hsdataset_path" "$HSDS_DIR" \
    "hsdataset_commit" "$actual_hsds_sha"

  log "Unified backend (HiggsTools $HT_VERSION) installed successfully."
}

# ── Subcommand: install ───────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "install" ]; then
  BACKEND="legacy"
  FORCE=0

  for arg in "$@"; do
    case "$arg" in
      --backend=unified)
        BACKEND="unified"
        ;;
      --backend=legacy)
        BACKEND="legacy"
        ;;
      --force)
        FORCE=1
        ;;
    esac
  done

  # Unified backend requires env-var gate
  if [ "$BACKEND" = "unified" ] && [ "${HEPPH_HIGGSTOOLS_BACKEND:-}" != "unified" ]; then
    emit_blocker "HIGGSTOOLS_BACKEND_UNAVAILABLE" "recoverable" \
      "--backend=unified requires HEPPH_HIGGSTOOLS_BACKEND=unified to be set" \
      "Set HEPPH_HIGGSTOOLS_BACKEND=unified in your environment to enable the unified C++ backend."
    exit 1
  fi

  # Toolchain check (fast, do before disk check)
  if ! command -v gfortran >/dev/null 2>&1; then
    emit_blocker "HIGGSTOOLS_TOOLCHAIN_MISSING" "fatal" \
      "gfortran not found in PATH." \
      "Install gfortran: on macOS run 'brew install gcc'; on Linux run 'apt install gfortran' or equivalent."
    exit "$EXIT_NO_GFORTRAN"
  fi

  if ! command -v cmake >/dev/null 2>&1; then
    emit_blocker "HIGGSTOOLS_TOOLCHAIN_MISSING" "fatal" \
      "cmake not found in PATH." \
      "Install cmake: 'brew install cmake' or 'apt install cmake'."
    exit "$EXIT_NO_CMAKE"
  fi

  # Offline check
  if [ "${HEPPH_NO_NETWORK:-0}" = "1" ]; then
    emit_blocker "HIGGSTOOLS_OFFLINE_NO_CACHE" "fatal" \
      "Network access disabled (HEPPH_NO_NETWORK=1) and no offline cache available." \
      "Provide an offline source cache via HEPPH_OFFLINE_CACHE_DIR or disable HEPPH_NO_NETWORK."
    exit "$EXIT_DOWNLOAD"
  fi

  # Disk check
  check_disk 3

  # Install directories
  INSTALL_ROOT="${HEPPH_INSTALL_ROOT:-$HOME}"
  HB_SRC="$INSTALL_ROOT/HiggsBounds-$HB_VERSION"
  HS_SRC="$INSTALL_ROOT/HiggsSignals-$HS_VERSION"
  HB_BUILD="$HB_SRC/build"
  HS_BUILD="$HS_SRC/build"

  # ── Clone HiggsBounds ──────────────────────────────────────────────────────
  if [ ! -d "$HB_SRC" ] || [ "$FORCE" = "1" ]; then
    log "Cloning HiggsBounds $HB_TAG from $HB_REPO"
    rm -rf "$HB_SRC"
    if ! git clone --depth 1 --branch "$HB_TAG" "$HB_REPO" "$HB_SRC" 2>&1; then
      emit_blocker "HIGGSTOOLS_DOWNLOAD_FAILED" "fatal" \
        "git clone failed for HiggsBounds $HB_TAG" \
        "Check network access and GitLab availability at $HB_REPO"
      exit "$EXIT_DOWNLOAD"
    fi
  fi

  # Verify commit SHA
  local_hb_sha=$(git -C "$HB_SRC" rev-parse HEAD 2>/dev/null || echo "unknown")
  if [ "$local_hb_sha" != "$HB_COMMIT" ]; then
    warn "HiggsBounds HEAD SHA mismatch: got $local_hb_sha, expected $HB_COMMIT"
    warn "Proceeding — this may indicate the tag was re-tagged on GitLab."
  fi

  # ── Build HiggsBounds ──────────────────────────────────────────────────────
  log "Building HiggsBounds $HB_VERSION"
  mkdir -p "$HB_BUILD"
  if ! cmake -S "$HB_SRC" -B "$HB_BUILD" -DCMAKE_BUILD_TYPE=Release 2>&1 | tee "$HB_BUILD/cmake.log" >&2; then
    emit_blocker "HIGGSTOOLS_BUILD_FAILED" "fatal" \
      "CMake configure failed for HiggsBounds $HB_VERSION" \
      "Check $HB_BUILD/cmake.log for details."
    exit "$EXIT_NO_CMAKE"
  fi
  if ! cmake --build "$HB_BUILD" -j "$(python3 -c 'import os; print(os.cpu_count() or 2)')" 2>&1 | tee "$HB_BUILD/build.log" >&2; then
    emit_blocker "HIGGSTOOLS_BUILD_FAILED" "fatal" \
      "cmake --build failed for HiggsBounds $HB_VERSION" \
      "Check $HB_BUILD/build.log for details."
    exit 1
  fi
  log "HiggsBounds $HB_VERSION built successfully."

  # ── Clone HiggsSignals ─────────────────────────────────────────────────────
  if [ ! -d "$HS_SRC" ] || [ "$FORCE" = "1" ]; then
    log "Cloning HiggsSignals $HS_TAG from $HS_REPO"
    rm -rf "$HS_SRC"
    if ! git clone --depth 1 --branch "$HS_TAG" "$HS_REPO" "$HS_SRC" 2>&1; then
      emit_blocker "HIGGSTOOLS_DOWNLOAD_FAILED" "fatal" \
        "git clone failed for HiggsSignals $HS_TAG" \
        "Check network access and GitLab availability at $HS_REPO"
      exit "$EXIT_DOWNLOAD"
    fi
  fi

  # Verify commit SHA
  local_hs_sha=$(git -C "$HS_SRC" rev-parse HEAD 2>/dev/null || echo "unknown")
  if [ "$local_hs_sha" != "$HS_COMMIT" ]; then
    warn "HiggsSignals HEAD SHA mismatch: got $local_hs_sha, expected $HS_COMMIT"
    warn "Proceeding — this may indicate the tag was re-tagged on GitLab."
  fi

  # ── Build HiggsSignals ─────────────────────────────────────────────────────
  log "Building HiggsSignals $HS_VERSION"
  mkdir -p "$HS_BUILD"
  if ! cmake -S "$HS_SRC" -B "$HS_BUILD" \
      -DCMAKE_BUILD_TYPE=Release \
      -DHiggsBounds_DIR="$HB_BUILD" \
      2>&1 | tee "$HS_BUILD/cmake.log" >&2; then
    emit_blocker "HIGGSTOOLS_BUILD_FAILED" "fatal" \
      "CMake configure failed for HiggsSignals $HS_VERSION" \
      "Check $HS_BUILD/cmake.log for details. Ensure HiggsBounds is built at $HB_BUILD."
    exit "$EXIT_NO_CMAKE"
  fi
  if ! cmake --build "$HS_BUILD" -j "$(python3 -c 'import os; print(os.cpu_count() or 2)')" 2>&1 | tee "$HS_BUILD/build.log" >&2; then
    emit_blocker "HIGGSTOOLS_BUILD_FAILED" "fatal" \
      "cmake --build failed for HiggsSignals $HS_VERSION" \
      "Check $HS_BUILD/build.log for details."
    exit 1
  fi
  log "HiggsSignals $HS_VERSION built successfully."

  # ── Smoke test + SM reference cache ────────────────────────────────────────
  log "Running smoke test and caching SM chi2 reference..."
  bash "$SCRIPT_DIR/smoke_test.sh" "$HB_BUILD" "$HS_BUILD" || {
    emit_blocker "HIGGSTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "Smoke test failed after install." \
      "Check smoke test output. Try reinstalling with --force."
    exit "$EXIT_SMOKE"
  }

  # ── Write config (legacy) ────────────────────────────────────────────────────
  config_merge \
    "higgstools_backend" "legacy" \
    "higgsbounds_path" "$HB_BUILD" \
    "higgsbounds_version" "$HB_VERSION" \
    "higgssignals_path" "$HS_BUILD" \
    "higgssignals_version" "$HS_VERSION" \
    "higgstools_installed_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  log "HiggsBounds $HB_VERSION + HiggsSignals $HS_VERSION installed successfully."

  # ── Unified backend opt-in ────────────────────────────────────────────────────
  if [ "$BACKEND" = "unified" ]; then
    _install_unified_backend
  fi

  exit 0
fi

# ── Unknown subcommand ─────────────────────────────────────────────────────────
err "Unknown subcommand: $SUBCOMMAND"
err "Usage: install.sh detect|use-path|install [options]"
exit 1
