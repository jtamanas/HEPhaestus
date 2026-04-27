---
name: model-router
description: Model-to-tool compatibility router. Given a registered BSM model ID, determines which tool chains are reachable for each observable (relic density, direct detection, indirect detection, Higgs constraints), ranks them by role (primary > validator > specialty > escape_hatch), surfaces structural blockers, and routes exception paths (analytic backend, sign-off required, hard halt).
---

# /model-router

Route a registered BSM model to its viable tool chains across all requested observables.
Returns a structured routing report (JSON + Markdown) describing which tool chains to use,
any structural blockers, and which path to take when an analytic exception is triggered.

## Prerequisites

- **`hep-ph-demo` plugin** must be installed. `model-router` imports
  `plugins/hep-ph-toolkit/skills/_shared/matrix_lookup.py`. If this import fails at runtime, the
  skill raises `WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO` with exit code 3 and a remediation
  message: `"install hep-ph-demo plugin"`.
- Model must be registered in `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` under
  `models.<model-id>`. See **Step 0: register your model** in Usage below.
- WS1 `taxonomy.read_axes` must be present at
  `plugins/hep-ph-toolkit/skills/_shared/taxonomy.py`. If absent, exit 1 with `WS1NotMerged`.
- WS2 `ConstraintRow.capability_blockers` must be present. If absent, exit 3 with `WS2NotMerged`.
- ModelSpec must be at `_schema_version: 2` (v2 schema). Run the WS1 migration tool on any
  v1 specs before invoking `/model-router`.

## Usage

### Step 0: register your model

1. Add a model entry under `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml`:
   ```yaml
   models:
     my-model:
       spec_path: plugins/my-plugin/skills/my-model/spec.yaml
       analytic_module: null  # or "analytic_models.my_module" if registered
   ```
2. Ensure the spec file exists at the declared `spec_path` and is at `_schema_version: 2`.

### Basic usage

```
/model-router <model-id>
```

Example:
```
/model-router dark-su3
```

Routes `dark-su3` across all observables declared in its `dm_phenomenology.candidates` block
(typically `relic`, `dd`, `id`).

### Specify observables

```
/model-router <model-id> --observables relic dd
```

Restricts routing to the specified observables only. Useful for targeted constraint analyses.

### Strict mode

```
/model-router <model-id> --strict
```

In strict mode:
- `supported_with_caveat` matrix cells are treated as `BLOCKED` for active-chain selection.
- Missing matrix acknowledgement contradictions raise exit code 4.
- `HALT_FOR_SIGNOFF` exits with code 5.
- `HARD_HALT` exits with code 6.

Default mode (without `--strict`) exits 0 for all verdicts.

### Output options

```
/model-router <model-id> --output md|json|both
```

Default: `md` (Markdown). Use `--output both` to get both the JSON sidecar and Markdown report.
Use `--output-dir <path>` to write reports to files instead of stdout.

### Explain a prereq verdict

```
/model-router <model-id> --explain maddm
```

Appends a `## Verdict trace for maddm` section to the Markdown report showing the per-prereq
fold breakdown — matrix verdict, blockers, caveats, role assignment.

### Python API

```python
import sys
sys.path.insert(0, 'plugins/hep-ph-toolkit/skills/model-router/scripts')

from model_router import route, RouterOptions

report = route(
    model_id="dark-su3",
    observables=["relic", "dd", "id"],
    options=RouterOptions(strict=False),
)
sys.exit(report.exit_code)
```

## Routing pipeline

The router executes six stages in sequence:

| Stage | Name | Description |
|-------|------|-------------|
| P0 | Load | Load `constraints.yaml`, `blocker_catalog.yaml`, `analytic_exceptions.yaml`, and the ModelSpec. Verify WS2 presence (D1 gate). |
| P1 | Extract axes | Call `taxonomy.read_axes` (WS1); populate `AxisBundle` (A1–A8). Halt early on `A8 == archived`. Compute `analytic_module_status` via `STUB` marker detection. |
| P2 | Detect exception | Invoke WS4 `/analytic-exception-detector`. HARD_HALT or HALT_FOR_SIGNOFF jump directly to P5. |
| P3 | Matrix lookup | Load capability matrix via `hep-ph-demo._shared.matrix_lookup`. Look up per-observable, per-prereq verdicts. |
| P4 | Compose + rank | Combine P1–P3 results; rank prereqs by role → priority → user memory. Emit `ComposedRouting`. |
| P5 | Render | Build JSON + Markdown report. Inject placement banners. Validate JSON against schema. Compute exit code. |

### Short-circuit paths

- **HARD_HALT:** After P2, skip P3 and P4. Render a hard-halt prompt with no sign-off option.
- **HALT_FOR_SIGNOFF:** After P2, skip P3 and P4. Render per-observable rows showing what
  *would* have been routed, plus the §5 sign-off prompt as an appended "Required next steps"
  section.

## Ranking policy

Chain ranking uses a three-layer sort applied to `PrereqFold` items per observable:

1. **Role** (primary first): `primary` < `validator` < `specialty` < `escape_hatch` < `none`.
2. **Priority tiebreak**: lower `priority_tiebreak` integer wins (set by the matrix).
3. **User memory**: if `RouterOptions.user_preferences` is set (dict of `{prereq_id: int}`),
   lower integer wins. Prereqs absent from user_preferences get default priority 999.
4. **Alphabetical by `prereq_id`**: deterministic final tiebreak.

The matrix is the primary authority. User memory is a tertiary tiebreak only — it does **not**
override role or priority. A `primary` tool always ranks above a `validator` regardless of user
preferences.

### ROUTE_TO_ANALYTIC path

When WS4 returns `ROUTE_TO_ANALYTIC`:
- The `analytic_backend` is pinned as the active chain (escape_hatch role).
- For DM observables (`relic`, `dd`, `id`) with multiple candidates, per-candidate routing
  is rendered: each candidate gets its own `expected_observable_label` (e.g., `Omega_V_h2`).
- A disclosure banner is injected via placement `{position: before_per_observable, kind: analytic}`.

## Strict mode + exit codes

| Code | Condition |
|------|-----------|
| 0 | Success — all verdicts in default mode; CLEAR and ROUTE_TO_ANALYTIC in strict mode |
| 1 | `WS1NotMerged` — `taxonomy.read_axes` not importable |
| 3 | `WS2NotMerged` or `WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO` |
| 4 | `--strict` + matrix acknowledgement contradiction |
| 5 | `--strict` + `HALT_FOR_SIGNOFF` verdict |
| 6 | `--strict` + `HARD_HALT` verdict |

## Report structure

The JSON report (`routing_report.schema.json` v1) contains:

```json
{
  "schema_version": 1,
  "model_id": "dark-su3",
  "observables": ["relic", "dd", "id"],
  "verdict": "ROUTE_TO_ANALYTIC",
  "model_props": {"analytic_module_status": "registered_active"},
  "axis_snapshot": {"A1": "SM + extra SU(N)", "A8": "complete"},
  "per_observable": {
    "relic": {
      "observable": "relic",
      "status": "ROUTED",
      "active_chain": {"prereq_id": "analytic_backend", "role": "escape_hatch", "status": "ROUTED"},
      "ranked_alternatives": [],
      "per_candidate": [
        {
          "candidate_name": "V",
          "active_chain": {"prereq_id": "analytic_backend", ...},
          "expected_observable_label": "Omega_V_h2"
        }
      ]
    }
  },
  "placements": [
    {"position": "before_per_observable", "content": "...", "kind": "analytic"}
  ],
  "diagnostics": {},
  "exit_code": 0
}
```

### Placement positions

| Position | Description |
|----------|-------------|
| `top` | Before everything — used for hard-halt and halt-for-signoff notices |
| `before_results_table` | Before the per-observable results table |
| `before_per_observable` | Before the per-observable section — used for analytic disclosure banner |
| `appendix` | At end of report — used for sign-off prompts |
| `inline` | Inline within a section |

## Schema versioning

- `routing_report.schema.json` is at `schema_version: 1`. The integer is embedded in every
  emitted JSON report. Breaking changes (e.g., removing required fields) require incrementing
  `schema_version` and a migration guide.
- `ranked_chain.schema.json` defines the `ActiveChain` sub-schema; it is referenced via
  `$ref` from `routing_report.schema.json`.
- JSON validation runs automatically via `jsonschema` (if installed). If `jsonschema` is
  absent, validation is skipped (fail-open at import time).

## Validation

The router has an integration test suite at
`plugins/hep-ph-toolkit/skills/model-router/tests/integration/` that validates
the four canonical fixture models (`singlet-doublet`, `two-hdm-a`,
`dark-su3`, `dark-su3-confining-synthetic`) against the fixture
registry. Run with:

```
pytest plugins/hep-ph-toolkit/skills/model-router/tests/integration/ -v
```

For a one-page summary suitable for a merge report:

```
python3 plugins/hep-ph-toolkit/skills/model-router/scripts/validation_report.py
```

Snapshots are git-tracked under `tests/integration/snapshots/`; regenerate
after a legitimate router change with:

```
python3 plugins/hep-ph-toolkit/skills/model-router/scripts/regenerate_snapshots.py
```

Note: `dark-su3` strict-mode snapshot is absent (7 snapshots instead of 8)
because strict mode raises `MatrixAcknowledgementMissing` per the WS3 contract.
See `WS5_FINDINGS.md` Finding 4 for remediation options.

## Plugin-home override note

The `model-router` skill lives in the `workflow` plugin at
`plugins/hep-ph-toolkit/skills/model-router/`. This overrides the default plugin-home convention
because `workflow` also owns the `analytic-exception-detector` skill (WS4). Both skills
share the `plugins/hep-ph-toolkit/.claude-plugin/plugin.json` manifest.

The Python package uses an underscore name (`model_router`) per PEP 8, while the skill
directory uses a kebab-case name (`model-router`) per Claude Code skill convention. The
`router.py` CLI entrypoint inserts its parent directory into `sys.path` so `import model_router`
resolves without an editable install.

## Upstream dependencies

| Dependency | Purpose | Absent behavior |
|------------|---------|----------------|
| `plugins/hep-ph-toolkit/skills/_shared/taxonomy.py` (WS1) | `read_axes` — extract A1–A8 | Exit 1: `WS1NotMerged` |
| `plugins/hep-ph-toolkit/skills/_shared/time_budget.py` + `ConstraintRow.capability_blockers` (WS2) | Capability blocker lookup | Exit 3: `WS2NotMerged` |
| `plugins/hep-ph-toolkit/skills/_shared/matrix_lookup.py` (WS2) | Load capability matrix | Exit 3: `WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO` |
| `plugins/hep-ph-toolkit/skills/analytic-exception-detector/` (WS4) | Analytic exception detection | CLEAR stub verdict + `detector_unavailable: true` diagnostic; exit 0 |

**Out of scope:** `plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/` is never
read or modified by this skill.

## Adding a new tool

The router is registry-driven — onboarding a new tool is a YAML edit + a driver skill,
not a router source change. See [`references/onboarding_instructions.md`](references/onboarding_instructions.md)
for the full step-by-step procedure (status flip, capability matrix rows, ranking role,
optional analytic-exception registration, expected-YAML updates).
