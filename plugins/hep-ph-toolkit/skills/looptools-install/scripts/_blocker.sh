#!/usr/bin/env bash
# _blocker.sh — emit_blocker helper for /looptools-install.
# Sourced by install.sh, check_gfortran.sh, probe_looptools.sh.
# Usage: emit_blocker <code> <mode> <message> [user_instruction]
#
# Prints a single-line JSON blocker to stderr conforming to
# plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.

emit_blocker() {
  local code="$1"
  local mode="$2"
  local message="$3"
  local user_instruction="${4:-}"

  local _esc_message
  _esc_message="$(printf '%s' "$message" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
  _esc_message="${_esc_message:1:${#_esc_message}-2}"

  if [ -n "$user_instruction" ]; then
    local _esc_ui
    _esc_ui="$(printf '%s' "$user_instruction" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
    _esc_ui="${_esc_ui:1:${#_esc_ui}-2}"
    printf '{"code":"%s","mode":"%s","message":"%s","user_instruction":"%s"}\n' \
      "$code" "$mode" "$_esc_message" "$_esc_ui" >&2
  else
    printf '{"code":"%s","mode":"%s","message":"%s"}\n' \
      "$code" "$mode" "$_esc_message" >&2
  fi
}

emit_blocker_with_context() {
  # Emit blocker with a context JSON object (already JSON-encoded string).
  # Usage: emit_blocker_with_context <code> <mode> <message> <context_json>
  local code="$1"
  local mode="$2"
  local message="$3"
  local context_json="$4"

  local _esc_message
  _esc_message="$(printf '%s' "$message" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
  _esc_message="${_esc_message:1:${#_esc_message}-2}"

  printf '{"code":"%s","mode":"%s","message":"%s","context":%s}\n' \
    "$code" "$mode" "$_esc_message" "$context_json" >&2
}
