---
name: demo
description: Constraint-first interactive front door to the Profumo blind-spot demo (arXiv:2506.19062). Presents a model picker (Singlet-Doublet, 2HDM+a, Dark SU(3)) and delegates to the chosen per-model skill. Invoke when the user says "run the demo", "show me HEPhaestus", "reproduce the blind spot", or on fresh-install evaluation.
---

# Demo

Thin front door to the Profumo blind-spot demo. Presents a paper intro, lets the
user pick a model, and hands off to the per-model skill (`/singlet-doublet`,
`/2hdm-a`, or `/dark-su3`). Each per-model skill owns its own constraint
interview, time-estimate gate, and execution chain.

This skill must never fall back to analytic Python for an observable. All physics
observables come from real tools driven by the per-model skills.

## Flow

### Step 0 — Preflight

Read `${XDG_CONFIG_HOME:-~/.config}/hephaestus/config.json`. Required keys:
`madgraph_path`, `sarah_path`, `spheno_path`, `wolfram_engine_path`.

For each key, confirm the executable responds (`--version` or equivalent no-op).
Build the missing-list: every required key absent from the config or whose
executable does not respond. If it is empty, continue to Step 1. Otherwise,
present an `AskUserQuestion` gate offering to install the missing tools. The
`pick_subset` option is included only when the missing-list has more than one
entry.

```json
{
  "question": "<N> of 4 tools needed for /demo are missing: <comma-separated missing-list>. Install them now in their default locations?",
  "options": [
    {"id": "install_now",  "label": "Install missing tools now", "description": "Hand off to /install and let it install the missing tools in their defaults. /demo resumes once install completes."},
    {"id": "pick_subset",  "label": "Let me pick which to install", "description": "Hand off to /install in interactive mode so you can choose. Re-run /demo afterwards."},
    {"id": "cancel",       "label": "Cancel — I'll run /install myself later", "description": "Stop /demo cleanly with no install attempt."}
  ],
  "allowMultiple": false,
  "required": true
}
```

Dispatch per answer:

- **`install_now`** — for each tool in the missing-list, invoke `/install --tool <tool>` (mapping `madgraph_path → mg5`, `sarah_path → sarah`, `spheno_path → spheno`, `wolfram_engine_path → wolfram`). After all installs return, re-read the config and re-probe the four keys. If the missing-list is now empty, continue to Step 1. Otherwise stop and print:

  > "Install finished but these tools are still missing/unresponsive: `<list>`. Inspect the install logs, then re-run `/demo`."

- **`pick_subset`** — invoke `/install` with no arguments (its bundle/per-tool picker takes over). Then stop and print:

  > "Pick the tools you need in `/install`, then re-run `/demo`."

- **`cancel`** — stop and print:

  > "The demo needs MadGraph, SARAH, SPheno, and Wolfram Engine configured. Missing or unresponsive: `<list>`. Run `/install` to set them up, then re-run `/demo`."

Do not probe common install paths from `/demo` itself. `/install` owns
installation; `/demo` only orchestrates the gate above.

**Completion:** all four keys present and responsive (continue to Step 1), or the
skill has stopped with one of the printed messages above.

### Step 1 — Paper introduction

Print verbatim:

> Arcadi & Profumo ask: *where can dark matter hide from direct detection?* They identify **blind spots** — regions of parameter space where the tree-level DM-nucleon coupling vanishes by cancellation, so the direct-detection signal is suppressed far below naive expectations. Blind spots matter because they weaken "direct detection rules out WIMPs" arguments: a model can evade current limits not by tuning the DM mass, but by tuning the couplings to a cancellation.
>
> This demo walks the full pipeline for one of three paper-benchmark models — Lagrangian → SARAH → SPheno → MadGraph/MadDM → a figure — with constraint selection (relic, direct, indirect) driving which sub-skills run. Some prereq skills (the multi-component DM combiner and ID pull-computation) are on the roadmap. For **2HDM+a** the loop-only direct-detection chain (FeynArts → FormCalc → `/looptools eval` → `/ddcalc`) is now wired end-to-end and yields a real, EW-anchor-validated σ_SI at one benchmark point (box not folded into f_N (≤1.7× upward), SI only; not an experimental exclusion; Tier-3 smoke gated off by default, green on a tooled box); for the other models the per-model loop-DD chain is not yet integrated end-to-end. Pending constraints will surface as `[COMING SOON]` and you can choose to run only the ready subset.

### Step 2 — Gate: continue?

`AskUserQuestion`:

```json
{
  "question": "Ready to begin?",
  "options": [
    {"id": "continue", "label": "Continue"},
    {"id": "not_now",  "label": "Not now"}
  ],
  "allowMultiple": false,
  "required": true
}
```

On `not_now`, stop cleanly with no output. On `continue`, proceed to Step 3.

### Step 3 — Model picker

`AskUserQuestion` with three model options:

```json
{
  "question": "Which model do you want to explore?",
  "options": [
    {"id": "singlet-doublet", "label": "Singlet-Doublet (~2–4 hr cold; relic + tree-DD READY, ID COMING SOON)", "description": "3×3 neutralino-like mixing, tree-level blind spot, loop floor. Relic READY via /maddm. Direct detection READY tree-only via MadDM `generate direct_detection` → /ddcalc 90%-CL exclusion (canonical θ=0 benchmark sits far off the blind-spot locus); loop floor near the blind spot coming soon with /looptools eval runtime. Indirect detection COMING SOON with pull computation (v1+)."},
    {"id": "2hdm-a", "label": "2HDM + a (~2–5 hr cold; relic + parser-only ID READY, DD READY-with-caveat)", "description": "Pseudoscalar mediator, CP-forbidden tree SI, loop-only DD. Relic READY via hand-crafted SARAH model (Ω h² ≈ 10.494 at off-resonance benchmark). Indirect detection READY-with-caveat: MadDM `generate indirect_detection` → /gamlike v0 emits ⟨σv⟩ + channels + Fermi-LAT likelihood rows; pull computation deferred to dm-pull v1+. DD READY-with-caveat: loop-only via /feynarts → /formcalc → /looptools eval → /ddcalc yields a real, EW-anchor-validated σ_SI=1.18e-48 cm² at one benchmark point (~40% vs an independent EW box+triangle anchor; box not folded into f_N (≤1.7× upward), SI only; not an experimental exclusion; Tier-3 smoke gated off by default, green on a tooled box). The live /sarah-build renderer UFO backport remains separate, non-blocking debt."},
    {"id": "dark-su3", "label": "Dark SU(3) (~1–3 hr cold, relic only; DD/ID coming soon or vacuous)", "description": "Higgsed SU(3)_D → SU(2)_D dark sector with two DM candidates. Relic READY via analytic-only branch in /dark-matter-constraints. V DD/ID: COMING SOON — MG5_DARK_COLOR_TENSOR_WALL walls MadGraph/MadDM and an analytic DD/ID escape hatch is on the roadmap. Psi DD: PHYSICS-VACUOUS — σ_SI ≈ 0 by exact parameter-independent symmetry (Eq. 29), so the constraint is trivially satisfied rather than tool-blocked. Psi ID: COMING SOON, same MG5 chain."}
  ],
  "allowMultiple": false,
  "required": true
}
```

> **Disclosure (dsu3-002):** dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets.

The cold-hour estimates are total overlap-adjusted estimates assuming all prereqs
were implemented; they are hard-coded from each per-model skill's `## Constraints`
table and `constraints.yaml`. The user sees which constraints are actually
blocked inside the per-model skill's Step 3.

### Delegation

Based on the user's choice, read and execute
`plugins/hep-ph-toolkit/skills/<singlet-doublet|2hdm-a|dark-su3>/SKILL.md`. The
per-model skill runs its own Steps 1–4 (candidate declaration → constraint
interview → time-estimate gate → execution). `/demo` does not intervene.

### Closing block

After the per-model skill returns, read `./demo_output/<model>/summary.json`
(`<model>` = the id chosen in Step 3). If it exists, print three lines:

```
Model run:    <summary.model>
Artifacts:    <summary.artifacts_dir>
Skipped:      <comma-separated list of summary.skipped_constraints[*].id> — <reason> (or "none")
```

If it does not exist (per-model skill exited via Cancel or errored before
writing), print:

```
<model> interview was cancelled.
```

## Non-goals

- `/demo` does not own constraint interview, time gates, or execution. These live in each per-model skill.
- `/demo` does not probe the marketplace for prereq availability at runtime. Prereq status is static — declared in `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml`.
- `/demo` does not implement multi-component DM combination. Dark SU(3) per-candidate relic runs through the analytic-only branch of `/dark-matter-constraints [EXISTS]`; paper-fidelity multi-component combination into `Ω_tot h² ≈ 0.12` is on the upgrade roadmap of `analytic_models.dark_su3` (per the `dsu3-002` regression-anchor banner in dark-su3 SKILL.md), not blocked on `/dark-matter-constraints` itself.
- `/demo` does not install tools. `/install` owns environment setup.
- No collider execution. The collider option in per-model Step 2 is a placeholder only.
- Per-model skills are scoped to Profumo arXiv:2506.19062 benchmark ranges in this iteration.
