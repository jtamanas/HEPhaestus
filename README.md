# HEPhaestus

A Claude Code plugin marketplace for **high-energy physics phenomenology**,
named after the Greek god of the forge — Hephaestus wielded the existing
divine tools rather than rebuilding them, which is exactly how this project
treats FeynRules, SARAH, MadGraph, and the rest.

Skills and tools to help theorists draw Feynman diagrams, build BSM models,
compute one-loop amplitudes, drive Monte Carlo event generation, evaluate
dark-matter and Higgs constraints, and produce publication plots — all from
inside Claude Code.

## Guiding philosophy

**Augment the established hep-ph toolkit (FeynRules, SARAH, FeynArts, MadGraph,
MadDM, micrOMEGAs, Pythia, …) — do not replace it.** Each of those tools
encodes decades of validated craft (Feynman rules, color/Lorentz algebra,
phase-space integration, convention choices). Our job is to make those tools
*easier to drive* from a natural-language interface, while leaving room for
analytic-Python escape hatches where they make sense.

## Quick Start

```bash
# Add the marketplace
/plugin marketplace add github:jtamanas/hephaestus

# Install the toolkit and run the guided demo
/plugin install hep-ph-toolkit@hephaestus
/demo
```

The marketplace exposes a single plugin, **`hep-ph-toolkit`**, containing 37
skills. `/demo` walks you through the cold-start path (install MadGraph,
optionally install SARAH/SPheno, reproduce a benchmarked figure from
[arXiv:2506.19062](https://arxiv.org/abs/2506.19062)).

**Try this first:** `/demo` → pick **Singlet-Doublet** → relic-only — a ~3-minute
end-to-end run that exercises SARAH → SPheno → MadGraph → MadDM and reproduces
the paper's blind-spot figure.

## Skills

### Onboarding & demo
- **`/demo`** — Constraint-first front door to the blind-spot demo ([arXiv:2506.19062](https://arxiv.org/abs/2506.19062)). Picks a model and delegates to the per-model skill.
- **`/install`** — Directory and orchestrator for every toolkit installer. Groups tools into use-case bundles ("compute DM relic", "one-loop integrals", ...).
- **`/2hdm-a`** — Per-model workflow for 2HDM + pseudoscalar mediator ([arXiv:2506.19062](https://arxiv.org/abs/2506.19062) §III). Hand-crafted SARAH model → MadGraph → MadDM.
- **`/dark-su3`** — Per-model workflow for Dark SU(3) dark-Higgs benchmark (§IV). Vector V (tree-level SI) and pseudoscalar Ψ (exact blind spot); analytic-backend relic.
- **`/singlet-doublet`** — Per-model workflow for Singlet-Doublet fermion DM (§II). Drives `sarah-build` → `spheno-build` → `madgraph` → `maddm`.

### Feynman diagrams & one-loop amplitudes
- **`/draw-feynman`** — Generate diagrams in TikZ-Feynman, FeynMF, or ASCII.
- **`/feynarts`** + **`/feynarts-install`** — FeynArts 3.11 for diagram and amplitude generation; outputs `FeynAmpList.m`, diagrams PDF, topology JSON.
- **`/formcalc`** + **`/formcalc-install`** — FormCalc 9.10 (bundled with LoopTools 9.10 and FORM 4.3.1) to reduce FeynArts amplitudes; produces `amp_reduced.m` + `amp_reduced.meta.json`.
- **`/looptools-install`** — Build LoopTools from source (records the gfortran version used).
- **`/feynman-tikz`** — Render diagrams in TikZ-Feynman with the project's `hephaestus-tikz.sty` style package.

### BSM model building
- **`/lagrangian-builder`** — End-to-end pipeline: interview → ModelSpec → SARAH + SPheno → UFO + SLHA. Handles cold-start (Wolfram activation, SARAH install, model build, spectrum).
- **`/feynrules-install`** — FeynRules (UFO/FeynArts/CalcHEP/Sherpa exporter).
- **`/sarah-install`** + **`/sarah-build`** — Install SARAH; render SARAH `.m` files from a ModelSpec YAML and run SARAH headlessly.
- **`/spheno-install`** + **`/spheno-build`** — Build SPheno from gfortran source; compile a model-specific SPheno binary and run spectrum/RGE calculations.

### Constraints
- **`/dark-matter-constraints`** — Meta-skill: routes a DM question (relic / DD / ID) to MadDM, micrOMEGAs, or DRAKE; merges answers with caveats.
- **`/maddm`** + **`/maddm-install`** — MadDM relic density, DD/ID rates, parameter scans (runs inside an MG5 session).
- **`/micromegas`** + **`/micromegas-install`** — micrOMEGAs 6.0.5 for relic density, SI/SD nucleon cross-sections, annihilation spectra.
- **`/drake`** + **`/drake-install`** — DRAKE for relic density when ⟨σv⟩ Taylor expansion fails (resonances, kinetic decoupling, forbidden channels, Sommerfeld).
- **`/ddcalc`** + **`/ddcalc-install`** — DDCalc 2.2.0 direct-detection likelihoods and 90%-CL exclusion verdicts (consumes `scattering/v1` JSON).
- **`/higgstools`** + **`/higgstools-install`** — HiggsBounds-5 + HiggsSignals-2 against a model SLHA file (per-channel AND, Δχ² < 6.18, p-values).
- **`/gamlike`** — `MadDM_results.txt → gamlike/v1` JSON parser (v0 — parser only; pull computation v1+).

### Monte Carlo
- **`/madgraph`** — MadGraph5_aMC@NLO process generation, card writing, event generation, LHE parsing, parameter scans.
- **`/maddm`** + **`/maddm-install`** — see Constraints (MadDM is the MG5 DM plugin).

### Plotting
- **`/hep-plot`** — Distributions, stacked histograms, ratio panels, multi-panel figures with matplotlib + mplhep.
- **`/exclusion-contour`** — 2D BSM exclusion / discovery contours with observed, expected, and Brazil bands.
- **`/theory-data-comparison`** — Theory-vs-data overlays with uncertainty bands, pulls, χ².

### Workflow
- **`/model-router`** — Model-to-tool compatibility router. Maps a registered BSM model to reachable tool chains per observable; ranks by role; surfaces blockers.
- **`/analytic-exception-detector`** — Detects when a ModelSpec structurally requires the analytic-backend escape hatch and enforces user sign-off.

For the up-to-date inventory by category see [`CLAUDE.md`](CLAUDE.md). Skill
sources live in `plugins/hep-ph-toolkit/skills/<skill>/SKILL.md`.

## Coming soon

Skill stubs were removed because they only described workflow recipes without
real machinery. The use cases remain planned; each will return as a real skill
(with scripts, tests, and integration with the surrounding toolkit) rather
than a recipe-only placeholder.

| Planned skill | Will cover |
|---|---|
| `cross-section` | Hadronic σ at LO/NLO with PDF convolution and 7-point scale variation |
| `signal-background` | Cut-based and MVA collider analyses with cut-flow tables and significance |
| `rge-runner` | Standalone RGE running outside the SARAH pipeline (gauge unification, vacuum stability, perturbativity) |
| `amplitude-calc` | Tree-level squared-amplitude derivations (the FeynArts/FormCalc skills cover the loop case) |
| `pythia-config` | Pythia8 `.cmnd` configuration for parton showering, hadronization, decays |
| `root-analysis` | ROOT/PyROOT TTree processing, fitting, ATLAS/CMS-style plotting |
| `statistical-tools` | CLs limits, profile likelihood, asymptotic formulae (`pyhf`/`RooStats`) |
| `hep-paper-draft` | REVTeX/JHEP/EPJC paper scaffolding with HEP macros and bibliography |
| `arxiv-search` | Structured arXiv + INSPIRE-HEP queries with BibTeX output |
| `literature-review` | Annotated literature reviews with citation graphs |

Longer-term: detector simulation (Delphes/MadAnalysis), jet algorithms
(FastJet/RIVET), broader UFO-generation coverage (FeynRules / SARAH / LanHEP /
hand-authored), and a Whizard driver for lepton-collider work.

## License

Apache 2.0 — see [LICENSE](LICENSE).
