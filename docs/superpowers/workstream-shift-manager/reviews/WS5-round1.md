# WS5 Review — Round 1

**Verdict:** APPROVED

Integration workstream for the Profumo demo redesign. Mechanically green on the
`ws5/integration` worktree; all merges conflict-free; implementer self-report
checks out on every dimension.

## Mechanical done-criteria

| Criterion | Plan location | Observed | Pass |
|---|---|---|---|
| Pytest `91 passed, 0 skipped` on ws5/integration | §3 WS5 done, §5 post-integration | `91 passed in 0.31s` (0 skipped) | YES |
| `test_skill_structure.py` has no `skipif`/`skip_if`/`skip(` guards | §3 WS5 done | `grep -nE 'skipif\|skip_if\|skip\('` → `NO SKIP GUARDS` | YES |
| `MANUAL_WALKTHROUGH.md` at `plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md` | §3 WS5 new-files list (line 593); also §5 smoke `#4`, §WS5 walkthrough prompt (line 640) | Exists at that exact path | YES |
| `README.md` has `## Skills shipped` listing 5 skills + link to walkthrough, constraint-first framing | §3 WS5 done item 607; A5.2 pin line 107 | Section present, all 5 skills listed with one-line descriptions, link on line 15; constraint-first framing in line 4 and throughout | YES |
| `plugin.json` unchanged vs WS2 (skill order preserved) | §5 note 58 + §WS5 done | `git diff 0255333..ws5/integration -- plugin.json` → empty | YES |
| Commit messages contain no `Co-Authored-By` | §3 WS5 anti-pattern | `git log 0255333..ws5/integration --format='%b'` → no such trailer in any WS5 commit | YES |
| `grep -c "Observed:" MANUAL_WALKTHROUGH.md ≥ 5` | §WS5 reviewer check (line 672) | 5 | YES |
| `grep -c "MANUAL_WALKTHROUGH" README.md ≥ 1` | §WS5 reviewer check (line 674) | 1 | YES |

## Location note — `MANUAL_WALKTHROUGH.md`

Implementer flagged potential mis-location (`_shared/tests/` vs `plugins/hep-ph-demo/` root).
Plan is unambiguous: the `Modified/new files` list under §3 WS5 (line 593) reads

```
/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/MANUAL_WALKTHROUGH.md (NEW)
```

and every other mention in the plan (§5 smoke command line 799, §7 R13 line 820,
§8 line 848, WS5 writing prompt line 640) uses the same nested path.
**`_shared/tests/MANUAL_WALKTHROUGH.md` is correct; no move required.**

## MANUAL_WALKTHROUGH content audit

- Step coverage: 5 steps cover `/demo` preflight (Step 1) → Continue gate → model
  picker (Step 2) → per-model handoff (Step 3) → constraint interview with
  BLOCKED annotation (Step 4) → `run_ready` → first prose directive
  (`/sarah-build`) (Step 5). Matches plan §WS5 writing prompt specification
  (i)–(v) line-for-line.
- Three-model coverage: Step 2 lists all three models with hour ranges
  (3–5 / 5–9 / 6–12) and descriptions; `dark-su3` entry explicitly notes fully
  blocked on `/dark-matter-constraints`. Walkthrough deep-dives on
  singlet-doublet as specified; 2hdm-a and dark-su3 are referenced in Step 2
  but not walked end-to-end (plan only requires the singlet-doublet path).
- "Observed:" blocks: concrete. Each lists dated dry-run observations, references
  to option ids (`continue`, `not_now`, `run_ready`, `back`, `cancel`,
  `go`), literal quoted text snippets, and cross-references to
  `constraints.yaml` and per-model SKILL.md tables. Not boilerplate.
- Preamble: specifies exact `claude` invocation at repo root, dummy
  `~/.config/hep-ph-agents/config.json` JSON payload, and clarifies
  "conversation flow, not real SARAH runs." Matches plan requirement (line 640).
- Deviations section: explicit "None observed" plus a mechanical re-check
  (`pytest ... -v`) footer. Matches done-criteria (d).

Verdict: sufficient. No follow-up demands.

## README content audit

- Constraint-first framing: yes — line 4 "interactive constraint-first demo";
  line 11–13 each per-model bullet leads with which constraint is `[READY]` vs
  `[BLOCKED]`. No legacy figure-first language.
- Reference to `_shared/`, `summary.schema.json`, `constraints.yaml`: all three
  present in `## Structure` (lines 21–31).
- Planned prereq inventory: lines 40–42 correctly list `/feynarts`, `/formcalc`,
  `/package-x`, `/ddcalc`, `/gamlike`, `/nulike`, `/dark-matter-constraints` as
  future/planned. Matches plan §1.1 inventory.
- 5-skill list accurate and matches `plugin.json` order (`install`, `demo`,
  `singlet-doublet`, `2hdm-a`, `dark-su3`).
- Link to MANUAL_WALKTHROUGH (line 15): correct relative path
  `skills/_shared/tests/MANUAL_WALKTHROUGH.md`.

Verdict: sufficient. No demands.

## Cross-skill test audit

Four new tests in `TestCrossSkill` (lines 487–541 of `test_skill_structure.py`):

1. `test_all_skill_md_files_exist` — meaningful; asserts the three
   `_skill_md(sid).exists()` truths now that skip guards are removed. Non-trivial
   because a regression that deletes a SKILL.md would FAIL here, not skip silently.
2. `test_all_skills_have_same_six_section_headings` — meaningful; iterates all
   three files against `_EXPECTED_SECTIONS`. Catches header renaming drift.
3. `test_all_skills_have_sections_in_same_order` — meaningful; asserts section
   positions are sorted ascending in each file. Catches section reordering drift
   (e.g. a WS3/WS4 merge that puts Model metadata after Flow).
4. `test_step2_json_identical_shape_across_skills` — meaningful AND correctly
   implemented as a **shape** comparison (option ids + `allowMultiple` + `required`
   only), not an exact string. The `_step2_shape` helper (line 477–484)
   normalizes to a dict with three keys; Step 2 intro prose can differ per
   model without failing the test. Matches this reviewer's cross-check demand.

No trivial-always-pass tests detected. Audit clean.

## Merge tree audit

Exact `git log --oneline 0255333..ws5/integration` (i.e. commits added on top of
WS2's HEAD):

```
6ce3c99 W5(1): fix Observed: format in MANUAL_WALKTHROUGH.md for grep check
234b5e9 W5: structural-test finalization + manual walkthrough + README
841e958 W5 merge: dark-su3 (WS4)
ceed1ec W5 merge: 2hdm-a (WS3)
3fde886 W4: dark-su3 per-model skill — multi-component DM, all-blocked UX
da7f041 W3: 2hdm-a per-model skill — Dirac DM via pseudoscalar mediator
```

Top-level sequence (matching plan §5 step 3–4):

- WS1 (`7c60860`) → WS2 (`0255333`) → **merge WS3** (`ceed1ec`, bringing in
  `da7f041`) → **merge WS4** (`841e958`, bringing in `3fde886`) → WS5 work
  (`234b5e9` + `6ce3c99`). Merge order is WS3-then-WS4, which is permitted by
  plan §5 ("merge order does not matter").
- Both merge commits are conflict-free (implementer confirmed; working tree
  clean).

## Regression audit

- `git diff 0255333..ws5/integration -- plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` → empty.
- `git diff da7f041..ws5/integration -- plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` → empty.
- `git diff 3fde886..ws5/integration -- plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` → empty.

Per-model SKILL.md files are byte-identical to their branch heads. No stealth
edits. Pytest `91 passed` on the post-merge worktree confirms no structural
drift introduced by the merges.

## Summary

All §3 WS5 done-criteria met. All §5 integration notes honoured (`plugin.json`
untouched, test file pre-parametrized in WS2 now un-guarded in WS5, per-model
SKILL.md files untouched by this workstream). No changes requested.
