---
name: ddcalc
description: Compute direct-detection likelihoods and 90%-CL exclusion verdicts using DDCalc 2.2.0. Leaf consumer of scattering/v1 JSON from /micromegas or /formcalc.
---

# /ddcalc

Compute per-experiment log-likelihoods and WIMP exclusion verdicts using DDCalc 2.2.0.
Leaf consumer: requires a `scattering/v1` JSON from `/micromegas` (tree-level) or the FormCalc + LoopTools chain (loop-level).
Prerequisite: DDCalc installed (see `## Preflight: DDCalc` below).

---

## Preflight: DDCalc

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/ddcalc/detect.sh

- **exit 0** → DDCalc is installed and registered in config; proceed.
- **exit non-zero** → DDCalc is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/ddcalc/INSTALL.md` into
  context and follow it. When the install completes, re-run `detect.sh`
  before proceeding. If it still fails, halt with the blocker code from
  the install reference.

---

## When to invoke

Invoke after obtaining a `scattering/v1` JSON from `/micromegas` (tree-level) or
the FormCalc + LoopTools loop-integral chain (loop-level). Never auto-selects between
sources — pass `--sigma-json` explicitly. Does not compute relic density, indirect
detection, or collider signals.

---

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

---

## Subcommands

| Subcommand | Description |
|---|---|
| `run --sigma-json <path> [--halo <spec>] [--debug]` | Per-experiment logL + 90%-CL exclusion for one point |
| `exclude --sigma-json <path> [--cl 0.9]` | Verdict-only JSON for orchestration use |
| `scan-summary --scan-index <path>` | Reads scan dir, calls run per point, writes `ddcalc_scan.csv` |

---

## Input schema

`plugins/shared/schemas/scattering.schema.json` (`scattering/v1`).
Canonical field names:

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

Halo fields (if object): `model`, `v0_km_per_s`, `vesc_km_per_s`, `rho0_gev_per_cm3`.
If null or absent: SHM defaults (238 km/s, 544 km/s, 0.3 GeV/cm³).

---

## Output schema

`ddcalc_result/v1` (written to `$STATE_ROOT/runs/ddcalc/<TS>/result.json`):

```json
{
  "schema_version": "ddcalc_result/v1",
  "status": "ok",
  "verdict": "excluded" | "allowed" | "marginal",
  "m_dm_gev": 100.0,
  "experiments": {
    "XENON1T_2018": {"logL": -17.3, "p_value": 3e-8, "excluded_90cl": true},
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

The result JSON is written to `$STATE_ROOT/runs/ddcalc/<TS>/result.json` and also
printed to stdout. To produce a human-readable summary, read `result.json` directly
and render a Markdown table from the `experiments` dict (one row per experiment:
name, logL, p_value, excluded_90cl). The agent renders this inline — no separate
`render_report.py` exists.

---

## Blockers table

| Code | Mode | Cause | Resolution |
|---|---|---|---|
| `DDCALC_INPUT_INVALID` | fatal | Schema validation failed or NREFT present | Fix input JSON; check scattering/v1 schema |
| `DDCALC_MASS_OUT_OF_RANGE` | recoverable | m_DM < 0.1 GeV (sub-GeV) | Use DarkELF; `context.suggested_tool = "DarkELF"` |
| `DDCALC_DRIVER_FAILED` | fatal | Driver compile or runtime error | Check DDCalc install; `context.stderr_tail` |
| `DDCALC_NREFT_NOT_SUPPORTED` | fatal | `nreft_coefficients` key present in input | NREFT deferred to v1.1; remove key or wait for v1.1 |
| `DDCALC_OVERLAY_MISSING` | fatal | Overlay requested but files gone from disk | Re-run `_shared/installs/ddcalc/INSTALL.md install --with-overlay <name>` |

Forbidden blockers (not in codebase; grep-gated):
- `HEPPH_ALLOW_REFERENCE` — no analytic fallback exists
- `DDCALC_REFERENCE_ONLY` — removed per brainstorm §5
- `allow-analytic-fallback` — no such mode
- `reference_only` — not a valid status in v1

---

## Native experiments (v1)

| Experiment | Paper |
|---|---|
| XENON1T_2018 | arXiv:1805.12562 |
| LUX_2016 | arXiv:1602.03489 |
| PandaX_2017 | arXiv:1708.06917 |
| PICO_60_2019 | arXiv:1902.04031 |
| DarkSide_50 | arXiv:1802.06994 |

Post-2022 experiments (LZ WS2024, XENONnT 2023, PandaX-4T 2021) require
the overlay bundle, deferred to v1.1.

---

## Halo model (v1)

SHM only. Defaults: v₀=238 km/s, v_esc=544 km/s, ρ₀=0.3 GeV/cm³
(per 2506.19062, Arcadi–Profumo convention). Halo values are echoed
byte-identical into `halo_used` in the output.

Non-SHM halos (SHM++, Gaia-sausage) are v1.1. Specifying `model != "shm"`
triggers `DDCALC_INPUT_INVALID`.

---

## Neutrino floor (v1)

Default: DDCalc 2.2.0 built-in (no external CSV). Opt-in: `--nu-floor ohare_2021`
uses the vendored O'Hare 2021 SI Xenon floor (MIT license;
cajohare/NeutrinoFog@0df3d0c; data/neutrino_fog_ohare_2021.csv).

---

## Parser note

`scripts/_parse_driver_stdout.py` was kept (not shed with the other regex parsers)
because its `EXPERIMENT:/LOGL:/PVALUE:/EXCLUDED90:/STATUS:/VERSION:` protocol is
co-defined with `scripts/ddcalc_driver.c` in the same directory — both sides of
the format live here, so format drift is caught in the same repo. This differs from
`parse_maddm_output` / `parse_micromegas_out` / `parse_sarah_log`, which parsed
upstream tool output whose format could change invisibly between tool versions.

---

## Sharp edges

Playtest-surfaced gotchas from the Dark SU(3) run (2026-04-25). See `_shared/installs/ddcalc/INSTALL.md`
sharp edges for build-time issues.

### SE-DD-1 — LZ_2022 must be explicitly registered (FU-wsi-01)

**Symptom:** DDCalc runs without error but LZ_2022 is absent from the `experiments`
dict in `ddcalc_result/v1` JSON.

**Root cause:** DDCalc 2.2.0 ships `C_DDCalc_lz_init` in `DDExperiments.hpp` and
a populated `LZ/` data directory, but the v1 driver omitted the
`register_exp("LZ_2022", C_DDCalc_lz_init)` call in `ddcalc_driver.c`. Only the
5 experiments explicitly registered in the driver are available at runtime.

**Fixed in tier-1** (T1.4, landed on main at `5355461`). LZ_2022 is now registered.

**DARWIN is currently UNREGISTERED** — `C_DDCalc_darwin_init` exists in
`DDExperiments.hpp` but is absent from `ddcalc_driver.c`. Tier-2 follow-up: add
`register_exp("DARWIN", C_DDCalc_darwin_init)` and the corresponding data symlink
(see SE-DD-2 in `_shared/installs/ddcalc/INSTALL.md`).

### SE-DD-2 — DDCalc requires σ_SI / σ_SD inputs; raw SLHA not accepted (FU-wsi-03)

**Symptom:** Attempting to feed a SLHA spectrum directly to `/ddcalc` triggers
`DDCALC_INPUT_INVALID` — the schema rejects it.

**Root cause:** DDCalc 2.2.0 takes nucleon-level cross sections (σ_SI(p), σ_SI(n),
σ_SD(p), σ_SD(n)) as inputs, not a SLHA spectrum. The `scattering/v1` JSON must be
produced by an upstream tool (typically `/micromegas` for tree-level, or the
FormCalc + LoopTools chain for loop-level) that computes the cross sections from the
model Lagrangian.

**Workflow:** `/micromegas` → `scattering/v1` JSON → `/ddcalc run --sigma-json <path>`.
Do not attempt to pass a SLHA file or raw Wilson coefficients.

---

## Linkage

- Schema: `plugins/shared/schemas/scattering.schema.json`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Install skill: `_shared/installs/ddcalc/INSTALL.md`
- Data: `data/neutrino_fog_ohare_2021.csv` + `data/NOTICE`
- Overlays: `plugins/hep-ph-toolkit/_shared/installs/ddcalc/overlays/`
