#!/usr/bin/env bash
# test_install_offline.sh — integration test: offline install from cached tarball.
#
# GATED: requires HEPPH_RUN_NETWORK_TESTS=1
# Pre-stages tarball in cache, runs install under HEPPH_NO_NETWORK=1;
# asserts exit 0 + config keys + smoke passes.
#
# Usage:
#   HEPPH_RUN_NETWORK_TESTS=1 bash test_install_offline.sh
if [ "${HEPPH_RUN_NETWORK_TESTS:-0}" != "1" ]; then
  echo "SKIP: HEPPH_RUN_NETWORK_TESTS not set to 1"
  exit 0
fi

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$SCRIPT_DIR/../scripts/install_micromegas.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

TMP_DIR="$(mktemp -d)"
CACHE_DIR="$TMP_DIR/cache"
INSTALL_PARENT="$TMP_DIR/install"
CONFIG_DIR="$TMP_DIR/config"
mkdir -p "$CACHE_DIR" "$INSTALL_PARENT" "$CONFIG_DIR/hephaestus"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

MICROMEGAS_VERSION="${HEPPH_MICROMEGAS_VERSION:-6.0.5}"
TARBALL="micromegas_${MICROMEGAS_VERSION}.tgz"

# ── Stage 1: pre-stage tarball in cache ──────────────────────────────────────
if [ -n "${HEPPH_OFFLINE_CACHE_DIR:-}" ] && [ -f "${HEPPH_OFFLINE_CACHE_DIR}/${TARBALL}" ]; then
  cp "${HEPPH_OFFLINE_CACHE_DIR}/${TARBALL}" "$CACHE_DIR/${TARBALL}"
  pass "tarball found in existing HEPPH_OFFLINE_CACHE_DIR"
else
  # Download once to cache
  echo "Downloading $TARBALL for offline test..."
  curl -L --fail --progress-bar \
    -o "$CACHE_DIR/${TARBALL}" \
    "https://lapth.cnrs.fr/micromegas/downloadarea/${TARBALL}" \
    || fail "Could not pre-stage tarball"
  pass "tarball downloaded to cache"
fi

# ── Stage 2: run install under HEPPH_NO_NETWORK=1 ────────────────────────────
echo "Running offline install..."
rc=0
XDG_CONFIG_HOME="$CONFIG_DIR" \
HEPPH_NO_NETWORK=1 \
HEPPH_OFFLINE_CACHE_DIR="$CACHE_DIR" \
  bash "$INSTALL_SH" install "$INSTALL_PARENT" 2>&1 || rc=$?

if [ $rc -eq 0 ]; then
  pass "offline install exit 0"
else
  fail "offline install exited $rc"
fi

# ── Stage 3: verify config keys ──────────────────────────────────────────────
CONFIG_FILE="$CONFIG_DIR/hephaestus/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  fail "config.json not written"
fi

for key in micromegas_path micromegas_version calchep_path calchep_bundled micromegas_installed_at; do
  val="$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(d.get('$key',''))")"
  if [ -z "$val" ]; then
    fail "config key '$key' not written"
  fi
  pass "config key $key=$val"
done

# ── Stage 4: verify smoke test passes ────────────────────────────────────────
installed_path="$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['micromegas_path'])")"
if bash "$SCRIPT_DIR/../scripts/_smoke.sh" "$installed_path"; then
  pass "smoke test passes on installed path"
else
  fail "smoke test failed on installed path $installed_path"
fi

echo "All offline install integration tests passed."
