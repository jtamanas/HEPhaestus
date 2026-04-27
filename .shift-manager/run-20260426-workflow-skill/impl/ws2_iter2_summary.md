# WS2 iter-2 summary

**Date:** 2026-04-26  **Implementer:** Claude Sonnet (second implementer)  **Tool uses:** ~70

## Final test counts

```
pytest .shift-manager/tests/ plugins/hep-ph-demo/skills/_shared/tests/ -v
215 passed, 3 skipped, 1 failed, 13 warnings
```

The 1 failure is `Test2HdmA::test_step4_prose_directive_count_and_order` — pre-existing, confirmed not WS2's responsibility by iter-1 reviewer. The 13 warnings are expected [INV#13] noise (intel/digest.md not on disk).

## Blockers resolved (all 7)

- **B1** `test_schema_version` asserted ==1; updated to ==2 (S1 bumped schema_version).
- **B2** `test_missing_contains_required_prereqs` expected ddcalc in missing; updated to expect [feynarts, formcalc] only (ddcalc flipped to exists in S7-mega).
- **B3** DMC out-of-scope guard silently passed when origin/main unreachable; replaced with `git rev-parse main`, fails immediately with BASE_BRANCH_NOT_FOUND.
- **B4** `rank_by_role` tie branch had `pass`; added `MultipleSamePriorityRolesError` and replaced pass with raise; TDD test_06 added.
- **B5** Forward-drift test checked SKILL.md codes vs catalog (wrong direction); rewrote to check vs matrix codes using `_get_ws2_owned_codes()` to skip DMC-mirrored codes.
- **B6** Invariant #12 ended with `assert True`; implemented real contradiction check: walk chain_overrides, collect blockers for removed prereqs, assert all in accepted_blockers. Found data bug: MG5_MIRROR_COLOR_WALL + UFO_MISSING missing from constraints.yaml accepted_blockers — added both.
- **B7** Schema had no ChainOverride/MatrixAcknowledgement defs; added both to matrix_capabilities.schema.json, added loader validation, added 6 tests + malformed_acknowledgement.yaml fixture.

## Quality findings resolved (CQ1-CQ6, CQ8, CQ10-CQ12)

- **CQ1** Model-name hack `if "dark_su3" in analytic_module` removed; replaced with `dm_phenomenology.candidates[].cp == "odd"` read. WS1_NOT_MERGED diagnostic emitted if dm_phenomenology absent.
- **CQ2** Silent `n_higgs_doublets` floor and dead `if ... pass` block removed.
- **CQ3** Vacuous `if trigger_verdicts:` / `if spheno_blocked:` guards → hard `assert`.
- **CQ4** Invariant #11 `has_blocked` filtered to prereqs with non-`none` role for the observable.
- **CQ5** Invariant #7 "more than half" slack → explicit `KNOWN_UNCOVERED_A1 = {"Non-SM-embedding"}` allow-list.
- **CQ6** Invariant #9 (duplicate of #2) renamed to `test_invariant_9_no_matrix_code_missing_from_catalog` with accurate docstring.
- **CQ8** `test_blocker_regex_does_not_match_exclusion_list` (pass + assert True) → `test_exclusion_list_contains_no_real_catalog_codes` (real assertion).
- **CQ10** Dead `if "." in axis and not axis.startswith("A") is False: pass` branch removed from `_resolve_axis_value`.
- **CQ11** CLI test added asserting `analytic_backend.role.relic == escape_hatch` at fold level (registry-independent).
- **CQ12** Cross-plugin library note appended to ws2_iter1_log.md; test updated to assert log contains `[CROSS-PLUGIN-LIB]`.

## Not resolved in this iter

- **CQ7** (INV#14/#15 always-pass warnings): left as-is per plan (warning-tier); adding `-W error` filterwarnings is a future enhancement.
- **CQ9** (TDD discipline on S4a→S4b): historical; cannot retroactively create two-commit history.

## Commits (9 total)

`c14eeaa` B1+B2 | `b7a5d7c` B3 | `6522b94` B4 | `a5e5dbf` B5+CQ8 | `b867817` B6 | `ad23ac3` B7 | `d854e15` CQ1+CQ2 | `f2ee37d` CQ3-CQ6+CQ10-CQ12 | (log commit)
