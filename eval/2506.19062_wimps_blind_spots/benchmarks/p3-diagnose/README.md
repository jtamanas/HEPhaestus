# P3' diagnose: D1 + D2 + S2/S3 twist-2 discriminator

VALIDATION-ONLY / MEASUREMENT-ONLY. **No fix is coded in this directory.** All
artifacts here diagnose the BAR-3 FAIL from the P3' campaign (`benchmarks/p3prime/`):
our loop-induced spin-independent scalar Wilson coefficient `C_ours` is FLAT and
CLEAN across the verdict legs but carries the WRONG SIGN vs the Hisano
1104.0228 anchor (`C_ours` ~ +1.05e-11 / +1.15e-11 GeV^-2 at L2/L3 vs
`C_Hisano` ~ -2.23e-12). This directory localizes the sign fault to a single
sector-relative assembly sign.

## Files
- `sector_filter.wls` / `classify_sectors.wls` — split the symbolic 1PI amplitude
  into {triangle, directBox (S-channel), crossedBox (U-channel)} by zeroing PV heads.
- `d1_kernel.sh` — per-(leg,sector) driver+extract into the sector cours JSONs.
- `L{2,3}_{triangle,directBox,crossedBox}_cours.json` — per-sector kernel extracts.
- `d1_analysis.py` / `d1_analysis.json` — 8-sign-combo which-single-flip analysis.
- `d2_summary.py` / `d2_analysis.json` — crossed/direct box crossing-sign corroboration.
- `s2_s3_twist2_discriminator.py` / `s2_s3_twist2_analysis.json` — S2-vs-S3 on the
  twist-2 axis (NO kernel; sanctioned Hisano transcription only).

## Outcome (see also `/tmp/item4-d1d2-handoff.md`)
- **S1 (crossed-vs-direct box fermion-flow sign): EXCLUDED.** Flipping the crossed
  box ALONE fails to restore the Hisano sign at either leg (D1); direct and crossed
  boxes are same-sign additive and the projector crossing-rotation is exact (D2).
- **S2 (box-vs-triangle relative assembly sign): CONVICTED** on the SCALAR axis.
  Flipping the WHOLE box relative to the triangle is the UNIQUE single-sector flip
  that restores scalar-sign agreement + |ratio| in [0.2,5] + twist-2 positivity at
  BOTH verdict legs. Since |box|>|triangle| and Hisano<0, the wrong sign sits on the
  BOX side.
- **S3 (scalar-projection-only sign): NOT favoured** (see twist-2 discriminator below).
- **D3 (synthetic external-sign control) still owed** to pin the ABSOLUTE wrong-sign
  sector against an external reference and then apply the fix + L2/L3 re-run.

## D2 as-built deviation (recorded honestly)
D2 as-built is **corroborative only**: it is the same-kinematics crossed/direct
ratio + projector rotation-exactness, **NOT** the pre-registered s<->u
crossing-kinematics identity. Team-lead ruled NOT to re-run the proper D2 because
D1's 8-sign-combo enumeration excludes S1 outright. **S1 exclusion rests on D1**;
D2 is an independent same-kinematics check that is consistent with it.

## S2-vs-S3 twist-2 discriminator — INCONCLUSIVE (verdict WITHHELD)
Predictions were **pre-registered before compute** (locked in the script header and
`PREDICTIONS` dict): S2 => Hisano twist-2 at the ADDITIVE ~1.7e-10/2.2e-10 scale;
S3 => Hisano twist-2 at the CURRENT ~8e-12/5e-11 scale (O_Tq units). Scalar anchor
reproduces the campaign -2.23e-12 at both legs (inputs confirmed identical).

**Normalization is NOT apples-to-apples**, so per the pre-registered gate no magnitude
verdict is issued:
- Under the sanctioned static-limit bridge `C_hisano_OTq_equiv = (3/4)(g1+g2)m_q/M`,
  |C_Hisano_twist2| = **4.93e-15 (L2) / 5.09e-15 (L3)** — ~1.6e3–1.0e4x BELOW even
  the current-scenario O_Tq value, matching NEITHER prediction.
- The "closer scenario" FLIPS with the normalization choice: the physics bridge
  favours current/S3, the raw g_sum juxtaposition (NOT operator-matched) favours
  additive/S2. The residual factor between them (~1.4e5) dwarfs the ~20x S2/S3 gap.
- Sign does not discriminate: Hisano twist-2 is POSITIVE (g_sum>0), consistent with
  BOTH our positive scenarios.

Conclusion: the twist-2 axis neither confirms S2 nor rescues S3 — it is dominated by
the unsettled twist-2 operator normalization (the C^(1)/C^(2) split is an unshipped
item-4 deliverable). **The S2 conviction stands on the SCALAR axis (D1)**, which is
apples-to-apples and sign-restoring. S3 gains no positive support (in the physics
bridge its own magnitude is off by ~1.6e3x).

## Reviewer-hardening notes (for the D3 / fix round)
1. **S2 (+,-,-) is the UNIQUE admissible flip over the FULL 8-sign-combo space.**
   Twist-2 positivity forces the triangle sign, which forces BOTH boxes to flip
   together — no other combination satisfies scalar-sign + |ratio| in [0.2,5] +
   twist-2 positivity at both legs.
2. **Sectors sum to full within 0.18–0.64%** at both legs (linear-projection
   reconstruction of `C_scalar`), so the split is faithful and complete.
3. **L2 crossedBox spot-check reproduced BIT-IDENTICAL:** 3.4310782578629727e-12.
4. **`sector_filter.wls` split is disjoint + exhaustive by head-count:** crossedBox
   143 U-channel D0i / directBox 143 S-channel D0i / triangle 319 C0i + 23 B0i.

## FORWARD CONTEXT for the fix (do NOT act on it here)
The eventual fix must flip the sign at its **named mechanical source** in the
amplitude assembly — never as a compensating projection / read-off factor. The box
sign lives in the D0i box sector (S-channel + U-channel D0i heads) as it is combined
with the C0i/T-channel triangle penguin sector; that combination point is where the
relative sign enters. D3 pins which sector carries the wrong ABSOLUTE sign.
