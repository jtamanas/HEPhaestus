#!/usr/bin/env bash
# _blocker.sh — emit_blocker() helper for feynrules-install scripts.
# Source this file; do not execute directly.
#
# Usage: emit_blocker <code> <mode> <message> [user_instruction]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
#
# Examples:
#   emit_blocker FEYNRULES_DOWNLOAD_FAILED fatal "Download failed after 2 retries." \
#       "Check your network connection and retry bash _shared/installs/feynrules/install.sh install."
#   emit_blocker FEYNRULES_SMOKE_TEST_FAILED fatal "FeynRules smoke test returned no version."

emit_blocker() {
  local code="$1"
  local mode="$2"
  local message="$3"
  local user_instruction="${4:-}"

  python3 - "$code" "$mode" "$message" "$user_instruction" <<'PY' >&2
import json, sys

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

code, mode, message, user_instruction = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

blocker = {
    "code": code,
    "mode": mode,
    "message": message,
}
if user_instruction:
    blocker["user_instruction"] = user_instruction

print(json.dumps(blocker, separators=(",", ":")))
PY
}
