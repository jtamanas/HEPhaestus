# P3' BAR-3 FAIL — independent adversarial robustness review

Independent reviewer (no code/pushes; read-only) attempted to BREAK the
design-ratified Bar-3 FAIL at branch state d08f936 and could not. Verdict:
the FAIL is **ROBUST and well-posed**. This file persists the substance of that
review; it is the independent verification cited by the p3prime STATUS. Bar
arithmetic lives in `campaign_bars.json` / `campaign_comparison.txt`; the formal
ruling is `../../DESIGN-ITEM4-AMENDMENT8.md`.

## Verdict
The decoupled pure-doublet one-loop scalar floor is **+1.0e-11, robustly
wrong-sign and ~4.5–5× vs Hisano −2.23e-12**. It survives contamination
subtraction under every plausible mixing exponent; Re is physical (the i-trace
holds); and twist-2 sign agreement localizes the defect to the SCALAR SECTOR.
P3' cleanly convicts the loop-floor amplitude — sign-first diagnose indicated.
The verdict is not soft. "Could not break it."

## The five attacks tried

1. **Floor decomposition (the crux) — ROBUST.** Subtracting the extrapolated
   admixture contamination from C_ours(L2) across the full plausible
   mixing-exponent range p=0.5–2.0, the residual FLOOR stays wrong-sign and
   ~4.4–4.7× in every case:
   | p | contamination | % of C_ours | floor | ratio vs Hisano |
   |----|----|----|----|----|
   | 0.5 | 8.2e-13 | 7.8% | +9.71e-12 | −4.36 |
   | 1.0 | 3.0e-13 | 2.9% | +1.023e-11 | −4.59 |
   | 1.25 | 1.85e-13 | 1.8% | +1.035e-11 | −4.64 |
   | 2.0 | 4.2e-14 | 0.4% | +1.049e-11 | −4.71 |
   Even at the most pessimistic p=0.5 the floor is +9.7e-12 (wrong sign, 4.4×).
   Contamination is ≪ C_ours in every case — it cannot flip the sign or explain
   the 5×. The disagreement lives in the pure-doublet FLOOR itself, not the
   admixture residue. This is what makes the FAIL well-posed vs P3's NO-VERDICT.

2. **Is fraction 3e-5 really decoupled? — YES.** Flatness L2→L3 = 9.59% (<25%)
   is a genuine fixed-fraction / vary-MS decoupling test. The excess is POSITIVE
   and MONOTONICALLY shrinking (L1 3.13e-11 → L1b 2.21e-12 → L2 1.85e-13),
   asymptoting to a floor C0 ≈ +1.03e-11, NOT toward Hisano. For C_ours to reach
   −2.23e-12 it would have to reverse sign and plunge below fraction 3e-5 — no
   mechanism in the data; L2 and L3 (the two smallest fractions, different MS and
   m_chi1) both sit at +1.05/+1.15e-11. No hole where the true floor is unreached.

3. **Convention / instrument — CLEAN.** Re is physical here too: L2
   C_scalar_3op Im/Re = 6.9e-7 (essentially real), consistent with the
   by-construction i-trace (no global i). ours Im 2.411e-12 / |C_Hisano| 2.228e-12
   = 1.082 → this IS the named transfer-sampling artifact (reported, not invoked);
   the Im≈|Hisano| match is coincidence, not physics. **Twist-2 sign AGREES at
   all four legs while scalar DISAGREES** → rules out a global sign/convention
   flip and localizes the defect to the scalar sector. Supports sign-first
   diagnose.

4. **Recompute spot-checks — ALL REPRODUCE EXACTLY (bit-match).** C_Hisano
   recomputed at each leg's m_chi1 with its own on-shell EW inputs (n=2, Y=1/2,
   d-quark) from `hisano_1104_0228.py`: L1 −3.02487e-12, L1b −2.22174e-12,
   L2 −2.22766e-12, L3 −2.22885e-12 — bit-match to `campaign_bars.json`. Flatness
   9.586%, Bar-4 exponent 1.2493 raw / 1.0934 mh-corrected, cleanliness L2 8.33%
   / L3 8.77% — all reproduce. No arithmetic discrepancy.

5. **Thin cleanliness margin — NOT A THREAT.** 8.3–8.8% of |C_Hisano| is thin,
   but that is the wrong yardstick: the contamination (1.85e-13) is 1.8% of
   C_ours (the floor). The FAIL is about C_ours being +1.0e-11 (~5× |Hisano|),
   not about the |Hisano|-scale margin. Even 6× the designer's 1.3% estimate
   leaves contamination ≪ floor.

## The one caveat found (named; does NOT open the FAIL)
The L2 sidecar carries a documented PROTOCOL-CONFLICT flag: the verdict legs are
held at θ=−0.152 (the ORIGINAL m_chi1=150 benchmark blind spot), NOT the
decoupled-regime blind spot θ=−π/4. So χ1 sits slightly off the decoupled blind
spot with a residual tree Higgs coupling g_hχ1χ1 = −5.83e-4 (sidecar
tree_DD/loop_floor = 0.31). This does NOT break the FAIL because:
- (a) the projected `amp_reduced.m` is LOOP-ONLY (1PI core), so the tree coupling
  does not enter C_ours directly;
- (b) the residual coupling is mixing-induced (∝ singlet-doublet mixing ∝
  sqrt(fraction)) and vanishes as fraction→0 — its loop imprint is part of the
  excess that Bar-4 extrapolates away (measured exponent 1.25 > 0.5, i.e. it dies
  faster than the single-coupling rate);
- (c) the surviving fraction→0 floor is the pure-doublet EW gauge/Higgs one-loop
  content, which is θ-INDEPENDENT (θ is the singlet mixing angle, irrelevant for
  a pure doublet) = exactly Hisano's regime, so the floor→Hisano comparison is
  valid regardless of θ.

The definitive hole-CLOSER would be one leg at θ=−π/4 (decoupled blind spot) at
fraction→0 showing the same +1.0e-11 floor; the campaign did not run it because
that point is near-singular (m_chi1→m_D forces sin2θ=−1), relying instead on the
fraction→0 extrapolation, which the flatness gate + decomposition strongly
support.

## Recommendation
Proceed with the diagnose round, targeting the scalar-sector sign (see
AMENDMENT8 Ruling 2, probes S1–S4 / D1–D3, pursued on a separate
`item4-diagnose-*` branch).
