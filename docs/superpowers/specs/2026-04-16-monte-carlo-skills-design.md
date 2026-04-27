# Monte Carlo Tools Skills Redesign

## Summary

Redesign the `monte-carlo-tools` plugin to replace the thin `madgraph-helper` skill with a full `madgraph` Library & API Reference skill, and add a new `maddm` skill. Both follow Approach 2 (consolidated references, progressive disclosure) with scripts as composable library functions.

## Decisions

- **Plugin structure**: Umbrella — all skills stay under `plugins/monte-carlo-tools/`
- **Skill types**: Both are Library & API Reference (single type per skill)
- **Script pattern**: Library functions Claude composes per-task (not CLI executables)
- **MG5/MadDM boundary**: MadGraph covers the broad MG5 tool (generation + scanning + post-processing of MG5 output). MadDM covers specifically the MadDM plugin's relic/DD/ID workflows. Scanning and post-processing exist in both where relevant.
- **Reference depth**: Tiered progressive disclosure — lean SKILL.md with decision tree, detailed references in separate files loaded on-demand. Gotchas sections start as stubs and grow from real usage.
- **Pythia**: `pythia-config` stays unchanged for now

## Directory Structure

```
plugins/monte-carlo-tools/
├── .claude-plugin/plugin.json
├── README.md
└── skills/
    ├── madgraph/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── setup.md
    │   │   ├── generation.md
    │   │   └── analysis.md
    │   ├── scripts/
    │   │   ├── card_io.py
    │   │   ├── lhe_parser.py
    │   │   └── mg5_batch.py
    │   └── assets/
    │       └── example_cards/
    │           └── sm_ttbar/
    │               ├── proc_card.dat
    │               ├── param_card.dat
    │               └── run_card.dat
    ├── maddm/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── setup.md
    │   │   ├── observables.md
    │   │   └── scanning.md
    │   ├── scripts/
    │   │   ├── maddm_run.py
    │   │   ├── scan_grid.py
    │   │   └── limits.py
    │   └── assets/
    │       └── limit_data/
    │           └── README.md
    └── pythia-config/
        └── SKILL.md              # Unchanged
```

## Skill 1: madgraph

### SKILL.md (~200 lines)

Router that Claude loads on every invocation. Contains:

1. **Frontmatter** — name: `madgraph`, description triggers on MG5 process generation, card writing/editing, event generation, LHE parsing, parameter scans
2. **Overview** — MadGraph's role in the HEP MC chain, when to use this vs. pythia/maddm
3. **Decision tree** (flowchart) — "What are you trying to do?" routes to the right reference file:
   - Installing/configuring MG5 → `references/setup.md`
   - Defining processes or writing cards → `references/generation.md`
   - Parsing output or scanning parameters → `references/analysis.md`
4. **Quick-reference table** — most common process syntax patterns, key run_card fields, PDF set IDs (NNPDF4.0 NLO = 331100, etc.)
5. **Gotchas** — stub section, populated from real usage
6. **File map** — pointers to references/, scripts/, assets/

### references/setup.md

MG5 installation and environment:
- Source install, conda, Docker options
- Importing UFO models (from FeynRules model database, HEPMDB, GitHub repos)
- CUDACPP GPU backend: compilation requirements, supported processes
- Python/Fortran environment: required versions, common dependency issues
- Linking Pythia8 as shower plugin

### references/generation.md

The core MG5 workflow — process definition through event output:
- `generate` / `add process` syntax with examples
- Multiparticle labels (p, j, l+, l-, vl) and custom definitions
- Model import conventions (`import model <name>`, `import model <name>-<restriction>`)
- Excluding particles with `/` syntax
- proc_card.dat structure and best practices
- param_card.dat: SLHA block format, mass block, coupling blocks, BSM parameter blocks
- run_card.dat fields: beam config (`ebeam1`, `ebeam2`), nevents, PDF (`lhaid`), kinematic cuts (`ptj`, `ptl`, `etaj`, `drjj`, `mmll`), scale choices (`fixed_ren_scale`, `dynamical_scale_choice`), matching/merging (`ickkw`, `xqcut`)
- Launch workflow: `launch`, card replacement, multi-run
- NLO generation: `[QCD]`, `[QED]` syntax, MadLoop requirements

### references/analysis.md

Working with MG5 output:
- LHE XML structure: `<init>`, `<event>` blocks, weight info
- Banner files: extracting run metadata, cross-sections, input cards
- Parameter scanning: generating grids of param_card values, batch submission patterns, collecting and merging results across grid points
- Cross-section extraction from stdout and banner

### scripts/

Library functions Claude imports and composes:

**card_io.py**:
- `read_param_card(path) -> dict` — SLHA-aware parser, returns nested dict keyed by block/PID
- `write_param_card(card_dict, path)` — write back to SLHA format with comments
- `update_param(card, block, pid, value)` — modify a single parameter in-place
- `read_run_card(path) -> dict` — parse MG5 run_card format
- `update_run_card(card, key, value)` — modify a single run_card setting

**lhe_parser.py**:
- `parse_lhe(path) -> list[dict]` — parse events from LHE XML
- `extract_cross_section(path) -> (xsec, error)` — get cross-section from init block
- `event_kinematics(event) -> dict` — compute pT, eta, invariant masses from 4-vectors

**mg5_batch.py**:
- `generate_proc_card(processes, model, output_name) -> str` — build proc_card content
- `generate_launch_script(proc_card, param_card, run_card, nevents) -> str` — build bash launch script

### assets/example_cards/

**sm_ttbar/**: Complete working card set for SM pp -> tt~ at 13.6 TeV
- proc_card.dat, param_card.dat, run_card.dat
- Serves as a known-good reference for card format and field values

## Skill 2: maddm

### SKILL.md (~150 lines)

1. **Frontmatter** — name: `maddm`, description triggers on dark matter relic density, direct detection cross-sections, indirect detection rates, MadDM
2. **Overview** — MadDM as a MG5 plugin (not standalone), what it computes, relationship to the madgraph skill
3. **Decision tree** (flowchart):
   - Installing/configuring MadDM → `references/setup.md`
   - Computing relic density, SI/SD, or ID rates → `references/observables.md`
   - Running parameter scans or comparing to limits → `references/scanning.md`
4. **Quick-reference table** — key MadDM commands, observable names, common flags
5. **Gotchas** — stub
6. **File map**

### references/setup.md

- Installing MadDM via `install maddm` within MG5 session
- UFO model requirements: DM candidate particle, `DMParticle` flag, PDG ID conventions
- MadDM version compatibility with MG5 versions
- Required dependencies (numpy, scipy for numerical integration)

### references/observables.md

What MadDM computes and how:
- **Relic density**: freeze-out calculation, co-annihilation channels, Boltzmann equation settings, `relic_density` command
- **Direct detection**: SI and SD nucleon cross-sections, tree-level vs. loop-level (`loop` flag), nuclear form factors, hadronic matrix elements
- **Indirect detection**: velocity-averaged annihilation cross-section <sigma v>, channel-by-channel decomposition, velocity expansion settings (s-wave, p-wave)
- maddm_card.dat settings for each observable

### references/scanning.md

Parameter space exploration:
- Defining parameter grids in maddm_card.dat
- Batch orchestration: running MadDM across grid points, parallelization strategies
- Collecting and merging scan results
- Comparing against experimental limits: LUX-ZEPLIN, XENONnT (SI/SD), Fermi-LAT, MAGIC (indirect)
- Result format and post-processing

### scripts/

**maddm_run.py**:
- `generate_maddm_script(model, observables, params) -> str` — build MadDM session script
- `parse_maddm_output(path) -> dict` — extract computed observables from MadDM output

**scan_grid.py**:
- `make_grid(param_ranges, n_points) -> list[dict]` — generate parameter space grid
- `generate_batch(grid, template_script) -> list[str]` — create batch of MadDM scripts

**limits.py**:
- `load_limit(experiment, observable, data_dir) -> array` — load digitized exclusion curve from user-provided data files (see assets/limit_data/README.md for where to obtain them)
- `is_excluded(point, limit) -> bool` — check single point against limit
- `overlay_on_limit(results, limit) -> plot_data` — prepare data for exclusion plot overlay

### assets/limit_data/

**README.md**: Pointers to public data sources for experimental limits, not the data itself. Links to LZ, XENONnT, Fermi-LAT, MAGIC published limit tables and digitized data repositories.

## Cross-Skill Interactions

- **madgraph → pythia**: MG5 generates LHE → Pythia showers. madgraph's `generation.md` covers LHE output format; pythia-config covers LHE input. No overlap.
- **madgraph → maddm**: Share the MG5 runtime. MadDM's `setup.md` documents the plugin relationship. MadDM's scripts reference madgraph's `card_io.py` for param_card manipulation rather than duplicating the SLHA parser.

## What Gets Deleted

- `skills/madgraph-helper/SKILL.md` — replaced entirely by `skills/madgraph/`

## What Stays Unchanged

- `skills/pythia-config/SKILL.md`
- Everything in `eval/`
- Plugin-level `README.md` and `plugin.json` get updated to reflect new skill names
