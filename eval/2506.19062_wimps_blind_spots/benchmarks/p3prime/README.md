# P3' SPECTRUM-PREP — loop-level SPheno spectra for the re-posed Hisano anchor

Protocol: `DESIGN-ITEM4-AMENDMENT6.md` Ruling 1 (do not duplicate; read it there).
This half generates the LOOP-LEVEL SPheno spectra + sidecars; the Wolfram/LoopTools
projection is a later stage (kernel-gated) and is NOT run here.

Pipeline per leg: `SPhenoSingletDoublet(LesHouches.in, flag55=1, flag56=1)` ->
`SPheno.spc` -> `prepare_point.prepare_point(dm_pdg=9958431)` -> `point.json`.
Parametrization: MPsi = m_chi = 500, d-quark external flavor, held across legs;
`yh1 = y cos(theta)`, `yh2 = y sin(theta)`.

## THE THREE LEGS (as generated, theta = -0.152 held)

| leg | MS (TeV) | y | measured singlet frac \|N_s\|^2 (SPheno ZNMIX) | m_chi1 | split chi2-chi1 | m_h | loop non-tachyonic | g_h_chi1chi1 (Eq.7) | tree DD / loop floor |
|-----|----------|------|-----------------------------|--------|------|-------|------|---------|---------|
| L1  | 3  | 1.00 | 1.762e-3 | 480.80 | 10.50 | 106.97 | YES | -3.39e-2 | 18.3x |
| L2  | 3  | 0.35 | 2.112e-4 | 493.94 | 1.24  | 126.21 | YES | -4.22e-3 | 2.3x  |
| L3  | 10 | 0.50 | 3.032e-5 | 479.40 | 0.77  | 125.73 | YES | -2.27e-3 | 1.2x  |

- All three are LOOP-level (flag 55=1, two-loop-Higgs flag 56=1), non-tachyonic,
  positive m_h. L2/L3 have physical m_h ~ 126; L1's m_h = 107 (depressed by the
  heavy-singlet tadpole but positive).
- Bar-4 scaling pair (L1 vs L2, same MS=3, same theta): fraction ratio 8.3x (~10x).
- Bar-1 decoupling pair (L2 MS=3 -> L3 MS=10, same theta): both < 1e-3.
- Spectra live in scratch `/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch/{L1,L2,L3}/`
  (`SPheno.spc.SingletDoublet`, `point.json`). Sidecars + leg-configs committed here.

## TWO ITEMS FLAGGED TO THE DESIGN AUTHORITY (see handoff / SendMessage to main)

### (A) Blind-spot vs fraction is OVER-CONSTRAINED (protocol question, not resolved here)
The singlet fraction of chi1 and the tree h-chi1-chi1 coupling are the SAME order
parameter (both measure S-D mixing in chi1). The decoupled-regime blind spot is
`theta = -pi/4` (NOT -0.152; -0.152 solved Eq.8 only for the ORIGINAL m_chi1=150
benchmark). At `theta=-pi/4`, `y1=-y2` and chi1 is an EXACT pure doublet:
singlet fraction == 0 AND tree coupling == 0 for ALL y. You cannot hold the blind
spot AND have a nonzero fraction. Keeping tree Higgs-exchange DD at/below the
Hisano loop floor needs `|g_h_chi1chi1| <~ 1.85e-3`, which caps fraction at ~1e-4
(MS=3) / ~1e-4-1e-3 (MS=10) -- below L2/L3's <1e-3 bar and far below L1's 1e-2.
Consequence: L1 (fraction 1e-2 AND blind spot) is impossible; L2/L3 approach the
blind spot only as fraction -> 0. Legs were generated at theta=-0.152 (P3 lineage);
if the authority wants the DECOUPLED legs sitting closer to the true blind spot,
lower y (L2/L3 get cleaner, fraction smaller) or set theta=-pi/4 (fraction ~ noise).

### (B) L1 fraction ~1e-2 at loop level is a NAMED REFUSAL (vacuum wall)
At MS=3 TeV the EW vacuum destabilizes (`NaN ... tadpole equations for m2SM`) at
`y ~ 1.4` for EVERY theta tried (-pi/4, -0.25, -0.152, -0.10, -0.05, 0, +pi/4),
capping the loop-level singlet fraction at ~2e-3 (with physical m_h) / ~4e-3 (with
unphysical m_h~30). Fraction 1e-2 needs y~2.7 -> no loop spectrum (`NaN in MHp2`,
or a spurious wrong-vacuum m_h~1107 runaway that must be rejected). The full
MS/theta/y search is in `wall_map.json`. L1 as shipped is the CLOSEST loop-level
approach (fraction 1.762e-3 at y=1.0, m_h=107), NOT the 1e-2 target. A tree-mass
fallback would invalidate the leg (Ruling 1) and is deliberately NOT taken.
Note: MS=10 TeV loop spectra ARE reachable at low y (m_h~126 at y<=0.5), so L3
needs NO MS-substitution -- contrary to the P3 fixed-y=1 tachyon note.

## PROJECTION COMMAND (next, kernel-gated stage — NOT run here)
Per leg, drive the production projector on the leg's `point.json` (same recipe as
P3, `/tmp/item4-p3-handoff.md` "Pipeline provenance"):

```
DRV=<worktree>/plugins/hep-ph-toolkit/skills/looptools/scripts/run_eval_sd.wls
AMP=/Users/yianni/.claude/jobs/c703354a/tmp/subexpr-fix/reduce_chi1/amp_reduced.m
LT=/Users/yianni/LoopTools/LoopTools-2.16
PROJ=<worktree>/plugins/hep-ph-toolkit/skills/looptools/scripts/sd_projection.wl
BM=<worktree>/eval/2506.19062_wimps_blind_spots/benchmarks
export HEPPH_RUN_WOLFRAM_TESTS=1
# for L in L1 L2 L3:
cd <scratch>/$L
wolframscript -script "$DRV" "$AMP" <scratch>/$L/point.json none <scratch>/$L/eval_output.json "$LT" > driver.log 2>&1
MCHI=$(python3 -c "import json;print(json.load(open('point.json'))['m_dm_gev'])")
wolframscript -script $BM/p3_extract_cours.wls "$PROJ" "$AMP" <scratch>/$L/amp_dd.m "$MCHI" 4.67e-3 <scratch>/$L/cours_extract.json
```
Then compare vs Hisano (`hisano_1104_0228.py` / `p3_compare.py`) against the
AMENDMENT6 pre-registered bars (1 decoupling drift <25%, 2 PASS |ratio| in [0.2,5]
& same sign at both decoupled legs, 3 FAIL, 4 scaling exponent in [0.5,2]).
`4.67e-3` = m_d (GeV). `<worktree>`/`<scratch>` per "Artifact paths" below.
```
```
