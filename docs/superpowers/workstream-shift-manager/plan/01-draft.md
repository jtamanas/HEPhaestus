# Profumo Demo Workflow — Implementation Plan (Draft 01)

**Drafter:** Plan Drafter (shift-manager pipeline)
**Date:** 2026-04-19
**Authoritative inputs:**
- Spec: `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/specs/2026-04-19-profumo-demo-workflow-design.md`
- Synthesis: `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md`

**Verified in repo:**
- `plugins/hep-ph-demo/.claude-plugin/plugin.json` **does** carry a `skills[]` array. Adding new skills requires updating it (see WS1 — contradicts synthesis §2.1 "No change to `marketplace.json`" which is only true for the marketplace-level index; the plugin-level manifest must be edited).
- `plugins/hep-ph-toolkit/skills/_shared/tests/` precedent confirmed (`conftest.py`, several `test_*.py`, `fixtures/`).
- `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` exists and is adaptable per synthesis §2.7.
- Current `demo/SKILL.md` has a **Step 0 preflight** reading `${XDG_CONFIG_HOME:-~/.config}/hep-ph-agents/config.json` with four keys (`madgraph_path`, `sarah_path`, `spheno_path`, `wolfram_engine_path`). Must be preserved (synthesis risk #7).
- SKILL.md frontmatter convention: `name` + `description` only (sarah-build, spheno-build); `lagrangian-builder` adds `allowed-tools`.
- Commit-message style (from `git log`): short prefix + colon + terse summary, e.g. `W1(2): …`, `W2: …`, `design: …`. Multi-line body allowed. No Co-Authored-By lines in this repo's history — **do not add one**.

---

## A. Workstream Definitions

Five workstreams — WS1 → WS2 → (WS3 || WS4) → WS5. WS3 and WS4 are the only honestly-parallelizable pair.

### WS1 — Shared scaffolding + ModelSpec YAMLs + `/demo` rewrite

| Field | Value |
|---|---|
| **Owner** | Sonnet implementer (physics-literate — ModelSpec YAMLs are real physics work) |
| **Depends on** | — |
| **Parallel with** | none |
| **Worktree** | `../hep-ph-agents.ws1-demo-shared` on branch `ws1/demo-shared-scaffold` |
| **Estimated size** | ~1.5 days. ~800–1200 LOC including three ModelSpec YAMLs (~200 each), `constraints.yaml` (~120), `time_budget.py` (~120), `status_resolve.py` (~60), `demo/SKILL.md` rewrite (~150), tests (~200). |

**Deliverables (absolute paths):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/constraints.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/time_budget.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/status_resolve.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/singlet_doublet.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/two_hdm_a.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/dark_su3.yaml` (NEW, seeded from `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml`)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/conftest.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_constraints_yaml.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_time_budget.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/README.md` (NEW — one-line pytest command)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (REWRITTEN in place)

**Inputs to read first:**
- `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` — binding schema for the three YAMLs
- `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` — seed for Dark SU(3) asset
- `plugins/hep-ph-toolkit/skills/demo/SKILL.md` — current (to be rewritten); preserve Step 0 preflight semantics
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` — prose-directive dispatch precedent (see lines 40, 43, 45, 129, 167, 317–318, 348)
- `plugins/hep-ph-toolkit/skills/_shared/tests/conftest.py` — conftest precedent
- arXiv:2506.19062 §II (singlet-doublet) and §III (2HDM+a) — physics source for two of the three YAMLs

**Done criteria (reviewer checklist):**
- [ ] **Loader check:** After landing, running `claude` with the plugin loaded emits no "unknown skill `_shared`" error. If the loader complains, move `_shared/` to `plugins/hep-ph-toolkit/skills/_shared/` and fix all path references (synthesis risk #10).
- [ ] `constraints.yaml` validates against the schema implicit in `test_constraints_yaml.py`: every prereq referenced by any `constraints.*.chain` exists in `prereqs:`; every `models.*.time_overrides` key is a valid constraint id.
- [ ] `python3 -c "from time_budget import resolve; …"` returns a `TimeReport` with expected keys for all three models × known selection sets. See §C for exact contract.
- [ ] Each `_shared/assets/*.yaml` validates against `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` (`jsonschema` CLI or the repo's existing `test_modelspec_schema.py` fixture pattern).
- [ ] `demo/SKILL.md` structure matches §B.7 below: Step 0 preflight (preserved), Step 1 intro (2 paragraphs verbatim per synthesis §3), Step 2 Continue/Not-now gate, Step 3 three-option model picker, prose-directive delegation to per-model SKILL.md, closing-message block reading `./demo_output/<model>/summary.json`.
- [ ] `pytest plugins/hep-ph-toolkit/_shared/tests/` is green (at least `test_constraints_yaml.py` and `test_time_budget.py`; `test_skill_structure.py` is WS2 scope).
- [ ] `plugins/hep-ph-demo/.claude-plugin/plugin.json` unchanged at this stage (new skills are registered in WS2/3/4).
- [ ] Commit message uses `W1: …` prefix; no Co-Authored-By lines.

---

### WS2 — Reference per-model skill: `singlet-doublet`

| Field | Value |
|---|---|
| **Owner** | Sonnet implementer |
| **Depends on** | WS1 merged |
| **Parallel with** | none |
| **Worktree** | `../hep-ph-agents.ws2-singlet-doublet` on branch `ws2/singlet-doublet-skill` |
| **Estimated size** | ~1 day. ~400 LOC SKILL.md + ~200 LOC tests. |

**Deliverables (absolute paths):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` (NEW — scoped to one skill for now; WS5 generalizes)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/.claude-plugin/plugin.json` (MODIFIED — add `singlet-doublet` to `skills[]`)

**Inputs:**
- All WS1 deliverables (synthesis §2.3 body ordering; §3 interview scripting verbatim)
- `plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` — Error-paths table precedent
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` — prose-directive form

**Done criteria:**
- [ ] `singlet-doublet/SKILL.md` frontmatter uses `name` + `description` only; description matches synthesis §2.3 example.
- [ ] Body contains the seven sections in synthesis §2.3 order: title, When to invoke, Model metadata (YAML), Constraints and time estimates (table), Flow (Steps 1–4 verbatim from synthesis §3), Error paths, File map.
- [ ] Step 2 block contains exactly the `AskUserQuestion` JSON from synthesis §3 Step 2 (`relic`/`dd`/`id`/`collider`, `allowMultiple: true`, `required: true`).
- [ ] Step 3 reports `relic [READY]` and `dd`, `id` as `[BLOCKED — missing: …]` matching `constraints.yaml` statuses.
- [ ] Step 4 relic branch contains four prose directives in order: `/sarah-build` with `_shared/assets/singlet_doublet.yaml` → `/spheno-build` on `singlet_doublet` → `/madgraph` + `/maddm` walkthrough → `/hep-plotting` summary figure.
- [ ] At Step 4 end, skill writes `./demo_output/singlet-doublet/summary.json` per synthesis risk #8 contract.
- [ ] `plugin.json` `skills[]` gains `{"name": "singlet-doublet", "path": "./skills/singlet-doublet/SKILL.md"}`.
- [ ] `test_skill_structure.py` asserts the five things in synthesis §2.6 for the single skill; passes.
- [ ] `pytest plugins/hep-ph-toolkit/_shared/tests/` is green.
- [ ] Commit message `W2: …`.

---

### WS3 — `2hdm-a` per-model skill (parallel with WS4)

| Field | Value |
|---|---|
| **Owner** | Sonnet implementer |
| **Depends on** | WS2 merged (frozen template) |
| **Parallel with** | WS4 |
| **Worktree** | `../hep-ph-agents.ws3-2hdm-a` on branch `ws3/2hdm-a-skill` |
| **Estimated size** | ~0.5 day. ~400 LOC SKILL.md, mechanical adaptation of WS2 template. |

**Deliverables:**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/.claude-plugin/plugin.json` (MODIFIED — add `2hdm-a`)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` (MODIFIED — extend to cover `2hdm-a` alongside `singlet-doublet`)

**Inputs:**
- `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (WS2 output; this is the frozen template)
- `plugins/hep-ph-toolkit/_shared/constraints.yaml` — `models.2hdm-a` section (already present from WS1)
- `plugins/hep-ph-toolkit/_shared/assets/two_hdm_a.yaml` — (WS1)

**Done criteria:**
- [ ] Structural equivalence with `singlet-doublet/SKILL.md` on Step 2 options, Step 3 gate branches, Step 4 chain ordering.
- [ ] Per-model differences isolated to: title/hook wording, DM candidate name (`chi`), plot axes (`m_a`, `tan_beta`), time overrides (`dd: cold [3.0, 6.0]`).
- [ ] Step 3 shows all three constraints `[BLOCKED]` (DD needs loop subchain; ID needs `gamlike`; relic needs only existing skills → `[READY]`). Verify against `constraints.yaml`.
- [ ] `plugin.json` updated.
- [ ] `test_skill_structure.py` extended: assertions now iterate `["singlet-doublet", "2hdm-a"]` and pass.
- [ ] Commit message `W3: …`.

---

### WS4 — `dark-su3` per-model skill (parallel with WS3)

| Field | Value |
|---|---|
| **Owner** | Sonnet implementer |
| **Depends on** | WS2 merged |
| **Parallel with** | WS3 |
| **Worktree** | `../hep-ph-agents.ws4-dark-su3` on branch `ws4/dark-su3-skill` |
| **Estimated size** | ~0.5 day. ~400 LOC SKILL.md. |

**Deliverables:**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/.claude-plugin/plugin.json` (MODIFIED — add `dark-su3`)

**Inputs:** same as WS3, plus `constraints.yaml`'s `multi_component_prereq: dark-matter-constraints` injection rule.

**Done criteria:**
- [ ] Step 1 wording is the **multi-candidate variant** from synthesis §3 (two bullets for `phi` and `V` plus the `f_i` combination paragraph).
- [ ] Every chain in Step 3 appends `/dark-matter-constraints [PLANNED]`, so **every constraint surfaces as `[BLOCKED]`**.
- [ ] Gate after Step 3 offers the blocked-branch `AskUserQuestion` (`run_ready` / `back` / `cancel`). If user picks `run_ready` with zero ready constraints, skill prints `"Nothing to run; returning to constraint selection."` and loops to Step 2.
- [ ] Step 4 body documents the N=2 execution path (one invocation of each prereq per candidate, combined by `/dark-matter-constraints`) but is **unreachable** this iteration and says so explicitly.
- [ ] `plugin.json` updated. Merges after WS3 (or synchronize via the merge-order rule in §D).
- [ ] Commit message `W4: …`.

---

### WS5 — Structural test generalization + manual walkthrough doc

| Field | Value |
|---|---|
| **Owner** | Sonnet implementer |
| **Depends on** | WS2, WS3, WS4 all merged |
| **Parallel with** | none |
| **Worktree** | `../hep-ph-agents.ws5-tests-walkthrough` on branch `ws5/anti-drift-tests` |
| **Estimated size** | ~0.5 day. Test generalization + a ~200-line walkthrough markdown. |

**Deliverables:**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` (MODIFIED — parametrize over all three per-model skills)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/MANUAL_WALKTHROUGH.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/README.md` (MODIFIED — add §"Skills shipped" bullets for the three new per-model skills and a pointer to the manual walkthrough)

**Done criteria:**
- [ ] `pytest plugins/hep-ph-toolkit/_shared/tests/` runs all four test files green (`test_constraints_yaml.py`, `test_time_budget.py`, `test_skill_structure.py`, plus whatever else accumulated).
- [ ] `MANUAL_WALKTHROUGH.md` documents the five-minute dry-run per synthesis §4 WS5 done-criteria (pick singlet-doublet → select relic+DD → see DD blocked → `run_ready` → watch first prose directive fire).
- [ ] README updated. Commit message `W5: …`.

---

## B. File-by-file specification

### B.1 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/constraints.yaml`

**Purpose:** Single source of truth for prereq chains, per-prereq implementation status, and time budgets.

**Mandatory top-level keys:** `schema_version` (=1), `prereqs` (map of skill-name → `{status: exists|planned}`), `constraints` (map of constraint-id → `{chain: [...], default_time: {cold: [lo,hi], cached: [lo,hi]}}` — `collider` carries `placeholder: true` + `message`), `models` (map of model-id → `{display: {title, hook}, dm_candidates: [...], plot_axes: {x, y}, multi_component: bool, multi_component_prereq?: str, time_overrides: {...}}`).

**Content:** copy synthesis §2.2 verbatim. Values are authoritative for the first pass; revise only after the physicist agent reviews ModelSpec YAMLs for WS1 and wants to adjust time estimates.

**Interaction points:** read by `time_budget.py`, `status_resolve.py`, `test_constraints_yaml.py`, `test_skill_structure.py`. Each per-model SKILL.md duplicates the `models.<id>` section inside its `## Model metadata` block — the structure test asserts agreement.

### B.2 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/time_budget.py`

**Purpose:** Pure-function time-budget resolver.

**Public API:**
```python
def resolve(model: str, selected: list[str]) -> dict:
    """
    Returns:
      {
        "model": str,
        "rows": [
          {
            "constraint": str,                    # e.g. "relic"
            "chain": [(skill_name, "EXISTS"|"PLANNED")],
            "cold":   [lo, hi],                   # hours; applies model overrides
            "cached": [lo, hi],
            "status": "READY"|"BLOCKED",
            "missing": [skill_name, ...],         # prereqs with status=planned
          },
          ...
        ],
        "overlap_totals": {
          "cold_ready":   [lo, hi],               # selected ∧ READY
          "cached_ready": [lo, hi],
          "cold_all":     [lo, hi],               # selected, pretending all prereqs exist
          "cached_all":   [lo, hi],
        },
      }
    """
```

Overlap computation: union the chains of all selected constraints; sum each prereq's contribution once. (For v1, since `constraints.yaml` doesn't carry per-prereq hour budgets, overlap adjustment is approximated by taking `max` of constraint cold ranges and summing the unique-prereq extras — acceptable stand-in; revisit if numbers look off in WS2's smoke test.)

**CLI:** `python3 time_budget.py --model <id> --constraints <id> [<id> ...]` prints the block shown in synthesis §3 Step 3.

**Interaction points:** consumed by per-model SKILL.md Step 3 (prose directive invokes it or the skill reasons from `constraints.yaml` directly); `test_time_budget.py` asserts the CLI output shape.

### B.3 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/status_resolve.py`

**Purpose:** Thin helper used by `time_budget.py`.

**Public API:**
```python
def annotate(chain: list[str]) -> list[tuple[str, str]]:  # "EXISTS" or "PLANNED"
def missing(chain: list[str]) -> list[str]                 # subset with status=planned
```

Reads `constraints.yaml` once and caches. No other responsibilities.

### B.4 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/*.yaml` (three files)

**Purpose:** ModelSpec YAMLs consumed by `/sarah-build`.

**Mandatory structure:** conform to `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` — top-level keys `spec_version: 1`, `name`, `claim_source`, `sarah_version_required`, `gauge_groups`, `fermions`, `scalars`, `lagrangian`, `parameters`, `outputs`.

Per-file specifics (WS1 physicist agent authors — values below are the `name` field only, the rest follows the paper):
- `singlet_doublet.yaml` — `name: singlet_doublet`, `claim_source: "arXiv:2506.19062 §II"`.
- `two_hdm_a.yaml` — `name: two_hdm_a`, `claim_source: "arXiv:2506.19062 §III"`.
- `dark_su3.yaml` — `name: dark_su3`, `claim_source: "arXiv:2506.19062 §IV"`. Seed from the existing fixture at `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml`.

**Interaction points:** `/sarah-build` via the Step 4 prose directive. Must validate against `modelspec.schema.json`.

### B.5 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/conftest.py`

Standard pytest wiring. Add a fixture `shared_dir` returning `pathlib.Path(__file__).parent.parent` (the `_shared/` dir). Add a fixture `repo_root` returning four parents up.

### B.6 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_constraints_yaml.py`

**Assertions:**
- Top-level keys present: `schema_version`, `prereqs`, `constraints`, `models`.
- Every prereq referenced in `constraints.*.chain` appears as a key in `prereqs:`.
- Every `models.*.time_overrides` key is a valid `constraints.*` id (`relic`, `dd`, `id`, `collider`).
- Every `models.*.multi_component_prereq` (if present) is a key in `prereqs:`.
- Every `models.*.dm_candidates[*]` has keys `name`, `spin`, `notes`.
- `status` values are `exists` or `planned`.

### B.7 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (REWRITE)

**Frontmatter:**
```yaml
---
name: demo
description: Interactive front door to the Profumo blind-spots demo (arXiv:2506.19062). Runs preflight, prints intro on direct-detection blind spots, and routes the user to one of three per-model skills (singlet-doublet, 2hdm-a, dark-su3). /demo itself does not own the constraint interview, time gates, or execution — those live in the per-model skills. Invoke when the user says "run the demo", "show me hep-ph-agents", "reproduce the blind spot", or after /install on a fresh machine.
---
```

**Body (ordered):**
1. `# Demo` + 1-paragraph framing.
2. `## Flow`
3. **Step 0 — Preflight** (preserved verbatim from current `demo/SKILL.md` — synthesis risk #7). Reads `${XDG_CONFIG_HOME:-~/.config}/hep-ph-agents/config.json`; required keys `madgraph_path`, `sarah_path`, `spheno_path`, `wolfram_engine_path`; on failure, prints the existing missing-executable message and stops.
4. **Step 1 — Paper intro** (the 2 paragraphs from synthesis §3 "`/demo` intro text", verbatim).
5. **Step 2 — Continue / Not-now gate** (`AskUserQuestion` — `Continue`/`Not now`; on `Not now`, exit cleanly).
6. **Step 3 — Three-option model picker** (the JSON from synthesis §3, verbatim, with `cold` totals hard-coded and consistent with `constraints.yaml`).
7. **Delegation** — one prose line: `Based on the user's choice, read and execute plugins/hep-ph-toolkit/skills/<singlet-doublet|2hdm-a|dark-su3>/SKILL.md.`
8. **Closing** — after per-model skill returns, read `./demo_output/<model>/summary.json` and print a 3-line summary (`model`, `artifacts_dir`, `skipped_constraints`). If file missing (user cancelled), print `"<model> interview was cancelled."`.
9. `## Non-goals` — explicit one-liners: `/demo` does not own constraint interview, time gates, execution, or multi-DM combination.

### B.8 `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/<model>/SKILL.md` (three files)

**Frontmatter (singlet-doublet example — adapt title/description per model):**
```yaml
---
name: singlet-doublet
description: Constraint-first interactive workflow for the Singlet-Doublet fermion DM model (Arcadi & Profumo arXiv:2506.19062 §II). User picks constraints (relic/DD/ID); skill shows the prereq chain + time estimate + gate, then runs the chain via /sarah-build → /spheno-build → /madgraph → /maddm. Currently scoped to Profumo-paper benchmark ranges. Invoke when the user says "singlet-doublet", "blind-spot fermion DM", or is routed from /demo.
---
```

**Body (synthesis §2.3 ordering, identical across all three per-model skills):**
1. `# <Title>` + 1–3 sentence framing.
2. `## When to invoke` — bulleted.
3. `## Model metadata` — fenced YAML block duplicating `constraints.yaml`'s `models.<id>` section (display, dm_candidates, plot_axes, multi_component). **This is intentional duplication for scannability; `test_skill_structure.py` asserts agreement.**
4. `## Constraints and time estimates` — markdown table `| Constraint | Prereq chain | Cold | Cached |` plus the `All-constraints cold total (overlap-adjusted): **X–Y hr**` line (`/demo`'s picker reads this).
5. `## Flow` — Steps 1–4 verbatim from synthesis §3.
6. `## Error paths` — table matching the sarah-build SKILL.md pattern.
7. `## File map` — table pointing at `_shared/assets/<model>.yaml`, `_shared/constraints.yaml`, and sibling skills.

**Step 4 execution contract (all three skills):** on completion (or `Cancel`), write/don't-write `./demo_output/<model>/summary.json` per synthesis risk #8:
```json
{
  "model": "singlet-doublet",
  "run_at": "<ISO8601>",
  "ran": ["relic"],
  "skipped_constraints": [
    {"id": "dd", "reason": "blocked on /feynarts, /formcalc, /package-x, /ddcalc"},
    {"id": "id", "reason": "blocked on /gamlike"}
  ],
  "artifacts_dir": "./demo_output/singlet-doublet/",
  "headline": "Relic computed at 3 benchmark points; DD/ID skipped."
}
```

### B.9 `plugins/hep-ph-demo/.claude-plugin/plugin.json` (MODIFIED in WS2/3/4)

Add three entries to `skills[]`:
```json
{ "name": "singlet-doublet", "path": "./skills/singlet-doublet/SKILL.md" },
{ "name": "2hdm-a",          "path": "./skills/2hdm-a/SKILL.md" },
{ "name": "dark-su3",        "path": "./skills/dark-su3/SKILL.md" }
```
Preserve existing `install` and `demo` entries.

### B.10 `plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` (WS2 single-skill, generalized in WS5)

**Assertions (per synthesis §2.6):**
- For each per-model SKILL.md: parses `## Model metadata` YAML block; asserts agreement with `constraints.yaml`'s `models.<id>` on `display`, `dm_candidates`, `plot_axes`.
- Parses the Step 2 `AskUserQuestion` JSON block; asserts option ids == `["relic", "dd", "id", "collider"]`, `allowMultiple: true`, `required: true`.
- Parses Step 3 gate JSON blocks; asserts blocked-branch option ids == `["run_ready", "back", "cancel"]`; ready-branch == `["go", "back", "cancel"]`; both `allowMultiple: false`, `required: true`.
- Parses Step 4 chain ordering (per-constraint); asserts ordering matches `constraints.yaml`'s `constraints.<id>.chain`.
- Parses `## Constraints and time estimates` table's `All-constraints cold total (overlap-adjusted): **X–Y hr**` line; asserts equality with `time_budget.resolve(<model>, all_constraints).overlap_totals.cold_all` (tolerate rounding to 0.5 hr).

Parametrized test fixture: `SKILLS = ["singlet-doublet"]` in WS2; expanded to all three in WS5.

### B.11 `plugins/hep-ph-toolkit/_shared/tests/test_time_budget.py` (WS1)

Assert:
- `resolve("singlet-doublet", ["relic"]).rows[0].status == "READY"`
- `resolve("singlet-doublet", ["dd"]).rows[0].status == "BLOCKED"` and `missing` contains `feynarts`, `formcalc`, `package-x`, `ddcalc`.
- `resolve("dark-su3", ["relic"]).rows[0].status == "BLOCKED"` and `missing` contains `dark-matter-constraints`.
- Overlap totals: `resolve("singlet-doublet", ["relic","dd"]).overlap_totals.cold_all` does not double-count `sarah-build`/`spheno-build`/`madgraph`.

### B.12 `plugins/hep-ph-toolkit/_shared/tests/MANUAL_WALKTHROUGH.md` (WS5)

Five-minute scripted dry-run with expected outputs at each step. Documents the full `/demo` → `/singlet-doublet` → Step 3 blocked-branch → `run_ready` → first `/sarah-build` prose-directive path. The WS5 reviewer executes this and appends observed vs. expected notes.

---

## C. Test & verification plan

**Local commands that must pass:**

| Stage | Command | Expected |
|---|---|---|
| WS1 | `cd /Users/yianni/Projects/hep-ph-agents && pytest plugins/hep-ph-toolkit/_shared/tests/test_constraints_yaml.py plugins/hep-ph-toolkit/_shared/tests/test_time_budget.py -v` | all green |
| WS1 | `cd /Users/yianni/Projects/hep-ph-agents && python3 -c "import yaml, jsonschema; schema=yaml.safe_load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json')); …"` (or equivalent schema validator) against each `_shared/assets/*.yaml` | all valid |
| WS2 | `pytest plugins/hep-ph-toolkit/_shared/tests/ -v` | all green (single-skill structure test included) |
| WS3 | same | green, with structure test now covering 2 skills |
| WS4 | same | green, structure test covers 2 (WS4 doesn't extend — that's WS5) |
| WS5 | same | green, structure test covers all 3 |

**Manual smoke tests:**

- **WS1:** `python3 plugins/hep-ph-toolkit/_shared/time_budget.py --model singlet-doublet --constraints relic dd id` prints the block shape shown in synthesis §3 Step 3.
- **WS2 dry-run:** In a fresh Claude session with the plugin loaded, invoke `/singlet-doublet`. Walk through: Step 1 candidate line; Step 2 select `relic` + `dd`; Step 3 sees `dd [BLOCKED]`; pick `run_ready`; Step 4 prints the first prose directive (`Invoke /sarah-build with _shared/assets/singlet_doublet.yaml`). Do **not** actually run the chain.
- **WS5 dry-run:** Execute `MANUAL_WALKTHROUGH.md` top to bottom; append observations.

**Anti-drift pytest — exact spec:** `test_skill_structure.py` is the anti-drift test from synthesis D6. See §B.10 above for its precise assertion list.

---

## D. Integration & merge order

**Branching strategy:** each workstream in its own git worktree, branch named `ws<N>/<kebab-slug>`. Merge back to `main` in order **WS1 → WS2 → (WS3 and WS4 in either order, rebasing on the other if it lands first) → WS5**.

**Merge checkpoints:**
1. WS1 merges to main; tag commit with `W1: …` prefix.
2. WS2 merges after WS1 — the singlet-doublet SKILL.md is the frozen template for WS3/WS4.
3. WS3 and WS4 open PRs against main in parallel; the second-to-merge rebases on top of the first and resolves `plugin.json` conflicts manually (both add an entry — keep both).
4. WS5 rebases on final main after all three per-model skills are merged; generalizes `test_skill_structure.py` parametrization; updates `README.md`.

**Final glue commit (part of WS5):** update `plugins/hep-ph-demo/README.md` §"Skills" to list all five skills (`install`, `demo`, `singlet-doublet`, `2hdm-a`, `dark-su3`) and link to `MANUAL_WALKTHROUGH.md`. No separate `W6: glue` commit needed — bundle into `W5:`.

**Commit message convention (observed from `git log`):**
- Short prefix + colon, e.g. `W1: demo-shared scaffolding + 3 ModelSpec YAMLs + /demo rewrite`.
- Sub-commits inside a workstream may use `W1(1): …`, `W1(2): …` (precedent: commits `88acd11`, `06e3787`, …).
- No `Co-Authored-By:` line (no precedent in this repo).
- Imperative mood; lowercase after the colon.

---

## E. Explicit non-goals

**Out of scope for this plan (from spec + synthesis):**
- No new plugin; all four skills live in `plugins/hep-ph-demo/`.
- No changes to `install/` or the `install/SKILL.md` preflight contract.
- No change to the top-level `.claude-plugin/marketplace.json` (only the plugin-internal `plugin.json` changes).
- No multi-component DM combiner inside `hep-ph-demo/_shared/` (explicitly rejected in synthesis D2a — physics belongs in the future `/dark-matter-constraints` meta-skill).
- No collider execution — placeholder only.
- No autonomous skill composition inside per-model skills (prose-directive dispatch only, matching `/lagrangian-builder` convention).
- No runtime marketplace-status probe — `status:` is static in `constraints.yaml`.
- No template engine or generated-SKILL.md pipeline — 3× duplication with anti-drift tests is the accepted cost.
- No broadening of per-model skills beyond Profumo-paper benchmark ranges in this iteration.

**Future skills this plan deliberately does NOT wait for:**
- `/feynarts`, `/formcalc`, `/package-x` — required for full DD; their absence is surfaced as `[BLOCKED]`.
- `/ddcalc` — same.
- `/gamlike`, `/nulike` — required for full ID; same.
- `/dark-matter-constraints` — meta-skill for multi-component DM combination; its absence blocks all of Dark SU(3).

When any of these land, the only change needed is flipping its `status:` field in `_shared/constraints.yaml`. No SKILL.md edits required.

---

## F. Risks and mitigations

| # | Risk | Mitigation | Owner |
|---|---|---|---|
| R1 | Plugin loader treats `_shared/` as a skill and errors (synthesis risk #10). | WS1 first action: load the plugin in a fresh Claude session and observe. Fallback: move to `plugins/hep-ph-toolkit/skills/_shared/` and fix paths. | WS1 implementer |
| R2 | ModelSpec YAML authoring stalls WS2 (synthesis risk #2). | WS1 author may ship stub-quality YAMLs passing schema validation with placeholder parameters; WS2 starts against them. Physicist revision can land as `W1 fixup: …` after WS2 merges — the skill paths don't change. | WS1 implementer / shift manager |
| R3 | `constraints.yaml` drifts from per-model SKILL.md bodies (synthesis risk #4). | `test_skill_structure.py` catches drift on manual pytest run; PR-review checklist line: *"Ran `pytest plugins/hep-ph-toolkit/_shared/tests/` locally?"* Add this to `MANUAL_WALKTHROUGH.md` preamble (WS5). | Every workstream's reviewer |
| R4 | Step 4 prose directives for reference skills (`/madgraph`, `/maddm`, `/hep-plotting`) are too terse to be tractable (synthesis risk #1). | WS2 template must include 40–60 lines of MadDM-specific guidance (card settings, observable flags, output paths). WS2 reviewer verifies length + concreteness. | WS2 reviewer |
| R5 | User surprised that most constraints are `[BLOCKED]` (synthesis risk #3). | `/demo` intro paragraph 2 explicitly calls out the roadmap gaps. WS1 reviewer verifies the wording matches synthesis §3. | WS1 reviewer |
| R6 | WS3/WS4 parallel commits conflict on `plugin.json`. | Second-to-merge rebases and keeps both entries; shift manager confirms the merged array has all three new entries. | WS3/WS4 implementers |
| R7 | Someone proposes a "temporary" multi-DM combiner in `_shared/` (violates `augment_not_replace` memo). | Plan drafter, every reviewer: **push back**. Synthesis D2a is explicit — Dark SU(3) blocks cleanly. | All reviewers |
| R8 | No CI — anti-drift relies on human discipline. | Accept as a known cost. `_shared/tests/README.md` has the pytest one-liner; `MANUAL_WALKTHROUGH.md` reminds contributors. | Long-term repo maintainer |
| R9 | State-handoff contract (`./demo_output/<model>/summary.json`) missed by a per-model skill. | Pinned in WS2 done-criteria + structure test (WS5 could add a regex assertion that SKILL.md body contains the literal `demo_output/<model>/summary.json` string; recommended). | WS2 reviewer |
| R10 | WS1 physicist agent produces YAMLs that `/sarah-build` rejects at runtime (schema passes but SARAH fails). | Smoke-test one of the three through `/sarah-build detect` in a local shell during WS1 review. If infeasible (SARAH not installed on reviewer's box), accept the schema-only check and surface the risk in the WS2 dry-run. | WS1 reviewer |

---

## G. Handoff prompts

### WS1 — Implementer prompt (~200 words)

> You are implementing WS1 of the Profumo demo workflow redesign. Read these first (in order): `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/specs/2026-04-19-profumo-demo-workflow-design.md`, `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md`, `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/01-draft.md` (this plan; your scope is §A→WS1 and §B.1–B.7, B.11).
>
> Create a worktree `../hep-ph-agents.ws1-demo-shared` on branch `ws1/demo-shared-scaffold`. Deliverables are listed under "WS1 Deliverables" in the plan — 11 files. Before any coding, verify the plugin loader tolerates a top-level `_shared/` directory (synthesis R10 / plan R1). If it doesn't, move `_shared/` to `plugins/hep-ph-toolkit/skills/_shared/` and update all paths.
>
> Use `constraints.yaml` content from synthesis §2.2 verbatim. For the three ModelSpec YAMLs, seed `dark_su3.yaml` from `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml`; author `singlet_doublet.yaml` and `two_hdm_a.yaml` from arXiv:2506.19062 §II and §III. All three must validate against `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`.
>
> Preserve Step 0 preflight in the `demo/SKILL.md` rewrite — read the current file first. Use synthesis §3 "`/demo` intro text" verbatim for Step 1. Commit message prefix `W1:`. No `Co-Authored-By` line.
>
> Stop and iterate when the opus reviewer responds.

### WS1 — Reviewer prompt (~150 words)

> You are the opus skeptic for WS1. Read: the plan `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/01-draft.md` (§A WS1, §B.1–B.7, §B.11, §C, §F), then the implementer's diff.
>
> Check line-by-line: (1) loader check performed and documented; (2) `constraints.yaml` matches synthesis §2.2; (3) each `_shared/assets/*.yaml` validates against `modelspec.schema.json` — run the validator yourself; (4) `demo/SKILL.md` Step 0 preflight preserved verbatim from the pre-rewrite file, Step 1 intro matches synthesis §3 word-for-word, Step 3 picker JSON matches synthesis §3 word-for-word; (5) `pytest plugins/hep-ph-toolkit/_shared/tests/` green on your machine; (6) no Python physics logic added (violates `augment_not_replace`); (7) `plugin.json` untouched (new skills come in later workstreams); (8) commit message uses `W1:` prefix, no Co-Authored-By line.
>
> Be adversarial on ModelSpec physics correctness — stubs are allowed only if flagged.

### WS2 — Implementer prompt (~200 words)

> You are implementing WS2 of the Profumo demo workflow redesign. Read (in order): `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/01-draft.md` (§A→WS2, §B.8, §B.10), synthesis §2.3 and §3 (full interview scripting), and the frozen WS1 artifacts under `plugins/hep-ph-toolkit/_shared/`.
>
> Create worktree `../hep-ph-agents.ws2-singlet-doublet` on branch `ws2/singlet-doublet-skill`. Deliverables: `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md`, `plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` (single-skill for now), and a modification to `plugins/hep-ph-demo/.claude-plugin/plugin.json` adding the skill.
>
> Use synthesis §3 Step 1/2/3/4 text **verbatim** for the Flow section. Step 4 relic branch must be four prose directives (not tool calls) following the `/lagrangian-builder` SKILL.md convention — see `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` lines 40, 43, 45, 129, 167 for the form. Embed 40–60 lines of MadDM-specific guidance (card settings, observable flag, output parse) per plan R4.
>
> At Step 4 end (or cancel), write `./demo_output/singlet-doublet/summary.json` per plan §B.8 schema. Commit `W2: …`, no Co-Authored-By. Hand back when `pytest plugins/hep-ph-toolkit/_shared/tests/` is green.

### WS2 — Reviewer prompt (~150 words)

> You are the opus skeptic for WS2. Read the plan (§A WS2, §B.8, §B.10, §C) and the implementer's diff.
>
> Verify: (1) SKILL.md has all 7 sections in synthesis §2.3 order; (2) Step 2 `AskUserQuestion` JSON is verbatim from synthesis §3; (3) Step 3 reports `relic [READY]`, `dd [BLOCKED]`, `id [BLOCKED]` — chain annotation agreement with `constraints.yaml` (run `time_budget.py` yourself); (4) Step 4 uses prose directives, **not** invented `Skill(...)` calls; (5) MadDM guidance is concrete (card settings + observable + output parse), not a one-liner; (6) `summary.json` schema matches §B.8; (7) `plugin.json` gained exactly the singlet-doublet entry; (8) `test_skill_structure.py` asserts the five things in synthesis §2.6; (9) dry-run the skill in a fresh Claude session per plan §C Manual smoke tests; (10) commit message `W2:`, no Co-Authored-By.

### WS3 — Implementer prompt (~200 words)

> You are implementing WS3 of the Profumo demo workflow redesign. **WS4 is being implemented in parallel by a peer agent; do not touch `dark-su3` or files inside `plugins/hep-ph-toolkit/skills/dark-su3/`.**
>
> Read (in order): `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/01-draft.md` (§A→WS3, §B.8), then the **frozen WS2 template** at `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md`. Your `2hdm-a/SKILL.md` is a mechanical adaptation of it.
>
> Create worktree `../hep-ph-agents.ws3-2hdm-a` on branch `ws3/2hdm-a-skill`. Per-model differences are ONLY: title/hook wording, DM candidate (`chi`), `plot_axes: (m_a, tan_beta)`, `time_overrides.dd: cold [3.0, 6.0]` per `constraints.yaml`. Step 2/3/4 structural skeleton must match the WS2 template so `test_skill_structure.py` passes when you extend it to `["singlet-doublet", "2hdm-a"]`.
>
> Add the `2hdm-a` entry to `plugins/hep-ph-demo/.claude-plugin/plugin.json`. On merge, if WS4 landed first, rebase and keep both new entries. Commit prefix `W3:`, no Co-Authored-By. Hand back when `pytest plugins/hep-ph-toolkit/_shared/tests/` is green.

### WS3 — Reviewer prompt (~150 words)

> Opus skeptic for WS3. Read the plan (§A WS3, §B.8, §C, §D merge-order) and the diff.
>
> Verify: (1) `2hdm-a/SKILL.md` has the same 7 sections in the same order as `singlet-doublet/SKILL.md`; (2) differences are confined to title/hook, DM candidate name, plot axes, time overrides — diff the two SKILL.md files section-by-section; (3) Step 3 correctly shows `dd` as `[BLOCKED]` with the loop subchain missing; (4) `plugin.json` gained exactly the `2hdm-a` entry (preserves `install`, `demo`, `singlet-doublet`); (5) `test_skill_structure.py` extended to parametrize over both skills; all assertions pass; (6) commit `W3:`.

### WS4 — Implementer prompt (~200 words)

> You are implementing WS4 of the Profumo demo workflow redesign. **WS3 is being implemented in parallel; do not touch `2hdm-a` or files inside `plugins/hep-ph-toolkit/skills/2hdm-a/`.**
>
> Read: the plan (§A→WS4, §B.8), synthesis §3 Step 1 **multi-candidate variant** and the Dark SU(3) specifics in §2.2 and §4, and the frozen WS2 template.
>
> Create worktree `../hep-ph-agents.ws4-dark-su3` on branch `ws4/dark-su3-skill`. Step 1 uses the multi-candidate wording (two bullets `phi` + `V`, plus the `f_i` combination paragraph pointing at `/dark-matter-constraints [PLANNED]`). **Every chain in Step 3 appends `/dark-matter-constraints` from `multi_component_prereq`**, so every constraint surfaces as `[BLOCKED]`.
>
> The blocked-gate `AskUserQuestion` still fires. If user picks `run_ready` with zero ready constraints, print `"Nothing to run; returning to constraint selection."` and re-enter Step 2. Step 4 body documents the N=2 execution path but is never reached this iteration — say so explicitly.
>
> Add the `dark-su3` entry to `plugin.json`. On merge, if WS3 landed first, rebase. Commit `W4:`, no Co-Authored-By.

### WS4 — Reviewer prompt (~150 words)

> Opus skeptic for WS4. Read the plan (§A WS4, §B.8, synthesis §3 Step 1 multi-candidate variant) and the diff.
>
> Verify: (1) Step 1 shows **two** DM candidates with the `f_i` combination paragraph and the `/dark-matter-constraints [PLANNED]` annotation; (2) Step 3 shows **all three** constraints as `[BLOCKED]` — chain annotations include `dark-matter-constraints` in every row; (3) the `run_ready`-with-zero-ready-constraints branch loops back to Step 2 with the explicit message; (4) Step 4 body documents N=2 execution but is clearly gated; (5) **no multi-component combiner code** was added to `_shared/` — if it was, hard reject per plan R7 / synthesis D2a / memory `feedback_augment_not_replace`; (6) `plugin.json` updated; (7) commit `W4:`.

### WS5 — Implementer prompt (~200 words)

> You are implementing WS5 of the Profumo demo workflow redesign (final workstream). Read the plan (§A→WS5, §B.10, §B.12, §C, §D).
>
> Create worktree `../hep-ph-agents.ws5-tests-walkthrough` on branch `ws5/anti-drift-tests`. Deliverables:
>
> 1. Generalize `plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py` to parametrize over all three per-model skills `["singlet-doublet", "2hdm-a", "dark-su3"]`. All assertions in synthesis §2.6 must pass for all three.
> 2. Author `plugins/hep-ph-toolkit/_shared/tests/MANUAL_WALKTHROUGH.md` — a five-minute scripted `/demo` dry-run. Start at `/demo`, pick Singlet-Doublet, select relic+DD, observe DD `[BLOCKED]`, pick `run_ready`, watch the first prose directive fire (`Invoke /sarah-build with _shared/assets/singlet_doublet.yaml`). At each step, record expected vs. observed output. **Execute this walkthrough yourself end-to-end** and append your observations to the file before committing.
> 3. Update `plugins/hep-ph-demo/README.md` "Skills shipped" section to list all five skills (`install`, `demo`, `singlet-doublet`, `2hdm-a`, `dark-su3`) with one-line descriptions. Add a pointer to `MANUAL_WALKTHROUGH.md`.
>
> Commit `W5:`. No Co-Authored-By.

### WS5 — Reviewer prompt (~150 words)

> Opus skeptic for WS5. Read the plan (§A WS5, §B.10, §B.12) and the diff.
>
> Verify: (1) `test_skill_structure.py` parametrizes over all three per-model skills and all synthesis §2.6 assertions pass — run `pytest plugins/hep-ph-toolkit/_shared/tests/ -v` yourself; (2) `MANUAL_WALKTHROUGH.md` covers the full dry-run with expected outputs at each step **and** has the implementer's observation notes appended (not just the template); (3) if any observed-vs-expected mismatch is recorded, it has been either fixed or escalated, not swept under the rug; (4) README updated with all five skills and a pointer to the walkthrough; (5) commit `W5:`; (6) after this lands, the `hep-ph-demo` plugin loads cleanly and `/demo` → `/singlet-doublet` reaches Step 4's first prose directive without errors.

---

## Appendix — Absolute-path file map (all files created or modified)

**Created (15):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/constraints.yaml`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/time_budget.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/status_resolve.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/singlet_doublet.yaml`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/two_hdm_a.yaml`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/assets/dark_su3.yaml`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/conftest.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_constraints_yaml.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_time_budget.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/test_skill_structure.py`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/README.md`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/_shared/tests/MANUAL_WALKTHROUGH.md`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md`
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md`

**Modified (3):**
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (rewrite)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/.claude-plugin/plugin.json` (three skill entries added across WS2/3/4)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/README.md` (WS5)

**Total: 18 files touched** (15 created + 3 modified).
