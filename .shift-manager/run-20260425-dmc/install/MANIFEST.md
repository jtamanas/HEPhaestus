# Install Manifest — `/demo` reconnaissance

**Run:** `run-20260425-dmc`
**Author:** install-stack scout (read-only recon)
**Date:** 2026-04-25
**Host:** `Yiannis-MacBook-Air.local` (Darwin 25.4.0, arm64, macOS 26.4.1)
**Shared config probed:** `/Users/yianni/.config/hep-ph-agents/config.json`
**Validator pass:** `python3 plugins/hep-ph-demo/skills/install/scripts/check_config.py` → "All tools OK." (Wolfram/SARAH/SPheno/MG5).

> **TL;DR:** The 4-tool Demo bundle (Wolfram, SARAH, SPheno, MG5+MadDM) is INSTALLED and validated. Everything else needed to take `/demo` from "relic only" to "all constraints all models" — micrOMEGAs, LoopTools, FeynArts, FormCalc, Package-X, DDCalc, DRAKE, FeynRules — is MISSING. **Hard blocker before any new install:** only **1.5 GiB free** on `$HOME`; the bundle below needs ~10–13 GiB. Free disk first or installer agents will fail at the `check_disk` step.

---

## Status definitions

| Status | Meaning |
|---|---|
| `INSTALLED` | Path recorded in `config.json`, files present, smoke test passes (or already passed in `check_config.py`). |
| `INSTALLED_BUT_BROKEN` | Files present but a smoke probe / sentinel signals a known defect (e.g. patches not applied, version mismatch). |
| `PARTIAL` | Some sub-component installed, others missing. |
| `MISSING` | No trace of the tool found in config, well-known paths, or `mdfind`. |
| `UNKNOWN` | Could not probe non-invasively (e.g. requires a network call or interactive activation). |

---

## 1. Tool table

| Tool | Required by (skill : line) | Install status | Version (if installed) | Path (if installed) | Canonical install procedure | Dep graph parents |
|------|---------------------------|----------------|------------------------|---------------------|------------------------------|--------------------|
| **Wolfram Engine** | `demo/SKILL.md:18-29` (preflight); `2hdm-a/SKILL.md:524`; `singlet-doublet/SKILL.md` Step 4b; SARAH/FeynArts/FormCalc/Package-X/DRAKE/FeynRules installers | `INSTALLED` | 14.3.0 | `/usr/local/bin/wolframscript` (app: `/Applications/Wolfram Engine.app`) | Manual; see `install/SKILL.md:206-322` Wolfram walkthrough; `install/scripts/install_wolfram.sh` (detect/use-path only) | — |
| **SARAH** | `demo/SKILL.md:18` preflight; `2hdm-a/SKILL.md:213-272` Step 4a/4b; `singlet-doublet/SKILL.md` Step 4a-c | `INSTALLED` | 4.15.3 | `/Users/yianni/SARAH/SARAH-4.15.3` (`init.m` registers `~/SARAH/SARAH-current` in `$Path`) | `install/scripts/install_sarah.sh install`; tarball from `https://sarah.hepforge.org/downloads/SARAH-4.15.3.tar.gz`; SHA256 `TODO` in `install/skill_env.yaml:24` | Wolfram Engine |
| **SPheno** | `demo/SKILL.md:18` preflight; `singlet-doublet/SKILL.md` Step 4c via `/spheno-build` | `INSTALLED` | 4.0.5 | `/Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno` (src: `/Users/yianni/SPheno/SPheno-4.0.5`) | `install/scripts/install_spheno.sh install`; tarball from `https://spheno.hepforge.org/downloads/SPheno-4.0.5.tar.gz` | gfortran, LAPACK |
| **MadGraph5_aMC@NLO** | `demo/SKILL.md:18` preflight; all 3 model skills' Step 4c | `INSTALLED` | 3.5.6 | `/Users/yianni/MG5_aMC/bin/mg5_aMC` → `/Users/yianni/MG5_aMC_v3_5_6/bin/mg5_aMC` | `install/scripts/install_mg5.sh install`; tarball at `launchpad.net/mg5amcnlo/3.0/3.5.x/+download/MG5_aMC_v3.5.6.tar.gz` | gfortran |
| **MadDM** | All 3 model skills' Step 4c (relic & ID branches); `dark-matter-constraints/SKILL.md` Step 2 | `INSTALLED` (warning: `bin/maddm` symlink absent — see Open Q1) | 3.2.13 | `/Users/yianni/MG5_aMC_v3_5_6/PLUGIN/maddm` | `/maddm-install` skill: `mg5_aMC -f` running `install maddm` (primary) + git fallback `https://github.com/maddmhep/maddm`; auto-applies upstream patches (see `maddm-install/SKILL.md:51-61`) | MadGraph5, gfortran |
| **micrOMEGAs** | `dark-matter-constraints/SKILL.md` (validator role); `dark-su3` paper fidelity (project_dm_tool_roles memory); `singlet-doublet`/`2hdm-a` cross-check via `/dark-matter-constraints` | `MISSING` | — | — | `/micromegas-install install`; LAPTh archive, version 6.0.5 | gfortran, gcc, X11 (warn-only) |
| **DRAKE** | `dark-su3/SKILL.md` resonance overlay (Profumo Fig. 8); narrow-resonance bundle in `install/SKILL.md:58-65` | `MISSING` | — | — | `/drake-install` skill — auto-install **typically blocked** by hepforge Anubis bot-gate; routes to manual download from `https://drake.hepforge.org/` then `/drake-install use-path <dir>` | Wolfram Engine |
| **LoopTools** | Profumo paper scope (project memory: "hard dependency"); `install/SKILL.md:67-72`; bundled inside FormCalc 9.10 tarball (per `formcalc-install/skill_env.yaml:7`) | `MISSING` | — | — | `/looptools-install install` (standalone v2.16) **OR** comes free with `/formcalc-install install` (v9.10 bundled). Tarball: feynarts.de | gfortran, gcc |
| **FeynArts** | `2hdm-a/SKILL.md:117` DD; `singlet-doublet/SKILL.md` DD; `dark-su3/SKILL.md` DD; flagged `[PLANNED]` in `_shared/constraints.yaml:35` | `MISSING` | — (target 3.11) | — | `/feynarts-install install`; tarball `https://www.feynarts.de/FeynArts-3.11.tar.gz`; installs to `$UserBaseDirectory/Applications/FeynArts-3.11/` | Wolfram Engine |
| **FormCalc** | Same as FeynArts (DD chain); flagged `[PLANNED]` in `_shared/constraints.yaml:39` | `MISSING` | — (target 9.10) | — | `/formcalc-install install`; tarball `https://feynarts.de/formcalc/FormCalc-9.10.tar.gz` (sha256 verified in skill_env.yaml); also installs FORM 4.3.1 from github + bundled LoopTools 9.10 | Wolfram Engine, gfortran, gcc |
| **FORM** (FormCalc preprocessor) | Transitive via FormCalc | `MISSING` | — (target 4.3.1) | — | Co-installed by `/formcalc-install install` from `https://github.com/vermaseren/form/releases/download/v4.3.1/form-4.3.1.tar.gz` | gcc |
| **Package-X** | `singlet-doublet/SKILL.md` DD comment; `_shared/constraints.yaml:43`; FormCalc + Package-X is the canonical loop-SI chain | `MISSING` | — (target 2.1.1) | — | `/package-x-install install [parent]`; **upstream is currently unreachable** — `package-x-install/skill_env.yaml` records `package_x_sha256_primary: "UPSTREAM_UNREACHABLE_2026_04"`. Use `HEPPH_PACKAGE_X_SKIP_URL_CHECK=1` bypass + offline-cache (see Open Q3) | Wolfram Engine |
| **FeynCalc** | Profumo paper scope memory ("natural partner to Package-X for analytic reductions") | `MISSING` | — | — | **No install skill exists.** Standard Mathematica `<<FeynCalc\`` install via paclet manager, or hand-clone from `github.com/FeynCalc/feyncalc`. Out-of-band; not driven by any current skill. | Wolfram Engine |
| **DDCalc** | `2hdm-a/SKILL.md:117` DD; all 3 model DD chains; `_shared/constraints.yaml:47` | `MISSING` | — (target 2.2.0) | — | `/ddcalc-install install`; pure Fortran + C shim; needs `gfortran` and ≥ 2 GiB free | gfortran, gcc |
| **2HDMC** | Profumo memory ("nice-to-have for 2HDM+a"); not referenced from any current skill or `*-install` | `MISSING` | — | — | **No install skill exists.** User must build by hand from `https://2hdmc.hepforge.org/` if needed; SPheno can substitute for tree unitarity per memory. | gcc, make |
| **FeynRules** | `install/SKILL.md:27` (lists in tool directory); not invoked by any current `/demo` model skill — kept as user-facing convenience | `MISSING` | — (target 2.3.49) | — | `/feynrules-install install`; tarball from `feynrules.irmp.ucl.ac.be`; SARAH-first per `feynrules-install/SKILL.md:13-19` | Wolfram Engine |
| **HiggsBounds/HiggsSignals (HiggsTools)** | Not referenced from `/demo` skills directly; install skill exists at `constraints/skills/higgstools-install/` | `MISSING` | — | — | `/higgstools-install install` (legacy Fortran, default) or `--backend=unified` (C++) | gfortran |
| **Mathematica** (alternative to Wolfram Engine) | Same role as Wolfram Engine | `MISSING` | — | — | (Out of scope; Wolfram Engine is the default) | — |
| **Wolframscript** | Same probe as Wolfram Engine | `INSTALLED` | 14.3.0 | `/usr/local/bin/wolframscript` | Co-installed with Wolfram Engine | — |
| **Python (3.10.16)** | All skills (parsing, plotting, schema validation) | `INSTALLED` | 3.10.16 (pyenv) | `/Users/yianni/.pyenv/versions/3.10.16/bin/python3` | pyenv | — |
| **numpy** | Plotting + parsing | `INSTALLED` | 2.2.6 | site-packages | `pip install` (auto by `check_python_deps.py`) | Python |
| **matplotlib** | Plotting | `INSTALLED` | 3.10.8 | site-packages | `pip install matplotlib>=3.8` | Python |
| **scipy** | MadDM internals; some plotting | `INSTALLED` | 1.15.3 | site-packages | `pip install scipy` | Python |
| **pyyaml** | ModelSpec + constraints.yaml parsing | `INSTALLED` | 6.0.3 | site-packages | `pip install pyyaml` | Python |
| **jsonschema** | Provenance & summary schema validation | `INSTALLED` | 4.26.0 | site-packages | `pip install jsonschema` | Python |
| **gfortran** | SPheno, MG5, MadDM, LoopTools, DDCalc, micrOMEGAs, FormCalc, HiggsTools | `INSTALLED` | GCC 15.2.0 (Homebrew) | `/opt/homebrew/bin/gfortran` | `brew install gcc` | — |
| **gcc / clang** | C compilation | `INSTALLED` | Apple clang 21.0.0 (`/usr/bin/gcc` is the Apple clang shim) | `/usr/bin/gcc` & `/usr/bin/clang` | Xcode CLT | — |
| **make** | Every Fortran/C build | `INSTALLED` | GNU Make 3.81 (Apple-shipped) | `/usr/bin/make` | Xcode CLT (NOTE: SPheno docs warn that 3.81 is acceptable but old; consider `brew install make` for `gmake` if any installer fails) | — |
| **cmake** | Some HiggsTools backends; not on the demo critical path | `INSTALLED` | 4.3.1 | `/opt/homebrew/bin/cmake` | `brew install cmake` | — |
| **LAPACK** | SPheno (`install/skill_env.yaml:39`) | `UNKNOWN` (probably linked to Apple Accelerate; SPheno already built and runs, so functionally OK) | — | — | `brew install lapack` only if SPheno rebuild fails with `EXIT_NO_LAPACK=25` | — |
| **pythia** | Not on `/demo` critical path; `monte-carlo-tools/skills/pythia-config` exists | `MISSING` | — | — | Out of scope for this manifest | — |
| **git** | MadDM fallback path; FeynRules; some `*-install` retries | `INSTALLED` (assumed; `gh`/git work elsewhere in this repo) | — | system | system | — |

**Disk budget summary** (sums of `size_gb_approx` from skill_env.yaml files):
- Wolfram Engine ~4.0 GB *(already installed)*
- SARAH ~0.5 GB *(already installed)*
- SPheno ~0.3 GB *(already installed)*
- MG5+MadDM ~0.5 GB *(already installed)*
- micrOMEGAs ~3 GB (min) / ~5 GB (warn) — `micromegas-install/skill_env.yaml`
- LoopTools ~0.1 GB
- FeynArts ~0.05 GB (Mathematica package)
- FormCalc + bundled LoopTools + FORM ~3 GB min / ~5 GB warn
- Package-X ~0.05 GB
- DDCalc ~2 GB min / ~4 GB recommended
- DRAKE ~0.05 GB

**Net new install footprint: ~8–14 GB. Currently free in `$HOME`: 1.5 GiB.** This is the single most important blocker — see Open Q4.

---

## 2. Per-tool detail blocks (MISSING / PARTIAL / INSTALLED_BUT_BROKEN)

### 2.1 micrOMEGAs (MISSING)

- **Probe used.**
  - `mdfind -name "micromegas*"` → only worktree fixtures, no real install.
  - `ls /Users/yianni/micromegas* /opt/micromegas* /Users/yianni/Tools/micromegas*` → no matches.
  - No `micromegas_path` key in `config.json`.
- **Required by.**
  - Project memory `project_dm_tool_roles.md` — "MadDM primary, micrOMEGAs validator".
  - `plugins/constraints/skills/dark-matter-constraints/SKILL.md` Step 3-4 (cross-check trigger logic).
  - Profumo paper scope memory — "validator for coannihilation + DD cross-checks".
  - `plugins/hep-ph-demo/skills/dark-su3/SKILL.md:84-95` (paper uses micrOMEGAs for Ψ relic).
- **Install procedure.**
  - Skill: `plugins/constraints/skills/micromegas-install/SKILL.md`.
  - Subcommand: `/micromegas-install install [parent_dir] [--full-smoke]`.
  - Pin: `micromegas-install/skill_env.yaml:micromegas_version: "6.0.5"`. (Recent skill-env says 6.0.5 but `/install` directory table in `hep-ph-demo` says 6.2.3 — mismatch. See Open Q5.)
  - Disk: `disk_min_gb: 3`, `disk_warn_gb: 5`.
  - Builds CalcHEP from sources/ via `make -j<nproc>`; macOS env setup via `_macos_env.sh`.
- **External deps.** `gfortran` (✓ installed), `cc` (✓), `gmake` (Apple `make` is fine), X11 (warn-only — not strictly needed for headless).
- **Network.** LAPTh primary URL + Zenodo fallback during `download_with_retry`.
- **Estimated install time.** 20-40 min (download + CalcHEP/symbolic-link build + light smoke test).
- **Known gotchas.** SHA256 still `TODO`; `verify_checksum` warns but does not abort. Apple-Silicon-specific env shimming via `_macos_env.sh`. PPPC tables download is a separate post-make step.

### 2.2 LoopTools (MISSING)

- **Probe.** `mdfind -name "libooptools.a"` → none. No `looptools_path` key in config.
- **Required by.** Profumo memory — *"hard dependency, not optional"*. `plugins/hep-ph-demo/skills/install/SKILL.md:67-72` (one-loop bundle).
- **Install procedure.** `plugins/model-building/skills/looptools-install/SKILL.md` → `/looptools-install install`. Pin v2.16. Default prefix `~/LoopTools/LoopTools-2.16`. Records `looptools_path`, `looptools_version`, `looptools_gfortran_version`. **Note:** if `/formcalc-install` runs first, FormCalc 9.10 ships its own bundled LoopTools 9.10 — running both standalone v2.16 *and* bundled 9.10 is fine because the FormCalc one is internal to its tree, but downstream skills must read `looptools_path` from config (the standalone), not the FormCalc-internal one.
- **External deps.** `gfortran` (✓), C compiler (✓).
- **Network.** `https://feynarts.de/LoopTools/LoopTools-2.16.tar.gz`.
- **Estimated install time.** 5-10 min.
- **Known gotchas.** `.mod` files are gfortran-version-specific — installer records `looptools_gfortran_version` so downstream FormCalc/SPheno skills can detect compiler drift. Today's `gfortran` is GCC 15.2.0; if the user later switches compilers, LoopTools must be rebuilt.

### 2.3 FeynArts (MISSING)

- **Probe.** `mdfind -name "FeynArts.m"` → only worktree fixtures. No `feynarts_path` in config.
- **Required by.** All 3 model skills' DD branches; flagged `[PLANNED]` in `_shared/constraints.yaml:35`. Profumo memory.
- **Install procedure.** `/feynarts-install install`. Pin `feynarts_version: "3.11"`. Tarball `https://www.feynarts.de/FeynArts-3.11.tar.gz`. Installs to `$UserBaseDirectory/Applications/FeynArts-3.11/` (resolves on macOS to `~/Library/Mathematica/Applications/FeynArts-3.11/`, BUT the user's machine has only `~/Library/Wolfram/` — so the installer needs to honour the Wolfram Engine `$UserBaseDirectory`, currently `~/Library/Wolfram/`). See Open Q2.
- **External deps.** Wolfram Engine (✓).
- **Network.** feynarts.de.
- **Estimated install time.** 2-5 min.
- **Known gotchas.** SHA256 = `TODO`. `$UserBaseDirectory` resolution under Wolfram Engine vs. Mathematica differs (see Open Q2).

### 2.4 FormCalc + FORM + bundled LoopTools (MISSING)

- **Probe.** `mdfind -name "FormCalc.m"` → only worktree fixtures.
- **Required by.** Same DD chain as FeynArts.
- **Install procedure.** `/formcalc-install install` → `scripts/install_formcalc.sh` (light) or `install_formcalc_full.sh` (with smoke). Pins: FormCalc 9.10, FORM 4.3.1, LoopTools 9.10 (bundled). SHA256s **verified** for both FormCalc and FORM. Disk: 3 GB min / 5 GB warn.
- **External deps.** Wolfram Engine (✓), `gfortran` (✓), `gcc` (✓).
- **Network.** feynarts.de + github.com (FORM).
- **Estimated install time.** 30-90 min (FORM build + FormCalc Fortran codegen + LoopTools 9.10 build).
- **Known gotchas.** Apple Silicon branch logic in `install_formcalc.sh`. The bundled LoopTools 9.10 may co-exist with a standalone LoopTools 2.16 — config keys do NOT collide (`looptools_path` vs. `formcalc_looptools_lib`), but downstream skills MUST be careful about which they import.

### 2.5 Package-X (MISSING — UPSTREAM UNREACHABLE)

- **Probe.** `mdfind -name "X.m" -path "*Mathematica*"` → none.
- **Required by.** SI loop reduction (Passarino-Veltman); referenced in all 3 model DD chains.
- **Install procedure.** `/package-x-install install [parent_dir]`. Target version 2.1.1. Install path `$UserBaseDirectory/Applications/X-2.1.1/`.
- **External deps.** Wolfram Engine (✓).
- **Network.** **Currently broken.** `package-x-install/skill_env.yaml` records `package_x_sha256_primary: "UPSTREAM_UNREACHABLE_2026_04"`. The skill exits 30 (`PACKAGE_X_UPSTREAM_UNREACHABLE`) unless `HEPPH_PACKAGE_X_SKIP_URL_CHECK=1` is set AND a local offline cache is provided.
- **Estimated install time.** 5 min (after the user manually drops a tarball into the offline-cache location).
- **Known gotchas.** This is the install-blocker for the entire DD chain on a fresh machine. See Open Q3.

### 2.6 DDCalc (MISSING)

- **Probe.** `mdfind -name "libDDCalc.a"` → none.
- **Required by.** All 3 model DD branches; `_shared/constraints.yaml:47`.
- **Install procedure.** `/ddcalc-install install`. Target v2.2.0. Pure Fortran + C shim.
- **External deps.** `gfortran` (✓), `gcc` (✓), ≥ 2 GiB free in `$HOME` (4 GiB recommended).
- **Network.** ddcalc.hepforge.org (assumed — `skill_env.yaml` is sparse; see Open Q5).
- **Estimated install time.** 15-30 min.
- **Known gotchas.** Apple Silicon build quirks called out in skill description; confirm `gfortran` ABI matches (✓ Homebrew GCC 15.2.0 on arm64).

### 2.7 DRAKE (MISSING)

- **Probe.** No `drake_path` key; `mdfind -name "test.wls"` returned only fixtures.
- **Required by.** Optional Profumo Fig. 8 overlay (Dark SU(3) resonance); `install/SKILL.md:58-65` (narrow-resonance bundle).
- **Install procedure.** `/drake-install install` is **expected to fail** — hepforge protects DRAKE behind the Anubis bot-challenge gate. Skill prints `manual_download_required` (exit 18, `DRAKE_HEPFORGE_GATED`) and instructs the user to download `https://drake.hepforge.org/` zipball manually, unpack, then run `/drake-install use-path <dir>`.
- **External deps.** Wolfram Engine (✓), wolframscript (✓).
- **Network.** drake.hepforge.org (gated).
- **Estimated install time.** 5 min once the tarball is on disk.
- **Known gotchas.** Anubis gate cannot be bypassed by the installer agent — the user must do this step interactively in a browser.

### 2.8 FeynCalc (MISSING — no install skill)

- **Probe.** None matching.
- **Required by.** Soft requirement per Profumo paper memory ("natural partner to Package-X").
- **Install procedure.** **No `*-install` skill exists for FeynCalc.** Closest path: hand-install via Mathematica paclet (`PacletInstall["FeynCalc"]`) or git-clone `github.com/FeynCalc/feyncalc` into `$UserBaseDirectory/Applications/`.
- **Recommendation.** Defer; not on the `/demo` critical path. Surface as a manifest open question.

### 2.9 2HDMC (MISSING — no install skill)

- **Probe.** None.
- **Required by.** Optional per Profumo memory; SPheno can substitute. No skill references it.
- **Install procedure.** No skill. Tarball at `https://2hdmc.hepforge.org/` (David Eriksson). C++ build with `make`. Out of scope unless the user explicitly asks for 2HDM+a unitarity/vacuum-stability checks.
- **Recommendation.** Skip in this manifest; flag in Open Questions.

### 2.10 FeynRules (MISSING)

- **Probe.** No `feynrules_path` in config; `mdfind -name "FeynRulesPackage.m"` → only fixtures.
- **Required by.** Listed in `install/SKILL.md:27` but **not invoked from any `/demo` model skill** — `/lagrangian-builder` is SARAH-first per project memory `project_lagrangian_builder_backend.md`.
- **Install procedure.** `/feynrules-install install`. Pin 2.3.49.
- **Recommendation.** Skip from default install set unless user explicitly opts in.

### 2.11 HiggsTools (MISSING)

- **Probe.** None.
- **Required by.** Not referenced from any `/demo` skill or `dark-matter-constraints`. Skill exists at `constraints/skills/higgstools-install/`.
- **Recommendation.** Skip from `/demo` install bundle.

### 2.12 MadDM — `bin/maddm` symlink absent (POTENTIAL_BROKEN)

- **Probe.** `ls /Users/yianni/MG5_aMC_v3_5_6/bin/` shows only `mg5_aMC` and `maddm.py`; no `maddm` executable. The maddm-install flow is documented to copy `PLUGIN/maddm/maddm → <MG5_ROOT>/bin/maddm` (`maddm-install/SKILL.md:67`).
- **However:** `/demo` and the model skills invoke MadDM via `mg5_aMC --mode=maddm`, not the bare `maddm` binary, so this missing symlink is **not** on the `/demo` critical path.
- **Action.** Validator (`probe_maddm.sh`) may still fail; recommend running `/maddm-install detect` to confirm `status: configured` and re-running `/maddm-install install` if it returns `found` only.

---

## 3. Dependency graph

```
                   ┌───────────────────┐
                   │  Wolfram Engine   │ (4.0 GB; manual activation)  ✓ INSTALLED
                   │   14.3.0 (✓)      │
                   └─────────┬─────────┘
                             │
       ┌───────────┬─────────┼──────────────────┬──────────────┬────────────┐
       │           │         │                  │              │            │
   ┌───▼────┐ ┌────▼────┐ ┌──▼──────┐    ┌──────▼──────┐ ┌─────▼─────┐ ┌────▼────┐
   │ SARAH  │ │FeynArts │ │FormCalc │    │  Package-X  │ │   DRAKE   │ │FeynRules│
   │ 4.15.3 │ │  3.11   │ │  9.10   │    │   2.1.1     │ │   1.0     │ │ 2.3.49  │
   │  ✓     │ │ MISSING │ │ MISSING │    │ MISSING/    │ │  MISSING  │ │ MISSING │
   │        │ │         │ │ +FORM + │    │  UPSTREAM   │ │  (Anubis) │ │ (defer) │
   │        │ │         │ │ LT 9.10 │    │  UNREACH    │ │           │ │         │
   └───┬────┘ └─────────┘ └─────────┘    └─────────────┘ └───────────┘ └─────────┘
       │
       │  (SARAH spectrum drives /spheno-build)
       │
   ┌───▼─────────────────┐
   │ SPheno  4.0.5 (✓)   │  needs gfortran (✓), LAPACK (✓ via Accelerate)
   └─────────────────────┘

                   ┌───────────────────┐
                   │     gfortran      │  (Homebrew GCC 15.2.0)  ✓
                   └─────────┬─────────┘
                             │
       ┌────────────┬────────┼──────────┬──────────────┬───────────┐
       │            │        │          │              │           │
   ┌───▼────┐ ┌─────▼──┐ ┌───▼────┐ ┌───▼──────┐ ┌─────▼────┐ ┌────▼────┐
   │  MG5   │ │ MadDM  │ │ SPheno │ │ LoopTools│ │ DDCalc   │ │micrOMEGAs│
   │ 3.5.6  │ │ 3.2.13 │ │  4.0.5 │ │  2.16    │ │  2.2.0   │ │  6.0.5  │
   │  ✓     │ │  ✓     │ │   ✓    │ │ MISSING  │ │ MISSING  │ │ MISSING │
   └────────┘ └────┬───┘ └────────┘ └──────────┘ └──────────┘ └─────────┘
                   │  (MadDM is an MG5 plugin; needs MG5 ≥ 2.6.2)
```

**Read this graph as install-order constraints:**

1. Wolfram Engine before SARAH, FeynArts, FormCalc, Package-X, DRAKE, FeynRules.
2. gfortran before SPheno, MG5, MadDM, LoopTools, DDCalc, micrOMEGAs, FormCalc (FORM + bundled LoopTools).
3. MG5 before MadDM (plugin).
4. SARAH before any `/sarah-build`, but install-time SARAH is independent.
5. **No coupling** between FeynArts/FormCalc/Package-X/Package-X chain and the MG5/MadDM/micrOMEGAs chain. They share only Wolfram and gfortran → can be installed in parallel.
6. LoopTools (standalone v2.16) is independent; `looptools_path` is consumed by SARAH/SPheno/FormCalc-Fortran modules in the Profumo eval. The bundled LoopTools 9.10 inside FormCalc is for FormCalc's own use only.
7. DDCalc is downstream of nothing in our skill graph — fully parallel with the other Mathematica installs.
8. DRAKE is independent; only requires Wolfram. Installer expected to bounce off Anubis gate → enter manual-download branch.

---

## 4. Install track assignments

Five tracks; tracks 2-5 may run concurrently. Track 1 is a no-op given the existing config.

### Track 0 — disk-cleanup (MUST run first)

- **Owner:** human (Yianni) or `installer-disk` agent with `df`, `du`, `rm` tools.
- **Goal:** raise free space under `$HOME` from 1.5 GiB → ≥ 12 GiB.
- **Wall time:** 5-30 min depending on what can be evicted.
- **Why first:** `_common.sh:check_disk` aborts every installer if free space < tool's `disk_min_gb` (FormCalc alone needs 3 GB; sum of pending installs ~10-13 GB).

### Track 1 — `installer-baseline` (no-op verify only)

- **Tools:** Wolfram, SARAH, SPheno, MG5, MadDM, gfortran/gcc/make/cmake, Python+deps.
- **Action:** `python3 plugins/hep-ph-demo/skills/install/scripts/check_config.py` (already passing).
  Plus: `/maddm-install detect` to confirm `status: configured` (mitigate the missing `bin/maddm` symlink concern).
- **Wall time:** 1-2 min.

### Track 2 — `installer-mc` (Monte Carlo / Boltzmann validators)

- **Tools, in order:** micrOMEGAs → DDCalc.
- **Why grouped:** both are Fortran, both need `gfortran`+`gcc`, both write under `$HOME`, both serve the `/dark-matter-constraints` validator+DD pipeline. They have no Wolfram requirement, so they don't compete with the Mathematica track for kernel slots.
- **Wall time:** 35-70 min total (micrOMEGAs ~20-40, DDCalc ~15-30).

### Track 3 — `installer-mathematica-loop` (FeynArts + FormCalc + Package-X + LoopTools)

- **Tools, in order:** LoopTools (standalone) → FeynArts → FormCalc (which also installs FORM + bundled LoopTools 9.10) → Package-X.
- **Serialization rationale:** all four touch `$UserBaseDirectory/Applications/` and load Mathematica kernels that hold global file locks during package init. Running them in parallel risks `init.m` write races.
- **Why before / parallel with Track 2:** LoopTools 2.16 has zero overlap with Track 2 (different libs, different paths) so scheduling is free.
- **Special handling:** Package-X step **will fail** unless `HEPPH_PACKAGE_X_SKIP_URL_CHECK=1` is set and an offline tarball is provisioned. Installer agent must surface a `manual_download_required` blocker rather than retry.
- **Wall time:** 40-110 min (FeynArts ~5, FormCalc ~30-90, Package-X 5-15 once cache is in place, LoopTools ~5-10).

### Track 4 — `installer-drake` (Wolfram-only optional extension)

- **Tools:** DRAKE.
- **Action:** Run `/drake-install install`. Expect exit 18 (`DRAKE_HEPFORGE_GATED`) → emit `manual_download_required` and stop. Wait for human to drop the zipball, then `/drake-install use-path <dir>`.
- **Wall time:** 5 min compute + however long the human takes to clear the Anubis gate (interactive).

### Track 5 — `installer-defer` (low priority / out-of-scope)

- **Tools:** FeynRules, HiggsTools, FeynCalc, 2HDMC, pythia.
- **Action:** Do not install in this run. Recommend the user invoke `/feynrules-install` etc. on demand if a future workflow needs them. Surface as Open Questions for the manager.

**Recommended parallelism:** Tracks 2 and 3 can run concurrently in separate worktrees / shells. Track 4 is a human-in-the-loop step; can begin in parallel as soon as the user is ready.

---

## 5. Pre-flight environment summary

| Item | Value | Source |
|------|-------|--------|
| OS | macOS 26.4.1 (Build 25E253) | `sw_vers` |
| Kernel | Darwin 25.4.0 | `uname -a` |
| Arch | arm64 (Apple Silicon, T8122) | `uname -m` |
| Free disk under `$HOME` | **1.5 GiB on `/dev/disk3s5`** | `df -h $HOME` (**critical — see Track 0**) |
| Wolfram Engine | v14.3.0, `/usr/local/bin/wolframscript`, **activated and responsive** (`2+2 → 4`) | `wolframscript -code '2+2'` |
| Wolfram app bundle | `/Applications/Wolfram Engine.app` (note: not `Wolfram.app`; `install/SKILL.md` detect logic accepts both — `install/SKILL.md:177`) | `ls /Applications/` |
| Wolfram `init.m` | `~/Library/Wolfram/Kernel/init.m` registers `~/SARAH/SARAH-current` in `$Path` | `head -20 ~/Library/Wolfram/Kernel/init.m` |
| `gfortran` | GNU Fortran (Homebrew GCC 15.2.0_1), `/opt/homebrew/bin/gfortran` | `gfortran --version` |
| `gcc` (system) | Apple clang 21.0.0 (`/usr/bin/gcc` symlinks to clang), `/usr/bin/clang` | `gcc --version` |
| Homebrew GCC | Available; `gcc-15` and friends co-exist in `/opt/homebrew/bin` | `brew --version` |
| `make` | GNU Make 3.81 (Apple-shipped, `/usr/bin/make`) | `make --version` |
| `cmake` | 4.3.1 (`/opt/homebrew/bin/cmake`) | `cmake --version` |
| `brew` | Homebrew 5.1.6 (`/opt/homebrew/bin/brew`) | `brew --version` |
| Python | 3.10.16 via pyenv at `/Users/yianni/.pyenv/versions/3.10.16/bin/python3` | `python3 --version` |
| numpy / matplotlib / scipy / pyyaml / jsonschema | 2.2.6 / 3.10.8 / 1.15.3 / 6.0.3 / 4.26.0 | `import` probes |
| `pip` | 23.0.1 (older; consider `python -m pip install -U pip` if any installer needs PEP 668 features) | `pip --version` |
| Existing tool roots | `~/SARAH/`, `~/SPheno/`, `~/MG5_aMC_v3_5_6/` (with `~/MG5_aMC` symlink), `~/.local/share/hep-ph-agents/models/` | `ls` |
| Tools dirs not present | `~/Tools/`, `~/HEP/` (these are common roots in `install/SKILL.md` detect lists; absence is fine) | `ls -ld` |
| Worktrees | `/Users/yianni/Projects/hep-ph-agents-worktrees/` contains 8+ worktrees including `feyndiag-formcalc`, `feyndiag-feynarts`, `constraints-ddcalc`, `constraints-micromegas` — these are dev branches, not install targets | `find` |
| Shared config | `/Users/yianni/.config/hep-ph-agents/config.json` (1124 bytes; 4 model entries, 4 tool keys) | direct read |
| Validator | `check_config.py` reports **PASS** for all 4 demo-bundle tools | run output |
| Disk pressure | macOS shows 100% capacity used, only 1.5 GiB unallocated. iCloud purgeable space may be reclaimable. | `df -h` |
| LAPACK | `brew list lapack` → not installed via brew; SPheno is built and runs, so it is presumably linked against Apple Accelerate. No action needed unless rebuilding. | `brew list` |

---

## 6. Open questions

1. **MadDM `bin/maddm` symlink absent.** `maddm-install/SKILL.md:67` documents copying `PLUGIN/maddm/maddm → <MG5_ROOT>/bin/maddm`, but only `mg5_aMC` and `maddm.py` are present in `/Users/yianni/MG5_aMC_v3_5_6/bin/`. `check_config.py` does not exercise this path. Should `installer-baseline` re-run `/maddm-install install` to repair, or is the standalone-`maddm` invocation deprecated in favor of `mg5_aMC --mode=maddm` (which all three model skills use)? **Manager decision needed.**

2. **`$UserBaseDirectory` resolution.** FeynArts and Package-X install into `$UserBaseDirectory/Applications/<pkg>/`. On the user's box, the Wolfram Engine `$UserBaseDirectory` is `~/Library/Wolfram/`, not `~/Library/Mathematica/`. Confirm the install scripts call `wolframscript -code "$UserBaseDirectory"` rather than hard-coding `~/Library/Mathematica/Applications/`. (Quick fix if not: pass `parent_dir` explicitly.)

3. **Package-X upstream is dead.** `package-x-install/skill_env.yaml` records `package_x_sha256_primary: "UPSTREAM_UNREACHABLE_2026_04"`. The skill exits 30 unless `HEPPH_PACKAGE_X_SKIP_URL_CHECK=1` plus a local cached tarball. **Where is the cached tarball?** No fixture under the install scripts dir. The installer agent will need a manager directive: either skip Package-X (and acknowledge the DD chain is permanently blocked) or fetch a tarball out-of-band and place it at the expected cache path.

4. **Disk-space showstopper.** `$HOME` has 1.5 GiB free. The aggregate net-new install footprint is ≥ 8 GiB. **Do not dispatch installer agents until the user clears space.** Recommend Track 0 first.

5. **Version drift between `/install` SKILL.md and per-tool `skill_env.yaml`.** `hep-ph-demo/skills/install/SKILL.md:464` lists micrOMEGAs at v6.2.3 and DRAKE at v1.0; the canonical `micromegas-install/skill_env.yaml` pins v6.0.5. Manager should adjudicate which version each installer actually fetches.

6. **DDCalc `skill_env.yaml` is sparse.** It does not pin a tarball URL, SHA256, or default install path in the lines I greppped (only `disk_min_gb=2`, `disk_warn_gb=4` per skill body). Installer agent will need to read `ddcalc-install/scripts/install_ddcalc.sh` for the actual URL — recommend confirming this before dispatch.

7. **FeynCalc, 2HDMC have no install skills.** They are referenced by project memory only. **Are these in scope for `/demo`?** Profumo memory marks both as "nice-to-have / optional substitutable". Recommend explicit defer.

8. **micrOMEGAs offline-cache mode** is referenced (`install [parent_dir] [--full-smoke]` + Zenodo fallback) but the cache location convention is not documented in the skill body excerpt I read. If the network call to LAPTh fails, the installer agent needs to know the cache directory contract. Cross-check with `_common.sh:download_with_retry` before dispatch.

9. **DRAKE manual download is interactive.** Track 4 cannot complete autonomously. Confirm whether the manager wants installer agents to block on this (waiting for the user to clear the Anubis gate) or to skip DRAKE entirely for this `/demo` run, given the Profumo paper scope says DRAKE is *optional* (only for Fig. 8 overlay).

10. **`hep-ph-agents/scripts` outside the install skills?** I did not find a top-level install runner. The marketplace install is fully driven from per-skill `*-install/SKILL.md` + `scripts/`. No drift to flag.

---

*End of manifest.*
