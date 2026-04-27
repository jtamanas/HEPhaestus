# 2HDM+a Playtest — Skeptic

Author: brainstorm-skeptic
Verifies: `2hdma_propose.md`
Method: read every cited file; greps + diffs.

---

## 1. Verification of proposer's four flagged unknowns

### (a) `/sarah-build --skip-render` flag — **FAIL (aspirational)**

`grep -rn "skip-render\|skip_render"` across `plugins/model-building/sarah-build/` returns ZERO hits. The only `--skip-*` flag in the SARAH/SPheno tooling is `--skip-compile` in `plugins/model-building/skills/spheno-build/scripts/run_spheno.py:96` (different skill, different purpose). SKILL.md L245 ("Invoke /sarah-build with `--model TwoHdmAfix --skip-render`") is **fiction**. The fallback the proposer suggests (`math -run '<<SARAH\`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'`) is the *only* viable invocation today. **The proposer's Phase 2 plan is broken if the agent actually drives `/sarah-build`** — it has to bypass that skill and hit Wolfram directly.

### (b) `patch_paramcard.py` byte-equivalence to iter-8 — **FAIL (it is a reconstruction, not a copy)**

`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py:2-3` literally says: `"patch_paramcard.py — 2HDM+a param_card patcher (iter-8 reconstruction)"` and `"Reconstructed from the description in: ... POST_MORTEM.md"`. This is **not** the original 60-line iter-8 script — it is a 445-line reconstruction synthesized from the post-mortem. The original `iter_8_patch_paramcard.py` is **not present** in `demo_output/2hdm-a/fix_loop/` (verified by `ls`; only `iter_7_*` and earlier exist). Behavioural equivalence is therefore unproven. The reconstruction is far more aggressive than the post-mortem describes (HMIX VEVs, ZAMIX 3×3 with nonzero theta_a=0.1, ZHMIX, ZPMIX, alpha=-0.1 — none of these are mentioned in `POST_MORTEM.md` line 36 as part of the fix). **The "iter-8 was 60 lines; this is 445" gap is a real risk.**

### (c) `_shared/summary.schema.json` exists and matches — **PASS, partial**

File exists at `plugins/hep-ph-demo/skills/_shared/summary.schema.json` (26 lines). It validates `model`, `run_at`, `ran`, `skipped_constraints`, `artifacts_dir`, `headline`. **BUT** `additionalProperties: false` and the schema does **not** declare `relic_approx`, `model_source`, or `model_fixture`. SKILL.md L470-478 emits exactly those extra fields. So the example summary in SKILL.md **fails its own schema**. The proposer's success criterion "summary.json schema matches `_shared/summary.schema.json`" is ill-defined: it can't simultaneously match SKILL.md's example and the schema.

### (d) `iter_6_notes.md` (the seven renderer sites) — **FAIL (file does not exist)**

`find /Users/yianni/Projects/hep-ph-agents -name "iter_6_notes*"` returns **nothing**. `POST_MORTEM.md:79`, `:103`, `:117`, and `FINAL_STATUS.md:67,73,80` all reference `iter_6_notes.md` as the canonical list of seven renderer sites — **but the file was never written**. The closest artifact is `iter_6_playtest_report.md` (different file, different content). **The "seven renderer sites" in the scope doc are vapor.** Anyone planning a renderer backport has nothing concrete to read. This is a blocker for the renderer workstream and the proposer didn't catch it.

---

## 2. Factual errors / risks in the proposal

- **L40-42 fallback is the *only* path.** Proposer says "fall back to direct math invocation if the skill rejects --skip-render." But `--skip-render` doesn't exist *at all* — there's no skill to reject the flag, the skill will misroute. Update: the agent must *not* attempt `/sarah-build` for 2hdm-a. Drive `wolfram -script` directly.
- **L279 of SKILL.md (`from scripts.maddm_run import generate_maddm_script`)** points at `plugins/monte-carlo-tools/skills/maddm/scripts/maddm_run.py`. Import only works with that on `sys.path`. Proposer's "Exact sequence from SKILL.md L286-326 — no improvisation" inherits this import landmine.
- **Workspace already polluted.** `demo_output/2hdm-a/summary.json` exists with `run_at: 2026-04-22T12:10:00Z` and `"ran": []` plus a stale "BLOCKED at /sarah-build" headline. A naive playtest agent could read this as evidence the run completed and skip writing a fresh one. Proposer's artifact contract (§9) doesn't require deletion of stale outputs. **Add to invocation: `rm -rf demo_output/2hdm-a/` before Phase 0.**
- **Fixture deploy is already on disk and out of sync.** `/Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix/` already contains the four `.m` files (last modified 22 Apr). The fixture has a `README.md` that the deployed dir lacks; the four `.m` files match. Proposer's diff-then-copy block works correctly here, but the implied invariant ("hand-crafted means fragile") is wrong: this is a committed fixture; it is reproducible.

---

## 3. Scope challenges

### Keep: "fixture path only, no renderer backport" — **CONDITIONAL KEEP**

Proposer is right that a 1-night renderer fix is unrealistic and risks polluting singlet-doublet (which uses the same renderer). But the user's literal goal — "make sure they all work" — is **practitioner-facing**, not maintainer-facing. From a cold reader's POV, "it works" means "I select 2HDM+a from `/demo`, answer the questions, get Ωh²." That demands either (i) the renderer works, or (ii) the SKILL.md prose is honest about Step 4a being a copy step and the practitioner accepts that. The current SKILL.md (L12-19, L101-106) IS honest about this. So scope is fine **only if the playtest is allowed to print "uses hand-crafted SARAH model fixture (renderer is debt)" as part of success.**

### Reject: "strictly observe + log, no fix-loop" — **REJECT, narrow exception**

User said: "spin up agents to resolve any issues that arise." Proposer says: "no fix-loop authorization." That is a direct contradiction the proposer rationalized away. The principled middle path: **fix in `plugins/hep-ph-demo/skills/2hdm-a/` only**, never in `plugins/model-building/`. The proposer's §7 git-diff guard captures this — but then §7 also says "no fix-loop." Make up your mind. **Recommendation: spawn at most one fix-attempt per failure class, gated to the 2hdm-a skill subtree, max 3 iterations.**

### Challenge: "serialize SARAH between SD and 2hdm-a" — **WEAK EVIDENCE**

Proposer admits in §"Unknowns" that it's a guess ("Would prefer empirical confirmation"). Searching the repo for license/multi-seat evidence: no Mathematica activation log, no `.WolframKernel` lock files, no documented contention. Wolfram Engine free is single-seat per-user, but `wolframscript` invocations spawn separate kernel processes; SARAH `Start[...]` is in-process so a single `math` invocation is one kernel. Two simultaneous `math` invocations would consume two kernels — license depends on whether the user has Wolfram Engine (per-machine activation, multi-process OK) or paid Mathematica home-use (per-seat). **The serialization recommendation is plausible but not proven.** Synthesizer should treat it as caution, not gospel.

---

## 4. Quantitative challenges

### `Ωh² = 10.15 ± 10%` — **BAND IS UNJUSTIFIED**

The 10% comes from "MadDM's Romberg can drift in the third decimal" (proposer §4 narrative). But:
- Romberg drift in the *third* decimal of 10.15 is `±0.005`, i.e. 0.05%, not 10%.
- A ±10% band (9.1–11.2) would be permissive enough to mask real regressions like a wrong tan β, missing channel, or off-by-2× coupling.
- The 10.15 is a benchmark off-relic point (Planck Ωh²≈0.12; this is ~85× overabundant on purpose, see SKILL.md L392-394). It's not a fit; it's a determinism check.
- **Recommendation: tighten to ±2% (9.95–10.36).** If MadDM is truly nondeterministic at the percent level, that's its own bug worth surfacing.

### `PHASES[1]=1.0` sentinel — **WEAK SENTINEL**

`PHASES[1]=1.0` is the *patcher's default value*. The check "did the patcher run?" is satisfied iff the line `1  1.000000e+00  # rpchiR — real part...` appears. **But** if the patcher ran twice, or if a future patcher version flips the convention, this passes spuriously. **Stronger sentinel: timestamp-stat `Cards/param_card.dat` after `output` and after the patch step; require mtime delta. Or write a `.patched` marker file.** The grep alone is necessary but not sufficient.

### `chichibar_bbx ≥ 40%` — **THRESHOLD UNDOCUMENTED**

SKILL.md L363 claims "Dominant channel: `chichibar_bbx` at ~60% (Type-II 2HDM: b-quark coupling enhanced at tan β=10)." Proposer floors it at 40%. No data backs the 40% number — there is no iter-8 channel breakdown in the fix_loop dir (`iter_7_maddm_results.txt` exists but iter-8 results were not committed). **Recommendation: drop to ≥30% as a soft check, log the actual fraction, and let the synthesizer flag drift in a follow-up. If it's <30%, that's a real regression worth surfacing as a finding rather than a blocker.**

---

## 5. Practitioner realism — Q2 ambiguity

The proposer says "augment Q2 with a parenthetical, do not modify the script." But examine `practitioner_script.md` Q2 (lines 27-41):

```
Scalars:
1. H1 — SU(2)_L doublet, Y = +½
2. H2 — SU(2)_L doublet, Y = +½
3. a — real gauge singlet, CP-odd
Fermions (Dirac DM):
1. chiL — SM-singlet left Weyl, Y = 0
2. chiR — SM-singlet right Weyl, Y = 0
```

A cold reader actually answers Q2 *correctly* here — the script lists `chiL`/`chiR` as separate Weyls. The land-mine is that `/lagrangian-builder` will then either (a) auto-pair them into a Dirac fermion (good — SARAH renderer expects that), or (b) emit two independent Majorana-like entries (bad). **The proposer's worry about "a vs A collision" is a Q3 concern, not Q2.** Q2's actual risk is that `/lagrangian-builder` doesn't know about the PortalDM idiom (two LH Weyls, one wrapped in conj[]), so even with a perfect Q2 the YAML will not produce the hand-crafted `.m` files. **This is fine** because Step 4a bypasses `/lagrangian-builder` for 2hdm-a — but means the practitioner script for Q2 is **decorative**, not load-bearing, in this run.

---

## 6. Failure modes the proposer missed

1. **Stale `demo_output/2hdm-a/summary.json` from 22 Apr.** Already on disk, says "BLOCKED at /sarah-build, ran: []". A status-comparing playtest will be confused. **Mitigation: clean before run.**
2. **Stale `Cards/param_card.dat` from a prior aborted run.** The `output` step in MG5 typically overwrites but doesn't always — verify with mtime. The patcher will read whatever's there. (POST_MORTEM L58 explicitly warns: "MadDM's `output` overwrites Cards/param_card.dat. Order: (1) output (2) patch card (3) launch.")
3. **`from scripts.maddm_run import` import failure.** SKILL.md L279 imports a module that lives in a *different skill*. Without `PYTHONPATH` munging, this raises `ImportError`. **Add to preflight: `python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"`** — or accept that the agent will discover and route around it.
4. **MadDM "no DM candidate" auto-detect.** UFO declares `chi` PDG 9989932, antiname `chibar`, self_conj=False. MadDM's auto-pick prioritizes the *lightest* `Z2`-odd particle. With `Mchi=100` the lightest BSM is `chi` — should be fine. **But** the patcher writes `Wchi = 1 GeV` (decay width 1 GeV for a stable DM particle is wrong; DM should have width ~0). MadDM may interpret a 1 GeV width as "this is unstable" and reject `chi`. **The patcher's "set all BSM widths ≥1 GeV including chi" is suspicious — verify MadDM's tolerance.**
5. **`_shared/summary.schema.json` rejects the SKILL.md-prescribed extra fields** (`relic_approx`, `model_source`, `model_fixture`) due to `additionalProperties: false`. Strict jsonschema validation will fail. Either relax the schema or drop the extra fields from the example.

---

## 7. Concrete issue-log schema (proposer was vague)

The proposer's §6 schema is fine in shape but missing: (a) git SHA, (b) tool versions, (c) parent issue linkage for fix-loop, (d) artifact byte-hashes for tamper detection. Concrete revised JSON:

```json
{
  "issue_id":              "2hdma-001",
  "parent_issue_id":       null,
  "severity":              "blocker",
  "phase":                 "param_patch",
  "symptom":               "Omegah2 = -1.0 sentinel after launch",
  "expected":              "finite Omegah2 in MadDM_results.txt",
  "observed":              "Omegah2 = -1.0; sigmav_xf = 0; all channel fractions NaN",
  "evidence_paths":        ["abs/path/to/MadDM_results.txt", "abs/path/to/param_card.dat"],
  "evidence_hashes":       {"abs/path/to/param_card.dat": "sha256:..."},
  "hypothesis":            "PHASES[1] not set; patcher was skipped or failed silently",
  "blocking":              true,
  "auto_repro_command":    "grep '^   1' demo_output/2hdm-a/maddm_run/Cards/param_card.dat | head",
  "fix_owner_hint":        "skill_prose",
  "fix_attempts":          [],
  "captured_at":           "2026-04-24T20:35:00Z",
  "playtest_iteration":    0,
  "git_sha":               "a05f274",
  "tool_versions":         {"sarah": "4.15.3", "mg5": "...", "maddm": "...", "python": "3.x"},
  "config_snapshot_path":  "demo_output/2hdm-a/playtest_log/env.json"
}
```

Stored as JSONL at `demo_output/2hdm-a/playtest_log/issues.jsonl`. Append-only. Fix agent appends to `fix_attempts` array with `{ts, diff_path, outcome}` triples without rewriting prior entries.

---

## 8. What survives, what must change

**Survives:**
- Hand-crafted fixture path is correct (verified: 4 `.m` files match deployed dir).
- Two-phase `output` → patch → `launch` order (verified against POST_MORTEM L58).
- Failure taxonomy ranking (priors look right against POST_MORTEM history).
- Issue-log JSONL approach (with revisions in §7 above).

**Must change:**
1. Drop `--skip-render` references; drive Wolfram directly.
2. Hard-clean `demo_output/2hdm-a/` before run (stale summary.json from 22 Apr).
3. Tighten Ωh² band from ±10% to ±2%.
4. Replace `PHASES[1]=1.0` grep with mtime+grep dual sentinel.
5. Acknowledge: `iter_6_notes.md` does not exist; renderer-backport scope was vapor.
6. Acknowledge: `patch_paramcard.py` is a 445-line *reconstruction*, not the iter-8 60-line original — its extra HMIX/ZAMIX/ZHMIX/ZPMIX writes are unaudited.
7. Resolve schema/SKILL.md mismatch (`additionalProperties: false` vs extra fields).
8. Verify `Wchi = 1 GeV` in patcher doesn't break MadDM's DM auto-detect.
9. Allow narrow fix-loop in `plugins/hep-ph-demo/skills/2hdm-a/` only; not "strictly observe."

The core thesis (validate fixture path, defer renderer) survives. The execution details need the eight changes above before the synthesizer can hand it to a playtest agent.
