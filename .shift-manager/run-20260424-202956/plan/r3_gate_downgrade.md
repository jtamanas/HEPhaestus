# R3 — Gate-Downgrade Policy (pre-locked)

Per synthesis-locked decisions.

## Downgradable gates

| Gate | Default | Downgrade policy |
|---|---|---|
| G4 (iter_6_notes.md exists) | warning if file begins "RECONSTRUCTION INCOMPLETE" | Downgrade to WARNING unconditionally — G4 failing does not block playtest dispatch. |
| G6 (maddm_run import works) | fail if import fails | Downgrade to WARNING iff SKILL.md contains inline sys.path.insert workaround with comment. |

## Non-downgradable gates

| Gate | Rationale |
|---|---|
| G2 (patch_paramcard.AUDIT.md + Wchi=0.0) | Physics correctness. Wchi=0.0 is synthesis-locked. Must not be relaxed. |
| G3 (schema validates SKILL.md example) | Cross-workstream contract. Must not be relaxed. |

## Non-negotiable gates (cannot be downgraded or waived)

| Gate | Reason |
|---|---|
| G1 (demo_output clean, no stale POST_MORTEM) | Idempotency precondition for playtest |
| G5 (no --skip-render references) | Renderer invocation correctness |
| G7 (env.json has all 8 keys with dual SHA) | Audit trail completeness |
| G8 (Wolfram Engine responds) | SARAH runtime dependency |
| G9 (TwoHdmAfix absent or clean-diff vs fixture) | Model purity precondition |
| G10 (git status shows only allowed scope prefixes) | Scope isolation |

## Overall gate resolution

- Any non-negotiable (G1, G5, G7, G8, G9, G10) fails → overall = fail
- Any non-downgradable (G2, G3) fails → overall = fail
- Only G4 or G6 are warning/fail (within above policy) → overall = warning
- All gates pass → overall = pass
