# micrOMEGAs install workarounds

A catalogue of the upstream patches `/micromegas-install` applies during
installation. Every entry lists: **symptom** (what you see if it's missing),
**cause** (why it has to exist), **mitigation** (what we do), and **where**
(file:line where the workaround lives).

Mirrors the style of `plugins/hep-ph-toolkit/skills/maddm-install/
references/maddm-workarounds.md`. If a future micrOMEGAs release fixes one of
these upstream, delete the corresponding `patch_micromegas_*` function in
`scripts/_patches.sh`, bump the sentinel version, and note the upstream
release tag here.

Sentinel: `.hepph_micromegas_patches_applied_v1` inside the install
directory.

Version history:
- **v1** — patch 1 (CalcHEP archive `make -j` race). Manifests as a hard
  build failure on Apple Silicon (clang 15+); intermittent on x86_64 Linux.
- **v1 addendum** — smoke-test regex updated for 6.0.5 output format change
  and `_smoke.sh` fixed to pass SLHA argument to MSSM binary (FU-wsb-002,
  FU-wsb-003; 2026-04-25 playtest).

---

## 1. CalcHEP `make -j` archive race

- **Symptom:** Build aborts at the link of `CalcHEP_src/bin/plot_view` (or
  any binary linking `CalcHEP_src/lib/serv.a`) with errors like:

  ```
  Undefined symbols for architecture arm64:
    "_f_printf",     referenced from: _writetable0 in serv.a[3](file_scr.o)
    "_nextFileName", referenced from: _plot_Nar in serv.a[14](plot.o)
    "_pathtocalchep", "_sortie", "_trim", ...
  ld: symbol(s) not found for architecture arm64
  clang: error: linker command failed with exit code 1
  make[3]: *** [../../bin/plot_view] Error 1
  ```

  The blocker emitted by `/micromegas-install` is `MICROMEGAS_BUILD_FAILED`
  with `context.make_log_tail` containing the `Undefined symbols` block.

- **Cause:** Ten Makefiles under `CalcHEP_src/c_source/*/` use GNU make's
  archive-member rule

  ```
  $(lib)/serv.a:$(lib)/serv.a($(OBJ))
  ```

  which expands so that each `.o` member is added to the archive by an
  independent `ar rv` invocation. Under `make -jN` (N>1) those `ar` calls
  race: each one reads `serv.a` from disk, modifies its in-memory copy, and
  writes back. The **last writer wins**, so any `.o` files added by an
  intermediate `ar` are silently lost.

  In the build log this looks like normal output — `ar rv ... syst.o`
  appears, the confirmation `a - syst.o` prints — but `ar t serv.a` after
  the build shows `syst.o` and `edittab.o` are absent. Their definitions of
  `f_printf`, `nextFileName`, `pathtocalchep`, `sortie`, `trim` are
  therefore not in the archive, and any binary linking against `serv.a`
  fails to resolve them.

  This is a textbook "lost update" race; it is **not** an arm64-specific
  bug despite the symptoms presenting as `Undefined symbols for
  architecture arm64`. The architecture in the error message is the
  *target*, not the cause; the underlying defect is racy archive
  modification under `make -j`. Apple Silicon happens to expose it
  reliably because of timing characteristics on macOS arm64; x86_64 Linux
  builds the same source intermittently.

  Affected Makefiles (10):

  - `CalcHEP_src/c_source/chep_crt/Makefile`
  - `CalcHEP_src/c_source/dynamicME/Makefile`
  - `CalcHEP_src/c_source/getmem/Makefile`
  - `CalcHEP_src/c_source/polynom/Makefile`
  - `CalcHEP_src/c_source/ntools/Makefile`
  - `CalcHEP_src/c_source/strfun/Makefile`
  - `CalcHEP_src/c_source/num/Makefile`
  - `CalcHEP_src/c_source/symb/Makefile`
  - `CalcHEP_src/c_source/service2/Makefile`
  - `CalcHEP_src/c_source/SLHAplus/Makefile`

- **Mitigation:** Insert `.NOTPARALLEL:` at the top of each affected
  Makefile (before any rules). GNU make's `.NOTPARALLEL:` is local to the
  containing makefile, so the rest of the build retains `make -j`
  parallelism. Verified empirically: with the patch, a fresh tree builds
  cleanly under `make -j8` on macOS arm64 (clang 21.0.0 / Apple Silicon)
  and `serv.a` contains all ten `.o` members it should.

- **Where:** `scripts/_patches.sh` →
  `patch_micromegas_calchep_archive_race`. Invoked from
  `scripts/install_impl.sh` Stage 4.5, after extraction and before make.

- **Upstream report status:** Not yet filed against
  `nllab.in2p3.fr/calchep` (CalcHEP) or `lapth.cnrs.fr/micromegas`. The
  fix is small enough to upstream as a one-line addition per Makefile, but
  doing so requires a CalcHEP release rather than a micrOMEGAs release
  since CalcHEP is an embedded copy. Cite this doc in any future PR.

---

## Why the v1.1 SKILL.md note was misleading

Earlier versions of `SKILL.md` (lines 242–244) attributed this failure to
`CalcHEP_src/getFlags` "emit[ting] x86_64 flags on arm64 systems when using
clang 15+." That diagnosis was wrong: `getFlags` does no architecture-flag
emission at all, and the actual binaries it produces are arm64-native. The
true root cause is the `make -j` race documented above. The "compile on an
x86_64 machine" workaround the old note offered is not necessary; the patch
in this doc fixes the build on arm64 directly.

When upstream eventually addresses this in CalcHEP, the v1.1 SKILL.md note
should be removed alongside the patch function.

---

## 2. 6.0.5 changed `Omega` output text — 5.x-era smoke regex silently fails (FU-wsb-002)

- **Symptom:** `_smoke.sh` exits non-zero (code 32, `MICROMEGAS_SMOKE_TEST_FAILED`)
  even when the MSSM binary ran successfully and printed a finite Ωh². The smoke
  output contains a line like `Omega=1.47e-03` but the regex check reports
  `no_match`.

- **Cause:** micrOMEGAs 5.x printed `Omega h^2 = <val>`. Version 6.0.5 changed
  this to `Omega=<val>` (no `h^2`, no spaces around `=`). Any smoke script
  written against the 5.x pattern will find no match on 6.0.5 output.

- **Mitigation:** `_smoke.sh` now matches both formats via a two-pattern Python
  check: `pattern_v5` (`Omega h^2 = ...`) and `pattern_v6` (`Omega=...`). Both
  patterns are tried before declaring failure. The v5 pattern is retained for
  fixture stubs that still emit the old string.

- **Where:** `scripts/_smoke.sh`, `omega_ok` Python block (the two-pattern
  `re.search` call).

---

## 3. MSSM smoke binary requires SLHA argument — unconditional failure without it (FU-wsb-003)

- **Symptom:** `_smoke.sh` always fails with exit code 32 on a real (not stub)
  micrOMEGAs install. The MSSM binary prints `correct usage: ./main <SLHA_file>`
  to stderr and exits 1 before producing any output. Because there is no `Omega`
  line, the regex check fails.

- **Cause:** The real MSSM `main` binary shipped with micrOMEGAs 6.0.5 requires
  an SLHA spectrum file as its first argument. Earlier versions of `_smoke.sh`
  called `"$bin"` with no arguments, so the binary always exited immediately
  with the usage message.

- **Mitigation:** `_smoke.sh` now probes the binary's first output for
  `argument|usage|correct usage`. If matched, it re-runs the binary with the
  SLHA input file (`input.slha` or `work/lanhep/suspect2_lha.out`, whichever
  exists). This logic is encapsulated in the `_run_main()` helper introduced
  in the WS-B playtest fix.

- **Where:** `scripts/_smoke.sh`, `_run_main()` function.
