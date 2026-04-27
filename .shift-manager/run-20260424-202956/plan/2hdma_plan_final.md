# 2HDM+a Implementation Plan (FINAL)

Author: plan-synthesizer
Consumers: shift-manager (orchestrator) + sonnet implementers + opus reviewers.
Source-of-truth: `2hdma_synthesis.md` (LOCKED). Hard-blocks from `2hdma_plan_critique.md` are addressed inline.

---

## Scope

**This plan does**:
- Reproduce the 2HDM+a relic-density playtest end-to-end via the hand-crafted SARAH fixture path.
- Patch the seven prep items (P1–P7) under `plugins/hep-ph-demo/skills/2hdm-a/**`, `_shared/summary.schema.json` (one file only), and `demo_output/2hdm-a/**`.
- Run a tightly scoped fix-loop (≤5 attempts) against blockers surfaced by the playtest.

**This plan does NOT do**:
- Renderer backport (`plugins/model-building/skills/sarah-build/**` is FORBIDDEN).
- Code fixes outside `plugins/hep-ph-demo/skills/2hdm-a/**`, `demo_output/2hdm-a/**`, or `_shared/summary.schema.json`.
- Coordinate with SD/dark-su3 beyond the schema-edit lock and SARAH mutex.
- Re-litigate synthesis-locked decisions (Wchi, ±2% band, fixture path, channel ≥30%, dual sentinel).

---

## Cross-workstream protocol

### Lock files
Manager creates the directory `.shift-manager/locks/` if absent.

| Lock path | Purpose | Acquire | Release |
|-----------|---------|---------|---------|
| `.shift-manager/locks/summary_schema.lock` | Schema-edit ownership | Manager writes file containing `2hdm-a/run-20260424-202956` BEFORE dispatching P3 | Manager `rm` after P3 commit lands |
| `.shift-manager/locks/sarah.lock` | Wolfram/SARAH mutex (shared with SD) | Sonnet runs `flock -x -w 120 .shift-manager/locks/sarah.lock <wolframscript cmd>` | flock auto-releases on exit |

Sonnet prompts that touch SARAH MUST wrap the call. Example boilerplate (paste-ready):
```
flock -x -w 120 /Users/yianni/Projects/hep-ph-agents/.shift-manager/locks/sarah.lock \
  wolframscript -code '<<SARAH`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'
```
If `flock` exits 1 (timeout), sonnet logs a `severity: blocker, fix_owner_hint: tool_install` issue and aborts.

### Try-counter persistence
File: `.shift-manager/run-20260424-202956/state/2hdma-tries.json`

Initial content (manager writes at run start):
```json
{"phase0_opus_rounds": {}, "fix_loop": {"patcher": 0, "schema": 0, "fixture": 0, "skill_prose": 0, "parse": 0, "plot": 0}, "fix_total": 0, "playtest_attempts": 0}
```

Manager updates this file as a deliberate write step BEFORE dispatching the next sonnet/opus pair. No agent reads/writes it; only the manager.

### Cumulative-budget tracking
File: `.shift-manager/run-20260424-202956/state/2hdma-budget.json`

Manager appends an entry at every phase transition:
```json
{"phase": "prep_start", "wall_min": 0}
{"phase": "prep_done", "wall_min": 38}
{"phase": "playtest_start", "wall_min": 40}
...
```

**Hard stop**: After every phase transition, manager checks `wall_min`. If `wall_min >= 180`, manager writes `demo_output/2hdm-a/playtest_log/verdict.md` with `VERDICT: FAIL` + `cause: budget_exhausted` and halts. No further dispatches.

Soft warnings:
- `wall_min >= 60` entering playtest → log warning.
- `wall_min >= 120` entering fix-loop → fix-loop max-attempts cut to 3 (not 5).
- `wall_min >= 150` entering re-playtest → skip re-playtest, write current verdict.

---

## Worktree topology

| Branch | Path | Parent | Created when |
|--------|------|--------|--------------|
| `2hdma/prep-20260424` | `.../2hdma-prep/` | `main` (a05f274) | Run start |
| `2hdma/playtest-20260424` | `.../2hdma-playtest/` | `2hdma/prep-20260424` HEAD | After gate=pass/warning |
| `2hdma/fix-<class>-<n>-20260424` | `.../2hdma-fix-<class>-<n>/` | `2hdma/playtest-20260424` HEAD | Serialized per fix iter |
| `2hdma/playtest-2-20260424` | `.../2hdma-playtest-2/` | `2hdma/playtest-20260424` (post-fix-merge) | After fix-loop halts |

Worktree base: `/Users/yianni/Projects/hep-ph-agents.worktrees/`.

**Commit ordering**: (1) Each P/R task = one commit on prep branch. (2) Manager `git merge --ff-only` main→prep ONLY after gate passes. (3) Playtest worktree creation requires `gate_status.json` overall ∈ {pass, warning}. (4) Fix worktrees serialized; manager merges fix-N into playtest before creating fix-(N+1). (5) On merge conflict, dispatch fix-merger sonnet (allowed scope = fix-loop guard; out-of-scope conflict → `outcome: aborted_scope`).

---

## Phase 0: Prep (P1–P7 + R1/R2/R3)

All Phase 0 sonnet prompts begin with this preamble (paste-ready):
```
PREAMBLE: You are a sonnet implementer for the 2HDM+a workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-prep/
Repo root inside this worktree. All paths below are relative to that root unless absolute.
Allowed diff prefixes (any commit you create MUST satisfy `git diff --name-only` ⊆ this set):
  - plugins/hep-ph-demo/skills/2hdm-a/**
  - plugins/hep-ph-demo/skills/_shared/summary.schema.json
  - demo_output/2hdm-a/**
  - .gitignore (P1 only)
Forbidden everywhere else. If you need to edit elsewhere, STOP and emit a blocker note to your stdout.
Synthesis-locked decisions (do not relitigate): Wchi=0.0; Ωh² band ±2%; fixture path only; renderer is debt; channel ≥30% is soft; dual patch sentinel mandatory.
Commit each step with message `[2hdma-prep] <P-id>: <one-line>`.
```

All tasks: agent=sonnet (R1/R3 are opus), worktree=`2hdma-prep`. Each task commits with `[2hdma-prep] <P-id>: <one-line>`. Sonnet prompt = `<PREAMBLE>` + the task body shown below.

### P1 — Clean + sentinel gitignore (3 min, serial first)
- **Deliverable**: `demo_output/2hdm-a/` removed; `.gitignore` (3 lines: `playtest_log/.patched`, `playtest_log/.output_marker`, `playtest_log/output_mtime.txt`); `.cleaned` with `<ISO> <sha>`.
- **Prompt body**: `Task P1: rm -rf demo_output/2hdm-a/. Recreate dir. Write demo_output/2hdm-a/.gitignore (3 lines above). Write demo_output/2hdm-a/.cleaned: "$(date -u +%FT%TZ) $(git rev-parse HEAD)". Commit.`
- **Success**: `test -f demo_output/2hdm-a/.gitignore && test -f demo_output/2hdm-a/.cleaned && test ! -f demo_output/2hdm-a/fix_loop/POST_MORTEM.md`
- **Note**: P1 deletes `fix_loop/POST_MORTEM.md`; P4 must run AFTER P1.
- **On-failure**: dispatch worktree-medic.

### P2 — Audit patch_paramcard.py (25 min, parallel after P1)
- **Deliverable**: `plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md`; edited `patch_paramcard.py` with `Wchi=0.0`.
- **Prompt body**: `Task P2: Read patch_paramcard.py + recover POST_MORTEM via git show main:demo_output/2hdm-a/fix_loop/POST_MORTEM.md. For each block (HMIX, ZAMIX θ_a=0.1, ZHMIX, ZPMIX α=-0.1, Wchi, others) classify KEEP|REMOVE|DEFER. Wchi := 0.0 (LOCKED, do not relitigate). Add --dry-run flag, run, paste output into AUDIT.md "validation" section. Commit.`
- **Success**: `test -f plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md && grep -qE "Wchi.*=.*0\.0" plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py`
- **On-failure**: opus applies "audit-good-enough" — pass if HMIX, ZAMIX θ_a, Wchi, α decided; lower-risk blocks default KEEP+TODO.

### P3 — Reconcile _shared/summary.schema.json (20 min, parallel)
- **Deliverable**: edited schema; `plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` validating 3 stubs (2hdm-a from SKILL.md L470-478, SD, dark-su3).
- **Lock**: manager writes `.shift-manager/locks/summary_schema.lock` BEFORE dispatch; removes after commit lands.
- **Prompt body**: `Task P3: Add explicit defs for relic_approx (boolean), model_source (string), model_fixture (string) to _shared/summary.schema.json. Keep additionalProperties:false. Construct stub payloads from each SKILL.md. Write test_summary_schema.py validating all three. Commit.`
- **Success**: `python3 plugins/hep-ph-demo/skills/_shared/test_summary_schema.py`
- **On-failure**: 2 attempts to add missing field defs; then escalate to opus pair.

### P4 — Best-effort iter_6_notes.md (20 min, parallel after P1)
- **Deliverable**: `demo_output/2hdm-a/fix_loop/iter_6_notes.md` (header `RECONSTRUCTION INCOMPLETE` if <7 sites).
- **Prompt body**: `Task P4: git show main:demo_output/2hdm-a/fix_loop/POST_MORTEM.md and FINAL_STATUS.md. Mine renderer-site references. grep -rn "render|Dirac singlet|conj|EWSB.*Phases|ImaginaryI|Mchi" plugins/model-building/skills/sarah-build/scripts/sections/. Enumerate as many distinct sites as evidence supports with file:line refs. If <7, prefix file with "RECONSTRUCTION INCOMPLETE". Commit.`
- **Success**: `test -f demo_output/2hdm-a/fix_loop/iter_6_notes.md`
- **On-failure**: G4 starts as warning regardless.

### P5 — Strip --skip-render (15 min, parallel)
- **Deliverable**: SKILL.md uses direct wolframscript with flock wrapper.
- **Prompt body**: `Task P5: Remove every --skip-render and skip_render under plugins/hep-ph-demo/skills/2hdm-a/. Replace with: flock -x -w 120 /Users/yianni/Projects/hep-ph-agents/.shift-manager/locks/sarah.lock wolframscript -code '<<SARAH\`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'. Reference $SARAH_PATH from config.json. Commit.`
- **Success**: `! grep -rn "skip-render\|skip_render" plugins/hep-ph-demo/skills/2hdm-a/`
- **On-failure**: re-dispatch with grep output.

### P6 — maddm_run import + multi-importer audit (12 min, parallel)
- **Deliverable**: SKILL.md import wrapped with `sys.path.insert`; commit msg lists all importers found.
- **Prompt body**: `Task P6: FIRST run grep -rn "from scripts.maddm_run\|import maddm_run" plugins/ and report ALL importers in commit message. If multiple skills outside 2hdm-a import via different paths, prefer package-shim (option b). Else edit only 2hdm-a SKILL.md to wrap import with sys.path.insert(0, "plugins/monte-carlo-tools/skills/maddm/scripts") + inline comment. Commit.`
- **Success**: `cd $WORKTREE && python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"`
- **On-failure**: G6 may downgrade to warning iff inline workaround documented.

### P7 — Environment snapshot, dual SHA (15 min, parallel)
- **Deliverable**: `demo_output/2hdm-a/playtest_log/env.json` (keys: `config`, `git_sha_pre_run`, `git_sha_at_capture`, `sarah_version`, `mg5_version`, `maddm_version`, `python_version`, `wolfram_version`); `plugins/hep-ph-demo/skills/2hdm-a/scripts/capture_env.py`.
- **Prompt body**: `Task P7: Two SHAs: git_sha_pre_run = a05f274 (or read .shift-manager/run-20260424-202956/scoping/main_sha.txt if present); git_sha_at_capture = git rev-parse HEAD now. Write capture_env.py emitting env.json with all 8 keys. Run it. Commit.`
- **Success**: `python3 -c "import json; d=json.load(open('demo_output/2hdm-a/playtest_log/env.json')); assert all(k in d for k in ['config','git_sha_pre_run','git_sha_at_capture','sarah_version','mg5_version','maddm_version','python_version','wolfram_version'])"`

### R1 — Schema sign-off (8 min, opus on P3 output)
- **Deliverable**: `.shift-manager/run-20260424-202956/plan/r1_schema_signoff.md` with line `OWNER: 2hdm-a; ACK: SD-clean, dark-su3-clean`.

### R2 — Wchi citation probe (18 min, parallel with P2)
- **Deliverable**: `.shift-manager/run-20260424-202956/plan/r2_wchi_decision.md` with verbatim MadDM quote.
- **Prompt body**: `Task R2: Inspect plugins/monte-carlo-tools/skills/maddm/ and the MG5 plugin install for define darkmatter auto-detect. Find file:line where DECAY widths gate DM detection. Write r2_wchi_decision.md with verbatim quote. Synthesis-locked Wchi=0.0; this probe documents citation only.`
- **No P2 follow-up needed** (P2 already sets Wchi=0.0). If R2 finds contradiction, surfaces post-run as minor issue.

### R3 — Gate-downgrade policy (5 min, opus direct)
- **Deliverable**: `.shift-manager/run-20260424-202956/plan/r3_gate_downgrade.md` — pre-locked: G4 downgrade unconditional; G6 downgrade iff sys.path workaround documented; G2/G3 non-downgradable; G1/G5/G7/G8/G9/G10 non-negotiable.

### Phase 0 wall budget
Parallel: max(P2=25, P3=20, P4=20, P5=15, P6=12, P7=15) + opus review overhead 10 + P1 serial 3 = **38 min**. Hard ceiling 45 min before manager invokes R3 downgrades.

---

## Phase 1: Playtest (PT1)

### Pre-dispatch (manager)
1. Verify `gate_status.json` overall = pass (or pass-with-warning per R3).
2. Fast-forward `main` to `2hdma/prep-20260424`.
3. Create worktree at `/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-playtest/` from `2hdma/prep-20260424` HEAD on branch `2hdma/playtest-20260424`.
4. Update `2hdma-budget.json` with `playtest_start`.
5. Increment `playtest_attempts`.

### Sonnet prompt (paste-ready)
```
You are the 2HDM+a playtest practitioner.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-playtest/
Allowed diff prefixes: plugins/hep-ph-demo/skills/2hdm-a/**, demo_output/2hdm-a/**.
Forbidden everywhere else. If you need an out-of-scope edit, STOP, append a blocker to demo_output/2hdm-a/playtest_log/issues.jsonl, exit.

LOCKED RULES:
- Use the FIXTURE path. Do NOT invoke /lagrangian-builder or /sarah-build interactively for 2hdm-a.
- Hard cap: 15 min/pass; one retry on transient failure (Wolfram timeout, MG5 plugin reload). Wall total = 30 min.
- On 20-min single MG5 launch overrun: `kill -ABRT <pid>` + `sample <pid> > demo_output/2hdm-a/playtest_log/launch_hang.sample`, log blocker, abort.
- On global wall ≥25 min in retry: write demo_output/2hdm-a/playtest_log/verdict.md with VERDICT: FAIL + cause: wall_timeout, write blocker issue with phase=<last_completed>, exit. ALWAYS write verdict.md and issues.jsonl on exit, even on timeout.

PHASE ORDER (mandatory):
0. Preflight: run `python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"` — must exit 0.
1. Clean+deploy: `rm -rf $SARAH_ROOT/Models/TwoHdmAfix/`. Then copy plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/*.m → $SARAH_ROOT/Models/TwoHdmAfix/.
2. SARAH MakeUFO via:
   `flock -x -w 120 /Users/yianni/Projects/hep-ph-agents/.shift-manager/locks/sarah.lock wolframscript -code '<<SARAH`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'`
3. Vertex sanity: grep generated UFO for chichibar_bbx coupling presence.
4. MG5 output: drive MG5 to produce maddm_run/. Capture mtime: `stat -f %m maddm_run/Cards/param_card.dat > demo_output/2hdm-a/playtest_log/output_mtime.txt`. Also touch `demo_output/2hdm-a/playtest_log/.output_marker` immediately after MG5 output completes (this is the dual-sentinel reference).
5. Run plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py against maddm_run/Cards/param_card.dat. After it returns, write `demo_output/2hdm-a/playtest_log/.patched`.
6. MG5 launch (MadDM relic). Stream stdout to demo_output/2hdm-a/playtest_log/run.log.
7. Parse MadDM_results.txt → demo_output/2hdm-a/relic.json with Ωh², dominant channel, channel fractions.
8. Plot summary.{pdf,png}.
9. Emit demo_output/2hdm-a/summary.json. Validate against plugins/hep-ph-demo/skills/_shared/summary.schema.json. If schema fails: log severity=warning, proceed.
10. Verdict: write demo_output/2hdm-a/playtest_log/verdict.md. First three lines EXACTLY:
    VERDICT: PASS|FAIL
    MODEL_SOURCE: hand_crafted_sarah_model_fixture
    RENDERER_STATUS: debt
    Then 5-line summary.

DUAL PATCH SENTINEL (verify before declaring PASS):
(a) `grep '^   1 .*1.000000e+00' demo_output/2hdm-a/maddm_run/Cards/param_card.dat` returns ≥1 line.
(b) `[ "$(stat -f %m demo_output/2hdm-a/maddm_run/Cards/param_card.dat)" -gt "$(stat -f %m demo_output/2hdm-a/playtest_log/.output_marker)" ]`.
Both must pass.

ISSUE LOG: append every anomaly to demo_output/2hdm-a/playtest_log/issues.jsonl using the synthesis schema (issue_id 2hdma-NNN, severity, phase, fix_owner_hint, etc.). On re-playtest, read existing issues.jsonl and start from max(id)+1.

COMMIT: at exit, `git add demo_output/2hdm-a/ && git commit -m "[2hdma-playtest] PT1: <verdict>"`.
```

### Success check (manager runs)
```bash
test -f demo_output/2hdm-a/playtest_log/verdict.md && \
  head -1 demo_output/2hdm-a/playtest_log/verdict.md | grep -q "^VERDICT: PASS$" && \
  python3 -c "import json; r=json.load(open('demo_output/2hdm-a/relic.json')); assert 9.95 <= r['omega_h2'] <= 10.36" && \
  test -f demo_output/2hdm-a/playtest_log/.patched && \
  test -f demo_output/2hdm-a/playtest_log/.output_marker && \
  [ "$(stat -f %m demo_output/2hdm-a/maddm_run/Cards/param_card.dat)" -gt "$(stat -f %m demo_output/2hdm-a/playtest_log/.output_marker)" ]
```

### Cleanup (manager runs after PT1 exits, regardless of outcome)
```bash
rm -rf $SARAH_ROOT/Models/TwoHdmAfix/  # idempotency for next pass
```

### Timeout / mid-run fallback
- Wall ≥25 min in retry: ALWAYS write verdict.md + issues.jsonl + commit. Manager treats this as `outcome: timeout`, decides whether to enter Phase 2 based on issue list.

---

## Phase 2: Fix-loop (FL1..)

**SERIALIZED. One class, one iteration at a time.** No parallel fix worktrees.

### Trigger
Phase 1 produces ≥1 issue with `severity: blocker` AND `fix_owner_hint ∈ {patcher, schema, fixture, skill_prose, parse, plot}`. Issues with `fix_owner_hint: renderer` are out-of-scope; log as `outcome: deferred_renderer`, do NOT enter fix-loop.

### Per-iteration ordering
1. Manager picks highest-severity unresolved blocker.
2. Manager creates worktree `2hdma-fix-<class>-<n>` from `2hdma/playtest-20260424` HEAD.
3. Dispatch sonnet implementer.
4. Dispatch opus reviewer.
5. If outcome=pass: merge into `2hdma/playtest-20260424` (manager runs `git merge --no-ff` from playtest worktree). On merge conflict, dispatch fix-merger sonnet.
6. Manager updates `2hdma-tries.json`: `fix_loop[<class>] += 1`, `fix_total += 1`.
7. Goto 1 unless stop condition.

### Sonnet implementer prompt (paste-ready)
```
You are a sonnet fix-implementer for the 2HDM+a workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-fix-<class>-<n>/
ISSUE_ID=<issue_id from issues.jsonl>
Allowed diff prefixes: plugins/hep-ph-demo/skills/2hdm-a/**, demo_output/2hdm-a/**, plugins/hep-ph-demo/skills/_shared/summary.schema.json (only if class=schema).
Forbidden everywhere else (especially plugins/model-building/**, plugins/monte-carlo-tools/**, plugins/hep-ph-demo/skills/singlet-doublet/**, plugins/hep-ph-demo/skills/dark-su3/**, config.json, .shift-manager/**).

SYNTHESIS-LOCKED (do not relitigate): Wchi=0.0; Ωh² band ±2%; fixture path only; renderer is debt; channel ≥30% soft; dual sentinel mandatory; ±2% relic band [9.95, 10.36].

Read demo_output/2hdm-a/playtest_log/issues.jsonl, find issue ${ISSUE_ID}. Reproduce via auto_repro_command. Fix in scope. Append to fix_attempts: {ts, diff_path, outcome}. Re-run only the failing phase (not full pipeline). Commit `[2hdma-fix-<class>-<n>] <issue_id>: <one-line>`.
```

### Opus reviewer prompt (paste-ready)
```
You are an opus reviewer for a 2HDM+a fix attempt.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-fix-<class>-<n>/
ISSUE_ID=<issue_id>

SYNTHESIS-LOCKED DECISIONS (you MAY NOT relitigate; reject any sonnet diff that contradicts these):
- Wchi := 0.0 (citation: r2_wchi_decision.md)
- Ωh² target band: [9.95, 10.36] (±2% around 10.155)
- Fixture path only; renderer is debt; do NOT propose renderer fixes
- Dominant channel ≥30% is SOFT (do not require hard cutoff)
- Dual patch sentinel: grep + mtime, both required
- Schema additions limited to relic_approx, model_source, model_fixture

SCOPE GUARD — forbidden prefixes (any diff touching these = aborted_scope):
- plugins/model-building/skills/sarah-build/**
- plugins/model-building/skills/spheno-build/**
- plugins/monte-carlo-tools/**
- plugins/hep-ph-demo/skills/singlet-doublet/**
- plugins/hep-ph-demo/skills/dark-su3/**
- config.json
- .shift-manager/**

CHECKS:
1. Run `git diff --name-only HEAD~1 HEAD` from WORKTREE_PATH. Every line must match an allowed prefix; any forbidden prefix → outcome=aborted_scope, halt.
2. Run the issue's auto_repro_command. If now passes → outcome=pass.
3. If repro still fails but progress observable → outcome=fail.
4. Confirm no synthesis-locked decision was contradicted.

Write verdict to .shift-manager/run-20260424-202956/state/fix_review_<class>_<n>.md with first line `OUTCOME: pass|fail|aborted_scope`.
```

### Stopping rules (manager checks after every iteration)
- All blockers `outcome: pass` → exit fix-loop, dispatch re-playtest.
- `fix_total >= 5` → halt fix-loop.
- Any single class hits 3 sonnet+opus iterations without pass → escalate that class to opus-opus pair (1 round). If opus-opus also fails → mark class `unfixable_in_budget`, halt.
- Any iteration produces `outcome: aborted_scope` → halt fix-loop, treat as architectural escape.
- Wall-clock for fix phase ≥45 min → halt.
- Cumulative wall ≥150 min → halt; skip re-playtest.

### Iteration accounting
After each opus review, manager appends to `2hdma-tries.json`:
```json
{"fix_loop": {"<class>": <new count>, ...}, "fix_total": <new total>}
```

---

## Gate evaluator (inline)

After Phase 0 commits land on `2hdma/prep-20260424`, manager dispatches a single sonnet "gate-evaluator" with this exact prompt:

```
You are the gate-evaluator for the 2HDM+a prep phase.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-prep/
Run each gate G1–G10 below from WORKTREE_PATH. Write demo_output/2hdm-a/playtest_log/gate_status.json with structure:
  {"gates": {"G1": {"status": "pass|fail|warning", "evidence": "<path or output>"}}, ..., "overall": "pass|warning|fail"}

GATES:

G1. demo_output/2hdm-a/ does not contain stale artifacts (P1 done).
    CHECK: `test -f demo_output/2hdm-a/.cleaned && test ! -f demo_output/2hdm-a/fix_loop/POST_MORTEM.md`
    NON-NEGOTIABLE.

G2. patch_paramcard.AUDIT.md exists with Wchi decision (P2 done).
    CHECK: `test -f plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md && grep -q "Wchi" plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md && grep -qE "Wchi.*=.*0\.0" plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py`
    NON-DOWNGRADABLE.

G3. _shared/summary.schema.json validates SKILL.md L470-478 example.
    CHECK: `python3 plugins/hep-ph-demo/skills/_shared/test_summary_schema.py`
    NON-DOWNGRADABLE.

G4. iter_6_notes.md exists.
    CHECK: `test -f demo_output/2hdm-a/fix_loop/iter_6_notes.md`
    DOWNGRADABLE TO WARNING UNCONDITIONALLY (per R3). Start status as warning if file begins with `RECONSTRUCTION INCOMPLETE`.

G5. No --skip-render references.
    CHECK: `! grep -rn "skip-render\|skip_render" plugins/hep-ph-demo/skills/2hdm-a/`
    NON-NEGOTIABLE.

G6. maddm_run import works.
    CHECK: `python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"`
    DOWNGRADABLE TO WARNING iff plugins/hep-ph-demo/skills/2hdm-a/SKILL.md contains an inline sys.path.insert workaround.

G7. env.json has all required keys including dual SHA.
    CHECK: `python3 -c "import json; d=json.load(open('demo_output/2hdm-a/playtest_log/env.json')); assert all(k in d for k in ['config','git_sha_pre_run','git_sha_at_capture','sarah_version','mg5_version','maddm_version','python_version','wolfram_version'])"`
    NON-NEGOTIABLE.

G8. Wolfram Engine responds.
    CHECK: `wolframscript -code 'Print["ok"]'`
    NON-NEGOTIABLE.

G9. $SARAH_ROOT/Models/TwoHdmAfix/ either absent or clean-diff vs fixture.
    CHECK: `[ ! -d "$SARAH_ROOT/Models/TwoHdmAfix/" ] || diff -rq "$SARAH_ROOT/Models/TwoHdmAfix/" plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/`
    NON-NEGOTIABLE.

G10. git status --porcelain shows only allowed scope-guard prefixes.
    CHECK: `cd $WORKTREE_PATH && git status --porcelain | awk '{print $2}' | grep -v '^plugins/hep-ph-demo/skills/2hdm-a/' | grep -v '^plugins/hep-ph-demo/skills/_shared/summary.schema.json' | grep -v '^demo_output/2hdm-a/' | grep -v '^.shift-manager/' | grep -v '^.gitignore$'` should produce zero output.
    NON-NEGOTIABLE.

OVERALL:
- If any non-negotiable gate (G1, G5, G7, G8, G9, G10) fails → overall=fail.
- If non-downgradable (G2, G3) fail → overall=fail.
- If only G4 or G6 are warning/fail (within R3 policy) → overall=warning.
- Else → overall=pass.

Exit by writing gate_status.json. No other output.
```

Manager reads `gate_status.json`. If `overall in {pass, warning}` → proceed to PT1. Else → halt and write `verdict.md` with `VERDICT: FAIL`, `cause: gate_failure: <gate_id>`.

---

## Planner-to-resolve answers (final, locked)

**R1 (schema sign-off)**: 2hdm-a owns `_shared/summary.schema.json` for this run. Sign-off is obtained via P3 test script validating SD + dark-su3 stub payloads. Lock file `.shift-manager/locks/summary_schema.lock` enforces single-writer. SD/dark-su3 plans inherit the same lock protocol; they wait or coordinate.

**R2 (Wchi)**: `Wchi := 0.0` LOCKED. R2 probe documents the citation only; does not gate P2. If R2 finds a contradicting MadDM check, it surfaces as a `severity: minor` issue post-run, not a blocker.

**R3 (gate downgrades)**: G4 → warning unconditional. G6 → warning iff sys.path workaround documented inline. G2 → non-downgradable. G3 → non-downgradable. G1, G5, G7, G8, G9, G10 → non-negotiable.

---

## Failure recovery

| Trigger | Behavior |
|---------|----------|
| Phase 0 wall >45 min | Manager applies R3 downgrades; if G2/G3 still fail, halt with `cause: prep_unrecoverable`. |
| PT1 sonnet times out | PT1 prompt mandates always-write verdict.md + issues.jsonl. Manager treats `cause: wall_timeout` as fix-loop trigger. |
| Fix-loop stuck (3 sonnet+opus rounds same class) | Escalate to opus-opus (1 round). If still fails, mark class `unfixable_in_budget`, halt fix-loop, dispatch re-playtest with current state. |
| Opus disagrees with synthesis-locked decision | Opus prompt forbids relitigation. If opus output rejects on a locked decision, manager re-dispatches with explicit reminder. After 2 such cycles, escalate to opus-opus; if opus-opus also rejects, halt and write `cause: synthesis_lock_disputed`. |
| Worktree creation fails | Dispatch worktree-medic sonnet (`git worktree prune; git status`). |
| Cumulative wall ≥180 min | Hard halt; partial verdict.md. |

---

## Status marker files (manager polls these between dispatches)

| File | Written by | Manager reads when | Manager action |
|------|-----------|---------------------|----------------|
| `.shift-manager/run-20260424-202956/state/2hdma-tries.json` | Manager | Before each dispatch | Decide if budget allows next iter |
| `.shift-manager/run-20260424-202956/state/2hdma-budget.json` | Manager | After each phase transition | Hard-stop check vs 180 min |
| `demo_output/2hdm-a/playtest_log/gate_status.json` | gate-evaluator sonnet | Post-Phase 0 | Decide pass/warning/fail |
| `demo_output/2hdm-a/playtest_log/verdict.md` | PT1 sonnet (or manager on halt) | Post-Phase 1 | Decide if fix-loop needed |
| `demo_output/2hdm-a/playtest_log/issues.jsonl` | PT1 sonnet | Per fix-loop iteration | Pick next blocker |
| `.shift-manager/run-20260424-202956/state/fix_review_<class>_<n>.md` | Opus reviewer | After each fix iteration | Decide merge vs retry vs halt |
| `.shift-manager/locks/summary_schema.lock` | Manager (P3 start) | SD/dark-su3 dispatch | Block if lock held |
| `.shift-manager/locks/sarah.lock` | flock auto | Per SARAH invocation | OS-managed, no manager poll |

All polls are file-existence + `head -1` or single `jq` read. No judgment required.

---

End of plan.
