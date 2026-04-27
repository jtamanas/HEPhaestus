#!/usr/bin/env bash
# T05a spike driver — loads the Majorana MatterSector fixture into SARAH via
# wolframscript and checks that Start[] and CheckModel[] succeed.
#
# Usage: bash run_spike.sh
#
# Exit codes:
#   0 — SARAH loaded the model and CheckModel[] reported no abort
#   1 — Start[] failed with ModelFile::Aborted or CheckModel[] raised an error
#   2 — environment missing (wolframscript / SARAH path)

set -euo pipefail

SARAH_PATH="${SARAH_PATH:-/Users/yianni/SARAH/SARAH-4.15.3}"
WOLFRAMSCRIPT="${WOLFRAMSCRIPT:-/usr/local/bin/wolframscript}"
SPIKE_NAME="Spike"
PRIVATE_DIR="$SARAH_PATH/Private-Models/$SPIKE_NAME"
SPIKE_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$WOLFRAMSCRIPT" ]]; then
    echo "ERROR: wolframscript not found at $WOLFRAMSCRIPT" >&2
    exit 2
fi
if [[ ! -d "$SARAH_PATH" ]]; then
    echo "ERROR: SARAH_PATH not a directory: $SARAH_PATH" >&2
    exit 2
fi

mkdir -p "$PRIVATE_DIR"
# Stage the spike as Spike/Spike.m + particles.m + parameters.m
cp -f "$SPIKE_SRC_DIR/majorana_spike.m" "$PRIVATE_DIR/$SPIKE_NAME.m"
cp -f "$SPIKE_SRC_DIR/particles.m"      "$PRIVATE_DIR/particles.m"
cp -f "$SPIKE_SRC_DIR/parameters.m"     "$PRIVATE_DIR/parameters.m"

echo "[run_spike] staged $SPIKE_NAME at $PRIVATE_DIR"
echo "[run_spike] invoking wolframscript..."

# Capture full transcript.  Mathematica's Message[] writes to stderr via
# $Output on wolframscript -code; we redirect both to stdout for grep.
set +e
"$WOLFRAMSCRIPT" -code "
  AppendTo[\$Path, \"$SARAH_PATH\"];
  Needs[\"SARAH\`\"];
  Print[\"[wolframscript] SARAH loaded; \$sarahDir = \", \$sarahDir];
  Start[\"$SPIKE_NAME\"];
  Print[\"[wolframscript] Start[] returned\"];
  CheckModel[];
  Print[\"[wolframscript] CheckModel[] returned\"];
  Print[\"[wolframscript] SPIKE_OK\"];
" 2>&1
status=$?
set -e

echo "[run_spike] wolframscript exit status: $status"
exit $status
