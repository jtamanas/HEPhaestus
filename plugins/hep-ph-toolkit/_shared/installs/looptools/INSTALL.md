# LoopTools — Install Reference

Reference doc for installing **LoopTools** (numerical one-loop scalar and
tensor integrals, companion to FeynArts/FormCalc, built on FF). Driven by
`detect.sh` and `install.sh` in this directory; consumed by the `formcalc`
runner skill's preflight and by `/install`.

Three install modes are provided: **detect**, **use-path**, and **install**.

## Version pin

`detect.sh` pins LoopTools to **2.16**. Override with
`HEPPH_LOOPTOOLS_VERSION=x.y`. When this pin bumps, `install.sh` must
remove or migrate the previous install tree (e.g. `~/LoopTools/LoopTools-2.16`
→ `~/LoopTools/LoopTools-<new>`); old version-locked entries in
`init.m` or shell rc files (none for LoopTools) must also be cleaned up.
The new version is only written to `config.json` after the new install
verifies, so a half-finished upgrade does not leave the config pointing
at a stale binary.

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

## Decision flow

```
LoopTools install
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
`check_gfortran.sh`.

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

2. Downstream installers (`_shared/installs/spheno/install.sh`,
   `_shared/installs/formcalc/install.sh`, MG5/MadGraph build scripts)
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

**Mathematica / Wolfram** (if built with MathLink — see the section below):
```mathematica
link = Install[$PREFIX <> "/bin/LoopTools"];
LoopTools`B0[0, 100^2, 100^2]
Uninstall[link]
```

The `looptools_mathlink_available` config key records whether the MathLink
executable (`$PREFIX/bin/LoopTools`) is present **and verified**, so downstream
skills can decide whether to use the Wolfram frontend or the Fortran/C++ API.
`looptools_mathlink_path` records the absolute path to that binary.

---

## MathLink frontend (`bin/LoopTools`) — building under Wolfram Engine

`make lib` builds only the static Fortran library. The Wolfram-callable
`bin/LoopTools` MathLink executable is a **separate target** (`make all` /
`make mma1`) that the stock `./configure` enables **only if it can compile a
MathLink template**. The probe in `configure` does nothing more than call
`${MCC:-mcc}`; if `mcc` is not reachable it sets `ML = 0` in the generated
`makefile` and the frontend is **silently skipped** — `make lib` still
succeeds, so a "successful" install can lack `bin/LoopTools`. This is the
single most common reason the Wolfram frontend is missing.

### Failure signature when `mcc` is absent

- `bin/lt` (Fortran CLI), `lib/libooptools.a`, `include/*.h` all present, but
  **`bin/LoopTools` missing**.
- In the generated `makefile`: `ML = 0` and `MCC = mcc`.
- `./configure` output contains `do we have MathLink... no`.

### Wolfram Engine has no kernel and no `mcc` on PATH

Wolfram Engine (the free headless kernel) installs **none** of
`math` / `MathKernel` / `WolframKernel` / `mcc` on `PATH` — only
`wolframscript`. So neither `configure`'s `mcc` probe nor a `command -v math`
guard will ever find the toolchain. You must locate `mcc` inside the app
bundle yourself.

### Locating `mcc` (portable)

`mcc` (the MathLink Template Compiler) and its helper `mprep` live under the
Wolfram/Mathematica install at:

```
<WolframRoot>/SystemFiles/Links/MathLink/DeveloperKit/<platform>/CompilerAdditions/mcc
```

`<platform>` is OS+arch specific: `MacOSX-ARM64`, `MacOSX-x86-64`,
`Linux-x86-64`, `Linux-ARM64`. **Match it to the host arch** (`uname -m`) — an
arm64 host must use `MacOSX-ARM64`, otherwise the produced binary mismatches
the gfortran library's arch. Find it without hardcoding paths:

```bash
# macOS (Spotlight) — pick the line matching your platform dir:
mdfind -name mcc | grep CompilerAdditions/mcc | grep MacOSX-ARM64

# Anywhere — scan common roots (Wolfram Engine app shown):
find "/Applications/Wolfram Engine.app" -type f \
  -path "*MacOSX-ARM64/CompilerAdditions/mcc" 2>/dev/null
```

On this machine `mcc` resolves under
`/Applications/Wolfram Engine.app/Contents/Resources/Wolfram Player.app/Contents/SystemFiles/Links/MathLink/DeveloperKit/MacOSX-ARM64/CompilerAdditions/`
(Wolfram Engine nests a *Wolfram Player.app* inside it). Other installs put it
under `/Applications/Mathematica.app/...` or a Linux `WolframEngine`/`Mathematica` tree.

### Spaces-in-path gotcha — critical on macOS

`mcc` is an old `/bin/sh` script that derives its dev-kit dir from `$0` and
uses it **unquoted** to find `mprep`, `mathlink.h`, and `libMLi4.a`. The macOS
app path contains spaces (`Wolfram Engine.app`, `Wolfram Player.app`), so a
direct invocation fails with:

```
mcc: line 685: /Applications/Wolfram: No such file or directory
clang: error: no such file or directory: 'Engine.app/.../CompilerAdditions'
clang: error: no such file or directory: '/Applications/Wolfram/libMLi4.a'
```

Fix: expose the `CompilerAdditions` directory through a **space-free symlink**
and invoke `mcc` through that, so every `$0`-derived path is space-free (the
symlink resolves to the real spaced location transparently):

```bash
ln -sfn \
  "/Applications/Wolfram Engine.app/Contents/Resources/Wolfram Player.app/Contents/SystemFiles/Links/MathLink/DeveloperKit/MacOSX-ARM64/CompilerAdditions" \
  /tmp/wolfram-mldk-arm64
MCC=/tmp/wolfram-mldk-arm64/mcc
```

`install.sh::locate_mcc()` automates all of the above: it picks the platform
dir by `uname`, finds `mcc` via `mdfind`/`find`, and transparently creates the
space-free symlink (under `$TMPDIR`) when needed. Override detection with
`MCC=/path/to/mcc`; force library-only with `HEPPH_LOOPTOOLS_NO_MATHLINK=1`.

### Build incantation

Re-running `./configure` with `MCC` set will flip `ML = 1`; but you can also
build the frontend without reconfiguring by **overriding `MCC` on the make
command line** (command-line assignment wins over the makefile value) and
using the `all` target — this links against the **existing** `libooptools.a`,
so the static Fortran lib is **not** rebuilt with a different compiler:

```bash
cd "$PREFIX"                      # e.g. ~/LoopTools/LoopTools-2.16
make all MCC="$MCC"               # builds build/LoopTools
cp -p build/LoopTools bin/LoopTools
```

`make` invokes `mcc LoopTools.tm -o LoopTools -n fortranflush.o libooptools.a`.
`mcc` runs `mprep` (template → `.tm.c`), compiles via the wrapper scripts
`src/frontend/fcc`/`f++` (which forward to the configure-chosen `gcc`/`g++`),
and links the **static** `libMLi4.a` plus the gfortran runtime. A benign
`ld: warning: ignoring duplicate libraries: '-lSystem'` is expected.

### Compiler / arch coherence

- The host is arm64; `mcc`'s arch logic leaves clang's `-arch` empty for the
  ARM64 dev kit, so clang builds **arm64 natively** — correct. Confirm with
  `file bin/LoopTools` → `Mach-O 64-bit executable arm64`.
- The frontend links `libooptools.a`, so it inherits the **same gfortran
  (15.2.0)** used to build the lib — honour the "gfortran coherence" section;
  do **not** rebuild the lib with a different compiler just to get the frontend.
- `otool -L bin/LoopTools` shows it dynamically links Homebrew's
  `libgfortran.5.dylib` / `libquadmath.0.dylib` (rpath baked in by the
  makefile `LDFLAGS`). The Homebrew `gcc` runtime must remain present at run
  time; `libMLi4.a` (MathLink) is linked **statically** (no `libML*.dylib` in
  `otool -L`), so Wolfram itself need not be on the dynamic-link path.

### Verification (the pass condition)

Prove it evaluates an integral, not just that it compiled. Note: in
`wolframscript -code '...'`, bare `B0`/`A0` are interned into `Global`` at
**parse time**, before `Install` runs the package's `BeginPackage["LoopTools`"]`,
so they get shadowed and return unevaluated. Defer resolution with
`ToExpression` (runs after `Install`, binds to `LoopTools``), or fully qualify
as `LoopTools`B0`:

```bash
wolframscript -code 'link = Install["'"$PREFIX"'/bin/LoopTools"];
  Print["B0 = ", ToExpression["B0[0, 100^2, 100^2]"]];
  Print["A0 = ", ToExpression["A0[100^2]"]];
  Uninstall[link]'
```

Expected (default Delta=0, mu^2=1): `B0 = -9.210340371976184`
(`= -log(100^2)`), `A0 = -82103.40371976183` (`= 100^2*(1-log(100^2))`). Any
finite numbers = pass. **Only then** flip `looptools_mathlink_available` to
`"true"`.

Benign cosmetic artifact: a line
`libc++abi: terminating due to uncaught exception of type MathLink::MLException`
may appear on **stderr**, printed out-of-order. It comes from the child
LoopTools process tearing down during `Uninstall`; the kernel computes
correctly and exits 0. Ignore it (filter with `2>/dev/null` if noisy).

---

## Config keys written

| Key | Value |
|-----|-------|
| `looptools_path` | Absolute path to the install **prefix** (contains `lib/libooptools.a`) |
| `looptools_src_path` | Absolute path to the retained source tree |
| `looptools_version` | Version string, e.g. `2.16` |
| `looptools_gfortran_version` | Full `gfortran --version` first line at build time |
| `looptools_gfortran_path` | Absolute path to the `gfortran` binary used |
| `looptools_mathlink_available` | `"true"` if `$PREFIX/bin/LoopTools` was built+verified, else `"false"` |
| `looptools_mathlink_path` | Absolute path to `$PREFIX/bin/LoopTools` (set when available) |
| `looptools_mathlink_verified` | `"true"` if the B0 runtime check passed; `"unverified"` if the binary built but `wolframscript` was absent to run the check |
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

Note: a missing Wolfram/Mathematica dev kit (`mcc`) is **not** a blocker. When
`install.sh::locate_mcc()` finds no `mcc`, the MathLink frontend is skipped,
`looptools_mathlink_available` is set to `"false"`, and the core Fortran
library still builds via `make lib`. When `mcc` **is** found the installer
builds `bin/LoopTools` via `make all` and records `"true"` only after the
binary exists **and** passes the B0 runtime check (see "MathLink frontend"
above).

**The MathLink frontend is optional and never sinks the core deliverable.**
If `make all` fails (e.g. a broken or incompatible `mcc` toolchain on another
machine), `install.sh` retries `make lib`; if the **core** library builds it
downgrades to library-only (`looptools_mathlink_available="false"`) and the
install **succeeds**. A fatal `LOOPTOOLS_BUILD_FAILED` is emitted **only** when
the core `make lib` itself fails — mirroring the no-`mcc` branch.

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
| `install.sh` | Main entry point (`detect` / `use-path` / `install` / `validate`) |
| `check_gfortran.sh` | Checks for gfortran; records version + path |
| `probe_looptools.sh` | Smoke test (light: file presence; full: compile B0 test) |
| `b0_test.F` | Minimal Fortran program for `--full-smoke` |
| `_blocker.sh` | `emit_blocker` / `emit_blocker_with_context` bash helpers |

## Tests

| File | Type |
|------|------|
| `tests/test_detect.sh` | Bash smoke: detect, use-path, validate |
| `tests/fixtures/looptools_stub/` | Fake install tree (empty marker files) |

Run:

```bash
bash plugins/hep-ph-toolkit/_shared/installs/looptools/tests/test_detect.sh
```

---

## Smoke test contract

Light mode (`probe_looptools.sh <prefix>`):
- Asserts `<prefix>/lib/libooptools.a` is a regular file
- Asserts `<prefix>/bin/lt` is an executable file
- Asserts `<prefix>/include/looptools.h` is readable
- Asserts `<prefix>/include/clooptools.h` is readable

Full mode (`probe_looptools.sh --full-smoke <prefix>`):
- Compiles `b0_test.F` against `<prefix>` (requires `gfortran`)
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
