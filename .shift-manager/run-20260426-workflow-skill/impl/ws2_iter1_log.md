## WS2 iter-1 execution log (append-only)

S0: done — WS1_present=false, WS4_present=false; branch flags recorded; no taxonomy.py, no analytic_exceptions.yaml
S0b: done — 3 axis-bundle fixtures + ws1_axis_enums_snapshot.yaml + conftest.py committed
S1: done — schema_version 1→2, blocker_catalog_ref/taxonomy_ref/analytic_exceptions_ref added; matrix_capabilities.schema.json; 12 tests pass
S2: done — blocker_catalog.yaml (58 entries), blocker_catalog.schema.json; 12 tests pass
S3: done — matrix_lookup.py with loader, BlockerVerdict, ToolLevelVerdict, CapabilityMatrix; 9 tests pass
S3a: done — ws1_axis_reader.py Branch A (WS1_present=false); dsu3/sd/2hdm_a acceptance criterion pass
S4a+S4b+S5: done — 18 matcher tests (12 single-axis + 6 conjunction) all pass
S6: done — 5 fold/rank_by_role/viable_chain_for tests pass
S7-mega: done — 13 prereq capabilities blocks (sarah-build, spheno-build, madgraph, maddm, micromegas, drake, ddcalc, higgstools, analytic_backend, feynrules, feynarts, formcalc, looptools); acceptance criterion passes
S10: done — ConstraintRow.capability_blockers field added; time_budget.py renders [CAP BLOCK] lines; acceptance criterion passes
S11+S11b+S11c: done — 19 tests pass (16 hard-error + 3 warning-tier); negative fixtures created
S12: done — matrix_acknowledgement in dsu3 relic override; 4 acknowledgement tests pass

## [CROSS-PLUGIN-LIB] D7 note — plugins/hep-ph-demo/skills/_shared/ cross-plugin library status

plugins/hep-ph-demo/skills/_shared/ now hosts cross-plugin shared library code
(matrix_lookup.py, ws1_axis_reader.py, time_budget.py).  This is acknowledged in
WS2 plan D7.  A future CLAUDE.md update should document this boundary explicitly.
WS3 (workflow-router) and any downstream consumer should import from _shared/ the
same way that the test harness does (sys.path insertion or relative import).  The
_shared/ directory is not namespaced under hep-ph-demo and may be promoted to a
top-level shared lib in a future refactor; until then, importers must add the path
explicitly.  No circular imports have been introduced; the matrix_lookup public API
is stable (load_capability_matrix, lookup_blockers, fold, rank_by_role, viable_chain_for).
