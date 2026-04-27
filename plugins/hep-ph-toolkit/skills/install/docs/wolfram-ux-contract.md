# Wolfram Engine install UX — shared contract

**Date:** 2026-04-20
**Status:** locked. Authoritative source for all Wolfram-related user-facing prose, JSON shapes, and error strings. Referenced by `demo-install.sh` and `SKILL.md`. Do not paraphrase — copy verbatim.

---

## bundle-preflight-schema {#bundle-preflight-schema}

JSON shape emitted on stdout by `demo-install.sh bundle-preflight <bundle-id>` (exit 0, single line):

```json
{"bundle":"demo","tools":["wolfram","sarah","spheno","mg5"],"requires_wolfram":true,"wolfram_dependents":["sarah"]}
```

Key definitions:

- `bundle` (string): the canonical bundle-id (lowercased).
- `tools` (array of strings): ordered list of tool keys that the bundle installs.
- `requires_wolfram` (bool): true iff `wolfram` OR any of {`sarah`, `drake`, `feynrules`, `formcalc`, `feynarts`} is in `tools`.
- `wolfram_dependents` (array of strings): tools in this bundle that would be blocked BY missing Wolfram, excluding wolfram itself.

---

## bundle-preflight-truth-table {#bundle-preflight-truth-table}

Hardcoded truth table (drop into `demo-install.sh`):

```bash
declare -A BUNDLES=(
  [demo]="wolfram sarah spheno mg5"
  [bsm-spectrum]="wolfram sarah spheno"         # feynrules optional, not included by default
  [dm-relic]="mg5 maddm micromegas"
  [dm-narrow-resonance]="mg5 maddm micromegas drake"
  [one-loop]="looptools"
)

WOLFRAM_BLOCKERS=(wolfram sarah drake feynrules formcalc feynarts)
```

Note: `bsm-spectrum` intentionally omits `feynrules` (optional). The `wolfram_dependents` for `bsm-spectrum` is `["sarah"]`, NOT `["sarah","feynrules"]`.

---

## bundle-preflight-error-codes {#bundle-preflight-error-codes}

Exit-code table:

| Exit code | Condition |
|-----------|-----------|
| 0 | Success — valid bundle-id, JSON emitted to stdout |
| 2 | Usage error: unknown bundle-id, empty string, whitespace-only, or no args |

On exit 2, the error JSON is emitted to **stderr**:

```
{"error":"unknown bundle: <id>","known":["demo","bsm-spectrum","dm-relic","dm-narrow-resonance","one-loop"]}
```

Note: this string NEVER appears in SKILL.md. It is an internal script error, not user-facing prose.

---

## prompt-section1-warning {#prompt-section1-warning}

**Verbatim prompt text for Section 1 — Bundle-picker warning.**

Trigger: after the user selects a bundle, `scripts/demo-install.sh bundle-preflight <id>` returns `requires_wolfram: true`.

> **Heads up — this bundle needs Wolfram Engine**
>
> Wolfram is free but requires **~15 minutes of manual setup** that can't be fully automated:
>
> 1. Create a free Wolfram ID (browser, ~2 min)
> 2. Download + install Wolfram Engine (~10 min, ~4 GB)
> 3. Run `wolframscript --activate` yourself and sign in (~1 min)
>
> Without Wolfram, **{wolfram_dependents}** can't install either. You lose: new BSM Lagrangians, Feynman-rule generation, spectra for custom BSM models{, and beyond-Boltzmann DM if DRAKE is in your bundle}. You keep: SPheno on built-in models (MSSM spectra, Higgs/neutralino masses, branching ratios) and MadGraph on pre-shipped UFO models (cross sections).
>
> How do you want to handle Wolfram?
>
> 1. **Walk me through it now** — I'll guide you step-by-step and verify each step
> 2. **I've already got Wolfram set up** — I'll detect it
> 3. **I'll do it myself offline, continue without it** — install the non-Wolfram tools now, come back later
> 4. **Pause the whole install** — I'll come back when I have time

**DRAKE-conditional rendering rule.** The clause `{, and beyond-Boltzmann DM if DRAKE is in your bundle}` (including the leading comma and space) is rendered iff `drake` is an element of the `tools` array from `bundle-preflight`. When `drake` is not in `tools`, that entire curly-brace clause is omitted — the sentence ends with `spectra for custom BSM models.` (period added). This rule applies wherever that sentence appears.

**Routing:**
- Option 1 → Section 3 (walkthrough).
- Option 2 → run `install_wolfram.sh detect`. If `configured` → proceed to next tool. If `found` → auto-prompt "Use this path: `<path>`? (y/n)"; yes → `install_wolfram.sh use-path <path>`, no → Section 2 per-tool prompt. If `missing` → "Hm, I don't see it. Let me help you install it." → Section 3.
- Option 3 → Section 5 (defer, minimal demo).
- Option 4 → Section 5 (pause).

---

## prompt-section2-menus {#prompt-section2-menus}

**Verbatim Section 2 — Per-tool Wolfram prompt.**

Status dispatch:

- `configured` → no prompt; print `✅ Wolfram Engine configured (v{version}, {path})` and move on.
- `found` → show menu variant (A) below.
- `missing` → show menu variant (B) below.

**Menu variant (A) — status=`found`:**

> **Wolfram Engine — detected but not registered**
>
> Found `wolframscript` at `<path>`. How do you want to handle it?
>
> 1. **Use this install** — register it in the config (recommended)
> 2. **Walk me through a fresh install** (~15 min, I'll verify each step)
> 3. **I'll paste a different path** — if you have another install
> 4. **I'll set it up myself later** — skip for now, rerun `/install` when ready
> 5. **Skip the whole Wolfram-dependent part of this bundle** — continue with non-Wolfram tools only

**Menu variant (B) — status=`missing`:**

> **Wolfram Engine — not installed**
>
> Free, but requires manual activation (no bot can click "I agree" for you). How do you want to handle it?
>
> 1. **Walk me through it now** (~15 min, I'll verify each step)
> 2. **I've already installed it — let me paste the path**
> 3. **I'll set it up myself later** — skip for now, rerun `/install` when ready
> 4. **Skip the whole Wolfram-dependent part of this bundle** — continue with non-Wolfram tools only

---

## prompt-phase1 {#prompt-phase1}

**Verbatim Section 3 — Walkthrough Phase 1 (download + install).**

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

---

## prompt-phase2 {#prompt-phase2}

**Verbatim Section 4 — Walkthrough Phase 2 (activate + verify).**

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

If the relative path fails, use the fallback form:

```bash
bash -c "$REPO/plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh"
```

**Interpretation of the returned JSON** (retry cadence: poll once more; if still failing attempt 2 wait 20s; attempt 3 ~60s total)**:**

| JSON `status` | Claude's response |
|---------------|-------------------|
| `ok` | Proceed: run `install_wolfram.sh use-path <path>` to persist. Announce `✅ Wolfram Engine activated (v{version}, {path}). Continuing to SARAH…` |
| `activation_required` | Poll once more (re-run the check). If still `activation_required` on attempt 2, wait 20s and retry. If still failing on attempt 3 (~60s total): "Activation didn't register. Two things to try: (1) run `wolframscript --activate` again — sometimes the browser handoff drops. (2) If you're on a headless machine (SSH, no browser), you'll need the manual `mathpass` flow: https://support.wolfram.com/46072 — once that file is in `~/.WolframEngine/Licensing/mathpass`, tell me 'done' again. Otherwise, I can mark this skipped." |
| `error` | "Hmm, wolframscript returned an unexpected error: `<detail>`. If the message mentions 'License limit exceeded', go to https://account.wolfram.com, sign in, and deactivate an older machine; then tell me 'done' to retry. If it mentions 'could not connect', the activation server is unreachable — we can pause here and rerun `/install` later." |
| `missing` | "The wolframscript binary disappeared between Phase 1 and now. Let's re-run Phase 1 verification." → jump back to Section 3. |

---

## prompt-section5 {#prompt-section5}

**Verbatim Section 5 — Defer path + minimal demo pivot.**

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

(No "Ready to run the minimal demo?" close — `/demo` owns that handoff.)

---

## helper-invocations {#helper-invocations}

**Exact invocation forms for helper scripts.**

**`install_wolfram.sh` detect — three-way routing:**

```bash
"$SCRIPT_DIR/install_wolfram.sh" detect
```

Output routing: `configured` | `found` | `missing`.

**`check_wolfram_activation.sh` — primary form:**

```bash
"$SCRIPT_DIR/../../../shared/install-helpers/wolfram/check_wolfram_activation.sh"
```

**`check_wolfram_activation.sh` — fallback form** (used when the relative path from `SCRIPT_DIR` fails):

```bash
bash -c "$REPO/plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh"
```

**OS-detect one-liner:**

```bash
bash -c '. "$(git rev-parse --show-toplevel 2>/dev/null || echo .)/plugins/shared/install-helpers/_common.sh" 2>/dev/null || . "$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"; os_name'
```

Result: `macos` | `linux` | `other`.

---

## Verify acceptance

The `install_wolfram.sh verify` subcommand is the final gate confirming a Wolfram Engine install is functional. After `use-path` succeeds, the following steps constitute acceptance:

1. Run `install_wolfram.sh use-path /path/to/wolframscript`.
2. Run `install_wolfram.sh verify --path <path> --json` and verify `ok:true`.
3. Deactivate wolframscript; rerun verify; assert `status:"installed_broken"` and `hints[0].code == "wolfram_not_activated"`.
