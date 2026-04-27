# Singlet-Doublet Phase 0 (Prep) — Final Summary

**Workstream**: singlet-doublet  
**Branch**: `sd/prep-20260424`  
**Worktree**: `/Users/yianni/Projects/hep-ph-agents.worktrees/sd-prep/`  
**Implementer**: Sonnet 4.6  
**Wall budget consumed**: ~15 min (well within 45 min ceiling)

---

## Per-Step Status

| Step | Status | Notes |
|------|--------|-------|
| P1 | PASS | Stale demo_output moved to preplaytest-20260425010956/; real relic.json copied in; fresh .gitkeep dir created |
| P2 | PASS | baseline.json: omega_h2=0.292, drift_flag=false; exact match to hardcoded_reference=0.292 |
| P3 | PASS | XDG configs seeded per variant; practitioner_script_B.md with ZN→N (perl used, macOS sed lacks \b); schema sentinel absent → G9 warning |
| P4 | PASS | 0 broken-backup dirs in /Users/yianni/MG5_aMC/PLUGIN |
| P5 | PASS | wolframscript 14.3.0 prints "ok", exit=0 |
| P6 | PASS | HEPPH_STATE_ROOT env var honoured by resolve_state_root() |
| P7 | PASS | env.json written for both variants with all 5 required keys |

---

## 9-Item Gate Evaluation

| Gate | Status | Evidence |
|------|--------|---------|
| G1 [NON-NEG] | PASS | relic.json absent; preplaytest-20260425010956/ exists |
| G2 [NON-DOWN] | PASS | omega_h2=0.292, hardcoded_reference=0.292, drift_flag=false |
| G3 [NON-NEG] | PASS | XDG configs present; B script ZN→N (count=0) |
| G4 [NON-NEG] | PASS | 0 broken-backup dirs in /Users/yianni/MG5_aMC/PLUGIN |
| G5 [NON-NEG] | PASS | wolframscript "ok", exit=0 |
| G6 [NON-NEG] | PASS | state_root=/tmp/sd-smoke-42332 |
| G7 [NON-NEG] | PASS | sd-A and sd-B env.json all required keys present |
| G8 [NON-NEG] | PASS | Clean working tree at commit time |
| G9 [DOWNGRADABLE] | WARN | schema_v1_1.ready absent; schema_ready=0; downgraded per plan rule |

**Overall gate result: WARNING** → proceed to playtest

---

## Recommend: PROCEED

- All non-negotiable gates (G1-G8) pass.
- G9 warning is expected and non-blocking per plan.
- baseline.json shows omega_h2=0.292 with drift_flag=false — perfect alignment with synthesis reference.
- Wolfram 14.3.0, MG5 3.5.6, Python 3.10.16, SARAH 4.15.3 all confirmed operational.

---

## Notable Findings

1. macOS sed \b limitation: The plan's sed pattern is a no-op on macOS BSD sed. Used perl -i -pe instead.
2. demo_output gitignored: Worktrees share gitignored namespace with main checkout. Copied real relic.json into preplaytest dir for P2.
3. config.json madgraph_path is binary path, not MG5 root. Gate evaluator derives root via dirname(dirname(binary)).
4. G9 / schema sentinel: 2HDM+a's schema_v1_1.ready not present at poll time. Per plan: G9=warning, Phase 1 proceeds.

---

## Commits on sd/prep-20260424

1. 6b2cd8e — [sd-prep] P1: move stale demo_output/singlet-doublet aside, record baseline_ts
2. 369f344 — [sd-prep] P2-P7: baseline capture, variant configs, tool smokes, env.json
3. f339b55 — [sd-prep] gate-eval: overall=warning (G9 downgraded, schema sentinel absent)
