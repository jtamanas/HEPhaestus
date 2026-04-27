#!/usr/bin/env bash
# Orchestrator: dispatches to the four per-tool install scripts in dependency
# order (wolfram -> sarah -> spheno -> mg5). The AskUserQuestion loop lives in
# the skill prose; this script only does `detect` / `use-path` / `install` /
# `detect-all` and delegates to per-tool scripts. Keeps bash out of SKILL.md.
set -euo pipefail

_LOG_TAG="install"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
. "$SCRIPT_DIR/_common.sh"

# bundle-preflight: see docs/wolfram-ux-contract.md#bundle-preflight-schema
TOOL_ORDER=(wolfram sarah spheno mg5)

script_for() {
  case "$1" in
    wolfram) echo "$SCRIPT_DIR/install_wolfram.sh" ;;
    sarah)   echo "$SCRIPT_DIR/install_sarah.sh" ;;
    spheno)  echo "$SCRIPT_DIR/install_spheno.sh" ;;
    mg5)     echo "$SCRIPT_DIR/install_mg5.sh" ;;
    *)       err "Unknown tool: $1"; exit 2 ;;
  esac
}

cmd_detect_all() {
  # Emit one JSON object per tool, prefixed with the tool name, in order.
  # The skill prose reads these line-by-line and drives AskUserQuestion.
  for tool in "${TOOL_ORDER[@]}"; do
    local out
    out="$("$(script_for "$tool")" detect 2>/dev/null || echo '{"status":"error"}')"
    printf '{"tool":"%s","result":%s}\n' "$tool" "$out"
  done
}

cmd_detect() {
  local tool="$1"
  "$(script_for "$tool")" detect
}

cmd_use_path() {
  local tool="$1"; shift
  "$(script_for "$tool")" use-path "$@"
}

cmd_install() {
  local tool="$1"; shift
  "$(script_for "$tool")" install "$@"
}

cmd_bundle_preflight() {
  local raw="${1:-}"
  # Delegate entirely to python3 (bundle data and logic).
  # BUNDLES and WOLFRAM_BLOCKERS are defined here verbatim per
  # docs/wolfram-ux-contract.md#bundle-preflight-truth-table:
  #   declare -A BUNDLES=(
  #     [demo]="wolfram sarah spheno mg5"
  #     [bsm-spectrum]="wolfram sarah spheno"
  #     [dm-relic]="mg5 maddm micromegas"
  #     [dm-narrow-resonance]="mg5 maddm micromegas drake"
  #     [one-loop]="looptools"
  #   )
  #   WOLFRAM_BLOCKERS=(wolfram sarah drake feynrules formcalc feynarts)
  python3 - "$raw" <<'PYEOF'
import sys, json

BUNDLES = {
    "demo":               "wolfram sarah spheno mg5",
    "bsm-spectrum":       "wolfram sarah spheno",
    "dm-relic":           "mg5 maddm micromegas",
    "dm-narrow-resonance":"mg5 maddm micromegas drake",
    "one-loop":           "looptools",
}
WOLFRAM_BLOCKERS = {"wolfram", "sarah", "drake", "feynrules", "formcalc", "feynarts"}

raw = sys.argv[1] if len(sys.argv) > 1 else ""
bundle_id = raw.strip().lower()

if not bundle_id or bundle_id not in BUNDLES:
    msg = json.dumps({
        "error": "unknown bundle: " + bundle_id,
        "known": ["demo", "bsm-spectrum", "dm-relic", "dm-narrow-resonance", "one-loop"],
    }, separators=(',', ':'))
    print(msg, file=sys.stderr)
    sys.exit(2)

tools = BUNDLES[bundle_id].split()
wolfram_dependents = [t for t in tools if t != "wolfram" and t in WOLFRAM_BLOCKERS]
requires_wolfram = ("wolfram" in tools) or (len(wolfram_dependents) > 0)

print(json.dumps({
    "bundle": bundle_id,
    "tools": tools,
    "requires_wolfram": requires_wolfram,
    "wolfram_dependents": wolfram_dependents,
}, separators=(',', ':')))
PYEOF
}

cmd_validate() {
  # Run the Python validator against the current config.
  python3 "$SCRIPT_DIR/check_config.py" "${1:-}"
}

cmd_python_deps() {
  # Ensure matplotlib + numpy importable in the configured Python. Pip-installs
  # if missing. Records matplotlib_version / numpy_version / python_deps_checked_at
  # into the shared config. Fails loudly if pip install can't succeed.
  python3 "$SCRIPT_DIR/check_python_deps.py" "$@"
}

usage() {
  cat >&2 <<EOF
Usage: demo-install.sh <command> [args]

Commands:
  detect-all                       Print one JSON status line per tool (wolfram, sarah, spheno, mg5)
  detect <tool>                    Print JSON status for a single tool
  use-path <tool> <path>           Register an existing install in config
  install <tool> [dir]             Auto-install a single tool (mg5 / sarah / spheno; wolfram prints instructions)
  validate [--json]                Validate the config against all four tools (see check_config.py)
  python-deps [--python PATH]      Ensure matplotlib + numpy importable; pip-install if missing (see check_python_deps.py)
  bundle-preflight <bundle>        Emit JSON describing bundle membership and Wolfram dependency. See docs/wolfram-ux-contract.md

Tools:  wolfram  sarah  spheno  mg5
EOF
  exit 2
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    detect-all) cmd_detect_all ;;
    detect)     cmd_detect "${1:-}" ;;
    use-path)   cmd_use_path "${1:-}" "${2:-}" ;;
    install)    cmd_install "${1:-}" "${2:-}" ;;
    validate)         cmd_validate "${1:-}" ;;
    python-deps)      cmd_python_deps "$@" ;;
    bundle-preflight) cmd_bundle_preflight "${1:-}" ;;
    *)                usage ;;
  esac
}

main "$@"
