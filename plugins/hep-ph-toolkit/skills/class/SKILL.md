---
name: class
description: Drive CLASS v3.3.4 (via classy) for linear cosmology — background H(z), CMB Cℓ, P(k), transfer functions — for ΛCDM and upstream BSM extensions.
version: "1.0.0"
subcommands:
  - background
  - cmb
  - pk
  - transfer
---

# /class

Drive CLASS v3.3.4 (Cosmic Linear Anisotropy Solving System) to compute
linear-cosmology observables for ΛCDM and BSM extensions that affect the
CMB or large-scale structure. Does not reimplement physics — all Boltzmann
computation is delegated to the `classy` Python wrapper.

Outputs validated against `plugins/shared/schemas/cosmology.schema.json`
(`cosmology/v1`). Run directory: `$HEPPH_STATE_ROOT/cosmology_runs/<TS>/`.

---

## Preflight: CLASS

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/class/detect.sh

- **exit 0** → CLASS is installed and registered in config; `config.class_path`
  is set. Proceed.
- **exit non-zero** → CLASS is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/class/INSTALL.md` into context
  and follow it. When the install completes, re-run `detect.sh` before
  proceeding. If it still fails, halt and surface the blocker code from
  the install reference.

---

## When to invoke

Invoke `/class` when:
1. CLASS is installed (`config.class_path` set) via the preflight above.
2. A cosmological preset or custom config is available.
3. A downstream skill needs CMB Cℓ, P(k), background evolution, or transfer
   functions — for example, constraining BSM DM via CMB N_eff or ISW signals.
4. **Auto-invoked by `/dark-matter-constraints`** for cosmology side-checks
   when a runner spec opts in via `cosmology.kind != 'standard_thermal'`.

---

## Subcommands

```
/class background <preset> [options]
/class cmb        <preset> [options]
/class pk         <preset> [options]
/class transfer   <preset> [options]
```

| Subcommand   | Computes                                              | Output file    |
|--------------|-------------------------------------------------------|----------------|
| `background` | H(z), D_A(z), growth factor, Ω_i(z), thermodynamics  | `background.dat` |
| `cmb`        | Lensed TT, TE, EE, BB, PP Cℓ up to `--lmax`          | `cls.dat`      |
| `pk`         | Linear matter P(k,z) at redshifts `--z-pk`            | `pk.dat`       |
| `transfer`   | Transfer functions T(k,z) at redshifts `--z-pk`       | `tk.dat`       |

All subcommands also write `cosmology.json` (validated against `cosmology/v1`).

---

## Presets

| Preset           | Description                                               |
|------------------|-----------------------------------------------------------|
| `planck18`       | Planck 2018 ΛCDM best-fit (TT,TE,EE+lowE+lensing)        |
| `planck18_act`   | Planck 2018 + ACT DR4 joint best-fit                      |
| `custom`         | Requires `--config <path>` pointing to a YAML config file |

---

## Options

```
subcommand            background|cmb|pk|transfer
preset                planck18|planck18_act|custom

--config <path>       YAML config file (required for preset=custom,
                      optional override for planck18/planck18_act)
--bsm <path>          YAML BSM extension block (overrides preset's bsm_extension)
--output-dir <dir>    Run output directory (default: $HEPPH_STATE_ROOT/cosmology_runs/<TS>/)
--lmax <int>          Maximum multipole for CMB (default: 2500, cmb subcommand only)
--z-pk <str>          Comma-separated redshifts for P(k)/transfer (default: "0")
--k-min <float>       Minimum k [h/Mpc] (default: 1e-4)
--k-max <float>       Maximum k [h/Mpc] (default: 1.0)
```

---

## BSM extensions

Pass a YAML file via `--bsm` with keys:
```yaml
kind: dcdm           # one of: dcdm, idm_baryon, idm_dr, idm_photon,
                     #         exotic_injection, ncdm_extra
params:
  Gamma_dcdm: 1.0e-29  # extension-specific CLASS ini keys
```

The `kind` and `params` are forwarded verbatim to CLASS as ini-file entries.
Only upstream `lesgourg/class_public` v3.x extensions are supported.

---

## Outputs

Per run: `$HEPPH_STATE_ROOT/cosmology_runs/<TS>/`

| File              | Content                                                                     |
|-------------------|-----------------------------------------------------------------------------|
| `cosmology.json`  | Run metadata; validated against `cosmology/v1` schema                       |
| `cls.dat`         | CMB Cℓ TSV (`# ell TT TE EE BB PP` header); cmb only                       |
| `pk.dat`          | P(k,z) TSV (`# k_h/Mpc Pk_z0 ...`); k in h/Mpc, P in (Mpc/h)^3; pk only  |
| `background.dat`  | Background quantities TSV; background only                                  |
| `tk.dat`          | Transfer functions TSV (`# k_h/Mpc d_cdm d_b d_tot`); z=0 slice; transfer  |
| `tk_z{z}.dat`     | Per-redshift transfer function slices (one per `--z-pk` value)              |
| `class.ini`       | Rendered CLASS ini file used for the run                                    |
| `stdout.log`      | Raw classy subprocess stdout                                                |
| `stderr.log`      | Raw classy subprocess stderr                                                |

P(k) units convention: k grid is sampled in h/Mpc as specified by `--k-min`/`--k-max`.
The classy `pk_lin()` call takes k in 1/Mpc (converted internally as k × h), and the
returned P [Mpc^3] is divided by h^3 so that P(k) is in (Mpc/h)^3, consistent with the
`k_h/Mpc` header. Transfer functions use classy's `get_transfer(z)` and emit δ_cdm,
δ_b, and δ_tot (total matter) at the k-grid returned by CLASS (already in h/Mpc).

TSV files use `# col_a col_b ...` header lines and deterministic
`f"{x:.10e}"` float formatting throughout.

---

## Prerequisites (state contracts)

| Config key        | Source                                | Required for      |
|-------------------|---------------------------------------|-------------------|
| `config.class_path` | `_shared/installs/class/INSTALL.md` | All subcommands   |
| `config.class_version` | `_shared/installs/class/INSTALL.md` | All subcommands |

If `class_path` is not configured, the skill emits `CLASS_NOT_CONFIGURED`
(fatal) and halts.

---

## Recoverable vs fatal contract

| Code                       | Mode        | Notes                                                              |
|----------------------------|-------------|-------------------------------------------------------------------|
| `CLASS_NOT_CONFIGURED`     | fatal       | `class_path` missing from config                                  |
| `CLASS_CONFIG_INVALID`     | fatal       | Malformed or unresolvable config YAML                             |
| `CLASS_INI_RENDER_FAILED`  | fatal       | Template rendering failed                                         |
| `CLASSY_IMPORT_FAILED`     | recoverable | classy Python package not importable; re-run `/install class`     |
| `CLASS_COMPUTE_FAILED`     | recoverable | CLASS computation raised an exception; check ini params/stderr    |
| `CLASS_RUNTIME_FAILURE`    | recoverable | Non-zero exit from classy subprocess with no structured code      |
| `CLASS_OUTPUT_MISSING`     | fatal       | Expected output file not produced by CLASS                        |
| `CLASS_SCHEMA_INVALID`     | fatal       | cosmology.json failed schema validation                           |
| `CLASS_BSM_UNKNOWN_KIND`   | fatal       | Unrecognised BSM extension kind                                   |

---

## Out of scope

The following are explicitly **not** supported by this skill:

- **MontePython / Cobaya / sampling** — MCMC parameter estimation.
- **`class_sz`** — Sunyaev-Zel'dovich / cluster-count extensions.
- **ExoCLASS fork** — energy-injection capabilities from upstream CLASS v3.x
  *are* in scope; the ExoCLASS fork repository itself is not.
- **GW_CLASS / classnet / class_matter branches** — non-standard forks.
- **CMB foregrounds, beams, noise** — raw Cℓ only, no likelihood.
- **Non-linear corrections** — HaloFit/HMcode not invoked.
- **`/dark-matter-constraints` auto-routing.** `/class` is auto-invoked by
  `/dark-matter-constraints` when a runner spec declares
  `cosmology.kind != 'standard_thermal'`. The router invocation contract is
  documented in `dark-matter-constraints/SKILL.md` Step 6. **Cost disclosure:**
  `background` ≈ <1 s; `cmb` 5-30 s at default `lmax`; `pk` 2-10 s; `transfer`
  <5 s; multi-subcommand runs add roughly linearly. Router default
  `invoke: [background]` keeps overhead negligible. Other auto-routing
  (CMB-likelihood frameworks, MCMC orchestrators) remains out of scope.

---

## Scripts reference

| Script                      | Purpose                                                   |
|-----------------------------|-----------------------------------------------------------|
| `scripts/run_class.py`      | CLI entry point; argparse, dispatch, config loading       |
| `scripts/ini_render.py`     | Render YAML preset + BSM block → CLASS ini file           |
| `scripts/classy_driver.py`  | Subprocess wrapper for classy; captures logs              |
| `scripts/parse_outputs.py`  | Parse classy dict → TSV `.dat` files                      |
| `scripts/schema_validate.py`| Validate `cosmology.json` against `cosmology/v1`          |

---

## Fixture and testing notes

Unit tests are always-on (no network, no classy required).
The golden `cl[2,'tt']` test is gated on `HEPPH_RUN_NETWORK_TESTS=1`.

See `tests/test_smoke.py` for the integration gate (`cl[2,'tt']` within 5%
of `tests/fixtures/planck18_cls_l2_to_l10.json`, generated on Ubuntu 22.04
LTS with system gcc/libomp).

---

## Physics scope (v1)

**In scope:**
- Background: H(z), luminosity/angular distance, growth factor, thermodynamics.
- CMB: lensed TT, TE, EE, BB, PP Cℓ (scalar modes) up to ℓmax=2500.
- Matter power spectrum P(k, z) (linear).
- Transfer functions T_cdm(k), T_b(k), T_tot(k), etc.
- BSM extensions available in upstream CLASS v3.3.4: DCDM, IDM-baryon,
  IDM-DR, IDM-photon, exotic energy injection, ncdm_extra.
- ΛCDM presets: Planck 2018, Planck 2018 + ACT DR4.

**Out of scope (v1):**
- Tensor modes, primordial GW spectrum.
- Weak-lensing Cℓ beyond the lensed CMB Cℓ.
- Non-linear P(k) (HaloFit).
- CLASS-PT, class_sz, GW_CLASS.
- Parameter sampling / MCMC.
