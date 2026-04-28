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

MadDM uses the Hoferichter et al. (2017) values for hadronic matrix elements. **Always use these exact values when computing SI/SD cross-sections analytically — do not approximate f_N ≈ 0.3.**

#### SI form factors (scalar quark content of the nucleon)

| Parameter | Proton | Neutron | Description |
|-----------|--------|---------|-------------|
| f_u | 0.0153 | 0.0110 | Up quark scalar form factor |
| f_d | 0.0191 | 0.0273 | Down quark scalar form factor |
| f_s | 0.0447 | 0.0447 | Strange quark scalar form factor |

The gluon form factor is derived: `f_TG = 1 - f_u - f_d - f_s`.

The effective Higgs-nucleon coupling for SI scattering is:

```
f_N = f_u + f_d + f_s + (2/9) * f_TG
    = 0.0153 + 0.0191 + 0.0447 + (2/9)(1 - 0.0791)
    = 0.0791 + 0.2047
    = 0.2838   (for proton)
```

The factor 2/9 comes from heavy-quark (c, b, t) contributions via the trace anomaly: each heavy quark contributes (2/27) × f_TG, and there are 3 heavy flavors.

**The SI cross-section formula (Higgs portal):**

```
sigma_SI = (mu^2 / pi) * (m_p / v)^2 * y_h^2 / m_h^4 * f_N^2
```

where mu = m_chi * m_p / (m_chi + m_p) is the reduced mass.

#### SD form factors (spin content of the nucleon)

| Parameter | Proton | Description |
|-----------|--------|-------------|
| Delta_u^p | 0.842 | Proton spin from up quarks |
| Delta_d^p | -0.427 | Proton spin from down quarks |
| Delta_s^p | -0.085 | Proton spin from strange quarks |

#### Conversion factors

| Quantity | Value |
|----------|-------|
| 1 GeV^-2 | 0.3894 × 10^-27 cm^2 |
| m_p | 0.93827 GeV |
| m_n | 0.93957 GeV |
| v (Higgs VEV) | 246.22 GeV |
| m_h (Higgs mass) | 125.25 GeV |

These can be overridden in the maddm_card.dat if newer lattice values are available.

### Configuration

```
set direct_detection ON
set loop OFF               # Tree-level only (default)
```

### Output

```
SigmaN_SI_p                   = [1.23e-46, 4.30e-47]   # Xenon1ton
SigmaN_SI_n                   = [1.19e-46, 4.30e-47]   # Xenon1ton
SigmaN_SD_p                   = [4.56e-42, 6.50e-41]   # Pico60
SigmaN_SD_n                   = [3.89e-42, 3.50e-41]   # Lux2017
```

Each bracket is `[σ_DM_predicted_at_this_mass, σ_experiment_90CL_limit_at_this_mass]`;
the comment after `#` names the experiment whose limit appears in the second slot.

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
