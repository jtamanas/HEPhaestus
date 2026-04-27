# MadGraph UFO Models — arXiv:2511.21808

## Plan Status

| Portal | UFO | Plan | Status |
|--------|-----|------|--------|
| B-L Z' | U1B-L | **Plan C** | Not vendored in v1 (see below) |
| Higgs portal scalar | DMScalar (DMSimp) | Plan A | Reference only (no grader) |
| 3 Lᵢ-Lⱼ portals | — | None | No MG task in v1 |

## Plan C — B-L Z' (No UFO in v1)

The paper (arXiv:2511.21808) uses CalcHEP/micrOMEGAs internally, not MG5_aMC directly.
No U1B-L UFO with confirmed SHA was vendored for this benchmark.

`generate_mg_tasks.py` handles this gracefully: if `zprime_BminusL/model.sha256` is absent
or the SHA does not match `EXPECTED_SHA`, the script emits nothing and exits cleanly.
The harness then has no MG task for B-L (10 Tier-3 tasks instead of 11).

To activate Plan A/B in a future version:
1. Obtain U1B-L UFO from HEPMDB or rebuild via FeynRules.
2. Vendor it under `zprime_BminusL/UFO/`.
3. Compute SHA256: `sha256sum zprime_BminusL.tar.gz > zprime_BminusL/model.sha256`
4. Update `EXPECTED_SHA` in `generate_mg_tasks.py`.
5. The generated YAML will appear at `eval/tasks/tier3_mg_paper4.generated.yaml`.

## DMScalar (Higgs Portal Scalar)

The DMScalar UFO is from the DMSimp framework (Backovic et al., arXiv:1508.05327).
Public release: https://feynrules.irmp.ucl.ac.be/wiki/DMsimp

DM candidate: `Xs` (complex scalar).
Higgs portal coupling: `(1/2) λ |H|² |Xs|²` (DMScalar convention).

This UFO is used for the Tier-1 proc_card task only (reference, no numeric grader).
