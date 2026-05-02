#!/usr/bin/env bash
# detect.sh — fast config-path probe for CLASS installation.
# Delegates to _probe.sh for the full JSON status emission.
#
# Two-tier check:
#   1. Config fast path: class_path + class_version present and binary exists.
#      Short-circuits with exit 0 when pinned version matches.
#   2. Slow probe (via _probe.sh): emit full JSON status object.
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PINNED_CLASS_VERSION="${HEPPH_CLASS_VERSION:-3.3.4}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
class_path=""; class_version=""

if [ -f "$cfg" ]; then
  raw="$(python3 - "$cfg" <<'PY' 2>/dev/null || true
import json, sys
try:
  with open(sys.argv[1]) as f: d = json.load(f)
except Exception:
  print(); print(); sys.exit(0)
print(d.get("class_path", ""))
print(d.get("class_version", ""))
PY
  )"
  class_path="$(printf '%s\n' "$raw" | sed -n '1p')"
  class_version="$(printf '%s\n' "$raw" | sed -n '2p')"
fi

# Fast path: if version matches pinned and binary is present, exit 0.
if [ -n "$class_path" ] && [ "$class_version" = "$PINNED_CLASS_VERSION" ] && [ -x "$class_path/class" ]; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exec bash "$SCRIPT_DIR/_probe.sh"
fi

# Slow path: delegate to _probe.sh
exec bash "$SCRIPT_DIR/_probe.sh"
