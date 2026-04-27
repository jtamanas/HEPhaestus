---
name: formcalc-install
description: Detect, validate, or auto-install FormCalc 9.10 (bundled with LoopTools 9.10) and FORM 4.3.1. Handles existing installs, custom paths, Apple-Silicon branch, and offline-cache mode.
---

## When to invoke

Use `/formcalc-install` before running `/formcalc` to ensure FormCalc, LoopTools, and
FORM are present and the Wolfram Engine is reachable.  The skill is idempotent: if all
three components are already configured it returns `{"status":"configured"}` immediately
without touching disk.

## Disk footprint

- **Tarball:** ~40 MB estimated (FormCalc-9.10.tar.gz + FORM-4.3.1.tar.gz combined)
- **Installed tree:** ~200 MB estimated (FormCalc + bundled LoopTools 9.10 + FORM binary)
- **Build-time peak (transient):** ~3–5 GB during LoopTools + FORM compile
- **Estimated.** Source: `skill_env.yaml` `disk_min_gb: 3` / `disk_warn_gb: 5`.

Typical invocation order:

1. `/formcalc-install detect` — check current state (no side-effects).
2. `/formcalc-install use-path <dir>` — register an existing FormCalc directory.
3. `/formcalc-install install` — full auto-install (requires Wolfram Engine + network).

---

## Decision flow

```
/formcalc-install detect
       │
       ├── config has formcalc_path + valid FormCalc.m + version probe succeeds
       │       └── {"status":"configured","path":"...","formcalc_version":"9.10",
       │               "form_binary":"...","looptools_lib":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds FormCalc
       │       └── {"status":"found","path":"..."}                   exit 0
       │
       └── nothing found
               └── {"status":"missing"}                             exit 0

/formcalc-install use-path <dir>
       │
       ├── <dir>/FormCalc.m exists AND wolframscript configured
       │       ├── version probe succeeds → writes config keys;
       │       │   {"status":"configured",...}                       exit 0
       │       └── version probe fails → FORMCALC_SMOKE_TEST_FAILED  exit 15
       │
       ├── <dir>/FormCalc.m missing → FORMCALC_PATH_INVALID          exit 16
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT        exit 20

/formcalc-install install [dir]
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT        exit 20
       ├── gfortran not found → FORMCALC_NO_GFORTRAN blocker         exit 10
       ├── disk check (need ≥3 GB free in $HOME)
       ├── HEPPH_NO_NETWORK=1 → offline cache path (see below)
       ├── download FormCalc-10.0.tar.gz (bundles LoopTools)
       ├── verify_checksum
       ├── extract to <install-root>/
       ├── register $Path via init.m ($UserBaseDirectory/Applications/FormCalc-10.0/)
       ├── build_looptools.sh (Apple-Silicon branch for libquadmath)
       ├── download + build_form.sh (FORM 4.3.1)
       ├── smoke_test.wls
       │   ├── succeeds → writes nine config keys; check_wolfram_activation.sh
       │   │   ├── status ok   → log "FormCalc ready."               exit 0
       │   │   └── status activation_required
       │   │           └── {"status":"activation_required",...}       exit 0
       │   └── fails → FORMCALC_SMOKE_TEST_FAILED                    exit 15
       └── download failed → FORMCALC_DOWNLOAD_FAILED                exit 12
```

---

## Install root

```
<install-root> = $XDG_DATA_HOME/hephaestus/formcalc-<ver>/
              or $HOME/.local/share/hephaestus/formcalc-<ver>/   (fallback)
```

The FormCalc Mathematica application is additionally registered to
`$UserBaseDirectory/Applications/FormCalc-<ver>/` for Wolfram auto-load.

FORM binary lives at `<install-root>/form/<arch>-<os>/form`.  No `$PATH` symlink
is created; no shell rc is modified.  `form_binary` in config is the sole contract.

---

## Offline-cache mode

Set `HEPPH_NO_NETWORK=1` and point `HEPPH_OFFLINE_CACHE_DIR` at a directory
containing the pre-staged tarballs.  Cache miss emits
`FORMCALC_OFFLINE_CACHE_MISS` (JSON on stderr) and exits `EXIT_DOWNLOAD=12`.

---

## Apple-Silicon branch

When `uname -m == arm64` (macOS):

1. `build_looptools.sh` globs `gfortran-*` under `$(brew --prefix gcc@{13,14,15})`
   and `$(brew --prefix gcc)`.
2. Probes each for `libquadmath.dylib` via `gfortran -print-file-name=libquadmath.dylib`.
3. If absent → passes `--without-quad` to LoopTools `./configure` and records
   `looptools_quad: false` in config. Does NOT abort.
4. Uses `check_macos_sdk.sh` for `sdkroot` and `-Wl,-ld_classic` detection.

---

## JSON status contract

| `status` value | Meaning |
|---|---|
| `configured` | All three components present; version probe succeeded |
| `found` | FormCalc found via scan but not in config |
| `missing` | No FormCalc found anywhere |
| `activation_required` | FormCalc installed but Wolfram Engine needs activation |

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Exit | Trigger | `user_instruction` |
|---|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | 20 | `wolfram_engine_path` not set | Run `/install` |
| `FORMCALC_NO_GFORTRAN` | `fatal` | 10 | `gfortran` not in PATH | `brew install gcc` or `sudo apt install gfortran` |
| `FORMCALC_DOWNLOAD_FAILED` | `fatal` | 12 | `curl` failed twice | Check network |
| `FORMCALC_SMOKE_TEST_FAILED` | `fatal` | 15 | Version probe empty after install | Check Wolfram Engine activation |
| `FORMCALC_PATH_INVALID` | `fatal` | 16 | `use-path <dir>` has no `FormCalc.m` | Provide path to FormCalc package dir |
| `FORMCALC_OFFLINE_CACHE_MISS` | `fatal` | 12 | `HEPPH_NO_NETWORK=1` + tarball absent | Pre-stage tarballs in `HEPPH_OFFLINE_CACHE_DIR` |
| `FORM_BUILD_FAILED` | `fatal` | 28 | FORM `./configure && make` failed | Check C compiler; check log |
| `LOOPTOOLS_BUILD_FAILED` | `fatal` | 29 | LoopTools `./configure && make` failed | Check gfortran; check log |

`activation_required` is **not** emitted as a blocker by this skill.

---

## Config keys written

| Key | Value |
|---|---|
| `formcalc_path` | Path to FormCalc package dir (contains `FormCalc.m`) |
| `formcalc_version` | e.g. `"10.0"` |
| `form_binary` | Absolute path to FORM binary |
| `form_version` | e.g. `"4.3.1"` |
| `looptools_lib` | Path to `libooptools.a` |
| `looptools_version` | e.g. `"10.0"` |
| `looptools_quad` | `"true"` or `"false"` |
| `formcalc_installed_at` | UTC ISO 8601 timestamp |
| `last_configured` | UTC ISO 8601 timestamp (auto-set by `config_merge`) |

Keys **read**: `wolfram_engine_path` (set by `/install` or `feynarts-install`).

---

## Version pins

Set in `skill_env.yaml`:

| Tool | Pin |
|---|---|
| FormCalc | `10.0` |
| LoopTools | `10.0` (bundled in FormCalc tarball) |
| FORM | `4.3.1` |

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Atomic-write helper: `plugins/shared/install-helpers/atomic_write.sh`
- macOS SDK probe: `plugins/shared/install-helpers/check_macos_sdk.sh`
- Wolfram helpers: `plugins/shared/install-helpers/wolfram/`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Downstream: `/formcalc` (reads `form_binary`, `formcalc_path`, `looptools_lib`)
