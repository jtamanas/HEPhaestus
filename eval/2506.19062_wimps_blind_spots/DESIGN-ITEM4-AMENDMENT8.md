# DESIGN-ITEM4-AMENDMENT8 — P3' Bar-3 verdict confirmed; sign-first diagnose round

Amends the AMENDMENT6 family after the P3' campaign (item4-p3prime @ d08f936,
benchmarks/p3prime/, campaign_bars.json). Formal verdict against the
pre-registered bars:

## Ruling 1 — Verdict: BAR-3 FAIL. Assembly-level construction error, CONFIRMED

Flatness PASS (9.6% — the re-pose removed P3's confound); cleanliness PASS
both verdict legs; Bar 2 NOT MET — scalar sign DISAGREES at both legs
(ours +1.05/+1.15e-11 vs Hisano −2.23e-12, |ratio| 4.73/5.18); Bar 4 PASS
(exponent 1.25 raw / 1.09 m_h-corrected — MIXING PHYSICS confirmed: the P3
excess was real singlet-admixture loop content; the instrument measures real
physics). Since Q3 cleared the read-off and overall-i is closed, the defect
is in M's ASSEMBLY, and it is STRUCTURE-SPECIFIC: twist-2 sign agrees at all
four legs while scalar flips — a global or wholesale-sector sign flip is
EXCLUDED by that same fact (a flipped box sector would flip the
box-dominated twist-2 too). Arc consequence: the diagnose round PREEMPTS
per-flavor runs, production σ_SI, and everything downstream; the ~1e-10-scale
readings stay UNVALIDATED (magnitude near-band is noted but a sign error can
masquerade as a magnitude coincidence — no partial credit).

## Ruling 2 — Ranked hypotheses and the probe ladder (cheapest first; no fix
coded before a conviction)

**S1 (leading) — Majorana crossed-box fermion-flow sign** (FeynArts relative
sign between crossed and direct box, the same IRR-4 structure that carried
the crossing artifact). Prior: crossing exchange multiplies operator classes
by class-dependent signs — the one mechanism that naturally flips scalar
while preserving twist-2, matching the measured signature exactly. The
round-3 exactness guard cannot see it (it verifies rotation ≡ original ON M;
a sign already wrong in M is preserved faithfully).
**S2 — triangle-vs-box relative sign in assembly.** Hisano's Higgsino f_q is
a partial CANCELLATION between the induced-h-exchange and box pieces; P1
measured ours ADDITIVE (C_box ≈ +0.63×C_tri, canonical, unrotated).
Pre-registered arithmetic: if the decoupled-leg sector split preserves a
same-sign ratio ~0.6, flipping the relative sign moves |C| by
(1−0.63)/(1+0.63) ≈ 0.23× → |ratio| vs Hisano goes 4.7–5.2 → ≈ 1.1, IN BAND.
Whether the sign also lands depends on which sector is negative at the
decoupled point — measured by D1, not assumed.
**S3 — scalar-projection sign convention vs the external world** (e.g. a
γ5-scheme-induced sign specific to the O_S projection). Constrained by the
twist-2 agreement (shared spinor machinery) but not excluded — Q3 verified
INTERNAL consistency only, never the sign against an externally defined
amplitude.
**S4 (folded into S1) — the C-conjugation phase**: excluded as a
rotation-internal error by the exactness guard; survives only as S1's
upstream form.

**Probes (pre-registered outcomes each):**
- **D1** (pure kernel re-projection of existing L2/L3 artifacts — hours):
  rotated SECTOR SPLIT at both verdict legs — C_scalar and C_twist2
  separately for {triangle, direct box, crossed box}. Outcomes: (i) a SINGLE
  sector sign flip reproduces sign-match AND |ratio| ∈ [0.2,5] AND leaves
  twist-2 in-band → that sector is the convicted candidate (crossed box →
  S1; whole box vs triangle → S2), proceed to D2 for the mechanical source;
  (ii) NO single-sector flip can satisfy all three → S1/S2 class REFUTED,
  jump to D3.
- **D2** (machine-evaluated algebraic identity, same discipline as the Fierz
  guard): crossing-sign self-test — evaluate the direct-box sector at
  s↔u-exchanged kinematics against the crossed-box sector at original
  kinematics; the ratio must be the definite crossing sign for a Majorana
  amplitude. Measured sign ≠ required sign → S1 MECHANICALLY CONVICTED with
  the wrong sign named at its FeynArts/FormCalc source; equal → S1 cleared,
  run the same identity method on the h-vertex sign (S2), then D3.
- **D3** (synthetic external-sign control — the gap Q3 left): build a toy
  amplitude with an EXTERNALLY known scalar sign (FormCalc tree h-exchange,
  Dirac toy, positive coupling: attractive ⇒ C_scalar sign known a priori)
  and push it through the full projection. Wrong sign out → S3 convicted;
  right sign → S3 cleared and the remaining space is re-designed with the
  D1/D2 measurements in hand.
Fix protocol: after any conviction and fix, the verdict RE-RUN is L2/L3 only
(spectra exist) + triangle-fixture bit-identity + full suite; Bar-2 bars
unchanged ([0.2,5] + same sign). A fix that moves the fixture is a different
bug — stop and re-adjudicate.

## Ruling 3 — Dispositions

**item4-p3prime branch: MERGE NOW as the campaign record** (the verdict
machinery worked end-to-end; a measured FAIL is a result). Criteria:
AMENDMENT8 committed in-repo; STATUS updated (Bar-3 FAIL, diagnose round
open, Bar-4 mixing-physics positive result recorded); fresh reviewer; suite
green + protected-file byte-identity. **AMENDMENT7 bands: UNAFFECTED**
(twist-2 sign now validated at four legs; magnitude still bridge-caveated;
C_Q consistent-with-zero stands) — but production σ_SI's gate MOVES from
"P3' pass" to "diagnose conviction + fix + L2/L3 re-run pass". **Per-flavor
/production queue: formally PREEMPTED** until that gate clears. Ownership:
D1+D2 to one owner (kernel + identity work, campaign owner suggested), D3 to
the other (round-3 implementer knows the projection internals); reviewer
fresh for whichever produces a conviction.
