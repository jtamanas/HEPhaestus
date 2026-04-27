# Proposal 01 — Profumo Demo Workflow Implementation

**Role:** Proposer (brainstorming triad)
**Spec:** `docs/superpowers/specs/2026-04-19-profumo-demo-workflow-design.md`
**Deliverable set:** four SKILL.md files under `plugins/hep-ph-toolkit/skills/`

This proposal is deliberately opinionated. It picks the boring, repo-consistent
option on every split unless there is a clear physics or maintainability reason
to do otherwise. Where the spec is silent, I pick and name the pick.

---

## 1. File layout

```
plugins/hep-ph-toolkit/skills/
├── demo/
│   ├── SKILL.md                          # REWRITTEN — thin front door
│   └── scripts/
│       └── read_model_meta.py            # reads YAML frontmatter of sibling skills
├── singlet-doublet/
│   ├── SKILL.md                          # NEW
│   └── scripts/
│       └── run_chain.py                  # per-model dispatcher (thin wrapper)
├── 2hdm-a/
│   ├── SKILL.md                          # NEW
│   └── scripts/
│       └── run_chain.py
├── dark-su3/
│   ├── SKILL.md                          # NEW
│   └── scripts/
│       └── run_chain.py
└── _shared/                              # NEW shared directory (convention cf. plugins/hep-ph-toolkit/skills/_shared/)
    ├── constraints.yaml                  # master table: constraint -> prereq chain + time estimates + status
    ├── time_budget.py                    # overlap-adjusted total estimator; keyed by constraint ids
    ├── combine_multi_dm.py               # weighted-combination post-processor (Ω/DD/ID) over N candidates
    ├── prereq_probe.py                   # runtime [EXISTS]/[PLANNED] probe against marketplace
    └── model_meta_schema.json            # JSON schema for per-model frontmatter extensions
```

**Justification per file:**

- `_shared/` mirrors the existing convention at `plugins/hep-ph-toolkit/skills/_shared/` (schema files, name canonicalizer). This is the obvious spot for cross-skill assets that are scoped to the `hep-ph-demo` plugin.
- `_shared/constraints.yaml` is the single source of truth for prereq chains and cold/cached time estimates. The per-model SKILL.md references this file and overrides only those cells where per-model timings differ (e.g., 2HDM+a loop DD is slower than Singlet-Doublet loop DD). DRY by construction.
- `_shared/time_budget.py` is a pure function: `(selected_constraints, per_model_overrides) -> (table, total_cold, total_cached)`. Overlap adjustment (shared prereqs counted once) lives here.
- `_shared/combine_multi_dm.py` owns **all** multi-component DM math (Ω_tot, f_i weights, DD f-weight, ID f²-weight). The per-model SKILL.md knows only that Step 4 ends with `python3 ../_shared/combine_multi_dm.py --model <name>`. No per-model physics logic in the script.
- `_shared/prereq_probe.py` answers "does `/ddcalc` exist in the active marketplace right now?" by reading `.claude-plugin/marketplace.json` and the filesystem. This lets us move skills from `[PLANNED]` to `[EXISTS]` simply by adding them to the marketplace — no edits to the per-model SKILL.md required.
- `scripts/run_chain.py` per model is a ~30-line dispatcher that reads `_shared/constraints.yaml`, filters to the user's selected constraints, and emits an ordered list of `(skill_name, args)` for Claude to execute. It does **not** itself invoke Claude skills (Claude reads its stdout and dispatches). This keeps the "skills drive tools, not Python drives skills" invariant intact.
- `demo/scripts/read_model_meta.py` is the mirror: reads frontmatter from each sibling per-model SKILL.md to populate `/demo`'s one-line model picker. Keeps `/demo` terse.

No new plugin, no marketplace change, no `install/` change. Consistent with the non-goals.

---

## 2. SKILL.md structure

### Shared section ordering (all four files)

```
---
name: <skill-name>
description: <one-line, per-spec conventions>
---

# <Title>

<1–3 sentence framing: model physics, paper anchor, what this skill does>

## When to invoke
<bulleted triggers>

## Model metadata
<YAML fenced block: dm_candidates, scope, reference>

## Constraints and time estimates
<markdown table, per-constraint>

## Flow
<Steps 1–4, terse>

## Error paths
<table>

## File map
<table>
```

This is identical ordering across all three per-model SKILL.md files and matches the repo's existing `sarah-build`/`lagrangian-builder` shape.

### Frontmatter

Per repo convention, only `name` and `description` live in the top `---` block (see every existing SKILL.md: all use just those two keys except `lagrangian-builder` which adds `allowed-tools`). Structured model metadata goes in a **second** fenced YAML block under a `## Model metadata` heading — this is the pattern SARAH skills already use for their schema examples and it stays parseable.

### `dm_candidates` and time-estimate embedding

**`dm_candidates`:** embedded as a fenced YAML block under `## Model metadata`. Example for `dark-su3/SKILL.md`:

````markdown
## Model metadata

```yaml
scope:
  paper: arXiv:2506.19062
  section: IV
  benchmark: "Table 3, rows 1-4"
dm_candidates:
  - name: phi
    spin: 0
    notes: Scalar dark pion; exact parameter-independent blind spot in SI
  - name: V
    spin: 1
    notes: Vector dark meson; tree SI + resonance region (Fig. 8)
combination_rules:
  relic: sum        # Ω_tot = Σ Ω_i
  dd: linear        # σ_eff = Σ f_i σ_i
  id: quadratic     # flux ∝ Σ f_i^2 <σv>_i
```
````

`combination_rules` is declarative per-constraint — the scalar `dark-su3` candidate could in principle have a different rule than the vector if future physics required it. Today all three models pick the same three values, but keeping it explicit means `combine_multi_dm.py` is a pure lookup table with zero `if model == "dark_su3"` branches.

**Time-estimate table:** a plain markdown table under `## Constraints and time estimates`. The table is authoritative for display purposes; the machine-readable twin is `_shared/constraints.yaml`. Keeping both is a small duplication tax I'll pay because (a) a human maintainer scanning SKILL.md wants to see the numbers, (b) `_shared/constraints.yaml` is what the scripts consume, and (c) a CI test will assert they agree.

Example, `singlet-doublet/SKILL.md`:

```markdown
## Constraints and time estimates

| Constraint          | Prereq chain                                                                                     | Cold    | Cached     |
|---------------------|--------------------------------------------------------------------------------------------------|---------|------------|
| Relic density       | `/sarah-build` → `/spheno-build` → `/madgraph` → `/maddm`                                        | 1–2 hr  | 20–40 min  |
| Direct detection    | `/sarah-build` → `/spheno-build` → `/madgraph` → `/feynarts`*→`/formcalc`*→`/package-x`*→`/ddcalc`* | 2–4 hr  | 30–60 min  |
| Indirect detection  | `/sarah-build` → `/spheno-build` → `/madgraph` → `/maddm` → `/gamlike`*                          | 1–3 hr  | 20–40 min  |
| Collider            | — (placeholder)                                                                                  | n/a     | n/a        |

Prereqs marked `*` are `[PLANNED]`; see `../_shared/constraints.yaml` for authoritative status.
All-constraints cold total (overlap-adjusted): **3–5 hr**.
```

The "all-constraints cold total" line at the bottom is exactly the string `/demo` reads to populate its model-picker one-liners.

### Shared 4-step flow without duplication bloat

Option chosen: **explicit copy with narrow diffs**. Each SKILL.md spells out its four steps. The only per-model differences are (a) the Step 1 wording, which references that model's `dm_candidates` by name, (b) the Step 3 time numbers, which are the model's own numbers, (c) the Step 4 dispatch ordering (same for all, but the skill prints the ordered chain verbatim so the user sees it), and (d) the final plot channel names.

Why not an include / transclude mechanism? Claude Code's SKILL.md format has no transclusion primitive. Pretending otherwise by putting `{{ include shared_flow.md }}` would require a build step the repo doesn't have. Three ~180-line SKILL.md files with ~85% text overlap is the right trade: they stay human-readable and greppable, and the only shared logic that actually matters (prereq probing, time-budget math, multi-DM combining) is already factored to `_shared/`.

A CI test (W2 of the implementation workstream below) asserts the three SKILL.md files have identical Step 2 / Step 3 / Step 4 **structure** (same AskUserQuestion option sets, same dispatch order) by parsing the markdown — this prevents drift without forcing a templating layer.

---

## 3. Shared logic placement

Three pieces of shared logic, three principled homes:

| Logic | Home | Why |
|---|---|---|
| Multi-component DM combination | `_shared/combine_multi_dm.py` (script) | It is pure post-processing math on `maddm.json` / `ddcalc.json` outputs. No tool-driving. Not per-model physics. Lives once. |
| Time-budget / overlap-adjusted totals | `_shared/time_budget.py` (script) | Purely structural; reads `constraints.yaml`; zero physics. One test covers all three models. |
| Prereq `[EXISTS]`/`[PLANNED]` resolution | `_shared/prereq_probe.py` (script) | Marketplace state is a cross-cutting concern; per-SKILL.md declarations would drift. Probe is the source of truth. |

**Key design call:** `combine_multi_dm.py` is a script, not a Python library imported by other scripts, because nothing else imports it. It has one CLI:

```
python3 _shared/combine_multi_dm.py \
    --model dark-su3 \
    --candidate-outputs ./run/phi_maddm.json ./run/V_maddm.json \
    --constraint relic    # or dd, id
  → writes ./run/combined_<constraint>.json and prints headline
```

The per-model skill's Step 4 reads `dm_candidates` from its own metadata, runs the single-candidate skills N times (once per candidate), then invokes `combine_multi_dm.py` per-constraint. For Singlet-Doublet and 2HDM+a (N=1), the combiner is a pass-through that does nothing but rename the file — kept uniform so there's one code path.

This matches the "skills drive tools, not Python reimplements physics" rule because the combiner is not computing an observable — it is weighting outputs that MadDM / DDCalc already computed. This is algebra, explicitly carved out in `feedback_augment_not_replace.md` (valve c: symbolic identity / sum-rule / round-trip verification is exempt).

---

## 4. Interview flow, concretely scripted

Below is the verbatim flow for a per-model skill. The text in quote blocks is
the actual prompt the skill must print. `AskUserQuestion` call signatures are
given as JSON for specificity.

### Step 1 — Declare DM candidates

No user prompt. The skill prints (derived from its own `dm_candidates` metadata):

> For **Singlet-Doublet**, the DM candidate is:
>   - `chi1` — Majorana fermion, lightest eigenstate of the singlet-doublet mixing.
>
> This is a single-candidate model; relic, DD, and ID rates are computed directly for `chi1`.

For Dark SU(3), the same block lists two candidates and adds:

> Multi-component: per-candidate observables are combined with relic-weighted fractions f_i = Ω_i / Ω_tot. DD rates combine linearly in f_i; ID rates combine in f_i².

No AskUserQuestion here. The user sees this before Step 2 so the constraint multi-select is informed.

### Step 2 — Constraint multi-select

One `AskUserQuestion` call, `allowMultiple=true`:

```json
{
  "question": "Which constraints do you want computed for this model?",
  "options": [
    {"id": "relic",    "label": "Relic density",            "description": "Ω h² via MadDM"},
    {"id": "dd",       "label": "Direct detection",         "description": "σ_SI (tree+loop) via MadGraph + FormCalc + DDCalc"},
    {"id": "id",       "label": "Indirect detection",       "description": "Annihilation spectra via MadDM → GamLike/NuLike"},
    {"id": "collider", "label": "Collider (coming soon)",   "description": "Placeholder — execution is a no-op"}
  ],
  "allowMultiple": true,
  "required": true
}
```

Validation: at least one of `relic`, `dd`, `id`, `collider` must be present. If only `collider` is picked, skill prints "Collider is a placeholder in this iteration; nothing would run. Please also select relic, DD, or ID." and re-asks.

### Step 3 — Time estimate + prereq probe + gate

Skill runs:

```bash
python3 ../_shared/prereq_probe.py --constraints relic dd id
python3 ../_shared/time_budget.py --model singlet-doublet --constraints relic dd id
```

Prints a formatted block:

```
Planned chain for Singlet-Doublet:

  Relic density       [READY]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
    cold: 1–2 hr   cached: 20–40 min

  Direct detection    [BLOCKED — missing /feynarts, /formcalc, /package-x, /ddcalc]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS]
      → /feynarts [PLANNED] → /formcalc [PLANNED] → /package-x [PLANNED] → /ddcalc [PLANNED]
    cold: 2–4 hr   cached: 30–60 min

  Indirect detection  [BLOCKED — missing /gamlike]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS] → /gamlike [PLANNED]
    cold: 1–3 hr   cached: 20–40 min

Overlap-adjusted totals (shared prereqs counted once):
  selected + ready: cold ~1–2 hr,  cached ~20–40 min
  selected total  : cold ~3–5 hr,  cached ~50–100 min   (if all prereqs existed)
```

Then one `AskUserQuestion`, branching:

**If any selected constraint is BLOCKED:**
```json
{
  "question": "Some selected constraints have unimplemented prereqs. How to proceed?",
  "options": [
    {"id": "run_ready",   "label": "Run available (drop blocked)", "description": "Run relic; skip DD and ID with a note"},
    {"id": "back",        "label": "Back",                          "description": "Re-select constraints"},
    {"id": "cancel",      "label": "Cancel",                        "description": "Exit cleanly"}
  ],
  "allowMultiple": false, "required": true
}
```

**If all selected constraints are READY:**
```json
{
  "question": "Run it? Total cold-run estimate: 1–2 hr.",
  "options": [
    {"id": "go",     "label": "Run it",  "description": "Execute the chain"},
    {"id": "back",   "label": "Back",    "description": "Re-select constraints"},
    {"id": "cancel", "label": "Cancel",  "description": "Exit cleanly"}
  ],
  "allowMultiple": false, "required": true
}
```

Outcomes:
- `run_ready` → proceed to Step 4 with filtered constraint list, record `skipped=[dd, id]` for the final summary.
- `go` → proceed to Step 4.
- `back` → jump back to Step 2.
- `cancel` → exit cleanly with a one-line "Cancelled." message.

### Step 4 — Execute

The skill runs, for each candidate in `dm_candidates` and each ready constraint, the skill chain **in order**. For Singlet-Doublet (1 candidate, relic only — the common case given current `[PLANNED]` state):

```
1. /sarah-build plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml
2. /spheno-build singlet_doublet
3. /madgraph use singlet_doublet           # generates process cards for chi1 chi1 > SM SM
4. /maddm --model singlet_doublet --candidate chi1 --observables relic
5. python3 ../_shared/combine_multi_dm.py --model singlet-doublet --constraint relic \
       --candidate-outputs ./run/chi1_maddm.json
```

For Dark SU(3), steps 3–5 run **twice** (once per candidate `phi`, `V`) and step 5 (`combine_multi_dm.py`) runs with both candidate outputs.

Claude invokes each sub-skill through the Skill tool (same convention as `/lagrangian-builder` invoking `/sarah-install`, `/sarah-build`, `/spheno-install`, `/spheno-build`). Script wrappers under `scripts/run_chain.py` are used only to produce the *ordered list* of invocations; they never call Claude.

**Combined summary figure handoff to `/hep-plotting`:** after all constraints finish and `combine_multi_dm.py` has run for each selected constraint, the skill invokes:

```
/hep-plotting theory-data-comparison \
    --inputs ./run/combined_relic.json ./run/combined_dd.json ./run/combined_id.json \
    --model-name singlet-doublet \
    --axes "m_chi vs sin(2θ)"       # per-model choice, declared in model metadata
    --output ./demo_output/singlet-doublet/summary.png
```

The per-model skill declares its "natural parameter plane" as a `plot_axes` field under `## Model metadata`:

```yaml
plot_axes:
  x: {symbol: "m_chi", range: [100, 1500], units: GeV, scale: linear}
  y: {symbol: "sin_2theta", range: [-1, 1], scale: linear}
```

That block lives in the SKILL.md frontmatter (second YAML block) so `/hep-plotting` doesn't need any per-model knowledge — it just reads the fields.

Step 4 ends with:
- Print the figure path.
- Print a one-line headline derived from `combine_multi_dm.py`'s stdout (e.g., "σ_SI suppressed by 3.4 orders of magnitude at sin(2θ) = -0.31; Ω h² = 0.12 at m_χ = 380 GeV").
- Print the list of skipped constraints with reasons (if any).
- Return to `/demo`.

---

## 5. Prereq chain encoding

**Declarative source:** `_shared/constraints.yaml`. Example:

```yaml
constraints:
  relic:
    chain:
      - sarah-build
      - spheno-build
      - madgraph
      - maddm
    default_time:
      cold: [1, 2]       # hours
      cached: [0.33, 0.67]
  dd:
    chain:
      - sarah-build
      - spheno-build
      - madgraph
      - feynarts
      - formcalc
      - package-x
      - ddcalc
    default_time:
      cold: [2, 4]
      cached: [0.5, 1.0]
  id:
    chain:
      - sarah-build
      - spheno-build
      - madgraph
      - maddm
      - gamlike
    default_time:
      cold: [1, 3]
      cached: [0.33, 0.67]
  collider:
    chain: []
    placeholder: true

per_model_overrides:
  2hdm-a:
    dd:
      cold: [3, 6]    # loop-only DD is slower for 2HDM+a
  dark-su3:
    relic:
      cold: [1.5, 3]  # two candidates → two MadDM passes
    dd:
      cold: [3, 5]
    id:
      cold: [1.5, 4]
```

**Runtime `[EXISTS]`/`[PLANNED]` probe:** `_shared/prereq_probe.py` walks the chain and checks each entry against the marketplace. Resolution strategy, in order:

1. Look up `<skill-name>` in `.claude-plugin/marketplace.json` (all plugins + their `skills[]`).
2. If not listed, look on the filesystem: `plugins/*/skills/<skill-name>/SKILL.md` existence.
3. If neither, return `{status: "PLANNED"}` and append to the skill's user-facing block list.

The probe emits:

```json
{
  "constraints": {
    "relic": {"status": "READY", "chain": [{"name": "sarah-build", "status": "EXISTS"}, ...]},
    "dd":    {"status": "BLOCKED", "missing": ["feynarts", "formcalc", "package-x", "ddcalc"], "chain": [...]},
    ...
  }
}
```

Step 3's block/skip logic: `BLOCKED` constraints are dropped from Step 4's execution list only if the user picks `Run available`. Otherwise the gate returns the user to Step 2 or cancels. Nothing silently falls back — **this is the `feedback_augment_not_replace.md` invariant in code**.

Why not static declaration in each SKILL.md? Because the marketplace grows. When `/ddcalc` lands in the marketplace three weeks from now, we want Step 3 to say `[EXISTS]` on the next run without anyone editing any SKILL.md. Static declarations would rot.

---

## 6. `/demo` delegation

### Invocation of the per-model skill

`/demo` invokes the per-model skill via the **Skill tool** with the skill name `singlet-doublet` / `2hdm-a` / `dark-su3`. Per repo convention (see `/lagrangian-builder` calling `/sarah-install`), this is just `Skill(skill="<name>", args="")`. No path-based invocation. No arguments — the per-model skill owns its own interview per spec §/demo behavior point 4.

### Reading all-constraints cold totals for the model-picker

`/demo` runs `demo/scripts/read_model_meta.py` once at startup. That script:

1. Globs `plugins/hep-ph-toolkit/skills/*/SKILL.md` (excluding `demo/` and `install/`).
2. Parses frontmatter + the `## Model metadata` YAML block.
3. Parses the "All-constraints cold total" line from `## Constraints and time estimates`.
4. Emits one JSON line per model:

```json
{"name": "singlet-doublet", "title": "Singlet-Doublet", "hook": "3×3 neutralino-like mixing, tree-level blind spot, loop floor", "cold_total": "3–5 hr"}
```

`/demo`'s Step 3 `AskUserQuestion` consumes this JSON to produce the three option strings. No re-implementation of the time table.

The `title` and `hook` fields come from two new per-model metadata entries:

```yaml
display:
  title: "Singlet-Doublet"
  hook: "3×3 neutralino-like mixing, tree-level blind spot, loop floor"
```

These are the single-responsibility place for the model's one-liner, so `/demo`'s picker is a dumb renderer.

---

## 7. Workstream decomposition

Split into six workstreams. **Shared-scaffolding-first-then-per-skill** (not fully parallel) because the per-model SKILL.md files all reference `_shared/*`. Attempting to build them in parallel would force each stream to stub the shared pieces and guarantee drift.

| Workstream | Owner-agent | Deliverables | Depends on |
|---|---|---|---|
| **WS1: `_shared/` scaffolding** | one agent | `constraints.yaml`, `time_budget.py`, `prereq_probe.py`, `combine_multi_dm.py`, `model_meta_schema.json`, tests for each | — |
| **WS2: `demo/` rewrite** | one agent | `demo/SKILL.md`, `demo/scripts/read_model_meta.py`, tests | WS1 (for meta schema) |
| **WS3: `singlet-doublet/`** | agent | SKILL.md, `scripts/run_chain.py`, model metadata YAML, golden fixtures | WS1 |
| **WS4: `2hdm-a/`** | agent | same shape as WS3 | WS1 |
| **WS5: `dark-su3/`** | agent | same shape + multi-DM tests exercising `combine_multi_dm.py` with N=2 | WS1 |
| **WS6: Cross-cutting tests + docs** | agent | parser CI test (SKILL.md ↔ constraints.yaml agreement), integration test: `/demo` → each per-model skill → blocked-DD branch → clean exit | WS2–WS5 |

**Critical path:** WS1 → (WS2, WS3, WS4, WS5 in parallel) → WS6. WS1 is ~1 day; WS2–WS5 are ~1 day each; WS6 is ~0.5 day. Total wall time with one agent per stream: ~2.5 days.

**Dispatchable-to-parallel-agents check:** WS2–WS5 are truly independent once WS1 is done. They touch disjoint directories and reference WS1 via stable APIs (`constraints.yaml` schema, CLI of each `_shared/*.py`). Good candidates for `superpowers:dispatching-parallel-agents`.

**Smoke test per WS:** each WS's tests must include a "skill loads and Step 2 renders" dry run using the AskUserQuestion mocking pattern used in `superpowers:writing-skills`. WS6 adds an end-to-end dry run against a mocked marketplace where `/ddcalc` is present → DD should resolve `READY`.

---

## 8. Risks and open questions

These are the spec-silent choices I made above that a skeptic should push on:

1. **SKILL.md duplication vs. templating.** I chose explicit-copy across three per-model SKILL.md files. If the reviewer considers ~150 lines × 3 with ~85% overlap unacceptable, alternatives are (a) generate the three files from a Jinja template at build time (adds a build step the repo doesn't have), or (b) have each per-model SKILL.md be ~40 lines that just references `_shared/flow.md` and lists its own metadata (Claude would read `_shared/flow.md` as part of the skill context, but this breaks the "terse self-contained SKILL.md" user preference). I think explicit-copy is right but this is the most contestable call.

2. **`combine_multi_dm.py` as script not library.** If a future per-model skill wants to call it mid-flow with custom weights (e.g., for a non-trivial galactic-halo model with spatially-varying f_i), a script-only interface is awkward. Counter: that use-case doesn't exist and YAGNI.

3. **`prereq_probe.py` reading `marketplace.json` directly.** Tightly couples the skill to marketplace file layout. If that format changes upstream, the probe breaks. Alternative: a dedicated `superpowers:listing-skills` call. I chose direct read because the marketplace file is in-repo and stable, but if Claude Code grows a canonical "what skills exist" API, the probe should use it.

4. **Per-model `plot_axes` declared in metadata.** This assumes the "natural parameter plane" is a single fixed 2D projection per model. For Dark SU(3) in particular, `(m_V, m_φ)`, `(m_V, g_D)`, and `(sin θ, m_V)` are all defensible. I picked one per model with paper-figure justification, but different users might prefer different axes. An iteration-2 enhancement: make `plot_axes` a list and add a Step 3.5 "pick plot axes" `AskUserQuestion`. Out of scope for v1.

5. **Time estimates are guesses.** The cold/cached hour ranges are educated estimates, not measured. First real end-to-end run will probably require updating them. Low-stakes — they're pedagogical, not contractual.

6. **Multi-DM on single-candidate models.** I run `combine_multi_dm.py` uniformly (N=1 is a pass-through) for code-path uniformity. A skeptic might argue this is waste. Counter: it's 3 seconds of IO and it keeps Step 4 identical across the three skills, which makes the CI structural-equivalence test trivial to write.

7. **`/demo` doing no prereq probing of its own.** `/demo` happily lets the user pick Dark SU(3) knowing all three constraints are currently blocked (per today's marketplace). Only when the user enters `dark-su3`'s Step 3 does the block surface. Alternative: `/demo` runs `prereq_probe` at model-picker time and annotates each option with e.g. `(2 of 3 constraints currently blocked)`. I left this out because the spec explicitly says `/demo` is a thin front door and does not own interview/gate logic. Moving probe results into `/demo`'s picker dilutes that split.

8. **Passing `skipped` state from per-model skill back to `/demo`.** Spec says `/demo` prints a closing message after the per-model skill returns. It's unclear what structured data (if any) the per-model skill should hand back. I assume: the per-model skill writes a machine-readable `./demo_output/<model>/summary.json` and `/demo` reads it. Needs confirmation.

9. **Where the starter `.yaml` ModelSpec for each model lives.** Current `/demo` references `eval/2506.19062_wimps_blind_spots/sarah/*.m`. The spec does not say whether the rewrite continues to use those files or switches to ModelSpec YAMLs under `_shared/assets/`. I assume ModelSpec YAMLs (the `/sarah-build` input format) because `/demo`'s new dispatch goes through `/sarah-build`, which takes YAML, not `.m`. This means the eval `.m` files are superseded for the runtime path — they remain reference artifacts.

10. **`_shared/` as an implementation directory inside a skills directory.** The marketplace convention is `plugins/<p>/skills/<s>/`. A top-level `_shared/` sibling to skill directories isn't explicitly supported. Claude Code should still just read it as filesystem content, but it's worth confirming the plugin loader doesn't interpret every child of `skills/` as a skill. If it does, move `_shared/` up one level to `plugins/hep-ph-toolkit/_shared/`.
