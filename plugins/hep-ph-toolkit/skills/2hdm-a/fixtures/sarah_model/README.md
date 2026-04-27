# 2HDM+a Hand-Crafted SARAH Model Fixture

These four Mathematica files are the **working, verified SARAH model** for the
Two-Higgs-Doublet Model + pseudoscalar mediator (2HDM+a) dark matter benchmark
from Arcadi & Profumo (arXiv:2506.19062 §III).

## Provenance

Authored by the project owner in April 2026 during an eight-iteration fix loop
documented in `demo_output/2hdm-a/fix_loop/POST_MORTEM.md`.  The files were
developed against SARAH 4.15.3 and verified end-to-end:

  SARAH → UFO → MG5 import → MadDM → MadDM_results.txt → Ωh² ≈ 10.494 (rounded; deterministic 10.493759)
  (off-resonance benchmark: Mχ=100 GeV, Ma=400 GeV, gχ=1.0, tan β=10)

The original model directory is `/Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix/`.
These committed copies are the canonical fixture used by the demo skill.

## Why these files exist here

The `/sarah-build` renderer cannot yet emit a correct SARAH model for a Dirac
SM-singlet DM fermion coupled to a CP-odd scalar via the PortalDM idiom (two
separate LH Weyl fields, `DEFINITION[EWSB][Phases]` entry, field-name Lagrangian
terms, `\[ImaginaryI]` prefactor on CP-odd Yukawa).  Seven renderer sites need
backporting before the live YAML → SARAH path works.  Until that renderer loop
completes, the demo uses these hand-crafted files.

See `POST_MORTEM.md` §"How to apply this" and §"Remaining debt" for the
renderer backport plan.

## Files

| File | Contents |
|------|----------|
| `TwoHdmAfix.m` | Main model file: gauge fields, matter content, Lagrangian, EWSB definitions |
| `parameters.m` | Parameter definitions with LesHouches block assignments (YUKAWAU/YUKAWAD/YUKAWAE distinct) |
| `particles.m` | Particle definitions: PDG codes, output names, GaugeES + EWSB states |
| `SPheno.m` | Minimal SPheno interface (low-energy, MINPAR/EXTPAR for mchi/gchi) |

## Key design choices (from POST_MORTEM iter-5/6)

- **PortalDM idiom**: Dirac DM is two separate LH Weyl fields (`ChiL`, `ChiR` with `conj[chiR]`),
  NOT the "paired-component" FermionField notation (which silently drops vertices in stock SARAH).
- **Phases entry**: `DEFINITION[EWSB][Phases] = {{chiR, PhasechiR}}` is required; without it
  SARAH's mass diagonalizer drops `chi` during `MakeUFO[]`.
- **Field-name Lagrangian**: mass term is `mchi ChiR.ChiL` (field names), not `mchi chiL.chiR`
  (component names).
- **CP-odd prefactor**: `\[ImaginaryI] gchi a0s.ChiR.ChiL` — the `ImaginaryI` makes it pseudoscalar.
- **Distinct Yukawa blocks**: `YUKAWAU` / `YUKAWAD` / `YUKAWAE` (not all three at `YUKAWA [1,1]`).
  The collision caused `mdl_ryu211 is not defined` in MadDM's EFT re-import.
- **`a0` → `a0s`**: avoids collision with SARAH's internal gauge boson symbol `A`.
- **`Mchi` → `mchi`**: SARAH prefixes `M` on mass-eigenstate names; uppercase `M` causes `MMchi`.

## Usage by the demo skill

The demo's Step 3 copies this directory into `$SARAH_ROOT/Models/TwoHdmAfix/`
if the target is absent, then runs SARAH to produce the UFO.  See
`plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` Step 3 (hand-crafted path).
