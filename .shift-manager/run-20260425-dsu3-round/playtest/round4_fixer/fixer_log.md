# Round 4 Doc-Sweep Fixer Log

**Branch:** `worktree-agent-a5c532f834cda9315`
**Pre-edit HEAD:** `bd1c5bc76379ca771cef8b13b780885c7ffffd26`
**Scope:** `plugins/hep-ph-demo/skills/dark-su3/SKILL.md` (+ minor consistency fix in `/demo` SKILL.md)
**File line count:** 426 → 428 (+2 net; many lines reworded in place)

## Test counts

| Suite | Before | After | Status |
|---|---|---|---|
| `plugins/hep-ph-demo/skills/_shared/tests/` | 1 fail / 97 pass / 3 skip | 1 fail / 97 pass / 3 skip | OK (no regression; pre-existing 2hdm-a fail unchanged) |
| `plugins/constraints/skills/dark-matter-constraints/tests/` | 67 pass / 3 xfail / 3 xpass | 67 pass / 3 xfail / 3 xpass | OK |

**Note on baseline drift:** the task brief specified 100 pass for the shared
suite, but the actual baseline on this worktree before any edits was 97 pass
(measured pre-edit). My edits did not change that — the same 1 fail / 97 pass
/ 3 skip held before and after. Flagging in case the brief carried a stale
count from an earlier round.

## Sections changed (BEFORE → AFTER)

### 1. Top-of-file overview prose (line 34, mid-file)

BEFORE:
> Multi-component combination of per-candidate relic densities into experiment-level rates requires the planned `/dark-matter-constraints` meta-skill. DD and ID chains remain `[BLOCKED]`.

AFTER:
> ... driven through the analytic-only branch of `/dark-matter-constraints [EXISTS]`. Multi-component combination ... is on the upgrade roadmap (see the `dsu3-002` banner above) ... DD and ID chains remain `[BLOCKED]` on `/feynarts`/`/formcalc` (DD) and `/gamlike` (ID); `/dark-matter-constraints` itself is **EXISTS**.

### 2. Step 1 user-facing dialog (~line 107)

BEFORE:
> Multi-component weighting is handled by the planned `/dark-matter-constraints` meta-skill.

AFTER:
> Per-candidate relic density is available now via the analytic-only branch of `/dark-matter-constraints [EXISTS]` ... Paper-fidelity multi-component weighting into a total `Ω_tot h²` is on the upgrade roadmap (per the `dsu3-002` banner above) — emitted values are regression anchors only.

### 3. Step 3 gate question (~line 184) — REVIEWER-3 PRIMARY FLAG

BEFORE:
> "question": "All selected constraints require /dark-matter-constraints [PLANNED], which is not yet available. How to proceed?"

AFTER:
> "question": "Some selected constraints are blocked on missing prereqs (DD on /feynarts, /formcalc, /ddcalc; ID on /gamlike). /dark-matter-constraints is available. How to proceed?"

Surrounding prose updated: "Relic is now READY via the analytic-only branch of `/dark-matter-constraints [EXISTS]`. ... `/dark-matter-constraints` itself is no longer the blocker." Hypothetical-all-READY note now reads: "relic-only selection in this iteration; full READY for DD/ID requires `/feynarts`, `/formcalc`, `/ddcalc`, `/gamlike` to ship".

### 4. Step 3 "expected behavior" footer (~line 220)

BEFORE:
> This is the expected behavior for Dark SU(3) in this iteration: every constraint chain includes `/dark-matter-constraints [PLANNED]`, so `run_ready` finds nothing executable ...

AFTER:
> This branch fires only if the user selected DD and/or ID exclusively (without relic). In this iteration, relic is READY via the analytic-only branch ... DD and ID remain blocked on `/feynarts`/`/formcalc`/`/ddcalc` and `/gamlike` respectively — not on `/dark-matter-constraints`.

### 5. Step 4 relic-branch heading (~line 236)

BEFORE: `#### Step 4 — Relic density branch (BLOCKED — pending /dark-matter-constraints)`
AFTER:  `#### Step 4 — Relic density branch (READY via analytic-only branch of /dark-matter-constraints)`

Body rewritten: chain is now `/sarah-build [EXISTS]` → `/spheno-build [EXISTS]` (analytic dispatch) → `/dark-matter-constraints [EXISTS]` (analytic-only branch). Banner-aware caveat: emitted Ω h² is regression anchor only.

### 6. Step 4 analytic-backend note (~line 257)

BEFORE:
> Execution of the DD/ID chains remains additionally gated on `/dark-matter-constraints [PLANNED]` for multi-component weighting.

AFTER:
> Execution of the DD/ID chains remains gated on `/feynarts`/`/formcalc`/`/ddcalc` (DD) and `/gamlike` (ID); `/dark-matter-constraints` itself is no longer the blocker.

### 7. Step 4b heading (~line 263)

BEFORE: `##### 4b. SPheno spectrum generation (BLOCKED — analytic module unimplemented)`
AFTER:  `##### 4b. SPheno spectrum generation (READY via analytic dispatch)`

(The analytic module IS implemented post-round-3 — the BLOCKED label was stale.)

### 8. Step 4c per-candidate relic prose (~line 275)

BEFORE:
> Multi-component combination ... is the responsibility of `/dark-matter-constraints [PLANNED]`.

AFTER:
> ... surfaced through the analytic-only branch of `/dark-matter-constraints [EXISTS]`. ... Paper-fidelity multi-component combination ... is on the upgrade roadmap (per the `dsu3-002` banner); the values emitted today are regression anchors only.

### 9. Step 4 DD branch (~lines 287, 289)

BEFORE:
> Direct detection ... blocked on two separate prereq groups: 1. ... combination rule is the responsibility of `/dark-matter-constraints [PLANNED]`. 2. ... deferred to `/dark-matter-constraints [PLANNED]`.

AFTER:
> Direct detection ... blocked on the loop-DD prereq chain `/feynarts [PLANNED] → /formcalc [PLANNED] → /ddcalc [EXISTS] → /dark-matter-constraints [EXISTS]`. The `/dark-matter-constraints` meta-skill is available; the missing pieces are FeynArts and FormCalc ... Combination of per-candidate `σ_SI` ... is handled by `/dark-matter-constraints [EXISTS]`. This step is no longer the blocker; it waits on FeynArts/FormCalc upstream.

### 10. Step 4 ID branch (~line 297)

BEFORE:
> Indirect detection is blocked on `/gamlike [PLANNED]` and `/dark-matter-constraints [PLANNED]`. When both ship: ...

AFTER:
> Indirect detection is blocked on `/gamlike [PLANNED]`. The full ID chain is `… → /maddm [EXISTS] → /gamlike [PLANNED] → /dark-matter-constraints [EXISTS]`; `/dark-matter-constraints` itself is available, the missing piece is `/gamlike` ...

### 11. Step 4d plotting (~lines 306, 308)

BEFORE: `#### Step 4d. Plotting guidance (BLOCKED — no data until constraints run)` / "When `/dark-matter-constraints` ships and relic density runs ..."
AFTER:  `#### Step 4d. Plotting guidance (READY for relic; DD/ID overlays still blocked)` / "Once relic density has run via the analytic-only branch of `/dark-matter-constraints [EXISTS]` ..."

### 12. Step 4e summary.json prose (~line 370, 377)

BEFORE: "In this iteration, no constraints run for Dark SU(3) ..." / "If any constraints ran (future state, when `/dark-matter-constraints` ships) ..."
AFTER:  "In this iteration, relic runs via the analytic-only branch of `/dark-matter-constraints [EXISTS]` ..." / "When relic ran (the typical path in this iteration), write: ..."

### 13. summary.json skipped_constraints example (~lines 385–386)

BEFORE:
```json
{"id": "dd", "reason": "blocked on /feynarts, /formcalc, /ddcalc, /dark-matter-constraints"},
{"id": "id", "reason": "blocked on /gamlike, /dark-matter-constraints"}
```
AFTER:
```json
{"id": "dd", "reason": "blocked on /feynarts, /formcalc, /ddcalc"},
{"id": "id", "reason": "blocked on /gamlike"}
```

### 14. Error path table row for `/dark-matter-constraints` (~line 411)

BEFORE: `| /dark-matter-constraints | Not yet available | Skill not in marketplace | All Dark SU(3) constraints remain blocked; notify user and proceed only to planning mode |`
AFTER:  `| /dark-matter-constraints | ANALYTIC_BRANCH_FAILED | Analytic-only branch raises ... | Inspect the dispatch error; verify `analytic_only: true` ... Relic for dsu3 does not require MadDM in this iteration |`

### 15. /demo SKILL.md non-goals (line 118) — consistency fix

BEFORE:
> `/demo` does not implement multi-component DM combination. Dark SU(3) combination is deferred to `/dark-matter-constraints` (planned).

AFTER:
> `/demo` does not implement multi-component DM combination. Dark SU(3) per-candidate relic runs through the analytic-only branch of `/dark-matter-constraints [EXISTS]`; paper-fidelity multi-component combination into `Ω_tot h² ≈ 0.12` is on the upgrade roadmap of `analytic_models.dark_su3` (per the `dsu3-002` regression-anchor banner in dark-su3 SKILL.md), not blocked on `/dark-matter-constraints` itself.

**Logged per task brief:** the task said "do NOT touch any file outside ... unless your edits introduce inconsistency with another file ... in which case fix that too — but log it." The dark-su3 SKILL changes shifted `/dark-matter-constraints` from "(planned)" to "[EXISTS]"; the line in `/demo` SKILL.md that called the same skill "(planned)" was now contradictory and is updated above.

## Things explicitly NOT touched

- **`dsu3-002` regression-anchor banner** (lines 8–17): kept verbatim, per task brief. The mention of `/dark-matter-constraints` inside the banner is about the future upgrade roadmap (full Boltzmann + multi-component weighting), not a present-day blocker, so it remains accurate.
- **Constraints table near top of file** (lines 77–81): already correct (relic READY, DD/ID BLOCKED on FeynArts/FormCalc/DDCalc/GamLike, `/dark-matter-constraints [EXISTS]` in all three chains).
- **`multi_component_prereq: dark-matter-constraints`** in metadata (line 59): unchanged — this is a structural reference to the meta-skill, not a status claim.
- **`constraints.yaml`** and other shared assets: untouched.

## Surprises / notes

- Pre-existing test fail in `Test2HdmA::test_step4_prose_directive_count_and_order` is unrelated to dsu3 — it's about 2hdm-a's Step 4 prose directive structure. Confirmed unchanged before/after.
- Baseline shared-test pass count was 97, not 100 as stated in the brief. Flagged above; no regression introduced.
- The `dsu3-002` banner already correctly distinguishes "regression anchor" from "paper fidelity," so no banner edit was needed; the prose elsewhere just had to stop conflating "/dark-matter-constraints not available" with "paper fidelity not achievable." Those are two different things and now read that way.
- One minor scope-adjacent edit: in §1 (line 34), I added explicit pointer to the `dsu3-002` banner so readers don't think the analytic backend's regression-anchor caveat has been forgotten.

## Final commit

(commit will be created by the runner / next-step automation; this log records the scope, rationale, and test verification)
