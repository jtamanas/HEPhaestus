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
