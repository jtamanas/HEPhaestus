# FOLLOWUPS — run-20260426-workflow-skill (WS4)

Append-only. Follow-up items from the WS4 analytic-exception-detector implementation.

---

## FU-WS4-RUNTIME-001 — DMC renderer does not yet expose Python API; runtime emission test deferred

**Status:** open  
**Owner:** future workstream authorized to modify `dark-matter-constraints/scripts/`  
**Filed:** iter-2 (2026-04-26)

**Rationale.** Synthesis §4.4(b) requires a runtime emission test that invokes the DMC
merged-report renderer with a fixture, captures the emitted merged-report bytes, and asserts
the verbatim banner appears before the Results table. Iter-1 found (WS4 S5 spike) that the
DMC merged-report renderer is a Claude Code SKILL.md-driven agent action — NOT a Python
function or subprocess. There is no importable or subprocess-invokable Python renderer in
`plugins/constraints/skills/dark-matter-constraints/scripts/`.

**Gap.** The round-3 reviewer gap that WS4 was sized to close remains partially open: the
static placement test (test_analytic_exception_disclosure_static.py) enforces verbatim-banner
presence at every registered placement path (including DMC SKILL.md P1), but it does NOT
enforce runtime emission semantics (positional placement before the Results table in the
actual merged report bytes emitted at runtime).

Iter-1 self-authorized a rescope targeting render_disclosure.py (the workflow-skill upstream
renderer) as a tautological substitute. Iter-2 manager decision: formally descope to
pytest.skip with this tracked FU entry.

**Unblock criterion.** A future workstream adds a Python `render_merged_report()` function
to `dark-matter-constraints/scripts/` that accepts a model spec + registry entry and returns
the merged report bytes. Once that function exists, the deferred test in
`test_analytic_exception_disclosure_emission.py::test_dmc_runtime_emission_dsu3_002` can be
implemented by:
1. Importing `render_merged_report` from the new DMC scripts module.
2. Calling it with the `dsu3_stubbed_summary` fixture + registry `dsu3-002` entry.
3. Asserting `entry.banner.strip()` appears in the output bytes verbatim.
4. Asserting banner appears before the `## Results` or `### Results` heading.

---

## FU-WS4-PROXY-RUNTIME-001 — proxy_run runtime emission test deferred

**Status:** open  
**Owner:** future workstream authorized to modify `dark-matter-constraints/scripts/`  
**Filed:** iter-1 (2026-04-26), tracked here per iter-2

**Rationale.** Decision 1 in ws4_plan_final.md explicitly descoped the proxy_run runtime
emission test from WS4 v1. The static placement test covers `micromegas-singlet-doublet-proxy-001`
banner presence at P1 (DMC SKILL.md) and P2 (micromegas SKILL.md) — both added in iter-2 and
now passing with hard assert. The runtime emission test (verifying the proxy banner appears in
the actual micrOMEGAs merged-report bytes at runtime) requires DMC scripts/ modifications,
which are out of scope for WS4.

**Unblock criterion.** Same as FU-WS4-RUNTIME-001: a Python `render_merged_report()` function
in DMC scripts/ that can be tested in isolation.

---

## FU-WS4-PROXY-RUN-PLACEMENTS — proxy_run banner placements

**Status:** closed  
**Closed by:** iter-2 commit `3df63b4` (ws4-iter2(blocker-3))  
**Filed:** iter-1 (inline docstring), tracked here per iter-2

Proxy-run entry `micromegas-singlet-doublet-proxy-001` banner added verbatim to:
- `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (placement P1)
- `plugins/constraints/skills/micromegas/SKILL.md` (placement P2)

Static placement test now hard-asserts both placements. Closed.
