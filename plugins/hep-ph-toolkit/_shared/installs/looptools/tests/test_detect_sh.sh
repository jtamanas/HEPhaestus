#!/usr/bin/env bash
# Tests for _shared/installs/looptools/detect.sh (the runner-facing wrapper).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT="$SCRIPT_DIR/../detect.sh"
FIXTURE="$SCRIPT_DIR/fixtures/looptools_stub/LoopTools-2.16"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# 1) No config → exit 1
echo '{}' > "$XDG_CONFIG_HOME/hephaestus/config.json"
if bash "$DETECT" >/dev/null 2>&1; then echo "FAIL: empty config"; exit 1; fi

# 2) Config registers a path that does not exist on disk → exit 1
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "$TMP/nope", "looptools_version": "2.16"}
EOF
if bash "$DETECT" >/dev/null 2>&1; then echo "FAIL: missing binary"; exit 1; fi

# 3) Config registers fixture stub with correct version → exit 0 (fast path)
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "$FIXTURE", "looptools_version": "2.16"}
EOF
if ! bash "$DETECT" >/dev/null 2>&1; then echo "FAIL: configured fixture should pass fast path"; exit 1; fi

# 4) Version drift (pinned 2.16, config says 2.15) → fast path fails, slow
# probe runs against the fixture; if file-presence passes, detect.sh exits 0.
# This is the design contract per the spec: slow probe is "is binary
# functional", not "does version pin match".
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "$FIXTURE", "looptools_version": "2.15"}
EOF
if ! bash "$DETECT" >/dev/null 2>&1; then echo "FAIL: version drift on a real fixture should fall through to slow probe and pass"; exit 1; fi

# 5) HEPPH_FORCE_PROBE=1 with valid fixture → still exit 0 (slow probe passes)
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "$FIXTURE", "looptools_version": "2.16"}
EOF
if ! HEPPH_FORCE_PROBE=1 bash "$DETECT" >/dev/null 2>&1; then echo "FAIL: HEPPH_FORCE_PROBE on valid install should still pass"; exit 1; fi

echo OK
