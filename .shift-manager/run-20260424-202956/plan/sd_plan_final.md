# Singlet-Doublet Implementation Plan (FINAL)

Author: plan-synthesizer (SD)
Consumers: shift-manager (orchestrator) + sonnet implementers + opus reviewers.
Source-of-truth: `sd_synthesis.md` (LOCKED). Hard-blocks from `sd_plan_critique.md` addressed inline. Operational primitives borrowed verbatim from `2hdma_plan_final.md` (lock dir, try-counter schema, cumulative-budget, opus reviewer template, gate-evaluator shell). Dark-SU(3) synth must align to same primitives.

---

## Scope

**Does**: 2-variant playtest of singlet-doublet `/demo` (A canonical, B with `ZN→N`) under per-variant worktrees; 7 prep tasks; serialized fix-loop scope-guarded to `plugins/hep-ph-demo/skills/singlet-doublet/**`.

**Does NOT**: touch `_shared/summary.schema.json` (2HDM+a owns); edit other workstream skill dirs or `plugins/{model-building,monte-carlo-tools}/**`; bisect 0.163→0.292 drift (logged finding); relitigate synthesis-locked decisions.

---

## Cross-workstream protocol

### Lock files (shared with 2HDM+a, dark-su3)
Manager creates `.shift-manager/locks/` if absent (also creates `~/.cache/hep-ph-agents/` for any tool-side caches).

| Lock path | Purpose | Acquire | Release |
|-----------|---------|---------|---------|
| `.shift-manager/locks/summary_schema.lock` | Schema-edit ownership; held by 2HDM+a P3 | Manager (2HDM+a) writes file | Manager (2HDM+a) `rm` after P3 commits |
| `.shift-manager/locks/sarah.lock` | Wolfram/SARAH mutex (3-way: SD-A, SD-B, 2HDM+a) | Sonnet wraps wolframscript with `flock` | flock auto-releases |
| `.shift-manager/locks/maddm.lock` | First-launch MadDM PLUGIN init mutex (SD-A and SD-B both) | Sonnet wraps maddm.py with `flock` | flock auto-releases |

**SARAH FIFO queue (3-way fairness, paste-ready snippet — flock(2) on macOS not strictly fair)**:

```
mkdir -p .shift-manager/locks/sarah.queue/
TS=$(date +%s%N); ID="sd-A-${TS}"  # or sd-B / 2hdma-PT1
touch .shift-manager/locks/sarah.queue/${ID}.req
while true; do
  OLDEST=$(ls -t .shift-manager/locks/sarah.queue/*.req 2>/dev/null | tail -n 1 | xargs -n 1 basename)
  [ "${OLDEST}" = "${ID}.req" ] && break
  AGE=$(($(date +%s) - $(stat -f %B .shift-manager/locks/sarah.queue/${ID}.req)))
  [ ${AGE} -gt 300 ] && { echo "{\"severity\":\"warning\",\"phase\":\"sarah\",\"hypothesis\":\"FIFO starvation >300s — infra\"}" >> .playtest/sd-X/issues.jsonl; break; }
  sleep 2
done
flock -x -w 120 .shift-manager/locks/sarah.lock wolframscript -code '...'  # flock timeout → blocker, fix_owner_hint: tool_install
rm .shift-manager/locks/sarah.queue/${ID}.req
```

### State files (manager-only writes; same dir prefix `.shift-manager/run-20260424-202956/state/`)

- `sd-tries.json`: `{"phase0_opus_rounds":{}, "fix_loop":{"skill_prose":0,"tool_driver":0,"fixture":0,"parse":0,"plot":0,"lagrangian_builder":0,"validate_spec":0}, "fix_total":0, "playtest_attempts_A":0, "playtest_attempts_B":0}`
- `sd-budget.json`: append-only, `{"phase":"<name>","wall_min":<int>}` per transition.
- `sd-merge_ready.json`: `{"prep_committed":false,"ready_for_playtest":false}` (manager flips).
- `schema_v1_1.ready`: sentinel written by 2HDM+a P3 post-commit. SD P3 polls; 30 min timeout → G9 downgrades to warning.
- `escalation.md`: hard halt.

**Hard stop**: cumulative `wall_min >= 150` → manager writes `result.json` per variant with `VERDICT: FAIL, cause: budget_exhausted`, halts. Soft warnings at 30 (entering Phase 1) and 90 min (entering fix-loop → max attempts cut to 3).

---

## Worktree topology

Worktree base `/Users/yianni/Projects/hep-ph-agents.worktrees/`; branches local-only.

| Branch | Path | Parent | Created when |
|---|---|---|---|
| `sd/prep-20260424` | `hep-ph-agents-sd-prep/` | main (a05f274) | Run start |
| `sd/playtest-A-20260424` | `hep-ph-agents-sd-A/` | `sd/prep-20260424` HEAD | gate ∈ {pass,warning} AND `ready_for_playtest=true` |
| `sd/playtest-B-20260424` | `hep-ph-agents-sd-B/` | `sd/prep-20260424` HEAD | same trigger |
| `sd/fix-<class>-<n>-20260424` | `hep-ph-agents-sd-fix/` (reused) | playtest-A HEAD (or B if isolates) | Per fix iter |

**Commit ordering** (fixes critique #3): P1–P7 commit on `sd/prep-20260424` with `[sd-prep] <P-id>: ...`. After gate pass, manager ff-merges `main → sd/prep-20260424`, sets `sd-merge_ready.prep_committed=true`, creates A and B worktrees from `sd/prep-20260424` HEAD (NOT main), flips `ready_for_playtest=true`, dispatches PT-A and PT-B in parallel.

---

## Phase 0: Prep (P1–P7)

All Phase 0 sonnet prompts begin with this preamble (paste-ready):
```
PREAMBLE: You are a sonnet implementer for the singlet-doublet workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-prep/
All paths below are relative to this worktree root unless absolute.
Allowed diff prefixes (`git diff --name-only` ⊆ this set):
  - plugins/hep-ph-demo/skills/singlet-doublet/**
  - demo_output/singlet-doublet/**
  - demo_output/singlet-doublet.preplaytest-*/**
  - .playtest/sd-A/**
  - .playtest/sd-B/**
  - .gitignore (P1 only)
  - .shift-manager/run-20260424-202956/workstreams/sd/** (state captures)
Forbidden everywhere else (especially plugins/model-building/**, plugins/monte-carlo-tools/**, plugins/hep-ph-demo/skills/{2hdm-a,dark-su3,_shared}/**, config.json, .shift-manager/locks/**, .shift-manager/state/**).
Synthesis-locked decisions (do not relitigate): baseline 0.292±0.01; single-axis B perturbation (ZN→N only, NOT MS→MChi); observe-only during playtest; six success criteria.
Commit each step with `[sd-prep] <P-id>: <one-line>`.
```

### P1 — Move stale `demo_output/singlet-doublet/` aside (3 min, serial first)
- **Deliverable**: `demo_output/singlet-doublet.preplaytest-<TS>/` exists; `demo_output/singlet-doublet/` absent; `.shift-manager/run-20260424-202956/workstreams/sd/baseline_ts.txt` contains `<TS>`.
- **Prompt body**: `Task P1: TS=$(date -u +%Y%m%d%H%M%S); mv demo_output/singlet-doublet "demo_output/singlet-doublet.preplaytest-${TS}"; mkdir -p .shift-manager/run-20260424-202956/workstreams/sd/; echo "${TS}" > .shift-manager/run-20260424-202956/workstreams/sd/baseline_ts.txt; mkdir -p demo_output/singlet-doublet; touch demo_output/singlet-doublet/.gitkeep; commit.`
- **Success**: `test ! -e demo_output/singlet-doublet/relic.json && test -f .shift-manager/run-20260424-202956/workstreams/sd/baseline_ts.txt`

### P2 — Capture baseline (5 min, parallel after P1) — **DETERMINISM-CHECK ONLY**
- **Decision (critique #8)**: captured value drives Variant A's "G3 determinism check" (renamed from regression). 0.292 from sd_synthesis line 130 is hardcoded as `hardcoded_reference`. Captured ≠ 0.292±0.01 → escalate `major`, still proceed with 0.292 as regression target.
- **Deliverable**: `.shift-manager/run-20260424-202956/workstreams/sd/baseline.json` with `{omega_h2, source_ts, hardcoded_reference: 0.292, tolerance: 0.01, drift_flag}`.
- **Prompt body**: `Task P2: TS=$(cat .shift-manager/run-20260424-202956/workstreams/sd/baseline_ts.txt); python3 -c "import json; d=json.load(open(f'demo_output/singlet-doublet.preplaytest-${TS}/relic.json')); o=d['omega_h2']; ref=0.292; out={'omega_h2':o,'source_ts':'${TS}','hardcoded_reference':ref,'tolerance':0.01,'drift_flag':abs(o-ref)>0.01}; json.dump(out, open('.shift-manager/run-20260424-202956/workstreams/sd/baseline.json','w'), indent=2)"; commit.`
- **Success**: `python3 -c "import json; d=json.load(open('.shift-manager/run-20260424-202956/workstreams/sd/baseline.json')); assert 'omega_h2' in d"`

### P3 — Variant config skeleton + schema-sentinel wait (10 min, sequential after P1; gates P6/P7)
- **Deliverable**: `.playtest/sd-{A,B}/{state,xdg/hep-ph-agents}` (these travel into A/B worktrees when created from prep HEAD); `xdg/hep-ph-agents/config.json` per variant SEEDED by copy from `~/.config/hep-ph-agents/config.json` (critique #12); `practitioner_script_B.md` at `.shift-manager/run-20260424-202956/workstreams/sd/` (run-state, NOT plugin dir, per critique §4.1) with single `ZN→N` rename; `schema_wait_result.json` recording schema-sentinel poll.
- **Schema-sentinel wait (critique #5)**: poll `.shift-manager/run-20260424-202956/state/schema_v1_1.ready` for up to 1800s. Found → G9 pass. Timeout → G9 warning (R3-style downgrade); proceed.
- **Prompt body**: `Task P3:
  mkdir -p .playtest/sd-A/state .playtest/sd-A/xdg/hep-ph-agents .playtest/sd-B/state .playtest/sd-B/xdg/hep-ph-agents .shift-manager/run-20260424-202956/workstreams/sd/
  for V in A B; do cp ~/.config/hep-ph-agents/config.json .playtest/sd-${V}/xdg/hep-ph-agents/config.json; done
  cp plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md
  sed -i.bak 's/\\bZN\\b/N/g' .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md && rm .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md.bak
  diff plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md  # only ZN→N
  DEADLINE=$(($(date +%s)+1800)); while [ $(date +%s) -lt $DEADLINE ]; do [ -f .shift-manager/run-20260424-202956/state/schema_v1_1.ready ] && break; sleep 10; done
  [ -f .shift-manager/run-20260424-202956/state/schema_v1_1.ready ] && SR=1 || SR=0
  echo "{\"schema_ready\": ${SR}}" > .shift-manager/run-20260424-202956/workstreams/sd/schema_wait_result.json
  Commit. (Manager creates A/B worktrees AFTER gate passes.)`
- **Success**: `test -f .playtest/sd-A/xdg/hep-ph-agents/config.json && test -f .playtest/sd-B/xdg/hep-ph-agents/config.json && [ "$(grep -c '\\bZN\\b' .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md)" = "0" ]`

### P4 — MadDM PLUGIN cleanup (3 min, parallel)
- **Prompt**: `Task P4: MG5_PATH=$(python3 -c "import json; print(json.load(open('.playtest/sd-A/xdg/hep-ph-agents/config.json'))['madgraph_path'])"); mv "${MG5_PATH}/PLUGIN/maddm.broken-backup-"* /tmp/ 2>/dev/null || true; ls "${MG5_PATH}/PLUGIN/" | grep -c broken-backup > .shift-manager/run-20260424-202956/workstreams/sd/p4_cleanup.txt; commit.`
- **Success**: `[ "$(cat .shift-manager/run-20260424-202956/workstreams/sd/p4_cleanup.txt)" = "0" ]`

### P5 — Wolfram smoke (1 min, parallel)
- **Prompt**: `Task P5: timeout 5 wolframscript -code 'Print["ok"]' > .shift-manager/run-20260424-202956/workstreams/sd/wolfram_smoke.txt 2>&1; echo "exit=$?" >> .shift-manager/run-20260424-202956/workstreams/sd/wolfram_smoke.txt; commit.`
- **Success**: `grep -q "^ok$" wolfram_smoke.txt && grep -q "exit=0" wolfram_smoke.txt`

### P6 — `HEPPH_STATE_ROOT` smoke (3 min, sequential after P3)
- **Prompt**: `Task P6: HEPPH_STATE_ROOT=/tmp/sd-smoke-$$ python3 -c "import sys; sys.path.insert(0, 'plugins/model-building/skills/sarah-build/scripts'); from build import resolve_state_root; print(resolve_state_root())" > .shift-manager/run-20260424-202956/workstreams/sd/state_root_smoke.txt 2>&1; commit.`
- **Success**: `grep -q "^/tmp/sd-smoke-" state_root_smoke.txt`

### P7 — Capture `env.json` per variant (8 min, sequential after P3, P6)
- **Prompt body**: `Task P7: For V in A B: write .playtest/sd-${V}/env.json with keys: git_sha (git rev-parse HEAD), mg5_version (${MG5_PATH}/bin/mg5_aMC --version | head -1), maddm_plugin_sha ((cd ${MG5_PATH}/PLUGIN/maddm && git rev-parse HEAD) || echo "no-git"), sarah_version (grep VersionSARAH ${SARAH_PATH}/Package.m | head -1 || echo "unknown"), python_version (python3 --version), wolfram_version (wolframscript -code 'Print[$Version]'), config_json_snapshot (full JSON copy of .playtest/sd-${V}/xdg/hep-ph-agents/config.json). Commit.`
- **Success**: `for V in A B; do python3 -c "import json; d=json.load(open(f'.playtest/sd-${V}/env.json')); assert all(k in d for k in ['git_sha','mg5_version','python_version','wolfram_version','config_json_snapshot'])"; done`

### Phase 0 wall budget
Parallel: max(P2=5, P4=3, P5=1) + serial(P1=3, P3=10 incl up-to-30min wait, P6=3, P7=8) = nominal **27 min**, with schema-wait worst case **57 min**. Hard ceiling: **45 min** of effective work (schema-wait excluded if it dominates; G9 downgrade auto-triggers at 30 min wait).

---

## Phase 1: Playtest — 2 variants (A, B) in parallel

Manager creates worktrees A and B from `sd/prep-20260424` HEAD (after gate pass + `sd-merge_ready.ready_for_playtest=true`). Both sonnet sub-agents launch concurrently. Sub-agents are OBSERVE-ONLY: log to `issues.jsonl`, halt on first BLOCKER, do NOT modify code mid-run.

### JIT-loading directive (critique #9, both variants)

Sonnet walks up to 8 chained SKILL.md files. To bound context:
1. Before Phase 1 step 1, read `demo/SKILL.md` + `singlet-doublet/SKILL.md` ONCE.
2. Distill to `.playtest/sd-X/runbook.md` (~150 lines: per-phase bash commands, expected exit codes, expected artifacts, practitioner Q-A verbatim).
3. For each chain step (lagrangian-builder → sarah-build → spheno-build → madgraph → maddm → plot → summary), read that SKILL.md ONLY on entering; append distilled commands to `runbook.md`.
4. Execute from `runbook.md` thereafter; do not re-read SKILL.md.
5. **Context budget guard**: at every phase boundary, if self-estimated context >70%, write state to `run.log`, log `blocker, phase: agent_capacity, hypothesis: "context overflow during /demo emulation"`, exit. Do NOT compact silently.

### Variant A practitioner prompt (paste-ready, verbatim)

```
You are the Variant A playtest practitioner for the singlet-doublet workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-A/
Allowed diff prefixes: .playtest/sd-A/**, demo_output/singlet-doublet/** (within this worktree only).
You are OBSERVE-ONLY: log to .playtest/sd-A/issues.jsonl, do NOT modify any code or skill prose. Halt on first BLOCKER.

Every bash command in this session MUST be prefixed:
  cd ${WORKTREE_PATH} && export HEPPH_STATE_ROOT="${WORKTREE_PATH}.playtest/sd-A/state" && export XDG_CONFIG_HOME="${WORKTREE_PATH}.playtest/sd-A/xdg" && <command>
Or run inside a shell with these exports set.

JIT-LOADING: see "JIT-loading directive" above. Working memory file: .playtest/sd-A/runbook.md.

PRACTITIONER ANSWERS (verbatim from practitioner_script.md):
Model picker: "singlet-doublet"; MS=150; MPsi=500; y=1; theta=0; Mixing matrix: ZN; Constraint: relic only.
SARAH model name (separate prompt before Q1): "SingletDoublet_A".

PHASE ORDER:
0. Preflight: read xdg/hep-ph-agents/config.json; check each tool binary responds.
1-3. Intro/picker → "continue", "singlet-doublet".
4. /lagrangian-builder (JIT-read SKILL.md, execute, capture to console.log).
5. /sarah-build. WRAP wolframscript using FIFO+flock:
     [FIFO snippet from "Cross-workstream protocol" with ID="sd-A"]; then
     flock -x -w 120 .shift-manager/locks/sarah.lock wolframscript -code 'Start["SingletDoublet_A"]; MakeUFO[]; Quit[]'
6-7. /spheno-build, /madgraph.
8. /maddm — WRAP first invocation:
     flock -x -w 300 .shift-manager/locks/maddm.lock <maddm cmd>
   (shared lock with Variant B).
9-10. plot, summary.
11. Verdict: write .playtest/sd-A/result.json. First 5 lines EXACTLY:
    VERDICT: PASS|FAIL
    BASELINE_USED: <captured-from-baseline.json>
    HARDCODED_REFERENCE: 0.292
    WORKSTREAM: singlet-doublet
    VARIANT: A
    Then 6-criterion table.

SUCCESS CRITERIA (Variant A):
1. summary.json parseable, summary.json.ran contains "relic", relic.json.status=="ok".
2. relic.json.omega_h2 finite in [0.10, 0.40].
3. DETERMINISM CHECK: omega_h2 within ±0.01 of BASELINE_USED (P2 value). ALSO log HARDCODED_REGRESSION: pass iff |omega-0.292|<=0.01. Determinism pass + hardcoded fail → log major, phase:parse, hypothesis:"baseline drift since synthesis time".
4. summary.{pdf,png} exist, >1KB.
5. singlet_doublet_spec.yaml exists; validate_spec.py exits 0.
6. Wallclock <=45 min.

ISSUE LOG (cross-workstream, append-only at .playtest/sd-A/issues.jsonl): workstream="singlet-doublet", variant="A", issue_id "sd-A-NNN", phase, severity (blocker|major|minor|warning), hypothesis, fix_owner_hint, auto_repro_command, expected_fix_scope.
ON BLOCKER: tail 200 lines stderr/stdout, append issue, write result.json (VERDICT:FAIL + cause), commit, exit. ALWAYS write result.json on exit (incl wall_timeout).
COMMIT: `git add -A && git commit -m "[sd-playtest-A] result: <verdict>"`.
```

### Variant B practitioner prompt (delta from Variant A)

```
Identical to Variant A prompt with substitutions:
- WORKTREE_PATH=...hep-ph-agents-sd-B/; all `.playtest/sd-A/` → `.playtest/sd-B/`.
- HEPPH_STATE_ROOT=${WORKTREE_PATH}.playtest/sd-B/state
- XDG_CONFIG_HOME=${WORKTREE_PATH}.playtest/sd-B/xdg
- Practitioner script: .shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md (mixing matrix N, not ZN).
- SARAH model name: SingletDoublet_B (set via interview prompt before Q1; do NOT edit script).
- FIFO ID: sd-B. Issue IDs: sd-B-NNN. Commit msg: [sd-playtest-B] result: <verdict>.

VARIANT B SUCCESS CRITERIA (overrides A's 2 and 3):
- 2: omega_h2 finite in [0.10, 0.40] OR severity:major entry pinpointing ZN→N clash before MadDM (surfaced collision = pass; hunted failure).
- 3: omega_h2 within ±0.01 of BASELINE_USED OR issues.jsonl has severity:major entry with hypothesis containing "N" + "MSSM" + ("collision"|"reserved"|"clash"), logged before MadDM.
- If SARAH errors at parse on B (hard-fail): log major (NOT blocker), criteria 2/3 pass via alternate, criteria 4-5 may N/A, criterion 6 applies. VERDICT: PASS.

If B's SARAH-parse contaminates SD-A via shared SARAH state:
  Log blocker, hypothesis:"B contamination of A via shared SARAH state". Manager aborts B, restarts A with HEPPH_STATE_ROOT=/tmp/sd-A-recover-$$.
```

### Recording targets (under `.playtest/sd-X/`)

`console.log` (ts-prefixed stdout+stderr), `run.log` (phase narration), `runbook.md` (JIT-distilled), `issues.jsonl` (append-only schema), `demo_output/singlet-doublet/` (relic.json, summary.json, summary.{pdf,png}), `timing.json`, `env.json` (from P7), `result.json` (VERDICT + 6-criterion table).

### Timeouts / fallback

- 45 min wall per variant (criterion 6). On timeout: ALWAYS write `result.json` (`cause: wall_timeout`) + commit.
- MadDM single-launch >20 min: `kill -ABRT <pid> && sample <pid> > .playtest/sd-X/launch_hang.sample`, log blocker, abort.
- Combined Phase 1 ceiling: **75 min** (parallel; synthesis 90 min minus 15 buffer).
- If `${MG5_PATH}/PLUGIN/maddm.broken-backup-*` recurs mid-run, sub-agent re-runs P4 cleanup before next phase. Append to `runbook.md`.

---

## Phase 2: Fix-loop (conditional, SERIALIZED)

### Trigger
Phase 1 produces ≥1 issue with `severity ∈ {blocker, major}` AND `expected_fix_scope ∈ {skill_prose, tool_driver, fixture, parse, plot, lagrangian_builder, validate_spec}` AND `auto_repro_command` non-null. Issues with `expected_fix_scope ∈ {physics, unknown, renderer}` are out-of-scope; log `outcome: deferred`, escalate to user.

Skip Phase 2 iff Phase 1 PASS on both variants.

### Per-iteration (SERIALIZED, no parallel fix worktrees)

1. Pick highest-severity unresolved blocker (prefer A-issues for shared classes).
2. Create worktree `sd/fix-<class>-<n>-20260424` from playtest-A HEAD (or B if class isolates).
3. Dispatch sonnet implementer → 4. Dispatch opus reviewer.
5. outcome=pass → `git merge --no-ff` into appropriate playtest branch.
6. Manager updates `sd-tries.json`: `fix_loop[<class>]+=1`, `fix_total+=1`.
7. Goto 1 unless stop.

### Sonnet implementer prompt (paste-ready)

```
You are a sonnet fix-implementer for singlet-doublet.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-fix/
ISSUE_ID=<issue_id from issues.jsonl>
Allowed diff prefixes: plugins/hep-ph-demo/skills/singlet-doublet/**, demo_output/singlet-doublet/**, .playtest/sd-{A,B}/**.
Forbidden elsewhere (esp plugins/model-building/**, plugins/monte-carlo-tools/**, plugins/hep-ph-demo/skills/{2hdm-a,dark-su3,_shared}/**, config.json, .shift-manager/locks/**).
SYNTHESIS-LOCKED (do not relitigate): baseline 0.292±0.01; ZN→N is the only B perturbation; observe-only Phase 1; six success criteria; MS=150, MPsi=500, y=1, theta=0; SingletDoublet_{A,B} model names.

Read .playtest/sd-X/issues.jsonl, find ${ISSUE_ID}. Reproduce via auto_repro_command. Fix in scope. Append to fix_attempts: {ts,diff_path,outcome}. Re-run only the failing phase. Commit `[sd-fix-<class>-<n>] <issue_id>: <one-line>`.
```

### Opus reviewer prompt (paste-ready)

```
You are an opus reviewer for a singlet-doublet fix attempt.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-fix/
ISSUE_ID=<issue_id>

SYNTHESIS-LOCKED DECISIONS (MAY NOT relitigate; reject any contradicting diff):
- Baseline 0.292±0.01 (hardcoded); P2-captured = determinism check only.
- Variant B perturbation: ZN→N ONLY (MS→MChi was REJECTED at synthesis — 2HDM+a covers it).
- Variant prompts: MS=150, MPsi=500, y=1, theta=0 (radians). Models: SingletDoublet_{A,B}.
- Phase 1 observe-only; six-criterion success table is exhaustive.
- 2HDM+a owns _shared/summary.schema.json (do NOT touch). 0.163→0.292 drift = logged finding only, NOT a bisection target.

SCOPE GUARD — forbidden prefixes (any diff touching these = aborted_scope):
- plugins/model-building/**
- plugins/monte-carlo-tools/**
- plugins/hep-ph-demo/skills/2hdm-a/**
- plugins/hep-ph-demo/skills/dark-su3/**
- plugins/hep-ph-demo/skills/_shared/**
- config.json
- .shift-manager/locks/**
- .shift-manager/state/** (excluding workstream-owned subdir under workstreams/sd/)

CHECKS:
1. Run `git diff --name-only HEAD~1 HEAD` from WORKTREE_PATH. Every line must match an allowed prefix from the implementer prompt; any forbidden prefix → outcome=aborted_scope, halt.
2. Run the issue's auto_repro_command. If now passes → outcome=pass.
3. If repro still fails but progress observable → outcome=fail.
4. Confirm no synthesis-locked decision was contradicted.

Write verdict to .shift-manager/run-20260424-202956/state/sd_fix_review_<class>_<n>.md with first line `OUTCOME: pass|fail|aborted_scope`.
```

### Stopping rules
- All triggering blockers pass → exit, dispatch one re-playtest of affected variant.
- `fix_total >= 5` → halt.
- Single class hits 3 sonnet+opus rounds without pass → opus-opus pair (1 round). Still fails → `unfixable_in_budget`, halt.
- Any `outcome: aborted_scope` → halt (architectural escape).
- **Phase 2 wall (incl all opus rounds) ≥45 min** → halt (critique #10; was 30).
- Cumulative SD wall ≥150 min → halt, skip re-playtest, write `escalation.md`.

### Re-playtest (single, conditional)
If fix-loop halts with all triggering blockers passed AND wall budget remains AND `playtest_attempts_<variant> < 2`: dispatch one re-playtest from post-merge HEAD; fresh worktree `sd/playtest-<variant>-2-20260424`. Manager appends to `sd-tries.json` after each opus review.

---

## Gate evaluator (inline)

After Phase 0 commits land on `sd/prep-20260424`, manager dispatches gate-evaluator sonnet with this exact prompt:

```
You are the gate-evaluator for the singlet-doublet prep phase.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/hep-ph-agents-sd-prep/
Run each gate G1–G9 from WORKTREE_PATH. Write .playtest/sd/gate_status.json:
  {"gates":{"G1":{"status":"pass|fail|warning","evidence":"<output>"},...},"overall":"pass|warning|fail"}

Path shortcut for state files: SD_WS=.shift-manager/run-20260424-202956/workstreams/sd

G1 [NON-NEG]. P1 done — stale dir moved aside.
    `test ! -e demo_output/singlet-doublet/relic.json && ls demo_output/singlet-doublet.preplaytest-* >/dev/null 2>&1`
G2 [NON-DOWN]. P2 done — baseline.json captured (drift_flag=true logged but does NOT fail this gate).
    `python3 -c "import json; d=json.load(open('${SD_WS}/baseline.json')); assert isinstance(d['omega_h2'],(int,float)) and 'hardcoded_reference' in d"`
G3 [NON-NEG]. P3 done — per-variant XDG configs + B script.
    `test -f .playtest/sd-A/xdg/hep-ph-agents/config.json && test -f .playtest/sd-B/xdg/hep-ph-agents/config.json && test -f ${SD_WS}/practitioner_script_B.md && [ "$(grep -c '\\bZN\\b' ${SD_WS}/practitioner_script_B.md)" = "0" ]`
G4 [NON-NEG]. P4 done — MadDM backups absent.
    `MG5_PATH=$(python3 -c "import json; print(json.load(open('.playtest/sd-A/xdg/hep-ph-agents/config.json'))['madgraph_path'])"); [ "$(ls "${MG5_PATH}/PLUGIN/" 2>/dev/null | grep -c broken-backup)" = "0" ]`
G5 [NON-NEG]. P5 done — Wolfram smoke.
    `grep -q "^ok$" ${SD_WS}/wolfram_smoke.txt && grep -q "exit=0" ${SD_WS}/wolfram_smoke.txt`
G6 [NON-NEG]. P6 done — HEPPH_STATE_ROOT honoured.
    `grep -q "^/tmp/sd-smoke-" ${SD_WS}/state_root_smoke.txt`
G7 [NON-NEG]. P7 done — env.json per variant.
    `for V in A B; do python3 -c "import json; d=json.load(open(f'.playtest/sd-${V}/env.json')); assert all(k in d for k in ['git_sha','mg5_version','python_version','wolfram_version','config_json_snapshot'])"; done`
G8 [NON-NEG]. git status --porcelain only allowed prefixes.
    `cd ${WORKTREE_PATH} && git status --porcelain | awk '{print $2}' | grep -vE '^(plugins/hep-ph-demo/skills/singlet-doublet/|demo_output/singlet-doublet|\.playtest/sd-|\.shift-manager/run-20260424-202956/workstreams/sd/|\.gitignore$)' | wc -l` = 0
G9 [DOWNGRADABLE→warning if ${SD_WS}/schema_wait_result.json has schema_ready=0]. Schema sentinel.
    `test -f .shift-manager/run-20260424-202956/state/schema_v1_1.ready`

OVERALL:
- Any non-neg fails (G1,G3-G8) OR non-downgradable G2 fails → overall=fail.
- Only G9 warning → overall=warning. Else → overall=pass.
Exit by writing gate_status.json. No other output.
```

Manager reads `gate_status.json`. If `overall ∈ {pass, warning}` → flip `sd-merge_ready.json.ready_for_playtest=true`, dispatch PT-A and PT-B in parallel. Else → halt with `cause: gate_failure: <gate_id>`, write `escalation.md`.

---

## Four planner-to-resolve answers (final, locked)

1. **Schema ownership** — 2HDM+a owns `_shared/summary.schema.json`; SD reads. Sign-off via file-gate `schema_v1_1.ready` sentinel (2HDM+a P3 writes post-commit). SD P3 polls 1800s. Found → G9 pass. Timeout → G9 warning, Phase 1 proceeds; mid-run schema-validation fail → `validate_spec, minor`.
2. **0.163→0.292 drift** — log only. P2 captures determinism baseline; 0.292 hardcoded as regression target. A reproduces 0.292±0.01 → drift was real (likely intentional between a05f274 and HEAD per devlog 2026-04-22). Bisection is a separate workstream.
3. **Variant B failure interpretation** — `major` if SARAH/MadDM surface ZN→N clash before MadDM completes. `blocker` only if rename causes silent SARAH success + downstream Ωh² wildly wrong. Surfaced collision = PASS (criterion-3 alternate); silent-broken = FAIL.
4. **Repeat-A flake** — skip if cumulative wall >90 min at decision. If <60 min AND A passed AND no Phase 2: rerun A once with 30-min cap. Manager checks `sd-budget.json` before dispatching.

---

## Failure recovery

| Trigger | Behavior |
|---|---|
| SKILL.md drift (P3 finds commits > a05f274 on demo/ or singlet-doublet/ SKILL.md) | Log `major, phase: preflight, hypothesis: "skill text drifted"`, proceed; opus rejects fix-loop diffs that conflict with drifted prose. |
| Variant B silent `N` rebind to MSSM neutralino | `blocker, phase: sarah-build`, halt B. If A unaffected → A continues. If A subsequently fails → abort B, restart A with fresh `HEPPH_STATE_ROOT=/tmp/sd-A-recover-$$` + clean SARAH model dir. |
| Baseline drift P2 vs Phase 1 | Both within ±0.01 of 0.292 → criteria 2,3 pass. P2 in / Phase-1 out → criterion-3 fail (fix-loop trigger). Both out → `major, phase: parse, hypothesis: "regression from 0.292"`. |
| SARAH FIFO starvation >300s | `warning, phase: sarah-build, hypothesis: "FIFO starvation — infra"`, force flock contention. Not a physics blocker. |
| Schema sentinel never appears | G9 → warning, Phase 1 proceeds. Mid-run schema validation fail → `validate_spec, minor`. Verdict unaffected. |
| MadDM backup recurrence mid-Phase-1 | Sub-agent re-runs cleanup before next phase. Not a fix-loop trigger. |
| Phase 0 wall >45 min | Apply R3-style downgrades (G9→warning); other non-neg fails → `cause: prep_unrecoverable`. |
| Cumulative SD wall ≥150 min | Hard halt; partial `result.json` + `escalation.md`. |

---

## Status marker files (manager polls between dispatches)

State dir prefix `.shift-manager/run-20260424-202956/state/`; locks dir `.shift-manager/locks/`.

| File | Writer | Read when | Action |
|---|---|---|---|
| `sd-tries.json` | Manager | Before dispatch | Budget allows next iter? |
| `sd-budget.json` | Manager | After phase transition | Hard-stop vs 150 min |
| `sd-merge_ready.json` | Manager | Before A/B worktree create | Only when `ready_for_playtest=true` |
| `schema_v1_1.ready` | 2HDM+a P3 sonnet | SD P3, gate G9 | Pass G9 if present; warning if absent at eval |
| `gate_status.json` (prep wt `.playtest/sd/`) | gate-evaluator | Post-Phase 0 | pass/warning → flip ready_for_playtest |
| `.playtest/sd-{A,B}/result.json` | PT sonnet (or manager halt) | Post-Phase 1 | Fix-loop trigger? |
| `.playtest/sd-{A,B}/issues.jsonl` | PT sonnet | Per fix iter | Pick next blocker |
| `sd_fix_review_<class>_<n>.md` | Opus reviewer | After each fix iter | Merge / retry / halt |
| `escalation.md` | Manager | On hard halt | End SD |
| `locks/{sarah,maddm}.lock` | flock auto | per invocation | OS-managed |
| `locks/sarah.queue/*.req` | Sonnet | self-managed | Sonnet removes on release |

All polls = file-existence + `head -1` or single `jq` read. No judgment.

---

End of plan.
