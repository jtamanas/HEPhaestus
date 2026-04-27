# Opus Review — PT-B Singlet-Doublet (sd/playtest-B-20260424 @ eb918fa)

**ACCEPT-PASS-WITH-NOTES**

PT-B sonnet's PASS-via-alternate-path verdict is plan-compliant and the root-cause
hypothesis (Mathematica `N[]` shadowing) is verified. Two notes: (1) the major
finding sd-B-002 is fix-scoped *outside* the singlet-doublet plugin dir and is
therefore Phase-2-ineligible under the plan; (2) artifact storage path deviates
from PT-A and from the plan's recording targets.

---

## Per-letter findings

### A. Verdict accuracy — PASS plan-allowed
Plan §"Variant B failure interpretation" (line 356) and §Variant-B success-criteria
2/3 (lines 215-217) explicitly authorise PASS when ZN→N clash surfaces *before*
MadDM completes ("Surfaced collision = PASS; silent-broken = FAIL"). PT-B
surfaced via `check_vertices.py` → `VERTICES_MISSING(yh1,yh2)` at sarah-build
phase — well before MadDM. Verdict legal.

### B. `N` is Mathematica builtin — VERIFIED
`wolframscript -code 'Information[N]'` returns `FullName -> System\`N`,
`Attributes -> {Protected}`, `Usage -> N[expr] / N[expr, n]`. Sonnet's hypothesis
is correct: `N` is the numeric-precision built-in. Shadowing it with a
`Protected` symbol in `parameters.m` is not legal Mathematica.

### C. `N::precbd` errors → empty UFO — VERIFIED
- sarah.log (worktree-local at `.playtest/sd-B/state/models/singlet_doublet_b/sarah_output/sarah.log`)
  contains **188** `N::precbd|StringJoin::string` lines (sonnet's "200+" is a
  rounded-up but directionally-honest claim; `General::stop` truncated further
  output, so true count is higher).
- UFO `vertices.py` in sd-B has **2 total `V_` entries, 0 of which mention `Chi`**.
  PT-A's UFO was not preserved in sd-A worktree (state cleaned), but sd-A
  result.json shows MadDM ran cleanly to 0.292 — implying Chi vertices were
  present. Sonnet's "32 in A" is unverifiable post-hoc but the qualitative
  asymmetry (32 vs 0 → 2 vs 0) is unambiguous.
- `check_vertices.py` returned exit=1 with both `VERTICES_MISSING(yh1)` and
  `VERTICES_MISSING(yh2)` per transcript-B.md. Detection mechanism real.

### D. Detection cleanliness — CLEAN
A next-day physicist tracing the failure would see:
1. `build.py` exits 0 with `status: built` (silent failure).
2. `check_vertices.py` exits 1 with two clear `VERTICES_MISSING` blockers.
3. `run_spheno.py` exits 1 with `SPHENO_COMPILE_FAILED` + Fortran syntax errors.
4. Grep on sarah.log immediately shows `N::precbd` flooding.

The UI-level signal (`check_vertices.py`) is loud and points at the right
place. Time-to-root-cause for an experienced user: ~5 min. SARAH's silent
exit-0 is the only annoying bit (logged as sd-B-003).

### E. Issues triage
- **sd-B-001 (major, N shadows N[])**: SOLID. Root-cause correctly identified.
  `fix_owner_hint=skill_prose`, `expected_fix_scope=skill_prose`. In-scope for
  Phase 2 (singlet-doublet skill prose).
- **sd-B-002 (major, validate_spec.py gap)**: REAL.
  `plugins/model-building/skills/sarah-build/scripts/validate_spec.py:77-99`
  defines `_RESERVED_FIELD_NAMES` and `_RESERVED_PARAM_NAMES`; the param set is
  `{g1,g2,g3,Yu,Yd,Ye,v,mu2,\[Lambda],ThetaW,ZZ,ZW,Vu,Vd,Uu,Ud,Ve,Ue,AlphaS,e,
  Gf,aEWinv,mH2}`. No mixing-matrix coverage; no Mathematica-builtin coverage;
  `N` accepted. Validation gap confirmed. **HOWEVER**: this file lives at
  `plugins/model-building/**` which is *forbidden* by the plan's PT-B scope
  guard (line 87 + line 259). Phase-2 ineligible under SD scope. Should be
  escalated to manager as cross-plugin issue.
- **sd-B-003 (minor, SARAH exit 0 with corrupted UFO)**: REAL — build.py has no
  log scan post-build. `fix_owner_hint=tool_driver`, again outside SD scope.
  Not a sonnet exaggeration but also not Phase-2-eligible under SD plan.

### F. Schema validation
The plan's `summary.schema.json` covers per-model **demo** `summary.json`
(`model ∈ {singlet-doublet, 2hdm-a, dark-su3}`, requires `model, run_at, ran,
skipped_constraints, artifacts_dir, headline`). The playtest's `summary-B.json`
is a different ad-hoc playtest-result document, not subject to that schema.
N/A — not a deviation.

### G. Wall time 3 min — PLAUSIBLE
sd-A wall = 5.4 min (full pipeline through MadDM + plotting). sd-B halted at
SPheno compile. SARAH build alone took 23s per transcript-B. sd-B skipped
MadDM entirely (the long pole — sd-A spent ~3-4 min in MadDM alone). 3 min for
preflight + Q1-Q4 simulation + SARAH 23s + SPheno fail + diagnostics is
consistent. Not short-circuited.

### H. Phase 2 entry decision — NO-GO for SD-B
- sd-B-001: in-scope (skill_prose under singlet-doublet) — Phase-2-eligible,
  but `auto_fixable` requires the prose change to make the run pass; the
  practitioner would still type `N` if instructed. The right fix is in
  `lagrangian-builder` interview prose to forbid single-letter mixing-matrix
  names — that's `plugins/hep-ph-demo/skills/lagrangian-builder/**`, also
  outside the SD scope guard (line 87: SD-allowed dirs are
  `plugins/hep-ph-demo/skills/singlet-doublet/**` only).
- sd-B-002: `plugins/model-building/**` — **forbidden**.
- sd-B-003: `plugins/model-building/**` — **forbidden**.

All three issues are legitimate but escape SD's fix scope. Phase 2 SD entry is
**NO-GO**: an opus reviewer in fix-loop would mark every plausible diff as
`aborted_scope` (plan §"Stopping rules" line 302 — any aborted_scope halts).

Manager should: (1) accept PT-B PASS, (2) escalate sd-B-001/002/003 as cross-
workstream issues for a future `model-building` workstream or `lagrangian-
builder` workstream, (3) skip SD Phase 2.

### I. Cross-workstream flock alarm — INDIRECT CORROBORATION
sd-B did NOT independently confirm flock breakage because the pipeline halted
at SPheno compile, before any flock-on-maddm.lock was attempted. transcript-B
line 134 says "FIFO queue: sd-B acquired" but the actual `flock -x -w 120
sarah.lock` may or may not have been invoked — the sonnet did not log that
detail. **PT-A's sd-A-004 stands as the only direct evidence**: "flock not
available on macOS … exit=127". The SD-A reviewer's flock concern is
unrebutted. Recommend: trust sd-A-004; treat as confirmed for the workstream.

### J. Plan deviations
1. **Artifact storage path mismatch.** Plan §"Recording targets" (line 225)
   prescribes `.playtest/sd-X/result.json` etc. PT-A wrote artifacts there AND
   to `/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-.../workstreams/
   singlet-doublet/playtest/{runbook-A,issues-A,summary-A,verdict-A,…}.md/json/
   jsonl`. PT-B wrote ONLY to the worktree path
   (`.../sd-B/.shift-manager/.../playtest/`), not to the main repo's
   `.shift-manager/.../playtest/`. Manager (or PT-B sonnet) should copy the B
   artifacts into the canonical location for parity with A. Minor.
2. **`result.json` not in canonical playtest filename set.** PT-A wrote
   `.playtest/sd-A/result.json` (per plan line 182). PT-B wrote `verdict-B.md`
   + `summary-B.json`. Both styles present; this matches the plan's expanded
   recording targets but the asymmetry vs A's `result.json` is a one-line
   convention drift, not substantive.
3. **No `result.json` written by PT-B with VERDICT first 5 lines.** Plan B
   prompt line 217 inherits A's "first 5 lines EXACTLY: VERDICT/BASELINE_USED/
   HARDCODED_REFERENCE/WORKSTREAM/VARIANT". `verdict-B.md` lines 1-5 do match
   this convention — verdict-B.md is the de-facto result.json. OK.

---

## Cross-Variant comparison (A vs B)

|  | Variant A (canonical) | Variant B (ZN→N) |
|---|---|---|
| Verdict | PASS (omega_h2=0.292) | PASS (alternate, surfaced clash) |
| Wall | 5.4 min | 3 min (halted early) |
| Pipeline reach | end-to-end | halted at SPheno compile |
| omega_h2 | 0.292 (matches hardcoded ref) | not computed |
| SARAH exit | 0 | 0 (corrupted UFO) |
| Major issues | 2 (sd-A-003, sd-A-004) | 2 (sd-B-001, sd-B-002) |
| Flock concern | DIRECT (sd-A-004 exit=127) | INDIRECT (didn't reach lock) |

**What B's failure tells us that A's pass doesn't:**
1. **`validate_spec.py` reserved-name coverage is incomplete** for both
   Mathematica builtins AND mixing-matrix names. A passed only because `ZN`
   happens to be safe; the validator gives no signal one way or the other.
2. **SARAH silent-fail mode is a real risk.** A clean run hides this. B exposes
   it: the build phase exits 0 with broken UFO, and only the post-build
   `check_vertices.py` rescues the situation. Without that diagnostic, A could
   have produced wrong physics on a different perturbation.
3. **The plan's "MSSM ZN clash" hypothesis was wrong-mechanism but
   right-direction.** Real failure is Mathematica `System\`N` shadowing, not
   SLHA NMIX collision. The plan's "N is reserved for MSSM neutralinos"
   intuition was mechanically incorrect but operationally protective. Update
   skill prose to cite Mathematica builtins, not just MSSM convention.
4. **A's flock blocker (sd-A-004) is the only blocker the workstream surfaces.**
   B's pipeline halt before MadDM means B cannot independently corroborate.
   Trust A.

---

## Phase 2 entry — NO-GO

All three sd-B issues fix-scope to `plugins/model-building/**` or
`plugins/hep-ph-demo/skills/lagrangian-builder/**`, both forbidden by the SD
plan's scope guard. SD Phase 2 fix-loop would immediately abort_scope on any
plausible diff. Skip Phase 2 for SD-B.

**Recommended manager action:** write `escalation.md` cross-referencing
sd-B-001/002/003 as input to a future model-building or lagrangian-builder
workstream; close SD with PT-A pass + PT-B pass-via-alternate.

---

## Manager decisions needed

1. **Accept PT-B PASS-WITH-NOTES** and update sd-tries.json (done below).
2. **Decide on cross-plugin escalation** for sd-B-002 (validate_spec.py
   blacklist) and sd-B-003 (build.py log scan). These are real defects with
   high leverage (would have caught the failure at spec-validation time) but
   live outside SD's fix scope. Recommend: open issue in a separate file at
   `.shift-manager/run-20260424-202956/state/cross_plugin_escalation.md`.
3. **Confirm flock blocker disposition** with SD-A reviewer's verdict. PT-B
   does not corroborate; defer to SD-A.
4. **Re-playtest decision**: plan §"Re-playtest" allows one re-run if budget
   remains and `playtest_attempts < 2`. PT-B's failure is a
   plan-anticipated success; no re-playtest needed for B. A re-playtest of A
   is also unnecessary (A passed cleanly).
5. **Artifact path symmetry**: ask manager to copy B artifacts from worktree
   into canonical `/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-
   20260424-202956/workstreams/singlet-doublet/playtest/` so review-time tooling
   sees both A and B side by side.
