# W5 Review R1 — `/lagrangian-builder` orchestrator

Branch: `workstream/w5-lagrangian-builder`
Worktree: `wt-w5-lagrangian-builder`
Review budget: ~10 min (time-boxed)

## Verdict: APPROVE

## Test count
- `pytest plugins/hep-ph-toolkit/skills/lagrangian-builder/tests/ -q` → **36 passed, 2 skipped** in 0.85s. Matches implementer's claim.

## Findings

### Blocker
(none)

### Major
(none)

### Minor
- `sys.path.insert` with a `.resolve()` of a 4-up relative path into `plugins/shared/install-helpers/` works, but is fragile if the plugin is ever vendored into another layout. The existing `_SHARED_DIR` fallback mitigates this in tests. Consider a tiny `_helpers.py` shim with a single path-resolver, reused across the five scripts, to centralize the anchor. Not blocking — W3/W4 scripts already use the same pattern, so W5 is consistent with the rest of the plugin.

### Nit
- `check_state.py` doc header points at `phase2-plan-final.md §2.3` — fine, keep as-is.
- SKILL.md is long (~420 lines) but well-structured with a decision tree at top; meets the SKILL.md-driven contract.

## Check-by-check

1. Tests: 36 passed, 2 skipped — OK.
2. Diff stat: 20 files total. 18 under `plugins/hep-ph-toolkit/skills/lagrangian-builder/**`, plus `plugins/hep-ph-toolkit/README.md (model-building section)` (expected full rewrite) and top-level `README.md` (11 lines, brief line item). No scope creep.
3. `orchestrate.py` absent — OK. Directory listing confirms only the five named scripts.
4. SKILL.md lines 1–80: prose decision tree with Step 0..7, per-step bash snippets, and explicit "SKILL.md-driven ... no top-level Python state machine" statement. Correct.
5. Starter templates: `test_starter_templates.py` is in the passing set (135 lines, covers all three YAMLs).
6. `activation_required`: line 149 says "This is NOT a blocker. It is a user-actionable pause. Do not emit a fatal blocker JSON for this condition." Exactly the required contract. `orchestration.md` ledger lines 49, 126 concur.
7. `MODELSPEC_FEATURE_UNSUPPORTED`: present at SKILL.md lines 262, 273–290, with an explicit "Do NOT fall back to free-form Mathematica or analytic Python" — matches the augment-not-replace memory.
8. Cross-skill imports: zero. All `sys.path.insert` entries point at `plugins/shared/install-helpers/` (sanctioned shared helper) or the `_shared/` test fallback. No direct imports of other skills' modules.
9. (see decision below)
10. README diffs: top-level is a 10-line addition listing the five SARAH/SPheno skills under model-building — brief and appropriate. Plugin README is the expected full rewrite.

## Decision on flagged question
**Subprocess is the right call.** `validate_interview.py` invokes `sarah-build/scripts/validate_spec.py` via `subprocess.run([sys.executable, ...])`, captures stderr, and forwards the blocker JSON on failure. This keeps the two skills as independent tools (correct skill-as-CLI posture), avoids coupling W5 to W3's import surface, and naturally propagates exit codes and blocker JSON without needing to reshape exceptions. Direct import would create a cross-skill dependency that the rest of the plugin studiously avoids.
