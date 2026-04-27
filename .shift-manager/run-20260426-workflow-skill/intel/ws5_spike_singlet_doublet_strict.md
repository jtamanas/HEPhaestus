<!-- WS3:section=top -->
# Routing Report: `singlet-doublet`

**Status:** CLEAR

**Verdict:** CLEAR

**Observables requested:** relic, dd, id


## Axis snapshot (WS1 taxonomy)

| Axis | Description | Value |
|------|-------------|-------|
| A1 | Gauge extension class | SM |
| A2 | Symmetry-breaking patterns | — |
| A3 | Fermion projections | {'has_dark_charged_fermion': False, 'has_majorana': False, 'has_chiral_bsm': False} |
| A4 | Scalar topology | {'n_higgs_doublets': 0, 'cp_odd_scalar_present': False, 'replaces_higgs': False} |
| A5 | Global symmetries | — |
| A6 | Portal couplings | — |
| A7 | Extra colored matter | {'extra_colored_matter': False, 'fields': []} |
| A8 | Authoring status | active |

<!-- WS3:section=before_results_table -->
## Routing decisions per observable

<!-- WS3:section=before_per_observable -->
<!-- WS3:section=per-observable -->

#### Observable: `relic`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **maddm** | primary | ROUTED | — |
| 2 | micromegas | validator | BLOCKED | CALCHEP_MDL_MISSING |
| 3 | feynrules | validator | ROUTED | — |
| 4 | drake | specialty | BLOCKED | MATRIX_COVERAGE_GAP |
| 5 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 6 | ddcalc | none | ROUTED | — |
| 7 | higgstools | none | ROUTED | — |
| 8 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 9 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 10 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 11 | madgraph | none | ROUTED | — |
| 12 | sarah-build | none | ROUTED | — |
| 13 | spheno-build | none | ROUTED | — |

#### Observable: `dd`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **ddcalc** | primary | ROUTED | — |
| 2 | maddm | primary | ROUTED | — |
| 3 | micromegas | validator | BLOCKED | CALCHEP_MDL_MISSING |
| 4 | feynrules | validator | ROUTED | — |
| 5 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 6 | higgstools | none | ROUTED | — |
| 7 | drake | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 8 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 9 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 10 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 11 | madgraph | none | ROUTED | — |
| 12 | sarah-build | none | ROUTED | — |
| 13 | spheno-build | none | ROUTED | — |

#### Observable: `id`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **maddm** | primary | ROUTED | — |
| 2 | feynrules | validator | ROUTED | — |
| 3 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 4 | ddcalc | none | ROUTED | — |
| 5 | higgstools | none | ROUTED | — |
| 6 | micromegas | none | BLOCKED | CALCHEP_MDL_MISSING |
| 7 | drake | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 8 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 9 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 10 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 11 | madgraph | none | ROUTED | — |
| 12 | sarah-build | none | ROUTED | — |
| 13 | spheno-build | none | ROUTED | — |

<!-- WS3:section=appendix -->

---
*Methodology: WS3 model-router v1. Routing decisions are derived from WS1 taxonomy axes, WS4 analytic-exception detection, and the WS2 capability matrix. Model: `singlet-doublet`. See `plugins/workflow/skills/model-router/SKILL.md` for ranking policy.*

<!-- WS3:section=inline -->