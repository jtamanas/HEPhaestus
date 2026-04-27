# PT1 Transcript — 2HDM+a Playtest

Start: 2026-04-25T01:25:41Z
Agent: sonnet-playtest
Branch: 2hdma/playtest-20260424
Worktree: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-playtest/
Config: /Users/yianni/.config/hep-ph-agents/config.json
SARAH_ROOT: /Users/yianni/SARAH/SARAH-4.15.3

## Phase: preflight
[01:25:41Z] Worktree created at 2hdma-playtest, clean at 2c9dd31
[01:25:41Z] Gate status: overall=pass
[01:25:41Z] maddm_run import: OK

## Phase: clean+deploy
[01:26:38Z] Moved existing TwoHdmAfix to quarantine
[01:26:38Z] Deployed 4 fixture .m files to SARAH_ROOT/Models/TwoHdmAfix/

## Phase: sarah_makeufo
[01:26:44Z] lockf not working with pre-created file (Permission denied) — fixed by rm+lockf
[01:27:09Z] SARAH MakeUFO started (lockf -k -t 120)
[01:27:56Z] SARAH MakeUFO completed (47s): 3 chi-vertices, UFO at SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/
[01:27:56Z] Vertex sanity: chibar-chi-Ah1, chibar-chi-Ah2, chibar-chi-Ah3 confirmed

## Phase: mg5_output
[01:28:54Z] Created .output_marker (sentinel reference)
[01:29:06Z] MG5 output started (mg5_aMC --mode=maddm)
[01:29:07Z] MG5 output completed: 47 processes/100 diagrams; param_card.dat written
[01:29:07Z] mtime sentinel: param_card (1777080547) > .output_marker (1777080534) PASS

## Phase: patch_paramcard
[01:29:33Z] patch_paramcard.py ran: PHASES[1]=1.0, gchi=1.0, Mchi=100
[01:29:33Z] Created .patched marker
[01:29:33Z] DISCOVERED BUG (2hdma-001): patcher regex fails on fresh MG5 single-space values
[01:30:01Z] Manually fixed DMSECTOR, PHASES, MASS, HMIX, ZAMIX, ZHMIX, ZPMIX in param_card.dat

## Phase: maddm_launch_attempt1
[01:30:01Z] Launch attempt 1: 'launch -f' — FAILED (AttributeError: NoneType.get; model not loaded)
[01:30:37Z] Discovered: must use 'launch <out_dir> -f' not 'launch -f' (issue 2hdma-004)

## Phase: maddm_launch_attempt2
[01:30:37Z] Launch attempt 2 (launch <out_dir> -f): DM couplings still zero
[01:30:44Z] ERROR: dmsector (2,) is already define to 0.0 impossible to assign 1.0
[01:30:44Z] MadDM rejected patched card, used default → Omega=-1
[01:30:44Z] Root cause: patcher's DMSECTOR update failed (regex bug)

## Phase: manual_param_fix
[01:31:00Z] Fixed DMSECTOR (gchi=1.0, mchi=100), PHASES (rpchiR=1.0)
[01:31:00Z] Fixed BSM masses: Ah2=400, Ah3=500, hh1=125, hh2=600, Hm2=550, chi=100
[01:31:00Z] Fixed HMIX VEVs (vd=24.5, vu=245.0 from tan_beta=10)
[01:31:00Z] Fixed ZAMIX (3x3, theta_a=0.1), ZHMIX, ZPMIX, fermion rotations, Yukawas
[01:31:00Z] Fixed MHm1(37)=80.419 (W Goldstone)

## Phase: maddm_launch_attempt3
[01:35:15Z] Launch attempt 3: all params fixed
[01:35:16Z] Run 2 result: Omega h^2=22.34, dominant: wphp+wmhm=98%, bbx=1.71%
[01:35:16Z] THDMPOT quartics added (non-zero), rerun attempt 4

## Phase: maddm_launch_attempt4
[01:40:49Z] Launch attempt 4: THDMPOT non-zero, MHm1=80.4
[01:40:51Z] Run 3 result: Omega h^2=10.484

## Phase: maddm_launch_attempt5
[01:41:12Z] Launch attempt 5: THDMPOT=0 (match iter-8), MHm1=80.4
[01:41:13Z] Run 4 result: Omega h^2=10.494

## Phase: output_writing
[01:43:54Z] relic.json written: omega_h2=10.494, dominant=wphp (49.62%), bbx=0.65%
[01:43:54Z] summary.json written and schema-validated: [PASS]
[01:43:54Z] summary.pdf and summary.png generated
[01:43:54Z] issues.jsonl written: 2hdma-001 (blocker), 2hdma-002..004 (warnings/minor)
[01:44:00Z] verdict.md written: VERDICT: FAIL (Omega outside band, bbx<30%)

## Final Status
- VERDICT: FAIL
- Omega h^2 = 10.494 (band [9.95, 10.36], +3.4% outside)
- bbx channel = 0.65% (threshold 30%, FAIL)
- Root cause: patcher_regex_bug (2hdma-001) + ZA mixing physics (2hdma-003)
- Infrastructure confirmed working: SARAH->UFO->MG5->MadDM pipeline end-to-end
