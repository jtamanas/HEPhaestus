# Phase 0 Prep — SUMMARY

Worktree: /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-prep/
Branch: 2hdma/prep-20260424
Final HEAD: 4436b64
Overall gate: PASS (proceed to PT1)

---

## Step statuses

P1 PASS 93b337c — demo_output/2hdm-a/ created fresh; .gitignore + .cleaned written
P2 PASS 6fbca8c — Wchi=0.0 set (LOCKED); 12 blocks classified; --dry-run added; AUDIT.md written
P3 PASS 76919d4 — relic_approx/model_source/model_fixture added; all 3 stubs validate; schema lock released
P4 PASS 213b319 — iter_6_notes.md written; 7 renderer sites from git history + grep; no INCOMPLETE prefix
P5 PASS adbf16d — --skip-render removed; flock wolframscript invocation in place
P6 PASS 8a288a0 — sys.path.insert(0, plugins/monte-carlo-tools/skills/maddm/scripts) added; 3 importers audited
P7 PASS 4bb97d2 — capture_env.py + env.json with 8 keys; dual SHA pre_run=a05f274, at_capture=8a288a0
R1 PASS — Schema sign-off written; OWNER: 2hdm-a; ACK: SD-clean, dark-su3-clean
R2 PASS — Wchi=0.0 confirmed; MadDM DM detection not gated on DECAY width
R3 PASS — Gate-downgrade policy pre-locked and documented

## Gate evaluations

G1  PASS non-negotiable
G2  PASS non-downgradable
G3  PASS non-downgradable
G4  PASS downgradable (7 sites found, no INCOMPLETE prefix)
G5  PASS non-negotiable
G6  PASS downgradable (sys.path workaround documented)
G7  PASS non-negotiable
G8  PASS non-negotiable
G9  PASS non-negotiable
G10 PASS non-negotiable

OVERALL: PASS

RECOMMENDATION: PROCEED to Phase 1 (PT1 playtest).

---

# Round 2 — defects addressed (sonnet, 2026-04-24)

| D  | Severity | Resolution |
|----|----------|------------|
| D1 | minor    | FIXED — SKILL.md:252 invocation now reads SARAH_PATH from XDG config via jq and injects it via AppendTo[$Path,...]; prose updated to match. |
| D2 | minor    | FIXED — capture_env.py: added _strip_styleform() helper; sarah_version now "4.15.3" (was StyleForm-wrapped). |
| D3 | blocker  | FIXED — capture_env.py: added _find_config_path() with XDG-first search; added cfg-dict version shortcuts for mg5/maddm; env.json regenerated: mg5_version="3.5.6", maddm_version="3.2.13", config._config_source="~/.config/hep-ph-agents/config.json". |
| D4 | trivial  | FIXED — p7.md: corrected false claim about main_sha.txt; now truthfully states fallback PRE_RUN_SHA_FALLBACK was used. |

All 4 defects addressed. env.json is up to date with real tool versions. capture_env.py reads XDG config correctly. SKILL.md invocation is honest about $SARAH_PATH usage.
