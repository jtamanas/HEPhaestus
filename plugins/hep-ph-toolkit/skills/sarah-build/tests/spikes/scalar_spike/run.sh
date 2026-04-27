#!/bin/bash
# T05c spike runner.
#
# Stages tests/spikes/scalar_spike/{scalar_spike,parameters,particles}.m
# into $SARAH_DIR/Private-Models/ScalarSpike/ and runs
#
#     Start["ScalarSpike"]; CheckModel;
#
# under wolframscript. The staged files live in the first writable
# entry of SARAH[InputDirectories] so Start[] can find them without
# any PATH hackery (RC1 precondition for the real generator).
#
# Usage: tests/spikes/scalar_spike/run.sh [SARAH_DIR] [WOLFRAMSCRIPT]
# Defaults: SARAH_DIR=/Users/yianni/SARAH/SARAH-4.15.3
#           WOLFRAMSCRIPT=/usr/local/bin/wolframscript
set -euo pipefail

SARAH_DIR="${1:-/Users/yianni/SARAH/SARAH-4.15.3}"
WOLFRAMSCRIPT="${2:-/usr/local/bin/wolframscript}"
SPIKE_DIR="$(cd "$(dirname "$0")" && pwd)"
STAGE_DIR="$SARAH_DIR/Private-Models/ScalarSpike"

mkdir -p "$STAGE_DIR"
cp "$SPIKE_DIR/scalar_spike.m" "$STAGE_DIR/ScalarSpike.m"
cp "$SPIKE_DIR/parameters.m"   "$STAGE_DIR/parameters.m"
cp "$SPIKE_DIR/particles.m"    "$STAGE_DIR/particles.m"

# Clear any stale .mx cache from prior runs so we validate a fresh load.
rm -f "$STAGE_DIR"/*.mx

"$WOLFRAMSCRIPT" -code "
SetDirectory[\"$SARAH_DIR\"];
Needs[\"SARAH\`\"];
Start[\"ScalarSpike\"];
CheckModel;
Print[\"T05C_SPIKE_OK\"];
" 2>&1
