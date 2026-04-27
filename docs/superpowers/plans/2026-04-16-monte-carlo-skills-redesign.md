# Monte Carlo Skills Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the thin `madgraph-helper` skill with a full `madgraph` Library & API Reference skill and add a new `maddm` skill, both under the `monte-carlo-tools` plugin umbrella.

**Architecture:** Consolidated references with progressive disclosure. Each skill has a lean SKILL.md router that decision-trees users to detailed reference files. Python scripts are composable library functions (not CLI executables) that Claude imports and adapts per-task. MadDM scripts reuse the madgraph `card_io.py` SLHA parser rather than duplicating it.

**Tech Stack:** Python 3.10+, standard library only (except `numpy` for `limits.py`). Markdown for all documentation. SLHA format for param cards, MG5 run_card format, LHE XML for events.

---

## File Structure

All paths relative to `plugins/monte-carlo-tools/`:

```
skills/
├── madgraph/                          # NEW — replaces madgraph-helper/
│   ├── SKILL.md                       # Router (~200 lines)
│   ├── references/
│   │   ├── setup.md                   # Installation and environment
│   │   ├── generation.md              # Process definition → event output
│   │   └── analysis.md               # LHE parsing, scanning, cross-sections
│   ├── scripts/
│   │   ├── card_io.py                 # SLHA + run_card I/O
│   │   ├── lhe_parser.py             # LHE XML parser + kinematics
│   │   └── mg5_batch.py              # proc_card + launch script generation
│   └── assets/
│       └── example_cards/
│           └── sm_ttbar/
│               ├── proc_card.dat      # SM pp→tt̄ NLO
│               ├── param_card.dat     # SM parameters
│               └── run_card.dat       # 13.6 TeV, 100k events, NNPDF4.0
├── maddm/                             # NEW
│   ├── SKILL.md                       # Router (~150 lines)
│   ├── references/
│   │   ├── setup.md                   # MadDM installation
│   │   ├── observables.md             # Relic density, DD, ID
│   │   └── scanning.md               # Parameter scans + limits
│   ├── scripts/
│   │   ├── maddm_run.py              # Session scripting + output parsing
│   │   ├── scan_grid.py              # Grid generation + batch
│   │   └── limits.py                 # Exclusion curve comparison (needs numpy)
│   └── assets/
│       └── limit_data/
│           └── README.md              # Pointers to public data sources
├── pythia-config/
│   └── SKILL.md                       # UNCHANGED
└── madgraph-helper/                   # DELETE
    └── SKILL.md
```

**Also modified:**
- `.claude-plugin/plugin.json` — update skills list
- `README.md` — update documentation
- `../../.claude-plugin/marketplace.json` — update tags

## Parallelization Map

```
Parallel Group (all 11 tasks independent):
  T1: madgraph/SKILL.md
  T2: madgraph/references/ (3 files)
  T3: madgraph/scripts/card_io.py
  T4: madgraph/scripts/lhe_parser.py
  T5: madgraph/scripts/mg5_batch.py
  T6: madgraph/assets/example_cards/sm_ttbar/ (3 files)
  T7: maddm/SKILL.md
  T8: maddm/references/ + assets/ (4 files)
  T9: maddm/scripts/maddm_run.py
  T10: maddm/scripts/scan_grid.py
  T11: maddm/scripts/limits.py

Sequential (after all above):
  T12: Update plugin metadata + delete old skill
```

---

## Task 1: Create madgraph/SKILL.md

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/SKILL.md`

- [ ] **Step 1: Create the SKILL.md file**

```markdown
---
name: madgraph
description: MadGraph5_aMC@NLO — process generation, card writing/editing, event generation, LHE parsing, parameter scans
---

# MadGraph

Full interface for MadGraph5_aMC@NLO (MG5): define processes, write cards, generate events, parse LHE output, and run parameter scans. Covers leading-order and next-to-leading-order generation with any UFO model.

MG5 is the starting point of the HEP Monte Carlo chain. It computes hard-process matrix elements and generates parton-level events in LHE format. For parton showering and hadronization of the LHE output, hand it to **pythia-config**. For dark matter relic density and detection rates using a MG5 plugin, use the **maddm** skill.

## Decision Tree

**What are you trying to do?**

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

### Multiparticle Labels (default in SM)

| Label | Definition |
|-------|-----------|
| `p` | `g u c d s u~ c~ d~ s~` |
| `j` | `g u c d s u~ c~ d~ s~` |
| `l+` | `e+ mu+ ta+` |
| `l-` | `e- mu- ta-` |
| `vl` | `ve vm vt` |
| `vl~` | `ve~ vm~ vt~` |

### Key run_card Fields

| Field | Description | Example value |
|-------|-------------|---------------|
| `ebeam1` / `ebeam2` | Beam energies [GeV] | `6800` (13.6 TeV LHC) |
| `nevents` | Number of events | `100000` |
| `lhaid` | LHAPDF set ID | `331100` (NNPDF4.0 NLO) |
| `ptj` | Min jet pT cut [GeV] | `20.0` |
| `ptl` | Min lepton pT cut [GeV] | `10.0` |
| `etaj` / `etal` | Max jet/lepton \|η\| | `5.0` / `2.5` |
| `drjj` / `drll` | Min ΔR(j,j) / ΔR(l,l) | `0.4` / `0.4` |
| `mmll` | Min m(l+l−) [GeV] | `10.0` |
| `dynamical_scale_choice` | Scale choice | `-1` (default), `3` (HT/2) |
| `fixed_ren_scale` | Fixed μ_R | `.false.` |
| `fixed_fac_scale` | Fixed μ_F | `.false.` |
| `ickkw` | Matching scheme | `0` (none), `1` (MLM), `3` (FxFx) |
| `xqcut` | Matching scale [GeV] | `20.0` (for MLM) |
| `use_syst` | Systematics | `.true.` |

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

<!-- Populated from real usage — add entries here as edge cases are discovered -->

*No entries yet.*

## File Map

| Path | Description |
|------|-------------|
| `references/setup.md` | Installation, environment, GPU backend, Pythia8 linking |
| `references/generation.md` | Process definition → event output, full card reference |
| `references/analysis.md` | LHE parsing, scanning, cross-section extraction |
| `scripts/card_io.py` | SLHA param_card + run_card read/write/update functions |
| `scripts/lhe_parser.py` | LHE XML parser, cross-section extraction, kinematics |
| `scripts/mg5_batch.py` | proc_card content and bash launch script generation |
| `assets/example_cards/sm_ttbar/` | Known-good SM pp→tt̄ card set at 13.6 TeV NLO |
```

- [ ] **Step 2: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/SKILL.md
git commit -m "feat(madgraph): add SKILL.md router with decision tree and quick reference"
```

---

## Task 2: Create madgraph reference files

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/references/setup.md`
- Create: `plugins/monte-carlo-tools/skills/madgraph/references/generation.md`
- Create: `plugins/monte-carlo-tools/skills/madgraph/references/analysis.md`

- [ ] **Step 1: Create references/setup.md**

```markdown
# MadGraph Setup

Installation and environment configuration for MadGraph5_aMC@NLO.

## Installation Options

### Source install (recommended for development)

```bash
# Download latest release
wget https://launchpad.net/mg5amcnlo/3.0/3.6.x/+download/MG5_aMC_v3.6.0.tar.gz
tar xzf MG5_aMC_v3.6.0.tar.gz
cd MG5_aMC_v3_6_0

# Test the installation
python3 bin/mg5_aMC
# MG5_aMC> display version
```

### Conda

```bash
conda install -c conda-forge madgraph5amcatnlo
# Installs mg5_aMC on PATH
```

### Docker

```bash
docker pull scailfin/madgraph5-amc-nlo:latest
docker run -it -v $(pwd)/output:/work scailfin/madgraph5-amc-nlo
```

## Importing UFO Models

MG5 uses the Universal FeynRules Output (UFO) format for BSM models.

### From the FeynRules model database

Download the UFO tarball from https://feynrules.irmp.ucl.ac.be/wiki/ModelDatabaseMainPage and extract into the MG5 `models/` directory:

```bash
cd MG5_aMC_v3_6_0/models/
tar xzf /path/to/MyModel_UFO.tar.gz
```

Then in MG5:
```
import model MyModel
```

### From HEPMDB

The HEP Model Database (https://hepmdb.soton.ac.uk/) hosts validated UFO models. Download and extract the same way.

### From GitHub repositories

Many BSM models are hosted on GitHub. Clone into the models directory:

```bash
cd MG5_aMC_v3_6_0/models/
git clone https://github.com/author/model-ufo.git ModelName_UFO
```

### Model restrictions

Load a model with a restriction file (sets certain couplings to zero or unifies parameters):

```
import model sm-no_b_mass         # SM with massless b quark
import model mssm-full            # MSSM without any restrictions
import model 2hdm-type2           # 2HDM Type-II
```

Restriction files live in the model directory as `restrict_<name>.dat`.

## CUDACPP GPU Backend

MG5 supports GPU-accelerated matrix element evaluation via the CUDACPP backend (CUDA and C++ vectorized code).

### Requirements

- CUDA Toolkit 11.0+ (for NVIDIA GPUs) or C++17 compiler (for CPU vectorization)
- Supported process types: tree-level only (no loop processes)
- The `output` command must use the `standalone_cudacpp` plugin

### Compilation

```
# In MG5 session:
output standalone_cudacpp my_process
# Then compile:
cd my_process/SubProcesses/P1_xx_yy/
make -j$(nproc)
```

### Supported processes

CUDACPP works for any tree-level 2→N process. It does NOT support:
- NLO (loop) processes
- Processes requiring the MadLoop library
- Some models with non-standard Lorentz structures

## Python / Fortran Environment

### Python requirements

- Python 3.7+ (3.10+ recommended)
- `six` (usually bundled)
- `numpy` (optional, for analysis scripts)
- `f2py` / `gfortran` for Fortran compilation of matrix elements

### Fortran requirements

- `gfortran` 7+ or `ifort` 19+
- For NLO: `CutTools` and `IREGI` are bundled with MG5
- For NLO: `ninja` (optional, faster reduction) — install via `install ninja` in MG5

### Common issues

| Issue | Fix |
|-------|-----|
| `gfortran: command not found` | Install via `brew install gcc` (macOS) or `apt install gfortran` (Ubuntu) |
| `LHAPDF not found` | Install LHAPDF6 and set `lhapdf = /path/to/lhapdf-config` in `input/mg5_configuration.txt` |
| `Pythia8 not linked` | See Pythia8 section below |
| `f2py: command not found` | Install via `pip install numpy` (f2py is part of numpy) |

## Linking Pythia8 as Shower Plugin

MG5 can interface with Pythia8 for parton showering directly after event generation.

### Automatic install (within MG5)

```
MG5_aMC> install pythia8
```

This downloads and compiles Pythia8, then updates `input/mg5_configuration.txt`.

### Manual linking

Edit `input/mg5_configuration.txt`:

```
pythia8_path = /path/to/pythia8310
```

Pythia8 must be compiled with:

```bash
cd pythia8310
./configure --with-lhapdf6=/path/to/LHAPDF --with-hepmc2=/path/to/HepMC
make -j$(nproc)
```

### Verifying the link

```
MG5_aMC> launch my_process
# If Pythia8 is linked, MG5 will offer shower options during launch
```
```

- [ ] **Step 2: Create references/generation.md**

```markdown
# MadGraph Generation

The core MG5 workflow — from process definition through event output.

## Process Definition

### Basic syntax

```
generate <initial state> > <final state>
```

The `generate` command defines the primary process. Use `add process` for additional subprocesses (e.g., different jet multiplicities for matching):

```
generate p p > t t~
add process p p > t t~ j
add process p p > t t~ j j
```

### NLO syntax

Append `[QCD]` or `[QED]` to request next-to-leading-order corrections:

```
generate p p > t t~ [QCD]     # NLO QCD corrections to ttbar
generate p p > e+ e- [QED]    # NLO QED corrections to Drell-Yan
```

NLO requires MadLoop (bundled) and optionally `ninja` for faster tensor reduction. Install ninja:

```
MG5_aMC> install ninja
```

### Multiparticle labels

Default labels in the SM:

| Label | Definition |
|-------|-----------|
| `p` | `g u c d s u~ c~ d~ s~` |
| `j` | `g u c d s u~ c~ d~ s~` |
| `l+` | `e+ mu+ ta+` |
| `l-` | `e- mu- ta-` |
| `vl` | `ve vm vt` |
| `vl~` | `ve~ vm~ vt~` |

Define custom labels:

```
define ell = e+ e- mu+ mu-
generate p p > ell ell
```

### Model import

```
import model sm                    # Standard Model (default)
import model sm-no_b_mass          # SM with massless b quarks
import model mssm                  # MSSM with default restriction
import model mssm-full             # MSSM without restrictions
import model 2hdm-type2            # 2HDM Type-II
import model /path/to/MyModel_UFO  # Custom UFO model from path
```

Models with restrictions: the part after `-` is the restriction name, matching `restrict_<name>.dat` in the model directory.

### Excluding particles

Use `/` to exclude particles from internal propagators (s-channel):

```
generate p p > t t~ / a       # No photon in s-channel
generate p p > e+ e- / z      # Only photon exchange (no Z)
```

Use `$$` to exclude from all propagators (s-channel and t-channel):

```
generate p p > t j $$ w+ w-   # t-channel single top (no W propagators)
```

## Card Structure

### proc_card.dat

Defines the full process setup. Example for NLO tt̄:

```
import model sm
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
generate p p > t t~ [QCD]
output pp_ttbar_nlo
```

The `output` command creates the process directory with all needed code.

### param_card.dat

Sets physical parameters in SLHA (SUSY Les Houches Accord) block format. Each block contains numbered entries:

```
###################################
## INFORMATION FOR MASS
###################################
BLOCK MASS
      5  4.700000e+00  # MB
      6  1.725000e+02  # MT
     15  1.777000e+00  # MTA
     23  9.118760e+01  # MZ
     25  1.250000e+02  # MH

###################################
## INFORMATION FOR SMINPUTS
###################################
BLOCK SMINPUTS
     1  1.279000e+02  # aEWM1 (1/alpha_EW at MZ)
     2  1.166370e-05  # Gf (Fermi constant)
     3  1.180000e-01  # aS (alpha_s at MZ)
```

Key blocks:
- `MASS` — particle masses, keyed by PDG ID
- `SMINPUTS` — SM input parameters (α_EW⁻¹, G_F, α_s)
- `YUKAWA` — Yukawa couplings
- `DECAY` — particle widths and branching ratios
- For BSM: model-specific blocks (e.g., `NMIX`, `UMIX` for MSSM)

### run_card.dat

Configures the event generation run. Format: `value = parameter_name`:

```
100000 = nevents        ! Number of events
6800.0 = ebeam1         ! Beam 1 energy [GeV]
6800.0 = ebeam2         ! Beam 2 energy [GeV]
0      = lpp1           ! Beam 1 type (0=e, 1=p, -1=pbar)
1      = lpp1           ! Beam 1 type
1      = lpp2           ! Beam 2 type
331100 = lhaid          ! LHAPDF set ID
```

#### Beam configuration

| Field | Description |
|-------|-------------|
| `ebeam1`, `ebeam2` | Beam energies in GeV. For 13.6 TeV LHC: 6800 each |
| `lpp1`, `lpp2` | Beam type: 0 = electron/positron, 1 = proton, -1 = antiproton |
| `lhaid` | LHAPDF PDF set ID |

#### Kinematic cuts

| Field | Description | Typical value |
|-------|-------------|---------------|
| `ptj` | Min jet pT [GeV] | 20.0 |
| `ptl` | Min lepton pT [GeV] | 10.0 |
| `etaj` | Max jet \|η\| | 5.0 |
| `etal` | Max lepton \|η\| | 2.5 |
| `drjj` | Min ΔR(j,j) | 0.4 |
| `drll` | Min ΔR(l,l) | 0.4 |
| `drjl` | Min ΔR(j,l) | 0.4 |
| `mmll` | Min m(l+l−) [GeV] | 10.0 |
| `ptjmax`, `ptlmax` | Max pT cuts (use -1 for no cut) | -1 |

#### Scale choices

| Field | Description |
|-------|-------------|
| `fixed_ren_scale` | `.true.` = use `scale` value; `.false.` = dynamic |
| `fixed_fac_scale` | `.true.` = use `dsqrt_q2fact1` value; `.false.` = dynamic |
| `scale` | Fixed renormalization scale [GeV] |
| `dsqrt_q2fact1`, `dsqrt_q2fact2` | Fixed factorization scales [GeV] |
| `dynamical_scale_choice` | Dynamic scale: `-1` (default = sum of mass/pT), `1` (sqrt(ŝ)), `2` (sum of transverse mass), `3` (HT/2), `4` (HT/4) |
| `scalefact` | Multiplicative factor on dynamic scale | 1.0 |

#### Matching/merging (for multi-jet samples)

| Field | Description |
|-------|-------------|
| `ickkw` | `0` = no matching, `1` = MLM matching, `3` = FxFx merging (NLO) |
| `xqcut` | Matching scale [GeV] (MLM). Typically 20–30 GeV for LHC |
| `alpsfact` | α_s factor in CKKW scale | 1 |

## Launch Workflow

### Interactive launch

```
MG5_aMC> launch <process_dir>
```

MG5 will prompt:
1. Edit param_card? (1 = yes, enter = no)
2. Edit run_card? (2 = yes, enter = no)
3. Start generation

### Scripted launch (non-interactive)

Write commands to a file and pipe them:

```bash
cat << 'EOF' > launch_commands.txt
launch my_process
set nevents 100000
set ebeam1 6800
set ebeam2 6800
set lhaid 331100
done
EOF
python3 /path/to/mg5_aMC launch_commands.txt
```

### Card replacement

Replace cards entirely by specifying paths during launch:

```
launch my_process
/path/to/my_param_card.dat
/path/to/my_run_card.dat
done
```

MG5 identifies the card type by content, not by filename.

### Multi-run

Run the same process multiple times with different seeds:

```
launch my_process -n run_01
set iseed 12345
done
launch my_process -n run_02
set iseed 12346
done
```

Each run produces its own `Events/run_XX/` subdirectory.
```

- [ ] **Step 3: Create references/analysis.md**

```markdown
# MadGraph Analysis

Working with MG5 output: LHE parsing, banner files, cross-sections, and parameter scanning.

## LHE File Structure

MG5 produces Les Houches Event (LHE) files — XML format defined by the Les Houches Accord.

### Overall structure

```xml
<LesHouchesEvents version="3.0">
  <header>
    <!-- MG5 banner with input cards and run metadata -->
  </header>
  <init>
    <!-- Beam info, process cross-sections -->
    2212 2212 6.800000e+03 6.800000e+03 ...
    xsec  xerr  xmax  process_id
  </init>
  <event>
    <!-- Per-event: particle listing -->
    nparticles  proc_id  weight  scale  aqed  aqcd
    pdgid status mother1 mother2 color1 color2 px py pz energy mass lifetime spin
    ...
  </event>
  <!-- More <event> blocks -->
</LesHouchesEvents>
```

### `<init>` block

The first line has beam info:
```
IDBMUP(1) IDBMUP(2) EBMUP(1) EBMUP(2) PDFGUP(1) PDFGUP(2) PDFSUP(1) PDFSUP(2) IDWTUP NPRUP
```

Subsequent lines (one per subprocess):
```
XSECUP  XERRUP  XMAXUP  LPRUP
```

- `XSECUP` — cross-section in pb
- `XERRUP` — Monte Carlo integration error in pb
- `XMAXUP` — maximum weight
- `LPRUP` — subprocess ID

### `<event>` block

First line: `nparticles  process_id  weight  scale  alpha_QED  alpha_QCD`

Particle lines (one per particle):
```
PDG_ID  status  mother1  mother2  color1  color2  px  py  pz  energy  mass  lifetime  spin
```

Status codes:
- `-1` — initial state
- `1` — final state
- `2` — intermediate resonance

Momenta are in GeV, lifetime in mm/c.

## Banner Files

MG5 writes a banner file (`<run_name>_<tag>_banner.txt`) in the Events directory. It contains:

1. The input proc_card, param_card, and run_card (embedded verbatim)
2. Cross-section results
3. Run metadata (MG5 version, timestamp, random seed)

### Extracting info from banner

The banner is plain text with XML-like tags:

```
<MGGenerationInfo>
#  Number of Events        : 100000
#  Integrated weight (pb)  : 8.317e+02
</MGGenerationInfo>
```

Cross-section is in the `Integrated weight` line, in picobarns.

## Cross-Section Extraction

### From stdout

During generation, MG5 prints:
```
  === Results Summary for run: run_01 tag: tag_1 ===
     Cross-section :   831.7 +- 2.1 pb
     Nb of events  :   100000
```

### From LHE file

Use `scripts/lhe_parser.py`:

```python
from scripts.lhe_parser import extract_cross_section
xsec, error = extract_cross_section("Events/run_01/unweighted_events.lhe.gz")
print(f"σ = {xsec:.1f} ± {error:.1f} pb")
```

### From banner

```python
import re
with open("Events/run_01/run_01_tag_1_banner.txt") as f:
    banner = f.read()
match = re.search(r"Integrated weight \(pb\)\s*:\s*([\d.eE+-]+)", banner)
xsec_pb = float(match.group(1))
```

## Parameter Scanning

Systematic exploration of parameter space by generating events at multiple param_card points.

### Strategy

1. Define the parameter grid (which SLHA block entries to vary and their ranges)
2. Generate a param_card for each grid point
3. Run MG5 at each point (same proc_card and run_card)
4. Collect cross-sections and/or event files from each point

### Using scripts/card_io.py

```python
from scripts.card_io import read_param_card, update_param, write_param_card

base_card = read_param_card("param_card.dat")

# Scan top mass from 170 to 175 GeV in 6 steps
for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    card = dict(base_card)  # shallow copy (deep copy blocks if needed)
    update_param(card, "mass", 6, mt)
    write_param_card(card, f"param_card_mt{mt:.0f}.dat")
```

### Batch submission

Use `scripts/mg5_batch.py` to generate launch scripts for each grid point:

```python
from scripts.mg5_batch import generate_launch_script

for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    script = generate_launch_script(
        proc_dir="pp_ttbar",
        param_card=f"param_card_mt{mt:.0f}.dat",
        nevents=50000,
        seed=int(mt * 100),
        run_name=f"scan_mt{mt:.0f}",
    )
    with open(f"launch_mt{mt:.0f}.sh", "w") as f:
        f.write(script)
```

### Collecting results

After all runs complete, extract cross-sections:

```python
from scripts.lhe_parser import extract_cross_section

results = []
for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    lhe_path = f"pp_ttbar/Events/scan_mt{mt:.0f}/unweighted_events.lhe.gz"
    xsec, err = extract_cross_section(lhe_path)
    results.append({"mt": mt, "xsec": xsec, "error": err})
```
```

- [ ] **Step 4: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/references/
git commit -m "feat(madgraph): add reference docs for setup, generation, and analysis"
```

---

## Task 3: Create madgraph scripts/card_io.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/scripts/card_io.py`

- [ ] **Step 1: Create the card_io.py file**

```python
"""MadGraph card I/O utilities.

Read and write MadGraph param_card.dat (SLHA format) and run_card.dat files.
These are library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import re
from pathlib import Path


def read_param_card(path: str | Path) -> dict:
    """Parse an SLHA-format param_card.dat into a nested dict.

    Returns:
        Dict keyed by block name (lowercase). Each block is a dict
        mapping particle ID (int) or tuple of ints to float values.
        Special key '_decay' holds decay block entries.

    Example:
        card = read_param_card("param_card.dat")
        mt = card["mass"][6]          # top mass
        alpha_s = card["sminputs"][3] # alpha_s(MZ)
    """
    path = Path(path)
    card: dict = {}
    current_block = None

    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue

        block_match = re.match(r"block\s+(\w+)", line, re.IGNORECASE)
        if block_match:
            current_block = block_match.group(1).lower()
            card[current_block] = {}
            continue

        decay_match = re.match(
            r"decay\s+(-?\d+)\s+([\d.eE+-]+)", line, re.IGNORECASE
        )
        if decay_match:
            pid = int(decay_match.group(1))
            width = float(decay_match.group(2))
            card.setdefault("_decay", {})[pid] = {
                "width": width,
                "channels": [],
            }
            current_block = ("_decay", pid)
            continue

        if isinstance(current_block, tuple) and current_block[0] == "_decay":
            parts = line.split()
            if len(parts) >= 3:
                br = float(parts[0])
                n_daughters = int(parts[1])
                daughters = [int(p) for p in parts[2 : 2 + n_daughters]]
                card["_decay"][current_block[1]]["channels"].append(
                    {"br": br, "daughters": daughters}
                )
            continue

        if current_block and isinstance(current_block, str):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    if len(parts) == 2:
                        key = int(parts[0])
                        val = float(parts[1])
                    else:
                        key = tuple(int(p) for p in parts[:-1])
                        val = float(parts[-1])
                    card[current_block][key] = val
                except ValueError:
                    continue

    return card


def write_param_card(card: dict, path: str | Path) -> None:
    """Write a param_card dict back to SLHA format.

    Args:
        card: Dict as returned by read_param_card.
        path: Output file path.
    """
    path = Path(path)
    lines = []

    for block_name, entries in card.items():
        if block_name == "_decay":
            continue

        lines.append(f"BLOCK {block_name.upper()}")
        for key, val in sorted(
            entries.items(),
            key=lambda x: (x[0],) if isinstance(x[0], int) else x[0],
        ):
            if isinstance(key, tuple):
                key_str = "  ".join(f"{k:>4d}" for k in key)
            else:
                key_str = f"{key:>6d}"
            lines.append(f"  {key_str}  {val:16.8E}")
        lines.append("")

    if "_decay" in card:
        for pid, info in sorted(card["_decay"].items()):
            lines.append(f"DECAY  {pid:>6d}  {info['width']:16.8E}")
            for ch in info["channels"]:
                daughters_str = "  ".join(f"{d:>6d}" for d in ch["daughters"])
                lines.append(
                    f"  {ch['br']:16.8E}  {len(ch['daughters'])}  {daughters_str}"
                )
            lines.append("")

    path.write_text("\n".join(lines) + "\n")


def update_param(
    card: dict, block: str, pid: int | tuple[int, ...], value: float
) -> dict:
    """Modify a single parameter in a param_card dict in-place.

    Args:
        card: Dict as returned by read_param_card.
        block: Block name (case-insensitive, stored lowercase).
        pid: Particle ID or tuple of indices.
        value: New value.

    Returns:
        The modified card dict.

    Raises:
        KeyError: If block doesn't exist in the card.
    """
    block = block.lower()
    if block not in card:
        raise KeyError(
            f"Block '{block}' not found. Available: {list(card.keys())}"
        )
    card[block][pid] = value
    return card


def read_run_card(path: str | Path) -> dict:
    """Parse a MadGraph run_card.dat into a dict.

    MG5 run_card format: ``value = key  # comment``

    Returns:
        Dict mapping parameter names to values
        (auto-typed as int, float, bool, or str).

    Example:
        rc = read_run_card("run_card.dat")
        nevents = rc["nevents"]     # 100000
        ebeam1 = rc["ebeam1"]      # 6800.0
    """
    path = Path(path)
    card: dict = {}

    for line in path.read_text().splitlines():
        # Strip comments (! or #)
        for comment_char in ("#", "!"):
            line = line.split(comment_char)[0]
        line = line.strip()
        if not line or "=" not in line:
            continue

        parts = line.split("=", 1)
        if len(parts) != 2:
            continue

        value_str = parts[0].strip()
        key = parts[1].strip().split()[0]  # Take first word after =

        if value_str.lower() in (".true.", "true", "t"):
            value = True
        elif value_str.lower() in (".false.", "false", "f"):
            value = False
        else:
            try:
                value = int(value_str)
            except ValueError:
                try:
                    value = float(
                        value_str.replace("d", "e").replace("D", "E")
                    )
                except ValueError:
                    value = value_str

        card[key] = value

    return card


def update_run_card(card: dict, key: str, value) -> dict:
    """Modify a single run_card setting in-place.

    Args:
        card: Dict as returned by read_run_card.
        key: Parameter name.
        value: New value.

    Returns:
        The modified card dict.
    """
    card[key] = value
    return card
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/madgraph/scripts/card_io.py').read()); print('OK')"` from the repo root.

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/scripts/card_io.py
git commit -m "feat(madgraph): add card_io.py SLHA parser and run_card I/O"
```

---

## Task 4: Create madgraph scripts/lhe_parser.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/scripts/lhe_parser.py`

- [ ] **Step 1: Create the lhe_parser.py file**

```python
"""LHE (Les Houches Event) file parser.

Parse events from LHE XML files, extract cross-sections, and compute kinematics.
Library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import gzip
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def _open_lhe(path: str | Path):
    """Open an LHE file, handling .gz compression transparently."""
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt")
    return open(path, "r")


def parse_lhe(path: str | Path) -> list[dict]:
    """Parse events from an LHE XML file.

    Each event dict contains:
        - 'particles': list of particle dicts with keys:
            pdgid, status, mother1, mother2, color1, color2,
            px, py, pz, energy, mass, lifetime, spin
        - 'weight': event weight
        - 'scale': factorization scale
        - 'aqed': alpha_QED
        - 'aqcd': alpha_QCD

    Handles both plain .lhe and gzip-compressed .lhe.gz files.
    """
    with _open_lhe(path) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    events = []
    for event_elem in root.iter("event"):
        text = event_elem.text.strip()
        lines = [
            l.strip()
            for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        if not lines:
            continue

        header = lines[0].split()
        n_particles = int(header[0])
        event = {
            "weight": float(header[2]),
            "scale": float(header[3]),
            "aqed": float(header[4]),
            "aqcd": float(header[5]),
            "particles": [],
        }

        for i in range(1, min(n_particles + 1, len(lines))):
            parts = lines[i].split()
            if len(parts) < 13:
                continue
            event["particles"].append(
                {
                    "pdgid": int(parts[0]),
                    "status": int(parts[1]),
                    "mother1": int(parts[2]),
                    "mother2": int(parts[3]),
                    "color1": int(parts[4]),
                    "color2": int(parts[5]),
                    "px": float(parts[6]),
                    "py": float(parts[7]),
                    "pz": float(parts[8]),
                    "energy": float(parts[9]),
                    "mass": float(parts[10]),
                    "lifetime": float(parts[11]),
                    "spin": float(parts[12]),
                }
            )

        events.append(event)

    return events


def extract_cross_section(path: str | Path) -> tuple[float, float]:
    """Extract cross-section and error from the LHE <init> block.

    Returns:
        Tuple of (cross_section_pb, error_pb).
    """
    with _open_lhe(path) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    init_elem = root.find("init")
    if init_elem is None:
        raise ValueError(f"No <init> block found in {path}")

    text = init_elem.text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        raise ValueError(f"Malformed <init> block in {path}")

    # Second line: XSECUP XERRUP XMAXUP LPRUP
    parts = lines[1].split()
    return (float(parts[0]), float(parts[1]))


def event_kinematics(event: dict) -> dict:
    """Compute kinematic variables for final-state particles in an event.

    Returns dict with:
        - 'final_state': list of dicts with pdgid, pt, eta, phi, mass, rapidity
        - 'invariant_masses': dict of (i, j) -> m_ij for all final-state pairs
    """
    final = []
    for p in event["particles"]:
        if p["status"] != 1:
            continue

        px, py, pz, e = p["px"], p["py"], p["pz"], p["energy"]
        pt = math.sqrt(px**2 + py**2)

        p_mag = math.sqrt(px**2 + py**2 + pz**2)
        if p_mag > abs(pz):
            eta = 0.5 * math.log((p_mag + pz) / (p_mag - pz))
        else:
            eta = math.copysign(float("inf"), pz)

        phi = math.atan2(py, px)

        if e > abs(pz):
            rapidity = 0.5 * math.log((e + pz) / (e - pz))
        else:
            rapidity = math.copysign(float("inf"), pz)

        final.append(
            {
                "pdgid": p["pdgid"],
                "pt": pt,
                "eta": eta,
                "phi": phi,
                "mass": p["mass"],
                "rapidity": rapidity,
                "_4vec": (px, py, pz, e),
            }
        )

    inv_masses = {}
    for i in range(len(final)):
        for j in range(i + 1, len(final)):
            px = final[i]["_4vec"][0] + final[j]["_4vec"][0]
            py = final[i]["_4vec"][1] + final[j]["_4vec"][1]
            pz = final[i]["_4vec"][2] + final[j]["_4vec"][2]
            e = final[i]["_4vec"][3] + final[j]["_4vec"][3]
            m2 = e**2 - px**2 - py**2 - pz**2
            inv_masses[(i, j)] = math.sqrt(max(0.0, m2))

    for f in final:
        del f["_4vec"]

    return {"final_state": final, "invariant_masses": inv_masses}
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/madgraph/scripts/lhe_parser.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/scripts/lhe_parser.py
git commit -m "feat(madgraph): add lhe_parser.py for LHE XML parsing and kinematics"
```

---

## Task 5: Create madgraph scripts/mg5_batch.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/scripts/mg5_batch.py`

- [ ] **Step 1: Create the mg5_batch.py file**

```python
"""MadGraph5 batch scripting utilities.

Generate proc_card.dat content and bash launch scripts for MG5 runs.
Library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations


def generate_proc_card(
    processes: list[str],
    model: str = "sm",
    output_name: str = "output",
    multiparticle_defs: dict[str, str] | None = None,
) -> str:
    """Build proc_card.dat content.

    Args:
        processes: List of process strings. First becomes 'generate',
            rest become 'add process'.
            Example: ["p p > t t~", "p p > t t~ j"]
        model: Model name, e.g. 'sm', 'mssm', '2hdm', 'sm-no_b_mass'.
        output_name: Name for the MG5 output directory.
        multiparticle_defs: Optional extra multiparticle definitions.
            Example: {"vl": "ve vm vt", "vl~": "ve~ vm~ vt~"}

    Returns:
        Complete proc_card.dat content as a string.
    """
    lines = [f"import model {model}"]

    if multiparticle_defs:
        for name, definition in multiparticle_defs.items():
            lines.append(f"define {name} = {definition}")

    for i, proc in enumerate(processes):
        cmd = "generate" if i == 0 else "add process"
        lines.append(f"{cmd} {proc}")

    lines.append(f"output {output_name}")
    return "\n".join(lines) + "\n"


def generate_launch_script(
    proc_dir: str,
    param_card: str | None = None,
    run_card: str | None = None,
    nevents: int = 10000,
    seed: int = 0,
    run_name: str = "run_01",
) -> str:
    """Build a bash script that launches a MG5 run.

    Args:
        proc_dir: Path to the MG5 output directory.
        param_card: Path to custom param_card.dat (None = use default).
        run_card: Path to custom run_card.dat (None = use default).
        nevents: Number of events to generate.
        seed: Random seed (0 = automatic).
        run_name: Name tag for this run.

    Returns:
        Bash script content as a string.
    """
    mg5_lines = [
        f"launch {proc_dir}",
        f"  set nevents {nevents}",
        f"  set iseed {seed}",
        f"  set run_tag {run_name}",
    ]

    if param_card:
        mg5_lines.append(f"  {param_card}")
    if run_card:
        mg5_lines.append(f"  {run_card}")

    mg5_lines.append("done")
    mg5_script = "\n".join(mg5_lines)

    return f"""#!/usr/bin/env bash
# MadGraph5 launch script — generated by monte-carlo-tools
set -euo pipefail

MG5_DIR="${{MG5_DIR:-$(which mg5_aMC 2>/dev/null | xargs dirname)/..}}"
PROC_DIR="{proc_dir}"

MG5_CMD=$(mktemp /tmp/mg5_launch_XXXXXX.txt)
cat > "$MG5_CMD" << 'MG5EOF'
{mg5_script}
MG5EOF

echo "Launching MG5: $PROC_DIR (nevents={nevents}, seed={seed})"
python3 "$MG5_DIR/bin/mg5_aMC" "$MG5_CMD"

echo "Done. Output in: $PROC_DIR/Events/{run_name}/"
rm -f "$MG5_CMD"
"""
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/madgraph/scripts/mg5_batch.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/scripts/mg5_batch.py
git commit -m "feat(madgraph): add mg5_batch.py for proc_card and launch script generation"
```

---

## Task 6: Create madgraph example cards

**Files:**
- Create: `plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/proc_card.dat`
- Create: `plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/param_card.dat`
- Create: `plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/run_card.dat`

- [ ] **Step 1: Create proc_card.dat**

```
import model sm
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
generate p p > t t~ [QCD]
output pp_ttbar_nlo
```

- [ ] **Step 2: Create param_card.dat**

```
######################################################################
## PARAM_CARD — Standard Model
## Known-good reference for pp > t t~ at 13.6 TeV NLO
######################################################################

###################################
## INFORMATION FOR SMINPUTS
###################################
BLOCK SMINPUTS
      1  1.279000e+02  # aEWM1 (1/alpha_EW at MZ)
      2  1.166370e-05  # Gf (Fermi constant)
      3  1.180000e-01  # aS (alpha_s at MZ)

###################################
## INFORMATION FOR MASS
###################################
BLOCK MASS
      1  0.000000e+00  # MD (down)
      2  0.000000e+00  # MU (up)
      3  0.000000e+00  # MS (strange)
      4  1.270000e+00  # MC (charm)
      5  4.700000e+00  # MB (bottom)
      6  1.725000e+02  # MT (top)
     11  0.000000e+00  # Me
     13  0.000000e+00  # MMU
     15  1.777000e+00  # MTA
     23  9.118760e+01  # MZ
     24  8.039900e+01  # MW
     25  1.250000e+02  # MH

###################################
## INFORMATION FOR YUKAWA
###################################
BLOCK YUKAWA
      4  1.270000e+00  # ymc
      5  4.700000e+00  # ymb
      6  1.725000e+02  # ymt
     15  1.777000e+00  # ymtau

###################################
## INFORMATION FOR DECAY
###################################
DECAY   6  1.491500e+00  # WT (top width)
DECAY  23  2.441404e+00  # WZ
DECAY  24  2.047600e+00  # WW
DECAY  25  6.382339e-03  # WH
```

- [ ] **Step 3: Create run_card.dat**

```
#*********************************************************************
# run_card.dat — SM pp > t t~ at 13.6 TeV NLO
# Known-good reference configuration
#*********************************************************************
#
#*********************************************************************
# Tag name for the run
#*********************************************************************
  run_01 = run_tag
#
#*********************************************************************
# Number of events and calculation parameters
#*********************************************************************
  100000 = nevents          ! Number of unweighted events
       0 = iseed            ! Random seed (0=automatic)
#
#*********************************************************************
# Collider parameters
#*********************************************************************
     1   = lpp1             ! Beam 1 type (1=proton)
     1   = lpp2             ! Beam 2 type (1=proton)
  6800.0 = ebeam1           ! Beam 1 energy [GeV]
  6800.0 = ebeam2           ! Beam 2 energy [GeV]
#
#*********************************************************************
# PDF choice
#*********************************************************************
  331100 = lhaid            ! LHAPDF set ID (NNPDF4.0 NLO)
#
#*********************************************************************
# Renormalization and factorization scales
#*********************************************************************
 .false. = fixed_ren_scale  ! Use dynamic renormalization scale
 .false. = fixed_fac_scale  ! Use dynamic factorization scale
      -1 = dynamical_scale_choice ! Default MG5 dynamic scale
     1.0 = scalefact        ! Scale factor
#
#*********************************************************************
# Kinematic cuts
#*********************************************************************
  20.0 = ptj               ! Min jet pT [GeV]
  10.0 = ptl               ! Min lepton pT [GeV]
  -1.0 = ptjmax            ! Max jet pT (no cut)
  -1.0 = ptlmax            ! Max lepton pT (no cut)
   5.0 = etaj              ! Max jet |eta|
   2.5 = etal              ! Max lepton |eta|
   0.4 = drjj              ! Min delta R(j,j)
   0.4 = drll              ! Min delta R(l,l)
   0.4 = drjl              ! Min delta R(j,l)
  10.0 = mmll              ! Min m(l+l-) [GeV]
#
#*********************************************************************
# Matching / merging
#*********************************************************************
     0   = ickkw            ! No matching (pure NLO)
#
#*********************************************************************
# Systematics
#*********************************************************************
 .true.  = use_syst         ! Enable systematics
```

- [ ] **Step 4: Commit**

```bash
git add plugins/monte-carlo-tools/skills/madgraph/assets/
git commit -m "feat(madgraph): add SM pp→tt̄ example card set (13.6 TeV NLO)"
```

---

## Task 7: Create maddm/SKILL.md

**Files:**
- Create: `plugins/monte-carlo-tools/skills/maddm/SKILL.md`

- [ ] **Step 1: Create the SKILL.md file**

```markdown
---
name: maddm
description: MadDM — dark matter relic density, direct detection cross-sections, indirect detection rates, parameter scans with experimental limit comparison
---

# MadDM

Interface for MadDM, a MadGraph5 plugin for dark matter phenomenology. Computes relic density (Omega h^2), spin-independent and spin-dependent nucleon cross-sections, and velocity-averaged annihilation cross-sections <sigma v>.

MadDM runs within a MG5 session — it is not a standalone tool. It requires a UFO model with a designated dark matter candidate. For the underlying MG5 setup and card manipulation, see the **madgraph** skill. For parton showering of MG5 events, see **pythia-config**.

## Decision Tree

**What are you trying to do?**

### Install MadDM or set up a DM model?

Read: `references/setup.md`

Covers: `install maddm` command within MG5, UFO model requirements for DM candidates (PDG ID conventions, `DMParticle` flag), MadDM version compatibility with MG5 versions, required Python dependencies (numpy, scipy).

### Compute relic density, direct detection, or indirect detection?

Read: `references/observables.md`

Covers: freeze-out relic density calculation with co-annihilation, SI and SD nucleon cross-sections (tree-level and loop), velocity-averaged annihilation cross-section with channel decomposition (s-wave, p-wave), maddm_card.dat settings for each observable.

### Run parameter scans or compare to experimental limits?

Read: `references/scanning.md`

Covers: defining parameter grids in maddm_card.dat, batch orchestration and parallelization, collecting and merging results, comparing against LUX-ZEPLIN, XENONnT, PICO-60 (direct), Fermi-LAT, MAGIC (indirect).

## Quick Reference

### Key Commands

| Command | Description |
|---------|-------------|
| `install maddm` | Install MadDM plugin in MG5 session |
| `import model <name>` | Load UFO model with DM candidate |
| `generate_maddm` | Initialize MadDM for current model |
| `launch` | Run computation with current settings |
| `set relic_density ON/OFF` | Toggle Omega h^2 calculation |
| `set direct_detection ON/OFF` | Toggle SI/SD cross-sections |
| `set indirect_detection ON/OFF` | Toggle <sigma v> calculation |

### Observable Summary

| Observable | Symbol | Units | Experimental reference |
|-----------|--------|-------|----------------------|
| Relic density | Omega h^2 | dimensionless | 0.1200 +/- 0.0012 (Planck 2018) |
| SI proton xsec | sigma_SI^p | cm^2 | ~10^-47 at 30 GeV (LZ 2022) |
| SD proton xsec | sigma_SD^p | cm^2 | ~10^-42 (PICO-60) |
| Annihilation xsec | <sigma v> | cm^3/s | ~3e-26 (thermal relic) |

### Common DM UFO Models

| Model | Description | DM candidate (PDG ID) |
|-------|-------------|----------------------|
| `DMsimp_s_spin0` | Simplified, scalar mediator | chi (9000006) |
| `DMsimp_s_spin1` | Simplified, vector mediator | chi (9000006) |
| `DMscalar` | Real scalar DM + Higgs portal | S (9000006) |
| `Inert_Doublet` | Inert doublet model | H0 (35) |
| `MSSM_SLHA2` | MSSM (neutralino DM) | n1 (1000022) |

### Key maddm_card.dat Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `dm_candidate` | PDG ID of DM particle | auto-detected |
| `relic_density` | Compute Omega h^2 | ON |
| `direct_detection` | Compute sigma_SI, sigma_SD | OFF |
| `indirect_detection` | Compute <sigma v> | OFF |
| `loop` | Include loop corrections for DD | OFF |
| `sigmav_method` | `madevent` or `reshuffling` | `madevent` |

## Gotchas

<!-- Populated from real usage — add entries here as edge cases are discovered -->

*No entries yet.*

## File Map

| Path | Description |
|------|-------------|
| `references/setup.md` | MadDM installation and UFO model requirements |
| `references/observables.md` | Relic density, DD, ID computation details |
| `references/scanning.md` | Parameter scans and experimental limit comparison |
| `scripts/maddm_run.py` | MadDM session scripting and output parsing |
| `scripts/scan_grid.py` | Grid generation and batch orchestration |
| `scripts/limits.py` | Experimental exclusion curve loading and comparison |
| `assets/limit_data/README.md` | Pointers to public experimental limit data |

### Cross-Skill Dependencies

- **param_card manipulation**: Use `madgraph/scripts/card_io.py` — the SLHA parser is shared, not duplicated.
- **MG5 process generation**: If you need to generate DM signal events (not just compute observables), use the **madgraph** skill for process definition and the **maddm** skill for the DM-specific observables.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/monte-carlo-tools/skills/maddm/SKILL.md
git commit -m "feat(maddm): add SKILL.md router with decision tree and quick reference"
```

---

## Task 8: Create maddm reference files and limit_data README

**Files:**
- Create: `plugins/monte-carlo-tools/skills/maddm/references/setup.md`
- Create: `plugins/monte-carlo-tools/skills/maddm/references/observables.md`
- Create: `plugins/monte-carlo-tools/skills/maddm/references/scanning.md`
- Create: `plugins/monte-carlo-tools/skills/maddm/assets/limit_data/README.md`

- [ ] **Step 1: Create references/setup.md**

```markdown
# MadDM Setup

Installation and model configuration for MadDM.

## Installing MadDM

MadDM is a plugin for MadGraph5. Install it from within a MG5 session:

```
MG5_aMC> install maddm
```

This downloads and installs the latest compatible MadDM version. The plugin is stored in `<MG5_DIR>/HEPTools/maddm/`.

### Version Compatibility

| MG5 version | MadDM version | Notes |
|-------------|--------------|-------|
| 3.5.x | 3.2 | Stable, well-tested |
| 3.6.x | 3.2 | Latest recommended combination |
| 3.4.x | 3.1 | Older but functional |

### Dependencies

MadDM requires:
- Python 3.7+ with `numpy` and `scipy` (for numerical Boltzmann equation integration)
- MG5 with a working Fortran compiler (same requirements as standard MG5)
- LHAPDF (optional, for PDF-dependent calculations)

Install Python dependencies:
```bash
pip install numpy scipy
```

## UFO Model Requirements

MadDM requires a UFO model that defines a dark matter candidate.

### DM Candidate Specification

The model must have a particle flagged as the DM candidate. MadDM auto-detects the lightest stable neutral particle under the model's symmetry (typically Z2).

If the model has multiple possible DM candidates, specify explicitly:
```
set dm_candidate 9000006
```

### PDG ID Conventions for DM Models

| Model family | DM PDG ID | Mediator PDG ID |
|-------------|-----------|-----------------|
| Simplified (DMsimp) | 9000006 (chi) | 9000005 (Y0/Y1) |
| Scalar DM | 9000006 (S) | — (Higgs portal) |
| Inert doublet | 35 (H0) | 36 (A0), 37 (H+) |
| MSSM | 1000022 (neutralino) | various |
| Singlet-doublet | 9000007 | 9000008 |

### Model Validation

Before running MadDM, verify the model:

```
MG5_aMC> import model DMsimp_s_spin0
MG5_aMC> display particles
```

Check that:
1. The DM candidate particle exists with the expected PDG ID
2. The particle is self-conjugate or has a defined antiparticle
3. The model conserves the stabilizing symmetry (Z2, etc.)

### Installing Models for MadDM

Same as standard MG5 — see `madgraph/references/setup.md` for UFO model installation instructions. The most common DM simplified models are available from the DMsimp repository:

```bash
cd MG5_aMC_v3_6_0/models/
# Download from FeynRules or GitHub
```

Popular pre-built models:
- **DMsimp_s_spin0**: Scalar mediator, Dirac fermion DM
- **DMsimp_s_spin1**: Vector mediator, Dirac fermion DM
- **DMsimp_s_spin2**: Spin-2 mediator (graviton-like)
- **DMscalar**: Real scalar DM with Higgs portal
- **Inert_Doublet**: Inert two-Higgs-doublet model
```

- [ ] **Step 2: Create references/observables.md**

```markdown
# MadDM Observables

What MadDM computes and how to configure each observable.

## Relic Density

MadDM computes the thermal relic density Omega h^2 by solving the Boltzmann equation for DM freeze-out.

### How it works

1. MadDM generates all relevant annihilation diagrams for the DM candidate
2. Computes thermally-averaged annihilation cross-section <sigma v> as a function of temperature
3. Solves the Boltzmann equation numerically to get the freeze-out abundance
4. Reports Omega h^2 (compare to Planck: 0.1200 +/- 0.0012)

### Co-annihilation

If other BSM particles have masses within ~20% of the DM mass, co-annihilation channels are automatically included. MadDM detects these particles and includes their contributions.

### Configuration

In maddm_card.dat or via `set` commands:

```
set relic_density ON
```

Key settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `relic_density` | Enable calculation | ON |
| `fast_mode` | Skip higher-order contributions for speed | OFF |
| `x_freeze` | Freeze-out parameter x_f = m_DM/T_f | auto |

### Output

```
Omega h^2 = 0.1198
x_freeze = 25.3
```

## Direct Detection

MadDM computes spin-independent (SI) and spin-dependent (SD) DM-nucleon cross-sections.

### Spin-Independent (SI)

SI scattering proceeds through scalar (Higgs-like) or vector mediator exchange. The cross-section is coherently enhanced by the nuclear mass number A^2.

### Spin-Dependent (SD)

SD scattering proceeds through axial-vector exchange. Only couples to the nuclear spin — no A^2 enhancement, but sensitive to different couplings.

### Tree-Level vs. Loop

By default, MadDM computes tree-level cross-sections. For models where tree-level DD vanishes (e.g., pseudoscalar mediator), enable loop corrections:

```
set direct_detection ON
set loop ON
```

Loop calculation is significantly slower but necessary for:
- Pseudoscalar mediators (tree-level SI vanishes)
- Models with momentum-suppressed operators
- Precision comparison with experiments

### Nuclear Form Factors and Hadronic Matrix Elements

MadDM uses standard values for hadronic matrix elements:

| Parameter | Default value | Description |
|-----------|--------------|-------------|
| f_Tu | 0.0153 | Up quark contribution to proton mass |
| f_Td | 0.0191 | Down quark contribution to proton mass |
| f_Ts | 0.0447 | Strange quark contribution to proton mass |
| Delta_u^p | 0.842 | Proton spin from up quarks |
| Delta_d^p | -0.427 | Proton spin from down quarks |
| Delta_s^p | -0.085 | Proton spin from strange quarks |

These can be overridden in the maddm_card.dat if newer lattice values are available.

### Configuration

```
set direct_detection ON
set loop OFF               # Tree-level only (default)
```

### Output

```
sigma_SI (proton)  = 1.23e-46 cm^2
sigma_SI (neutron) = 1.19e-46 cm^2
sigma_SD (proton)  = 4.56e-42 cm^2
sigma_SD (neutron) = 3.89e-42 cm^2
```

## Indirect Detection

MadDM computes the velocity-averaged annihilation cross-section <sigma v> at present-day velocities (v ~ 10^-3 c), relevant for indirect DM searches.

### What it computes

- Total <sigma v> summed over all channels
- Channel-by-channel decomposition (e.g., chi chi -> b b~, chi chi -> W+ W-, etc.)
- Velocity expansion: s-wave (v^0) and p-wave (v^2) contributions

### Velocity Expansion

| Term | Velocity dependence | When important |
|------|-------------------|----------------|
| s-wave | constant | Most channels |
| p-wave | proportional to v^2 | Majorana DM to fermion pairs via scalar mediator |

For indirect detection at the galactic center (v ~ 10^-3 c), p-wave contributions are heavily suppressed compared to freeze-out (v ~ 0.3 c).

### Configuration

```
set indirect_detection ON
set sigmav_method madevent   # Full matrix element (default)
```

The `sigmav_method` options:
- `madevent`: Full matrix element calculation (slower, more accurate)
- `reshuffling`: Approximate method using relic density calculation (faster)

### Output

```
<sigma v> (total) = 2.98e-26 cm^3/s
  chi chi > b b~     : 7.45e-27 cm^3/s  (25.0%)
  chi chi > W+ W-    : 1.49e-26 cm^3/s  (50.0%)
  chi chi > t t~     : 7.45e-27 cm^3/s  (25.0%)
```

## maddm_card.dat Reference

Complete settings reference:

```
######################################################################
## maddm_card.dat
######################################################################

# Observables
ON   = relic_density         # Compute Omega h^2
OFF  = direct_detection      # Compute sigma_SI, sigma_SD
OFF  = indirect_detection    # Compute <sigma v>

# Direct detection options
OFF  = loop                  # Loop-level DD (slow but needed for pseudoscalar)

# Indirect detection options
madevent = sigmav_method     # 'madevent' or 'reshuffling'

# Numerical settings
auto = x_freeze              # Freeze-out x_f = m_DM/T_f
OFF  = fast_mode             # Skip subdominant contributions
```
```

- [ ] **Step 3: Create references/scanning.md**

```markdown
# MadDM Parameter Scanning

Systematic exploration of BSM parameter space with MadDM.

## Defining Parameter Grids

### Using scan_grid.py

The `scripts/scan_grid.py` module generates parameter grids:

```python
from scripts.scan_grid import make_grid

# Scan DM mass vs. coupling
grid = make_grid({
    "MASS:9000006": (10.0, 1000.0, 50),     # DM mass: 10–1000 GeV, 50 points
    "DMINPUTS:1": (0.01, 4.0, 20),           # Coupling: 0.01–4.0, 20 points
}, spacing="log")  # Log spacing for mass, linear also available

print(f"Total grid points: {len(grid)}")  # 50 * 20 = 1000
```

### Spacing options

- `linear`: Uniform spacing between min and max
- `log`: Logarithmic spacing (requires positive min/max) — preferred for mass scans spanning orders of magnitude

## Batch Orchestration

### Generating batch scripts

Use `maddm_run.py` and `scan_grid.py` together:

```python
from scripts.maddm_run import generate_maddm_script
from scripts.scan_grid import make_grid, generate_batch

# Define the grid
grid = make_grid({
    "MASS:9000006": (10.0, 1000.0, 50),
    "DMINPUTS:1": (0.01, 4.0, 20),
}, spacing="log")

# Create a template script
template = generate_maddm_script(
    model="DMsimp_s_spin0",
    observables=["relic", "direct_detection"],
    params={"MASS:9000006": 100.0, "DMINPUTS:1": 1.0},  # placeholder values
)

# Generate one script per grid point
scripts = generate_batch(grid, template)

# Write to disk
for i, script in enumerate(scripts):
    with open(f"scan/point_{i:04d}.mg5", "w") as f:
        f.write(script)
```

### Parallelization strategies

**Sequential (simple)**:
```bash
for f in scan/point_*.mg5; do
    python3 "$MG5_DIR/bin/mg5_aMC" "$f"
done
```

**GNU Parallel**:
```bash
ls scan/point_*.mg5 | parallel -j 8 python3 "$MG5_DIR/bin/mg5_aMC" {}
```

**Cluster submission (HTCondor/SLURM)**:
Generate a job submission script per grid point, or use an array job:

```bash
# SLURM array job
#SBATCH --array=0-999
python3 "$MG5_DIR/bin/mg5_aMC" "scan/point_$(printf '%04d' $SLURM_ARRAY_TASK_ID).mg5"
```

## Collecting and Merging Results

### Parsing output

After all grid points complete, extract results:

```python
from scripts.maddm_run import parse_maddm_output

results = []
for i, point in enumerate(grid):
    output_dir = f"scan/output_{i:04d}"
    obs = parse_maddm_output(output_dir)
    obs.update(point)  # Merge parameter values with observables
    results.append(obs)
```

### Result format

Each result dict contains the grid point parameters plus computed observables:

```python
{
    "MASS:9000006": 100.0,
    "DMINPUTS:1": 1.0,
    "omega_h2": 0.12,
    "sigma_si_proton": 1.23e-46,
    "sigma_sd_proton": 4.56e-42,
}
```

### Saving to CSV

```python
import csv

fieldnames = list(results[0].keys())
with open("scan_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
```

## Comparing Against Experimental Limits

### Loading limit data

Use `scripts/limits.py`:

```python
from scripts.limits import load_limit, is_excluded, overlay_on_limit

# Load the LZ SI limit
lz_limit = load_limit("LZ", "SI", data_dir="assets/limit_data/")
```

Limit files are CSV with columns: `mass_GeV, limit_value`. See `assets/limit_data/README.md` for where to obtain them.

### Checking exclusion

```python
# Check a single point
point = {"mass": 100.0, "value": 1.23e-46}
print(is_excluded(point, lz_limit))  # True or False

# Check all scan results
for r in results:
    r["excluded_LZ"] = is_excluded(
        {"mass": r["MASS:9000006"], "value": r["sigma_si_proton"]},
        lz_limit,
    )
```

### Preparing exclusion plots

```python
plot_data = overlay_on_limit(
    [{"mass": r["MASS:9000006"], "value": r["sigma_si_proton"]} for r in results],
    lz_limit,
)

# plot_data contains: limit_mass, limit_value, allowed_mass, allowed_value,
#                     excluded_mass, excluded_value
# Feed to matplotlib or the hep-plotting plugin for visualization
```

### Available Experiments

#### Direct detection (SI)

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| LZ (LUX-ZEPLIN) | SI | Phys. Rev. Lett. 131, 041002 (2023) |
| XENONnT | SI | Phys. Rev. Lett. 131, 041003 (2023) |
| PandaX-4T | SI | Phys. Rev. Lett. 127, 261802 (2021) |

#### Direct detection (SD)

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| PICO-60 | SD (proton) | Phys. Rev. D 100, 022001 (2019) |
| LZ | SD (neutron) | Phys. Rev. Lett. 131, 041002 (2023) |

#### Indirect detection

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| Fermi-LAT | <sigma v> (bb, WW, tautau channels) | Phys. Rev. Lett. 115, 231301 (2015) |
| MAGIC | <sigma v> (dSphs) | JCAP 02, 039 (2016) |
| H.E.S.S. | <sigma v> (GC) | Phys. Rev. Lett. 117, 111301 (2016) |
```

- [ ] **Step 4: Create assets/limit_data/README.md**

```markdown
# Experimental Limit Data

This directory is for user-provided digitized exclusion curves. The limit data files are **not bundled** — download them from the public sources below.

## Expected File Format

CSV files with two columns, no header row:

```
# mass_GeV, limit_value
10.0, 1.0e-43
20.0, 5.0e-45
50.0, 1.2e-46
...
```

- Mass in GeV
- SI/SD limits in cm^2
- <sigma v> limits in cm^3/s
- Lines starting with `#` are treated as comments

## File Naming Convention

```
{Experiment}_{Observable}.csv
```

Examples: `LZ_SI.csv`, `XENONnT_SI.csv`, `FermiLAT_sigmav_bb.csv`, `PICO60_SD.csv`

## Where to Get Limit Data

### Direct Detection

- **LZ (LUX-ZEPLIN)**: Data release at https://lz.lbl.gov/results/ — download the 90% CL upper limit table
- **XENONnT**: Data at https://xenonnt.org/results — published limit tables in supplementary materials
- **PandaX-4T**: Supplementary data in Phys. Rev. Lett. 127, 261802 (2021)

### Indirect Detection

- **Fermi-LAT**: Limit tables in supplementary materials of Phys. Rev. Lett. 115, 231301 (2015). Also available via the Fermi Science Support Center.
- **MAGIC**: Published limits in JCAP 02, 039 (2016), supplementary tables
- **H.E.S.S.**: Published limits in Phys. Rev. Lett. 117, 111301 (2016)

### Digitized Limit Repositories

- **HEPData**: https://www.hepdata.net/ — many experimental results include digitized limit curves
- **GAMBIT DarkBit**: https://github.com/GambitBSM — includes digitized limit data for many experiments
- **DDCalc**: https://github.com/GambitBSM/DDCalc — direct detection limit data and calculator

## Usage

```python
from scripts.limits import load_limit

# Place your downloaded CSV in this directory, then:
lz = load_limit("LZ", "SI", data_dir="path/to/this/directory")
```
```

- [ ] **Step 5: Commit**

```bash
git add plugins/monte-carlo-tools/skills/maddm/references/ plugins/monte-carlo-tools/skills/maddm/assets/
git commit -m "feat(maddm): add reference docs for setup, observables, scanning, and limit data sources"
```

---

## Task 9: Create maddm scripts/maddm_run.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py`

- [ ] **Step 1: Create the maddm_run.py file**

```python
"""MadDM session scripting and output parsing.

Generate MadDM session scripts and parse computed observables.
Library functions Claude composes per-task — not CLI executables.

For param_card manipulation, use the shared SLHA parser from the
madgraph skill: madgraph/scripts/card_io.py
"""

from __future__ import annotations

import re
from pathlib import Path


def generate_maddm_script(
    model: str,
    observables: list[str],
    params: dict[str, float] | None = None,
    dm_candidate: int | None = None,
) -> str:
    """Build a MadDM session script for MG5.

    Args:
        model: UFO model name (e.g. 'DMsimp_s_spin0').
        observables: List of observables to compute. Options:
            'relic', 'direct_detection', 'indirect_detection'
        params: Optional parameter overrides as 'BLOCK:PID' -> value.
            Example: {'MASS:9000006': 100.0, 'DMINPUTS:1': 1.0}
        dm_candidate: PDG ID of the DM candidate (if model has
            multiple neutral stable particles).

    Returns:
        MG5/MadDM script content as a string.
    """
    lines = [f"import model {model}"]

    if dm_candidate is not None:
        lines.append(f"define darkmatter {dm_candidate}")

    obs_flags = {
        "relic": "relic_density",
        "direct_detection": "direct_detection",
        "indirect_detection": "indirect_detection",
    }

    lines.append("generate_maddm")
    lines.append("launch")

    for key, flag in obs_flags.items():
        state = "ON" if key in observables else "OFF"
        lines.append(f"  set {flag} {state}")

    if params:
        for param_key, value in params.items():
            block, pid = param_key.split(":")
            lines.append(f"  set {block} {pid} {value}")

    lines.append("done")
    return "\n".join(lines) + "\n"


def parse_maddm_output(path: str | Path) -> dict:
    """Extract computed observables from MadDM output.

    Parses the maddm_results.txt file produced by MadDM.

    Args:
        path: Path to MadDM output directory or directly to
            the maddm_results.txt file.

    Returns:
        Dict with available keys:
            omega_h2, sigma_si_proton, sigma_si_neutron,
            sigma_sd_proton, sigma_sd_neutron,
            sigmav_total, sigmav_channels
    """
    path = Path(path)
    if path.is_dir():
        results_file = path / "maddm_results.txt"
    else:
        results_file = path

    text = results_file.read_text()
    results: dict = {}

    omega_match = re.search(r"Omega\s*h\^2\s*[=:]\s*([\d.eE+-]+)", text)
    if omega_match:
        results["omega_h2"] = float(omega_match.group(1))

    dd_patterns = [
        (r"sigma_SI.*proton", "sigma_si_proton"),
        (r"sigma_SI.*neutron", "sigma_si_neutron"),
        (r"sigma_SD.*proton", "sigma_sd_proton"),
        (r"sigma_SD.*neutron", "sigma_sd_neutron"),
    ]
    for pattern, key in dd_patterns:
        match = re.search(
            rf"{pattern}\s*[=:]\s*([\d.eE+-]+)", text, re.IGNORECASE
        )
        if match:
            results[key] = float(match.group(1))

    sigmav_match = re.search(
        r"<sigma\s*v>\s*(?:total)?\s*[=:]\s*([\d.eE+-]+)", text
    )
    if sigmav_match:
        results["sigmav_total"] = float(sigmav_match.group(1))

    channel_matches = re.findall(
        r"<sigma\s*v>\s*\((.+?)\)\s*[=:]\s*([\d.eE+-]+)", text
    )
    if channel_matches:
        results["sigmav_channels"] = {
            ch.strip(): float(val) for ch, val in channel_matches
        }

    return results
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py
git commit -m "feat(maddm): add maddm_run.py for session scripting and output parsing"
```

---

## Task 10: Create maddm scripts/scan_grid.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/maddm/scripts/scan_grid.py`

- [ ] **Step 1: Create the scan_grid.py file**

```python
"""Parameter space grid generation and batch orchestration for MadDM.

Generate grids of parameter points and batch MadDM scripts.
Library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import itertools
import math
import re


def make_grid(
    param_ranges: dict[str, tuple[float, float, int]],
    spacing: str = "linear",
) -> list[dict[str, float]]:
    """Generate a parameter space grid.

    Args:
        param_ranges: Dict mapping 'BLOCK:PID' names to
            (min, max, n_points) tuples.
        spacing: 'linear' or 'log' for all axes.

    Returns:
        List of dicts, each mapping parameter names to values.

    Example:
        grid = make_grid({
            "MASS:9000006": (10.0, 1000.0, 20),
            "DMINPUTS:1": (0.01, 4.0, 10),
        }, spacing="log")
    """
    axes = {}
    for name, (lo, hi, n) in param_ranges.items():
        if n < 1:
            raise ValueError(f"n_points must be >= 1, got {n} for {name}")
        if n == 1:
            axes[name] = [lo]
            continue
        if spacing == "log":
            if lo <= 0 or hi <= 0:
                raise ValueError(
                    f"Log spacing requires positive bounds, "
                    f"got ({lo}, {hi}) for {name}"
                )
            log_lo, log_hi = math.log(lo), math.log(hi)
            axes[name] = [
                math.exp(log_lo + i * (log_hi - log_lo) / (n - 1))
                for i in range(n)
            ]
        else:
            axes[name] = [
                lo + i * (hi - lo) / (n - 1) for i in range(n)
            ]

    names = list(axes.keys())
    points = list(itertools.product(*(axes[n] for n in names)))
    return [dict(zip(names, pt)) for pt in points]


def generate_batch(
    grid: list[dict[str, float]],
    template_script: str,
) -> list[str]:
    """Create a batch of MadDM scripts from a parameter grid.

    Replaces ``set BLOCK PID <value>`` lines in the template with
    each grid point's parameter values.

    Args:
        grid: List of parameter dicts from make_grid.
        template_script: MadDM script string containing
            ``set BLOCK PID <value>`` lines.

    Returns:
        List of script strings, one per grid point.
    """
    scripts = []
    for point in grid:
        script = template_script
        for param_key, value in point.items():
            block, pid = param_key.split(":")
            pattern = (
                rf"(set\s+{re.escape(block)}\s+{re.escape(pid)}\s+)"
                rf"[\d.eE+-]+"
            )
            script = re.sub(
                pattern, rf"\g<1>{value}", script, flags=re.IGNORECASE
            )
        scripts.append(script)

    return scripts
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/maddm/scripts/scan_grid.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/maddm/scripts/scan_grid.py
git commit -m "feat(maddm): add scan_grid.py for parameter space grid generation"
```

---

## Task 11: Create maddm scripts/limits.py

**Files:**
- Create: `plugins/monte-carlo-tools/skills/maddm/scripts/limits.py`

- [ ] **Step 1: Create the limits.py file**

```python
"""Experimental limit comparison utilities.

Load digitized exclusion curves and compare against computed predictions.
Library functions Claude composes per-task — not CLI executables.

Requires numpy.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_limit(
    experiment: str,
    observable: str,
    data_dir: str | Path,
) -> np.ndarray:
    """Load a digitized exclusion curve from a CSV file.

    Expects CSV with columns: mass_GeV, limit_value.
    File naming: {experiment}_{observable}.csv
    Lines starting with '#' are treated as comments.

    See assets/limit_data/README.md for data sources.

    Args:
        experiment: Experiment name (e.g. 'LZ', 'XENONnT',
            'FermiLAT', 'MAGIC').
        observable: Observable type (e.g. 'SI', 'SD',
            'sigmav_bb', 'sigmav_WW').
        data_dir: Directory containing CSV limit files.

    Returns:
        Array of shape (N, 2): columns [mass_GeV, limit_value].

    Raises:
        FileNotFoundError: If the limit file doesn't exist.
    """
    data_dir = Path(data_dir)
    filename = f"{experiment}_{observable}.csv"
    filepath = data_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Limit file not found: {filepath}\n"
            f"See assets/limit_data/README.md for data sources."
        )

    data = np.loadtxt(filepath, delimiter=",", comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def is_excluded(
    point: dict,
    limit: np.ndarray,
    mass_key: str = "mass",
    value_key: str = "value",
) -> bool:
    """Check whether a theory point is excluded by an experimental limit.

    Uses log-linear interpolation of the limit curve.

    Args:
        point: Dict with mass and observable value.
        limit: Array from load_limit, shape (N, 2).
        mass_key: Key for mass in point dict.
        value_key: Key for observable value in point dict.

    Returns:
        True if the point's value exceeds (is above) the limit.
        False if the mass is outside the limit curve's range.
    """
    mass = point[mass_key]
    value = point[value_key]

    limit_masses = limit[:, 0]
    limit_values = limit[:, 1]

    if mass < limit_masses.min() or mass > limit_masses.max():
        return False

    log_limit = np.interp(
        np.log10(mass),
        np.log10(limit_masses),
        np.log10(limit_values),
    )
    return float(value) > 10**log_limit


def overlay_on_limit(
    results: list[dict],
    limit: np.ndarray,
    mass_key: str = "mass",
    value_key: str = "value",
) -> dict:
    """Prepare data for an exclusion plot overlay.

    Separates theory points into allowed and excluded, alongside
    the limit curve.

    Args:
        results: List of dicts with mass and observable value.
        limit: Array from load_limit.
        mass_key: Key for mass in result dicts.
        value_key: Key for observable value in result dicts.

    Returns:
        Dict with keys: limit_mass, limit_value,
        allowed_mass, allowed_value, excluded_mass, excluded_value
        (all numpy arrays).
    """
    allowed_m, allowed_v = [], []
    excluded_m, excluded_v = [], []

    for r in results:
        if is_excluded(r, limit, mass_key, value_key):
            excluded_m.append(r[mass_key])
            excluded_v.append(r[value_key])
        else:
            allowed_m.append(r[mass_key])
            allowed_v.append(r[value_key])

    return {
        "limit_mass": limit[:, 0],
        "limit_value": limit[:, 1],
        "allowed_mass": np.array(allowed_m),
        "allowed_value": np.array(allowed_v),
        "excluded_mass": np.array(excluded_m),
        "excluded_value": np.array(excluded_v),
    }
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('plugins/monte-carlo-tools/skills/maddm/scripts/limits.py').read()); print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/monte-carlo-tools/skills/maddm/scripts/limits.py
git commit -m "feat(maddm): add limits.py for experimental exclusion curve comparison"
```

---

## Task 12: Update plugin metadata and delete old skill

**Files:**
- Modify: `plugins/monte-carlo-tools/.claude-plugin/plugin.json`
- Modify: `plugins/monte-carlo-tools/README.md`
- Modify: `.claude-plugin/marketplace.json`
- Delete: `plugins/monte-carlo-tools/skills/madgraph-helper/SKILL.md`

- [ ] **Step 1: Update plugin.json**

Replace the full contents of `plugins/monte-carlo-tools/.claude-plugin/plugin.json` with:

```json
{
  "name": "monte-carlo-tools",
  "description": "Interfaces for MadGraph, MadDM, Pythia, and other Monte Carlo event generators",
  "version": "0.1.0",
  "skills": [
    {
      "name": "madgraph",
      "path": "./skills/madgraph/SKILL.md"
    },
    {
      "name": "maddm",
      "path": "./skills/maddm/SKILL.md"
    },
    {
      "name": "pythia-config",
      "path": "./skills/pythia-config/SKILL.md"
    }
  ]
}
```

- [ ] **Step 2: Update README.md**

Replace the full contents of `plugins/monte-carlo-tools/README.md` with:

```markdown
# Monte Carlo Tools

Interfaces for standard HEP event generators. Generate process cards, run dark matter calculations, configure parton showers, and set up full simulation chains.

## Skills

### `/madgraph`
Full MadGraph5_aMC@NLO interface — process definition, card writing/editing, event generation, LHE parsing, and parameter scans. Covers LO and NLO generation with any UFO model. Includes reference documentation, composable Python scripts, and example cards.

### `/maddm`
MadDM dark matter phenomenology — relic density, spin-independent/dependent nucleon cross-sections, and indirect detection rates. Includes parameter scanning and comparison against LZ, XENONnT, Fermi-LAT, and MAGIC experimental limits.

### `/pythia-config`
Configure Pythia8 for parton showering, hadronization, underlying event, and particle decays. Generate `.cmnd` configuration files.

## Prerequisites

- MadGraph5_aMC@NLO (v3.5+)
- Pythia8 (v8.3+)
- Python 3.10+ with numpy (for MadDM limit comparison scripts)
```

- [ ] **Step 3: Update marketplace.json**

In `.claude-plugin/marketplace.json`, update the monte-carlo-tools entry's description and tags:

Replace:
```json
    {
      "name": "monte-carlo-tools",
      "source": "./plugins/monte-carlo-tools",
      "description": "Interfaces for MadGraph, Pythia, and other Monte Carlo generators",
      "version": "0.1.0",
      "tags": ["madgraph", "pythia", "monte-carlo", "event-generation"]
    }
```

With:
```json
    {
      "name": "monte-carlo-tools",
      "source": "./plugins/monte-carlo-tools",
      "description": "Interfaces for MadGraph, MadDM, Pythia, and other Monte Carlo generators",
      "version": "0.1.0",
      "tags": ["madgraph", "maddm", "pythia", "monte-carlo", "dark-matter", "event-generation"]
    }
```

- [ ] **Step 4: Delete the old madgraph-helper skill**

```bash
rm -rf plugins/monte-carlo-tools/skills/madgraph-helper/
```

- [ ] **Step 5: Verify the new structure**

Run: `find plugins/monte-carlo-tools/ -type f | sort`

Expected output (confirm all new files present, madgraph-helper gone):
```
plugins/monte-carlo-tools/.claude-plugin/plugin.json
plugins/monte-carlo-tools/README.md
plugins/monte-carlo-tools/skills/madgraph/SKILL.md
plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/param_card.dat
plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/proc_card.dat
plugins/monte-carlo-tools/skills/madgraph/assets/example_cards/sm_ttbar/run_card.dat
plugins/monte-carlo-tools/skills/madgraph/references/analysis.md
plugins/monte-carlo-tools/skills/madgraph/references/generation.md
plugins/monte-carlo-tools/skills/madgraph/references/setup.md
plugins/monte-carlo-tools/skills/madgraph/scripts/card_io.py
plugins/monte-carlo-tools/skills/madgraph/scripts/lhe_parser.py
plugins/monte-carlo-tools/skills/madgraph/scripts/mg5_batch.py
plugins/monte-carlo-tools/skills/maddm/SKILL.md
plugins/monte-carlo-tools/skills/maddm/assets/limit_data/README.md
plugins/monte-carlo-tools/skills/maddm/references/observables.md
plugins/monte-carlo-tools/skills/maddm/references/scanning.md
plugins/monte-carlo-tools/skills/maddm/references/setup.md
plugins/monte-carlo-tools/skills/maddm/scripts/limits.py
plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py
plugins/monte-carlo-tools/skills/maddm/scripts/scan_grid.py
plugins/monte-carlo-tools/skills/pythia-config/SKILL.md
```

- [ ] **Step 6: Commit**

```bash
git add -A plugins/monte-carlo-tools/ .claude-plugin/marketplace.json
git commit -m "feat(monte-carlo-tools): update plugin metadata, add maddm to registry, remove madgraph-helper"
```
