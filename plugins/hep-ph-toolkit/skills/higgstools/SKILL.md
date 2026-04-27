---
name: higgstools
description: Run HiggsBounds-5 + HiggsSignals-2 constraint checks on a model SLHA file. Computes hb_allowed (per-channel AND), hs_consistent (Δχ² < 6.18), p-values, and per-channel CSV. Supports single-point and scan-directory modes.
---

## When to invoke

Use `/higgstools` after `/higgstools-install` has configured HiggsBounds and
HiggsSignals. Requires an SLHA2 file produced by `/spheno-build` with
`WriteHiggsBoundsBlocks=True` in the SARAH `SPheno.m`.

One subcommand:

```
/higgstools run <model>          # per-point HB + HS on the latest SLHA
```

---

## Inputs

| Flag | Type | Default | Description |
|---|---|---|---|
| `--model <name>` | string | required | reads `config.models[<name>].latest_slha` |
| `--slha <path>` | path | — | explicit SLHA override (skips config lookup) |
| `--dMh <GeV\|json>` | float or JSON | `{"h0":2.0,"heavy":5.0}` | theoretical mass uncertainty for HS χ² |
| `--mode <both\|hb\|hs>` | enum | `both` | run HB only, HS only, or both |
| `--backend <legacy\|unified>` | enum | `legacy` | override config backend |
| `--channels <all\|neutral\|charged\|csv>` | string | `all` | HB channel filter |
| `--delta-chi2 <float>` | float | `6.18` | Δχ² threshold for hs_consistent |
| `--workers <int>` | int | `os.cpu_count()` | parallelism for scan-dir mode |
| `--scan-dir <path>` | path | — | fan out over all SLHA files in directory |

### `--dMh` detail

Default: 2 GeV for Higgs-like states with m < 200 GeV; 5 GeV for heavier
scalars. JSON form allows per-state override: `{"h0":2.0, "H0":5.0, "A0":5.0}`.

---

## Data contract (input)

**Only SLHA2 from `/spheno-build`.**

Required SLHA blocks:
- `MASS` — Higgs masses
- `HMIX` — mixing angles
- Decay tables for neutral + charged Higgs
- `HiggsBoundsInputHiggsCouplingsFermions`
- `HiggsBoundsInputHiggsCouplingsBosons`

If the `HiggsBoundsInputHiggsCouplingsX` blocks are absent but the legacy
`HiggsBounds` block is present, a warning is emitted and the legacy block is
used. If both are absent: fatal `HIGGSTOOLS_SLHA_MISSING_BLOCKS`.

**No analytic fallback, no effective-coupling synthesis in Python.**
Missing blocks must be fixed at the SPheno generation level.

v1 scope: CP-conserving scalar sectors only. CPV / complex mixing matrices
are deferred to v1.1 (tracked as follow-up issue).

---

## Outputs

Per point, under `$STATE_ROOT/models/<name>/runs/<TS>/higgstools/`:

### `result.json`

```json
{
  "hb_allowed": true,
  "hs_consistent": true,
  "obsratio_max": 0.72,
  "most_sensitive_channel": {
    "id": 342,
    "expref": "ATLAS-HIGG-2016-07",
    "obsratio": 0.72,
    "reference": "Aaboud:2018xdt"
  },
  "chi2_total": 89.1,
  "chi2_rates": 85.0,
  "chi2_masses": 4.1,
  "ndf_rates": 80,
  "ndf_masses": 5,
  "p_value_rates": 0.21,
  "p_value_masses": 0.54,
  "backend": "legacy",
  "dataset_version": "HB-5.10.2/HS-2.6.2"
}
```

### `per_channel.csv`

All HB channels tried: `id, expref, obsratio, hb_result, reference`.

### `report.md`

Human-readable summary — rendered inline by the agent from `result.json`
(no `report.py` script exists; the agent emits the Markdown table directly).

To render `report.md` from `result.json`, emit a Markdown document with this
structure:

```markdown
# HiggsTools Constraint Report

**Backend:** <result.backend>
**Dataset:** <result.dataset_version>

## HiggsBounds-5

- **hb_allowed:** <result.hb_allowed>
- **obsratio_max:** <result.obsratio_max>  (4 decimal places)
- **Most sensitive:** channel <result.most_sensitive_channel.id>
  (<result.most_sensitive_channel.expref>),
  obsratio=<result.most_sensitive_channel.obsratio>

## HiggsSignals-2

- **hs_consistent:** <result.hs_consistent>
- **chi2_total:** <result.chi2_total>  (3 decimal places)
- **chi2_rates:** <result.chi2_rates> (ndf=<result.ndf_rates>)
- **chi2_masses:** <result.chi2_masses> (ndf=<result.ndf_masses>)
- **p_value_rates:** <result.p_value_rates>  (4 decimal places)
- **p_value_masses:** <result.p_value_masses>  (4 decimal places)

> p-values assume the null hypothesis of SM + best-fit HS nuisance
> parameters; they are *not* a global goodness-of-fit — see HS manual §4.3.
```

Omit any sub-block whose key is absent from `result.json` (e.g. omit the
HiggsSignals-2 block when running with `--mode hb`).

### `input_dump.json`

Effective couplings + masses passed to the backend, plus dataset SHA for
reproducibility. Read by `/hep-plotting` for provenance.

---

## Exclusion conventions

### HiggsBounds-5 (`hb_allowed`)

A point is HB-allowed iff **all per-channel `HBresult` values equal 1**:

```python
hb_allowed = all(ch.hb_result == 1 for ch in channels)
```

This is the AND-of-per-channel convention from HB-5's C++ API. It differs
from the legacy scalar `obsratio_max < 1.0` check — the per-channel AND is
stricter and correct for multi-Higgs sectors.

### HiggsSignals-2 (`hs_consistent`)

```python
hs_consistent = (chi2_total - chi2_sm_ref) < delta_chi2
```

Default `delta_chi2 = 6.18` (2D 95% CL, two free parameters). The SM
reference `chi2_sm_ref` is cached at install time by running HS on the
bundled SM SLHA fixture. Override with `--delta-chi2`.

If the SM reference cache (`$STATE_ROOT/cache/hs2_chi2_sm_ref.json`) is
absent, a fatal `HIGGSTOOLS_SM_REF_MISSING` blocker is emitted.

### p-values

```python
p_value_rates  = scipy.stats.chi2.sf(chi2_rates,  ndf_rates)
p_value_masses = scipy.stats.chi2.sf(chi2_masses, ndf_masses)
```

`(chi2, ndf)` pairs come from HS native output (`HiggsSignals_get_Peak_Chisq`)
— **never** computed Python-side from `len(channels)`.

---

## Scan aggregation (agent-driven)

After a scan with `--scan-dir <dir>`, each point produces a
`result.json` under `$STATE_ROOT/models/<name>/runs/<TS>/higgstools/`.
To build a scan summary CSV, read those files directly:

1. `find <scan_dir> -name "result.json"` — collect all result files.
2. For each file, parse JSON and extract: `index`, `hb_allowed`,
   `hs_consistent`, `obsratio_max`, `chi2_total`, `chi2_rates`,
   `chi2_masses`, `ndf_rates`, `ndf_masses`, `p_value_rates`,
   `p_value_masses`, `backend`, `dataset_version`, `slha_file`.
3. Sort rows by the `index` field (integer).
4. Write `higgstools_index.csv` with those columns in that order.

Priority columns (put first): `index`, `hb_allowed`, `hs_consistent`,
`obsratio_max`, `chi2_total`, `chi2_rates`, `chi2_masses`, `ndf_rates`,
`ndf_masses`, `p_value_rates`, `p_value_masses`, `backend`,
`dataset_version`, `slha_file`.

**Never re-invoke HB or HS during aggregation.** Re-running constraint
checks is the job of `run --scan-dir <dir>`.

---

## Error modes

| Code | Mode | Trigger |
|---|---|---|
| `HIGGSTOOLS_SLHA_MISSING_BLOCKS` | `fatal` | required HB input blocks absent from SLHA |
| `HIGGSTOOLS_SM_REF_MISSING` | `fatal` | chi2_SM_ref cache absent (re-run `/higgstools-install install`) |
| `HIGGSTOOLS_DATASET_MISMATCH` | `fatal` | (unified) dataset SHA ≠ config pin |
| `HIGGSTOOLS_BACKEND_UNAVAILABLE` | `recoverable` | unified Python module import failed |
| `HIGGSTOOLS_NUMERIC_CRASH` | `recoverable` | backend segfault on one scan row; row marked bad, scan continues |

No `reference_only` exits. No `--native` path (dropped per manager decision).

---

## Scan parallelism

`run --scan-dir <dir>` fans out per-point evaluations under
`multiprocessing.Pool(workers)`. Output `higgstools_index.csv` is sorted by
SPheno `index` column — byte-identical across worker counts.

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`

- Install skill: `plugins/hep-ph-toolkit/skills/higgstools-install/`
- Implementation plan: `docs/roadmap/v1-constraints-work/higgstools/plan/final.md`
