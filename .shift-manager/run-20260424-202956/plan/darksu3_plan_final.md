# Dark SU(3) Implementation Plan (FINAL)

Source-of-truth: `darksu3_synthesis.md` (LOCKED). All 12 critique hard-blocks addressed inline. Shared primitives copied verbatim from `2hdma_plan_final.md`.

## Scope

**Does**: playtest `/demo` model #3 via SKILL.md walk (no slash-command); ≤3 sonnet+opus + 1 opus-opus docs-only fix-loop; touch only the three named `_shared/` lines + `plugins/hep-ph-demo/skills/dark-su3/**` + `demo_output/dark-su3/**`.

**Does NOT**: edit `_shared/time_budget.py`, `_shared/analytic_models/**`, `_shared/backends/**`, sibling-model trees. Auto-relocate stale strings. Re-litigate synthesis-locked decisions (BP1 ranges, drift bands, banner wording, fix-scope rules).

---

## Cross-workstream protocol

### Lock files (manager creates `.shift-manager/run-20260424-202956/locks/` if absent)

| Lock path | Purpose | Acquire | Release |
|-----------|---------|---------|---------|
| `locks/dsu3_shared_lines.lock` | Ownership of three named `_shared/` lines (SKILL.md:73, constraints.yaml:148, MANUAL_WALKTHROUGH.md:90) | Manager writes content `dark-su3/run-20260424-202956` BEFORE Phase 2 dispatches | Manager `rm` after Phase 2 commit lands |
| `locks/summary_schema.lock` | Schema-edit ownership (held by 2HDM+a) | dark-su3 reads only; never touches schema | n/a |

Sonnet edit boilerplate (paste-ready, CRITIQUE FIX #4 — real flock, not hash-diff):
```bash
LOCKFILE=$HEPPH_STATE_ROOT/locks/dsu3_shared_lines.lock
test -f "$LOCKFILE" && grep -q "dark-su3/run-20260424-202956" "$LOCKFILE" || { echo "LOCK MISSING"; exit 2; }
flock -x -w 60 "$LOCKFILE" -c "<edit command>"
```
flock timeout → log `severity:blocker, fix_owner_hint:cross_workstream_lock_held`, abort.

### Try-counter (CRITIQUE FIX #3): `state/dsu3-tries.json`
Initial: `{"phase0_opus_rounds":{}, "fix_loop":{"docs":0}, "fix_total":0, "playtest_attempts":0, "opus_opus_rounds":0}`. Manager writes at run start + updates BEFORE each dispatch. No agent touches.

### Cumulative-budget (CRITIQUE FIX #5): `state/dsu3-budget.json`
Manager appends `{"phase":"...","wall_min":N}` at every phase transition. **Hard stop**: `wall_min >= 90` → `verdict.md: FAIL, cause: budget_exhausted`, halt (synthesis §10). Soft: ≥30→warn-into-playtest; ≥60→fix-loop cap cut from 3 to 2; ≥80→skip opus-opus.

### Merge-ready (CRITIQUE FIX #9, shared across all 3 workstreams): `state/merge_ready.json`
Schema: `{"singlet-doublet":false, "2hdm-a":false, "dark-su3":false, "updated":"<UTC>"}`. Read: `jq -r .<workstream>`. Write: each workstream flips own bit after opus-opus ACK (or PT1 pass if no fix needed); use `flock -x -w 30 merge_ready.json.lock`. Merge order SD→2HDM+a→dark-su3. dark-su3 merges to `main` ONLY when SD ∧ 2HDM+a both true.

---

## Worktree topology

```
main (a05f274)
 └─ dsu3/prep-20260424     […worktrees/dsu3-prep/]    P0.1..P0.6 commit here
     └─ dsu3/playtest-20260424  […worktrees/dsu3-playtest/]  PT1 commits demo_output/** only
         └─ dsu3/fix-docs-<n>-20260424  [.../dsu3-fix-docs-<n>/]  serialized; one in flight
```

Rules: each P0.x = one commit; manager records prep-tip SHA in `state/dsu3-prep-tip.txt` after gate passes; playtest branches from that exact SHA; fix worktrees serialized; on conflict dispatch sonnet "fix-merger" with same scope guard. Final merge to `main` ONLY when `state/merge_ready.json` shows SD ∧ 2HDM+a both true (synthesis: dark-su3 LAST).

---

## Phase 0: Prep (P0.1 – P0.6)

All Phase 0 sonnet prompts begin with this preamble:
```
PREAMBLE: You are a sonnet implementer for the dark-su3 workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-prep/
HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
Repo root inside this worktree. All paths below are relative unless absolute.
Allowed diff prefixes (any commit you create MUST satisfy `git diff --name-only` ⊆ this set):
  - demo_output/dark-su3/**
  - .shift-manager/run-20260424-202956/workstreams/dark-su3/**
  - .shift-manager/run-20260424-202956/state/dsu3-*.{json,txt}
  - demo_output/.rotated/**  (P0.1 only)
Forbidden everywhere else. If you need an out-of-scope edit, STOP and emit a blocker note to stdout.
Synthesis-locked decisions (do not relitigate): BP1 ranges Ω_V∈[31.6,35.0], Ω_Psi∈[2846,3146]; drift <5% pass / ≥5% major-non-blocking; relic_approx=False; sigmav_approx=True; banner verbatim.
Read-only sub-agent rule (P0.3, P0.4): no `git add`, no `git commit`, no source edits.
Commit each step with message `[dsu3-prep] <P-id>: <one-line>`.
```

### P0.1 — Rotate stale demo_output
- Agent sonnet | Worktree `dsu3-prep` | Serial first | 3 min
- Deliverable: `demo_output/.rotated/dark-su3-preplaytest-<UTC>/` + fresh empty `demo_output/dark-su3/`; same for underscore variant `demo_output/dark_su3/` if present; record both in `.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/rotation.json`.
- Prompt: `<PREAMBLE>\nP0.1: mv demo_output/dark-su3/ → demo_output/.rotated/dark-su3-preplaytest-$(date -u +%Y%m%d%H%M%S)/ if exists; same for dark_su3 (underscore) using same UTC. Recreate empty demo_output/dark-su3/. Write preflight/rotation.json with {rotated_paths, created_at_utc}. Commit.`
- Success: `test -d demo_output/dark-su3 && [ -z "$(ls -A demo_output/dark-su3)" ] && test -f .shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/rotation.json`
- On-failure: dispatch worktree-medic sonnet.

### P0.2 — POST_MORTEM STALE header
- Agent sonnet | Worktree `dsu3-prep` | Serial after P0.1 | 2 min
- Deliverable: rotated POST_MORTEM line 1 prepended exactly: `> STALE — superseded by 3a2da2c (prose rewrite) and b66ab35 (Boltzmann integrator). See run-20260424-202956 synthesis.`
- Prompt: `<PREAMBLE>\nP0.2: Locate demo_output/.rotated/dark-su3-preplaytest-*/fix_loop/POST_MORTEM.md (path from P0.1 rotation.json). sha256 the original. Prepend EXACTLY: "> STALE — superseded by 3a2da2c (prose rewrite) and b66ab35 (Boltzmann integrator). See run-20260424-202956 synthesis." Verify tail-from-line-2 sha256 unchanged. Commit.`
- Success: `head -1 demo_output/.rotated/dark-su3-preplaytest-*/fix_loop/POST_MORTEM.md | grep -q "^> STALE — superseded by 3a2da2c"`
- On-failure: re-dispatch.

### P0.3 — Confirm 3 stale-string hits + locate banner template
- Agent sonnet (READ-ONLY) | Worktree `dsu3-prep` | Parallel with P0.4 | 2 min
- Deliverable: `.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/stale_strings.json` with `hits[]` (must be exactly: SKILL.md:73, constraints.yaml:148, MANUAL_WALKTHROUGH.md:90), `hit_count:3`, `banner_template_line:<int|null>`, `banner_status:"present|missing"`.
- Prompt: `<PREAMBLE>\nP0.3 READ-ONLY (no commits, no edits). Run: grep -rn --exclude-dir=demo_output "Confining dark sector" plugins/hep-ph-demo/skills/. Expect 3 hits at SKILL.md:73, constraints.yaml:148, MANUAL_WALKTHROUGH.md:90. Locate banner template: grep -n "regression-anchors\\|sigmav_approx=True\\|out of reach this run" plugins/hep-ph-demo/skills/demo/SKILL.md (lowest line). Write preflight/stale_strings.json {hits, hit_count, banner_template_line, banner_status}. If hit_count!=3 ALSO write preflight/escalation.md with diff and exit 2.`
- Success: `python3 -c "import json; d=json.load(open('.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/stale_strings.json')); assert d['hit_count']==3"`
- On-failure: F2 (see Failure recovery) — halt + escalation.md.

### P0.4 — Capture pre-run hashes
- Agent sonnet (READ-ONLY) | Worktree `dsu3-prep` | Parallel with P0.3 | 2 min
- Deliverable: `preflight/preflight_hashes.json` with sha256 of `_shared/constraints.yaml`, `_shared/time_budget.py`, `_shared/analytic_models/dark_su3.py`, `_shared/backends/analytic.py`, `demo/SKILL.md` + `git_sha`.
- Prompt: `<PREAMBLE>\nP0.4 READ-ONLY. sha256 these 5 paths: plugins/hep-ph-demo/skills/_shared/{constraints.yaml,time_budget.py,analytic_models/dark_su3.py,backends/analytic.py}, plugins/hep-ph-demo/skills/demo/SKILL.md. git rev-parse HEAD. Write preflight/preflight_hashes.json {git_sha, hashes: {<path>: <sha>}}. Exit 0.`
- Success: `python3 -c "import json; d=json.load(open('.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/preflight_hashes.json')); assert len(d['hashes'])==5"`
- On-failure: re-dispatch.

### P0.5 — Smoke-test compute() with perturbation (CRITIQUE FIX #7)
- Agent sonnet | Worktree `dsu3-prep` | Serial after P0.3+P0.4 | 6 min
- Deliverable: `preflight/smoke_test.json` with two points: BP1 `{g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:150, m_Psi:70}` at n=200 (expect Ω_V∈[31.6,35.0], Ω_Psi∈[2846,3146], relic_approx=False, sigmav_approx=True, wall_seconds≤60); PERTURBATION same but m_V=300 (expect Ω_V ∉ [31.6,35.0] — proves not constant).
- Prompt: `<PREAMBLE>\nP0.5: Import compute from plugins/hep-ph-demo/skills/_shared/analytic_models/dark_su3.py. Call (a) compute({}, {g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:150, m_Psi:70}, n_points=200) — record wall_seconds and outputs. (b) compute({}, {g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:300, m_Psi:70}, n_points=200) — record outputs. Write preflight/smoke_test.json {bp1: {Omega_V_h2, Omega_Psi_h2, relic_approx, sigmav_approx, wall_seconds}, perturbation_mV300: {Omega_V_h2, Omega_Psi_h2}, signature_args: ["spec","params","n_points"]}. Pre-write assertions: bp1.Ω_V∈[31.6,35.0], bp1.Ω_Psi∈[2846,3146], bp1.relic_approx==False, bp1.sigmav_approx==True, bp1.wall_seconds≤60, perturbation.Ω_V ∉ [31.6,35.0]. Any failure → write preflight/escalation.md, exit 2. Commit smoke_test.json only.`
- Success: `python3 -c "import json; d=json.load(open('.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight/smoke_test.json')); assert 31.6<=d['bp1']['Omega_V_h2']<=35.0 and d['bp1']['wall_seconds']<=60 and not (31.6<=d['perturbation_mV300']['Omega_V_h2']<=35.0)"`
- On-failure: F1 — halt before Phase 1; write `state/escalation.md`. NO playtest if smoke fails or wall>60s.

### P0.6 — Lock regression baseline
- Agent sonnet | Worktree `dsu3-prep` | Serial after P0.5 | 12 min
- Deliverable: `regression_baseline.json` with three rows for n∈{200,400,800} × {Omega_V_h2, Omega_Psi_h2, wall_seconds, relic_approx, sigmav_approx}. Manager writes `state/dsu3-prep-tip.txt` AFTER gate passes.
- Prompt: `<PREAMBLE>\nP0.6: For n in [200,400,800], call compute({}, {g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:150, m_Psi:70}, n_points=n). Write regression_baseline.json {rows:[{n_points, Omega_V_h2, Omega_Psi_h2, wall_seconds, relic_approx, sigmav_approx},...]}. Assert n=200 row matches smoke_test.json bp1 within 1e-9. DO NOT enforce drift — Phase 1 evaluates. Commit.`
- Success: `python3 -c "import json; d=json.load(open('.shift-manager/run-20260424-202956/workstreams/dark-su3/regression_baseline.json')); assert [r['n_points'] for r in d['rows']]==[200,400,800]"`
- On-failure: re-dispatch; if wall(n=800)>180s, downgrade G3 to warning (PT1 may skip n=800 re-run).

**Phase 0 wall budget**: P0.1 (3) + P0.2 (2) + max(P0.3,P0.4)=2 + P0.5 (6) + P0.6 (12) + gate (3) = ~28 min. Ceiling 35 min.

---

## Gate evaluator (inline) — CRITIQUE FIX #1

After Phase 0 commits land, manager dispatches sonnet "gate-evaluator":

```
You are the gate-evaluator for the dark-su3 prep phase.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-prep/
HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
Run gates G1–G6 from WORKTREE_PATH. Write $HEPPH_STATE_ROOT/workstreams/dark-su3/preflight/gate_decision.json:
  {"gates": {"G1": {"status": "pass|fail|warning", "evidence": "..."}}, ..., "overall": "pass|warning|fail"}

GATES (5 primary success criteria from synthesis verbatim + perturbation + strings):

G1 PRIMARY-1 pipeline connectivity (NON-NEGOTIABLE): finite positive Ω, relic_approx=False, sigmav_approx=True.
  CHECK: `python3 -c "import json; d=json.load(open('$HEPPH_STATE_ROOT/workstreams/dark-su3/preflight/smoke_test.json')); assert d['bp1']['Omega_V_h2']>0 and d['bp1']['Omega_Psi_h2']>0 and d['bp1']['relic_approx']==False and d['bp1']['sigmav_approx']==True"`

G2 PRIMARY-3 BP1 bands at n=200 (NON-NEGOTIABLE): Ω_V∈[31.6,35.0], Ω_Psi∈[2846,3146].
  CHECK: `python3 -c "import json; d=json.load(open('$HEPPH_STATE_ROOT/workstreams/dark-su3/preflight/smoke_test.json'))['bp1']; assert 31.6<=d['Omega_V_h2']<=35.0 and 2846<=d['Omega_Psi_h2']<=3146"`

G3 PRIMARY-4 convergence baseline locked (NON-NEGOTIABLE): three rows n∈{200,400,800}.
  CHECK: `python3 -c "import json; d=json.load(open('$HEPPH_STATE_ROOT/workstreams/dark-su3/regression_baseline.json')); assert [r['n_points'] for r in d['rows']]==[200,400,800]"`

G4 perturbation non-constant (NON-NEGOTIABLE): m_V=300 moves Ω_V outside BP1 band.
  CHECK: `python3 -c "import json; d=json.load(open('$HEPPH_STATE_ROOT/workstreams/dark-su3/preflight/smoke_test.json'))['perturbation_mV300']; assert not (31.6<=d['Omega_V_h2']<=35.0)"`

G5 PRIMARY-5 iter-5 guard (DEFERRED to PT1; mark pass here): time_budget.py probe in playtest worktree.

G6 strings + banner template (NON-NEGOTIABLE for hit_count, WARNING-DOWNGRADABLE for banner): preflight/stale_strings.json has hit_count==3; banner_template_line non-null.
  CHECK: `python3 -c "import json; d=json.load(open('$HEPPH_STATE_ROOT/workstreams/dark-su3/preflight/stale_strings.json')); assert d['hit_count']==3"; if banner_template_line is None: warning`

(PRIMARY-2 — summary.json schema-valid — is a Phase 1 PT1 check, not a prep gate.)

OVERALL:
- Any non-negotiable fail → overall=fail.
- G6 banner_status==missing → overall=warning (Phase 2 scope-guard widens to include banner-insertion line).
- Else → overall=pass.

Exit by writing gate_decision.json. No other output.
```

Manager: `overall ∈ {pass, warning}` → PT1; else halt + `state/escalation.md` with `cause: gate_failure: <gate_id>`.

---

## Phase 1: Playtest (PT1)

### Pre-dispatch (manager)
1. Verify `gate_decision.json` overall ∈ {pass, warning}.
2. Manager writes `.shift-manager/run-20260424-202956/state/dsu3-prep-tip.txt` with `git -C $WORKTREE_PATH rev-parse HEAD`.
3. Create worktree `/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-playtest/` from `dsu3/prep-20260424` HEAD on branch `dsu3/playtest-20260424`.
4. Update `dsu3-budget.json` with `playtest_start`.
5. Increment `playtest_attempts` in `dsu3-tries.json`.

### Sonnet prompt (paste-ready)
```
You are the dark-su3 playtest practitioner.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-playtest/
HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
Allowed diff prefixes:
  - demo_output/dark-su3/**
  - .shift-manager/run-20260424-202956/workstreams/dark-su3/playtest/**
Forbidden everywhere else (including any source under plugins/). If you need an out-of-scope edit, STOP, append a blocker to demo_output/dark-su3/playtest/issues.json, exit.

LOCKED RULES (synthesis-locked; do not relitigate):
- BP1 numeric bands: Ω_V ∈ [31.6, 35.0], Ω_Psi ∈ [2846, 3146] at n=200.
- Drift <5% pass / ≥5% major-non-blocking (severity=major, fix_scope=physics).
- relic_approx=False, sigmav_approx=True.
- compute() signature: (spec, params, n_points=200).
- Banner finding (absent/paraphrased) ⇒ severity=blocker, fix_scope=docs.
- Ω-too-far-from-paper finding ⇒ severity=major, fix_scope=physics. NEVER conflate with banner.
- Authoritative path: SKILL.md walkthrough. DO NOT invoke /demo as a slash command. The plan does not depend on slash-command resolution.

VERBATIM STRINGS (must appear unchanged in your transcript / findings.md):
A. Picker entry #3 label + description (located at plugins/hep-ph-demo/skills/demo/SKILL.md:73 — quote the entry verbatim).
B. Constraint hook label at plugins/hep-ph-demo/skills/_shared/constraints.yaml:148 (quote verbatim).
C. Walkthrough sentence at plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md:90 (quote verbatim).
D. Banner template (banner_template_line from stale_strings.json) — quote the exact template string the SKILL.md instructs the assistant to emit. The expected production banner is:
   "NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets."

PARAPHRASEABLE STRINGS (do not enforce verbatim): step 1 intro prose, headers, decoration; step 2 interview commentary outside practitioner_script.md auto-answer; generic prose around iter-5 guard; any flavor text outside picker/hook/walkthrough/banner.

WALL CAP: 50 min target, 90 hard. ALWAYS write playtest/verdict.md + playtest/issues.json on exit (even on timeout). 90-min cap → VERDICT: FAIL, cause: wall_timeout.

RUNBOOK (mandatory order):
0. Preflight: preflight_hashes.json exists; dsu3-prep-tip.txt SHA == git rev-parse HEAD~.
1. Read plugins/hep-ph-demo/skills/demo/SKILL.md cover-to-cover. Quote VERBATIM A, B, C, D into demo_output/dark-su3/playtest/findings.md.
2. Picker (~SKILL.md:60–80): pick #3. If string A is stale "Confining dark sector...", file dsu3-001 severity=blocker, fix_scope=docs, auto_fixable=true.
3. Interview: consume practitioner_script.md auto-answers; pick `relic only` + `analytic`.
4. Time-budget probe (PRIMARY-5): `python3 plugins/hep-ph-demo/skills/_shared/time_budget.py --model dark-su3 --constraints relic` → playtest/timing.json. Assert stdout is `READY` and does NOT contain `/dark-matter-constraints`.
5. Analytic relic FRESH (do NOT reuse baseline values): compute(spec, params, n_points∈{200,400,800}) for BP1. Write playtest/diagnostics.json. Compare n=400/800 against n=200 row of $HEPPH_STATE_ROOT/workstreams/dark-su3/regression_baseline.json — drift <5% pass; ≥5% file severity=major, fix_scope=physics, blocking=true.
6. Banner: locate template in SKILL.md; verify rendering would produce string D verbatim. Write playtest/banner_check.json {present, verbatim_match, template_line}. If present=false OR verbatim_match=false → file severity=blocker, fix_scope=docs, auto_fixable=true (BANNER finding, NOT Ω finding).
7. Emit playtest/summary.json. Validate vs _shared/summary.schema.json (PRIMARY-2). Failure → severity=major, fix_scope=schema (defer to 2HDM+a; do NOT edit schema).
8. Hash-diff: re-sha256 the five files from preflight_hashes.json. Any change → severity=blocker, fix_scope=cross_workstream.
9. Verdict: write playtest/verdict.md. First three lines EXACTLY:
     VERDICT: PASS|FAIL
     MODEL_SOURCE: analytic_compute_dark_su3
     RENDERER_STATUS: n/a
   Then 5-line summary referencing issues.json.

ISSUE LOG SCHEMA v1.1 (synthesis-locked, use this exact field set):
{schema_version:"1.1", workstream:"dark-su3", iter:"playtest-1", id:"dsu3-NNN", severity:"blocker|major|minor|info", phase:"preflight|picker|interview|sarah|spheno|madgraph|maddm|summary|plot|docs", symptom, evidence_path, evidence_excerpt, expected, hypothesis, blocking:bool, auto_fixable:bool, fix_scope:"docs|physics|build|test|schema|cross_workstream", fix_owner_hint, related_commit}

Aggregate as JSON array at playtest/issues.json. ids dsu3-001, dsu3-002, ...

ARTIFACTS: diagnostics.json, summary.json, issues.json, findings.md, run.log, banner_check.json, timing.json, verdict.md.

COMMIT: `git add demo_output/dark-su3/ .shift-manager/run-20260424-202956/workstreams/dark-su3/playtest/ && git commit -m "[dsu3-playtest] PT1: <verdict>"`.
```

### Success check (manager runs)
```bash
test -f demo_output/dark-su3/playtest/verdict.md && \
  head -1 demo_output/dark-su3/playtest/verdict.md | grep -q "^VERDICT: PASS$" && \
  python3 -c "import json; d=json.load(open('demo_output/dark-su3/playtest/diagnostics.json')); rows=d['rows'] if 'rows' in d else d; \
    bp1=[r for r in rows if r.get('n_points')==200][0]; \
    assert 31.6<=bp1['Omega_V_h2']<=35.0 and 2846<=bp1['Omega_Psi_h2']<=3146 and bp1['relic_approx']==False and bp1['sigmav_approx']==True" && \
  python3 -c "import json; b=json.load(open('demo_output/dark-su3/playtest/banner_check.json')); assert b['present'] and b['verbatim_match']" && \
  test -f demo_output/dark-su3/playtest/timing.json
```

### Timeout / mid-run fallback + cleanup
Wall ≥90 min → PT1 mandates always-write verdict.md + issues.json (cause: wall_timeout). Manager decides Phase 2 from issues.json. Cleanup (analytic-only, idempotent): `rm -rf /Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-playtest/demo_output/dark-su3/scratch/ 2>/dev/null || true`.

---

## Phase 2: Fix-loop (docs-only)

**SERIALIZED.** Max 1 fix worktree at a time.

### Trigger
Phase 1 produces ≥1 issue with `severity:blocker` AND `fix_scope:docs` AND
`auto_fixable:true` ONLY. Any blocker with `fix_scope ∈ {physics, build, test, schema, cross_workstream}` → halt, write `state/escalation.md`, do NOT enter Phase 2.

### Pre-dispatch (manager)
1. Acquire lock: `echo "dark-su3/run-20260424-202956" > .shift-manager/run-20260424-202956/locks/dsu3_shared_lines.lock`.
2. Re-run P0.3 line-locator: re-grep "Confining dark sector" — must still return same 3 hits at same lines. Mismatch → release lock, write `state/escalation.md`, halt (synthesis §"Reconciliation if SD synth differs": no auto-relocate).
3. Create worktree `dsu3-fix-docs-<n>` from `dsu3/playtest-20260424` HEAD.

### Per-iteration ordering
1. Manager picks the (single) docs blocker (typically: stale-string trio + banner if missing).
2. Dispatch sonnet implementer.
3. Dispatch opus reviewer.
4. If outcome=pass: merge into `dsu3/playtest-20260424` (manager runs `git merge --no-ff`). On conflict, dispatch fix-merger sonnet with same scope guard.
5. Manager updates `dsu3-tries.json`: `fix_loop.docs += 1`, `fix_total += 1`.
6. Goto 1 unless stop condition.

### Sonnet implementer prompt (paste-ready)
```
You are a sonnet fix-implementer for the dark-su3 workstream.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-fix-docs-<n>/
HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
ISSUE_IDS=<comma-list from issues.json filtered to docs+auto_fixable+blocker>

Allowed diff prefixes (NARROW — exceeding scope = aborted_scope):
  - plugins/hep-ph-demo/skills/dark-su3/**
  - plugins/hep-ph-demo/skills/demo/SKILL.md (lines 70–80 ONLY for picker; ALSO the banner_template_line resolved by P0.3 — see preflight/stale_strings.json key banner_template_line — that single line)
  - plugins/hep-ph-demo/skills/_shared/constraints.yaml (line 148 ONLY)
  - plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md (line 90 ONLY)
  - demo_output/dark-su3/fix_loop/POST_MORTEM.md (refresh OK)
  - .shift-manager/run-20260424-202956/workstreams/dark-su3/**

Forbidden everywhere else, ESPECIALLY:
  - plugins/hep-ph-demo/skills/_shared/time_budget.py
  - plugins/hep-ph-demo/skills/_shared/analytic_models/**
  - plugins/hep-ph-demo/skills/_shared/backends/**
  - plugins/hep-ph-demo/skills/_shared/summary.schema.json (held by 2HDM+a)
  - plugins/hep-ph-demo/skills/{singlet-doublet,2hdm-a}/**
  - SD/2HDM+a workstream issue logs

LOCK CHECK (mandatory):
  test -f $HEPPH_STATE_ROOT/locks/dsu3_shared_lines.lock && grep -q "dark-su3/run-20260424-202956" $HEPPH_STATE_ROOT/locks/dsu3_shared_lines.lock || { echo "LOCK MISSING"; exit 2; }

SYNTHESIS-LOCKED (do not relitigate):
- Banner verbatim wording: "NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets."
- BP1 ranges, drift bands, relic_approx, sigmav_approx — see PT1 prompt.
- Stale-string locations are FIXED by P0.3; do not relocate. If grep shows the lines moved, abort with outcome=aborted_scope.
- Three named lines + banner-template line are the ONLY allowed `_shared/` edits.

For each issue in ISSUE_IDS: read issues.json, reproduce via auto_repro_command (the verbatim-quote check), apply minimal diff. After all issues addressed, re-run banner_check.json verification. Append to .shift-manager/run-20260424-202956/workstreams/dark-su3/fix_loop/iter_<n>_attempts.json.

Commit `[dsu3-fix-docs-<n>] <issue_ids>: refresh picker/hook/walkthrough[/banner]`.
```

### Opus reviewer prompt (paste-ready)
```
You are an opus reviewer for a dark-su3 fix attempt.
WORKTREE_PATH=/Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-fix-docs-<n>/
HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
ISSUE_IDS=<comma-list>

SYNTHESIS-LOCKED DECISIONS (you MAY NOT relitigate; reject any sonnet diff that contradicts these):
- BP1 ranges Ω_V ∈ [31.6, 35.0], Ω_Psi ∈ [2846, 3146] at n=200.
- Drift <5% pass / ≥5% major-non-blocking, fix_scope=physics (NEVER docs-fix-loop).
- relic_approx=False, sigmav_approx=True.
- compute() signature (spec, params, n_points=200).
- Banner verbatim: "NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets."
- Stale-string fix is the ONLY docs-fix permitted on these three lines. Do NOT propose physics fixes.
- POST_MORTEM disposition is option (ii) STALE-header (P0.2 done); do NOT demand body refresh unless an issue explicitly cites POST_MORTEM contradiction with HEAD as a blocker.

SCOPE GUARD — forbidden prefixes (any diff touching these = aborted_scope):
- plugins/hep-ph-demo/skills/_shared/time_budget.py
- plugins/hep-ph-demo/skills/_shared/analytic_models/**
- plugins/hep-ph-demo/skills/_shared/backends/**
- plugins/hep-ph-demo/skills/_shared/summary.schema.json
- plugins/hep-ph-demo/skills/singlet-doublet/**
- plugins/hep-ph-demo/skills/2hdm-a/**
- plugins/model-building/**
- plugins/monte-carlo-tools/**
- config.json
- .shift-manager/** (except .shift-manager/run-20260424-202956/workstreams/dark-su3/**)

ALLOWED line-level constraints:
- plugins/hep-ph-demo/skills/demo/SKILL.md: lines 70–80 (picker entry) AND the single banner_template_line recorded in preflight/stale_strings.json. Any edit outside these two regions = aborted_scope.
- plugins/hep-ph-demo/skills/_shared/constraints.yaml: line 148 only.
- plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md: line 90 only.

CHECKS:
1. Run `git diff --name-only HEAD~1 HEAD` from WORKTREE_PATH. Every line must match an allowed prefix; any forbidden prefix → outcome=aborted_scope, halt.
2. For each `_shared/` file in the diff, run `git diff -U0 HEAD~1 HEAD <file>` and confirm hunk line ranges fit the allowed line-level constraints. Out-of-bounds hunks → outcome=aborted_scope.
3. Verify lock file: `test -f $HEPPH_STATE_ROOT/locks/dsu3_shared_lines.lock && grep -q "dark-su3/run-20260424-202956" $HEPPH_STATE_ROOT/locks/dsu3_shared_lines.lock`.
4. For each ISSUE_ID, run the issue's auto_repro_command (verbatim-quote check). If now passes → record pass for that issue; else fail.
5. Confirm no synthesis-locked decision was contradicted (especially: banner wording must match VERBATIM; sonnet must not have proposed a "shorter form" of the banner).

Write verdict to .shift-manager/run-20260424-202956/state/dsu3_fix_review_<n>.md with first line `OUTCOME: pass|fail|aborted_scope` and a brief evidence section (2-5 lines).
```

### Stopping rules (manager checks after every iteration)
All blockers `outcome:pass` → exit + re-playtest. `fix_total >= 3` → opus-opus (1 round); fail → `unfixable_in_budget`, halt. Any `outcome:aborted_scope` → halt + `state/escalation.md`. Fix wall ≥30 min → halt. Cumulative ≥80 min → halt + skip re-playtest.

### Iteration accounting
Manager updates `dsu3-tries.json` after each opus review: `{"fix_loop":{"docs":<n>}, "fix_total":<n>, "opus_opus_rounds":<0|1>}`.

---

## Five planner-to-resolve answers (final, locked)

1. **POST_MORTEM**: option (ii) — prepend STALE header in P0.2; do not refresh body. Phase 2 opus may demand body refresh via explicit issue; default keep STALE.

2. **Per-candidate `relic_*.json`**: dropped from REQUIRED. If analytic module emits anyway, informational only — do NOT delete (forensic). Note in findings.md.

3. **Banner verbatim** (locked):
   > `NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets.`
   Shortening → severity=minor post-run.

4. **`_shared/` lock — flock protocol**: real `flock(1)` on `locks/dsu3_shared_lines.lock` (NOT hash-diff). Manager writes content `dark-su3/run-20260424-202956` BEFORE Phase 2; sonnet wraps edits with `flock -x -w 60 <lockfile> -c "<edit>"`; manager `rm` after Phase 2 commit. SD/2HDM+a sonnets that read these three lines check for the lock; if held, wait or `severity:warning, fix_owner_hint:cross_workstream_lock_held`. Hash-diff is end-of-run audit, not lock.

5. **SD-divergence**: manager re-runs P0.3 line-locator before Phase 2 dispatch (Pre-dispatch step 2). Mismatch → `state/escalation.md`, halt dark-su3, NO auto-relocate, NO auto-probe. Manager surfaces file at next poll tick.

---

## Failure recovery

- **F1** P0.5 smoke fails (signature drift, Ω out of band, perturbation flat, or wall>60s): halt before Phase 1, write `state/escalation.md`, NO playtest, no auto-recovery.
- **F2** P0.3 hits ≠ 3 or wrong lines: halt workstream, write `state/escalation.md`, NO auto-probe, NO auto-relocate (synthesis §"Reconciliation"). Manager surfaces to user.
- **F3** dropped — no longer dual-path. SKILL.md walk is authoritative; PT1 does NOT attempt slash-command invocation.
- **F4** wall_seconds blow-out: F4a (n=200>60s) treat as F1 (halt). F4b (n=800>180s) downgrade G3 to warning; PT1 may skip n=800 re-run.
- **F5** Phase 2 opus rejects synthesis-locked: re-dispatch with reminder once, after 2 cycles escalate to opus-opus; opus-opus reject → halt + `state/escalation.md` cause:`synthesis_lock_disputed`.
- Worktree creation fails: dispatch worktree-medic sonnet (`git worktree prune; git status`).
- Cumulative wall ≥90 min: hard halt, partial verdict.md.

---

## Status marker files (manager polls between dispatches; all polls = file-exists + `head -1` or `jq` read; no judgment)

State (`.shift-manager/run-20260424-202956/state/`):
- `dsu3-tries.json` (manager-written, pre-dispatch read; budget gate)
- `dsu3-budget.json` (post-phase-transition; hard-stop vs 90 min)
- `dsu3-prep-tip.txt` (post-gate; branch playtest from this SHA)
- `merge_ready.json` (shared all 3; final merge gate)
- `escalation.md` (any halting agent; halt workstream + surface to user)
- `dsu3_fix_review_<n>.md` (opus reviewer; merge/retry/halt)

Locks (`.shift-manager/run-20260424-202956/locks/`):
- `dsu3_shared_lines.lock` (manager at Phase 2 start; cross-workstream gate on three named lines)
- `summary_schema.lock` (2HDM+a manager; dark-su3 read-only check)

Workstream artifacts:
- `workstreams/dark-su3/preflight/gate_decision.json` (gate-evaluator; post-Phase 0)
- `demo_output/dark-su3/playtest/verdict.md` (PT1; post-Phase 1)
- `demo_output/dark-su3/playtest/issues.json` (PT1; pick next docs blocker)

End of plan.
