#!/usr/bin/env bash
# _probe.sh — idempotent probe for CLASS installation.
# Usage: _probe.sh
# Emits JSON on stdout: {"status":"configured"|"missing", ...}
# Exit 0 in all cases (detect is never fatal).
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../../shared/install-helpers/_common.sh"
if [ ! -f "$COMMON" ]; then
  COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
fi
. "$COMMON"

_LOG_TAG="class-detect"

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
CONFIG_FILE="$CONFIG_DIR/config.json"

# ── Read config fields ────────────────────────────────────────────────────────
class_path=""
class_version=""
classy_version=""
class_openmp_enabled=""

if [ -f "$CONFIG_FILE" ]; then
  class_path=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("class_path", "") or "")
except Exception:
    print("")
PY
)
  class_version=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("class_version", "") or "")
except Exception:
    print("")
PY
)
  classy_version=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("classy_version", "") or "")
except Exception:
    print("")
PY
)
  class_openmp_enabled=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("class_openmp_enabled", "") or "")
except Exception:
    print("")
PY
)
fi

# ── Check if configured path has the class binary ────────────────────────────
_has_class_binary() {
  local dir="$1"
  [ -x "$dir/class" ]
}

if [ -n "$class_path" ] && _has_class_binary "$class_path"; then
  python3 - "$class_path" "$class_version" "$classy_version" "$class_openmp_enabled" <<'PY'
import json, sys
class_path, class_version, classy_version, class_openmp_enabled = sys.argv[1:]
print(json.dumps({
    "status": "configured",
    "class_path": class_path,
    "class_version": class_version or "unknown",
    "classy_version": classy_version or "unknown",
    "class_openmp_enabled": class_openmp_enabled or "unknown",
}, indent=2))
PY
  exit 0
fi

# ── Emit missing ──────────────────────────────────────────────────────────────
python3 -c "import json; print(json.dumps({'status': 'missing'}))"
exit 0
