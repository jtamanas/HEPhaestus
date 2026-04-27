# Expected merged output — Point A (on-resonance, configured)
# HUMAN REFERENCE ONLY — NOT a verbatim gate assertion.
# Hard assertions use expected_table_structure_v1.json for structural checks.

## Dark matter constraints: darksu3

### Tools invoked
- MadDM [maddm_run_dir]
- micrOMEGAs [micromegas_run_dir]  (cross-check: coannihilation/near-resonance trigger)
- DRAKE [drake_run_dir]            (narrow-resonance regime)

### Results
| Observable      | MadDM   | micrOMEGAs | DRAKE   | Status |
|-----------------|---------|------------|---------|--------|
| Ωh²             | 0.135   | 0.118      | (value) | FLAG   |
| σ_SI(p) [cm²]  | 1.23e-45| 1.21e-45   | —       | OK     |
| σ_SD(p) [cm²]  | 5.67e-42| 5.60e-42   | —       | OK     |
| ⟨σv⟩ [cm³/s]   | 2.34e-26| 2.31e-26   | —       | OK     |

Planck 2018 target: Ωh² = 0.1200 ± 0.0012

ADJUDICATION REQUIRED

### Flags
CROSSCHECK_DISAGREEMENT: Ωh² — MadDM: 0.135, micrOMEGAs: 0.118 (rel. diff ~14.4%)
User adjudication required before proceeding.

### Caveats
DRAKE_[STATUS]: [branch-dependent message]
