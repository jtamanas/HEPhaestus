# Dark SU(3) Plan Draft — Skeptic

Author: plan-skeptic
Method: synthesis-vs-plan diff; pattern-match against 2HDM+a critique's 10 hard-blocks; attack the seams.

---

## 1. Synthesis → plan faithfulness gaps

- **Phase-0 prep tasks (P0.1–P0.6)**: all six map to synthesis "Pre-playtest preparation steps 1–6". Faithful in shape. Each has an explicit success criterion. Good.
- **Success-criteria numerics (BP1 ranges, drift bands, flags)**: faithful — `[31.6, 35.0]`, `[2846, 3146]`, `relic_approx:False`, `sigmav_approx:True`, drift `<5%`. Faithful.
- **Scope guard (allowed/off-limits paths)**: §"Scope guard" reproduces synthesis verbatim. Good.
- **Banner exact wording**: pasted verbatim into PT1 prompt and §3 of planner-resolves. Faithful.
- **Issue-log schema v1.1**: PT1 prompt cites "schema v1.1 per synthesis §Issue-log JSON schema" but does **NOT inline the field list**. Sonnet must back-pointer to synthesis. **Hard-block (mirrors 2HDM+a §1 G1–G10 gap)**: paste the schema fields into the PT1 prompt verbatim, otherwise sonnet will guess fields and break aggregation across workstreams.
- **Phase-0 go/no-go gate**: enumerated in plan §"Phase 0 go/no-go gate" but only as manager-side checks. **Gap**: no gate-evaluator sub-agent prompt exists. Manager evaluates locally — fine, but plan never says where the gate decision is logged. Add `preflight/gate_decision.json` deliverable.
- **Off-limits enforcement check**: §"Scope guard" says "manager runs `git diff --name-only` and re-`sha256sum`s shared files" but the **opus reviewer prompt is not drafted** anywhere. Mirror of 2HDM+a hard-block #2: paste the off-limits prefix list into the opus reviewer prompt verbatim.

## 2. F3 implementability verdict — HARD CALL: SKILL.md WALKTHROUGH ONLY

The plan's F3 says "if the sub-agent does have working Skill-tool `/demo` access, attempt it AND record both outputs noting any divergence." Reality check:

- A sonnet sub-agent dispatched via Task has the Skill tool, but its skill list is the same global registry; `/demo` is a slash command in `plugins/hep-ph-demo/commands/` (or a SKILL the plugin exposes). Whether it resolves from inside a sub-agent worktree depends on plugin-load semantics that are NOT verified anywhere in the plan.
- "Run both approaches" with no definition of "divergence" is unactionable. If `/demo` outputs a stdout transcript and the SKILL.md walk produces `findings.md`, what counts as a divergence? String-diff? Banner present in one and not the other? The plan never says.
- **Verdict (hard-block)**: drop the dual-path attempt. The SKILL.md walkthrough is authoritative regardless. If a sonnet probe wants to *try* `/demo` first, it must be a separate P0.0 probe ("does `/demo` resolve as a Skill in a sub-agent?") whose result decides Phase-1 mode. Otherwise the playtest sonnet wastes wall time chasing a path that may not exist.
- **Quote-verbatim rules under SKILL.md walk**: plan says "quote every user-visible string verbatim … picker entries, constraint hooks, summary banner". Good shape, but does NOT enumerate the strings. **Fix**: list them — picker entry #3 label+description (SKILL.md:73), constraint hook label (constraints.yaml:148), walkthrough sentence (MANUAL_WALKTHROUGH.md:90), banner template (synthesis §"Success criteria" para 2). Anything else (intro prose, headers) may be paraphrased.

## 3. Numerical-range feasibility — TIGHT

Plan budgets P0.5 = 5 min and P0.6 = 10 min for the smoke + n∈{200,400,800} baseline. PT1 step 5 re-runs `compute()` at n=400 and n=800 inside the 90-min playtest cap. Three concerns:

- **`compute()` wall-time per call is unknown to the plan.** P0.5 records `wall_seconds` only at n=200; P0.6 then times n=400 and n=800. If n=200 takes ~2s, scaling is fine. If n=200 takes ~30s (Boltzmann Radau on stiff system), n=800 could be minutes. Plan never asserts a wall-time ceiling per call. **Fix (hard-block)**: P0.5 must record `wall_seconds` and abort if `wall_seconds(n=200) > 60s` — that's the canary that n=800 will blow the playtest budget.
- **Convergence drift threshold conflict**: P0.6 says drift 5–25% logs as `major/physics` but does NOT block; drift `>25%` escalates. Synthesis §"Success criteria" item 4 says drift `>5%` is `severity=major`, `fix_scope=physics`. Both agree it's not a Phase-2 candidate (physics, not docs), so the *outcome* is the same, but the plan has invented a 5–25% / >25% split that synthesis does not. **Fix**: collapse to synthesis's binary <5% pass / ≥5% major-non-blocking. Don't add bands the synthesis didn't sanction.
- **Re-run at n=400/800 inside Phase 1**: PT1 step 5 says re-run and compare. If P0.6 already locked the baseline at n∈{200,400,800}, Phase 1 is comparing against a 25-minute-old baseline on the same HEAD. That's a tautology unless the playtest sonnet runs `compute()` itself in the playtest worktree (which it should, but the plan must say so). **Fix**: make explicit "PT1 invokes `compute()` fresh in `dsu3-playtest` worktree; baseline file is the comparand, not the source of the n=400/800 numbers."

## 4. P0.3 ∥ P0.4 parallelism risk — REAL

Plan says P0.3 (grep) and P0.4 (sha256sum + git rev-parse) run in parallel "in the same `dsu3-prep` worktree." Two sonnet sub-agents in one worktree is asking for trouble:

- Both write under `preflight/` — fine if filenames are disjoint (`stale_strings.json` vs `preflight_hashes.json`). They are. So no write collision.
- But: both run `git`-adjacent commands. `git rev-parse HEAD` is read-only; safe. `grep -rn` is read-only; safe. So in *this* specific case, parallelism is benign.
- **Real risk**: if either sub-agent goes off-script and stages or commits, the other sees a moving tree. Plan does not forbid commits inside P0.3/P0.4. **Fix**: PT0 prompts must include "no `git add`, no `git commit`, no source edits — read-only sub-agents." Mirror this guard in both prompts.
- Lower risk than the cross-workstream `_shared/` issue, but cheap to fix. Nice-to-fix, not hard-block.

## 5. Cross-workstream coordination — INSUFFICIENT (mirrors 2HDM+a §6)

Two distinct cross-workstream issues, both under-specified:

- **`_shared/` lock by hash-diff alone**: §"Scope guard" relies on end-of-run hash-diff to *detect* an unauthorized edit, not *prevent* concurrent read/write. If dark-su3's fix sonnet writes `_shared/constraints.yaml:148` while 2HDM+a's playtest sonnet is reading the same file for schema validation, the read sees a torn or partial state on some filesystems — or worse, sees the new line and reports a "stale string moved" finding that's actually dark-su3's in-progress edit.
  **Fix (hard-block)**: introduce a real file-lock protocol. Mirror 2HDM+a's `.schema_owner.lock` pattern: `plugins/hep-ph-demo/skills/_shared/.dsu3_lines_owner.lock` containing `dark-su3/run-20260424-202956`. Any other workstream sonnet must check for the lock before reading `constraints.yaml:148`, `SKILL.md:70-80`, or `MANUAL_WALKTHROUGH.md:90`. Created when Phase 2 starts; removed at end-of-run. (Hash-diff is the *audit*, not the *lock*.)
- **Merge order SD → 2HDM+a → dark-su3**: plan says it but does not say *who* enforces. There's no manager-readable readiness state file. If SD/2HDM+a are still in prep when dark-su3 finishes Phase 2, dark-su3's manager just blocks on its own merge — fine — but how does dark-su3 *know* the others are done? **Fix (hard-block)**: shared `.shift-manager/run-20260424-202956/state/merge_ready.json` with `{singlet-doublet: bool, 2hdm-a: bool, dark-su3: bool}`. Each workstream's manager flips its own bit after opus-opus ACK; dark-su3's merge step polls until SD and 2HDM+a are both true.

## 6. Stale `demo_output` rotation collision

P0.1 rotates `demo_output/dark-su3/` and `demo_output/dark_su3/` (underscore variant) to `demo_output/dark-su3.preplaytest-<UTC>/`. Two issues:

- **Rotation target collides with sibling rotations** if SD/2HDM+a use the same naming pattern. Unlikely (dirs are model-keyed) but the plan never asserts the sibling pattern. Cheap fix: include workstream prefix → `demo_output/.rotated/dark-su3-preplaytest-<UTC>/`.
- **Accidental cleanup by sibling workstream**: if 2HDM+a's prep does a broad `demo_output/*.preplaytest-*` cleanup, dark-su3's rotated dir vanishes and forensics are lost. Plan has no rule against broad-glob cleanups. **Fix**: add to scope guard: "no workstream may delete or move `demo_output/<other-model>*` paths." Document in plan §"Off-limits."

## 7. Paper-fidelity banner — Phase 2 trigger logic is correct but fragile

The banner finding is `severity:blocker` (per synthesis: "absent or paraphrased ⇒ blocker"). Phase 2 entry condition is `fix_scope=='docs' ∧ auto_fixable==true`. Two cases:

- **Banner ABSENT from SKILL.md template**: `fix_scope:docs`, `auto_fixable:true` — Phase 2 SHOULD edit SKILL.md to add the banner. But the scope guard only allows `SKILL.md` lines **70–80**. The banner template lives in the summary section (likely L150+). **Hard-block**: scope guard does NOT authorize the banner-insertion line. Plan must either widen SKILL.md authorization to cover the summary section, OR pre-locate the banner template line in P0.3 and add it to the allow-list explicitly.
- **Banner present but the underlying `Ω_tot ≠ 0.12` finding**: this is `fix_scope:physics`, NOT docs. Phase 2 must NOT trigger on this. Plan §"Trigger conditions" correctly says "Any blocker with `fix_scope ∈ {physics, build, test}` ⇒ escalate; do NOT enter Phase 2." Faithful — but the playtest sonnet must classify the banner-finding correctly. **Fix**: PT1 prompt must say "the banner finding is `fix_scope:docs`; the four-orders-off Ω finding is `fix_scope:physics`; never conflate them."

## 8. P0.5 smoke-test tautology risk

P0.5 calls `compute({}, {…BP1…})` and asserts `Omega_V_h2 ∈ [31.6, 35.0]`. P0.6 then runs the same BP1 at n=200 and writes `regression_baseline.json`. Phase 1 then re-runs BP1 and compares to that baseline. **Three runs of the same input on the same HEAD all expected to land in the same band** = a tautology that proves only that `compute()` is deterministic.

**Fix (hard-block)**: P0.5 should smoke-test **two parameter points**, not one:
- BP1 (the locked target): `g_tilde=2.0, sin_theta=0.10, m_H2=500, m_V=150, m_Psi=70`.
- A perturbation, e.g., `m_V=300` (double): expect `Omega_V_h2` to MOVE outside `[31.6, 35.0]`. The exact target doesn't matter — the assertion is "the function is not constant."

This catches a class of bugs (cached return, hardcoded output) that the single-point test cannot.

## 9. F2 escalation path — UNDEFINED

§"F2 — 3 stale hits not at expected lines": "Manager writes `preflight/escalation.md` … User decides whether another workstream moved them …" — but the manager-only-delegates rule means the manager is supposed to dispatch, not decide. Who actually reads the escalation? Three options the plan doesn't pick:

- (a) Manager pauses the run and waits for user (synchronous).
- (b) Manager dispatches an opus probe to determine "did SD or 2HDM+a touch these lines?" and proceeds based on probe output.
- (c) Manager auto-aborts the workstream and proceeds with the other two.

**Fix (hard-block, mirrors 2HDM+a §4 opus-opus deadlock fix)**: pick (a) explicitly. Write `preflight/escalation.md`, HALT dark-su3 workstream, return control to user, do NOT auto-relocate or auto-probe. This matches synthesis §"Reconciliation if SD synth differs": "Do NOT auto-relocate lines."

## 10. Try-counter persistence — MISSING (mirrors 2HDM+a §4)

Plan §"Phase 2" says "3 sonnet-opus cycles max, then opus-opus." Manager dispatches each cycle as an independent sub-agent task. There is no state file recording "we are on cycle 2" — the manager must remember across dispatches.

**Fix (hard-block, identical to 2HDM+a hard-block #6)**: counter lives at `.shift-manager/run-20260424-202956/state/dsu3_fix_attempts.json` as `{cycle: int, last_outcome: "ack"|"revise"|"aborted_scope"}`. Manager updates as a deliberate write step between dispatches. Without this, the 3-cycle cap is unenforceable across the manager's stateless dispatch loop.

---

## Shared concerns with 2HDM+a plan critique

The 10 hard-blocks identified for 2HDM+a were checked against this plan. Here's the matrix:

| 2HDM+a hard-block | Dark SU(3) status |
|---|---|
| 1. Gate criteria not inlined into evaluator prompt | **Same gap** — issue-schema v1.1 not inlined into PT1; gate criteria only in manager checks (no sub-agent). See §1. |
| 2. Scope-guard prefixes not pasted into opus reviewer prompt | **Same gap** — opus reviewer prompt not drafted; off-limits list not inlined. See §1. |
| 3. `.output_marker` referenced but never created | N/A — no MG5/sentinel mechanic in dark-su3 (analytic-only). |
| 4. Reconstructibility / sonnet fabrication | N/A — no analog (no missing iter_6_notes equivalent). |
| 5. Prep→playtest branching point unspecified | **Partially fixed** — plan says `dsu3-playtest` branches "off `dsu3-prep`" explicitly. But never says when prep tip is committed/captured. **Fix**: add P0.6 deliverable "manager records `git rev-parse dsu3-prep` after gate passes; playtest branches from that exact SHA." |
| 6. Try-counter has no persistence | **Same gap.** See §10. |
| 7. Cross-workstream schema-edit lock missing | **Same gap** in different form — `_shared/` line-level lock missing. See §5. |
| 8. SARAH serialization unspecified | N/A — dark-su3 is analytic-only, no SARAH/Wolfram contention. |
| 9. Cumulative-budget abort missing | **Same gap** — plan states 90-min hard cap on Phase 1 + 90-min combined cap on Phase 2 stopping rule, but no explicit cumulative-budget check across phases. Manager could overrun if Phase 0 takes 40 min, Phase 1 takes 90, Phase 2 takes 90 = 220 min with no abort. **Fix**: log wall-clock at each phase transition; abort if cumulative >180 min before Phase 2 starts. |
| 10. Multi-importer / cross-skill regression check | N/A in this exact form, but related: P0.3's grep is hard-coded to `plugins/hep-ph-demo/skills/`. If the stale string lives elsewhere (e.g., `demo_output/dark-su3/fix_loop/POST_MORTEM.md` itself), grep returns more than 3 hits and F2 fires spuriously. **Fix**: grep should restrict to non-`demo_output` paths, OR explicitly exclude `demo_output/`. |

---

## Summary

### Hard-blocks (must fix before plan ships)

1. **Issue-schema v1.1 not inlined into PT1 prompt** (§1).
2. **Off-limits prefix list not inlined into opus reviewer prompt** (§1).
3. **F3 dual-path "divergence" undefined**; drop dual-attempt or define divergence concretely (§2).
4. **Verbatim-quote string list not enumerated** in PT1 (§2).
5. **`compute()` wall-time-per-call ceiling not asserted in P0.5** — n=800 may blow Phase 1 budget (§3).
6. **P0.5 smoke-test is single-point ⇒ tautological**; add a perturbation point (§8).
7. **`_shared/` line-level lock missing** — hash-diff is audit, not lock; mirror 2HDM+a's `.schema_owner.lock` pattern (§5).
8. **Merge-order enforcement has no readable state file** — add `state/merge_ready.json` (§5).
9. **Banner-template line not in scope guard allow-list** — Phase 2 cannot legally insert the banner if it's missing (§7).
10. **F2 escalation path undefined** — pick "halt + return to user" explicitly (§9).
11. **Try-counter has no persistence** — add `state/dsu3_fix_attempts.json` (§10).
12. **Cumulative-budget abort missing across phases** (shared concerns table row 9).

### Nice-to-fixes

- Read-only guard explicit in P0.3/P0.4 prompts (§4).
- Rotated `demo_output` path includes workstream prefix; sibling-cleanup forbidden (§6).
- Drift-threshold bands collapsed to synthesis's <5% / ≥5% binary (§3).
- Phase-1 re-run wording clarified: PT1 invokes `compute()` fresh, baseline is comparand only (§3).
- Banner finding vs Ω finding classification rule pasted into PT1 prompt (§7).
- P0.6 records `dsu3-prep` tip SHA so playtest branches from a captured ref (shared concerns row 5).
- P0.3 grep excludes `demo_output/` to avoid false F2 trips (shared concerns row 10).
- `preflight/gate_decision.json` deliverable so go/no-go is auditable (§1).

### Bottom line

Plan is faithful to synthesis on every numeric and scope decision. The 12 hard-blocks are operational mechanics gaps — same flavor as 2HDM+a (counters, locks, inlined prompts, budget tracking). Six of the twelve are direct rhymes with 2HDM+a hard-blocks; this is a cross-workstream pattern. **Recommendation**: synthesizer should not redesign — instead, do a single inline-and-state-file pass across all three workstream plans simultaneously, since the gaps are nearly identical. Counter-proposal: factor the operational mechanics (try-counter, lock files, merge-ready state, cumulative-budget abort, opus-reviewer prompt template) into a shared `.shift-manager/run-20260424-202956/plan/_operational_mechanics.md` that all three plans reference, rather than copy-pasting the same fixes into three plans.
