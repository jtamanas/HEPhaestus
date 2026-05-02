# CLASS — Install Reference

Reference doc for installing **CLASS v3.3.4** (upstream
`lesgourg/class_public`). Driven by `detect.sh` and `install.sh` in this
directory; consumed by the `/class` runner skill's preflight and by `/install`.
Handles existing installs, custom paths, and the `c.age()` smoke test.

**Out of scope:** MontePython, Cobaya, class_sz, classnet, GW_CLASS, ExoCLASS
fork, class_matter. Only upstream `lesgourg/class_public` v3.3.4 is supported.
Exotic energy-injection (absorbed into upstream v3.x from the ExoCLASS fork)
*is* in scope.

## Version pin

`detect.sh` pins CLASS to **3.3.4**. Override with
`HEPPH_CLASS_VERSION=x.y.z`. When a pin bumps, `install.sh` must remove or
migrate the previous build tree; the new version is only written to
`config.json` after the new install verifies, so a half-finished upgrade does
not leave the config pointing at a stale binary.

Pin staleness: CLASS has shipped ~5 tags per year. Plan for a 12-month review
cadence. The `test_version_pin_consistency.py` test suite flags drift.

## Disk footprint

- **Source + build tree:** ~500 MB estimated (CLASS is C, no Fortran; includes
  classy wheel build artifacts)
- **Build-time peak (transient):** ~1 GB
- **Estimated.** Source: `skill_env.yaml` `disk_min_gb: 1`.

Typical invocation order:

1. `install.sh detect` — check current state (no side-effects).
2. `install.sh use-path <class_src_dir>` — register an existing CLASS build.
3. `install.sh install` — full auto-install.
4. `install.sh install --force` — re-install even if already configured.

---

## Decision flow

```
install.sh detect
       │
       ├── config has class_path + class binary present
       │       └── {"status":"configured","class_version":"..."}  exit 0
       │
       └── nothing found
               └── {"status":"missing"}                           exit 0

install.sh use-path <class_src_dir>
       │
       ├── dir has class binary
       │       └── writes config keys                             exit 0
       │
       └── dir missing class binary → CLASS_PATH_INVALID blocker  exit 16

install.sh install [--force]
       │
       ├── HEPPH_NO_NETWORK=1 → CLASS_OFFLINE_NO_CACHE fatal      exit 12
       ├── check_disk 1
       ├── toolchain check (cc, make, python3, Cython)
       │       → CLASS_TOOLCHAIN_MISSING fatal                    exit 1
       ├── macOS: brew list libomp (non-fatal; sets class_openmp_enabled)
       ├── git clone --depth 1 --branch v3.3.4 class_public
       ├── git rev-parse HEAD verified against skill_env.yaml class_commit
       ├── make -j
       │       → CLASS_BUILD_FAILED fatal                         exit 30
       ├── <python> -m pip install <class_src>/python
       │       → CLASSY_PIP_INSTALL_FAILED recoverable; retry --user
       ├── python -c "import classy"
       │       → CLASSY_IMPORT_FAILED fatal                       exit 1
       ├── smoke_test.sh → c.age() within 0.5% of 13.797 Gyr
       │       → CLASS_SMOKE_FAILED fatal                         exit 15
       └── config_merge writes all 6 config keys
```

---

## JSON status contract

`detect` emits JSON on **stdout**. Blockers go to **stderr**.

| `status` value | Meaning |
|---|---|
| `configured` | class_path set, class binary present |
| `missing`    | No CLASS found in config |

Fields for `configured`:
```json
{
  "status": "configured",
  "class_path": "/path/to/class_public/class-3.3.4",
  "class_version": "3.3.4",
  "classy_version": "3.3.4",
  "class_openmp_enabled": "1"
}
```

---

## Smoke test reference

At install time, `smoke_test.sh` runs CLASS via classy and asserts `c.age()`
within 0.5% of the reference value:

- **Reference:** `13.797` Gyr (Planck 2018 Table 2; reproduced on Ubuntu 22.04
  LTS with system gcc + CLASS v3.3.4 at default precision).
- **Tolerance:** 0.5% (tight but compiler-stable; `c.age()` is a background
  quantity, byte-stable to <0.01% across compilers).
- **Timeout:** 60 seconds.

The runner-skill golden test (`skills/class/tests/test_smoke.py`, gated on
`HEPPH_RUN_NETWORK_TESTS=1`) asserts `cl_lensed[2,'tt']` within 5% of a JSON
fixture generated on Ubuntu 22.04 LTS with system gcc/libomp. The looser
tolerance there accommodates compiler-induced drift in the CMB power spectrum.

---

## macOS notes

**libomp:** On macOS, OpenMP requires libomp via Homebrew. The installer checks
`brew list libomp`; if absent, CLASS builds without OpenMP (single-threaded) and
`class_openmp_enabled=0` is written to config. This is non-fatal — CLASS is
fully functional single-threaded but substantially slower for high-`l_max` runs.

Install libomp: `brew install libomp`. Then re-run `install.sh install --force`.

**Clang vs gcc:** CLASS v3.3.4 builds with Apple Clang on macOS arm64 without
patches. The CI fixture (Ubuntu 22.04 LTS, system gcc) differs in
floating-point rounding at the `1e-5` level; the smoke tolerance (0.5%) is set
to survive this drift.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | `user_instruction` |
|---|---|---|---|
| `CLASS_TOOLCHAIN_MISSING` | `fatal` | cc/make/python3/Cython absent | Install build tools (see above) |
| `CLASS_OFFLINE_NO_CACHE` | `fatal` | `HEPPH_NO_NETWORK=1` | Disable network restriction or provide cache |
| `CLASS_DOWNLOAD_FAILED` | `fatal` | git clone failed | Check network and GitHub availability |
| `CLASS_BUILD_FAILED` | `fatal` | make non-zero | Check build.log in class_src dir |
| `CLASSY_PIP_INSTALL_FAILED` | `recoverable` | pip install failed | Retry with `pip install --user` |
| `CLASSY_IMPORT_FAILED` | `fatal` | `import classy` fails | Check PYTHONPATH and pip install |
| `CLASS_SMOKE_FAILED` | `fatal` | c.age() out of 0.5% range | Reinstall with `--force`; check gcc/clang version |
| `CLASS_PATH_INVALID` | `fatal` | use-path target missing class binary | Provide valid CLASS build directory |

---

## Config keys written

| Key | Value |
|---|---|
| `class_path` | Absolute path to CLASS source/build directory |
| `class_version` | `3.3.4` |
| `class_commit` | 40-hex SHA of the cloned HEAD |
| `classy_version` | Version string from `classy.__version__` |
| `class_openmp_enabled` | `1` (Linux) or `0`/`1` (macOS, depends on libomp) |
| `class_installed_at` | ISO 8601 UTC timestamp |

---

## Version pin and override

Pinned version (from `skill_env.yaml`):
- **CLASS:** `3.3.4` (tag `v3.3.4`, commit pinned in skill_env.yaml)

Override via environment:
```bash
HEPPH_CLASS_VERSION=3.3.3 bash install.sh install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Pin lint: `plugins/hep-ph-toolkit/_shared/installs/tests/test_version_pin_consistency.py`
