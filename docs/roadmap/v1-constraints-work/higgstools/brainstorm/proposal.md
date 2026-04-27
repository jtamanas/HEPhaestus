# /higgstools — Proposal (Proposer)

Skill pair for **HiggsTools**: scalar-sector exclusion (HiggsBounds-5 logic) and
Higgs-signal chi² fits (HiggsSignals logic), consuming SPheno SLHA from W4.
Follows the `detect | use-path | install` + `blocker.schema.json` pattern
established by `/sarah-install` and `/spheno-install`.

---

## 1. Backend choice: HiggsTools unified library (recommended)

There are two viable backends:

| Option | Pros | Cons |
|---|---|---|
| **HiggsTools** (C++ library, pybind11 bindings; combines HB-5 + HS + HiggsPredictions) | Active upstream (Bahl, Biekötter, Heinemeyer, Papaefstathiou, Weiglein; v1.2 as of 2024). Single library. Python API. Charged-Higgs channels first-class. Effective couplings + cross-section / BR input. Dataset lives in a separate git repo (`hbdataset`, `hsdataset`) so experimental-data updates don't require a code rebuild. | C++17 + Eigen + GSL + pybind11 build. Newer → less battle-tested against SPheno-SLHA edge cases. |
| Legacy **HiggsBounds 5.10.2 + HiggsSignals 2.6.2** (Fortran) | Directly consumes SLHA `HiggsBoundsInputHiggsCouplingsFermions/Bosons` blocks that SPheno-SARAH already writes. Stable, well-documented. Reference for arXiv:2506.19062-era papers. | Two separate builds, Fortran-only, no ongoing releases (last tag ~2020), dataset frozen in source tree. |

**Recommendation:** default to **HiggsTools unified** (current best practice),
but support a `--backend legacy` escape hatch for exact reproduction of older
papers (including 2506.19062, which likely used HB-5/HS-2 Fortran). Both
backends reuse the same SLHA-to-input adapter.

### Upstream pins

- `higgstools` v1.2 — https://gitlab.com/higgsbounds/higgstools (tag `v1.2`).
- `hbdataset` commit `HEAD@{2024-09-01}` — https://gitlab.com/higgsbounds/hbdataset.
- `hsdataset` commit `HEAD@{2024-09-01}` — https://gitlab.com/higgsbounds/hsdataset.
- Legacy fallback: `HiggsBounds-5.10.2`, `HiggsSignals-2.6.2` from the same
  GitLab group (tarballs). Pins live in `skill_env.yaml`.

Datasets are **pinned independently from the code** — this is the whole point
of splitting them out upstream. Reproducibility requires both pins in
`~/.config/hep-ph-agents/config.json`.

---

## 2. `/higgstools-install` subcommands

Pattern copied from `/sarah-install`:

```
/higgstools-install detect          # emits {"status":"configured|found|missing"}
/higgstools-install use-path <dir>  # register existing HiggsTools build
/higgstools-install install         # auto-build HiggsTools + clone datasets
/higgstools-install update-dataset  # pull newer hbdataset/hsdataset pin only
```

### Install flow

1. `check_disk 2` (via `_common.sh`) — HiggsTools build + Eigen + datasets ~1.5 GB.
2. Check for `cmake ≥ 3.16`, `g++ ≥ 9`, `python3` with `pybind11` headers. Missing → `HIGGSTOOLS_TOOLCHAIN_MISSING` fatal blocker with `user_instruction`.
3. `download_with_retry` the HiggsTools source tarball (pinned tag).
4. `verify_checksum` (`TODO` placeholder OK per `_common.sh` convention; warn).
5. `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DHiggsTools_BUILD_PYTHON=ON`, `cmake --build build -j<cpu_count>`, `cmake --install build --prefix $HOME/HiggsTools-<ver>`.
6. `git clone --depth 1 --branch <pin>` `hbdataset` and `hsdataset` into sibling dirs.
7. Smoke test: import `Higgs.predictions` + `Higgs.bounds` from Python; run a trivial SM-like point → expect `allowed=True`, finite chi².
8. Write config keys; mark `last_configured`.

### Config keys written

| Key | Value |
|---|---|
| `higgstools_path` | Install prefix (`$HOME/HiggsTools-<ver>`) |
| `higgstools_version` | e.g. `1.2` |
| `higgstools_backend` | `unified` or `legacy` |
| `hbdataset_path` | Absolute path to `hbdataset/` clone |
| `hbdataset_commit` | SHA pin |
| `hsdataset_path` | Absolute path to `hsdataset/` clone |
| `hsdataset_commit` | SHA pin |
| `higgstools_installed_at` | ISO 8601 UTC |

### Blockers

| Code | Mode | Trigger |
|---|---|---|
| `HIGGSTOOLS_TOOLCHAIN_MISSING` | fatal | cmake / g++ / pybind11 absent |
| `HIGGSTOOLS_DOWNLOAD_FAILED` | fatal | tarball + two retries failed |
| `HIGGSTOOLS_BUILD_FAILED` | fatal | cmake/make non-zero; tail of build.log in `context` |
| `HIGGSTOOLS_DATASET_MISSING` | fatal | hbdataset or hsdataset clone absent |
| `HIGGSTOOLS_SMOKE_TEST_FAILED` | fatal | Python import or SM-like check fails |
| `HIGGSTOOLS_PATH_INVALID` | fatal | `use-path` dir lacks `include/Higgs/` or `lib/libHiggs*` |

New shared exit codes in `_common.sh` (request W0 allocation): `EXIT_NO_CMAKE=26`, `EXIT_NO_PYBIND=27`. No changes required if we reuse `EXIT_GENERIC`; prefer named.

---

## 3. `/higgstools` usage skill

### Inputs

- `--model <name>` — reads `config.models[<name>].latest_slha` written by `/spheno-build`.
- `--slha <path>` — override SLHA file explicitly.
- `--native <path>` — bypass SLHA and consume a HiggsTools-native YAML input
  (for models whose couplings aren't representable in SLHA `HiggsBoundsInput*`
  blocks; see open question 2).
- `--channels all|neutral|charged|<csv>` — limit channel search (e.g. restrict
  to `HBcharged` for H±-focused studies).
- `--backend unified|legacy` — overrides config default.

### Operations

```
/higgstools run <model>            # HB exclusion + HS chi² in one shot
/higgstools exclude <model>        # HB only
/higgstools signals <model>        # HS only
/higgstools scan-summary <run_dir> # aggregate over a /spheno-build --scan dir
```

`scan-summary` walks `$STATE_ROOT/models/<name>/runs/scan_<TS>/` and writes a
joined `higgstools_index.csv` keyed by SPheno `index`.

### Outputs

Per point, written to `$STATE_ROOT/models/<name>/runs/<TS>/higgstools/`:

| File | Content |
|---|---|
| `result.json` | `{allowed: bool, obsratio: float, most_sensitive: {channel, expref, obsratio, reference}, chi2_total, chi2_rates, chi2_masses, ndof, pvalue}` |
| `per_channel.csv` | All HB channels tried, with obsratio + ref; sortable |
| `report.txt` | Human-readable summary mirroring HS `print_results()` |
| `input_dump.json` | The effective HiggsPredictions input used (for reproducibility) |

### Error / recoverable modes

| Code | Mode | Trigger |
|---|---|---|
| `HIGGSTOOLS_SLHA_MISSING_BLOCKS` | recoverable | SLHA lacks `HiggsBoundsInputHiggsCouplings*` blocks (SARAH-generated SPheno usually writes these; fallback: compute effective couplings from `Block MASS` + decay tables — emit caveats) |
| `HIGGSTOOLS_DATASET_VERSION_MISMATCH` | fatal | Dataset commit differs from config pin (drift protection) |
| `HIGGSTOOLS_NO_CHARGED_HIGGS` | reference_only | Model has no H± but user asked for charged channels — fall back + caveat |
| `HIGGSTOOLS_NUMERIC_CRASH` | recoverable | libHiggs threw; point marked bad in scan index, continue |

`reference_only` exits follow Blocker #25 — must include `reference_method` and non-empty `caveats` list.

---

## 4. Integration

**Phase A parallel** with `/micromegas` and `/ddcalc` (per roadmap). Data contract:

```
/spheno-build  →  $STATE_ROOT/models/<name>/runs/<TS>/SPheno.spc
                    │
                    ├──► /higgstools run <name>
                    ├──► /micromegas relic <name>
                    └──► /ddcalc limits <name>
```

Zero mutual dependencies. `/higgstools` reads only `config.models[<name>].latest_slha`.

### arXiv:2506.19062 reproduction (2HDM+a)

The 2HDM+a has three neutral CP-even (h, H, a_light/a_heavy mixing), one CP-odd
A, and charged H±. HiggsBounds' charged-Higgs + heavy-Higgs searches (ttbar,
tau-tau, A→Zh) are precisely the constraints the paper overlays on its blind-spot
grids (fig. 8–10 era plots). HiggsSignals pins the 125 GeV h to ATLAS/CMS
combined measurements — crucial because blind-spot directions often drive the
light CP-even mixing angle α − β ≠ π/2, which HS chi² penalizes.

Deliverable checkpoint: `/higgstools scan-summary` over the paper's
(tan β, m_A, m_a, sin θ) scan, overlaid with the paper's fig. 8 excluded region.

---

## 5. Plugin placement

**Proposal:** new `plugins/constraints/` plugin housing `/higgstools`,
`/micromegas`, `/ddcalc`. Rationale:

1. `plugins/model-building/` is already ~7 skills deep (sarah-install,
   sarah-build, spheno-install, spheno-build, rge-runner, lagrangian-builder,
   _shared). Adding 3 constraint skills bloats it.
2. Constraint skills are **consumers**, not builders. Different mental model:
   "given a spectrum, compare to experiment." Users searching "direct detection"
   should land in a focused plugin.
3. Sharing: the blocker schema and `_common.sh` already live under
   `plugins/shared/` and `plugins/hep-ph-toolkit/skills/_shared/` — both are
   reachable from a sibling plugin. No duplication needed.
4. The roadmap explicitly lists this option as an open question; I'm taking a
   stand.

Manifest: `plugins/constraints/.claude-plugin/plugin.json`; register in
`.claude-plugin/marketplace.json`. SHARED.md copied minimally (env-var
overrides, three-state blocker contract reference).

---

## 6. Open questions for critic

1. **Legacy vs unified default.** If arXiv:2506.19062 used HB-5/HS-2 Fortran
   and our demo must reproduce their exclusion boundary bit-for-bit, should
   `--backend legacy` be the default, with unified as the forward-looking
   option? Or always default to unified and accept small numeric drift?
2. **Non-SLHA input path.** SPheno-SARAH SLHA covers most neutral-scalar
   content, but 2HDM+a has CP-violating mixing that sometimes breaks the
   `HiggsBoundsInput*` block ordering. Do we maintain our own SLHA→native
   converter, or require upstream SPheno patches? The former is fragile; the
   latter delays the skill.
3. **Dataset pinning UX.** `update-dataset` can drift silently — if a user runs
   it, their old scan results are no longer reproducible. Should we refuse to
   update when `$STATE_ROOT/models/*/runs/*/higgstools/` exists without an
   explicit `--force`? Or snapshot the dataset commit *into* each run dir?
4. **Charged-Higgs channels vs model introspection.** HiggsTools errors
   unhelpfully when fed a neutral-only model with `--channels charged`. Do we
   introspect SLHA `Block MASS` for H± PDG 37 before dispatching, or trust
   upstream? Introspection adds coupling to SARAH's PDG conventions.
5. **Scan-mode parallelism.** `/spheno-build --scan` is sequential by design.
   HiggsTools is fast (~10 ms/point in C++). Do we parallelize over scan points
   here, or stay sequential to match the W4 determinism contract?
6. **chi² significance vs absolute.** HS returns raw chi². Users will want a
   p-value against N_obs degrees of freedom; do we compute it inline (scipy)
   or leave it to downstream plotting?

---

## Deliverables summary

- `plugins/constraints/.claude-plugin/plugin.json`
- `plugins/hep-ph-toolkit/skills/higgstools-install/SKILL.md` + `scripts/` +
  `skill_env.yaml` + tests (gated on `HEPPH_RUN_NETWORK_TESTS=1`).
- `plugins/hep-ph-toolkit/skills/higgstools/SKILL.md` + `scripts/run_higgstools.py`,
  `scripts/slha_adapter.py`, `scripts/report.py`, `scripts/scan_summary.py`.
- Marketplace registration.
- Fixture: one pre-canned SPheno SLHA (2HDM benchmark) + golden `result.json`
  for the smoke test. Hard cap 100 KB.
