# Singlet-Doublet Variant A Playtest — Run 2

Run started: 2026-04-25T08:20:46Z
Variant: A
Practitioner answers: MS=150, MPsi=500, y=1, theta=0, mixing=ZN, constraint=relic, model=SingletDoublet_A

## Phase 0 — Preflight
  wolframscript: OK
  mg5_aMC: OK
  SPheno: present
  SARAH: present
  SPhenoSingletDoublet: present

## Phase 1 — demo/SKILL.md Steps 0-3

Step 0: Preflight PASS (see Phase 0)

Step 1 (paper intro — observe only):
  > Arcadi & Profumo arXiv:2506.19062 §II — Singlet-Doublet fermion DM
  > Tree-level SI blind spot: singlet + doublet components interfere destructively.

Step 2: Gate Q 'Ready to begin?' → answer: continue

Step 3: Model picker → answer: singlet-doublet
  ANSWER (VERBATIM): singlet-doublet

## Phase 2 — singlet-doublet/SKILL.md Steps 1-3

Step 1 (DM-candidate declaration — observe only):
  > DM candidate: chi1 (Majorana, lightest eigenstate of the singlet-doublet mixing)

Step 2: Constraint multi-select
  ANSWER (VERBATIM): ["relic"]

Step 3: Time estimate + prereq resolve + gate
  Relic density: READY
  Gate Q: Run it? → answer: go
  ANSWER (VERBATIM): go

## Phase 3 — Step 4a: lagrangian-builder JIT

Interview replay (VERBATIM from practitioner_script.md):

Q1 — What are you studying?

> Singlet-doublet fermion DM from Arcadi & Profumo, arXiv:2506.19062 §II.
> The paper's whole point is the tree-level SI blind spot — the singlet
> and doublet components interfere destructively and the induced
> Higgs–DM coupling goes to zero along a specific mass-eigenstate locus.
> For this run I just want relic density

Q2 — What new fields and gauge groups?

> SM gauge groups, unchanged. Two new fermions:
>
> 1. A gauge-singlet Majorana fermion. Call it the singlet
> 2. A vectorlike SU(2)_L doublet with Y = ±½

Q3 — Confirm the Lagrangian

*(deltas against Claude's enumerated draft)*

> A few edits:
>
> 1. **Keep both Yukawa contractions.** The paper uses them both —
>    name the couplings `yh1` and `yh2`.
> 2. **Delete any Yukawa coupling the BSM fermions to SM fermions.**
>    The DM candidate has to be stable; call whatever symmetry you
>    infer from those deletions `DMParity`.
> 3. **Parameter names:** `MS` for the singlet mass, `MPsi` for the
>    doublet mass.
> 4. **Drop any extra scalar-potential terms you drafted.** We're not
>    touching the SM Higgs sector.

Q4 — Confirm post-EWSB mixings

*(deltas against Claude's detected mixing sectors)*

> Both sectors look right. Renames:
>
> - Neutral Majorana 3×3: matrix `ZN`, eigenstates `Chi1`, `Chi2`,
>   `Chi3` (ascending mass; `Chi1` is the DM).
> - Charged Dirac: left matrix `UM`, right matrix `UP`, eigenstates
>   `ChiM` (Q = −1) and `ChiP` (Q = +1).
>
> No scalar mixing.

SARAH model name: SingletDoublet_A
Benchmark: MS=150, MPsi=500, y=1, theta=0 => (yh1,yh2)=(1.0,0.0)

singlet_doublet_spec.yaml written to: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/singlet_doublet_spec.yaml

## Phase 4 — Step 4b: SPheno spectrum generation

Benchmark: (MS=150, MPsi=500, yh1=1.0, yh2=0.0)
SLHA input: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/runs/2026-04-22T2241Z-aee644cc/SPheno.spc
SPheno binary: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/spheno_bin/SPhenoSingletDoublet
  SPheno exit: 0
  Output: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/SPheno.spc.singlet_doublet

## Phase 5 — Step 4c: MadDM relic density

UFO: /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/SingletDoublet
DM candidate: chi1
param_card_source: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/SPheno.spc.singlet_doublet
  MadDM setup exit: 0
  SLHA overlay: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/SPheno.spc.singlet_doublet → /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/maddm_run/Cards/param_card.dat
  MadDM launch exit: 0
  Omega_h2 = 2.92e-01
  m_chi1 = 1.32692344E+02 GeV (from SLHA Block MASS # FChi_1)
  relic.json written: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/relic.json

## Phase 6 — Step 4d: Annihilation-channel bar chart
  summary.pdf: 32444 bytes
  summary.png: 28343 bytes

## Phase 7 — Step 4f: summary.json
  summary.json written: /Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest/runs/run-2/demo_output/singlet-doublet/summary.json

Run 2 complete: 2026-04-25T08:21:00Z
Omega_h2 = 2.92e-01
