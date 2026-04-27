# Fix-r1 Summary — Singlet-Doublet Phase 2 (R1)

**Date**: 2026-04-24
**Branch**: `sd/fix-r1-20260424` (worktree: `/Users/yianni/Projects/hep-ph-agents.worktrees/sd-A/`)
**Wall time**: ~12 min

## Counts

| Category | Count | IDs |
|----------|-------|-----|
| Fixed    | 3     | sd-A-005, sd-A-006, sd-A-007 |
| Skipped (out-of-scope) | 4 | sd-A-001, sd-A-002, sd-A-003, sd-A-004 |

## Fixed issues

### sd-A-005 — MadDM version-validation warning
Added a named note block in SKILL.md Step 4c (after the `--mode=maddm` paragraph)
documenting that the "PLUGIN.maddm has marked as NOT being validated with this version"
warning is cosmetic when running MadDM 3.2 with MG5 3.5.6. Directs the skill to log at
DEBUG and not retry.
- Commit: `a96eb89`
- Evidence file: `e1_sd-A-005.md`

### sd-A-006 — Unicode glyph rendering (chi, Omega) in cmr10 font
Replaced bare Unicode characters in the ax.text() annotation in SKILL.md Step 4d
with LaTeX math-mode strings ($\chi_1$, $\Omega h^2$). Works correctly in both
usetex=True and usetex=False (mathtext/cm fallback) modes.
- Commit: `5934f95`
- Evidence file: `e2_sd-A-006.md`

### sd-A-007 — SARAH model name SingletDoublet_A clarification
Added a named note block in SKILL.md Step 4a explaining that `SingletDoublet` is the
canonical SARAH model name and that playtest-variant suffixes are no-ops on the
cached-build path.
- Commit: `63a6932`
- Evidence file: `e3_sd-A-007.md`

## Skipped issues

See SKIPPED.md for full rationale. Summary:
- sd-A-001: Fix is in demo/SKILL.md (outside singlet-doublet/** scope)
- sd-A-002: Fix is in plugins/model-building check_state.py (outside scope)
- sd-A-003: Fix is in plugins/model-building run_spheno.py (out of scope per reviewer + MANAGER_DECISIONS.md)
- sd-A-004: Host-system binary (flock); deferred to future session per MANAGER_DECISIONS.md

## Recommendation

SD Phase 2 fix-r1 complete. All 3 in-scope issues fixed; 4 out-of-scope issues logged.
Branch sd/fix-r1-20260424 is ready for PT-A re-review or promotion. The 2 MAJOR issues
(sd-A-003, sd-A-004) remain open and require manager/model-building owner action.
