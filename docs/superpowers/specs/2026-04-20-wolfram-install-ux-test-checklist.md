# Wolfram install UX — manual test checklist

**Date:** 2026-04-20
**Scope:** human QA paths that require a real Wolfram Engine install (or a deliberate absence of one). The automated test battery covers config-neutrality, bundle membership, and skill-section structure; these 5 paths cover everything else.

## Path 1: Walkthrough → success

Steps:
1. Invoke `/install` and select the `demo` bundle. Confirm the Section 1 warning appears: "Heads up — this bundle needs Wolfram Engine" with the 4-option menu (Walk me through it now / I've already got Wolfram set up / I'll do it myself offline / Pause the whole install).
2. Select option 1 ("Walk me through it now"). Confirm Phase 1 prose appears (macOS: download link + drag-to-Applications instructions; Linux: `sudo bash WolframEngine_14.1_LINUX.sh` instructions). Complete the download and drag/install step, then tell Claude "done".
3. Confirm Claude runs `install_wolfram.sh detect` and reports the detected path. Confirm Phase 2 prose appears: "Phase 2 of 2 — Activate Wolfram Engine (~3 min)" with instructions to run `wolframscript --activate` in a terminal.
4. Run `wolframscript --activate` in a terminal, sign in with a Wolfram ID in the browser, and tell Claude "done" once the browser says activated.
5. Confirm Claude runs `check_wolfram_activation.sh` and returns status `ok`. Confirm Claude announces `✅ Wolfram Engine activated (v{version}, {path}). Continuing to SARAH…` and proceeds to install SARAH.
6. After SARAH installs, run `wolframscript -code '1+1'` in a terminal and confirm it returns `2`.

Pass criteria: `wolframscript -code '1+1'` returns `2` and the session ends with SARAH successfully installed with no error summary.

## Path 2: Walkthrough → Phase 1 fail (no .app)

Steps:
1. Invoke `/install`, select the `demo` bundle, and choose option 1 ("Walk me through it now"). Download the Wolfram Engine installer DMG but deliberately drag `Wolfram.app` to the Desktop instead of `/Applications`.
2. Tell Claude "done" after the copy completes. Confirm Claude runs `install_wolfram.sh detect` and gets `missing` (because `/Applications/Wolfram.app` is absent).
3. Confirm Claude shows the Phase 1 failure branch for macOS (no `/Applications/Wolfram.app`): "I don't see Wolfram.app in /Applications — it might still be in Downloads or on your Desktop. Want to drag it over and tell me 'done' again?"
4. Drag `Wolfram.app` from the Desktop to `/Applications`. Tell Claude "done" again.
5. Confirm Claude re-runs `install_wolfram.sh detect`, now gets `found` or `configured`, announces the detected path, and proceeds to Phase 2.

Pass criteria: After the corrective drag, Claude re-detects the binary and advances to Phase 2 without requiring the user to restart the install.

## Path 3: Walkthrough → Phase 2 fail (activation stuck)

Steps:
1. Invoke `/install`, select the `demo` bundle, choose "Walk me through it now", and successfully complete Phase 1 (Wolfram.app installed in `/Applications`, detect returns `found`).
2. When Phase 2 prompts `wolframscript --activate`, run the command but do NOT complete the browser sign-in (leave the browser tab open and stalled, or close the browser before finishing).
3. Tell Claude "done". Confirm Claude runs `check_wolfram_activation.sh` and gets `activation_required`.
4. Confirm Claude polls once more immediately. Confirm that on attempt 2 Claude waits 20 seconds before retrying. Confirm that after ~60 seconds total (attempt 3) Claude shows the fallback message: "Activation didn't register. Two things to try: (1) run `wolframscript --activate` again… (2) If you're on a headless machine, you'll need the manual `mathpass` flow: https://support.wolfram.com/46072".
5. Complete the browser sign-in (or place the `mathpass` file at `~/.WolframEngine/Licensing/mathpass`). Tell Claude "done" again. Confirm Claude re-runs `check_wolfram_activation.sh` and now gets `ok`.

Pass criteria: The 20s/3-attempt poll cadence is observable (timed), the `mathpass` URL is surfaced verbatim, and success on a subsequent "done" resumes normal flow.

## Path 4: Defer → minimal demo

Steps:
1. Invoke `/install` and select the `demo` bundle. Confirm the Section 1 Wolfram warning appears with the 4-option menu.
2. Select option 3 ("I'll do it myself offline, continue without it"). Confirm the Section 5 defer block appears, listing the loss-of-functionality items: custom BSM Lagrangians, Feynman-rule generation, SARAH → SPheno pipeline, and the two "What you keep" items (SPheno on built-in models, MadGraph on pre-shipped UFO models).
3. Confirm the two-choice menu appears: "Continue with the minimal demo (SPheno + MadGraph)" and "Pause the whole bundle."
4. Select option 1 ("Continue with the minimal demo"). Confirm Claude asks exactly once: "OK, installing SPheno and MadGraph now, ~15 min, no questions until done — start?" and then runs both installs without further prompts.
5. Confirm the final summary appears verbatim: "Installed: SPheno 4.0.5, MadGraph 3.5.6 / Deferred: Wolfram Engine, SARAH" along with the re-run hint "To unlock the full demo: rerun `/install` after activating Wolfram."
6. Rerun `/install` (same `demo` bundle). Confirm `detect-all` re-discovers SPheno + MG5 as already installed and the skill offers only the Wolfram + SARAH portion.

Pass criteria: Final summary prints `Installed: SPheno 4.0.5, MadGraph 3.5.6` with the correct Deferred list, and a subsequent `/install` skips SPheno and MG5.

## Path 5: Defer → pause

Steps:
1. Invoke `/install` and select the `demo` bundle. Confirm the Section 1 Wolfram warning appears.
2. Select option 4 ("Pause the whole install"). Confirm the Section 5 defer block appears with the two-choice menu.
3. Select option 2 ("Pause the whole bundle"). Confirm Claude does NOT call any install scripts (no SPheno, no MG5, no Wolfram scripts run).
4. Confirm the pause confirmation block appears verbatim: "⏸ Paused. Your config has: `{list of *_path keys currently set}`. To resume, run `/install` (same bundle works) — I'll re-detect everything and pick up where you left off."
5. Inspect the config directory (e.g., `$XDG_CONFIG_HOME/hep-ph-agents/`) and confirm no new config keys were written as a result of this session.
6. Rerun `/install` with the same `demo` bundle. Confirm the skill starts fresh at bundle selection, `detect-all` re-runs, and the prior pause state has no hidden resume-pointer effect.

Pass criteria: The `⏸ Paused.` block is printed verbatim, the config is unchanged from before the session, and the follow-up `/install` presents a clean bundle-selection prompt.
