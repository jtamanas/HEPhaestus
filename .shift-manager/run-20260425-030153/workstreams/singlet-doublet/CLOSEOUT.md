# CLOSEOUT — singlet-doublet workstream (run-20260425-030153)

**Final state: PASS (5/5 IN_BAND) — auto-merge gate CLEAR per FINAL_SCOPE; sd-T9 may proceed.**

Branch: `sd/playtest-r2-20260425` | Pre-shift HEAD: `611d12e`

---

## Merge audit (NOT a merge action this shift)

Prior `sd/fix-r1-20260424` already merged to main at `54ef9cb` (parent tip `5934f95`); this shift performed no merge of that branch.

Shift-start HEAD: `611d12e` (merge of `sd/playtest-B-20260424` — Variant B N-shadow finding).

Cross-link: `ORIENTATION_GLOBAL.md` lines 41-44, 53 — "Recent merge history" and "Git log" tables confirm `54ef9cb` ← `sd/fix-r1` and `611d12e` ← `sd/playtest-B` as the two most recent singlet-doublet merges prior to this shift.

NOTE: This shift performed NO new merge. sd-T9 (diff-discipline gate + review) and sd-T10 (merge) are separate downstream tasks.

---

## Variant-A re-playtest results

Pre-shift HEAD: `611d12e`. Band: `[0.286, 0.298]`. Screen label: `"screen, not metric"`.

Parameters: MS=150 GeV, MPsi=500 GeV, y=1, θ=0; mixing=ZN, constraint=relic, model=SingletDoublet_A.

| Run | Ωh² | ∈ [0.286, 0.298]? | Verdict |
|-----|-----|-------------------|---------|
| run-1 | 0.292 | YES | IN_BAND |
| run-2 | 0.292 | YES | IN_BAND |
| run-3 | 0.292 | YES | IN_BAND |
| run-4 | 0.292 | YES | IN_BAND |
| run-5 | 0.292 | YES | IN_BAND |

**5/5 IN_BAND.**

Run-1 Ωh² = 0.292 (sd-T2; commit `1c79021`). Verdict artefact: `playtest/determinism-screen.json`.

Reviewer caveat (sd-T3, opus): MadDM reports 3 significant figures only. The uniform value "0.292 exact" cannot distinguish true bit-determinism from sub-0.0005 stochasticity. This is a tool-precision limitation, not a workstream failure — recorded here and does not affect the band-membership verdict.

---

## Schema validation

All 5 `summary.json` files validated against schema v1.1 (`plugins/hep-ph-demo/skills/_shared/summary.schema.json`).

Result: **schema PASS×5**

Artefact: [`playtest/schema-validation.json`](playtest/schema-validation.json) (see also `playtest/schema-validation.log` alias).

Per-run summary:
- [PASS] runs/run-1/demo_output/singlet-doublet/summary.json
- [PASS] runs/run-2/demo_output/singlet-doublet/summary.json
- [PASS] runs/run-3/demo_output/singlet-doublet/summary.json
- [PASS] runs/run-4/demo_output/singlet-doublet/summary.json
- [PASS] runs/run-5/demo_output/singlet-doublet/summary.json

Reviewer caveat (sd-T4, opus): the artefact is `schema-validation.json` (not `schema-validation.log` as literally named in PLAN_FINAL §sd-T4). Minor deviation — contents are equivalent. Recorded here for audit completeness.

---

## Doc-edit diff summary

Output of `git diff --stat main..sd/playtest-r2-20260425 -- 'plugins/hep-ph-demo/skills/singlet-doublet/SKILL.md'`:

```
 .../hep-ph-demo/skills/singlet-doublet/SKILL.md    | 36 ++++++++++++++++++++++
 1 file changed, 36 insertions(+)
```

Edit: appended `## Known limitations` section to `SKILL.md` (sd-T6; commit `7d5311e`). Path-restricted to the allowed file only; diff-discipline compliant per PLAN_FINAL allow-list.

---

## Variant-B error string (regression anchor)

Verbatim contents of `variant-b-error.txt` (sd-T7):

```
ERROR_STRING: N::precbd: Requested precision <xgen> is not a machine-sized real number
OCCURRENCE_COUNT: 4
SOURCE: .shift-manager/run-20260424-202956/workstreams/singlet-doublet/playtest/verdict-B.md
CAPTURED_AT: 2026-04-25T03:01:53Z
```

Artefact: `variant-b-error.txt` (this workstream dir). N::precbd is a Mathematica kernel precision error surfaced by SARAH during Variant B's SPheno run. Occurrence count: 4. Plugin owners for follow-up: sd-A-001 (lagrangian-builder) and sd-A-003 (model-building) per sd-T6 Known limitations cross-references. See Handoff queue below.

---

## Handoff queue

| id | owner-plugin | summary | age |
|----|--------------|---------|-----|
| sd-A-001 | lagrangian-builder | SARAH/SPheno Variant B: N::precbd Mathematica precision error (4 occurrences) blocks non-ZN mixing paths | 1-shift-old |
| sd-A-002 | hep-ph-demo/demo | Demo scaffold: pre-seeded SPheno SPC files and 232-file MadDM output bloat inflate run directories; needs cleanup pass | 1-shift-old |
| sd-A-003 | model-building | SARAH model SingletDoublet_A: Variant B triggers N::precbd; root cause in model file or SARAH interface | 1-shift-old |
| sd-A-004 | hep-ph-demo/demo | Demo scaffold: MadDM 3-sig-fig output precision precludes sub-0.5% determinism verification for relic density | 1-shift-old |

---

## Determinism screen verdict

Verdict: **PASS**

Label: `"screen, not metric"` — this is a band-membership screen, not a stochastic metric. Forbidden keys (`stdev`, `std`, `sigma`, `mean`, `average`, `coefficient_of_variation`, `cv`) are absent from all artefacts (enforced at sd-T9).

Five values inline: [0.292, 0.292, 0.292, 0.292, 0.292] — all ∈ [0.286, 0.298].

Artefact: [`playtest/determinism-screen.json`](playtest/determinism-screen.json)

```json
{
  "label": "screen, not metric",
  "band": [0.286, 0.298],
  "values": [0.292, 0.292, 0.292, 0.292, 0.292],
  "all_in_band": true,
  "verdict": "PASS"
}
```

Reviewer caveat (sd-T3): MadDM 3-sig-fig precision means "0.292 exact" cannot distinguish bit-determinism from sub-0.0005 stochasticity. Recorded as sd-A-004 in handoff queue; does not affect the band-membership verdict.

---

## Deviations

- **Validator wrapper vs upstream extension**: PLAN_FINAL §sd-T4 literally specifies `python3 plugins/hep-ph-demo/skills/_shared/test_summary_schema.py <summary.json>`. This shift implements `validate_one.py` as a standalone wrapper under the run-dir (`playtest/validate_one.py`) rather than extending `_shared/test_summary_schema.py`. Rationale: (1) `_shared/` edits carry cross-workstream blast radius (2HDM+a and dsu3 depend on the same file); (2) wrapper is ~10 lines, fully contained, and deletable without side effects; (3) diff-discipline is the dominant constraint this shift. The wrapper honours the spirit of PLAN_FINAL crit. 5 — each `summary.json` is validated against schema v1.1. Recorded per PLAN_FINAL §"Validator-wrapper vs upstream-extension decision" and PLAN_FINAL §CLOSEOUT structure item 8.

- **Artefact name deviation**: `schema-validation.json` committed as `.json` (not `.log` as PLAN_FINAL §sd-T4 pass/fail signal states). Contents are equivalent. Noted in §Schema validation above.

---

## Task audit trail

All tasks completed this shift on branch `sd/playtest-r2-20260425`:

| task | cycles | final verdict | notes |
|------|--------|---------------|-------|
| sd-T0 [c1] | 1 | REVISE | dirty-tree FAIL; D5 accept-list extension required |
| sd-T0 [c2] | 2 | ACCEPT (DONE) | 5/5 PASS w/ D5 accept-list; worktree created |
| sd-T1 [c1] | 1 | REVISE | BLOCKING: schema path traversal wrong; Q1-Q4 paraphrased not verbatim |
| sd-T1 [c2] | 2 | ACCEPT (DONE) | schema path parents[5] correct; Q1-Q4 byte-verbatim; commit `a14f590` |
| sd-T2 | 1 | ACCEPT (DONE) | Ωh²=0.292 IN_BAND; commit `1c79021` |
| sd-T3 | 1 | ACCEPT (DONE) | 5/5 IN_BAND; commits `593dec3`, `2d7691e` |
| sd-T4 | 1 | ACCEPT (DONE) | 5/5 schema PASS; commit `82a031a`; artefact .json not .log (noted) |
| sd-T5 | 1 | ACCEPT (DONE) | 4/4 literal strings; commit `8c9c51a` |
| sd-T6 | 1 | ACCEPT (DONE) | 9/9 strings; commit `7d5311e`; diff-disciplined |
| sd-T7 | 1 | ACCEPT (DONE) | N::precbd verbatim + count=4 captured |
| sd-T8 | 1 | (this document) | CLOSEOUT |

---

## References

- Prior shift CLOSEOUT: `.shift-manager/run-20260424-202956/` (continuity; `sd/fix-r1-20260424` merged at `54ef9cb`)
- Manager decision D5: `state/MANAGER_DECISIONS.md` §D5 — dirty-tree accept-list extension for sd-T0
- FINAL_SCOPE: `.shift-manager/run-20260425-030153/brainstorm/singlet-doublet/FINAL_SCOPE.md`
- PLAN_FINAL: `.shift-manager/run-20260425-030153/plan/singlet-doublet/PLAN_FINAL.md`
- ORIENTATION_GLOBAL: `.shift-manager/run-20260425-030153/scoping/ORIENTATION_GLOBAL.md` lines 41-44, 53
