<!-- WS3:section=top -->
# Routing Report: `dark-su3`

**Status:** ROUTE_TO_ANALYTIC

**Verdict:** ROUTE_TO_ANALYTIC

**Observables requested:** relic, dd, id


> **Routing to the analytic backend.** Default Monte Carlo chains cannot represent this model. The disclosure banner below is mandatory and verbatim from the analytic_exceptions registry.

## Axis snapshot (WS1 taxonomy)

| Axis | Description | Value |
|------|-------------|-------|
| A1 | Gauge extension class | SM + extra SU(N) |
| A2 | Symmetry-breaking patterns | [{'factor': 'GD', 'kind': 'dark', 'pattern': 'Higgsed-partial'}] |
| A3 | Fermion projections | {'has_dark_charged_fermion': False, 'has_majorana': False, 'has_chiral_bsm': False} |
| A4 | Scalar topology | {'n_higgs_doublets': 0, 'cp_odd_scalar_present': False, 'replaces_higgs': False} |
| A5 | Global symmetries | — |
| A6 | Portal couplings | — |
| A7 | Extra colored matter | {'extra_colored_matter': False, 'fields': []} |
| A8 | Authoring status | complete |

<!-- WS3:section=before_results_table -->
## Routing decisions per observable

<!-- WS3:section=before_per_observable -->
**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (dsu3-002).** Dark-SU(3)
relic density runs through the analytic backend (`analytic_models.dark_su3`)
and currently uses `<sigma v>` approximations (`sigmav_approx=True`). The
emitted Ωh² values are roughly **25000× the Planck target** and must be read
as regression anchors for the analytic pipeline, **not** as a physics
prediction or a paper-fidelity result. Paper fidelity (Ω_tot h² ≈ 0.12) is
out of reach this iteration and requires the upgrade roadmap in
`analytic_models.dark_su3` (full Boltzmann integration + multi-component
weighting in `/dark-matter-constraints`). Any downstream report that quotes
these numbers MUST embed this banner verbatim — do not silently strip it.


<!-- WS3:section=per-observable -->

#### Observable: `relic`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **analytic_backend** | escape_hatch | ROUTED | — |
| 2 | sarah-build | none | ROUTED | — |
| 3 | spheno-build | none | BLOCKED | SPHENO_NOT_REQUESTED |
| 4 | madgraph | none | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 5 | maddm | primary | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 6 | micromegas | validator | BLOCKED | CALCHEP_MDL_MISSING |
| 7 | drake | specialty | BLOCKED | DRAKE_SINGLE_SPECIES_ONLY |
| 8 | ddcalc | none | ROUTED | — |
| 9 | higgstools | none | BLOCKED | HIGGSTOOLS_SLHA_MISSING_BLOCKS |
| 10 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 11 | feynrules | validator | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 12 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 13 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 14 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |

##### Per-candidate routing

##### Candidate `V`

- **Field type:** vector
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `Omega_V_h2`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

##### Candidate `Psi`

- **Field type:** Dirac fermion
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `Omega_Psi_h2`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

#### Observable: `dd`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **analytic_backend** | escape_hatch | ROUTED | — |
| 2 | sarah-build | none | ROUTED | — |
| 3 | spheno-build | none | BLOCKED | SPHENO_NOT_REQUESTED |
| 4 | madgraph | none | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 5 | maddm | primary | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 6 | micromegas | validator | BLOCKED | CALCHEP_MDL_MISSING |
| 7 | drake | none | BLOCKED | DRAKE_SINGLE_SPECIES_ONLY |
| 8 | ddcalc | primary | ROUTED | — |
| 9 | higgstools | none | BLOCKED | HIGGSTOOLS_SLHA_MISSING_BLOCKS |
| 10 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 11 | feynrules | validator | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 12 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 13 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 14 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |

##### Per-candidate routing

##### Candidate `V`

- **Field type:** vector
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `sigma_SI_V`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

##### Candidate `Psi`

- **Field type:** Dirac fermion
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `sigma_SI_Psi`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

#### Observable: `id`

**Status:** ROUTED

| Rank | Prereq | Role | Status | Blockers |
|------|--------|------|--------|----------|
| **1** | **analytic_backend** | escape_hatch | ROUTED | — |
| 2 | sarah-build | none | ROUTED | — |
| 3 | spheno-build | none | BLOCKED | SPHENO_NOT_REQUESTED |
| 4 | madgraph | none | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 5 | maddm | primary | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 6 | micromegas | none | BLOCKED | CALCHEP_MDL_MISSING |
| 7 | drake | none | BLOCKED | DRAKE_SINGLE_SPECIES_ONLY |
| 8 | ddcalc | none | ROUTED | — |
| 9 | higgstools | none | BLOCKED | HIGGSTOOLS_SLHA_MISSING_BLOCKS |
| 10 | analytic_backend | escape_hatch | BLOCKED | ANALYTIC_MODULE_MISSING |
| 11 | feynrules | validator | BLOCKED | MG5_DARK_COLOR_TENSOR_WALL |
| 12 | feynarts | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 13 | formcalc | none | BLOCKED | MATRIX_COVERAGE_GAP |
| 14 | looptools | none | BLOCKED | MATRIX_COVERAGE_GAP |

##### Per-candidate routing

##### Candidate `V`

- **Field type:** vector
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `Phi_id_V`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

##### Candidate `Psi`

- **Field type:** Dirac fermion
- **Mediator regime:** off-resonance
- **UV provenance:** analytic-only
- **Expected observable label:** `Phi_id_Psi`
- **Active chain:** `analytic_backend` (role: escape_hatch, status: ROUTED)

## Blockers on alternative chains (model-level)

The following matrix prereqs were ranked but bypassed by the analytic backend selection:

- `relic` / `sarah-build` (role: none, status: ROUTED) — blockers: —
- `relic` / `spheno-build` (role: none, status: BLOCKED) — blockers: SPHENO_NOT_REQUESTED
- `relic` / `madgraph` (role: none, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `relic` / `maddm` (role: primary, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `relic` / `micromegas` (role: validator, status: BLOCKED) — blockers: CALCHEP_MDL_MISSING
- `relic` / `drake` (role: specialty, status: BLOCKED) — blockers: DRAKE_SINGLE_SPECIES_ONLY
- `relic` / `ddcalc` (role: none, status: ROUTED) — blockers: —
- `relic` / `higgstools` (role: none, status: BLOCKED) — blockers: HIGGSTOOLS_SLHA_MISSING_BLOCKS
- `relic` / `analytic_backend` (role: escape_hatch, status: BLOCKED) — blockers: ANALYTIC_MODULE_MISSING
- `relic` / `feynrules` (role: validator, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `relic` / `feynarts` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `relic` / `formcalc` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `relic` / `looptools` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `dd` / `sarah-build` (role: none, status: ROUTED) — blockers: —
- `dd` / `spheno-build` (role: none, status: BLOCKED) — blockers: SPHENO_NOT_REQUESTED
- `dd` / `madgraph` (role: none, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `dd` / `maddm` (role: primary, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `dd` / `micromegas` (role: validator, status: BLOCKED) — blockers: CALCHEP_MDL_MISSING
- `dd` / `drake` (role: none, status: BLOCKED) — blockers: DRAKE_SINGLE_SPECIES_ONLY
- `dd` / `ddcalc` (role: primary, status: ROUTED) — blockers: —
- `dd` / `higgstools` (role: none, status: BLOCKED) — blockers: HIGGSTOOLS_SLHA_MISSING_BLOCKS
- `dd` / `analytic_backend` (role: escape_hatch, status: BLOCKED) — blockers: ANALYTIC_MODULE_MISSING
- `dd` / `feynrules` (role: validator, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `dd` / `feynarts` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `dd` / `formcalc` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `dd` / `looptools` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `id` / `sarah-build` (role: none, status: ROUTED) — blockers: —
- `id` / `spheno-build` (role: none, status: BLOCKED) — blockers: SPHENO_NOT_REQUESTED
- `id` / `madgraph` (role: none, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `id` / `maddm` (role: primary, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `id` / `micromegas` (role: none, status: BLOCKED) — blockers: CALCHEP_MDL_MISSING
- `id` / `drake` (role: none, status: BLOCKED) — blockers: DRAKE_SINGLE_SPECIES_ONLY
- `id` / `ddcalc` (role: none, status: ROUTED) — blockers: —
- `id` / `higgstools` (role: none, status: BLOCKED) — blockers: HIGGSTOOLS_SLHA_MISSING_BLOCKS
- `id` / `analytic_backend` (role: escape_hatch, status: BLOCKED) — blockers: ANALYTIC_MODULE_MISSING
- `id` / `feynrules` (role: validator, status: BLOCKED) — blockers: MG5_DARK_COLOR_TENSOR_WALL
- `id` / `feynarts` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `id` / `formcalc` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP
- `id` / `looptools` (role: none, status: BLOCKED) — blockers: MATRIX_COVERAGE_GAP

<!-- WS3:section=appendix -->

---
*Methodology: WS3 model-router v1. Routing decisions are derived from WS1 taxonomy axes, WS4 analytic-exception detection, and the WS2 capability matrix. Model: `dark-su3`. See `plugins/workflow/skills/model-router/SKILL.md` for ranking policy.*

<!-- WS3:section=inline -->