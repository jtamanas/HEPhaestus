# Orchestration: state diagram and blocker propagation

This document describes the complete state machine for `/lagrangian-builder`
at an operational level.  The SKILL.md is the authoritative driver; this
document provides the underlying logic for tracing a run.

---

## Entry points

Three entry points; each converges on a validated ModelSpec YAML before
invoking sub-skills.

| Entry | Trigger | Path |
|---|---|---|
| Interview | User describes a model in prose | SKILL.md §Step 0(a) → `interview.md` → `validate_spec.py` |
| Existing spec | User provides a YAML file or path | SKILL.md §Step 0(b) → `validate_spec.py` |
| Named model | User references a registered model | SKILL.md §Step 0(c) → `check_state.py --model <name>` |

---

## State diagram (prose)

```
ENTRY
 │
 ├─ Input is named model
 │     └─ check_state.py --model <name>
 │           ├─ model.status == "present"
 │           │     └─ DONE: report UFO + SLHA paths; suggest /madgraph
 │           └─ model.status == "missing"
 │                 └─ look for starter template → (offer interview or proceed)
 │
 ├─ Input is spec YAML or interview result
 │     └─ validate_spec.py <spec.yaml>
 │           ├─ exit 0 → VALIDATED_SPEC
 │           └─ exit 1 (MODELSPEC_INVALID blocker on stderr) → surface + STOP
 │
VALIDATED_SPEC
 │
 ├─ check_state.py
 │     ├─ sarah_install == "configured" → SARAH_READY
 │     └─ sarah_install == "missing"
 │           └─ /sarah-install detect
 │                 ├─ configured → SARAH_READY
 │                 ├─ found → ask user; /sarah-install use-path <path> → SARAH_READY
 │                 └─ missing → /sarah-install install
 │                       ├─ ok → SARAH_READY
 │                       ├─ activation_required
 │                       │     └─ PAUSE: show user_instruction; STOP (not a blocker)
 │                       └─ fatal blocker → surface full JSON; STOP
 │
SARAH_READY
 │
 └─ /sarah-build (build.py <spec.yaml> [--force])
       ├─ {"status":"cached"} → skip; already built → SARAH_BUILT
       ├─ success → SARAH_BUILT
       └─ fatal blocker (stderr) → surface full JSON; STOP
             Codes: MODELSPEC_INVALID, WOLFRAM_KERNEL_ABSENT,
                    ANOMALY_CANCELLATION_FAILED, SARAH_OUTPUT_MISSING
 │
SARAH_BUILT
 │
 ├─ check_state.py
 │     ├─ spheno_install == "configured" → SPHENO_READY
 │     └─ spheno_install == "missing"
 │           └─ /spheno-install detect
 │                 ├─ configured or version_mismatch+fresh → SPHENO_READY
 │                 └─ missing → /spheno-install install
 │                       ├─ ok → SPHENO_READY
 │                       └─ fatal blocker → surface; STOP
 │                             Codes: GFORTRAN_ABSENT, SPHENO_DOWNLOAD_FAILED,
 │                                    SPHENO_BASE_BUILD_FAILED
 │
SPHENO_READY
 │
 └─ /spheno-build (run_spheno.py <name>)
       ├─ success → SPHENO_RAN
       ├─ recoverable blocker (stderr)
       │     Codes: SPHENO_SPECTRUM_PROBLEM, SPHENO_RGE_NONCONVERGENT
       │     └─ show blocker; offer alternatives; continue to SPHENO_RAN with caveat
       └─ fatal blocker → surface; STOP
             Codes: SPHENO_COMPILE_FAILED, SPHENO_NO_OUTPUT, SPHENO_PATH_INVALID
 │
SPHENO_RAN
 │
 └─ register_model.py <name> --spec ... --ufo ... [--latest-slha ...] ...
       └─ DONE: report paths; suggest /madgraph use <name>
```

---

## Skip conditions

A step is skipped entirely when:

| Step | Skip condition |
|---|---|
| `/sarah-install` | `check_state.py → sarah_install == "configured"` |
| `/spheno-install` | `check_state.py → spheno_install == "configured"` |
| `/sarah-build` | `build.py` returns `{"status":"cached"}` (spec unchanged + cache key matches) |
| `/spheno-build` compile stage | `compile_model.py` finds matching `.build_key` and binary present |
| Entire pipeline | `check_state.py --model <name> → model.status == "present"` and user does not ask to rebuild |

---

## Blocker propagation rules

Three-state contract (PR-D commit `f72e19e`):

| Mode | Field shape | Pipeline action |
|---|---|---|
| `fatal` | `{code, mode:"fatal", message, [context], [user_instruction]}` | Surface full JSON; stop immediately |
| `recoverable` | `{code, mode:"recoverable", message, [context], [user_instruction]}` | Surface JSON; offer mitigation; continue scan if applicable |
| `reference_only` | `{status:"reference_only", reference_method, caveats}` | **Not emitted by /lagrangian-builder sub-skills in v1** (see note) |

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

Note on `reference_only`: none of W1–W4 sub-skills emit this mode.  It is
defined in the schema for future use (e.g., if a fallback analytic calculator
is added).  Do NOT emit `reference_only` from within this pipeline.

### Activation-required is NOT a blocker

`{"status":"activation_required","user_instruction":"..."}` is printed on
**stdout** by `/sarah-install install`, not on stderr.  Claude must:
1. Read this JSON from stdout.
2. Show `user_instruction` to the user.
3. Stop the pipeline without emitting any blocker.

This is the only non-blocker status that causes a pipeline stop.

---

## Config keys written (cumulative)

The table below shows which keys are written at each stage.  All writes are
atomic (via `config_helpers.merge_config`).

| Stage | Config key | Value |
|---|---|---|
| `/sarah-install` | `sarah_path` | SARAH package dir |
| `/sarah-install` | `sarah_version` | e.g. `4.15.3` |
| `/sarah-install` | `sarah_installed_at` | UTC ISO 8601 |
| `/spheno-install` | `spheno_path` | binary path |
| `/spheno-install` | `spheno_src_path` | source tree root |
| `/spheno-install` | `spheno_version` | e.g. `4.0.5` |
| `/spheno-install` | `spheno_installed_at` | UTC ISO 8601 |
| `/sarah-build` | `config.models[name].spec` | spec YAML path |
| `/sarah-build` | `config.models[name].ufo` | UFO dir path |
| `/sarah-build` | `config.models[name].sarah_built_at` | UTC ISO 8601 |
| `/spheno-build` | `config.models[name].spheno_bin` | binary path |
| `/spheno-build` | `config.models[name].latest_slha` | latest `.spc` path |
| `/spheno-build` | `config.models[name].latest_run` | run timestamp |
| `/spheno-build` | `config.models[name].spheno_built_at` | UTC ISO 8601 |
| `register_model.py` | consolidates all model sub-keys | (idempotent update) |

---

## References

- Three-state blocker contract: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- ModelSpec v3 schema: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-model-building.md`
- Implementation plan: `docs/superpowers/workstream-sarah-spheno/phase2-plan-final.md §W5`
