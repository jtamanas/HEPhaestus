# Singlet-Doublet Phase 0 (Prep) — Opus Review #1

**Verdict**: ACCEPT-WITH-NOTES — green-light proceed-to-Phase-1.

**Reviewer**: opus-4-7  •  **Branch**: `sd/prep-20260424` (commits 6b2cd8e, 369f344, f339b55) •  **Wall consumed**: ~15 min of 30-min budget.

---

## Per-letter findings

### A. Scope-guard — PASS
12 files changed; all match allowed prefixes. `.playtest/sd/gate_status.json` looks at first like a violation against the P1–P7 preamble (which whitelists only `.playtest/sd-A/**` and `.playtest/sd-B/**`), but it is the gate-evaluator's plan-mandated output (plan §"Gate evaluator" line 318: `Write .playtest/sd/gate_status.json`). Documentation gap in the preamble, not a sonnet error.

### B. P1 — `mv` quarantine — PASS, but worth flagging the seeding mechanism
- Worktree's pre-existing `demo_output/singlet-doublet/` (only `.gitkeep`, no real data because `demo_output/` is gitignored and worktree starts empty) was renamed to `…preplaytest-20260425010956/`.
- Real `relic.json` was COPIED IN from the main checkout's `demo_output/singlet-doublet/relic.json` (mtime 2026-04-23 22:33). Byte-for-byte identical to production: `omega_h2=0.292`, `m_chi1=132.692344`, `status=ok`, MS=150, MPsi=500. Not fabricated.
- The copied file is NOT committed (gitignore blocks it) — it lives only in the worktree's untracked tree as a P2 read-target. This is FINE for Phase 0 (P2 reads it), but the SD plan never explicitly authorized cross-worktree data import. Sonnet's p1.md transparently documents the move.
- Risk to flag: if the worktree gets pruned, P2's data source vanishes. baseline.json (the persistent artifact) captures the value, so no actual fragility for Phase 1.

### C. P2 baseline 0.292 — PASS
- baseline.json: `{omega_h2: 0.292, source_ts: 20260425010956, hardcoded_reference: 0.292, tolerance: 0.01, drift_flag: false}`. Source: copied real relic.json. Trace: production run 2026-04-22T2241Z-aee644cc → relic.json in main demo_output → copied into worktree → read by P2.
- `drift_flag=false` is correct for THIS captured value (0.292 == 0.292, |Δ|=0). The 0.163→0.292 drift the synthesis flagged is an inter-version drift between commit a05f274 and earlier states; P2 captures the CURRENT-prod value and compares against the synthesis-locked 0.292 reference, so no drift is the right answer here.

### D. P3 — Variant B substitution — PASS
- Diff `practitioner_script.md` vs `practitioner_script_B.md`: exactly one line differs (line 61), exactly one token: `` `ZN` `` → `` `N` ``. Inside the SARAH "Neutral Majorana 3×3" mixing-matrix description — exactly the SARAH-relevant token the synthesis specified.
- No prose mentions of `ZN` elsewhere in the original script (verified `grep -n ZN` returned only line 61).
- macOS sed-vs-perl substitution: sonnet used `perl -i -pe 's/\bZN\b/N/g'` because BSD sed lacks `\b`. Documented clearly. Functionally correct.

### E. P3 — XDG seeding — PASS
- `diff` against `~/.config/hep-ph-agents/config.json` for both `sd-A` and `sd-B`: identical (byte-equal).
- For downstream consumers, sub-agents will set `XDG_CONFIG_HOME=…/.playtest/sd-X/xdg` (per Phase 1 prompt template), pointing readers at the variant-local copy. Correct topology.
- Note: per-variant `state/` dirs are not yet created (gitignored empty dirs vanish at commit). The Phase 1 launcher exports `HEPPH_STATE_ROOT` which auto-creates on demand. Non-issue.

### F. P3 — schema poll timeout — DEFECT (cosmetic, non-blocking)
- Plan §P3: poll up to 1800s in 10s increments via explicit `while [ $(date +%s) -lt $DEADLINE ]; do … sleep 10; done`.
- Reality: P1 commit at 21:11:50 → P2-P7 omnibus commit at 21:12:53. Total elapsed for steps P1–P7 inclusive: 63 seconds. The poll loop did not wait. Sonnet's transcript implies one check, sentinel absent → wrote `schema_ready=0` and moved on.
- Manager-written sentinel landed at 21:16:53 — about 4 min AFTER P3 completed. Even a faithful 1800s poll would have caught it.
- Per the manager's review brief: WARN stays for this round; do NOT instruct sonnet to re-run. So this is a logged-only deviation. Phase 1 is unaffected because G9 WARN was the plan's downgrade-anyway path.

### G. P4 — broken-backups — PASS
- Both candidate roots checked: `/Users/yianni/MG5_aMC/PLUGIN/` (the config's MG5 root) — no `*broken-backup*`. Also `/Users/yianni/MG5_aMC_v3_5_6/PLUGIN/` — no matches. p4_cleanup.txt = `0`. G4 evidence reflects the canonical path.

### H. P5 — wolframscript probe — PASS (matches plan spec)
- Plan demands `timeout 5 wolframscript -code 'Print["ok"]'` and grep `^ok$` + `exit=0`. Sonnet ran with `timeout 30` (slack increase) — output `ok\nNull\nexit=0`. Both grep predicates satisfied. Plan does NOT call for a SARAH `Get["SARAH.m"]` smoke at this stage; that ships with the Phase 1 FIFO+flock wrapper. No defect.

### I. P7 — env.json — PASS, no XDG-config bug recurrence
- All 5 plan-required keys present in both variants: `git_sha`, `mg5_version`, `python_version`, `wolfram_version`, `config_json_snapshot`. Plus the bonuses (`maddm_plugin_sha`, `sarah_version`).
- Critical contrast vs 2HDM+a's prep: `mg5_version` is `"3.5.6 (2024-09-26)"` — NOT `"unavailable"`. Sonnet pulled it from `${MG5_DIR}/VERSION` (per p7.md), bypassing the broken `mg5_aMC --version` path. The 2HDM+a XDG-config bug does NOT recur in SD's env capture.
- `maddm_plugin_sha=no-git` is a real finding (the maddm plugin dir is not a git repo). Faithfully reported, not a fabrication.

### J. Gates G1–G9 — re-evaluation matches sonnet's gate_status.json
| Gate | My eval | Sonnet | Notes |
|------|---------|--------|-------|
| G1 | PASS | PASS | preplaytest dir exists, fresh demo_output/singlet-doublet has only .gitkeep |
| G2 | PASS | PASS | baseline.json well-formed, includes hardcoded_reference |
| G3 | PASS | PASS | XDG configs faithful; B script ZN-count=0 |
| G4 | PASS | PASS | 0 broken-backup dirs |
| G5 | PASS | PASS | wolfram exit=0, "ok" printed |
| G6 | PASS | PASS | state_root=/tmp/sd-smoke-42332 |
| G7 | PASS | PASS | env.json keys complete on both variants |
| G8 | PASS | PASS | working tree clean post-commit |
| G9 | WARN | WARN | sentinel was absent at poll time; per plan, WARN; manager has since written sentinel but per brief, WARN stays this round |

Overall: WARNING — exactly as expected per plan §G9-downgradable. Phase 1 dispatch is plan-sanctioned.

### K. Plan deviations — minimal
1. **P3 schema poll did not run the full 1800s loop** (defect F above). Cosmetic; outcome unaffected.
2. **`mkdir -p …/state` skipped** in committed tree (empty dirs don't survive git). Phase 1 auto-creates via HEPPH_STATE_ROOT export. Non-issue.
3. **wolfram timeout 5 → 30** (P5). Slack increase, no risk.
4. **P1 cross-worktree relic.json copy** is plan-implicit (P2 needs to read it). Not in plan, but P2 cannot execute without it. The plan's prompt body was authored assuming the file would be there; sonnet had to bridge that gap. Documented.

Nothing skipped. Nothing added beyond plan scope.

---

## Concrete defect list

| ID | Severity | File / location | Defect | Fix (deferred — does not block Phase 1) |
|----|----------|-----------------|--------|------------------------------------------|
| R1-1 | minor | P3 poll execution (no artifact) | Schema-sentinel poll did not honor 1800s deadline; returned in <60s. | Cosmetic; G9=WARN still correct. If we ever expect sentinel write to lag prep dispatch by minutes, plan should require evidence of the poll duration (e.g. log start_ts+end_ts in `schema_wait_result.json`). |
| R1-2 | warning | Plan §Phase 0 preamble (l. 79–87) | Phase 0 preamble whitelists `.playtest/sd-A/**` and `.playtest/sd-B/**` but the gate-evaluator (separate dispatch) writes `.playtest/sd/gate_status.json`. Scope-guard regex would flag this if applied uniformly. | Plan should note `.playtest/sd/**` as an allowed gate-evaluator output prefix (or carve out a separate allowlist for the gate evaluator dispatch). |
| R1-3 | minor | `baseline.json` provenance | `source_ts` claims `20260425010956` but the underlying relic.json was authored 2026-04-23 22:33 (production), not 2026-04-25. The TS reflects when sonnet renamed the dir, not when the data was generated. | Add a `relic_authored_at` field in future to disambiguate run-time vs file-mtime. |

None of R1-1/2/3 block Phase 1.

---

## Green-light: proceed to Phase 1

- All 8 non-negotiable gates PASS.
- G9 is WARN per plan-sanctioned downgrade.
- Real production data sources baseline (no fabrication).
- Variant B perturbation is exactly the locked single-axis ZN→N rename, no prose contamination.
- env capture clean — sidesteps the 2HDM+a `mg5_version=unavailable` bug.
- Scope-guard clean.
- Manager may flip `sd-merge_ready.json.ready_for_playtest=true` and dispatch PT-A and PT-B in parallel from `sd/prep-20260424` HEAD (f339b55).

Tries: `{phase:"prep", sonnet_tries:1, opus_tries:1, status:"ACCEPT-WITH-NOTES"}` written to `.shift-manager/run-20260424-202956/state/sd-tries.json`.
