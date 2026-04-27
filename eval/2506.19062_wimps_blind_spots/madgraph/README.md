# MadGraph Setup for 2506.19062

Cross-validation of the paper's analytical calculations against
MadGraph5_aMC@NLO Monte Carlo output.

## Models Required

### 1. Singlet-Doublet Model
**UFO model**: Custom, generated via FeynRules.

The minimal singlet-doublet model adds a Dirac singlet S and a vector-like
doublet D to the SM. The FeynRules model file should implement Eq. (1):

```
L = L_SM - 1/2 m_S S^2 - m_D D_L D_R - y_1 D_L H S - y_2 D_R H~ S + h.c.
```

Physical spectrum: 3 neutral Majorana fermions (chi_1, chi_2, chi_3) and
1 charged Dirac fermion (psi^+/-).

**Source**: Generate with FeynRules or use existing implementations:
- `SingletDoublet_UFO` from the HEPMDB or FeynRules model database
- Calibbi et al. (2015): arXiv:1503.09133

### 2. 2HDM+a
**UFO model**: `DMPseudo_2HDM` (official LHC DM WG model).

This is a well-established model with publicly available UFO files:
- LHC DM WG: https://github.com/LHC-DMWG/model-repository
- Model: `DMPseudo_2HDM` (Bauer et al. 2017, arXiv:1701.07427)

### 3. Dark SU(3)
**UFO model**: Custom, generated via FeynRules.

The dark SU(3) model requires a non-trivial FeynRules implementation
with a new confining gauge group. References:
- Gross et al. (2015): arXiv:1502.07358
- Arcadi et al. (2016): arXiv:1611.00365

## Processes to Generate

### DM-nucleon scattering (for SI cross-section comparison)
```
# Singlet-doublet: chi1 q -> chi1 q via h exchange
generate chi1 u > chi1 u    # t-channel Higgs
generate chi1 d > chi1 d

# 2HDM+a: chi q -> chi q via pseudoscalar loop
# (requires NLO / MadLoop for the loop-induced process)
generate chi chi~ > u u~ [QCD]

# Dark SU(3): V q -> V q via Higgs exchange
generate V1 u > V1 u
```

### DM pair annihilation (for relic density comparison)
```
# Singlet-doublet
generate chi1 chi1 > w+ w-
generate chi1 chi1 > z z
generate chi1 chi1 > h h
generate chi1 chi1 > t t~
generate chi1 chi1 > b b~

# 2HDM+a
generate chi chi~ > b b~
generate chi chi~ > t t~
generate chi chi~ > a a       # pseudoscalar pair
generate chi chi~ > w+ w-

# Dark SU(3)
generate V1 V1~ > w+ w-
generate V1 V1~ > z z
generate V1 V1~ > h h
```

## Running

```bash
# Install the UFO model (example for 2HDM+a)
cp -r DMPseudo_2HDM /path/to/MG5_aMC/models/

# Run MadGraph
cd /path/to/MG5_aMC
./bin/mg5_aMC madgraph/two_hdm_plus_a/proc_card.dat

# Or use the comparison script
python run_comparison.py --model 2HDMa --point benchmark_1
```
