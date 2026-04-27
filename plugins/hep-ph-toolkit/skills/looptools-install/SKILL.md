---
name: looptools-install
description: Detect, validate, or build LoopTools (Thomas Hahn's numerical one-loop integral library) from source. Records looptools_path plus the gfortran version used at build time for downstream compiler-coherence checks.
---

# /looptools-install

Detects, validates, or compiles **LoopTools** (numerical one-loop scalar and
tensor integrals, companion to FeynArts/FormCalc, built on FF). Works in three
modes: **detect**, **use-path**, and **install**.

## Disk footprint

- **Tarball:** ~600 KB (`https://feynarts.de/looptools/LoopTools-2.16.tar.gz`)
- **Installed tree:** ~13 MB at `~/LoopTools/LoopTools-2.16`
- **Build-time peak (transient):** ~50 MB during configure + make
- **Measured 2026-04-25 on macOS arm64.** Source: run-20260425-dmc/installer_mathematica_report.md.

LoopTools is **required** for the Profumo 2506.19062 (`eval/2506.19062_wimps_blind_spots/`)
paper reproduction — blind-spot amplitudes in the 2HDM+a model use LoopTools
B0/C0/D0 calls inside the FormCalc-generated Fortran. Keep the install real;
never emulate loop integrals analytically or in Python.

---

## When to invoke

- Before any FormCalc-generated Fortran build that links `-looptools`.
- Before any SARAH/SPheno-generated module that imports `looptools.h`.
- Before reproducing the Profumo 2HDM+a calculation.
- When the user supplies an existing LoopTools install prefix.

---

## Decision flow

```
/looptools-install
    │
    ├─ detect         Check current state. Returns one of:
    │                   {"status":"missing"}
    │                   {"status":"found","path":"<prefix>"}
    │                   {"status":"configured","path":"<prefix>","version":"<v>",
    │                                          "gfortran_version":"<g>"}
    │
    ├─ use-path <p>   Accept a user-supplied prefix directory.
    │                 Validates lib/libooptools.a + include/looptools.h,
    │                 runs light smoke test, records looptools_path
    │                 and looptools_gfortran_version in config.
    │
    └─ install [dir]  Full auto-install from feynarts.de. Downloads tarball,
                      runs ./configure && make && make install, retains
                      source tree. Default prefix: ~/LoopTools/LoopTools-<version>
                      Override: HEPPH_LOOPTOOLS_VERSION=x.y
```

---

## gfortran precondition

`gfortran` must be present on `$PATH` before `install` runs. Checked by
`scripts/check_gfortran.sh`.

| OS | Command to install gfortran |
|----|----------------------------|
| macOS | `brew install gcc` |
| Debian/Ubuntu | `sudo apt-get install -y gfortran` |
| RHEL/CentOS | `sudo yum install -y gcc-gfortran` |

If absent, a `GFORTRAN_ABSENT` fatal blocker is emitted and the script exits
with `EXIT_NO_GFORTRAN` (10).

A C compiler (`gcc` or `clang`) is also required; absence emits `CC_ABSENT`
fatal blocker.

---

## gfortran coherence — critical

LoopTools builds a **static Fortran library** (`libooptools.a`) plus `.mod`
module files. `.mod` files are **gfortran-version-specific**: a LoopTools
installed with `gfortran-11` cannot be linked against Fortran code compiled
with `gfortran-13`. Symptoms are cryptic `unresolved symbol` or
`wrong module version` errors at link time.

To protect downstream skills, this skill:

1. Records the **full gfortran version string** (`gfortran --version | head -n1`)
   and the **absolute binary path** (`command -v gfortran`) at install time
   into config under:

   | Config key | Example |
   |-----------|---------|
   | `looptools_gfortran_version` | `GNU Fortran (Homebrew GCC 13.2.0) 13.2.0` |
   | `looptools_gfortran_path` | `/opt/homebrew/bin/gfortran-13` |

2. Downstream skills (`/spheno-install`, `/formcalc-build`, `/madgraph-install`)
   **must** read `looptools_gfortran_version` from config before compiling
   anything that links `-looptools`. If their own gfortran string differs,
   they should either:
   - rebuild LoopTools with the same compiler (`HEPPH_LOOPTOOLS_REBUILD=1`), or
   - emit a warning blocker recommending a rebuild.

3. On macOS with Homebrew, multiple gfortran binaries typically coexist
   (`/opt/homebrew/bin/gfortran`, `gfortran-13`, `gfortran-14`). Users can
   pin a specific one by exporting `FC=/opt/homebrew/bin/gfortran-13` before
   running `install`. The selected binary's full version is recorded.

**Reproducibility invariant for the Profumo paper**: `looptools_gfortran_version`
at the time of Figure-8 generation must match the `gfortran` subsequently used
to build FormCalc output in `eval/2506.19062_wimps_blind_spots/`.

---

## `.F` vs `.f` usage note

LoopTools headers use C-preprocessor `#include` directives. Any Fortran
source file that does `#include "looptools.h"` **must use the uppercase `.F`
extension** (or `.F90`). The `.f` extension tells gfortran to skip the
preprocessor, leading to `Unclassifiable statement at (1)` errors on the
first `#include`.

Correct:

```fortran
! file: my_amp.F   (capital F)
      implicit none
#include "looptools.h"
      print *, B0(1000D0, 50D0, 80D0)
```

Wrong: `my_amp.f` → fails to parse `#include`.

---

## Linkage

Once installed at `$PREFIX`:

**Fortran**:
```
gfortran -I$PREFIX/include my_amp.F -L$PREFIX/lib -looptools -o my_amp
```

**C/C++** (via the shipped wrapper):
```
$PREFIX/bin/fcc my_amp.cc -o my_amp
```

**Mathematica** (if built with MathLink — i.e., Mathematica was present
during `./configure`):
```mathematica
Install[$PREFIX <> "/bin/LoopTools"]
```

The `looptools_mathlink_available` config key records whether the MathLink
executable is present, so downstream skills can decide whether to use the
Mathematica frontend or the Fortran/C++ API.

---

## Config keys written

| Key | Value |
|-----|-------|
| `looptools_path` | Absolute path to the install **prefix** (contains `lib/libooptools.a`) |
| `looptools_src_path` | Absolute path to the retained source tree |
| `looptools_version` | Version string, e.g. `2.16` |
| `looptools_gfortran_version` | Full `gfortran --version` first line at build time |
| `looptools_gfortran_path` | Absolute path to the `gfortran` binary used |
| `looptools_mathlink_available` | `"true"` if `$PREFIX/bin/LoopTools` exists, else `"false"` |
| `looptools_installed_at` | UTC ISO 8601 timestamp |

---

## Failure modes → blockers

All blockers are emitted on stderr as single-line JSON per
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Cause | `user_instruction` | Exit |
|------|------|-------|--------------------|------|
| `GFORTRAN_ABSENT` | fatal | `gfortran` not on PATH | per-OS install command | 25 |
| `CC_ABSENT` | fatal | neither `gcc` nor `clang` on PATH | install a C compiler | 25 |
| `LOOPTOOLS_DOWNLOAD_FAILED` | fatal | curl failed twice | check internet; URL given | 12 |
| `LOOPTOOLS_CONFIGURE_FAILED` | fatal | `./configure` exited non-zero | see `/tmp/looptools_build.log` | 11 |
| `LOOPTOOLS_BUILD_FAILED` | fatal | `make` exited non-zero | see `/tmp/looptools_build.log` | 13 |
| `LOOPTOOLS_SMOKE_TEST_FAILED` | fatal | probe could not confirm working install | see message | 15 |
| `LOOPTOOLS_PATH_INVALID` | fatal | `use-path` argument invalid | see message | 16 |

Note: Mathematica absence is **not** a blocker. `./configure` detects it and
silently skips the MathLink build; `looptools_mathlink_available` is set
to `"false"` and the core Fortran library still builds via `make lib`.

---

## Version pin

| Variable | Purpose | Default |
|----------|---------|---------|
| `HEPPH_LOOPTOOLS_VERSION` | Pin a specific LoopTools release | `2.16` |
| `FC` | Choose a specific gfortran binary (macOS multi-install) | `$(command -v gfortran)` |
| `XDG_CONFIG_HOME` | Override config directory (test isolation) | `~/.config` |

Release 2.16 (2024-11-02) is the current default. Changelog: "Fixed missing
dummy arg in Ecoeffb."

Tarball URL: `https://feynarts.de/looptools/LoopTools-2.16.tar.gz`

---

## JSON status contract

| `status` | Meaning |
|----------|---------|
| `missing` | No LoopTools install found anywhere |
| `found` | Prefix found by scanning but not in config |
| `configured` | `looptools_path` set in config and validated |
| `installed` | Fresh install completed successfully |

---

## Scripts

| File | Purpose |
|------|---------|
| `scripts/install.sh` | Main entry point (`detect` / `use-path` / `install` / `validate`) |
| `scripts/check_gfortran.sh` | Checks for gfortran; records version + path |
| `scripts/probe_looptools.sh` | Smoke test (light: file presence; full: compile B0 test) |
| `scripts/b0_test.F` | Minimal Fortran program for `--full-smoke` |
| `scripts/_blocker.sh` | `emit_blocker` / `emit_blocker_with_context` bash helpers |

## Tests

| File | Type |
|------|------|
| `tests/test_detect.sh` | Bash smoke: detect, use-path, validate |
| `tests/fixtures/looptools_stub/` | Fake install tree (empty marker files) |

Run:

```bash
bash plugins/hep-ph-toolkit/skills/looptools-install/tests/test_detect.sh
```

---

## Smoke test contract

Light mode (`probe_looptools.sh <prefix>`):
- Asserts `<prefix>/lib/libooptools.a` is a regular file
- Asserts `<prefix>/bin/lt` is an executable file
- Asserts `<prefix>/include/looptools.h` is readable
- Asserts `<prefix>/include/clooptools.h` is readable

Full mode (`probe_looptools.sh --full-smoke <prefix>`):
- Compiles `scripts/b0_test.F` against `<prefix>` (requires `gfortran`)
- Runs the resulting binary
- Parses stdout for `B0(1000, 50, 80) = (-4.40593283, 2.7041431)`
- Tolerates floating-point differences to 4 decimal places
- Emits `LOOPTOOLS_SMOKE_TEST_FAILED` fatal blocker if output doesn't match

The `install` subcommand runs the **light** smoke test by default (fast,
sufficient for file-presence validation). Call `install.sh validate` to
re-run the light test on an existing install. Set
`HEPPH_LOOPTOOLS_FULL_SMOKE=1` to require the B0 numerical test at install
time as well.

---

## Augment, don't replace

LoopTools computes one-loop integrals numerically using FF. This skill does
**not** and **never will** emulate those integrals in Python or rely on
closed-form B0/C0 formulas. If LoopTools cannot be built, emit
`LOOPTOOLS_BUILD_FAILED` and stop. Downstream callers must treat LoopTools
absence as a hard blocker — see project memory
`feedback_augment_not_replace.md`.
