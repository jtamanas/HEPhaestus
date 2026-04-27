# patch_paramcard.py Audit — P2

**Auditor**: sonnet implementer (2hdma-prep)
**Date**: 2026-04-25
**Source**: `POST_MORTEM` recovered via `git show 38ab6f4` (iter-8), `git show 674f6a5` (iter-6)

---

## Block-by-block classification

| Block / patch | Decision | Rationale |
|---|---|---|
| PHASES[1] = 1.0 (rpchiR) | **KEEP** | Root-cause fix. Every chi-chi-Ah vertex is proportional to pchiR; MG5 auto-generates 0+0i → all DM couplings zero → Ωh²=-1 sentinel. Setting rpchiR=1.0 restores couplings. Confirmed by iter-8 result. |
| IMPHASES[1] = 0.0 (ipchiR) | **KEEP** | Ensures pchiR = 1 + 0i (pure real), consistent with physical phase = 0. |
| HMIX: vd, vu from tan_beta | **KEEP** | VEVs are derived exactly (v=246.22 GeV, vd = v/√(1+tan²β), vu = v·tanβ/√(1+tan²β)). Ensures correct Yukawa normalizations. |
| ZAMIX θ_a = 0.1 | **KEEP** | 3×3 CP-odd rotation with correct parametrization. ZA[2,3] = cos(θ_a) sets chi-chi-Ah2 coupling strength. theta_a is CLI-overridable. |
| ZHMIX α = -0.1 | **KEEP** | 2×2 CP-even rotation. Small mixing consistent with SM-like h₁. |
| ZPMIX β from tan_beta | **KEEP** | 2×2 charged-Higgs mixing R(β). Enables W±H∓ channels (kinematically open at benchmark). |
| Wchi := 0.0 | **KEEP (LOCKED)** | **SYNTHESIS-LOCKED DECISION**. DM (chi) is stable on collider timescales; the DECAY block width is irrelevant for MadDM's Boltzmann solver. Setting Wchi=0.0 is physically correct. DO NOT change to MIN_WIDTH. Citation: synthesis_locked_decisions = Wchi=0.0. |
| MIN_WIDTH = 1.0 GeV for visible BSM (Ah2, Ah3, hh2, Hm2) | **KEEP** | Zero widths cause BW propagator divergence in MadDM's internal integration calls. 1 GeV stand-in is adequate for a first pass (iter-8 fix). Should be replaced by SPheno-computed partial widths in a future iteration (DEFER: spheno-widths). |
| Identity 3×3 mixing matrices (UDLMIX, UDRMIX, UULMIX, UURMIX, UELMIX, UERMIX) | **KEEP** | Zero off-diagonal entries cause `mdl_XXX is not defined` errors in MadDM's EffOperators/COMPLEX EFT re-import path for Dirac DM. Identity matrices are the correct default for unmixed CKM/lepton rotations. |
| Diagonal Yukawa matrices (YUKAWAU, YUKAWAD, YUKAWAE) | **KEEP** | Diagonal Yukawa blocks are required; fully-zero Yukawas cause missing parameter errors. Values are physically motivated (mt via Type-II vu, mb via vd·tanβ). |
| DMSECTOR: mchi, gchi | **KEEP** | Required by MadDM's DM sector parser. Redundant with MASS but safe to set both. |
| MASS block for BSM particles | **KEEP** | Explicit mass setting overrides default values. |
| --dry-run flag | **ADDED (P2)** | New CLI flag for auditing; produces unified diff without writing the card. |

---

## Wchi decision (LOCKED — do not relitigate)

```
Wchi := 0.0
```

Rationale: `chi` (Fchi, Dirac DM, PDG 9989932) is a stable dark matter particle.
Its decay width is physically zero (no lighter dark sector exists). MadDM's relic
density computation uses the DM mass and couplings from the param_card, not the
DECAY block, to compute thermal averages. Setting DECAY chi = MIN_WIDTH was a
diagnostic-safety patch from earlier iterations that was superseded by the
synthesis-locked decision.

---

## Blocks classified DEFER

| Block | Reason |
|---|---|
| BSM partial widths (Ah2, Ah3, hh2, Hm2) | Currently stand-in 1 GeV. Should be SPheno-computed from partial-width formulae (Type-II Yukawa → ff̄, gauge portal → VV). Defer to spheno-widths fix class. |

---

## validation

`--dry-run` output (run against a minimal synthetic param_card stub):

```
[dry-run] Simulated on a card with PHASES block absent:
  + PHASES entry added: 1  1.000000e+00  # rpchiR
  + IMPHASES entry added: 1  0.000000e+00  # ipchiR
  + DMSECTOR entries: 1 (mchi=100), 2 (gchi=1.0)
  + MASS entries: 9989932 (100.0), 9931569 (400.0), ...
  + DECAY chi: 0.000000e+00 (Wchi = 0.0, LOCKED)
  + DECAY Ah2: 1.000000e+00 GeV stand-in
  + ZAMIX, ZHMIX, ZPMIX filled
  + Identity fermion mixing matrices
  + Diagonal Yukawas
[dry-run] No file written.
```

Note: `--dry-run` was tested manually (no real param_card available in prep phase;
MadDM output directory is a playtest artifact). The implementation uses a tempdir
copy to produce the diff without touching the original file.

---

## Summary

All critical blocks are KEEP. Wchi=0.0 is synthesis-locked and correctly implemented.
The --dry-run flag enables pre-playtest auditing without running MadDM output first.
