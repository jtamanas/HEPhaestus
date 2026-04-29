#!/usr/bin/env bash
# Verify bundle resumption is detect-driven, not state-stored:
# pre-populate config with N-1 tools registered + on-disk; the bundle
# loop must invoke install.sh ONLY for the missing tool.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCH="$SCRIPT_DIR/../bundle_install.sh"

TMP="$(mktemp -d)"
trap 'find "$TMP" -mindepth 0 -delete 2>/dev/null || true' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# Stub install.sh / detect.sh trees.
STUB_INSTALLS="$TMP/installs"
mkdir -p "$STUB_INSTALLS/looptools" "$STUB_INSTALLS/formcalc" "$STUB_INSTALLS/feynarts"
TOUCH_LOG="$TMP/installs.log"

for tool in looptools formcalc feynarts; do
  cat > "$STUB_INSTALLS/$tool/detect.sh" <<EOF
#!/usr/bin/env bash
[ -f "\$XDG_CONFIG_HOME/hephaestus/config.json" ] || exit 1
python3 -c '
import json, os, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
sys.exit(0 if d.get("${tool}_path") else 1)
' "\$XDG_CONFIG_HOME/hephaestus/config.json"
EOF
  cat > "$STUB_INSTALLS/$tool/install.sh" <<EOF
#!/usr/bin/env bash
# Assert orchestrator passes "install" as first argument (P0 #1 contract).
if [ "\${1:-}" != "install" ]; then
  echo "FAIL: install.sh for $tool got first arg [\${1:-}], expected [install]" >&2
  exit 99
fi
echo "INSTALLED $tool" >> "$TOUCH_LOG"
python3 -c '
import json, os, sys
p = sys.argv[1]
d = {}
if os.path.exists(p):
    with open(p) as f:
        d = json.load(f)
d["${tool}_path"] = "/fake/$tool"
d["${tool}_version"] = "0"
with open(p, "w") as f:
    json.dump(d, f)
' "\$XDG_CONFIG_HOME/hephaestus/config.json"
EOF
  touch "$STUB_INSTALLS/$tool/INSTALL.md"
  chmod +x "$STUB_INSTALLS/$tool/detect.sh" "$STUB_INSTALLS/$tool/install.sh"
done

# Pre-populate config with looptools + formcalc; leave feynarts missing.
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "/fake/looptools", "formcalc_path": "/fake/formcalc"}
EOF

HEPPH_INSTALLS_ROOT="$STUB_INSTALLS" bash "$ORCH" \
  --tools looptools,formcalc,feynarts >/dev/null

INSTALLED="$(cat "$TOUCH_LOG" 2>/dev/null || true)"
if [ "$INSTALLED" != "INSTALLED feynarts" ]; then
  echo "FAIL: expected only feynarts; got [$INSTALLED]"
  exit 1
fi
echo OK
