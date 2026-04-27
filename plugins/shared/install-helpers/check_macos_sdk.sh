#!/usr/bin/env bash
# check_macos_sdk.sh — standalone wrapper around check_macos_sdk() in _common.sh.
# Usage: ./check_macos_sdk.sh
# Output: one-line JSON to stdout; exit code is check_macos_sdk's return value.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/_common.sh"
check_macos_sdk
