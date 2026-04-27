# plan-with-bug.md — Fixture for T-SF-8 lint test (plan-level buggy plan)
# This is the cycle-1 G-S1-9 buggy gate that references .provenance.run_id in summary.json.
# The core schema has additionalProperties: false and no 'provenance' key.
# check_plan.py must exit non-zero with R-1 error citing provenance.run_id and summary.json.

## T-BUG — Gate with schema violation

Run the cache-warm regression:

```bash
RUN_ID="20260425T122317Z-55c01ea"
RUN=$PT_DIR/runs/run-1
jq -e --arg rid "$RUN_ID" '.provenance.run_id == $rid' $RUN/summary.json
```

This gate is buggy: `summary.json` has `additionalProperties: false` in the core schema
and no `provenance` key. The jq filter `.provenance.run_id` will always return null.
