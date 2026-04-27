#!/usr/bin/env bash
# Stub: touch a sentinel file to prove the stub was invoked, then emit configured
SENTINEL_FILE="${HEPPH_SENTINEL_FILE:-/tmp/drake_sentinel_was_touched}"
touch "$SENTINEL_FILE"
echo '{"status": "configured", "path": "/fake/drake"}'
