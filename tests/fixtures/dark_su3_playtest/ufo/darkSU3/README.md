# Dark SU(3) UFO — Synthetic Sentinel

This directory is an **empty-dir sentinel** for the WS-3 Dark SU(3) router
playtest. It contains **no real UFO source files** and is never read by any
real tool in Tier-1 or Tier-2 tests.

## Purpose

The router's `check_prereqs.py` helper asserts only that the configured
`ufo_path` exists as a directory (per `contracts/router_contract.json`
manifest dispatch type `path_or_bool`). It does **not** inspect directory
contents in Tier-1 or Tier-2. This sentinel directory satisfies that check
without requiring a real Dark SU(3) UFO.

## Tier-3 (real /maddm) use

If you want to run the `pytest -m smoke` Tier-3 suite against a real Dark
SU(3) UFO, place your UFO package here:

    tests/fixtures/dark_su3_playtest/ufo/darkSU3/dark_su3_real.ufo

The Tier-3 smoke test `test_smoke_pointA_real` in
`tests/dark_su3_playtest/test_playtest_tier3_smoke.py` will pick it up. The
test is skipped automatically if the real `maddm-launcher` binary is absent.

## Distinct-categories disclaimer

The numeric values in `tests/fixtures/dark_su3_playtest/canned/` are
**fixture inputs** driving the router's rel-diff arithmetic — they are
**not** gate thresholds asserting "the answer must be X." The `golden/`
directory's `expected_blockers_v1.json` and `expected_table_structure_v1.json`
are structural gate specs (column presence, row count, code presence) — also
distinct from inline numeric thresholds. This distinction is required by the
routing-lens constraint in `briefs/ROUTING_LENS.md`.
