#!/usr/bin/env bash
# install_formcalc.sh — orchestrator for /formcalc-install.
# Subcommands: detect | use-path <dir> | install [dir]
#
# Sourcing pattern (5 levels deep from repo root):
#   plugins/hep-ph-toolkit/skills/formcalc-install/scripts/install_formcalc.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# From .../plugins/hep-ph-toolkit/skills/formcalc-install/scripts/
# go up 4 levels to reach .../plugins/
PLUGINS_DIR="$(cd "$SCRIPT_DIR/../../../../.." && pwd)/plugins"
SHARED_COMMON="$PLUGINS_DIR/shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  echo "[formcalc-install] ERROR: shared _common.sh not found at $SHARED_COMMON" >&2
  exit 1
fi
. "$SHARED_COMMON"

ATOMIC_WRITE="$PLUGINS_DIR/shared/install-helpers/atomic_write.sh"
if [ ! -f "$ATOMIC_WRITE" ]; then
  err "atomic_write.sh not found at $ATOMIC_WRITE"
  exit 1
fi
. "$ATOMIC_WRITE"

_LOG_TAG="formcalc-install"

# ── Version pins (override via env) ──────────────────────────────────────────
# FormCalc 10.0 does not exist; latest is 9.10 (feynarts.de, 2024-10-11).
FORMCALC_VERSION="${HEPPH_FORMCALC_VERSION:-9.10}"
FORM_VERSION="${HEPPH_FORM_VERSION:-4.3.1}"
LOOPTOOLS_VERSION="${FORMCALC_VERSION}"   # always bundled

FORMCALC_SHA256="${HEPPH_FORMCALC_SHA256:-352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b}"
FORM_SHA256="${HEPPH_FORM_SHA256:-f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce}"

# ── Install root ─────────────────────────────────────────────────────────────
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_ROOT="${DATA_HOME}/hephaestus/formcalc-${FORMCALC_VERSION}"

# ── Download URLs ─────────────────────────────────────────────────────────────
# FormCalc: feynarts.de canonical URL (verified live, HTTP 200).
FORMCALC_URL="https://feynarts.de/formcalc/FormCalc-${FORMCALC_VERSION}.tar.gz"
# FORM: GitHub release mirror (redirects via form-dev/form, resolves HTTP 200).
FORM_URL="https://github.com/vermaseren/form/releases/download/v${FORM_VERSION}/form-${FORM_VERSION}.tar.gz"

# ── Helpers ───────────────────────────────────────────────────────────────────
blocker_json() {
  # blocker_json <code> <mode> <message> [extra_json_fragment]
  local code="$1" mode="$2" msg="$3" extra="${4:-}"
  if [ -n "$extra" ]; then
    printf '{"code":"%s","mode":"%s","message":"%s",%s}\n' \
      "$code" "$mode" "$msg" "$extra" >&2
  else
    printf '{"code":"%s","mode":"%s","message":"%s"}\n' \
      "$code" "$mode" "$msg" >&2
  fi
}

detect_formcalc() {
  local cfgpath
  cfgpath="$(config_get "formcalc_path" 2>/dev/null || true)"
  if [ -n "$cfgpath" ] && [ -f "$cfgpath/FormCalc.m" ]; then
    local ver
    ver="$(config_get "formcalc_version" 2>/dev/null || true)"
    local form_bin
    form_bin="$(config_get "form_binary" 2>/dev/null || true)"
    local lt_lib
    lt_lib="$(config_get "looptools_lib" 2>/dev/null || true)"
    printf '{"status":"configured","path":"%s","formcalc_version":"%s","form_binary":"%s","looptools_lib":"%s"}\n' \
      "$cfgpath" "${ver:-unknown}" "${form_bin:-}" "${lt_lib:-}"
    return 0
  fi

  # Scan candidates.
  local found=()
  while IFS= read -r candidate; do
    if [ -f "$candidate/FormCalc.m" ]; then
      found+=("$candidate")
    fi
  done < <(
    find "$HOME" -maxdepth 8 -name "FormCalc.m" 2>/dev/null \
      | xargs -I{} dirname {} 2>/dev/null | sort -u || true
  )

  if [ ${#found[@]} -eq 1 ]; then
    printf '{"status":"found","path":"%s"}\n' "${found[0]}"
  elif [ ${#found[@]} -gt 1 ]; then
    local paths_json
    paths_json="$(printf '"%s",' "${found[@]}" | sed 's/,$//')"
    printf '{"status":"ambiguous","paths":[%s]}\n' "$paths_json"
  else
    printf '{"status":"missing"}\n'
  fi
}

use_path_cmd() {
  local dir="${1:-}"
  if [ -z "$dir" ]; then
    err "use-path requires a directory argument."
    exit $EXIT_BAD_PATH
  fi

  # Check Wolfram engine.
  local wolfram_bin
  wolfram_bin="$(config_get "wolfram_engine_path" 2>/dev/null || true)"
  if [ -z "$wolfram_bin" ] || [ ! -x "$wolfram_bin" ]; then
    blocker_json "WOLFRAM_KERNEL_ABSENT" "fatal" "wolfram_engine_path not set or binary missing" \
      '"user_instruction":"Run /install to install and configure Wolfram Engine first."'
    exit $EXIT_NO_WOLFRAM
  fi

  if [ ! -f "$dir/FormCalc.m" ]; then
    blocker_json "FORMCALC_PATH_INVALID" "fatal" "$dir/FormCalc.m not found" \
      "\"user_instruction\":\"Provide the path to the FormCalc package directory (the one containing FormCalc.m).\",\"path\":\"$dir\""
    exit $EXIT_BAD_PATH
  fi

  # Version probe.
  local version
  version="$(
    "$wolfram_bin" -script "$SCRIPT_DIR/probe_formcalc.wls" "$dir" 2>/dev/null || true
  )"
  version="${version//[$'\r\n']/}"
  if [ -z "$version" ]; then
    blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" "FormCalc version probe returned empty" \
      '"user_instruction":"Check Wolfram Engine activation and that FormCalc.m is loadable."'
    exit $EXIT_SMOKE
  fi

  config_merge \
    "formcalc_path" "$dir" \
    "formcalc_version" "$version" \
    "formcalc_installed_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"status":"configured","path":"%s","formcalc_version":"%s"}\n' "$dir" "$version"
}

# ── Subcommand dispatch ───────────────────────────────────────────────────────
SUBCMD="${1:-detect}"
shift || true

case "$SUBCMD" in
  detect)
    detect_formcalc
    ;;
  use-path)
    use_path_cmd "$@"
    ;;
  install)
    # Delegate to install subcommand (implemented in C6).
    "$SCRIPT_DIR/install_formcalc_full.sh" "$@"
    ;;
  *)
    err "Unknown subcommand: $SUBCMD  (valid: detect | use-path <dir> | install [dir])"
    exit $EXIT_GENERIC
    ;;
esac
