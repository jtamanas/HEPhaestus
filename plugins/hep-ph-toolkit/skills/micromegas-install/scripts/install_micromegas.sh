#!/usr/bin/env bash
# install_micromegas.sh — dispatcher for /micromegas-install skill.
#
# Usage:
#   install_micromegas.sh detect
#   install_micromegas.sh use-path <dir> [--calchep-path <dir>]
#   install_micromegas.sh install [parent_dir] [--full-smoke]
#   install_micromegas.sh validate
#
# The `validate` subcommand re-validates the currently configured install
# (markers + light smoke) without writing config. Emits
# MICROMEGAS_PATH_INVALID if the path is missing from config or on disk.
#
# Exit codes mirror those returned by the sub-commands.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="micromegas-install"

if [ $# -lt 1 ]; then
  err "Usage: install_micromegas.sh {detect|use-path|install|validate} [args...]"
  exit $EXIT_GENERIC
fi

subcmd="$1"; shift

case "$subcmd" in
  detect)
    exec bash "$SCRIPT_DIR/detect.sh" "$@"
    ;;
  use-path)
    exec bash "$SCRIPT_DIR/use_path.sh" "$@"
    ;;
  install)
    exec bash "$SCRIPT_DIR/install_impl.sh" "$@"
    ;;
  validate)
    exec bash "$SCRIPT_DIR/validate.sh" "$@"
    ;;
  *)
    err "Unknown subcommand: $subcmd. Expected detect|use-path|install|validate."
    exit $EXIT_GENERIC
    ;;
esac
