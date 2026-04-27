#!/usr/bin/env bash
# Emit a blocker JSON document to stdout.
# Usage: _blocker.sh <CODE> <message> [<context-json-object>] [recoverable]
# Always exits 0 (caller decides exit code).

set -euo pipefail
# Note: _blocker.sh is standalone — it does NOT source _common.sh (no circular dep)
CODE="${1:?blocker code required}"
MESSAGE="${2:?message required}"
CONTEXT="${3:-{}}"
SEVERITY="${4:-fatal}"

# Validate severity
case "$SEVERITY" in
  fatal|recoverable) ;;
  *) SEVERITY="fatal" ;;
esac

# Escape message for JSON (basic: replace \ " newline)
MSG_ESC="$(printf '%s' "$MESSAGE" | python3 -c "
import sys, json
print(json.dumps(sys.stdin.read())[1:-1]
)")"

printf '{"code":"%s","mode":"%s","message":"%s","context":%s}\n' \
  "$CODE" "$SEVERITY" "$MSG_ESC" "$CONTEXT"
