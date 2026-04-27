# R2 — Wchi Citation Probe

## Finding

**Wchi := 0.0 confirmed correct** (LOCKED, citation below).

## Verbatim MadDM quote

From `plugins/monte-carlo-tools/skills/maddm/references/setup.md:41`:

> The model must have a particle flagged as the DM candidate. MadDM auto-detects the
> lightest stable neutral particle under the model's symmetry (typically Z2).

## Analysis

MadDM determines the DM candidate via `define darkmatter <name>` (explicit) or by
auto-detecting the lightest stable neutral particle. The DECAY block width in the
param_card is **not** used as a gate for DM candidate detection — MadDM reads the
PDG code and the `self_conj` flag from the UFO's `particles.py` to classify particles.

The chi (Fchi, PDG 9989932) particle in TwoHdmAfix has `self_conj = False` (Dirac DM)
and is explicitly designated via `define darkmatter chi`. The DECAY block width is
irrelevant for this path.

**DECAY width of chi** is only relevant for internal MadDM width calculations when
computing co-annihilation channels or when chi itself decays — neither applies at the
benchmark point where chi is stable DM.

## Key file:line ref
- `plugins/monte-carlo-tools/skills/maddm/references/setup.md:41` — auto-detect mechanism
- `plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py:107` — `define darkmatter chi` explicit designation

## Conclusion

No contradiction found. Wchi = 0.0 is correct and does not interfere with MadDM's DM
detection. R2 surfaces as informational only; no P2 follow-up needed.
