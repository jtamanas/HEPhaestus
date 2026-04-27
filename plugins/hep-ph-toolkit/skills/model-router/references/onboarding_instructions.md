# Onboarding a new tool into `/model-router`

The router is registry-driven — adding a new tool is a YAML edit + a driver skill, not a router source change. This file captures the full procedure.

## Architecture recap

The router is a pure consumer of three registries:

| Registry | Path | What it declares |
|---|---|---|
| Constraint chains | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` | Per-tool `status`, default chain per observable, `chain_overrides` per model, ranking roles |
| Capability matrix | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (matrix section) | Which (gauge × fermion × scalar × DM-type × mediator-regime) tuples each tool supports |
| Analytic exceptions | `plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml` | Structural-blocker escape hatches with mandatory disclosure banners |

No router source code change is required to add a tool. The router stages (`load`, `extract_axes`, `analytic_module_status`, `detect_exception`, `matrix_lookup`, `compose_rank`, `render`) read these registries at runtime.

## Step-by-step

### 1. Build the tool-driver skill
Author `plugins/<category>/skills/<tool>-install/SKILL.md` and `plugins/<category>/skills/<tool>/SKILL.md`. Follow the pattern of an existing peer (e.g. `plugins/hep-ph-toolkit/skills/micromegas/SKILL.md` for a constraint tool, `plugins/hep-ph-toolkit/skills/maddm/SKILL.md` for a Monte Carlo). The user-facing rule applies: skills must drive the real tool, never reimplement the physics.

This is the only physics-touching work.

### 2. Flip status in `constraints.yaml`
```yaml
# plugins/hep-ph-toolkit/skills/_shared/constraints.yaml
<tool>:
  status: exists      # was: planned
  hours: [<low>, <high>]
```
That field flip is what tells the router the tool is real.

### 3. Add capability rows to the matrix
Under the per-tool capability section, declare which axis-tuples the tool supports:

```yaml
matrix:
  <tool>:
    - axes: { A1: { kind: SM_X_extra_U1 }, A4: { type: dirac }, ... }
      verdict: SUPPORTED
    - axes: { A1: { kind: SM_X_extra_SUN, group: SU3 } }
      verdict: BLOCKED
      blocker: <BLOCKER_CODE>     # must be in blocker_catalog.yaml
```

P3 `matrix_lookup` reads these to fold per-prereq verdicts. Add any new blocker codes to `_shared/blocker_catalog.yaml` first.

### 4. Add role/priority for ranking
```yaml
<tool>:
  role: { id: primary }       # or validator, escape_hatch
  priority_tiebreak: 10
```
P4 `compose_rank` uses this to pick the tool over alternatives when multiple cover the same observable. Lower `priority_tiebreak` wins; ties break alphabetically by `prereq_id`.

### 5. (Optional) Register an analytic exception if the tool has a structural wall
If the tool has its own analytic-wall pattern (e.g. "can't handle Sommerfeld for U(1)_D mediators"), add an entry to `_shared/analytic_exceptions.yaml`:

```yaml
exceptions:
  <exception-id>:
    triggered_by:
      A1: { kind: SM_X_extra_U1, group: U1 }
      A6: { mediator_type: vector, regime: sommerfeld }
    disclosure_required: true
    banner: |
      [REGRESSION-ANCHOR <exception-id>]
      ...verbatim banner text...
    placements: [P1, P2, P3]
```

The detector + auto-disclosure machinery (`/analytic-exception-detector` skill) wires up the rest. Failure to add a banner when `disclosure_required: true` causes the renderer to raise `DisclosureBannerMissing` rather than ship un-disclosed analytic results.

### 6. Update WS5 expected YAMLs
The four expected-output YAMLs at `plugins/hep-ph-toolkit/skills/model-router/tests/integration/expected/` encode the ground truth for routing assertions. Any model whose chain now resolves through your new tool (instead of blocking on `PREREQ_NOT_INSTALLED`) needs its `<observable>.active_chain.prereq_id` updated.

Workflow:
1. Run the WS5 spike to capture new actual output:
   ```
   python plugins/hep-ph-toolkit/skills/model-router/tests/integration/conftest.py  # or equivalent
   ```
2. Tests will fail with new expected vs actual mismatches — that's the validation contract working as intended.
3. Update the expected YAMLs to reflect the new routing.
4. Regenerate snapshots if tripwires are tied to the affected models:
   ```
   python plugins/hep-ph-toolkit/skills/model-router/scripts/regenerate_snapshots.py
   ```

### 7. (Optional) Update `chain_overrides` for special-case models
If a specific model needs a non-default chain involving the new tool, add an override under `models.<id>.chain_overrides.<observable>` in `constraints.yaml`. Strict mode requires `matrix_acknowledgement.accepted_blockers` to enumerate any known blockers the operator is consciously accepting.

## What you do NOT touch

- `plugins/hep-ph-toolkit/skills/model-router/scripts/model_router/` — router source. If a new tool requires router source changes, the registry schema is wrong; fix the schema, not the router.
- `plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/` — meta-router scope; out-of-scope for tool onboarding.
- The canonical model assets (`plugins/hep-ph-toolkit/skills/_shared/assets/{singlet_doublet,2hdm_a,dark_su3}.yaml`) — these are pinned for validation reproducibility.

## Verification checklist

After onboarding:
- [ ] `python plugins/hep-ph-toolkit/skills/model-router/scripts/router.py <model> --output json` runs end-to-end on at least one model that exercises the new tool.
- [ ] Full test suite green: `cd /tmp/ws5-test-cwd && python -m pytest plugins/hep-ph-toolkit/skills/model-router/tests/ -v` (208+ passing).
- [ ] Out-of-scope guard passes — no edits to router source or DMC scripts.
- [ ] If exception added: `disclosure_required` banner appears in rendered output for triggering models.
- [ ] WS5 validation findings document (`.shift-manager/run-<TS>-<topic>/WS5_FINDINGS.md`) gets a new entry if any deferred items are now resolvable.

## Quick reference: where each step's edit lands

| Step | File | Type |
|---|---|---|
| 1 | `plugins/<category>/skills/<tool>{,-install}/SKILL.md` | NEW |
| 2 | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (`<tool>.status`) | EDIT |
| 3 | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (matrix section) + `_shared/blocker_catalog.yaml` | EDIT |
| 4 | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (`<tool>.role`, `priority_tiebreak`) | EDIT |
| 5 | `plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml` | EDIT |
| 6 | `plugins/hep-ph-toolkit/skills/model-router/tests/integration/expected/*.yaml` + snapshots | EDIT |
| 7 | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` (`models.<id>.chain_overrides`) | EDIT |
