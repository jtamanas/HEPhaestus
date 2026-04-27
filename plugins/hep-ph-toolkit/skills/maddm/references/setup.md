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
