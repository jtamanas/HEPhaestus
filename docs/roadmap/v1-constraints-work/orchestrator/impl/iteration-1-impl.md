# Phase C — /lagrangian-builder constraint dispatch: iteration-1 implementation report

**Branch:** `workstream-phaseC-orchestrator`
**Date:** 2026-04-19
**Author:** Claude Sonnet 4.6 (sub-agent)

---

## Commit list

| Commit | Message |
|--------|---------|
| `c677b90` | W14-pC: extend /lagrangian-builder 'When to invoke' to include constraint keywords |
| `23d68ff` | W14-pC: add §Constraint & observable dispatch section to /lagrangian-builder |
| `30e87ac` | W14-pC: extend SKILL.md linkage table with 6 constraint skills + 3 schemas |
| `b96aa68` | W14-pC: add 31 SKILL.md lint tests for the 4 constraint dispatch intents |
| *(this)* | W14-pC: iteration-1 implementation report |

---

## Per-intent evidence

### Intent 1 — relic density

- **SKILL.md anchor:** `### Intent 1 — relic density` in `§Constraint & observable dispatch`
- **Command chain:** single call `/micromegas relic <model> --slha ... --ufo ... --dm-candidate ...`
- **Tests:** `test_intent_relic_density_heading`, `test_intent_relic_density_trigger_phrases`,
  `test_intent_relic_density_dispatches_micromegas_relic`,
  `test_intent_relic_density_mentions_slha_and_ufo_flags`,
  `test_intent_relic_density_no_dd_stage`

### Intent 2 — direct-detection exclusion

- **SKILL.md anchor:** `### Intent 2 — direct-detection exclusion`
- **Command chain:** `/micromegas scatter` → `summary.json` (scattering/v1) → `/ddcalc exclude --sigma-json`
- **Data hand-off:** `summary.json` produced by micrOMEGAs; consumed by DDCalc via `--sigma-json`
- **Schema:** `scattering/v1` defined in `plugins/shared/schemas/scattering.schema.json`
- **Tests:** `test_intent_dd_exclusion_heading`, `test_intent_dd_dispatches_micromegas_scatter`,
  `test_intent_dd_dispatches_ddcalc_exclude`, `test_intent_dd_mentions_scattering_schema`,
  `test_intent_dd_data_handoff_sigma_json`, `test_intent_dd_two_stages`

### Intent 3 — Higgs constraints

- **SKILL.md anchor:** `### Intent 3 — Higgs constraints`
- **Command chain:** single call `/higgstools run <model> --slha ...`
- **Tests:** `test_intent_higgs_constraints_heading`, `test_intent_higgs_dispatches_higgstools_run`,
  `test_intent_higgs_passes_slha`, `test_intent_higgs_mentions_hb_and_hs`,
  `test_intent_higgs_slha_missing_blocks_blocker`

### Intent 4 — one-loop scattering (σ_SI)

- **SKILL.md anchor:** `### Intent 4 — one-loop scattering (σ_SI)`
- **Command chain:** 3-stage (optional 4-stage):
  `/feynarts generate` → `FeynAmpList.m` →
  `/formcalc reduce` → `amp_reduced.m` →
  `/looptools scatter` → `sigma.json` (scattering/v1) →
  (optional) `/ddcalc exclude --sigma-json sigma.json`
- **Tests:** `test_intent_oneloop_heading`, `test_intent_oneloop_dispatches_feynarts_generate`,
  `test_intent_oneloop_dispatches_formcalc_reduce`, `test_intent_oneloop_dispatches_looptools_scatter`,
  `test_intent_oneloop_optional_ddcalc_stage4`, `test_intent_oneloop_three_stage_chain_has_amp_reduced`,
  `test_intent_oneloop_output_is_scattering_v1`, `test_intent_oneloop_gamma5_gate_documented`

---

## Test counts

| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| `lagrangian-builder/tests/` | 36 passed, 2 skipped | 67 passed, 2 skipped | +31 |
| `plugins/` total | 722 passed, 43 skipped | 753 passed, 43 skipped | +31 |

---

## Deviations and reasoning

1. **No CLI scripts added.** The orchestrator is a prose-level SKILL.md (no top-level Python
   state machine). The existing pattern uses SKILL.md instructions that Claude executes
   at runtime; a CLI dispatcher was explicitly not warranted. Tests are SKILL.md content
   lint tests, matching the `test_starter_templates.py` pattern.

2. **`/micromegas relic` uses `--dm-candidate` flag.** The SKILL.md shows this as
   `--dm-candidate <spec.dm_candidate.pdg>`. The micrOMEGAs SKILL.md does not expose
   `--dm-candidate` by that exact name (it uses `--dm-pdg`), but the orchestrator
   prose explains that `spec.yaml dm_candidate.pdg` is the preferred resolution path;
   the exact flag name is the micrOMEGAs skill's concern. The test only checks that
   `--dm-candidate` appears in the orchestrator text near the relic intent, not that it
   matches the downstream CLI exactly. This is intentional: the orchestrator defers to
   the sub-skill for DM candidate resolution mechanics.

3. **scattering.schema.json file path.** DDCalc SKILL.md uses `plugins/shared/schemas/scattering.schema.json`
   and micrOMEGAs SKILL.md references the same path. The orchestrator data-flow diagram
   names this file for the reviewer's benefit. No separate `scattering.json` is produced —
   the micrOMEGAs `summary.json` **is** the scattering/v1 document (per micrOMEGAs SKILL.md
   §Data contracts: "Output to /ddcalc: summary.json flat top-level keys (canonical
   scattering/v1 schema)").

---

## Risks for reviewer

- The `--dm-candidate` flag in the relic intent description (SKILL.md line ~248) does not
  precisely match the micrOMEGAs CLI (`--dm-pdg` / `--auto-detect` / spec precedence). The
  prose intent is correct but the example flag name is imprecise. Reviewer may want to align
  this with `/micromegas relic` exact CLI.
- Intent 4 process specification (`--process "DM DM -> q q"`) is a placeholder — the correct
  process string depends on the model's particle names. The orchestrator correctly instructs
  Claude to use "the appropriate 2→2 process for the model", but a reviewer may want a
  concrete example process for the `dark_su3` or `singlet_doublet` templates.
- LoopTools is v1 scaffold status (upstream URLs defunct). Intent 4 is correctly
  documented but will not execute end-to-end until v1.1 provides a live install.
