# Profumo Demo Workflow Redesign

**Date:** 2026-04-19
**Status:** Approved design
**Scope:** Rewrite `/demo` and introduce three per-model workflow skills inside `plugins/hep-ph-demo/`, organized around constraint selection rather than figure reproduction.

## Motivation

The current `/demo` skill (at `plugins/hep-ph-toolkit/skills/demo/SKILL.md`) is figure-first: it interviews the user for one of the three models in Arcadi & Profumo (arXiv:2506.19062) and then one of three figures, and reproduces the chosen figure end-to-end. This framing is rigid and hides the underlying capability.

The redesign pivots to a constraint-first framing:

- The user picks a model and a set of constraints they want computed (relic density, direct detection, indirect detection; collider listed but not yet implemented).
- The per-model skill assembles the necessary prerequisite skill chain for those constraints, shows a time estimate, gates for confirmation, then runs.

This framing makes the real workflows tailored per-user (a user interested in only DD doesn't pay for relic), matches the way HEP phenomenologists actually think about model constraints, and positions the model skills to grow beyond one paper when Claude becomes capable of composing skills autonomously.

## Deliverables

Four new or rewritten SKILL.md files inside `plugins/hep-ph-toolkit/skills/`:

| Path | Kind | Purpose |
|------|------|---------|
| `demo/SKILL.md` | Rewrite | Thin front door: intro + model picker + delegation |
| `singlet-doublet/SKILL.md` | New | Interactive orchestrator for the Singlet-Doublet fermion model |
| `2hdm-a/SKILL.md` | New | Interactive orchestrator for the 2HDM + pseudoscalar mediator model |
| `dark-su3/SKILL.md` | New | Interactive orchestrator for the Dark SU(3) model (two DM candidates) |

No new plugin is created. Per-model skill names are paper-agnostic; the SKILL.md description calls out that they are currently scoped to Profumo 2506.19062 benchmarks.

## `/demo` behavior

`/demo` is a thin front door whose only responsibility is model selection and delegation.

1. Print a short intro (1–2 paragraphs) explaining the paper and the concept of "blind spots" in DM direct detection.
2. Gate: `AskUserQuestion` with options `Continue` / `Not now`. On `Not now`, exit cleanly.
3. `AskUserQuestion` with three model options, each annotated with a one-line physics hook and a combined "all constraints, cold run" time estimate:
   - `Singlet-Doublet (~3–5 hr)` — 3×3 neutralino-like mixing, tree-level blind spot, loop floor.
   - `2HDM+a (~5–9 hr)` — pseudoscalar mediator, CP-forbidden tree SI, loop-only DD.
   - `Dark SU(3) (~6–12 hr)` — confining dark sector, two DM candidates with exact parameter-independent blind spot.
4. Invoke the chosen per-model skill. Pass no arguments; the per-model skill owns its own interview.
5. On the per-model skill's return, print a short closing message (what ran, where artifacts landed, how to iterate on the parameter scan).

`/demo` does **not** own constraint interview, time gates, or execution.

## Per-model skill behavior

Each of `singlet-doublet`, `2hdm-a`, `dark-su3` runs the same four-step interactive flow. The shared structure keeps the interview logic consistent; per-skill differences live in static metadata (DM candidates, time-estimate table, prereq chain specifics).

### Step 1 — Declare DM candidates (metadata)

Each SKILL.md has a metadata block near the top listing the model's DM candidates. Example:

```yaml
dm_candidates:
  - name: chi1
    spin: 1/2
    notes: Lightest mass eigenstate of the singlet-doublet mixing matrix
```

For Dark SU(3):

```yaml
dm_candidates:
  - name: phi
    spin: 0
    notes: Scalar dark pion; exact blind spot in SI scattering
  - name: V
    spin: 1
    notes: Vector dark meson; tree-level SI plus resonance region
```

This metadata is read by constraint prereq chains (see Multi-component DM below) to know how many channels to sum over.

### Step 2 — Constraint interview

`AskUserQuestion` with multi-select options:

- `Relic density`
- `Direct detection`
- `Indirect detection`
- `Collider (coming soon — skipped)`

At least one must be selected. Selecting `Collider` is allowed but has no execution effect; it adds a note to the final summary saying collider constraints are planned for a future release.

### Step 3 — Time estimate, prereq check, and gate

Print a table derived from the SKILL.md's static time-estimate metadata, showing for each selected constraint:

- The prereq skill chain that will be invoked (in order), with each skill annotated `[EXISTS]` or `[PLANNED]`.
- Cold-run and cached-run time ranges.

Print a combined total at the bottom (overlap-adjusted: shared prereqs like `/sarah-build` are counted once).

If any selected constraint's chain contains a `[PLANNED]` prereq that is not yet implemented in the marketplace, mark that constraint as blocked and list the missing skills. The user chooses how to proceed:

- `Run available` → drop blocked constraints, run the rest. Final summary notes what was skipped and why.
- `Back` → return to Step 2 to re-select constraints.
- `Cancel` → exit cleanly.

If no constraints are blocked, the gate offers `Run it` / `Back` / `Cancel` with the same semantics (`Run it` proceeds to Step 4).

### Step 4 — Execute the chain

For each selected constraint, invoke the prereq sibling skills in order. On completion, generate a combined summary figure using `/hep-plotting` that overlays all computed constraints on the model's natural parameter plane.

## Multi-component DM handling

Multi-component DM is treated as a **constraint-level** concern, not a per-model branch.

- Each per-model skill declares its `dm_candidates` list in metadata.
- Per-candidate computations are performed by the standard single-candidate skills (`/maddm`, `/ddcalc`, `/gamlike`, etc.), invoked once per candidate. These skills remain single-candidate; they are not modified to know about multi-component DM.
- A thin post-processing step — owned by the per-model skill's Step 4 execution — reads the per-candidate outputs and combines them:
  - **Relic:** Ω_total h² = Σᵢ Ωᵢ h², with population weights fᵢ = Ωᵢ / Ω_total derived from the per-candidate relics.
  - **DD:** likelihoods use recoil rates weighted by fᵢ.
  - **ID:** annihilation spectra and fluxes weighted by fᵢ² (since rate ∝ n² ∝ fᵢ²).
- Singlet-Doublet and 2HDM+a declare one candidate each; the post-processing is a trivial pass-through. Dark SU(3) declares two candidates; the post-processing does the weighted combination.

The per-model skills contain no model-specific multi-component logic. They only enumerate candidates and apply a generic weighted-combination post-process; the combination rules are per-constraint, not per-model.

## Time-estimate tables

Each per-model SKILL.md embeds a static time-estimate table, keyed by constraint, with columns `cold` and `cached`. Example shape (values illustrative, to be finalized during implementation):

| Constraint | Cold | Cached |
|------------|------|--------|
| Relic density | 1–2 hr | 20–40 min |
| Direct detection | 2–4 hr | 30–60 min |
| Indirect detection | 1–3 hr | 20–40 min |

Step 3 of the per-model skill flow reads this table, filters to selected constraints, adds overlap-adjusted totals, and presents to the user. `/demo`'s model picker reads the `all-constraints cold` total from each SKILL.md to produce the per-model one-line estimates.

## Collider handling

Listed in the Step 2 multi-select as `Collider (coming soon — skipped)`. If selected:

- Does not trigger any execution.
- Adds a one-line note to the final summary output: `Collider constraints are not yet implemented; planned for future release.`
- Does not block other selections.

Rationale: the user has explicitly scoped collider constraints out of this iteration but wants the option visible so users understand it is a known gap, not an oversight.

## Presentation affordances

Two places in the flow are candidates for richer presentation (ASCII tables, bordered boxes, color) if a future iteration decides a nicer UX is warranted:

1. The per-model skill's Step 3 time-estimate table.
2. `/demo`'s Step 3 model-picker.

The design keeps interview logic separable from output formatting so presentation upgrades are content-only changes to those two spots.

## Prereq skill chains (reference)

These chains are informative for the spec. Exact mappings are finalized during implementation and live in each per-model SKILL.md.

Prereqs marked `[EXISTS]` are present in the marketplace today; prereqs marked `[PLANNED]` are on the DM-tool roadmap (see the project memory `project_dm_tool_roles.md`) but not yet implemented. A constraint whose chain contains any `[PLANNED]` skill cannot actually execute in this iteration; the per-model skill must surface this gracefully (Step 3 prints the missing prereqs and offers to skip that constraint, rather than failing mid-execution).

**Relic density** — all prereqs exist.
- `/sarah-build` [EXISTS] → `/spheno-build` [EXISTS] → `/madgraph` [EXISTS] → `/maddm` [EXISTS] → per-model post-process (multi-component combination)

**Direct detection** — `/feynarts`, `/formcalc`, `/package-x` are on the DM-tool roadmap.
- `/sarah-build` [EXISTS] → `/spheno-build` [EXISTS] → `/madgraph` [EXISTS] (tree σ_SI) → `/feynarts` [PLANNED] → `/formcalc` [PLANNED] → `/package-x` + LoopTools [PLANNED] → `/ddcalc` [PLANNED] → per-model post-process
- The loop subchain is required for Singlet-Doublet and Dark SU(3) scalar; it is the primary signal for 2HDM+a (tree ≈ 0 by CP) and Dark SU(3) scalar (exact blind spot). Tree-only DD via `/madgraph` is available today for the vector Dark SU(3) candidate and the tree regions of Singlet-Doublet.

**Indirect detection** — `/gamlike` and `/nulike` are on the DM-tool roadmap.
- `/sarah-build` [EXISTS] → `/spheno-build` [EXISTS] → `/madgraph` [EXISTS] → `/maddm` [EXISTS] (annihilation spectra, Pythia showering) → `/gamlike` [PLANNED] and/or `/nulike` [PLANNED] → per-model post-process

**Collider**
- Not implemented in this iteration. Multi-select option is a placeholder; execution is a no-op with an informational note.

## Migration of existing `/demo`

The existing `demo/SKILL.md` is rewritten in place. No file rename. Git preserves the prior figure-reproduction logic in history. Content from the old skill that corresponds to specific figure reproductions migrates into the per-model skills' `all constraints` output path, since running all constraints on a model produces a superset of the information in the paper's figures.

The `install/` skill inside `plugins/hep-ph-demo/` is unchanged.

## Non-goals

- No new plugin. All four skills live in `plugins/hep-ph-demo/`.
- No change to the preflight / install flow. The existing `install/` skill still owns environment setup.
- No attempt to make per-model skills reusable beyond the Profumo benchmark ranges in this iteration. The SKILL.md description calls out the paper-scoped nature; broadening is deferred to a later iteration.
- No autonomous skill composition. `/demo` remains the opinionated pedagogical front door until Claude is capable of composing the underlying skills without it.
- No collider implementation. Placeholder only.
- No change to `.claude-plugin/marketplace.json` — the `hep-ph-demo` plugin entry already exists.
