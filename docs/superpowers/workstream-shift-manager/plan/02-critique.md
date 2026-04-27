# Plan Draft 01 — Skeptic Critique

**Role:** Skeptic (shift-manager pipeline, round 2)
**Target:** `docs/superpowers/workstream-shift-manager/plan/01-draft.md`
**Verified against repo:** `plugins/hep-ph-demo/.claude-plugin/plugin.json`, current `plugins/hep-ph-toolkit/skills/demo/SKILL.md`, `plugins/hep-ph-toolkit/skills/_shared/tests/`, `git log` (last 40 commits), synthesis §2.2–§4, spec §Deliverables–§Migration.

The plan is well-organized and materially honest about most of what the synthesizer decided. It has one genuinely dangerous structural defect, several hidden ambiguities, and a handful of done-criteria that a tired reviewer could rubber-stamp without having actually tested anything. Sections below.

---

## Section 1 — Specific attacks per workstream

### WS1 (scaffolding + ModelSpec YAMLs + `/demo` rewrite)

**A1.1 — Loader-check is in the done-criteria, not the plan.** Done-criterion #1 says "running `claude` with the plugin loaded emits no 'unknown skill `_shared`' error." There is **no procedure** for this. How does the WS1 implementer load the plugin? Does `claude` tail a log? Is the expected failure mode a startup error, a silent warning, or a runtime "skill not found"? The implementer prompt falls back on "use good judgment" here. If the loader in fact scans every subdir of `plugins/hep-ph-demo/` for `SKILL.md` (it almost certainly doesn't, but nobody has checked), the plan offers no detection signal. **The synthesizer must give this a concrete check: a shell command, expected stdout/stderr, and a decision tree.** Otherwise the WS1 agent will do what agents always do — ship and declare done — and the bug surfaces at WS2 dry-run.

**A1.2 — Step 0 preflight is "preserved verbatim" but the intro is being reordered around it.** The current `demo/SKILL.md` has Step 0 preflight → Step 1 paper intro (short, one paragraph) → gate → model picker → figure picker → compute. The rewrite keeps Step 0 but replaces the short intro with synthesis §3's **two-paragraph verbatim intro** mentioning blind spots AND the roadmap-gap caveat. Done-criterion says "Step 0 preflight preserved verbatim" + "Step 1 intro matches synthesis §3 word-for-word." Both can simultaneously pass with the preflight running BEFORE or AFTER the intro. The current file runs preflight FIRST. Synthesis is silent on order. The plan does not pin this. If the WS1 agent moves preflight after the intro (because it looks nicer pedagogically), users on broken installs see a 2-paragraph intro they can't act on. **Pin: preflight runs before intro, matching current behavior.**

**A1.3 — `time_budget.py` overlap-computation is hand-waved.** §B.2: "Overlap computation: union the chains of all selected constraints; sum each prereq's contribution once. (For v1, since constraints.yaml doesn't carry per-prereq hour budgets, overlap adjustment is approximated by taking `max` of constraint cold ranges and summing the unique-prereq extras — acceptable stand-in; revisit if numbers look off.)" This is not a spec, this is a TODO. The synthesizer cites `sarah-build`/`spheno-build` being counted once as a demo-user-visible promise. The `max + unique-extras` heuristic has pathological cases (two constraints whose chains share ONLY `sarah-build` would under-report). `test_time_budget.py` done-criterion §B.11 asserts "does not double-count" which the `max` heuristic will satisfy without actually implementing overlap. **Either ship per-prereq time budgets in `constraints.yaml` now, or document the `max + extras` algorithm explicitly and add a unit test pinning the promised behavior on a specific example.**

**A1.4 — ModelSpec YAML done-criterion is "validates against the schema."** Schema validation is necessary but not sufficient. The synthesis risk #2 ("physics-capable agent … stub allowed but flagged") is mentioned in R2 but the done-criteria do not gate on physics correctness at all. A Sonnet that doesn't know the singlet-doublet Lagrangian will produce a schema-valid, physics-wrong YAML, and done-criteria pass. The reviewer prompt says "Be adversarial on ModelSpec physics correctness — stubs are allowed only if flagged," which is the right instruction, but the SHAPE of that flag is unspecified. **Pin: every stub YAML carries a literal `status: stub` or `provisional: true` field AND a `# TODO(physics)` comment naming what's unverified. Reviewer rejects absent flag.**

**A1.5 — `demo/SKILL.md` closing block reads `summary.json` but the contract is introduced in WS2.** §B.7 item 8 says `/demo` reads `./demo_output/<model>/summary.json`. §B.8 defines the schema. But §B.8 is WS2's responsibility (per §A WS2 deliverables). WS1 therefore writes a reader against a schema WS2 hasn't shipped. This is a real cross-workstream coupling the plan hides. **Either pin the schema in WS1's deliverables (as `_shared/tests/summary_schema.json` or inline in WS1's `demo/SKILL.md`), or demote WS1's closing-block to a stub that WS2 fills in.**

### WS2 (singlet-doublet reference skill)

**A2.1 — "Step 4 relic branch contains four prose directives in order" (§A WS2 done-crit #5).** Four what, exactly? `/sarah-build`, `/spheno-build`, `/madgraph`+`/maddm` (one directive or two?), `/hep-plotting`. The synthesis §2.5 example has three invocations for the MadGraph+MadDM step fused into one narrative paragraph. The plan says "four prose directives"; the synthesis's example is three compound bullets. The reviewer has no way to mechanically check this — they'll count paragraphs vs bullets vs "directive-shaped blocks." **Pin: define "prose directive" by a regex or structural rule (e.g. "a blockquote starting with `Invoke /<skill>`") so the structure test can count them.**

**A2.2 — "40–60 lines of MadDM-specific guidance" is a length target.** §R4 and the WS2 implementer prompt both say "40–60 lines." That's a soft gate. A tired reviewer sees 45 lines of MadDM-*flavored filler* and passes it. Synthesis risk #1 is the real risk: is the guidance **tractable**? The test for tractability is: can a separate Sonnet, given only this SKILL.md and access to `/madgraph` + `/maddm` references, drive an MG5 session to produce `Omega h²` for `chi1`? The plan has no such check. The dry-run in §C manual smoke tests stops at "Step 4 prints the first prose directive" — it never validates the guidance downstream of step 1 of the chain. **Pin: WS2 done-criterion adds a second dry-run: the reviewer reads the MadDM section aloud, asks themselves "could I drive MG5 from this?" and attaches written answer to the PR.** Still soft, but at least forces engagement.

**A2.3 — `test_skill_structure.py` fixture is parametrized over `SKILLS = ["singlet-doublet"]`.** Real problem: when WS3 and WS4 run in parallel worktrees, both will need to **modify** `test_skill_structure.py` to extend `SKILLS` — merge conflict at the list literal. Plan §D acknowledges `plugin.json` conflicts but not this one. **Pin: WS3 extends `SKILLS` to `["singlet-doublet", "2hdm-a"]`; WS4 extends to `["singlet-doublet", "dark-su3"]` (each adds only its own); WS5 reconciles to all three.** Or better: have WS2 ship the test parametrized over **all three skill names**, with a skip-if-missing guard, so WS3 and WS4 only add files, never touch the test.

**A2.4 — `summary.json` schema is described but not validated.** §B.8 gives a JSON example; §R9 says "WS5 could add a regex assertion" — "could" is not a plan. There's no test asserting that WS2's SKILL.md actually tells Claude to write this file with this shape, and there's no test asserting the schema. At best `test_skill_structure.py` asserts the SKILL.md body *contains the literal path string*. **Pin: add `test_summary_contract.py` in WS2 that asserts the SKILL.md body contains the literal keys `ran`, `skipped_constraints`, `artifacts_dir`, `headline`, matching §B.8. Or drop the contract and have `/demo` parse whatever the per-model skill emits.**

### WS3 (2hdm-a, parallel with WS4)

**A3.1 — "Mechanical adaptation" hides physics.** The done-criterion "differences confined to title/hook wording, DM candidate name, plot axes, time overrides" is mechanically checkable against a diff, but the 2HDM+a's DM phenomenology IS different from singlet-doublet's. The relic-density chain is the same, but the *MadDM card settings* for a pseudoscalar-mediated Dirac DM are not the same as for a Majorana singlet-doublet. If WS2's 40–60 lines of MadDM guidance are copy-pasted verbatim, WS3 ships physically-wrong directives. The synthesis risk #1 lands squarely on WS3. The plan says nothing. **Pin: WS3 done-criterion adds "Step 4 MadDM guidance adjusted for Dirac DM + pseudoscalar mediator (explicit mention of CP-odd coupling, s-channel a-resonance)". Reviewer checks the MadDM lines differ from WS2's where the physics demands.**

**A3.2 — `2hdm-a` is listed in constraints.yaml as `2hdm-a`** (with hyphen and digit prefix). YAML top-level keys beginning with digits parse as strings only if quoted; unquoted `2hdm-a:` in a map is fine in YAML 1.1 but some loaders flag. More important: the skill directory is `skills/2hdm-a/`, an unusual name. Does the Claude plugin loader accept digit-leading skill names? The synthesis and plan both assume yes with zero verification. Memory: the only other digit-named thing in the repo is `eval/2506.19062_wimps_blind_spots/`, which is not a skill. **Pin: WS1 loader check explicitly includes a test that `skills/2hdm-a/` loads; if not, rename to `two-hdm-a`.**

**A3.3 — The "rebase on whichever lands first" rule for `plugin.json`.** Git merge semantics on a JSON array are "second writer wins unless hand-merged." The plan's §D step 3 says "keep both entries." Fine, but the implementer prompt for WS3 says "Add the `2hdm-a` entry" with no rebase instruction. **Pin WS3 implementer prompt: if `plugin.json` already contains a `dark-su3` entry at merge time, preserve it; this may require a post-merge commit.**

### WS4 (dark-su3, parallel with WS3)

**A4.1 — "Every constraint is BLOCKED" is the entire demo.** This is the right call per D2a, but the UX test needs more care. §A WS4 done-criterion #3: "If user picks `run_ready` with zero ready constraints, skill prints `'Nothing to run; returning to constraint selection.'` and loops to Step 2." The synthesis §3 Step 3 gate options do not define this loop-back behavior — they show three branches (`run_ready`, `back`, `cancel`) and say `run_ready` "drops blocked constraints and proceeds." If there are no ready constraints after dropping, "proceed" means an empty Step 4. The plan invents the loop-back silently. Is this the right UX, or should `run_ready` with zero ready be `cancel`-equivalent with a different message? **Synthesizer must decide.**

**A4.2 — Step 4 body "documents the N=2 execution path but is unreachable."** This is a real content-authoring burden the plan glosses. Writing an accurate description of how `/dark-matter-constraints` would combine per-candidate observables for Dark SU(3) is physics work equivalent to writing half of `/dark-matter-constraints` itself. Sonnet will either (a) hand-wave with "compute per-candidate then combine with `/dark-matter-constraints`" (useless) or (b) re-derive the combination inline (violates D2a / `augment_not_replace`). There's no third option. **Pin: WS4 Step 4 body describes ONLY the per-candidate invocation sequence; the combination step is one sentence pointing at `/dark-matter-constraints` as future work. Reviewer rejects any inline combination math.**

### WS5 (anti-drift tests + walkthrough)

**A5.1 — MANUAL_WALKTHROUGH done-criterion: "Execute this walkthrough yourself end-to-end and append your observations."** The WS5 agent will do this in a Claude subprocess where the marketplace plugin may or may not be loaded depending on how the harness is invoked. The plan does not specify *how* the walkthrough is executed. From the current `claude` CLI? From a fresh session with the repo cloned? Does the walkthrough require `/install` to have run first (since `/demo` Step 0 preflight otherwise hard-stops)? **Pin: MANUAL_WALKTHROUGH's preamble specifies the exact `claude` invocation, prerequisites (is `/install` required? if yes, provide a mock-config sidecar), and whether deviations from expected output block WS5 merge.**

**A5.2 — README update scope is vague.** "Update README.md 'Skills shipped' section." Does this section currently exist? Unchecked. If not, WS5 is authoring a new README section and deciding its shape — that's not "update", that's "design." **Pin: spec the section's heading and bullet format in §B.12 or a new §B.13.**

---

## Section 2 — Cross-cutting plan issues

**CX.1 — Worktree strategy collides with `_shared/` writes.** WS1 creates `_shared/` and tests. WS2 adds `test_skill_structure.py` under `_shared/tests/`. WS3 and WS4 **both** modify `test_skill_structure.py` in parallel worktrees (per A2.3). WS5 further modifies it. That's four workstreams writing the same file, two of them in parallel. The plan's merge-order note handles `plugin.json` but not `test_skill_structure.py`. And `_shared/assets/*.yaml` are all written in WS1 but if a WS3/WS4 physicist finds a bug in `singlet_doublet.yaml` or `two_hdm_a.yaml`, whose worktree does the fix commit from? **Fix: either (a) parametrize the test in WS2 so WS3/WS4 only add SKILL.md files (A2.3 fix); (b) serialize WS3 and WS4 (drops parallelism but kills all merge hazard); or (c) explicit "rebase on top of whichever lands first, keep both entries" per-file instruction beyond `plugin.json`.**

**CX.2 — The `skills[]` plugin.json registration order.** Plan proposes appending each new skill in its own workstream. Does the plugin loader care about order? Currently `install` precedes `demo`. Does `/demo`'s model picker assume anything about list order? The picker is hard-coded so no, but the structure test's expected-order on parsed JSON is unspecified. **Pin: document canonical order `install, demo, singlet-doublet, 2hdm-a, dark-su3` and have `test_plugin_json.py` (new, WS5) assert it.**

**CX.3 — Spec-fidelity misses one detail.** Spec §Step 3 item on gates: "If no constraints are blocked, the gate offers `Run it` / `Back` / `Cancel`." Plan's Step 3 ready-branch JSON uses `id: "go"` with `label: "Run it"`. Fine — label matches. But spec §Step 3 blocked branch says "`Run available` → drop blocked." Plan uses `id: "run_ready"` with label "Run available (drop blocked)". Label prefix matches. The structure test asserts `option ids == ["run_ready", "back", "cancel"]` — which would break if a future edit renames to match spec's literal label "run_available" or if someone interprets "Run available" as the id. **Pin: `test_skill_structure.py` asserts LABELS, not ids, since spec speaks in labels.** Or explicitly note the id-vs-label mapping.

**CX.4 — `dm_candidates` metadata format.** Spec §Step 1 shows YAML with `name/spin/notes` keys. Synthesis §2.2 adds `display`, `plot_axes`, `multi_component` at the `models.<id>` level, with `dm_candidates` inside. Plan §B.1 repeats synthesis. All consistent. The per-model `## Model metadata` YAML block in SKILL.md **duplicates** the `constraints.yaml` entry (§B.8 step 3: "duplicating `constraints.yaml`'s `models.<id>` section"). This duplication is called out as intentional for human-scannability. But the structure test (§B.10 first bullet) asserts "agreement with constraints.yaml on display, dm_candidates, plot_axes." What about `multi_component` and `multi_component_prereq`? Silent. **Pin: test asserts agreement on ALL keys of `models.<id>`, not a subset.**

**CX.5 — The "physics-literate implementer" assumption is load-bearing and unspecified.** Plan WS1 says "Owner: Sonnet implementer (physics-literate — ModelSpec YAMLs are real physics work)." There is no mechanism in the pipeline that selects a physics-literate Sonnet vs. a generic one. The dispatch recommendation in synthesis §4 is "single-agent." The implementer prompt does not establish physics competence or require the agent to verify the Lagrangian against arXiv:2506.19062 via a specific procedure. **Pin: the WS1 implementer prompt has a literal instruction: "before authoring each YAML, WebFetch `https://arxiv.org/abs/2506.19062` and quote the relevant Lagrangian section verbatim in a `claim_source` block of the YAML comment header. Do not stub without explicit `status: stub` field."**

**CX.6 — No mechanism for the demo to actually land and ship.** WS5's done is "tests green and walkthrough documented." No workstream has "run `/demo` in anger and observe the paper-figure output." That's fine given the spec's "no end-to-end execution possible" (R3), but the plan does not say `/demo` is NOT expected to reach a figure in this iteration. Someone reading only the plan could interpret the final state as "demo works; here's the walkthrough." **Pin: add a closing §H "What the user sees after this plan lands" with an honest statement that the demo is an interactive interview with a partial relic-only execution path for Singlet-Doublet and 2HDM+a; all other constraints block.**

**CX.7 — No branch-naming enforcement.** Plan uses `ws<N>/<slug>` for branches (`ws1/demo-shared-scaffold`). Repo's `git log` shows merges like `Merge PR-D`, `PR-A:`, `W2 fixup:`, not `ws<N>/...` branch merges. No precedent for the proposed scheme. Not wrong, just invented. Not a blocker.

**CX.8 — Commit style is mostly right but one claim is wrong.** Plan §D claims "lowercase after the colon." Checked `git log`: `W5: /lagrangian-builder orchestrator rewrite` — that's a `/` not a letter, but `W3: implement /sarah-build skill` is lowercase, `W2: add tests` is lowercase. `design: profumo demo workflow redesign spec` lowercase. `W0(3): schemas, SHARED.md, ...` mixed. `W6: add named-model resolver for /madgraph skill` lowercase. Fine, claim holds. Sub-commits `W1(1): sarah-install scripts — detect/use-path/install` are canonical — plan references these correctly.

**CX.9 — No `Co-Authored-By` line is correctly identified, but CLAUDE.md does not say this explicitly.** It's a load-bearing instruction that lives only in the plan's "Verified in repo" bullet. If a future pipeline ingests only the synthesis + plan body sections, it could miss this. Low-consequence.

---

## Section 3 — Handoff prompt weaknesses

For each workstream, the single most important fix:

### WS1
- **Implementer:** Adds no concrete loader-verification command. Most important fix: replace "verify the plugin loader tolerates a top-level `_shared/` directory" with `run exactly this command: <shell snippet>. On success, <observable>. On failure, move _shared/ inside skills/ and document the move in the commit message.`
- **Reviewer:** Does not say how to check ModelSpec physics correctness. Most important fix: require the reviewer to open arXiv:2506.19062 §II and cross-reference the singlet_doublet.yaml field content (fermion singlet + Higgs-doublet mixing Yukawa) by name; reject if unmapped.

### WS2
- **Implementer:** "Use synthesis §3 Step 1/2/3/4 text verbatim" is one sentence; it omits the Step 1 single-candidate variant is the right one and the multi-candidate variant is WS4's. Most important fix: state "Use the SINGLE-CANDIDATE variant in synthesis §3 Step 1 (the first block, not the Dark SU(3) one)."
- **Reviewer:** Item (4) "Step 4 uses prose directives, not invented `Skill(...)` calls." Good. But does not define "prose directive." Most important fix: "Prose directive = a blockquote (`>` prefix) whose first line starts with `Invoke /<skill>`, matching the form in `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` line 40. Count occurrences; there must be exactly FOUR in the relic branch."

### WS3
- **Implementer:** Does not instruct the adapter to change MadDM-specific guidance for Dirac-DM + pseudoscalar physics. Most important fix: "Per A3.1: adjust Step 4's MadDM guidance for the 2HDM+a's s-channel pseudoscalar mediator. Do not copy MadDM card settings verbatim from WS2."
- **Reviewer:** Diff-based structural check is thorough but does not catch a correct-looking-but-wrong-physics MadDM section. Most important fix: reviewer must open the 2HDM+a's `dd` discussion and verify it mentions "loop-only," "CP-odd," and "a-resonance" — or reject.

### WS4
- **Implementer:** "Step 4 body documents the N=2 execution path but is never reached" invites inline combination math. Most important fix: explicit "Do NOT derive the f_i combination formula in the SKILL.md body. Reference `/dark-matter-constraints [PLANNED]` as the single owner. Any combination prose beyond one sentence is a reject trigger."
- **Reviewer:** Already has the "hard reject" on combiner code in `_shared/`. Most important fix: extend rejection to combiner MATH in the SKILL.md body, not just code.

### WS5
- **Implementer:** MANUAL_WALKTHROUGH execution procedure is unspecified (A5.1). Most important fix: "Start a fresh Claude session at this repo's root. If `/install`'s config is absent, write a mock at `~/.config/hep-ph-agents/config.json` with dummy paths; the walkthrough's concern is conversation flow, not SARAH actually running."
- **Reviewer:** Does not distinguish "walkthrough notes include real deviations" from "walkthrough is a template with 'all good' appended." Most important fix: reviewer rejects if observation notes are shorter than expected section × 0.5 or contain no specific output quote.

---

## Section 4 — What the drafter got right

Calibration matters. These are real strengths the synthesizer should preserve:

1. **Correctly identified `plugin.json` carries `skills[]`.** Synthesis §2.1 claimed "No change to marketplace.json" and glossed plugin.json. Drafter caught the distinction and pins it in the "Verified in repo" header. **Verified correct against repo.**
2. **Step 0 preflight preservation surfaced to top-level (§B.7 item 3).** Synthesis R7 mentioned it; the drafter promoted it into a concrete done-criterion. Good.
3. **`summary.json` hand-back contract escalated from synthesis R8 into §B.8.** Synthesis had it in risks; drafter moved it into a concrete schema. Good, though the contract-enforcement hole (A2.4) remains.
4. **`test_skill_structure.py` parametrization strategy is correct** (WS2 single-skill, WS5 generalizes). The only fix needed is to ship empty-parametrized in WS2 rather than single-skill (A2.3) to avoid the merge hazard.
5. **Risk table is reasonably complete** — R1 (loader), R4 (MadDM tractability), R7 (combiner push-back), R9 (summary contract regex) are all real and correctly owned.
6. **Commit-message convention pinned from actual `git log`.** Drafter verified `W<N>:` prefix, sub-commit `W<N>(<k>):` form, no Co-Authored-By. I re-verified — correct.
7. **Explicit out-of-scope list (§E) ends with "flip `status:` in `constraints.yaml`" as the only future-work diff** — accurate and load-bearing for the sustainability of this architecture.
8. **Dispatch model (prose directives, not `Skill(...)`)** correctly inherited from synthesis D4; no drift.
9. **"Second-to-merge rebases" for `plugin.json`** is the right merge policy for a declared JSON array. Should be extended to `test_skill_structure.py` (CX.1).
10. **Absolute paths throughout.** Satisfies the repo's preference and the Sonnet implementer's need for unambiguous filenames.

---

## Section 5 — The 5 decisions the synthesizer must make

**D-SYN-1. Who owns `summary.json`?**
Options: (a) WS1 ships the schema + a stub reader; WS2 ships the writer. (b) WS2 owns both schema and writer; WS1's `demo/SKILL.md` reads "whatever file is there" and degrades gracefully on missing keys. (c) Drop the contract; `/demo` reads Claude's own transcript state.
*Recommend (a) — concrete schema file in `_shared/summary.schema.json` at WS1, validated by `test_constraints_yaml.py`'s sibling.*

**D-SYN-2. Does the `dark-su3` `run_ready`-with-zero-ready-constraints branch loop to Step 2, cancel, or show a new "nothing to run" gate?**
A4.1 — synthesis is silent, plan invents the loop. The user's mental model matters: looping back suggests retry; cancelling suggests fail-fast. Either is fine, but picking one in the synthesizer determines the structure-test's expected state machine.
*Recommend: loop back to Step 2 with the message. Matches the plan; user retains agency to pick different constraints if any ever become ready.*

**D-SYN-3. Is `test_skill_structure.py` shipped parametrized-over-all-three-skills in WS2 (with skip-if-missing) or single-skill and extended by WS3/WS4/WS5?**
A2.3 / CX.1. Parametrize-and-skip eliminates the merge hazard completely. Single-skill matches the plan as written but guarantees two parallel workstreams touching the same test file.
*Recommend: parametrize-and-skip in WS2. Trivial change; kills an entire risk category.*

**D-SYN-4. How is ModelSpec physics correctness gated?**
A1.4 / CX.5. Options: (a) every YAML must carry `status: stub|provisional|verified`; reviewer rejects if `verified` without a verification note. (b) Block WS2 on a physicist-human sign-off of WS1's YAMLs. (c) Accept schema-only validation; flag physics-correctness as known-R2, iterate in fixup commits.
*Recommend (a). The repo's existing convention has TODOs in commit messages (`W2: add skill_env.yaml pinning SPheno 4.0.5 with TODO sha256`); `status: stub` matches.*

**D-SYN-5. Does the loader-check for `plugins/hep-ph-toolkit/_shared/` happen as a blocking prerequisite to any work, or as a WS1 first-commit gate?**
A1.1 / synthesis R10. If the loader rejects `_shared/` at top level, every file path in the plan is wrong and all five workstreams restart.
*Recommend: extract the loader-check into a WS0 (15-minute task) that precedes WS1. WS0 either (a) confirms loader OK, or (b) downgrades plan to `_shared/` inside `skills/` and the synthesizer reissues paths. Do not let WS1 discover this mid-work.*

---

## Section 6 — Missing from the risks list

The drafter's §F is good but these were skipped:

- **R11 (not listed):** `/hep-plotting` is a **reference skill** per memory `project_dm_tool_roles` and synthesis §D4. Step 4 says "invoke `/hep-plotting` guidance to produce `summary.png`" — but the skill is a decision tree, not a plotter. The SKILL.md needs concrete matplotlib/mplhep guidance, not a reference punt. Not called out in R4 (which is MadDM-focused).
- **R12 (not listed):** The `test_skill_structure.py` assertions rely on **parsing markdown with embedded JSON blocks**. Markdown JSON parsing is brittle — a stray blank line or trailing comma breaks the parser. The plan says nothing about robustness. Recommend: use `python -c "import json; json.loads(...)"` on extracted fenced blocks, explicitly.
- **R13 (not listed):** The plan's `claim_source` comment-header convention for the YAMLs (my CX.5 pin) is invented; it does not exist in existing `_shared/tests/fixtures/dark_su3_spec.yaml` or the modelspec schema. If introduced, should it be a schema field or a comment?
- **R14 (not listed):** `/install` preflight check assumes four configured paths (madgraph/sarah/spheno/wolfram). The rewritten `/demo` inherits this. But `/sarah-build` + `/spheno-build` + `/madgraph` + `/maddm` chain implicitly requires MadDM being configured — not in the preflight's key list. If the user runs `/demo`, passes preflight, then hits `/maddm` not installed, they see a cryptic error. Out of scope for this plan but worth a note.
