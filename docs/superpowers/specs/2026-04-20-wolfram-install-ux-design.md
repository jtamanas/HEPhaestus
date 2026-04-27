# Wolfram Engine install UX — design

**Date:** 2026-04-20
**Scope:** `plugins/hep-ph-toolkit/skills/install/` — how the `/install` skill handles Wolfram Engine, whose activation cannot be automated and requires a browser + free Wolfram ID.

## Problem

When the user runs `/install` and picks the Demo bundle (or any bundle containing Wolfram), the current flow presents a generic 5-option menu with an "Install for me" option. Choosing it invokes `install_wolfram.sh install`, which prints a multi-step instruction block to stderr and exits with code 20. The agent sees this as an error and responds with a passive summary ("Wolfram needs you to do 3 manual steps, I can keep going…") that neither walks the user through the steps nor sets expectations beforehand.

The target audience is tech-illiterate. "Drag Wolfram.app into /Applications" is not always trivial for them. Framing a walkthrough as an error is actively harmful.

## Goals

1. Warn the user **before** they commit to a Wolfram-requiring bundle that manual steps are needed.
2. Offer **two defer paths** on both the bundle screen and the per-tool screen:
   - "I'll set it up myself later, skip for now"
   - "Pause the whole install"
3. When the user picks "walk me through it", hand-hold in **two phases with verification between them**.
4. When the user defers, be **very explicit** about what functionality is lost — and still offer a **runnable minimal demo** (SPheno + MG5) so they see something work.

## Non-goals

- Automating Wolfram activation. It requires a browser-based Wolfram ID sign-in and cannot be scripted.
- Expanding the Demo bundle to add MadDM or other DM tools.
- Changing the config schema.
- Building new validator logic in `check_config.py` — existing detection already handles resumability.

---

## Design

### Section 1 — Bundle-picker warning

When the user picks a bundle that contains Wolfram (Demo, BSM→spectrum, Narrow-resonance DM), before starting the per-tool loop, the skill shows:

> **Heads up — this bundle needs Wolfram Engine**
>
> Wolfram is free but requires **~15 minutes of manual setup** that can't be automated:
>
> 1. Create a free Wolfram ID (browser, ~2 min)
> 2. Download + install Wolfram Engine (~10 min, ~4 GB)
> 3. Run `wolframscript --activate` and log in (~1 min)
>
> Without Wolfram, **SARAH** and **DRAKE** can't install either — meaning we can't build new BSM Lagrangians, generate Feynman rules, compute spectra for custom BSM models, or handle resonance/Sommerfeld-enhanced dark-matter regimes. You'd still be able to run SPheno on built-in models (MSSM spectra, Higgs/neutralino masses, branching ratios) and run MadGraph on pre-shipped UFO models (cross sections).
>
> How do you want to handle Wolfram?
>
> 1. **Walk me through it now** — I'll guide you step-by-step and check each step
> 2. **I've already got Wolfram set up** — I'll detect it
> 3. **I'll do it myself offline, continue without it** — install the non-Wolfram tools now, come back later
> 4. **Pause the whole install** — I'll come back when I have time

Options 3 and 4 route to the defer path (Section 5). Option 1 routes to Section 3. Option 2 short-circuits to the normal `detect` → `use-path` flow.

### Section 2 — Per-tool Wolfram prompt

When the per-tool loop reaches Wolfram and the status is `missing`:

> **Wolfram Engine — not installed**
>
> Free, but requires manual activation (no bot can click "I agree" for you). How do you want to handle it?
>
> 1. **Walk me through it now** (~15 min, I'll verify each step)
> 2. **I've already installed it — let me paste the path**
> 3. **I'll set it up myself later** — skip for now, rerun `/install` when ready
> 4. **Skip the whole Wolfram-dependent part of this bundle** — continue with SPheno + MG5 only

If status is `found` (binary detected but not in config), add a "use detected install at `<path>`" option at the top. If status is `configured`, skip the prompt entirely.

### Section 3 — Walkthrough Phase 1 (download + install)

Claude detects OS via `uname -s` and shows only the relevant instructions.

**macOS version:**

> **Phase 1 of 2 — Download and install Wolfram Engine (~10 min)**
>
> 1. Open this link in your browser: **https://www.wolfram.com/engine/**
> 2. Click the big "Download" button. You'll be asked to sign in or create a free Wolfram ID — use any email. The form is a little long; you only have to fill the required fields.
> 3. When the download finishes, you'll have a file called something like `WolframEngine_14.1_MACOS.dmg`. Double-click it.
> 4. A window opens with a "Wolfram.app" icon and an arrow pointing to an "Applications" folder shortcut. **Drag Wolfram.app onto the Applications folder.**
> 5. Reply "done" here when the app has finished copying.

**Linux version** (replaces steps 3–4):

> 3. You'll get a file like `WolframEngine_14.1_LINUX.sh`. Open a terminal in the download folder and run:
>    ```
>    sudo bash WolframEngine_14.1_LINUX.sh
>    ```
> 4. Accept the defaults (press Enter through the prompts). Installation takes a few minutes.

**Verification after "done":**

```bash
# macOS
test -x "/Applications/Wolfram.app/Contents/MacOS/wolframscript" && echo OK

# Linux
command -v wolframscript && echo OK
```

**Failure branches:**

- Not in Applications (macOS) → "I don't see Wolfram.app in /Applications. Did it end up on your Desktop or in Downloads? Drag it to Applications and tell me 'done' again."
- `wolframscript` not on PATH (Linux) → Claude himself runs `which wolframscript` and scans `/usr/local/Wolfram/WolframEngine/*/Executables/`. If a candidate is found, he asks: "I found `wolframscript` at `<path>` — does that look like the one you just installed? (version 14.1)". Only if nothing is found does he ask the user to look around.
- "I'm stuck on the Wolfram signup form" → offer to pause; user can resume later via `/install`.

### Section 4 — Walkthrough Phase 2 (activate + verify)

After Phase 1 verification passes:

> **Phase 2 of 2 — Activate Wolfram Engine (~3 min)**
>
> Wolfram needs a one-time activation using your Wolfram ID. I'll run the activation command for you.
>
> Running: `wolframscript --activate`
>
> This will open a browser window asking you to sign in with the same Wolfram ID you just created. After you sign in, the browser will say "Wolfram Engine activated" and the terminal will return.
>
> Tell me "done" once the browser says activated.

Claude runs `wolframscript --activate` via Bash. After the user reports done, Claude verifies:

```bash
wolframscript -code '2+2'
# Expected: 4
```

On success, Claude calls `install_wolfram.sh use-path <detected-path>` to persist to config, then:

> ✅ **Wolfram Engine activated** (version 14.1, path: `<path>`)
> Continuing to SARAH…

**Failure branches:**

- `2+2` ≠ `4` → "Activation didn't fully complete. Let's re-run `wolframscript --activate`. If the browser says 'already activated', try signing out of Wolfram ID in the browser and back in."
- "Could not connect to Wolfram activation servers" → pause with instruction to rerun `/install` once connectivity is back.
- "License limit exceeded" → direct user to https://account.wolfram.com to deactivate an older machine, then retry.
- `wolframscript: command not found` → re-run Phase 1 verification before retrying activation.

### Section 5 — Defer path + minimal demo pivot

Triggered when the user picks a defer option at either the bundle screen or the per-tool screen.

**Pivot message:**

> **OK — deferring Wolfram. Here's exactly what that means:**
>
> **Deferring Wolfram also defers SARAH and DRAKE** (they need the Wolfram kernel). What you lose:
>
> - ❌ **Can't build custom BSM Lagrangians** — no new physics models, no custom field content
> - ❌ **Can't generate Feynman rules** from a Lagrangian
> - ❌ **Can't compute mass spectra for new BSM models** (the SARAH → SPheno pipeline is blocked)
> - ❌ **No beyond-Boltzmann dark matter** — resonance funnels, Sommerfeld enhancement, early kinetic decoupling all need DRAKE
>
> **What you keep:**
>
> - ✅ **SPheno on built-in models** — MSSM, NMSSM, and other pre-packaged spectrum generators. You get real observables: Higgs masses, neutralino masses, branching ratios, LesHouches output.
> - ✅ **MadGraph on pre-shipped UFO models** — cross sections, parton-level events for SM / MSSM processes
>
> **Two choices:**
>
> 1. **Continue with the minimal demo** (SPheno + MadGraph). I'll install those now (~15 min) and walk you through computing an MSSM spectrum + an LHC cross section at the end. When you're ready for the full BSM story, come back and run `/install` — I'll pick up at Wolfram.
> 2. **Pause the whole bundle.** I'll leave your current state untouched. Rerun `/install` when you've activated Wolfram and I'll resume from where we left off.

**State tracking:** no config schema changes. On rerun, the existing `detect-all` flow sees Wolfram as `missing`, SARAH refuses to auto-install without `wolfram_engine_path` (existing precondition), SPheno and MG5 show as `configured`. The skill simply re-reads current state.

**Final summary after minimal-demo path:**

> ✅ **Installed:** SPheno 4.0.5, MadGraph 3.5.6
> ⏸️ **Deferred:** Wolfram Engine, SARAH, DRAKE
>
> To unlock the full demo: rerun `/install` after activating Wolfram. I'll detect SPheno + MG5 are already there and only walk you through Wolfram + SARAH.
>
> Ready to run the minimal demo? I can compute an MSSM spectrum and an LHC cross section for you right now.

---

## Concrete file changes

### `plugins/hep-ph-toolkit/skills/install/SKILL.md`

Rewrite the Flow section:

- **New step 0: "Bundle-level Wolfram warning"** before the detect-all loop. Fires only when the selected bundle contains Wolfram. Contains the Section 1 prompt text.
- **Rewrite the per-tool Wolfram branch inside step 2** to use the 4-option menu from Section 2 (instead of the generic 5-option menu used for other tools).
- **New subsection "Wolfram walkthrough"** — the Phase 1 / Phase 2 scripts (Sections 3 + 4) with OS-detection instructions for Claude.
- **New subsection "Deferred Wolfram path"** — the pivot message + minimal-demo summary (Section 5).
- The existing "Per-tool detection and install §1 Wolfram Engine" block stays (it documents the script). A pointer is added to the new sections.

### `plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh`

Soften `cmd_install`:

- **Today:** prints instructions to stderr, exits 20 (`$EXIT_NO_WOLFRAM`). Framed as an error.
- **New:** prints a short pointer to stdout, exits 0. Body becomes:
  ```
  Wolfram Engine activation can't be automated — needs a browser.
  The /install skill walks you through it interactively. If you're
  running this script directly, see SKILL.md §"Wolfram walkthrough".
  ```
- `$EXIT_NO_WOLFRAM` stays reserved for genuine errors (e.g. `install` called with conflicting args).
- No new subcommands — the walkthrough is Claude's chat behavior, not script behavior. Script's job remains: `detect`, `use-path`, `install` (now informational).

### `plugins/hep-ph-toolkit/skills/install/scripts/demo-install.sh`

One new subcommand: `bundle-preflight <bundle>` that prints JSON listing whether the bundle contains Wolfram, SARAH, and/or DRAKE. The skill uses this to decide whether to show the Section 1 warning. Avoids hardcoding bundle contents in two places.

### No changes

- `check_config.py` — existing detection + bitfield exit code already handle resumability.
- `_common.sh`, `skill_env.yaml`, and the other `install_*.sh` scripts — untouched.

---

## Decisions recorded

| Question | Decision |
|----------|----------|
| Where to warn about manual Wolfram steps | Both the bundle-picker screen and the per-tool screen |
| Walkthrough granularity | 2 phases (download+install, activate+verify), with a verification check between them |
| Who runs `which wolframscript` on Linux failure | Claude, not the user; confirms with the user if a path is found |
| "Done" vs "tell me 'done'" | "tell me 'done' again" — consistent conversational voice |
| What happens to SARAH / DRAKE when Wolfram is deferred | Auto-deferred; user sees explicit loss-of-functionality bullets, then chooses minimal demo vs pause-entire-bundle |
| Minimal-demo scope | SPheno + MadGraph (option A=2). Does not pull in MadDM. |
| State tracking for resumability | None. Existing `detect-all` flow already handles it via live detection. |

## Open questions

None at design time. Implementation plan will handle:

- Exact OS-detection snippet (macOS vs Linux vs "something else" fallback).
- Exact text of the `bundle-preflight` JSON output.
- Whether to add a smoke test for the minimal-demo path (run SPheno on a sample MSSM input as part of the install verification).
