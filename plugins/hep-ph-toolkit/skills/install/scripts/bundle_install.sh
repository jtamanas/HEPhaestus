#!/usr/bin/env bash
# /install bundle orchestrator. Drives _shared/installs/<tool>/{detect,install}.sh
# directly. No sub-skill dispatching.
#
# Usage:
#   bundle_install.sh --bundle <name>
#   bundle_install.sh --tool <name>
#   bundle_install.sh --tools <a,b,c>
#
# Bundle resumption is detect-driven, not state-stored. Re-invocation
# re-runs detect.sh for every tool in the bundle; tools that completed
# pass the fast path and are skipped, so the bundle effectively resumes
# at the first tool whose detect.sh still fails.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLS_ROOT="${HEPPH_INSTALLS_ROOT:-$(cd "$SCRIPT_DIR/../../../_shared/installs" && pwd)}"
BUNDLES_FILE="${HEPPH_BUNDLES_FILE:-$SCRIPT_DIR/bundles.json}"

usage() {
  echo "usage: $0 [--bundle <name>] [--tool <name>] [--tools a,b,c]" >&2
  exit 2
}

mode=""; arg=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) mode=bundle; arg="$2"; shift 2;;
    --tool)   mode=tool;   arg="$2"; shift 2;;
    --tools)  mode=tools;  arg="$2"; shift 2;;
    -h|--help) usage;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
[ -n "$mode" ] || usage

resolve_tools() {
  case "$mode" in
    bundle)
      python3 -c '
import json, sys
with open(sys.argv[1]) as f:
    b = json.load(f)
if sys.argv[2] not in b:
    sys.stderr.write("unknown bundle: " + sys.argv[2] + "\n")
    sys.stderr.write("available: " + ", ".join(sorted(b.keys())) + "\n")
    sys.exit(2)
print(",".join(b[sys.argv[2]]["tools"]))
' "$BUNDLES_FILE" "$arg"
      ;;
    tool)  echo "$arg";;
    tools) echo "$arg";;
  esac
}

tools_csv="$(resolve_tools)"
IFS=',' read -ra tools <<<"$tools_csv"

for tool in "${tools[@]}"; do
  detect="$INSTALLS_ROOT/$tool/detect.sh"
  install="$INSTALLS_ROOT/$tool/install.sh"
  install_md="$INSTALLS_ROOT/$tool/INSTALL.md"
  if [ ! -x "$detect" ] || [ ! -x "$install" ]; then
    echo "ERROR: missing scripts for tool '$tool' under $INSTALLS_ROOT/$tool/" >&2
    exit 3
  fi
  if bash "$detect" >/dev/null 2>&1; then
    echo "[OK]   $tool already installed"
    continue
  fi
  echo "[GO]   installing $tool"
  if ! bash "$install"; then
    code=$?
    echo "[FAIL] $tool install exited $code -- see $install_md" >&2
    exit "$code"
  fi
  if ! bash "$detect" >/dev/null 2>&1; then
    echo "[FAIL] $tool: install.sh exited 0 but detect.sh still fails -- see $install_md" >&2
    exit 4
  fi
  echo "[DONE] $tool installed"
done
echo "all tools ready"
