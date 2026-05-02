#!/usr/bin/env bash
# install.sh — _shared/installs/class entry point.
# Install CLASS v3.3.4 (git-clone-by-tag, make, pip install classy).
# No venv. classy installed into the active Python recorded in config["python"].
# No MontePython, no class_sz, no ExoCLASS fork — upstream class_public only.
#
# Usage:
#   install.sh detect
#   install.sh use-path <class_src_dir>
#   install.sh install [--force]
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="class-install"

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

CLASS_VERSION="$(_read_yaml CLASS_VERSION)"
CLASS_REPO="$(_read_yaml class_repo)"
CLASS_TAG="$(_read_yaml class_tag)"
CLASS_COMMIT="$(_read_yaml class_commit)"

SUBCOMMAND="${1:-}"
if [ -z "$SUBCOMMAND" ]; then
  err "Usage: install.sh detect|use-path|install [options]"
  exit 1
fi
shift || true

# ── Subcommand: detect ────────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "detect" ]; then
  exec bash "$SCRIPT_DIR/_probe.sh"
fi

# ── Subcommand: use-path ──────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "use-path" ]; then
  CLASS_DIR="${1:-}"

  if [ -z "$CLASS_DIR" ]; then
    emit_blocker "CLASS_PATH_INVALID" "fatal" \
      "use-path requires one argument: <class_src_dir>" \
      "Provide the path to a CLASS source/build directory containing the 'class' binary."
    exit "$EXIT_BAD_PATH"
  fi

  if [ ! -x "$CLASS_DIR/class" ]; then
    emit_blocker "CLASS_PATH_INVALID" "fatal" \
      "CLASS binary not found at $CLASS_DIR/class" \
      "Provide a valid CLASS build directory containing the 'class' executable."
    exit "$EXIT_BAD_PATH"
  fi

  log "Registering CLASS at $CLASS_DIR"

  # Determine classy version if importable
  CONFIG_PYTHON="$(config_get python)"
  PYTHON_BIN="${CONFIG_PYTHON:-python3}"
  CLASSY_VERSION=""
  CLASSY_VERSION="$("$PYTHON_BIN" -c "import classy; print(classy.__version__)" 2>/dev/null || true)"

  config_merge \
    "class_path" "$CLASS_DIR" \
    "class_version" "$CLASS_VERSION" \
    "class_commit" "$CLASS_COMMIT" \
    "classy_version" "${CLASSY_VERSION:-unknown}" \
    "class_openmp_enabled" "unknown" \
    "class_installed_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  log "use-path: configuration written successfully."
  python3 -c "import json; print(json.dumps({'status': 'configured', 'class_path': '${CLASS_DIR}'}))"
  exit 0
fi

# ── Subcommand: install ───────────────────────────────────────────────────────
if [ "$SUBCOMMAND" = "install" ]; then
  FORCE=0

  for arg in "$@"; do
    case "$arg" in
      --force)
        FORCE=1
        ;;
    esac
  done

  # ── Offline check (fast, before toolchain + disk) ────────────────────────────
  if [ "${HEPPH_NO_NETWORK:-0}" = "1" ]; then
    emit_blocker "CLASS_OFFLINE_NO_CACHE" "fatal" \
      "Network access disabled (HEPPH_NO_NETWORK=1) and no offline cache available." \
      "Provide an offline source cache via HEPPH_OFFLINE_CACHE_DIR or disable HEPPH_NO_NETWORK."
    exit "$EXIT_DOWNLOAD"
  fi

  # ── Toolchain checks ──────────────────────────────────────────────────────────
  TOOLCHAIN_MISSING=""
  for tool in cc make python3; do
    command -v "$tool" >/dev/null 2>&1 || TOOLCHAIN_MISSING="$TOOLCHAIN_MISSING $tool"
  done

  # Check Cython (required by classy)
  if ! python3 -c "import Cython" 2>/dev/null; then
    TOOLCHAIN_MISSING="$TOOLCHAIN_MISSING Cython"
  fi

  if [ -n "$TOOLCHAIN_MISSING" ]; then
    emit_blocker "CLASS_TOOLCHAIN_MISSING" "fatal" \
      "Required toolchain components missing:$TOOLCHAIN_MISSING" \
      "Install missing tools. On Debian/Ubuntu: apt install build-essential python3-dev cython3. On macOS: brew install gcc and pip install Cython."
    exit 1
  fi

  # ── Disk check ────────────────────────────────────────────────────────────────
  DISK_MIN_GB="$(_read_yaml disk_min_gb)"
  DISK_WARN_GB="$(_read_yaml disk_warn_gb)"
  check_disk "${DISK_MIN_GB:-1}" "${DISK_WARN_GB:-2}"

  # ── macOS libomp check (non-fatal, sets openmp flag) ─────────────────────────
  OPENMP_ENABLED="0"
  if [ "$(uname -s)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1 && brew list libomp >/dev/null 2>&1; then
      OPENMP_ENABLED="1"
      log "macOS: libomp found via Homebrew — OpenMP enabled."
    else
      OPENMP_ENABLED="0"
      warn "macOS: libomp not found (brew list libomp failed). Building without OpenMP (single-threaded)."
      warn "To enable OpenMP: brew install libomp"
    fi
  else
    # Linux: assume OpenMP available via gcc
    OPENMP_ENABLED="1"
  fi

  # ── Install directory ─────────────────────────────────────────────────────────
  INSTALL_ROOT="${HEPPH_INSTALL_ROOT:-$HOME}"
  CLASS_SRC="$INSTALL_ROOT/class_public/class-$CLASS_VERSION"

  # ── Clone CLASS ────────────────────────────────────────────────────────────────
  if [ ! -d "$CLASS_SRC" ] || [ "$FORCE" = "1" ]; then
    log "Cloning CLASS $CLASS_TAG from $CLASS_REPO"
    rm -rf "$CLASS_SRC"
    mkdir -p "$(dirname "$CLASS_SRC")"
    if ! git clone --depth 1 --branch "$CLASS_TAG" "$CLASS_REPO" "$CLASS_SRC" 2>&1; then
      emit_blocker "CLASS_DOWNLOAD_FAILED" "fatal" \
        "git clone failed for CLASS $CLASS_TAG from $CLASS_REPO" \
        "Check network access and GitHub availability at $CLASS_REPO"
      exit "$EXIT_DOWNLOAD"
    fi
  fi

  # ── Verify commit SHA ──────────────────────────────────────────────────────────
  local_sha=$(git -C "$CLASS_SRC" rev-parse HEAD 2>/dev/null || echo "unknown")
  if [ "$local_sha" != "$CLASS_COMMIT" ]; then
    warn "CLASS HEAD SHA mismatch: got $local_sha, expected $CLASS_COMMIT"
    warn "Proceeding — this may indicate the tag was re-tagged on GitHub."
  fi

  # ── Build CLASS ─────────────────────────────────────────────────────────────────
  log "Building CLASS $CLASS_VERSION (make -j)"
  BUILD_RC=0
  if ! make -C "$CLASS_SRC" -j "$(python3 -c 'import os; print(os.cpu_count() or 2)')" \
      2>&1 | tee "$CLASS_SRC/build.log" >&2; then
    BUILD_RC=$?
  fi

  if [ $BUILD_RC -ne 0 ]; then
    emit_blocker "CLASS_BUILD_FAILED" "fatal" \
      "make failed for CLASS $CLASS_VERSION (exit $BUILD_RC)" \
      "Check $CLASS_SRC/build.log for details. Ensure cc and make are available."
    exit "$EXIT_CLASS_BUILD"
  fi
  log "CLASS $CLASS_VERSION built successfully."

  # ── Install classy Python wheel ────────────────────────────────────────────────
  CONFIG_PYTHON="$(config_get python)"
  PYTHON_BIN="${CONFIG_PYTHON:-python3}"
  log "Installing classy Python module via $PYTHON_BIN"

  PIP_RC=0
  if ! "$PYTHON_BIN" -m pip install "$CLASS_SRC/python" 2>&1; then
    PIP_RC=$?
  fi

  if [ $PIP_RC -ne 0 ]; then
    emit_blocker "CLASSY_PIP_INSTALL_FAILED" "recoverable" \
      "pip install classy failed (exit $PIP_RC) — may be a write-permission issue" \
      "Retry with: $PYTHON_BIN -m pip install --user $CLASS_SRC/python"
    warn "Retrying with --user flag..."
    if ! "$PYTHON_BIN" -m pip install --user "$CLASS_SRC/python" 2>&1; then
      emit_blocker "CLASSY_PIP_INSTALL_FAILED" "fatal" \
        "pip install classy failed even with --user flag" \
        "Check pip installation and Python environment: $PYTHON_BIN"
      exit 1
    fi
  fi

  # ── Verify classy import ────────────────────────────────────────────────────────
  if ! "$PYTHON_BIN" -c "import classy" 2>/dev/null; then
    emit_blocker "CLASSY_IMPORT_FAILED" "fatal" \
      "import classy failed after pip install" \
      "Check PYTHONPATH and Python environment: $PYTHON_BIN -c 'import classy'"
    exit 1
  fi

  CLASSY_VERSION="$("$PYTHON_BIN" -c "import classy; print(classy.__version__)" 2>/dev/null || echo "unknown")"
  log "classy $CLASSY_VERSION installed successfully."

  # ── Smoke test ─────────────────────────────────────────────────────────────────
  log "Running smoke test..."
  bash "$SCRIPT_DIR/smoke_test.sh" "$CLASS_SRC" || {
    emit_blocker "CLASS_SMOKE_FAILED" "fatal" \
      "Smoke test failed after install." \
      "Check smoke test output. Try reinstalling with --force."
    exit "$EXIT_SMOKE"
  }

  # ── Write config ────────────────────────────────────────────────────────────────
  config_merge \
    "class_path" "$CLASS_SRC" \
    "class_version" "$CLASS_VERSION" \
    "class_commit" "$local_sha" \
    "classy_version" "$CLASSY_VERSION" \
    "class_openmp_enabled" "$OPENMP_ENABLED" \
    "class_installed_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  log "CLASS $CLASS_VERSION installed successfully."
  exit 0
fi

# ── Unknown subcommand ─────────────────────────────────────────────────────────
err "Unknown subcommand: $SUBCOMMAND"
err "Usage: install.sh detect|use-path|install [options]"
exit 1
