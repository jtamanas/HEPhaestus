#!/usr/bin/env bash
# probe_feynrules.sh — load FeynRules in wolframscript and print its version.
#
# Usage:
#   probe_feynrules.sh <feynrules_pkg_dir> [wolframscript_path]
#
# Prints the version string (e.g. "2.3.49") to stdout on success.
# Exits 0 on success, non-zero if the probe fails or the directory is invalid.
#
# On Mathematica 12.2+ the ValueQ deprecation warning can block FeynRules from
# loading. We prepend SetOptions[ValueQ, Method -> "Legacy"] to sidestep it.
set -euo pipefail

_LOG_TAG="probe_feynrules"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# shellcheck source=detect_wolfram.sh
. "$SCRIPT_DIR/detect_wolfram.sh"

probe_feynrules_version() {
  local pkg_dir="$1"
  local ws="${2:-}"
  [ -d "$pkg_dir" ] || return 1
  [ -f "$pkg_dir/FeynRules.m" ] || return 1
  [ -f "$pkg_dir/FeynRulesPackage.m" ] || return 1
  if [ -z "$ws" ]; then
    ws="$(detect_wolfram_path)"
  fi
  [ -x "$ws" ] || return 1

  # Build probe code. $FeynRulesPath must be set BEFORE loading FeynRules.m
  # (the loader reads it). AppendTo[$Path] lets `<<FeynRules`` resolve.
  local code
  code=$(cat <<WL
Quiet[SetOptions[ValueQ, Method -> "Legacy"]];
\$FeynRulesPath = "$pkg_dir";
If[!MemberQ[\$Path, "$pkg_dir"], AppendTo[\$Path, "$pkg_dir"]];
<<FeynRules\`;
Print["FR_VERSION=", FR\$VersionNumber];
WL
)
  "$ws" -code "$code" 2>/dev/null \
    | grep -Eo 'FR_VERSION=[0-9]+\.[0-9]+\.[0-9]+' \
    | head -n1 \
    | sed 's/^FR_VERSION=//'
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  pkg_dir="${1:-}"
  ws="${2:-}"
  if [ -z "$pkg_dir" ]; then
    echo "usage: probe_feynrules.sh <feynrules_pkg_dir> [wolframscript_path]" >&2
    exit 2
  fi
  v="$(probe_feynrules_version "$pkg_dir" "$ws" || true)"
  if [ -n "$v" ]; then
    echo "$v"
    exit 0
  fi
  exit 1
fi
