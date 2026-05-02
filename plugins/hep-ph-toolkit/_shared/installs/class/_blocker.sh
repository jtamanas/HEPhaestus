#!/usr/bin/env bash
# _blocker.sh — emit_blocker() helper for class-install scripts.
# Source this file; do not execute directly.
#
# Usage: emit_blocker <code> <mode> <message> [user_instruction]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
#
# Blocker codes defined for CLASS:
#   CLASS_TOOLCHAIN_MISSING    fatal     cc/make/python3/Cython absent
#   CLASS_OFFLINE_NO_CACHE     fatal     HEPPH_NO_NETWORK=1 and no offline cache
#   CLASS_DOWNLOAD_FAILED      fatal     git clone failed
#   CLASS_BUILD_FAILED         fatal     make non-zero (exits $EXIT_CLASS_BUILD=30)
#   CLASSY_PIP_INSTALL_FAILED  recoverable  pip install classy failed
#   CLASSY_IMPORT_FAILED       fatal     python3 -c "import classy" fails
#   CLASS_SMOKE_FAILED         fatal     c.age() assertion out of range (exits $EXIT_SMOKE=15)
#   CLASS_PATH_INVALID         fatal     use-path target missing class binary (exits $EXIT_BAD_PATH=16)

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
