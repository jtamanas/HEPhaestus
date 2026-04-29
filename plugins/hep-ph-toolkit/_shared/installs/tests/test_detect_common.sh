#!/usr/bin/env bash
# Test the shared fast-path helper used by every <tool>/detect.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/../_detect_common.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# Fixture: a fake tool installed at $TMP/install/bin
mkdir -p "$TMP/install/bin"
touch "$TMP/install/bin/footool"
chmod +x "$TMP/install/bin/footool"

write_config() {
  cat >"$XDG_CONFIG_HOME/hephaestus/config.json"
}

# 1) No config → fail (exit non-zero)
echo '{}' | write_config
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: empty config should not pass"; exit 1
fi

# 2) Config registers tool with matching path + version → pass (exit 0)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool", "footool_version": "1.0"}
EOF
if ! bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: matched config should pass"; exit 1
fi

# 3) Path on disk missing → fail
rm "$TMP/install/bin/footool"
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: missing binary should not pass"; exit 1
fi
touch "$TMP/install/bin/footool"; chmod +x "$TMP/install/bin/footool"

# 4) Version drift → fail (forces caller to fall through to slow probe)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool", "footool_version": "0.9"}
EOF
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: version drift should not pass"; exit 1
fi

# 5) Missing version field in config → fail (forces re-verification)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool"}
EOF
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: missing version should not pass"; exit 1
fi

echo OK
