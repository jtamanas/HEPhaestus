# v1 Constraint & Loop-Integral Skills — TODO

**Goal:** bring the toolchain up to end-to-end coverage for the Arcadi–Profumo blind-spots paper (arXiv:2506.19062) and comparable BSM/DM phenomenology studies.

**Context:** SARAH, SPheno, MadGraph, and `/lagrangian-builder` landed 2026-04-19 (session). The existing Wolfram-Engine activation covers every Mathematica-based skill below — no extra licensing.

---

## Skills to add (6)

### Diagrams + symbolic amplitudes (Mathematica stack)
1. **`/feynarts`** — model-to-diagrams + amplitude generation. Consumes FeynArts model files (SARAH can emit them) and produces diagram PDFs + symbolic amplitude expressions.
2. **`/formcalc`** — algebraic simplification of FeynArts amplitudes: Dirac algebra, fermion-chain handling, tensor reduction to Passarino–Veltman functions. Emits Mathematica expressions or standalone Fortran.
3. **LoopTools** — numeric evaluation of Passarino–Veltman functions. Primary consumer of FormCalc output for the loop-level SI cross sections (paper Eqs. 9, 14, 23). Integrated via the FormCalc driver.

### Dark matter observables
4. **`/micromegas`** — relic density (Planck target Ωh²=0.120), tree-level σ_SI/σ_SD, annihilation channels, indirect-detection spectra. Consumes UFO (from W3 `/sarah-build`) + SLHA (from W4 `/spheno-build`).

### Experimental-limit overlays
5. **`/ddcalc`** — direct-detection likelihoods (LZ, XENONnT, PandaX, DarkSide) + neutrino-fog curves. Consumes σ_SI/σ_SD + DM mass from micrOMEGAs or the FormCalc + LoopTools loop chain.
6. **`/higgstools`** — HiggsBounds + HiggsSignals limits on extended Higgs sectors (2HDM, 2HDM+a). Consumes SPheno-format SLHA (already produced by W4).

---

## Ordering

- **Phase A (parallel):** `/micromegas`, `/ddcalc`, `/higgstools` — all three are SLHA/UFO consumers with no mutual dependencies. Pattern mirrors Wave A installers from the SARAH/SPheno build-out.
- **Phase B (sequential):** `/feynarts` → `/formcalc` (+ LoopTools) — each consumes the previous stage's output.
- **Phase C:** update `/lagrangian-builder` orchestrator to dispatch the new skills when the user asks for "relic density," "direct-detection exclusion," "Higgs constraints," or "one-loop scattering."

## Per-skill scope (sketch — expand in a spec before implementation)

Each skill follows the pattern established for `/sarah-install` … `/spheno-build`:

- `install` subcommand using `plugins/shared/install-helpers/_common.sh`.
- `detect | use-path <path> | install` subcommands for tools with an install step (micrOMEGAs, DDCalc, HiggsTools, FeynArts, FormCalc are all either Mathematica apps or small Fortran builds).
- Config keys under `~/.config/hep-ph-agents/config.json` with explicit version pins.
- Blockers per `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` (three-state: fatal / recoverable / reference_only).
- Tests gated on `HEPPH_RUN_NETWORK_TESTS=1` for anything requiring real tool execution.

## Open design questions (resolve in Phase-1-style brainstorm)

- Shared `plugins/constraints/` plugin or co-locate with `/model-building`?
- Should `/micromegas` install include the CalcHEP back-end it depends on, or gate on `/madgraph` having a UFO?
- Does the LoopTools integration need a state file for cached loop reductions, or is re-evaluation per call cheap enough?
- `/feynarts` model-file generation — from SARAH directly, or via an intermediate converter?

## Done-when

All six skills installed, registered in `plugins/*/.claude-plugin/plugin.json`, merged to local main.
