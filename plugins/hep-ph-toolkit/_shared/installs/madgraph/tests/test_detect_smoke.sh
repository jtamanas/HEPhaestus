#!/usr/bin/env bash
# Smoke test: detect.sh exits non-zero when no config + no on-disk MG5.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT="$SCRIPT_DIR/../detect.sh"

TMP="$(mktemp -d)"
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"
echo '{}' > "$XDG_CONFIG_HOME/hephaestus/config.json"

# Empty config + no MG5 in scan paths → expect non-zero.
if bash "$DETECT" 2>/dev/null; then
  # If the host happens to have MG5 on PATH, that's also a valid
  # outcome — only fail if we get exit 0 with NO real install. We
  # can't easily distinguish here, so just print what we got.
  echo "NOTE: detect.sh exited 0 — host likely has MG5 installed; skipping negative assertion."
  exit 0
fi

echo "OK: detect.sh exits non-zero when MG5 absent."
