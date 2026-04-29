#!/usr/bin/env bash
# install_impl.sh — bundled micrOMEGAs install.
#
# Usage: install_impl.sh [parent_dir] [--full-smoke]
#   parent_dir defaults to $HOME/micrOMEGAs
#
# Stages:
#   0. check_toolchain (CC_ABSENT / GFORTRAN_ABSENT / GNU_MAKE_ABSENT)
#      — optional X11 headers warn-only
#   1. check_disk 3 5
#   2. download_with_retry (HEPPH_NO_NETWORK-aware; LAPTh → Zenodo fallback)
#   3. verify_checksum (TODO → warn)
#   4. extract to parent_dir/micromegas_<ver>/
#   5. source _macos_env.sh (macOS only)
#   6. make -j<nproc> under netguard PATH sandbox
#      — LAPACK_ABSENT signature detection on non-zero exit
#   7. _smoke.sh  (optional --full-smoke flag runs MSSM example)
#   8. PPPC tables check
#   9. config_merge (5 keys)
#
# Local exit codes:
#   30 — CALCHEP_PATH_INVALID
#   31 — MICROMEGAS_MACOS_SDK_MISMATCH
#   32 — MICROMEGAS_SMOKE_TEST_FAILED
#   33 — MICROMEGAS_BUILD_NEEDS_NETWORK
#   34 — PPPC_TABLES_MISSING
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"
. "$SCRIPT_DIR/_blocker.sh"
. "$SCRIPT_DIR/_netguard.sh"
# shellcheck source=check_toolchain.sh
. "$SCRIPT_DIR/check_toolchain.sh"

_LOG_TAG="micromegas-install"

EXIT_CALCHEP_BAD=30
EXIT_MACOS_SDK=31
EXIT_MICROMEGAS_SMOKE=32
EXIT_BUILD_NET=33
EXIT_PPPC_MISSING=34

MICROMEGAS_VERSION="${HEPPH_MICROMEGAS_VERSION:-6.0.5}"
MICROMEGAS_URL="https://lapth.cnrs.fr/micromegas/downloadarea/micromegas_${MICROMEGAS_VERSION}.tgz"
# Zenodo mirror — last-resort fallback when LAPTh is unreachable. Only
# exercised when HEPPH_NO_NETWORK is unset (offline mode goes through the
# cache). Mirror pin is independent of MICROMEGAS_VERSION; it is the latest
# version known to be archived on Zenodo at consolidation time (v1).
MICROMEGAS_ZENODO_FALLBACK_VERSION="6.1.15"
MICROMEGAS_ZENODO_FALLBACK_URL="https://zenodo.org/records/13376690/files/micromegas_6.1.15.tgz"
MICROMEGAS_SHA256="TODO"

# Parse flags. Positional: parent_dir. Flag: --full-smoke.
FULL_SMOKE=0
positional=()
for arg in "$@"; do
  case "$arg" in
    --full-smoke) FULL_SMOKE=1 ;;
    *)            positional+=("$arg") ;;
  esac
done

parent_dir="${positional[0]:-$HOME/micrOMEGAs}"
install_dir="$parent_dir/micromegas_${MICROMEGAS_VERSION}"

# ── Stage 1: disk check ───────────────────────────────────────────────────────
if [ "${HEPPH_SKIP_DISK_CHECK:-0}" != "1" ]; then
  check_disk 3 5
fi

# ── Stage 2: download ─────────────────────────────────────────────────────────
tarball_name="micromegas_${MICROMEGAS_VERSION}.tgz"
tarball_dest="/tmp/${tarball_name}"

log "Downloading micrOMEGAs ${MICROMEGAS_VERSION}..."

# Pre-check: if HEPPH_NO_NETWORK=1, check cache before calling download_with_retry.
# download_with_retry calls exit() on cache miss which would exit our process.
# We do the check ourselves to emit the micromegas-specific blocker.
if [ "${HEPPH_NO_NETWORK:-0}" = "1" ]; then
  cache_dir="${HEPPH_OFFLINE_CACHE_DIR:-}"
  if [ -z "$cache_dir" ]; then
    emit_blocker MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY fatal \
      "HEPPH_NO_NETWORK=1 is set but HEPPH_OFFLINE_CACHE_DIR is not defined." \
      "Set HEPPH_OFFLINE_CACHE_DIR to a directory containing ${tarball_name}." \
      "{\"url\":\"${MICROMEGAS_URL}\"}"
    exit $EXIT_DOWNLOAD
  fi
  if [ ! -r "${cache_dir}/${tarball_name}" ]; then
    emit_blocker MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY fatal \
      "HEPPH_NO_NETWORK=1 is set and ${tarball_name} is not in HEPPH_OFFLINE_CACHE_DIR." \
      "Pre-stage ${tarball_name} in ${cache_dir} and retry." \
      "{\"url\":\"${MICROMEGAS_URL}\",\"cache_dir\":\"${cache_dir}\"}"
    exit $EXIT_DOWNLOAD
  fi
  # Cache hit — copy to dest
  cp "${cache_dir}/${tarball_name}" "$tarball_dest"
  log "Offline cache hit: ${cache_dir}/${tarball_name}"
else
  # Network mode: use download_with_retry, fall back to Zenodo mirror if
  # LAPTh is unreachable. Zenodo only provides
  # MICROMEGAS_ZENODO_FALLBACK_VERSION; if the fallback succeeds the installed
  # version will differ from the requested pin — we warn but do not abort.
  download_err_file="/tmp/micromegas_dl_err_$$.txt"
  installed_from_mirror=0
  if ! (download_with_retry "$MICROMEGAS_URL" "$tarball_dest" "MICROMEGAS") 2>"$download_err_file"; then
    warn "LAPTh download failed. Trying Zenodo mirror ($MICROMEGAS_ZENODO_FALLBACK_VERSION)..."
    rm -f "$tarball_dest"
    if ! curl -L --fail --progress-bar -o "$tarball_dest" "$MICROMEGAS_ZENODO_FALLBACK_URL" 2>"$download_err_file"; then
      emit_blocker MICROMEGAS_DOWNLOAD_FAILED fatal \
        "micrOMEGAs download failed after 2 retries from LAPTh ($MICROMEGAS_URL) and Zenodo fallback ($MICROMEGAS_ZENODO_FALLBACK_URL)." \
        "Check your network connection, or visit https://lapth.cnrs.fr/micromegas/ to download manually and use '/micromegas-install use-path <dir>' instead." \
        "{\"url\":\"${MICROMEGAS_URL}\",\"fallback_url\":\"${MICROMEGAS_ZENODO_FALLBACK_URL}\"}"
      rm -f "$download_err_file"
      exit $EXIT_DOWNLOAD
    fi
    installed_from_mirror=1
    # Fallback pins a different version — adjust install_dir to match the
    # fallback tarball's internal layout.
    MICROMEGAS_VERSION="$MICROMEGAS_ZENODO_FALLBACK_VERSION"
    install_dir="$parent_dir/micromegas_${MICROMEGAS_VERSION}"
    tarball_name="micromegas_${MICROMEGAS_VERSION}.tgz"
    warn "Installed from Zenodo mirror: version=$MICROMEGAS_VERSION (requested ${HEPPH_MICROMEGAS_VERSION:-6.0.5} may differ)."
  fi
  rm -f "$download_err_file"
fi

# ── Stage 3: verify checksum ─────────────────────────────────────────────────
verify_checksum "$tarball_dest" "$MICROMEGAS_SHA256"

# ── Stage 4: extract ──────────────────────────────────────────────────────────
mkdir -p "$parent_dir"
log "Extracting to $install_dir..."
tar -xzf "$tarball_dest" -C "$parent_dir"
# micrOMEGAs tarballs extract to micromegas_X.Y.Z/
if [ ! -d "$install_dir" ]; then
  err "Extraction produced unexpected layout; expected $install_dir"
  exit $EXIT_EXTRACT
fi

# ── Stage 4.5: vendored upstream patches ─────────────────────────────────────
# See references/micromegas-workarounds.md for the rationale behind each patch.
. "$SCRIPT_DIR/_patches.sh"
apply_micromegas_upstream_patches "$install_dir"

# ── Stage 5: macOS environment ────────────────────────────────────────────────
if [ "$(uname -s)" = "Darwin" ]; then
  . "$SCRIPT_DIR/_macos_env.sh"
  _macos_env_setup "$install_dir"
fi

# ── Stage 5.5: toolchain precondition ────────────────────────────────────────
# Runs right before make to catch missing cc/gfortran/gmake with a friendly
# per-OS hint instead of an opaque make failure. Placed AFTER download so the
# offline-policy blocker path (MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY) remains
# reachable on machines that happen to lack a full build toolchain.
if [ "${HEPPH_SKIP_TOOLCHAIN_CHECK:-0}" != "1" ]; then
  check_toolchain_present
fi

# ── Stage 6: build under netguard ────────────────────────────────────────────
NETGUARD_LOG="/tmp/micromegas_netguard_$$.log"
netguard_setup "$NETGUARD_LOG"

NCPUS="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)"

log "Building micrOMEGAs with make -j${NCPUS}..."
make_rc=0
MAKE_LOG_FILE="/tmp/micromegas_make_$$.log"
PATH="$NETGUARD_STUB_DIR:$PATH" make -C "$install_dir" -j"$NCPUS" 2>&1 | tee "$MAKE_LOG_FILE" || make_rc=$?

# Check netguard log before checking make result
if ! netguard_check "$NETGUARD_LOG"; then
  netguard_cleanup
  exit $EXIT_BUILD_NET
fi
netguard_cleanup

if [ $make_rc -ne 0 ]; then
  make_tail="$(tail -40 "$MAKE_LOG_FILE" | tr '\n' '|' | sed 's/"/\\"/g')"
  # LAPACK signature detection: if the tail mentions lapack-family symbols,
  # emit the more specific LAPACK_ABSENT blocker with a per-OS install hint
  # (migrated from monte-carlo-tools/micromegas-install v0).
  lapack_re='lapack|liblapack|-llapack|dgesv|dgemm|dgetrf|dsyev'
  if tail -40 "$MAKE_LOG_FILE" | grep -Eqi "$lapack_re"; then
    case "$(os_name)" in
      macos) lapack_hint="Install LAPACK with Homebrew: brew install lapack  (Xcode vecLib is usually sufficient; try reinstalling gcc via brew if linking still fails)" ;;
      linux) lapack_hint="Install LAPACK dev headers: sudo apt-get install -y liblapack-dev  (Debian/Ubuntu) or sudo yum install -y lapack-devel  (RHEL/CentOS)" ;;
      *)     lapack_hint="Install LAPACK development libraries for your OS." ;;
    esac
    emit_blocker LAPACK_ABSENT fatal \
      "micrOMEGAs build failed with a LAPACK-related error (see context.make_log_tail). Install LAPACK dev headers and retry." \
      "$lapack_hint" \
      "{\"make_log_tail\":\"${make_tail}\",\"likely_cause\":\"lapack\"}"
    exit $EXIT_NO_LAPACK
  fi
  emit_blocker MICROMEGAS_BUILD_FAILED fatal \
    "micrOMEGAs make failed (exit $make_rc)." \
    "Check make.log for details." \
    "{\"make_log_tail\":\"${make_tail}\"}"
  exit $make_rc
fi

# ── Stage 7: smoke test ───────────────────────────────────────────────────────
log "Running smoke test..."
if ! bash "$SCRIPT_DIR/_smoke.sh" "$install_dir"; then
  exit $EXIT_MICROMEGAS_SMOKE
fi

# Optional full smoke: compile and run the MSSM reference example.
# Adds ~5 min on first run. Off by default; the light smoke above is
# sufficient for validating that micrOMEGAs + CalcHEP built correctly.
if [ "${FULL_SMOKE:-0}" = "1" ]; then
  log "Running full smoke (MSSM example — this adds ~5 min)..."
  mssm_log="/tmp/micromegas_mssm_smoke_$$.log"
  maker="make"
  command -v gmake >/dev/null 2>&1 && maker="gmake"
  if ! ( cd "$install_dir/MSSM" && "$maker" main=main.c && ./main input ) >"$mssm_log" 2>&1; then
    mssm_tail="$(tail -40 "$mssm_log" 2>/dev/null | tr '\n' '|' | sed 's/"/\\"/g')"
    emit_blocker MICROMEGAS_SMOKE_TEST_FAILED fatal \
      "MSSM full-smoke run failed. See context.mssm_smoke_log_tail." \
      "Check $mssm_log for the full log." \
      "{\"mssm_smoke_log_tail\":\"${mssm_tail}\"}"
    exit $EXIT_MICROMEGAS_SMOKE
  fi
  log "MSSM full smoke passed."
fi

# ── Stage 8: PPPC tables check ───────────────────────────────────────────────
# micrOMEGAs 6.0.5 ships PPPC4DMID tables in Data/
pppc_file="$install_dir/Data/AtProduction_gammas.dat"
if [ ! -f "$pppc_file" ]; then
  emit_blocker PPPC_TABLES_MISSING fatal \
    "PPPC4DMID indirect-detection table not found at '$pppc_file'." \
    "Verify the micrOMEGAs installation is complete." \
    "{\"expected_path\":\"${pppc_file}\"}"
  exit $EXIT_PPPC_MISSING
fi

# ── Stage 9: config_merge ────────────────────────────────────────────────────
ts="$(python3 -c "import datetime; print(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))")"

ver=""
if [ -f "$install_dir/include/VERSION" ]; then
  ver="$(head -1 "$install_dir/include/VERSION" | tr -d '[:space:]')"
fi

config_merge \
  micromegas_path "$install_dir" \
  micromegas_version "${ver:-$MICROMEGAS_VERSION}" \
  calchep_path "$install_dir/CalcHEP_src" \
  calchep_bundled "true" \
  micromegas_installed_at "$ts"

log "micrOMEGAs ${ver:-$MICROMEGAS_VERSION} installed at $install_dir"
printf '{"status":"installed","path":"%s","version":"%s"}\n' \
  "$install_dir" "${ver:-$MICROMEGAS_VERSION}"
exit 0
