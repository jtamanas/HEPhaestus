# Fix Loop R1 — Dark SU(3) — SUMMARY

**Agent:** sonnet fix-loop (dsu3/fix-r1-20260424)
**Branch:** dsu3/fix-r1-20260424 (from a46f796)
**Commits:** f22bd53, 256bb16, 09db9d5, 3161092
**Timestamp:** 2026-04-24

---

## Edit Status

| # | Issue | File | Line(s) | Status |
|---|---|---|---|---|
| 1 | dsu3-001b | `plugins/hep-ph-demo/skills/_shared/constraints.yaml` | 148 | FIXED |
| 2 | dsu3-001c | `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md` | 90 | FIXED |
| 3 | dsu3-001a | `plugins/hep-ph-demo/skills/demo/SKILL.md` | 73 | FIXED |
| 4 | dsu3-002  | `plugins/hep-ph-demo/skills/demo/SKILL.md` | 80 (inserted) | FIXED |

All 4 edits FIXED. 0 SKIPPED. 0 escalations.

---

## Stale-string verification

```
grep -rnI "Confining dark sector" plugins/hep-ph-demo/skills/
→ ZERO HITS
```

## Banner verification

```
grep -rnI "regression-anchors|sigmav_approx=True|out of reach this run" plugins/hep-ph-demo/skills/
→ plugins/hep-ph-demo/skills/demo/SKILL.md:80  (exactly 1 match)
```

Banner line: 80 (recorded in banner_inserted.txt)

---

## Hash-diff vs. PT1 baseline (five_hashes)

| File | PT1 baseline sha256 | Post-fix sha256 | Changed | In allow-list |
|---|---|---|---|---|
| `_shared/constraints.yaml` | d42d654b... | 7877a96c... | YES | YES (line 148) |
| `_shared/time_budget.py` | f9eb22b9... | f9eb22b9... | NO | --- |
| `analytic_models/dark_su3.py` | f26de75d... | f26de75d... | NO | --- |
| `demo/SKILL.md` | 6ad3df20... | 7ae92258... | YES | YES (lines 73, 80) |
| `dark-su3/SKILL.md` | 17bf1bdb... | 17bf1bdb... | NO | --- |

Only allow-listed files changed. Scope guard: PASS.

---

## Scope guard audit

- No edits to `_shared/summary.schema.json` - PASS
- No edits to `_shared/time_budget.py` - PASS
- No edits to `_shared/analytic_models/**` - PASS
- No edits to any singlet-doublet or 2hdm-a file - PASS
- `_shared/constraints.yaml` edit confined to line 148 - PASS
- `_shared/tests/MANUAL_WALKTHROUGH.md` edit confined to line 90 - PASS
- `demo/SKILL.md` edits: line 73 (stale string) + line 80 (banner insert) - PASS
- Lock acquired via `mkdir` before each `_shared/` edit; released after - PASS
- Banner insertion line recorded in `banner_inserted.txt` - PASS

---

## Git log (fix branch)

```
3161092 fix(dsu3-r1): dsu3-002
09db9d5 fix(dsu3-r1): dsu3-001a
256bb16 fix(dsu3-r1): dsu3-001c
f22bd53 fix(dsu3-r1): dsu3-001b
a46f796 [PT1 baseline]
```
