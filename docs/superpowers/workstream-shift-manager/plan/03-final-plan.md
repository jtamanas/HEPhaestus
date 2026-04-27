# Profumo Demo Workflow — FINAL Implementation Plan

**Synthesizer:** Plan Synthesizer (shift-manager pipeline)
**Date:** 2026-04-19
**Status:** AUTHORITATIVE — execution reads from this file.
**Supersedes:** `plan/01-draft.md`, `plan/02-critique.md`.
**Inputs verified against repo state on 2026-04-19.**

---

## 0. Summary

This plan delivers a constraint-first rewrite of `/demo` plus three new per-model orchestrator skills (`singlet-doublet`, `2hdm-a`, `dark-su3`) inside `plugins/hep-ph-demo/`, backed by a small non-physics orchestration layer in `plugins/hep-ph-toolkit/skills/_shared/` (sibling-of-skills path avoided — see §1.4). The deliverable is an interactive interview: user picks a model → picks constraints (relic/DD/ID) → sees a prereq chain with `[EXISTS]`/`[PLANNED]` annotations, time estimate, and a gate → on `Run it`, executes the ready subset via prose-directive dispatch to `/sarah-build` → `/spheno-build` → `/madgraph` + `/maddm` → `/hep-plotting`. Only Singlet-Doublet relic and 2HDM+a relic are fully unblocked this iteration; everything else surfaces as `[BLOCKED]` on known-planned skills. Multi-component DM math is deferred to the planned `/dark-matter-constraints` meta-skill (Dark SU(3) fully-blocks, honestly). Anti-drift is enforced by a parametrized pytest at `plugins/hep-ph-toolkit/skills/_shared/tests/`. Five workstreams: WS1 → WS2 → (WS3 ∥ WS4) → WS5.

---

## 1. Final decisions

### 1.1 `summary.json` schema — **PIN IN WS1** (resolves critique D-SYN-1)

The schema is owned by WS1 as a JSON Schema file at `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json` and validated by a new WS1 test `test_summary_schema.py`. WS2/WS3/WS4 per-model SKILL.md files MUST write a file conforming to this schema at the end of Step 4 (or on cancel, write nothing). WS1's `/demo` closing block reads the file, prints three lines, degrades gracefully to `"<model> interview was cancelled."` when the file is missing. **Rationale:** the reader cannot exist without a contract; deferring the schema to WS2 creates a hidden cross-workstream coupling the critique flagged (A1.5). Pinning the schema in WS1 eliminates the coupling, gives WS2–4 a mechanical check, and makes the `/demo` closing deterministic. Exact schema in §4.

### 1.2 "Prose directive" is mechanically defined (resolves critique A2.1 / WS2 handoff weakness)

**A prose directive is a markdown blockquote (line starts with `> `) whose first non-whitespace word is `Invoke` followed by a forward-slash-prefixed skill name.** Matched by the regex `^>\s*Invoke\s+/[a-z0-9-]+\b`. Reviewers and `test_skill_structure.py` count occurrences per Step-4 branch via that regex. Reference precedent: `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` lines 40, 43, 45, 129, 167. The Step-4 relic branch in each per-model SKILL.md must contain **exactly four** prose directives, in order: `/sarah-build`, `/spheno-build`, `/madgraph` (reference-skill consultation), `/maddm` (reference-skill consultation). The plot step (`/hep-plotting`) lives outside the count — it runs after all selected constraints are computed.

### 1.3 Physics adaptation for WS3 (2HDM+a) and WS4 (dark-su3) is REQUIRED, not copy-paste (resolves critique A3.1)

**Copying WS2's MadDM guidance block verbatim is grounds for rejection.** The three models differ:

- **WS2 singlet-doublet** — Majorana fermion DM via Higgs-portal mixing. MadDM: Majorana candidate flag, t-channel Higgs exchange, tree SI dominant.
- **WS3 2HDM+a** — Dirac DM coupled via the CP-odd pseudoscalar mediator `a`. MadDM guidance MUST mention: Dirac candidate flag, s-channel `a`-resonance in relic, **CP-forbidden tree SI** (so `σ_SI_tree ≈ 0`), loop-only DD is the primary signal, annihilation channels dominated by `a → SM SM` with `tan β`-dependence. The WS3 implementer MUST rewrite the Step-4 MadDM paragraph and Step-4 DD discussion. Reviewer rejects if the words `Dirac`, `CP-odd`, `loop-only`, `a-resonance`, `tan β` do not all appear.
- **WS4 dark-su3** — Confining dark sector with two DM candidates: scalar `phi` (exact parameter-independent SI blind spot) and vector `V` (tree SI + resonance region). MadDM guidance MUST mention: two DM candidates (scalar + vector), confining dynamics implies composite states from SARAH's HLS-like Lagrangian, relic combines via `Ω_tot = Σ Ωᵢ` (but COMBINATION IS DEFERRED to `/dark-matter-constraints` [PLANNED]), blind-spot discussion for `phi` cites the exact cancellation (not parameter-tuned), resonance region for `V`. Reviewer rejects if the words `scalar dark pion`, `vector dark meson`, `blind spot`, `confining`, `multi-component` do not all appear. Reviewer ALSO rejects any inline `f_i` combination math in the SKILL.md body beyond a single pointer sentence.

Both implementer prompts carry this list verbatim. Both reviewer prompts carry the rejection word lists.

### 1.4 Loader-check for top-level `_shared/` — **AVOID IT ENTIRELY; use `plugins/hep-ph-toolkit/skills/_shared/`** (resolves critique A1.1 / D-SYN-5)

The precedent at `plugins/hep-ph-toolkit/skills/_shared/` (verified: `blocker.schema.json`, `modelspec.schema.json`, `config_migration.py`, `sarah_name.py`, `tests/`) places `_shared/` INSIDE `skills/`. The synthesis (§2.1) proposed the opposite sibling-of-skills location citing loader ambiguity, but gave no evidence the sibling location works and admitted (R10) it was unverified. **Decision:** follow the existing precedent — put everything under `plugins/hep-ph-toolkit/skills/_shared/`. This eliminates the loader-risk entirely (we know this location works because another plugin already uses it in production). No WS0 check is needed. All paths in this plan use `plugins/hep-ph-toolkit/skills/_shared/`.

If for any reason the WS1 implementer believes the loader rejects this path (it won't, but belt-and-suspenders): run `ls plugins/hep-ph-toolkit/skills/_shared/` and confirm that plugin currently loads without error before starting work. That's the test. No code changes gated on it.

### 1.5 Worktree / merge strategy — **WS1, WS2, WS5 serial on trunk-ish worktrees; WS3 ∥ WS4 in separate worktrees with pre-parametrized test in WS2** (resolves critique CX.1)

**Worktree matrix:**

| WS | Worktree path | Branch | Runs in parallel with |
|---|---|---|---|
| WS1 | `../hep-ph-agents.ws1-shared` | `ws1/shared-scaffold` | none |
| WS2 | `../hep-ph-agents.ws2-singlet-doublet` | `ws2/singlet-doublet` | none |
| WS3 | `../hep-ph-agents.ws3-2hdm-a` | `ws3/2hdm-a` | WS4 |
| WS4 | `../hep-ph-agents.ws4-dark-su3` | `ws4/dark-su3` | WS3 |
| WS5 | `../hep-ph-agents.ws5-polish` | `ws5/polish` | none |

**Key anti-merge-conflict moves:**

1. **WS2 ships `test_skill_structure.py` already parametrized over all three skill names** with a `skip-if-missing` guard on each SKILL.md file path. WS3 and WS4 only ADD files; they do NOT touch the test. WS5 removes the skip guards. (Resolves CX.1's test-file merge hazard.)
2. **WS2 ships `plugin.json` already containing all three per-model entries** (`singlet-doublet`, `2hdm-a`, `dark-su3`). WS3 and WS4 do NOT touch `plugin.json`. WS5 confirms. (Resolves plan §D `plugin.json` collision.)
3. **WS3 and WS4 touch disjoint directories** — `skills/2hdm-a/` vs `skills/dark-su3/` — so their diffs merge trivially.

**Concrete git sequence:**

```bash
# WS1 (agent A, serial):
cd /Users/yianni/Projects/hep-ph-agents
git worktree add ../hep-ph-agents.ws1-shared -b ws1/shared-scaffold main
# implementer works in that worktree; commits with W1: prefix
# on review approval:
git checkout main
git merge --no-ff ws1/shared-scaffold
git worktree remove ../hep-ph-agents.ws1-shared

# WS2 (agent B, serial, after WS1 merged):
git worktree add ../hep-ph-agents.ws2-singlet-doublet -b ws2/singlet-doublet main
# implementer works; commits with W2: prefix
git checkout main
git merge --no-ff ws2/singlet-doublet
git worktree remove ../hep-ph-agents.ws2-singlet-doublet

# WS3 + WS4 (agents C and D, parallel, both branched off main-after-WS2):
git worktree add ../hep-ph-agents.ws3-2hdm-a -b ws3/2hdm-a main
git worktree add ../hep-ph-agents.ws4-dark-su3 -b ws4/dark-su3 main
# implementers work concurrently; neither touches plugin.json or test_skill_structure.py
# on both reviews approved (order doesn't matter):
git checkout main
git merge --no-ff ws3/2hdm-a
git merge --no-ff ws4/dark-su3        # trivial merge; disjoint files
git worktree remove ../hep-ph-agents.ws3-2hdm-a
git worktree remove ../hep-ph-agents.ws4-dark-su3

# WS5 (agent E, serial, after both merged):
git worktree add ../hep-ph-agents.ws5-polish -b ws5/polish main
# implementer removes skip-guards from test_skill_structure.py; adds MANUAL_WALKTHROUGH.md; updates README
git checkout main
git merge --no-ff ws5/polish
git worktree remove ../hep-ph-agents.ws5-polish
```

### 1.6 Other resolved items

- **Preflight-vs-intro order (A1.2):** PIN — Step 0 preflight runs BEFORE the paper intro, matching current `demo/SKILL.md` behavior. A broken install must not be greeted with 2 paragraphs of physics.
- **ModelSpec physics correctness (A1.4, D-SYN-4, CX.5):** PIN — every ModelSpec YAML carries a top-level `provisional: true|false` boolean. If `provisional: true`, the YAML MUST carry a `# TODO(physics):` comment block naming exactly what is unverified. WS1 may ship stubs as `provisional: true`. A subsequent fixup commit (`W1 fixup: …`) flips to `provisional: false` after physicist sign-off. WS1 reviewer MUST cross-reference each non-provisional YAML against arXiv:2506.19062 §II/§III/§IV by field name.
- **Dark SU(3) `run_ready` with zero ready constraints (A4.1, D-SYN-2):** PIN — loop back to Step 2 with the message `"No selected constraints are currently runnable. Re-select constraints or Cancel."` Matches the plan draft; gives the user agency.
- **Overlap-computation algorithm (A1.3):** PIN — `time_budget.py` implements the per-prereq hour model. Each prereq carries a `hours: {cold: [lo, hi], cached: [lo, hi]}` entry in `constraints.yaml`'s `prereqs:` map. Total cold time for selected constraints = sum over UNIQUE prereqs in the union of their chains. Unit test pins this with a fixture where two constraints share 3 prereqs and differ in 1.
- **MadDM guidance tractability (A2.2):** PIN — WS2 reviewer MUST write a 3-sentence "could-I-drive-MG5-from-this" attestation in the PR review comment. Not a full dry-run, but forces engagement. WS3/WS4 reviewers inherit the same requirement against adapted content.
- **Digit-leading skill name `2hdm-a` (A3.2):** PIN — VERIFY once in WS1 by confirming `plugins/hep-ph-toolkit/skills/_shared/` sibling directories load (they will; digit-leading is fine in marketplace.json `plugins[]` already — `hep-ph-demo` starts with `h` but `.claude-plugin/plugin.json`'s `skills[]` entries are just path+name strings). If the WS1 loader-smoke fails on `2hdm-a`, rename to `two-hdm-a` in all three locations (plugin.json, constraints.yaml, skills/dir name).
- **README section scope (A5.2):** PIN — WS5 writes/updates a `## Skills shipped` section in `plugins/hep-ph-demo/README.md` with one row per skill: `- **/<name>** — one-line description`. Current README does not have this section; WS5 creates it.
- **`/hep-plotting` reference-skill gap (R11):** PIN — WS2 Step-4 plotting paragraph includes concrete mplhep/matplotlib guidance (ATLAS style, black data points per HEP memory `feedback_data_point_color`, axis labels from `plot_axes` metadata), not just "invoke `/hep-plotting`." WS3/WS4 inherit with per-model axes.
- **Commit messages:** `W<N>: <imperative lowercase>` prefix, sub-commits `W<N>(<k>): …`, **NO `Co-Authored-By:` line** (verified absent from `git log`).
- **Multi-component combiner in `_shared/`:** BANNED. Any PR that adds `combine_multi_dm.py` or inline `f_i` math in a SKILL.md body is rejected per memory `feedback_augment_not_replace` and synthesis D2a.

---

## 2. Workstream DAG

```
    WS1 ──► WS2 ──┬──► WS3 ──┐
                  │          │
                  └──► WS4 ──┴──► WS5
```

| WS | Depends on | Parallel with | Agent |
|---|---|---|---|
| WS1 | — | — | Sonnet (physics-literate for YAMLs) |
| WS2 | WS1 | — | Sonnet |
| WS3 | WS2 | WS4 | Sonnet |
| WS4 | WS2 | WS3 | Sonnet |
| WS5 | WS3 ∧ WS4 | — | Sonnet |

**Dispatch recommendation:** `superpowers:dispatching-parallel-agents` for the WS3+WS4 pair only; WS1/WS2/WS5 are single-agent.

---

## 3. Per-workstream spec

### WS1 — Shared scaffolding + ModelSpec YAMLs + `/demo` rewrite

#### Deliverables (absolute paths)

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/time_budget.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/status_resolve.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/summary.schema.json` (NEW — pins §4 schema)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/assets/two_hdm_a.yaml` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/assets/dark_su3.yaml` (NEW, seeded from existing fixture)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/conftest.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_constraints_yaml.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_time_budget.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_summary_schema.py` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/README.md` (NEW — one-line pytest command)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (REWRITE in place)

#### Inputs (files to read first, in order)

1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/specs/2026-04-19-profumo-demo-workflow-design.md`
2. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md` (esp. §2.2, §3)
3. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (this file)
4. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (current — preserve Step 0 preflight verbatim)
5. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` (schema for YAMLs)
6. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` (seed for dark_su3.yaml)
7. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` (prose-directive precedent, lines 40, 43, 45, 129, 167)

#### Done criteria (mechanically checkable)

- [ ] `ls plugins/hep-ph-toolkit/skills/_shared/` exists and contains the 6 top-level artifacts + `assets/` + `tests/`.
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0.
- [ ] `test_constraints_yaml.py` asserts: top-level keys `schema_version`, `prereqs`, `constraints`, `models`; every prereq in `constraints.*.chain` exists in `prereqs:`; every `models.*.time_overrides` key ∈ `{relic, dd, id}`; every `models.*.multi_component_prereq` ∈ `prereqs`; every prereq has `status ∈ {exists, planned}` and `hours.cold` + `hours.cached` as 2-element lists.
- [ ] `test_time_budget.py` asserts (at minimum): `resolve("singlet-doublet", ["relic"]).rows[0].status == "READY"`; `resolve("singlet-doublet", ["dd"]).rows[0].status == "BLOCKED"` with `missing` containing `feynarts`, `formcalc`, `package-x`, `ddcalc`; `resolve("dark-su3", ["relic"]).rows[0].status == "BLOCKED"` with `missing` containing `dark-matter-constraints`; overlap totals don't double-count shared prereqs (fixture case: relic+dd with `sarah-build` shared).
- [ ] `test_summary_schema.py` asserts `summary.schema.json` is valid JSON Schema Draft 7 and validates the canonical example in §4.
- [ ] Each `_shared/assets/*.yaml` validates against `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`. Run: `python3 -c "import json, yaml, jsonschema; s=json.load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json')); jsonschema.validate(yaml.safe_load(open('plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml')), s)"` (repeat for each).
- [ ] Each YAML that is provisional carries `provisional: true` AND a `# TODO(physics):` comment. Non-provisional YAMLs have `provisional: false` and were cross-checked by reviewer against the paper.
- [ ] `demo/SKILL.md` structure, in order: frontmatter → `# Demo` + framing → `## Flow` → Step 0 Preflight (verbatim from current file) → Step 1 Intro (verbatim from synthesis §3 two-paragraph text) → Step 2 Continue/Not-now gate → Step 3 three-option model picker (verbatim JSON from synthesis §3) → Delegation line → Closing block (reads `./demo_output/<model>/summary.json`) → `## Non-goals`.
- [ ] Preflight precedes intro (order check).
- [ ] `demo/SKILL.md` frontmatter is only `name` + `description`.
- [ ] `plugin.json` UNCHANGED at this stage (new skill entries come from WS2).
- [ ] All commits use `W1:` or `W1(<k>):` prefix; no `Co-Authored-By:` line.

#### Worktree + branch

- Worktree: `../hep-ph-agents.ws1-shared`
- Branch: `ws1/shared-scaffold`
- Merge: `git checkout main && git merge --no-ff ws1/shared-scaffold`

#### Commit message template

```
W1: shared scaffolding + ModelSpec YAMLs + /demo rewrite

- _shared/constraints.yaml: prereq chains, per-prereq hours, model metadata
- _shared/time_budget.py, status_resolve.py: pure-function resolvers
- _shared/summary.schema.json: contract for per-model → /demo handoff
- _shared/assets/*.yaml: ModelSpec YAMLs for 3 Profumo benchmarks
  (dark_su3 provisional: false, seeded from existing fixture)
  (singlet_doublet, two_hdm_a: provisional: <true|false> depending on physics review)
- _shared/tests/: constraints/yaml + time_budget + summary_schema tests
- demo/SKILL.md: rewritten — Step 0 preflight → Step 1 intro → Step 2 gate
  → Step 3 model picker → delegation → closing block reads summary.json
```

Sub-commits allowed using `W1(1): …`, `W1(2): …` per repo precedent (see commit `88acd11`, `06e3787`).

#### Implementer prompt

> You are implementing WS1 of the Profumo demo redesign. **STOP before declaring done until the entire "Done criteria" checklist is green.**
>
> **Read first (absolute paths), in this order:**
> 1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/specs/2026-04-19-profumo-demo-workflow-design.md`
> 2. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md` (focus §2.2 constraints.yaml, §3 Step 1/2/3/4 verbatim scripting, §3 `/demo` intro text)
> 3. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (this plan — WS1 section and §4 schemas)
> 4. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/demo/SKILL.md` (current file — preserve Step 0 preflight)
> 5. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`
> 6. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml`
> 7. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` (prose-directive precedent)
>
> **Worktree:** `git worktree add ../hep-ph-agents.ws1-shared -b ws1/shared-scaffold main`. All work in that worktree.
>
> **Path discipline:** all new files go under `plugins/hep-ph-toolkit/skills/_shared/` (INSIDE `skills/`, matching the `plugins/hep-ph-toolkit/skills/_shared/` precedent). No top-level `_shared/`. The final plan §1.4 explains why.
>
> **Key tasks, in order:** (1) author `constraints.yaml` with per-prereq `hours: {cold, cached}` populated (not placeholder) — pull from synthesis §2.2 for chain/model content, then add a `hours:` field to each prereq entry based on synthesis default_time values amortized per prereq; (2) author `summary.schema.json` per §4 of the final plan; (3) author `time_budget.py` and `status_resolve.py` per §B.2/B.3 of the draft plan, with `resolve()` implementing per-prereq UNIQUE-union overlap (not `max+extras`); (4) write all four test files and make them green; (5) author the three ModelSpec YAMLs — dark_su3 seeds from the existing fixture (set `provisional: false` if unchanged); singlet_doublet and two_hdm_a author from arXiv:2506.19062 §II/§III; if you are not confident in the Lagrangian, ship `provisional: true` with a `# TODO(physics):` comment naming the unverified pieces; (6) rewrite `demo/SKILL.md` — PRESERVE Step 0 preflight VERBATIM from the current file, THEN Step 1 intro (synthesis §3 "`/demo` intro text", two paragraphs verbatim), THEN Step 2 gate, THEN Step 3 model picker (synthesis §3 three-option JSON verbatim), THEN delegation line: `Based on the user's choice, read and execute plugins/hep-ph-toolkit/skills/<singlet-doublet|2hdm-a|dark-su3>/SKILL.md.`, THEN closing block that reads `./demo_output/<model>/summary.json` and prints three lines (model / artifacts_dir / skipped_constraints).
>
> **DO NOT:** touch `plugin.json`; add any multi-component combiner code; invent a `Skill(...)` tool call.
>
> **Commit:** `W1:` prefix, imperative lowercase, no `Co-Authored-By:`.
>
> **STOP before declaring done** checklist:
> - [ ] Done-criteria list (§WS1 above) all ticked
> - [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green
> - [ ] Each `_shared/assets/*.yaml` validates against `modelspec.schema.json` (you ran the validator)
> - [ ] `demo/SKILL.md` order is Preflight → Intro → Gate → Picker → Delegation → Closing
> - [ ] `plugin.json` untouched
> - [ ] No `Co-Authored-By:` in any commit

#### Reviewer prompt

> You are the opus skeptic for WS1. Your output format is **APPROVED** or **CHANGES REQUESTED: <bulleted list of specific file:line demands>**.
>
> **Read:** `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` §WS1 and §4 (schemas), then the implementer's diff.
>
> **Mechanical checks (run these yourself, don't take the implementer's word):**
> 1. `ls plugins/hep-ph-toolkit/skills/_shared/` contains: constraints.yaml, time_budget.py, status_resolve.py, summary.schema.json, assets/, tests/. **Not** at top level `plugins/hep-ph-toolkit/_shared/` — reject if wrong path.
> 2. `cd /Users/yianni/Projects/hep-ph-agents && pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0.
> 3. `python3 -c "import json, yaml, jsonschema; s=json.load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json')); [jsonschema.validate(yaml.safe_load(open(f)), s) for f in ['plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml','plugins/hep-ph-toolkit/skills/_shared/assets/two_hdm_a.yaml','plugins/hep-ph-toolkit/skills/_shared/assets/dark_su3.yaml']]"` — no exception.
> 4. `grep -c "^provisional:" plugins/hep-ph-toolkit/skills/_shared/assets/*.yaml` — each file has exactly one. For any `provisional: true`, `grep "TODO(physics):"` in that file returns ≥1 hit.
> 5. `head -1 plugins/hep-ph-toolkit/skills/demo/SKILL.md` = `---` and the `## Flow` section orders Preflight BEFORE Intro (use `grep -n '### Step' plugins/hep-ph-toolkit/skills/demo/SKILL.md` and check numeric order: Step 0 preflight, Step 1 intro).
> 6. The intro text in `demo/SKILL.md` Step 1 matches synthesis §3 "`/demo` intro text" word-for-word (diff manually; must start with "Arcadi & Profumo ask:").
> 7. The Step 3 model-picker JSON in `demo/SKILL.md` matches synthesis §3 "Then the three-model picker" JSON including the three ids `singlet-doublet`, `2hdm-a`, `dark-su3` and the cold-hr ranges.
> 8. `git diff main -- plugins/hep-ph-demo/.claude-plugin/plugin.json` shows NO changes.
> 9. `git log --format=%B main..HEAD | grep -c "Co-Authored-By"` = 0.
> 10. **Physics spot-check (the hard one):** for each YAML with `provisional: false`, open arXiv:2506.19062 §II/§III/§IV (WebFetch `https://arxiv.org/abs/2506.19062`) and verify the fermion/scalar content and Lagrangian-term list matches the paper. Reject if field list is wrong, regardless of schema validity.
>
> If any check fails, emit **CHANGES REQUESTED** with exact file:line demands.

---

### WS2 — Reference per-model skill: `singlet-doublet`

#### Deliverables

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` (NEW — parametrized over ALL THREE model ids with `skip-if-missing` on each SKILL.md file path)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/.claude-plugin/plugin.json` (MODIFIED — add ALL THREE entries: `singlet-doublet`, `2hdm-a`, `dark-su3` — WS3/WS4 do NOT touch this file)

#### Inputs

1. Final plan §WS2, §1.2 (prose-directive regex), §1.3 (physics-adaptation rules), §4 (summary schema)
2. Synthesis §2.3 (body ordering) and §3 (verbatim Step 1 single-candidate variant, Step 2/3/4 scripting)
3. All WS1 artifacts in `plugins/hep-ph-toolkit/skills/_shared/`
4. `plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` — error-paths table precedent
5. `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` — prose-directive precedent

#### Done criteria

- [ ] `singlet-doublet/SKILL.md` frontmatter: `name: singlet-doublet` + `description:` only.
- [ ] Body contains, in order: `# Singlet-Doublet`, `## When to invoke`, `## Model metadata` (fenced YAML), `## Constraints and time estimates` (markdown table + `All-constraints cold total (overlap-adjusted): **X–Y hr**` line), `## Flow` (Steps 1–4), `## Error paths` (table), `## File map` (table).
- [ ] Step 1 uses the SINGLE-CANDIDATE variant from synthesis §3 (the FIRST block, not the Dark SU(3) one).
- [ ] Step 2 block contains the AskUserQuestion JSON from synthesis §3 Step 2 verbatim (ids `relic`, `dd`, `id`, `collider`; `allowMultiple: true`; `required: true`).
- [ ] Step 3 reports `relic [READY]` and `dd`, `id` as `[BLOCKED — missing: ...]` with missing lists matching `constraints.yaml`.
- [ ] Step 3 gate JSON blocks: blocked-branch ids `[run_ready, back, cancel]`; ready-branch ids `[go, back, cancel]`; both `allowMultiple: false`, `required: true`.
- [ ] Step 4 relic branch contains EXACTLY FOUR prose directives matching the regex `^>\s*Invoke\s+/[a-z0-9-]+\b`, in order: `/sarah-build` (with `plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml`), `/spheno-build` (on model `singlet_doublet`), `/madgraph` (consultation), `/maddm` (consultation).
- [ ] Step 4 MadDM paragraph is concrete: mentions `Majorana` candidate flag, `relic_density ON`, `launch`, parse of `Omega h^2`; length 40–60 lines.
- [ ] Step 4 plotting paragraph embeds concrete mplhep guidance (ATLAS style, black data points, axes from `plot_axes`).
- [ ] At Step 4 end (or on `Cancel`), SKILL.md tells Claude to write `./demo_output/singlet-doublet/summary.json` conforming to `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json`. The literal path string appears in the SKILL.md body.
- [ ] `plugin.json` `skills[]` now contains 5 entries: existing `install`, `demo`, plus new `singlet-doublet`, `2hdm-a`, `dark-su3` (in that canonical order). The WS3/WS4 SKILL.md files don't exist yet — that's fine, plugin.json is forward-declarative.
- [ ] `test_skill_structure.py` is parametrized over `SKILLS = ["singlet-doublet", "2hdm-a", "dark-su3"]` with `@pytest.mark.skipif(not SKILL_MD_EXISTS)` on each; passes (skips 2hdm-a and dark-su3 for now; fully asserts singlet-doublet).
- [ ] Assertions in `test_skill_structure.py`: (a) `## Model metadata` YAML block agrees with `constraints.yaml` `models.<id>` on ALL keys (display, dm_candidates, plot_axes, multi_component, multi_component_prereq, time_overrides); (b) Step 2 JSON parses and has exact ids/flags; (c) Step 3 gate JSONs parse with exact branch ids; (d) Step 4 relic branch has exactly 4 prose directives per regex; (e) `All-constraints cold total` line value matches `time_budget.resolve(<id>, all).overlap_totals.cold_all` within 0.5hr; (f) SKILL.md body contains literal string `demo_output/singlet-doublet/summary.json`.
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green.
- [ ] Commits use `W2:` prefix; no `Co-Authored-By:`.

#### Worktree + branch

- Worktree: `../hep-ph-agents.ws2-singlet-doublet`
- Branch: `ws2/singlet-doublet`

#### Commit message template

```
W2: singlet-doublet per-model skill + parametrized structure test

- skills/singlet-doublet/SKILL.md: 7-section body, Step 4 relic branch
  with 4 prose directives (/sarah-build → /spheno-build → /madgraph → /maddm)
- skills/_shared/tests/test_skill_structure.py: parametrized over 3 model
  ids with skip-if-missing (WS3/WS4 add files, not test wiring)
- .claude-plugin/plugin.json: forward-declare all 3 per-model skills
```

#### Implementer prompt

> You are implementing WS2 of the Profumo demo redesign. WS1 is merged and frozen. **STOP before declaring done until every item in Done criteria is ticked.**
>
> **Read first (absolute paths):**
> 1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (§WS2, §1.2 prose-directive regex, §4 summary schema)
> 2. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md` (§2.3 body ordering; §3 Step 1/2/3/4 scripting — use SINGLE-CANDIDATE variant of Step 1)
> 3. All files under `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/` (frozen WS1 output)
> 4. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` (prose directives at lines 40, 43, 45, 129, 167)
> 5. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` (error-paths table style)
>
> **Worktree:** `git worktree add ../hep-ph-agents.ws2-singlet-doublet -b ws2/singlet-doublet main`. Work there.
>
> **Deliverables:** three files — `skills/singlet-doublet/SKILL.md`, `skills/_shared/tests/test_skill_structure.py` (parametrized over all three model ids, skip-if-missing), and `.claude-plugin/plugin.json` (add ALL THREE per-model entries — forward-declare WS3/WS4; they will NOT touch this file).
>
> **Prose-directive definition:** a markdown blockquote line (starts with `> `) whose first non-whitespace word is `Invoke` followed by `/<skill-name>`. Regex: `^>\s*Invoke\s+/[a-z0-9-]+\b`. The relic branch of Step 4 must contain EXACTLY FOUR such lines, in this order: `/sarah-build`, `/spheno-build`, `/madgraph`, `/maddm`.
>
> **MadDM guidance (critical, R4):** the Step-4 MadDM paragraph must be concrete enough that another Sonnet reading only this SKILL.md + the `/madgraph`/`/maddm` reference SKILL.md files could drive an MG5 session to produce `Omega h²` for `chi1`. At minimum: mention Majorana candidate flag, which card sections to edit, `relic_density ON`, `launch`, output parse from MadDM scan directory. Target 40–60 lines.
>
> **Plot guidance (R11):** Step-4 `/hep-plotting` block must embed concrete mplhep guidance: ATLAS style, black data points (per memory `feedback_data_point_color`), axes from `plot_axes` metadata (`m_chi`, `sin_2theta` for this model).
>
> **summary.json contract (§4 of final plan):** at end of Step 4 or on `Cancel`, write `./demo_output/singlet-doublet/summary.json` conforming to `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json`. The literal path string must appear in the SKILL.md body.
>
> **DO NOT:** invent `Skill(...)` calls; copy-paste MadDM guidance that will be shared with WS3/WS4 verbatim (they adapt; you write the Majorana-DM-via-Higgs-portal form); add multi-component combiner logic.
>
> **Commit:** `W2:` prefix.
>
> **STOP before declaring done:**
> - [ ] All 14 Done-criteria items for WS2 ticked
> - [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green (test_skill_structure.py passes the singlet-doublet case; skips 2hdm-a and dark-su3)
> - [ ] Regex `^>\s*Invoke\s+/[a-z0-9-]+\b` matches EXACTLY 4 lines in the Step-4 relic branch
> - [ ] `plugin.json` has all 5 skill entries in canonical order
> - [ ] No `Co-Authored-By:` in commits

#### Reviewer prompt

> You are the opus skeptic for WS2. Output format: **APPROVED** or **CHANGES REQUESTED: <bullets>**.
>
> **Read:** final plan §WS2, §1.2 (prose-directive regex), §1.3 (adaptation is REQUIRED for WS3/4 — your job here is WS2, but remember the template will be adapted), §4 (summary schema). Then the diff.
>
> **Mechanical checks:**
> 1. `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0.
> 2. `grep -cE '^>\s*Invoke\s+/[a-z0-9-]+' plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` ≥ 4; `awk` the Step-4 relic subsection and confirm EXACTLY 4 there, in order `/sarah-build, /spheno-build, /madgraph, /maddm`.
> 3. `grep -c "demo_output/singlet-doublet/summary.json" plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` ≥ 1.
> 4. `python3 -c "import json; p='plugins/hep-ph-demo/.claude-plugin/plugin.json'; d=json.load(open(p)); names=[s['name'] for s in d['skills']]; assert names==['install','demo','singlet-doublet','2hdm-a','dark-su3'], names"` passes.
> 5. `grep -n '^### Step' plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` lists Steps 1, 2, 3, 4 in order under a `## Flow` section.
> 6. Step 1 text (grep the Step 1 block) is the SINGLE-candidate variant (mentions "single-candidate model"), not the Dark SU(3) multi-candidate text.
> 7. The MadDM paragraph (Step 4) mentions: `Majorana`, `relic_density`, `launch`, `Omega`. Count ≥4 matches for these tokens.
> 8. The Step-4 plotting block mentions `mplhep`, `ATLAS`, and `black` (data points).
> 9. `git log main..HEAD --format=%B | grep -c 'Co-Authored-By'` = 0.
> 10. **Tractability attestation (per §1.6 A2.2):** in your review comment, write 3 sentences stating whether another Sonnet could drive MG5 from the Step-4 MadDM paragraph alone. If you can't, request changes.
>
> If ANY fails, emit **CHANGES REQUESTED** with file:line demands.

---

### WS3 — `2hdm-a` per-model skill (parallel with WS4)

#### Deliverables

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` (NEW)

**WS3 does NOT touch** `plugin.json` (WS2 forward-declared) or `test_skill_structure.py` (WS2 parametrized).

#### Inputs

1. Final plan §WS3, §1.3 (**physics adaptation is required**)
2. `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (frozen WS2 template)
3. `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (`models.2hdm-a` section from WS1)
4. `plugins/hep-ph-toolkit/skills/_shared/assets/two_hdm_a.yaml` (from WS1)
5. arXiv:2506.19062 §III (2HDM+a Lagrangian, CP-odd mediator phenomenology)

#### Done criteria

- [ ] `skills/2hdm-a/SKILL.md` exists, has same 7 sections in same order as `singlet-doublet/SKILL.md`.
- [ ] Structural diff with singlet-doublet is confined to: title/hook wording, DM candidate name (`chi`), `plot_axes` (`m_a`, `tan_beta`), time overrides.
- [ ] **Physics adaptation (critical):** Step-4 MadDM paragraph mentions `Dirac`, `CP-odd`, `loop-only`, `a-resonance`, `tan β`. ALL FIVE words appear. Text is NOT verbatim-copied from WS2.
- [ ] Step-4 DD discussion explicitly notes `σ_SI_tree ≈ 0` (CP-forbidden) and that loop-level DD is the primary signal — blocked on `/feynarts`, `/formcalc`, `/package-x`, `/ddcalc`.
- [ ] Step 1 uses SINGLE-candidate variant with `chi` as the DM name.
- [ ] Step 3 reports `relic [READY]`; `dd [BLOCKED]` (loop subchain); `id [BLOCKED]` (`/gamlike`). Chain annotations match `constraints.yaml`.
- [ ] Step-4 relic branch has exactly 4 prose directives (regex match).
- [ ] SKILL.md tells Claude to write `./demo_output/2hdm-a/summary.json`.
- [ ] `test_skill_structure.py` now asserts 2hdm-a (skip guard lifts because file exists) + continues to assert singlet-doublet.
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green.
- [ ] Commits use `W3:` prefix; no `Co-Authored-By:`.

#### Worktree + branch

- Worktree: `../hep-ph-agents.ws3-2hdm-a`
- Branch: `ws3/2hdm-a`

#### Commit message template

```
W3: 2hdm-a per-model skill — Dirac DM via pseudoscalar mediator

- skills/2hdm-a/SKILL.md: adapted from singlet-doublet template
  MadDM guidance rewritten for Dirac + CP-odd mediator:
    loop-only DD (tree CP-forbidden), a-resonance relic,
    tan-beta dependence
- Step-4 chains: relic READY; dd/id BLOCKED (loop subchain, gamlike)
```

#### Implementer prompt

> You are implementing WS3 of the Profumo demo redesign. **WS4 is being implemented in parallel** by a peer agent on the `dark-su3` skill — do NOT touch `plugins/hep-ph-toolkit/skills/dark-su3/` or any file outside `plugins/hep-ph-toolkit/skills/2hdm-a/`.
>
> **STOP before declaring done until every Done-criteria item is ticked.**
>
> **Read first:**
> 1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (§WS3, §1.2 prose-directive regex, **§1.3 physics adaptation — the adaptation is REQUIRED, not optional**)
> 2. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (frozen WS2 template)
> 3. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` — `models.2hdm-a`
> 4. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/assets/two_hdm_a.yaml`
> 5. arXiv:2506.19062 §III (WebFetch `https://arxiv.org/abs/2506.19062` and read Section III)
>
> **Worktree:** `git worktree add ../hep-ph-agents.ws3-2hdm-a -b ws3/2hdm-a main`. Work there.
>
> **Mechanical template mapping:** same 7 sections in same order as WS2's singlet-doublet SKILL.md. Structural changes limited to: title/hook, DM candidate name `chi` (Dirac), plot axes `(m_a, tan_beta)`, time overrides (per `constraints.yaml` `models.2hdm-a.time_overrides`).
>
> **PHYSICS ADAPTATION IS REQUIRED — DO NOT COPY-PASTE MadDM GUIDANCE FROM WS2.** The 2HDM+a's DM phenomenology is fundamentally different from singlet-doublet's:
> - **Dirac** DM candidate (not Majorana) → different MadDM candidate flag.
> - Mediator is **CP-odd pseudoscalar `a`** → annihilation goes through s-channel `a`, with `tan β`-dependent strength.
> - **Tree SI is CP-forbidden (`σ_SI_tree ≈ 0`)** → direct detection is a **loop-only** signal, hence why `/feynarts`, `/formcalc`, `/package-x` are on the critical path.
> - Relic region has `a`-resonance features distinct from t-channel mediator physics.
>
> Your Step-4 MadDM paragraph MUST contain the words `Dirac`, `CP-odd`, `loop-only`, `a-resonance`, `tan β` (or `tan_beta`). Your Step-4 DD discussion MUST state `σ_SI_tree ≈ 0` (or equivalent) and name the loop subchain. Reviewer will reject if any of these words is missing.
>
> **DO NOT:** touch `plugin.json` (WS2 forward-declared — your entry is already there); touch `test_skill_structure.py` (WS2 parametrized — your entry is already there); add multi-component combiner logic; copy the MadDM block from WS2 verbatim.
>
> **Commit:** `W3:` prefix.
>
> **STOP before declaring done:**
> - [ ] All 10 Done-criteria items for WS3 ticked
> - [ ] `grep -E "(Dirac|CP-odd|loop-only|a-resonance|tan.?β|tan_beta)" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` shows all 5 matched
> - [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green
> - [ ] `plugin.json` untouched vs main
> - [ ] `test_skill_structure.py` untouched vs main

#### Reviewer prompt

> Opus skeptic for WS3. Output: **APPROVED** or **CHANGES REQUESTED: <bullets>**.
>
> **Read:** final plan §WS3, §1.3 (physics adaptation words-required list), §1.2 (prose-directive regex). Then the diff.
>
> **Mechanical checks:**
> 1. `diff -u plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` — structural differences limited to title/hook, `chi`, `(m_a, tan_beta)`, time overrides. Section order and heading list identical.
> 2. `grep -c "Dirac" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 3. `grep -c "CP-odd" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 4. `grep -c "loop-only" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 5. `grep -Ec "a-resonance|a resonance" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 6. `grep -Ec "tan.?β|tan_beta|tan beta" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 7. `grep -Ec "σ_SI.*≈ 0|sigma_SI.*tree.*zero|CP-forbidden" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 8. Step-4 relic branch has exactly 4 prose directives (`awk` the relic sub-section, regex `^>\s*Invoke\s+/`).
> 9. `grep -c "demo_output/2hdm-a/summary.json" plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ≥ 1.
> 10. `git diff main -- plugins/hep-ph-demo/.claude-plugin/plugin.json plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` shows NO changes to either file (WS3 must not touch them).
> 11. `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green.
> 12. **Anti-copy-paste check:** pull the MadDM paragraph from WS2's SKILL.md and diff against WS3's MadDM paragraph. If the diff is trivially-small or the physics words (#2–#7) are absent, REJECT.
> 13. `git log main..HEAD --format=%B | grep -c 'Co-Authored-By'` = 0.
>
> On any fail, emit **CHANGES REQUESTED** with file:line demands.

---

### WS4 — `dark-su3` per-model skill (parallel with WS3)

#### Deliverables

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` (NEW)

**WS4 does NOT touch** `plugin.json` or `test_skill_structure.py` (both forward-declared by WS2).

#### Inputs

1. Final plan §WS4, §1.3 (physics adaptation required; **NO inline combination math**)
2. `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (frozen template)
3. `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` — `models.dark-su3`
4. `plugins/hep-ph-toolkit/skills/_shared/assets/dark_su3.yaml`
5. arXiv:2506.19062 §IV
6. Synthesis §3 **multi-candidate variant** of Step 1 (the block after "Multi-candidate skill (`dark-su3`):")
7. Memory `feedback_augment_not_replace` (re-read before writing Step 4 body)

#### Done criteria

- [ ] `skills/dark-su3/SKILL.md` exists, same 7 sections in same order as template.
- [ ] Step 1 uses the MULTI-CANDIDATE variant from synthesis §3 (two bullets: `phi` and `V`; explicit `f_i` combination paragraph pointing at `/dark-matter-constraints [PLANNED]`).
- [ ] `multi_component: true` in `## Model metadata` block; `multi_component_prereq: dark-matter-constraints` present.
- [ ] **Physics adaptation words required:** `scalar dark pion`, `vector dark meson`, `blind spot`, `confining`, `multi-component` all appear in the SKILL.md body.
- [ ] Step 3 shows ALL THREE constraints as `[BLOCKED]`, each chain appends `/dark-matter-constraints [PLANNED]`.
- [ ] Blocked-branch `AskUserQuestion` fires. If user picks `run_ready` with zero ready constraints, skill prints `"No selected constraints are currently runnable. Re-select constraints or Cancel."` and loops back to Step 2.
- [ ] Step 4 body documents the N=2 execution path in ONE paragraph pointing at `/dark-matter-constraints [PLANNED]` — **NO inline `f_i` combination math**. No formulas beyond naming the combination rule by reference (e.g., "DD rates combine linearly in `f_i`; ID rates in `f_i²` — see `/dark-matter-constraints`"). Any derivation is a REJECT.
- [ ] Scalar `phi` blind-spot paragraph cites the EXACT parameter-independent cancellation (not a tuned blind spot).
- [ ] Vector `V` paragraph mentions the resonance region (paper Fig. 8).
- [ ] SKILL.md tells Claude to write `./demo_output/dark-su3/summary.json` (on cancel, no write).
- [ ] `test_skill_structure.py` now asserts dark-su3 (skip guard lifts).
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green.
- [ ] Commits use `W4:` prefix; no `Co-Authored-By:`.

#### Worktree + branch

- Worktree: `../hep-ph-agents.ws4-dark-su3`
- Branch: `ws4/dark-su3`

#### Commit message template

```
W4: dark-su3 per-model skill — multi-component DM, all-blocked UX

- skills/dark-su3/SKILL.md: multi-candidate (phi scalar + V vector)
  Step 3 surfaces all 3 constraints as [BLOCKED] on
  /dark-matter-constraints [PLANNED] (per augment_not_replace)
  Step 4 documents N=2 path by reference only; no inline f_i math
  Blind-spot discussion: exact parameter-independent cancellation (phi);
  resonance region for V (paper Fig. 8)
```

#### Implementer prompt

> You are implementing WS4 of the Profumo demo redesign. **WS3 is being implemented in parallel** by a peer agent on the `2hdm-a` skill — do NOT touch `plugins/hep-ph-toolkit/skills/2hdm-a/` or any file outside `plugins/hep-ph-toolkit/skills/dark-su3/`.
>
> **STOP before declaring done until every Done-criteria item is ticked.**
>
> **Read first:**
> 1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (§WS4, **§1.3 physics adaptation — required and has a NO-MATH rule for Step 4**)
> 2. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/brainstorm/03-synthesis.md` (§3 Step 1 **multi-candidate variant** — the block labeled "Multi-candidate skill (`dark-su3`):")
> 3. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` (frozen template — same 7 sections, you adapt)
> 4. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` — `models.dark-su3`
> 5. `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/assets/dark_su3.yaml`
> 6. arXiv:2506.19062 §IV (WebFetch `https://arxiv.org/abs/2506.19062` §IV)
> 7. The memory `feedback_augment_not_replace` — re-read before writing Step 4.
>
> **Worktree:** `git worktree add ../hep-ph-agents.ws4-dark-su3 -b ws4/dark-su3 main`. Work there.
>
> **Physics adaptation is REQUIRED.** Do NOT copy WS2's MadDM guidance. Dark SU(3) is a **confining dark sector with two DM candidates**:
> - `phi` — **scalar dark pion**; the SI blind spot is EXACT and parameter-INDEPENDENT (not a tuned cancellation).
> - `V` — **vector dark meson**; tree SI is non-zero; features a **resonance region** per the paper Fig. 8.
> - The sector is **confining**; SARAH models composite states via an HLS-like Lagrangian.
> - This is a **multi-component** model. Constraint combination uses `f_i = Ω_i / Ω_tot` weights.
>
> Your SKILL.md body MUST contain the words `scalar dark pion`, `vector dark meson`, `blind spot`, `confining`, `multi-component`. Reviewer rejects if any missing.
>
> **CRITICAL NO-MATH RULE (per augment_not_replace + §1.3):** Step 4 documents the N=2 execution path in ONE paragraph at most. **Do NOT derive the `f_i` combination formula in the SKILL.md body.** One sentence is enough: `"DD rates combine linearly in f_i; ID rates in f_i² — see /dark-matter-constraints [PLANNED]."` Anything more (writing out `Σ f_i σ_i`, halo-distribution assumptions, coherence discussion) is grounds for immediate rejection. Physics decisions belong in the future `/dark-matter-constraints` meta-skill, not in this SKILL.md.
>
> **Blocked-UX:** every chain in Step 3 appends `/dark-matter-constraints [PLANNED]`, so all three constraints surface as `[BLOCKED]`. Blocked-branch gate fires. If user picks `run_ready` when zero ready constraints exist, print `"No selected constraints are currently runnable. Re-select constraints or Cancel."` and loop back to Step 2.
>
> **DO NOT:** touch `plugin.json`; touch `test_skill_structure.py`; copy WS2's MadDM block verbatim; add any `f_i` derivation or inline combination code; add a `combine_multi_dm.py` anywhere.
>
> **Commit:** `W4:` prefix.
>
> **STOP before declaring done:**
> - [ ] All 12 Done-criteria items for WS4 ticked
> - [ ] `grep -E "(scalar dark pion|vector dark meson|blind spot|confining|multi-component)" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` shows all 5 matched
> - [ ] No `f_i` formula derivation beyond a single pointer sentence
> - [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green
> - [ ] `plugin.json` and `test_skill_structure.py` untouched vs main

#### Reviewer prompt

> Opus skeptic for WS4. Output: **APPROVED** or **CHANGES REQUESTED: <bullets>**.
>
> **Read:** final plan §WS4, **§1.3 physics-adaptation list + no-inline-math rule**, synthesis §3 multi-candidate variant, memory `feedback_augment_not_replace`. Then the diff.
>
> **Mechanical checks:**
> 1. `grep -c "scalar dark pion" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 2. `grep -c "vector dark meson" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 3. `grep -ci "blind spot" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 4. `grep -ci "confining" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 5. `grep -ci "multi-component" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 6. **Anti-inline-math check:** search for patterns that indicate inline combination derivation — `grep -cE "Σ|\\sum|Ω_tot|f_i\\s*=|n_i\\^2|halo"` `plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` should be ≤ 3 (allow the Step 1 multi-candidate paragraph's one use of each, nothing more). If higher, open the file and reject inline derivations.
> 7. **NO new Python files:** `git diff main --stat | grep -E "\.py$"` should show NO .py files touched under `_shared/`. If a `combine_multi_dm.py` or similar appeared, hard-reject per memory `feedback_augment_not_replace`.
> 8. `grep -c "dark-matter-constraints" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 3 (appears in every chain).
> 9. Step 3 blocked-branch message "No selected constraints are currently runnable" is present — `grep -c "No selected constraints are currently runnable"` ≥ 1.
> 10. `grep -c "demo_output/dark-su3/summary.json" plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` ≥ 1.
> 11. `git diff main -- plugins/hep-ph-demo/.claude-plugin/plugin.json plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` shows NO changes.
> 12. `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green.
> 13. `git log main..HEAD --format=%B | grep -c 'Co-Authored-By'` = 0.
>
> Any fail → **CHANGES REQUESTED** with file:line demands.

---

### WS5 — Polish: lift test skip guards, manual walkthrough, README

#### Deliverables

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` (MODIFIED — remove `@skipif` guards so all three parametrized cases run unconditionally)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md` (NEW)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/README.md` (MODIFIED — add `## Skills shipped` section)

#### Inputs

1. Final plan §WS5
2. All three per-model SKILL.md files (merged state on main)
3. Current `plugins/hep-ph-demo/README.md`

#### Done criteria

- [ ] `test_skill_structure.py` no longer has `skipif` guards on the parametrized cases; all three run unconditionally.
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0 with all three parametrized cases PASSED (not skipped).
- [ ] `MANUAL_WALKTHROUGH.md` exists and contains: (a) preamble specifying the exact Claude invocation (`claude` at repo root, ensure `~/.config/hep-ph-agents/config.json` exists with dummy paths — the walkthrough's concern is conversation flow, not real SARAH runs), (b) 5-step scripted dry-run (invoke `/demo` → Continue → pick Singlet-Doublet → select relic+DD → see `dd [BLOCKED]` → pick `run_ready` → observe first prose directive `/sarah-build`), (c) expected vs observed column for each step, (d) implementer's observations appended at the bottom, (e) any mismatch escalated as a follow-up issue or fixed before WS5 merges.
- [ ] README `## Skills shipped` section lists all 5 skills: `install`, `demo`, `singlet-doublet`, `2hdm-a`, `dark-su3`, each with one-line description, plus a link to `MANUAL_WALKTHROUGH.md`.
- [ ] Commits use `W5:` prefix; no `Co-Authored-By:`.

#### Worktree + branch

- Worktree: `../hep-ph-agents.ws5-polish`
- Branch: `ws5/polish`

#### Commit message template

```
W5: structural-test finalization + manual walkthrough + README

- _shared/tests/test_skill_structure.py: remove skip-if-missing guards;
  all three per-model skills now asserted unconditionally
- _shared/tests/MANUAL_WALKTHROUGH.md: 5-minute scripted /demo dry-run
  with expected/observed columns; executed end-to-end
- README.md: add ## Skills shipped section (5 skills) + walkthrough link
```

#### Implementer prompt

> You are implementing WS5 (final) of the Profumo demo redesign. WS3 and WS4 are merged. **STOP before declaring done until every item in Done criteria is ticked.**
>
> **Read first:**
> 1. `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/workstream-shift-manager/plan/03-final-plan.md` (§WS5)
> 2. All three merged per-model SKILL.md files in `plugins/hep-ph-toolkit/skills/{singlet-doublet,2hdm-a,dark-su3}/SKILL.md`
> 3. Current `plugins/hep-ph-demo/README.md`
>
> **Worktree:** `git worktree add ../hep-ph-agents.ws5-polish -b ws5/polish main`. Work there.
>
> **Tasks:**
> 1. Edit `plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py`: remove the `@pytest.mark.skipif(not SKILL_MD_EXISTS)` guards on the parametrized cases so all three run unconditionally. Run pytest — all 3 must pass, none skipped.
> 2. Author `plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md`. Preamble: "Prereq: `~/.config/hep-ph-agents/config.json` must exist. If not, write one with dummy paths (`{\"madgraph_path\": \"/tmp/mg5\", ...}`). This walkthrough tests conversation flow, not real SARAH runs." Five-step script: (i) invoke `/demo`, expect Step 0 preflight pass + intro + Continue gate; (ii) pick Continue, expect model picker with 3 options; (iii) pick `singlet-doublet`, expect handoff + per-model Step 1 candidate text; (iv) select `relic` and `dd`, expect Step 3 showing `relic [READY]`, `dd [BLOCKED — missing: /feynarts, /formcalc, /package-x, /ddcalc]`; (v) pick `run_ready`, expect first prose directive `> Invoke /sarah-build with plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml`. Execute the walkthrough end-to-end yourself; append an "Observed:" block under each step with exact output quotes. If any step deviates materially from expected, file a follow-up issue at the bottom of the doc and cc the WS in charge of the affected skill; if the deviation is trivial (wording), fix it in this worktree.
> 3. Edit `plugins/hep-ph-demo/README.md`: add a `## Skills shipped` section (before any existing "Getting started" section, or at end if none). Format:
>    ```
>    ## Skills shipped
>    - **/install** — auto-detects or installs MadGraph, SARAH, SPheno, Wolfram Engine; writes config.json.
>    - **/demo** — interactive front door to the Profumo blind-spot demo; routes to a per-model skill.
>    - **/singlet-doublet** — constraint-first workflow for Singlet-Doublet fermion DM (§II).
>    - **/2hdm-a** — constraint-first workflow for 2HDM + pseudoscalar mediator (§III).
>    - **/dark-su3** — constraint-first workflow for Dark SU(3) multi-component DM (§IV).
>
>    See `skills/_shared/tests/MANUAL_WALKTHROUGH.md` for a scripted dry-run.
>    ```
>
> **DO NOT:** add new Python tests (scope creep); modify SKILL.md files beyond wording fixes flagged by the walkthrough.
>
> **Commit:** `W5:` prefix.
>
> **STOP before declaring done:**
> - [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` green, 0 skipped
> - [ ] `MANUAL_WALKTHROUGH.md` has "Observed:" blocks filled from your actual dry-run
> - [ ] README `## Skills shipped` section present with 5 entries
> - [ ] No `Co-Authored-By:` in commits

#### Reviewer prompt

> Opus skeptic for WS5. Output: **APPROVED** or **CHANGES REQUESTED: <bullets>**.
>
> **Read:** final plan §WS5. Then the diff.
>
> **Mechanical checks:**
> 1. `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0; output shows 3 parametrized cases for `test_skill_structure.py`, ALL PASSED (zero skipped).
> 2. `grep -c "skipif" plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` == 0.
> 3. `grep -c "Observed:" plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md` ≥ 5 (one per step).
> 4. `grep -c "## Skills shipped" plugins/hep-ph-demo/README.md` ≥ 1; section contains bullet rows for `/install`, `/demo`, `/singlet-doublet`, `/2hdm-a`, `/dark-su3`.
> 5. `grep -c "MANUAL_WALKTHROUGH" plugins/hep-ph-demo/README.md` ≥ 1.
> 6. **Anti-template-fill check:** spot-read 2 random "Observed:" blocks — they must contain specific output quotes, not generic "looks good." If either is < 2 lines or has no quoted string, REJECT.
> 7. `git log main..HEAD --format=%B | grep -c 'Co-Authored-By'` = 0.
>
> Any fail → **CHANGES REQUESTED** with file:line demands.

---

## 4. Cross-file schema contracts

### 4.1 `summary.json` schema (pinned by WS1, consumed by `/demo` Closing + emitted by each per-model Step 4)

File: `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json` (JSON Schema Draft 7)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "hep-ph-demo per-model summary",
  "type": "object",
  "required": ["model", "run_at", "ran", "skipped_constraints", "artifacts_dir", "headline"],
  "additionalProperties": false,
  "properties": {
    "model":       {"type": "string", "enum": ["singlet-doublet", "2hdm-a", "dark-su3"]},
    "run_at":      {"type": "string", "format": "date-time"},
    "ran":         {"type": "array", "items": {"type": "string", "enum": ["relic", "dd", "id"]}, "uniqueItems": true},
    "skipped_constraints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "reason"],
        "additionalProperties": false,
        "properties": {
          "id":     {"type": "string", "enum": ["relic", "dd", "id", "collider"]},
          "reason": {"type": "string"}
        }
      }
    },
    "artifacts_dir": {"type": "string"},
    "headline":      {"type": "string"}
  }
}
```

Canonical example (used by `test_summary_schema.py`):

```json
{
  "model": "singlet-doublet",
  "run_at": "2026-04-19T14:23:00Z",
  "ran": ["relic"],
  "skipped_constraints": [
    {"id": "dd", "reason": "blocked on /feynarts, /formcalc, /package-x, /ddcalc"},
    {"id": "id", "reason": "blocked on /gamlike"}
  ],
  "artifacts_dir": "./demo_output/singlet-doublet/",
  "headline": "Relic computed at 3 benchmark points; DD/ID skipped."
}
```

### 4.2 `constraints.yaml` schema (pinned by WS1, consumed by all per-model skills + tests)

File: `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml`. Top-level keys:

- `schema_version: 1` (int)
- `prereqs:` — map of `skill-name → {status: "exists"|"planned", hours: {cold: [float, float], cached: [float, float]}}`. The `hours` entries are REQUIRED (resolves critique A1.3).
- `constraints:` — map of constraint-id ∈ `{relic, dd, id, collider}` → object:
  - For `relic/dd/id`: `{chain: [prereq-name, ...], default_time: {cold: [float, float], cached: [float, float]}}`
  - For `collider`: `{chain: [], placeholder: true, message: str}`
- `models:` — map of model-id ∈ `{singlet-doublet, 2hdm-a, dark-su3}` → object:
  - `display: {title: str, hook: str}`
  - `dm_candidates: [{name: str, spin: str, notes: str}, ...]`
  - `plot_axes: {x: {symbol: str, range: [float, float], units: str?, scale: "linear"|"log"}, y: {symbol: str, range: [float, float], units: str?, scale: "linear"|"log"}}`
  - `multi_component: bool`
  - `multi_component_prereq: str?` (OPTIONAL, only when `multi_component: true`)
  - `time_overrides: {constraint-id: {cold: [float, float], cached?: [float, float]}, ...}`

### 4.3 Per-model SKILL.md `## Model metadata` YAML block schema

Inside each per-model SKILL.md, a fenced YAML block under `## Model metadata` duplicates the `models.<id>` section of `constraints.yaml`. Required keys MUST match EXACTLY (`test_skill_structure.py` asserts full agreement, not a subset — resolves critique CX.4): `display`, `dm_candidates`, `plot_axes`, `multi_component`, `multi_component_prereq` (if present), `time_overrides`.

### 4.4 Prose-directive syntax (pinned by §1.2)

- Regex: `^>\s*Invoke\s+/[a-z0-9-]+\b`
- Counted per Step-4 sub-branch (relic / dd / id).
- Relic branch: EXACTLY 4 matches, in order `/sarah-build, /spheno-build, /madgraph, /maddm`.
- Plot invocation lives outside the count (after all selected constraints).

### 4.5 Commit message convention

- Top-level: `W<N>: <imperative lowercase summary>`
- Sub-commits: `W<N>(<k>): <imperative lowercase summary>`
- No `Co-Authored-By:` lines in any commit (verified absent from `git log`).

---

## 5. Integration sequence

1. **WS1 merges first.** `git checkout main && git merge --no-ff ws1/shared-scaffold`. Tag commit with `W1:` prefix. Verify `pytest plugins/hep-ph-toolkit/skills/_shared/tests/` still green on main.
2. **WS2 merges next.** `git merge --no-ff ws2/singlet-doublet`. After merge: `plugin.json` on main contains all 5 skills (2 old + 3 forward-declared); `test_skill_structure.py` is parametrized over all 3 with 2 skipped. `pytest` green. Canonical manual smoke: invoke `/singlet-doublet` in a fresh Claude session, walk through to Step 4 first prose directive.
3. **WS3 and WS4 develop in parallel** (different worktrees, disjoint directories, both skip `plugin.json` and `test_skill_structure.py`). Merge order does not matter; both are trivial merges. After both: `pytest` passes singlet-doublet + 2hdm-a + dark-su3 cases (0 skipped on test_skill_structure? — still 0 because WS5 hasn't lifted guards yet; but the guards auto-unskip when the SKILL.md file appears, so the tests DO run. This is the whole point of the skip-if-missing design).
4. **WS5 merges last.** Removes skip guards (defensive-only at this point — the files exist so skips auto-lift), adds `MANUAL_WALKTHROUGH.md`, updates README.

**No separate glue commit needed.** README update is bundled into `W5:`.

**Post-integration manual smoke (shift manager runs after WS5 merges):**

```bash
# 1. Full test suite
cd /Users/yianni/Projects/hep-ph-agents
pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v
# Expect: 4 test files green, 0 skipped, 0 failed.

# 2. Schema validation of all three YAMLs
python3 -c "import json, yaml, jsonschema
s = json.load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json'))
for p in ['singlet_doublet','two_hdm_a','dark_su3']:
    jsonschema.validate(yaml.safe_load(open(f'plugins/hep-ph-toolkit/skills/_shared/assets/{p}.yaml')), s)
print('ok')"

# 3. plugin.json sanity
python3 -c "import json
d = json.load(open('plugins/hep-ph-demo/.claude-plugin/plugin.json'))
assert [s['name'] for s in d['skills']] == ['install','demo','singlet-doublet','2hdm-a','dark-su3']
print('ok')"

# 4. Execute MANUAL_WALKTHROUGH.md top to bottom in a fresh claude session
```

---

## 6. Risks + mitigations + owners

| # | Risk | Mitigation | Owner |
|---|---|---|---|
| R1 | `_shared/` at `skills/_shared/` is wrong | Matches `plugins/hep-ph-toolkit/skills/_shared/` precedent — verified. No mitigation needed. | — |
| R2 | ModelSpec physics-wrong while schema-valid | `provisional: true|false` field + `# TODO(physics):` comment + WS1 reviewer cross-check against arXiv:2506.19062 | WS1 reviewer |
| R3 | WS3/WS4 copy-paste MadDM guidance | §1.3 word-required lists + reviewer regex checks | WS3/WS4 reviewers |
| R4 | WS4 inline `f_i` math in SKILL.md | Explicit "no derivation beyond pointer sentence" rule + reviewer grep for `Σ`/`sum`/`f_i =` | WS4 reviewer |
| R5 | summary.json schema drift between WS1 reader and WS2/3/4 writers | Schema pinned in WS1 `summary.schema.json` + `test_summary_schema.py` | WS1; enforced by per-model reviewers |
| R6 | plugin.json merge conflict between WS3/WS4 | WS2 forward-declares all 3 entries; WS3/WS4 don't touch file | WS3/WS4 implementers |
| R7 | test_skill_structure.py merge conflict | WS2 ships parametrized-over-all-3 with skip-if-missing; WS3/WS4 don't touch test | WS3/WS4 implementers |
| R8 | MadDM guidance too terse to be tractable | 40–60 line target + reviewer 3-sentence attestation | WS2/3/4 reviewers |
| R9 | `/demo` reader breaks on missing summary.json | Closing block degrades to `"<model> interview was cancelled."` on missing file | WS1 implementer |
| R10 | `2hdm-a` digit-leading directory name rejected by loader | WS1 loader-smoke by checking existing `plugins/hep-ph-toolkit/skills/_shared/` loads; fallback rename to `two-hdm-a` across `plugin.json`, `constraints.yaml`, and skills/dir | WS1 implementer |
| R11 | `/hep-plotting` is reference-only — vague plotting in Step 4 | Step 4 plotting paragraph carries concrete mplhep/ATLAS/black-points guidance per memory `feedback_data_point_color` | WS2 implementer; inherited by WS3/WS4 |
| R12 | Markdown JSON-block parsing is brittle | test_skill_structure.py uses `json.loads` on extracted fenced blocks with explicit error messages | WS2 implementer |
| R13 | Contributor flips a `status:` in constraints.yaml without re-running pytest | README `## Skills shipped` + `_shared/tests/README.md` one-liner + MANUAL_WALKTHROUGH preamble reminder | WS5 implementer; long-term repo maintainer |
| R14 | `/install` preflight's four-key set does not cover MadDM → cryptic error at chain time | Out of scope for this plan; noted for future `/install` work. | — (parking) |

---

## 7. Non-goals (reiterated)

- **No new plugin.** All 4 skill SKILL.md files live in `plugins/hep-ph-toolkit/skills/`.
- **No change to `install/`.** `/install` continues to own environment setup; `/demo` Step 0 preserves the current preflight contract.
- **No change to top-level `.claude-plugin/marketplace.json`.** Only the plugin-internal `.claude-plugin/plugin.json` is updated.
- **No multi-component combiner.** No `combine_multi_dm.py`. No inline `f_i` math in any SKILL.md body beyond a pointer sentence. Multi-component combination is deferred to the future `/dark-matter-constraints` meta-skill (memory `project_dm_tool_roles`).
- **No collider execution.** Placeholder only; selecting `Collider` adds a note, runs nothing.
- **No autonomous skill composition.** Prose-directive dispatch matches `/lagrangian-builder`. No invented `Skill(...)` tool call.
- **No runtime marketplace probe.** `status:` fields in `constraints.yaml` are static; flip them manually when a prereq ships.
- **No template engine or generated SKILL.md pipeline.** ~85% overlap across three SKILL.md files is the accepted cost, bounded by `test_skill_structure.py`.
- **No broadening beyond Profumo benchmark ranges** this iteration.
- **No end-to-end figure reproduction this iteration.** Only Singlet-Doublet relic and 2HDM+a relic are fully unblocked. All other constraints surface `[BLOCKED]` — this is honest and intended. The `/demo` intro and per-model Step 3 messaging prepare the user.
- **No CI.** Manual pytest is the discipline; documented in `_shared/tests/README.md` and `MANUAL_WALKTHROUGH.md`.

---

## 8. What the user sees after this plan lands

- `/demo` → preflight → intro (2 paragraphs on blind spots + roadmap caveats) → Continue gate → three-option model picker.
- Singlet-Doublet: relic runs end-to-end via prose-directive walk through `/sarah-build` → `/spheno-build` → `/madgraph` + `/maddm` → plot. DD/ID block with named missing skills.
- 2HDM+a: same shape. Relic runs; DD is loop-only and blocks on `/feynarts/formcalc/package-x/ddcalc`; ID blocks on `/gamlike`.
- Dark SU(3): multi-component; all three constraints block on `/dark-matter-constraints [PLANNED]`. Interview runs to Step 3 and stops honestly at the gate.
- Anti-drift: `pytest plugins/hep-ph-toolkit/skills/_shared/tests/` catches any SKILL.md / `constraints.yaml` disagreement.
- Manual walkthrough at `plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md` documents the dry-run.

When future skills land (`/feynarts`, `/formcalc`, `/package-x`, `/ddcalc`, `/gamlike`, `/nulike`, `/dark-matter-constraints`), the only code change is flipping `status: planned → exists` in `constraints.yaml`. No SKILL.md edits.
