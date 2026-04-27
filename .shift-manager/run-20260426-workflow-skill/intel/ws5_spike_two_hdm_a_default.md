<!-- WS3:section=top -->
> **HALT FOR SIGN-OFF REQUIRED**
> An analytic exception has been detected for this model. Routing cannot proceed without sign-off. See Required Next Steps below.

# Routing Report: `two-hdm-a`

**Status:** HALT_FOR_SIGNOFF [HALT — see Required next steps]

**Verdict:** HALT_FOR_SIGNOFF

**Observables requested:** relic, dd, id


> **HALT FOR SIGN-OFF:** an analytic exception requires human authorization before routing can proceed. The diagnostic per-observable rows below are pinned to `status: HALT`; see *Required next steps* in the appendix.

## Axis snapshot (WS1 taxonomy)

| Axis | Description | Value |
|------|-------------|-------|
| A1 | Gauge extension class | SM |
| A2 | Symmetry-breaking patterns | — |
| A3 | Fermion projections | {'has_dark_charged_fermion': False, 'has_majorana': False, 'has_chiral_bsm': False} |
| A4 | Scalar topology | {'n_higgs_doublets': 2, 'cp_odd_scalar_present': True, 'replaces_higgs': False} |
| A5 | Global symmetries | — |
| A6 | Portal couplings | — |
| A7 | Extra colored matter | {'extra_colored_matter': False, 'fields': []} |
| A8 | Authoring status | provisional |

<!-- WS3:section=before_results_table -->
## Per-observable rows (status: HALT)

<!-- WS3:section=before_per_observable -->
<!-- WS3:section=per-observable -->

#### Observable: `relic`

**Status:** HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|

#### Observable: `dd`

**Status:** HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|

#### Observable: `id`

**Status:** HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|


## Diagnostics

```json
{
  "analytic_stub_short_circuit": true
}
```

<!-- WS3:section=appendix -->
## Required next steps (analytic exception sign-off)

An analytic exception was triggered for this model. To proceed:

1. Review the analytic exception details above.
2. Either author a real analytic module and register it, or declare this model is not analytic-eligible.
3. Re-run `/model-router` after resolving the sign-off.



---
*Methodology: WS3 model-router v1. Routing decisions are derived from WS1 taxonomy axes, WS4 analytic-exception detection, and the WS2 capability matrix. Model: `two-hdm-a`. See `plugins/workflow/skills/model-router/SKILL.md` for ranking policy.*

<!-- WS3:section=inline -->