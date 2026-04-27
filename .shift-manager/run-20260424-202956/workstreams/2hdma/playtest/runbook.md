# PT1 Runbook — 2HDM+a Playtest (JIT-distilled)

## Environment
- WORKTREE: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-playtest/
- Branch: 2hdma/playtest-20260424 (from 2hdma/prep-20260424 tip 2c9dd31)
- SARAH_ROOT: /Users/yianni/SARAH/SARAH-4.15.3
- MG5_PATH: /Users/yianni/MG5_aMC_v3_5_6
- MadDM: /Users/yianni/MG5_aMC_v3_5_6/PLUGIN/maddm (v3.2.13)

## Preflight
```bash
python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"
# Result: OK
```

## Phase 1: Clean + Deploy SARAH Fixture
```bash
# Move existing TwoHdmAfix to quarantine
mv $SARAH_ROOT/Models/TwoHdmAfix /path/to/quarantine/TwoHdmAfix-pre-$(date +%s)
# Deploy fixture
mkdir -p $SARAH_ROOT/Models/TwoHdmAfix
cp plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/*.m $SARAH_ROOT/Models/TwoHdmAfix/
```

## Phase 2: SARAH MakeUFO (lockf on macOS, not flock)
```bash
# NOTE: flock not available on macOS; use lockf
LOCK=/path/to/locks/sarah.lock
touch $LOCK && chmod 600 $LOCK
lockf -k -t 120 $LOCK \
  wolframscript -code "AppendTo[\$Path, \"$SARAH_ROOT\"]; <<SARAH\`; Start[\"TwoHdmAfix\"]; MakeUFO[]; Quit[]"
# Output: $SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/
# Time: ~50 seconds
```

## Phase 3: Vertex Sanity
```bash
grep -c "chi" $SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/vertices.py
# Returns 3 (chi-chi-Ah1, chi-chi-Ah2, chi-chi-Ah3)
```

## Phase 4: MG5 Output + .output_marker
```bash
touch demo_output/2hdm-a/playtest_log/.output_marker
cat > /tmp/mg5_setup.cmd << EOF
import model $SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO
define darkmatter chi
generate relic_density
output demo_output/2hdm-a/maddm_run
exit
EOF
mg5_aMC --mode=maddm /tmp/mg5_setup.cmd
# Writes Cards/param_card.dat
```

## Phase 5: Patch param_card
```bash
python3 plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py \
  demo_output/2hdm-a/maddm_run \
  --Mchi 100.0 --Ma-Ah2 400.0 --gchi 1.0 --tan-beta 10.0
touch demo_output/2hdm-a/playtest_log/.patched
```

**CRITICAL BUG (2hdma-001)**: patcher regex fails on fresh MG5 cards.
Must manually fix these blocks after patcher runs:
- `DMSECTOR`: set index 1=100 (mchi), index 2=1.0 (gchi)
- `PHASES`: set index 1=1.0 (rpchiR)
- `MASS`: set BSM masses (Ah2=400, Ah3=500, Mh1=125, Mh2=600, Hm1=80.4, Hm2=550, chi=100)
- `HMIX`: set 102=vd, 103=vu from tan_beta
- `ZAMIX`, `ZHMIX`, `ZPMIX`: set from analytical mixing matrices
- `DECAY` BSM widths: ≥1 GeV (except Wchi=0.0 locked)

## Phase 6: MadDM Relic Density Launch
```bash
# NOTE: must use 'launch <out_dir> -f' not 'launch -f'
echo "launch demo_output/2hdm-a/maddm_run -f" > /tmp/mg5_launch.cmd
mg5_aMC --mode=maddm /tmp/mg5_launch.cmd 2>&1 | tee demo_output/2hdm-a/playtest_log/run.log
```

## Phase 7: Parse Results
```
Results in: demo_output/2hdm-a/maddm_run/output/run_04/MadDM_results.txt
Omega h^2 = 10.494
Dominant channel: chichibar_wphp = 49.62%, chichibar_wmhm = 49.62%
chichibar_bbx = 0.65%
```

## Known Issues
1. **2hdma-001** (BLOCKER): patcher regex fails — must manually fix param_card
2. **2hdma-002** (WARNING): flock not available on macOS; use lockf
3. **2hdma-003** (WARNING): Omega h^2 3.4% outside synthesis band; bbx<30%
4. **2hdma-004** (MINOR): launch script requires 'launch <out_dir> -f' form
