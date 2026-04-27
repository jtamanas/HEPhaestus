# D2 — env.json sarah_version wrapped in Mathematica StyleForm

**Status**: FIXED
**Severity**: minor (cosmetic)
**Round**: 2 (sonnet address)

## What was wrong
`env.json` `sarah_version` contained the raw Mathematica styled output:
`"StyleForm[SARAH , Section, FontSize -> 14]StyleForm[4.15.3, Section, FontSize -> 14]"`

SARAH's `Print[$SARAHVersion]` emits styled Mathematica output including `StyleForm[...]` wrappers that the original parser did not strip.

## Fix applied
Added `_strip_styleform(s)` helper to `capture_env.py` that:
1. Uses regex to extract the first argument of each `StyleForm[content, ...]` occurrence.
2. Returns the last argument that matches a version pattern (`\d+\.\d+[\.\d]*`).
3. Falls back to stripping all `StyleForm[...]` tokens and returning bare text.

Updated `get_sarah_version()` to call `_strip_styleform()` on each candidate line.

After fix: `sarah_version = "4.15.3"`.

## File changed
- `plugins/hep-ph-demo/skills/2hdm-a/scripts/capture_env.py`
- `demo_output/2hdm-a/playtest_log/env.json` (regenerated)
