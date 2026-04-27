# SARAH Output Fixture Directory — DarkSU3 (PLACEHOLDER)

This directory is a placeholder. The committed fixture tarball is at:
`tests/fixtures/sarah_output_darksu3.tar.gz`

## Post-W3 regeneration

After W3 (`/sarah-build`) merges and produces real SARAH output for `dark_su3`, the manager
runs:

```bash
python3 plugins/hep-ph-toolkit/skills/spheno-build/scripts/regenerate_fixture.py --force
```

This overwrites `tests/fixtures/sarah_output_darksu3.tar.gz` with real content extracted from:
`$STATE_ROOT/models/dark_su3/sarah_output/SPheno/DarkSU3/`

## Constraints

- Hard cap: **10 MB gzipped** (§2.11 of phase2-plan-final.md).
- No git-LFS, no cloud-fetch fallback.
- Committed in-repo.

## Integration test gating

Tests that require the fixture to contain valid SPheno Fortran sources are gated on:
- `HEPPH_RUN_NETWORK_TESTS=1`, OR
- Both `gfortran` and `SPheno` present in PATH.

Unit tests (parse_slha, leshouches_template, scan_expansion, scan_recoverable_row)
do NOT require this fixture.
