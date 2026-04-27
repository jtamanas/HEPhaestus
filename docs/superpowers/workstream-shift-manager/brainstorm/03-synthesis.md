# Synthesis 03 — Profumo Demo Workflow Implementation

**Role:** Synthesizer (brainstorming triad)
**Output status:** Authoritative input for the planning phase. The planner treats this as the decision set; deviations require a new round.
**Inputs read:** `spec 2026-04-19`, `01-proposal.md`, `02-critique.md`, memories `project_dm_tool_roles`, `feedback_augment_not_replace`.
**Verified independently:** `marketplace.json` has no `skills[]` (critic correct); `/lagrangian-builder` uses prose-directive dispatch like `"Invoke /sarah-install subskill"` (critic correct); `/maddm` is a decision-tree reference skill (critic correct); `plugins/hep-ph-toolkit/skills/_shared/` holds schemas + helpers + a manually-run pytest suite under `tests/` (not CI — critic correct); `sarah-build` consumes a ModelSpec YAML, not raw `.m` (critic correct); `eval/2506.19062_wimps_blind_spots/sarah/` referenced by the current `/demo` **does not exist on disk** — the ModelSpec YAMLs have to be authored, not translated; one fixture (`dark_su3_spec.yaml`) exists inside `_shared/tests/fixtures/` and is adaptable.

---

## Section 1 — Decisions

Six big decisions up front. Each carries a one-paragraph rationale and a line on what was rejected and why.

### D1. Per-model SKILL.md duplication strategy → **explicit copy with narrow diffs, anti-drift via a manually-run `pytest` alongside `_shared/tests/`**

Each of `singlet-doublet/SKILL.md`, `2hdm-a/SKILL.md`, `dark-su3/SKILL.md` is an independent self-contained SKILL.md that spells out all four steps verbatim. Per-model differences are confined to (a) Step 1 DM-candidate wording, (b) Step 3 time-table numbers and chain annotations, (c) Step 4 per-candidate loop count, and (d) per-model plot axes. The only shared artifact referenced by name is `plugins/hep-ph-toolkit/_shared/constraints.yaml` and the scripts that read it (see D2). Drift is bounded by a `test_skill_structure.py` (see D6) that parses the three SKILL.md files and asserts identical Step 2 / Step 3 gate semantics (option ids, `allowMultiple`, `required`) and identical `Step 4` chain ordering for the same constraint.

**Rejected — the critic's inversion (b1):** putting the flow in `/demo` and making per-model skills metadata-only. This violates the spec's clearly-asserted "`/demo` does **not** own constraint interview, time gates, or execution." The spec is deliberate — per-model skills are meant to be invocable on their own, not only via `/demo`. Collapsing them into metadata would make each model unusable without `/demo`, which kills the "per-model skill as a first-class entry point" motivation from the spec.

**Rejected — thin-skill + shared-flow-reference (critic's fallback):** a per-model SKILL.md that terminates with `"Flow: see ../_flow.md"`. Indirection-opacity is real: a first-time reader of `singlet-doublet/SKILL.md` would not see Step 3's actual AskUserQuestion options without chasing a separate file, and Claude's skill loader surfaces the SKILL.md file itself to the model. The proposer's concern here is correct.

**Accept as known cost:** ~85% text overlap across three files. Mitigated by D6.

### D2. `_shared/` location and contents → **`plugins/hep-ph-toolkit/_shared/` (sibling to `skills/`, not inside it), containing ONLY non-physics orchestration helpers**

Location: `plugins/hep-ph-toolkit/_shared/`, **one level up from `skills/`**, to avoid the ambiguity the proposer flagged in risk #10 (whether every `skills/<foo>/` is interpreted as a skill by the plugin loader). The `plugins/hep-ph-toolkit/skills/_shared/` precedent is kept as precedent-for-name-only; the safer parent-level location is chosen here.

Contents — and **only** these contents:

| Path | Purpose |
|---|---|
| `_shared/constraints.yaml` | Declarative single source of truth for each constraint's prereq chain + cold/cached time ranges + static `status: exists \| planned` field per prereq (see D3). |
| `_shared/time_budget.py` | Pure function: `(selected_constraints, model_overrides) -> (table, cold_total, cached_total)` with overlap-adjustment. ~60 lines. |
| `_shared/status_resolve.py` | Reads `constraints.yaml` and emits the `[EXISTS]`/`[PLANNED]` annotations per chain (see D3 — static, not runtime probe). |
| `_shared/assets/singlet_doublet.yaml` | ModelSpec YAML consumed by `/sarah-build`. Newly authored (the `.m` files referenced by today's `/demo` do not actually exist on disk). |
| `_shared/assets/two_hdm_a.yaml` | Ditto. |
| `_shared/assets/dark_su3.yaml` | Ditto; adapted from existing `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml`. |
| `_shared/tests/test_constraints_yaml.py` | Asserts `constraints.yaml` schema; asserts every SKILL.md's time-table agrees with it. |
| `_shared/tests/test_skill_structure.py` | Parses the three per-model SKILL.md files and asserts Step 2/3/4 structural equivalence (D6). |
| `_shared/tests/conftest.py` | Standard pytest wiring. |

**Not present (explicit non-contents):**

- **No `combine_multi_dm.py`.** Multi-component DM math is deferred to `/dark-matter-constraints` (see D2a). This iteration does not ship multi-component combination.
- **No `prereq_probe.py` reading the marketplace.** Status is static — see D3.
- **No per-model `run_chain.py` dispatcher.** Per-model skills dispatch sibling skills via prose directives (see D4), so no Python orchestrator is needed.
- **No `model_meta_schema.json`.** The per-model SKILL.md metadata block is illustrative + parsed-by-tests, not gate-kept by a JSON schema in v1. (Can add later.)
- **No `demo/scripts/read_model_meta.py`.** `/demo` is a Claude skill; it reads sibling SKILL.md files natively — a Python helper is over-engineering (the critic was right on this).

**Rejected — the proposer's maximal `_shared/` directory with four Python scripts + schema.** It conflates three different concerns (status resolution, time math, multi-DM physics) and puts physics logic in the `hep-ph-demo` plugin's private code. Split them.

### D2a. Multi-component DM math → **deferred to `/dark-matter-constraints` meta-skill, marked `[PLANNED]` in this iteration; Dark SU(3) ships with a clean blocked-constraint UX, not a home-rolled combiner**

The `Ω_tot = Σ Ωᵢ`, linear-in-f DD combination, and quadratic-in-f ID combination encode physics assumptions (halo uniformity, detector response independence, coherence) that belong in a DM-constraint meta-skill, per memory `project_dm_tool_roles.md` ("/dark-matter-constraints meta-skill planned") and per the `augment_not_replace` memo. Burying them inside `hep-ph-demo/_shared/combine_multi_dm.py` puts physics decisions in the demo plugin's private code, exactly inverting the repo's stated principle.

**Consequence for Dark SU(3):** its three constraints all depend on the (not-yet-built) `/dark-matter-constraints`. In this iteration, Dark SU(3) surfaces as a model where **every constraint is `[BLOCKED]`**. That is honest. The per-model skill still works (it prints the chain, explains the block, offers `Back`/`Cancel`) and becomes fully functional the day `/dark-matter-constraints` lands. Singlet-Doublet and 2HDM+a each declare one DM candidate, so N=1 and no combiner is needed — they can demonstrate end-to-end (relic today, DD/ID when the loop subchain skills land).

**Rejected — the proposer's `combine_multi_dm.py` inside `hep-ph-demo/_shared/`.** Violates `augment_not_replace`. The proposer's valve-(c) defense stretches the carve-out: weighted detection rates are modeling assumptions, not sum-rules.

**Rejected — shipping a "temporary home" inside `hep-ph-demo` with a note to move later.** Temporary homes calcify. Block cleanly now.

### D3. `[EXISTS]`/`[PLANNED]` mechanism → **static `status:` field in `_shared/constraints.yaml`, maintained by humans**

Per prereq in each chain, `constraints.yaml` carries `status: exists | planned`. When `/ddcalc` lands, one diff to this file flips its status. The per-model skill's Step 3 reads the field and prints `[EXISTS]`/`[PLANNED]` accordingly.

**Rejected — the proposer's runtime marketplace-json probe.** The critic verified that `marketplace.json` has no `skills[]` field — it lists plugins, not skills. The probe as specified cannot work.

**Rejected — runtime filesystem probe (glob `plugins/*/skills/<name>/SKILL.md`).** A stub SKILL.md could exist without being functional; a filesystem probe would lie. Product-planning status is a changelog-style fact, not a runtime fact — static is honest.

**Rejected — per-skill status file.** Spreads status across N files; `constraints.yaml` already centralizes prereq chains, so status co-locates there.

### D4. Sub-skill dispatch → **prose directive, matching `/lagrangian-builder` convention exactly**

Verified precedent: `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` lines 40, 43, 45, 129, 167, 317-318, 348 — all dispatch is prose, e.g. `"Invoke /sarah-install subskill"` and `"Runs /sarah-install detect"`. There is no `Skill(...)` tool call anywhere in the existing skills. The per-model skills follow this exact pattern: each Step 4 sub-skill invocation is a prose directive in the SKILL.md (`Invoke /sarah-build with _shared/assets/singlet_doublet.yaml`), and Claude-the-agent dispatches.

**Implication for `/demo` → per-model:** `/demo` ends with `"Based on the user's choice, read and execute plugins/hep-ph-toolkit/skills/<model>/SKILL.md."` No tool call, no invented dispatch mechanism.

**Implication for reference-skill invocations:** the critic correctly pointed out that `/maddm`, `/madgraph`, `/hep-plotting/theory-data-comparison` are **reference skills** (decision trees, not runnable orchestrators). The per-model SKILL.md's Step 4 therefore reads: `"Consult the /madgraph and /maddm SKILL.md decision trees; compose the session following references/... per their guidance."` This is honest about what Claude actually has to do. The per-model SKILL.md must embed enough MadDM-specific know-how (which card, which observables flag) to make the reference-skill-walk practical — treat those steps as "guided manual work" in the SKILL.md, not "mechanical dispatch."

**Rejected — `Skill(skill=<name>)` tool invocation.** No such invocation exists anywhere in the repo; inventing it would break the marketplace's established convention. The critic was right: the proposer's framing of `/lagrangian-builder` as a tool-based dispatcher was factually wrong.

### D5. Workstream DAG → **four workstreams, maximum-two-parallel, honest about shared dependencies**

See Section 4 for the DAG. Summary: WS1 (`_shared/` scaffolding + 3 ModelSpec YAMLs + `/demo` rewrite) → WS2 (reference per-model skill: `singlet-doublet`, N=1, relic-ready path) → WS3 & WS4 parallel (`2hdm-a` and `dark-su3` as mechanical adaptations of WS2's template) → WS5 (structural tests + manual integration walkthrough doc).

**Rejected — the proposer's 6-workstream "WS3/4/5 fully parallel" plan.** The critic correctly identified this as fake parallelism: three agents writing three SKILL.md files with 85% shared text in parallel guarantees drift. WS2 establishes the template; WS3/WS4 are mechanical copies, honestly parallelizable.

**Rejected — the critic's 5-workstream variant with CI stripped.** Keep the tests (moved into `_shared/tests/` alongside existing precedent), just acknowledge they are manually-run pytest like the rest of the repo.

### D6. Anti-drift mechanism → **`_shared/tests/test_skill_structure.py` (manually-run pytest), plus a one-line review-checklist item in the workstream PRs**

Concrete mechanism, zero dependency on CI infrastructure the repo lacks:

1. **`test_skill_structure.py`** — pytest file living at `plugins/hep-ph-toolkit/_shared/tests/`, co-located with the existing `_shared/tests/` pattern in `plugins/hep-ph-toolkit/skills/_shared/tests/` (verified — that directory exists with `conftest.py`, `test_blocker_schema.py`, etc.). Two assertions: (a) parsing the three per-model SKILL.md files yields identical Step 2 `AskUserQuestion` option ids, `allowMultiple`, `required`, and identical Step 3 gate-branch structure; (b) each per-model SKILL.md's time-estimate markdown table values match the corresponding rows of `constraints.yaml` within the given per-model override set.
2. **Review checklist line** for any PR touching `plugins/hep-ph-toolkit/skills/*/SKILL.md`: `"Ran plugins/hep-ph-toolkit/_shared/tests/ locally? [y/n]"` added to the PR template or to `CONTRIBUTING.md` (wherever the repo's existing checklist lives — if no template exists, add it to a new `plugins/hep-ph-toolkit/_shared/tests/README.md` with a single-command `pytest` instruction).

**Rejected — "CI will catch it".** Critic correctly noted the repo has no CI. Don't promise what doesn't exist.

**Rejected — a build-step that regenerates SKILL.md from a template.** Would require introducing a template engine, commits that are noisy diffs, and opacity. Two tests are cheaper.

---

## Section 2 — Architecture

### 2.1 File layout

```
plugins/hep-ph-demo/
├── .claude-plugin/plugin.json                (unchanged)
├── README.md                                 (unchanged)
├── _shared/                                   NEW — sibling to skills/, NOT inside it
│   ├── constraints.yaml                       NEW
│   ├── time_budget.py                         NEW
│   ├── status_resolve.py                      NEW
│   ├── assets/
│   │   ├── singlet_doublet.yaml               NEW ModelSpec for /sarah-build
│   │   ├── two_hdm_a.yaml                     NEW ModelSpec
│   │   └── dark_su3.yaml                      NEW ModelSpec (seed from existing fixture)
│   └── tests/
│       ├── conftest.py                        NEW
│       ├── test_constraints_yaml.py           NEW
│       ├── test_skill_structure.py            NEW
│       └── README.md                          NEW (one-liner: `pytest` command)
└── skills/
    ├── install/                               UNCHANGED
    │   └── SKILL.md
    ├── demo/
    │   └── SKILL.md                           REWRITTEN — thin front door
    ├── singlet-doublet/
    │   └── SKILL.md                           NEW
    ├── 2hdm-a/
    │   └── SKILL.md                           NEW
    └── dark-su3/
        └── SKILL.md                           NEW
```

No new plugin. No change to `marketplace.json`. No change to `install/`.

### 2.2 `constraints.yaml` schema

```yaml
# plugins/hep-ph-toolkit/_shared/constraints.yaml
#
# Single source of truth for:
#   - prereq chains per constraint
#   - per-prereq implementation status (exists | planned)
#   - cold/cached hour ranges for the default (single-candidate) case
#   - per-model time overrides where warranted
#
# Edit the `status` field when a prereq skill ships.

schema_version: 1

prereqs:
  # Canonical list of every skill referenced by any chain. One source of truth
  # for the status flag per skill.
  sarah-build:         {status: exists}
  spheno-build:        {status: exists}
  madgraph:            {status: exists}
  maddm:               {status: exists}          # reference skill, not orchestrator
  hep-plotting:        {status: exists}          # reference skill
  feynarts:            {status: planned}
  formcalc:            {status: planned}
  package-x:           {status: planned}
  ddcalc:              {status: planned}
  gamlike:             {status: planned}
  nulike:              {status: planned}
  dark-matter-constraints: {status: planned}    # for multi-component DM combination

constraints:
  relic:
    chain: [sarah-build, spheno-build, madgraph, maddm]
    default_time:
      cold:   [1.0, 2.0]    # hours
      cached: [0.33, 0.67]
  dd:
    chain: [sarah-build, spheno-build, madgraph, feynarts, formcalc, package-x, ddcalc]
    default_time:
      cold:   [2.0, 4.0]
      cached: [0.5, 1.0]
  id:
    chain: [sarah-build, spheno-build, madgraph, maddm, gamlike]
    default_time:
      cold:   [1.0, 3.0]
      cached: [0.33, 0.67]
  collider:
    chain: []
    placeholder: true
    message: "Collider constraints are not yet implemented; planned for a future release."

models:
  singlet-doublet:
    display:
      title: "Singlet-Doublet"
      hook:  "3×3 neutralino-like mixing, tree-level blind spot, loop floor."
    dm_candidates:
      - {name: chi1, spin: "1/2", notes: "Majorana, lightest eigenstate of the singlet-doublet mixing."}
    plot_axes:
      x: {symbol: "m_chi",       range: [100, 1500], units: "GeV", scale: linear}
      y: {symbol: "sin_2theta",  range: [-1, 1],                   scale: linear}
    multi_component: false
    time_overrides: {}   # uses defaults

  2hdm-a:
    display:
      title: "2HDM + a"
      hook:  "Pseudoscalar mediator, CP-forbidden tree SI, loop-only DD."
    dm_candidates:
      - {name: chi, spin: "1/2", notes: "Dirac DM coupled via the CP-odd mediator a."}
    plot_axes:
      x: {symbol: "m_a",    range: [10, 1500], units: "GeV", scale: log}
      y: {symbol: "tan_beta", range: [0.5, 50],              scale: log}
    multi_component: false
    time_overrides:
      dd:  {cold: [3.0, 6.0]}    # loop-only DD is the primary signal; slower

  dark-su3:
    display:
      title: "Dark SU(3)"
      hook:  "Confining dark sector, two DM candidates with exact parameter-independent blind spot."
    dm_candidates:
      - {name: phi, spin: "0", notes: "Scalar dark pion; exact parameter-independent SI blind spot."}
      - {name: V,   spin: "1", notes: "Vector dark meson; tree SI plus resonance region (paper Fig. 8)."}
    plot_axes:
      x: {symbol: "m_V",   range: [50, 2000], units: "GeV", scale: log}
      y: {symbol: "m_phi", range: [10, 2000], units: "GeV", scale: log}
    multi_component: true
    multi_component_prereq: dark-matter-constraints   # adds this to every chain
    time_overrides:
      relic: {cold: [1.5, 3.0]}
      dd:    {cold: [3.0, 5.0]}
      id:    {cold: [1.5, 4.0]}
```

`time_budget.py` public contract: `resolve(model: str, selected: list[str]) -> TimeReport` returning a dict with per-constraint rows (cold, cached, chain with `[EXISTS]`/`[PLANNED]` per prereq, `status: READY|BLOCKED`, `missing: list[str]`) plus an `overlap_totals` section (cold/cached for selected-and-ready constraints, and for selected-all-if-prereqs-existed). Overlap is computed by flattening the union of chains and counting each prereq's time once.

`status_resolve.py`: one function `annotate(chain: list[str]) -> list[tuple[str, "EXISTS"|"PLANNED"]]` plus `missing(chain) -> list[str]`. Reads `constraints.yaml`. That's it.

### 2.3 Per-model SKILL.md — structure (identical across the three)

Frontmatter follows repo convention exactly (verified: only `name` and `description` except `lagrangian-builder` which adds `allowed-tools`):

```markdown
---
name: singlet-doublet
description: Constraint-first interactive workflow for the Singlet-Doublet fermion DM model (Arcadi & Profumo arXiv:2506.19062 §II). User picks constraints (relic/DD/ID); skill shows prereq chain + time estimate + gate, then runs the chain via /sarah-build → /spheno-build → /madgraph → /maddm. Invoke when the user says "singlet-doublet", "blind-spot fermion DM", or is routed from /demo.
---
```

Body ordering, same across all three per-model skills:

1. `# <Title>` + 1–3 sentence framing (model physics, paper anchor).
2. `## When to invoke` (bulleted).
3. `## Model metadata` — a fenced YAML block containing `display`, `dm_candidates`, `plot_axes`, `multi_component`. **This YAML block duplicates the per-model section of `constraints.yaml`** — intentional, for human-scannability. `test_skill_structure.py` asserts agreement.
4. `## Constraints and time estimates` — markdown table per-constraint with `| Constraint | Prereq chain | Cold | Cached |` rows and an explicit `All-constraints cold total (overlap-adjusted): **X–Y hr**` line. This is the line `/demo` reads to populate the model-picker.
5. `## Flow` — Steps 1 through 4, explicit text. Step wording is the one place real duplication lives. See Section 3 for the verbatim text.
6. `## Error paths` — table mirroring the pattern in `sarah-build/SKILL.md` (verified).
7. `## File map` — table pointing at `_shared/assets/<model>.yaml`, `_shared/constraints.yaml`, and the sibling skills.

### 2.4 `/demo` SKILL.md structure (rewrite)

1. Frontmatter: unchanged name/description style.
2. `# Demo` + short framing.
3. `## Flow` — exactly three steps:
   - **Step 1** — print verbatim intro (2 paragraphs on the paper and blind spots).
   - **Step 2** — `AskUserQuestion` gate `Continue` / `Not now`.
   - **Step 3** — `AskUserQuestion` with three model options. The three option strings are hard-coded in the SKILL.md body, each with the physics hook and the cold-total hours. Numbers are consistent with each per-model SKILL.md and with `constraints.yaml` — `test_skill_structure.py` asserts this.
   - **Delegation** — one prose line: `"Based on the user's choice, read and execute plugins/hep-ph-toolkit/skills/<singlet-doublet|2hdm-a|dark-su3>/SKILL.md."`
   - **Closing** — after the per-model skill returns, print a 3-line summary (model run, artifacts path from `./demo_output/<model>/`, any skipped constraints with reason).
4. `## Non-goals` — one-liners: `/demo` does not own the constraint interview, time gates, execution, or multi-DM combination.

### 2.5 Dispatch mechanism (D4 concrete form)

Every place a skill invokes a sibling skill is a **prose directive**, sitting inline in the SKILL.md body, following the exact form used by `/lagrangian-builder`. Examples that will appear in the per-model SKILL.md Step 4:

> Invoke `/sarah-build` with the ModelSpec at `plugins/hep-ph-toolkit/_shared/assets/singlet_doublet.yaml`. On success, the UFO path is available as `config.models.singlet_doublet.ufo`.
>
> Invoke `/spheno-build` on model `singlet_doublet`. On success, the SPheno binary path is at `config.models.singlet_doublet.spheno_bin`.
>
> Consult the `/madgraph` decision tree (it is a reference skill, not an orchestrator). Drive an MG5 session to load the UFO, set the DM candidate `chi1`, and enable `relic_density ON`. Consult `/maddm` for the `maddm_card.dat` settings per its `references/observables.md`.

No `Skill(...)` tool calls. No invented dispatch API.

### 2.6 Anti-drift (D6 concrete form)

`plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` — pytest, runnable with `pytest plugins/hep-ph-toolkit/_shared/tests/`. Asserts:

- Step 2 `AskUserQuestion` options are literally `[relic, dd, id, collider]` in that order across all three SKILL.md files; `allowMultiple: true`; `required: true`.
- Step 3 gate offers exactly `[run_ready, back, cancel]` (blocked branch) or `[go, back, cancel]` (ready branch) across all three.
- Step 4 chain ordering for constraint X is identical across all three (different candidate loop counts aside).
- The `All-constraints cold total (overlap-adjusted)` line in each SKILL.md matches `time_budget.resolve(<model>, all).overlap_totals.cold`.
- Each SKILL.md's `## Model metadata` YAML block agrees with the corresponding `models.<model>` section of `constraints.yaml` on `display`, `dm_candidates`, `plot_axes`.

`plugins/hep-ph-toolkit/_shared/tests/test_constraints_yaml.py` — asserts schema of `constraints.yaml` itself (every prereq in every chain is listed in `prereqs:`; every model's `time_overrides` keys are valid constraint names).

`_shared/tests/README.md` — one line: `From repo root: pytest plugins/hep-ph-toolkit/_shared/tests/`. Pointer added to `CONTRIBUTING.md` if one exists, else just relied upon.

### 2.7 ModelSpec YAML starters (the spec-silent piece)

Three fresh ModelSpec YAMLs under `_shared/assets/`, conforming to `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`:

- `singlet_doublet.yaml` — authored from scratch against the paper §II Lagrangian (fermionic singlet mixed with a doublet via a Higgs coupling).
- `two_hdm_a.yaml` — authored against §III with the CP-odd mediator `a`.
- `dark_su3.yaml` — seeded from `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` (confirmed to exist), adapted for §IV benchmarks.

Authoring these is a **real task** inside WS1, not glue. No `.m` translation — the `eval/.../sarah/` path referenced by today's `/demo` does not exist, so there is nothing to translate.

---

## Section 3 — Interview scripting

These are the **exact prompts** each per-model SKILL.md prints. Variations across the three are confined to bracketed tokens; the rest is identical text. Tokens marked `{…}` come from the SKILL.md's own `## Model metadata` YAML block.

### Step 1 — DM-candidate declaration (no user prompt, just output)

**Single-candidate skills (`singlet-doublet`, `2hdm-a`):**

> For **{display.title}**, the DM candidate is:
>
>   - `{dm_candidates[0].name}` — {dm_candidates[0].notes}
>
> This is a single-candidate model; relic, DD, and ID rates are computed directly for `{dm_candidates[0].name}`.

**Multi-candidate skill (`dark-su3`):**

> For **Dark SU(3)**, the DM candidates are:
>
>   - `phi` — Scalar dark pion; exact parameter-independent SI blind spot.
>   - `V`   — Vector dark meson; tree SI plus resonance region.
>
> This is a **multi-component** model. Per-candidate observables must be combined using relic-weighted fractions `f_i = Ω_i / Ω_tot`. DD rates combine linearly in `f_i`; ID rates combine in `f_i²`. This combination is the responsibility of `/dark-matter-constraints`, which is not yet available in this marketplace. In this iteration, every constraint chain for Dark SU(3) includes `/dark-matter-constraints` as a `[PLANNED]` prereq, so every constraint will surface as `[BLOCKED]` in Step 3. Proceed through the interview to see the planned chain; execution is gated until `/dark-matter-constraints` ships.

### Step 2 — Constraint multi-select (identical across all three skills)

Prose: `Which constraints do you want computed for this model?` followed by one `AskUserQuestion`:

```json
{
  "question": "Which constraints do you want computed for this model?",
  "options": [
    {"id": "relic",    "label": "Relic density",            "description": "Ω h² via MadDM"},
    {"id": "dd",       "label": "Direct detection",         "description": "σ_SI (tree + loop) via MadGraph + FeynArts/FormCalc + DDCalc"},
    {"id": "id",       "label": "Indirect detection",       "description": "Annihilation spectra via MadDM → GamLike / NuLike"},
    {"id": "collider", "label": "Collider (coming soon)",   "description": "Placeholder — execution is a no-op"}
  ],
  "allowMultiple": true,
  "required": true
}
```

Validation: at least one selection required; collider-only triggers a re-ask with the message `"Collider is a placeholder in this iteration; nothing would run. Please also select relic, DD, or ID."`

### Step 3 — Time estimate + prereq resolve + gate

The skill runs (or, equivalently, reasons from `constraints.yaml`):

```
python3 plugins/hep-ph-toolkit/_shared/time_budget.py \
    --model {model} \
    --constraints {selected_ids_space_separated}
```

and prints a block shaped like:

```
Planned chain for {display.title}:

  Relic density       [READY]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
    cold: 1–2 hr   cached: 20–40 min

  Direct detection    [BLOCKED — missing: /feynarts, /formcalc, /package-x, /ddcalc]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS]
      → /feynarts [PLANNED] → /formcalc [PLANNED] → /package-x [PLANNED] → /ddcalc [PLANNED]
    cold: 2–4 hr   cached: 30–60 min

  Indirect detection  [BLOCKED — missing: /gamlike]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
      → /gamlike [PLANNED]
    cold: 1–3 hr   cached: 20–40 min

Overlap-adjusted totals (shared prereqs counted once):
  selected + ready : cold ~1–2 hr,  cached ~20–40 min
  selected total   : cold ~3–5 hr,  cached ~50–100 min  (if all prereqs existed)
```

Gate (identical logic across all three skills):

**If any selected constraint is `BLOCKED`:**

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

**If all selected are `READY`:**

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

Outcomes: `run_ready` drops blocked constraints and proceeds; `go` proceeds; `back` returns to Step 2; `cancel` prints `"Cancelled."` and exits.

### Step 4 — Execute (per-model differences isolated here)

Per-model skill prints the executable ordered list, then works through it via prose directives.

**`singlet-doublet` (N=1, relic ready today; DD/ID blocked):**

For relic:

1. Invoke `/sarah-build` with `plugins/hep-ph-toolkit/_shared/assets/singlet_doublet.yaml`.
2. Invoke `/spheno-build` on model `singlet_doublet`.
3. Consult `/madgraph` (reference) and `/maddm` (reference) to drive an MG5 session: import the UFO, set DM candidate `chi1`, enable `relic_density ON`, `launch`. Parse the MadDM output (`py.py` / scan directory) for `Omega h^2`.
4. Record output to `./demo_output/singlet-doublet/relic.json`.

Then invoke `/hep-plotting` (reference skill) guidance to produce `./demo_output/singlet-doublet/summary.png` with axes `(m_chi, sin_2theta)`.

**`2hdm-a` (N=1):** same shape as singlet-doublet with the `two_hdm_a.yaml` spec and DM candidate `chi`. Plot axes `(m_a, tan_beta)`.

**`dark-su3` (N=2, all `[BLOCKED]` in this iteration):** Step 4 never executes end-to-end; the skill exits at Step 3. Documented in the SKILL.md body: the full N=2 execution path is described (`/dark-matter-constraints` would be invoked once per candidate per constraint), but gated.

### `/demo` intro text

Verbatim (2 paragraphs):

> Arcadi & Profumo ask: *where can dark matter hide from direct detection?* They identify **blind spots** — regions of parameter space where the tree-level DM-nucleon coupling vanishes by cancellation, so the direct-detection signal is suppressed far below naive expectations. Blind spots matter because they weaken "direct detection rules out WIMPs" arguments: a model can evade current limits not by tuning the DM mass, but by tuning the couplings to a cancellation.
>
> This demo walks the full pipeline for one of three paper-benchmark models — Lagrangian → SARAH → SPheno → MadGraph/MadDM → a figure — with constraint selection (relic, direct, indirect) driving which sub-skills run. Some prereq skills (FeynArts, FormCalc, DDCalc, GamLike, and the multi-component DM combiner) are on the roadmap but not yet implemented; those constraints will surface as `[BLOCKED]` and you can choose to run only the ready subset.

Then the `Continue` / `Not now` gate.

Then the three-model picker:

```json
{
  "question": "Which model do you want to explore?",
  "options": [
    {"id": "singlet-doublet", "label": "Singlet-Doublet (~3–5 hr cold, all constraints)",        "description": "3×3 neutralino-like mixing, tree-level blind spot, loop floor."},
    {"id": "2hdm-a",          "label": "2HDM + a        (~5–9 hr cold, all constraints)",         "description": "Pseudoscalar mediator, CP-forbidden tree SI, loop-only DD."},
    {"id": "dark-su3",        "label": "Dark SU(3)      (~6–12 hr cold, all constraints)",        "description": "Confining dark sector, two DM candidates with exact blind spot. Currently fully blocked on /dark-matter-constraints."}
  ],
  "allowMultiple": false,
  "required": true
}
```

The labels include cold totals directly — `/demo` does **not** prereq-probe (per spec + proposer risk #7). The user sees blockages only inside the per-model skill's Step 3.

---

## Section 4 — Workstream DAG

Four workstreams. One agent per workstream where honest; WS3 and WS4 parallelizable once WS2 commits.

```
    WS1 ───────────┬──── WS2 ──┬──── WS3 ──┐
                   │           │           │
                   │           └──── WS4 ──┼──── WS5
                   │                       │
                   └───────────────────────┘
                   (WS5 also sequenced behind all of WS2–WS4)
```

| WS | Title | Depends on | Deliverables | Done criterion |
|---|---|---|---|---|
| **WS1** | Shared scaffolding + assets + `/demo` rewrite | — | (a) `_shared/constraints.yaml`, (b) `_shared/time_budget.py` with `resolve()` contract, (c) `_shared/status_resolve.py`, (d) three ModelSpec YAMLs under `_shared/assets/`, (e) `_shared/tests/conftest.py` + `test_constraints_yaml.py`, (f) `_shared/tests/README.md`, (g) **`demo/SKILL.md` rewrite**. | `pytest plugins/hep-ph-toolkit/_shared/tests/` green. `demo/SKILL.md` renders the intro + gate + 3-option picker + delegation prose directive. Each ModelSpec YAML validates against `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`. |
| **WS2** | Reference per-model skill: `singlet-doublet` | WS1 | (a) `skills/singlet-doublet/SKILL.md`, (b) addition of `test_skill_structure.py` covering ONE skill (fails open on missing skills until WS3/4 land — then generalized). | Skill loads in a fresh session; Step 1 prints the candidate line; Step 2 multi-select round-trips; Step 3 shows `relic [READY]` and `dd / id [BLOCKED]`; on `run_ready`, Step 4 emits the prose directive sequence through `/sarah-build`. Smoke dry-run documented. |
| **WS3** | `2hdm-a` per-model skill | WS2 | `skills/2hdm-a/SKILL.md` — mechanical adaptation of WS2's template. | Same as WS2 done-criteria for this model. `test_skill_structure.py` (extended) asserts Step 2/3/4 structural equivalence with singlet-doublet. |
| **WS4** | `dark-su3` per-model skill | WS2 | `skills/dark-su3/SKILL.md` with Step 1 multi-candidate wording and **explicit `/dark-matter-constraints [PLANNED]` injection into every chain** via `multi_component_prereq`. | All three constraints surface as `[BLOCKED]` in Step 3; `run_ready` with no ready constraints returns the user to Step 2 cleanly; `test_skill_structure.py` asserts Step 2/3 gate structure matches singlet-doublet. |
| **WS5** | Structural test generalization + manual integration walkthrough doc | WS2, WS3, WS4 | (a) `test_skill_structure.py` extended to the three skills; (b) `_shared/tests/MANUAL_WALKTHROUGH.md` — a five-minute scripted `/demo` dry-run (pick Singlet-Doublet → select relic+DD → see `dd [BLOCKED]` → `run_ready` → watch first prose directive for `/sarah-build`). | `pytest plugins/hep-ph-toolkit/_shared/tests/` green. `MANUAL_WALKTHROUGH.md` has been executed end-to-end by the WS5 agent with result notes appended. |

**Parallelization honesty:** WS3 and WS4 are truly parallel once WS2 commits — they touch disjoint directories and consume WS2's template as a frozen artifact. **WS3 and WS4 are the only honestly-parallelizable pair.** WS5 is sequential behind all three per-model skills. WS2 must not be parallelized with WS1 because it depends on `constraints.yaml` + `time_budget.py` being frozen.

**Estimated sizes (coarse):** WS1 ~1.5 days (three ModelSpec YAMLs are the real work); WS2 ~1 day; WS3 ~0.5 day; WS4 ~0.5 day (the multi-candidate UX nuance adds a bit); WS5 ~0.5 day.

**Dispatch recommendation:** `superpowers:dispatching-parallel-agents` for WS3 + WS4 only. WS1, WS2, WS5 are single-agent.

---

## Section 5 — Known risks carried into planning

1. **Reference-skill heaviness in Step 4.** `/madgraph`, `/maddm`, and `/hep-plotting` are all reference skills (decision trees), not orchestrators. The per-model SKILL.md's Step 4 prose directive has to carry enough MadDM-specific knowledge (observable flags, card settings, output path) to make the walk tractable. The planner must allocate SKILL.md body length for that guidance — expect ~40–60 lines per per-model skill just for the Step 4 "how to drive `/madgraph` and `/maddm` for this model" section. This is real content, not filler.

2. **ModelSpec YAML authoring is non-trivial.** The paper's §II (singlet-doublet) and §III (2HDM+a) Lagrangians must be translated into the `/sarah-build`-consumable YAML schema. This is physics work, not glue code. WS1 needs a physics-capable agent and should be treated as the critical path, not as scaffolding. If authoring stalls, WS2 stalls — fallback is to start WS2 against a stub ModelSpec with known-invalid content and iterate once WS1's physicist agent finishes.

3. **No end-to-end execution possible in this iteration.** Only Singlet-Doublet's relic constraint is fully unblocked today. DD and ID for every model (and everything for Dark SU(3)) is blocked. The demo's user-facing promise becomes "interactive interview with a partial-execution path" — this is honest, but the planner should ensure `/demo`'s intro text and the per-model Step 3 messaging prepare the user for this rather than surfacing it as a surprise.

4. **`constraints.yaml` single-source-of-truth invariant depends on tests being run.** If contributors add a new per-model override or flip a prereq's `status` without running `pytest _shared/tests/`, the SKILL.md time-tables and chain annotations will drift from `constraints.yaml`. The anti-drift mechanism (D6) relies on human discipline. Planner: add a line to PR-review checklist; if no checklist exists, include creation of one as a tiny WS5 sub-deliverable.

5. **Order of per-model skill output in `/demo`.** Spec lists Singlet-Doublet → 2HDM+a → Dark SU(3). Synthesis keeps that order. If a future iteration wants "easiest to hardest" or "most-ready-first," the `/demo` picker's hard-coded option order must be updated in lock-step with `constraints.yaml` status changes. Planner: note this as a maintenance point in `demo/SKILL.md`.

6. **Plot handoff via `/hep-plotting` (reference skill).** The SKILL.md plot-axes metadata (D2 `plot_axes`) assumes a fixed 2D projection per model. For Dark SU(3) in particular, `(m_V, m_phi)` is the paper's natural plane; a user wanting `(sin θ, m_V)` has no UX to pick it in v1. Flagged as a deferred v2 enhancement.

7. **`install/` prerequisite implicit.** `/demo` Step 0 in the *current* (pre-rewrite) skill does a preflight that fails cleanly if `/install` hasn't run. The rewrite should **retain this preflight** as the first action in the rewritten `demo/SKILL.md`, **before** the intro paragraph, matching current behavior. Planner: explicitly include the preflight in WS1's done-criteria for `demo/SKILL.md`, lest it be lost in the rewrite.

8. **State hand-back from per-model skill to `/demo`.** Spec says `/demo` prints a closing message after the per-model skill returns. The mechanism for passing back `{skipped_constraints, artifact_paths, headline}` is unspecified. Synthesis decision: per-model skill writes `./demo_output/<model>/summary.json` at the end of Step 4, and `/demo`'s closing block reads it. If the per-model skill exits via `Cancel`, no file is written and `/demo` prints `"{model} interview was cancelled."`. Planner: pin this contract into WS2's deliverables.

9. **The `augment_not_replace` memo applies to the planner too.** If during implementation someone suggests "let's just add a small Python combiner inside `hep-ph-demo/_shared/` as a temporary stand-in for `/dark-matter-constraints`," push back — that's exactly the pattern the memo forbids. Block Dark SU(3) cleanly; don't half-implement physics.

10. **Plugin loader semantics of a non-`skills/` top-level directory.** Placing `_shared/` at `plugins/hep-ph-toolkit/_shared/` (D2) rather than inside `skills/` assumes the plugin loader ignores non-`skills/` subdirectories. This is unverified; the `plugins/hep-ph-toolkit/skills/_shared/` precedent is inside `skills/`, which is the opposite choice. Planner: first action of WS1 is to verify the loader tolerates `plugins/hep-ph-toolkit/_shared/` — load the plugin, confirm no spurious "unknown skill `_shared`" errors. Fallback if the loader complains: move `_shared/` to `plugins/hep-ph-toolkit/skills/_shared/` (precedent-matching); adjust all paths in per-model SKILL.md files accordingly.
