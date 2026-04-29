# DDCalc — Install Reference

Reference doc for installing **DDCalc 2.2.0** (direct-detection
likelihood library). Driven by `detect.sh` and `install.sh` in this
directory; consumed by the `ddcalc` runner skill's preflight and by
`/install`. Handles existing installs, custom paths, Apple Silicon
build quirks, and offline cache mode.

## Version pin

`detect.sh` pins DDCalc to **2.2.0**. Override with
`HEPPH_DDCALC_VERSION=x.y.z`. When this pin bumps, `install.sh` must
remove or migrate the previous install tree
(e.g. `~/.local/share/hephaestus/tools/DDCalc-2.2.0`); the new version
is only written to `config.json` after the new install verifies, so
a half-finished upgrade does not leave the config pointing at a
stale tree.

---

## Disk footprint

- **Tarball:** n/a (git clone — no tarball)
- **Installed tree:** ~1.8 MB at `~/.local/share/hephaestus/tools/DDCalc` (lib build only)
- **Build-time peak (transient):** ~50 MB during compile
- **Measured 2026-04-25 on macOS arm64.** Source: run-20260425-dmc/installer_mc_report.md.

---

## Prerequisites

- `gfortran` in PATH (DDCalc is pure Fortran + C shim).
- At least 2 GB disk free under `$HOME` (4 GB recommended).

If DDCalc is already at `config.ddcalc_path` and `libDDCalc.a` is present,
the skill returns immediately without touching disk.

---

## Decision flow

```
install.sh detect
       │
       ├── config has ddcalc_path + libDDCalc.a exists
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates finds libDDCalc.a
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

install.sh use-path <dir>
       │
       ├── <dir>/lib/libDDCalc.a exists
       │       ├── smoke test passes → writes ddcalc_path, ddcalc_version,
       │       │   ddcalc_installed_at; {"status":"configured",...}        exit 0
       │       └── DDCALC_PATH_INVALID blocker (libDDCalc.a missing)      exit 16
       └── <dir> does not exist → DDCALC_PATH_INVALID blocker             exit 16

install.sh install [<dir>]
       │
       ├── gfortran absent → GFORTRAN_ABSENT blocker                      exit 10
       ├── check_disk 2 4
       ├── HEPPH_NO_NETWORK=1 + HEPPH_OFFLINE_CACHE_DIR not set
       │       └── DDCALC_DOWNLOAD_FAILED (cache miss)                    exit 12
       ├── probe mirror URL chain (primary → mirror → archive.org)
       │       └── all fail → DDCALC_UPSTREAM_UNREACHABLE                 exit 12
       ├── download tarball (or serve from offline cache)
       ├── verify SHA256 (b12d63f7...) — hard error, no TODO allowed
       ├── extract + apply version_banner.patch
       ├── check_macos_sdk → injects SDKROOT + LDFLAGS=-Wl,-ld_classic
       ├── make lib FFLAGS="-std=legacy -fallow-invalid-boz -O2"
       │          CFLAGS="-Wno-implicit-function-declaration"
       │   ├── success → install to <dir>/lib/libDDCalc.a
       │   └── failure → DDCALC_BUILD_FAILED (context.build_log_tail)    exit 1
       ├── smoke test → DDCALC_SMOKE_TEST_FAILED                          exit 15
       └── config_merge ddcalc_path ddcalc_version ddcalc_installed_at
               ddcalc_upstream_url ddcalc_upstream_commit ddcalc_experiment_set
```

---

## Subcommands

| Subcommand | Description |
|---|---|
| `detect` | Probe config + scan candidates; no side-effects. |
| `use-path <dir>` | Register an existing DDCalc directory. |
| `install [<dir>]` | Full download + build + install. Default dir: `$STATE_ROOT/tools/DDCalc`. |

---

## Blockers table

| Code | Mode | Cause | Resolution |
|---|---|---|---|
| `DDCALC_DOWNLOAD_FAILED` | fatal | Network error or all mirrors exhausted | Check network; use `HEPPH_OFFLINE_CACHE_DIR` |
| `DDCALC_BUILD_FAILED` | fatal | `make lib` exited non-zero | See `context.build_log_tail`; check gfortran version |
| `DDCALC_SMOKE_TEST_FAILED` | fatal | `libDDCalc.a` missing or empty after build | Re-run install with `--force` |
| `DDCALC_PATH_INVALID` | fatal | `libDDCalc.a` not found at given path | Provide a valid DDCalc build directory |
| `DDCALC_OVERLAY_APPLY_FAILED` | fatal | `git apply --3way` rejected a patch | See `context.patch_reject_files`; v1.1 overlay required |
| `DDCALC_UPSTREAM_UNREACHABLE` | fatal | All mirror URLs returned non-200 | Set `HEPPH_OFFLINE_CACHE_DIR` or check network |
| `DDCALC_MACOS_SDK_MISMATCH` | fatal | `check_macos_sdk` detected SDK incompatibility | Run `xcode-select --install`; update Xcode CommandLineTools |
| `GFORTRAN_ABSENT` | fatal | `gfortran` not found in PATH | `brew install gcc` (macOS) or `apt install gfortran` (Linux) |
| `DDCALC_UPSTREAM_UNVERIFIED` | fatal | Planning-phase only — URL/SHA unresolved | Fetch date + real SHA256 must be committed to `skill_env.yaml` before merge |

---

## Config keys (written to `$XDG_CONFIG_HOME/hephaestus/config.json`)

| Key | Type | Description |
|---|---|---|
| `ddcalc_path` | path | Absolute path to DDCalc install root (contains `lib/libDDCalc.a`) |
| `ddcalc_version` | string | Detected version (e.g. `"2.2.0"`) |
| `ddcalc_installed_at` | ISO 8601 | Timestamp of last successful install or `use-path` |
| `ddcalc_experiment_set` | string | `"native"` (v1) or overlay name (v1.1+) |
| `ddcalc_experiment_overlay_sha` | string | SHA256 of overlay manifest (null for native) |
| `ddcalc_upstream_url` | URL | Mirror URL used for install |
| `ddcalc_upstream_commit` | SHA | Upstream git commit (`9364c02...` for v2.2.0) |

---

## `HEPPH_NO_NETWORK` behaviour

When `HEPPH_NO_NETWORK=1`:
- All `curl` calls are skipped.
- `HEPPH_OFFLINE_CACHE_DIR` must be set and contain a file named by
  the destination basename (e.g. `v2.2.0.tar.gz`).
- On cache miss: `DDCALC_OFFLINE_CACHE_MISS` blocker; exit 12.
- Use `use-path <dir>` if a pre-built DDCalc directory is available.

---

## Overlay support (v1 status: DEFERRED to v1.1)

`install --with-overlay <name>` applies a patch bundle from
`plugins/hep-ph-toolkit/skillsinstall.sh/overlays/<name>/`.

In **native-only v1**, overlays are deferred. The manifest file is a stub
with `deferred: v1.1`. Overlay work is blocked by the central-dispatcher
registration pattern in DDCalc 2.2.0 (`DDExperiments.f90` + `include/DDExperiments.hpp`
+ `Makefile` all require edits per experiment — `git apply --3way` is fragile).

See `apply_overlay.sh` for `DDCALC_OVERLAY_NOT_SUPPORTED_V1` gate.

---

## Sharp edges

Playtest-surfaced gotchas from the Dark SU(3) run (2026-04-25).

### SE-DD-2 — `DATA_DIR` baked into `libDDCalc.a` at build time (FU-wsi-01)

**Symptom:** After a successful build and install, runtime data loading for
newer experiments (LZ, DARWIN) silently fails. `energies.dat` or `efficiencies.dat`
cannot be opened; logL values are zero or NaN.

**Root cause:** DDCalc 2.2.0's `DDInput.f90` hardcodes the build-temp absolute path
(e.g. `/private/var/folders/.../tmp.XXXX/src/data/`) into the compiled `libDDCalc.a`
at build time. Once the temp build directory is garbage-collected, data files for
experiments that rely on the runtime path (LZ, DARWIN) are unreachable.

**Fix (T1.4):** The driver's `_ensure_ddcalc_data_symlinks()` function parses the
string table of `libDDCalc.a` (via `strings`) to recover the compile-time path and
recreates symlinks at that path pointing to the installed data directory. **Fixed in
tier-1** (T1.4, landed on main at `5355461`).

**Long-term fix:** rebuild DDCalc with a stable install prefix:
`make lib DATA_DIR=$(prefix)/share/DDCalc/data`. This requires patching
`DDInput.f90` before compilation.

### SE-DD-3 — Apple Silicon requires `-L/opt/homebrew/lib/gcc/current` for `-lgfortran` (FU-wsi-02)

**Symptom:** Linking `ddcalc_driver.c` against `libDDCalc.a` on Apple Silicon
(arm64 macOS) fails with `ld: library 'gfortran' not found`.

**Root cause:** Homebrew installs GCC (and `libgfortran`) under
`/opt/homebrew/lib/gcc/current/` rather than a standard linker search path.
The system linker does not find `libgfortran` without an explicit `-L` flag.

**Fix:** Pass `-L/opt/homebrew/lib/gcc/current` when linking the C driver:
```bash
gcc ddcalc_driver.c -L"$DDCALC_PATH/lib" -lDDCalc \
    -L/opt/homebrew/lib/gcc/current -lgfortran -o ddcalc_driver
```
The `build_driver.sh` helper injects this flag automatically on `arm64`
macOS. **Fixed in tier-1** (T1.4, landed on main at `5355461`).

---

## Linkage

- Schema: `plugins/shared/schemas/scattering.schema.json` (consumed by `/ddcalc`)
- Shared helpers: `plugins/shared/install-helpers/_common.sh`
- macOS SDK helper: `plugins/shared/install-helpers/check_macos_sdk.sh`
- Downstream: `/ddcalc` reads `config.ddcalc_path`
