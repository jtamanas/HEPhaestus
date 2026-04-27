<!-- WS3:section=top -->
> **HARD HALT — EFT REWRITE REQUIRED**
> This model's gauge structure requires an EFT rewrite before routing can proceed. Monte Carlo and analytic tools cannot handle this model in its current form.

# Routing Report: `dark-su3-confining-synthetic`

**Status:** HARD_HALT

**Verdict:** HARD_HALT

**Observables requested:** relic, dd, id


> **HARD HALT:** This model's gauge structure (or other fundamental property) prevents any registered tool chain from producing physically meaningful output. The default and alternative chains are listed below for diagnostic purposes only.

## Axis snapshot (WS1 taxonomy)

| Axis | Description | Value |
|------|-------------|-------|
| A1 | Gauge extension class | SM + extra SU(N) |
| A2 | Symmetry-breaking patterns | [{'factor': 'GD', 'kind': 'dark', 'pattern': 'unbroken-confining'}] |
| A3 | Fermion projections | {'has_dark_charged_fermion': True, 'has_majorana': False, 'has_chiral_bsm': False} |
| A4 | Scalar topology | {'n_higgs_doublets': 0, 'cp_odd_scalar_present': False, 'replaces_higgs': False} |
| A5 | Global symmetries | — |
| A6 | Portal couplings | — |
| A7 | Extra colored matter | {'extra_colored_matter': False, 'fields': []} |
| A8 | Authoring status | active |

<!-- WS3:section=before_results_table -->
## Per-observable diagnostic rows

<!-- WS3:section=before_per_observable -->
<!-- WS3:section=per-observable -->

#### Observable: `relic`

**Status:** HARD_HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|

- **Required action:** `EFT_REWRITE_REQUIRED` — model gauge structure incompatible with registered tools.

#### Observable: `dd`

**Status:** HARD_HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|

- **Required action:** `EFT_REWRITE_REQUIRED` — model gauge structure incompatible with registered tools.

#### Observable: `id`

**Status:** HARD_HALT

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|

- **Required action:** `EFT_REWRITE_REQUIRED` — model gauge structure incompatible with registered tools.

<!-- WS3:section=appendix -->

---
*Methodology: WS3 model-router v1. Routing decisions are derived from WS1 taxonomy axes, WS4 analytic-exception detection, and the WS2 capability matrix. Model: `dark-su3-confining-synthetic`. See `plugins/workflow/skills/model-router/SKILL.md` for ranking policy.*

<!-- WS3:section=inline -->