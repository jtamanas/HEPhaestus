# Runbook — Variant B (ZN→N rename regression test)
# Generated: 2026-04-24 by sd-B playtest agent
# WORKTREE_PATH: /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B
# HEPPH_STATE_ROOT: /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B/.playtest/sd-B/state
# XDG_CONFIG_HOME: /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B/.playtest/sd-B/xdg

## Variant B specifics
- SARAH model name: SingletDoublet_B
- Practitioner script: .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md
- Mixing matrix in Q4: N (renamed from ZN in canonical script A)
- FIFO ID: sd-B
- Issue prefix: sd-B-NNN
- Ωh² target: 0.292 ± 0.01 (same as A)
- BASELINE_USED: 0.292 (from baseline.json, drift_flag=false)

## Key concern
ZN→N rename should NOT change physics. If Ωh²(B) differs measurably from
Ωh²(A), that is a finding (rename leaked). If SARAH chokes on `N` (clashes
with MSSM neutralino convention), capture cleanly as major finding.

---

## Phase 0 — Preflight

### Commands
```bash
WROOT=/Users/yianni/Projects/hep-ph-agents.worktrees/sd-B
CONFIG="${WROOT}/.playtest/sd-B/xdg/hep-ph-agents/config.json"
MG5_PATH=$(python3 -c "import json; print(json.load(open('${CONFIG}'))['madgraph_path'])")
SARAH_PATH=$(python3 -c "import json; print(json.load(open('${CONFIG}'))['sarah_path'])")
SPHENO_PATH=$(python3 -c "import json; print(json.load(open('${CONFIG}'))['spheno_path'])")
WOLFRAM_PATH=$(python3 -c "import json; print(json.load(open('${CONFIG}'))['wolfram_engine_path'])")

# Tool checks
${MG5_PATH} --version        # expect: "Usage: mg5_aMC..." or version line
${WOLFRAM_PATH} -code 'Print["ok"]'  # expect: "ok"
ls ${SPHENO_PATH}            # expect: binary present
```

### Expected exit codes: 0 for all

---

## Phase 1 — /demo → singlet-doublet flow

### Step 1-3: /demo intro, continue, model picker
- Practitioner answer: "singlet-doublet"
- No AskUserQuestion calls (scripted demo)

### Step 4a: /lagrangian-builder interview
SARAH model name (before Q1): SingletDoublet_B

Practitioner answers (from practitioner_script_B.md):
- Q1: Physics description (singlet-doublet, tree-level SI blind spot, relic only)
- Q2: SM gauge groups; 2 new fermions (singlet Majorana + vectorlike SU(2)_L doublet Y=±½)
- Q3: Keep both Yukawa (yh1, yh2); delete BSM-SM Yukawa; MS/MPsi parameters; drop extra scalar potential
- Q4: (VARIANT B DELTA) Neutral Majorana 3×3: matrix N (NOT ZN), eigenstates Chi1/Chi2/Chi3;
       Charged Dirac: UM, UP matrices; eigenstates ChiM/ChiP

**CRITICAL WATCH POINT**: SARAH parses model files. The name `N` is a reserved
symbol in SARAH for MSSM neutralinos (mixing matrix). This rename is the
Variant B regression test. Possible outcomes:
  1. SARAH errors at parse → log major (sd-B-001), criteria 2/3 pass via alternate path
  2. SARAH silently rebinds N to MSSM definition → log major (sd-B-001) with
     hypothesis containing "N MSSM collision"
  3. SARAH accepts N cleanly → proceed, compare Ωh² to A

### Step 4b: SPheno spectrum generation
```bash
SPHENO_BIN=/Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno
STATE_ROOT=${WROOT}/.playtest/sd-B/state
# SPheno input: ${STATE_ROOT}/models/singlet_doublet_b/SPheno/
# SPheno output: ${STATE_ROOT}/models/singlet_doublet_b/SPheno.spc.singlet_doublet_b
```
Expected: exit 0, SPheno.spc produced

### Step 4c: MadDM relic density
```bash
MG5_BIN=/Users/yianni/MG5_aMC/bin/mg5_aMC
UFO_PATH=${STATE_ROOT}/models/singlet_doublet_b/SingletDoublet_B  # symlink from sarah-build
DM_CANDIDATE=chi1
OUT_DIR=${WROOT}/demo_output/singlet-doublet/maddm_run/
SLHA_PATH=${STATE_ROOT}/models/singlet_doublet_b/SPheno.spc.singlet_doublet_b

# FIFO lock acquisition
TS=$(date +%s%N); ID="sd-B-${TS}"
touch ${WROOT}/.shift-manager/run-20260424-202956/locks/sarah.queue/${ID}.req

# MadDM invocation (with flock on maddm.lock)
flock -x -w 300 ${WROOT}/.shift-manager/run-20260424-202956/locks/maddm.lock \
  ${MG5_BIN} --mode=maddm setup.mg5
```
Expected: MadDM_results.txt with Omegah2 line

### Step 4d: Plotting
```bash
cd ${WROOT}
python3 -c "
from styles.hep_ph_style import set_hep_context, check_overlaps
import matplotlib.pyplot as plt
# ... channel bar chart
"
```
Expected: summary.pdf, summary.png >1KB

### Step 4f: summary.json
Expected keys: model, run_at, ran, skipped_constraints, artifacts_dir, headline

---

## Success criteria (Variant B)

1. summary.json parseable; ran contains "relic"; relic.json.status=="ok"
2. omega_h2 finite in [0.10, 0.40] OR issues.jsonl has major entry with
   N+MSSM+collision/reserved/clash hypothesis (logged before MadDM)
3. omega_h2 within ±0.01 of 0.292 OR issues.jsonl has major entry as above
4. summary.{pdf,png} exist, >1KB
5. singlet_doublet_spec.yaml exists; validate_spec.py exits 0
6. Wallclock ≤ 45 min

---

## Issue schema (append to issues-B.jsonl)
{
  "ts": "<ISO-8601>",
  "workstream": "singlet-doublet",
  "variant": "B",
  "issue_id": "sd-B-NNN",
  "phase": "<phase name>",
  "severity": "blocker|major|minor|warning",
  "hypothesis": "<text>",
  "fix_owner_hint": "<skill_prose|tool_driver|fixture|parse|plot|lagrangian_builder|validate_spec|physics|unknown>",
  "auto_repro_command": "<bash command>",
  "expected_fix_scope": "<scope>"
}
