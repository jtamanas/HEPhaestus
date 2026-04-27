# Dark SU(3) Phase 2 — Fix R1 Opus Review

**Verdict: ACCEPT**

Branch: `dsu3/fix-r1-20260424` @ `3161092`
Base: `a46f796`
4 commits, 3 files changed, +5/-4 lines. Docs-only as scoped.

---

## A. Scope-guard compliance — PASS

`git diff a46f796..HEAD --name-only` returns exactly:
- `plugins/hep-ph-demo/skills/_shared/constraints.yaml`
- `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md`
- `plugins/hep-ph-demo/skills/demo/SKILL.md`

All three are on the allow-list. Line ranges:
- constraints.yaml: line 148 only (the `hook:` field).
- MANUAL_WALKTHROUGH.md: lines 90–91 (collapsed two lines into one — minor expansion of allow-listed line 90, no scope creep).
- demo/SKILL.md: line 73 (description string) + new banner inserted as new line at 80 — within dark-su3 model selection section, exactly as specified.

Zero out-of-scope edits.

## B. dsu3-001a/b/c (stale strings) — PASS

All three replacements:
- **001a (constraints.yaml:148)**: "Confining dark sector, two DM candidates with exact parameter-independent blind spot." → "Higgsed SU(3)_D → SU(2)_D dark sector; dark Higgs doublet PhiD, vector DM (V) and fermion DM (Psi); exact parameter-independent SI blind spot." Consistent with synthesis Higgsing model and dark-su3 SKILL.md prose. Minimum diff (single line).
- **001b (demo/SKILL.md:73)**: "Confining dark sector, two DM candidates with exact blind spot." → "Higgsed SU(3)_D → SU(2)_D dark sector with two DM candidates and exact parameter-independent SI blind spot." Single line, preserves blocking note. Clean.
- **001c (MANUAL_WALKTHROUGH.md:90)**: same Higgsed wording, collapses the two-line description into one with the "blocked" note preserved. Acceptable formatting consolidation, still minimum-impact.

All three eliminate "Confining dark sector" and replace with Higgsing-correct prose. No collateral edits.

## C. dsu3-002 (banner) — PASS

Inserted at `demo/SKILL.md:80` as a single line:

```
<!-- dsu3-banner: NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets. -->
```

- Position: directly after the `AskUserQuestion` JSON block that contains the `dark-su3` option, before the cold-hour-estimates paragraph. Squarely within the dark-su3 model selection section.
- Marker comment present: `<!-- dsu3-banner: ... -->` — `grep -c dsu3-banner` returns 1 (single insertion, not duplicated).
- Wording: contains all three required substrings — `sigmav_approx=True`, `out of reach this run`, `regression-anchors`. Verbatim match against synthesis lines 117–119.

## D. "Confining dark sector" eradication — PASS

`grep -rn "[Cc]onfining dark sector" plugins/hep-ph-demo/skills/` → ZERO HITS. Sonnet's claim verified.

## E. Hash-diff (file-set) — PASS (sonnet's SUMMARY claim was inaccurate, actual state is correct)

`git diff a46f796..HEAD --stat`:
```
 plugins/hep-ph-demo/skills/_shared/constraints.yaml            | 2 +-
 plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md | 3 +--
 plugins/hep-ph-demo/skills/demo/SKILL.md                       | 4 +++-
 3 files changed, 5 insertions(+), 4 deletions(-)
```

All three allow-listed files changed (including MANUAL_WALKTHROUGH.md from commit 256bb16, as expected).

## F. Banner line tracking — PASS

`banner_inserted.txt` contains `80`. Matches actual insertion line in `demo/SKILL.md`.

## G. No physics drift — PASS

Note: there is no `analytic_models/dark_su3.py` in this codebase. Physics code lives in `plugins/hep-ph-demo/skills/dark-su3/` and `plugins/hep-ph-demo/skills/_shared/assets/dark_su3.yaml`. Verified neither path appears in `git diff a46f796..HEAD --name-only`. Physics code byte-for-byte unchanged.

## H. Commit hygiene — PASS

```
3161092 fix(dsu3-r1): dsu3-002
09db9d5 fix(dsu3-r1): dsu3-001a
256bb16 fix(dsu3-r1): dsu3-001c
f22bd53 fix(dsu3-r1): dsu3-001b
```

All four follow `fix(dsu3-r1): <short-id>`. Topologically odd order (b,c,a,002 by author time) but each commit is atomic and self-describing — non-blocking.

---

## Final state

**dark-su3 workstream: COMPLETE**

All 4 PT1 spec items addressed with minimum-diff, scope-compliant edits. No physics drift. Stale "Confining dark sector" wording fully eradicated. Banner correctly placed and worded verbatim per synthesis. Round 1 sonnet+opus pass — no need for round 2.

Tip SHA: `3161092`
