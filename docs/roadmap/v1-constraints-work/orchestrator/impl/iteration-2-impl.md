# Phase C — /lagrangian-builder constraint dispatch: iteration-2 implementation

**Implementer:** Claude Sonnet 4.6 (sub-agent, iteration-2)
**Branch:** `workstream-phaseC-orchestrator`
**Date:** 2026-04-19
**Verdict input:** NEEDS_FIXES from iteration-1-review.md

---

## Commits

```
1af899d W14-pC: clarify Intent-4 process-string placeholder with dark_su3 example
a608ea5 W14-pC: fix Intent-1 flag name (--dm-candidate → --dm-pdg)
```

---

## Fix A — `--dm-candidate` → `--dm-pdg` (required)

### Evidence: zero occurrences in SKILL.md

`git grep -n '\-\-dm-candidate' plugins/hep-ph-toolkit/skills/lagrangian-builder/` returns
only hits in `test_constraint_dispatch.py` (docstrings and assertion messages) — zero
in `SKILL.md`.

### What changed

`SKILL.md` Intent 1 CLI chain (previously line 263) replaced:

```
# Before (wrong — argparse error at runtime):
    --dm-candidate <spec.dm_candidate.pdg>

# After (matches run_micromegas.py lines 80-81):
    # Preferred: spec.yaml carries dm_candidate.pdg — no extra flag needed.
    # Fallback:  --dm-pdg <spec.dm_candidate.pdg>   (explicit PDG override)
    # Opt-in:    --auto-detect                       (parse SLHA + UFO attrs)
```

Confirmed against `plugins/hep-ph-toolkit/skills/micromegas/scripts/run_micromegas.py`
argparse (lines 80–81: `--dm-pdg`, `--auto-detect`) and SKILL.md lines 67–69.

### Regression tests added

Two new tests in `test_constraint_dispatch.py`:

| Test | Behaviour |
|------|-----------|
| `test_no_dm_candidate_flag` | Asserts `--dm-candidate` is absent from SKILL.md text |
| `test_intent_relic_density_uses_correct_dm_flag` | Asserts at least one of `--dm-pdg`, `--auto-detect`, or `dm_candidate` appears in the Intent 1 block |

Both tests **failed before the fix** (confirmed by running them against the unmodified
SKILL.md) and **pass after** (SHA `a608ea5`).

---

## Fix B — Intent-4 process-string placeholder clarity (nice-to-have)

### What changed

Added a prose block immediately above the `Stage 1` shell fence in Intent 4:

- Explains that `"DM DM -> q q"` is a placeholder; real field names from `particles.m`
  must be substituted.
- Gives the exact substitution source: `particles.m` (the SARAH output file).
- Provides a concrete worked example for the shipped `dark_su3` template:
  `"psiD psiDbar -> u uBar"` with the full Stage 1 invocation.
- Explicitly states that passing the placeholder literally causes a FeynArts parse error.

The Stage 1 `--process` argument was also updated from `"DM DM -> q q"` (with a
parenthetical comment) to `"<dm-field> <dm-field> -> <sm-field> <sm-field>"` — an
unambiguous angle-bracket placeholder consistent with the rest of the SKILL.md style.

---

## Test counts

| Milestone | Passed | Skipped | xfailed |
|-----------|--------|---------|---------|
| Pre-iteration-2 (iteration-1 head, SHA 2813536) | 753 | 43 | 1 |
| Post-Fix A (SHA a608ea5) | 755 | 43 | 1 |
| Post-Fix B (SHA 1af899d) | 755 | 43 | 1 |

Delta: **+2 tests** (both regression guards for Fix A). Fix B added no new tests.

Full suite command: `pytest plugins/ --import-mode=importlib -q`

---

## Deviations from spec

None. All required steps executed in order. Fix B worked example uses `dark_su3`
(the canonical shipped template) exactly as specified in the review.
