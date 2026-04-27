# Negative Control — Sabotaged SKILL.md files

Four sabotaged copies of the live SKILL.md, each targeting a distinct hard assertion.
Used by `tests/dark_su3_playtest/test_negative_control.py` via the
`WS3_SKILL_OVERRIDE_PATH` env var.

## Sabotage map

| Sabotage ID | Edit to SKILL.md | Expected hard-assertion fail | Gate |
|---|---|---|---|
| NC-1 | `--schema-version` arg removed from `extract_field` invocations in Step 4b AND Step 5 | `extract_field_schema_version_arg` | `! grep -E "extract_field.*--schema-version"` |
| NC-2 | Step 4b instructs LLM to extract only `omega_h2`; `sigma_v_zero` extraction invocation removed | `extract_field_sigma_v_zero_invocation` | grep confirms only omega_h2 extraction |
| NC-3 | "do NOT silently average" sentence weakened; `CROSSCHECK_DISAGREEMENT` blocker code removed from both Step 4b prose and the blocker table. Also the example Flags section updated. | `crosscheck_disagreement_blocker_present` | `! grep -F "do NOT silently average"` AND `! grep -F "CROSSCHECK_DISAGREEMENT"` |
| NC-4 | `--spec <yaml>` row removed from the Invocation table | `spec_flag_preflight` | `! grep -F -- "--spec"` |

## Bell-ring semantics

When the test suite runs against these sabotaged files (normal mode), the
expected hard-assertion MUST appear in `result.hard_failures`. If it doesn't,
the negative-control test fails (the sabotage didn't fire).

When `WS3_FORCE_LIVE=1` is set, the test inverts: it asserts the expected
hard-assertion is NOT in `result.hard_failures` (verifying the live SKILL.md
is not accidentally sabotaged). All 4 cases should PASS in force-live mode.

## Sacrosanct labels (WS-4 T7 §7)

The sabotages in this directory do NOT modify the 9 sacrosanct section headings
from the WS-4 T7 plan (Step 1, Step 2, Step 3, Step 4, Step 4b, Step 5,
Invocation, Blocker/notice codes, Config keys read). Sabotages target only
prose content within those sections, not the headings themselves.
