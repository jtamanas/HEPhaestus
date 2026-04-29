# HiggsTools — Install Reference

Reference doc for installing **HiggsBounds-5.10.2 + HiggsSignals-2.6.2**
(legacy Fortran, default) or the **unified HiggsTools 1.2 C++ library**
(opt-in). Driven by `detect.sh` and `install.sh` in this directory;
consumed by the `higgstools` runner skill's preflight and by
`/install`. Handles existing installs, custom paths, and SM
reference-chi2 caching.

## Version pin

`detect.sh` pins HiggsBounds to **5.10.2** (and HiggsSignals to
**2.6.2**). Override with `HEPPH_HB_VERSION=x.y.z` /
`HEPPH_HS_VERSION=x.y.z`. When a pin bumps, `install.sh` must remove
or migrate the previous build trees; the new version is only written
to `config.json` after the new install verifies, so a half-finished
upgrade does not leave the config pointing at a stale binary.

## Disk footprint

- **Tarball:** n/a (git clone — HB + HS each cloned from GitLab)
- **Installed tree:** ~500 MB estimated (HB-5.10.2 + HS-2.6.2 builds + datasets)
- **Build-time peak (transient):** ~1–2 GB during CMake build
- **Estimated.** Source: `skill_env.yaml` `disk_min_gb: 1` / `disk_warn_gb: 2`; unified backend raises peak to ~2 GB.

Typical invocation order:

1. `install.sh detect` — check current state (no side-effects).
2. `install.sh use-path <hb_dir> <hs_dir>` — register existing builds.
3. `install.sh install` — full auto-install (legacy Fortran, default).
4. `install.sh install --backend=unified` — opt-in C++ build (requires `HEPPH_HIGGSTOOLS_BACKEND=unified`).

---

## Decision flow

```
install.sh detect
       │
       ├── config has higgsbounds_path + higgssignals_path + binaries present
       │       └── {"status":"configured","hb_version":"...","hs_version":"..."}  exit 0
       │
       ├── config missing / invalid BUT HB/HS binaries found on disk
       │       └── {"status":"found","hb_path":"...","hs_path":"..."}             exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                           exit 0

install.sh use-path <hb_dir> <hs_dir>
       │
       ├── both dirs have HB/HS executables/libraries
       │       └── writes config keys; caches chi2_SM_ref               exit 0
       │
       ├── dir missing executables → HIGGSTOOLS_PATH_INVALID blocker    exit 16
       └── chi2_SM_ref cache fails → HIGGSTOOLS_SMOKE_TEST_FAILED       exit 15

install.sh install [--backend=legacy|unified]
       │
       ├── HEPPH_NO_NETWORK=1 → HIGGSTOOLS_OFFLINE_NO_CACHE fatal       exit 12
       ├── check_disk 3
       ├── gfortran check (legacy path) → HIGGSTOOLS_TOOLCHAIN_MISSING  exit 10
       ├── git clone --depth 1 --branch 5.10.2 HiggsBouns
       ├── git rev-parse HEAD verified against skill_env.yaml hb_commit
       ├── cmake build HB-5
       ├── git clone --depth 1 --branch 2.6.2 HiggsSignals
       ├── git rev-parse HEAD verified against skill_env.yaml hs_commit
       ├── cmake build HS-2 (with -DHiggsBounds_DIR=<hb-build>)
       ├── smoke_test.sh (asserts HBresult=1; HS chi² finite < 200)
       ├── cache_sm_reference.py → $STATE_ROOT/cache/hs2_chi2_sm_ref.json
       └── config_merge writes all keys; marks last_configured
```

### Unified backend opt-in (--backend=unified)

Requires both `HEPPH_HIGGSTOOLS_BACKEND=unified` AND `--backend=unified`.
**Apple Silicon / macOS arm64 caveat:** the unified C++ build is unverified on
macOS-14 arm64 due to known Eigen/Boost ABI issues. CI targets ubuntu-22.04.
On any build failure on macOS arm64, the skill emits a `recoverable` blocker
and continues — the legacy install remains authoritative.

Additional toolchain requirements: cmake ≥ 3.16, g++ ≥ 11, Eigen3, GSL,
pybind11, Boost ≥ 1.74.

---

## JSON status contract

`detect` emits JSON on **stdout**. Blockers go to **stderr**.

| `status` value | Meaning |
|---|---|
| `configured` | higgsbounds_path + higgssignals_path set, binaries present, chi2_SM_ref cached |
| `found` | HB/HS found on disk via scan but not in config |
| `missing` | No HB/HS found anywhere |

Fields for `configured`:
```json
{
  "status": "configured",
  "hb_path": "/path/to/HiggsBounds-5.10.2/build",
  "hb_version": "5.10.2",
  "hs_path": "/path/to/HiggsSignals-2.6.2/build",
  "hs_version": "2.6.2",
  "backend": "legacy"
}
```

---

## SM reference chi² cache

At install time, `smoke_test.sh` runs HS on the bundled SM SLHA fixture and
caches `chi2_SM_ref` to `$STATE_ROOT/cache/hs2_chi2_sm_ref.json`:

```json
{"chi2_sm_ref": 85.23, "ndf": 80, "hb_version": "5.10.2", "hs_version": "2.6.2"}
```

The `/higgstools run` command reads this cache on every invocation. If the cache
is absent, it emits a fatal `HIGGSTOOLS_SM_REF_MISSING` blocker with the
instruction to re-run `install.sh install`.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | `user_instruction` |
|---|---|---|---|
| `HIGGSTOOLS_TOOLCHAIN_MISSING` | `fatal` | `gfortran` absent (legacy) or cmake/pybind11 absent (unified) | Install gfortran (e.g. `brew install gcc` or `apt install gfortran`) |
| `HIGGSTOOLS_OFFLINE_NO_CACHE` | `fatal` | `HEPPH_NO_NETWORK=1` and no cached source | Provide a cached source directory via `HEPPH_OFFLINE_CACHE_DIR` |
| `HIGGSTOOLS_DOWNLOAD_FAILED` | `fatal` | git clone failed | Check network and GitLab accessibility |
| `HIGGSTOOLS_BUILD_FAILED` | `fatal` | CMake/make non-zero | Check build.log in the build directory |
| `HIGGSTOOLS_SMOKE_TEST_FAILED` | `fatal` | SM example output out of range | Reinstall with `install.sh install --force` |
| `HIGGSTOOLS_PATH_INVALID` | `fatal` | `use-path` target missing HB/HS binaries | Provide path to a valid HiggsBounds/HiggsSignals build |
| `HIGGSTOOLS_BACKEND_UNAVAILABLE` | `recoverable` | Unified backend import fails | Install higgstools Python module or use legacy backend |

---

## Config keys written

| Key | Value |
|---|---|
| `higgstools_backend` | `legacy` (default) or `unified` |
| `higgsbounds_path` | Absolute path to HB build directory |
| `higgsbounds_version` | `5.10.2` |
| `higgssignals_path` | Absolute path to HS build directory |
| `higgssignals_version` | `2.6.2` |
| `higgstools_path` | (unified only) Absolute path to HiggsTools install |
| `higgstools_version` | (unified only) Pinned HiggsTools C++ release |
| `hbdataset_path` | (unified only) Absolute path to hbdataset clone |
| `hbdataset_commit` | (unified only) Full SHA of hbdataset clone |
| `hsdataset_path` | (unified only) Absolute path to hsdataset clone |
| `hsdataset_commit` | (unified only) Full SHA of hsdataset clone |
| `higgstools_installed_at` | ISO 8601 UTC timestamp |

---

## Version pin and override

Pinned versions (from `skill_env.yaml`):
- **HiggsBounds:** `5.10.2` (commit `3d9c992b14ca983f9551eb0153463882160751f7`)
- **HiggsSignals:** `2.6.2` (commit `2253ca7ebf881bffd634ddcef88705e71750dd4b`)
- **HiggsTools (unified):** `v1.2` (commit `7ab57ca559f2ec6adbeaedba2625f34c1a998b5f`)
- **hbdataset (unified):** `v1.7` (commit `3539f9adf3724f8752701208bf059d1658824cd2`)
- **hsdataset (unified):** `v1.1` (commit `3c6c2538d9ba0549ea0559cf9b38c18eb80c3af1`)

Override via environment:
```bash
HEPPH_HB_VERSION=5.10.1 install.sh install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`

- Implementation plan: `docs/roadmap/v1-constraints-work/higgstools/plan/final.md`
