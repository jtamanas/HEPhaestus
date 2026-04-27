# dark-su3 benchmarks

No paper-cited numeric benchmark has been committed for dark-su3 yet.

## Convention

Add `benchmarks/<name>/expectations.json` here when a paper-cited benchmark is
committed for a specific parameter point. Use the universal expectations schema at
`singlet-doublet/benchmarks/canonical-2026/expectations.schema.json` as the template.

Until a fixture is committed, plan gates MUST NOT inline numeric thresholds for
dark-su3 (e.g., no `omega_h2 > X` literals). Any plan gate on dark-su3 physics
output must either:
1. Cite a fixture in `benchmarks/<name>/expectations.json`, OR
2. Use structural checks only (e.g., `status == "ok"`, `omega_h2 > 0`).
