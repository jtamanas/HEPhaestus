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

## D4 per-sector Hisano decomposition (SCALAR axis) — STOP + ESCALATE
`d4_per_sector_hisano.py` / `d4_analysis.json`. Pure-Python, no kernel. Rule +
hypothesis-map + STOP condition pre-registered before compute. This is the CLEAN
scalar-axis (f_q) tie-breaker — it does NOT use the unreliable twist-2 O_Tq bridge.
Uniform −1 was treated as a NEUTRAL candidate (its prior exclusion ran through that
bridge and was downgraded by the designer).

**Mapping (documented):** Hisano f_q has TWO analytic classes — `g_H` (Higgs-exchange
penguin) ↔ our **triangle**, and `g_S` (gauge box, a SINGLE class) ↔ our **box-total**
(directBox+crossedBox). The 2^3 scan collapses to two Hisano refs {tri_H, box_H};
the box is scored in both readings (A) box-total vs box_H and (B) each box sector vs
the shared box_H, the latter breaking the mixed-box degeneracy.

**Sanity anchor:** per-sector Hisano f_q·m_q sums to −2.228e-12 (L2)/−2.229e-12 (L3),
reproducing the campaign C_Hisano exactly (both legs). Hisano split: tri_H = −2.073e-12
(93.1%), box_H = −1.542e-13 (6.9%) — **BOTH classes NEGATIVE**.

**Result: NO sign assignment satisfies the rule at both legs → STOP + ESCALATE**
(pre-registered magnitude-structure branch). Two sub-findings:
- **SIGN → uniform −1, not S2.** Our triangle and both boxes are POSITIVE; both Hisano
  classes are NEGATIVE. Sign-match alone forces (−,−,−) = uniform −1 global flip. S2's
  s_tri=+1 MISMATCHES Hisano's negative triangle class — **S2 is refuted on the clean
  scalar axis.** (The triangle gate passes under s_tri=−1: |ratio_tri| 1.65/2.19.)
- **MAGNITUDE (the crux) → box structurally too large.** Hisano's gauge-box class is only
  6.9% of its scalar coupling; our boxes are ~60–67%. |box_total/box_H| ≈ 46 (L2)/45 (L3)
  and |directBox/box_H| ≈ 22–24 — far outside [0.2,5] under EVERY sign. So the defect is
  NOT a pure sign flip; it includes a box-sector magnitude-structure mismatch.

**Reframing of the earlier D1 S2 conviction:** D1 compared TOTALS and found tri−box
(S2) gives the best total ratio — but it does so by cancelling our too-large box against
our triangle to land near Hisano's total. Per-sector, that structure does not match
Hisano (93% triangle / 7% box). The scalar-axis per-sector test therefore downgrades S2
and reopens uniform −1 on sign, while flagging that neither is a clean fit because the
box magnitude is off by ~45×. Escalated to the designer before any fix.

## B3 box internal-line mapping audit (AMENDMENT8R1) — MAPPING-ARTIFACT
`b3_mapping_audit.py` / `b3_mapping_audit.json`. Static, no kernel. Adversarial
internal-line enumeration testing whether D4's ~45× box mismatch is a genuine
defect or an artifact of comparing our FULL box-total against a PARTIAL Hisano
class. Outcomes pre-registered in the header before the verdict.

**Our box internal lines** (from `DIAGRAM-CENSUS.md` IRR-3/4 + mass-token census of
`amp_directBox.m`/`amp_crossedBox.m`, both boxes identical): bosons {W, H±, Z, h, A},
fermions {χ±, χ0, internal up-quark}. Channels: **W/χ± (CC, magnitude-DOMINANT — gauge,
no Yukawa suppression), H±/χ± (CC, sub-dominant), Z/χ0 (NC), h/χ0 & A/χ0 (NC,
NEGLIGIBLE — y_d-suppressed)**. Token counts (h 100, A 98, Z 93, H± 61, W 47) prove
presence but are NOT a magnitude proxy — the fewest-term W channel is magnitude-dominant,
the most-term h/A channels are negligible.

**Hisano g_S scope:** the transcription's f_q box term is `(a_qV²−a_qA²)(Y²/cw⁴)(α₂²/m_Z³)·g_S(z)`
— **Z-mediated neutral-current box ONLY** (no g_S(w)). Hisano assigns ALL W strength to
the g_H **penguin** (nfac/(8m_W)·g_H(w), inside the 1/m_h² Higgs-exchange bracket), none
to the box.

**KEY TEST:** out-of-scope channels present = {W, H±, h, A}; in-scope = {Z} only. The
magnitude-dominant W/χ± charged-current box is OUT of g_S scope (Hisano routes it to the
penguin). **VERDICT: MAPPING-ARTIFACT.** The ~45× reflects a triangle/box PARTITION
mismatch — Hisano W→penguin, our pipeline W→box (plus H±/h/A boxes g_S has no counterpart
for); only the subdominant Z box is genuinely in g_S scope. This also revises the B3
brief's REAL-DEFECT premise ("g_S represents W/χ±(+Z)"): g_S is Z-only, so even the
leading gauge-box channel is out of scope — the mismatch is broader than anticipated.
**Residual caveat:** exact per-channel C_scalar cannot be isolated without a kernel
re-projection (forbidden here), so the fraction of the 45× explained is not numerically
pinned — but the direction is certain and the dominant channel is definitively out of
scope. **Recommendation:** do NOT hand the 45× to B1/B2 as a box-magnitude bug; the
correct sector comparison is TOTAL-vs-TOTAL (D4 anchor reproduces exactly) or a
re-partitioned comparison grouping our W box with the penguin to match Hisano's g_H.

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
