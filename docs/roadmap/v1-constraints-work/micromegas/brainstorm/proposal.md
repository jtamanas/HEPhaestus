# `/micromegas` — design proposal (PROPOSER)

Author: proposer agent
Date: 2026-04-19
Target: Phase A of `docs/roadmap/v1-constraint-skills.md` (parallel with `/ddcalc`, `/higgstools`)

This proposal covers both the installer skill `/micromegas-install` and the usage skill `/micromegas`. It stakes out concrete positions where the roadmap leaves open questions so the critic has sharp claims to attack.

---

## 1. Install skill `/micromegas-install`

### Tool source + pin

- Upstream: `https://lapth.cnrs.fr/micromegas/downloads/micromegas_<ver>.tgz` (LAPTh hosts; no HEPForge mirror).
- **Pinned version: `6.1.15`** (latest stable 2025 release; supports arbitrary UFO input via the CalcHEP/LanHEP bridge it ships with).
- Env override: `HEPPH_MICROMEGAS_VERSION=6.1.15`.
- Parent install dir default: `~/micrOMEGAs/micromegas_<ver>/` (mirrors `~/SPheno/...` convention).

### Subcommands (mirrors `/spheno-install`)

```
/micromegas-install detect
/micromegas-install use-path <dir>
/micromegas-install install [parent_dir]
```

Stdout JSON contract (same shape as `/spheno-install`):

| `status` | Meaning |
|----------|---------|
| `missing` | No micrOMEGAs found |
| `found` | Found via scan, not in config |
| `configured` | `micromegas_path` set and smoke test passed |
| `version_mismatch` | Existing install disagrees with pin → install fresh alongside |
| `installed` | Fresh install completed |

Smoke test: compile + run the shipped `MSSM/main.c` example, parse `Omega h^2` from stdout, verify it is a positive finite number. Do **not** verify the numeric value — the reference MSSM example is sufficient as a liveness probe.

### CalcHEP backend — position: **bundled, co-installed from the same tarball**

The roadmap open question (§"Should `/micromegas` install include the CalcHEP back-end...") has a clean answer. micrOMEGAs ships its own vendored CalcHEP 3.8.x under `micromegas_<ver>/CalcHEP_src/` — the tarball `make` target builds it automatically. We therefore:

1. Do **not** treat CalcHEP as a separable dependency.
2. Do **not** gate on the user having an external CalcHEP install.
3. Run `make -C $micromegas_path` at install time; this builds both the CalcHEP numeric backend and the `main.c` driver template. Compile output captured to `install.log`; on failure emit `MICROMEGAS_BUILD_FAILED` (fatal) with last-40-line `make_log_tail` via `_make_log_parse.py` (reuse the helper from `/spheno-install`).
4. Record `calchep_path = $micromegas_path/CalcHEP_src` so `/madgraph` or future skills can find it without reinstallation.

Rationale: treating CalcHEP as independent would force users to solve a second build in a different tree, and the bundled version is the tested one. If a user already has a system CalcHEP, `use-path` accepts a directory whose `CalcHEP_src/` subdir exists; we do not try to re-point CalcHEP.

### gfortran + C toolchain preconditions

- `gfortran` check: reuse `plugins/hep-ph-toolkit/skills/spheno-install/scripts/check_gfortran.sh`. Emit `GFORTRAN_ABSENT` fatal on miss.
- C compiler: `gcc` or `clang` on PATH; absent → `CC_ABSENT` fatal (new code, above 20 per `_common.sh` convention).
- LAPACK is not required by micrOMEGAs itself but is already pulled in by `/spheno-install` in most real environments.

### `_common.sh` helpers used

| Helper | Use |
|--------|-----|
| `check_disk 2` | 2 GB min (tarball ~150 MB, build tree ~1 GB) |
| `download_with_retry` | tarball fetch with one retry |
| `verify_checksum` | SHA256 pin; initial value `TODO` with the warn-not-abort path |
| `config_merge` | atomic write of all config keys |
| shared exit codes `EXIT_NO_GFORTRAN`, `EXIT_DOWNLOAD`, `EXIT_SMOKE` | re-used directly |

### Config keys written

```
micromegas_path           ~/micrOMEGAs/micromegas_6.1.15
micromegas_version        6.1.15
calchep_path              $micromegas_path/CalcHEP_src
micromegas_installed_at   <UTC ISO 8601>
```

### Install-skill blockers

| Code | Mode | Trigger |
|------|------|---------|
| `GFORTRAN_ABSENT` | fatal | reused from shared vocabulary |
| `CC_ABSENT` | fatal | new, no C compiler on PATH |
| `MICROMEGAS_DOWNLOAD_FAILED` | fatal | `download_with_retry` failed twice |
| `MICROMEGAS_BUILD_FAILED` | fatal | bundled `make` returned non-zero; `context.make_log_tail` + `likely_cause` |
| `MICROMEGAS_PATH_INVALID` | fatal | `use-path <dir>` lacks `CalcHEP_src/` or `sources/` |
| `MICROMEGAS_SMOKE_TEST_FAILED` | fatal | MSSM liveness probe did not produce a finite `Omega h^2` |

---

## 2. Usage skill `/micromegas`

### Inputs

Positional: `<model_name>`. Everything else is read from config + state.

Required state (checked before any work):
- `config.models[<name>].ufo_path` — absolute path to UFO dir emitted by `/sarah-build`. (SARAH's UFO export lives at `$STATE_ROOT/models/<name>/sarah_output/UFO/<SarahName>/`.)
- `config.models[<name>].latest_slha` — SLHA `.spc` from `/spheno-build`.
- `config.micromegas_path` — from `/micromegas-install`.

If any is missing → fatal blocker: `MICROMEGAS_INPUT_MISSING` with `context.missing: [...]`.

### DM candidate identification

micrOMEGAs requires a designated DM candidate (the lightest stable Z2-odd particle). Resolution order:

1. **Explicit:** `--dm-pdg <id>` CLI flag wins.
2. **Spec annotation:** `spec.yaml` may declare `dm_candidate: <field_name>`; resolved to PDG via the UFO `particles.py`.
3. **Auto:** parse SLHA `Block MASS`, pick the lightest particle among those marked stable in the UFO (`goldstoneboson=False`, no decay widths in `DECAY` blocks, non-SM). If ambiguous → recoverable blocker `DM_CANDIDATE_AMBIGUOUS` with `context.candidates: [{pdg, mass}, ...]`.
4. If the lightest Z2-odd is charged or colored → fatal blocker `DM_CANDIDATE_UNPHYSICAL` (charge/color from UFO).

### Operations (subcommands)

```
/micromegas relic     <model>          # Ωh²
/micromegas scatter   <model>          # σ_SI, σ_SD on proton + neutron
/micromegas annihilate <model>         # channel-resolved σv at v→0 + freeze-out
/micromegas indirect  <model>          # γ, e+, p-bar, ν spectra via PPPC4DMID tables shipped with mO
/micromegas all       <model>          # run all four, emit aggregated JSON
```

Each subcommand is a thin Python driver that:

1. Materialises a micrOMEGAs project dir at `$STATE_ROOT/models/<name>/micromegas_project/`.
2. Generates `main.c` from a Jinja-like template (`scripts/main_c_template.py`) per the requested op. Templates mirror the shipped `MSSM/main.c`, `singletDM/main.c`, etc. — we pick the minimal variant that calls only the functions we need.
3. Imports the UFO using the `CalcHEP/ufoModel.py` converter shipped with micrOMEGAs. (micrOMEGAs does **not** read UFO natively; the bundled converter produces CalcHEP lgrng/func files. Output cached at `$STATE_ROOT/models/<name>/micromegas_project/work/models/`.)
4. Patches SLHA-derived numerics into the CalcHEP `vars1.mdl` via the `readVarSLHA` API (standard micrOMEGAs pattern).
5. Runs `make main` inside the project dir (subprocess; cached on `sha256(ufo_path) + sha256(slha) + subcommand`).
6. Executes the resulting `./main` binary, captures stdout.
7. Parses stdout into JSON via `scripts/parse_micromegas_out.py`.

### Outputs

Per-point directory: `$STATE_ROOT/models/<name>/micromegas_runs/<TS>/`

| File | Content |
|------|---------|
| `main.c` | generated driver (for reproducibility) |
| `stdout.log` | raw micrOMEGAs output |
| `summary.json` | parsed results |
| `report.md` | human-readable summary with Planck comparison |

`summary.json` schema (load-bearing):

```json
{
  "dm_candidate": {"pdg": 1000022, "name": "chi0_1", "mass_gev": 62.4},
  "relic": {
    "omega_h2": 0.118,
    "xf": 24.1,
    "planck_target": 0.120,
    "planck_sigma": 0.0012,
    "pull": -1.67
  },
  "scatter": {
    "sigma_si_proton_cm2": 1.2e-46,
    "sigma_si_neutron_cm2": 1.1e-46,
    "sigma_sd_proton_cm2": 3.4e-42,
    "sigma_sd_neutron_cm2": 3.2e-42
  },
  "annihilation": {
    "sigma_v_zero_cm3_s": 2.1e-26,
    "channels": [{"final_state": "b b~", "fraction": 0.87}, ...]
  },
  "indirect": {
    "gamma_spectrum_path": ".../gamma.dat",
    "positron_spectrum_path": ".../positron.dat"
  }
}
```

`pull` is signed: `(omega_h2 - 0.120) / 0.0012` using Planck 2018 (Aghanim et al., arXiv:1807.06209). Matches paper Eq. (3) of arXiv:2506.19062.

### Physics references (for the template bodies)

- Relic density Boltzmann solve: standard Gondolo–Gelmini formulation, micrOMEGAs function `darkOmega(&Xf, fast=1, Beps=1e-6)`. Paper Eq. (3).
- σ_SI tree-level: paper Eq. (6) — t-channel Higgs exchange. micrOMEGAs handles this via `nucleonAmplitudes()`.
- σ_SD tree-level: paper Eq. (7) — Z/axial exchange.
- Annihilation channels + freeze-out: `calcSpectrum(...)` yields both σv(v=0) and channel fractions for indirect.
- Indirect-detection spectra: micrOMEGAs ships PPPC4DMID-derived tables (Cirelli et al., 1012.4515).

Loop-level σ_SI blind-spot analysis (paper Eqs. 9, 14, 23) is **out of scope** for `/micromegas` — that is Phase B `/looptools`.

### Error modes → blockers (three-state per schema)

| Code | Mode | Trigger |
|------|------|---------|
| `MICROMEGAS_INPUT_MISSING` | fatal | UFO or SLHA path absent |
| `DM_CANDIDATE_AMBIGUOUS` | recoverable | multiple stable Z2-odd at near-degenerate mass |
| `DM_CANDIDATE_UNPHYSICAL` | fatal | LSP is charged or colored |
| `UFO_CONVERT_FAILED` | fatal | CalcHEP converter rejects UFO (context: converter stderr tail) |
| `MICROMEGAS_PROJECT_BUILD_FAILED` | fatal | `make main` failed; `make_log_tail` |
| `MICROMEGAS_RUNTIME_FAILURE` | recoverable | `./main` crashed on a scan point — scan continues, row marked |
| `OMEGA_UNCONVERGED` | recoverable | `darkOmega` returned negative/NaN (numerical blow-up, typical at coannihilation threshold) |
| `MICROMEGAS_ANALYTIC_FALLBACK` | reference_only | explicitly requested fallback when tool unavailable; fields `reference_method: "single-channel s-channel Higgs σv from paper Eq. 4"`, non-empty `caveats` array — matches augment-not-replace policy |

`reference_only` is only emitted when the user passes `--allow-analytic-fallback`. Default is to fatal out if micrOMEGAs is unreachable, per user's "augment not replace" memory.

### Scan mode

Mirror `/spheno-build --scan` exactly: `scripts/scan.py` runs sequential points, writes `scan_index.csv` with columns `index, <params>, omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0, status, blocker_code, run_dir, timing_s`. Recoverable blockers (e.g. `OMEGA_UNCONVERGED`) mark a row bad and continue.

---

## 3. Integration

### Phase A placement

`/micromegas` sits in Phase A alongside `/ddcalc` and `/higgstools`. No mutual dependencies — all three consume UFO + SLHA from W3/W4.

### Data flow

```
spec.yaml
   │
   ▼
/sarah-build ──── UFO dir ──┐
   │                         │
   ▼                         ▼
/spheno-build ── SLHA ──▶ /micromegas ──▶ summary.json
                              │                │
                              │                ├─ σ_SI, σ_SD ──▶ /ddcalc   (LZ/XENONnT exclusion)
                              │                ├─ Ωh² ─────────▶ /lagrangian-builder report
                              │                └─ indirect ────▶ (Phase C overlay plots)
                              ▼
                         scan_index.csv ──▶ /hep-plotting
```

### Hand-off to `/ddcalc`

`/ddcalc` (Phase A sibling) reads `summary.json` directly:
- `dm_candidate.mass_gev`
- `scatter.sigma_si_proton_cm2`, `scatter.sigma_sd_proton_cm2`
- isospin-asymmetric case: both proton + neutron entries

No shared state beyond the JSON file path; `/ddcalc` never re-runs micrOMEGAs.

### Orchestrator update (Phase C)

`/lagrangian-builder` dispatches `/micromegas all <model>` when the user phrase contains "relic density," "dark matter abundance," "annihilation cross section," or "indirect detection."

---

## 4. Plugin placement — position: **new `plugins/constraints/`**

The roadmap open question "shared `plugins/constraints/` plugin or co-locate with `/model-building`?" — answer: **new plugin**.

Arguments:

1. **Separation of concerns.** `model-building` currently describes the tools that *produce* a model (Lagrangian → UFO → SLHA). `constraints` is what *tests* a model against experiment. Different mental model, different user entry points.
2. **Install-skill locality.** Each of `/micromegas`, `/ddcalc`, `/higgstools` has a distinct upstream tool with its own installer, version pin, and config key namespace. Putting three more install skills under `model-building` would bloat its skill list from 6 to 12.
3. **Phase-B additions (`/feynarts`, `/formcalc`, `/looptools`) are a different beast** — those are symbolic calculators, not constraints. They probably deserve yet another plugin (`plugins/loop-integrals/`) later. Keeping `constraints` narrow now leaves room.
4. **`_shared/` stays portable.** `blocker.schema.json` already lives at `plugins/hep-ph-toolkit/skills/_shared/`; the new `plugins/hep-ph-toolkit/skills/_shared/` can symlink or re-reference it. Better: the schema is arguably a marketplace-wide contract and should move to `plugins/shared/schemas/` — but that refactor is out of scope for this skill.

Proposed layout:

```
plugins/constraints/
  .claude-plugin/plugin.json
  README.md
  SHARED.md                # env vars, conventions
  skills/
    _shared/               # blocker schema ref, sarah_name reuse
    micromegas-install/
    micromegas/
    ddcalc-install/        # later (Phase A sibling)
    ddcalc/
    higgstools-install/
    higgstools/
```

### Counterposition (for the critic)

A co-location alternative exists: just add `skills/micromegas-install/` and `skills/micromegas/` under `plugins/model-building/`. It reuses `_shared/` with zero refactoring and keeps related physics in one place. I reject it because the "model-building vs constraints" conceptual split is strong enough to justify the second plugin. Critic is invited to disagree.

---

## 5. Open questions for the critic to attack

1. **CalcHEP bundling.** I position "bundle always." But if a user's machine already has CalcHEP 3.9 installed for a different workflow, our bundled 3.8.x wastes disk and could confuse path resolution. Should `use-path` support a split — external CalcHEP + micrOMEGAs-only build? I say no; critic should push back.

2. **UFO→CalcHEP conversion caching.** I cache on `sha256(ufo_path)`. But the CalcHEP converter shipped with micrOMEGAs is sensitive to micrOMEGAs version itself, and UFO 2.0 vs 1.0 vs 1.1 compatibility matters. Is the cache key complete? Should it include `micromegas_version` and UFO-version probe?

3. **DM candidate auto-detection.** The SARAH-generated UFO labels Z2-odd particles via `LanHEP`-style `TeX` names, not a clean `parity` attribute. My heuristic (lightest stable non-SM with SARAH's `odd` tag) is fragile for models with broken Z2 or multi-component DM. Should I refuse to auto-detect and require explicit `dm_candidate` in spec.yaml?

4. **Reference-only fallback policy.** The user's memory says "augment not replace — block on missing tool-drivers rather than fall back to analytic." Does that mean `--allow-analytic-fallback` should be removed entirely and `reference_only` never emitted by this skill? I left it in as an opt-in escape hatch for offline work. Critic: should it come out?

5. **Indirect-detection spectra — file outputs vs in-JSON arrays.** I plan to write spectra to separate `.dat` files and reference them by path in `summary.json`. For scans with 10³ points this produces 10³ files. Should the arrays be inlined into `summary.json` (larger JSON) or compressed to a single HDF5 per scan?

6. **Three-state blocker: is `OMEGA_UNCONVERGED` truly recoverable?** In scan mode, yes — the row is lost but the scan continues. In single-point mode it is effectively fatal for the user's intent. Do I need a mode-aware blocker, or is "recoverable" correct by the schema's definition?

7. **Version pin 6.1.15 vs 6.0.x LTS.** 6.1.x has better UFO2 support but is younger. Do we take the risk, or pin 6.0.5 and accept UFO1-only?

---

End of proposer output. Word count: ~1180.
