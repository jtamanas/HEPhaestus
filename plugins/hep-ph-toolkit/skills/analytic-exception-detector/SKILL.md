---
name: analytic-exception-detector
description: Detects when a BSM ModelSpec structurally requires the analytic-backend escape hatch (dsu3-002 pattern), enforces the user-sign-off gate, and renders the mandatory disclosure banner upstream of /dark-matter-constraints.
---

# analytic-exception-detector

Workflow-layer predecessor to `/dark-matter-constraints`. Given a BSM ModelSpec YAML,
it detects whether the model's gauge/fermion/scalar structure hits a wall that no
standard tool chain (MadDM / SARAH / MG5) can handle, determines whether an analytic
backend has been authorized, and emits a routing recommendation with the mandatory
disclosure banner. It does NOT invoke any tool, compute any observable, or modify the
`/dark-matter-constraints` router contract.

---

## Overview

**What this skill detects.** The analytic-exception class: a BSM model whose dark
non-abelian gauge structure prevents MG5/MadDM from importing the UFO (the `dt1`
NameError wall), AND whose DM candidates are not UV fields but broken-generator or
composite states (so MadDM could not generate the coannihilation set even if the UFO
imported). The dark-SU(3) Higgsed model (`dsu3-002`) is the canonical example.

**Verdicts (synthesis §3.3).**

| Verdict | Meaning | Action |
|---------|---------|--------|
| `CLEAR` | No structural signals fired; model routes normally. | Proceed to WS2/WS3 capability lookup → `/dark-matter-constraints`. |
| `ROUTE_TO_ANALYTIC` | Analytic backend declared AND wired (registry entry exists). | Emit disclosure banner (see §Exception registry); recommend invoking `/dark-matter-constraints` analytic-only branch. |
| `HALT_FOR_SIGNOFF` | Analytic declared but not wired, OR structural signals fired without authorization. | Emit §Sign-off contract prompt. No dispatch until registry entry is authored. |
| `HARD_HALT` | Confining dark sector detected — no analytic escape hatch conceivable. | Halt with "paper-grade modelling required" verdict. Do NOT offer sign-off path. |

**Signals (structural; active inference from ModelSpec).**

| Signal | Fires when |
|--------|------------|
| `S_GAUGE_DARK_NONABELIAN` | Dark `SU(N)` gauge group (N≥2) with non-trivial fermion/scalar reps. |
| `S_CONFINING_DARK` | `confining: true` on dark gauge group, OR composite hadron names in scalar_potential without UV scalar counterpart, OR outputs excludes both ufo and spheno with a dark gauge group present. |
| `S_DM_NOT_IN_UV_FIELDS` | Documented DM candidates include names absent from UV fields (fermions/scalars/gauge_bosons); only fires when a dark gauge group is present (mass-eigenstate DM in SM-only models is correctly excluded). |

**Short-circuit inputs (passive read; override structural inference).**

| Input | Fires when |
|-------|-----------|
| `SC_ANALYTIC_DECLARED` | `backends.spectrum == "analytic"` in the ModelSpec. |
| `SC_ANALYTIC_MODULE_WIRED` | `backends.analytic_module` resolves to a real file under `analytic_models/` AND the registry has an active entry with that module path for this model. |

---

## Inputs

- **ModelSpec YAML** (primary, required) — the model's spec file. Schema: `spec_version`, `name`, `gauge_groups`, `fermions`, `scalars`, `lagrangian`, `backends`, `outputs`. See `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/` for v3 reference vocabulary.

- **`_shared/constraints.yaml`** (side input, read-only) — used only to read `models.<name>.multi_component`. Does NOT read `chain_overrides`, `prereqs`, or anything else. Does NOT alter the verdict.

- **WS1 axis inputs** (optional, when WS1 is available) — `SignalInputs` dataclass passed to `detect()`:
  ```python
  SignalInputs(
      gauge_extension_class="dark",         # e.g. 'dark', 'SM + extra SU(N)'
      dm_candidate_uv_provenance="broken_generator",  # 'fundamental' | 'broken_generator' | ...
      stabilizing_symmetry=None,            # recorded in evidence; does not affect verdict
      raw_modelspec=spec,                   # always required as fallback
  )
  ```
  When `signal_inputs` is `None` or individual axes are `None`, the detector falls back to direct ModelSpec inspection. Both paths produce identical results for the canonical demo models.

---

## Outputs

**Markdown routing report** (human-facing) — includes:
- Verdict heading and evidence block.
- For `ROUTE_TO_ANALYTIC`: the verbatim disclosure banner (blockquote-wrapped) **before** the `### Results` anchor.
- For `HALT_FOR_SIGNOFF` / `HARD_HALT`: the sign-off prompt (see §Sign-off contract).

**JSON Verdict sidecar** (agent-facing) — the full `Verdict` dataclass serialized to JSON:
```json
{
  "verdict": "ROUTE_TO_ANALYTIC",
  "short_circuits_fired": ["SC_ANALYTIC_DECLARED", "SC_ANALYTIC_MODULE_WIRED"],
  "signals_fired": ["S_GAUGE_DARK_NONABELIAN", "S_DM_NOT_IN_UV_FIELDS"],
  "evidence": { ... },
  "disclosure_required": true,
  "exception_id": "dsu3-002",
  "analytic_module": "/path/to/analytic_models/dark_su3.py",
  "lint_warnings": [],
  "reason_human": "..."
}
```

Both outputs include the rendered disclosure banner inline when `disclosure_required: true`.

---

## Exception registry

Registry file: `plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml`

Co-located with `constraints.yaml`. Each entry pins a **verbatim banner** that must appear at registered placement file paths (P1=DMC SKILL.md, P2=model SKILL.md, P3=analytic module docstring for `analytic` kind).

**Registry schema (schema_version: 1):**

```yaml
schema_version: 1
disclosure_version: 1  # reserved for future cross-cutting banner-text migrations (no tooling ships in WS4)

exceptions:
  - id: dsu3-002           # per-model serial: <modelname>-<NNN>
    kind: analytic         # analytic | proxy_run
    model: dark-su3
    status: active         # active | deprecated | retired
    analytic_module: plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py
    signals_recorded: [S_GAUGE_DARK_NONABELIAN, S_DM_NOT_IN_UV_FIELDS]
    placements:
      P1: plugins/hep-ph-toolkit/skills/dark-matter-constraints/SKILL.md
      P2: plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md
      P3: plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py
    banner: |
      **REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (dsu3-002).** ...
      ... MUST embed this banner verbatim — do not silently strip it.
    deprecated_in: null
    retired_in: null

proxy_runs:
  - id: micromegas-singlet-doublet-proxy-001
    kind: proxy_run
    model: singlet-doublet
    ...
    banner: |
      **PROXY-RUN DISCLOSURE.** ...
      ... tag every affected table row with `[proxy]`.
```

**Banner well-formedness (enforced by CI):**
- `analytic` kind: must match `**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (<id>).**` AND end with `MUST embed this banner verbatim — do not silently strip it.`
- `proxy_run` kind: must match `**PROXY-RUN DISCLOSURE.**` AND end with `tag every affected table row with \`[proxy]\`.`

**Adding a new exception:** open a PR adding an entry to the registry with a hand-authored verbatim banner. CI runs the static placement test; if the banner fails well-formedness or is absent from any placement path, merge is blocked. There is no auto-generation path. The friction is the point.

The `disclosure_version` field is reserved for future cross-cutting banner-text migrations; no tooling for it ships in WS4. Bump it only when all registered banners need simultaneous rewording.

---

## Sign-off contract

When the verdict is `HALT_FOR_SIGNOFF`, the skill emits this structured prompt:

```
ANALYTIC EXCEPTION DETECTED — USER SIGN-OFF REQUIRED

Model: <name>
Verdict: HALT_FOR_SIGNOFF
Signals fired:
  - S_GAUGE_DARK_NONABELIAN  (evidence: scalars[0].reps.GD = 3)
  - S_DM_NOT_IN_UV_FIELDS    (evidence: DM candidate "V" not in fermions/scalars)

Standing rule: skills must drive real upstream tools. New analytic modules
are the documented exception (dsu3 is the only existing case).

This model has no analytic module wired. The workflow skill will NOT proceed
to dispatch; the analytic-backend escape hatch requires explicit user sign-off.

To authorize the analytic backend for this model:
  1. Author <plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/<modelname>.py>
     by hand. The workflow skill will not write this for you.
  2. Open a PR adding an entry to plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml
     with a hand-authored verbatim banner specific to this model's physics.
  3. Embed the banner verbatim in all registered placement paths (P1, P2, P3).
  4. Land the PR. CI runs the static contract test against the new entry.
  5. Re-run the workflow skill. Verdict will be ROUTE_TO_ANALYTIC.

To proceed without the analytic backend:
  - Document why the model's blocker is *not* a fundamental group-theory gap.
  - The workflow skill's verdict cannot be overridden by a CLI flag.
    There is no escape hatch — registry edit required.
```

**No CLI override flag.** No `--override-detector-verdict`. No TTY check. The act of authorization is opening a PR. This is PR review-gated, agent-illegal-by-convention, audit-trailed, and CI-tested.

**`HARD_HALT` does NOT offer the sign-off path.** When `S_CONFINING_DARK` fires, the skill emits "paper-grade modelling required, no escape hatch" and stops. The archived `dark_su3_confining.yaml` is the canonical exemplar.

---

## Retirement contract

Registry entries carry `status: active | deprecated | retired`.

**`active` → `deprecated`:** an upstream tool feature lands obviating the exception (e.g., MG5 ships SU(N)_D color algebra → dsu3-002 deprecated). PR adds `deprecated_in: <commit>` and `replacement: <text>`. CI tests warn (don't fail) on missing placements. Routing report adds a "recommended migration" section.

**`deprecated` → `retired`:** (a) analytic backend removed from codebase, (b) replacement path operational and validated, (c) deprecation live for ≥1 release cycle. PR removes analytic module; sets `status: retired`, `retired_in: <commit>`; removes banner from placements. CI tests skip. Entry remains in registry as audit trail.

---

## What this skill does NOT do

- Does NOT modify the `/dark-matter-constraints` router contract (inputs, outputs, blocker codes, AND-gate in `check_prereqs.py`).
- Does NOT call `/dark-matter-constraints`. Its output is a routing recommendation; the user or downstream agent invokes DMC.
- Does NOT author analytic modules. The module is the physics; an agent writing it would violate "skills must drive real tools."
- Does NOT auto-allocate exception IDs. The author allocates them in the PR.
- Does NOT auto-edit any SKILL.md or analytic module file. Placement edits are human-applied in the same PR.
- Does NOT timeout or suppress re-checks. Subsequent invocations on the same un-authorized ModelSpec re-fire the prompt.
- Does NOT probe installed tools (no `config.json` read). Tool availability is WS2/WS3's responsibility.
- Does NOT compute observables. Purely structural reasoning.

---

## Lint warnings

Lint warnings appear in the routing report's **main summary** AND in the JSON sidecar (visibility wins). Current lint warnings:

| Code | Fires when |
|------|-----------|
| `analytic_module_without_structural_justification` | `SC_ANALYTIC_MODULE_WIRED=True` but no structural signal (`S_GAUGE_DARK_NONABELIAN`, `S_DM_NOT_IN_UV_FIELDS`) fires. Verdict is still `ROUTE_TO_ANALYTIC`; this is a warning to review the registry entry's `signals_recorded` field. |
| `module_wired_without_declaration` | `backends.analytic_module` resolves to a real file but `backends.spectrum != "analytic"`. Verdict is `HALT_FOR_SIGNOFF`. |

---

## Tests

| Test file | Tier | Description |
|-----------|------|-------------|
| `tests/test_exceptions_registry.py` | unit | Loader: seed parsing, id/model/kind lookup, malformed-banner rejection, status filtering. 6 tests. |
| `tests/test_detector.py` | unit | Detector: 4 verdicts (CLEAR/ROUTE_TO_ANALYTIC/HALT_FOR_SIGNOFF/HARD_HALT), lint gate, WS1 axis input path, WS1 fallback, multi_component evidence. 8 tests. |
| `plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/test_analytic_exception_disclosure_static.py` | static | Registry-driven placement test (marker: `disclosure_contract`). 5 tests (well-formedness + placements per entry + status filtering). |
| `plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/test_analytic_exception_disclosure_emission.py` | runtime | Workflow-skill upstream renderer: dsu3-002 banner verbatim + positionally before `### Results`. 2 tests. |

**Known WS4 v1 limitations (follow-up FUs):**
- `FU-ws4-dmc-renderer`: DMC has no Python merged-report renderer; DMC-side runtime emission test deferred.
- `FU-ws4-proxy-runtime-emission`: proxy_run runtime emission test deferred (requires DMC scripts/ modification, out of scope for WS4).
- `FU-ws4-proxy-run-placements`: proxy_run banner not yet added to micromegas/SKILL.md and DMC SKILL.md (out of scope for WS4 v1 per out-of-scope manifest). Static test emits warnings for proxy_run placements.
