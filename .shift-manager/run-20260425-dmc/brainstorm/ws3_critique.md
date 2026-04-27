# WS-3 Critique — Dark SU(3) End-to-End Playtest

**Critic:** WS-3 brainstorm critic
**Verdict:** **ACCEPT-WITH-MAJOR-REVISIONS.** The hybrid scope is defensible but the proposer hides three load-bearing assumptions that don't survive verification: (a) the existence of a usable Dark SU(3) UFO inside `plugins/hep-ph-demo/skills/dark-su3/benchmarks/` — there is **no UFO there, just a README explicitly forbidding numeric benchmarks**; (b) the existence of a "test-agent harness with temperature pinning" — `eval/harness/` exists, but it shells out to `claude --model sonnet` and the underlying CC binary exposes **no temperature flag**; (c) the survival of the `--spec spec.yaml` invocation flag through the WS-4 rewrite — the synthesis says nothing about it and the plan's preserve-verbatim ranges (lines 20–35) keep it, but no T7 gate asserts it. The N=3 majority-rule is then papering over a flake source the proposer doesn't acknowledge. The single-spectrum choice is defensible on resonance physics but under-tests the routing tree. Six revisions below; if accepted, WS-3 ships with much higher confidence.

---

## 1. Per-decision rebuttal

### Decision 1 — Hybrid scope (helpers real, physics tools mocked)

**Proposer's pick:** hybrid. **My pushback:** the proposer waves at "WS-1 §6.4 explicitly defers" without engaging with what that deferral *costs*. Canned MadDM stdout encodes the proposer's *belief* about MadDM output — the same belief WS-1's own AUDIT.md flagged as `verified_against_synthetic`, not `verified_against_real`. WS-3 was nominated, in part, as the workstream that promotes those rows. **Hybrid-with-canned-fixtures is structurally incapable of doing that promotion.** The proposer's §1 asserts WS-3 "catches what WS-1 deferred: real-format MadDM output drift" but §5 case 3 only catches schema-version drift between SKILL.md and the helpers — **not real-MadDM-vs-fixture drift**. The two are not the same.

The dry-run-only alternative the proposer dismisses ("loses contract-guard verification") deserves more credit. Helpers are pure functions of their inputs; their contract is verified to bedrock by WS-2. WS-3's distinct value is the *routing* not the *helpers*. A pure dry-run (LLM walks the tree, helpers stubbed at the subprocess boundary, behavioral assertions on argv lists captured from the stub) achieves 90% of the routing assertion at 10% of the fixture-authoring cost.

The real-run-where-installed alternative is the **right answer for at least one tool**: `/drake-install detect` is already in the proposer's "real" list because it's cheap. The same logic applies to `/maddm` for the no-DRAKE branch fixture: a Dark SU(3) MadDM relic-only run is ~5–15 min on a laptop, well within CI budget. The proposer's "30-min-to-multi-hour" estimate is for the full DRAKE solver path, not the MadDM path.

**Counter-proposal:** Tier the playtest. **Tier-1 (CI, every run):** dry-run, helpers stubbed at subprocess boundary, behavioral assertions only — fast, no fixture-vs-reality risk. **Tier-2 (`pytest -m integration`, on-demand):** hybrid with canned fixtures — exercises helpers for real but stubs physics tools, current proposal. **Tier-3 (`pytest -m smoke`, manual):** real `/maddm` + `/micromegas`, real `/drake-install detect`, real DRAKE if installed; this is what promotes `verified_against_synthetic` → `verified_against_real`. The proposer's plan collapses Tier-1 and Tier-2 into one and omits Tier-3 entirely — that's the gap.

### Decision 2 — Spectrum choice (m_χ=100, m_med=199)

The arithmetic is correct: 2m_χ = 200, |Δ| = |2·100 − 199| = 1, ratio = 1/200 = 0.005. **Inside the 5% window. ✓**

But "inside the 5% window" is the *router's heuristic* for narrow-resonance, not a statement about whether the resonance actually IS narrow. A narrow resonance has Γ/m_med ≪ 1 (typically ≪ 0.05). The proposer specifies no width. For the Dark SU(3) vector mediator at m_med = 199 GeV decaying to 100 GeV χχ, Γ depends on the gauge coupling — at α_dark ~ 0.1, Γ ~ α·m_med/12 ~ 1.6 GeV, so Γ/m_med ~ 0.008, which IS narrow. At α_dark ~ 0.5, Γ/m_med ~ 0.04, marginally narrow. **The spectrum point fires the router but doesn't pin whether DRAKE materially differs from micrOMEGAs** — which is the only reason to invoke DRAKE.

This matters for §5 failure mode 5 (silent-winner regression): if DRAKE and micrOMEGAs produce essentially identical Ωh² for this point, the "no silent winner" assertion is testing a tautology. A real test of the router needs a parameter point where the three tools *disagree* in a physically meaningful way.

The proposer also doesn't give a coannihilator width or coupling — m = 105 GeV is "within 10%" but Step 3's coannihilation trigger (Trigger A) cares about whether the partner has the same conserved charge as the DM (so it can co-deplete). A floating "m = 105 GeV partner" without a model role might trigger the heuristic but not match a real Dark SU(3) topology. Verify the Dark SU(3) UFO actually has a partner at this mass.

**Counter-proposal — TWO points:**
- **Point A (DRAKE-narrow):** m_χ = 100, m_med = 199, declared Γ/m_med = 0.005 (specify in fixture README). Fires Step 5 narrow-res. ✓
- **Point B (off-resonance control):** m_χ = 100, m_med = 230 (Δ/(2m_χ) = 0.15, NO Step 5; Step 4 still fires from Trigger A coann if you keep m = 105, otherwise NO Step 4 either). Verifies the LLM does NOT invoke DRAKE when triggers are absent.

The four DRAKE-branch fixtures the proposer already has cover the *availability* of DRAKE (configured/missing/activation_required/unset). They do NOT cover the *trigger* logic. Point B is what does. Without it, "Step 5 fires when triggers say so" is asserted but "Step 5 does NOT fire when triggers say not-to" is unasserted — a half-test.

### Decision 3 — Behavioral assertions over golden table

I largely agree with the direction (string-equality on LLM prose is a flake factory) but the proposer's framing has gaps:

**Gap A — golden artifacts as "debug aid only" understates them.** `golden/expected_step_trace.json` is referenced by the behavioral assertions (the proposer says so explicitly in §3). That makes it a gate, not a debug aid. Naming matters: call them `expected_*.json` and treat them as part of the gate spec, with a versioning convention (`expected_step_trace_v1.json`).

**Gap B — what catches numeric-caveat regressions in the merged table?** The proposer's behavioral-assertion list checks structure (4 observable rows, DRAKE column populated for Ωh²) but NOT *content* of caveats. If the merged-output Caveats section says "Ωh² disagreement: 14% rel-diff" but a future SKILL.md edit changes it to "Ωh² disagreement: ~10%" (rounding) or drops the section entirely, the proposer's gate misses it. **Add an assertion:** the merged-output's Caveats section MUST contain the canonical phrases `CROSSCHECK_DISAGREEMENT` (when triggered) and the rel-diff value to ≥1 sig-fig precision.

**Gap C — negative-control fixture is hand-waved.** Proposer §4 says "deliberately-broken SKILL.md fixture (e.g. swap §2.1 prose)" but doesn't specify (a) where the broken SKILL.md lives, (b) how the harness loads it instead of the live file, (c) what the failure signature should look like. Without a concrete spec, "negative control exists" is unverifiable. **Specify:** the negative-control fixture is a complete `SKILL.md.broken` file in `tests/fixtures/dark_su3_playtest/negative_control/` with one specific edit (e.g. Step 4b's `--schema-version` arg removed); the harness sets a `SKILL_OVERRIDE_PATH` env var; the playtest is parameterized to run twice (live + broken) and ASSERTS the broken variant fails with a specific assertion code.

### Decision 4 — N=3 majority-rule

This is the weakest decision. The proposer admits the harness's "deterministic mode" is "best-effort" but doesn't engage with what that means: **Claude Code's underlying model is reached via the `claude` CLI which exposes no temperature flag.** Verified: `eval/harness/runners/claude_code.py` line 475 does `--model <name>` only. **The harness CANNOT pin temperature.** Sampling nondeterminism is real and unavoidable.

Given that, N=3 majority-rule is a coping mechanism, not a fix. Two issues:

1. **Statistical math:** if true per-run pass rate is p, then 2-of-3 majority pass rate is `p³ + 3p²(1-p) = 3p² - 2p³`. For p=0.95, majority = 0.993 (good). For p=0.85, majority = 0.939 (still flaky). The proposer's §7 risk-3 "5% per-run flake → 14% per-scenario flake" treats N=3 as fixing the issue but ALSO admits "tune N upward" is needed. That contradiction means N is undertermined.

2. **Retry-on-flake is the better protocol.** A flake is "1 of 3 fails with a soft assertion (prose mismatch, paraphrase miss)." A real bug is "3 of 3 fail with a hard assertion (helper not called, wrong arg)." Distinguish them: **(a) hard assertions are gated 1-of-1 (must pass first try);** **(b) soft assertions are gated retry-up-to-N times** with explicit retry-budget logging. This is statistically cleaner than majority vote AND surfaces flake rate as a metric.

**Counter-proposal:** Drop N=3 majority. Adopt: hard assertions = single-shot pass-required; soft assertions = retry budget of 2 (i.e. 3 attempts total) with the run logging "passed on attempt K." If K>1 frequently, that's a signal to harden the assertion or the SKILL.md prose, NOT to raise N.

### Decision 5 — Reuse from `plugins/hep-ph-demo/skills/dark-su3/`

**This is the biggest factual error in the proposal.** Proposer §6 says: "`benchmarks/` already contains a runnable Dark SU(3) UFO benchmark" — this is **false**. Verified by `ls`:

```
plugins/hep-ph-demo/skills/dark-su3/benchmarks/
└── README.md
```

The README explicitly says: *"No paper-cited numeric benchmark has been committed for dark-su3 yet... Until a fixture is committed, plan gates MUST NOT inline numeric thresholds for dark-su3."*

There is NO UFO to symlink. The proposer's §2 fixture layout `ufo/darkSU3/` symlinking the demo's UFO **cannot be constructed**. Three options:

- **Option A — Author a synthetic UFO for WS-3.** Hand-roll a minimal Dark SU(3) UFO with the three masses fixed (m_χ=100, m_med=199, m_partner=105). This is real scope (~150 lines of UFO Python).
- **Option B — Drop the UFO from the fixture entirely.** WS-3 doesn't actually run MadGraph or MadDM; `ufo/darkSU3/` is referenced by the SLHA file but never read. Replace `ufo_path` in `config.yaml` with a sentinel (`/tmp/fake_ufo_dir/`) and let `check_prereqs` see the directory exists (synthetic empty dir). The UFO contents are never inspected.
- **Option C — Use the singlet-doublet UFO** that DOES exist (verified at `.claude/worktrees/from-main/demo_output/singlet-doublet/`) and rebrand the playtest as "single-doublet narrow-resonance" — but this contradicts the manager's lock on Dark SU(3) and breaks the Profumo Fig. 8 framing.

**Recommend Option B.** WS-3 is a router playtest, not a physics validation; the UFO is irrelevant to the routing logic. Empty-dir sentinel matches the §2 framing ("fixture mirrors WS-1's tests/fixtures/router_contract/") because that WS-1 fixture is itself synthetic. **Synthesizer must lock this.**

Also flagged: the `benchmarks/README.md` says "plan gates MUST NOT inline numeric thresholds for dark-su3 (e.g. no `omega_h2 > X` literals)." The proposer's §3 *does* inline literals (Ωh²=0.135 for MadDM, 0.118 for micrOMEGAs, rel-diff 14.4%). These are FIXTURE values, not gate thresholds — the README's prohibition is on physics gates ("the answer must be X"), not on canned-fixture content driving rel-diff arithmetic. Distinct, but the synthesizer should explicitly note this distinction in the WS-3 plan to prevent misreading.

### Decision 6 — Failure modes (6 listed)

Proposer's six are reasonable. Misses I see:

**Missing FM-A (proposer hint #1, my expansion):** Helper invocation paths drift after WS-4. The proposer's §3 helper-invocation arg assertion uses literal paths like `scripts/extract_field.py`. WS-4's plan T7 gate #4 only checks for the *presence* of these strings in SKILL.md — it doesn't ensure they survive future edits. If a post-WS-4 PR moves `scripts/` to `helpers/`, the live SKILL.md still has the old path (broken), and WS-3 catches it via "agent invokes wrong path → subprocess fails → `check_prereqs` never returns → behavioral assertion (a) fails." Useful! **But:** the proposer doesn't list this; should be explicit. It's the *boundary check* WS-3 uniquely owns.

**Missing FM-B (proposer hint #2):** SKILL.md preamble changes affecting "default observable = all." The router's Step 4 cross-check table has 4 observables; if the rewritten YAML frontmatter or invocation section says "default to relic-only when --observable is unset," the playtest fixture (which doesn't pass --observable) might silently get a 1-row merged output and pass the structural assertion if it's lax. **Tighten the assertion:** "merged-output table has exactly 4 rows" (`==`, not `>=`).

**Missing FM-C (proposer hint #3):** Caveats section omitted entirely from merged-output. See Decision-3 Gap B above. The proposer's structural check on the table doesn't reach the post-table prose. Add a separate assertion that the Caveats section exists and contains either "(none)" or named blocker codes.

**Missing FM-D — `--spec spec.yaml` flag drops out of SKILL.md.** The current SKILL.md line 30 documents `--spec <yaml>` as the way to pass `dm_candidate`. Synthesis §3.1 says lines 20–35 (Invocation) are "Unchanged" but no T7 gate asserts that. If the rewrite collapses Invocation into prose and drops `--spec`, the playtest fixture (which uses `--spec spec.yaml`) silently breaks. **WS-3 catches this** if the fixture invocation is what's used to drive the agent.

**Missing FM-E — schema files don't exist at runtime.** WS-4 T1 ships `relic.schema.json` / `annihilation.schema.json` to `plugins/shared/schemas/`. If a packaging step (.claude-plugin manifest) doesn't include these, the helper's `--schema-root` default points at a missing dir, `extract_field` exits 2 (`EXTRACT_FIELD_INTERNAL`), and the LLM may misinterpret as a contract failure. **WS-3's helper-invocation-result assertion catches this** if it asserts not just "helper was called" but "helper exit code == 0."

So actually 9–10 failure modes when I count them. The proposer's list of 6 is a starting point; synthesizer should expand.

---

## 2. Adjudication of the 3 unknowns

### Unknown 1 — Test-agent harness with temperature pinning

**Verdict:** **harness exists; temperature pinning DOES NOT.**

- `eval/harness/` exists (verified by `ls`): contains `run.py`, `loader.py`, `graders.py`, `outcome.py`, `report.py`, plus `runners/{base.py, claude_code.py, reference.py}`. This is a real evaluation harness, not vapor.
- `claude_code.py` (485 lines) shells out via `subprocess` with `--model <name>` (line 475). **No `--temperature` flag exists in the `claude` CLI**, so the harness has no surface to pin it. The "deterministic mode is best-effort" the proposer hand-waves about IS this gap.
- Existing harness tests live in `eval/harness/` but don't appear to drive Skill prose evaluations specifically; closest analogue is `runners/reference.py` for golden-output tests.

**Implication:** WS-3 has hidden harness scope **only if it needs prose evaluation infrastructure that doesn't exist.** The existing `eval/harness/` can drive a Claude subprocess; WS-3 needs a thin wrapper that captures stdout/stderr of helper subprocesses called BY the agent, parses them into a structured event log, and runs assertions. That wrapper is ~200–400 LoC and is genuinely new — not in the WS-3 proposal as scoped work. **Synthesizer must add a "harness extension" task** OR explicitly defer it (and downgrade WS-3 from "ships in this run" to "scaffolds in this run, gates fire next run").

### Unknown 2 — MadDM stdout fixture format stability

**Verdict:** **reuse WS-1's existing synthetic fixtures; do NOT author new ones.**

- Verified file exists: `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` (WS-1 synthetic).
- That fixture is the format WS-1 already calibrated against the WS-4 manifest's `audit_status: verified_against_synthetic` rows.
- Authoring a new Dark-SU(3)-specific MadDM fixture multiplies the "fixture-vs-reality" surface by 2× without buying anything: WS-3 is testing the routing, not the model-specific MadDM output. Use the WS-1 fixture **with the relic value monkey-patched** (a sed of `omega_h2 = 0.135` is fine) to ensure cross-check disagreement fires.
- Bonus: this naturally promotes WS-1's fixture from "router contract test only" to "router-contract-test + WS-3 playtest input," giving the fixture more usage signal and surfacing format drift faster.

### Unknown 3 — `--spec spec.yaml` flag preserved post-rewrite

**Verdict:** **PROBABLY preserved (WS-4 synthesis §3.1 Invocation is "Unchanged"); but UNVERIFIED — no T7 gate asserts it.**

- Live SKILL.md line 30 has the flag. Confirmed via grep.
- WS-4 synthesis §3.1 lists Invocation (lines 20–35) as "Unchanged" — preserved.
- But §3.2 preserve-verbatim list does NOT include lines 20–35; only 60–66, 79–100, 219–254, 258–291, 295–309, 328–339, 343–356.
- T7 gate #2 reads ranges from HEAD~1 but **only those 7 ranges**. Lines 20–35 are NOT in the gate.
- T7 gate #4 asserts direct-path helper invocations exist; says nothing about top-level `--spec`.

**Implication:** the flag is at meaningful drift risk. If the rewriter collapses Invocation into a different format ("just say `/dark-matter-constraints` and let the agent pick up `dm_candidate` from context"), the flag silently disappears. **Synthesizer must request a T7 gate addition** — `grep -F -- '--spec' "$S"` — OR WS-3 must include a precondition check that reads the live SKILL.md and aborts if `--spec` is missing.

---

## 3. New issues (not in proposer's list)

1. **No spec for "what the LLM agent system prompt looks like."** WS-3 invokes Sonnet via the harness reading the rewritten SKILL.md. Does the agent get any other context? If it gets the user's CLAUDE.md, project memory, etc., the playtest is testing those too — large surface area for false negatives. Synthesizer must specify the *minimal* prompt envelope.

2. **`/drake-install detect` real invocation has side effects on developer machines.** Proposer §1 lists it as "real" and §7 risk-3 acknowledges "wolframscript can emit licensing prompts." For CI on a host without Wolfram, the real call returns "missing" — acceptable. For the developer's laptop with Wolfram installed, it could differ between runs. **The proposer's "stub HEPPH_DRAKE_DETECT_CMD for the four-branch fixtures, only run the real detect script in a single end-to-end smoke variant" is right but should be the ONLY mode for Tier-1 CI** — never the default.

3. **W4-D landing in T7 affects WS-3's expected assertion.** WS-4 plan §9 item 9 promotes W4-D into T7: SKILL.md must say `omega_h2` (lowercase) for DRAKE's relic field. WS-3's helper-arg assertion needs `--key omega_h2`, not `--key OmegaH2` or other variants. Pin the casing in the WS-3 assertion spec; don't rely on the LLM normalizing.

4. **Coupling between WS-3's transcript parser and the harness's transcript format.** Proposer §3 talks about "structured trace" but doesn't specify the parser. Is it grep-line? Is it a JSONL log? `eval/harness/runners/claude_code.py` line 442+ formats transcripts in a specific shape; WS-3's parser must match. Synthesizer should pin this — or accept that the transcript parser is its own ~100 LoC of code WS-3 must author.

5. **No criterion for declaring WS-3 itself "passing."** The proposer's "behavioral assertions are gates, prose is informational" is fine but doesn't define HOW MANY assertions must pass. All? 90%? Synthesizer needs a single sentence: "WS-3 passes iff every hard assertion across all 1+4 = 5 spectrum/branch fixtures passes; soft assertions logged but non-gating."

---

## 4. Synthesizer must resolve

1. **Tier the playtest:** Tier-1 (dry-run, CI, every PR), Tier-2 (hybrid w/ canned fixtures, on-demand), Tier-3 (real `/maddm`+`/micromegas`, manual, the path that promotes WS-1 audit rows to `verified_against_real`). Drop the proposer's collapse of all into one tier.
2. **Spectrum: add Point B (off-resonance control, e.g. m_med=230) to verify Step 5 does NOT fire when triggers absent.** Pin Γ/m_med in the fixture README for both points.
3. **UFO reuse: USE EMPTY-DIR SENTINEL** (Option B above). The dark-su3 demo benchmarks dir contains only a README — no UFO to symlink. Synthesizer must fix the proposer's factual error.
4. **Replace N=3 majority with hard/soft assertion split + retry budget on soft.** Hard = 1-of-1; soft = retry-up-to-3.
5. **Negative-control: spec the file path, the env override, the parameterization.** Don't leave it at "exists."
6. **Add T7 gates (delivered back to WS-4): `grep -F -- '--spec' SKILL.md` AND assertion that Invocation lines 20–35 survive verbatim.** Expand T7 preserve-verbatim to 8 ranges.
7. **Harness extension task: ~200–400 LoC for transcript-event-log parser + helper-subprocess capture.** Either in WS-3 scope or explicitly deferred (and WS-3 gates downgraded to scaffolding).
8. **Missing failure modes A–E (helper-path drift, "default observable" preamble, Caveats section, `--spec` drop, schema files not packaged) added to the gate spec.**
9. **Reuse WS-1's `MadDM_results_synthetic.txt`** with sed-patched relic value; do NOT author a Dark-SU(3)-specific MadDM fixture.
10. **Tier-1 `/drake-install detect` runs ONLY against `HEPPH_DRAKE_DETECT_CMD` stub; real-detect is Tier-3 only.**
11. **Define WS-3's pass criterion explicitly** ("all hard assertions across 5 fixtures must pass; soft are non-gating").
