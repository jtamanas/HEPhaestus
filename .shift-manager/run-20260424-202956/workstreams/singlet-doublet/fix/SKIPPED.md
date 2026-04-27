# SKIPPED — Out-of-Scope Issues

## sd-A-001 — mg5_aMC --version flag not supported
**Reason**: The preflight `--version` check lives in `plugins/hep-ph-demo/skills/demo/SKILL.md` Step 0, not in `plugins/hep-ph-demo/skills/singlet-doublet/**`. Fixing it requires editing `demo/SKILL.md`, which is outside the allowed scope for SD Phase 2 fix-r1. The install scripts (`install_mg5.sh`) already document this (B6 fix, use `--help` banner). Logged for demo-skill owner.

## sd-A-002 — SARAH Package.m vs SARAH.m
**Reason**: The referenced file `check_state.py` lives in `plugins/model-building/skills/lagrangian-builder/scripts/check_state.py` — outside SD's allowed scope. The singlet-doublet skill files contain no `Package.m` reference. Per PT-A reviewer: "stale doc string in check_state.py". Logged for model-building owner.

## sd-A-003 — HEPPH_STATE_ROOT isolation breaks run_spheno.py
**Reason**: `run_spheno.py` lives in `plugins/model-building/skills/spheno-build/scripts/`. Explicitly called out as OUT OF SD'S PHASE-2 SCOPE by the PT-A opus reviewer. Per MANAGER_DECISIONS.md: SD cannot fix this; requires model-building owner or per-variant state root bootstrap. Skipped per reviewer instruction.

## sd-A-004 — flock not available on macOS
**Reason**: Host-system binary, not in any plugin skill dir. Per MANAGER_DECISIONS.md: accepted as-is for this run. Forward action is plan revision (python fcntl wrapper) in a future session. Explicitly out of scope per PT-A reviewer.
