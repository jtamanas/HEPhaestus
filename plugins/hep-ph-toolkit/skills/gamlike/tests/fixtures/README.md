# gamlike test fixtures

Per-fixture provenance, gate mapping, and expected parser behavior.

All producer-format references are to `maddm_run_interface.py` (MadDM 3.2).

---

## Real fixtures

### `relic_only_xsi_eq_1_2hdma.txt`

**Source:** Real MadDM 3.2 output, copied from
`.shift-manager/run-20260426-punchlist-tier2/fixtures/MadDM_results_2hdma.txt`
(originally from `.claude/worktrees/agent-aa0dba254bcf80001/demo_output/2hdm-a/maddm_run/output/output/run_01/MadDM_results.txt`).

**Model:** 2HDM+a; initial state `chichibar`.

**Sections present:** Header, Relic Density.

**Expected `present` flags:** `relic: true`, `direct: false`, `indirect: false`, `spectral: false`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic banner present)
- G2 (xsi = 1.00e+00)

**Notes:** `Omegah2 = 1.05e+01` (over-abundant; ξ=1 is the cap). Channels are physical (wphp + wmhm dominant). Run `run_02` of sd is also available at the dmc playtest tree if needed (documents O5 decision to skip).

---

### `relic_only_xsi_eq_1_sd.txt`

**Source:** Real MadDM 3.2 output, copied from
`.shift-manager/run-20260426-punchlist-tier2/fixtures/MadDM_results_sd.txt`
(originally from `.shift-manager/run-20260425-dmc/playtest/work/maddm_sd_run1/output/run_01/MadDM_results.txt`).

**Model:** Singlet-Doublet; initial state `chi1chi1`.

**Sections present:** Header, Relic Density.

**Expected `present` flags:** `relic: true`, `direct: false`, `indirect: false`, `spectral: false`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic banner present)
- G2 (xsi = 1.00e+00)
- D15 / I6: all channel percentages are `nan %` → `null` + `FIELD_NAN` warnings

**Notes:** `Omegah2 = -1.00e+00` (model calculation failed; MadDM sets sentinel). All channel percentages are `nan %` because MadDM failed to compute cross sections. Parser must handle `nan %` with D15 → `null + FIELD_NAN` warning. `x_f = 0.00e+00` is also a sentinel value.

---

## Synthetic fixtures

All synthetic fixtures are hand-authored using real `form_s`/`form_n` formatting
(see `maddm_run_interface.py:3451-3457`). Conformance verified by `check_fixture_format.py`.

### `full_run_xsi_lt_1.txt` (T3a)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density, Direct Detection, Indirect Detection.

**Expected `present` flags:** `relic: true`, `direct: true`, `indirect: true`, `spectral: false`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic banner)
- G2 (xsi = 5.00e-01 < 1)
- G3 (direct banner)
- G4 (per-experiment direct: Xenon1T_2018_SI, Xenon1T_2018_SD_neutron)
- G5 (indirect banner)
- G6 (sigmav_method = madevent — captured from comment line)
- G7 (continuum sub-block present: chichibar_bbx, chichibar_ttx)
- G8 (line sub-block present: chichibar_za)
- G9 (flux_method = pythia8 — captured from Global Fermi comment)
- G10 (Total_xsec non-null; TotalSM_xsec null — madevent != inclusive)
- G12 (Fermi_Likelihood, Fermi_pvalue)
- G13 (xsi < 1 → Fermi_Likelihood(Thermal) and Fermi_pvalue(Thermal) emitted; thermal_emitted=true)

---

### `full_run_xsi_eq_1.txt` (T3b)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density, Indirect Detection.

**Expected `present` flags:** `relic: true`, `direct: false`, `indirect: true`, `spectral: false`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic)
- G2 (xsi = 1.00e+00; thermal pair NOT emitted)
- G5 (indirect)
- G6 (sigmav_method = madevent)
- G7 (continuum sub-block)
- G9 (flux_method = pythia8)
- G10 (Total_xsec)
- G12 (Fermi_Likelihood, Fermi_pvalue)
- G13 (xsi >= 1 → Fermi_Likelihood(Thermal) absent; thermal_emitted=false; FIELD_GATED warning)

**Notes:** G13 non-emit case. `FIELD_GATED` warning with `source_ref="maddm_run_interface.py:3572-3574"` is mandatory.

---

### `direct_detection_only.txt` (T3c)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Direct Detection.

**Expected `present` flags:** `relic: false`, `direct: true`, `indirect: false`, `spectral: false`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G3 (direct banner)
- G4 (3 per-experiment rows: Xenon1T_2018_SI, Xenon1T_2018_SD_neutron, LUX_2016_SI)

---

### `spectral_with_lines.txt` (T3d)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density, Indirect Detection (line sub-block), Gamma-line spectrum.

**Expected `present` flags:** `relic: true`, `direct: false`, `indirect: true`, `spectral: true`, `fluxes_source: false`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic)
- G2 (xsi = 1.00e+00)
- G5 (indirect)
- G6 (sigmav_method = madevent)
- G8 (line sub-block: chichibar_za)
- G9 (flux_method = pythia8)
- G10 (Total_xsec)
- G12 (Fermi_Likelihood, Fermi_pvalue)
- G13 (xsi=1 → thermal pair absent)
- G14 (spectral banner — 1-line + column-comment, D11)
- G15 (per-experiment spectral: Fermi LAT 2015)
- G17 (peak_0 has like/pvalue; peak_1 does NOT — G17 missing case)
- G18 (peak_1 has error_code=2 from inline `# error: 2` comment)
- G19 (astrophysical_parameters reserved null)

---

### `spectral_no_peaks_oo_range.txt` (T3e)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density, Indirect Detection (line sub-block), Gamma-line spectrum.

**Expected `present` flags:** `relic: true`, `indirect: true`, `spectral: true`.

**Expected exit code:** 0.

**Gates exercised:**
- G14 (spectral banner)
- G15 (per-experiment: Fermi LAT 2015 — but no peaks found)
- G16 (# No peaks found: out of detection range. → peaks=[], no_peaks_out_of_range=true)
- G19 (astrophysical_parameters reserved null)

**Expected warnings:** `NO_PEAKS_OUT_OF_DETECTION_RANGE` for experiment `Fermi LAT 2015`.

---

### `fluxes_source.txt` (T3f)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density, CR Flux at Earth.

**Expected `present` flags:** `relic: true`, `direct: false`, `indirect: false`, `spectral: false`, `fluxes_source: true`.

**Expected exit code:** 0.

**Gates exercised:**
- G20 (CR Flux banner with 49-char `#` border)
- G21 (positrons reserved null — commented out in producer `:3627-3628`)

**Notes:** CR Flux banner uses 49 `#` chars, not 48 (different banner style in producer). Parser must handle both.

---

### `coannihilation_two_initial_states.txt` (T3g)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density.

**Expected `present` flags:** `relic: true`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic)
- G2 (xsi = 1.00e+00)
- D4 (two initial states: chichibar, chi1psi1; nested channels schema)

**Expected `relic.channels`:**
```json
{
  "chichibar": {"bbx": 40.00, "ttx": 10.00},
  "chi1psi1":  {"bbx": 30.00, "ttx": 20.00}
}
```

**Expected `relic.initial_states`:** `["chi1psi1", "chichibar"]` (sorted).

---

### `legacy_omega_h2_alias.txt` (T3j — U2/D8)

**Source:** Synthetic, hand-authored using `Omega h^2` (with space) to simulate MadDM <3.2 output.

**Sections present:** Header (reports MadDM v. 2.0), Relic Density.

**Expected `present` flags:** `relic: true`.

**Expected exit code:** 0.

**Gates exercised:**
- G1 (relic)
- G2 (xsi = 1.00e+00)
- D8 (Omega h^2 legacy alias → parsed identically to Omegah2)

**Expected warnings:** `MADDM_VERSION_UNTESTED` (unrecognized version banner).

---

### `malformed_truncated.txt` (T3h)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density (banner only — no content fields).

**Expected exit code:** 3.

**Gates exercised:**
- I2 (relic banner present but Omegah2 missing → malformed)

**Expected stderr:** Structured error with section name + line number.

---

### `malformed_unknown_section.txt` (T3i)

**Source:** Synthetic, hand-authored.

**Sections present:** Header, Relic Density (complete), Experimental Extras (unknown).

**Expected exit code:** 0 (recoverable; unknown section is a forward-compat warning).

**Expected warnings:** `UNKNOWN_SECTION` with section name "Experimental Extras".

**Gates exercised:**
- G1 (relic — complete and parsed)
- UNKNOWN_SECTION warning path

---

## Snapshot files (`expected/`)

Each `expected/<fixture>.json` is the snapshotted parser output produced by
`regenerate_expected.py`. Fields `_meta.parsed_at` and `_meta.source_file`
are scrubbed to `"<SCRUBBED>"` for byte-stability.

Run `python tests/regenerate_expected.py` from the repo root to refresh.
