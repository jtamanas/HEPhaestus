#!/usr/bin/env bash
# _blocker.sh — emit_blocker() helper for higgstools-install scripts.
# Source this file; do not execute directly.
#
# Usage: emit_blocker <code> <mode> <message> [user_instruction]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
#
# Examples:
#   emit_blocker HIGGSTOOLS_TOOLCHAIN_MISSING fatal "gfortran not found." \
#       "Install gfortran: brew install gcc or apt install gfortran"
#   emit_blocker HIGGSTOOLS_BUILD_FAILED fatal "CMake build failed."

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
