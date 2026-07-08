# micrOMEGAs — Install Reference

Reference doc for installing **micrOMEGAs 6.0.5** (with bundled CalcHEP)
for dark matter calculations. Driven by `detect.sh` and `install.sh` in
this directory; consumed by the `micromegas` runner skill's preflight
and by `/install`. Serves both as the primary relic/SI/SD driver for
`/micromegas` and as the MadDM validator for `/maddm` cross-checks.

## Version pin

`detect.sh` pins micrOMEGAs to **6.0.5**. Override with
`HEPPH_MICROMEGAS_VERSION=x.y.z`. When this pin bumps, `install.sh`
must remove or migrate the previous install tree
(e.g. `~/micrOMEGAs/micromegas_6.0.5` →
`~/micrOMEGAs/micromegas_<new>`); the new version is only written to
`config.json` after the new install verifies, so a half-finished
upgrade does not leave the config pointing at a stale tree.

## Disk footprint

- **Tarball:** ~33 MB (`micromegas_6.0.5.tgz` from LAPTh; Zenodo mirror: ~32.5 MB / 32588296 B for 6.1.15)
- **Installed tree:** ~300–400 MB for a full build (x86_64 measured; the arm64 full build succeeds on 6.1.15, size expected comparable but not separately measured; see arm64 note below)
- **Build-time peak (transient):** ~3 GB warned / ~5 GB max (includes CalcHEP compile)
- **Sources:** `skill_env.yaml` `disk_min_gb: 3` / `disk_warn_gb: 5`.

> **arm64 builds natively — no Rosetta.** The "build fails at CalcHEP `getFlags`
> on arm64 / arm64 known broken" warning came from an early 6.0.5 partial
> (run-20260425-dmc) and **did NOT reproduce on 6.1.15**: `make` returned 0,
> `s_calchep` and all CalcHEP libs built, and the bundled `SingletDM` example ran
> end-to-end (`darkOmega`/`nucleonAmplitudes`) — clang + Homebrew gfortran, native
> arm64, with `SDKROOT=$(xcrun --show-sdk-path)`. The only patch still required is
> the CalcHEP `make -j` archive race (see `## macOS build notes` /
> `.NOTPARALLEL` on the `CalcHEP_src/c_source/*` Makefiles). Do not add a
> Rosetta/x86-only requirement.

> **LAPTh 6.0.5 URL 404s.** The pinned LAPTh archive URL for 6.0.5 currently
> returns 404 (stale upstream). In network mode the installer already falls back
> to the Zenodo mirror pinned at **6.1.15** (see `install` below); that is the
> working source today. Zenodo throttles/aborts the 32.5 MB tarball mid-transfer —
> download with a `curl -L -C -` resume loop until the size reaches 32588296 B.

---

## Roles

This skill serves **two complementary roles** in the hephaestus workflow. A single
micrOMEGAs installation is shared by both paths:

1. **Lead role — relic/SI/SD driver for `/micromegas`.** Provides the
   `config.micromegas_path` used by the `/micromegas` skill to compute Ωh², σ_SI, σ_SD,
   ⟨σv⟩, and indirect-detection spectra. This is the v1 audited contract; failure modes
   and offline/low-disk behavior are covered below.

2. **MadDM-validator role for `/maddm`.** Per the project's DM-tool policy (MadDM
   primary; micrOMEGAs validator; DRAKE for narrow resonances), `/maddm` is the default
   driver for novel BSM models (its MG5/UFO pipeline handles exotic Lorentz/color
   structures correctly). micrOMEGAs, with its mature coannihilation bookkeeping and
   pre-wired experimental likelihoods, is the cross-check. Both paths resolve to the
   same `config.micromegas_path`; downstream orchestration (e.g.,
   `/dark-matter-constraints`) can invoke this skill once and use the same install for
   either role.

**Augments, not replaces.** This skill drives real `make` builds of upstream
micrOMEGAs — it does not reimplement relic-density, direct-detection, or
annihilation calculations in Python.

---

## Decision flow

```
install.sh
       │
       ├─ detect
       │       └─ Probe config + well-known paths → JSON state
       │
       ├─ use-path <dir> [--calchep-path <dir>]
       │       ├─ Validate sources/ + CalcHEP_src/ (or --calchep-path)
       │       ├─ Run smoke test (_smoke.sh)
       │       └─ Write config keys
       │
       ├─ install [parent_dir] [--full-smoke]
       │       ├─ check_disk 3 5
       │       ├─ Download / offline cache (+ Zenodo fallback in network mode)
       │       ├─ verify_checksum (TODO → warn)
       │       ├─ Extract to parent_dir/micromegas_6.0.5/
       │       ├─ macOS env setup (_macos_env.sh)
       │       ├─ check_toolchain (cc / gfortran / gmake; X11 warn-only)
       │       ├─ make -j<nproc> under netguard PATH sandbox
       │       ├─ Build-failure signature sniff → LAPACK_ABSENT if matched
       │       ├─ Light smoke test (always)
       │       ├─ Full MSSM smoke (only with --full-smoke)
       │       ├─ PPPC tables check
       │       └─ config_merge (5 keys)
       │
       └─ validate
               ├─ Read config.micromegas_path
               ├─ Re-check markers + run light smoke
               └─ Read-only: does not write config
```

---

## Subcommands

### `detect`

```
install.sh detect
```

Probes for an existing micrOMEGAs installation. No side-effects.

Emits JSON to stdout:

| Status | Meaning |
|--------|---------|
| `configured` | `config.micromegas_path` set and directory validates. |
| `found` | Valid installation found at a well-known path but not in config. |
| `missing` | No valid installation found. |

Example output:
```json
{"status": "configured", "path": "/home/user/micrOMEGAs/micromegas_6.0.5", "version": "6.0.5"}
```

Exit 0 in all three states.

---

### `use-path`

```
install.sh use-path <dir>
install.sh use-path <dir> --calchep-path <calchep_src_dir>
```

Validates and registers an existing micrOMEGAs tree.

**Validation performed:**
1. `<dir>/sources/` exists.
2. `<dir>/CalcHEP_src/` exists (or `--calchep-path` provided).
3. If `--calchep-path <calchep_src_dir>`: validates `getFlags` + `bin/s_calchep` in the CalcHEP tree.
4. Runs smoke test (MSSM/main.c).

On success, writes config keys and prints `{"status":"configured",...}`.

---

### `install`

```
install.sh install [parent_dir] [--full-smoke]
```

Downloads micrOMEGAs 6.0.5 from the LAPTh archive and builds it.
`parent_dir` defaults to `$HOME/micrOMEGAs`. The installation lands at
`<parent_dir>/micromegas_6.0.5/`.

**`--full-smoke` flag:** After the mandatory light smoke (markers + compile stub), also
compile and run the canonical MSSM reference example
(`cd <install>/MSSM && make main=main.c && ./main input`). Adds ~5 min on first run;
off by default. Use when you need end-to-end confidence the install can produce a
finite Ωh². Failures emit `MICROMEGAS_SMOKE_TEST_FAILED` with the MSSM log tail in
`context.mssm_smoke_log_tail`.

**Offline mode:** Set `HEPPH_NO_NETWORK=1` and `HEPPH_OFFLINE_CACHE_DIR=<dir>` with
`micromegas_6.0.5.tgz` pre-staged in that directory. The install runs without any
network access.

**Network-mode Zenodo fallback:** When `HEPPH_NO_NETWORK` is unset and the LAPTh URL
fails after retries, the installer falls back to the Zenodo mirror pinned at
`6.1.15`. A warning is logged; the installed version reflects the fallback (e.g.
`micromegas_6.1.15/`) and `config.micromegas_version` is updated accordingly. The
offline cache path does NOT attempt Zenodo — it strictly requires the cached tarball.

**Low-disk environments:** The install stage runs `check_disk 3 5` (requires 3 GB free,
warns at 5 GB) before downloading. On constrained machines (e.g., CI runners with 2 GB
free) or when testing network-policy blockers in isolation, set `HEPPH_SKIP_DISK_CHECK=1`
to bypass the disk check:
```
HEPPH_SKIP_DISK_CHECK=1 HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/pkg \
  install.sh install
```
Note: the disk check runs before the network-policy check in `install_impl.sh`. If you
want to verify the network-policy blocker (`MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`) on a
low-disk machine, set both `HEPPH_SKIP_DISK_CHECK=1` and `HEPPH_NO_NETWORK=1`.

**Toolchain precondition:** Before `make`, the installer verifies `gcc`/`clang`,
`gfortran`, and GNU `make`/`gmake` are on PATH. Missing tools emit per-OS install hints
(`CC_ABSENT`, `GFORTRAN_ABSENT`, `GNU_MAKE_ABSENT`). X11 dev headers are warn-only —
batch-mode DM observables do not need X11; only the CalcHEP GUI (`s_calchep`) does.
Set `HEPPH_SKIP_TOOLCHAIN_CHECK=1` to bypass (useful for network-policy tests).

---

### `validate`

```
install.sh validate
```

Re-validates the currently configured install: reads `config.micromegas_path`, checks
that the path still exists with the expected structural markers, and runs the light
smoke test. **Read-only** — never writes to config on success.

Emits `MICROMEGAS_PATH_INVALID` if the path is missing from config, gone from disk, or
lacks `sources/`/`CalcHEP_src/`. Emits `MICROMEGAS_SMOKE_TEST_FAILED` if the smoke
check fails. On success prints `{"status":"configured","path":"...","version":"..."}`.

Useful for CI / post-install verification and for `/dark-matter-constraints` to
precheck the validator path before a MadDM cross-check run.

---

## JSON status contract

```json
{
  "status": "configured | found | missing | installed",
  "path": "/path/to/micromegas_6.0.5",
  "version": "6.0.5"
}
```

Blockers are emitted as single-line JSON to **stderr** conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

---

## CalcHEP handling

micrOMEGAs 6.0.5 ships with a vendored CalcHEP source tree in `CalcHEP_src/`. The default
`make` target builds it automatically. For users with an existing CalcHEP 3.9 installation,
`use-path --calchep-path <CalcHEP_src_dir>` registers the external copy and skips the
bundled build.

The `calchep_bundled` config key is `"true"` when using the bundled copy, `"false"` otherwise.

---

## `HEPPH_NO_NETWORK` handling

When `HEPPH_NO_NETWORK=1`:
- The download stage skips `curl` and reads `micromegas_6.0.5.tgz` from `$HEPPH_OFFLINE_CACHE_DIR`.
- If the tarball is not in cache → fatal `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`.
- The Zenodo fallback is **not** attempted in offline mode (the policy forbids network).
- The build stage wraps `make` with a PATH-override sandbox (`_netguard.sh`) that stubs
  `curl`, `wget`, and `git`. Any network attempt during build → fatal
  `MICROMEGAS_BUILD_NEEDS_NETWORK` with `context.attempted_url`.

---

## macOS build notes

On macOS 14+:
1. `SDKROOT` is set to `$(xcrun --show-sdk-path)` before `make`.
2. When Homebrew gfortran is detected: `FFLAGS=-ff2c`, `LDFLAGS=-Wl,-ld_classic`.
3. `DYLD_LIBRARY_PATH` is set for the smoke test scope only, never written to the user shell.
4. SDK missing/stale → fatal `MICROMEGAS_MACOS_SDK_MISMATCH` with `context.sdkroot`.

**Vendored upstream patches:** Stage 4.5 of `install_impl.sh` applies
patches from `_patches.sh` between extraction and build. See
`references/micromegas-workarounds.md` for the rationale behind each
patch. Currently one patch is applied (CalcHEP `make -j` archive race);
without it, `make -j$NCPUS` silently loses `.o` files from `serv.a` and
the build fails at the `bin/plot_view` link with `Undefined symbols`.

---

## Failure modes → blockers

| Code | Mode | Trigger | User action |
|------|------|---------|-------------|
| `MICROMEGAS_PATH_INVALID` | fatal | `use-path <dir>` or `validate` — missing `sources/`/`CalcHEP_src/` | Run install or fix path |
| `CALCHEP_PATH_INVALID` | fatal | `--calchep-path` missing `getFlags` or `s_calchep` | Fix CalcHEP path |
| `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY` | fatal | `HEPPH_NO_NETWORK=1` + no cache | Pre-stage tarball |
| `MICROMEGAS_DOWNLOAD_FAILED` | fatal | LAPTh + Zenodo both failed | Check network, use use-path |
| `MICROMEGAS_BUILD_FAILED` | fatal | `make` exited non-zero (generic) | Check `context.make_log_tail` |
| `LAPACK_ABSENT` | fatal | `make` failed with a LAPACK-family signature | Install LAPACK dev headers |
| `MICROMEGAS_BUILD_NEEDS_NETWORK` | fatal | `make` attempted curl/wget/git | Pre-stage packages or disable policy |
| `MICROMEGAS_MACOS_SDK_MISMATCH` | fatal | `xcrun --show-sdk-path` failed | `xcode-select --install` |
| `MICROMEGAS_SMOKE_TEST_FAILED` | fatal | Light smoke or `--full-smoke` MSSM run failed | Recompile micrOMEGAs |
| `PPPC_TABLES_MISSING` | fatal | `Data/AtProduction_gammas.dat` absent | Verify tarball integrity |
| `CC_ABSENT` | fatal | No `gcc`/`clang` on PATH before `make` | Install a C compiler (per-OS hint) |
| `GFORTRAN_ABSENT` | fatal | `gfortran` not in PATH | Install gfortran (per-OS hint) |
| `GNU_MAKE_ABSENT` | fatal | No `gmake` nor GNU `make` on PATH | Install GNU make (per-OS hint) |

---

## Config keys written

After a successful `install` or `use-path`:

| Key | Value |
|-----|-------|
| `micromegas_path` | Absolute path to the micrOMEGAs installation |
| `micromegas_version` | Version string (e.g. `"6.0.5"`) |
| `calchep_path` | Path to CalcHEP_src (`$micromegas_path/CalcHEP_src` or user-supplied) |
| `calchep_bundled` | `"true"` if using bundled CalcHEP, `"false"` if external |
| `micromegas_installed_at` | UTC ISO 8601 timestamp |

The `validate` subcommand is read-only and does not touch these keys.

---

## Version pin + override

Default version: `6.0.5`. Override via environment:
```
HEPPH_MICROMEGAS_VERSION=6.0.5 install.sh install
```

Zenodo mirror fallback pin: `6.1.15` (fixed; only exercised when LAPTh is
unreachable and network mode is allowed). If the mirror is used the installed
version is recorded as `6.1.15` rather than the requested pin.

Re-pinning the default to 6.1.x is a v1.1 ticket gated on W3 emitting UFO 2.0 output.

---

## Linkage

- **Consumed by:**
  - `/micromegas` (primary driver — reads `config.micromegas_path` for relic/SI/SD/annihilation).
  - `/maddm` / `/dark-matter-constraints` (validator role — same `config.micromegas_path`
    re-used for MadDM cross-checks).
- **Depends on:** `gfortran`, `cc`/`gcc`, GNU `make`/`gmake` in PATH; Phase-0
  `_common.sh`, `check_macos_sdk.sh` helpers.
- **Scripts:**
  - `install.sh` — dispatcher (detect / use-path / install / validate).
  - `detect.sh`, `use_path.sh`, `install_impl.sh`, `validate.sh` — subcommand handlers.
  - `check_toolchain.sh` — cc/gfortran/gmake precondition with per-OS install hints.
  - `_blocker.sh`, `_smoke.sh`, `_netguard.sh`, `_macos_env.sh` — shared helpers.
