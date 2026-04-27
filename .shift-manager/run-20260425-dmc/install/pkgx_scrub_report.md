# Package-X Scrub Report — 2026-04-25

## Files edited

| File | Change |
|------|--------|
| `demo_output/dark-su3/playtest/summary.json` | drop token — removed `/package-x` from blocked-skills list in `dd` reason string |
| `demo_output/2hdm-a/summary.json` | drop token — removed `/package-x` from blocked-skills list in `dd` reason string |
| `demo_output/2hdm-a/fix_loop/POST_MORTEM.md` | drop token — removed `/package-x` from blocked planned-skills list in "direct detection" paragraph |
| `plugins/constraints/skills/ddcalc/tests/test_schema_validate.py` | drop token — renamed fixture reference from `sigma_package_x_sample.json` → `sigma_looptools_sample.json` in docstring and path |
| `plugins/constraints/skills/ddcalc/tests/test_integration_xenon1t_golden.py` | drop token — renamed two occurrences of `sigma_package_x_sample.json` → `sigma_looptools_sample.json` (docstring + method body) |
| `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md` | drop token — removed `/package-x` from blocked reason string in Step 5 description |
| `plugins/hep-ph-demo/skills/_shared/tests/test_time_budget.py` | drop token + rewrite count — removed `package-x` from `TestOverlapDedup` docstring prereq list; updated counts from 4 dd-only/8 total to 3 dd-only/7 total |
| `plugins/model-building/skills/lagrangian-builder/tests/test_constraint_dispatch.py` | rewrite — changed assertion message from `FormCalc→Package-X hand-off` to `FormCalc→LoopTools hand-off` |
| `docs/roadmap/v1-constraints-work/feynarts/plan/critique.md` | drop token — removed `PACKAGE_X_*` from blocker-code enum extension list |
| `eval/METHODOLOGY.md` | rewrite sentence — replaced `Package-X, FeynRules` with `FeynRules, LoopTools` in computational-tools example list |
| `eval/2506.19062_wimps_blind_spots/paper_metadata.json` | rewrite — replaced `loop_integrals` value from `"Package-X (Patel 2015, 2016) [paper]; LoopTools (Hahn & Perez-Victoria 1999) [skill replacement]"` to `"LoopTools (Hahn & Perez-Victoria 1999)"` |
| `eval/2506.19062_wimps_blind_spots/loop_functions/passarino_veltman.py` | rewrite — module docstring cross-check line changed from `Package-X (Patel 2015, 2016) or LoopTools` to `LoopTools` only |

## Skipped files

None — all 12 files were edited.

## Final grep verification

```
grep -rIln -i "package[ _-]\?x\|packagex\|X-2\.1\.1\|hpatel1612\|package_x" \
  --include='*.md' --include='*.py' --include='*.yaml' --include='*.yml' \
  --include='*.json' --include='*.sh' --include='*.wls' --include='*.m' \
  . 2>/dev/null | grep -v '\.shift-manager/' | grep -v 'demo_output/.rotated'
```

**Output: (empty)** — no Package-X references remain outside `.shift-manager/` directories.
