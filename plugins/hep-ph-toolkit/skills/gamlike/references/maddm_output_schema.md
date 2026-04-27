# MadDM results output schema reference

Field-by-field reference for `MadDM_results.txt` as produced by MadDM 3.2
(`maddm_run_interface.py:3444-3628`).

All fields are in **native MadDM units** (never converted by the parser). Units documented per field below.

---

## R-XSI: Producer-side xsi clamp finding

**Grep result:** `maddm_run_interface.py:1795-1803`

```python
if result['Omegah^2'] < 0:
    result['xsi'] = 1.0
elif result['Omegah^2'] < self.limits._oh2_planck and result['Omegah^2'] > 0:
    result['xsi'] = result['Omegah^2'] / self.limits._oh2_planck
else:
    result['xsi'] = 1.0
```

**Conclusion:** `xsi` is **clamped to 1.0** on the producer side. Values are always in (0, 1].
Specifically:
- `Ωh² < 0` (sentinel for failed run): `xsi = 1.0`
- `0 < Ωh² < Ωh²_Planck` (underabundant): `xsi = Ωh²/Ωh²_Planck` ∈ (0, 1)
- `Ωh² ≥ Ωh²_Planck` (overabundant or exact): `xsi = 1.0`

The parser threshold `xsi >= 1.0` (D16) is correct: the only value at exactly 1.0 is the clamped value.

---

## Header section (`:3461-3463`)

| Field | Type | Producer format | Notes |
|---|---|---|---|
| `_meta.maddm_version` | string | `MadDM v. <ver>` in second banner line | Captured from `#                 MadDM v. X.Y                 #` |

---

## Relic Density section (`:3466-3488`)

Gate: `relic` mode flag (`:3465`).

| Field | JSON key | Type | Units | Source line | Gate | Notes |
|---|---|---|---|---|---|---|
| `Omegah2` | `relic.Omegah2` | float or null | dimensionless | `:3472` | G1 (section present) | Also recognized as `Omega h^2` (D8/MadDM <3.2) |
| `Omegah_Planck` | `relic.Omegah_Planck` | float | dimensionless | `:3473` | G1 | Planck 2018 value; typically 0.120 |
| `xsi` | `relic.xsi` | float | dimensionless | `:3474-3475` | G2 (`xsi > 0` — always in practice) | `ξ = Ωh²/Ωh²_Planck`, clamped to 1.0; see R-XSI |
| `x_f` | `relic.x_f` | float | dimensionless | `:3476` | G1 | Freeze-out parameter |
| `sigmav_xf` | `relic.sigmav_xf` | float or null | cm³ s⁻¹ | `:3477` | G1 | Thermal-averaged annihilation cross section at freeze-out |
| `%_<init>_<final>` | `relic.channels[<init>][<final>]` | float or null | percent | `:3479-3480` | G1 | Channel contributions; D4 nested by initial state; format `'%.2f %%'` |
| (derived) | `relic.initial_states` | list[str] | — | — | — | Sorted unique list of initial states |
| (derived) | `relic.channels_sum_pct` | float | percent | — | — | Sum of all channel percentages; consumer checks vs 100 |

**Producer trailing-whitespace quirk (D14):** `xsi` and `sigmav_xf` lines have a trailing space before `\t #` comment. The `\t` character is a literal tab.

**NaN handling (D15):** `nan %` appears in real fixtures (SD model failure). Parser converts to `null` + `FIELD_NAN` warning.

---

## Direct Detection section (`:3490-3498`)

Gate: `direct` mode flag (`:3489`).

| Field | JSON key | Type | Units | Source line | Notes |
|---|---|---|---|---|---|
| Per-experiment key | `direct.results[i].name` | string | — | `:3493` | From `D['n']` field; e.g. `Xenon1T_2018_SI` |
| Inline comment | `direct.results[i].experiment_label` | string | — | `:3497` | `# XENON1T 2018 (SI)` stripped of `# ` prefix |
| `sig` | `direct.results[i].sig_cm2` | float | cm² | `:3493` | Prediction; from bracketed `[sig,lim]` |
| `lim` | `direct.results[i].lim_cm2` | float | cm² | `:3493` | Upper limit; from bracketed `[sig,lim]` |

**Format:** `form_s(D['n']) + '= ' + form_s('[' + form_n(cross) + ',' + form_n(ul) + ']') + '# ' + exp`

Note: the `form_s` applied to `[sig,lim]` means the bracket string gets padded to 30 chars. The `#` after the bracket is immediately followed by the experiment label (no space before label in MadDM 3.2 output format). Actually looking at real fixture: `# XENON1T 2018 (SI)` — one space after `#`.

---

## Indirect Detection section (`:3504-3574`)

Gate: `indirect` or `spectral` mode (`:3504`).

### Section structure

The Indirect Detection section contains comment lines with embedded method names:

| Comment line shape | Information captured | JSON key |
|---|---|---|
| `# Annihilation cross section computed with the method: <method>` | `sigmav_method` string | `indirect.sigmav_method` |
| `# Global Fermi dSph Limit computed with <method> spectra` | `flux_method` string | `indirect.global.flux_method` |

These are comment lines, NOT key=value pairs. The parser must match these specific comment patterns.

### Global Fermi block fields

| Field | JSON key | Type | Units | Source line | Gate |
|---|---|---|---|---|---|
| `Total_xsec` | `indirect.global.Total_xsec` | float or null | cm³ s⁻¹ | `:3565-3566` | G10 (`sigmav_method != 'inclusive'`) |
| `TotalSM_xsec` | `indirect.global.TotalSM_xsec` | float or null | cm³ s⁻¹ | `:3567-3568` | G11 (`sigmav_method == 'inclusive'`) |
| `Fermi_Likelihood` | `indirect.global.Fermi_Likelihood` | float or null | dimensionless | `:3569` | G12 |
| `Fermi_pvalue` | `indirect.global.Fermi_pvalue` | float or null | dimensionless | `:3570` | G12 |
| `Fermi_Likelihood(Thermal)` | `indirect.global.Fermi_Likelihood_Thermal` | float or null | dimensionless | `:3572` | G13 (`xsi < 1`) |
| `Fermi_pvalue(Thermal)` | `indirect.global.Fermi_pvalue_Thermal` | float or null | dimensionless | `:3574` | G13 (`xsi < 1`) |
| (derived) | `indirect.global.thermal_emitted` | bool | — | — | true iff G13 fired |

**G10/G11 XOR invariant (I1):** Exactly one of `Total_xsec` / `TotalSM_xsec` is non-null when `indirect.present=true`. Both null → exit 3. Both non-null → exit 3.

**Note on Total_xsec format:** The key=value format is `form_s('Total_xsec') + '= ' + form_s('[' + form_n(tot_th) + ',' + form_n(tot_ul) + ']')` — it's a **bracketed pair** `[prediction, upper_limit]`. Parser takes `[0]` as Total_xsec (the prediction).

**G13 source reference:** `maddm_run_interface.py:3572-3574` (literal; used in test assertion).

**Producer trailing-whitespace quirk (`:3574`):** `Fermi_pvalue(Thermal)` line ends with `\n ` (trailing space after newline on producer side). Parser's `\s*$` tolerates this.

### Continuum sub-block (G7)

Gate: `if cont_procs:` at `:3530`.

| Field | JSON key | Type | Notes |
|---|---|---|---|
| Process prediction+limit | `indirect.continuum.channels[<proc>].sigmav` | float | From `[sigmav, limit]` bracketed pair; first element |
| Process upper limit | `indirect.continuum.channels[<proc>].limit` | float | Second element |

Key format: bare process name (after stripping `taacsID#` prefix on producer side, then sub-keyed without the initial-state prefix). E.g., `chichibar_bbx` is the key.

### Line sub-block (G8)

Gate: `if line_procs:` at `:3534`. Same format as continuum sub-block.

---

## Gamma-line spectrum section (`:3577-3617`)

Gate: `spectral` mode (`:3577`).

**Banner shape (D11):** 1-line banner `# Gamma-line spectrum and line limits` followed by 1-line column-comment `# peak[GeV], flux[cm^-2 s^-1], J-factor[GeV^2 cm^-5]`. NOT a 3-line `#`-bordered banner.

Module-level constant: `SPECTRAL_SECTION_HEADER = "# Gamma-line spectrum and line limits"`.

Per-experiment structure (G15):

| Field | JSON key | Type | Notes |
|---|---|---|---|
| Experiment name | `spectral.experiments[i].experiment_name` | string | From `# <Name> (ArXiv:<num>)` comment |
| ArXiv number | `spectral.experiments[i].arxiv_number` | string | From same comment |
| `ROI` | `spectral.experiments[i].ROI` | float | degrees; format `'%1.1f'` |
| `J-factor` | `spectral.experiments[i].Jfactor` | float | GeV² cm⁻⁵ |
| (reserved) | `spectral.experiments[i].astrophysical_parameters` | null | G19; producer lines `:3580-3582` commented out |

Per-peak fields (G17/G18; aggregated by `_<n>` suffix per O8):

| Field | JSON key | Type | Notes |
|---|---|---|---|
| `peak_<n>(<states>)` | `.peaks[k].num`, `.states` | int, string | Energy in GeV; states from key parenthetical |
| Peak energy | `.peaks[k].energy_GeV` | float | Value of `peak_<n>` key |
| `flux_<n>` | `.peaks[k].flux`, `.peaks[k].flux_UL` | float | Bracketed pair `[flux, flux_UL]` |
| `-2*log(Likelihood)_<n>` | `.peaks[k].loglike_neg2` | float or null | G17: null if KeyError on producer |
| `p-value_<n>` | `.peaks[k].pvalue` | float or null | G17: null if KeyError |
| Inline `# error: <code>` | `.peaks[k].error_code` | int | G18; default 0 |

**G16 path:** `# No peaks found: out of detection range.` → `peaks: []` + `no_peaks_out_of_range: true` + `NO_PEAKS_OUT_OF_DETECTION_RANGE` warning.

---

## CR Flux at Earth section (`:3619-3628`)

Gate: `fluxes_source` mode (`:3620`).

Banner: 49-char `#` border (not 48); `# CR Flux at Earth [particles cm^-2 s^-1 sr^-1) #`.

Method line: `# Fluxes calculated using the spectra from <method>` — comment line, not key=value.

| Field | JSON key | Type | Units | Source line |
|---|---|---|---|---|
| `Flux_neutrinos_e` | `fluxes_source.fluxes.neutrinos_e` | float | particles cm⁻² s⁻¹ sr⁻¹ | `:3624` |
| `Flux_neutrinos_mu` | `fluxes_source.fluxes.neutrinos_mu` | float | same | `:3625` |
| `Flux_neutrinos_tau` | `fluxes_source.fluxes.neutrinos_tau` | float | same | `:3626` |
| `Flux_gammas` | `fluxes_source.fluxes.gammas` | float | same | `:3627` |
| (reserved) | `fluxes_source.fluxes.positrons` | null | — | `:3627-3628` commented out |

---

## Warning code catalog

| Code | Meaning | When emitted |
|---|---|---|
| `FIELD_GATED` | Field null because producer gate did not fire | G13 (xsi >= 1); possibly others |
| `NO_PEAKS_OUT_OF_DETECTION_RANGE` | G16 path: no peaks in detection range | spectral experiment with no peaks |
| `FIELD_NAN` | Numeric field was `nan` in producer output | D15; any field |
| `FIELD_INF` | Numeric field was `inf` in producer output | D15; any field |
| `MADDM_VERSION_UNTESTED` | Header banner shows unrecognized MadDM version | D8/U2; MadDM < 3.2 |
| `UNKNOWN_SECTION` | Unrecognized 3-line `#`-bordered banner | Forward-compat; new MadDM section |

---

## Encoding

UTF-8 with `errors="replace"`. Real MadDM output is plain ASCII.
