# /higgstools — Final Design (Synthesizer)

Reconciles proposer + critic under manager-imposed cross-workstream decisions.
Legacy HB-5.10.2 + HS-2.6.2 Fortran is the v1 default; unified C++ is opt-in.
SLHA-with-CP-conservation is the only v1 input path. Two subcommands.
`allowed` splits into `hb_allowed` + `hs_consistent`.

---

## 0. Upstream pin audit (resolves critic §2)

Verified four separate public GitLab repos under `gitlab.com/higgsbounds/`:

| Repo | v1 pin | Date | Purpose |
|---|---|---|---|
| `higgsbounds` | tag **`5.10.2`** | 2021-12-13 | Legacy Fortran HB-5 source |
| `higgssignals` | tag **`2.6.2`** | 2021-09-28 | Legacy Fortran HS-2 source |
| `hbdataset` | tag **`v1.7`** | 2025-09-11 | HB experimental data (for unified backend) |
| `hsdataset` | tag **`v1.1`** | 2023-05-22 (SHA `3c6c2538`) | HS experimental data (for unified backend) |
| `higgstools` | tag **`v1.2`** | — | Unified C++ library, opt-in only |

Legacy HB-5.10.2 and HS-2.6.2 ship their experimental data *inside the source
tree* (`Expt_tables/`, `Data_tables/`) — no separate dataset pin is needed when
`backend=legacy`. The `hbdataset`/`hsdataset` pins apply only when a user sets
`HEPPH_HIGGSTOOLS_BACKEND=unified`. This sidesteps the critic's "who updates
the SHA" concern for v1: legacy data is frozen with the source pin.

---

## 1. `/higgstools-install`

### Subcommands
```
/higgstools-install detect          # emits {status: configured|found|missing}
/higgstools-install use-path <dir>  # register existing build(s)
/higgstools-install install         # auto-build legacy HB + HS
```
(`update-dataset` deferred to v1.1 with unified backend.)

### Install flow (default, backend=legacy)

1. `check_disk 3` — two Fortran builds + sources.
2. Toolchain check: `gfortran` (reuses `EXIT_NO_GFORTRAN=10`). No cmake/pybind
   on legacy path. On Apple Silicon, check `gfortran -v` reports
   aarch64-apple-darwin; warn-and-continue if Homebrew `gcc@13`+ is not linked
   on `$PATH` (known M-series Fortran trap — Homebrew ships `gfortran-13`, not
   `gfortran`; installer symlinks into `$HOME/.local/bin` on request).
3. If `HEPPH_NO_NETWORK=1`, bail early with `HIGGSTOOLS_OFFLINE_NO_CACHE`
   fatal (matches SPheno-install behavior).
4. `download_with_retry` the two source tarballs:
   - `https://gitlab.com/higgsbounds/higgsbounds/-/archive/5.10.2/higgsbounds-5.10.2.tar.gz`
   - `https://gitlab.com/higgsbounds/higgssignals/-/archive/2.6.2/higgssignals-2.6.2.tar.gz`
5. `verify_checksum` with real SHA256 in `skill_env.yaml` (pre-computed at
   plugin-build time; `TODO` only permitted during scaffolding per `_common.sh`
   convention).
6. Build HB-5:
   `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j`.
7. Build HS-2 with `-DHiggsBounds_DIR=<hb-build>` (HS's CMakeLists auto-links
   HB; this resolves critic §15's "two separate builds / configure-with-chiSq"
   concern — modern CMake handles it).
8. Smoke test: run HB's bundled `example_SM_vs_4thgen` executable; expect
   `HBresult=1` (not excluded). Run HS's bundled example on the same SM point;
   expect finite chi² < 200. Fatal if either binary is absent or output
   differs.
9. `config_merge` keys (see §1.1). Mark `last_configured`.

### Opt-in unified backend

Gated on `HEPPH_HIGGSTOOLS_BACKEND=unified` *and* explicit
`/higgstools-install install --backend=unified`. Adds:
- Toolchain: cmake ≥ 3.16, g++ ≥ 11 (for full C++17 `<filesystem>`), Eigen3,
  GSL, pybind11 headers, Boost ≥ 1.74. Missing → `HIGGSTOOLS_TOOLCHAIN_MISSING`.
- `git clone --depth 1 --branch v1.7 hbdataset`, ditto `--branch v1.1 hsdataset`.
- Build `higgstools` v1.2 with `-DHiggsTools_BUILD_PYTHON=ON`.
- Smoke test: `python3 -c "import Higgs.bounds, Higgs.signals"`.
- Apple Silicon caveat in SKILL.md: "unified build is currently unverified on
  macOS-14 arm64; expect Eigen/Boost ABI issues. CI matrix targets ubuntu-22.04
  first." (critic §1 concession.)

### 1.1 Config keys

| Key | Value |
|---|---|
| `higgstools_backend` | `legacy` (default) or `unified` |
| `higgsbounds_path` | `$HOME/HiggsBounds-5.10.2/build` |
| `higgsbounds_version` | `5.10.2` |
| `higgssignals_path` | `$HOME/HiggsSignals-2.6.2/build` |
| `higgssignals_version` | `2.6.2` |
| `higgstools_path` | (unified only) `$HOME/HiggsTools-1.2` |
| `hbdataset_path` / `hbdataset_commit` | (unified only) clone + SHA |
| `hsdataset_path` / `hsdataset_commit` | (unified only) clone + SHA |
| `higgstools_installed_at` | ISO 8601 UTC |

### 1.2 Blocker codes

| Code | Mode | Trigger |
|---|---|---|
| `HIGGSTOOLS_TOOLCHAIN_MISSING` | fatal | gfortran absent (legacy) or cmake/pybind11 absent (unified) |
| `HIGGSTOOLS_OFFLINE_NO_CACHE` | fatal | `HEPPH_NO_NETWORK=1` and no cached tarball |
| `HIGGSTOOLS_DOWNLOAD_FAILED` | fatal | tarball + one retry failed |
| `HIGGSTOOLS_BUILD_FAILED` | fatal | CMake/make non-zero; tail of build.log in `context` |
| `HIGGSTOOLS_SMOKE_TEST_FAILED` | fatal | SM example output out of range |
| `HIGGSTOOLS_PATH_INVALID` | fatal | `use-path` target missing HB/HS binaries or headers |

New shared exit codes requested from W0: `EXIT_NO_CMAKE=26`, `EXIT_NO_PYBIND=27`
(unified-only). Legacy path reuses `EXIT_NO_GFORTRAN=10`.

---

## 2. `/higgstools` — usage skill

### Subcommands (collapsed to 2 per critic §7)

```
/higgstools run <model>       # per-point HB + HS on the latest SLHA
/higgstools aggregate <dir>   # join across a /spheno-build --scan run dir
```

### Inputs

- `--model <name>` (required): reads
  `config.models[<name>].latest_slha` (SLHA2 from `/spheno-build`).
- `--slha <path>`: explicit override.
- `--dMh <GeV>` or `--dMh <json>`: theoretical mass uncertainty for HS χ²
  (resolves critic §9). Default 2 GeV for h-like (m < 200), 5 GeV for heavy.
  JSON form: `{"h0":2.0, "H0":5.0, "A0":5.0}`.
- `--mode=both|hb|hs` (default `both`).
- `--backend=legacy|unified` (overrides config).
- `--channels=all|neutral|charged|<csv>` (HB only).

### Data contract (input)

Only SLHA2 from `/spheno-build`. The SARAH-generated SPheno must emit:
`SPhenoInput` block with the HB switch on, producing
`HiggsBoundsInputHiggsCouplingsFermions` and
`HiggsBoundsInputHiggsCouplingsBosons` blocks. No intermediate schema:
**SLHA is the schema**. Missing blocks → fatal
`HIGGSTOOLS_SLHA_MISSING_BLOCKS` with `user_instruction` to rerun
`/sarah-build` with `SPheno.m` directive `WriteHiggsBoundsBlocks=True`. **No
analytic fallback, no effective-coupling synthesis in Python** (per "augment
not replace" and critic §3).

v1 scope: CP-conserving scalar sectors only. CPV / complex mixing matrices
deferred to v1.1 (tracked as follow-up; SKILL.md states this explicitly).

### Outputs

Per point, under `$STATE_ROOT/models/<name>/runs/<TS>/higgstools/`:

`result.json`:
```
{
  "hb_allowed": bool,           # max(obsratio) < 1.0 (HB-5 convention)
  "hs_consistent": bool,        # chi2_total < chi2_SM_ref + 6.18 (2D 95% CL default)
  "obsratio_max": float,
  "most_sensitive_channel": {"id": int, "expref": str, "obsratio": float, "reference": str},
  "chi2_total": float,
  "chi2_rates": float,
  "chi2_masses": float,
  "ndf_rates": int,
  "ndf_masses": int,
  "p_value_rates": float,       # see §5
  "p_value_masses": float,
  "backend": "legacy" | "unified",
  "dataset_version": "HB-5.10.2/HS-2.6.2" | "hbdataset@<sha>+hsdataset@<sha>"
}
```
`per_channel.csv`: all HB channels tried (id, expref, obsratio, reference) —
critic §4 "full set not just most sensitive".
`report.md`: human-readable, mirrors HS `print_results()`.
`input_dump.json`: effective couplings + masses passed to the backend, for
reproducibility.

### Exclusion convention (critic §4)

HB-5 exclusion: **a point is HB-excluded iff the observed ratio of the most
sensitive single channel exceeds 1 at 95% CL** (Bechtle, Brein, Heinemeyer,
Stefaniak, Weiglein — HB manual §3.2). `hb_allowed = (obsratio_max < 1.0)`.

HS consistency: the paper arXiv:2506.19062 cites the Δχ² < 6.18 contour for
2-parameter 2D exclusion; v1 default matches. Emitted as
`hs_consistent = (chi2_total - chi2_SM_ref < 6.18)` where `chi2_SM_ref` is
HS's bundled reference. User-tunable via `--delta-chi2 <float>`. The exact
quote will be lifted into SKILL.md when the implementer reads §4 of the paper
(ACTION for W-phase implementer).

### Error modes

| Code | Mode | Trigger |
|---|---|---|
| `HIGGSTOOLS_SLHA_MISSING_BLOCKS` | fatal | required HB input blocks absent |
| `HIGGSTOOLS_DATASET_MISMATCH` | fatal | (unified) dataset SHA ≠ config pin |
| `HIGGSTOOLS_NUMERIC_CRASH` | recoverable | backend segfault on one scan row; row marked bad, scan continues |

No `reference_only` exits. No `--native` path (dropped per manager decision).

### Scan parallelism (critic §6 resolved)

`aggregate` walks scan dir; per-point `run` evaluations are independent and
run under `multiprocessing.Pool(os.cpu_count())` (or user-set
`HEPPH_HIGGSTOOLS_WORKERS`). Output `higgstools_index.csv` is sorted by SPheno
`index` column for byte-identical output across worker counts.

---

## 3. Data contracts

Upstream (from `/spheno-build`): SLHA2 file at
`config.models[<name>].latest_slha`. Required blocks: `MASS`, `HMIX`, decay
tables for neutral + charged Higgs, `HiggsBoundsInputHiggsCouplingsFermions`,
`HiggsBoundsInputHiggsCouplingsBosons`. No shared JSON schema — SLHA2 is the
contract.

Downstream (to `/hep-plotting`): `result.json` + `per_channel.csv`.
`/hep-plotting` reads `p_value_*` and `hb_allowed`/`hs_consistent` directly;
no recomputation (critic §8).

Cross-plugin note (critic §5): `/higgstools` lives in `plugins/constraints/`
but reads a config key written by `/spheno-build` in `plugins/model-building/`.
This is documented in `plugins/constraints/SHARED.md` as an intentional
cross-plugin dependency — both plugins share the same
`~/.config/hep-ph-agents/config.json`, and that file *is* the cross-plugin
contract.

---

## 4. Experimental dataset coverage (v1 scope)

Legacy HB-5.10.2 ships (from `Expt_tables/` in source tarball):
- **Neutral-Higgs searches** relevant to 2HDM+a: LHC ATLAS/CMS A→Zh,
  H→ττ (high-mass), H→hh, A→bb, gg→H→γγ, VBF H→WW, H→ZZ(4l).
- **Charged-Higgs searches**: ATLAS/CMS H±→τν (light + heavy), H±→tb
  (heavy), H±→cs (light). PDG 37 assumed (SARAH convention — critic §15
  accepts coupling).
- LEP + Tevatron Higgs-width constraints.

Legacy HS-2.6.2 ships:
- ATLAS + CMS Run-2 combined 125 GeV Higgs signal-strength measurements
  (μ per production × decay mode).
- 36/fb and 137/fb STXS bins for the dominant channels.

Unified backend pins (`hbdataset@v1.7`, `hsdataset@v1.1`): superset of the
above, including post-2021 ATLAS/CMS Run-2 full-lumi results. v1 does not
rely on these; v1.1 promotes when unified backend is CI-green.

Dataset version string is emitted in every `result.json` so downstream plots
carry provenance.

---

## 5. p-value computation (resolved from critic §8)

Inline, using scipy (already a project dep via SARAH scripts). Fixed formula:

```
p_value_rates  = 1 - scipy.stats.chi2.cdf(chi2_rates,  ndf_rates)
p_value_masses = 1 - scipy.stats.chi2.cdf(chi2_masses, ndf_masses)
```

The `result.json` schema doc (`report.md` boilerplate) states: "p-values
assume the null hypothesis of SM + best-fit HS nuisance parameters; they are
*not* a global goodness-of-fit — see HS manual §4.3." `/hep-plotting` reads
these fields and never recomputes.

---

## 6. Test matrix

**Unit** (no network):
1. `slha_adapter` parses a canned 2HDM SLHA and constructs the HB input
   record; asserts couplings, masses, widths.
2. `exclusion.compute_hb_allowed` on a synthetic `obsratio_max=0.7` →
   `hb_allowed=True`; on `1.3` → `False`.
3. `p_value` on `(chi2=10, ndf=5)` matches `scipy` to 1e-12.
4. `aggregate` joins 3 fake per-point `result.json` files into one sorted CSV.
5. Blocker shape: every emitted blocker validates against
   `blocker.schema.json`.

**Integration** (gated on `HEPPH_RUN_NETWORK_TESTS=1`):
6. Install legacy HB-5.10.2 + HS-2.6.2 end-to-end, run the SM smoke test.
7. Run `/higgstools run` on a **golden fixture** — a 2HDM Type-II benchmark
   at `(m_A=400, tanβ=10, cos(β-α)=0.1)`. Expected `hb_allowed=False`
   (ATLAS H→ττ high-mass excludes this region per HB-5 manual Fig. 7);
   obsratio within ±5% of the manual's quoted value. This is the
   correctness smoke test the critic demanded (§14).
8. `aggregate` over a 5-point mini-scan; assert CSV determinism across
   `--workers=1` vs `--workers=4`.

**Goldens**: SLHA fixture + `result.json` capped at 100 KB, committed under
`plugins/hep-ph-toolkit/skills/higgstools/tests/fixtures/`. Source: adapt the
`2HDM-II-benchmark.slha` example shipped in HB-5.10.2's `example_data/`.

---

## 7. Open questions → defaults picked

| Question | Default |
|---|---|
| `--dMh` for heavy scalars? | 2 GeV (light), 5 GeV (heavy ≥ 200 GeV); JSON override. |
| Python floor? | 3.10 (matches `_common.sh` assert, sufficient for scipy + legacy Fortran f2py). |
| SARAH dual-format SLHA (critic §11)? | Prefer `HiggsBoundsInputHiggsCouplings{Fermions,Bosons}` (newer). Fall back to legacy `HiggsBounds` block with warning; error if both absent. |
| `aggregate` snapshot of dataset SHA into each run dir? | Yes — written to `input_dump.json` at run time. Resolves critic §12. |
| v1.1 backlog | CPV / `--native` input; unified C++ backend promoted to default; `HEPPH_HIGGSTOOLS_DATASET_OVERLAY` for user-local limits. |

Word count: ~1,560.
