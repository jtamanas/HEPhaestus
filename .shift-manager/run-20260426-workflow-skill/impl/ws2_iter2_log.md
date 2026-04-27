# WS2 iter-2 implementation log

**Date:** 2026-04-26
**Implementer:** Claude Sonnet (second implementer)
**Baseline:** main HEAD at start (includes all 27 iter-1 steps)

## Session start state
- 107 shift-manager tests pass, 3 skip, 0 fail
- 2 pre-existing regressions on main (Blockers 1 + 2)
- 7 blockers + 12 quality findings from iter-1 review

## Commits (in order)

### B1+B2 — `c14eeaa` — test regression fixes
- `test_schema_version`: `==1` → `==2` (S1 bumped schema_version)
- `test_missing_contains_required_prereqs`: expect `[feynarts, formcalc]` only (ddcalc is now exists)

### B3 — `b7a5d7c` — DMC out-of-scope guard
- Replaced `git merge-base origin/main HEAD` with `git rev-parse main`
- Fails immediately with `BASE_BRANCH_NOT_FOUND` if local main absent
- Never silently passes when base is unreachable

### B4 — `6522b94` — `MultipleSamePriorityRolesError`
- Added exception class to matrix_lookup.py
- Replaced `pass` in `rank_by_role` tie branch with actual `raise`
- Added test_06_tie_error_on_same_priority_same_role to test_matrix_fold.py (TDD: RED→GREEN)

### B5+CQ8 — `a5e5dbf` — drift test direction fix + exclusion list test
- Rewrote `test_forward_drift_skill_codes_in_catalog` → `test_forward_drift_skill_codes_in_matrix`
- Now tests SKILL.md codes vs `_get_matrix_blocker_codes()`, not catalog
- Added `_get_ws2_owned_codes()` helper using `owned_by: this-ws` field to skip DMC-mirrored codes
- `test_blocker_regex_does_not_match_exclusion_list` (tautology) → `test_exclusion_list_contains_no_real_catalog_codes` (real assertion)

### B6 — `b867817` — real invariant #12 check
- Replaced `assert True` with actual contradiction check:
  walk chain_overrides, find removed_prereqs, collect blockers for those prereqs,
  assert all blockers in `accepted_blockers`
- Found data bug: `MG5_MIRROR_COLOR_WALL` and `UFO_MISSING` were missing from
  dark-su3 relic `accepted_blockers` (madgraph+maddm carry these codes)
- Fixed constraints.yaml to add both codes to accepted_blockers

### B7 — `ad23ac3` — ChainOverride + MatrixAcknowledgement schema
- Added `MatrixAcknowledgement` and `ChainOverride` $defs to matrix_capabilities.schema.json
- MatrixAcknowledgement enforces `accepted_blockers` as list[str], not string
- load_capability_matrix now validates each chain_override against ChainOverride schema
- 6 new tests in TestChainOverrideSchema; negative fixture `malformed_acknowledgement.yaml` added

### CQ1+CQ2 — `d854e15` — remove model-name hack from ws1_axis_reader
- Removed `if "dark_su3" in analytic_module: cp_odd_scalar_present = True` (non-negotiable)
- Replacement: read from `dm_phenomenology.candidates[].cp == "odd"`
- WS1_NOT_MERGED diagnostic emitted via warnings.warn if dm_phenomenology absent
- Removed `n_higgs_doublets if n_higgs_doublets > 0 else max(...)` silent floor
- Removed dead `if spec.get("name") == "dark_su3" or not any(...): pass` block
- Removed redundant `elif name == "Psi"` (already in name-in tuple above)

## Status after these commits
- 214 pass, 3 skip, 1 fail (pre-existing 2hdm-a prose test, not WS2)
- All 7 blockers resolved
- CQ1+CQ2+CQ8 resolved
- Remaining: CQ3, CQ4, CQ5, CQ6, CQ9, CQ10, CQ11, CQ12
