# 2HDM+a Implementation Plan (draft)

Author: plan-drafter
Inputs: locked synthesis, critique, proposal, scope.
Execution model: sonnet implementer + opus reviewer pair, up to 3 cycles per task, then opus-opus. Manager dispatches; manager does not code or review.

---

## Phase structure

- **Phase 0 (Prep)**: Seven prep tasks P1–P7 from synthesis, plus three planner-to-resolve probes (R1–R3). Mostly **parallel**, with a single ordering constraint: P3 (schema edit) must complete before any task that emits a `summary.json` schema check, and P4 (iter_6_notes reconstruction) is documentation-only so it does not gate runtime. Everything in Phase 0 is gated by the **10-item go/no-go gate** before Phase 1 spawns.
- **Phase 1 (Playtest)**: Single sonnet agent executes the locked recipe end-to-end inside a fresh worktree. Hard cap 15 min; one retry permitted (30 min total). One-shot, not multi-variant. Opus reviews the verdict + issue log.
- **Phase 2 (Fix-loop, conditional)**: Spawned only if Phase 1 produces blocker-severity issues that fall inside the scope guard. Per-failure-class budget = 3 iterations; total run cap = 5 fix attempts. Each iteration is a sonnet implementer + opus reviewer pair.

---

## Worktree scheme

Manager will create worktrees with the `superpowers:using-git-worktrees` skill. Branches are local-only (no GitHub).

- **Prep worktree**: `/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-prep/` on branch `2hdma/prep-20260424`. All P1–P7 + R1–R3 land here. Each prep task is its own commit. After the gate passes, prep worktree is merged back to `main` (or its branch fast-forwarded).
- **Playtest worktree**: `/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-playtest/` on branch `2hdma/playtest-20260424`, branched from the post-prep tip. Read/write isolated; only writes to `demo_output/2hdm-a/`. No code edits expected here.
- **Fix-loop worktrees** (one per failure class, lazily created): `/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-fix-<class>-<n>/` on branch `2hdma/fix-<class>-<n>-20260424`. `<class>` ∈ {patcher, schema, sarah_cmd, parse, plot}. Each fix worktree starts from playtest tip (not prep) so reproduction is faithful.
- **Cross-workstream coordination**: SD has its own worktree tree under `.../singlet-doublet-*`; dark-su3 likewise. Shared SARAH install dir (`/Users/yianni/SARAH/SARAH-4.15.3/`) and MG5 install dir are read-shared. Per-run `demo_output/<model>/` is write-isolated by worktree.

---

## Phase 0 tasks

Run P1, P2, P4, P5, P6, P7 in parallel as a single batch. P3 runs in parallel too but its result must be acked by SD/dark-su3 leads (R1) before being relied on by gate G3.

### P1: Clean stale demo_output/2hdm-a/
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: directory removed; note at `demo_output/2hdm-a/.cleaned` (one-line timestamp + git sha at clean time).
- Success: `test ! -d demo_output/2hdm-a/` AND `git status --porcelain` shows no leftover tracked files in that path.
- Parallel with: P2, P4, P5, P6, P7
- Estimated: 2 min

### P2: Audit patch_paramcard.py against POST_MORTEM
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: `plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md` listing every block written by the 445-line reconstruction (HMIX, ZAMIX θ_a=0.1, ZHMIX, ZPMIX α=−0.1, Wchi, etc.). For each block, mark KEEP+rationale, REMOVE, or DEFER. The agent may modify `patch_paramcard.py` to remove blocks marked REMOVE.
- Success: AUDIT.md exists; every block has a decision; if `Wchi` decision = `0`, the script is updated and a unit-style test (`python3 patch_paramcard.py --dry-run` or equivalent) shows the new output; if decision is "leave at 1 GeV", a citation to MadDM source is included.
- Parallel with: P1, P4, P5, P6, P7. Coordinates with R2.
- Estimated: 25 min

### P3: Reconcile _shared/summary.schema.json
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: edited `plugins/hep-ph-demo/skills/_shared/summary.schema.json` with explicit field defs for `relic_approx` (bool), `model_source` (string), `model_fixture` (string). Plus a tiny test script `plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` that validates SKILL.md L470-478's example payload AND a stub SD payload AND a stub dark-su3 payload (agent constructs realistic stubs from the three SKILL.md files).
- Success: `python3 plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` exits 0; all three stubs validate.
- Parallel with: others; gates Phase 1 G3.
- Estimated: 20 min
- **Coordination**: Triggers planner-to-resolve R1 (sign-off from SD/dark-su3 reviewers — opus reviewing this task plays that role).

### P4: Reconstruct iter_6_notes.md (seven renderer sites)
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: `demo_output/2hdm-a/fix_loop/iter_6_notes.md` enumerating the seven renderer patch sites. Sources to mine: `demo_output/2hdm-a/fix_loop/POST_MORTEM.md` lines 79/103/117, `FINAL_STATUS.md` lines 67/73/80, plus grep through `plugins/model-building/skills/sarah-build/scripts/sections/` for likely render functions (Dirac singlet emission, conj[] handling, DEFINITION[EWSB][Phases], `\[ImaginaryI]` Yukawa prefix, field-name vs component-name rule, Mchi→mchi prefix mangling, `a → a0` / `a0s` collision rename). Each of the 7 entries gets `file:line` ref.
- Success: file exists with exactly 7 enumerated sites, each with at least one `plugins/model-building/.../sections/<file>.py:<line>` reference. If fewer than 7 distinct sites can be located, document the gap and mark as `DEFERRED — fewer than 7 sites identifiable from POST_MORTEM`. Documentation only; not a runtime requirement.
- Parallel with: P1, P2, P5, P6, P7
- Estimated: 30 min
- **Fallback**: If genuinely unreconstructible (see "Failure modes" below), emit a stub with whatever the agent could find and mark `iter_6_notes.md` as `RECONSTRUCTION INCOMPLETE`; gate G4 may then be downgraded to a warning per R3.

### P5: Strip --skip-render references
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: `plugins/hep-ph-demo/skills/2hdm-a/SKILL.md` rewritten so L245 (and any sibling) invokes `wolframscript -code` directly with the inline SARAH boot. No `--skip-render` token anywhere under `plugins/hep-ph-demo/skills/2hdm-a/`.
- Success: `grep -rn "skip-render\|skip_render" plugins/hep-ph-demo/skills/2hdm-a/` exits with no matches; SKILL.md still parses as valid markdown; new wolframscript snippet is copy-pasteable and references `$SARAH_PATH` from `config.json`.
- Parallel with: P1, P2, P4, P6, P7
- Estimated: 15 min

### P6: Fix maddm_run import landmine
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: SKILL.md L279 (or whatever line currently imports `from scripts.maddm_run import ...`) wrapped with an explicit `sys.path.insert(0, "plugins/monte-carlo-tools/skills/maddm/scripts")` preamble, plus inline comment explaining the cross-skill import. Alternatively, if trivially refactorable, copy `maddm_run.generate_maddm_script` into a thin shim under `plugins/hep-ph-demo/skills/2hdm-a/scripts/`. Prefer the sys.path approach (less duplication).
- Success: `cd /Users/yianni/Projects/hep-ph-agents && python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run; print(maddm_run.__file__)"` exits 0 from a clean shell.
- Parallel with: P1, P2, P4, P5, P7
- Estimated: 10 min

### P7: Capture environment snapshot
- Agent: sonnet
- Worktree: `2hdma-prep`
- Deliverable: `demo_output/2hdm-a/playtest_log/env.json` containing: full `config.json` body, `git rev-parse HEAD`, SARAH version (parse from `$SARAH_ROOT/Package.m` or version banner), MG5 version (`mg5_aMC --version` or banner), MadDM version (parse plugin), Python version, Wolfram version (`wolframscript -version`). One-shot script committed at `plugins/hep-ph-demo/skills/2hdm-a/scripts/capture_env.py` so playtest agent can re-run it.
- Success: `env.json` valid JSON with all eight keys present (no nulls except for tools that legitimately have no version string); `capture_env.py` is idempotent.
- Parallel with: P1, P2, P4, P5, P6
- Estimated: 15 min

### R1: Schema sign-off probe (planner-to-resolve #1)
- Agent: sonnet (probe), opus (decide)
- Deliverable: `.shift-manager/run-20260424-202956/plan/r1_schema_signoff.md` — read SD's and dark-su3's SKILL.md `summary.json` example payloads, confirm P3's relaxed schema validates them. Opus reviews and writes a one-line decision: `OWNER: 2hdm-a; ACK: SD-clean, dark-su3-clean`.
- Success: file exists with explicit ACK lines for SD and dark-su3.
- Serial after P3.
- Estimated: 10 min

### R2: Wchi=0 vs 1 GeV decision probe (planner-to-resolve #2)
- Agent: sonnet (probe), opus (decide)
- Deliverable: `.shift-manager/run-20260424-202956/plan/r2_wchi_decision.md` — inspect MadDM source (`plugins/monte-carlo-tools/skills/maddm/` and the MG5 plugin install) for the `define darkmatter` auto-detect path; specifically, find where it reads `DECAY` widths and what threshold (if any) flips a particle off the DM-candidate list. Opus writes the decision: either `Wchi := 0.0` (set in patcher) or `Wchi := 1 GeV with citation: <file:line>`.
- Success: file exists with a one-line decision and a verbatim quote of the relevant MadDM check.
- Serial: feeds into P2 (P2 may need to be redone if R2 lands late). Recommended order: launch R2 in parallel with P2; if R2 finishes first, P2 incorporates the answer. If P2 finishes first with one assumption, a follow-up patch lands after R2.
- Estimated: 20 min

### R3: Gate-downgrade policy (planner-to-resolve #3)
- Agent: opus (decide directly — no implementation)
- Deliverable: `.shift-manager/run-20260424-202956/plan/r3_gate_downgrade.md` — explicit policy: if prep budget is blown, which of G2/G3/G4/G6 may be downgraded to warning, in what order, and what the auto-downgrade trigger is.
- Recommended decision (drafter's suggestion): G4 (iter_6 notes — pure docs) downgradable to warning unconditionally; G6 (import landmine) downgradable iff a manual workaround is documented in the playtest prompt; G2 and G3 stay non-negotiable because they affect runtime correctness.
- Estimated: 5 min, no worktree needed.

---

## Go / no-go gate (manager evaluates after Phase 0 completes)

Manager dispatches a single sonnet "gate-evaluator" sub-agent that runs the 10 checks from synthesis (G1–G10) and writes `demo_output/2hdm-a/playtest_log/gate_status.json` with each gate's pass/fail/warning state plus evidence path. If any non-negotiable gate fails (G1, G5, G7, G8, G9, G10), HALT and escalate. If a downgradable gate fails (G2, G3, G4, G6), apply R3's policy.

---

## Phase 1 task

### PT1: Execute 2HDM+a playtest
- Agent: sonnet
- Worktree: `2hdma-playtest` (fresh, branched from post-prep tip)
- Practitioner prompt (exact text the manager hands to the sonnet agent):

> You are the 2HDM+a playtest practitioner. Your job is to validate the hand-crafted SARAH fixture path end-to-end and produce the artifact tree at `demo_output/2hdm-a/`.
>
> CONSTRAINTS:
> - Hard scope: do not edit anything outside `demo_output/2hdm-a/` and `plugins/hep-ph-demo/skills/2hdm-a/`. If you find yourself wanting to edit elsewhere, STOP and log a blocker issue.
> - Use the FIXTURE path. Do NOT invoke `/lagrangian-builder` or `/sarah-build` interactively for 2hdm-a. The renderer is debt; copy `plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/*.m` → `$SARAH_ROOT/Models/TwoHdmAfix/`, then drive `wolframscript -code '<<SARAH\`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'` directly.
> - Hard cap: 15 minutes per pass. One retry permitted on transient failure (Wolfram timeout, MG5 plugin reload). Total wall = 30 minutes.
> - Phase order is mandatory: (0) preflight + import-landmine check, (1) clean+deploy fixture, (2) SARAH MakeUFO, (3) vertex sanity grep, (4) MG5 output, (5) patch_paramcard.py + write `.patched` marker, (6) MG5 launch (MadDM relic), (7) parse, (8) plot, (9) summary, (10) verdict.
> - Schema validate `summary.json` against `_shared/summary.schema.json`. If schema validation fails, log as `severity: warning` (not blocker), proceed.
> - Issue log: append every anomaly to `demo_output/2hdm-a/playtest_log/issues.jsonl` using the locked schema (see synthesis §"Final issue-log JSON schema"). Issue IDs `2hdma-001` upward.
> - Verdict file `demo_output/2hdm-a/playtest_log/verdict.md` MUST start with three lines exactly:
>   ```
>   VERDICT: PASS|FAIL
>   MODEL_SOURCE: hand_crafted_sarah_model_fixture
>   RENDERER_STATUS: debt
>   ```
>   followed by a 5-line summary.
> - Patch sentinel: dual check. (a) `grep '^   1 .*1.000000e+00' demo_output/2hdm-a/maddm_run/Cards/param_card.dat` returns at least one line; (b) `mtime(param_card.dat) > mtime(.output_marker)`. Write `demo_output/2hdm-a/playtest_log/.patched` after step 5.
> - On 20-minute single-`launch` overrun: `kill -ABRT` + `sample <pid>` for evidence, log blocker, abort.
> - On any out-of-scope diff need: STOP, log blocker, exit (do NOT modify outside scope; that is the fix-loop's job, dispatched separately by the manager).

- Success criteria (opus reviewer applies all):
  1. `demo_output/2hdm-a/playtest_log/verdict.md` exists with first line `VERDICT: PASS`.
  2. `Ωh²` ∈ [9.95, 10.36] in `demo_output/2hdm-a/relic.json`.
  3. Dominant channel logged (≥30% on `chichibar_bbx` is soft; <30% logs minor finding only).
  4. Both patch sentinel checks pass; `.patched` marker exists.
  5. `summary.json` validates against schema (or warning logged with rationale).
  6. `issues.jsonl` exists (may be empty; absence ≠ pass).
  7. Wall time < 30 min.
  8. `git diff --name-only` in worktree shows zero files outside the scope-guard prefixes.

- Issue-log path: `demo_output/2hdm-a/playtest_log/issues.jsonl`
- Deliverables: full artifact tree per synthesis §Q9 (relic.json, summary.json, summary.{pdf,png}, maddm_run/, playtest_log/{run.log, timing.json, issues.jsonl, env.json, verdict.md, .patched, git_sha.txt, gate_status.json}).
- Estimated: 15 min cold, 30 min with retry.

---

## Phase 2 (conditional fix-loop)

**Trigger**: Phase 1 produces ≥1 issue with `severity: blocker` AND `fix_owner_hint` ∈ {patcher, schema, fixture, skill_prose}. Issues with `fix_owner_hint: renderer` are out of scope — log and defer.

**Dispatch pattern (per failure class)**:
1. Manager picks the highest-severity blocker not yet attempted.
2. Manager creates worktree `2hdma-fix-<class>-<iter>` from playtest tip.
3. Sonnet implementer prompt: "Read `demo_output/2hdm-a/playtest_log/issues.jsonl` issue `<issue_id>`. Reproduce via the `auto_repro_command`. Fix in scope (`plugins/hep-ph-demo/skills/2hdm-a/**` or `demo_output/2hdm-a/**`). Append to `fix_attempts` array with `{ts, diff_path, outcome}`. Re-run the playtest's failing phase only (not the full pipeline). Output: diff + new outcome line."
4. Opus reviewer prompt: "Verify the fix is in-scope (`git diff --name-only` against allowed prefixes). Verify the issue's `auto_repro_command` now passes. If yes → outcome `pass`. If no but progress made → outcome `fail`, increment iteration. If diff escapes scope → outcome `aborted_scope`, hard halt."
5. Up to 3 iterations per class. After 3, mark class `unfixable_in_budget`, escalate.

**Stop conditions** (any one halts Phase 2):
- All blockers `outcome: pass`.
- 5 total fix attempts across all classes consumed.
- Per-class iteration limit of 3 hit on every remaining class.
- Wall-clock 45 min for fix phase exceeded.
- Any `outcome: aborted_scope`.

**Re-playtest after fix**: Once Phase 2 halts, manager dispatches a single PT1-equivalent re-run in a fresh `2hdma-playtest-2` worktree to confirm the fixes integrate. If second playtest also fails on a different class, escalate to opus-opus pair (no further sonnet attempts).

**Manager stop heuristic for the fix loop**: Stop iterating when (a) all blockers resolve, OR (b) total fix attempts hit 5, OR (c) the same issue class fails 3 times (treat as architectural — outside this run's authority). The manager does not re-evaluate physics; it counts.

---

## Three planner-to-resolve answers

### (1) Schema edit sign-off
**Decision**: 2hdm-a fix agent owns `_shared/summary.schema.json`. SD/dark-su3 sign-off is implicit via R1 probe (sonnet enumerates SD + dark-su3 example payloads, opus reviewer validates). No human sync required. Risk acceptance: if SD/dark-su3 emit fields not anticipated by P3, schema treats them as `additionalProperties` warnings, not failures — explicit field defs only for the three known extras (`relic_approx`, `model_source`, `model_fixture`).

### (2) Wchi=0 vs 1 GeV
**Decision**: defer to R2 probe. Drafter's prior: `Wchi := 0.0` is correct for stable DM and is what MadDM expects. `Wchi := 1 GeV` is suspicious because MadDM's `define darkmatter` uses width as a stability heuristic for some configurations. R2 sonnet probe inspects MadDM source; opus writes the binding decision. P2 incorporates whichever R2 returns. If R2 returns "no clear evidence either way," default to `Wchi := 0.0` and add a comment.

### (3) Gate downgrades under budget pressure
**Decision** (per R3):
- **G4** (iter_6_notes.md docs): downgradable to warning **unconditionally** — pure docs, no runtime impact.
- **G6** (maddm_run import): downgradable to warning **only if** a one-line `sys.path.insert` workaround is documented inline in the playtest prompt.
- **G2** (patcher audit): non-downgradable — runtime correctness depends on it.
- **G3** (schema reconciled): non-downgradable — failure surfaces as warning at playtest time anyway, so the gate is the only place to catch it pre-run.
- **G1, G5, G7, G8, G9, G10**: non-negotiable per synthesis.

---

## Failure modes within the plan itself

1. **P4 unreconstructible**: POST_MORTEM may not actually contain enough detail to enumerate seven distinct renderer sites — the references are scattered prose, not a list. **Fallback**: P4 emits whatever it can find (maybe 3–5 sites) and marks the file `RECONSTRUCTION INCOMPLETE`. Gate G4 downgrades to warning per R3. Renderer-backport workstream remains unblocked because the partial list is still better than nothing.
2. **R2 inconclusive**: MadDM source may not have a single canonical `define darkmatter` width check. **Fallback**: default to `Wchi := 0.0`, document the uncertainty in `patch_paramcard.AUDIT.md`, flag as a known unknown for the next run.
3. **P3 schema breaks SD or dark-su3 payloads**: relaxed schema may still reject SD payload fields the drafter didn't anticipate. **Fallback**: P3's test script catches this; sonnet adds the missing field def or escalates as a parallel-workstream coordination issue, dispatched as its own R1-followup.
4. **Wolfram contention with SD**: serialization is recommended, not enforced. If SD's playtest agent and 2hdm-a's prep both invoke `wolframscript` simultaneously, one may hang on the kernel. **Fallback**: manager schedules SD's SARAH steps and 2hdm-a's playtest serially. Dark-su3 (analytic, no Wolfram) runs fully parallel.
5. **Patcher-audit (P2) drags >25 min**: the 445-line reconstruction has many blocks; auditing each may exceed the budget. **Fallback**: opus reviewer at iteration 2 declares "audit-good-enough" if the four highest-risk blocks (HMIX, ZAMIX θ_a, Wchi, alpha) are decided; lower-risk blocks (ZHMIX, ZPMIX) may default to KEEP with a TODO comment.
6. **Phase 1 hits an issue with `fix_owner_hint: renderer`**: by the synthesis-locked rules, these are out of scope. **Fallback**: log as `blocker` with `outcome: deferred_renderer`, do not spawn fix-loop, surface to synthesizer as "renderer-backport workstream needed." Run still ends in `VERDICT: FAIL` — that's the honest outcome.
7. **Worktree creation fails** (e.g., dirty index, git lock): manager's first dispatch will fail. **Fallback**: dispatch a tiny "worktree-medic" sonnet that runs `git worktree prune`, `git status` and either resolves or escalates.
8. **Playtest agent ignores the scope guard**: sonnet may "helpfully" edit `plugins/model-building/...` to fix a renderer issue. **Fallback**: opus reviewer's first check is `git diff --name-only`; out-of-scope diffs trigger immediate revert + `outcome: aborted_scope` log + blocker.
9. **Sonnet-opus disagreement loop**: sonnet implements, opus rejects, sonnet re-implements identically. **Fallback**: after 3 sonnet attempts on the same task, escalate to opus-opus (per execution model). If opus-opus also disagrees with itself across two passes, the manager halts that task and escalates to the synthesizer.
10. **Time budget overrun across all phases**: prep 45 min + playtest 30 min + fix 45 min + re-playtest 30 min = 150 min worst case. If real wall time exceeds 180 min, manager halts and writes a partial `verdict.md` documenting which phase consumed the budget — better than running indefinitely.
