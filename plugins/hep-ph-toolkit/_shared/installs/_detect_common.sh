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

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <tool> <expected_path> <pinned_version>" >&2
  exit 2
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
