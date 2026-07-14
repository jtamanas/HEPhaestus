# P3' SPECTRUM-PREP — loop-level SPheno spectra for the re-posed Hisano anchor

## STATUS — P3' campaign verdict (design-ratified; AMENDMENT8)

Ratified in `../../DESIGN-ITEM4-AMENDMENT8.md` (Ruling 1). This branch is the
CAMPAIGN RECORD of a well-posed, design-ratified FAIL — not a physics
validation. No coefficient here is asserted as a validated physics value.

- **BAR-3: FAIL (ratified).** The decoupled pure-doublet loop-floor C_scalar
  disagrees with Hisano (arXiv:1104.0228) in SIGN and magnitude: floor
  ~+1.0e-11 vs Hisano −2.23e-12, |ratio| ~4.5–5×. An independent adversarial
  robustness review CONFIRMED the FAIL is robust and well-posed ("could not
  break it") — five attacks tried, floor stays wrong-sign and ~4.4–4.7× after
  contamination subtraction across mixing exponents p=0.5–2.0, campaign numbers
  bit-reproduce; full substance in `ROBUSTNESS_REVIEW.md` (this directory). The
  signature is STRUCTURE-SPECIFIC (twist-2 sign AGREES at all four legs while
  scalar flips), so a global/wholesale-sector sign flip is excluded.
- **BAR-4: POSITIVE.** The mixing-physics extrapolation is well-behaved — the
  admixture excess monotonically shrinks L1→L2, exponent ~1.25 raw / ~1.09
  m_h-corrected, flatness ~9.6%. Confirms the P3 excess was real
  singlet-admixture loop content (the instrument measures real physics).
- **DIAGNOSE ROUND: OPEN.** A structure-specific scalar-sector sign slip is
  suspected; probes S1–S4 / D1–D3 (see AMENDMENT8 Ruling 2) are pursued on a
  SEPARATE branch (`item4-diagnose-*`). NOT resolved on this branch. Production
  σ_SI is formally PREEMPTED until a conviction + fix + L2/L3 re-run passes.
- **HONEST CAVEAT (θ-placement).** The four verdict legs sit at θ=−0.152, NOT
  the true decoupled blind spot θ=−π/4; a residual tree coupling
  g_hχ1χ1=−5.83e-4 remains (tree_DD/loop_floor ~0.31). This does NOT soften the
  FAIL: the projected amplitude is LOOP-ONLY (no tree χ1χ1h term in C_ours;
  verified by code-read of `amp_reduced.m`), and the residual mixing-induced
  coupling vanishes as singlet fraction→0 — its imprint lives inside the
  Bar-4-extrapolated admixture excess, which is already accounted. A θ=−π/4 leg
  at fraction→0 would be the definitive hole-closer but is near-singular
  (m_χ1→m_D forces sin2θ=−1); the campaign relied on the fraction→0
  extrapolation instead.
- **Optional post-fix validation:** θ=−π/4 decoupled leg — near-singular by
  construction (m_χ1→mD forces sin2θ=−1); deferred per manager ruling this round.

Protocol: `DESIGN-ITEM4-AMENDMENT6.md` Ruling 1 (do not duplicate; read it there).
This half generates the LOOP-LEVEL SPheno spectra + sidecars; the Wolfram/LoopTools
projection is a later stage (kernel-gated) and is NOT run here.

Pipeline per leg: `SPhenoSingletDoublet(LesHouches.in, flag55=1, flag56=1)` ->
`SPheno.spc` -> `prepare_point.prepare_point(dm_pdg=9958431)` -> `point.json`.
Parametrization: MPsi = m_chi = 500, d-quark external flavor, held across legs;
`yh1 = y cos(theta)`, `yh2 = y sin(theta)`.

## CAMPAIGN COMPLETE (6R3) — FOUR kernel legs projected, all bars computed

Protocol as re-pinned by 6R1/6R2/6R3: four legs all at theta=-0.152; verdict
legs placed by FRACTION only (loop-only amp => no tree in C_ours). All four are
LOOP-level (flag 55=1, 56=1), non-tachyonic. C_ours = Re(R_S_S) rotated-complete
scalar; C_Hisano = f_q*m_d (pure doublet n=2, Y=1/2, d-quark) at each leg's m_chi1.

| leg | role | MS | y | frac \|N_s\|^2 | m_chi1 | m_h | Re(C_ours) | C_Hisano | ratio | scalar sign | twist2 sign |
|-----|------|----|----|------|--------|------|-----------|----------|-------|------|------|
| L1  | scaling ref | 3  | 1.00 | 1.762e-3 | 480.80 | 106.97 | +4.181e-11 | -3.025e-12 | -13.82 | DISAGREE | agree |
| L1b | scaling partner | 3 | 0.35 | 2.112e-4 | 493.94 | 126.21 | +1.274e-11 | -2.222e-12 | -5.73 | DISAGREE | agree |
| L2  | VERDICT (MS3) | 3 | 0.13 | 2.906e-5 | 495.51 | 126.06 | +1.053e-11 | -2.228e-12 | -4.73 | DISAGREE | agree |
| L3  | VERDICT (MS10) | 10 | 0.50 | 3.032e-5 | 479.40 | 125.73 | +1.154e-11 | -2.229e-12 | -5.18 | DISAGREE | agree |

Instrument health (all legs): completeness ~2.88e-9, rotation ~5e-16, basis rank
256, si_shift ~1.000-1.003 — green. Full raw C_ours in `L*_cours_extract.json`;
bar arithmetic in `campaign_bars.json`; comparison in `campaign_comparison.txt`.

### BARS (MEASURED; formal PASS/FAIL is the design authority's to ratify)
- **BAR 1 flatness gate (L2->L3): PASS** — Re(C_ours) drift 9.6% < 25%. The
  verdict legs measure a genuinely DECOUPLED object (P3's 2.35x drift flattened).
- **BAR 2 PASS: NOT met.** Scalar sign DISAGREES at both verdict legs (C_ours
  positive ~+1.1e-11, Hisano negative ~-2.23e-12); |ratio| L2=4.73 (in [0.2,5]),
  L3=5.18 (just outside).
- **BAR 3 FAIL: FIRES** — flatness met + sign disagrees at both (+ L3 magnitude
  out) => assembly-level construction error indicated. Diagnose SIGN first
  (twist-2 sign AGREES while scalar disagrees = structure-specific slip, not a
  global convention). NB the overall-i rescue is CLOSED per AMENDMENT6 (ours Im
  ~ |C_Hisano| is the named transfer artifact; reported, not invoked).
- **BAR 4 scaling (L1 vs L1b): mixing physics** — excess exponent in fraction
  = 1.25 raw / 1.09 m_h-corrected / 1.21 (3-pt fit); all in [0.5,2], no straddle.
  Excess ratio 14.15x over an 8.3x fraction span. L1 stays (not disqualified).
  Independently corroborates that the P3 excess was real singlet-admixture loop
  content, not an assembly artifact.
- **Cleanliness (verdict legs): PASS** — extrapolated admixture contamination
  L2=1.86e-13 (8.3% of |C_Hisano|), L3=1.96e-13 (8.8%); both < 2.3e-13. (This is
  the admixture excess only; distinct from the floor-vs-Hisano discrepancy above.)
- **BAR 5 twist-2: sign agrees at all legs** (sign-only weight; magnitude
  caveated by the O_Tq bridge + the measured 11.46% twist-2 v-drift sampling
  systematic, design-adjudication pending).

Net measured picture: the decoupled pure-doublet loop floor is now FLAT (bar 1)
and CLEAN (cleanliness) — the P3 confound is removed — but the flat clean floor
DISAGREES with Hisano in SIGN and is ~5x in magnitude, so BAR 3 FAIL fires
(assembly-level, sign-first diagnose round). Bar 4 confirms the mixing-excess
reading. This is a well-posed FAIL, not P3's NO-VERDICT.

## STATUS — theta-naming correction (6R1 R3)
theta=-0.152 is the Eq.-8 blind-spot solution for the m_chi1=150 canonical
benchmark; the exact tree-coupling zero at MPsi-degenerate parameters (m_chi1 ->
MPsi) is theta=-pi/4. Prior arc results at -0.152 are UNAFFECTED (they measured
that benchmark's dip, which is where its physical blind spot is). The distinction
was made operational by the wall map (`wall_map.json`) + the singlet_doublet.py
blind-spot re-derivation. Immaterial to past verdicts; material to leg placement.

## HISTORICAL — spectrum-prep flags + wall analysis (superseded by 6R1/6R2/6R3 above)

The three-leg build below preceded the 6R1-6R3 rulings; retained for the wall map
and the loop-only finding. The old "L2" (y=0.35) is now L1b; the old "L3" (MS=10,
frac 3.03e-5) is re-accepted as the verdict L3; a new L2 (y=0.13, frac 2.9e-5) was
added; L1 unchanged.

## TWO ITEMS FLAGGED TO THE DESIGN AUTHORITY (see handoff / SendMessage to main)

> **AMPLITUDE IS LOOP-ONLY (verified by code-read of `amp_reduced.m`).** The
> projected amplitude is the χ1-pinned 1PI core (32 one-loop diagrams = 2
> triangles + 2 boxes; heads B0i/C0i/D0i only, A0i=0; the 18 `Den[T,m²]` are
> one-loop penguin mediator propagators, 18/18 co-occurring with a loop head,
> ZERO bare tree terms). So the tree χ1χ1h coupling is NOT in C_ours. The
> residual-tree-coupling / contamination numbers in the sidecars describe the
> PHYSICAL σ_SI (tree Higgs exchange), NOT the loop object compared to Hisano.
> For the Hisano comparison only the SINGLET FRACTION (pure-doubletness) matters;
> "at the blind spot" ≡ "zero fraction" ≡ "pure doublet" are the same order
> parameter, so the low-fraction decoupled legs L2/L3 ARE the Hisano-comparable
> points regardless of the exact θ. Item (A) below is thereby SOFTENED (θ=−π/4
> not required); item (B) is unaffected.

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
