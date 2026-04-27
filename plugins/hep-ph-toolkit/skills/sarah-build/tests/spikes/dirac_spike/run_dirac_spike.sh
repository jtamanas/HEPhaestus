#!/usr/bin/env bash
# T05b spike runner — loads the DiracSpike fixture under wolframscript and
# verifies Start["DiracSpike"] + CheckModel[EWSB] run without aborting.
#
# Env overrides:
#   SARAH_DIR       default /Users/yianni/SARAH/SARAH-4.15.3
#   WOLFRAMSCRIPT   default /usr/local/bin/wolframscript

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SARAH_DIR=${SARAH_DIR:-/Users/yianni/SARAH/SARAH-4.15.3}
WOLFRAMSCRIPT=${WOLFRAMSCRIPT:-/usr/local/bin/wolframscript}

if [[ ! -d "$SARAH_DIR" ]]; then
  echo "ERROR: SARAH_DIR not found: $SARAH_DIR" >&2
  exit 2
fi
if [[ ! -x "$WOLFRAMSCRIPT" ]]; then
  echo "ERROR: wolframscript not executable: $WOLFRAMSCRIPT" >&2
  exit 2
fi

# Stage the fixture into a temp tree so SARAH sees the expected
# <InputDir>/<ModelName>/<ModelName>.m layout.  We prepend this temp
# tree to SARAH[InputDirectories] at runtime.
STAGE_ROOT=$(mktemp -d -t dirac_spike.XXXXXX)
trap 'rm -rf "$STAGE_ROOT"' EXIT

mkdir -p "$STAGE_ROOT/DiracSpike"
cp "$SCRIPT_DIR/DiracSpike.m"  "$STAGE_ROOT/DiracSpike/DiracSpike.m"
cp "$SCRIPT_DIR/parameters.m"  "$STAGE_ROOT/DiracSpike/parameters.m"
cp "$SCRIPT_DIR/particles.m"   "$STAGE_ROOT/DiracSpike/particles.m"

cat <<EOF
[dirac_spike] SARAH_DIR     = $SARAH_DIR
[dirac_spike] WOLFRAMSCRIPT = $WOLFRAMSCRIPT
[dirac_spike] STAGE_ROOT    = $STAGE_ROOT
EOF

# Mathematica idiom (see tests/spikes/dirac_spike/run_spike.m for the
# full load sequence).  We pass SARAH_DIR + STAGE_ROOT as script
# arguments via -file / -args.
"$WOLFRAMSCRIPT" -file "$SCRIPT_DIR/run_spike.m" "$SARAH_DIR" "$STAGE_ROOT"
STATUS=$?

echo "[dirac_spike] wolframscript exit status: $STATUS"
exit "$STATUS"
