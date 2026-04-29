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

# Halt-status JSON keys we honor from install.sh stdout. When install.sh
# emits a status of activation_required (SARAH/Wolfram) or
# manual_download_required (DRAKE Anubis gate), the orchestrator surfaces
# the user_instruction and halts the bundle without re-running detect.
# The user resumes by re-invoking /install <bundle> after the manual step.
parse_halt_status() {
  python3 - "$1" <<'PY'
import json, re, sys
text = sys.argv[1]
# Pull the last JSON object on stdout (install.sh may emit log lines too).
candidates = re.findall(r'\{[^{}]*"status"[^{}]*\}', text)
status = ""
instruction = ""
message = ""
for c in reversed(candidates):
    try:
        d = json.loads(c)
    except Exception:
        continue
    s = d.get("status", "")
    if s in ("activation_required", "manual_download_required"):
        status = s
        instruction = d.get("user_instruction", "")
        message = d.get("message", "")
        break
print(status)
print(instruction)
print(message)
PY
}

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
  install_out_file="$(mktemp)"
  set +e
  bash "$install" install 2> >(tee /dev/stderr) > >(tee "$install_out_file")
  code=$?
  set -e
  install_out="$(cat "$install_out_file")"
  rm -f "$install_out_file"

  # Special case: hepforge Anubis gate (DRAKE) → exit 18.
  if [ "$code" -eq 18 ]; then
    halt_info="$(parse_halt_status "$install_out")"
    halt_status="$(printf '%s\n' "$halt_info" | sed -n '1p')"
    halt_instruction="$(printf '%s\n' "$halt_info" | sed -n '2p')"
    halt_message="$(printf '%s\n' "$halt_info" | sed -n '3p')"
    echo "[HALT] $tool requires manual action (status=${halt_status:-manual_download_required})" >&2
    [ -n "$halt_message" ]     && echo "       $halt_message" >&2
    [ -n "$halt_instruction" ] && echo "       Next step: $halt_instruction" >&2
    echo "       See $install_md. Re-invoke /install <bundle> after completing the manual step." >&2
    exit 18
  fi

  if [ "$code" -ne 0 ]; then
    echo "[FAIL] $tool install exited $code -- see $install_md" >&2
    exit "$code"
  fi

  # exit 0 path: check for activation_required (SARAH/Wolfram) or
  # manual_download_required emitted with exit 0 (defensive — DRAKE now
  # uses exit 18, but legacy code paths may still emit the JSON).
  halt_info="$(parse_halt_status "$install_out")"
  halt_status="$(printf '%s\n' "$halt_info" | sed -n '1p')"
  if [ -n "$halt_status" ]; then
    halt_instruction="$(printf '%s\n' "$halt_info" | sed -n '2p')"
    halt_message="$(printf '%s\n' "$halt_info" | sed -n '3p')"
    echo "[HALT] $tool requires manual action (status=$halt_status)" >&2
    [ -n "$halt_message" ]     && echo "       $halt_message" >&2
    [ -n "$halt_instruction" ] && echo "       Next step: $halt_instruction" >&2
    echo "       See $install_md. Re-invoke /install <bundle> after completing the manual step." >&2
    exit 18
  fi

  if ! bash "$detect" >/dev/null 2>&1; then
    echo "[FAIL] $tool: install.sh exited 0 but detect.sh still fails -- see $install_md" >&2
    exit 4
  fi
  echo "[DONE] $tool installed"
done
echo "all tools ready"
