---
name: madgraph
description: MadGraph5_aMC@NLO — process generation, card writing/editing, event generation, LHE parsing, parameter scans
---

# MadGraph

Full interface for MadGraph5_aMC@NLO (MG5): define processes, write cards, generate events, parse LHE output, and run parameter scans. Covers leading-order and next-to-leading-order generation with any UFO model.

MG5 is the starting point of the HEP Monte Carlo chain. It computes hard-process matrix elements and generates parton-level events in LHE format. Parton showering and hadronization of the LHE output is left to an external Pythia8 driver (a dedicated `pythia-config` skill is on the roadmap). For dark matter relic density and detection rates using a MG5 plugin, use the **maddm** skill.

## Preflight

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/madgraph/detect.sh

- **exit 0** → MadGraph is installed and registered in config; proceed.
- **exit non-zero** → MadGraph is missing or version-drifted. Load
  `plugins/hep-ph-toolkit/_shared/installs/madgraph/INSTALL.md` into context and follow it (or
  invoke `/install madgraph`). When the install completes, re-run
  `detect.sh` before proceeding. If it still fails, halt with the
  blocker code from the install reference.

## Decision Tree

**What are you trying to do?**

### Using a named hephaestus model?

If the user says `use <name>`, `/madgraph use dark_su3`, or `--model <name>`,
resolve registered paths before writing any MG5 script:

```bash
UFO  = python3 scripts/resolve_named_model.py <name> --key ufo
SLHA = python3 scripts/resolve_named_model.py <name> --key latest_slha
```

- If `UFO` is non-empty, use `import model <UFO>` in the generated MG5 script.
- If `SLHA` is non-empty, supply it as `param_card.dat` during `launch`.
- If the name is not registered (exit 1), fall through to the standard
  path-based flow below (ask the user to supply a UFO path directly).

**Example generated MG5 script** (passed as a script-file, NOT via `-c`):

```
# /tmp/dark_su3_run.mg5
import model /home/user/.local/share/hephaestus/models/dark_su3/ufo/DarkSU3
generate p p > psiD psiD~
output /tmp/dark_su3_out
launch /tmp/dark_su3_out
  /home/user/.local/share/hephaestus/models/dark_su3/latest_slha/LesHouches.out
  done
```

Invoke with:
```bash
mg5_aMC /tmp/dark_su3_run.mg5
```

See `references/generation.md` — "Named-model handoff" for the full callout.

---

### Install or configure MG5?

Read: `references/setup.md`

Covers: source install, conda, Docker options, importing UFO models (FeynRules, HEPMDB, GitHub), CUDACPP GPU backend compilation, Python/Fortran environment requirements, linking Pythia8 as a shower plugin.

### Define processes or write cards?

Read: `references/generation.md`

Covers: `generate` / `add process` syntax, multiparticle labels, model import conventions, excluding particles with `/` syntax, proc_card.dat structure, param_card.dat SLHA format, run_card.dat field reference, launch workflow, NLO generation with `[QCD]`/`[QED]` and MadLoop.

### Parse MG5 output or scan parameters?

Read: `references/analysis.md`

Covers: LHE XML structure (`<init>`, `<event>` blocks), banner files, cross-section extraction from stdout and banner, parameter scanning (generating param_card grids, batch submission, merging results).

## Quick Reference

### Common Process Syntax

| Process | MG5 syntax |
|---------|-----------|
| Drell-Yan | `generate p p > e+ e-` |
| tt̄ (LO) | `generate p p > t t~` |
| tt̄ (NLO QCD) | `generate p p > t t~ [QCD]` |
| W+jets (merged) | `generate p p > w+ j` then `add process p p > w+ j j` |
| Single top (t-ch) | `generate p p > t j $$ w+ w-` |
| Higgs via ggF | `generate g g > h [QCD]` |
| BSM stop pair | `import model mssm` then `generate p p > t1 t1~` |
| Exclude particle | `generate p p > t t~ / a` (no photon in s-channel) |
| Z+bb | `generate p p > z b b~` |
| 4-lepton | `generate p p > e+ e- mu+ mu-` |

Multiparticle labels (`p`, `j`, `l+`, `vl`, …) and the full `run_card`
field reference (beam, cuts, scale, matching) live in `references/generation.md`
— consult it when writing cards.

### PDF Set IDs (LHAPDF)

| PDF set | `lhaid` |
|---------|---------|
| NNPDF4.0 NLO (central) | `331100` |
| NNPDF4.0 NNLO (central) | `331300` |
| NNPDF3.1 NLO | `303200` |
| NNPDF3.1 NNLO | `303400` |
| CT18 NLO | `14000` |
| CT18 NNLO | `14200` |
| MSHT20 NLO | `27400` |
| MSHT20 NNLO | `27000` |

### Particle Name Map

| Particle | MG5 name | PDG ID |
|----------|----------|--------|
| electron | `e-` / `e+` | 11 |
| muon | `mu-` / `mu+` | 13 |
| tau | `ta-` / `ta+` | 15 |
| e-neutrino | `ve` / `ve~` | 12 |
| μ-neutrino | `vm` / `vm~` | 14 |
| τ-neutrino | `vt` / `vt~` | 16 |
| up | `u` / `u~` | 2 |
| down | `d` / `d~` | 1 |
| strange | `s` / `s~` | 3 |
| charm | `c` / `c~` | 4 |
| bottom | `b` / `b~` | 5 |
| top | `t` / `t~` | 6 |
| gluon | `g` | 21 |
| photon | `a` | 22 |
| Z boson | `z` | 23 |
| W boson | `w+` / `w-` | 24 |
| Higgs | `h` | 25 |

## Gotchas

Non-obvious UFO-import failure modes are catalogued in
[`references/mg5-model-import-gotchas.md`](references/mg5-model-import-gotchas.md):

1. **`import model <bare-name>` can silently resolve to a `$MG5_HOME/models/`
   stub** with a completely different particle set. Always pass the **absolute
   path** to the SARAH-output UFO (or `config.json`'s `models.<name>.ufo`), never
   the bare name.
2. **MG5 lowercases UFO particle names at import** (`Chi1` → `chi1`). Use the
   lowercased name in all MG5/MadDM commands — this is why the singlet-doublet
   workflow passes `dm_candidate = "chi1"`.

## File Map

| Path | Description |
|------|-------------|
| `references/setup.md` | Installation, environment, GPU backend, Pythia8 linking |
| `references/generation.md` | Process definition → event output, full card reference (multiparticle labels, run_card fields) |
| `references/analysis.md` | LHE parsing, scanning, cross-section extraction |
| `references/mg5-model-import-gotchas.md` | UFO-import failure modes (bare-name stub resolution, particle-name lowercasing) |
| `scripts/resolve_named_model.py` | Named-model resolver: looks up UFO/SLHA paths from config.json |
| `scripts/card_io.py` | SLHA param_card + run_card read/write/update functions |
| `scripts/lhe_parser.py` | LHE XML parser, cross-section extraction, kinematics |
| `scripts/mg5_batch.py` | proc_card content and bash launch script generation |
| `assets/example_cards/sm_ttbar/` | Known-good SM pp→tt̄ card set at 13.6 TeV NLO |
