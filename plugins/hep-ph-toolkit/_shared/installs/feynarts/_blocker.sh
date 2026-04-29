#!/usr/bin/env bash
# _blocker.sh — emit_blocker() helper for feynarts-install scripts.
# Source this file; do not execute directly.
#
# Usage: emit_blocker <code> <mode> <message> [user_instruction] [context_json]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
#
# Examples:
#   emit_blocker FEYNARTS_DOWNLOAD_FAILED fatal "Download failed after 2 retries." \
#       "Check your network connection and retry /feynarts-install install."
#   emit_blocker FEYNARTS_SMOKE_TEST fatal "FeynArts smoke test returned no version."

emit_blocker() {
  local code="$1"
  local mode="$2"
  local message="$3"
  local user_instruction="${4:-}"
  local context_json="${5:-}"

  python3 - "$code" "$mode" "$message" "$user_instruction" "$context_json" <<'PY' >&2
import json, sys

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

code, mode, message, user_instruction, context_json = \
    sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]

blocker = {
    "code": code,
    "mode": mode,
    "message": message,
}
if user_instruction:
    blocker["user_instruction"] = user_instruction
if context_json:
    try:
        blocker["context"] = json.loads(context_json)
    except json.JSONDecodeError:
        blocker["context_raw"] = context_json

print(json.dumps(blocker, separators=(",", ":")))
PY
}
