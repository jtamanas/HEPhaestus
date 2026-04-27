---
name: lagrangian-builder
description: Orchestrate the full BSM model pipeline — interview the user to build a ModelSpec, install SARAH and SPheno if needed, run SARAH and SPheno, and hand the UFO + SLHA outputs to /madgraph or other tools.
allowed-tools: Bash, Read, Write, Edit
---

# /lagrangian-builder

End-to-end orchestrator for building a new BSM model with SARAH and SPheno.
This is a **SKILL.md-driven** skill: Claude reads these instructions and executes
sub-skills and scripts directly — there is no top-level Python state machine.

Philosophy: augment, don't replace. Every step drives a real tool
(SARAH/SPheno) rather than emulating physics in Python.
If a required tool is missing and cannot be installed, the skill emits a fatal
blocker and stops.

---

## Iteration accounting (applies to Step 2b-verify and Step 2d-verify)

The SARAH and SPheno stages have **silent failure modes** (SARAH drops
vertices; SPheno produces degenerate spectra; observables fall into
physically impossible regions). The interview preamble (`references/interview.md` §0)
promises the user 2–3 passes are normal; this skill must surface every pass
rather than silently looping.

Maintain a visible retry state that is **shown to the user on every attempt**:

```
Attempt <N> of 3 — <SARAH verification | SPheno verification>
  Prior blockers: [<code>, <code>, ...]
  Prior patches:  [<short description>, ...]
```

Rules:
- **Cap: 3 attempts per verification stage.** A stage is either
  SARAH-output verification (Step 2b-verify) or SPheno-spectrum verification
  (Step 2d-verify).
- Each attempt appends to a running list `blockers_seen[]` and `patches_applied[]`
  carried into Step 4 (the final report).
- When a blocker fires, name the corresponding **interview question**
  (`references/interview.md` §Iteration expectations) in the user-facing
  message so the user learns which part of the spec is being re-authored:
  - `check_vertices.py` blockers → Q3 (Lagrangian enumeration)
  - `check_mass_matrix.py` blockers → Q4 (post-EWSB mixing)
  - `check_spectrum.py` blockers → Q3, or parameter defaults set at Q2
- **Don't hide retries.** Print every attempt banner, every blocker JSON, and
  every patch diff. The user opted into the loop; they deserve to watch it run.
- **Don't retry forever.** If attempt 3 fails, print the accumulated blockers
  and patches and stop. Do not silently fall through to the next step.

---

## When to invoke

- User asks to "build a BSM model", "create a Lagrangian with SARAH", or
  "run SARAH + SPheno for my model".
- User provides a ModelSpec YAML and wants to process it.
- User says "use model `<name>`" and the model is already registered in config.
- User asks for "relic density", "direct-detection exclusion", "Higgs
  constraints", or "one-loop scattering" on a built model — see
  §Constraint & observable dispatch below.

---

## Overview: what this skill does

```
User input
    │
    ├─ (a) Interactive interview  ─┐
    ├─ (b) Existing spec YAML  ───┤─→ validated ModelSpec YAML
    └─ (c) Named model (config) ──┘
                 │
    Step 1: Check state (check_state.py)
                 │
    Step 2: Install SARAH if missing (/sarah-install)
          ↳  if activation_required: pause + show user_instruction, stop
                 │
    Step 3: Run /sarah-build <spec.yaml>
                 │
    Step 3b: SARAH output verification  (check_vertices + check_mass_matrix)
          ↳  on blocker: consult sarah-gotchas.md, patch spec (Q3/Q4),
             re-validate, re-run Step 3. Max 3 attempts.
                 │
    Step 4: Install SPheno if missing (/spheno-install)
                 │
    Step 5: Run /spheno-build <name>
                 │
    Step 5b: SPheno spectrum verification  (check_spectrum)
          ↳  on blocker: consult sarah-gotchas.md. If SARAH-stage,
             jump back to Step 3 with a Q3 patch; if SPheno-stage,
             re-run Step 5 with a Q2-defaults patch. Max 3 attempts.
                 │
    Step 6: Register model (register_model.py)
                 │
    Step 7: Report paths (+ iteration history) + suggest /madgraph use <name>
```

---

## Step 0: What is your input?

Before doing anything else, determine which input path the user is on.

### (a) Interactive interview

The user wants to describe a model in natural language. Follow
`references/interview.md` to elicit the minimal ModelSpec fields through a
guided Q&A. **Start by announcing the scope tier** (§0 of `interview.md`) so
the user knows whether this is a 30-minute cheap authoring job, a
paper-reviewer-required session, or specialist scope that needs an analytic
module first. **During the field-content phase**, run the mixing-choice gate
(§4.5 of `interview.md`) whenever the detection heuristic matches — the DSL
cannot guess which rotation the paper uses. When the draft is complete, show
it as YAML and ask the user to confirm. Then validate:

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/validate_spec.py \
    <draft_spec.yaml>
```

If validation fails, the script emits `MODELSPEC_INVALID` on stderr. Show the
error to the user, offer to fix the specific field, and re-validate. Repeat
until exit 0.

### (b) Existing ModelSpec YAML

The user provides a path or pastes a YAML. Write it to a temp file, then
validate as above. Proceed on exit 0.

### (c) Named model from config

The user says something like "build dark_su3" or "use dark_su3". Check if it
is already registered:

```bash
python3 plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py \
    --model dark_su3
```

- If `model.status == "present"`: the model is already built. Show the user the
  registered paths (UFO, latest SLHA) and offer `/madgraph use dark_su3`.
  Do NOT rebuild unless the user explicitly asks.
- If `model.status == "missing"`: look for a v3 reference spec in
  `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/`.
  If found, offer to use it as a starting point or to run the interview to build a fresh spec.
  If not found, fall through to path (a).

---

## Step 1: Check state

```bash
python3 plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py
```

Output JSON:
```json
{
  "sarah_install": "configured|missing",
  "spheno_install": "configured|missing",
  "wolfram_install": "configured|missing",
  "model": {"status": "present|missing", "name": "<name-or-null>"}
}
```

Use this JSON to decide which steps are skippable:
- `sarah_install == "configured"` → skip Step 2 (SARAH install).
- `spheno_install == "configured"` → skip Step 4 (SPheno install).
- `model.status == "present"` and the user did not ask to rebuild → stop at
  Step 0(c) and report existing outputs.

---

## Step 2: Sequence installs + builds

### 2a. SARAH install (if sarah_install == "missing")

Invoke `/sarah-install` subskill. The decision tree inside `/sarah-install`:

```
/sarah-install detect
    │
    ├─ configured → skip (already in config)
    ├─ found → ask user if they want to use the found path
    └─ missing → invoke /sarah-install install
```

**Handling `activation_required`** (CRITICAL):

If `/sarah-install` returns `{"status":"activation_required","user_instruction":"..."}`:

1. Show the user exactly the `user_instruction` field from the JSON.
2. **Stop the pipeline here.** Do not continue to SARAH build.
3. Tell the user: "Once you have activated Wolfram Engine, run
   `/lagrangian-builder` again — it will detect SARAH as configured and
   skip the install step."

This is NOT a blocker. It is a user-actionable pause. Do not emit a fatal
blocker JSON for this condition.

### 2b. SARAH build

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py \
    <spec.yaml> [--force]
```

On success: SARAH has written UFO and SPheno source trees under
`$STATE_ROOT/models/<name>/`. Move to Step 2b-verify (SARAH output
verification) **before** advancing to Step 2c. Do not skip 2b-verify even
if `build.py` exited 0 — SARAH can exit cleanly while silently dropping
vertices or producing a degenerate mass matrix.

On failure: a blocker JSON is emitted on stderr. See the Blocker handling
table below.

### 2b-verify. SARAH output verification  *(this is the "Step 3b" the retry loop targets)*

SARAH can exit 0 and still be wrong in two well-known ways: it can drop
vertices it judges redundant (silently), and it can emit a mass matrix
that is degenerate or rank-deficient. Two diagnostic checks run after
every successful SARAH build:

> **Invoke** `check_vertices.py` and `check_mass_matrix.py` in sequence.

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/check_vertices.py \
    --spec <spec.yaml> \
    --output-dir $STATE_ROOT/models/<name>/sarah_output/UFO/<SarahName>/

python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/check_mass_matrix.py \
    --spec <spec.yaml> \
    --output-dir $STATE_ROOT/models/<name>/sarah_output/
```

`<SarahName>` is the CamelCase form of the spec's `name` as produced by
`plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` (e.g. `singlet_doublet`
→ `SingletDoublet`). A convenience symlink
`$STATE_ROOT/models/<name>/<SarahName>` points at the same UFO directory and
is equally valid as `--output-dir` for `check_vertices.py`.

Expected blocker codes (non-zero exit, JSON on stderr):

| Exit | Code | What it means | Interview question implicated |
|---|---|---|---|
| 1 | `VERTICES_MISSING` | A vertex implied by the spec's Lagrangian isn't in the UFO | Q3 — enumeration missed a contraction, or a term was wrongly deleted |
| 2 | `VERTICES_UNEXPECTED` | UFO contains a vertex the spec did not declare | Q3 — spurious term, often a discrete-symmetry violation that should have been marked |
| 1 | `MASS_MATRIX_DEGENERATE` | Two eigenvalues are numerically identical (no mixing to resolve them) | Q4 — missing or misnamed mixing |
| 2 | `MASS_MATRIX_RANK_DEFICIENT` | Mass matrix has a zero eigenvalue where one is not expected | Q4 (missing mixing), or Q3 (missing mass term) |

**Retry loop (bounded: max 3 attempts per stage).**

On each non-zero exit from either check:

1. Print the attempt banner:
   `Attempt <N> of 3 — SARAH verification`
   Include `blockers_seen[]` and `patches_applied[]` so far.
2. Print the full blocker JSON to the user.
3. Tell the user which interview question the blocker maps to (from the
   table above) and that you are re-authoring that part of the spec.
   Example: *"`VERTICES_MISSING` implies Q3 missed a contraction.
   Consulting `references/sarah-gotchas.md` for the patch recipe."*
4. Look up the blocker code in
   `plugins/hep-ph-toolkit/skills/lagrangian-builder/references/sarah-gotchas.md`.
   The doc maps each code above to a concrete spec patch (e.g.
   "add `AddHC->True` to this mass term", "split contraction into
   `conj[H]·FS·PsiDu` + `H·FS·PsiDd`").
5. Apply the patch to the spec YAML. Show the diff to the user.
6. Re-validate:
   ```bash
   python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/validate_spec.py \
       <patched_spec.yaml>
   ```
   If validation fails, that's a fatal — surface `MODELSPEC_INVALID` and stop.
   (The patch recipe in the gotchas doc is expected to produce a valid
   spec; a validation miss there means the gotchas doc is wrong, which
   the user needs to see.)
7. Re-run Step 2b (`build.py <patched_spec.yaml> --force`).
8. Re-run the two checks. Increment the attempt counter.
9. Append `{code, attempt, patch}` to `blockers_seen[]` and
   `patches_applied[]`.

**On attempt 3 failure:** print all accumulated blockers and patches.
Emit a fatal-style summary (no new blocker code — surface the last
blocker JSON) and stop the pipeline. The user must inspect the spec
manually or update the gotchas doc with the novel failure mode.

**If the blocker schema or either check script itself fails to parse
(invalid JSON on stderr, non-schema-conformant output):** that is a
genuine fatal — do not swallow it, do not retry. Surface the raw stderr
and stop.

### 2c. SPheno install (if spheno_install == "missing")

Invoke `/spheno-install` subskill:

```
/spheno-install detect
    │
    ├─ configured → skip
    ├─ version_mismatch → /spheno-install install (fresh alongside)
    └─ missing → /spheno-install install
```

### 2d. SPheno build

```bash
python3 plugins/hep-ph-toolkit/skills/spheno-build/scripts/run_spheno.py \
    <model_name>
```

On success: SLHA spectrum file written to
`$STATE_ROOT/models/<model_name>/runs/<TS>/SPheno.spc`. Move to
Step 2d-verify (SPheno spectrum verification) **before** advancing to
Step 3. As with SARAH, SPheno can exit 0 with a spectrum that is NaN,
unphysical, or that contains a zero for a parameter the spec declared
as non-zero.

On recoverable failure from `run_spheno.py` (e.g. `SPHENO_SPECTRUM_PROBLEM`):
**do not offer "scan a different region" yet** — first run Step 2d-verify
(below). If `check_spectrum.py` also fires, the retry loop owns the
resolution; the recoverable offer only applies when `check_spectrum.py`
passes cleanly. See §Recoverable outcomes and the handler-scope table at
the end of Step 2d-verify.

On fatal failure: see Blocker handling table.

### 2d-verify. SPheno spectrum verification  *(this is the "Step 5b" the retry loop targets)*

> **Invoke** `check_spectrum.py` on the freshly written SLHA file.

```bash
python3 plugins/hep-ph-toolkit/skills/spheno-build/scripts/check_spectrum.py \
    --spec <spec.yaml> \
    --slha $STATE_ROOT/models/<name>/runs/<TS>/SPheno.spc
```

Expected blocker codes:

| Exit | Code | What it means | Likely stage to retry | Interview question |
|---|---|---|---|---|
| 1 | `SPECTRUM_NAN` | One or more entries in `Block MASS` are NaN/inf | SPheno-stage first — almost always a parameter default that drove the spectrum off a branch; try a different Q2 default. If the same NaN reappears after a defaults patch, fall back to SARAH (missing term in Q3). | Q2 (defaults) first, Q3 second |
| 2 | `SPECTRUM_UNPHYSICAL` | Negative-mass-squared, tachyonic vacuum, or charged LSP | SPheno-stage — parameter defaults drove EWSB into a bad vacuum. Patch Q2 defaults, re-run SPheno only. | Q2 (defaults) |
| 3 | `SPECTRUM_ZERO_NONZERO_PARAM` | A parameter the spec declared as non-zero comes out exactly zero in the SLHA | **SARAH-stage first** — this is the canonical fingerprint of a dropped vertex (the coupling was never wired through, so SPheno sees it as 0). Jump back to Step 2b with a Q3 patch. Only if the jump-back also yields zero, fall through to Q2 defaults. | Q3 (primary), Q2 (fallback) |

**Judgment call on `SPECTRUM_ZERO_NONZERO_PARAM`:** this blocker straddles
the SARAH/SPheno boundary. A zero parameter in the SLHA can mean (a) SARAH
dropped the vertex that parameter lives on (Q3 issue, fix upstream) or
(b) the spec set the parameter's default to zero in a way that cascaded
(Q2 issue, fix downstream).
**The SARAH-stage explanation is dominant in practice** (dropped vertices
are the #1 silent failure of this pipeline per the interview preamble),
so retry there first. `references/sarah-gotchas.md` entry for
`SPECTRUM_ZERO_NONZERO_PARAM` defines the discriminating test (run
`check_vertices.py` again with a `--coupling <param>` filter — if the
coupling is missing from the UFO, it's a Q3 patch; if present with a
non-zero value, it's a Q2-defaults issue).

**Retry loop (bounded: max 3 attempts per stage).** Logic:

1. Print the attempt banner:
   `Attempt <N> of 3 — SPheno verification`
   Include `blockers_seen[]` and `patches_applied[]` so far.
2. Print the full blocker JSON.
3. Determine **which stage to retry** by consulting
   `references/sarah-gotchas.md` for this blocker code.
   - If the doc says "SARAH-stage": patch the spec per the recipe,
     **jump back to Step 2b** (re-run SARAH from scratch with
     `--force`), then re-run 2b-verify, then come back and re-run 2d
     and 2d-verify. The SARAH-stage attempt counter is shared with
     Step 2b-verify (a patch that bounces from 2d-verify back to 2b
     counts against the 3-attempt cap of *both* stages — don't let a
     `SPECTRUM_ZERO_NONZERO_PARAM` → Q3 patch ping-pong silently).
   - If the doc says "SPheno-stage": patch the spec's parameter
     defaults (Q2) per the recipe, **re-run only Step 2d**
     (`run_spheno.py <name>` again — no SARAH rebuild needed since the
     couplings are unchanged).
4. Show the patch diff to the user. Name the interview question (Q2
   or Q3) that the patch corresponds to, so the user sees which part
   of the spec is being re-authored.
5. Re-validate the spec (`validate_spec.py`) after every patch.
6. Re-run the appropriate stage, then re-run `check_spectrum.py`.
   Increment the attempt counter.
7. Append `{code, attempt, stage, patch}` to `blockers_seen[]` and
   `patches_applied[]`.

**On attempt 3 failure:** same contract as Step 2b-verify — print
accumulated blockers + patches and stop.

**If `check_spectrum.py` itself fails to produce valid blocker JSON:**
fatal, surface the raw stderr, stop.

### Handler scope: `SPECTRUM_*` (retry loop) vs `SPHENO_SPECTRUM_PROBLEM` (recoverable)

Two independent detectors run on the freshly-written SLHA. They must not be
confused — they answer different questions, and when both fire on the same
run, the retry loop wins.

| Detector | Emits from | Semantic | Handler |
|---|---|---|---|
| `check_spectrum.py` | *our* SLHA scan (NaN / unphysical mass / zero-default-nonzero-spec-param) | **Spec correctness** — the spec, SARAH output, or MINPAR wiring is broken and re-authoring will fix it | **Retry loop** (§Step 2d-verify above) |
| `run_spheno.py` emits `SPHENO_SPECTRUM_PROBLEM` | SPheno's own `Block PROBLEM` codes 1/2/3 in the SLHA | **Parameter-point physicality** — the spec is fine, this parameter point is in a bad region (tachyonic vacuum, charged LSP per SPheno's internal check) and a different point will succeed | **Recoverable offer-to-user** (§Recoverable outcomes below) |

**Ordering rule when both fire on the same run.** `run_spheno.py` emits
`SPHENO_SPECTRUM_PROBLEM` *before* `check_spectrum.py` runs, so both signals
can be present for the same SLHA. Resolve in this order:

1. **Always run `check_spectrum.py`, even if `run_spheno.py` already emitted
   `SPHENO_SPECTRUM_PROBLEM`.** SPheno's `Block PROBLEM` flag frequently
   fires *because* of an upstream spec bug (a dropped vertex leaves a zero in
   a mass matrix, which then tachyonic-squares after EWSB and SPheno flags
   it). Fixing the spec usually clears the `Block PROBLEM` flag too.
2. If `check_spectrum.py` emits any `SPECTRUM_*` blocker, **route to the
   retry loop** (treat `SPHENO_SPECTRUM_PROBLEM` as a downstream symptom,
   not the root cause). Show the user both blockers; name which one is
   driving the retry.
3. If `check_spectrum.py` exits 0 (spectrum is structurally fine — no NaN,
   no unphysical mass, no zero-where-nonzero-was-declared) *and*
   `SPHENO_SPECTRUM_PROBLEM` was emitted, **route to §Recoverable outcomes**
   — the spec is correct, this is a genuine "bad parameter point" and the
   user should scan elsewhere. Do **not** engage the retry loop for this
   case; it will not converge (re-running SARAH with the same spec produces
   the same UFO, and the same point will fail the same way).
4. If `check_spectrum.py` exits 0 and no `SPHENO_SPECTRUM_PROBLEM` was
   emitted, the spectrum is clean — proceed to Step 3.

The retry loop's 3-attempt cap owns `SPECTRUM_*` only. Never count a
`SPHENO_SPECTRUM_PROBLEM` against the retry budget.

---

## Step 3: Register model

```bash
python3 plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/register_model.py \
    <name> \
    --spec    <path/to/spec.yaml> \
    --ufo     <path/to/ufo/> \
    [--latest-slha   <path/to/SPheno.spc>] \
    [--spheno-bin    <path/to/binary>] \
    [--sarah-built-at  <iso8601>] \
    [--spheno-built-at <iso8601>]
```

This writes the model registry entry atomically via `config_helpers.register_model`.

---

## Step 4: Report paths and next steps

Show the user a brief summary, **including the iteration history** from
Steps 2b-verify and 2d-verify. This is the "don't hide the retries"
contract from the interview preamble — the user opted into 2–3 passes,
so the final report tells them exactly how many passes happened and why.

```
Model `<name>` is ready.

  UFO directory:  <ufo_path>
  Latest SLHA:    <slha_path>   (parameter defaults from spec)
  Config key:     config.models["<name>"]

Iteration history:
  SARAH verification:   <1|2|3> attempt(s)
  SPheno verification:  <1|2|3> attempt(s)

  Blockers encountered and patched:
    - [attempt 1, SARAH] VERTICES_MISSING (Q3)
        patch: split Yukawa contraction `H·FS·PsiD` into
               `conj[H]·FS·PsiDu` + `H·FS·PsiDd`  (per sarah-gotchas.md)
    - [attempt 2, SPheno] SPECTRUM_ZERO_NONZERO_PARAM (Q3 via fallback to SARAH)
        patch: added `AddHC->True` to Majorana mass term `MN`
  (If both counters are 1 and no blockers fired, print
   "Pipeline converged on first pass — no patches needed.")

Next steps:
  /madgraph use <name>         — import the UFO model and generate events
  /spheno-build <name> --scan  — scan the parameter space
```

If either verification stage exhausted its 3-attempt cap, this Step 4
is not reached — the pipeline stopped at the cap. In that case the
"accumulated blockers and patches" dump is printed at the stop point,
not here.

---

## Constraint & observable dispatch

After a model is built (UFO + SLHA present), the orchestrator recognises four
additional user intents and emits the corresponding sub-skill chain. The model
**must** already be registered (Step 3 complete) before dispatching any
constraint chain; if it is not, run the full build pipeline first.

### Prerequisites

Before dispatching any constraint chain, verify that the relevant install-time
tool is configured. If it is missing, stop and instruct the user to run the
corresponding install skill:

| Intent | Required install skill |
|---|---|
| relic density | `/micromegas-install` |
| direct-detection exclusion | `/micromegas-install` + `/ddcalc-install` |
| Higgs constraints | `/higgstools-install` |
| one-loop scattering | `/feynarts-install` + `/formcalc-install` (+ optionally `/ddcalc-install`) |

### Intent 1 — relic density

**Trigger phrases:** "compute relic density", "what is Ωh²", "check relic
abundance", "does this model saturate the Planck relic?"

**Single-call chain:**

```
/micromegas relic <model> \
    --slha    <config.models[<name>].latest_slha> \
    --ufo     <config.models[<name>].ufo_path>
    # Preferred: spec.yaml carries dm_candidate.pdg — no extra flag needed.
    # Fallback:  --dm-pdg <spec.dm_candidate.pdg>   (explicit PDG override)
    # Opt-in:    --auto-detect                       (parse SLHA + UFO attrs)
```

Emit `summary.json` at `$STATE_ROOT/models/<name>/micromegas_runs/<TS>/`.
Report Ωh² versus the Planck 2018 target (0.120 ± 0.0012) and flag
`RELIC_BEPS_SENSITIVE` if present.

### Intent 2 — direct-detection exclusion

**Trigger phrases:** "direct-detection exclusion", "DD exclusion",
"LUX/XENON/PandaX limits", "is this model excluded by direct detection?"

**Two-stage chain:**

```
Stage 1:
/micromegas scatter <model> \
    --slha  <config.models[<name>].latest_slha> \
    --ufo   <config.models[<name>].ufo_path>

    → produces: summary.json
      (schema: scattering/v1 at micromegas_runs/<TS>/summary.json)

Stage 2:
/ddcalc exclude \
    --sigma-json <micromegas_runs/<TS>/summary.json>

    → produces: ddcalc_result/v1 at $STATE_ROOT/runs/ddcalc/<TS>/result.json
```

Pass the `summary.json` path from Stage 1 directly into `--sigma-json` for
Stage 2. Do not read or reformat its contents — `/ddcalc` reads it natively.
Report the overall verdict (`excluded` / `allowed` / `marginal`) and list any
per-experiment exclusions.

### Intent 3 — Higgs constraints

**Trigger phrases:** "Higgs constraints", "HiggsBounds check",
"HiggsSignals consistency", "does the model pass Higgs signal rates?",
"check LEP/Tevatron/LHC Higgs bounds"

**Single-call chain:**

```
/higgstools run <model> \
    --slha <config.models[<name>].latest_slha>
```

Produces `result.json` at `$STATE_ROOT/models/<name>/runs/<TS>/higgstools/`.
Report `hb_allowed` (HiggsBounds AND-of-channels) and `hs_consistent`
(Δχ² < 6.18 by default). Show `obsratio_max` and the most sensitive channel.

**Prerequisite note:** the SLHA must contain
`HiggsBoundsInputHiggsCouplingsX` blocks (produced by SPheno with
`WriteHiggsBoundsBlocks=True` in `SPheno.m`). If they are absent, stop and
emit fatal `HIGGSTOOLS_SLHA_MISSING_BLOCKS` — do **not** synthesize effective
couplings in Python.

### Intent 4 — one-loop scattering (σ_SI)

**Trigger phrases:** "one-loop scattering", "loop-level σ_SI",
"loop-corrected direct detection", "blind-spot analysis",
"compute σ_SI at one loop"

**Process string:** replace the placeholder process with your model's actual 2→2
string using particle labels from `particles.m`. The format is
`"<dm-field> <dm-field> -> <sm-field> <sm-field>"` where field names come from
the SARAH `particles.m` output (not PDG names).

For the confining-variant `dark_su3` (now deleted; the canonical Higgsed
dark-Higgs spec is `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/dark_su3.yaml`),
`particles.m` defines `psiDL`/`psiDR` as the dark-quark Weyl components;
the Dirac pair is conventionally written `psiD`. The concrete Stage 1 call
becomes:
```
/feynarts generate \
    --process   "psiD psiDbar -> u uBar" \
    --sarah-model dark_su3 \
    --loop-order  1
```
Passing the generic placeholder `"DM DM -> q q"` literally will cause a
FeynArts parse error — always substitute real field names.

**Three-stage chain (with optional Stage 4):**

```
Stage 1:
/feynarts generate \
    --process   "<dm-field> <dm-field> -> <sm-field> <sm-field>" \
    --sarah-model <name> \
    --loop-order  1

    → produces: FeynAmpList.m + FeynAmpList.meta.json

Stage 2:
/formcalc reduce \
    --feynamp    <feynarts_output/FeynAmpList.m> \
    --process    <feynarts_output/FeynAmpList.meta.json> \
    [--gamma5    naive]  (omit if no γ₅; see FORMCALC_G5_SCHEME_REQUIRED)

    → produces: amp_reduced.m + amp_reduced.meta.json

Stage 3:
/formcalc looptools \
    --amp-x      <formcalc_output/amp_reduced.m> \
    --meta       <formcalc_output/amp_reduced.meta.json> \
    --m-dm       <DM mass in GeV from SLHA>

    → produces: sigma.json
      (schema: scattering/v1; source = "looptools")

Stage 4 (optional — invoke if user also wants exclusion verdict):
/ddcalc exclude \
    --sigma-json <formcalc_output/sigma.json>

    → produces: ddcalc_result/v1
```

If the user asked only for σ_SI, stop after Stage 3 and report the value.
If the user asked whether the model is excluded, run Stage 4 and report the
verdict.

**γ₅ gate:** before running Stage 2, check whether the model's DM–quark
amplitude contains γ₅ projectors. For Dirac DM with axial couplings, pass
`--gamma5 naive` unless the user specifies otherwise. Omitting this flag when
γ₅ is present causes `FORMCALC_G5_SCHEME_REQUIRED` (fatal).

---

## Data-flow diagram

```
SLHA file                  UFO directory
    │                           │
    └───────────┬───────────────┘
                ▼
        ┌─────────────────────────────────────────────────────────┐
        │  Intent 1: relic density                                │
        │  /micromegas relic  →  summary.json  →  report (Ωh²)   │
        └─────────────────────────────────────────────────────────┘
                │
                │ (same inputs also feed Intent 2)
                ▼
        ┌─────────────────────────────────────────────────────────┐
        │  Intent 2: direct-detection exclusion (tree-level)      │
        │  /micromegas scatter  →  summary.json (scattering/v1)   │
        │                            │                            │
        │                            ▼                            │
        │                   /ddcalc exclude  →  result.json       │
        │                        (ddcalc_result/v1)               │
        └─────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────────┐
        │  Intent 3: Higgs constraints                            │
        │  /higgstools run  →  result.json  →  report (hb+hs)     │
        └─────────────────────────────────────────────────────────┘

        ┌─────────────────────────────────────────────────────────┐
        │  Intent 4: one-loop scattering (σ_SI)                   │
        │  /feynarts generate  →  FeynAmpList.m                   │
        │          │                                              │
        │          ▼                                              │
        │  /formcalc reduce   →  amp_reduced.m                    │
        │          │                                              │
        │          ▼                                              │
        │  FormCalc + LoopTools  →  sigma.json (scattering/v1)    │
        │          │                                              │
        │          └─ (optional) /ddcalc exclude  →  result.json  │
        └─────────────────────────────────────────────────────────┘

Key data contracts:
  scattering/v1       plugins/shared/schemas/scattering.schema.json
  ddcalc_result/v1    in /ddcalc SKILL.md §Output schema
  amp_reduced.meta/v1 plugins/shared/schemas/amp_reduced.meta.schema.json
  processspec/v1      plugins/shared/schemas/processspec.schema.json
```

---

## Recoverable outcomes

These conditions are NOT fatal. The pipeline continues, but the user should
be informed. These are **parameter-point** signals — the spec is sound, but
this point in parameter space doesn't give a good spectrum. For
**spec-correctness** signals (`SPECTRUM_NAN`, `SPECTRUM_UNPHYSICAL`,
`SPECTRUM_ZERO_NONZERO_PARAM`) see §Step 2d-verify / the retry loop — those
codes are owned there, not here.

| Blocker code | Meaning | Suggested action |
|---|---|---|
| `SPHENO_SPECTRUM_PROBLEM` | SPheno's own `Block PROBLEM` flagged a spectrum problem at this parameter point (and `check_spectrum.py` passed, ruling out a spec bug) | Try different parameter values; use `--scan` to map the valid region |
| `SPHENO_RGE_NONCONVERGENT` | RGE solution did not converge | Try a lighter spectrum (smaller `MpsiD`); tighten the SPHENOINPUT convergence threshold |

When a recoverable blocker appears in the output:
1. Show the user the blocker JSON (code + message + context).
2. Do NOT stop the pipeline if there are other scan points remaining.
3. Offer the suggested action.

**Gate before offering "try different parameters" on `SPHENO_SPECTRUM_PROBLEM`:**
always run `check_spectrum.py` first (see §Step 2d-verify). If it emits any
`SPECTRUM_*` code, the spec is broken — engage the retry loop instead of
offering a parameter scan. Offering a scan on a broken spec wastes the
user's time because the next point will fail the same way.

---

## Fatal outcomes

These conditions stop the pipeline. Show the full blocker JSON from stderr.

| Blocker code | Source skill | Meaning | Resolution |
|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `/sarah-install` | Wolfram Engine not configured | Run `/install` first; install Wolfram Engine |
| `SARAH_DOWNLOAD_FAILED` | `/sarah-install` | Tarball download failed | Check network; retry |
| `SARAH_SMOKE_TEST_FAILED` | `/sarah-install` | SARAH installed but version probe fails | Check Wolfram activation; try `wolframscript --activate` |
| `MODELSPEC_INVALID` | `/sarah-build` | Spec fails schema or semantic validation | Fix the spec per the error context; see `validate_spec.py` output |
| `ANOMALY_CANCELLATION_FAILED` | `/sarah-build` | Gauge anomalies do not cancel | See `references/anomaly-ledger.md`; modify the field content |
| `SARAH_OUTPUT_MISSING` | `/sarah-build` | SARAH ran but produced no UFO directory | Check `sarah.log`; may indicate SARAH version mismatch |
| `GFORTRAN_ABSENT` | `/spheno-install` | `gfortran` not on PATH | Install per OS (see `/spheno-install` SKILL.md) |
| `SPHENO_BASE_BUILD_FAILED` | `/spheno-install` | `make` failed during SPheno base install | See `context.make_log_tail` and `likely_cause` |
| `SPHENO_COMPILE_FAILED` | `/spheno-build` | Model-specific SPheno compile failed | Check `make.log` in `context`; verify SARAH output is complete |
| `SPHENO_NO_OUTPUT` | `/spheno-build` | SPheno binary ran but produced no `.spc` | Check SLHA input card; inspect stderr from run |
| `MODELSPEC_FEATURE_UNSUPPORTED` | (W5 guard) | User requested out-of-schema feature | See "Unsupported features" section below |

For every fatal blocker:
1. Show the full JSON (code, message, context if present, user_instruction if present).
2. **Stop the pipeline.** Do not proceed to the next step.
3. If `user_instruction` is set, show it prominently as a concrete action.

---

## Unsupported features

If the user requests any of the following, emit `MODELSPEC_FEATURE_UNSUPPORTED`
and stop. Do NOT fall back to free-form Mathematica or analytic Python.

- Superpotential blocks (SUSY models).
- `MakeCalcHEP[]`, `MakeFeynArts[]`, `MakeWHIZARD[]`.
- Outputs other than `ufo` and `spheno`.
- Free-form `.m` file injection into SARAH templates.
- Dimension-5 or higher operators in the ModelSpec.

Emit the blocker on stderr:
```json
{
  "code": "MODELSPEC_FEATURE_UNSUPPORTED",
  "mode": "fatal",
  "message": "The requested feature is not supported in ModelSpec v1.",
  "context": {"requested_feature": "<description>"},
  "user_instruction": "See plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md §Unsupported features for the v1 scope."
}
```

---

## Example: end-to-end transcript (dark_su3 — confining variant, archived)

> **Archived narrative.** This transcript walks through the *confining*
> dark-quark variant of dark SU(3); that template has been deleted in the
> v3 modelspec rollout. The canonical Higgsed dark-Higgs Dark SU(3) (used
> by the `/dark-su3` demo skill and the `analytic_models.dark_su3` spectrum
> module) is at
> `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/dark_su3.yaml`.
> The transcript is retained here as worked-example prose for the
> `/lagrangian-builder` interview flow; do not treat it as a recipe to
> reproduce arXiv:2506.19062.

This transcript shows the full cold-start flow for `dark_su3` — a vector-like
dark quark with a new confining SU(3)_dark gauge group. No tools are installed
at the start.

**User:** Build a dark SU(3) model with a Dirac dark quark charged under a new
SU(3)_dark, singlet under SU(2)_L and U(1)_Y.

**Claude:**

1. Starts Step 0 (interview): asks about gauge groups, fermion reps,
   mass terms.  User confirms the spec matches `dark_su3.yaml`.

2. Writes spec to `/tmp/dark_su3_spec.yaml`. Runs `validate_spec.py`. Exit 0.

3. Runs `check_state.py`. Output:
   ```json
   {"sarah_install":"missing","spheno_install":"missing","wolfram_install":"missing","model":{"status":"missing","name":null}}
   ```

4. SARAH is missing; Wolfram is missing. Shows the user:
   "SARAH requires Wolfram Engine (free). Invoking `/sarah-install`..."
   Runs `/sarah-install detect` → `{"status":"missing"}`.
   Runs `/sarah-install install`.
   SARAH tarball downloads and extracts.
   `check_wolfram_activation.sh` runs.
   Returns: `{"status":"activation_required","user_instruction":"Run `wolframscript --activate` in your terminal..."}`.

5. **Pipeline pauses.** Claude shows:
   ```
   Wolfram Engine activation required.
   Action: Run `wolframscript --activate` in your terminal.
   This opens a browser for a free Wolfram ID signup.
   Once done, run /lagrangian-builder again.
   ```

---

*(User activates Wolfram Engine and re-runs /lagrangian-builder)*

---

6. `check_state.py` now returns `sarah_install: "configured"`. Skip install.

7. Runs `build.py /tmp/dark_su3_spec.yaml`.
   SARAH renders `DarkSU3.m`, runs `wolframscript -code
   'AppendTo[$Path,"~/SARAH/SARAH-4.15.3/.."]; <<SARAH`; Start["DarkSU3"]; ...'`.
   `CheckModel[]` passes (anomaly cancellation OK for vector-like quarks).
   `MakeUFO[]` and `MakeSPheno[]` complete.
   UFO at `$STATE_ROOT/models/dark_su3/ufo/`.
   SARAH output at `$STATE_ROOT/models/dark_su3/sarah_output/`.

8. SPheno is missing. Runs `/spheno-install install`. `gfortran` present.
   Tarball downloads; `make` compiles (~5 min). Both keys written.

9. Runs `run_spheno.py dark_su3`.
   Compiles model-specific binary `SPheno<DarkSU3>` (~2 min).
   Runs single point (defaults: `MpsiD=500`, `gD=1.0`).
   `SPheno.spc` written. Clean `Block MASS` present.

10. `register_model.py dark_su3 --spec ... --ufo ... --latest-slha ...`

11. Reports:
    ```
    Model `dark_su3` is ready.

    UFO directory: ~/.local/share/hephaestus/models/dark_su3/ufo/
    Latest SLHA:   ~/.local/share/hephaestus/models/dark_su3/runs/<TS>/SPheno.spc

    Next steps:
      /madgraph use dark_su3       — generate collider events
      /spheno-build dark_su3 --scan MpsiD=200:1000:step=100 gD=0.5:2.5:step=0.5
    ```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/check_state.py` | Probe SARAH/SPheno/Wolfram install state + model registration |
| `scripts/register_model.py` | CLI to write `config.models[<name>]` atomically |

Reference docs in `references/`:
- `interview.md` — structured interview flow to elicit ModelSpec from user
  (§Iteration expectations maps checkpoint blockers to Q3/Q4 revisions)
- `orchestration.md` — full state diagram, skip conditions, blocker propagation
- `anomaly-ledger.md` — reading `ANOMALY_CANCELLATION_FAILED` output
- `sarah-gotchas.md` — per-blocker-code patch recipes consulted by the
  Step 2b-verify / 2d-verify retry loops; also the place to add novel
  failure modes if attempt 3 exhausts without resolving.

v3 reference specs in `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/`:
- `singlet_doublet.yaml` — minimal fermion DM
- `2hdm_a.yaml` — two-Higgs-doublet model + pseudoscalar mediator
- `dark_su3.yaml` — SU(3)_D → SU(2)_D Higgsed dark sector (canonical Higgsed variant)
- `ssm.yaml` — scalar singlet model

---

## Linkage

| Dependency | Location |
|---|---|
| Shared Python helpers | `plugins/shared/install-helpers/config_helpers.py` |
| ModelSpec v3 schema | `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json` |
| ModelSpec v3 SM template | `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml` |
| ModelSpec v3 reference specs | `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/{singlet_doublet,dark_su3,2hdm_a,ssm}.yaml` |
| Blocker schema | `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` |
| SARAH name canonicalization | `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` |
| Shared conventions | `plugins/hep-ph-toolkit/SHARED-model-building.md` |
| Sub-skill: SARAH install | `plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md` |
| Sub-skill: SARAH build | `plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` |
| Sub-skill: SPheno install | `plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md` |
| Sub-skill: SPheno build | `plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` |
| Named model resolver | `plugins/hep-ph-toolkit/skills/madgraph/scripts/resolve_named_model.py` |
| Constraint: micrOMEGAs | `plugins/hep-ph-toolkit/skills/micromegas/SKILL.md` |
| Constraint: DDCalc | `plugins/hep-ph-toolkit/skills/ddcalc/SKILL.md` |
| Constraint: HiggsTools | `plugins/hep-ph-toolkit/skills/higgstools/SKILL.md` |
| Loop: FeynArts | `plugins/hep-ph-toolkit/skills/feynarts/SKILL.md` |
| Loop: FormCalc | `plugins/hep-ph-toolkit/skills/formcalc/SKILL.md` |
| Loop: LoopTools | (via FormCalc integration) |
| Scattering schema | `plugins/shared/schemas/scattering.schema.json` |
| Amplitude reduced schema | `plugins/shared/schemas/amp_reduced.meta.schema.json` |
| Process spec schema | `plugins/shared/schemas/processspec.schema.json` |
