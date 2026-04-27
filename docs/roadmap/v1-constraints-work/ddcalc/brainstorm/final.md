# `/ddcalc` — Final synthesized design (v1)

Ships as **two skills** — `/ddcalc-install` and `/ddcalc` — inside a new
`plugins/constraints/` plugin co-hosting `/micromegas` and `/higgstools`.
Leaf consumer of σ_SI/σ_SD from `/micromegas` (tree-level) and `/formcalc`
(loop-level). Direct-detection likelihoods only. No relic density, no indirect
detection, no collider. Phase A, parallel to `/micromegas`.

This document reconciles the proposer and critic; where they disagreed, a
ruling is made and justified.

---

## 1. `/ddcalc-install`

**Upstream URL.** DDCalc's canonical home is the GAMBIT DarkBit ecosystem —
the authoritative mirror is `https://gitlab.com/ddcalc/ddcalc.git`. The
proposer's `C0RI0LIS/ddcalc` is a personal fork and is rejected. Because
neither the proposer nor critic could confirm the canonical URL with 100%
certainty from primary sources, the **first task of the planning phase** is a
verification step: clone both the GAMBIT-linked gitlab.com/ddcalc repo and
the HEPForge Redmine mirror (if reachable), confirm v2.2.0 tag exists, and
record the tag SHA. Block on `DDCALC_UPSTREAM_UNVERIFIED` if neither resolves.

**Version pin.** `HEPPH_DDCALC_VERSION=2.2.0` in `skill_env.yaml`. Tarball
`DDCalc-2.2.0.tar.gz`; SHA256 MUST be a real value before merge. Authoring
path: planning-phase implementer fetches once, records sha256 in
`skill_env.yaml`, commits. `verify_checksum`'s `TODO` placeholder path is
forbidden for this skill (contrast `/sarah-install` where network flakiness
justified it — DDCalc is one 6 MB tarball).

**Build.** Pure Fortran + tiny C shim. `gfortran` only; no LAPACK. Apple
Silicon quirks:
- Force `FFLAGS="-std=legacy -fallow-invalid-boz -O2"` in the install script
  (gfortran 13+ rejects DDCalc 2.2.0's legacy BOZ literals and implicit I/O).
- `CFLAGS="-Wno-implicit-function-declaration"` for the C shim under clang 15+.
- Smoke test parses `DDCalc_exampleC` stdout for a line matching
  `DDCalc\s+v?([0-9.]+)`; if stock 2.2.0 only prints the copyright banner
  (critic's Q6), add a one-line patch `src/DDCalc_util.f90` to print
  `DDCalc 2.2.0` on startup. The patch lives in
  `plugins/hep-ph-toolkit/skills/ddcalc-install/patches/version_banner.patch`.

**Subcommands.** `detect | use-path <dir> | install [<dir>]
[--with-overlay <spec>]`. Mirrors `/sarah-install` conventions.

**`HEPPH_NO_NETWORK=1`.** `install` fails closed with
`DDCALC_DOWNLOAD_FAILED` and `user_instruction` = "set `ddcalc_path` via
`/ddcalc-install use-path <dir>` or unset `HEPPH_NO_NETWORK`".

**Overlay install mode (RULING).** Adopt **option (a)**: overlays are
Fortran source patches applied to `src/experiments/` and recompiled into
`libDDCalc.a`. The critic is correct that exposure, binning, and likelihood
constructor are compiled code; rsync-over-data is broken.

- `install --with-overlay <name>` reads
  `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/<name>/manifest.yaml`
  (pinned upstream commit SHA, list of `.patch` files, list of new efficiency
  tables, SHA256 of each).
- The installer applies patches with `git apply --3way`, drops new tables
  into `data/experiments/<name>/`, and re-runs `make`.
- Config records `ddcalc_experiment_set`: the overlay name, and
  `ddcalc_experiment_overlay_sha`: SHA256 of the concatenated manifest.
- Rejected option (b) — "defer post-2022 limits to v1.1 and mark
  `reference_only`" — violates the blocker schema (`reference_only` is a
  result status, not an experiment-availability flag) and conflicts with the
  "augment not replace" rule.

**Blockers (install).** `DDCALC_DOWNLOAD_FAILED` (fatal),
`DDCALC_BUILD_FAILED` (fatal, `context.build_log_tail`),
`DDCALC_SMOKE_TEST_FAILED` (fatal), `DDCALC_PATH_INVALID` (fatal),
`DDCALC_OVERLAY_APPLY_FAILED` (fatal, `context.patch_reject_files`),
`GFORTRAN_ABSENT` (fatal, reuses `EXIT_NO_GFORTRAN`),
`DDCALC_UPSTREAM_UNVERIFIED` (fatal, planning-phase only).

**Config keys.** `ddcalc_path`, `ddcalc_version`, `ddcalc_installed_at`,
`ddcalc_experiment_set`, `ddcalc_experiment_overlay_sha`,
`ddcalc_upstream_url`, `ddcalc_upstream_commit`.

---

## 2. `/ddcalc` usage skill

**Subcommands.** Three only: `run`, `exclude`, `scan-summary`. `debug-dump`
is folded into `run --debug`. No `marginalize-halo` in v1.

- `ddcalc run --sigma-json <path> [--halo <spec>] [--debug]` —
  per-experiment logL + 90 %CL exclusion verdict for one point.
- `ddcalc exclude --sigma-json <path> [--cl 0.9]` — thin wrapper that emits
  only the verdict JSON (for orchestration use).
- `ddcalc scan-summary --scan-index <path>` — reads a `/spheno-build` or
  `/micromegas` scan dir, calls `run` per point, writes
  `$STATE_ROOT/models/<name>/ddcalc_runs/<TS>/ddcalc_scan.csv`. Never
  overwrites upstream scan artefacts. Serial execution. File lock at
  `$STATE_ROOT/.locks/ddcalc` (flock) around any rebuild-dependent op
  (none in v1, but reserved).

**Input schema.** Validated against
`plugins/shared/schemas/scattering.schema.json` (**snake_case**,
consumer-wins-from-critique):

```
m_dm_gev                : number > 0
sigma_si_proton_cm2     : number >= 0
sigma_si_neutron_cm2    : number >= 0  (defaults to sigma_si_proton_cm2)
sigma_sd_proton_cm2     : number >= 0  (defaults to 0)
sigma_sd_neutron_cm2    : number >= 0  (defaults to 0)
source                  : enum {"micromegas","looptools"}
source_run              : path-string
schema_version          : const "scattering/v1"
halo                    : object (optional; see below)
nucleon_form_factors    : object (optional; f_Tu, f_Td, f_Ts, f_TG, citation)
```

**Halo default.** SHM with `v0=238 km/s`, `vesc=544 km/s`, `rho_0=0.3
GeV/cm^3` (McCabe 2010 / Arcadi–Profumo 2506.19062 convention). DDCalc's
built-in SHM uses (235, 550, 0.3); the skill overrides via `SetHalo` on
every call and records the chosen values in the output JSON. Non-SHM halos
(SHM++, Gaia-sausage) deferred to v1.1.

**NREFT / form-factor / CP-violation inputs.** v1 rejects with
`DDCALC_NREFT_NOT_SUPPORTED` (fatal). Schema carries an optional
`nreft_coefficients` key purely so upstream producers can start filling it
now without invalidating; `/ddcalc` treats its presence as a fatal.

**Precedence when both tree-level (`/micromegas`) and loop-level
(`/formcalc`) scattering exist for the same point:** `/ddcalc` does NOT
auto-select. It requires an explicit `--sigma-json` path. The orchestrator
in Phase C is responsible for choosing which producer's JSON to feed in.
This matches the "leaf consumer" discipline.

---

## 3. Experiment list for v1

Native (DDCalc 2.2.0, compiled from stock `src/experiments/`):

| Experiment         | Status | Data-table path                        |
|--------------------|--------|----------------------------------------|
| LUX 2016           | native | `data/experiments/LUX_2016.eff`        |
| PandaX-II 2017     | native | `data/experiments/PandaX_2017.eff`     |
| XENON1T 2018       | native | `data/experiments/XENON1T_2018.eff`    |
| PICO-60 2019       | native | `data/experiments/PICO_60_2019.dat`    |
| DarkSide-50 2018   | native | `data/experiments/DarkSide_50_2018.eff`|

Overlay (installable via `--with-overlay lz_xenonnt_pandax4t_2024`):

| Experiment         | Overlay path                                          | Pinned SHA256 |
|--------------------|-------------------------------------------------------|---------------|
| LZ WS2024          | `overlays/.../src/experiments/LZ_WS2024.f90`+`.eff`   | recorded at overlay publication |
| XENONnT 2023       | `overlays/.../src/experiments/XENONnT_2023.f90`+`.eff`| recorded at overlay publication |
| PandaX-4T 2021     | `overlays/.../src/experiments/PandaX_4T_2021.f90`+`.eff` | recorded at overlay publication |

Each overlay file's SHA256 is pinned in the overlay `manifest.yaml`; the
concatenated manifest SHA is stamped into every output JSON as
`experiment_overlay_sha`. Overlay Fortran modules are derived from published
efficiency + exposure tables; provenance + licence notes in
`plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/<name>/NOTICE`.

If the overlay manifest authoring stalls, v1 ships with only the native set
and the 2506.19062 reproduction uses XENON1T 2018 as the benchmark. This is
documented as a known gap — but the skill still works and `/ddcalc scan-summary`
still produces a figure.

---

## 4. Neutrino fog (RULING)

**Default: DDCalc's built-in ν-floor**, accessed via DDCalc's own C API.
Reason: matches "augment not replace" and gives us audit-free provenance.
Output JSON records `neutrino_fog.source = "ddcalc_builtin_2.2.0"`.

O'Hare 2021 is available as an opt-in overlay driven by `--nu-floor
ohare_2021`. In that mode we **do** vendor
`plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_ohare_2021.csv` with a
`NOTICE` file crediting "O'Hare, PRL 127, 251802 (2021)" and a pointer to the
public GitHub notebook (MIT-licensed). Before merge, verify the actual
licence on the source data and the specific curve used in Fig. 6/7 of
2506.19062 (open question carried into planning).

Output JSON field names are fixed regardless of source:
```
neutrino_fog: {source, definition ("discovery_limit_90cl"|"fog_gradient_n=2"), n_sigma_above_floor, in_fog: bool}
```

---

## 5. Output contract

Per-experiment JSON `$STATE_ROOT/runs/ddcalc/<TS>/result.json`:

```
{
  "schema_version": "ddcalc_result/v1",
  "status": "ok",
  "verdict": "excluded"|"allowed"|"marginal",
  "m_dm_gev": 62.5,
  "experiments": {
    "XENON1T_2018": {"logL": -17.3, "p_value": 3e-8, "excluded_90cl": true},
    "LZ_WS2024":    {...}
  },
  "neutrino_fog": {"source": "ddcalc_builtin_2.2.0", ...},
  "halo_used": {"model":"SHM","v0_kms":238,"vesc_kms":544,"rho0_gev_cm3":0.3},
  "nucleon_form_factors_used": {...},
  "inputs_echo": {...},
  "ddcalc_version": "2.2.0",
  "ddcalc_upstream_commit": "<sha>",
  "experiment_set": "native"|"lz_xenonnt_pandax4t_2024",
  "experiment_overlay_sha": "<sha256>|null",
  "report_path": "$STATE_ROOT/runs/ddcalc/<TS>/report.md"
}
```

Plus `report.md` (markdown) and, for scan mode, `ddcalc_scan.csv` with one
row per input point (columns: `point_idx, m_dm_gev, sigma_si_proton_cm2,
verdict, logL_<expt>..., n_sigma_fog`).

**Blockers (usage).** `DDCALC_INPUT_INVALID` (fatal),
`DDCALC_MASS_OUT_OF_RANGE` (recoverable; `context.suggested_tool` if
sub-GeV), `DDCALC_DRIVER_FAILED` (fatal),
`DDCALC_NREFT_NOT_SUPPORTED` (fatal),
`DDCALC_OVERLAY_MISSING` (fatal — overlay referenced in config but files
gone from disk). **Removed:** `DDCALC_REFERENCE_ONLY` and
`HEPPH_ALLOW_REFERENCE`. There is no Lewin-Smith analytic path.

---

## 6. Test matrix

- **Unit (always on):** input-schema validation, halo-override logging,
  blocker JSON conforms to `blocker.schema.json`, output conforms to
  `ddcalc_result/v1`.
- **Integration (gated on `HEPPH_RUN_NETWORK_TESTS=1`):** real
  `/ddcalc-install install`; smoke run; verify native experiment list.
- **Golden fixture (gated):** σ_SI_p = σ_SI_n = 1e-46 cm², m_DM = 100 GeV,
  no SD. Expected: **excluded** by XENON1T 2018 (p < 1e-3, known from
  XENON1T Fig. 5). Tolerance ±10 % on logL. When the overlay is installed,
  add a second assertion: **excluded** by LZ WS2024 (p < 1e-6).
- **Schema round-trip fixture:** `/micromegas` sample JSON +
  `/formcalc` sample JSON each pass `scattering.schema.json` validation
  and produce identical `verdict` from `/ddcalc run`.

---

## 7. Resolved open questions / carried-forward to planning

Resolved here:
- Halo marginalization → v1.1.
- Isospin-violating input → accepted (schema supports it).
- Sub-GeV / Migdal → out of scope; `DDCALC_MASS_OUT_OF_RANGE` recoverable.
- Scan parallelism → serial, matches `/spheno-build`.
- `/micromegas` vs `/formcalc` precedence → orchestrator chooses; `/ddcalc`
  never auto-selects.
- Plugin placement → `plugins/constraints/` with `_shared/` dir for overlays;
  shared schema at `plugins/shared/schemas/scattering.schema.json`;
  `CLAUDE.md` category table + `marketplace.json` updated in a single prep
  PR landing before any of the three constraint skills.
- Shared p-value helper → `plugins/shared/pvalue.py` created in prep PR.

Carried to planning phase (must resolve before implementation PR):
1. Verify canonical DDCalc URL (task: clone, tag-check, record SHA).
2. Compute real DDCalc 2.2.0 tarball SHA256; commit to `skill_env.yaml`.
3. Confirm `DDCalc_exampleC` version-print behaviour; decide whether the
   banner patch is needed.
4. Confirm licence for O'Hare 2021 CSV vendoring; write `NOTICE`.
5. Confirm the actual ν-floor curve used in Fig. 6/7 of 2506.19062.
6. Author the `lz_xenonnt_pandax4t_2024` overlay manifest (Fortran modules
   + efficiency tables + SHA pins). If stall > 1 week, ship v1 with native
   experiments only and XENON1T 2018 as the reproduction benchmark.
