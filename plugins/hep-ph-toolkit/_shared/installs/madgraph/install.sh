#!/usr/bin/env bash
# install.sh — _shared/installs/madgraph entry point.
#
# Subcommands:
#   detect              JSON status of existing MG5 install
#   use-path <path>     Register an existing mg5_aMC binary in config
#   install [dir]       Auto-install MadGraph5_aMC@NLO (default ~/MG5_aMC)
#   verify              Re-verify the configured install
#
# Implementation: thin wrapper that delegates to the canonical
# `skills/install/scripts/install_mg5.sh`. The canonical script holds the
# detect/install/verify logic (URL pin, version probe, smoke test). We
# present the standard `_shared/installs/<tool>/install.sh` interface so
# the runner self-healing preflight pattern works for MadGraph too.
#
# Note: MadDM's install.sh has its own MG5 install path (it shells out
# to MG5's `install maddm` command, which builds MG5 itself when
# missing). MadDM does not call this wrapper today; we keep its
# transitive path working by leaving the maddm install logic untouched.
# When MadDM users prefer to seed MG5 separately first, /install madgraph
# (or any madgraph-runner preflight) will use this wrapper.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MG5="$SCRIPT_DIR/../../../skills/install/scripts/install_mg5.sh"

if [ ! -x "$INSTALL_MG5" ]; then
  echo "ERROR: $INSTALL_MG5 not found or not executable" >&2
  exit 3
fi

exec bash "$INSTALL_MG5" "$@"
