---
name: _test_model_x
description: Synthetic stub skill for forward-compatibility testing (T-SF-9 / C4). Demonstrates that a new BSM model can be added without modifying _shared/ or tools/. Do not invoke in production.
---

# _test_model_x (forward-compat harness)

This is a **synthetic stub** used to verify the C4 forward-compatibility protocol.
It demonstrates the 6-step recipe for adding a new BSM model. See `CONVENTIONS.md`.

## Model metadata

- `model`: `model-x` (synthetic)
- Backend: none (stub only)
- Benchmark: `benchmarks/synthetic-1/expectations.json`

## Step 4e — Write summary.json

When a real run completes, write `summary.json` conforming to the per-skill schema:

```json
{
  "schema_version": "1",
  "model": "model-x",
  "run_at": "<ISO-8601-UTC>",
  "ran": ["relic"],
  "skipped_constraints": [],
  "artifacts_dir": "./demo_output/model-x",
  "headline": "model-x relic density run complete",
  "benchmark_id": "synthetic-1",
  "provenance_ref": "provenance.json"
}
```

Write `provenance.json` **before** `summary.json` (atomic-write invariant).

Cite `benchmarks/synthetic-1/expectations.json` in any plan gate comparing `omega_h2`.
