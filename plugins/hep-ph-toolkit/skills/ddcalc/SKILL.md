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
    "XENON1T_2018": {"logL": -4.397586, "p_value": 0.4738713, "excluded_90cl": false},
    "LZ_2022": {"logL": -104.0234, "p_value": 7.08e-45, "excluded_90cl": true},
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

(The XENON1T_2018 and LZ_2022 rows above are real measured values at
m_DM = 100 GeV, σ_SI = 1e-46 cm², SHM defaults — DDCalc's simplified
single-bin XENON1T likelihood does *not* exclude that point on its own;
LZ_2022 does, so the overall verdict is "excluded".)

The result JSON is written to `$STATE_ROOT/runs/ddcalc/<TS>/result.json` and also
printed to stdout. For a human-readable summary, read `result.json` and render a
Markdown table from the `experiments` dict (one row per experiment: name, logL,
p_value, excluded_90cl) inline — no separate `render_report.py` exists.

**`p_value` statistic (fixed 2026-07-11):** `p_value` is a **likelihood ratio to
background-only**, `p = exp(lnL_signal - lnL_background)` (clamped to `[0, 1]`),
with `excluded_90cl = (p_value <= 0.1)`. This reduces to DDCalc's native
convention in the background-free limit; the ratio normalization follows the
standard GAMBIT/DarkBit generalization. It is *not* DDCalc's own
`DDCalc_ScaleToPValue` — that function takes a target log-p and returns a
sigma-scale factor, and is structurally unusable for high-count xenon TPCs
(XENON1T/LZ/PandaX/LUX): it guards on the background-only absolute
log-likelihood being near 0, which only holds for near-background-free
counting experiments (PICO, DarkSide). Behaviour is empirically verified for
**both the SI and SD channels** across every experiment in the registry. See
`scripts/ddcalc_driver.c` (file header) for the full derivation.

**SD channel (fixed 2026-07-11):** the spin-dependent channel is live. DDCalc
loads its SD nuclear form factors from `DATA_DIR/SDFF/<Z>_<A>.dat`, where
`DATA_DIR` is a compile-time path; `run_ddcalc._ensure_ddcalc_data_symlinks`
heals that path for the `SDFF/` and `Wbar/` data dirs (previously only the
experiment dirs were healed, so DDCalc silently zeroed every SD rate — the
historical "dead SD channel" bug). PICO-60 (C3F8) is SD-proton-led and the
xenon TPCs are SD-neutron-led, as expected. Covered by
`tests/test_integration_pvalue_statistic.py::TestSDChannel`.

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

| Experiment | Paper |
|---|---|
| XENON1T_2018 | arXiv:1805.12562 |
| LUX_2016 | arXiv:1602.03489 |
| PandaX_2017 | arXiv:1708.06917 |
| PICO_60_2019 | arXiv:1902.04031 |
| DarkSide_50 | arXiv:1802.06994 |

Post-2022 experiments (LZ WS2024, XENONnT 2023, PandaX-4T 2021) require the
overlay bundle, deferred to v1.1.

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

### SE-DD-1 — LZ_2022 must be explicitly registered (FU-wsi-01)

**Symptom:** DDCalc runs without error but LZ_2022 is absent from the
`experiments` dict in `ddcalc_result/v1` JSON.

**Root cause:** DDCalc 2.2.0 ships `C_DDCalc_lz_init` in `DDExperiments.hpp` and a
populated `LZ/` data directory, but the v1 driver omitted the
`register_exp("LZ_2022", C_DDCalc_lz_init)` call in `ddcalc_driver.c`. Only the 5
experiments explicitly registered in the driver are available at runtime.

**Fixed in tier-1** (T1.4, landed on main at `5355461`). LZ_2022 is now
registered. **DARWIN is currently UNREGISTERED** — `C_DDCalc_darwin_init` exists
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
  parsers) because its `EXPERIMENT:/LOGL:/PVALUE:/EXCLUDED90:/STATUS:/VERSION:`
  protocol is co-defined with `scripts/ddcalc_driver.c` in the same directory —
  both sides of the format live here, so format drift is caught in the same repo.
- Schema: `plugins/shared/schemas/scattering.schema.json`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Install skill: `_shared/installs/ddcalc/INSTALL.md`
- Data: `data/neutrino_fog_ohare_2021.csv` + `data/NOTICE`
- Overlays: `plugins/hep-ph-toolkit/_shared/installs/ddcalc/overlays/`
