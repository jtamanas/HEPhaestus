# Runbook — Singlet-Doublet Variant A Playtest
# Distilled from demo/SKILL.md + singlet-doublet/SKILL.md (JIT)
# Date: 2026-04-24

## Environment
```
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/sd-A
HEPPH_STATE_ROOT=${WORKTREE_PATH}/.playtest/sd-A/state
XDG_CONFIG_HOME=${WORKTREE_PATH}/.playtest/sd-A/xdg
```

## Practitioner Answers (Variant A — VERBATIM from plan)
- Model picker: "singlet-doublet"
- MS=150, MPsi=500, y=1, theta=0
- Mixing matrix: ZN
- Constraint: relic only
- SARAH model name: "SingletDoublet_A"

## Config (from xdg/hep-ph-agents/config.json)
- madgraph_path: /Users/yianni/MG5_aMC/bin/mg5_aMC
- sarah_path: /Users/yianni/SARAH/SARAH-4.15.3
- spheno_path: /Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno
- wolfram_engine_path: /usr/local/bin/wolframscript
- singlet_doublet ufo: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/SingletDoublet
- singlet_doublet latest_slha: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/runs/2026-04-22T2241Z-aee644cc/SPheno.spc
- singlet_doublet spheno_bin: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/spheno_bin/SPhenoSingletDoublet

## Baseline (from prep P2)
- omega_h2: 0.292
- hardcoded_reference: 0.292
- drift_flag: false

## Phase 0 — Preflight
- Read config.json ✓
- Verify each tool binary responds:
  - wolframscript: `timeout 5 wolframscript -code 'Print["ok"]'`
  - mg5_aMC: `/Users/yianni/MG5_aMC/bin/mg5_aMC --version`
  - SPheno: `/Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno --version` (or check exists)
  - SARAH dir: `ls /Users/yianni/SARAH/SARAH-4.15.3/Package.m`

## Phase 1 — demo/SKILL.md Steps 0-3
- Step 0: Preflight (see above)
- Step 1: Paper intro (print verbatim — observe only)
- Step 2: Gate Q "Ready to begin?" → "continue"
- Step 3: Model picker → "singlet-doublet"

## Phase 2 — singlet-doublet/SKILL.md Steps 1-3
- Step 1: DM-candidate declaration (print; observe)
- Step 2: Constraint multi-select → ["relic"]
- Step 3: Time estimate + gate → "go" (relic READY, 1-2 hr cold)

## Phase 3 — Step 4a: lagrangian-builder (JIT read at entry)
- check_state.py: singlet_doublet already present → skip rebuild unless --force
- SARAH model name: SingletDoublet_A (set via interview prompt before Q1)
- Interview Q1-Q4 (scripted from practitioner_script.md)
- validate_spec.py on generated YAML
- Expected: singlet_doublet_spec.yaml at demo_output/singlet-doublet/singlet_doublet_spec.yaml
- Success check: validate_spec.py exits 0

## Phase 4 — Step 4b: SPheno spectrum
- Run SPheno at benchmark (MS=150, MPsi=500, y=1, theta=0)
- Cmd: `$SPHENO_BIN $LESHOUCHES_INPUT $STATE_ROOT/models/singlet_doublet/runs/<TS>/SPheno.spc`
- Expected: SPheno.spc.singlet_doublet produced

## Phase 5 — Step 4c: MadDM relic density
- SARAH FIFO + flock for SARAH (wolframscript step only)
- MadDM flock for first launch
- Expected: relic.json with omega_h2 in [0.10, 0.40]
- UFO path: config.models.singlet_doublet.ufo = /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/SingletDoublet
- dm_candidate: "chi1"
- out_dir: demo_output/singlet-doublet/maddm_run/
- param_card_source: config.models.singlet_doublet.latest_slha

## Phase 6 — Step 4d: Plotting
- annihilation-channel bar chart
- Output: demo_output/singlet-doublet/summary.{pdf,png} >1KB

## Phase 7 — Step 4f: summary.json
- Write per summary.schema.json
- ran: ["relic"], skipped: [dd, id]

## Success Criteria (Variant A)
1. summary.json parseable; summary.json.ran contains "relic"; relic.json.status=="ok"
2. relic.json.omega_h2 finite in [0.10, 0.40]
3. Determinism: omega_h2 within ±0.01 of BASELINE (0.292)
4. summary.{pdf,png} exist, >1KB
5. singlet_doublet_spec.yaml exists; validate_spec.py exits 0
6. Wallclock <= 45 min

## SARAH FIFO snippet (Variant A)
```bash
mkdir -p $REPO/.shift-manager/run-20260424-202956/locks/sarah.queue/
TS=$(date +%s%N); ID="sd-A-${TS}"
touch $REPO/.shift-manager/run-20260424-202956/locks/sarah.queue/${ID}.req
while true; do
  OLDEST=$(ls -t $REPO/.shift-manager/run-20260424-202956/locks/sarah.queue/*.req 2>/dev/null | tail -n 1 | xargs -n 1 basename)
  [ "${OLDEST}" = "${ID}.req" ] && break
  AGE=$(($(date +%s) - $(stat -f %B $REPO/.shift-manager/run-20260424-202956/locks/sarah.queue/${ID}.req)))
  [ ${AGE} -gt 300 ] && { echo "FIFO starvation" >> issues; break; }
  sleep 2
done
flock -x -w 120 $REPO/.shift-manager/run-20260424-202956/locks/sarah.lock wolframscript -code '...'
rm $REPO/.shift-manager/run-20260424-202956/locks/sarah.queue/${ID}.req
```

## Issue schema
{
  "issue_id": "sd-A-NNN",
  "workstream": "singlet-doublet",
  "variant": "A",
  "phase": "<phase>",
  "severity": "blocker|major|minor|warning",
  "hypothesis": "...",
  "fix_owner_hint": "skill_prose|tool_driver|fixture|parse|plot",
  "auto_repro_command": "...",
  "expected_fix_scope": "..."
}
