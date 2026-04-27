# R1 — Schema Sign-Off

OWNER: 2hdm-a; ACK: SD-clean, dark-su3-clean

## Basis

The P3 test script `plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` validates
stub payloads for all three models (2hdm-a, singlet-doublet, dark-su3) against the
updated `summary.schema.json`.

- **2hdm-a stub**: uses `relic_approx: false`, `model_source: hand_crafted_sarah_model`,
  `model_fixture: plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/` — all new
  optional fields. PASSES.
- **singlet-doublet stub**: uses no new optional fields (they are not required by the schema,
  and `additionalProperties: false` only rejects undeclared properties, not absent optional ones).
  PASSES — SD schema compatibility confirmed.
- **dark-su3 stub**: uses `relic_approx: true` only. PASSES — dark-su3 schema compatibility confirmed.

## Test result (commit 76919d4)

```
[PASS] 2hdm-a
[PASS] singlet-doublet
[PASS] dark-su3
All 3 stubs validated successfully.
```

## Lock status

Schema lock `.shift-manager/locks/summary_schema.lock` was held during P3 edit and
released immediately after commit 76919d4 landed.

## Cross-workstream note

SD and dark-su3 workstreams may use the same lock protocol if they need to edit the
schema in the future. The new fields are optional (not in `required`) so existing SD
and dark-su3 summary.json files remain valid without modification.
