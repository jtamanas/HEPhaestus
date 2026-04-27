# Verdict — Variant A merge-confirm re-run (sd-T5)

## Verdict

**PASS — Variant A confirmed 5/5 IN_BAND on branch `sd/playtest-r2-20260425` (pre-shift HEAD `611d12e`).**

Prior merge: `sd/fix-r1-20260424` landed on `main` at `54ef9cb` (parent `5934f95`). This shift does NOT re-merge that branch; it performs a fresh 5-run band-membership screen against the current branch tip.

## Per-run results

| Run | Ωh² | Band [0.286, 0.298] | Result |
|-----|-----|---------------------|--------|
| run-1 | 0.292 | ✓ | IN_BAND |
| run-2 | 0.292 | ✓ | IN_BAND |
| run-3 | 0.292 | ✓ | IN_BAND |
| run-4 | 0.292 | ✓ | IN_BAND |
| run-5 | 0.292 | ✓ | IN_BAND |

**5/5 IN_BAND.**

Run-1 Ωh² = **0.292** (task sd-T2; commit `1c79021`).

## Determinism screen

Artefact: [`determinism-screen.json`](determinism-screen.json)

This is a band-membership screen ("screen, not metric") — not a stochastic analysis. The 5 values [0.292, 0.292, 0.292, 0.292, 0.292] all fall within [0.286, 0.298]. Verdict in artefact: `PASS`.

Reviewer note (sd-T3): MadDM reports 3 significant figures only. The uniform value "0.292 exact" cannot distinguish true bit-determinism from sub-0.0005 stochasticity. This limitation is recorded as a CLOSEOUT note and does not affect the band-membership verdict.

## Schema validation

Artefact: [`schema-validation.json`](schema-validation.json)

All 5 `summary.json` files validated against schema v1.1 (`_shared/summary.schema.json`). Result: **schema PASS×5**.

Reviewer note (sd-T4): the artefact is `schema-validation.json` (not `schema-validation.log` as literally named in PLAN_FINAL). Minor deviation recorded here; contents are equivalent.

## Benchmark parameters

- MS = 150 GeV, MPsi = 500 GeV, y = 1, θ = 0
- Mixing: ZN, Constraint: relic, Model: SingletDoublet_A
- Branch tip at run time: `611d12e`

## Pass/fail signal

Four required literal strings present: `611d12e`, `54ef9cb`, `5934f95`, `"screen, not metric"` (see above and determinism-screen.json).

Five-run band-membership screen: 5/5 IN_BAND → `PASS`.
Schema validation: 5/5 PASS.
