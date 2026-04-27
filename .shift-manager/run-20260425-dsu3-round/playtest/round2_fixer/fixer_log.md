# Round 2 Fixer Log — Dark SU(3)

Worktree branch: `worktree-agent-ac1ac6278c7808b45`
Pre-fix HEAD: `612dcff` (`merge(docs): tier1/sharp-edges-ht-router ...`)

## Fix 1 — `/spheno-build` analytic-backend data-loss bug

**Files changed**

- `plugins/model-building/skills/spheno-build/scripts/backends/analytic.py`
  - Around the SLHA round-trip (was line 152). Added a merge step right
    after `summary = ps.parse(spc_path)` and before writing
    `summary.json`: now merges `result_dict["diagnostics"]` and
    `result_dict["mixing"]` into the summary payload. Tuple keys in
    `mixing[*]` are stringified (e.g. `(1,2)` -> `"1,2"`) so the JSON
    survives a round-trip. Also writes a separate `diagnostics.json`
    alongside `summary.json`.
- `plugins/model-building/skills/spheno-build/tests/test_dark_su3_analytic.py`
  - Added `test_dispatcher_summary_preserves_diagnostics`: invokes the
    dispatcher with the analytic backend at BP1 and asserts that
    `summary.json` carries `diagnostics.{Omega_V_h2, Omega_Psi_h2,
    blind_spot_Psi_tree}` and `mixing.MHHMIX`, and that
    `diagnostics.json` is emitted with the full diagnostics dict.

**Test result.** All 135 spheno-build tests pass:
`pytest plugins/model-building/skills/spheno-build/tests/ -q` →
`135 passed in 1.49s`. The new regression test passes.

## Fix 2 — Unblock `/dark-matter-constraints` for dsu3

### Part A — flag flip

**File:** `plugins/hep-ph-demo/skills/_shared/constraints.yaml` line ~67.

The actual value was `status: planned` (not already `exists`). Flipped
to `status: exists` with an inline comment explaining that the router
contract is committed and the analytic-only branch supports
multi-component DM.

### Part B — chain_overrides for dsu3

**File:** same `constraints.yaml`.

Added a `chain_overrides:` section under `models.dark-su3` that
replaces the relic chain with `[sarah-build, spheno-build,
dark-matter-constraints]` and pins `backend_hint: analytic`. dd and id
default chains untouched (they remain BLOCKED on planned tools —
feynarts/formcalc/ddcalc/gamlike — which is correct).

A schema for `chain_overrides` was added to the YAML's header comment
(it described `models.<m>.chain_overrides.<constraint>.{chain, reason,
backend_hint}`).

`time_budget.py` was extended to honor `chain_overrides`: when present
for a constraint, the override.chain replaces the default chain (the
multi_component_prereq is still appended). The
`multi_component_prereq` (`dark-matter-constraints`) was already in
the override chain so no duplicate appears.

### Part C — analytic-only branch in `/dark-matter-constraints` Step 2

**File:** `plugins/constraints/skills/dark-matter-constraints/SKILL.md`.

Step 2 now opens with a documented "analytic-only branch" gate: when
the model spec carries `multi_component: true` AND `backends.spectrum
== "analytic"`, MadDM is skipped entirely; the router consumes
`<spheno_run>/diagnostics.json` (per-component Omega + diagnostics)
and `<spheno_run>/summary.json` (`mixing.MHHMIX`) directly. Steps 3-5
are skipped. An informational notice `ANALYTIC_BACKEND_PATH`
(recoverable, not fatal) was added to the blocker code table. The
`MADDM_MISSING` row was qualified to clarify it is only fatal on the
default pipeline branch, not the analytic-only branch.

The `contracts/router_contract.json` did not need updating — the
analytic-only branch is a control-flow gate, not a new field
producer/consumer pair. Field-level provenance still maps cleanly to
existing manifest rows for the default-pipeline branch. The contract
tests confirm this.

### Test results

- `pytest plugins/hep-ph-demo/skills/_shared/tests/test_constraints_yaml.py
  plugins/hep-ph-demo/skills/_shared/tests/test_time_budget.py -q` →
  `31 passed`. The R2 changes flipped four pre-existing
  `TestDarkSU3{Relic,AllBlocked}.*` assertions that asserted the old
  reality (BLOCKED on `dark-matter-constraints`); those tests were
  rewritten to reflect post-fix reality (relic READY via override; dd
  and id remain BLOCKED on planned tools — `feynarts`/`formcalc`/
  `ddcalc`/`gamlike`).
- `pytest plugins/constraints/skills/dark-matter-constraints/tests/ -q`
  → `65 passed, 3 xfailed, 3 xpassed, 1 warning in 1.88s`. Router
  contract tests intact.

## Fix 3 — Resolve dual `dark_su3.yaml` specs

**Files moved**

- `plugins/model-building/skills/lagrangian-builder/assets/modelspec-templates/dark_su3.yaml`
  → `plugins/model-building/skills/lagrangian-builder/assets/modelspec-templates/archived/dark_su3_confining.yaml`
  (via `git mv`, so history is preserved).

**Files added**

- `.../assets/modelspec-templates/archived/README.md` — explains the
  archived/ subdir's purpose and inventories the dark_su3_confining.yaml
  archive reason (factual conflict with the canonical analytic module).

**References updated** (greppe`d for `dark_su3.yaml` /
`modelspec-templates/dark_su3` first):

- `plugins/model-building/README.md` — removed `dark_su3.yaml` from the
  starter template list; added a paragraph pointing to the canonical
  spec and the archive.
- `plugins/model-building/skills/lagrangian-builder/SKILL.md`:
  - §Intent 4 (one-loop scattering) — updated the path to the archived
    location and noted the canonical spec.
  - §Example end-to-end transcript (dark_su3) — added an "Archived
    narrative" callout explaining the confining variant is no longer
    canonical.
  - §Scripts/Starter templates list — moved dark_su3.yaml to a new
    "Archived templates" subsection with explanation.
- `plugins/model-building/skills/lagrangian-builder/tests/test_starter_templates.py`:
  - Removed `dark_su3.yaml` from `_TEMPLATE_FILES`.
  - Added `_ARCHIVED_TEMPLATE_FILES` and a parametrised
    `test_archived_template_validates` that still validates the
    archived spec against the live schema.
  - Renamed `test_dark_su3_gauge_groups` → `test_dark_su3_confining_archived_gauge_groups`,
    with the path updated to point under `archived/`.
- `plugins/model-building/skills/lagrangian-builder/tests/integration/dark_su3_e2e.sh`:
  - `SPEC=` updated to the archived path.
  - Header docstring updated to flag that this script exercises
    SARAH/SPheno orchestration on an archived spec; canonical Higgsed
    Dark SU(3) lives elsewhere.

**Test result.** `pytest plugins/model-building/skills/lagrangian-builder/tests/ -q`
→ `66 passed, 2 skipped` (the 2 skips were pre-existing).

## Surprises / notes

- The `dark-matter-constraints` `status` flag was actually `planned` in
  constraints.yaml (the task description said "verify the actual value
  first; if it's already `exists`, skip Part A" — Part A was needed).
- `time_budget.py` had no notion of `chain_overrides` yet; I had to
  thread it through the resolver. Done minimally and the test suite
  shows the dedup logic still works (overlap totals deduped correctly).
- Four pre-existing tests in `test_time_budget.py` had to be rewritten
  because they baked in the BLOCKED-on-dark-matter-constraints
  reality. The replacements assert the post-fix reality (READY via
  override; dd/id still BLOCKED on planned tools) and add a positive
  assertion that the override chain skips madgraph and maddm.
- Five pre-existing failures in
  `plugins/hep-ph-demo/skills/_shared/tests/test_skill_structure.py`
  (`Test2HdmA::test_step4_prose_directive_count_and_order`,
  `TestDarkSU3::{test_metadata_display, test_metadata_dm_candidates,
  test_metadata_plot_axes, test_physics_adaptation_words}`) were
  verified to fail on pre-fix `HEAD=612dcff` as well. They are
  unrelated to the R2 fix scope (dsu3 metadata/plot-axes/physics-words
  drift between SKILL.md prose and constraints.yaml). Punted —
  out-of-scope per the brief "Do not refactor anything unrelated to
  the 3 fixes."
- Two pre-existing failures in `sarah-build` tests
  (`test_scan_fp_empirical.py::test_known_corrupt_baselines_are_flagged[dark_su3-DarkSU3]`,
  `test_scan_outputs.py::test_scan_attaches_log_hints`) likewise
  verified on pre-fix HEAD. Unrelated to R2 fix scope (sarah-build
  scan_outputs corruption-detector logic). Punted.

## Punted items

- Deeper SKILL.md prose harmonisation between `/dark-su3` SKILL.md and
  `_shared/constraints.yaml` (the 5 pre-existing test_skill_structure
  failures). Out-of-scope.
- sarah-build scan_outputs detector. Out-of-scope.
- Updating `router_contract.json` with an explicit row for the analytic
  branch. Decision: not needed; the analytic-only branch is a
  control-flow gate, not a new field producer. The existing rows are
  documented as default-pipeline; the new SKILL.md text makes the
  branch logic clear. If a future round wants explicit manifest rows
  for `Omega_V_h2`/`Omega_Psi_h2` (per-component, analytic-sourced),
  add them then.
