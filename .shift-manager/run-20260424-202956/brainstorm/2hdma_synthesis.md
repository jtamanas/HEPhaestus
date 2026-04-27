# 2HDM+a Playtest — Brainstorm Synthesis (LOCKED)

Author: brainstorm-synthesizer
Inputs: `2hdma_propose.md`, `2hdma_critique.md`, `scoping/scope.md`
Posture: decisive. The planner consumes this verbatim.

---

## Decisions on the proposer's 10 questions

### Q1 — Test design (renderer vs fixture)
**KEEP.** Validate the hand-crafted fixture path only; do not chase the renderer this run.
- Proposer: SKILL.md L12-19 already designates fixture as the supported path; renderer is loop-B debt.
- Skeptic concedes this is the correct scope, conditional on the run honestly reporting "uses hand-crafted SARAH model fixture (renderer is debt)" in `verdict.md`.
- Position on disagreement: **adopt skeptic's labeling requirement**. `verdict.md` MUST include the line `MODEL_SOURCE: hand_crafted_sarah_model_fixture` and `RENDERER_STATUS: debt`. Do NOT attempt `/sarah-build` opportunistically; the renderer is out of scope.

### Q2 — Practitioner persona / Q2 ambiguity
**REVISE.** Do not modify `practitioner_script.md`; do not augment Q2 with the `a→a0s` parenthetical.
- Skeptic verified the script is *decorative* in this run because Step 4a bypasses `/lagrangian-builder` for 2hdm-a entirely. The "a vs A collision" is a renderer concern, irrelevant when the fixture is copied wholesale.
- Position: the playtest agent invokes `/lagrangian-builder` only enough to satisfy `/demo`'s gate logic (if at all). If the practitioner-script auto-answer fails, log it as a `minor` issue and proceed — the fixture deploy is what matters.

### Q3 — Invocation sequence
**REVISE.** Drop `--skip-render` entirely. Drive Wolfram directly for SARAH; preserve everything else.
- Skeptic verified `--skip-render` does not exist in any skill (zero hits across `plugins/model-building/`).
- The Phase 2 invocation must be the direct fallback: `wolframscript -code '<<SARAH\`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'` (or `math -run` equivalent).
- Preflight must additionally `python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"` to surface the SKILL.md L279 import landmine before anything expensive runs.
- **Hard-fail rule from proposer kept**: Phase 1 or Phase 2 failure → STOP, log BLOCKER, exit. No silent fallback.

### Q4 — Success criteria
**REVISE.** Tighten Ωh² band; weaken channel threshold; harden patch sentinel.
- Ωh²: **±2%** (9.95–10.36), per skeptic. The ±10% proposer band would mask real regressions; Romberg drift is sub-percent.
- Dominant channel `chichibar_bbx`: **≥30% (soft check, log fraction)**. SKILL.md's "60%" claim is unbacked; the 40% floor was guesswork. <30% surfaces as a `minor` finding, not a blocker.
- Patch sentinel: **dual check** — (a) grep `PHASES[1] = 1.000000e+00`, AND (b) `mtime(param_card.dat) > mtime(maddm_run/Cards/.output_marker)`. Write a `.patched` marker after the patcher runs.
- All other rows from proposer's table KEEP.
- **Add row**: `summary.json` validates against `_shared/summary.schema.json` AFTER schema is reconciled (see prep step P3). If schema mismatch unresolved at run time, treat schema check as `warning` not `blocker`.

### Q5 — Failure taxonomy
**KEEP**, with two additions from skeptic:
- Add **#10 Schema-validation failure** (~5%): `summary.json` rejected by `_shared/summary.schema.json` due to `relic_approx`/`model_source`/`model_fixture` extras under `additionalProperties: false`.
- Add **#11 MadDM rejects DM candidate due to `Wchi=1 GeV`** (~5%): the patcher's blanket "set BSM widths ≥1 GeV" may flip MadDM's auto-detect off `chi`. If `define darkmatter chi` succeeds but downstream Ωh² is wrong by orders of magnitude, suspect this.
- Failure-mode #2 (PHASES not set) remains the prior-#1 silent killer per POST_MORTEM. Keep it ranked first among non-deployment failures.

### Q6 — Issue-log JSON schema
**REVISE — adopt skeptic's expanded shape, carved into a cross-workstream contract.** See **Final Schema** section below. This schema is shared across 2hdm-a, singlet-doublet, and dark-su3.

### Q7 — Fix-loop authorization
**REJECT proposer; ADOPT skeptic's narrow exception.** Fix-loop IS authorized, scoped tightly.
- User explicitly said "spin up agents to resolve any issues that arise" + "keep grinding." Proposer's "strictly observe" contradicts this.
- **Scope**: diffs allowed ONLY under `plugins/hep-ph-demo/skills/2hdm-a/**` and `demo_output/2hdm-a/**`. See **Fix-loop scope guard** below.
- **Budget**: max 3 fix iterations per failure class, hard cap of 5 total fix attempts across the run.
- **Kill switch**: any diff outside the allowed prefix → abort the fix attempt, append `parent_issue_id` chain entry, escalate to `blocker`.

### Q8 — Parallelism
**REVISE.** Treat SARAH-kernel contention as caution, not gospel; serialize anyway as cheap insurance.
- Skeptic correctly notes the serialization recommendation is unproven. Wolfram Engine free is per-machine multi-process OK; paid Mathematica home-use is per-seat.
- **Decision**: serialize the SARAH `MakeUFO[]` step between SD and 2hdm-a (~2 min cost). Run dark-su3 (no SARAH) fully parallel. Cheap, defensible, removes a class of flake.
- `config.json` is **read-only** for all workstreams (planner-to-resolve if any workstream needs to write). MG5 install dir and SARAH install dir are read-shared; per-run output dirs (`demo_output/<model>/`) are write-isolated.

### Q9 — Artifact contract
**KEEP** the directory tree from proposer, with these additions:
- Add `playtest_log/.patched` marker file (post-patcher).
- Add `playtest_log/git_sha.txt` (one-line, captured at run start).
- `verdict.md` first line: `VERDICT: PASS` or `VERDICT: FAIL`. Second line: `MODEL_SOURCE: hand_crafted_sarah_model_fixture`. Third line: `RENDERER_STATUS: debt`. Then a 5-line summary.
- All paths absolute or repo-relative as listed in proposer §9.

### Q10 — Time budget
**KEEP.** 15 min hard cap per pass, 30 min with one retry. 20 min on a single MadDM `launch` → suspect on-resonance hang, abort with `kill -ABRT` + `sample <pid>` for evidence.

---

## Final issue-log JSON schema (cross-workstream contract)

Used by 2hdm-a, singlet-doublet, dark-su3. JSONL at `demo_output/<model>/playtest_log/issues.jsonl`, append-only.

```json
{
  "issue_id":              "<model>-NNN",
  "parent_issue_id":       null,
  "workstream":            "2hdm-a | singlet-doublet | dark-su3",
  "severity":              "blocker | major | minor | nit",
  "phase":                 "preflight | fixture_deploy | sarah_build | mg5_setup | param_patch | mg5_launch | parse | plot | summary | schema_validate",
  "symptom":               "one-line human description",
  "expected":              "what should have happened",
  "observed":              "verbatim error or quoted artifact line",
  "evidence_paths":        ["abs/path/1", "abs/path/2"],
  "evidence_hashes":       {"abs/path/1": "sha256:..."},
  "hypothesis":            "best-guess root cause",
  "blocking":              true,
  "auto_repro_command":    "shell snippet reproducing in <60s, or null",
  "fix_owner_hint":        "renderer | spec | skill_prose | tool_install | fixture | patcher | schema | unknown",
  "fix_attempts":          [{"ts": "ISO-8601", "diff_path": "abs/path", "outcome": "pass|fail|aborted_scope"}],
  "captured_at":           "ISO-8601",
  "playtest_iteration":    0,
  "git_sha":               "a05f274",
  "tool_versions":         {"sarah": "4.15.3", "mg5": "x.y.z", "maddm": "x.y", "python": "3.x", "wolfram": "x.y"},
  "config_snapshot_path":  "demo_output/<model>/playtest_log/env.json"
}
```

Fix agents append to `fix_attempts` without rewriting prior entries. `parent_issue_id` chains derived issues (e.g., schema-validate failure caused by patcher mtime miss).

---

## Pre-playtest preparation steps (fix agent must complete before playtest spawns)

P1. **Clean stale demo output.** `rm -rf demo_output/2hdm-a/`. The 22 Apr `summary.json` with stale `BLOCKED` headline must not be on disk when the playtest agent starts. (Skeptic §6.1.)

P2. **Re-audit `patch_paramcard.py` against POST_MORTEM.** The 445-line reconstruction adds HMIX/ZAMIX/ZHMIX/ZPMIX writes not in the original 60-line iter-8 script. Fix agent must:
  - Diff the reconstruction's mutations against `POST_MORTEM.md` line 36's described scope.
  - For each extra block (HMIX VEVs, ZAMIX with theta_a=0.1, ZHMIX, ZPMIX, alpha=-0.1): either justify with a comment citing physics rationale, or delete it.
  - Specifically verify: `Wchi=1 GeV` for stable DM. Either set `Wchi=0` (or omit), OR add a comment explaining MadDM tolerates 1 GeV widths on Z2-odd particles. Test by inspecting MadDM's `define darkmatter` auto-detect logic.
  - Output: `plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md` documenting decisions.

P3. **Resolve `summary.schema.json` mismatch.** SKILL.md L470-478 emits `relic_approx`, `model_source`, `model_fixture`; schema has `additionalProperties: false`. Fix agent must:
  - Edit `plugins/hep-ph-demo/skills/_shared/summary.schema.json` to add these three optional fields (relax `additionalProperties` to `true`, OR add explicit field defs). Prefer explicit field defs.
  - Verify schema validates SKILL.md's example.
  - Coordinate with SD/dark-su3 workstreams: those workstreams emit `summary.json` too — additions must not break their existing payloads.

P4. **Reconstruct `iter_6_notes.md` from POST_MORTEM.** The "seven renderer sites" referenced at POST_MORTEM L79/103/117 and FINAL_STATUS L67/73/80 is vapor. Fix agent must:
  - Extract the renderer-site list from POST_MORTEM and FINAL_STATUS prose.
  - Write `demo_output/2hdm-a/fix_loop/iter_6_notes.md` with the enumerated seven sites, each with file:line refs into `plugins/model-building/skills/sarah-build/scripts/sections/`.
  - This unblocks any future renderer-backport workstream. Does NOT unblock this run (still fixture-only).

P5. **Patch SKILL.md to remove `--skip-render` references.** SKILL.md L245 (and any sibling) must be rewritten to either invoke `/sarah-build` honestly (no flag) or invoke `wolframscript` directly. Fix agent: pick the direct-Wolfram path; document why in commit message.

P6. **Verify `from scripts.maddm_run import` import landmine.** SKILL.md L279 imports across skills without `sys.path` munging. Fix agent must either: (a) add an explicit `sys.path.insert` in the SKILL.md instructions, or (b) make `maddm_run.py` importable as a proper package, or (c) document the workaround inline at L279.

P7. **Capture environment snapshot.** Write `demo_output/2hdm-a/playtest_log/env.json` with: config.json contents, `git rev-parse HEAD`, tool versions (SARAH, MG5, MadDM, Python, Wolfram). Required by issue schema's `config_snapshot_path`.

All P1–P7 are in-scope under the fix-loop guard (all touch only `plugins/hep-ph-demo/skills/2hdm-a/**`, `plugins/hep-ph-demo/skills/_shared/**` (P3 only), or `demo_output/2hdm-a/**`).

**Planner-to-resolve**: P3 touches `_shared/`, which is technically outside the strict 2hdm-a subtree. Planner must decide whether `_shared/` edits require coordination with SD/dark-su3 fix agents or whether 2hdm-a fix agent owns the schema. Recommended: 2hdm-a owns it but circulates the diff for one-line ack from SD/dark-su3 leads.

---

## Fix-loop scope guard

**Allowed diff prefixes** (the union of):
- `plugins/hep-ph-demo/skills/2hdm-a/**`
- `demo_output/2hdm-a/**`
- `plugins/hep-ph-demo/skills/_shared/summary.schema.json` (P3 only; one file, not the whole `_shared/` tree)

**Forbidden everywhere else**, especially:
- `plugins/model-building/skills/sarah-build/**` (renderer — out of scope)
- `plugins/model-building/skills/spheno-build/**`
- `plugins/monte-carlo-tools/**`
- `plugins/hep-ph-demo/skills/singlet-doublet/**`
- `plugins/hep-ph-demo/skills/dark-su3/**`
- `config.json` (read-only)
- `.shift-manager/**` (run state)

**Kill-switch condition** (any one trips abort):
1. `git diff --name-only` after a fix touches a forbidden prefix → revert the fix, log `severity: blocker`, `fix_owner_hint: <inferred>`, `outcome: aborted_scope`, escalate.
2. Total `fix_attempts.length` across all issues for this workstream > 5 → halt fix loop, log remaining issues, run playtest with current state.
3. Per-failure-class iterations > 3 → mark that class `blocker`, move on.
4. Wall-clock budget for fix phase exceeds 45 minutes → halt fix loop, hand off to playtest with whatever's done.
5. Any attempt to invoke `/sarah-build` interactively or modify the renderer → immediate abort, log `severity: blocker`.

---

## Go / no-go gate (must be true before playtest agent executes)

All must be `true`:

- [ ] G1. `demo_output/2hdm-a/` does not exist (P1 done).
- [ ] G2. `plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.AUDIT.md` exists and either justifies or removes the extra HMIX/ZAMIX/ZHMIX/ZPMIX blocks; `Wchi` decision documented (P2 done).
- [ ] G3. `_shared/summary.schema.json` validates SKILL.md L470-478's example payload (P3 done). Run `python3 -c "import jsonschema, json; jsonschema.validate(json.loads(EXAMPLE), json.load(open('plugins/hep-ph-demo/skills/_shared/summary.schema.json')))"` and confirm it passes.
- [ ] G4. `demo_output/2hdm-a/fix_loop/iter_6_notes.md` exists with seven enumerated renderer sites (P4 done). Not a runtime requirement, but a documentation requirement to close the vapor reference.
- [ ] G5. `grep -rn "skip-render\|skip_render" plugins/hep-ph-demo/skills/2hdm-a/` returns zero hits (P5 done).
- [ ] G6. SKILL.md L279 import works: `cd <repo>; python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"` exits 0 (P6 done).
- [ ] G7. `demo_output/2hdm-a/playtest_log/env.json` exists with git_sha + tool versions (P7 done).
- [ ] G8. Wolfram Engine responds: `wolframscript -code 'Print["ok"]'` exits 0.
- [ ] G9. `$SARAH_ROOT/Models/TwoHdmAfix/` either does not exist OR diffs clean against `plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/` (idempotency check passes).
- [ ] G10. `git status --porcelain` shows only files under the allowed scope-guard prefixes.

If any gate fails: do not spawn the playtest agent. Log the failed gate in `demo_output/2hdm-a/playtest_log/gate_status.json` and escalate to the synthesizer/shift-manager. Per user directive "keep grinding": if G2/G3/G4/G6 fail and the underlying issue is non-trivial, the synthesizer MAY downgrade those gates to `warning` and proceed — but G1, G5, G7, G8, G9, G10 are non-negotiable.

---

## What the planner inherits

- **Scope**: fixture path only, renderer is debt, honestly labeled.
- **Fix-loop**: authorized but tightly scoped; 7 prep steps before run; 5-attempt cap during run.
- **Schema**: cross-workstream issue JSON above; `_shared/summary.schema.json` to be relaxed in P3.
- **Success bar**: Ωh² ∈ [9.95, 10.36], finite, with patcher mtime+grep dual sentinel.
- **Time**: 45 min fix-prep + 30 min playtest (with retry) = 75 min wall budget for 2hdm-a alone.
- **Parallelism**: serialize SARAH steps with SD; dark-su3 fully parallel.

Planner-to-resolve items (flagged):
1. Whether P3 `_shared/` edit needs SD/dark-su3 sign-off or 2hdm-a fix agent owns it.
2. Whether `Wchi=0` vs `Wchi=1 GeV` is the correct call (P2) — needs MadDM source inspection.
3. Whether to downgrade G2/G3/G4/G6 to warnings if prep blows budget.
