# `/micromegas` — final design doc (SYNTHESIZER)

Author: synthesizer agent
Date: 2026-04-19
Status: input to planning phase
Inputs: `proposal.md` (proposer), `critique.md` (skeptic), manager cross-workstream decisions.

This doc reconciles the proposer and critic into a single plan. Manager-imposed cross-workstream decisions (plugin placement at `plugins/constraints/`, shared scattering schema path, no analytic fallbacks, `spec.yaml > CLI > auto-detect`, mandatory `dm_candidate`) are treated as fixed — they shape every section below and are not reopened.

---

## 1. Install skill `/micromegas-install`

### Version pin — **6.0.5** (LTS)

The critic's §2 objection is correct: 6.1.x adds UFO2 support but SARAH 4.15 (the version `/sarah-build` templates target) emits **UFO 1.x by default**. Until W3 is demonstrated to emit UFO 2.0 end-to-end, pinning 6.1.15 buys an unneeded feature and takes on immaturity risk. Pin **`micromegas_6.0.5`**, with env override `HEPPH_MICROMEGAS_VERSION` (default `6.0.5`). Re-pin to 6.1.x is a v1.1 ticket gated on a concrete UFO2 migration in W3.

### Subcommands

```
/micromegas-install detect
/micromegas-install use-path <dir> [--calchep-path <dir>]
/micromegas-install install [parent_dir]
```

Stdout JSON contract mirrors `/spheno-install`: `{status: missing|found|configured|version_mismatch|installed, ...}`.

### CalcHEP handling — bundled build, split allowed via `use-path`

Build the vendored CalcHEP with the micrOMEGAs tarball (the normal `make -C $micromegas_path` target). The critic's §1 concern — that 6.x `Packages/` step can pull network — is handled by: (a) running the install under `HEPPH_NO_NETWORK=1` in CI; (b) if any step tries to reach out to the network while `HEPPH_NO_NETWORK=1`, emit the new fatal blocker `MICROMEGAS_BUILD_NEEDS_NETWORK` with the offending URL in `context.attempted_url`.

The proposer's "never accept external CalcHEP" is softened: `use-path` accepts `--calchep-path <dir>` so users with a working CalcHEP 3.9 tree can avoid a 1 GB duplicate. If `--calchep-path` is supplied, we validate `CalcHEP_src/getFlags` exists and `$dir/bin/s_calchep` runs; otherwise emit `CALCHEP_PATH_INVALID`. Without that flag, we always use the bundled copy recorded at `calchep_path = $micromegas_path/CalcHEP_src`.

### `HEPPH_NO_NETWORK` support

- Download step: when `HEPPH_NO_NETWORK=1` and tarball missing from a local cache (`$HEPPH_CACHE_DIR/micromegas_6.0.5.tgz`), abort with fatal `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`.
- Build step: any `make` sub-target that issues `curl`/`wget`/`git` must be trapped and promoted to `MICROMEGAS_BUILD_NEEDS_NETWORK`.
- Test harness: the install golden test runs with `HEPPH_NO_NETWORK=1` after the tarball is staged in cache, proving offline build.

### macOS build notes

The critic's §9 is accepted. Installer must:

1. Set `SDKROOT="$(xcrun --show-sdk-path)"` before `make` on macOS 14+.
2. When Homebrew gfortran is detected, export `FFLAGS="-ff2c"` and `LDFLAGS="-Wl,-ld_classic"` (handles the Xcode-15 linker split).
3. Set `DYLD_LIBRARY_PATH="$micromegas_path/lib:$DYLD_LIBRARY_PATH"` for the smoke test only (not written to user shell).
4. If `xcrun --show-sdk-path` fails or returns a stale SDK, emit fatal `MICROMEGAS_MACOS_SDK_MISMATCH` with `context.sdkroot` and `user_instruction: "Install Xcode Command Line Tools: xcode-select --install"`.

### Config keys (written via `config_merge`)

```
micromegas_path           ~/micrOMEGAs/micromegas_6.0.5
micromegas_version        6.0.5
calchep_path              $micromegas_path/CalcHEP_src   # or user-supplied
calchep_bundled           true | false
micromegas_installed_at   <UTC ISO 8601>
```

### Install-skill blockers (final list)

| Code | Mode | Rationale |
|---|---|---|
| `GFORTRAN_ABSENT` | fatal | reused from shared vocabulary |
| `CC_ABSENT` | fatal | no C compiler on PATH |
| `MICROMEGAS_DOWNLOAD_FAILED` | fatal | `download_with_retry` exhausted |
| `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY` | fatal | `HEPPH_NO_NETWORK=1` and no cached tarball |
| `MICROMEGAS_BUILD_FAILED` | fatal | bundled `make` non-zero; last 40 lines via `_make_log_parse.py` |
| `MICROMEGAS_BUILD_NEEDS_NETWORK` | fatal | build attempted network under `HEPPH_NO_NETWORK=1` |
| `MICROMEGAS_PATH_INVALID` | fatal | `use-path <dir>` lacks `sources/` or (bundled) `CalcHEP_src/` |
| `CALCHEP_PATH_INVALID` | fatal | `--calchep-path` given but not a working CalcHEP tree |
| `MICROMEGAS_MACOS_SDK_MISMATCH` | fatal | xcrun SDK missing/stale on macOS 14+ |
| `MICROMEGAS_SMOKE_TEST_FAILED` | fatal | MSSM liveness probe produced no finite `Omega h^2` |
| `PPPC_TABLES_MISSING` | fatal | shipped indirect-detection tables absent after `use-path` |

Smoke test = compile + run bundled `MSSM/main.c`; assert stdout contains an `Omega h^2 =` line with a finite positive number. Do not check the numeric value.

---

## 2. Usage skill `/micromegas`

### Subcommands

```
/micromegas relic        <model> [--precompiled <project>]
/micromegas scatter      <model>
/micromegas annihilate   <model>
/micromegas indirect     <model>
```

`all` is **dropped** (critic §7). The orchestrator (`/lagrangian-builder`) composes subcommands as needed. `--precompiled <project>` (values: `MSSM`, `NMSSM`, `singletDM`, `IDM`) bypasses UFO conversion when the user's model maps to a micrOMEGAs-shipped project — a 10× speedup on the common MSSM-family case.

### Inputs

Positional: `<model>` (resolves via config `models.<name>`).

Required state:
- `config.models[<name>].ufo_path` (from `/sarah-build`) — except when `--precompiled` is used.
- `config.models[<name>].latest_slha` (from `/spheno-build`).
- `config.models[<name>].spec_yaml` — must contain **mandatory** `dm_candidate` (see §3).
- `config.micromegas_path`.

Any missing → fatal `MICROMEGAS_INPUT_MISSING` with `context.missing`.

### DM candidate resolution (per manager rule `spec.yaml > CLI > auto-detect`)

1. `spec.yaml`'s `dm_candidate` wins unconditionally (reproducibility).
2. `--dm-pdg <id>` honoured only when spec omits it; when used, we write a run-scoped override file `runs/<TS>/dm_override.json` and error-log a notice.
3. `--auto-detect` is an explicit opt-in flag. It parses SLHA `Block MASS` + UFO particle attributes (Z2-odd tag, non-zero DECAY widths parsed — not presence of block, per critic §3), and **refuses ambiguous cases** with recoverable `DM_CANDIDATE_AMBIGUOUS`. No silent guessing.
4. Charged or colored LSP → `DM_CANDIDATE_UNPHYSICAL` (fatal). Split from color: `DM_CANDIDATE_COLOR_MISMATCH` (fatal) when specifically the color-triplet case (helps orchestrator messaging per critic §10).

### Outputs

Per run: `$STATE_ROOT/models/<name>/micromegas_runs/<TS>/`

| File | Content |
|---|---|
| `main.c` | generated driver |
| `stdout.log` | raw output |
| `summary.json` | conforms to `plugins/shared/schemas/scattering.schema.json` (draft below) plus micromegas-specific sections |
| `report.md` | human-readable + Planck comparison |
| `spectra.h5` | indirect-detection spectra (single file per run; not per scan point) |

`summary.json` keys (draft — to be finalized in the planning phase together with `/ddcalc` and `/looptools` synthesizers):

```
m_dm_gev                 # flat mirror (ddcalc wants it flat)
sigma_si_proton_cm2
sigma_si_neutron_cm2
sigma_sd_proton_cm2
sigma_sd_neutron_cm2
source                   # "micromegas"
source_run               # UTC timestamp + model hash
halo:                    # {rho_local_gev_cm3, v_esc_km_s, v_0_km_s}
nucleon_form_factors:    # {preset: "default" | "A1", sigma_piN_mev, ...}
cosmology                # "standard_thermal" (default); tag downstream interpreters
dm_candidate             # {pdg, name, mass_gev}
relic                    # {omega_h2, xf, planck_target, planck_sigma, pull, beps_used, beps_sensitivity}
annihilation             # {sigma_v_zero_cm3_s, channels[]}
indirect                 # {spectra_h5_path, coarse: {gamma, positron, pbar, nu}}  (20 log-bins inlined)
```

Scan mode writes `scan_index.csv` with columns `index, <params>, omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0, status, blocker_code, run_dir, timing_s`.

### Blocker set (usage, three-state)

| Code | Mode | Notes |
|---|---|---|
| `MICROMEGAS_INPUT_MISSING` | fatal | UFO/SLHA/spec absent |
| `DM_CANDIDATE_AMBIGUOUS` | recoverable | auto-detect only; scan marks row |
| `DM_CANDIDATE_UNPHYSICAL` | fatal | charged LSP |
| `DM_CANDIDATE_COLOR_MISMATCH` | fatal | colored LSP |
| `UFO_CONVERT_FAILED` | fatal | CalcHEP converter stderr tail |
| `CALCHEP_CONVERTER_VERSION_SKEW` | fatal | cache key mismatch against current `micromegas_version` |
| `MICROMEGAS_PROJECT_BUILD_FAILED` | fatal | `make main` failed; `make_log_tail` |
| `MICROMEGAS_RUNTIME_FAILURE` | recoverable | `./main` crashed on a scan point |
| `OMEGA_UNCONVERGED` | recoverable | NaN/negative from `darkOmega` |
| `RELIC_BEPS_SENSITIVE` | recoverable | Ωh² shifts >20% between `Beps=1e-4` and `1e-6` — coannihilation wall |
| `MULTICOMPONENT_UNSUPPORTED` | fatal | two stable Z2-odd states detected; v1 refuses (v1.1 via `darkOmega2`) |

Per manager rule, **no** `reference_only` blocker from this skill: `MICROMEGAS_ANALYTIC_FALLBACK` and `--allow-analytic-fallback` are deleted. The schema's `reference_only` state remains legal across the marketplace but is forbidden here.

---

## 3. Data contracts

- **UFO in:** from `/sarah-build` at `$STATE_ROOT/models/<name>/sarah_output/UFO/<SarahName>/`. Cache key for CalcHEP conversion: `sha256(ufo_dir_tar) || micromegas_version || ufo_dialect`. Stored at `$STATE_ROOT/models/<name>/micromegas_project/cache/<hash>/`.
- **SLHA in:** from `/spheno-build` at path under `config.models[<name>].latest_slha`.
- **σ out to `/ddcalc`:** `/ddcalc` reads `summary.json` directly; the draft schema above is a superset of ddcalc's requirements. Field-name convergence is owned by the cross-synthesizer handshake (manager-imposed). `/micromegas` does NOT write a separate `scattering.json` — the flat top-level keys are the contract.
- **Cosmology assumption:** always emit `cosmology: "standard_thermal"` in v1. Any non-standard history is out of scope.
- **Nucleon form factors:** default preset `"default"` uses micrOMEGAs' built-in 2018 lattice values. `spec.yaml` may set `nucleon_form_factors: A1` (Arcadi–Profumo paper set) or `micromegas_default`. Preset name is echoed into `summary.json.nucleon_form_factors.preset`.

---

## 4. Physics scope for v1

**In-scope:**
- Relic density Ωh² via `darkOmega(&Xf, fast=1, Beps=1e-6)`; Planck 2018 target `0.120 ± 0.0012`. Plus a `Beps` sensitivity probe (see §10 blocker `RELIC_BEPS_SENSITIVE`) to detect coannihilation-wall numerical instability.
- Tree-level σ_SI and σ_SD on proton and neutron via `nucleonAmplitudes()`.
- Annihilation at v→0: `sigma_v_zero`, channel-resolved fractions, freeze-out `xf`.
- Indirect-detection spectra: γ, e+, p̄, ν via shipped PPPC4DMID tables. Coarse 20-log-bin summary inline in JSON; full spectra in `spectra.h5`.

**Out of scope (v1.1 backlog, explicitly):**
- NREFT operator-basis σ (Anand–Fitzpatrick–Haxton). Promoted to v1.1.
- Asymmetric DM / `darkOmega2` two-component path. v1 refuses with `MULTICOMPONENT_UNSUPPORTED`.
- Loop-level σ_SI blind-spot analysis (paper Eqs. 9, 14, 23) — owned by Phase B `/looptools`.
- Non-standard cosmologies (early matter domination, entropy injection).

---

## 5. Test matrix

**Unit (always on):**
- Pure-Python parsers: `parse_micromegas_out.py`, `parse_slha_mass_block.py`, `resolve_dm_candidate.py`. Fixtures at `tests/fixtures/micromegas/stdout_*.txt`.
- JSON schema validator: every emitted `summary.json` validates against `plugins/shared/schemas/scattering.schema.json` (draft) and blocker contract.
- Template renderer: `main_c_template.py` produces identical bytes against golden `main.c` fixtures for each subcommand.

**Integration (gated on `HEPPH_RUN_NETWORK_TESTS=1`):**
- End-to-end install from LAPTh upstream on clean `$HOME` sandbox (Linux + macOS runners).
- Offline rebuild from cached tarball with `HEPPH_NO_NETWORK=1` — proves the "bundled" claim.
- UFO→CalcHEP conversion on a SARAH-emitted singletDM UFO.

**Golden fixture (single benchmark):**
- Model: **Singlet-scalar DM**, `m_S = 100 GeV`, `λ_hS = 0.05`.
- Expected: `Ωh² = 0.118 ± 0.002` (benchmark from micrOMEGAs manual §5, reproducible on `singletDM/main.c`).
- Expected: `σ_SI(p) ≈ 1.1e-46 cm²` within ±10% (tolerance covers form-factor-preset drift).
- Test asserts both values from a single `/micromegas relic` + `/micromegas scatter` call against the SPheno-generated SLHA.

**Concurrency:**
- Per critic §11: runs are **serial** (matching `/spheno-build --scan`). Per-run project dir `$STATE_ROOT/models/<name>/micromegas_runs/<TS>/project/` avoids shared-state trampling; the top-level `micromegas_project/cache/` is read-only across concurrent scans.

---

## 6. Open questions deferred (with defaults)

These genuinely require planning-phase alignment; each carries a **default** so planners aren't blocked.

1. **Final shared-schema field names and required-vs-optional split.** Default: the snake_case list in §3 above. Final: to be finalized by the three synthesizers (`/micromegas`, `/ddcalc`, `/looptools`) together; the schema file at `plugins/shared/schemas/scattering.schema.json` is the artifact.
2. **Nucleon form-factor presets available in v1.** Default: `"default"` (micrOMEGAs built-in) and `"A1"` (Arcadi–Profumo). Additional presets (`"MILC"`, `"CHPT"`) are v1.1.
3. **Halo model presets.** Default: SHM (`ρ=0.3 GeV/cm³, v₀=220 km/s, v_esc=544 km/s`). Exposed in `spec.yaml` as `halo: shm` (default) or as an inline object. Non-default: v1.1.
4. **PRNG seed for CalcHEP phase-space integration.** Default: fix to `HEPPH_MICROMEGAS_SEED=42`. Written into `summary.json.source_run`.
5. **Schema relocation for `blocker.schema.json`.** Default: leave at `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` and symlink from `plugins/hep-ph-toolkit/skills/_shared/`. Promoting to `plugins/shared/schemas/` is a W0-style prework — propose but do not block on it; the planner can sequence it before `plugins/constraints/` lands.
6. **Marketplace registration.** Default: add `plugins/constraints/` to `.claude-plugin/marketplace.json` and a row to `CLAUDE.md`'s category table in the same PR that introduces the plugin skeleton. Make this an explicit checklist item for the implementation planner.
7. **`--precompiled` project mapping.** Default: v1 maps `MSSM`, `NMSSM`, `singletDM`, `IDM` by exact spec-name match; UFO path still required for all other models.

Word count: ~1520.
