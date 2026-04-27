# Singlet-Doublet Playtest — Brainstorm Synthesis (LOCKED)

Author: brainstorm-synthesizer
Inputs: `sd_propose.md`, `sd_critique.md`, `2hdma_synthesis.md` (for cross-workstream alignment)
Posture: decisive. The planner consumes this verbatim.

---

## Decisions on the proposer's 10 questions

### Q1 — Two-variant test design
**KEEP with revision.** Two variants (A canonical, B perturbed) is the right shape. Drop "cold-read" framing.
- Skeptic correctly notes `MS→MChi` re-tests a documented gotcha (scope.md:25, 2HDM+a POST_MORTEM `Mchi → mchi` SARAH M-prefix collision). That's still a useful regression — but call it what it is.
- Variant A = canonical regression (verbatim `practitioner_script.md`, baseline 0.292).
- Variant B = known-gotcha regression (`ZN → N` MSSM-collision) + drop `MS→MChi` to avoid duplicating 2HDM+a coverage. See Q2.

### Q2 — Practitioner persona / Variant B perturbation
**REVISE — drop `MS→MChi`, keep `ZN→N`.**
- Critique-verified: the practitioner script literally says `MS` and `ZN` (no underscores). Proposer's `M_S`/`M_Psi` is against text that does not exist.
- `ZN→N` is the load-bearing test (genuine MSSM neutralino-conventions collision; SARAH-side reserved-name handling). KEEP this one.
- `MS→MChi` is gratuitous here — the 2HDM+a workstream already covers the SARAH M-prefix path via POST_MORTEM iter 4. Removing it shrinks B to a single-axis perturbation, which is cleaner anyway.
- Variant B's practitioner copy lives at `.shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md` with only the Q4 mixing-matrix rename applied.

### Q3 — Invocation (CRITICAL REWRITE)
**REJECT proposer; REWRITE.** `drive.py --flags` is fiction (verified: 5 positional args only at `drive.py:108-117`; UFO path hardcoded at line 25). The proposer's "thin wrapper" escape hatch silently expands to "rewrite the harness." Not acceptable.

**Actual invocation** is Claude executing the `/demo` SKILL in a session. Per-variant runbook:

```
Variant A (canonical):
  1. cd <worktree>; export HEPPH_STATE_ROOT=<worktree>/.playtest/sd-A/state
  2. export XDG_CONFIG_HOME=<worktree>/.playtest/sd-A/xdg
  3. Capture env.json (git_sha, tool versions, config snapshot)
  4. Invoke /demo
  5. At "select model": answer 1 (singlet-doublet)
  6. At Q1-Q4: read answers verbatim from
     plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md
     (MS=150, MPsi=500, y=1, theta=0; mixing matrix named ZN; constraint=relic only)
  7. Let /demo drive /lagrangian-builder, /sarah-build, /spheno-build,
     /madgraph, /maddm, plot, summary in sequence
  8. On any phase BLOCKER: capture stderr/stdout tail, append issues.jsonl, halt
  9. On success: copy demo_output/singlet-doublet/ → .playtest/sd-A/demo_output/
 10. Write result.json

Variant B (ZN→N rename):
  Same as A but with practitioner_script_B.md and HEPPH_STATE_ROOT/XDG pointed
  at sd-B paths. Distinct SARAH model name SingletDoublet_B (set in interview
  Q4 by the playtest agent, NOT by editing the practitioner script).
```

The playtest agent IS Claude in a session, not a script. Issue logging is a side-channel append the agent performs after each phase transition.

### Q4 — Success criteria — REWRITE
**REVISE.** Baseline is **0.292**, not 0.163. Tolerance ±0.01. Collapse 10 checks to 6.

| # | Check | Threshold |
|---|---|---|
| 1 | `summary.json` parseable, `summary.json.ran` contains `"relic"`, `relic.json.status == "ok"` | exact |
| 2 | `relic.json.omega_h2` finite, in `[0.10, 0.40]` | range |
| 3 | **A only:** `omega_h2 == 0.292 ± 0.01` | regression-strict |
| 4 | `summary.{pdf,png}` exist, > 1 KB | size |
| 5 | `singlet_doublet_spec.yaml` exists; `validate_spec.py` exits 0 | exit code |
| 6 | Wallclock ≤ ceiling (see Q10) | hard timeout |

**On the 0.163 → 0.292 drift:** itself a finding. Log as `severity: major, phase: parse, hypothesis: "18h drift from devlog 2026-04-22 baseline; suspect SPheno/MadDM/UFO change between commits a05f274 and current HEAD"`. Do NOT block on it — adopt 0.292 as today's truth, but flag for synthesizer attention. If A reproduces 0.292 ± 0.01 cleanly, the drift was a real (likely intentional) change, not flake.

Variant B "pass" = items 1, 4, 5, 6 PLUS either (a) 2, 3 also pass (rename handled correctly) OR (b) `issues.jsonl` has a `severity: major` entry pinpointing the `ZN→N` clash before MadDM (failure surfaced, not silent).

Drop proposer's items 8 (`mg5_aMC --mode=maddm` grep — unverified target) and 9 (`SAxDynkin` grep) — too brittle, route through phase-completion log markers instead.

### Q5 — Failure taxonomy
**KEEP** proposer's 9 modes, with two cross-workstream additions from 2HDM+a's lessons:
- Add **#10 Stale `demo_output/singlet-doublet/`** (HIGH likelihood — 5+ `maddm_run*` dirs + `relic_{1..4}.json` present today). Mitigation: P1 below.
- Add **#11 Global `config.json` cross-variant overwrite** (MEDIUM). `register_model()` from A could stomp B's slot. Mitigation: per-variant `XDG_CONFIG_HOME`.
- Move proposer's #1 (MadDM PLUGIN backup crash) to top — it's the most-reproduced failure in this codebase per `maddm-workarounds.md:363-372`.

### Q6 — Issue-log JSON schema
**ADOPT 2HDM+a's cross-workstream contract verbatim** (see 2hdma_synthesis.md §"Final issue-log JSON schema"). Workstream field is `"singlet-doublet"`; phase enum gets two SD-specific values added: `lagrangian_builder`, `validate_spec`. Issue IDs follow `sd-A-NNN` / `sd-B-NNN`.

Drop proposer's `$schema` line per critique (JSONL doesn't carry per-line schema; reference once in `result.json`).

### Q7 — Fix-loop authorization
**REJECT proposer's "strictly observe"; ADOPT 2HDM+a's narrow-scope fix-loop pattern.** User said "spin up agents to resolve any issues that arise" + "keep grinding." Observe-only contradicts the directive.
- **Two-phase contract:** the playtest session itself is observe-only (Claude executing `/demo` does not patch code mid-run; it logs and halts on blockers). The synthesizer/shift-manager has standing authority to dispatch fix subagents per `issues.jsonl` between iterations.
- See **Fix-loop scope guard** below for path prefixes and kill switch.

### Q8 — Parallelism
**REVISE.** A and B in parallel with stronger isolation than proposer specified.
- `HEPPH_STATE_ROOT` (NOT `STATE_ROOT` — verified at `plugins/model-building/SHARED.md:18-22`, honoured by `sarah-build/scripts/build.py:82` and `spheno-build/scripts/run_point.py:95`) per variant.
- Per-variant `XDG_CONFIG_HOME=<worktree>/.playtest/sd-X/xdg` to isolate global `config.json` (critique §5.2).
- Distinct SARAH model names `SingletDoublet_A` / `SingletDoublet_B` — verified parallel-safe at SARAH per `sarah-build/scripts/run_sarah.py:176-196` (per-model fcntl lock).
- MadDM `$MG5_PATH/PLUGIN/` is shared. Serialize the FIRST MadDM launch with flock on `$MG5_PATH/.playtest.lock`; subsequent per-variant launches are fine.
- **Cross-workstream serialization:** per 2HDM+a synthesis Q8, serialize SARAH `MakeUFO[]` between SD and 2HDM+a (~2 min cost). dark-su3 (no SARAH) runs fully parallel with SD.
- Wolfram seat: if single-seat, SARAH calls naturally serialize. Add a 5-second `wolframscript -code 'Print["ok"]'` smoke at launch (P5 below).

### Q9 — Artifact contract
**KEEP** proposer's tree, with hyphen fixes and 2HDM+a-aligned additions:

```
.playtest/sd-X/
├── run.log                          # ts-prefixed, full fidelity
├── console.log                      # raw stdout+stderr from /demo session
├── issues.jsonl                     # cross-workstream schema (Q6)
├── timing.json                      # {phase: wallclock_seconds}
├── env.json                         # config.json snapshot, tool versions, HEPPH_STATE_ROOT, git_sha
├── practitioner_script.used.md      # exact bytes played back
├── demo_output/singlet-doublet/     # HYPHEN — singlet_doublet_spec.yaml,
│                                    # relic.json, summary.json, summary.{pdf,png}, maddm_run/
├── state/                           # HEPPH_STATE_ROOT contents
├── xdg/                             # XDG_CONFIG_HOME contents (config.json snapshot)
└── result.json                      # {variant, passed, criteria: {1..6}, baseline_used: 0.292}
```

`result.json` first lines mirror 2HDM+a's `verdict.md` style: `VERDICT: PASS|FAIL`, `BASELINE_USED: 0.292`, `WORKSTREAM: singlet-doublet`.

### Q10 — Time budget
**REVISE per critique.** 90 min is TOTAL ceiling, not per-variant.
- Per variant cold: 25–45 min (proposer's estimate stands).
- Parallel best case: ~45 min (Wolfram allows).
- Parallel realistic: 60–80 min (Wolfram serializes).
- Hard total ceiling: **90 min** for both A and B combined.
- Repeat-A flake check only if budget remains AND A passed first try.

---

## Pre-playtest preparation steps (fix agent runs before playtest spawns)

P1. **Move stale `demo_output/singlet-doublet/` aside.** `mv demo_output/singlet-doublet/ demo_output/singlet-doublet.preplaytest-<TS>/`. Eliminates 5+ `maddm_run*` dirs + `relic_{1..4}.json` interleaving risk (critique §5.1).

P2. **Capture today's baseline.** Run `python3 -c "import json; print(json.load(open('demo_output/singlet-doublet.preplaytest-<TS>/relic.json'))['omega_h2'])"` and confirm 0.292. Pin in `result.json.baseline_used`.

P3. **Per-variant worktree setup.**
  - `git worktree add ../hep-ph-agents-sd-A main`
  - `git worktree add ../hep-ph-agents-sd-B main`
  - In each: `mkdir -p .playtest/sd-{A,B}/{state,xdg}`
  - Copy `practitioner_script.md` → `practitioner_script_B.md` with `ZN → N` rename only.

P4. **MadDM PLUGIN cleanup (one-shot).** `mv $MG5_PATH/PLUGIN/maddm.broken-backup-* /tmp/ 2>/dev/null || true`. Logged as `expected_fix_scope: tool-driver, blocking: false` if it fired. Recurrence is the issue, not the cleanup.

P5. **Wolfram smoke.** `wolframscript -code 'Print["ok"]'` exits 0 within 5s. If fails, halt — offline-night risk realized.

P6. **Verify `HEPPH_STATE_ROOT` honoured.** Quick smoke: `HEPPH_STATE_ROOT=/tmp/sd-smoke python3 -c "from plugins.model_building.skills.sarah_build.scripts.build import resolve_state_root; print(resolve_state_root())"` returns `/tmp/sd-smoke`. If env var not honoured, halt — proposer's isolation strategy fails.

P7. **Capture `env.json`.** Per variant: `git rev-parse HEAD`, `mg5_aMC --version`, MadDM plugin SHA, SARAH version, Python version, Wolfram version, full `config.json` snapshot.

All P1–P7 are in-scope under the fix-loop guard (touch only `demo_output/singlet-doublet*` or worktree-local paths under `.playtest/`).

---

## Fix-loop scope guard

**Allowed diff prefixes** (union):
- `plugins/hep-ph-demo/skills/singlet-doublet/**`
- `demo_output/singlet-doublet/**` and `demo_output/singlet-doublet.*/`
- `.playtest/sd-{A,B}/**` (worktree-local; not main repo)

**Forbidden everywhere else**, especially:
- `plugins/model-building/skills/sarah-build/**` (renderer/build — out of scope for SD playtest)
- `plugins/model-building/skills/spheno-build/**`
- `plugins/monte-carlo-tools/**`
- `plugins/hep-ph-demo/skills/2hdm-a/**`
- `plugins/hep-ph-demo/skills/dark-su3/**`
- `plugins/hep-ph-demo/skills/_shared/**` (2HDM+a synthesis owns the schema edit; SD must not touch it concurrently — see planner-to-resolve)
- `config.json` (read-only)
- `.shift-manager/**` (run state)

**Kill-switch conditions** (any one trips abort):
1. `git diff --name-only` after a fix touches a forbidden prefix → revert, log `severity: blocker, outcome: aborted_scope`, escalate.
2. Total `fix_attempts.length` for SD workstream > 5 → halt fix loop, run playtest with current state.
3. Per-failure-class iterations > 3 → mark class `blocker`, move on.
4. Wall-clock for fix phase > 30 min → halt fix loop.
5. Any attempt to invoke `/sarah-build` interactively or modify renderer → immediate abort.

---

## Issue-log JSON schema (cross-workstream — aligned with 2HDM+a)

Reference: `2hdma_synthesis.md` §"Final issue-log JSON schema". SD additions:
- `workstream: "singlet-doublet"`
- `phase` enum gains: `lagrangian_builder`, `validate_spec`
- `issue_id` pattern: `^sd-[AB]-[0-9]{3}$`
- `variant` field (string, A or B) — SD-specific; null for other workstreams.

Append-only at `.playtest/sd-X/issues.jsonl`. Fix agents append to `fix_attempts` without rewriting prior entries. `parent_issue_id` chains derived issues.

---

## Go / no-go gate (must be true before playtest agent executes)

All must be `true`:

- [ ] G1. `demo_output/singlet-doublet/` does not exist as raw dir (P1 done — moved aside).
- [ ] G2. `demo_output/singlet-doublet.preplaytest-<TS>/relic.json` parseable, `omega_h2 == 0.292 ± 0.001` (P2 done).
- [ ] G3. Both worktrees exist, both `.playtest/sd-{A,B}/{state,xdg}/` exist, `practitioner_script_B.md` differs from canonical only by `ZN → N` (P3 done; verify with `diff`).
- [ ] G4. `$MG5_PATH/PLUGIN/maddm.broken-backup-*` does not exist (P4 done).
- [ ] G5. `wolframscript -code 'Print["ok"]'` exits 0 within 5s (P5 done).
- [ ] G6. `HEPPH_STATE_ROOT=/tmp/sd-smoke` smoke returns the expected path (P6 done).
- [ ] G7. `.playtest/sd-{A,B}/env.json` exist with git_sha + tool versions (P7 done).
- [ ] G8. `git status --porcelain` in main repo + each worktree shows only files under allowed scope-guard prefixes.
- [ ] G9. 2HDM+a `_shared/summary.schema.json` edit (their P3) is either complete OR confirmed not to break SD's `summary.json` payload — see planner-to-resolve.

If any gate fails: do not spawn the playtest agent. Log to `.playtest/sd/gate_status.json`, escalate to synthesizer.

Per "keep grinding": G2/G6/G9 may be downgraded to `warning` if the underlying issue is non-trivial. G1, G3, G4, G5, G7, G8 are non-negotiable.

---

## What the planner inherits

- **Scope**: two-variant A/B playtest, observe-only during run, fix-loop authorized between iterations.
- **Baseline**: 0.292 ± 0.01 (NOT 0.163; that number is 18h stale per critique §2b).
- **Variant B**: `ZN → N` mixing-matrix rename only; `MS → MChi` dropped (covered by 2HDM+a).
- **Invocation**: Claude executing `/demo` skill in a session per worktree, NOT a CLI script. `drive.py` flag surface is fiction.
- **Isolation**: per-variant `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME` + distinct SARAH model name + flock on first MadDM launch.
- **Schema**: cross-workstream issue JSON aligned with 2HDM+a synthesis.
- **Time**: 30 min fix-prep + 90 min total playtest ceiling = 120 min wall budget for SD.
- **Cross-workstream serialize**: SARAH `MakeUFO[]` between SD and 2HDM+a; dark-su3 fully parallel.

**Planner-to-resolve** (flagged ambiguity):
1. **`_shared/summary.schema.json` ownership.** 2HDM+a synthesis P3 edits this file to add `relic_approx`/`model_source`/`model_fixture`. SD's `summary.json` payload differs (no `model_fixture`, no `relic_approx` — uses analytic-bypass directly). Planner must decide: (a) 2HDM+a edit must include explicit field defs that don't break SD's payload, OR (b) SD waits for 2HDM+a's P3 to complete and validates SD payload against the new schema before its run starts. Recommended: (a) with a one-line ack from SD lead before 2HDM+a's P3 commits.
2. **0.163 → 0.292 drift root cause.** Likely intentional change between `a05f274` (regex parser shed) and HEAD, but unverified. Should the playtest agent attempt to bisect, or just log as `major` finding? Recommended: log only; bisection is a separate workstream.
3. **Variant B failure mode interpretation.** If `ZN → N` rename causes silent SARAH success but downstream MadDM Ωh² wildly wrong, is that a `blocker` (silent breakage = the failure we hunt) or `major` (failure surfaced eventually)? Recommended: `blocker` — silent-until-physics-broken is exactly what cold-read regression catches.
4. **Repeat-A flake check budget.** If budget remains, run A a second time to characterize variance? Worth 30 min only if A passed first time. Recommended: yes — single-sample regression at ±0.01 is fragile.
