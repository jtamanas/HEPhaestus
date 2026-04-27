#!/usr/bin/env bash
# install.sh — thin orchestrator dispatching to install_feynrules.sh.
#
# Subcommands:
#   detect              Print JSON state (no side-effects)
#   use-path <dir>      Register an existing FeynRules install
#   install [dir]       Full auto-install (default dir: ~/feynrules-current)
#   validate            Alias for detect
#
# All behaviour, blockers, and status JSON are produced by install_feynrules.sh.
# This wrapper exists so callers can standardize on `scripts/install.sh <cmd>`.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/install_feynrules.sh" "$@"
