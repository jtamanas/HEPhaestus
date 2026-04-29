#!/usr/bin/env bash
# detect_higgstools.sh — idempotent probe for HiggsBounds + HiggsSignals.
# Usage: detect_higgstools.sh
# Emits JSON on stdout: {status: configured|found|missing, ...}
# Exit 0 in all cases (detect is never fatal).
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../../shared/install-helpers/_common.sh"
if [ ! -f "$COMMON" ]; then
  COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
fi
. "$COMMON"

_LOG_TAG="higgstools-detect"

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
CONFIG_FILE="$CONFIG_DIR/config.json"

# ── Read config fields ────────────────────────────────────────────────────────
hb_path=""
hs_path=""
hb_version=""
hs_version=""
backend=""

if [ -f "$CONFIG_FILE" ]; then
  hb_path=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("higgsbounds_path", "") or "")
except Exception:
    print("")
PY
)
  hs_path=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("higgssignals_path", "") or "")
except Exception:
    print("")
PY
)
  hb_version=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("higgsbounds_version", "") or "")
except Exception:
    print("")
PY
)
  hs_version=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("higgssignals_version", "") or "")
except Exception:
    print("")
PY
)
  backend=$(python3 - "$CONFIG_FILE" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get("higgstools_backend", "") or "")
except Exception:
    print("")
PY
)
fi

# ── Check if configured paths have actual binaries ────────────────────────────
_has_hb_binary() {
  local dir="$1"
  [ -x "$dir/bin/HiggsBounds" ] || [ -x "$dir/HiggsBounds" ]
}

_has_hs_binary() {
  local dir="$1"
  [ -x "$dir/bin/HiggsSignals" ] || [ -x "$dir/HiggsSignals" ]
}

if [ -n "$hb_path" ] && [ -n "$hs_path" ]; then
  if _has_hb_binary "$hb_path" && _has_hs_binary "$hs_path"; then
    # Fully configured
    python3 - "$hb_path" "$hs_path" "$hb_version" "$hs_version" "${backend:-legacy}" <<'PY'
import json, sys
hb_path, hs_path, hb_version, hs_version, backend = sys.argv[1:]
print(json.dumps({
    "status": "configured",
    "hb_path": hb_path,
    "hb_version": hb_version or "unknown",
    "hs_path": hs_path,
    "hs_version": hs_version or "unknown",
    "backend": backend,
}, indent=2))
PY
    exit 0
  fi
fi

# ── Emit missing ────────────────────────────────────────────────────────────
python3 -c "import json; print(json.dumps({'status': 'missing'}))"
exit 0
