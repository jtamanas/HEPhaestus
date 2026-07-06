---
name: singlet-doublet
description: Constraint-first workflow for the Singlet-Doublet fermion DM model (arXiv:2506.19062 §II). Interviews the user for constraints (relic, direct detection, indirect detection), shows the prereq chain with a time estimate, gates for confirmation, then drives /sarah-build → /spheno-build → /madgraph → /maddm for the ready subset. Invoke when the user picks Singlet-Doublet from /demo or says "run singlet-doublet".
---

# Singlet-Doublet

Per-model constraint workflow for the Singlet-Doublet fermion dark matter
benchmark from Arcadi & Profumo (arXiv:2506.19062 §II). The DM candidate is a
Majorana fermion `chi1` — the lightest eigenstate of the singlet-doublet mixing
matrix — whose tree-level SI cross-section vanishes at the **blind spot** where
the singlet and doublet components interfere destructively.

This skill never computes physics analytically. Every observable is produced by
a real HEP tool driven via the steps below.

## When to invoke

- User selects `Singlet-Doublet` from `/demo`'s model picker (Step 3).
- User says "run singlet-doublet", "compute relic density for singlet-doublet", or similar.
- Do NOT invoke if `/demo` Step 0's preflight failed (missing config.json keys or unresponsive executables).

## Model metadata

```yaml
display:
  title: "Singlet-Doublet"
  hook:  "3×3 neutralino-like mixing, tree-level blind spot, loop floor."
dm_candidates:
  - {name: chi1, spin: "1/2", notes: "Majorana, lightest eigenstate of the singlet-doublet mixing."}
plot_axes:
  x: {symbol: "m_chi",      range: [100, 1500], units: "GeV", scale: linear}
  y: {symbol: "sin_2theta", range: [-1, 1],                   scale: linear}
multi_component: false
time_overrides:
  dd: {cold: [1.0, 2.0]}
```

## Constraints

Prereq chains and time ranges resolve from
`plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (model
`singlet-doublet`) via `_shared/time_budget.py`. Chains share the
`/sarah-build → /spheno-build → /madgraph → /maddm` prefix; a **cold** run pays
SARAH UFO (~5–8 min) + SPheno compile (~5 min) + one SPheno run (~1–10 s), a
**cached** run skips SARAH (UFO stamped) and the SPheno compile (binary
stamped) and fires only the single MadDM run.

| Constraint | Status | Tail after the shared prefix | Cold | Cached |
|---|---|---|---|---|
| Relic density | **READY** | — | 1–2 hr | 25–50 min |
| Direct detection | **READY (tree-only)** — loop floor near the blind spot pending `/looptools eval` runtime | `/maddm generate direct_detection` → `/ddcalc` | 1–2 hr | 25–50 min |
| Indirect detection | **COMING SOON** — pull computation pending (v1) | `/gamlike [v0 — parser only]` | 1–3 hr | 25–50 min |

All-constraints cold total (overlap-adjusted): **2.0–5.5 hr**. The demo is
scoped to one benchmark point — scans are out of scope and belong to callers
that drive `/maddm` directly.

## Flow

### Step 1 — DM-candidate declaration

Print verbatim:

> For **Singlet-Doublet**, the DM candidate is:
>
>   - `chi1` — Majorana, lightest eigenstate of the singlet-doublet mixing.
>
> This is a single-candidate model; relic, DD, and ID rates are computed directly for `chi1`.
>
> **Reference Lagrangian** — this is the physics content the pipeline reproduces. At Step 4a, `/lagrangian-builder` is driven interactively (using a pre-written practitioner script) to author a ModelSpec YAML from scratch; the result should be physics-equivalent to the block below up to naming:
>
>     -L ⊃ ½ M_S  FS FS                           + h.c.   # singlet Majorana mass
>        +   M_Ψ  PsiDu·PsiDd                     + h.c.   # vectorlike-doublet Dirac mass
>        +   y_h1  H*·FS·PsiDu                    + h.c.   # Higgs-portal Yukawa (Y=+½ contraction)
>        +   y_h2  H·FS·PsiDd                     + h.c.   # Higgs-portal Yukawa (Y=-½ contraction)
>
> Fields: `FS` (SM-singlet Weyl, Y=0), `PsiDu` / `PsiDd` (two left-Weyl SU(2)_L doublets with Y=+½ and Y=-½ respectively; together they form the vectorlike Dirac doublet — physically equivalent to the paper's Ψ_L + Ψ_R pair, SARAH-tooling-idiomatic because writing both as left-Weyls is what SARAH's `CalcMixingsOfMatterFields` handles without silently collapsing the neutralino mass matrix to `OnlyZero`), `H` (SM Higgs, `Y=+½`; `conj[H]` denotes the `Y=-½` conjugate). Parameters: `M_S`, `M_Ψ` (singlet and doublet Majorana-basis masses), `y_h1`, `y_h2` (the two SU(2)×U(1)-invariant singlet-doublet-Higgs contractions).
>
> The Arcadi-Profumo single Yukawa `y` and mixing angle `θ` map to the spec-level couplings via `(y_h1, y_h2) = (y cosθ, y sinθ)` — matching paper Eq. (6) as implemented in `eval/2506.19062_wimps_blind_spots/models/singlet_doublet.py::y1_y2_from_y_theta`. At θ=0 only `y_h1` is nonzero (single-Yukawa limit, Y=+½ contraction active). Both contractions are required because SU(2)×U(1) admits two independent singlet-doublet-Higgs invariants. The tree-level SI blind spot is the mass-eigenstate locus `m_{χ₁} + M_Ψ · sin(2θ) = 0` (paper Eq. 8; see `eval/.../singlet_doublet.py::blind_spot_parameter`). The induced `h-χ₁-χ₁` coupling (paper Eq. 7) vanishes on this locus, so the tree-level `σ_SI` goes to zero there.
>
> Reference YAML: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`. Practitioner script driving the interview: `plugins/hep-ph-toolkit/skills/singlet-doublet/practitioner_script.md`.

**Completion:** the block above is printed.

### Step 2 — Constraint multi-select

Ask which constraints to compute:

```json
{
  "question": "Which constraints do you want computed for this model?",
  "options": [
    {"id": "relic",    "label": "Relic density",            "description": "Ω h² via MadDM"},
    {"id": "dd",       "label": "Direct detection (tree-only)", "description": "Tree σ_SI/σ_SD via MadDM `generate direct_detection` → /ddcalc 90%-CL exclusion. Loop floor near the blind spot pending /looptools eval runtime."},
    {"id": "id",       "label": "Indirect detection",       "description": "Annihilation spectra via MadDM → GamLike / NuLike"},
    {"id": "collider", "label": "Collider (coming soon)",   "description": "Placeholder — execution is a no-op"}
  ],
  "allowMultiple": true,
  "required": true
}
```

**Completion:** at least one non-collider option is selected. If the user
selects `collider` only, re-ask with: `"Collider is a placeholder in this
iteration; nothing would run. Please also select relic, DD, or ID."`

### Step 3 — Time estimate + gate

Run (or reason from) `_shared/time_budget.py` for the selected constraints and
print the chain table, adapted to the actual selection. For `[relic, dd, id]`:

```
Planned chain for Singlet-Doublet:

  Relic density       [READY]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
    cold: 1–2 hr   cached: 25–50 min

  Direct detection    [READY — tree-only; loop floor pending /looptools eval]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS]
      → /maddm [EXISTS] (generate direct_detection) → /ddcalc [EXISTS]
    cold: 1–2 hr   cached: 25–50 min
    Note: tree σ_SI is non-zero at the canonical θ=0 benchmark
    (blind spot is m_χ₁ + M_Ψ·sin(2θ) = 0 — far from this point).

  Indirect detection  [COMING SOON — pull computation pending (v1)]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
      → /gamlike [v0 — parser only; pull-computation v1+]
    cold: 1–3 hr   cached: 25–50 min

Overlap-adjusted totals (shared prereqs counted once):
  selected + ready : cold ~1–2.5 hr,  cached ~25–55 min
  selected total   : cold ~3.2–8 hr,  cached ~1–2 hr  (if all prereqs existed)
```

Then gate. **If any selected constraint is COMING SOON:**

```json
{
  "question": "Some selected constraints have unimplemented prereqs. How to proceed?",
  "options": [
    {"id": "run_ready", "label": "Run available (drop blocked)", "description": "Run the ready constraints; skip blocked ones with a note in the final summary."},
    {"id": "back",      "label": "Back",                          "description": "Re-select constraints."},
    {"id": "cancel",    "label": "Cancel",                        "description": "Exit cleanly."}
  ],
  "allowMultiple": false,
  "required": true
}
```

**If all selected are READY:**

```json
{
  "question": "Run it? Total cold-run estimate: {cold_total} hr.",
  "options": [
    {"id": "go",     "label": "Run it", "description": "Execute the chain in order."},
    {"id": "back",   "label": "Back",   "description": "Re-select constraints."},
    {"id": "cancel", "label": "Cancel", "description": "Exit cleanly."}
  ],
  "allowMultiple": false,
  "required": true
}
```

**Completion:** one of — `cancel` (print `"Cancelled."`, exit, do NOT write
`summary.json`); `back` (return to Step 2); `run_ready` or `go` (proceed to
Step 4 with only the READY subset).

### Step 4 — Execute

Execute the READY subset of the selected constraints in order. Relic density
and tree-level direct detection are READY today; indirect detection is COMING
SOON and is skipped with a note in `summary.json`. The canonical benchmark is
the paper Fig. 1 fiducial `(MS, MPsi, y, θ) = (150, 500, 1, 0)` — the
single-Yukawa limit where `(yh1, yh2) = (1.000, 0.000)`. **One point, not a
scan.**

#### 4a. Build the model via /lagrangian-builder

> Invoke /lagrangian-builder on input path (a) (interactive interview), with the practitioner script at `plugins/hep-ph-toolkit/skills/singlet-doublet/practitioner_script.md` playing the role of the user.

This replays the four-question interview from
`plugins/hep-ph-toolkit/skills/lagrangian-builder/references/interview.md` with
both sides pre-written. For each question:

1. Print Claude's side (preamble, scope-tier announcement for Q1, enumerated Lagrangian for Q3, detected mixing sectors for Q4) as a blockquote prefixed `Claude:`.
2. Print the corresponding answer from `practitioner_script.md` as a blockquote prefixed `Practitioner:`.
3. Do **NOT** call `AskUserQuestion` — this is a rehearsed demo, not a live interview. Both sides are scripted; the formatting lets the audience follow what a real interview looks like.
4. Proceed to Claude's next interview step (extraction for Q1/Q2, reconciliation for Q3/Q4) using the scripted answer as the user turn.

After Q4, present the drafted YAML, validate it with `validate_spec.py`, and on
success proceed through `/lagrangian-builder`'s remaining steps — install SARAH
/ SPheno if missing, run `/sarah-build`, run `/spheno-build`, register the
model. Write the generated YAML to
`./demo_output/singlet-doublet/singlet_doublet_spec.yaml` so it is inspectable.
If it differs materially from the canonical reference at
`_shared/modelspec_v3/specs/singlet_doublet.yaml`, note the diff in the final
summary — the interview is new and still proving itself out across the three
benchmark models.

On diagnostic-checkpoint failure (`check_vertices.py`, `check_mass_matrix.py`,
`check_spectrum.py`), `/lagrangian-builder` retries per its own iteration loop
(see `interview.md` §"Iteration expectations"). Surface the retry — don't hide
it — but continue automatically. If the retry budget is exhausted, fail the
demo and dump the accumulated blockers; do **not** silently fall back to the
canonical reference YAML. Pass `--force` to the underlying `/sarah-build` only
if the user explicitly asks to rebuild from scratch.

**SARAH model name.** The Q4 answer names the neutral mixing eigenstates
`Chi1/Chi2/Chi3` and the charged ones `ChiM/ChiP`. `/sarah-build` registers the
SARAH model as `SingletDoublet`, matching the pre-existing cached build. A
playtest-variant suffix (e.g. `SingletDoublet_A`) would only take effect on a
cold rebuild; on the cached path `/sarah-build` sees the build as up-to-date and
the suffix is a no-op. **Do not append a playtest-variant suffix to the SARAH
model name unless explicitly instructed** — use `SingletDoublet` so the UFO and
SPheno binaries from a prior run are reused correctly.

**Completion:** validated YAML written to `./demo_output/…/singlet_doublet_spec.yaml`;
SARAH UFO + SPheno source emitted; model registered.

#### 4b. SPheno spectrum generation

SARAH emission and the initial SPheno compile were handled in 4a. Here, run
SPheno once at the canonical benchmark to produce
`SPheno.spc.singlet_doublet`, encoding the physical mass spectrum (m_chi1,
m_chi2, m_chi3, mixing angles) MadDM requires. SPheno is the default spectrum
backend for this model — the SARAH → SPheno path is verified end-to-end (commit
`1fb8ad8`) and gives RGE running, 1-loop mass corrections, and decay widths.

| MS  | MPsi | y   | θ | (yh1, yh2)     | Position            |
|-----|------|-----|---|----------------|---------------------|
| 150 | 500  | 1.0 | 0 | (1.000, 0.000) | single-Yukawa limit |

The blind spot `m_{χ₁} + MPsi · sin(2θ) = 0` (paper Eq. 8) is not crossed here;
the point illustrates the pipeline, not the dip. `eval/.../singlet_doublet.py::blind_spot_parameter`
can report the blind-spot distance for cross-check.

**Completion:** `SPheno.spc.singlet_doublet` written with a physical spectrum
(no negative/`NaN` masses).

#### 4c. MadDM: relic density

Drive `/maddm` for the single benchmark point with `observables = ["relic"]`
and `out_dir = ./demo_output/singlet-doublet/maddm_run/`, following the
two-phase SLHA-overlay pattern, the `--mode=maddm` requirement, the
`generate relic_density` rule, the Majorana note, the version-validation
warning, `parse_mass_by_pdg`, and the relic-parsing block — all in
[`references/maddm-invocation.md`](references/maddm-invocation.md).

Record the result to `./demo_output/singlet-doublet/relic.json` with `m_chi1`
parsed from the SLHA `Block MASS` (never hardcoded):

```json
{
  "m_chi1":     <parsed from SLHA Block MASS by DM PDG id>,
  "sin_2theta": 0.0,
  "omega_h2":   <value from MadDM>,
  "status":     "ok" | "failed",
  "benchmark":  {"MS": 150.0, "MPsi": 500.0, "yh1": 1.0, "yh2": 0.0},
  "slha_path":     "<abs path to SPheno.spc used as param_card>",
  "maddm_results": "<abs path to MadDM_results.txt>"
}
```

The Planck value is `Omega h^2 = 0.120 ± 0.001`; record whether the computed
`omega_h2` is within 3σ. The demo does not sit on the blind spot — this single
point illustrates the pipeline.

**Completion:** `relic.json` written with non-null `omega_h2`; channel fractions
pass the `[0.99, 1.01]` gate (see reference).

#### 4d. Plotting

The figure is a single-point diagnostic: an **annihilation-channel breakdown**
bar chart of the per-channel contributions MadDM emits in
`MadDM_results.txt`. A (m_χ, sin 2θ) scatter with one marker is not
informative; channel composition is.

Consult `/hep-plot`. The Profumo blind-spot paper is theory-only with no
experimental affiliation — use the analytic context from `styles/hep_ph_style.py`:

```python
from styles.hep_ph_style import set_hep_context, check_overlaps
import matplotlib.pyplot as plt

palette = set_hep_context("analytic")

channels = sorted(results["sigmav_channels"].items(),
                  key=lambda kv: kv[1], reverse=True)[:10]
labels   = [c for c, _ in channels]
percents = [p for _, p in channels]

fig, ax = plt.subplots(figsize=(85/25.4, 63.75/25.4))
ax.barh(labels, percents, color=palette["data"])
ax.invert_yaxis()
ax.set_xlabel(r"$\langle\sigma v\rangle$ contribution [%]")
ax.text(0.02, 0.98,
        r"Singlet-Doublet $\chi_1$" + f", m={m_chi1:.1f} GeV\n"
        r"$\Omega h^2 = $" + f"{results['Omegah2']:.3f}" + " (Planck 0.120)\n"
        "arXiv:2506.19062 Sec. II",
        transform=ax.transAxes, va="top", ha="left",
        fontsize=7, color=palette["deemph"])

issues = check_overlaps(fig)
assert not issues, f"Overlaps detected: {issues}"

fig.tight_layout()
fig.savefig("./demo_output/singlet-doublet/summary.pdf", bbox_inches="tight")
fig.savefig("./demo_output/singlet-doublet/summary.png", dpi=200, bbox_inches="tight")
```

Per HEP convention: analytic style via `set_hep_context("analytic")`; bars in
**black** via `palette["data"]` (per `feedback_data_point_color`); figure size
85mm × 63.75mm (single-column 4:3); no legend box; left + bottom axes only.

**Completion:** `summary.{pdf,png}` written; `check_overlaps` returns no issues.

#### 4e. Direct detection (READY, tree-only)

Drive `/maddm` a second time at the same canonical benchmark with
`observables = ["direct_detection"]` and
`out_dir = ./demo_output/singlet-doublet/maddm_run_dd/` (rmtree it first — MG5
`output` refuses to overwrite), following the same two-phase pattern plus the
direct-detection parsing block (nucleon-σ extraction, `scattering/v1` wrap,
`/ddcalc` dispatch) in
[`references/maddm-invocation.md`](references/maddm-invocation.md).

At θ=0 the blind spot `m_χ₁ + M_Ψ·sin(2θ) = 0` collapses to `m_χ₁ = 0`, so the
benchmark is far from the cancellation and tree σ_SI is non-zero. Loop-floor
enhancement near the blind spot is a v2 extension requiring the `/looptools
eval` runtime to bridge `/formcalc` to `/ddcalc`.

Record the result to `./demo_output/singlet-doublet/dd.json`:

```json
{
  "m_chi1":              <m_chi1>,
  "sin_2theta":          0.0,
  "blind_spot_distance": <m_chi1 + 500.0 * 0.0 = m_chi1; far from 0>,
  "sigma_si_proton_cm2":   <copied from scattering.json — non-null>,
  "sigma_si_neutron_cm2":  <copied from scattering.json — non-null>,
  "sigma_sd_proton_cm2":   <copied from scattering.json — non-null>,
  "sigma_sd_neutron_cm2":  <copied from scattering.json — non-null>,
  "ddcalc": <verbatim ddcalc_result/v1 JSON>,
  "regime":              "tree-only",
  "loop_floor_pending":  true,
  "status":              "ok" | "failed",
  "scattering_json":     "<abs path>",
  "maddm_results":       "<abs path to MadDM DD results>"
}
```

`regime: "tree-only"` and `loop_floor_pending: true` make the scope explicit;
downstream consumers know the loop contribution at the blind spot is not yet
included.

**Completion:** `dd.json` written with all four nucleon-σ fields non-null and a
`ddcalc` verdict block.

#### 4f. Indirect detection (COMING SOON)

Record as skipped in `summary.json`: blocked on the pull-computation skill
[future: dm-pull (v1+)]; `/gamlike [v0 — parser only]` provides parsed MadDM
output but does not compute likelihood pulls. A full ID constraint would feed
MadDM annihilation spectra to GamLike for gamma-ray and neutrino flux limits.

#### 4g. Write summary.json

After all READY constraints have run, write
`./demo_output/singlet-doublet/summary.json` conforming to
`plugins/hep-ph-toolkit/skills/singlet-doublet/summary.schema.json` (which
`$ref`s `_shared/summary.core.schema.json`). Create the directory first
(`mkdir -p ./demo_output/singlet-doublet/`), then write. Example for the default
READY subset (relic + DD):

```json
{
  "schema_version": "1",
  "model": "singlet-doublet",
  "run_at": "<ISO-8601 timestamp>",
  "ran": ["relic", "dd"],
  "dd_regime": "tree-only",
  "loop_floor_pending": true,
  "skipped_constraints": [
    {"id": "id", "reason": "blocked on pull-computation skill (v1+); /gamlike v0 parses MadDM output but does not compute likelihood pulls"}
  ],
  "artifacts_dir": "./demo_output/singlet-doublet/",
  "headline": "Relic + tree-DD at canonical benchmark (MS=150, MPsi=500, y=1, θ=0): Ω h² = <value>; σ_SI(p) = <value> cm² (tree-only; loop floor pending /looptools eval). ID skipped."
}
```

Adapt `ran`, `skipped_constraints`, and `headline` to what actually ran. On
`Cancel` at the Step 3 gate: do NOT write `summary.json` — `/demo`'s closing
block degrades to `"singlet-doublet interview was cancelled."`.

**Completion:** `summary.json` written and schema-valid, with `ran` and
`skipped_constraints` matching the executed subset.

## Acceptance criteria (sd-A-004)

Acceptance values for the canonical benchmark live in
`benchmarks/canonical-2026/expectations.json`. Plans MUST cite that fixture in
any gate that compares against `omega_h2`.

## Error paths

| Skill step | Error code | Trigger | Action |
|---|---|---|---|
| `/sarah-build` | `WOLFRAM_KERNEL_ABSENT` | `wolfram_engine_path` not set in config | Run `/install` to configure Wolfram Engine, then retry |
| `/sarah-build` | `SARAH_ABSENT` | `sarah_path` not set in config | Run `/install` to configure SARAH, then retry |
| `/sarah-build` | `MODELSPEC_INVALID` | v3 validator rejects `singlet_doublet.yaml` | Check `singlet_doublet.yaml` against `modelspec_v3/schema.json`; authoring error |
| `/sarah-build` | `ANOMALY_CANCELLATION_FAILED` | SARAH anomaly check fails | Inspect `context.coefficients` in the blocker JSON; singlet-doublet is anomaly-free, so this is a Lagrangian authoring error |
| `/sarah-build` | `SARAH_OUTPUT_MISSING` | UFO output absent after successful SARAH exit | Check `sarah.log` in `$STATE_ROOT/models/singlet_doublet/`; may indicate SARAH version mismatch |
| `/spheno-build` | SPheno compile error | Source compiles but spectrum is unphysical | Check SPheno log; parameter values may be outside physical range |
| MadDM launch | UFO import fails | `chi1` PDG id unknown to MadGraph | Confirm UFO was generated by the current `/sarah-build` run; run with `--force` if stale |
| MadDM launch | `Omega h^2` absent from output | MadDM run crashed or timed out | Check `singlet_doublet_maddm/Events/run_01/` for partial output; retry a single point first |
| Plotting | `styles.hep_ph_style` import error | `styles/` not on `PYTHONPATH` | Put the repo root on `PYTHONPATH` (the `styles/` package ships with hephaestus); `/hep-plot` §Style covers the analytic interface |

## File map

| File | Produced by | Contents |
|---|---|---|
| `$STATE_ROOT/models/singlet_doublet/sarah_output/UFO/singlet_doublet/` | `/sarah-build` | MadGraph UFO model files |
| `$STATE_ROOT/models/singlet_doublet/sarah_output/SPheno/singlet_doublet/` | `/sarah-build` | SPheno Fortran source |
| `$STATE_ROOT/models/singlet_doublet/SPheno.spc.singlet_doublet` | `/spheno-build` | Mass spectrum at the benchmark point |
| `./demo_output/singlet-doublet/relic.json` | Step 4c | `Omega h²` + channel breakdown |
| `./demo_output/singlet-doublet/summary.png` | Step 4d | Annihilation-channel bar chart |
| `./demo_output/singlet-doublet/maddm_run_dd/` | Step 4e | MadDM direct-detection session output |
| `./demo_output/singlet-doublet/maddm_run_dd/scattering.json` | Step 4e | `scattering/v1` JSON consumed by `/ddcalc` |
| `./demo_output/singlet-doublet/dd.json` | Step 4e | Tree σ_SI/σ_SD + DDCalc per-experiment verdict |
| `./demo_output/singlet-doublet/summary.json` | Step 4g | Per-model summary consumed by `/demo` closing block |

## Known limitations

Two confirmed playtest limitations bound where this pipeline has been proven —
reserved Mathematica symbol names in mixing matrices (sd-A-003) and the
unvalidated `/lagrangian-builder` interview at θ≠0 (sd-A-001). Neither blocks
the canonical θ=0 run. Full detail and the owed fixes are in
[`references/known-limitations.md`](references/known-limitations.md).
