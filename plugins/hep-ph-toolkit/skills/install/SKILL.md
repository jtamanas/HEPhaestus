---
name: install
description: Directory and orchestrator for all hephaestus tool installers. Lists every supported tool, groups them into use-case bundles ("compute DM relic", "one-loop integrals", etc.), and runs the selected bundle. Invoke when the user says "install", "set up <tool>", "configure hephaestus", "what tools are available", or on first use of any downstream skill that needs a tool.
---

# Install

Top-level directory for every external tool hephaestus can drive. Every
successful per-tool install writes to a single unified config at
`~/.config/hephaestus/config.json` (or `$XDG_CONFIG_HOME/hephaestus/config.json`).
Downstream skills read that config to locate every tool.

---

## Disk footprint

Demo bundle (Wolfram Engine + SARAH + SPheno + MadGraph5_aMC@NLO):

| Tool | Tarball | Installed | Peak (transient) | Path |
|---|---|---|---|---|
| Wolfram Engine 14.3.0 | ~3 GB DMG | ~7.6 GB | ~3 GB during install | `/Applications/Wolfram Engine.app` |
| SARAH 4.15.3 | ~30 MB | ~71 MB | ~80 MB | `~/SARAH/SARAH-4.15.3` |
| SPheno 4.0.5 | ~10 MB | ~69 MB | ~150 MB | `~/SPheno/SPheno-4.0.5` |
| MadGraph5_aMC@NLO 3.5.6 | ~80 MB | ~665 MB | ~1 GB | `~/MG5_aMC_v3_5_6` |

**Demo bundle total: ~8.4 GB installed; ~12 GB free recommended for a clean install.**
**Measured 2026-04-25 on macOS arm64.** Source: du measured 2026-04-25.

---

## Tool directory

| Tool | Install skill | What it does |
|------|---------------|--------------|
| Wolfram Engine | (this skill, §Per-tool) | Free Wolfram kernel; prerequisite for SARAH, FeynRules, DRAKE |
| SARAH | `/sarah-install` or (this skill) | BSM Lagrangian → model files, analytic spectrum, beta functions |
| SPheno | `/spheno-install` or (this skill) | Compiles SARAH output → numerical mass spectrum + decays |
| MadGraph5_aMC@NLO | (this skill, §Per-tool) | Tree-level amplitudes, cross sections, event generation |
| MadDM | `/maddm-install` | MG5 plugin: DM relic density, direct/indirect detection |
| micrOMEGAs | `/micromegas-install` | Standalone DM observables; cross-check for MadDM |
| DRAKE | `/drake-install` | DM relic density beyond kinetic equilibrium (resonances, Sommerfeld) |
| LoopTools | `/looptools-install` | Numerical one-loop scalar/tensor integrals (Hahn) |
| FeynRules | `/feynrules-install` | Lagrangian → Feynman rules, UFO/FeynArts/CalcHEP export |

---

## Use-case bundles

Each bundle is a preset that installs a coherent set of tools for a specific task.
Invoke `/install <bundle>` or pick one interactively.

### 🎬 Demo bundle
**Useful if you want to** reproduce a published paper figure end-to-end, or
this is your first setup and you want a working baseline.

**Installs**: Wolfram Engine, SARAH, SPheno, MadGraph5_aMC@NLO. **Disk: ~5.3 GB.**

This is the historical `/install` flow — see §Per-tool installers below.

### 🔬 BSM model → spectrum
**Useful if you want to** build a new BSM Lagrangian and compute its mass
spectrum, mixing matrices, and decay widths. FeynRules is optional — SARAH
covers the same territory with tighter integration downstream.

**Installs**: Wolfram Engine, SARAH, SPheno, (optional) FeynRules. **Disk: ~5 GB.**

### 🌑 Dark matter relic + detection
**Useful if you want to** compute Ωh² and direct/indirect detection rates
for a given DM candidate. MadDM is the primary driver, micrOMEGAs is the
independent validator.

**Installs**: MadGraph5_aMC@NLO, MadDM, micrOMEGAs. **Disk: ~1.2 GB.**

### 🌊 Narrow-resonance / early-decoupling DM
**Useful if you want to** resolve resonance funnels, Sommerfeld enhancement,
or early kinetic decoupling — regimes where the standard Boltzmann solver
breaks down. Extends the DM bundle above.

**Installs**: everything in the DM bundle **plus** DRAKE. **Disk: ~1.2 GB + Wolfram.**
**Required for** reproducing Profumo 2506.19062 Fig. 8.

### ∮ One-loop calculations
**Useful if you want to** evaluate one-loop scalar and tensor integrals
numerically (Passarino–Veltman reduction). LoopTools is the canonical
numerical backend. **Required for** Profumo 2506.19062 reproduction.

**Installs**: LoopTools (and gfortran dependency check). **Disk: ~100 MB.**

---

## Bundle flow

1. If no bundle specified, present an `AskUserQuestion` with the 5 bundles
   above + "Pick individual tools" + "Just show me what's installed".

1b. Call `scripts/demo-install.sh bundle-preflight <id>`. If `requires_wolfram: true`, enter `## Wolfram walkthrough → Bundle warning`. Route per user choice (4 options). If `false`, proceed to step 2. Section 1 Option 2 branches on `install_wolfram.sh detect`: `configured` → continue to step 2; `found` → auto-prompt `Use this path: <path>? (y/n)`, yes runs `use-path`, no falls to Section 2; `missing` → Section 3.

2. For each tool in the chosen bundle, walk the §Per-tool detect/install
   flow below (for the 4 demo tools) or delegate to the corresponding
   `/<tool>-install` skill (for the other 5).

3. After the bundle completes, run `scripts/check_config.py` and report the
   final pass/fail table.

Delegation rule: this skill OWNS install logic only for Wolfram, SARAH, SPheno,
MG5. Every other tool is delegated to its dedicated `*-install` skill, which
writes to the same shared config. Do NOT reimplement MadDM/micrOMEGAs/DRAKE/
LoopTools/FeynRules logic here.

---

## Per-tool installers (legacy Demo-bundle flow)

The text below this line is the pre-existing per-tool flow for the 4 demo
tools. It remains the canonical implementation for the Demo bundle.

Philosophy: augment, don't replace. This skill drives the real tools — it
never emulates them. If a tool is already installed, detect it; never
reinstall without explicit user consent.

## When to invoke

- User asks to install, set up, or configure any of: Wolfram Engine, SARAH, SPheno, MadGraph5_aMC@NLO, hephaestus.
- A downstream skill fails because a `*_path` key is missing from the config.
- User says "first run" or the config file does not exist.

## The four tools (dependency order)

| Order | Tool | Depends on | Install method | Disk |
|-------|------|-----------|----------------|------|
| 1 | Wolfram Engine (free) | — | Manual (interactive activation) | ~4.0 GB |
| 2 | SARAH | Wolfram Engine | Tarball + register in `$Path` | ~0.5 GB |
| 3 | SPheno | gfortran (+ LAPACK) | Tarball + `make` | ~0.3 GB |
| 4 | MadGraph5_aMC@NLO | gfortran | Tarball (existing flow) | ~0.5 GB |

Total ~5.3 GB free in `$HOME` needed for a clean install of all four.
Order matters: SARAH needs Wolfram; SPheno compiles standalone Fortran; MG5
is independent. The orchestrator always walks in the order above.

## Flow

1. Call `scripts/demo-install.sh detect-all`. It prints one JSON line per tool, in
   order. Each line looks like
   `{"tool":"<name>","result":{"status":"configured|found|missing", ...}}`.
   - `configured`: config already has a valid path and the binary responds to its smoke check.
   - `found`: a likely install was detected on disk or in `PATH` but isn't in the config yet.
   - `missing`: nothing detected.

2. For each tool in the order printed, present an `AskUserQuestion`:

   ```
   <Tool> status: <STATUS>

     1. Keep current config               [only if status=configured]
     2. Use detected install at <path>    [only if status=found]
     3. I'll paste a path
     4. Install for me
     5. Skip (demo features requiring <Tool> will be unavailable)
   ```

   Options 1 and 2 are mutually exclusive (whichever matches the current
   status). Always offer 3-5.

   Wolfram is special-cased. When the per-tool loop reaches `wolfram`, render Section 2 menu variants from `## Wolfram walkthrough`:
   - `configured` → no prompt; print `✅ Wolfram Engine configured (v{version}, {path})` and continue.
   - `found` → menu variant (A) — 5 options including "Use this install" and "Walk me through a fresh install".
   - `missing` → menu variant (B) — 4 options including "Walk me through it now".

3. Dispatch per answer:
   - Keep current → no-op, move to next tool.
   - Use detected → `scripts/demo-install.sh use-path <tool> <path>`.
   - Paste a path → prompt the user, then `scripts/demo-install.sh use-path <tool> <path>`.
   - Install for me → `scripts/demo-install.sh install <tool> [dir]` with the tool's default dir unless the user overrides.
     - for `wolfram` → enter `## Wolfram walkthrough` (Phase 1 then Phase 2); do NOT call `scripts/demo-install.sh install wolfram` directly. For other tools, behavior unchanged.
   - Skip → record nothing; continue. At the end, warn which downstream `/demo` features are blocked.

   When Wolfram has been deferred (Section 5), do NOT route `sarah` into 'Install for me' — SARAH's installer will exit 20. Offer only the defer path for SARAH until Wolfram is resolved.

4. After all four tools have been offered, run `scripts/demo-install.sh python-deps`
   to enforce that `matplotlib` and `numpy` are importable in the configured
   Python (`config.python`). See `## Python plotting deps` below. Fail loudly
   if the pip install can't succeed — `/hep-plot` would otherwise crash at
   first use.

5. After python-deps succeeds, run `scripts/demo-install.sh validate`
   (wraps `check_config.py`). Report the per-tool pass/fail table and the
   final config path. `check_config.py` now delegates to `install_<tool>.sh verify`; run `install_<tool>.sh verify --path <p>` for per-tool diagnostics.

## Per-tool detection and install

### 1. Wolfram Engine (manual)

- **Detect**: `/Applications/Wolfram.app/...`, `/Applications/Wolfram Engine.app/...`, `/Applications/Mathematica.app/...` (Mathematica ships `wolframscript`), `/usr/local/bin/wolframscript`, `/usr/local/Wolfram/WolframEngine/*/Executables/wolframscript`, and `command -v wolframscript`.
- **Smoke test**: `wolframscript -code '2+2'` → `4`.
- **Auto-install**: Not possible to automate (activation requires a browser and a free Wolfram ID). See `## Wolfram walkthrough` below for the interactive flow. Running `install_wolfram.sh install` directly prints a short pointer and exits 0.
- **Error branches**: activation servers unreachable → suggest skipping for now and rerunning `/install --tool wolfram` when back online; binary exists but `2+2` does not return `4` → probably unactivated, print `wolframscript --activate` hint.

### 2. SARAH (Mathematica package)

- **Detect**: look for `SARAH.m` under `~/SARAH`, `~/software/SARAH`, `/usr/local/SARAH` (direct or one level deep, e.g. `~/SARAH/SARAH-4.15.3/SARAH.m`). The recorded `sarah_path` is the **package directory** (the one containing `SARAH.m`), not a binary.
- **Smoke test**: `wolframscript -code '<<SARAH\`; Print[SARAH\`SA\`Version]'` → version string.
- **Auto-install**: download the tarball to `/tmp`, extract under the chosen install dir (default `~/SARAH`), create a `SARAH-current` symlink pointing at the versioned dir, and register the parent dir in Wolfram's user `init.m` (`~/Library/Wolfram/Kernel/init.m` on macOS, `~/.WolframEngine/Kernel/init.m` on Linux) so `<<SARAH\`` works from any `wolframscript` invocation. Guarded by a comment marker so the block is idempotent.
- **Precondition**: `wolfram_engine_path` must already be in the config. The script refuses to install otherwise.
- **Error branches**: `<<SARAH\`` loads but version probe empty → the script re-registers `$Path` once and retries; second failure aborts with a `$Path` diagnostic.

### 3. SPheno (Fortran build-from-source)

- **Detect**: `~/SPheno/bin/SPheno`, `~/software/SPheno/.../bin/SPheno`, `/usr/local/SPheno/.../bin/SPheno`, `command -v SPheno`.
- **Smoke test**: `SPheno` with no args → "Usage" / "input file" / "LesHouches" banner.
- **Auto-install**: download tarball, extract under the install dir, `cd SPheno-*; make` (5-10 min). Capture `make` output to `/tmp/spheno_make.log`. On success, record `<install_dir>/SPheno-<version>/bin/SPheno` in the config.
- **Error branches**: `gfortran` missing → per-OS install command; `make` fails and log contains `lapack` → `brew install lapack` / `apt install liblapack-dev` with a specific exit code ($EXIT_NO_LAPACK=25); other `make` failure → tail the log and tell the user to inspect `/tmp/spheno_make.log`.

### 4. MadGraph5_aMC@NLO (existing)

Flow unchanged from the previous version. See `scripts/install_mg5.sh` for
stage-by-stage error handling (gfortran check, disk check, download-with-retry,
SHA256 verify, extract + symlink, smoke-test `e+ e- > mu+ mu-`, atomic config
write). All helpers are now shared with the other three installers via
`scripts/_common.sh`.

## Wolfram walkthrough

### Bundle warning

**Heads up — this bundle needs Wolfram Engine**

Wolfram is free but requires **~15 minutes of manual setup** that can't be fully automated:

1. Create a free Wolfram ID (browser, ~2 min)
2. Download + install Wolfram Engine (~10 min, ~4 GB)
3. Run `wolframscript --activate` yourself and sign in (~1 min)

Without Wolfram, **{wolfram_dependents}** can't install either. You lose: new BSM Lagrangians, Feynman-rule generation, spectra for custom BSM models{, and beyond-Boltzmann DM if DRAKE is in your bundle}. You keep: SPheno on built-in models (MSSM spectra, Higgs/neutralino masses, branching ratios) and MadGraph on pre-shipped UFO models (cross sections).

How do you want to handle Wolfram?

1. **Walk me through it now** — I'll guide you step-by-step and verify each step
2. **I've already got Wolfram set up** — I'll detect it
3. **I'll do it myself offline, continue without it** — install the non-Wolfram tools now, come back later
4. **Pause the whole install** — I'll come back when I have time

**DRAKE-conditional rendering rule.** The `{, and beyond-Boltzmann DM if DRAKE is in your bundle}` clause renders iff `drake ∈ tools` from the bundle-preflight output. When `drake` is not in `tools`, that entire curly-brace clause is omitted — the sentence ends with `spectra for custom BSM models.` (period added).

**Routing:**
- Option 1 → Section 3 (walkthrough).
- Option 2 → run `install_wolfram.sh detect`. If `configured` → proceed to next tool. If `found` → auto-prompt "Use this path: `<path>`? (y/n)"; yes → `install_wolfram.sh use-path <path>`, no → Section 2 per-tool prompt. If `missing` → "Hm, I don't see it. Let me help you install it." → Section 3.
- Option 3 → Section 5 (defer, minimal demo).
- Option 4 → Section 5 (pause).

### Phase 1 of 2 — Download and install

OS detection:

```bash
bash -c '. "$(git rev-parse --show-toplevel 2>/dev/null || echo .)/plugins/shared/install-helpers/_common.sh" 2>/dev/null || . "$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"; os_name'
```

Result: `macos` | `linux` | `other`.

**macOS prose:**

> **Phase 1 of 2 — Download and install Wolfram Engine (~10 min)**
>
> 1. Open this link in your browser: **https://www.wolfram.com/engine/**
> 2. Click the big "Download" button. You'll be asked to sign in or create a free Wolfram ID — any email works. The form is a little long; you only have to fill the required fields.
> 3. When the download finishes, you'll have a file called something like `WolframEngine_14.1_MACOS.dmg`. Double-click it.
> 4. A window titled **"Wolfram Engine"** opens. On the left is a "Wolfram Engine" icon with an arrow pointing to an "Applications" folder shortcut. **Drag the Wolfram Engine icon onto the Applications folder.**
> 5. On the right side of the same window is a **`WolframScript.pkg`** icon. **Double-click it** to install the `wolframscript` command-line tool — click through the macOS installer prompts (accept defaults).
> 6. Tell me "done" when both steps are complete.

**Linux prose (replaces steps 3–4):**

> 3. You'll get a file like `WolframEngine_14.1_LINUX.sh`. Open a terminal in the download folder and run:
>    ```
>    sudo bash WolframEngine_14.1_LINUX.sh
>    ```
> 4. Accept the defaults (press Enter through the prompts). Installation takes a few minutes.
> 5. Tell me "done" when the installer finishes.

**"other" prose:** "I only have walkthrough text for macOS and Linux. For Windows/BSD/WSL, see the official guide at https://www.wolfram.com/engine/ — once installed, come back and pick 'I've already got it set up'."

**Verification after "done"** — Claude runs:

```bash
"$SCRIPT_DIR/install_wolfram.sh" detect
```

Interpretation:
- Output `{"status":"configured",...}` or `{"status":"found","path":"<path>"}` → Phase 1 success; announce detected path and proceed to Phase 2.
- Output `{"status":"missing"}` → Phase 1 failure branch.

**Phase 1 failure branches:**

| Signal | Claude's response |
|--------|-------------------|
| macOS, `/Applications/Wolfram.app` exists but binary not executable | "macOS is blocking Wolfram because it was downloaded from the web. Fix: open Finder, go to Applications, **right-click Wolfram.app and choose Open**. macOS will ask once; click Open. If that doesn't work, go to System Settings → Privacy & Security, scroll to 'Wolfram was blocked', and click Allow. Then tell me 'done' again." |
| macOS, no `/Applications/Wolfram.app` | "I don't see Wolfram.app in /Applications — it might still be in Downloads or on your Desktop. Want to drag it over and tell me 'done' again?" |
| Linux, no `wolframscript` found anywhere | "I scanned `/usr/local/bin`, `/usr/local/Wolfram/…`, `/opt/Wolfram/…`, `~/.local/Wolfram/…`, and `/usr/share/WolframEngine/…` but didn't find wolframscript. Can you run `which wolframscript` in your terminal and paste the path? If it's empty, the installer probably didn't complete — try re-running `sudo bash WolframEngine_…_LINUX.sh`." |
| Linux, `detect` finds a candidate but not at the typical location | "I found `wolframscript` at `<path>`. Does that look like the one you just installed (version 14.1)?" (y/n) |
| User says "I'm stuck on the signup form" | Offer to pause (Section 5 pause path). |

### Phase 2 of 2 — Activate and verify

> **Phase 2 of 2 — Activate Wolfram Engine (~3 min)**
>
> Wolfram needs a one-time activation using your Wolfram ID. The activation happens **in your terminal** — `wolframscript --activate` prompts for your Wolfram ID and password directly, so **you need to run it yourself** (I can't type into an interactive prompt).
>
> 1. Open your terminal (the same one where you ran the installer, or any terminal).
> 2. Run:
>    ```
>    wolframscript --activate
>    ```
> 3. You'll see a message like "The Wolfram Engine requires one-time activation on this computer" along with a link to `wolfram.com/engine/free-license` — that link is only needed if you don't already have a Wolfram ID, so you can ignore it (you created one in Phase 1).
> 4. At the `Wolfram ID:` prompt, type the email you used to create your Wolfram ID. At the `Password:` prompt, type your password (the terminal won't echo the characters as you type — that's normal).
> 5. You should see: `Wolfram Engine activated. See https://www.wolfram.com/wolframscript/ for more information.`
> 6. Tell me "done" once you see that activated message.

**Verification after "done"** — primary form:

```bash
"$SCRIPT_DIR/../../../shared/install-helpers/wolfram/check_wolfram_activation.sh"
```

If the relative path fails, use the fallback form (use the fallback if the relative path fails):

```bash
bash -c "$REPO/plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh"
```

**Interpretation of the returned JSON** (retry cadence: poll once more; if still failing attempt 2 wait 20s; attempt 3 ~60s total):

| JSON `status` | Claude's response |
|---------------|-------------------|
| `ok` | Proceed: run `install_wolfram.sh use-path <path>` to persist. Announce `✅ Wolfram Engine activated (v{version}, {path}). Continuing to SARAH…` |
| `activation_required` | Poll once more (re-run the check). If still `activation_required` on attempt 2, wait 20s and retry. If still failing on attempt 3 (~60s total): "Activation didn't register. Two things to try: (1) run `wolframscript --activate` again — sometimes the browser handoff drops. (2) If you're on a headless machine (SSH, no browser), you'll need the manual `mathpass` flow: https://support.wolfram.com/46072 — once that file is in `~/.WolframEngine/Licensing/mathpass`, tell me 'done' again. Otherwise, I can mark this skipped." |
| `error` | "Hmm, wolframscript returned an unexpected error: `<detail>`. If the message mentions 'License limit exceeded', go to https://account.wolfram.com, sign in, and deactivate an older machine; then tell me 'done' to retry. If it mentions 'could not connect', the activation server is unreachable — we can pause here and rerun `/install` later." |
| `missing` | "The wolframscript binary disappeared between Phase 1 and now. Let's re-run Phase 1 verification." → jump back to Section 3. |

## Deferred Wolfram path

> **OK — deferring Wolfram. Here's exactly what that means:**
>
> **Deferring Wolfram also defers {wolfram_dependents}** (they need the Wolfram kernel). What you lose:
>
> - Can't build custom BSM Lagrangians — no new physics models, no custom field content
> - Can't generate Feynman rules from a Lagrangian
> - Can't compute mass spectra for new BSM models (the SARAH → SPheno pipeline is blocked)
> - (If DRAKE is in your bundle) No beyond-Boltzmann dark matter — resonance funnels, Sommerfeld enhancement, early kinetic decoupling all need DRAKE
>
> **What you keep:**
>
> - SPheno on built-in models — MSSM, NMSSM, and other pre-packaged spectrum generators. You get real observables: Higgs masses, neutralino masses, branching ratios, LesHouches output.
> - MadGraph on pre-shipped UFO models — cross sections, parton-level events for SM / MSSM processes
>
> **Two choices:**
>
> 1. **Continue with the minimal demo** (SPheno + MadGraph). I'll confirm once ("OK, installing SPheno and MadGraph now, ~15 min, no questions until done — start?") then run them. When you're ready for the full BSM story, rerun `/install` — I'll pick up at Wolfram.
> 2. **Pause the whole bundle.** I'll leave your current state untouched. Rerun `/install` when you've activated Wolfram and I'll resume from where we left off.

**"Pause" semantics (concrete).** When the user picks pause:

1. Claude does NOT call any further install scripts.
2. Claude prints:

   > ⏸ Paused. Your config has: `{list of *_path keys currently set}`. To resume, run `/install` (same bundle works) — I'll re-detect everything and pick up where you left off.

3. The AskUserQuestion loop exits. No `validate` call, no bundle-completion summary.
4. On next `/install` invocation, the skill starts fresh at bundle selection. `detect-all` re-discovers state. No hidden resume-pointer.

**Final summary after minimal-demo path:**

> Installed: SPheno 4.0.5, MadGraph 3.5.6
> Deferred: Wolfram Engine, SARAH, {DRAKE if applicable}
>
> To unlock the full demo: rerun `/install` after activating Wolfram. I'll detect SPheno + MG5 are already there and only walk you through Wolfram + SARAH.

## Python plotting deps

`/hep-plot` (and the plotting steps of `/demo`) import `matplotlib` and
`numpy` from `config.python`. If either is missing, plotting dies silently
mid-run. `scripts/check_python_deps.py` closes that hole:

1. Resolves the interpreter: `--python`, else `config.python`, else
   `which python3`.
2. Probes `import matplotlib` and `import numpy` in that interpreter and
   records `__version__` for each.
3. If either is missing, runs `<python> -m pip install matplotlib>=3.8 numpy`
   (matplotlib floor pinned) and re-probes.
4. On success, merges `matplotlib_version`, `numpy_version`, and a
   `python_deps_checked_at` UTC ISO-8601 stamp into the shared config.
5. On failure — pip non-zero, or re-probe still missing — exits non-zero
   with a specific exit code (see `check_python_deps.py` docstring). Callers
   MUST NOT continue; the downstream `/hep-plot` invocation would crash.

Invoke via `scripts/demo-install.sh python-deps` as part of the bundle flow,
or directly with `scripts/check_python_deps.py [--python PATH] [--json]`.

## Config schema

```json
{
  "wolfram_engine_path": "/Applications/Wolfram.app/Contents/MacOS/wolframscript",
  "wolfram_engine_version": "14.1",
  "sarah_path": "/Users/you/SARAH/SARAH-4.15.3",
  "sarah_version": "4.15.3",
  "spheno_path": "/Users/you/SPheno/SPheno-4.0.5/bin/SPheno",
  "spheno_version": "4.0.5",
  "madgraph_path": "/Users/you/MG5_aMC/bin/mg5_aMC",
  "madgraph_version": "3.5.6",
  "last_configured": "2026-04-18T12:34:56Z",
  "python": "/usr/bin/python3",
  "matplotlib_version": "3.9.2",
  "numpy_version": "2.0.1",
  "python_deps_checked_at": "2026-04-22T21:25:00Z"
}
```

Every `*_path` key is optional (skipped tools leave their key absent). Every
successful install writes its key atomically via `_common.sh`'s `config_merge`
helper — other keys are preserved across per-tool runs.

## Validator (`check_config.py`)

`python3 scripts/check_config.py` (or `scripts/demo-install.sh validate`) loads the
config and runs the smoke check for each of the four tools. Prints one
`PASS`/`FAIL` line per tool plus the config path. The exit code is a bitfield
so callers can see which tools failed:

| Bit | Tool |
|-----|------|
| 1 | Wolfram Engine |
| 2 | SARAH |
| 4 | SPheno |
| 8 | MadGraph5_aMC@NLO |
| 16 | Config file missing / unreadable |
| 17 | Not configured (tool path absent from config) |
| 32 | Internal error |

Exit `0` means all four tools validated. Exit `3` means Wolfram and SARAH both
failed; exit `12` means SPheno and MG5 both failed. `/demo`'s preflight step
should abort on non-zero and re-invoke `/install`.

## File map

| Path | Description |
|------|-------------|
| `scripts/demo-install.sh` | Top-level orchestrator. `detect-all`, `detect <tool>`, `use-path <tool> <path>`, `install <tool> [dir]`, `validate`. |
| `scripts/_common.sh` | Shared bash helpers: `log` / `warn` / `err`, `check_disk`, `download_with_retry`, `verify_checksum` (placeholder-SHA256 warn-not-abort), `config_get`, `config_merge`. Sourced by every `install_*.sh`. |
| `scripts/install_wolfram.sh` | Detect-only / use-path. `install` prints manual instructions (activation cannot be automated). |
| `scripts/install_sarah.sh` | Detect + tarball install + Wolfram `$Path` registration. |
| `scripts/install_spheno.sh` | Detect + tarball + `make` build. LAPACK-aware diagnostics. |
| `scripts/install_mg5.sh` | Existing MG5 flow, refactored to source `_common.sh`. Backward-compatible subcommands. |
| `scripts/check_config.py` | Python validator. Exit code is a bitfield (see above). |
| `scripts/check_python_deps.py` | Enforces that `matplotlib` + `numpy` are importable in `config.python`; pip-installs if missing; writes versions + timestamp into the shared config. |
| `skill_env.yaml` | Pinned versions + source URLs + (placeholder) sha256s for all four tools. |

## Delegated installers

For tools outside the Demo bundle, this skill delegates to dedicated install
skills that write to the same shared config. Do not reimplement their logic
here.

| Tool | Skill | Plugin | Writes config keys |
|------|-------|--------|--------------------|
| MadDM | `/maddm-install` | `monte-carlo-tools` | `maddm_path`, `maddm_version` |
| micrOMEGAs | `/micromegas-install` | `monte-carlo-tools` | `micromegas_path`, `micromegas_version` |
| DRAKE | `/drake-install` | `monte-carlo-tools` | `drake_path`, `drake_version` |
| LoopTools | `/looptools-install` | `model-building` | `looptools_path`, `looptools_version`, `looptools_gfortran_version` |
| FeynRules | `/feynrules-install` | `model-building` | `feynrules_path`, `feynrules_version` |

## Pinned versions

| Tool | Version | Pinned in |
|------|---------|-----------|
| Wolfram Engine | 14.1 | `skill_env.yaml`, `install_wolfram.sh` |
| SARAH | 4.15.3 | `skill_env.yaml`, `install_sarah.sh` |
| SPheno | 4.0.5 | `skill_env.yaml`, `install_spheno.sh` |
| MadGraph5_aMC@NLO | 3.5.6 | `skill_env.yaml`, `install_mg5.sh` |
| MadDM | 3.2.13 | `/maddm-install` `skill_env.yaml` |
| micrOMEGAs | 6.2.3 | `/micromegas-install` `skill_env.yaml` |
| DRAKE | 1.0 | `/drake-install` `skill_env.yaml` |
| LoopTools | 2.16 | `/looptools-install` `skill_env.yaml` |
| FeynRules | 2.3.49 | `/feynrules-install` `skill_env.yaml` |

All four SHA256s are currently `TODO` placeholders. The shared
`verify_checksum` helper warns but does not abort on `TODO`, matching the
existing pre-v1 pattern. Before v1 release, compute each tarball's real
SHA256 and update both `skill_env.yaml` and the corresponding `install_*.sh`.
