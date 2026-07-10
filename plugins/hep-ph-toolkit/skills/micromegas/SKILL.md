---
name: micromegas
description: Compute DM relic density, direct/indirect-detection cross-sections, and annihilation spectra using micrOMEGAs 6.0.5.
---

# /micromegas

Drive micrOMEGAs 6.0.5 to compute dark matter observables from SARAH/SPheno model output:
relic density Ωh², spin-independent and spin-dependent nucleon cross-sections, annihilation
channels, and indirect-detection spectra. Does not reimplement physics — all calculations
are delegated to micrOMEGAs.

> **micrOMEGAs is a direct-detection cross-check only for singlet-doublet — NOT a relic authority.** The native micrOMEGAs route builds from SARAH's `MakeCHep[]` CalcHEP export, which has no `IMZNMIX` slot, so Majorana phases are silently dropped. The resulting relic density is invalid for singlet-doublet (Ωh² ≈ 0.0742 vs the validated 0.2916) — do not report micrOMEGAs Ωh² for this model or compute Planck pulls from it. Use micrOMEGAs only as a σ_SI/σ_SD direct-detection cross-check; **MadDM is the relic authority.**

---

## Preflight: micrOMEGAs

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/micromegas/detect.sh

- **exit 0** → micrOMEGAs is installed and registered in config; proceed.
- **exit non-zero** → micrOMEGAs is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/micromegas/INSTALL.md` into
  context and follow it. When the install completes, re-run `detect.sh`
  before proceeding. If it still fails, halt with the blocker code from
  the install reference.

---

## When to invoke

Invoke `/micromegas` after:
1. micrOMEGAs is installed (see `## Preflight: micrOMEGAs` above) and `config.micromegas_path` is set.
2. `/sarah-build` has produced a UFO model at `config.models[<name>].ufo_path`
   (unless using `--precompiled`).
3. `/spheno-build` has produced an SLHA spectrum at `config.models[<name>].latest_slha`.
4. A `spec.yaml` with `dm_candidate` is present at `config.models[<name>].spec_yaml`
   (or provided via `--spec`).

If any prerequisite is missing, the skill emits `MICROMEGAS_INPUT_MISSING` (fatal) with
`context.missing` listing what is absent.

---

## Subcommands

```
/micromegas relic      <model> [options]
/micromegas scatter    <model> [options]
/micromegas annihilate <model> [options]
/micromegas indirect   <model> [options]
```

| Subcommand | Computes |
|------------|---------|
| `relic` | Ωh², Xf, Beps sensitivity probe, Planck comparison |
| `scatter` | σ_SI(p,n), σ_SD(p,n) |
| `annihilate` | ⟨σv⟩(v→0), channel fractions |
| `indirect` | Photon/positron/antiproton/neutrino spectra via PPPC4DMID |

**Note:** `/micromegas all` is not implemented in v1. The orchestrator (`/lagrangian-builder`)
composes subcommands.

---

## Prerequisites (state contracts)

| Config key | Source skill | Required for |
|------------|-------------|-------------|
| `config.micromegas_path` | `_shared/installs/micromegas/INSTALL.md` | All subcommands |
| `config.models[<name>].ufo_path` | `/sarah-build` | All (unless `--precompiled`) |
| `config.models[<name>].latest_slha` | `/spheno-build` | DM mass resolution |
| `config.models[<name>].spec_yaml` | User-authored | DM candidate identification |

---

## DM candidate resolution (`spec.yaml > CLI > auto-detect`)

Spec loading routes through `plugins/shared/runner_spec_loader.py`
(legacy scalar still accepted; new specs SHOULD use the object
form). The router validates the normalized spec against
`plugins/shared/schemas/runner_spec.schema.json`.
Migration note: Existing scalar-form spec.yaml files continue
to work; no manual update required.

The DM candidate is resolved in strict priority order:

1. **`spec.yaml`** `dm_candidate.pdg` — wins unconditionally. Recommended.
2. **`--dm-pdg <id>`** — used only when spec omits `dm_candidate`.
   Writes `runs/<TS>/dm_override.json` and logs a notice.
3. **`--auto-detect`** — explicit opt-in only. Parses SLHA + UFO particle attributes.
   Refuses ambiguous cases with recoverable `DM_CANDIDATE_AMBIGUOUS`.

Charged or colored LSP → `DM_CANDIDATE_UNPHYSICAL` / `DM_CANDIDATE_COLOR_MISMATCH` (fatal).
Two stable Z2-odd candidates → `MULTICOMPONENT_UNSUPPORTED` (fatal, v1).

---

## Options

```
--dm-pdg <id>          PDG id override (spec.yaml wins)
--auto-detect          Auto-detect DM candidate
--spec <yaml>          Path to spec.yaml
--slha <path>          Path to SLHA spectrum file
--precompiled <proj>   Use micrOMEGAs-shipped project (MSSM|NMSSM|singletDM|IDM)
--output-dir <dir>     Run output directory
--scan NAME=start:stop:step=s  Scan axis (repeatable)
```

---

## Outputs

Per run: `$STATE_ROOT/models/<name>/micromegas_runs/<TS>/`

| File | Content |
|------|---------|
| `main.c` | Generated micrOMEGAs driver (HEPPH_MICROMEGAS_SEED=42) |
| `stdout.log` | Raw micrOMEGAs output |
| `summary.json` | Validated against `plugins/shared/schemas/scattering.schema.json` |
| `relic.json` | Relic density result; validated against `plugins/shared/schemas/relic.schema.json` (`relic/v1`) |
| `annihilation.json` | Annihilation cross-section at v→0; validated against `plugins/shared/schemas/annihilation.schema.json` (`annihilation/v1`) |
| `report.md` | Human-readable with Planck comparison |
| `spectra.h5` | Indirect-detection spectra (indirect subcommand) |

Scan mode writes `scan_index.csv` with columns:
`index, <params>, omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0, status, blocker_code, run_dir, timing_s`.

---

## Scan mode (v1.1 backlog)

**Scan execution is deferred to v1.1.** Invoking `/micromegas --scan` emits a
recoverable `MICROMEGAS_SCAN_NOT_IMPLEMENTED` blocker. The grid-logic library
(`expand_axis`, `parse_scan_arg`, CSV column layout) is implemented and tested;
the per-point `run_point.run()` wiring is the v1.1 deliverable.

Planned usage (v1.1):
```
/micromegas relic singletDM --scan m_s=50:200:step=50 --scan lhs=0.01:0.1:step=0.01
```

Axes will be expanded to Cartesian product; runs will be serial (deterministic
ordering). Recoverable failures will mark the row `status=recoverable` and
continue. The CSV will be byte-identical across runs given the same inputs.

---

## Recoverable vs fatal contract

| Code | Mode | Notes |
|------|------|-------|
| `MICROMEGAS_INPUT_MISSING` | fatal | Config or file missing |
| `DM_CANDIDATE_AMBIGUOUS` | recoverable | `--auto-detect` only |
| `DM_CANDIDATE_UNPHYSICAL` | fatal | Charged LSP |
| `DM_CANDIDATE_COLOR_MISMATCH` | fatal | Colored LSP |
| `MULTICOMPONENT_UNSUPPORTED` | fatal | Two stable DM candidates (v1) |
| `UFO_CONVERT_FAILED` | fatal | **Vestigial** — presupposes a UFO→CalcHEP importer that does not ship (sharp edge #4). Use the SARAH `MakeCHep[]` export instead. |
| `CALCHEP_CONVERTER_VERSION_SKEW` | fatal | **Vestigial** — same dead UFO-importer path as `UFO_CONVERT_FAILED` (sharp edge #4). |
| `MICROMEGAS_PROJECT_BUILD_FAILED` | fatal | `make main` non-zero |
| `MICROMEGAS_RUNTIME_FAILURE` | recoverable | Binary crash on scan point |
| `OMEGA_UNCONVERGED` | recoverable | NaN/negative Ωh² |
| `RELIC_BEPS_SENSITIVE` | recoverable | Ωh² shifts >20% between Beps probes |

No `reference_only` state or analytic fallback — per manager rule.

---

## Data contracts

**Input from `/sarah-build`:** the CalcHEP model files (`{prtcls1,vars1,func1,lgrng1}.mdl`)
from the SARAH `MakeCHep[]` export (sharp edge #1/#4) — SARAH must have run
`MakeCHep[]`/`WriteCalcHEP[]` alongside the UFO. (The `sha256(ufo_dir_tar) || … ||
ufo_dialect` cache key documented here belonged to the vestigial UFO→CalcHEP
converter path — see sharp edge #4; there is no UFO importer to cache.)

**Input from `/spheno-build`:** SLHA at `config.models[<name>].latest_slha`.

**Output to `/ddcalc`:** `summary.json` flat top-level keys (canonical scattering/v1 schema).
`/ddcalc` reads `summary.json` directly; no separate `scattering.json`.

**Cosmology:** always `"standard_thermal"` in v1.

**Nucleon form factors:** `"default_2018"` (micrOMEGAs built-in lattice) or `"A1"` (Arcadi–Profumo).

---

## Sharp edges

### 1. CalcHEP `.mdl` files required — `WriteCalcHEP[]` is not optional (FU-wsg-01)

**Symptom:** micrOMEGAs refuses to load the model or the driver fails at the
`CalcHEP/work/` setup step with errors about missing `.mdl` files or an empty
`models/` directory.

**Cause:** micrOMEGAs uses CalcHEP-format model files (`.mdl`, `func1.mdl`,
`vars1.mdl`, etc.) internally. SARAH's `WriteUFO[]` and `WriteSPheno[]` outputs
do not include these files; only `WriteCalcHEP[]` produces them.

**Fix:** In the SARAH run for the model, call `WriteCalcHEP[]` before exiting.
The output directory (`CalcHEP/`) must be present alongside the UFO output before
`/micromegas` is invoked. Models built with only `WriteUFO[]`/`WriteSPheno[]`
will block the driver unconditionally.

---

### 2. `Mcdm` is a micrOMEGAs C macro — do not shadow it in driver code (FU-wsg-01)

**Symptom:** Compilation of the generated `main.c` fails with a macro-redefinition
error or a confusing type error on any line that declares a local variable named
`Mcdm`.

**Cause:** micrOMEGAs 6.x defines `Mcdm` as a C preprocessor macro in its header
files. Declaring a local or global variable with the same name causes a redefinition
conflict or silently replaces the variable reference with the macro expansion.

**Fix:** Use a different local name for the DM mass variable in generated driver
code (e.g., `dm_mass_gev`, `mDM`, `mass_dm`). Do not use `Mcdm` as a C identifier
in any driver source file.

---

### 3. `vSigmaA(0.0)` returns NaN in 6.0.5 — use `calcSpectrum()` instead (FU-wsg-02)

**Symptom:** The annihilation cross-section at v→0 is `NaN` in `stdout.log` and
`annihilation.json` records `sigma_v_zero: null` with `OMEGA_UNCONVERGED` flagged,
even when the relic density converged cleanly.

**Cause:** In micrOMEGAs 6.0.5, the function `vSigmaA(0.0)` has a known numerical
issue at exactly v=0 and returns NaN. This is a version-specific defect; it does
not affect the relic density calculation path (`darkOmega`).

**Fix:** Call `calcSpectrum(0, Xf, fast, Beps, &Xf, &omgh2)` (or the equivalent
spectrum function) to obtain ⟨σv⟩ at v→0. The result is available via `vSigmaA()`
after `calcSpectrum()` has been called. Do not call `vSigmaA(0.0)` directly in
6.0.5 driver code.

---

### 4. There is no UFO→CalcHEP importer — "Route A" does not exist; use SARAH `MakeCHep[]`

**Symptom:** You reach for a UFO→CalcHEP conversion step (a `ufo_to_calchep`
"Route A") and find no such tool. `newProject <X>` only unpacks a blank CalcHEP
project template; there is no `ufo`/import binary anywhere in the micrOMEGAs or
bundled-CalcHEP tree.

**Cause:** micrOMEGAs 6.1.x and its bundled CalcHEP ship **no UFO importer**. The
only supported way to get CalcHEP `.mdl` files for a SARAH model is to export them
from SARAH directly. (`scripts/ufo_to_calchep.sh` / the `UFO_CONVERT_FAILED`
blocker presuppose an importer that this distribution does not contain.)

**Fix — Route B (the working route):** generate the CalcHEP model in the same
SARAH session that produced the UFO:

```wolfram
Get["…/SARAH.m"]; Start["<ModelName>"]; MakeCHep[]
```

`MakeCHep[]` == SARAH's `WriteCalcHEP[]` (sharp edge #1). It writes
`{prtcls1,vars1,func1,lgrng1}.mdl` under
`Output/<ModelName>/EWSB/CHep/`; copy them into the micrOMEGAs project's
`work/models/` and hand-author a minimal `extlib1.mdl` (SARAH does not emit that
one). Because it comes from the same SARAH source as the UFO, the CalcHEP export
is consistent with what MadDM consumes. Verified end-to-end for singlet-doublet
(28.5 s export) on native arm64 micrOMEGAs 6.1.15.

**Version note:** this skill's pin is 6.0.5, but neither bundled CalcHEP ships a
UFO importer — the fact is version-independent (6.0.5 and 6.1.x alike). The
network-fallback install actually lands **6.1.15** (Zenodo mirror; see the install
reference), which is the build these gotchas were reproduced on.

---

### 5. SARAH-CalcHEP export is real-mixing-only (no `IMZNMIX`) — relic is invalid for negative Majorana eigenvalues

**Symptom:** For a Majorana model with a **negative** fermion mass eigenvalue,
micrOMEGAs' relic density lands in a known-invalid family — for singlet-doublet
`canonical-2026` (MS=150, MPsi=500, yh1=1, yh2=0, θ=0): **Ωh² = 0.0742** with
**χ1χ1→hZ spuriously dominant at 52.8%** (h h 30.4%, W⁺W⁻ 8.8%, ZZ 6.1%),
versus the correct **MadDM Ωh² = 0.2916** whose decomposition has WW dominant
(~33.5%) and Zh subdominant (~20%). The `hZ`-dominant signature is the tell.

**Cause:** SARAH's CalcHEP export reads the **real `ZNMIX` only** (`func1.mdl`:
`slhaVal("ZNMIX",…)`) — there is **no `IMZNMIX` slot at all**. The Majorana phase
of the negative eigenvalue (carried as `IMZNMIX` in the SPheno/UFO convention
MadDM uses) is silently dropped, so the real-orthogonal mixing corrupts the
χ2/χ3 t-channel interference in χ1χ1→hZ. The physically-correct alternative —
real eigenvectors with a **signed** negative mass — **SEGFAULTS** micrOMEGAs/
CalcHEP (`RUN=139` = SIGSEGV in the width/phase-space machinery; the failing card
differs from the working one by a single sign bit). You cannot represent the
phase in this path either way.

**Rule:** For models with complex/negative Majorana mixing, **MadDM (UFO path,
complex `ZN`/`IMZNMIX`) is the relic authority**; micrOMEGAs-via-CalcHEP is a
**DD / σ_SI / σ_SD cross-check tool only** and MUST NOT arbitrate Ωh² for such
models. (σ_SI is unaffected when the DM candidate is the *positive* eigenvalue —
its `IMZNMIX` row is identically zero, so its own couplings are phase-free.) This
matches `/dark-matter-constraints`' MadDM-primary policy.

---

### 6. `CDM1` global comes back NULL for SARAH models — use `sortOddParticles(cdmName)`

**Symptom:** Printing or passing the `CDM1` global segfaults
(`nucleonAmplitudes(WIMP=CDM1)` → `pMass(NULL)` → `strcmp(NULL)`), even though the
relic and spectrum ran fine.

**Cause:** For a SARAH-generated CalcHEP model, micrOMEGAs' `CDM1` global is not
populated (comes back NULL); the DM name is only available from
`sortOddParticles(cdmName)`.

**Fix:** Use the name filled by `sortOddParticles(cdmName)` (e.g. `~Chi1`) for the
DM candidate everywhere the driver needs it — that is what `nucleonAmplitudes`
must receive. The `Mcdm` mass macro is fine to use; only the `CDM1` name global is
the trap. (See sharp edge #2 for the separate `Mcdm`-as-identifier hazard.)

---

## Fixture and testing notes

Unit tests are always-on. Integration tests require `HEPPH_RUN_NETWORK_TESTS=1`.
The golden fixture uses the micrOMEGAs-shipped `Singlet_DM/` benchmark project
(no hand-authored arithmetic). See `scripts/regenerate_fixture.py`.

---

## Physics scope (v1)

**In-scope:**
- Relic density Ωh² via `darkOmega(&Xf, fast=1, Beps=1e-6)`.
- Planck 2018 target: Ωh² = 0.120 ± 0.0012.
- Beps sensitivity probe at 1e-4 and 1e-6 (coannihilation-wall detection).
- Tree-level σ_SI and σ_SD on proton and neutron via `nucleonAmplitudes()`.
- Annihilation at v→0: `sigma_v_zero`, channel fractions, freeze-out Xf.
- Indirect spectra via shipped PPPC4DMID tables.

**Out of scope (v1.1):**
- `/micromegas --scan` execution (grid logic exists; `run_point.run()` wiring deferred;
  emits `MICROMEGAS_SCAN_NOT_IMPLEMENTED` recoverable blocker when invoked).
- NREFT operator-basis σ (Anand–Fitzpatrick–Haxton).
- Asymmetric DM / `darkOmega2` two-component path.
- Loop-level σ_SI blind-spot analysis (Phase B FormCalc + LoopTools chain).
- Non-standard cosmologies.
- micrOMEGAs 6.1.x / UFO 2.0.

---

## Scripts reference

| Script | Purpose |
|--------|---------|
| `scripts/run_micromegas.py` | CLI entry point (subcommand routing, DM resolution) |
| `scripts/run_point.py` | Single-point execution; writes `stdout.log`; returns log path |
| `scripts/scan.py` | Sequential Cartesian-product scan |
| `scripts/main_c_template.py` | Deterministic C driver generator (SEED=42) |
| `scripts/parse_slha_mass_block.py` | SLHA Block MASS reader |
| `scripts/resolve_dm_candidate.py` | DM candidate resolver (spec>CLI>auto-detect) |
| `scripts/ufo_to_calchep.sh` | **Vestigial** — no UFO→CalcHEP importer ships (sharp edge #4); the working route is SARAH `MakeCHep[]`. Do not rely on this. |
| `scripts/build_project.sh` | `make main` + log tail |
| `scripts/regenerate_fixture.py` | Regenerate golden from shipped Singlet_DM benchmark |

### Reading micrOMEGAs output (agent-driven)

**Steady-state path (post-W4-B):** when `relic.json` and `annihilation.json` exist alongside `summary.json`, downstream skills MUST prefer the schema-pinned JSONs and treat the stdout regex extraction as a legacy fallback for hand-driven runs predating those schema files.

After a successful run, the raw micrOMEGAs stdout is written to
`<run_dir>/stdout.log`. Open that file and extract:

- **Omega h^2**: line matching `Omega h^2 = <value>` (case-insensitive).
  Example: `Omega h^2 = 0.119  Xf = 22.4`
- **Freeze-out parameter**: same line, `Xf = <value>`
- **SI cross-sections**: lines matching `sigma_SI(p) = <value> cm^2` and
  `sigma_SI(n) = <value> cm^2`
- **SD cross-sections**: lines matching `sigma_SD(p) = <value> cm^2` and
  `sigma_SD(n) = <value> cm^2`
- **Annihilation at v=0**: line matching `sigma_v(v=0) = <value> cm^3/s`
- **Channel fractions**: lines with pattern `<particle1> <particle2> <pct>%`,
  e.g. `b b~ 62.3%`. Divide percentage by 100 for fraction.

If `Omega h^2` is `NaN` or negative, record `omega_h2: null` and flag
`OMEGA_UNCONVERGED`. If the field is completely absent, raise an error —
do not silently return zero values.

Assemble and emit as `summary.json` with `scattering/v1` schema:
```json
{
  "schema_version": "scattering/v1",
  "m_dm_gev": <float>,
  "sigma_si_proton_cm2": <float>,
  "sigma_si_neutron_cm2": <float>,
  "sigma_sd_proton_cm2": <float>,
  "sigma_sd_neutron_cm2": <float>,
  "source": "micromegas",
  "source_run": "<run_identifier>",
  "nucleon_form_factors": {"preset": "default_2018"},
  "halo": null
}
```
Use 0.0 for any cross-section that is absent or negative (schema requires
non-negative values). Write `summary.json` to `<run_dir>/summary.json`.

In the steady-state path (post-W4-B), also emit `relic.json` and `annihilation.json`:

```json
{
  "schema_version": "relic/v1",
  "m_dm_gev": <float>,
  "omega_h2": <float or null>,
  "xf": <float or null>,
  "source": "micromegas",
  "source_run": "<run_identifier>",
  "cosmology": "standard_thermal"
}
```

```json
{
  "schema_version": "annihilation/v1",
  "m_dm_gev": <float>,
  "sigma_v_zero": <float or null>,
  "source": "micromegas",
  "source_run": "<run_identifier>"
}
```
