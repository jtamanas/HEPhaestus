# Round 3 Verification

Worktree: `agent-a9ae6c9923eb92eb7`. Forked from `afaa015`.

## Baseline (afaa015) failures (recorded before applying fixes)

- `plugins/model-building/skills/spheno-build/tests/test_dark_su3_analytic.py`
  → 11 passed.
- `plugins/constraints/skills/dark-matter-constraints/tests/`
  → 65 passed, 3 xfailed, 3 xpassed.
- `plugins/hep-ph-demo/skills/_shared/tests/`
  → **5 failed**, 93 passed, 3 skipped. The 5 failures were:
    - `Test2HdmA::test_step4_prose_directive_count_and_order` (pre-existing,
      unrelated to dsu3 — `2hdm-a/SKILL.md` last touched at `75942bf` /
      `179ed37`, no edits in this worktree).
    - `TestDarkSU3::test_metadata_display`
    - `TestDarkSU3::test_metadata_dm_candidates`
    - `TestDarkSU3::test_metadata_plot_axes`
    - `TestDarkSU3::test_physics_adaptation_words`
- `python3 plugins/hep-ph-demo/skills/_shared/time_budget.py
  --model dark-su3 --constraints relic dd id`
  → already showed Relic READY (`afaa015` round-2 fix had set
  `dark-matter-constraints: status: exists`).

## Post-fix results

### V1 — analytic backend tests
```
pytest plugins/model-building/skills/spheno-build/tests/test_dark_su3_analytic.py -v
```
Result: **11 passed in 0.80s**. All BP1/BP2/BP3 round-trip tests still green.
Direct call at BP1 still produces:
- `Omega_V_h2 = 33.306640485317786`
- `Omega_Psi_h2 = 2995.5574465839336`
- `sigmav_approx = True`

(`Omega_V_h2 = 33.30664…` matches the round-2 dispatcher anchor.)

### V2 — dark-matter-constraints tests
```
pytest plugins/constraints/skills/dark-matter-constraints/tests/ -q
```
Result: **67 passed, 3 xfailed, 3 xpassed in 2.10s**. Was 65 passed in
baseline → +2 new tests:
- `test_dsu3_002_disclosure_propagation_contract` (PASS) — asserts the
  `REGRESSION-ANCHOR ONLY` phrase is present in both
  `/dark-matter-constraints` and `/dark-su3` SKILL.md files, and that the
  DMC analytic-only branch contains the word `MUST`.
- `test_check_prereqs_dsu3_analytic_demotion` (PASS) — asserts that for the
  dsu3 analytic-only branch (multi_component=true + backends.spectrum=analytic),
  check_prereqs returns status=ok, notices contains
  `ANALYTIC_BACKEND_PATH`, and real_blockers does NOT contain `UFO_MISSING`.

XFAILED preserved (1 dsu3 model-not-in-config, 2 unrelated). XPASSED counts
unchanged from baseline.

### V3 — _shared structural tests
```
pytest plugins/hep-ph-demo/skills/_shared/tests/ -q
```
Result: **1 failed, 100 passed in 0.35s**. Was 5 failed, 93 passed → **-4
failures, +7 passes** (the difference is that newly-passing tests previously
failed at fixture setup or assertion). The remaining 1 failure is
`Test2HdmA::test_step4_prose_directive_count_and_order` — pre-existing on
`afaa015`, unrelated to dsu3 (no 2hdm-a SKILL.md edits in this worktree
per `git diff --stat`).

The 4 dsu3 failures that dropped:
- `TestDarkSU3::test_metadata_display` — fixed by Fix 1 (constraints.yaml
  hook now matches SKILL.md).
- `TestDarkSU3::test_metadata_dm_candidates` — fixed by Fix 1.
- `TestDarkSU3::test_metadata_plot_axes` — fixed by Fix 1.
- `TestDarkSU3::test_physics_adaptation_words` — fixed by Fix 3 banner +
  variant note that explicitly mentions `scalar dark pion`, `vector dark
  meson`, `confining` in the historical-context paragraph.

### V4 — time_budget for dark-su3
```
python3 plugins/hep-ph-demo/skills/_shared/time_budget.py \
    --model dark-su3 --constraints relic dd id
```
Result:
```
Planned chain for Dark SU(3):

  Relic density         READY
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /dark-matter-constraints [EXISTS]
    cold: 1.5–3 hr   cached: 0.3–0.7 hr

  Direct detection      BLOCKED [BLOCKED — missing: /feynarts, /formcalc, /ddcalc]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS]
      → /feynarts [PLANNED] → /formcalc [PLANNED] → /ddcalc [PLANNED]
      → /dark-matter-constraints [EXISTS]
    cold: 3–5 hr   cached: 0.5–1 hr

  Indirect detection    BLOCKED [BLOCKED — missing: /gamlike]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS]
      → /maddm [EXISTS] → /gamlike [PLANNED] → /dark-matter-constraints [EXISTS]
    cold: 1.5–4 hr   cached: 0.3–0.7 hr

Overlap-adjusted totals (shared prereqs counted once):
  selected + ready : cold ~1–3 hr,  cached ~0.3–0.6 hr
  selected total   : cold ~3.5–9 hr,  cached ~1.1–2.3 hr  (if all prereqs existed)
```
Relic READY ✓; DD/ID BLOCKED on the right list ✓.

### V5 — BP1 dispatcher anchor
Direct compute() call at BP1 produces `Omega_V_h2 = 33.306640485317786`,
matching the round-2 anchor. Full dispatcher round-trip is exercised by
`test_dispatcher_round_trip_at_BP1` in V1 (passes).

## Summary deltas vs `afaa015`

| Test bucket               | Before | After | Delta |
|---------------------------|--------|-------|-------|
| spheno-build dark_su3     | 11p    | 11p   | 0     |
| DMC tests                 | 65p    | 67p   | +2    |
| _shared/tests             | 5f/93p | 1f/100p | -4f / +7p |

The single residual failure (`Test2HdmA::test_step4_prose_directive_count_and_order`)
is pre-existing on `afaa015`; outside scope per round-3 brief.
