#!/usr/bin/env bash
# detect-fast-path helper used by every _shared/installs/<tool>/detect.sh.
#
# Usage:
#   bash _detect_common.sh <tool> <expected_path> <pinned_version>
#
# Exit 0 iff config.json registers <tool>_path == <expected_path> AND
# <tool>_version == <pinned_version> AND <expected_path> exists on disk.
# Otherwise exit 1 (caller falls through to slow binary probe).
set -euo pipefail

_dc_usage() {
  echo "usage: $0 <tool> <expected_path> <pinned_version>" >&2
  echo "       $0 path-version-match <path> <pinned_version>  # slow-path helper" >&2
  exit 2
}

# Slow-path helper: check whether `expected_path` is plausibly the
# pinned version by inspecting the path components (e.g. SARAH-4.15.3,
# LoopTools-2.16, MG5_aMC_v3_5_6) and any nearby VERSION files.
#
# Exit 0  iff a strict version match is found.
# Exit 1  if a different version is detected (drift; caller should treat
#         as not-ready and trigger reinstall).
# Exit 2  if no version stamp is parseable (caller's existing
#         file-presence check is the best we can do; treat as ready when
#         the on-disk binary exists).
_dc_path_version_match() {
  local p="$1"
  local pin="$2"
  [ -n "$p" ] && [ -n "$pin" ] || return 2

  # 1. VERSION file at the path or one level up.
  local vfile
  for vfile in "$p/VERSION" "$(dirname "$p")/VERSION"; do
    if [ -f "$vfile" ]; then
      local got
      got="$(head -n1 "$vfile" 2>/dev/null | grep -Eo '[0-9]+(\.[0-9]+){1,3}' | head -n1 || true)"
      if [ -n "$got" ]; then
        [ "$got" = "$pin" ] && return 0
        return 1
      fi
    fi
  done

  # 2. Walk up the path looking for a versioned component.
  local dir="$p"
  local _i
  for _i in 1 2 3 4; do
    local base
    base="$(basename "$dir")"
    # Match e.g. SARAH-4.15.3, LoopTools-2.16, FeynArts-3.11,
    # MG5_aMC_v3_5_6, drake-1.0, FeynRules-2.3.49.
    local extracted
    extracted="$(printf '%s' "$base" | grep -Eo '[0-9]+(\.[0-9]+){1,3}|[0-9]+_[0-9]+_[0-9]+' | head -n1 || true)"
    if [ -n "$extracted" ]; then
      # Normalize: SARAH-style path uses dots; MG5 uses underscores.
      local extracted_norm
      extracted_norm="${extracted//_/.}"
      [ "$extracted_norm" = "$pin" ] && return 0
      [ "$extracted" = "$pin" ] && return 0
      # Detected a version, but it differs — definite drift.
      return 1
    fi
    dir="$(dirname "$dir")"
    [ "$dir" = "/" ] && break
  done

  return 2
}

# Public CLI: standalone subcommand for callers that want to invoke the
# slow-path helper without sourcing this file.
if [ "${1:-}" = "path-version-match" ]; then
  shift
  _dc_path_version_match "${1:-}" "${2:-}"
  exit $?
fi

if [ "$#" -ne 3 ]; then
  _dc_usage
fi

tool="$1"
expected_path="$2"
pinned_version="$3"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
[ -f "$cfg" ] || exit 1

# Use python3 for JSON parsing (Python is a hephaestus prereq).
python3 - "$cfg" "$tool" "$expected_path" "$pinned_version" <<'PY' || exit 1
import json, os, sys
cfg_path, tool, expected_path, pinned_version = sys.argv[1:5]
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except Exception:
    sys.exit(1)
got_path = cfg.get(f"{tool}_path")
got_ver  = cfg.get(f"{tool}_version")
if got_path != expected_path:
    sys.exit(1)
if got_ver != pinned_version:
    sys.exit(1)
if not os.path.exists(expected_path):
    sys.exit(1)
sys.exit(0)
PY
