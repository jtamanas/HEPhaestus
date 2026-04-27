# Playtest Transcript — Variant B (ZN→N rename regression)
# Run: 2026-04-24 / Wall start: ~21:30Z
# Agent: sonnet playtest agent (sd-B)
# Branch: sd/playtest-B-20260424 from sd/prep-20260424 HEAD (f339b55)

---

## Worktree setup

```
git worktree add -b sd/playtest-B-20260424 \
    /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B \
    sd/prep-20260424
HEAD is now at f339b55 [sd-prep] gate-eval: overall=warning (G9 downgraded, schema sentinel absent)
```

Worktree clean (git status --porcelain: empty).

---

## Phase 0 — Preflight

### Config read
XDG_CONFIG_HOME: /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B/.playtest/sd-B/xdg
HEPPH_STATE_ROOT: /Users/yianni/Projects/hep-ph-agents.worktrees/sd-B/.playtest/sd-B/state

Config keys:
- madgraph_path: /Users/yianni/MG5_aMC/bin/mg5_aMC
- sarah_path: /Users/yianni/SARAH/SARAH-4.15.3
- spheno_path: /Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno
- wolfram_engine_path: /usr/local/bin/wolframscript

### Tool checks
- MadGraph: responds (Usage: mg5_aMC ...) ✓
- Wolfram Engine: responds (ok) ✓
- SPheno binary: present at /Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno ✓
- SARAH 4.15.3 at /Users/yianni/SARAH/SARAH-4.15.3 ✓

### Env.json
- git_sha: 6b2cd8e9d37180620e3319bf2bf345ded5ffea1d
- mg5_version: 3.5.6 (2024-09-26)
- maddm_plugin_sha: no-git
- sarah_version: 4.15.3
- python_version: Python 3.10.16
- wolfram_version: 14.3.0

### Schema sentinel
schema_v1_1.ready: absent → G9 warning (as captured in gate_status.json)
schema_wait_result.json: {"schema_ready": 0}

---

## Phase 1 — Demo flow simulation

### Steps 1-3: /demo intro, continue, model picker

Claude [demo/SKILL.md Step 0]: Read config.json. All required keys present and tools respond.

Claude [demo/SKILL.md Step 1 — verbatim]:
> Arcadi & Profumo ask: where can dark matter hide from direct detection? ...

Practitioner: "continue"
Practitioner: "singlet-doublet"

---

### Step 4a: /lagrangian-builder interview (Variant B)

SARAH model name set before Q1: **SingletDoublet_B**

Claude [Q1 preamble]: Scope tier announced. Model: BSM singlet-doublet fermion DM.

**Practitioner Q1**: Singlet-doublet fermion DM from Arcadi & Profumo, arXiv:2506.19062 §II.
Tree-level SI blind spot. Single-Yukawa limit. Relic only.

Claude [Q2]: Field content enumeration for SM singlet Majorana + SU(2)_L doublet.

**Practitioner Q2**: SM gauge groups. Two new fermions:
  1. Gauge-singlet Majorana (the singlet)
  2. Vectorlike SU(2)_L doublet with Y=±½

Claude [Q3]: Enumerated Lagrangian draft presented.

**Practitioner Q3**:
  - Keep both Yukawa contractions (yh1, yh2)
  - Delete BSM-SM Yukawa (DMParity symmetry inferred)
  - Parameter names: MS (singlet), MPsi (doublet)
  - Drop extra scalar-potential terms

Claude [Q4]: Detected mixing sectors presented:
  - Neutral 3×3 Majorana block
  - Charged Dirac block

**Practitioner Q4 (VARIANT B DELTA)**:
  - Neutral Majorana 3×3: matrix **N** (not ZN), eigenstates Chi1, Chi2, Chi3
  - Charged Dirac: UM, UP matrices; ChiM/ChiP eigenstates
  - No scalar mixing

Spec generated: singlet_doublet_b spec with mixing_matrix: N

### validate_spec.py check

```
python3 plugins/model-building/skills/sarah-build/scripts/validate_spec.py \
    /tmp/singlet_doublet_b_spec.yaml
→ {"status": "valid", "name": "singlet_doublet_b"}
exit=0
```

**OBSERVATION**: validate_spec.py PASSES for mixing_matrix: N.
The reserved-name sets (_RESERVED_FIELD_NAMES, _RESERVED_PARAM_NAMES) do NOT
include N, ZN, or any mixing matrix symbol. This is a gap in validation coverage.

### Rendered model file inspection

render_templates.py renders SingletDoubletB.m with:
  Line 47: {{s0, PsiDd0, PsiDu0}, {Chi, N}}

parameters.m renders:
  {N, { Description -> "Majorana-Mixing-Matrix-Chi",
             OutputName -> N,
             LesHouches -> NMIX }}

**CRITICAL**: LesHouches -> NMIX in the model-specific parameters.m is the same
SLHA block that SARAH's global parameters.m uses for the MSSM neutralino mixing
matrix ZN (LesHouches -> NMIX, OutputName -> ZN). But more critically, N is the
Mathematica built-in precision function N[expr, prec]. Shadowing N breaks every
internal SARAH call to N[...] for numeric computation.

---

### SARAH build (SingletDoublet_B)

FIFO queue: sd-B acquired (queue was empty)
Lock file: .shift-manager/run-20260424-202956/locks/sarah.lock (advisory)

```
python3 plugins/model-building/skills/sarah-build/scripts/build.py \
    /tmp/singlet_doublet_b_spec.yaml --force
Wall time: 23s
exit=0
→ {"status": "built", "sarah_name": "SingletDoubletB", ...}
```

**build.py exit=0 — SARAH did not hard-fail.**

### SARAH log analysis

sarah.log contains hundreds of:
```
N::precbd: Requested precision xgen is not a machine-sized real number between
           $MinPrecision and $MaxPrecision.
StringJoin::string: String expected at position 2 in W<>None.
ToExpression::notstrbox: W<>None<>1 is not a string or a box.
```

Root cause: `N` as mixing matrix symbol shadows Mathematica's built-in N[expr, prec]
precision function. Every internal SARAH call to N[...] for numeric computation of
precision-controlled values fails. The StringJoin errors follow because SARAH's
SPheno code generation uses N[] internally to convert expressions to numeric strings.

### check_vertices.py

```
python3 check_vertices.py --spec singlet_doublet_b_spec.yaml \
    --output-dir .../SingletDoubletB/
exit=1
```

Output (2 blockers):
1. VERTICES_MISSING: yh1 — no matching UFO vertex for [conj[H], FS, PsiDu]
2. VERTICES_MISSING: yh2 — no matching UFO vertex for [H, FS, PsiDd]

**Both Higgs-portal Yukawa vertices were dropped from the UFO.**

Comparison:
- Variant A (ZN): 32 Chi-containing vertices in vertices.py
- Variant B (N):   0 Chi-containing vertices in vertices.py

### check_mass_matrix.py

```
exit=0
```

The mass matrix structure is intact (3×3 Majorana sector present in SARAH output).
The failure is specifically at the vertex engine / UFO emission stage.

### SPheno build (cascade failure)

```
python3 run_spheno.py singlet_doublet_b
exit=1
→ {"code": "SPHENO_COMPILE_FAILED", ...}
```

SPheno Fortran compile fails:
  Couplings_SingletDoubletB.f90:128: Error: Unexpected assignment statement in CONTAINS section
  (malformed Fortran due to StringJoin failures in SARAH code generation)

Pipeline halted at SPheno compile. MadDM not reached.

---

## Summary

The ZN→N rename caused:
1. N shadows Mathematica's N[expr, prec] → N::precbd errors in SARAH
2. SARAH vertex engine drops all Higgs-portal Yukawa vertices (yh1, yh2)
3. UFO has zero Chi-containing vertices
4. SPheno Fortran code is syntactically broken → SPHENO_COMPILE_FAILED
5. MadDM never reached → Ωh² cannot be computed

The failure was SILENT at the SARAH exit level (exit=0) but DETECTED
by check_vertices.py (VERTICES_MISSING for both yukawa terms).

This is the "naming-conflict regression" the plan predicted.
VERDICT: PASS (alternate criterion 2/3 satisfied by VERTICES_MISSING finding)
