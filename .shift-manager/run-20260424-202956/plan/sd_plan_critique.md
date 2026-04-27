# Singlet-Doublet Plan Draft — Skeptic

Author: plan-skeptic (SD)
Method: 2HDM+a parity check + SD-specific seam attacks.

---

## 1. Hard-block parity check (vs 2HDM+a critique)

| # | 2HDM+a hard-block | SD plan status | Verdict |
|---|---|---|---|
| 1 | G1–G10 inlined into gate-evaluator prompt | **MISSING.** Plan references G1–G9 by name in tasks but never inlines the 9-item gate from synthesis lines 192–204 into a gate-evaluator agent prompt. G8 says "Manager verifies"; no sonnet prompt body. | **Hard-block.** |
| 2 | Forbidden-prefix list pasted into opus reviewer prompt | **PARTIAL.** Plan §"Scope guard paths" lists prefixes in prose, but Phase 2 dispatch description (lines 207–214) never embeds them into the opus reviewer/verify prompt template. | **Hard-block.** |
| 3 | Sentinel files explicitly created | **N/A for SD** (no `.patched`/`.output_marker` analog needed — SD has no patcher phase). However the `flock` lockfile path `~/.cache/hep-ph-agents/sarah_makeufo.lock` is referenced but the plan never says who creates the parent dir or what permissions. Add `mkdir -p ~/.cache/hep-ph-agents` to P3 or P5. | Nice-to-fix. |
| 4 | Prep→playtest branching specified (commit before branch) | **MISSING.** Worktree table shows `sd-A-20260424` "from main HEAD post-prep" but the plan never says "manager commits sd-prep, fast-forwards main to sd-prep tip, THEN creates sd-A/sd-B." If sd-prep commits don't reach `main`, sd-A and sd-B branch from stale `main`. P3 itself runs in `sd-prep`, but it creates the A/B worktrees *from main* — so P3's own work isn't visible to A/B unless an explicit merge step exists. | **Hard-block.** |
| 5 | Try-counter persistent state file | **MISSING.** Plan §"Stopping rule" item 2 says "Total `fix_attempts.length` for SD > 5" but never names the file. Should be `.shift-manager/run-20260424-202956/state/sd_fix_attempts.json` written deliberately by manager between dispatches. | **Hard-block.** |
| 6 | Cross-workstream schema lock — file-based gate | **WEAK.** Plan §"Cross-workstream gate" / G9 is a one-line ack ("2HDM+a owns; SD reads"). No sentinel file `_shared/.schema_owner.lock`, no concrete check ("SD blocks until `.shift-manager/.../2hdma_p3_done.marker` exists"). Plan says "If 2HDM+a P3 not done by SD prep-end, downgrade G9 to warning" — that's a soft fallback, not a gate. | **Hard-block.** |
| 7 | SARAH serialization mechanism with 2HDM+a — concrete how | **PARTIAL.** Plan names lock path (`~/.cache/hep-ph-agents/sarah_makeufo.lock`) and `flock -w 300` semantics — that's better than 2HDM+a critique's complaint. But plan never says: (a) who creates the lock file, (b) whether SD-A and SD-B both contend (two SD-internal acquisitions), (c) what happens at 300s timeout. Three-way queue (SD-A, SD-B, 2HDM+a) is not analyzed at all. | **Hard-block** (see §3.1 below). |
| 8 | Cumulative-budget abort at 150 min | **MISSING.** Plan declares "150 min ceiling" but no manager step that logs wall-clock at phase boundaries and aborts. Same gap as 2HDM+a. | **Hard-block.** |
| 9 | Multi-importer grep (P6 analog) | **N/A for SD.** SD's P6 is a smoke test of `HEPPH_STATE_ROOT`, not a sys.path edit. No code being patched ⇒ no multi-importer concern. | OK. |
| 10 | `.patched`/sentinels in gitignore | **N/A** (no sentinels created). Worth checking: does `demo_output/singlet-doublet/` get gitignored or is it tracked? P1 moves it aside which `git status` will see — does the prep commit include the moved dir? Plan is silent. | Nice-to-fix. |

**Parity score: 6 hard-blocks carry over (1, 2, 4, 5, 6, 7, 8) + 1 SD-specific that 2HDM+a critique missed.**

---

## 2. SD-specific attacks

### 2.1 Two-variant + 2HDM+a three-way SARAH flock — **HARD-BLOCK**
Plan says SD-A, SD-B, and 2HDM+a all flock on `~/.cache/hep-ph-agents/sarah_makeufo.lock`. `flock` with `-w 300` is FIFO-ish but not strictly fair on macOS (BSD flock semantics). Three-way queue: if 2HDM+a grabs first, holds ~2 min; then either SD-A or SD-B grabs (race). The plan claims "B's whole point is testing rename regression" but if B starves >300s it gets timeout failure, polluting issues.jsonl with a non-physics error. **Verdict**: enumerate ordering — manager must dispatch SD-A SARAH first, hold SD-B until A releases, both ack before yielding to 2HDM+a. Or add `flock` queue with explicit `lockf` ordering. Current plan: hand-waves "manager polls at 5s." Not enough.

### 2.2 Baseline tautology — **HARD-BLOCK (conceptual)**
Plan P2 captures `omega_h2` from the **moved-aside** `demo_output/singlet-doublet.preplaytest-<TS>/relic.json`. That value becomes baseline. Variant A G3 then checks freshly-produced `omega_h2 == captured ± 0.01`. **This is comparing the run's output to a snapshot taken from a prior run of the same code at the same SHA** — i.e. a determinism check, not a regression check. If the bug being hunted is "code drifted between commits," P2's baseline already encodes the drift. The drift from 0.163 → 0.292 is itself a bug; capturing 0.292 as truth bakes it in. **Verdict**: defensible only if P2's baseline + criterion 3 is renamed "determinism check" and a separate hard-coded historical baseline (0.163 from devlog 2026-04-22, OR a literature value) is added as a secondary criterion logged at `severity: major` if violated. Plan §"Failure modes" item 3 acknowledges the drift but treats P2 as ground truth; that's theater.

### 2.3 Manual `/demo` emulation reading budget — **HARD-BLOCK**
Plan §"KEY DESIGN" says sonnet reads `demo/SKILL.md` then `singlet-doublet/SKILL.md` then chains into `lagrangian-builder/SKILL.md` → `sarah-build/SKILL.md` → `spheno-build/SKILL.md` → `madgraph/SKILL.md` → `maddm/SKILL.md` → plot/summary skills. Eight SKILL.md files plus their referenced runbooks/scripts. At ~500–2000 lines each, that's 5–15k lines of context just for instruction-reading **before** any tool runs. **No reading-budget cap is set in the prompt.** Sonnet may compact mid-chain, losing the practitioner script answers. **Verdict**: prompt must say "read SKILL.md JIT — only when entering that phase" and "if context >70% capacity, write current state to `run.log` and halt with `severity: blocker, phase: agent_capacity`." Plan as written assumes infinite context.

### 2.4 Variant B `N` clashes with MSSM neutralino — **MAJOR FINDING (plan acknowledges, but…)**
Plan §"Failure modes / Variant B" treats SARAH-error or MadDM-rejection as `severity: major` and silent breakage as `blocker`. Good. But the plan never asks: does SARAH **actually** allow `N` as a user-defined Weyl spinor name? SARAH ships MSSM with `N[1..4]` reserved for neutralinos; user-model collision behavior is implementation-defined. **If SARAH errors immediately at parse**, B never reaches MadDM and the test of "silent semantic break" never executes. Failure mode is captured (per Q4 acceptance) but the *intended* test (silent rebind) cannot fire. **Verdict**: plan should add a pre-Phase-1 5-line probe — `wolframscript` running `Get` on the B model and reporting any `N` symbol clash — so the team knows in advance what failure surface is being tested. Otherwise we're testing SARAH's parser, not skill prose.

### 2.5 Observe-only contract — **HOLDS**
Plan §"Phase 1" prompts both variants explicitly say "OBSERVE-ONLY: log issues to issues.jsonl, do NOT modify any code." Sonnet bullet 5 logs and halts on blocker. No sneak-in writes. Synthesis Q7 satisfied.

### 2.6 30-min fix budget vs opus rounds — **HARD-BLOCK**
Plan §"Phase structure" says "≤30 min fix-loop." Phase 2 lists sonnet diagnose ≤15 + opus review ≤10 + sonnet implement (no cap) + opus verify (no cap). 15+10 = 25 already; one cycle's implement+verify could easily blow the 30-min cap, and three cycles certainly will. Plan never says whether opus review wall-time counts, same problem as 2HDM+a. **Verdict**: explicitly include opus rounds in budget; cap at 30 min wall-clock for the whole Phase 2 from kick-off, with a manager abort at +30 regardless of cycle position.

### 2.7 MadDM first-launch flock — **HARD-BLOCK**
Variant B prompt (line 167–168) names `flock -w 300 $MG5_PATH/.playtest.lock` — only B has it. Variant A doesn't. If A launches MadDM first (most likely) and B is gated by a flock A doesn't acquire, **A's first launch races against any 2HDM+a MadDM init**. Plan does not say if 2HDM+a uses the same lock. Realistic answer: 2HDM+a workstream isn't doing MadDM (it's MG5+SPheno per its synthesis), so there's no SD↔2HDM+a MadDM contention — but A and B both initialize the MadDM PLUGIN dir. **Verdict**: A's prompt also must acquire `$MG5_PATH/.playtest.lock` before its first MadDM launch. Otherwise A and B race on `PLUGIN/maddm/` initialization (which is the most-cited bug in `maddm-workarounds.md`).

### 2.8 `HEPPH_STATE_ROOT` per-worktree env var — **VERIFIED present**
Variant A prompt line 128–129 sets `HEPPH_STATE_ROOT=$PWD/.playtest/sd-A/state` and `XDG_CONFIG_HOME=$PWD/.playtest/sd-A/xdg`. Variant B mirrors. Good. **But**: env vars are set in the prompt text, not in a parent shell the sonnet inherits. Sonnet must `export` them at the top of every bash invocation. Prompt should say "every bash command in this session must be prefixed with these exports OR run inside a shell where they're set." Otherwise the second bash call drops them.

### 2.9 P1 cleanup vs P2 baseline — **MINOR ORDER ISSUE**
P1 moves `demo_output/singlet-doublet/` → `demo_output/singlet-doublet.preplaytest-<TS>/`. P2 reads `demo_output/singlet-doublet.preplaytest-<TS>/relic.json`. P2's "Cmd" line 46 has the literal placeholder `<TS>` — sonnet must template-substitute the timestamp from P1. Plan never says how (env var? file? deterministic re-glob?). **Verdict**: P1 should `echo $TS > .shift-manager/.../sd/baseline_ts.txt`; P2 reads it. Minor but unambiguous.

Cleanup-vs-baseline ordering itself is fine: P1 moves aside, P2 reads from the moved-aside copy. The moved-aside copy IS the prior-run artifact, so reading from it gives a clean snapshot of the prior state. No contamination.

### 2.10 `XDG_CONFIG_HOME` vs repo `config.json` — **HARD-BLOCK**
Plan claims per-variant `XDG_CONFIG_HOME` isolates `config.json`. **But** the project's `config.json` is at `~/.config/hep-ph-agents/config.json` — yes, that IS XDG-compliant, so the isolation works for *that* file. However, P7 deliverable line 90 says `config_json_snapshot` is "verbatim copy of `~/.config/hep-ph-agents/config.json`" — that's the **host** path, not the per-worktree XDG path. If the variant-specific `XDG_CONFIG_HOME=.../sd-A/xdg` is empty (because nothing populated it), the demo skill will read no config and fail at preflight. **Verdict**: P3 or P7 must seed `$XDG_CONFIG_HOME/hep-ph-agents/config.json` with a copy of the host config (or a per-variant-edited version) before Phase 1. Otherwise isolation = empty config = preflight blocker.

---

## 3. Cross-workstream coordination gaps

1. **Three-way SARAH flock fairness** (§2.1) — already covered.
2. **G9 is ack-only** (§1 row 6) — needs `2hdma_p3_done.marker` file SD checks before Phase 1.
3. **MadDM flock scope** (§2.7) — must include Variant A.
4. **Schema lock**: 2HDM+a critique recommended `_shared/.schema_owner.lock` sentinel. SD plan inherits the missing sentinel — neither plan creates it, both assume the other respects ownership. Manager must create lock when 2HDM+a P3 starts.
5. **Manager has no live scheduler**: plan says "manager polls lock at 5s intervals when SD enters sarah-build." Manager is a one-shot orchestrator, not a daemon. Realistic: sonnet itself runs `flock -w 300` inline; manager just dispatches sequence. Plan's wording suggests an unrealistic manager role.

---

## 4. Missed in-plan failure modes

1. **`practitioner_script_B.md` location ambiguity**: P3 says "in sd-B: copy `plugins/.../practitioner_script.md` → `practitioner_script_B.md`" but never specifies destination dir. Synthesis line 22 says it lives at `.shift-manager/.../sd/practitioner_script_B.md` (run-state); plan implies it lives in the worktree's `plugins/.../singlet-doublet/`. Inconsistent. Pick run-state to avoid editing committed plugin dir.
2. **G9 timing race**: SD prep can finish before 2HDM+a P3. Plan says "downgrade to warning" but doesn't say SD blocks Phase 1 entry. If SD enters Phase 1 with an unvalidated schema, summary.json may fail validation mid-run, polluting issues.jsonl.
3. **Repeat-A flake check (§4 line 257)**: budget says "30 min for the rerun." But Phase 1 ceiling is 90 min total; if A+B used 70 min, only 20 min remain — rerun cap of 30 violates global budget. Plan never reconciles.
4. **MadDM PLUGIN backup recurrence**: P4 cleans `maddm.broken-backup-*` once. If a Phase 1 crash re-creates it mid-run, neither variant cleans up, and the next phase preflight fails. Add a per-variant cleanup at Phase 1 phase boundary.
5. **`SingletDoublet_B` model name set "BY YOU, not by editing the script"**: Variant B prompt says model name is a separate prompt earlier in the chain. Synthesis Q3/Q5 confirm. But singlet-doublet `SKILL.md` may not actually have a separate model-name prompt; it may derive the model name from a slug. Plan never verifies this prompt exists. If SKILL.md doesn't ask for model name, Variant B silently uses `SingletDoublet` (canonical), and B's distinct-name isolation collapses — A and B share SARAH model dir, race condition.
6. **`env.json` `wolfram_version` capture**: P7 lists `wolfram_version` but never says how (`wolframscript -version`? `WolframKernel --version`?). If sonnet picks the wrong form on macOS (no `WolframKernel` symlink), P7 fails late.
7. **`fix_attempts.length` semantics**: stopping rule says ">5 total". Plan never says whether a single fix-class iteration counts as 1 or N. 2HDM+a uses class-iteration counter; SD uses total. Inconsistency across workstreams complicates manager logic.

---

## 5. Summary

### Hard-blocks (must fix before plan ships)
1. Inline 9-item gate (G1–G9) into a gate-evaluator prompt verbatim (§1.1).
2. Paste forbidden-prefix list into opus reviewer prompt (§1.2).
3. Specify prep→playtest branching: commit sd-prep, ff `main`, then create sd-A/sd-B (§1.4).
4. Persistent try-counter file with explicit path (§1.5).
5. File-based G9 gate (`2hdma_p3_done.marker` or `.schema_owner.lock`), not ack-only (§1.6).
6. SARAH flock three-way ordering and Variant A/B serialization (§1.7, §2.1).
7. Cumulative-budget abort step at 150 min (§1.8).
8. Baseline strategy: separate "determinism vs regression" criteria; pin a literature/historical value (§2.2).
9. SKILL.md reading budget cap + JIT-load directive in sonnet prompts (§2.3).
10. Phase 2 wall-clock cap covers opus rounds (§2.6).
11. Variant A also acquires `$MG5_PATH/.playtest.lock` for first MadDM launch (§2.7).
12. Seed per-variant `$XDG_CONFIG_HOME/hep-ph-agents/config.json` before Phase 1 (§2.10).

### Nice-to-fixes
- `~/.cache/hep-ph-agents/` parent dir creation (§1.3).
- `demo_output/...preplaytest-<TS>/` gitignore handling (§1.10).
- Pre-Phase-1 SARAH `N`-name probe for Variant B (§2.4).
- Bash export wrapping for HEPPH_STATE_ROOT/XDG_CONFIG_HOME in every command (§2.8).
- `baseline_ts.txt` for P1→P2 handoff (§2.9).
- `practitioner_script_B.md` location: pick run-state, not plugin dir (§4.1).
- Repeat-A flake budget reconciled with 90-min Phase 1 ceiling (§4.3).
- Model-name prompt verification in singlet-doublet SKILL.md before Phase 1 (§4.5).
- `wolfram_version` capture command spelled out (§4.6).
- Align `fix_attempts.length` semantics across workstreams (§4.7).

### Bottom line
SD plan inherits **7 of 10** 2HDM+a hard-blocks (gate inlining, scope-guard prompt, branching, try-counter, schema gate, SARAH serialization, budget abort) plus adds **5 SD-specific hard-blocks** (baseline tautology, reading budget, fix-budget opus accounting, MadDM flock A-coverage, XDG config seeding). All are textual fixes — no redesign needed, but the plan as drafted is **not yet sonnet-completable safely**. Synthesizer should require an inlining pass before dispatch.
