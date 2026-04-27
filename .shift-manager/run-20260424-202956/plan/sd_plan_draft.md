# Singlet-Doublet Implementation Plan (draft)

Inputs: `sd_synthesis.md` (LOCKED), `sd_critique.md`, `2hdma_synthesis.md`, `darksu3_synthesis.md`. Sonnet-completable; skeptic reviews next.

---

## Phase structure

- **Phase 0 — Prep (P1–P7).** Sequential: **P3 → P6 → P7.** Parallel: **P1, P2, P4, P5.** G9 depends on 2HDM+a P3 (see Cross-workstream gate).
- **Phase 1 — Playtest (A, B).** Parallel under per-variant worktrees; SARAH MakeUFO[] serialized cross-workstream with 2HDM+a (Wolfram seat).
- **Phase 2 — Fix-loop (conditional).** Triggered only on `severity: blocker`/`major` issues. Sonnet→opus dispatch by manager.

Wall budget: 30 min prep + 90 min playtest + ≤30 min fix = **150 min ceiling.**

---

## Worktree scheme

Under `/Users/yianni/Projects/hep-ph-agents.worktrees/`:

| Worktree | Purpose | Branch |
|---|---|---|
| `hep-ph-agents-sd-prep/` | P1–P7 prep work; commits land on a short-lived branch | `sd-prep-20260424` |
| `hep-ph-agents-sd-A/` | Variant A canonical playtest, observe-only Claude session | `sd-A-20260424` (from main HEAD post-prep) |
| `hep-ph-agents-sd-B/` | Variant B `ZN→N` playtest, observe-only Claude session | `sd-B-20260424` |
| `hep-ph-agents-sd-fix/` | Fix-loop subagent edits (Phase 2 only) | `sd-fix-20260424` |

Rationale: separate prep so playtest worktrees start from a frozen commit; per-variant worktrees for hard isolation of `HEPPH_STATE_ROOT`/`XDG_CONFIG_HOME`/`demo_output/`; fix-loop worktree atomic on revert. Local git only.

---

## Phase 0 tasks

### P1 — Move stale `demo_output/singlet-doublet/` aside
- **Worktree:** sd-prep
- **Tier:** sonnet
- **Deliverable:** `demo_output/singlet-doublet.preplaytest-<TS>/` exists; `demo_output/singlet-doublet/` no longer present as a raw dir; commit on `sd-prep` branch.
- **Cmd:** `TS=$(date +%Y%m%d%H%M%S); mv demo_output/singlet-doublet "demo_output/singlet-doublet.preplaytest-$TS"`
- **Verify:** `test ! -e demo_output/singlet-doublet && test -d demo_output/singlet-doublet.preplaytest-*`
- **Gates:** G1.

### P2 — Capture today's baseline (0.292)
- **Worktree:** sd-prep
- **Tier:** sonnet
- **Deliverable:** `omega_h2` value pinned in `.shift-manager/run-20260424-202956/workstreams/sd/baseline.json`.
- **Cmd:** `python3 -c "import json,sys; d=json.load(open('demo_output/singlet-doublet.preplaytest-<TS>/relic.json')); print(d['omega_h2'])"`
- **Verify:** value within `0.292 ± 0.001`. If outside, escalate to manager — synthesis assumption broken, do not proceed.
- **Gates:** G2.

### P3 — Per-variant worktree setup (sequential gate)
- **Worktree:** main repo (creates worktrees)
- **Tier:** sonnet
- **Deliverable:** both worktrees exist; `.playtest/sd-{A,B}/{state,xdg}` dirs created in each; `practitioner_script_B.md` derived from canonical with single `ZN → N` rename (no other diff).
- **Cmds:**
  - `git worktree add /Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-A -b sd-A-20260424 main`
  - `git worktree add /Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-B -b sd-B-20260424 main`
  - In each worktree: `mkdir -p .playtest/sd-{A,B}/{state,xdg}` (matched to its variant)
  - In sd-B: copy `plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md` → `practitioner_script_B.md`, apply `ZN → N` rename, verify with `diff` that exactly one symbol changed.
- **Verify:** `diff <(grep -v ZN canonical) <(grep -v "\bN\b" sd-B/practitioner_script_B.md)` produces empty output modulo the renamed lines.
- **Gates:** G3. **Blocks P6, P7.**

### P4 — MadDM PLUGIN cleanup
- **Worktree:** main host filesystem (touches `$MG5_PATH/PLUGIN/`)
- **Tier:** sonnet
- **Deliverable:** no `maddm.broken-backup-*` dirs under `$MG5_PATH/PLUGIN/`.
- **Cmd:** `mv $MG5_PATH/PLUGIN/maddm.broken-backup-* /tmp/ 2>/dev/null || true`
- **Verify:** `ls $MG5_PATH/PLUGIN/ | grep -c broken-backup` returns `0`.
- **Gates:** G4.

### P5 — Wolfram smoke
- **Worktree:** any
- **Tier:** sonnet
- **Deliverable:** `wolframscript -code 'Print["ok"]'` exits 0 within 5s; recorded to `.shift-manager/run-20260424-202956/workstreams/sd/wolfram_smoke.txt`.
- **Verify:** stdout contains `ok` and exit code 0.
- **Failure mode:** halt SD workstream — Wolfram unavailable means SARAH cannot run.
- **Gates:** G5.

### P6 — Verify `HEPPH_STATE_ROOT` honoured (sequential after P3)
- **Worktree:** sd-A (smoke only)
- **Tier:** sonnet
- **Deliverable:** smoke result in `.shift-manager/run-20260424-202956/workstreams/sd/state_root_smoke.txt`.
- **Cmd:** `HEPPH_STATE_ROOT=/tmp/sd-smoke-$$ python3 -c "from plugins.model_building.skills.sarah_build.scripts.build import resolve_state_root; print(resolve_state_root())"`
- **Verify:** stdout matches `/tmp/sd-smoke-$$`.
- **Failure mode:** halt — proposer's isolation strategy fails; escalate to manager.
- **Gates:** G6.

### P7 — Capture `env.json` per variant (sequential after P3, P6)
- **Worktree:** sd-A and sd-B (parallel, one each)
- **Tier:** sonnet
- **Deliverable:** `.playtest/sd-{A,B}/env.json` with: `git_sha` (`git rev-parse HEAD`), `mg5_version` (`mg5_aMC --version`), `maddm_plugin_sha` (`git -C $MG5_PATH/PLUGIN/maddm rev-parse HEAD` if applicable), `sarah_version`, `python_version`, `wolfram_version`, `config_json_snapshot` (verbatim copy of `~/.config/hep-ph-agents/config.json`).
- **Verify:** `python3 -c "import json; d=json.load(open('.playtest/sd-A/env.json')); assert all(k in d for k in ['git_sha','mg5_version','python_version','wolfram_version','config_json_snapshot'])"`
- **Gates:** G7.

### G8 — `git status --porcelain` clean
- Run after P1–P7 complete in each worktree. Only paths under allowed scope-guard prefixes may show modifications. Manager verifies.

### G9 — Cross-workstream schema ack
- See "Cross-workstream gate" below. **Resolved by 2HDM+a owning the schema fix; SD validates after.**

---

## Phase 1: Playtest

Both variants run in parallel under their respective worktrees. Each variant is a single sonnet sub-agent acting as the "playtest practitioner." The sub-agent is OBSERVE-ONLY (Two-phase contract from synthesis Q7) — it does not patch code mid-run.

### KEY DESIGN: sonnet sub-agent simulates `/demo` by hand

A sonnet sub-agent cannot invoke slash commands (harness-dispatched). **Resolution: sub-agent reads `plugins/hep-ph-demo/skills/demo/SKILL.md` and follows its Flow steps manually**:

| SKILL.md Step | Simulation |
|---|---|
| Step 0 Preflight | Read `$XDG_CONFIG_HOME/hep-ph-agents/config.json`, confirm each of `madgraph_path`/`sarah_path`/`spheno_path`/`wolfram_engine_path` binary responds. Fail → log `phase: preflight, severity: blocker`, halt. |
| Steps 1–2 | Print intro to `console.log`; auto-answer `continue`. |
| Step 3 picker | Auto-answer `singlet-doublet`. |
| Delegation | Read `plugins/hep-ph-demo/skills/singlet-doublet/SKILL.md`, follow Steps 1–4. At each `AskUserQuestion`, answer from `practitioner_script.md` (A) or `practitioner_script_B.md` (B). |
| Chain | lagrangian-builder → sarah-build → spheno-build → madgraph → maddm → plot → summary: sub-agent reads each SKILL.md, executes bash/python steps directly, captures stdout/stderr to `console.log`. |
| Closing | Read `./demo_output/singlet-doublet/summary.json`, write three-line block to `result.json`. |

This is "/demo by hand" — synthesis Q3's "Claude executing `/demo` in a session." The simulation IS the test of skill text being well-formed.

### Variant A practitioner prompt (verbatim text for sonnet)

```
You are the Variant A playtest practitioner. You are OBSERVE-ONLY: log issues
to issues.jsonl, do NOT modify any code. Halt on the first BLOCKER.

CWD: /Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-A
ENV:  HEPPH_STATE_ROOT=$PWD/.playtest/sd-A/state
      XDG_CONFIG_HOME=$PWD/.playtest/sd-A/xdg

1. Read plugins/hep-ph-demo/skills/demo/SKILL.md and execute its Flow steps
   manually as described in the runbook. Print every step to
   .playtest/sd-A/console.log with timestamps.
2. At Step 3 model picker, answer "singlet-doublet".
3. At the per-model interview Q1–Q4, answer verbatim from
   plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md
   (MS=150, MPsi=500, y=1, theta=0; mixing matrix named ZN; constraint=relic only).
4. Drive the chain: /lagrangian-builder, /sarah-build, /spheno-build, /madgraph,
   /maddm, plot, summary — by reading each skill's SKILL.md and executing its
   commands directly with stdout/stderr redirected into console.log.
5. On any phase BLOCKER (non-zero exit, missing artifact, plugin import error):
   capture the last 200 lines of stderr/stdout, append a JSON line to
   .playtest/sd-A/issues.jsonl using the cross-workstream schema (workstream:
   "singlet-doublet", variant: "A", issue_id "sd-A-NNN"), then halt.
6. On success: copy demo_output/singlet-doublet/ → .playtest/sd-A/demo_output/
   and write .playtest/sd-A/result.json with criteria 1–6 evaluated against
   baseline 0.292 ± 0.01.
7. Hard timeout: 90 min total Phase-1 budget. If sd-B is still running at
   60 min wall and your variant is done, do NOT start a flake-check rerun
   without manager authorization.
```

### Variant B practitioner prompt (verbatim text for sonnet)

```
Same as Variant A, with these substitutions:
- CWD: /Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-B
- ENV: HEPPH_STATE_ROOT=$PWD/.playtest/sd-B/state, XDG_CONFIG_HOME=$PWD/.playtest/sd-B/xdg
- Practitioner script: plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script_B.md
  (mixing matrix named N, NOT ZN; everything else identical to A)
- SARAH model name: SingletDoublet_B (set in interview Q4 BY YOU, not by editing
  the script — the script's Q4 answer asks for the matrix name, the model name
  is a separate prompt earlier in the chain).
- Issue IDs: sd-B-NNN; variant: "B".
- Success criteria: items 1, 4, 5, 6 plus EITHER (2 AND 3 pass) OR
  issues.jsonl has a severity:major entry pinpointing ZN→N clash before MadDM.
- MadDM first-launch flock: acquire `flock -w 300 $MG5_PATH/.playtest.lock`
  before invoking maddm.py. Release after MadDM has produced its first card.
```

### 10-step runbook invocation (per variant)

The 10 steps from synthesis Q3 are followed exactly. Steps 1–3 are bash/env setup the sub-agent issues directly. Steps 4–7 are SKILL.md emulation. Steps 8–10 are halt/success bookkeeping. Total wall: 25–45 min cold per variant; both ≤ 90 min combined.

### Recording targets (per variant, under `.playtest/sd-X/`)

- `console.log` — ts-prefixed stdout+stderr from simulated `/demo` session.
- `run.log` — sub-agent narration of phase transitions.
- `issues.jsonl` — append-only, cross-workstream schema (`2hdma_synthesis.md`), with SD additions: `workstream: "singlet-doublet"`, `variant: "A"|"B"`, phases `lagrangian_builder`/`validate_spec`, IDs `sd-[AB]-NNN`.
- `relic.json`, `summary.json`, `summary.{pdf,png}` — copies from `demo_output/`.
- `timing.json` — `{phase: wallclock_seconds}`.
- Screenshots N/A (no GUI); substitute is `console.log` block-quotes at phase boundaries.
- `result.json` — first lines `VERDICT`/`BASELINE_USED`/`WORKSTREAM`/`VARIANT`, then 6-criterion table.

### Success check against Ωh² = 0.292 ± 0.01

```python
omega = json.load(open('demo_output/singlet-doublet/relic.json'))['omega_h2']
passed_3 = abs(omega - 0.292) <= 0.01  # Variant A
```
Variant B passes criterion 3 iff (a) `omega` within band, OR (b) `issues.jsonl` has a `severity: major` entry naming the `ZN→N` clash before MadDM.

---

## Phase 2: Fix-loop (conditional)

### Trigger conditions

Enter Phase 2 iff Phase 1 produced any of:
- `severity: blocker` issue in either variant's `issues.jsonl`.
- `severity: major` with `expected_fix_scope: skill-prose | tool-driver | fixture` AND `auto_repro_command` is non-null.
- Variant A criterion 3 fails (`omega_h2` outside `0.292 ± 0.01`).

Skip Phase 2 iff Phase 1 PASS on both variants OR all `major`/`blocker` issues have `expected_fix_scope: physics | unknown` (escalate to user instead).

### Sonnet→opus cycle dispatch (≤3 sonnet-opus, then opus-opus)

1. **sonnet diagnose** — read `issues.jsonl`, group by failure class, propose one-paragraph fix per class with diff target paths. ≤15 min.
2. **opus review** — mark each `accept | revise | reject`. ≤10 min.
3. **sonnet implement** — write diff for accepted fixes in `sd-fix` worktree.
4. **opus verify** — check diff vs scope guard; run `auto_repro_command` if any.
5. Loop ≤3 cycles. After 3, escalate remaining to **opus-opus** (synthesizer + manager) for one attempt; else halt, write `escalation.md`.

Manager only delegates; never edits code.

### Scope guard paths (verbatim from synthesis)

**Allowed:**
- `plugins/hep-ph-demo/skills/singlet-doublet/**`
- `demo_output/singlet-doublet/**` and `demo_output/singlet-doublet.*/`
- `.playtest/sd-{A,B}/**` (worktree-local)

**Forbidden** (immediate revert + escalate): `plugins/model-building/**`, `plugins/monte-carlo-tools/**`, `plugins/hep-ph-demo/skills/2hdm-a/**`, `plugins/hep-ph-demo/skills/dark-su3/**`, `plugins/hep-ph-demo/skills/_shared/**` (2HDM+a owns), `config.json`, `.shift-manager/**`.

After every fix iteration: `git diff --name-only HEAD~1 HEAD | grep -vE '^(plugins/hep-ph-demo/skills/singlet-doublet/|demo_output/singlet-doublet|\.playtest/sd-)' | wc -l` must return 0. Non-zero → revert, log `outcome: aborted_scope`, escalate.

### Stopping rule

Halt Phase 2 when ANY one trips:
1. All Phase 1 blocking issues `outcome: pass` in `fix_attempts`.
2. Total `fix_attempts.length` for SD > 5 (synthesis kill-switch #2).
3. Per-class iterations > 3 (kill-switch #3).
4. Wall-clock for Phase 2 > 30 min (kill-switch #4).
5. Any forbidden-path diff (kill-switch #1, #5).

On halt, manager re-runs Phase 1 ONCE if budget allows AND at least one accepted fix landed; otherwise writes `escalation.md` to workstream dir and ends SD workstream.

---

## Four planner-to-resolve answers

### 1. `_shared/summary.schema.json` ownership — **2HDM+a owns; SD reads**

**Decision:** 2HDM+a's P3 fix agent owns the schema edit. SD does NOT touch the schema. **SD's G9 gate** verifies (post-2HDM+a-P3) the schema validates SD's `summary.json` payload before Phase 1 fires.

**Justification:** 2HDM+a P3 enumerates additions (`relic_approx`, `model_source`, `model_fixture`); SD's payload contains none of those fields, so additions with explicit optional defs are strictly additive. SD planner hereby acks: "additions must remain optional/non-required; if 2HDM+a makes any required, ack REVOKED and we coordinate." If 2HDM+a P3 not done by SD prep-end, downgrade G9 to warning per "keep grinding" and record `phase: schema_validate, severity: minor` if SD `summary.json` fails the unmodified schema.

### 2. 0.163 → 0.292 drift root cause — **log only, do not bisect**

Per synthesis: log as `severity: major, phase: parse, hypothesis: "18h drift from devlog 2026-04-22"`. Bisection is a separate workstream (likely intentional change between `a05f274` and HEAD per 2026-04-22 devlog). If A reproduces 0.292 cleanly, drift was real — done.

### 3. Variant B failure mode interpretation — **`blocker` if silent**

If `ZN → N` causes silent SARAH success but downstream Ωh² wildly wrong, log as `blocker` with `hypothesis: "silent-name-collision; SARAH accepted N as MSSM neutralino convention and rebound mixing semantics"`. Silent-until-physics-broken IS the failure cold-read regression catches. If failure surfaces (SARAH error, MadDM rejection), `severity: major`.

### 4. Repeat-A flake check budget — **yes if budget remains AND A passed**

If wall-clock at end of Phase 1 < 60 min AND A criterion 3 passed AND no Phase 2 triggered: rerun A once for variance characterization. Budget cap: 30 min for the rerun. Single-sample regression at ±0.01 tolerance is fragile; second sample materially reduces "lucky run" risk. If rerun's Ωh² differs from first by > 0.005, log `severity: major, phase: parse, hypothesis: "deterministic two-phase relic should have variance < 0.001; >5x drift suggests nondeterminism"`.

### 5. (SD-specific) Variant B SARAH model name override

Synthesis: model name set in interview "by the playtest agent, NOT by editing the practitioner script." **Resolution:** singlet-doublet SKILL.md prompts model name BEFORE Q1–Q4. Variant B sub-agent answers `SingletDoublet_B` at that prompt and `N` at Q4 mixing-matrix prompt. `practitioner_script_B.md` carries the `ZN→N` rename only; model name is a per-variant runtime override.

---

## Cross-workstream gate

### Serialization with 2HDM+a (Wolfram seat)

**SARAH `MakeUFO[]` serialized via file lock** at `~/.cache/hep-ph-agents/sarah_makeufo.lock` (host path agreed with 2HDM+a). SD acquires entering sarah-build, releases on exit. 2HDM+a Q8 commits to same lock. ~2 min sequencing cost. Fallback: SARAH per-model fcntl + distinct names (`SingletDoublet_A` vs `TwoHdmAfix`) parallel-safe at SARAH layer; Wolfram seat may serialize anyway.

Manager enforcement: poll lock at 5s intervals when SD enters sarah-build; SD blocks until clear.

### Parallelism with Dark SU(3) — zero overlap

Dark SU(3) is analytic-only (no SARAH/MG5/MadDM). Their fix-loop touches `_shared/constraints.yaml:148`, `_shared/tests/MANUAL_WALKTHROUGH.md:90`, `demo/SKILL.md:73` — none intersect 2HDM+a's `_shared/summary.schema.json`, and SD touches no `_shared/`. **Confirmed zero file overlap; no SD↔dark-su3 coordination needed.**

---

## Failure modes in the plan itself

### `/demo` skill changed since synthesis?

P3 freezes worktrees at `main` HEAD. Pre-Phase-1: sub-agent runs `git log --oneline plugins/hep-ph-demo/skills/{demo,singlet-doublet}/SKILL.md`, confirms most recent commit ≤ `a05f274`. Drift → log `severity: major, phase: preflight, hypothesis: "skill text drifted from synthesis assumptions"` and proceed.

### Variant B `ZN→N` causes latent SARAH naming conflict?

This IS the test — synthesis Q4 accepts surfaced failure as PASS. **Fallback only if conflict crashes SD-A via shared SARAH state**: distinct model names + per-model fcntl should prevent cross-contamination. If A fails AFTER B fails: abort B, log `blocker, phase: sarah-build, hypothesis: "B contamination"`, restart A from clean `HEPPH_STATE_ROOT`. If A still fails: kill workstream, escalate.

### Baseline 0.292 drifts further before run?

P2 captures baseline at prep time, pins in `result.json.baseline_used`. Variant A criterion 3 uses P2-captured value, not synthesis-time `0.292`; tolerance `±0.01` preserved. If P2 captures > `0.292 + 0.01`: synthesis baseline assumption broken, halt before P3, escalate.

---

## Summary

7 prep tasks (≤30 min) → 2 parallel sonnet sub-agents simulating `/demo` by hand under sd-A/sd-B worktrees (≤90 min) → conditional sonnet-opus fix loop ≤3 cycles + 1 opus-opus pair (≤30 min). 2HDM+a owns `_shared/summary.schema.json`; dark-su3 zero file overlap; SARAH MakeUFO[] serialized via file lock. 4 worktrees, local git only, 150 min ceiling.
