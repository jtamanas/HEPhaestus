# PT2 Log — 2HDM+a

**Run at:** 2026-04-25T08:21:31.222305+00:00
**Worktree:** /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2
**Branch:** 2hdma/fix-r1-20260425 (detached HEAD)

**Band:** lo=9.9693 hi=11.0187 (source: fixture-calibration ±5% post-patcher Ωh²=10.494 (iseed_status=unset→ODE-deterministic; single probe; PhasechiR=1.0 from T2 fix a96940818; same as PT1 manually-corrected run; source: T2_IMPL_NOTE.md + run-20260424-202956/workstreams/2hdma/playtest/relic.json))

## Band snapshot

```json
{
  "lo": 9.9693,
  "hi": 11.0187,
  "source": "fixture-calibration \u00b15% post-patcher \u03a9h\u00b2=10.494 (iseed_status=unset\u2192ODE-deterministic; single probe; PhasechiR=1.0 from T2 fix a96940818; same as PT1 manually-corrected run; source: T2_IMPL_NOTE.md + run-20260424-202956/workstreams/2hdma/playtest/relic.json)",
  "basis": "fixture-calibration"
}
```

## Steps

[2026-04-25T08:21:22.150121+00:00] ======================================================================
[2026-04-25T08:21:22.150242+00:00] PT2 START — 2HDM+a demo
[2026-04-25T08:21:22.150260+00:00] ======================================================================
[2026-04-25T08:21:22.150278+00:00] WORKTREE: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2
[2026-04-25T08:21:22.150282+00:00] SARAH_ROOT: /Users/yianni/SARAH/SARAH-4.15.3
[2026-04-25T08:21:22.150285+00:00] MG5_BIN: /Users/yianni/MG5_aMC/bin/mg5_aMC
[2026-04-25T08:21:22.150291+00:00] OUT_DIR: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run
[2026-04-25T08:21:22.150294+00:00] ======================================================================
[2026-04-25T08:21:22.150296+00:00] Step 4a: Deploy SARAH model
[2026-04-25T08:21:22.150298+00:00] ======================================================================
[2026-04-25T08:21:22.150930+00:00] TwoHdmAfix already up to date at /Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix
[2026-04-25T08:21:22.150938+00:00] ======================================================================
[2026-04-25T08:21:22.150940+00:00] Step 4b: Verify UFO (SARAH already run)
[2026-04-25T08:21:22.150943+00:00] ======================================================================
[2026-04-25T08:21:22.150967+00:00] CMD: grep -c chi /Users/yianni/SARAH/SARAH-4.15.3/Output/TwoHdmAfix/EWSB/UFO/vertices.py
[2026-04-25T08:21:22.156282+00:00]   exit=0  elapsed=0.0s
[2026-04-25T08:21:22.156309+00:00]   STDOUT: 3
[2026-04-25T08:21:22.156320+00:00] UFO OK: 3 chi vertices found in vertices.py
[2026-04-25T08:21:22.156325+00:00] ======================================================================
[2026-04-25T08:21:22.156329+00:00] Step 4c Phase 1: MadGraph5 output
[2026-04-25T08:21:22.156331+00:00] ======================================================================
[2026-04-25T08:21:22.156352+00:00] Removing existing /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run
[2026-04-25T08:21:22.162241+00:00] Wrote setup.mg5 to /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/setup.mg5
[2026-04-25T08:21:22.162254+00:00] CMD: /Users/yianni/MG5_aMC/bin/mg5_aMC --mode=maddm /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/setup.mg5
[2026-04-25T08:21:22.162258+00:00]   cwd: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a
[2026-04-25T08:21:23.684905+00:00]   exit=0  elapsed=1.5s
[2026-04-25T08:21:23.685032+00:00] param_card.dat written at /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run/Cards/param_card.dat
[2026-04-25T08:21:23.685044+00:00] ======================================================================
[2026-04-25T08:21:23.685048+00:00] Step 4c Phase 2: Patch param_card
[2026-04-25T08:21:23.685050+00:00] ======================================================================
[2026-04-25T08:21:23.685071+00:00] CMD: /Users/yianni/.pyenv/versions/3.10.16/bin/python3 /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run --Mchi 100.0 --Ma-Ah2 400.0 --gchi 1.0 --tan-beta 10.0
[2026-04-25T08:21:23.685076+00:00]   cwd: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2
[2026-04-25T08:21:23.760829+00:00]   exit=0  elapsed=0.1s
[2026-04-25T08:21:23.761118+00:00]   Block DMSECTOR: present
[2026-04-25T08:21:23.761198+00:00]   Block PHASES: present
[2026-04-25T08:21:23.761304+00:00]   Block ZAMIX: present
[2026-04-25T08:21:23.761310+00:00] ======================================================================
[2026-04-25T08:21:23.761314+00:00] Step 4c Phase 3: MadDM launch
[2026-04-25T08:21:23.761316+00:00] ======================================================================
[2026-04-25T08:21:23.761436+00:00] Wrote launch.mg5 to /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/launch.mg5
[2026-04-25T08:21:23.761440+00:00]   Content: launch /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run -f
[2026-04-25T08:21:23.761452+00:00] CMD: /Users/yianni/MG5_aMC/bin/mg5_aMC --mode=maddm /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/launch.mg5
[2026-04-25T08:21:23.761457+00:00]   cwd: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a
[2026-04-25T08:21:31.220320+00:00]   exit=0  elapsed=7.5s
[2026-04-25T08:21:31.220622+00:00] MadDM run directory: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run/output/run_01
[2026-04-25T08:21:31.220690+00:00] MadDM_results.txt content (2416 chars):
[2026-04-25T08:21:31.220701+00:00]   ################################################
[2026-04-25T08:21:31.220703+00:00]   #                 MadDM v. 3.2                 #
[2026-04-25T08:21:31.220706+00:00]   ################################################
[2026-04-25T08:21:31.220708+00:00]   
[2026-04-25T08:21:31.220710+00:00]   
[2026-04-25T08:21:31.220715+00:00] ======================================================================
[2026-04-25T08:21:31.220717+00:00] Copy patched param_card to run_dir/Cards/
[2026-04-25T08:21:31.220719+00:00] ======================================================================
[2026-04-25T08:21:31.220987+00:00] Copied param_card.dat to /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/maddm_run/output/run_01/Cards
[2026-04-25T08:21:31.221050+00:00]   Block DMSECTOR in run_dir/Cards/param_card.dat: FOUND
[2026-04-25T08:21:31.221097+00:00]   Block PHASES in run_dir/Cards/param_card.dat: FOUND
[2026-04-25T08:21:31.221175+00:00]   Block ZAMIX in run_dir/Cards/param_card.dat: FOUND
[2026-04-25T08:21:31.221177+00:00] ======================================================================
[2026-04-25T08:21:31.221179+00:00] Parse MadDM output
[2026-04-25T08:21:31.221181+00:00] ======================================================================
[2026-04-25T08:21:31.221193+00:00] Omega_h2 = 22.3
[2026-04-25T08:21:31.221231+00:00] Channel percentages (47 channels):
[2026-04-25T08:21:31.221241+00:00]   wphp: 49.02%
[2026-04-25T08:21:31.221244+00:00]   wmhm: 49.02%
[2026-04-25T08:21:31.221247+00:00]   bbx: 1.71%
[2026-04-25T08:21:31.221250+00:00]   ccx: 0.16%
[2026-04-25T08:21:31.221252+00:00]   tamtap: 0.1%
[2026-04-25T08:21:31.221260+00:00] Channel fractions sum = 1.000000
[2026-04-25T08:21:31.221269+00:00] gate_check = {'bbx_fraction': 0.017098290170982904, 'channels_sum_in_unity_range': True, 'bbx_threshold_passed': False}
[2026-04-25T08:21:31.221672+00:00] Band: [9.9693, 11.0187]
[2026-04-25T08:21:31.221681+00:00] omega_h2=22.3 in band: False
[2026-04-25T08:21:31.221684+00:00] ======================================================================
[2026-04-25T08:21:31.221686+00:00] Write relic.json
[2026-04-25T08:21:31.221688+00:00] ======================================================================
[2026-04-25T08:21:31.221880+00:00] Wrote relic.json to /Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-030153/workstreams/2hdma/playtest/relic.json
[2026-04-25T08:21:31.222027+00:00] Wrote relic.json to /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/relic.json
[2026-04-25T08:21:31.222034+00:00] ======================================================================
[2026-04-25T08:21:31.222036+00:00] Write summary.json
[2026-04-25T08:21:31.222039+00:00] ======================================================================
[2026-04-25T08:21:31.222145+00:00] Wrote summary.json to /Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-030153/workstreams/2hdma/playtest/summary.json
[2026-04-25T08:21:31.222236+00:00] Wrote summary.json to /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/demo_output/2hdm-a/summary.json
[2026-04-25T08:21:31.222240+00:00] ======================================================================
[2026-04-25T08:21:31.222242+00:00] PT2 COMPLETE
[2026-04-25T08:21:31.222244+00:00] ======================================================================
[2026-04-25T08:21:31.222246+00:00] omega_h2 = 22.3
[2026-04-25T08:21:31.222250+00:00] in_band = False  (9.9693 <= 22.3 <= 11.0187)
[2026-04-25T08:21:31.222252+00:00] channels_sum_in_unity_range = True
[2026-04-25T08:21:31.222255+00:00] verdict = FAIL
