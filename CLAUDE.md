# HEPhaestus

Claude Code plugin marketplace for high-energy physics phenomenology.

> **Note on naming:** The marketplace and brand are **HEPhaestus**; the
> slug is `hephaestus`. The env-var prefix `HEPPH_*` (HEP-phenomenology)
> names the *domain*, not the project, and is preserved.

## Structure

This marketplace exposes a single plugin, `hep-ph-toolkit`, located at `plugins/hep-ph-toolkit/`:
- `.claude-plugin/plugin.json` — plugin manifest
- `skills/<skill-name>/SKILL.md` — individual skill definitions (37 skills)
- `skills/_shared/` — cross-skill helpers (matrix lookup, blocker schema, taxonomy, etc.)
- `_shared/` — plugin-level install helpers (`installs/<tool>/`) and shared tests (`tests/`)
- `hooks/hooks.json` + `scripts/install-followup.sh` — post-install Stop hook
- `SHARED-feynman.md`, `SHARED-model-building.md` — cross-skill convention docs

`plugins/shared/` holds plugin-agnostic install helpers and JSON schemas.

The marketplace index is at `.claude-plugin/marketplace.json`.

## Conventions

- Skill names use kebab-case
- All physics notation follows standard HEP conventions (natural units, Einstein summation, etc.)
- LaTeX output should compile with standard `revtex4-2` or `jheppub` class files
- Code output for Monte Carlo tools should target the latest stable release of each tool
- When generating Feynman diagrams, prefer TikZ-Feynman unless the user specifies otherwise

## Skill Categories

| Category | Skills |
|----------|--------|
| Installs (reference) | `_shared/installs/<tool>/` for {class, ddcalc, drake, feynarts, feynrules, formcalc, higgstools, looptools, maddm, micromegas, sarah, spheno} — driven by runner-skill preflights and `/install` |
| Onboarding & demo | `2hdm-a`, `dark-su3`, `demo`, `install`, `singlet-doublet`, `_test_model_x` |
| Feynman / amplitudes | `draw-feynman`, `feynarts`, `formcalc` |
| BSM model building | `lagrangian-builder`, `sarah-build`, `spheno-build` |
| Constraints | `dark-matter-constraints`, `ddcalc`, `gamlike`, `higgstools`, `micromegas` |
| Cosmology | `class` |
| Monte Carlo | `drake`, `maddm`, `madgraph` |
| Publishing | `feynman-tikz` |
| Plotting | `exclusion-contour`, `hep-plot`, `theory-data-comparison` |
| Workflow | `analytic-exception-detector`, `model-router` |

Coming-soon categories (no skills yet; tracked in the README's "Coming soon" section): collider analysis (`cross-section`, `signal-background`), RGE running (`rge-runner`), tree-level amplitude calculation (`amplitude-calc`), parton-shower configuration (`pythia-config`), ROOT analysis (`root-analysis`), statistical inference (`statistical-tools`), LaTeX paper drafting (`hep-paper-draft`), arXiv/literature search (`arxiv-search`, `literature-review`).
