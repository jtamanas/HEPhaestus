# B6 — per-channel box split, chirality-corrected partition (AMENDMENT8R3 R3)

**MEASUREMENT ONLY. No fix. No World ruling** — that call belongs to the
manager + designer (8R3 R4). Scored against the FROZEN pre-registered bars of
`DESIGN-ITEM4-AMENDMENT8R3.md` R3; bars were not moved after any number was
seen. Machine-readable results: `b6_box_split.json` (this directory); raw
per-run kernel extracts committed as `b6_L{2,3}_{db,cb}_{Wpure,Zpure,Yukawa,WwithHp}_cours.json`.

## Method (reproducible)

Partition of the BOX amplitude (directBox `db` + crossedBox `cb`, the D1
sector split) into channels by INTERNAL BOSON, read from the boson masses
appearing in each D0i loop function's argument list
({MassVWp, MassVZ, Masshh, MassAh, MassHp}):

| channel | keep D0i whose boson-set is | D0i count (per box sector) |
|---|---|---|
| `Wpure`  | exactly {W}                      | 11 |
| `Zpure`  | exactly {Z}                      | 11 |
| `Yukawa` | intersects {h, A, H±} (i.e. {H±}, {W,H±}, {Z,h}, {Z,A}, {h}, {A}, {h,A}) | 121 |
| (subset) `WwithHp` | exactly {W, H±} — subset of Yukawa, reported for the P-i sensitivity | 22 |

11 + 11 + 121 = 143 = ALL D0i in each box sector → **exhaustive and
non-overlapping by construction** (verified per run; census in
`b6_boson_filter.wls` output). There is NO {W,Z} mixed D0i, so the only
partition-boundary choice is where the MIXED Higgs-gauge boxes go.

**Boundary choice (χ±/W bookkeeping):** mixed boxes with one gauge and one
Higgs leg ({W,H±}, {Z,h}, {Z,A}) route to `Yukawa` (Higgs-dominant rule): the
Higgs leg carries the quark-side Yukawa (chirality-flipping) coupling, so
these are NOT pure left-handed gauge boxes and the P-i chirality argument does
not protect them. **Effect on P-i:** none in practice — the {W,H±} subclass
measures ≈ −1e-14 (L2) / −4e-14 (L3), so P-i's ratio moves from 0.6213 to
0.6213 (L2) under the alternative "any-W" convention (`alt_anyW_ratio` in the
JSON). P-i's verdict is insensitive to the boundary choice.

Projection: same instrument as P3'/D1 (`run_eval_sd.wls` driver +
`p3_extract_cours.wls` re-projection, `C_scalar_full_re` = rotated-complete
R_S_S read-off), at the frozen L2/L3 verdict legs. Scripts:
`b6_boson_filter.wls` (partition), `b6_kernel.sh` / `b6_run_all.sh` (runs),
`b6_analysis.py` (scoring). Raw kernel logs (driver.log/extract.log per run):
`/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-scratch/runs/` (not committed;
sizes ~7 kB each).

**Remainder (measured deviation):** the 4 no-D0i finite terms per sector
cannot be kernel-driven alone (run_eval_sd.wls dies with a MathLink
MLException on a 0-loop-function amplitude — measured, logs in
`runs/L*_*_remainder/`). The remainder is DERIVED from projection linearity:
rem = (Wf + Zf + Yf − box_D1)/2 per (sector, leg). Independent evidence the
derivation is sound: rem derived from db vs cb agrees to 1.1e-7 (L2) / 1.1e-5
(L3) relative — the two sectors share the identical no-D0i term structure —
and the remainder is tiny (−1.9e-14 / −7.4e-14, i.e. 0.3–1.1% of box-total).
Channel-sum closure vs the D1 box-total is exact by construction of rem, so
the db/cb agreement + D1's own 0.18–0.64% sector-sum closure are the honest
closure evidence.

**Provenance note:** the kernel batch completed 2026-07-14 09:16 ("ALL DONE"
in `p3-b6-scratch/run_all.log`) shortly before a machine outage. All 16
extracts parse, ok=true. Integrity certified by a fresh spot-check
reproduction of L3/cb/Zpure after the outage (see `b6_spotcheck.json` /
commit message) — reproduced to machine precision.

## Measured per-channel scalar coefficients (box channels, db+cb summed, GeV^-2)

| channel | L2 | sign | L3 | sign |
|---|---|---|---|---|
| W/χ± (`Wpure`) | +4.4015e-12 | + | +4.3670e-12 | + |
| Z (`Zpure`) | +2.7004e-12 | + | +2.6120e-12 | + |
| Yukawa (h/A/H±, incl. mixed) | +1.2584e-15 | + | +6.3394e-15 | + |
| remainder (no-D0i, derived) | −1.8967e-14 | − | −7.4425e-14 | − |
| box-total (D1 reference) | +7.0842e-12 | + | +6.9109e-12 | + |
| triangle class (D1, for P-iii) | +3.4266e-12 | + | +4.5544e-12 | + |

Hisano frozen references (leg-scaled, from d4): g_S box class −1.5424e-13 (L2)
/ −1.5417e-13 (L3); g_H class −2.0734e-12 / −2.0747e-12.

## Probe verdicts vs the FROZEN 8R3 bars

- **P-i (internal falsifier, parameter-free): FAIL at both legs.**
  |C_scalar(W)| / |C_scalar(box-total)| = **0.6213 (L2) / 0.6319 (L3)** vs bar
  < 0.05. Our pure W-W gauge box scalar does NOT vanish — it is the single
  LARGEST box channel. Per the pre-registration this is a NEW defect localized
  to the W channel (quark-side chirality is model-independent: W is pure
  left-handed → a_R = 0 → box scalar ∝ a_L·a_R = 0), to be diagnosed
  SEPARATELY from the D3 total-sign case; it part-explains the total
  magnitude excess. Verdict robust to the mixed-box boundary choice
  (alt ratio identical to 4 s.f.).
- **P-ii (Z class vs g_S): wrong-sign, OUT of band.** ratio = −17.51 (L2) /
  −16.94 (L3); |ratio| outside [0.2, 5]. Sign: ours +, Hisano − (the
  World-B-expected inversion), but the magnitude bar FAILS — our Z-Z box is
  ~17× the Hisano g_S class.
- **P-iii (g_H counterpart = triangle + surviving W-scalar): wrong-sign, IN
  band.** ratio = −3.78 (L2) / −4.30 (L3); |ratio| within [0.2, 5]. (Triangle
  alone: −1.65 / −2.20.) Note the surviving W-scalar is what brings the
  grouped comparison toward the band edge; with a vanishing W-box (as
  chirality demands) this would reduce to the triangle-only ratio, also
  in-band.
- **P-iv (no-counterpart class): NOT the excess.** Yukawa boxes carry 0.01%
  (L2) / 0.05% (L3) of the total excess over Hisano — far below the majority
  threshold. The FAIL-L3 total-magnitude excess is NOT reclassified as a
  candidate model-difference on this evidence; the Yukawa-box escape hatch is
  closed. (B3's static token-census expectation that these channels are
  y_d-suppressed-negligible is CONFIRMED dynamically.)

## Per-class sign pattern (for the World read — reported, not ruled)

All measured classes POSITIVE at both legs: (W +, Z +, Yukawa +, triangle +)
vs Hisano's uniformly NEGATIVE classes — a UNIFORM sign inversion, no split
pattern. The 8R3 World-B coherence read required P-i PASS + P-ii/P-iii both
wrong-sign in-band; the sign half of that pattern is present (uniform
inversion, consistent with a single process-global −1), but **World-B
coherence as pre-registered FAILS on P-i** (a W-channel scalar that should
vanish identically does not) and on P-ii's band. MEASURED summary: the box
excess is pure-gauge (W 62% + Z 37%), not Yukawa; the W-channel anomaly is a
new, separately-diagnosable defect under the 8R3 rules; interpretation and
the A/B ruling remain with the designer (8R4: P-i FAIL ⇒ two-defect ledger
route).

## Deviations from spec (flagged)

1. `remainder` channel derived algebraically (kernel cannot run a
   0-loop-function amp) — method + cross-check above; affects channel values
   at the ≤1% level and no verdict.
2. Channel-sum closure vs box-total is exact by construction of the derived
   remainder; the independent closure evidence is the db/cb remainder
   agreement (1e-7/1e-5) and D1's sector-sum closure (0.18–0.64%), not a
   fourth independent kernel number.
3. The imaginary parts of the channel extracts are non-negligible for the
   gauge channels (e.g. W-channel Im/Re ~ 0.2 at L2, ~0.6 at L3/cb) —
   physical above-threshold absorptive parts consistent with m_χ > m_W,Z;
   all scoring uses Re per the campaign convention (D1/D4 precedent).
4. Campaign interrupted by a machine outage AFTER batch completion; surviving
   extracts certified by a fresh post-outage spot-check reproduction rather
   than a full regeneration (coordinator's "regenerate everything" premise
   — that no output survived — was contradicted by the on-disk `ALL DONE`
   log + 16 valid extracts; flagged per verified-artifact discipline).
