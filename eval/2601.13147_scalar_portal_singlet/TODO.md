# TODO: Stretch Items for 2601.13147 Benchmark

## Priority 1 — Phase Transition / GW Signatures

Install CosmoTransitions, add `cosmology/` subpackage, ship 9 EWPT BP pins.
The paper's Eqs. 32-70 cover gravitational wave signatures and electroweak phase transition
strength. These require CosmoTransitions and are out of scope for the current benchmark.

## Priority 2 — Relic Density

Implement/interface Boltzmann equation solver (MadDM or custom) to compute Ωh² for BP1-BP9.
BP1 paper value: Ωh² = 0.119. Benchmark currently defers this to a stretch PR.

## Priority 3 — Paper-Match Reconciliation

Investigate the ~11% gap between our sigma_SI (6.17e-50) and paper's (6.96e-50) at BP1.
See RECONCILIATION.md for hypotheses.

## Priority 4 — Full MadGraph Integration

Build the UFO model from feynrules/scalar_portal_singlet.fr and run run_comparison.py.
Currently has_ufo = False in madgraph/__init__.py.
