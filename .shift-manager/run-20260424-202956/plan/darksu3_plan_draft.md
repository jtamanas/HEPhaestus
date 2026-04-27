# Dark SU(3) Implementation Plan (draft)

Author: plan-drafter. Consumes locked synthesis verbatim. Skeptic reviews next.
Workstream: `dark-su3` (model 3 of 3, run-20260424-202956). Local git only.
Manager-only-delegates; no coding/reviewing in manager thread.

---

## Phase structure

- **Phase 0 — Prep** (~25 agent-min): six prep tasks. Order:
  P0.1 → P0.2 → (P0.3 ∥ P0.4) → P0.5 → P0.6. Go/no-go gate at end.
- **Phase 1 — Playtest** (50-min target, 90-min hard cap):
  one sonnet sub-agent walks `/demo` for model #3, records artifacts.
- **Phase 2 — Fix-loop** (~20–30 min, conditional): entered only when every
  blocker has `fix_scope:docs` ∧ `auto_fixable:true`. Sonnet impl + opus
  review, 3 cycles max, then opus-opus final.

---

## Worktree scheme

Worktrees under `/Users/yianni/Projects/hep-ph-agents.worktrees/`. Local branches.

- **Prep**: branch `dsu3-prep` at HEAD (`a05f274`) → `…worktrees/dsu3-prep/`.
- **Playtest**: branch `dsu3-playtest` off `dsu3-prep` → `…worktrees/dsu3-playtest/`.
  No source edits permitted.
- **Fix-loop**: branch `dsu3-fix` off `dsu3-playtest` → `…worktrees/dsu3-fix/`.
  Manager merges to `main` only after opus-opus ACK.

End-of-run merge order: SD → 2HDM+a → dark-su3 (dark-su3 LAST per synthesis §8;
hash-diff at merge).

---

## Phase 0 tasks

Single sonnet sub-agent, `dsu3-prep` worktree. Artifacts under
`.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/` unless noted.

### P0.1 — Rotate stale `demo_output/dark-su3/`
- Deliverable: `demo_output/dark-su3.preplaytest-<UTC>/`; fresh empty
  `demo_output/dark-su3/`. Same for underscore variant `demo_output/dark_su3/`
  if present; record both in `preflight/rotation.json`.
- Success: `ls demo_output/dark-su3/` empty; rotated dir intact.
- Serial, runs first. ~3 min.

### P0.2 — POST_MORTEM disposition (option ii: STALE header)
- Deliverable: rotated `…/fix_loop/POST_MORTEM.md` line 1 prepended:
  `> STALE — superseded by 3a2da2c (prose rewrite) and b66ab35 (Boltzmann
  integrator). See run-20260424-202956 synthesis.`
- Success: `head -1` matches; `tail -n +2` sha256 unchanged.
- Serial, after P0.1. ~2 min.

### P0.3 — Confirm 3 stale-string hits
- Cmd: `grep -rn "Confining dark sector" plugins/hep-ph-demo/skills/`.
- Deliverable: `preflight/stale_strings.json` listing exactly:
  `demo/SKILL.md:73`, `_shared/constraints.yaml:148`,
  `_shared/tests/MANUAL_WALKTHROUGH.md:90`.
- Success: exactly 3 hits. ≠3 ⇒ write `preflight/escalation.md`, STOP.
- Parallel with P0.4. ~2 min.

### P0.4 — Capture pre-run hashes
- Deliverable: `preflight/preflight_hashes.json` with sha256 of
  `_shared/constraints.yaml`, `_shared/time_budget.py`,
  `_shared/analytic_models/dark_su3.py`, `_shared/backends/analytic.py`,
  `demo/SKILL.md`. Plus `git rev-parse HEAD`.
- Success: file written, all five hashes present.
- Parallel with P0.3. ~2 min.

### P0.5 — Smoke-test `compute()`
- Deliverable: `preflight/smoke_test.json` from running:
  `compute({}, {g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:150, m_Psi:70})`.
  Record `Omega_V_h2`, `Omega_Psi_h2`, `relic_approx`, `sigmav_approx`,
  signature arity.
- Success: `Omega_V_h2 ∈ [31.6, 35.0]`, `Omega_Psi_h2 ∈ [2846, 3146]`,
  `relic_approx==False`, `sigmav_approx==True`, two-arg + `n_points` kwarg.
  Any miss ⇒ `preflight/escalation.md` and STOP.
- Serial, after P0.3 + P0.4. ~5 min.

### P0.6 — Lock regression baseline
- Deliverable: `…/workstreams/dark-su3/regression_baseline.json` with three
  rows for `n_points ∈ {200, 400, 800}` × `{Omega_V_h2, Omega_Psi_h2,
  wall_seconds, relic_approx, sigmav_approx}`.
- Success: n=200 row matches P0.5; drift on n=400/800 vs n=200 < 5% on each
  Ω. Drift 5–25% logged as `major/physics` issue but does NOT block. Drift
  >25% ⇒ escalate.
- Serial, after P0.5. ~10 min.

### Phase 0 go/no-go gate (manager checks)
All true: smoke-test green; 3 stale-string hits at expected lines;
`preflight_hashes.json` written; `regression_baseline.json` written with
n=200 row in spec range. Any fail ⇒ escalate, no Phase 1.

---

## Phase 1: Playtest

Single sonnet sub-agent in `dsu3-playtest` worktree. 90-min hard cap.

### Practitioner prompt (verbatim for sonnet)

> You are a phenomenology practitioner playtesting `hep-ph-demo`'s `/demo`
> walkthrough for model #3 (dark SU(3)). Follow the walkthrough as a real
> user would; record everything; do NOT edit source files.
>
> Worktree: `…worktrees/dsu3-playtest/`. Outputs to
> `demo_output/dark-su3/` and
> `.shift-manager/run-20260424-202956/workstreams/dark-su3/playtest/`.
>
> Walkthrough simulation (you cannot invoke `/demo` as a slash command;
> see "Failure modes F3" — simulate by reading SKILL.md):
> 1. Read `plugins/hep-ph-demo/skills/demo/SKILL.md` cover-to-cover. This
>    is the script `/demo` would execute. Quote every user-visible string
>    verbatim into `playtest/findings.md` — picker entries, constraint
>    hooks, summary banner.
> 2. At picker (~L60–80), pick entry #3. Record exact label + description.
> 3. Walk Step 1 (intro), Step 2 (interview / `practitioner_script.md`
>    auto-answer), Step 3 (`time_budget.py --model dark-su3 --constraints
>    relic`), Step 4 (analytic relic via `compute(spec, params,
>    n_points=200)`), Step 5 (summary + banner).
> 4. Choose `relic only` and analytic backend (`analytic_only: true`).
> 5. Re-run `compute()` at `n_points ∈ {400, 800}`; compare to
>    `regression_baseline.json` (drift <5%).
> 6. Verify summary banner present and verbatim:
>    `NOTE: dark-SU(3) relic uses sigma_v approximations
>    (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach
>    this run; values reported are regression-anchors, not physics targets.`
>    Absent or paraphrased ⇒ `severity:blocker` issue.
>
> Log every divergence into `playtest/issues.json` (schema v1.1 per
> synthesis §"Issue-log JSON schema"; `id` prefix `dsu3-`). Set
> `auto_fixable` and `fix_scope` for each. Also write
> `playtest/diagnostics.json` (raw analytic output),
> `playtest/summary.json` (must validate vs `_shared/summary.schema.json`),
> `playtest/timing.json`, `playtest/findings.md`,
> `playtest/banner_check.json`, `playtest/run.log`.
>
> Hard rules: no source edits; no merges; no GitHub; end-of-run hash-diff
> against `preflight_hashes.json` — only allow-list paths may differ. At
> 90 min, write `playtest/escalation.md` and STOP.

### Invocation sequence
`/demo` (simulated by SKILL.md walk) → picker → model #3 → constraints
menu: `relic only` → backend menu: `analytic`.

### What to record
`issues.json`, `diagnostics.json`, `summary.json`, `timing.json`,
`findings.md`, `banner_check.json`, `run.log` (paths above).

### Success check (synthesis §"Success criteria" 1–5)
- BP1 at n=200: `Omega_V_h2 ∈ [31.6, 35.0]`, `Omega_Psi_h2 ∈ [2846, 3146]`.
- Drift <5% at n=400, n=800.
- `relic_approx:False`, `sigmav_approx:True`.
- `time_budget.py` emits READY (no `/dark-matter-constraints` append).
- Banner present + verbatim.
- `summary.json` schema-valid.
- End-of-run hash-diff: only allow-list paths changed.

---

## Phase 2: Fix-loop (conditional)

### Trigger conditions
Enter Phase 2 iff every blocking issue has `fix_scope=="docs"` ∧
`auto_fixable==true`. Any blocker with `fix_scope ∈ {physics, build, test}`
⇒ escalate to user; do NOT enter Phase 2. Most likely entry: the three
stale "Confining dark sector" strings.

### Dispatch pattern (sonnet impl → opus review)
- **Cycle 1**: sonnet edits the three authorized lines in `dsu3-fix`
  worktree; commits `dark-su3 fix-loop iter1: refresh picker/hook/walkthrough`.
  Opus reviews diff vs scope guard + issue text → ACK or revise.
- **Cycle 2**: any opus-requested revisions.
- **Cycle 3**: optional POST_MORTEM refresh (only if cycle 1–2 opus
  reviewer demands it; default keeps STALE header from P0.2).
- **Final opus-opus**: two opus reviewers cross-check full diff +
  hash-diff + `issues.json`. Both ACK ⇒ manager merges `dsu3-fix` → `main`.

3 sonnet-opus cycles max, then opus-opus. ~30 agent-min.

### Scope guard (exact paths, verbatim from synthesis)
Allowed:
- `plugins/hep-ph-demo/skills/dark-su3/**`
- `plugins/hep-ph-demo/skills/demo/SKILL.md` lines **70–80 only**
- `plugins/hep-ph-demo/skills/_shared/constraints.yaml` line **148 only**
- `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md` line **90 only**
- `demo_output/dark-su3/fix_loop/POST_MORTEM.md`
- `.shift-manager/run-20260424-202956/workstreams/dark-su3/**`

Off-limits (escalate; do not edit): everything else under `_shared/`,
`backends/`, `analytic_models/`, SD/2HDM+a per-model trees. After each
cycle, manager runs `git diff --name-only` and re-`sha256sum`s shared
files; out-of-scope diff ⇒ revert cycle, log `outcome:aborted_scope`,
escalate.

### Stopping rule
Stop on first opus-opus ACK after a clean cycle, OR cycle-count == 3
unresolved (escalate), OR scope-guard trip (revert + escalate), OR 90-min
combined wall-clock cap reached.

---

## Five planner-to-resolve answers

1. **POST_MORTEM disposition**: option (ii) — prepend STALE header in
   P0.2; do not refresh body. Refresh only if a Phase 2 opus reviewer
   explicitly demands it. Cheaper, no re-derivation risk.

2. **Per-candidate `relic_*.json` duplicates**: drop from REQUIRED list.
   If the analytic module emits them anyway, accept as informational
   artifacts; do NOT delete (forensic signal). Note in `findings.md`.

3. **Banner exact wording** (verbatim from synthesis):
   > `NOTE: dark-SU(3) relic uses sigma_v approximations
   > (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of
   > reach this run; values reported are regression-anchors, not physics
   > targets.`
   Shortening proposals ⇒ filed as `minor` post-run; non-load-bearing.

4. **Cross-workstream `_shared/` lock**: real contention is nil at the
   line level. dark-su3 owns three named lines (SKILL.md:73,
   constraints.yaml:148, MANUAL_WALKTHROUGH.md:90). 2HDM+a owns one file
   (`_shared/summary.schema.json`, P3 of its synthesis). SD synthesis
   in-flight; assume it claims nothing in `_shared/` until proven. Enforce
   via end-of-run hash-diff. Merge order SD → 2HDM+a → dark-su3 so
   dark-su3 sees others' diffs and re-checks line numbers before its
   three edits.

5. **Reconciliation if SD synth differs**: manager re-runs P0.3
   line-locator immediately before Phase 2 starts. Any mismatch ⇒
   escalation trigger fires; abort Phase 2; route the docs fix through a
   user-approved cross-workstream coordinator. Do NOT auto-relocate lines.

---

## Failure modes in the plan itself

### F1 — Smoke-test fails (compute() signature drift)
P0.5 fails. Manager halts before Phase 1; writes `preflight/escalation.md`
with seen vs. expected `(spec, params, n_points=200)`. User decides:
re-pin HEAD, revert commit, or accept as `physics` blocker. NO playtest
under signature drift.

### F2 — 3 stale hits not at expected lines
P0.3 returns ≠3 hits, or hits at unexpected file:line. Manager writes
`preflight/escalation.md` listing actual vs expected. Does NOT guess new
line numbers. User decides whether another workstream moved them
(dark-su3 loses fix-authority on those lines) or strings were intentionally
removed (issue downgraded). Phase 1 may still proceed (playtest will
re-discover wherever they live), but Phase 2's authorized-line list is
invalidated until reconciled.

### F3 — Sonnet sub-agent cannot invoke `/demo` slash command
**Expected case.** Slash commands are user-invocable; a sub-agent's Skill
tool may not accept `/demo`. The plan does NOT depend on slash-command
access. The sub-agent **simulates** the walkthrough by:
- Reading `plugins/hep-ph-demo/skills/demo/SKILL.md` cover-to-cover.
- Following its instructions step by step using ordinary tools (Read,
  Bash, write to output dirs only).
- Quoting every user-visible string verbatim from SKILL.md source —
  picker entries, constraint hooks, summary banner template — into
  `playtest/findings.md` and `playtest/issues.json`. Stale strings are
  caught by quoting; the picker does NOT need to render to be discovered.
- Invoking `compute(spec, params, n_points=200)` directly via Python for
  Step 4 (the supported analytic path per synthesis §3).
- Running `time_budget.py --model dark-su3 --constraints relic` directly
  via Bash for the iter-5 guard regression check.
- Treating the summary banner as a string SKILL.md instructs the assistant
  to print: locate the template (or its absence), record verbatim, flag
  absence as blocker.

If the sub-agent **does** have working Skill-tool `/demo` access, attempt
it AND record both outputs noting any divergence. The SKILL.md-walked
simulation is authoritative for issue-logging; slash-command output is
bonus evidence.

---

End of draft.
