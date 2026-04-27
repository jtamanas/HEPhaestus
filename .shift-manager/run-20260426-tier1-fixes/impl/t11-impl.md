# T11 Implementation Log — extract_field schema fixes

## Date
2026-04-25

## Branch / HEAD
`tier1/t11-extract-field-r1-20260426` @ `5268e20`

## Diff summary
Three schemas modified in `plugins/shared/schemas/`:

| File | Change |
|------|--------|
| `relic.schema.json` | `additionalProperties: false` → `true` |
| `annihilation.schema.json` | `additionalProperties: false` → `true` |
| `scattering.schema.json` | `additionalProperties: false` → `true` + SD fields allow null |

The `additionalProperties: true` change was from cycle-1. An additional fix was needed for `scattering.schema.json`: `sigma_sd_proton_cm2` and `sigma_sd_neutron_cm2` were typed as `number` but WS-G proxy runs set them to `null` (with `sigma_sd_status: "not_applicable_proxy"`). Fixed by changing both to `oneOf: [number, null]`.

## Smoke command

```
python3 plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py \
  --json <ws-g-path>/relic.json --key omega_h2 --schema-version relic/v1 \
  --schema-root plugins/shared/schemas

python3 plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py \
  --json <ws-g-path>/scattering.json --key sigma_si_proton_cm2 --schema-version scattering/v1 \
  --schema-root plugins/shared/schemas

python3 plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py \
  --json <ws-g-path>/annihilation.json --key sigma_v_zero --schema-version annihilation/v1 \
  --schema-root plugins/shared/schemas
```

WS-G path: `/Users/yianni/Projects/hep-ph-agents-ws-g/.shift-manager/run-20260425-dsu3-playtest/playtest/ws-g/`

## Per-JSON results

| JSON | Key extracted | Value | Result |
|------|--------------|-------|--------|
| `relic.json` | `omega_h2` | `0.003554792` | PASS |
| `scattering.json` | `sigma_si_proton_cm2` | `4.400856e-44` | PASS |
| `annihilation.json` | `sigma_v_zero` | `8.264214e-25` | PASS |

## Notes
- Cycle-1 agent stalled at watchdog after the `additionalProperties` swap but did not catch the SD null issue in scattering. Fixed here as a minimal additional change (2 lines).
- No other files modified.

---

## Cycle-2 — 2026-04-25

### Branch / HEAD
`tier1/t11-extract-field-r1-20260426` @ `59294e5`

### Regression fixed
T1.1 cycle-1 review flagged that `verify_router_field_contract.py:206` called `prop.get("type")` expecting `"number"` but `sigma_sd_proton_cm2` in `scattering.schema.json` was changed to `oneOf: [{type:number}, {type:null}]`. This caused `DRIFT_PRODUCER_DOC_GAP` on `test_every_summary_json_row_resolves_against_pinned_schema`.

### File edited
`plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py`
- Lines 172–188 (new): added `_resolve_type(prop) -> set[str]` helper that recursively unpacks `oneOf`/`anyOf` branches to collect all types.
- Lines 222–227 (updated): replaced `prop.get("type") != "number"` check with `"number" not in _resolve_type(props[prop_name])`.

### Test command
```
python -m pytest plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py -k test_every_summary_json_row_resolves_against_pinned_schema -v
```
**Result: PASS**

### Broader contract suite
```
python -m pytest plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py -v
```
**Result: 18 passed, 1 xfailed, 3 xpassed — all green**

### Sentinel update
`state/t11.complete` overwritten with new `head_sha: 59294e5` and `verifier_fixed` stanza.
