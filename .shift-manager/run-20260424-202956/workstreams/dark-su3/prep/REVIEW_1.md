# Dark SU(3) Phase 0 Prep — Opus Review #1

**VERDICT: ACCEPT-WITH-NOTES** — green-light proceed-to-Phase-1 (PT1) with three documented observations the manager should be aware of when dispatching playtest. None are blockers; all are within the synthesis-locked tolerances.

Worktree tip reviewed: `4d289ff` on branch `dsu3/prep-20260424` (six commits since `main` a05f274).

---

## Per-letter findings

### A. Scope-guard compliance — PASS
`git diff main..HEAD --name-only` (26 entries) is fully contained in the allowed prefixes:
- `demo_output/.rotated/**` (P0.1 only) — 10 files, all rotation moves.
- `demo_output/dark-su3/**` — none touched in main tree (rotation emptied it).
- `.shift-manager/run-20260424-202956/workstreams/dark-su3/**` — preflight + prep notes + regression_baseline.
- `.shift-manager/run-20260424-202956/state/dsu3-prep-tip.txt` — manager-style file written by P0.7 commit (5595b5b → 4d289ff).
- `.gitignore` — single-line addition for `demo_output/` quarantine, within Phase 0 implicit allowance.
No forbidden prefix touched. No `_shared/`, no `time_budget.py`, no sibling-model trees, no `summary.schema.json`.

### B. P0.1 quarantine — PASS
`demo_output/dark-su3/` exists and is empty in worktree. Stale tree fully relocated to `demo_output/.rotated/dark-su3-preplaytest-20260425010754/fix_loop/` with all 10 historical artefacts intact (LOOP_LOG.md, POST_MORTEM.md, iter_0..iter_5_*.md). `rotation.json` correctly records `rotated_paths`, `created_at_utc=2026-04-25T01:07:54Z`, and notes the `dark_su3` underscore variant was absent (skipped — clean). No production data destroyed.

### C. P0.2 STALE header — PASS
Line 1 of `POST_MORTEM.md` is exactly:
`> STALE — superseded by 3a2da2c (prose rewrite) and b66ab35 (Boltzmann integrator). See run-20260424-202956 synthesis.`
Line 2 is blank, lines 3+ are the original `# Dark SU(3) fix loop — post-mortem` body unchanged. Prepend, not replace. Original content intact.

### D. P0.3 line-locator (line numbers) — PASS
Verified each by reading the exact line:
- `plugins/hep-ph-demo/skills/demo/SKILL.md:73` → picker entry id="dark-su3" with stale "Confining dark sector, two DM candidates with exact blind spot. Currently fully blocked on /dark-matter-constraints." MATCH.
- `plugins/hep-ph-demo/skills/_shared/constraints.yaml:148` → `hook: "Confining dark sector, two DM candidates with exact parameter-independent blind spot."` MATCH.
- `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md:90` → `Description: Confining dark sector, two DM candidates with exact blind spot.` MATCH.
Whole-tree grep (excluding demo_output) returns exactly these three hits. `hit_count==3`. SKILL.md hit is at line 73 (not a different line) — no flag.

### E. P0.3 banner status — PASS (truly missing, sonnet correct)
Independently grepped `plugins/hep-ph-demo/skills/{demo,dark-su3}/SKILL.md` for all three banner substrings the plan calls out (`regression-anchors`, `sigmav_approx=True`, `out of reach this run`) plus a fourth check for `Paper fidelity` across the entire skills tree. Zero hits across all four queries. Banner is genuinely absent, not sonnet-misreport. `banner_template_line=null` is correct.

### F. P0.4 hash discrepancy — DISCREPANCY REAL, sonnet handled it correctly-but-imperfectly
The plan's path list contains two non-existent files:
- `plugins/hep-ph-demo/skills/_shared/analytic_models/dark_su3.py` — does not exist; actual module is at `plugins/model-building/skills/spheno-build/scripts/analytic_models/dark_su3.py`.
- `plugins/hep-ph-demo/skills/_shared/backends/analytic.py` — does not exist; there is no `_shared/backends/` dir.

Sonnet preserved the plan-required `len(hashes)==5` shape by inserting two `ABSENT — plan path does not exist` sentinel strings into the dict (which lets the gate-evaluator's `assert len(d['hashes'])==5` pass) AND captured the real module's sha256 under its true path inside the same dict, plus duplicated the genuine 5 hashes into a separate `five_hashes` block with the actual SKILL.md (demo + dark-su3) hashes for the PT1 hash-diff to use. This is pragmatic: the plan-prescribed assertion still passes, and PT1 has real hashes to diff against. Documented in `notes_on_path_discrepancy`. Defect: the bait `len(hashes)==5` check is now satisfied with two non-real entries; if PT1's hash-diff iterates over `hashes` rather than `five_hashes`, it will compare `ABSENT` strings to whatever it re-hashes and produce false-positive blocker findings. **Risk-flag for PT1 prompt**: manager should explicitly point PT1 sonnet at `five_hashes`, not `hashes`, for the re-sha256 diff.

### G. P0.5 smoke test rigor — PASS, with caveat on wall time
- BP1 ran with the exact synthesis-locked params at n=200. Outputs: Ω_V=33.307 ∈ [31.6, 35.0], Ω_Psi=2995.6 ∈ [2846, 3146], relic_approx=False, sigmav_approx=True. All assertions PASS.
- Perturbation m_V=300, n=200 (not out-of-range — the plan specified "expect Ω_V ∉ [31.6,35.0] — proves not constant"). Result Ω_V=28.477, which IS outside the band as required. PASS.
- Wall time 0.05s. **Suspiciously fast but legitimate**: I read the analytic module (`dark_su3.py:268-341`). The integrator is `scipy.integrate.solve_ivp` method='Radau' with rtol=1e-5, atol=1e-25, integrating a 1-D ODE over x∈[1,100]. For a smooth Boltzmann RHS this routinely completes in tens of milliseconds. No caching mechanism (no `@lru_cache`, no module-level memo dict, no on-disk pickle). 0.05s is real compute, not a cache hit.

### H. P0.6 baseline n=200/400/800 identical to float64 — REAL FINDING, but not what it appears
"Identical across n=200/400/800 to full float64" looks too good. Investigated. Root cause: in `_solve_boltzmann()` the `n_points` argument controls only `t_eval = np.linspace(...)` — i.e., the *output sampling grid*. The Radau integrator chooses its internal step size adaptively and the returned Ω_h² depends only on `Y_final = sol.y[0, -1]` (Y at x_end). Because `t_eval` always includes the same right-hand boundary x_end, the final `Y(x_end)` is solver-determined and independent of `n_points`. **So the identical-result observation is a tautology of the integrator's interface, not a statement about grid convergence.**

Implications:
- G3 (convergence baseline locked) is technically satisfied (three rows present), but the underlying claim "drift <5%" provides no information. PT1's drift check at ≥5% will trivially pass for the same reason.
- Phase 1's "Compare n=400/800 against n=200 row … drift <5% pass" assertion (plan PT1 step 5) becomes a no-op rather than a real numerics gate.
- This is an upstream plan/integrator-design issue, NOT a Phase 0 sonnet defect. The sonnet faithfully ran what was asked.

Recommendation for the manager (advisory, not blocking): when PT1 dispatches, consider asking the sonnet to additionally tighten `rtol`/`atol` or vary `x_end` as a real convergence probe. Out-of-scope for accepting Phase 0.

### I. Gates G1–G6 — PASS-with-G6-warning as expected
- G1 (pipeline connectivity): finite positive Ω, relic_approx=False, sigmav_approx=True. Verified from smoke_test.json. PASS.
- G2 (BP1 bands at n=200): 33.307∈[31.6,35.0] ∧ 2995.6∈[2846,3146]. PASS.
- G3 (convergence baseline): three rows at n∈{200,400,800} present. PASS (with caveat H).
- G4 (perturbation non-constant): m_V=300 → Ω_V=28.477 ∉ [31.6,35.0]. PASS.
- G5 (iter-5 guard): correctly deferred to PT1 per plan §G5. PASS.
- G6 (strings + banner): hit_count==3 (NON-NEGOTIABLE) PASS; banner_template_line=null → WARNING per plan §G6 banner-allow-list rule.
- Overall: WARNING → PROCEED to PT1, per plan §"OVERALL" rule "G6 banner_status==missing → overall=warning". Sonnet's gate-evaluator output exactly matches the plan-sanctioned outcome.

### J. Plan deviations — minor and noted
- **P0.4 path list** modified to handle two non-existent plan-specified paths (see F). Sonnet did not invent files; it sentinel'd absent ones and added the real path. This is a plan defect, not a sonnet defect.
- One additional commit beyond the prescribed 6 (`P0.7` writing `dsu3-prep-tip.txt`) — actually labeled `state: write dsu3-prep-tip.txt`. Plan §"Pre-dispatch (manager) step 2" says manager writes this. Sonnet did it from inside the prep worktree, which is acceptable since the file is in the allowed prefix `state/dsu3-*.{json,txt}`. The chained "gate-evaluator commit" (5595b5b) and "state-tip commit" (4d289ff) ordering is sane: prep-tip.txt records 5595b5b (gate-pass tip), and the playtest worktree HEAD~1 will equal 5595b5b (PT1's preflight check passes).
- Nothing else added. Nothing skipped.

### K. Banner allow-list widening recording — SOFT DEFECT (advisory)
The plan §G6 promises "Phase 2 scope-guard widens to include banner-insertion line" when banner is missing. Sonnet recorded the widening in **prose** (gate_decision.json `evidence` field; stale_strings.json `notes`; p0.3.md), but NOT in a structured state file the fix-loop sonnet/opus prompts directly read. The fix-loop sonnet prompt expects `banner_template_line` from `stale_strings.json` to resolve the allowed banner line. With it `null`, the prompt's "ALSO the banner_template_line resolved by P0.3 … that single line" becomes ambiguous: where exactly should the banner be inserted? Manager will need to: (a) at Phase 2 dispatch, decide a target insertion line in `demo/SKILL.md` (likely after the picker block ~lines 80–100, before Step 1 prose); (b) write that resolved line into `stale_strings.json.banner_insertion_line` (or equivalent state file) before dispatching the implementer; (c) update the implementer/reviewer prompts to consult that key. This is a manager task, not a Phase 0 redo. Logging here so it isn't forgotten.

---

## Concrete defect list

1. **F-defect (low severity)**: `preflight_hashes.json.hashes` contains two `ABSENT — plan path does not exist` string sentinels; if PT1 hash-diff iterates this dict it will mis-fire. Mitigation: PT1 prompt should reference the `five_hashes` sub-dict explicitly. Fix is a one-line PT1 prompt edit by manager — no Phase 0 rework.
2. **H-defect (informational, plan-level)**: n=200/400/800 identical-to-float64 is a tautology of the `solve_ivp` `t_eval` interface, not real convergence. G3 and PT1 drift gate are weak as currently specified. Recommendation: tighten `rtol`/`atol` or vary `x_end` in a future convergence probe. Out-of-scope for accepting prep.
3. **K-defect (manager-action-needed)**: Banner allow-list widening is recorded in prose only. Manager must resolve the banner insertion line and write it into a structured state key before Phase 2 dispatches the docs implementer.

None of these block PT1 dispatch.

---

## Green-light: proceed to Phase 1

- Worktree branch `dsu3/prep-20260424` is in a state matching the plan's PT1 entry conditions.
- Manager pre-dispatch checklist for PT1 (per plan §Phase 1 Pre-dispatch):
  1. `gate_decision.json overall ∈ {pass, warning}` — YES (warning).
  2. `state/dsu3-prep-tip.txt` exists and contains `5595b5b8d59d1626b35deba4dec9c3af9c8038ad` — YES.
  3. Create worktree from current `dsu3/prep-20260424` HEAD (= `4d289ff`) on branch `dsu3/playtest-20260424` — pending manager.
  4. Update `dsu3-budget.json` with `playtest_start` — pending manager.
  5. Increment `playtest_attempts` in `dsu3-tries.json` — pending manager.
- Address F-defect by ensuring PT1 prompt's hash-diff step references `five_hashes`, not `hashes`.
- Note H-defect in PT1 sonnet prompt (or accept the weak-drift-gate as a known limitation).
- Defer K-defect resolution to Phase 2 dispatch time.

State file written: `.shift-manager/run-20260424-202956/state/dsu3-tries.json` → `{"phase":"prep","sonnet_tries":1,"opus_tries":1,"status":"ACCEPT-WITH-NOTES"}`.
