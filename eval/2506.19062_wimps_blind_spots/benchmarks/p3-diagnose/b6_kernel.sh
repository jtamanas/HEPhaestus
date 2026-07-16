#!/bin/bash
# B6 per-(leg,sector,channel) DD projection. Mirrors d1_kernel.sh.
# Usage: b6_kernel.sh <leg L2|L3> <sector db|cb> <channel Wpure|Zpure|Yukawa|WwithHp|remainder>
set -x
LEG=$1; SEC=$2; CHAN=$3
WT=/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-worktree
BSC=/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-scratch
PSC=/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch
BM=$WT/eval/2506.19062_wimps_blind_spots/benchmarks
DRV=$WT/plugins/hep-ph-toolkit/skills/looptools/scripts/run_eval_sd.wls
PROJ=$WT/plugins/hep-ph-toolkit/skills/looptools/scripts/sd_projection.wl
AMP=$BSC/${SEC}_${CHAN}.m
LT=/Users/yianni/LoopTools/LoopTools-2.16
export HEPPH_RUN_WOLFRAM_TESTS=1
D=$BSC/runs/${LEG}_${SEC}_${CHAN}; mkdir -p "$D"; cd "$D"
[ -f amp_dd.m ] && rm -f amp_dd.m
echo "=== $LEG/$SEC/$CHAN DRIVER $(date +%T) ==="
wolframscript -script "$DRV" "$AMP" "$PSC/$LEG/point.json" none "$D/eval_output.json" "$LT" > driver.log 2>&1
echo "driver rc=$? ($(date +%T))"
ls -la amp_dd.m 2>/dev/null || { echo "$LEG/$SEC/$CHAN AMPDD-MISSING"; tail -8 driver.log; exit 9; }
MCHI=$(python3 -c "import json;print(json.load(open('$PSC/$LEG/point.json'))['m_dm_gev'])")
wolframscript -script $BM/p3_extract_cours.wls "$PROJ" "$AMP" "$D/amp_dd.m" "$MCHI" 4.67e-3 "$D/cours.json" > extract.log 2>&1
echo "extract rc=$? ($(date +%T))"
python3 -c "import json;d=json.load(open('$D/cours.json'));print('  $LEG/$SEC/$CHAN: C_scalar_re=%s C_scalar_im=%s completeness=%s'%(d.get('C_scalar_full_re'),d.get('C_scalar_full_im'),d.get('full_basis_completeness_rel_residual')))"
