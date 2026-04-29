#!/usr/bin/env bash
# _blocker.sh — emit_blocker() helper for micromegas-install scripts.
# Source this file; do not execute directly.
#
# Usage: emit_blocker <code> <mode> <message> [user_instruction] [context_json]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
#
# The optional 5th argument context_json must be a valid JSON object string,
# e.g. '{"attempted_url":"https://...","sdkroot":"/Library/..."}'.
# micrOMEGAs-specific context fields: attempted_url, sdkroot, make_log_tail.
#
# Examples:
#   emit_blocker MICROMEGAS_DOWNLOAD_FAILED fatal "Download failed after 2 retries." \
#       "Check your network connection and retry bash _shared/installs/micromegas/install.sh install."
#   emit_blocker MICROMEGAS_MACOS_SDK_MISMATCH fatal "xcrun SDK missing." \
#       "Install Xcode Command Line Tools: xcode-select --install" \
#       '{"sdkroot":""}'

emit_blocker() {
  local code="$1"
  local mode="$2"
  local message="$3"
  local user_instruction="${4:-}"
  local context_json="${5:-}"

  python3 - "$code" "$mode" "$message" "$user_instruction" "$context_json" <<'PY' >&2
import json, sys

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

code, mode, message, user_instruction, context_json = (
    sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
)

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
        blocker["context"] = {"raw": context_json}

# Best-effort schema validation when jsonschema is importable.
try:
    import jsonschema
    from pathlib import Path
    schema_path = (
        Path(__file__).resolve().parents[4]
        / "_shared" / "blocker.schema.json"
    )
    if schema_path.exists():
        import json as _json
        with open(schema_path) as f:
            schema = _json.load(f)
        jsonschema.validate(blocker, schema)
except Exception:
    pass  # best-effort only

print(json.dumps(blocker, separators=(",", ":")))
PY
}
