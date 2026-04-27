#!/usr/bin/env bash
# One-line shim: sources the canonical shared copy.
# Single source of truth is at plugins/shared/install-helpers/_common.sh.
# This shim exists so any external consumer that directly sources this path
# continues to work without change (reviewer judgment-call #2).
#
# Path: from plugins/hep-ph-toolkit/skills/install/scripts/ go up 4 levels to
# reach plugins/, then descend to shared/install-helpers/.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
