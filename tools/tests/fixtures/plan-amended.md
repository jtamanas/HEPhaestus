# plan-amended.md — Fixture for T-SF-8 lint test (amended plan, no violations)
# This is the corrected gate: run_id is read from provenance.json (not summary.json).
# check_plan.py must exit 0 on this fixture.

## T-AMENDED — Gate with correct schema reference + fixture citation

Run the cache-warm regression:

```bash
RUN_ID="20260425T122317Z-55c01ea"
RUN=$PT_DIR/runs/run-1
# Verify run_id from provenance.json (correct: provenance has run_id, not summary)
jq -e --arg rid "$RUN_ID" '.run_id == $rid' $RUN/provenance.json
```

Check omega_h2 is in the expected band:

```bash
# fixture: plugins/hep-ph-toolkit/skills/singlet-doublet/benchmarks/canonical-2026/expectations.json
jq -e '(.expectations.omega_h2.central == 0.292)' $RUN/provenance.json
```

This gate is correct: `provenance.json` contains `run_id` and is the right target.
The omega_h2 gate cites the canonical-2026 fixture as required by R-3.
The provenance.json is referenced in the same task block as would be summary.json (R-4 satisfied).
