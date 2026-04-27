# Evaluation Suite

Benchmark calculations extracted from published hep-ph papers. Each subdirectory
contains one paper's worth of equations, model definitions, and MadGraph comparison
scripts.

The goal is to validate our skill suite against known results: we implement the
paper's analytical formulas as Python functions, set up MadGraph with the same BSM
models, and cross-check over a range of inputs.

## Papers

| Directory | arXiv | Model Class | Title |
|-----------|-------|-------------|-------|
| [`2506.19062_wimps_blind_spots/`](2506.19062_wimps_blind_spots/) | [2506.19062](https://arxiv.org/abs/2506.19062) | singlet-doublet / 2HDM+a / dark-SU(3) | WIMPs Below the Radar: Blind Spots and Benchmarks Beyond the Neutrino Floor |
| [`2601.13147_scalar_portal_singlet/`](2601.13147_scalar_portal_singlet/) | [2601.13147](https://arxiv.org/abs/2601.13147) | scalar-portal singlet fermion | Scalar Portal Singlet-Fermion DM: blind spots in the two-Higgs sigma_SI (Eq. 31) |
| [`2603.23040_scotogenic_inverse_seesaw/`](2603.23040_scotogenic_inverse_seesaw/) | [2603.23040](https://arxiv.org/abs/2603.23040) | scotogenic inverse-seesaw | Scotogenic Inverse Seesaw: thermal relic, SI/SD via NREFT, mu->e gamma |
| [`2509.08043_gce_2hdma_secluded/`](2509.08043_gce_2hdma_secluded/) | [2509.08043](https://arxiv.org/abs/2509.08043) | 2HDM+a + secluded hypercharge | 2HDM+a & Secluded Hypercharge for the Galactic Center Excess (exact 1-loop SI) |
| [`2511.21808_gce_wimp_comprehensive/`](2511.21808_gce_wimp_comprehensive/) | [2511.21808](https://arxiv.org/abs/2511.21808) | Higgs-portal / B-L Z' | Comprehensive WIMP survey for the GCE (Higgs portal + Z' B-L) |
| [`2509.15121_nmssm_ml_blind_spot/`](2509.15121_nmssm_ml_blind_spot/) | [2509.15121](https://arxiv.org/abs/2509.15121) | NMSSM (ML-explored) | NMSSM ML blind-spot study: machine-learning neutralino SI suppression |

## Running

Each paper directory contains:
- `models/` — Python implementations of the paper's equations
- `cross_sections/` — SI/SD and annihilation cross-section formulas
- `madgraph/` — proc/param/run cards for MadGraph comparison
- `benchmarks/` — specific parameter points with expected numerical outputs
- `constants.py` — physical constants used in the paper

```bash
# Run all benchmarks for a paper
cd eval/2506.19062_wimps_blind_spots
python -m pytest benchmarks/ -v

# Run MadGraph comparison (requires MadGraph5_aMC@NLO installed)
python madgraph/run_comparison.py
```
