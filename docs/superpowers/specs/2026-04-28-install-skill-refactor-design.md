# Install Skill Refactor — Design

**Date:** 2026-04-28
**Status:** Design (pending implementation plan)
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

- Not changing install script behavior. Pure relocation plus a small new `detect.sh` per tool where one doesn't already exist.
- Not changing the config schema or the `~/.config/hephaestus/config.toml` paths.
- Not touching `plugins/shared/install-helpers/` (cross-plugin atomic-write / config helpers).

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
- Checks the config *and* probes the binary (e.g. `sarah --version` runs, Wolfram kernel responds).
- Exit 0 = ready; exit non-zero = not ready. The runner does not need to know which.
- Reusable: `/install` (the bundle skill, §4) calls the same `detect.sh`.

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
7. Run the runner's tests to confirm preflight wiring works.

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

So the repo is never broken mid-migration:

1. Land `_shared/installs/<tool>/` for one tool. Start with **looptools** — simplest, no interactive activation.
2. Update its consumer (`formcalc`) preflight; verify.
3. Delete `looptools-install/`. Repeat the pattern for the next tool.
4. Save **sarah** for last (most consumers; has the Wolfram activation gate).
5. Final pass: rewrite `/install` meta-skill (§4) and update README + CLAUDE.md categories.

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
   - For each tool in the bundle, run `_shared/installs/<tool>/detect.sh`.
   - Exit 0 → log "✓ <tool> already installed" and skip.
   - Non-zero → load `_shared/installs/<tool>/INSTALL.md` and walk through the install. On `activation_required`, halt the bundle and surface the activation instruction; user resumes by re-invoking `/install <bundle>` after activating.
   - Continue with the next tool.

4. **Single-tool form supported.** `/install sarah` runs the same loop with one entry. Matches today's mental model where `/sarah-install` exists.

5. **No more "directory of installers."** The list of available tools comes from the contents of `_shared/installs/`, not from a hardcoded enumeration of skills.

#### Net effect

- `/install profumo-paper` → set up everything for the paper.
- `/install sarah` → install just SARAH.
- `/sarah-build` (or any other runner) → installs SARAH on demand if missing.

All three paths converge on the same `_shared/installs/sarah/{detect,install}.sh` plus `INSTALL.md`.

## What this design does NOT do

- Does not change install script behavior — relocation only, plus a new `detect.sh` per tool where missing.
- Does not touch `plugins/shared/install-helpers/`.
- Does not change config schema or `~/.config/hephaestus/config.toml` paths.
- Does not change the runner skills' physics behavior — they get a preflight prepended; their actual job is unchanged.

## Open questions

None at design time. Implementation plan should decide:
- Whether to migrate looptools → formcalc end-to-end as a "vertical slice" before any other tool, to validate the pattern before applying it 10 more times.
- Whether the `/install` rewrite lands in the same PR as the last tool migration or a separate PR.
