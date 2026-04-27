# Conditional emission gates — gamlike v0

Enumeration of every conditional-emission gate in
`maddm_run_interface.py:3444-3628`. Each gate controls whether a field or
block appears in `MadDM_results.txt`. Implementer cross-checked each gate
against the producer source before shipping.

Format: one H2 section per gate so `test_gate_coverage.py` can tokenize gate IDs.

---

## G1 — Relic Density section

**Controlled fields:** Entire `# Relic Density` block (all relic fields).

**Producer condition:** `if relic:` at source line `:3465`.

**Source line:** `:3465`

**v0 handling:** `relic.present: true` iff the banner is found in the file.

**Fixtures:** `relic_only_xsi_eq_1_2hdma.txt`, `relic_only_xsi_eq_1_sd.txt`, `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `coannihilation_two_initial_states.txt`, `legacy_omega_h2_alias.txt`, `malformed_truncated.txt`, `malformed_unknown_section.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`, `fluxes_source.txt`

---

## G2 — xsi field

**Controlled fields:** `relic.xsi`

**Producer condition:** `if self.last_results['xsi'] > 0:` at `:3474-3475`. In practice this is always True since the producer clamps xsi ≥ 0.

**Source line:** `:3474-3475`

**v0 handling:** Numeric field in JSON; no separate gate (condition is always true for well-formed runs). The `xsi >= 1.0` boundary controls G13 (thermal pair), not G2.

**Fixtures:** `relic_only_xsi_eq_1_2hdma.txt`, `relic_only_xsi_eq_1_sd.txt`, `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `coannihilation_two_initial_states.txt`, `legacy_omega_h2_alias.txt`

---

## G3 — Direct Detection section

**Controlled fields:** Entire `# Direct Detection [cm^2]` block.

**Producer condition:** `if direct:` at `:3489`.

**Source line:** `:3489`

**v0 handling:** `direct.present: true` iff the banner is found.

**Fixtures:** `full_run_xsi_lt_1.txt`, `direct_detection_only.txt`

---

## G4 — Per-experiment direct detection row

**Controlled fields:** Each `direct.results[i]` object.

**Producer condition:** `for D in self.last_results['direct_results']:` at `:3493-3497`.

**Source line:** `:3493-3497`

**v0 handling:** Array of objects; each bracketed `[sig,lim]` line with inline comment.

**Fixtures:** `full_run_xsi_lt_1.txt`, `direct_detection_only.txt`

---

## G5 — Indirect Detection section

**Controlled fields:** Entire `# Indirect Detection` block.

**Producer condition:** `if indirect or spectral:` at `:3504`.

**Source line:** `:3504`

**v0 handling:** `indirect.present: true` iff the banner is found.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G6 — sigmav_method

**Controlled fields:** `indirect.sigmav_method`

**Producer condition:** Always emitted when indirect section fires; from `self.maddm_card['sigmav_method']` at `:3509`.

**Source line:** `:3509`

**v0 handling:** Captured from comment line `# Annihilation cross section computed with the method: <method>`. String field.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G7 — Continuum sub-block

**Controlled fields:** `indirect.continuum.present` and `indirect.continuum.channels[*]`

**Producer condition:** `if cont_procs:` at `:3530`. Only fires when non-spectral final states exist.

**Source line:** `:3530`

**v0 handling:** `indirect.continuum.present: true` iff the `# <sigma v>[cm^3 s^-1] of continuum spectrum final states` header is found.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`

---

## G8 — Line sub-block

**Controlled fields:** `indirect.lines.present` and `indirect.lines.channels[*]`

**Producer condition:** `if line_procs:` at `:3534`. Only fires when spectral/line final states exist.

**Source line:** `:3534`

**v0 handling:** `indirect.lines.present: true` iff the `# <sigma v>[cm^3 s^-1] of line spectrum final states` header is found.

**Fixtures:** `full_run_xsi_lt_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G9 — flux_method

**Controlled fields:** `indirect.global.flux_method`

**Producer condition:** Always emitted when indirect section fires; from `method = self.maddm_card['indirect_flux_source_method']` at `:3502` and then `# Global Fermi dSph Limit computed with <method> spectra` at `:3564`.

**Source line:** `:3502, :3564`

**v0 handling:** Captured from comment line `# Global Fermi dSph Limit computed with <method> spectra`. String field.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G10 — Total_xsec

**Controlled fields:** `indirect.global.Total_xsec`

**Producer condition:** `if sigmav_meth != 'inclusive':` at `:3565-3566`. XOR with G11.

**Source line:** `:3565-3566`

**v0 handling:** Non-null when `sigmav_method != 'inclusive'`. Bracketed pair `[pred,ul]`; parser takes first element as `Total_xsec`. Invariant I1: exactly one of G10/G11 non-null.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`, `coannihilation_two_initial_states.txt`

---

## G11 — TotalSM_xsec

**Controlled fields:** `indirect.global.TotalSM_xsec`

**Producer condition:** `else:` (when `sigmav_meth == 'inclusive'`) at `:3567-3568`. XOR with G10.

**Source line:** `:3567-3568`

**v0 handling:** Non-null when `sigmav_method == 'inclusive'`. Bracketed pair; parser takes first element. Invariant I1.

**Fixtures:** `full_run_xsi_lt_1.txt` (validates XOR invariant: Total_xsec non-null, TotalSM_xsec null). The `inclusive` sigmav_method case (TotalSM_xsec non-null) is covered by an inline synthetic fixture in `TestTotalXsecXOR` in `test_parse_maddm_results.py`.

---

## G12 — Fermi_Likelihood and Fermi_pvalue

**Controlled fields:** `indirect.global.Fermi_Likelihood`, `indirect.global.Fermi_pvalue`

**Producer condition:** Always emitted when indirect mode fires (`:3569-3570`).

**Source line:** `:3569-3570`

**v0 handling:** Numeric or null (if malformed). Always present under `indirect.present=true`.

**Fixtures:** `full_run_xsi_lt_1.txt`, `full_run_xsi_eq_1.txt`, `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G13 — Fermi_Likelihood(Thermal) and Fermi_pvalue(Thermal)

**Controlled fields:** `indirect.global.Fermi_Likelihood_Thermal`, `indirect.global.Fermi_pvalue_Thermal`, `indirect.global.thermal_emitted`

**Producer condition:** `if self.last_results['xsi'] < 1:` at `:3572-3574`. Strict less-than (no FP slop per D16).

**Source line:** `maddm_run_interface.py:3572-3574` (exact source_ref string for test assertion)

**v0 handling:**
- `xsi < 1.0` → thermal fields non-null, `thermal_emitted: true`.
- `xsi >= 1.0` → thermal fields null, `thermal_emitted: false`, `FIELD_GATED` warning with `source_ref="maddm_run_interface.py:3572-3574"`.

**Fixtures:** `full_run_xsi_lt_1.txt` (emit case), `full_run_xsi_eq_1.txt` (non-emit case)

---

## G14 — Gamma-line spectrum section

**Controlled fields:** Entire `# Gamma-line spectrum and line limits` block.

**Producer condition:** `if spectral:` at `:3577`.

**Source line:** `:3577`

**v0 handling:** `spectral.present: true` iff the 1-line banner `# Gamma-line spectrum and line limits` is found (D11 — NOT a 3-line bordered banner).

**Fixtures:** `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G15 — Per-experiment spectral block

**Controlled fields:** Each `spectral.experiments[i]` object.

**Producer condition:** `for line_exp in self.line_experiments:` at `:3585-3617`.

**Source line:** `:3585-3617`

**v0 handling:** Array of objects; each started by `# <ExpName> (ArXiv:<num>)` comment.

**Fixtures:** `spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`

---

## G16 — No peaks out of detection range

**Controlled fields:** `spectral.experiments[i].no_peaks_out_of_range`, `spectral.experiments[i].peaks`

**Producer condition:** `len(energy_peaks) == 0` AND vave-range condition at `:3590-3595`.

**Source line:** `:3590-3595`

**v0 handling:** `# No peaks found: out of detection range.` line → `peaks: []`, `no_peaks_out_of_range: true`, `NO_PEAKS_OUT_OF_DETECTION_RANGE` warning. Invariant I5.

**Fixtures:** `spectral_no_peaks_oo_range.txt`

---

## G17 — Per-peak like/pvalue (optional)

**Controlled fields:** `spectral.experiments[i].peaks[k].loglike_neg2`, `.pvalue`

**Producer condition:** `try: like = ...; except KeyError: continue` at `:3609-3614`. These fields are absent if MadDM did not compute them.

**Source line:** `:3609-3614`

**v0 handling:** `null` when the `like_<n>` / `pvalue_<n>` keys are absent (KeyError on producer side). No warning emitted (expected absence).

**Fixtures:** `spectral_with_lines.txt` (peak_0 has them; peak_1 does not)

---

## G18 — Per-peak error_code

**Controlled fields:** `spectral.experiments[i].peaks[k].error_code`

**Producer condition:** `error_str = "# error: %s" % error_code if error_code != 0 else ''` at `:3603-3604`.

**Source line:** `:3603-3604`

**v0 handling:** Integer; default 0. Parsed from inline `# error: <code>` comment on the `peak_<n>` line.

**Fixtures:** `spectral_with_lines.txt` (peak_1 has `# error: 2`)

---

## G19 — astrophysical_parameters (reserved)

**Controlled fields:** `spectral.experiments[i].astrophysical_parameters`

**Producer condition:** Source lines `:3580-3582` are currently commented out in MadDM 3.2. Would emit density profile and related parameters.

**Source line:** `:3580-3582` (commented out)

**v0 handling:** Always `null` in v0. Reserved schema slot; documented in schema as reserved. v1 will populate when producer uncomments these lines.

**Fixtures:** all spectral fixtures (`spectral_with_lines.txt`, `spectral_no_peaks_oo_range.txt`)

---

## G20 — CR Flux at Earth section

**Controlled fields:** Entire `# CR Flux at Earth` block.

**Producer condition:** `if fluxes_source:` at `:3620`.

**Source line:** `:3620`

**v0 handling:** `fluxes_source.present: true` iff the 49-char `#`-bordered banner is found.

**Fixtures:** `fluxes_source.txt`

---

## G21 — flux_positrons (reserved)

**Controlled fields:** `fluxes_source.fluxes.positrons`

**Producer condition:** Source lines `:3627-3628` are currently commented out in MadDM 3.2.

**Source line:** `:3627-3628` (commented out)

**v0 handling:** Always `null` in v0. Reserved schema slot.

**Fixtures:** `fluxes_source.txt`
