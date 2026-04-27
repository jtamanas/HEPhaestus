# Critique 02 — Profumo Demo Workflow Implementation

**Role:** Skeptic (brainstorming triad)
**Target:** `01-proposal.md`
**Method:** Independent verification of repo conventions; attacks keyed to proposal sections.

---

## (a) Specific attacks keyed to proposal sections

### §1 File layout — `_shared/` location is plausible but not audited; `install/` omitted

- **`_shared/` claim partly verified, partly false.** `plugins/hep-ph-toolkit/skills/_shared/` exists and holds schemas + a name canonicalizer. Good — convention is real. But the proposer cites it as cover for putting four Python scripts plus a YAML plus a JSON schema there. Today's `_shared/` holds **static schema-and-helper content**, not a mini-runtime of orchestration scripts. Proposer is silently expanding the convention. That might be fine, but it should be called out, not smuggled in.
- **`hep-ph-demo/install/` is already a skill** (verified: `plugins/hep-ph-toolkit/skills/install/SKILL.md`). Proposer never reasons about whether `install/` should end up in the `/demo` flow's prereq chain — spec says `install/` is untouched, but that leaves a loose end: what does the user hit if they run `/demo` before `/install`? The spec defers this; the proposal should at least flag it.
- **"No new plugin, no marketplace change"** — true and correctly aligned with spec non-goals. Keep.
- **`demo/scripts/read_model_meta.py`** is a new Python utility whose only job is parsing sibling SKILL.md frontmatter. Two problems: (i) it introduces a **parse-at-runtime** dependency on an underspecified markdown format (see §2 below); (ii) `/demo` itself is a Claude skill — Claude can read those files directly and extract a one-line title without a Python helper. Adding a Python helper for what Claude can do natively is over-engineering.

### §2 SKILL.md structure — the "second YAML block" convention is invented

- **Claim:** "structured model metadata goes in a **second** fenced YAML block under a `## Model metadata` heading — this is the pattern SARAH skills already use for their schema examples."
  - **Reality:** SARAH skills (`sarah-build`, `lagrangian-builder`, `spheno-build`) use YAML blocks **as example inputs inside documentation** (e.g., "Example (`dark_su3`)"), not as machine-parseable metadata. There is no second-YAML-block-as-metadata convention in this repo. The proposer invented it and dressed it up as precedent.
  - **Consequence:** `read_model_meta.py`, `prereq_probe.py` consumption of `plot_axes`, and the `/demo` picker all depend on this invented convention. If drift breaks parsing, the whole chain breaks. Worse: a contributor editing a SKILL.md has no way to know that the second YAML block is load-bearing vs. illustrative. This is a footgun.
- **Frontmatter claim** — "only `name` and `description` live in the top `---` block, except `lagrangian-builder` which adds `allowed-tools`" — verified. Correct.
- **Shared 4-step flow, explicit copy** — I disagree with the choice, see counter-proposal (b) below. The "~85% text overlap" admission is a concession the proposer undersells. Three ~180-line SKILL.md files with 85% shared content is ~450 lines of near-duplication. That is a lot for a repo with six real orchestrator SKILL.md files.

### §3 Shared logic placement — mostly right, but `combine_multi_dm.py` is suspicious

- **`combine_multi_dm.py` doing weighted combination** is exactly the boundary the `augment_not_replace.md` memo warns about. Proposer invokes valve (c) ("symbolic identity / sum-rule"), which is a stretch:
  - fᵢ = Ωᵢ/Ω_tot is a sum-rule, OK.
  - Linear combination of direct-detection rates (σ_eff = Σ fᵢ σᵢ) is a **physics modeling assumption** about how independent DM populations contribute to the same detector, not a symbolic identity. Real multi-component DM analyses debate coherence, spatially-varying fᵢ, and detector recoil-spectrum shape — not all of these are "just algebra."
  - Quadratic combination for ID (f_i²) assumes same galactic halo profile for all candidates. That's a physics choice.
  - **This logic ought to live in `/maddm` and `/ddcalc` themselves** (or a dedicated `/dark-matter-constraints` meta-skill — memory `project_dm_tool_roles.md` explicitly calls for one). Burying it in a `_shared/combine_multi_dm.py` under `hep-ph-demo/` puts physics decisions in the demo plugin's private code, exactly inverting the `augment_not_replace` principle. See counter-proposal (b3).
- **`prereq_probe.py` reading `marketplace.json`** is broken as described. `marketplace.json` lists **plugins**, not skills. Verified: the top-level `plugins` array in the file has no `skills[]` sub-field. So step 1 of the probe's resolution strategy ("Look up `<skill-name>` in `.claude-plugin/marketplace.json`") cannot work as written. Only step 2 (filesystem glob of `plugins/*/skills/<skill-name>/SKILL.md`) would actually resolve anything. Probe is half-spec.
- **Time-budget script** is fine in principle but low-value. A 40-line Python script to sum three-to-four numbers and subtract double-counted prereqs is not carrying its weight. See counter-proposal (b2).

### §4 Interview flow — concrete where it matters, but confuses tool capabilities

- **Step 4 invocations** hit the biggest factual error in the proposal. Proposer writes:
  ```
  1. /sarah-build plugins/hep-ph-toolkit/skills/_shared/assets/singlet_doublet.yaml
  2. /spheno-build singlet_doublet
  3. /madgraph use singlet_doublet
  4. /maddm --model singlet_doublet --candidate chi1 --observables relic
  ```
  **`/maddm` is not a runnable orchestrator skill.** Verified by reading `plugins/hep-ph-toolkit/skills/maddm/SKILL.md`: it's a decision-tree reference skill (like `/madgraph`) that routes Claude to reference docs — it has no CLI, no `--model` argument, no orchestrator. The proposer is treating all sibling skills as uniform callable APIs, but this repo has two classes:
    1. **Orchestrator skills** with scripts + specific inputs: `/sarah-build`, `/spheno-build`, `/sarah-install`, `/spheno-install`, `/lagrangian-builder`, `/install` (`hep-ph-demo`).
    2. **Reference skills** with decision trees pointing to `references/`: `/madgraph`, `/maddm`, `/hep-plot`, plus every non-orchestrator skill I sampled.
  - This distinction is load-bearing for the spec. Steps 3–5 of the Step 4 flow **cannot be a mechanical skill invocation** — Claude has to read `/madgraph`'s and `/maddm`'s reference trees and do the work manually. The proposer glosses over this, which means the per-model SKILL.md files will need to embed a lot more MadDM-specific know-how than the proposal admits.
- **Passing `--axes "m_chi vs sin(2θ)"` to `/hep-plotting theory-data-comparison`** — this isn't how `/hep-plotting`'s sub-skills work. Verified: `/theory-data-comparison` is a reference skill documenting a workflow, not a CLI. The per-model skill will be writing its own plot script, not shelling out to a nonexistent CLI.
- **Pre-`combine_multi_dm.py` pass-through for N=1** — defensible for code-path uniformity but "it's 3 seconds of IO" understates the annoyance of a pass-through step. Counter: just skip it when `len(dm_candidates) == 1` and let tests cover the branch. Uniformity for uniformity's sake is a code smell.

### §5 Prereq chain encoding — `constraints.yaml` is fine; runtime probe is broken

- **Declarative `constraints.yaml` as single source of truth** — good call. Central table of prereq chains keyed by constraint id is the right factoring.
- **Duplicating time numbers into per-model SKILL.md markdown tables plus a "CI test" to keep them in sync** — the repo has no CI. Verified: no `.github/`, no `.gitlab-ci.yml`, nothing. Proposer's "a CI test will assert they agree" is vaporware. A test file with no runner is a promise a contributor will ignore. Either (i) the SKILL.md table is generated from the YAML at edit time (which the proposer explicitly rejected because the repo has no build step), (ii) the SKILL.md table is removed and the YAML is authoritative, or (iii) the tests live alongside the scripts (like `plugins/hep-ph-toolkit/skills/_shared/tests/`) and someone runs them manually. Proposer picks (i) implicitly by invoking CI, which doesn't exist. This needs to be fixed.
- **`[EXISTS]`/`[PLANNED]` runtime probe** — as noted in §3, the marketplace lookup doesn't work. But deeper: is runtime probing even the right semantics? The spec says `[PLANNED]` prereqs are **on the DM-tool roadmap**. Roadmap state is a product decision, not a filesystem state — a skill could exist as a stub SKILL.md but not be functional. A runtime probe that says `[EXISTS]` just because the SKILL.md file exists will lie. Static declaration in `constraints.yaml` (with an explicit `status: planned | exists` field maintained by the team) is probably more honest than autodetection. See counter-proposal (b4).

### §6 `/demo` delegation — the Skill-tool invocation claim is sloppy

- **Claim:** "`/demo` invokes the per-model skill via the **Skill tool** with the skill name `singlet-doublet` / `2hdm-a` / `dark-su3`. Per repo convention (see `/lagrangian-builder` calling `/sarah-install`)."
  - **Reality:** `/lagrangian-builder` does not mechanically call `Skill(skill=...)`. It says "Invoke `/sarah-install` subskill" in prose and Claude (the agent reading the SKILL.md) decides how to dispatch. Verified by grepping `lagrangian-builder/SKILL.md`: there is no `Skill(skill=...)` syntax, no tool-invocation boilerplate — just English directives. The repo convention is **prose-driven dispatch**, where Claude reads the parent SKILL.md and then reads the child SKILL.md, not a tool-call protocol.
  - Whether the Skill tool is the right mechanism in this marketplace is actually unclear. The proposer **assumes** there is a `Skill` tool callable from `/demo`; I cannot confirm this from the repo. If Claude Code's plugin runtime exposes a Skill dispatch tool, great, use it; if not, the /demo SKILL.md should say "Instruct the user / the agent: read `plugins/hep-ph-toolkit/skills/<chosen-model>/SKILL.md` and execute it" — in other words, the same prose-driven convention as `/lagrangian-builder`.
  - This matters because the Step 4 execution pattern inherits the same assumption: "Claude invokes each sub-skill through the Skill tool." If there is no Skill tool, the per-model skills have to work purely as SKILL.md Claude reads in sequence, which changes how metadata is read and how state passes between steps.

### §7 Workstream decomposition — mostly fake parallelism

- **WS1 on critical path** → correct that it has to go first.
- **WS3/WS4/WS5 (one per model) "truly independent"** → **false**. All three share:
  - The `_shared/flow.md` / Step 2–4 template
  - Constraint-table schema
  - The yet-to-be-decided "second YAML block" metadata format
  - The combination-rules physics
  - The plot-handoff contract
  Three agents writing three SKILL.md files with 85% shared text in parallel will produce three divergent implementations of the shared text. That's the drift the proposer is worried about in §2, now elevated into the workstream plan. The honest decomposition is: **WS1 + WS2 (template + one reference implementation) first, THEN WS3/4/5 as mechanical adaptations**. WS2 is currently "demo/ rewrite" — it should be "demo/ rewrite plus one reference per-model skill that establishes the template."
- **WS6 "CI test"** → no CI, see §5. If WS6 is "write tests that nobody runs," it's not a workstream.
- **"Good candidates for `superpowers:dispatching-parallel-agents`"** — yes, once WS1 + one reference per-model skill exist. Not three in parallel from a blank slate.

### §8 Risks — proposer's self-flagged weak points

- **(1) SKILL.md duplication vs. templating** — proposer correctly flags this as weakest. Counter-proposal (b1) below.
- **(7) `/demo` doing no prereq probing of its own** — proposer's reasoning is correct: keeping `/demo` as a thin front door is aligned with the spec. **Keep this**; don't let the synthesizer push prereq probing up into `/demo`.
- **(9) Starter `.yaml` location** — this is a real open question. The eval `.m` files and the new `/sarah-build` ModelSpec YAML format are two different things. Need to either (i) convert the three eval `.m` presets to ModelSpec YAML and check them into `plugins/hep-ph-toolkit/skills/_shared/assets/`, or (ii) have the per-model skill call `/sarah-build` in a mode that accepts a raw `.m` (which `/sarah-build` does not currently support — verified: `sarah-build` takes a ModelSpec YAML). Option (i) is the real work, and it's not in anyone's workstream.
- **(10) `_shared/` inside `skills/`** — proposer is right to worry. Neither the repo nor any doc I can find states whether Claude Code's plugin loader treats every subdirectory of `skills/` as a skill. The `plugins/hep-ph-toolkit/skills/_shared/` precedent exists but is not blessed by any documentation. Moving it up to `plugins/hep-ph-toolkit/_shared/` is safer. This should be the default; proposer is correct to flag but should have just picked the safer location.

---

## (b) Counter-proposals

### (b1) SKILL.md duplication: inversion — keep per-model skills thin, push shared flow into `demo`

Instead of three ~180-line SKILL.md files with 85% shared content, invert:

- `/demo` owns **the interactive flow** (Step 1–4). It accepts the chosen model as a parameter, reads the per-model skill's metadata file, and runs the same four-step interview with model-specific substitutions.
- Per-model skills are **metadata + model-specific text snippets**, not orchestrators. `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` is ~40 lines: frontmatter + `## Model metadata` YAML block + a `## DM physics narrative` prose block that Step 1 pastes verbatim + a `## Natural parameter plane` block Step 4 reads for plot axes.

Spec tension: the spec says "`/demo` does **not** own constraint interview, time gates, or execution" and "`/demo` is a thin front door." That's the crux — if we obey it strictly, we need three near-duplicate flow implementations. I think the spec is over-specifying here. Flag to synthesizer: either relax the spec (let `/demo` own the flow, per-model skills become data) or accept that three per-model SKILL.md files will duplicate flow text and put drift prevention on a real mechanism, not imaginary CI.

If the spec is held, then: the three SKILL.md files should load a shared flow **by explicit reference**, not by copy-paste. Pattern: each per-model SKILL.md contains only (a) frontmatter, (b) a `## Model metadata` YAML block, (c) a line at the end: **"Flow: see `../_flow.md`"**. `_flow.md` is a non-SKILL markdown file under `plugins/hep-ph-demo/` containing the Step 1–4 recipe with placeholders like `{dm_candidates}`. Claude reads both files when executing the skill. This is not transclusion — it's explicit multi-file reading, which Claude does natively. No build step, no templating engine, no drift.

### (b2) Time-budget: markdown is the source of truth, YAML is derived

Reverse the proposer's factoring:

- Each per-model SKILL.md is authoritative for its time table (markdown, human-scannable, co-located with the skill).
- No `constraints.yaml`. No `time_budget.py`. No parallel YAML source.
- `/demo`'s picker does Claude-native frontmatter reading: "Read the 'All-constraints cold total' line from each `plugins/hep-ph-toolkit/skills/*/SKILL.md`." Claude reads markdown natively; no helper needed.
- Step 3's prereq-chain table is also markdown in the per-model SKILL.md. Overlap adjustment is a half-paragraph Claude can do by inspection — these are hour-ranges, not precise numbers.
- If we later need the YAML, generate it from the markdown, not the other way round.

This saves ~3 files and one invented "second-YAML-block" convention. Physics is written once, near the skill.

### (b3) Multi-component DM: push into a new `/dark-matter-constraints` meta-skill (or into `/maddm`)

Memory `project_dm_tool_roles.md` says: "MadDM primary, micrOMEGAs validator, DRAKE for narrow resonances; /dark-matter-constraints meta-skill planned." Exactly this use case.

- The `combine_multi_dm.py` logic belongs in the DM-tool ecosystem, not inside `hep-ph-demo`.
- If `/dark-matter-constraints` doesn't exist yet, make its creation a prereq of `dark-su3/SKILL.md` (list it as `[PLANNED]` in the prereq chain, block the multi-component constraint until it's built).
- Singlet-Doublet and 2HDM+a have N=1, so they do not need `/dark-matter-constraints`. Their constraints run today against `/maddm` + `/ddcalc` (once `/ddcalc` lands).
- This is the `augment_not_replace` memo applied correctly: don't bury physics math in `hep-ph-demo/_shared/`; put it in the skill whose job is DM-constraint combination.

Concretely: Dark SU(3) in this iteration is *blocked* on `/dark-matter-constraints` (just as it's blocked on `/ddcalc`). That's a spec-allowed outcome (the "Run available, drop blocked" path). The demo can show the one-candidate models end-to-end today and Dark SU(3) as the "come back when these prereqs land" case. This matches what the spec already effectively concedes about `[PLANNED]` prereqs.

### (b4) Prereq status: static metadata with an explicit status field, not a runtime probe

- `constraints.yaml` (or the per-model markdown table) lists each prereq with an explicit `status: exists | planned` field, maintained by humans.
- No filesystem probe. No marketplace.json parsing.
- When a prereq ships, a human edits the field to `exists` in one place. A line-level diff, not a runtime oracle.
- Runtime probing is valuable when state genuinely changes under you (a service is up or down). Marketplace skill status is product-planning state — it changes on commits, not on seconds. Source-of-truth it like a changelog.

This eliminates `prereq_probe.py` entirely. Step 3 reads the YAML (or markdown) and prints `[EXISTS]`/`[PLANNED]` from the field.

### (b5) `/demo` → per-model dispatch: prose directive, not tool invocation

Follow `/lagrangian-builder`'s convention exactly. `/demo`'s SKILL.md just says:

> Based on the user's choice in Step 3, read and execute the corresponding per-model SKILL.md: `plugins/hep-ph-toolkit/skills/<model>/SKILL.md`.

Claude reads that, finds the right SKILL.md, and runs it. No Skill-tool call, no dispatch mechanism to invent. Mirror the existing pattern.

### (b6) Workstream recut

- **WS1:** `_shared/` scaffolding (if kept at all — see (b2)): `constraints.yaml` OR the decision that per-model markdown is authoritative, plus ModelSpec YAMLs for the three Profumo models under `plugins/hep-ph-toolkit/_shared/assets/` (this was missing from proposer's plan).
- **WS2:** `/demo` rewrite + one reference per-model skill (**singlet-doublet, N=1, relic-only ready path**). Establishes the template. One agent.
- **WS3:** `2hdm-a` per-model skill. **Mechanical adaptation of WS2's template.** One agent, can start as soon as WS2's template is committed.
- **WS4:** `dark-su3` per-model skill + either `/dark-matter-constraints` meta-skill (if we take (b3)) or an explicit `[PLANNED]` on multi-DM post-processing. One agent.
- **WS5:** Manual integration test (no CI — a human runs it): does `/demo` pick `singlet-doublet` → enter the flow → hit the blocked DD constraint → exit cleanly? Documented as a manual regression test in a `TESTING.md` inside the plugin.

Three workstreams on the critical path, one (WS3) optionally parallel once WS2's template is frozen. This is the honest parallelization.

---

## (c) Things the proposer got RIGHT (keep these)

1. **`constraints.yaml` as the declarative prereq-chain source.** Even if the runtime probe is wrong, the idea of a single YAML table keyed by constraint id, listing the chain and time bounds, is correct factoring. Keep the idea; drop the probe.
2. **Multi-select `AskUserQuestion` for Step 2** with per-constraint options — matches the spec and is the right UX.
3. **`Run available` / `Back` / `Cancel` ternary gate** when some constraints are blocked — exactly the spec's semantics, well-scripted. Keep verbatim.
4. **Valve-c acknowledgment of `augment_not_replace`** (even though I disagree with the application — §3 above). The proposer did read the memory and tried to defend the combiner on its grounds. That's the right instinct.
5. **Per-model `plot_axes` concept** — a declarative "natural parameter plane" per model is the right shape for handoff to plotting. The wrong part is embedding it in an invented second YAML block inside SKILL.md; the right form is a sibling `metadata.yaml` next to the SKILL.md, or inlined into `constraints.yaml`.
6. **§8 risk list** is disciplined and honest. The proposer flagged the real weak points, including `_shared/` location, `marketplace.json` coupling, and their own duplication choice. This is calibrated self-review; the synthesizer should treat those flags as the genuine decision points.
7. **Keeping `/demo` as a thin front door, not as a prereq-probing orchestrator** (risk #7) — correct call, spec-aligned. Don't let anyone move probing up into `/demo`.
8. **Dispatching to sibling skills from per-model skills** (Step 4) follows the existing `/lagrangian-builder` pattern — directionally correct, even though the Skill-tool framing is wrong.

---

## (d) Top 3 decisions the synthesizer MUST make

1. **Duplication vs. relaxed spec.** Either (a) hold the spec's "thin `/demo`" and accept three SKILL.md files with real duplication mitigated by shared-markdown reference (my (b1)), or (b) relax the spec so `/demo` owns the flow and per-model files are pure metadata. The proposer's "explicit copy + imagined CI" is the worst of both worlds. This is THE decision.

2. **Multi-component DM combination home.** Either (a) a script inside `plugins/hep-ph-toolkit/skills/_shared/` (proposer), or (b) a new `/dark-matter-constraints` meta-skill that owns this responsibility and is a prereq for `dark-su3` (my (b3), aligned with `project_dm_tool_roles.md`). This has downstream consequences: option (b) means Dark SU(3) is fully `[PLANNED]`-blocked for multi-component in this iteration, which is honest but reduces what the demo can show today. The spec's "owned by per-model skill's Step 4 execution" is compatible with (b) if we read "per-model skill's Step 4" as "per-model skill delegates to `/dark-matter-constraints`."

3. **Runtime probe vs. static status.** Either (a) runtime filesystem/marketplace probe (proposer — and the probe as described doesn't even work because marketplace.json doesn't list skills), or (b) static `status: exists | planned` field maintained by humans, edited when a prereq ships (my (b4)). Coupled to this: do we invent a "second YAML block in SKILL.md" metadata convention, or use a sibling `metadata.yaml`, or inline everything into `constraints.yaml`? Pick one metadata home and stick to it.

**Bonus decision (lower stakes but real):** ModelSpec YAML starter files for the three Profumo models need to be authored and placed somewhere. Proposer punted. Synthesizer should pin: `plugins/hep-ph-toolkit/_shared/assets/{singlet_doublet,2hdm_a,dark_su3}.yaml`, and this authoring is a real workstream item, not glue.
