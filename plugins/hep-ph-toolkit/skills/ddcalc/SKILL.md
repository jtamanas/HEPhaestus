---
name: ddcalc
description: Compute direct-detection likelihoods and 90%-CL exclusion verdicts using DDCalc 2.2.0. Leaf consumer of scattering/v1 JSON from /micromegas or /formcalc.
---

# /ddcalc

Compute per-experiment log-likelihoods and WIMP exclusion verdicts using DDCalc
2.2.0. Leaf consumer: requires a `scattering/v1` JSON from `/micromegas`
(tree-level) or the FormCalc + LoopTools chain (loop-level). Prerequisite: DDCalc
installed (see `## Preflight: DDCalc`).

## Preflight: DDCalc

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/ddcalc/detect.sh

- **exit 0** → DDCalc is installed and registered in config; proceed.
- **exit non-zero** → DDCalc is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/ddcalc/INSTALL.md` into context and
  follow it. When the install completes, re-run `detect.sh` before proceeding.
  If it still fails, halt with the blocker code from the install reference.

## When to invoke

Invoke after obtaining a `scattering/v1` JSON from `/micromegas` (tree-level) or
the FormCalc + LoopTools loop-integral chain (loop-level). Never auto-selects
between sources — pass `--sigma-json` explicitly. Does not compute relic density,
indirect detection, or collider signals.

## Decision flow

```
/ddcalc run --sigma-json <path>
       │
       ├── config missing ddcalc_path → DDCALC_DRIVER_FAILED              exit 1
       ├── validate_scattering.py (jsonschema + NREFT guard)
       │       └── fails → DDCALC_INPUT_INVALID                           exit 1
       ├── m_dm_gev < 0.1 GeV → DDCALC_MASS_OUT_OF_RANGE (recoverable)   exit 1
       ├── resolve_halo() (SHM only in v1; non-SHM → DDCALC_INPUT_INVALID)
       ├── _ensure_driver() — build ddcalc_driver from source (cached)
       │       └── compile fail → DDCALC_DRIVER_FAILED                    exit 1
       ├── exec driver → ddcalc_driver <sigma_json>
       │       └── non-zero exit → DDCALC_DRIVER_FAILED                   exit 1
       ├── _parse_driver_stdout() → experiments dict
       └── emit ddcalc_result/v1 JSON to stdout + $STATE_ROOT/runs/ddcalc/<TS>/result.json

/ddcalc exclude --sigma-json <path>
       └── thin wrapper around run; emits verdict + excluded flags

/ddcalc scan-summary --scan-index <path>
       └── reads scan index JSON → calls run per point → ddcalc_scan.csv
```

## Subcommands

| Subcommand | Description |
|---|---|
| `run --sigma-json <path> [--halo <spec>] [--debug]` | Per-experiment logL + 90%-CL exclusion for one point |
| `exclude --sigma-json <path> [--cl 0.9]` | Verdict-only JSON for orchestration use |
| `scan-summary --scan-index <path>` | Reads scan dir, calls run per point, writes `ddcalc_scan.csv` |

## Input schema

`plugins/shared/schemas/scattering.schema.json` (`scattering/v1`). Canonical
field names:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | const `"scattering/v1"` | Required |
| `m_dm_gev` | number > 0 | Required |
| `sigma_si_proton_cm2` | number ≥ 0 | Required |
| `sigma_si_neutron_cm2` | number ≥ 0 | Required |
| `sigma_sd_proton_cm2` | number ≥ 0 | Required |
| `sigma_sd_neutron_cm2` | number ≥ 0 | Required |
| `source` | `"micromegas"`, `"looptools"`, or `"maddm"` | Required (`"maddm"` for tree-level σ_SI/σ_SD parsed from `MadDM_results.txt`) |
| `source_run` | path string | Required |
| `halo` | object or null | Optional; see below |
| `nucleon_form_factors` | `{"preset": "default_2018"|"A1"}` | Required |

Halo fields (if object): `model`, `v0_km_per_s`, `vesc_km_per_s`,
`rho0_gev_per_cm3`. If null or absent: SHM defaults (238 km/s, 544 km/s,
0.3 GeV/cm³).

## Output schema

`ddcalc_result/v1` (written to `$STATE_ROOT/runs/ddcalc/<TS>/result.json`):

```json
{
  "schema_version": "ddcalc_result/v1",
  "status": "ok",
  "verdict": "excluded" | "allowed" | "marginal",
  "m_dm_gev": 100.0,
  "experiments": {
    "XENON1T_2018": {"logL": -4.397586, "delta_chi2": 1.493639, "significance": 1.222145, "p_value": 0.2216527, "excluded_90cl": false},
    "LZ_projected": {"logL": -104.0234, "delta_chi2": 203.3188, "significance": 14.25899, "p_value": 3.94e-46, "excluded_90cl": true},
    "LUX_2016": {...},
    "PandaX_2017": {...},
    "PICO_60_2019": {...},
    "DarkSide_50": {...}
  },
  "neutrino_fog": {"source": "ddcalc_builtin_2.2.0"},
  "halo_used": {"model": "shm", "v0_km_per_s": 238, "vesc_km_per_s": 544, "rho0_gev_per_cm3": 0.3},
  "nucleon_form_factors_used": {"preset": "default_2018"},
  "inputs_echo": {...},
  "ddcalc_version": "2.2.0",
  "ddcalc_upstream_commit": "9364c02...",
  "experiment_set": "native",
  "experiment_overlay_sha": null
}
```

(The XENON1T_2018 and LZ_projected rows above are real measured values at
m_DM = 100 GeV, σ_SI = 1e-46 cm², SHM defaults — DDCalc's simplified
single-bin XENON1T likelihood does *not* exclude that point on its own;
LZ_projected does, so the overall verdict is "excluded".)

The result JSON is written to `$STATE_ROOT/runs/ddcalc/<TS>/result.json` and also
printed to stdout. For a human-readable summary, read `result.json` and render a
Markdown table from the `experiments` dict (one row per experiment: name, logL,
delta_chi2, p_value, excluded_90cl) inline — no separate `render_report.py` exists.

**Exclusion statistic — Wilks likelihood-ratio (calibrated 2026-07-11,
`ddcalc-pvalue-calibration`):** for each experiment the driver reports

- `delta_chi2 = -2 (lnL_signal - lnL_background)` — the one-parameter
  profile-likelihood-ratio test statistic, clamped `>= 0` (a signal fitting no
  worse than background carries no exclusion). `lnL_background` is DDCalc's
  log-likelihood at zero cross section (a second zero-signal WIMP handle).
- `significance = sqrt(delta_chi2)` — Gaussian-sigma Z.
- `p_value = erfc(sqrt(delta_chi2 / 2))` — the χ²₁ survival function, a real
  p-value in `[0, 1]`, monotone non-increasing in σ.
- `excluded_90cl = (p_value < 0.1)` ⇔ `(delta_chi2 > 2.706)` — the χ²₁ 90%
  quantile (equivalently `sqrt(-2 ΔlnL) > 1.645`). This is the asymptotic
  (Wilks) rule GAMBIT/DarkBit apply to DDCalc log-likelihoods; "90% CL" now
  carries an actual χ²/Wilks calibration.

This replaced two earlier statistics: DDCalc's own `DDCalc_ScaleToPValue`
(misused, pinned "p" near 1.0 — structurally unusable for high-count xenon
TPCs, see `ddcalc-diag/DIAGNOSIS.md`), and the interim `p = exp(lnL_signal -
lnL_background)` ratio (smooth/monotone but *uncalibrated* — its 0.1 cut is
Z≈2.15, not 90% CL — and it **underflowed to a hard 0** for large signals,
turning any bisection-for-p=0.1 into a numerical-underflow contour). **For
limit scans, bracket/bisect on `delta_chi2 = 2.706`, never on `p_value`**:
`delta_chi2` stays finite and monotone where `p_value` underflows to 0.

**Validation (SI, SHM defaults):** the `delta_chi2 > 2.706` crossing
reproduces the *published* per-nucleon SI limits of the analyses DDCalc
actually ships to within a factor ~2 across 30–200 GeV — LZ vs the LZ
*projected* design sensitivity (arXiv:1802.06039; see the LZ row below),
XENON1T_2018 vs the observed 1t·yr result (arXiv:1805.12562, ~1.7× weaker,
the known single-bin limitation). SD channel **liveness and isospin structure**
(PICO SD-proton-led, xenon TPCs SD-neutron-led) are covered separately (see
below). See `scripts/ddcalc_driver.c` (file header) for the full derivation.

**SD channel (fixed 2026-07-11):** the spin-dependent channel is live. DDCalc
loads its SD nuclear form factors from `DATA_DIR/SDFF/<Z>_<A>.dat`, where
`DATA_DIR` is a compile-time path; `run_ddcalc._ensure_ddcalc_data_symlinks`
heals that path for the `SDFF/` and `Wbar/` data dirs (previously only the
experiment dirs were healed, so DDCalc silently zeroed every SD rate — the
historical "dead SD channel" bug). PICO-60 (C3F8) is SD-proton-led and the
xenon TPCs are SD-neutron-led, as expected. Covered by
`tests/test_integration_pvalue_statistic.py::TestSDChannel`. A loud runtime
guard (`run_ddcalc._verify_sd_data_dirs`) refuses to run — emitting a
`DDCALC_DRIVER_FAILED` blocker — if the SD tables do not resolve, since a
zeroed SD form factor yields a finite background-equal lnL that would
otherwise pass silently; covered by `tests/test_sd_data_guard.py`.

## Blockers table

| Code | Mode | Cause | Resolution |
|---|---|---|---|
| `DDCALC_INPUT_INVALID` | fatal | Schema validation failed or NREFT present | Fix input JSON; check scattering/v1 schema |
| `DDCALC_MASS_OUT_OF_RANGE` | recoverable | m_DM < 0.1 GeV (sub-GeV) | Use DarkELF; `context.suggested_tool = "DarkELF"` |
| `DDCALC_DRIVER_FAILED` | fatal | Driver compile or runtime error | Check DDCalc install; `context.stderr_tail` |
| `DDCALC_NREFT_NOT_SUPPORTED` | fatal | `nreft_coefficients` key present in input | NREFT deferred to v1.1; remove key or wait for v1.1 |
| `DDCALC_OVERLAY_MISSING` | fatal | Overlay requested but files gone from disk | Re-run `_shared/installs/ddcalc/INSTALL.md install --with-overlay <name>` |

Forbidden blockers (not in codebase; grep-gated) — there is no analytic fallback,
so never emit these: `HEPPH_ALLOW_REFERENCE`, `DDCALC_REFERENCE_ONLY`
(removed per brainstorm §5), `allow-analytic-fallback`, `reference_only`.

## Native experiments (v1)

| Experiment | Paper | Kind |
|---|---|---|
| XENON1T_2018 | arXiv:1805.12562 | observed |
| LUX_2016 | arXiv:1602.03489 | observed |
| PandaX_2017 | arXiv:1708.06917 | observed |
| PICO_60_2019 | arXiv:1902.04031 | observed |
| DarkSide_50 | arXiv:1802.06994 | observed |
| LZ_projected | arXiv:1802.06039 | **projected sensitivity** |

**LZ is projected, not observed.** DDCalc 2.2.0's built-in `lz` analysis
(`C_DDCalc_lz_init`) is the LZ *projected design sensitivity* (arXiv:1802.06039,
~1000 live-days, min ~1.4e-48 cm²), so it is registered as **`LZ_projected`**.
It is **not** the observed LZ WS2022 first-results limit (arXiv:2207.03764, min
~9.2e-48 cm²): comparing the projected contour to the published observed limit
makes the toolkit look ~6× more stringent than LZ actually is. The `delta_chi2 >
2.706` crossing reproduces the *projected* SI curve within a factor ~2 across
30–200 GeV. The observed WS2022 analysis is the deferred `LZ_WS2024` overlay
(v1.1), absent from the native install.

Post-2022 observed experiments (LZ WS2022/WS2024, XENONnT 2023, PandaX-4T 2021)
require the overlay bundle, deferred to v1.1.

## Halo model (v1)

SHM only. Defaults: v₀=238 km/s, v_esc=544 km/s, ρ₀=0.3 GeV/cm³ (per 2506.19062,
Arcadi–Profumo convention). Halo values are echoed byte-identical into
`halo_used` in the output. Non-SHM halos (SHM++, Gaia-sausage) are v1.1;
`model != "shm"` triggers `DDCALC_INPUT_INVALID`.

## Neutrino floor (v1)

Default: DDCalc 2.2.0 built-in (no external CSV). Opt-in: `--nu-floor ohare_2021`
uses the vendored O'Hare 2021 SI Xenon floor (MIT license;
cajohare/NeutrinoFog@0df3d0c; data/neutrino_fog_ohare_2021.csv).

## Sharp edges

Playtest-surfaced gotchas from the Dark SU(3) run (2026-04-25). Build-time issues
are in `_shared/installs/ddcalc/INSTALL.md` sharp edges.

### SE-DD-1 — the native LZ analysis is projected, and must be registered as `LZ_projected` (FU-wsi-01)

**Symptom:** DDCalc runs without error but LZ is absent from the `experiments`
dict, OR an "LZ" curve reads ~6× more stringent than the published LZ WS2022
limit (a projected-sensitivity contour presented as the observed result).

**Root cause:** DDCalc 2.2.0 ships `C_DDCalc_lz_init` in `DDExperiments.hpp` and a
populated `LZ/` data directory, but (a) the v1 driver first omitted the
`register_exp(...)` call entirely, and (b) it was then registered under the
misleading name `LZ_2022`. The analysis is actually the LZ **projected design
sensitivity** (arXiv:1802.06039, min ~1.4e-48 cm²), *not* the observed WS2022
limit (arXiv:2207.03764, min ~9.2e-48 cm²). Only experiments explicitly
registered in the driver are available at runtime.

**Fixed** (`ddcalc-pvalue-calibration`, 2026-07-11): registered as
**`LZ_projected`** with its true identity documented; the `delta_chi2 > 2.706`
crossing reproduces the published *projected* SI curve within a factor ~2. The
observed WS2022 limit is the deferred `LZ_WS2024` overlay (v1.1).
**DARWIN is currently UNREGISTERED** — `C_DDCalc_darwin_init` exists
in `DDExperiments.hpp` but is absent from `ddcalc_driver.c`. Tier-2 follow-up:
add `register_exp("DARWIN", C_DDCalc_darwin_init)` and the corresponding data
symlink (see SE-DD-2 in `_shared/installs/ddcalc/INSTALL.md`).

### SE-DD-2 — DDCalc requires σ_SI / σ_SD inputs; raw SLHA not accepted (FU-wsi-03)

**Symptom:** Feeding a SLHA spectrum directly to `/ddcalc` triggers
`DDCALC_INPUT_INVALID` — the schema rejects it.

**Root cause:** DDCalc 2.2.0 takes nucleon-level cross sections (σ_SI(p), σ_SI(n),
σ_SD(p), σ_SD(n)) as inputs, not a SLHA spectrum. The `scattering/v1` JSON must be
produced by an upstream tool (typically `/micromegas` for tree-level, or the
FormCalc + LoopTools chain for loop-level) that computes the cross sections from
the model Lagrangian.

**Workflow:** `/micromegas` → `scattering/v1` JSON →
`/ddcalc run --sigma-json <path>`. Do not pass a SLHA file or raw Wilson
coefficients.

### SE-DD-3 — isoscalar p/n sanity check on σ_SI input (catch model-file bugs before the exclusion plot)

**Symptom:** The `scattering/v1` input has `sigma_si_proton_cm2` and
`sigma_si_neutron_cm2` differing by a large factor (~8×), or — from the upstream
nucleon *amplitudes* — proton and neutron SI amplitudes of **opposite sign**. The
exclusion verdict computed from it looks plausible but is wrong.

**Root cause — this is a MODEL-FILE bug, not physics.** For Higgs-portal /
scalar-exchange Majorana DM the only tree-level SI operator is scalar Higgs
exchange, which couples nearly isoscalar: every quark scalar coupling shares one
sign, so σ_SI(p) ≈ σ_SI(n) and **p/n ≈ 0.97** (micrOMEGAs' own default form
factors give `f_N^p = 0.2837` vs `f_N^n = 0.2868`). A large asymmetry or an
opposite-sign p/n amplitude is impossible for pure isoscalar Higgs exchange; it is
the fingerprint of a broken model file. The canonical case: an up/down Yukawa
**relative sign error** in the SARAH export made up-type couplings `+m_q/v` and
down-type `−m_q/v`, degrading the coherent nucleon sum to a small
isospin-violating residual — suppressing σ_SI **~200×** and faking p/n ≈ 8
(MadDM) / opposite-sign −4 (micrOMEGAs). There is **no** physical destructive
cancellation here (Majorana χ has no second tree SI operator to cancel against).

**One-line check (run before drawing any exclusion contour):** for scalar/Higgs-
portal Majorana DM, assert `0.9 ≲ sigma_si_neutron_cm2 / sigma_si_proton_cm2 ≲ 1.1`
(isoscalar) and reject any input whose upstream proton/neutron SI amplitudes carry
opposite signs. A failure means the upstream model file (SARAH quark-sector
Yukawa signs) is wrong — fix the model and regenerate; do **not** feed the number
to `run`/`exclude`. This is a sibling of the PR #1 SARAH quark-sector bug class
(there: h-q vertices silently zeroed; here: up-vs-down Yukawa relative sign).

## Notes and linkage

- `scripts/_parse_driver_stdout.py` is kept (not shed with the other regex
  parsers) because its
  `EXPERIMENT:/LOGL:/DELTACHI2:/SIGNIFICANCE:/PVALUE:/EXCLUDED90:/STATUS:/VERSION:`
  protocol is co-defined with `scripts/ddcalc_driver.c` in the same directory —
  both sides of the format live here, so format drift is caught in the same repo.
- Schema: `plugins/shared/schemas/scattering.schema.json`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Install skill: `_shared/installs/ddcalc/INSTALL.md`
- Data: `data/neutrino_fog_ohare_2021.csv` + `data/NOTICE`
- Overlays: `plugins/hep-ph-toolkit/_shared/installs/ddcalc/overlays/`
