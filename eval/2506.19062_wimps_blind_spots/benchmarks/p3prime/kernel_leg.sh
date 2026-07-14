#!/bin/bash
# Run the projection kernel for one leg: driver -> amp_dd.m -> extract C_ours.
# Usage: kernel_leg.sh <legname>
set -x
L=$1
WT=/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-worktree
SCR=/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch
BM=$WT/eval/2506.19062_wimps_blind_spots/benchmarks
DRV=$WT/plugins/hep-ph-toolkit/skills/looptools/scripts/run_eval_sd.wls
PROJ=$WT/plugins/hep-ph-toolkit/skills/looptools/scripts/sd_projection.wl
AMP=/Users/yianni/.claude/jobs/c703354a/tmp/subexpr-fix/reduce_chi1/amp_reduced.m
LT=/Users/yianni/LoopTools/LoopTools-2.16
export HEPPH_RUN_WOLFRAM_TESTS=1

cd $SCR/$L
echo "=== $L DRIVER $(date +%T) ==="
wolframscript -script "$DRV" "$AMP" "$SCR/$L/point.json" none "$SCR/$L/eval_output.json" "$LT" > $SCR/$L/driver.log 2>&1
echo "$L driver rc=$? ($(date +%T))"
ls -la $SCR/$L/amp_dd.m || { echo "$L AMPDD-MISSING"; exit 9; }
echo "=== $L EXTRACT $(date +%T) ==="
MCHI=$(python3 -c "import json;print(json.load(open('$SCR/$L/point.json'))['m_dm_gev'])")
wolframscript -script $BM/p3_extract_cours.wls "$PROJ" "$AMP" "$SCR/$L/amp_dd.m" "$MCHI" 4.67e-3 "$SCR/$L/cours_extract.json"
echo "$L extract rc=$? ($(date +%T))"
cat $SCR/$L/cours_extract.json
