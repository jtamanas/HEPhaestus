# Install Skill Refactor — Design

**Date:** 2026-04-28
**Status:** Implemented (2026-04-29 — see [implementation plan](../plans/2026-04-29-install-skill-refactor.md))
**Owner:** yianni

## Problem

The toolkit has 11 standalone install skills — `ddcalc-install`, `drake-install`, `feynarts-install`, `feynrules-install`, `formcalc-install`, `higgstools-install`, `looptools-install`, `maddm-install`, `micromegas-install`, `sarah-install`, `spheno-install` — plus a top-level `install` meta-skill that dispatches to them.

Today's pattern: a runner skill (e.g. `sarah-build`) discovers a tool is missing, halts, and tells the user to invoke `/sarah-install`. `lagrangian-builder` goes further — it runs its own preflight (`scripts/check_state.py`) and orchestrates `/sarah-install` and `/spheno-install` as sub-skills, including the Wolfram activation handoff (`lagrangian-builder/SKILL.md` lines 78, 162, 170, 179–193, 736–738, 807–832).

Costs of this shape:
- Every consumer of a tool re-implements the install-state probe and sub-skill orchestration.
- Install knowledge is duplicated across `*-install/SKILL.md` and the consumer skills' error tables.
- Adding a new consumer of SARAH (or any tool) means wiring up sub-skill orchestration again.
- Users have to learn a separate vocabulary of `/sarah-install`, `/spheno-install`, etc., when conceptually they just want "use SARAH."

## Goal

Collapse the 11 install skills into shared install references plus self-healing runner skills. A consumer skill (e.g. `lagrangian-builder`) calls a runner (e.g. `sarah-build`); the runner does its own preflight and, if the tool is missing, walks through the install using a shared reference. No consumer skill carries install logic.

## Non-goals

- Not changing install script behavior for tools that already have a clean detect/install split. Most existing `install.sh` scripts move verbatim.
- Not changing the config schema or the `~/.config/hephaestus/config.toml` paths.
- Not touching `plugins/shared/install-helpers/` (cross-plugin atomic-write / config helpers).

**Caveat on "relocation only."** Three tools need genuinely new `detect.sh` work, not a trivial extraction:
- **SARAH** — detection today is split across `install_sarah.sh`, `detect_wolfram.sh`, `check_wolfram_activation.sh`, and `_activation_parse.py`, returning `configured | found | missing | activation_required`. The new `detect.sh` must compose config-read + Wolfram reachability + version probe + activation parse into one exit code.
- **DRAKE** — install includes a hepforge Anubis bot-protection gate (`manual_download_required`, exit 18). The runner cannot self-heal this; preflight must surface the manual-download path and halt rather than silently retrying.
- **MadDM** — install delegates to `MG5_aMC>install maddm`, which is itself an interactive multi-minute build. Preflight on first runner invocation triggers a long, visible operation by design (see "Self-healing UX contract" below).

## Design

### 1. Layout

```
plugins/hep-ph-toolkit/
├── _shared/
│   └── installs/
│       ├── sarah/
│       │   ├── INSTALL.md
│       │   ├── detect.sh
│       │   ├── install.sh
│       │   ├── _activation_parse.py
│       │   ├── check_wolfram_activation.sh
│       │   └── tests/
│       ├── spheno/
│       ├── maddm/
│       ├── micromegas/
│       ├── formcalc/
│       ├── feynarts/
│       ├── feynrules/
│       ├── looptools/
│       ├── ddcalc/
│       ├── higgstools/
│       └── drake/
└── skills/
    ├── sarah-build/                # gains preflight at top
    ├── maddm/                      # gains preflight at top
    ├── micromegas/                 # gains preflight at top
    ├── formcalc/                   # gains preflight at top
    ├── feynarts/                   # gains preflight at top
    ├── ddcalc/                     # gains preflight at top
    ├── higgstools/                 # gains preflight at top
    ├── drake/                      # gains preflight at top
    ├── lagrangian-builder/         # ignorant of installs; just invokes /sarah-build, /spheno-build
    ├── install/                    # rewritten as bundle front door (see §4)
    └── … (all 11 *-install skill directories deleted)
```

Two locations carry install knowledge, with a clean split:

1. **`_shared/installs/<tool>/`** — *what to install and how.* Reference doc plus scripts.
2. **Runner skill** (e.g. `sarah-build`) — *that* it depends on the tool, and where to find the reference. Does not carry install steps inline.

**Tools without a current runner.** Of the 11 install targets, **FeynRules has no runner skill today** — it is only referenced by `/install` and `_shared/constraints.yaml`. Under this design, `_shared/installs/feynrules/` still exists and is reachable via `/install feynrules` and `/install bsm-model-building`. No preflight wiring is added until a runner that depends on FeynRules exists (anticipated when `lagrangian-builder` is rebuilt as a SARAH/FeynRules interface — out of scope for this refactor).

This is a transitional carve-out, not a competing architecture. The design still says "runners self-heal." FeynRules simply has no runner *yet* to attach a preflight to. When the rebuilt `lagrangian-builder` lands, it will preflight FeynRules the same way `sarah-build` preflights SARAH.

### 2. Preflight contract

Each runner skill that depends on a tool gets a uniform preflight block at the top of its `SKILL.md`:

```markdown
## Preflight

Before any other action, run:

    bash _shared/installs/sarah/detect.sh

- **exit 0** → SARAH is installed and registered in config; proceed.
- **exit non-zero** → SARAH is missing or misconfigured. Load
  `_shared/installs/sarah/INSTALL.md` into context and follow it. When
  the install completes (or returns `activation_required`), re-run
  `detect.sh` before proceeding. If it still fails, halt with the
  blocker code from the install reference.
```

#### `detect.sh` contract

- The single source of truth for "is this tool ready."
- Two-tier check, fast path first:
  1. **Config fast path** — read `~/.config/hephaestus/config.toml`; if the tool is registered, the binary path exists, and the config's recorded version matches the current `INSTALL.md` version pin, exit 0 immediately. Cost: ~5 ms.
  2. **Binary probe (slow path)** — only run when the fast path misses (config absent, version drift, or `HEPPH_FORCE_PROBE=1`). E.g. `sarah --version`, Wolfram kernel handshake. Cold Wolfram boot is 2–6 s; reserve this for first-invocation-per-session or post-install verification.
- Exit 0 = ready; exit non-zero = not ready. The runner does not need to know which.
- Reusable: `/install` (the bundle skill, §4) calls the same `detect.sh`.

#### Cache & version hygiene

Self-healing runners only work if the install state recorded in config tracks reality. The fast path above pins on `version`; whenever `INSTALL.md` bumps a tool's pinned version, `detect.sh` falls through to the slow path on the next run, and `install.sh` is responsible for:

- Removing or migrating the previous install tree (e.g. `~/.hephaestus/sarah-4.15.x` → `sarah-4.16.x`), not stacking versions silently.
- Rewriting any `init.m` / dotfile edits the previous version made (SARAH, FeynRules append paths to `init.m`; old entries must be removed before the new path is added).
- Updating the config's recorded version atomically *after* the new install verifies, so a half-finished install does not leave the config pointing at a working older binary.

`INSTALL.md` for each tool must list which side-effects (`init.m` lines, env vars, downloaded archives) the install owns and the uninstall/upgrade path for each.

#### `install.sh` contract

- Returns 0 on full success.
- Returns a documented non-zero code on `activation_required` (Wolfram), `download_failed`, `build_failed`, etc. Codes are listed in the tool's `INSTALL.md`.
- The runner does not interpret codes; if non-zero, it loads `INSTALL.md` and lets the agent walk the user through it.

#### `INSTALL.md` shape

Replaces today's `*-install/SKILL.md`. No skill frontmatter (it is a reference doc, not a skill). Sections:

- Prerequisites
- Detection logic
- Install steps
- Interactive checkpoints (e.g. Wolfram activation)
- Blocker codes & remediation
- Smoke test

Content is the same as today's install skills — relocated and stripped of skill metadata.

### 3. Migration

#### Per-tool migration (repeat for all 11 tools)

1. Create `_shared/installs/<tool>/`.
2. Move scripts: `skills/<tool>-install/scripts/*` → `_shared/installs/<tool>/` (flat — no `scripts/` subdir, except keep `tests/`).
3. Convert `skills/<tool>-install/SKILL.md` → `_shared/installs/<tool>/INSTALL.md`:
   - Strip the YAML frontmatter (`name:`, `description:`, `type:`).
   - Drop "when to invoke this skill" framing.
   - Keep prerequisites, detect/install logic, blocker tables, smoke tests verbatim.
4. Add a `detect.sh` if one does not already exist. Some current install skills only have `install.sh` plus `_blocker.sh`; we need a clean "is it ready" probe separate from the install action.
5. Update the runner skill (`sarah-build`, `maddm`, etc.) to add the preflight block from §2 and remove existing "Run `/sarah-install` first" error-table rows that point at deleted skills.
6. Delete `skills/<tool>-install/`.

#### Repo-wide cleanup (one-time)

- Grep for stale `/<tool>-install` invocations and references across all `SKILL.md` files; replace each with either a `_shared/installs/<tool>/INSTALL.md` reference or remove if no longer relevant.
- Most-impacted file: `lagrangian-builder/SKILL.md`. Rip out:
  - `check_state.py`'s install-state probing
  - The Step 2 sub-skill orchestration block (lines 78, 162, 170, 179–193, 736–738, 807–832)
  - The "Sub-skill: SARAH install" footer reference
  - The equivalent SPheno block
- Replace with: "Step 2: invoke `/sarah-build` (it self-heals if SARAH/Wolfram missing)." Same for SPheno.
- Update `.claude-plugin/marketplace.json` and `plugin.json` if they enumerate the install skills.
- Update the `Skill Categories` table in the root `CLAUDE.md` (the "BSM model building" row currently lists `sarah-install`, `spheno-install`, `looptools-install`, `feynrules-install`).
- Update the README's Skill Categories section similarly.

#### Order of work

**Single PR.** Doing this in one PR sidesteps the half-converted-state problem (e.g. `lagrangian-builder` referencing some `*-install` skills that still exist and others that don't). The diff is large but mostly mechanical — relocations, frontmatter strips, preflight blocks, deletions.

Sequence within the PR, for sanity-checking the pattern as it expands:

1. **looptools first** as a vertical slice — simplest, no interactive activation. Land `_shared/installs/looptools/`, wire `formcalc`'s preflight, delete `looptools-install/`. Confirm the pattern works end-to-end before fanning out.
2. **The other 8 non-SARAH tools** — `spheno`, `maddm`, `micromegas`, `formcalc`, `feynarts`, `feynrules`, `ddcalc`, `higgstools`, `drake`. Each follows the per-tool checklist above. DRAKE's preflight halts on the Anubis gate rather than self-healing — call this out explicitly in `_shared/installs/drake/INSTALL.md`.
3. **SARAH last** — most consumers, Wolfram activation gate. Update `lagrangian-builder` in the same step to drop `check_state.py`'s install probing and the Step 2 sub-skill orchestration block (lines 78, 162, 170, 179–193, 736–738, 807–832).
4. **Rewrite `/install`** (§4) and update README + CLAUDE.md categories + `marketplace.json` + `plugin.json`.

All in the same PR. CI runs the full preflight smoke once at the end.

### 4. Rewritten `/install` meta-skill

Purpose unchanged: front door for "set me up before I start working." User picks a bundle, the skill runs the appropriate installs back-to-back so they can walk away.

#### What changes

1. **No more dispatching to sub-skills.** The `/sarah-install` etc. skills no longer exist. `/install` directly drives the same `_shared/installs/<tool>/{detect,install}.sh` that the runners use.

2. **Bundle definitions stay in `/install/SKILL.md`** as a table. No logic change. Example:

   | Bundle              | Tools                                                  |
   |---------------------|--------------------------------------------------------|
   | profumo-paper       | sarah, spheno, maddm, micromegas, looptools, formcalc  |
   | dm-relic            | maddm, micromegas                                      |
   | dm-direct-detection | micromegas, ddcalc                                     |
   | dm-indirect         | maddm, gamlike                                         |
   | one-loop            | looptools, formcalc, feynarts                          |
   | bsm-model-building  | sarah, spheno, feynrules                               |

3. **Bundle execution loop:**
   - For each tool in the bundle (in declaration order), run `_shared/installs/<tool>/detect.sh`.
   - Exit 0 → log "✓ <tool> already installed" and skip to the next tool.
   - Non-zero → load `_shared/installs/<tool>/INSTALL.md` and walk through the install.
   - On `activation_required` (Wolfram) or `manual_download_required` (DRAKE Anubis), halt the bundle and surface the next-step instruction. The user resumes by re-invoking `/install <bundle>`.
   - **Queue resumption is detect-driven, not state-stored.** Re-invocation re-runs `detect.sh` for every tool in the bundle. Tools that completed pass the fast path (~5 ms each) and are skipped; the bundle effectively resumes at the first tool whose `detect.sh` still fails. There is no separate resume cursor — the config + `detect.sh` are the queue state.
   - This implies: (a) `detect.sh` must be cheap on the fast path (see §2 contract); (b) every `install.sh` must leave the config in a consistent state on partial completion (no recorded path until the install verifies); (c) bundle order matters when later tools depend on earlier ones (e.g. `formcalc` after `looptools`) — `/install`'s bundle table fixes the order.

   A test fixture covers the resume case: pre-populate config with N-1 tools registered, leave one missing, run the bundle, assert only the missing tool's `install.sh` is invoked.

4. **Single-tool form supported.** `/install sarah` runs the same loop with one entry. Matches today's mental model where `/sarah-install` exists.

5. **No more "directory of installers."** The list of available tools comes from the contents of `_shared/installs/`, not from a hardcoded enumeration of skills.

#### Net effect

- `/install profumo-paper` → set up everything for the paper.
- `/install sarah` → install just SARAH.
- `/sarah-build` (or any other runner) → installs SARAH on demand if missing.

All three paths converge on the same `_shared/installs/sarah/{detect,install}.sh` plus `INSTALL.md`.

## What this design does NOT do

- Does not change `install.sh` behavior for tools that already have a clean detect/install split. New `detect.sh` work is required for SARAH, DRAKE, and MadDM (see Non-goals caveat).
- Does not touch `plugins/shared/install-helpers/`.
- Does not change config schema or `~/.config/hephaestus/config.toml` paths (a new `version` field on tool entries is additive and read-only-when-absent).
- Does not change the runner skills' physics behavior — they get a preflight prepended; their actual job is unchanged.

## Open questions

None.

Resolved at design time:
- **Migration scope:** single PR (see §3 Order of work). Avoids the half-converted-state problem.
- **Vertical slice:** looptools → formcalc lands first *within* that PR, as a sanity check before the other tools are migrated.
- **`/install` rewrite:** same PR, after all tool migrations.
