# 2HDM+a Plan Draft — Skeptic

Author: plan-skeptic
Method: synthesis-vs-plan diff; attack the seams.

---

## 1. Synthesis → plan faithfulness gaps

- **P1–P7 deliverables**: all seven present, each with success criterion. Faithful.
- **R1/R2/R3 probes**: faithfully cover synthesis "planner-to-resolve" items 1/2/3. Good.
- **10-item gate (G1–G10)**: not enumerated in plan. Plan says "the 10 checks from synthesis (G1–G10)" and defers to a single sonnet "gate-evaluator" sub-agent. **Gap**: the plan never restates the gate criteria, so the gate-evaluator agent's prompt is implicit. If sonnet reads only the plan, it must follow a back-pointer. Fix: inline G1–G10 into the gate-evaluator prompt verbatim, or include them as a checklist in the plan itself.
- **Fix-loop scope guard**: synthesis lists 5 forbidden prefixes + 5 kill-switch conditions; plan §"Phase 2" only restates the iteration cap and reproduces "fix in scope" prose. **Gap**: plan never enumerates the forbidden prefixes for the opus reviewer's `git diff --name-only` check. Reviewer-prompt is too thin to enforce the guard mechanically. Fix: paste the 5 forbidden prefixes verbatim into the opus reviewer prompt.
- **Dual patch sentinel**: present (PT1 prompt §"Patch sentinel: dual check"). The grep is exact, mtime is named, and `.patched` write is specified. But: synthesis specifies `mtime(param_card.dat) > mtime(maddm_run/Cards/.output_marker)`; plan says `mtime(param_card.dat) > mtime(.output_marker)` with no path. Fix: spell out the marker path. Also, **`.output_marker` is never created by the plan** — neither MG5 nor the playtest steps explicitly write it. Sonnet will be left guessing how mtime ordering is established. Fix: add a phase-(1.5) step "stat Cards/param_card.dat right after `output`, store mtime in playtest_log/output_mtime.txt" so the sentinel has a real reference.
- **±2% Ωh² band**: present in PT1 success criteria as `[9.95, 10.36]`. Faithful.
- **`VERDICT:` 3-line header + 5-line summary**: present and exact. Faithful.

## 2. P4 reconstructibility verdict — HARD CALL: NOT RECONSTRUCTIBLE

The critique was unambiguous: `iter_6_notes.md` does not exist, and POST_MORTEM only references it; it does not enumerate seven sites in prose. The plan's P4 strategy is "mine POST_MORTEM lines 79/103/117 and FINAL_STATUS lines 67/73/80, plus grep `sections/`." Those lines are *back-references* to the missing file, not descriptions of seven sites. A 30-min sonnet pass will produce a best-effort enumeration of *some* renderer issues from the prose it can find, but it will not faithfully reconstruct the original list because the original list was never written down.

**Verdict**: P4 should not be a runtime gate at all. The plan correctly identifies it as documentation-only and applies the R3 fallback (downgrade G4 to warning unconditionally). But P4's stated success criterion ("exactly 7 enumerated sites") sets sonnet up to fabricate to hit the count. **Fix (hard-block)**: change P4's success to "enumerate as many distinct renderer sites as POST_MORTEM/FINAL_STATUS support, with `RECONSTRUCTION INCOMPLETE` header if <7." Don't ask for a number sonnet can't honestly produce. G4 starts as `warning`, not `pass`.

## 3. Worktree scheme attack

- **Prep → playtest branching**: plan says playtest branches "from the post-prep tip" but never specifies *when* the prep worktree commits and merges. If P1–P7 each commit but the prep branch is not merged/fast-forwarded to a tip the playtest worktree can branch from, the playtest worktree sees stale `main`. **Hard-block fix**: insert an explicit step "manager fast-forwards `main` to `2hdma/prep-20260424` HEAD after gate passes" or equivalently "playtest worktree branches from `2hdma/prep-20260424` HEAD, not `main`."
- **Per-failure-class fix worktree**: plan says fix worktrees branch from "playtest tip" — fine for reproduction, but if two classes (e.g., `patcher` and `schema`) both produce diffs, plan never specifies how they merge. Manager dispatches the diffs sequentially but never describes the merge agent. **Risk (real)**: two fix worktrees touch different files cleanly → trivial merge; touch same file → conflict, no resolver named. **Fix**: serialize fix-loop dispatch (one class at a time, merge before next dispatches) — the run cap is 5 attempts anyway so parallelism gains are tiny. Alternatively, name a "fix-merger" sonnet step. Pick one.
- **Re-playtest worktree (`2hdma-playtest-2`)**: plan implies it branches from the merged-fix tip but never says so. Specify.

## 4. Sonnet/opus handoff issues

- **Try-counter state**: plan says "after 3 sonnet attempts" but manager has no cross-turn memory other than tasks/log. **Hard-block fix**: counter must live in `.shift-manager/run-20260424-202956/state/fix_attempts.json` (JSON map: `{class: count}`), updated by manager *as a deliberate write step* between dispatches. Without this, "3 attempts" is unenforceable.
- **Opus rejects synthesis-sanctioned decision**: e.g., opus reviewer reads `Wchi=0` (sanctioned by R2) and rejects it as wrong physics. Plan has no tie-break. **Fix**: opus reviewer prompts must be seeded with a "synthesis-locked decisions" preamble (Wchi value, schema relaxation, ±2% band, fixture-only scope, etc.). Reviewer must not relitigate locked decisions; if it tries, escalate to opus-opus where the synthesis doc itself is the tiebreaker.
- **Opus-opus deadlock**: plan says "if opus-opus also disagrees with itself across two passes, escalate to synthesizer" — fine, but synthesizer is a once-per-run role. Concretely this means HALT and write a partial verdict. Make that explicit.

## 5. Phase-1 single-sonnet feasibility

- **Single sonnet doing preflight + fixture deploy + SARAH MakeUFO (~2 min Wolfram) + MG5 output + patch + MG5 launch (potentially 20 min) + parse + plot + summary + verdict** is a long chain. SARAH alone is ~2 min; MG5 launch can be ~5–20 min; total tool time alone could approach the 15-min hard cap before any sonnet thought time. **Risk**: sonnet runs out of context or wall time mid-launch. **Fix**: explicit fallback — if `MadDM_results.txt` is unwritten when wall-clock hits 25 min on the retry, sonnet writes a `verdict.md` with `VERDICT: FAIL` + `phase: mg5_launch` blocker issue and exits. Plan hints at this with the `kill -ABRT` rule but only for a single 20-min `launch` overrun, not for the global wall.
- **Mid-run timeout**: plan never says what state to leave behind on timeout. Specify: always write `verdict.md` (even partial), always write `issues.jsonl` (open issue with last completed phase), always commit. Otherwise the fix-loop has nothing to read.

## 6. Cross-workstream conflicts

- **`_shared/summary.schema.json` ownership**: plan declares 2hdm-a owns it (via R1). But the SD plan was in flight when this draft was written. If SD also wants to edit the schema, two worktrees collide. **Fix (hard-block)**: introduce a sentinel file `plugins/hep-ph-demo/skills/_shared/.schema_owner.lock` containing `2hdm-a/run-20260424-202956`. SD plan must read this and route schema edits through 2hdm-a's R1 probe (or wait). Manager creates the lock when P3 starts; removes it when run ends.
- **SARAH serialization with SD**: plan says "manager schedules SD's SARAH steps and 2hdm-a's playtest serially." **HOW** is unspecified. Manager has no live process scheduler. Realistic mechanisms: (a) file-based mutex `/tmp/sarah_kernel.lock` checked at the start of any `wolframscript` invocation, with sonnet polling for ≤2 min; (b) manager-mediated dispatch order (don't spawn SD's SARAH until 2hdm-a's playtest writes `sarah_done.marker`). Pick (b) — simpler, no new code paths in the skills. Document explicitly.

## 7. Time-budget pressure points

- Plan totals: prep 30 min wall (parallel) + playtest 30 min (with retry) + fix 45 min + re-playtest 30 min = **135 min worst case**, vs synthesis hard-stop **180 min**. Headroom: 45 min.
- But: plan §"Failure modes" item 10 already cites "150 min worst case" — drafter and skeptic both notice the budget is tight. The 45-min headroom evaporates if (a) any prep step blows estimate (P2 is budgeted 25 min, drafter explicitly notes "may exceed"), (b) Wolfram contention adds wait, (c) opus review iterations on prep tasks are not counted.
- **Hard-block fix**: opus review time must be added to the prep wall budget. With 7 prep tasks each potentially seeing 1–2 opus rounds, add ≥10 min. Budget should be: prep 40 min (parallel + opus) + playtest 30 + fix 45 + re-playtest 30 = 145 min. Still under 180, but if any phase overruns, the manager must HALT, not "find a way."
- **Missing**: explicit budget-check step. Manager should log wall-clock at each phase transition and abort if cumulative >150 min when entering re-playtest.

## 8. Missed in-plan failure modes

1. **P6 sys.path fix breaks another skill**: plan picks "sys.path.insert" approach but never grep-checks for *other* importers of `maddm_run`. If singlet-doublet or dark-su3 SKILL.md has the same import, P6's per-skill workaround is fine; if they import via a different path that this fix breaks, it's a regression. **Fix**: P6 must include `grep -rn "maddm_run" plugins/` and report all importers. If multiple importers exist, prefer the package-shim path (P6 alternative b) over inline sys.path.
2. **`.patched` sentinel commits as repo noise**: `demo_output/2hdm-a/playtest_log/.patched` lives under `demo_output/` which is git-tracked in this repo (`demo_output/2hdm-a/fix_loop/POST_MORTEM.md` is committed). The marker will commit too. Either gitignore `demo_output/2hdm-a/playtest_log/.patched` (and `.output_marker`, `output_mtime.txt`) or accept it as artifact-not-noise. Plan is silent. **Fix**: add to P1 deliverable a tiny `.gitignore` line under `demo_output/2hdm-a/playtest_log/` for sentinels.
3. **Pre-run hash capture order**: P7 captures env *during* prep — i.e., AFTER P1 has already mutated the working tree. The captured `git rev-parse HEAD` will reflect prep commits, not the pre-run state. If issues need to reproduce against pre-prep `main`, the SHA is wrong. **Fix**: P7 captures TWO SHAs — `git_sha_pre_run` (read from `.shift-manager/run-20260424-202956/scoping/`-era `main` tip) and `git_sha_at_capture` (the prep tip). Issue schema includes both.
4. **Stale `$SARAH_ROOT/Models/TwoHdmAfix/`**: G9 checks idempotency but plan never says who cleans it if diff is dirty. Sonnet playtest agent must `rm -rf $SARAH_ROOT/Models/TwoHdmAfix/` before redeploying — otherwise an aborted prior run leaves cruft. Add to PT1 phase 1.
5. **Issue ID collisions across re-playtest**: PT1 says "Issue IDs `2hdma-001` upward." On re-playtest, who counts? If `2hdma-playtest-2` starts from `2hdma-001` again, IDs collide with first-pass issues. **Fix**: re-playtest sonnet reads existing `issues.jsonl`, starts from `max(id)+1`.
6. **Opus reviewer can't see worktree FS**: most agent dispatches assume opus can read `git diff --name-only` against allowed prefixes. Opus reviewing a sonnet diff *inside a worktree* needs the worktree path passed in its prompt. Plan never specifies that the manager hands the worktree path to opus. **Fix**: every opus reviewer prompt template must include `WORKTREE_PATH=<abs path>`.
7. **R2 timing race**: plan says "launch R2 in parallel with P2; if R2 finishes first, P2 incorporates the answer. If P2 finishes first with one assumption, a follow-up patch lands after R2." That follow-up patch is unscoped — who dispatches it? Adds to attempt counter? Counts toward fix-loop budget? **Fix**: declare R2-followup as a Phase 0 task (P2b), not a fix-loop attempt. Don't burn fix budget on a known followup.

---

## Summary

### Hard-blocks (must fix before plan ships)

1. **G1–G10 not inlined into gate-evaluator prompt** (§1).
2. **Fix-loop scope-guard prefixes not pasted into opus reviewer prompt** (§1).
3. **`.output_marker` referenced but never created**; mtime sentinel will fail (§1).
4. **P4 success criterion of "exactly 7" sets sonnet up to fabricate** — relax to "as many as evidence supports" (§2).
5. **Prep→playtest branching point unspecified** (§3).
6. **Try-counter has no persistence mechanism** (§4).
7. **Cross-workstream schema-edit lock missing** (§6).
8. **SARAH serialization mechanism unspecified** (§6).
9. **Opus review time not in budget; no cumulative-budget abort** (§7).
10. **Multi-importer check missing for P6** (§8.1).

### Nice-to-fixes

- Synthesis-locked-decisions preamble for opus reviewers (§4).
- Mid-run timeout always-write rule (§5).
- Sentinel files in .gitignore (§8.2).
- Pre-run vs at-capture SHA both stored (§8.3).
- $SARAH_ROOT/Models/TwoHdmAfix/ clean step in PT1 (§8.4).
- Issue-ID continuation across re-playtest (§8.5).
- WORKTREE_PATH passed to all opus reviewers (§8.6).
- R2-followup as P2b, not fix-loop attempt (§8.7).
- Fix-loop dispatch serialized to avoid worktree merge conflicts (§3).

### Bottom line

The plan is faithful to the synthesis on the big decisions (fixture path, ±2% band, dual sentinel, 5-attempt cap, scope guard prose) but thin on operational mechanics (counters, locks, branching points, budget tracking). The 10 hard-blocks above are all small textual fixes — none require redesign. Synthesizer should accept the plan's structure and require the synthesizer-pass to inline the missing prompt content and state files.
