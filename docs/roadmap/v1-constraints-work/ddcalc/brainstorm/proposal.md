# `/ddcalc` — Proposer brief

**Scope:** Two skills landed together — `/ddcalc-install` (detect/use-path/install) and `/ddcalc` (usage). Direct-detection likelihood + exclusion verdict against LZ, XENONnT, PandaX-4T, DarkSide-50, plus a neutrino-fog overlay. Inputs are (σ_SI_p, σ_SI_n, σ_SD_p, σ_SD_n, m_DM), optionally with halo overrides. Designed to run downstream of `/micromegas` (tree-level σ) and `/formcalc` (loop-level σ) without caring which produced the number.

---

## 1. `/ddcalc-install`

**Upstream.** DDCalc 2.2.0, upstream at GitLab `https://gitlab.com/C0RI0LIS/ddcalc` (historically Redmine at ddcalc.hepforge.org — GitLab mirror is the canonical build target in 2024+). Pin `HEPPH_DDCALC_VERSION=2.2.0` in `skill_env.yaml`, tarball `DDCalc-2.2.0.tar.gz`, SHA256 as a real value (no `TODO` placeholder — DDCalc releases are small enough to compute at author time).

Build: pure Fortran with a tiny C shim. `make` at the root produces `bin/DDCalc_exampleC`, `bin/DDCalc_exclusionC`, `bin/DDCalc_logLikelihoodC`, `lib/libDDCalc.a`. No LAPACK. Depends only on `gfortran` — reuse `EXIT_NO_GFORTRAN` from `_common.sh`. macOS/Linux parity is clean; the one known footgun is `-std=legacy` on recent gfortran, which the install script should force via `FFLAGS`.

**Subcommands** (mirror `/sarah-install` exactly):

- `/ddcalc-install detect` — scan `config.ddcalc_path`, then `~/DDCalc`, then `$HEPPH_STATE_ROOT/tools/DDCalc-*`. Emits `{"status":"configured"|"found"|"missing"}`.
- `/ddcalc-install use-path <dir>` — register an existing build. Validates `<dir>/bin/DDCalc_exclusionC` exists and runs `<dir>/bin/DDCalc_exampleC` as smoke (prints "DDCalc vX.Y" — parse for version).
- `/ddcalc-install install [<dir>]` — `check_disk 1`, `download_with_retry`, `verify_checksum`, extract, `make -j$(os.cpu_count)`, run smoke, write config.

**Scripts.**

| Script | Purpose |
|---|---|
| `scripts/install.sh` | Top-level installer; sources `_common.sh` |
| `scripts/detect_ddcalc.sh` | Candidate scan + config probe |
| `scripts/probe_version.sh` | Runs `DDCalc_exampleC`, regex `DDCalc ([0-9.]+)` |
| `scripts/_common.sh` | One-line shim to `plugins/shared/install-helpers/_common.sh` |

**Config keys written.**

| Key | Value |
|---|---|
| `ddcalc_path` | Absolute path to build dir (contains `bin/` and `lib/`) |
| `ddcalc_version` | e.g. `2.2.0` |
| `ddcalc_installed_at` | UTC ISO-8601 |
| `ddcalc_experiment_set` | `"bundled-2024.1"` — tag identifying which table rev is live |

**Blockers.**

| Code | Mode | Trigger |
|---|---|---|
| `DDCALC_DOWNLOAD_FAILED` | fatal | curl twice failed |
| `DDCALC_BUILD_FAILED` | fatal | `make` nonzero; tail of `build.log` in `context` |
| `DDCALC_SMOKE_TEST_FAILED` | fatal | `DDCalc_exampleC` nonzero or no version match |
| `DDCALC_PATH_INVALID` | fatal | `use-path` dir missing `bin/DDCalc_exclusionC` |
| `GFORTRAN_ABSENT` | fatal | reused code from SPheno pattern |

**Experiment-data currency (position I'll defend).** Bundle the tables that ship with DDCalc 2.2.0 and call them the "canonical set" (`ddcalc_experiment_set="bundled-2024.1"`). Do *not* try to hot-patch LZ/XENONnT updates into a stock DDCalc tree — experiment analysis files live at `data/experiments/*.eff/*.dat` and changing them silently invalidates the published likelihoods. Instead: provide an **override directory** via `HEPPH_DDCALC_EXPT_OVERLAY=<dir>` that is rsync-copied over `data/experiments/` before a run, and record a second config key `ddcalc_experiment_overlay` (path + its sha256) in every output JSON. This keeps reproducibility auditable. Newer analyses (e.g. LZ WS2024 full likelihood) land as named overlays shipped out of band, versioned in `plugins/hep-ph-toolkit/skills/_shared/expt_overlays/`. Rejected alternative: auto-pulling from HEPData — network dependence at runtime is a regression vs. the SARAH/SPheno hermetic-install pattern.

---

## 2. `/ddcalc`

**When to invoke.** After `/micromegas observables` or `/looptools scattering` writes a σ result JSON. Also usable stand-alone if the user hands in σ values.

**Input contract** (stdin or `--sigma-json <path>`):

```json
{
  "m_DM_GeV": 62.5,
  "sigma_SI_p_cm2": 1.3e-47,
  "sigma_SI_n_cm2": 1.3e-47,
  "sigma_SD_p_cm2": 0.0,
  "sigma_SD_n_cm2": 0.0,
  "source": "micromegas-6.2.3",
  "source_run": "/path/to/run/summary.json",
  "halo": {"profile":"SHM","v0":238,"vesc":544,"rho0":0.3}
}
```

`halo` is optional; default is DDCalc's built-in SHM (v0=235, vesc=550, rho0=0.3 — matches DDCalc defaults, NOT `/micromegas` defaults; the skill must log when it substitutes). `sigma_SI_n` defaults to `sigma_SI_p` if omitted (isospin-conserving, the common case).

**Operations.** One run triggers four calculations in the same process (one invocation of a small Fortran driver linked against `libDDCalc.a`, built once at install):

1. Per-experiment **log-likelihood** `logL_i` for i ∈ {LZ\_2024, XENONnT\_2023, PandaX4T\_2021, DarkSide50\_2018, plus whatever overlay is active}.
2. **90% CL exclusion check**: `p_excluded_i = LogLikelihoodToPValue(logL_i)`; verdict `excluded | allowed | marginal` thresholded at p<0.1 / p>0.1 / within 0.08–0.12.
3. **Neutrino-fog distance**: scalar `n_ν_SI` = σ_SI / σ_ν-floor(m_DM). Position: use the **Ruppin/O'Hare 2018 Xenon ν-floor curve** tabulated in `plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_xe.csv` rather than DDCalc's built-in (DDCalc's floor is older, O'Hare+ 2021 "neutrino fog" with the gradient-based definition is what the Arcadi–Profumo blind-spots paper overlays). Ship both, select via `HEPPH_NU_FLOOR={ohare2021,ruppin2014,ddcalc}`.
4. **Text report** + JSON emit.

**Output.**

```json
{
  "status": "ok",
  "verdict": "excluded|allowed|marginal",
  "m_DM_GeV": 62.5,
  "experiments": {
    "LZ_2024": {"logL": -17.3, "p_value": 3e-8, "excluded_90cl": true},
    "XENONnT_2023": {...}, "PandaX4T_2021": {...}, "DarkSide50_2018": {...}
  },
  "neutrino_fog": {"source":"ohare2021", "n_sigma_above_floor": 0.3, "in_fog": true},
  "inputs_echo": {...},
  "ddcalc_version": "2.2.0",
  "experiment_set": "bundled-2024.1",
  "overlay": null,
  "report_path": "$STATE_ROOT/runs/<TS>/report.md"
}
```

JSON to stdout; human report (markdown) to the path in `report_path`; blockers to stderr.

**Error modes / blockers.**

| Code | Mode | Trigger |
|---|---|---|
| `DDCALC_INPUT_INVALID` | fatal | σ negative, m_DM ≤ 0, or JSON schema violation |
| `DDCALC_MASS_OUT_OF_RANGE` | recoverable | m_DM outside [1, 1e5] GeV — most experiments have no efficiency data |
| `DDCALC_DRIVER_FAILED` | fatal | Fortran driver exit ≠ 0; `context.stderr_tail` attached |
| `DDCALC_OVERLAY_MISSING` | fatal | `ddcalc_experiment_overlay` path gone since install |
| `DDCALC_REFERENCE_ONLY` | — | `{"status":"reference_only","reference_method":"Lewin-Smith 1995 analytic","caveats":["no halo marginalization","no experiment efficiency curves"]}` — only used when `HEPPH_ALLOW_REFERENCE=1` is explicitly set. Default: block. This is the "augment not replace" rule from the roadmap memo. |

---

## 3. Integration

**Phase A placement.** `/ddcalc` is a leaf consumer — no mutual dep with `/micromegas` or `/higgstools`. Build in parallel with `/micromegas`.

**Data contract with upstream σ producers.** Both `/micromegas` and `/formcalc` write a `scattering.json` to `$STATE_ROOT/models/<name>/scattering/<TS>/scattering.json` with the exact schema in §2. `/ddcalc` accepts either via `--from-micromegas <path>` or `--from-looptools <path>` (syntactic sugar; both normalize to the same schema). The JSON must carry a `source` string so `report.md` can cite which σ the exclusion was computed from (tree- vs one-loop makes a ~10x difference in the blind-spot region — this is precisely the figure in arXiv:2506.19062).

**Paper reproduction (arXiv:2506.19062).** The 2HDM+a blind-spot figure 6/7 plots σ_SI vs m_DM with the LZ 2024 exclusion and the Xenon ν-floor. Reproduction recipe:

1. `/lagrangian-builder` → 2HDM+a via SARAH.
2. `/spheno-build` scans (m_a, tanβ, sinθ).
3. `/looptools scattering` → loop-level σ_SI per point → `scattering.json`.
4. `/ddcalc --from-looptools <path> --scan-index <scan_index.csv>` runs per-point, writes `ddcalc_scan.csv` with `(point_idx, sigma_SI, logL_LZ2024, excluded, n_sigma_fog)`.
5. `/hep-plotting` reads `ddcalc_scan.csv` and draws the exclusion contour + ν-fog overlay.

That chain gives an exact reproduction path.

---

## 4. Plugin placement

**Create `plugins/constraints/`** and put `/ddcalc`, `/ddcalc-install`, `/higgstools`, `/higgstools-install`, `/micromegas`, `/micromegas-install` there. Justification:

- The constraint skills are a coherent semantic group ("does this BSM point pass experiment X?") distinct from `model-building` (construction) and `collider-pheno` (predictions).
- They share `_shared/expt_overlays/`, `_shared/scattering.schema.json`, and a common SLHA/UFO-consumer pattern that makes a shared plugin dir reduce duplication.
- Keeping them in `model-building` would bloat a plugin that is already the marketplace's heaviest, and co-locating LHC-Higgs-limits skills with Lagrangian-construction skills is semantically wrong.
- Rejected alternative (co-locate in `model-building`): saves one plugin.json but muddles the marketplace category table in `CLAUDE.md`, which already has distinct "Theory" vs an implied "Constraints" slot.

Plugin manifest entry:

```json
{"name":"constraints","description":"Constraint & likelihood skills (direct detection, Higgs limits, relic density)"}
```

and update `CLAUDE.md`'s category table to add a "Constraints" row.

---

## 5. Open questions for the critic

1. **Halo-parameter marginalization.** Should `/ddcalc` offer a `--marginalize-halo` mode that profiles over (v0, vesc, rho0) priors à la Green 2017? DDCalc supports it via repeated evaluations; cost is ~50× single-point. My position: expose as opt-in, default off — the paper reproduction uses fixed SHM.
2. **Emit DDCalc-native input files for debugging.** When the Fortran driver fails or the user wants to inspect by hand, should we dump the generated `DDCalc.in`-equivalent input (or the C driver's stdin stream) alongside `report.md`? Cheap to do and saves hours in the debug loop, but adds a file nobody normally reads. My position: yes, always, gated behind `--debug` flag but on by default when `DDCALC_DRIVER_FAILED` fires.
3. **Neutrino fog source of truth.** I argue for O'Hare 2021 as default (matches Arcadi–Profumo figures). Critic may prefer DDCalc's bundled curve for audit simplicity. Rebuttal I'd make: we already record `source` in JSON, so provenance is clean either way.
4. **Isospin-violating input.** Do we accept `sigma_SI_p ≠ sigma_SI_n`? DDCalc supports it natively. `/micromegas` rarely emits the split. Position: accept both, but default `sigma_SI_n = sigma_SI_p` on missing and log a warning.
5. **Sub-GeV masses.** LZ/XENONnT have migdal/sub-GeV analyses now; DDCalc 2.2.0 does not include them. Do we scope-creep into a "migdal" overlay, or leave sub-GeV as `MASS_OUT_OF_RANGE`? My position: out of scope for v1, note in README.
6. **Scan-mode parallelism.** Should `/ddcalc --scan-index` fork N workers, or stay serial like `/spheno-build`? σ_SI per point via DDCalc is ~50 ms, so serial is fine up to ~10k points. Position: serial in v1; matches SPheno's determinism guarantee.

---

**Summary position.** Ship `/ddcalc-install` + `/ddcalc` together in a new `plugins/constraints/` dir, in Phase A parallel with `/micromegas`. Bundle DDCalc 2.2.0 experiment tables as the canonical set with an overlay-override mechanism; use O'Hare 2021 as the default ν-floor; block on `reference_only` unless explicitly opted in; standardize a `scattering.json` schema shared with `/micromegas` and `/formcalc` so the paper-reproduction chain is a 4-command pipe.
