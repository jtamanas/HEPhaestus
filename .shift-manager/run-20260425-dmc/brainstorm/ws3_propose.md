# WS-3 Proposal — Dark SU(3) End-to-End Playtest

**Proposer:** WS-3 brainstorm proposer
**Spectrum (LOCKED by manager):** m_χ = 100 GeV, m_med = 199 GeV → |Δ|/(2m_χ) = |199 − 200|/200 = 0.005 < 0.05 → **DRAKE branch fires**.
**Inputs consumed:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md`; `memory/project_profumo_paper_scope.md` (5-day-old; treated as orientation only); current `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (pre-rewrite, 356 lines); listing of `plugins/hep-ph-demo/skills/dark-su3/` (`benchmarks/`, `practitioner_script.md`, `SKILL.md`, `summary.schema.json`).

WS-3 is the integration test for the rewritten SKILL.md prose itself. WS-4 ships four helpers + a refactored decision tree; WS-2 unit-tests each helper in isolation; WS-3 verifies that an LLM following the rewritten SKILL.md, given the Dark SU(3) spectrum, actually walks Steps 1→5 in order, calls each helper at the right step, and produces the merged-output table the rubric expects. WS-3 is the end-to-end check that the helpers compose, the prose disambiguates, and the four-branch DRAKE detection actually surfaces correctly to the LLM.

---

## 1. Playtest scope — **Hybrid**

Pick: **hybrid playtest**, with the seam pinned at the tool-driver boundary.

What runs for real:
- The SKILL.md decision tree, walked by an LLM agent (Claude Sonnet, separate context), reading the post-WS-4 SKILL.md verbatim.
- The four WS-4 helpers (`check_prereqs`, `detect_drake`, `extract_field`, `verify_router_field_contract`) — invoked exactly as the LLM is instructed to invoke them, via the SKILL.md `python …/scripts/<name>.py` strings. These are the contract-guard layer; they are model-agnostic by WS-4 construction; WS-3 exercises them under realistic config + manifest paths.
- `/drake-install detect` — invoked for real (it's a 100ms bash script reading filesystem state and calling `wolframscript`). Cheap and the four-branch logic is the load-bearing thing WS-3 must verify.

What is stubbed:
- `/maddm`, `/micromegas`, `/drake` themselves are NOT executed. Stubbed at the subagent boundary by canned fixture outputs (MadDM stdout text, micrOMEGAs `relic.json` + `annihilation.json` + `summary.json`, DRAKE Wolfram-stdout). Running the real tools is a 30-min-to-multi-hour computation per branch and is what WS-1 §6.4 explicitly defers.
- The LLM agent is invoked via the harness's existing test-agent shim (no real Claude API calls in CI; transcripts captured by replay or by a recorded session pinned to the helper-version hash).

Lens conformance: helpers are "deterministic + model-agnostic" per the lens, so they are SAFE to run for real. Tool drivers are not the lens-target of WS-3 (they're the lens-target of WS-1's manifest); stubbing them keeps WS-3 cheap and reproducible while leaving the routing logic — the actual subject under test — fully exercised.

The dry-run alternative (LLM walks the SKILL.md but no helpers run) loses the contract-guard verification that is the whole point of post-WS-4 architecture. The real-run alternative (full MadDM + micrOMEGAs + DRAKE) is at least 2 hours per playtest, can't run in CI, and surfaces tool bugs that aren't WS-3's mandate. Hybrid is the right scope.

---

## 2. Spectrum + fixture location

Spectrum: m_χ = 100 GeV, m_med = 199 GeV (LOCKED). This is inside the 5% DRAKE window (Δ/2m_χ = 0.005) and inside the 10% micrOMEGAs window — both Step 4 and Step 5 fire. There is also a coannihilator at m = 105 GeV (within 10% of m_χ) added to fire Trigger A; this matches the Dark SU(3) Fig. 8 region of arXiv:2506.19062 (Profumo paper, vector resonance branch).

Fixture location: `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/dark_su3_playtest/`. Subdirs:

```
tests/fixtures/dark_su3_playtest/
  config.yaml                          # spec.models.darksu3 with ufo_path, latest_slha
  spec.yaml                            # dm_candidate, channels, etc. (passed via --spec)
  ufo/darkSU3/                         # symlink to plugins/hep-ph-demo/skills/dark-su3/benchmarks/<existing UFO>
  slha/darksu3_spectrum.slha           # mass spectrum: m_chi=100, m_med=199, m_coann=105
  maddm_run/MadDM_results.txt          # canned MadDM output (see §5)
  micromegas_run/relic.json            # canned post-W4-A schema
  micromegas_run/annihilation.json     # canned post-W4-B schema
  micromegas_run/summary.json          # scattering/v1 (already exists in WS-1)
  drake_run/drake_stdout.txt           # canned DRAKE Wolfram output
  golden/                              # see §3
    expected_merged_table.md
    expected_blockers.json
    expected_step_trace.json
```

Reuse path for the UFO: the `plugins/hep-ph-demo/skills/dark-su3/benchmarks/` dir already contains a runnable Dark SU(3) benchmark (per directory listing). Symlink rather than copy. The SLHA file is small and synthetic (hand-authored to put the masses exactly where Step 3/Step 5 triggers fire); we don't run SPheno in WS-3. A README in the fixture dir cites m_χ, m_med, Δ/(2m_χ), and which steps the spectrum is calibrated to fire.

The fixture mirrors `tests/fixtures/router_contract/` from WS-1 — adjacent to it, same `tests/fixtures/` parent. WS-2 unit-test fixtures live alongside; WS-3 is a sibling subdir, not nested.

---

## 3. Verification structure — **Behavioral + golden-table hybrid**

Pick: **behavioral assertions as the load-bearing layer; golden table as a tiebreaker artifact**, NOT trace-replay.

The assertion layer (behavioral, what WS-3 actually gates on):

- **Step ordering.** The agent's transcript must show, in order, evidence of: (a) `check_prereqs` invocation; (b) reading MadDM output; (c) Step 3 spectrum analysis prose mentioning the 0.5% Δ/(2m_χ) figure or equivalent; (d) `extract_field` invocation against `relic.json` and `annihilation.json`; (e) rel-diff arithmetic in prose; (f) `detect_drake` invocation; (g) DRAKE branch decision based on `router_action` field. Each evidence rule is a single regex or function-call assertion against the transcript.
- **Helper invocation arguments.** `check_prereqs` must be called with `--config` pointing at the fixture config and `--model darksu3`. `extract_field` must be called separately for `omega_h2` against `relic.json` with `--schema-version relic/v1` and for `sigma_v_zero` against `annihilation.json` with `--schema-version annihilation/v1`. Argument-shape assertions, not literal command-string assertions (whitespace/quoting tolerance).
- **Branch correctness.** Given `config.drake_path` IS set in fixture and the canned `drake-install detect` output is `"configured"`, the agent must hit Branch 2 + invoke `/drake`. WS-3 includes three sibling fixtures that flip ONLY `drake_path` / detect output to test all four branches (`configured` → invoke; `missing` → DRAKE_MISSING; `activation_required` → DRAKE_ACTIVATION_REQUIRED; unset → Branch 1 DRAKE_MISSING).
- **Merged-output schema.** The agent's final merged-output Markdown must contain ALL four observable rows (Ωh², σ_SI, σ_SD, ⟨σv⟩), with the DRAKE column present and populated for Ωh², `—` for the rest. Asserted by parsing the Markdown table, NOT by string-equality.
- **Flag correctness.** Given the canned MadDM (Ωh²=0.135) vs micrOMEGAs (Ωh²=0.118) values, the agent must emit `CROSSCHECK_DISAGREEMENT` (rel-diff = 14.4% > 10%). Asserted by presence of the named code in the transcript.
- **No silent winner.** The transcript must NOT contain phrases that average or pick — assertion is a negative regex over a small allow-list ("rel-diff", "FLAG", "ADJUDICATION REQUIRED" allowed; "average of", "we'll go with", "ignore the disagreement" forbidden).

The golden-table layer (artifact, NOT a gate):

- `golden/expected_merged_table.md` — pretty-printed expected table with values pinned. Used as a HUMAN-READABLE diff target when an assertion fails. NOT diffed verbatim against actual output (LLM nondeterminism makes string-equality flaky).
- `golden/expected_blockers.json` — list of expected blocker codes that should fire across the four DRAKE-branch fixtures. Behavioral assertions reference this file as a lookup.
- `golden/expected_step_trace.json` — sequence of expected helper invocations + their argument shapes. Behavioral assertions reference this file as a lookup.

Rationale: trace-replay (record one good run, diff future runs against it) is brittle under LLM nondeterminism — paraphrase changes break the diff. Golden-table-as-gate is brittle for the same reason. Behavioral assertions over a structured trace are robust because they assert on what the agent DOES (which helpers, with which args, in which order) rather than what it SAYS. The golden artifacts exist to make failures human-debuggable.

---

## 4. LLM nondeterminism strategy

The single biggest WS-3 risk is "passes flakily, fails opaquely." Three mitigations:

- **Behavioral assertions over structured trace, not literal string equality.** See §3. The transcript is parsed into a structured event log (helper invocations, file reads, decision-tree branches taken) before assertion. Phrasing changes are invisible to the assertion layer.
- **Temperature pinning + N=3 majority-rule.** Test agent runs with temperature=0 (or harness's nearest equivalent). Each playtest scenario runs N=3 times; assertions pass if ≥2 of 3 pass. Catches genuine bugs (assertion fails 3/3) without thrashing on rare phrasing edge cases (1/3 paraphrase miss). Three runs at temperature=0 still vary because of nondeterminism in the helper invocation surface (subprocess timing, etc.) and because the harness's "deterministic mode" is best-effort.
- **Blockers and helper-invocation args are GATES; merged-table prose is INFORMATIONAL.** A failure in "did `check_prereqs` get called with `--model darksu3`" is a hard fail. A failure in "did the agent's caveat paragraph mention DRAKE four-branch" is a soft fail (warned in test output, not gating). This separates behaviors that MUST be reproducible (helper invocations) from prose that's allowed to vary (rationale text).

Negative-control test: a deliberately-broken SKILL.md fixture (e.g. the rewritten Step 4b prose with the §2.1 snippet swapped out for prose that omits the `--schema-version` arg) MUST cause the playtest to fail. This is the bell that proves WS-3 isn't trivially passing.

---

## 5. Failure modes WS-3 catches

Six concrete failure modes, each one a real WS-4 regression risk:

1. **SKILL.md prose loses an `extract_field` invocation in the Step 4b refactor.** WS-4's §2.1 snippet specifies invoking `extract_field` for both `omega_h2` (relic) and `sigma_v_zero` (annihilation). If the rewritten prose only mentions one — easy oversight when refactoring — WS-3's helper-invocation assertion catches it. WS-2 cannot catch this (WS-2 unit-tests the helper, not the SKILL.md prose).

2. **DRAKE four-branch logic mis-routes `activation_required`.** The `cmd_detect` 5-line bash fix in W4-E is the most error-prone WS-4 task. If it falls through to `found` instead of emitting `activation_required`, the LLM never emits `DRAKE_ACTIVATION_REQUIRED`. WS-3's per-branch fixture (the `activation_required` variant) makes this a single-assertion catch. WS-2 unit-tests `detect_drake.py` against canned input but doesn't exercise the bash fix end-to-end.

3. **Schema-version drift between SKILL.md prose and shipped schema files.** The §2.1 snippet hardcodes `relic/v1` and `annihilation/v1`. If W4-B ships `relic/v1.0` instead, `extract_field` exits 1 with `VERSION_DRIFT`. WS-3 catches it because `extract_field`'s exit 1 should propagate as a router blocker AND because the merged table's Ωh² row will be empty. WS-2 catches the helper's behavior; WS-3 catches the doc-vs-schema agreement.

4. **Step ordering inversion: agent invokes `detect_drake` before reading MadDM output.** A subtle prose-rewrite failure where Step 5 prose ends up before Step 4 prose. WS-2 cannot catch this (no ordering between unit tests). WS-3's transcript-ordering assertion catches it.

5. **Silent-winner regression.** The §2.1 snippet step 5 forbids "silently average, pick a winner, or paper over." If a future SKILL.md edit weakens this prose ("if values disagree by less than 20%, you may use the MadDM result"), WS-3's negative-regex assertion catches it. This is a UX-correctness regression that WS-2 unit tests cannot see (it's prose-level).

6. **`check_prereqs` SLHA-hint misuse for simplified-model UFO.** Dark SU(3) is not MSSM-class; a simplified-model UFO with `param_card.dat` should NOT block on `latest_slha`. If the rewritten Step 1 prose treats `SLHA_MISSING_HINT` as fatal, WS-3 fails because the agent emits a fatal blocker for a model where the helper correctly hint-only'd. This catches a lens-violation (LLM judgment ground in the helper).

WS-3 also surfaces (without explicitly gating on) **doc-vs-CLI drift** — the WS-2 doc-vs-CLI test catches "SKILL.md mentions a flag the helper doesn't have," but WS-3 surfaces the dual: the agent gives up because the prose says the helper has a flag and the helper says it doesn't. Useful debug signal even though WS-2 covers the gate.

---

## 6. Reuse from `plugins/hep-ph-demo/skills/dark-su3/` — **Partial**

Decision: **Partial reuse**, scoped narrowly.

Reuse:
- **`benchmarks/`** — symlink one of the existing Dark SU(3) UFO benchmark directories into the WS-3 fixture as `ufo/darkSU3/`. The UFO is the model definition; the listing confirms it's already there; reusing it costs nothing and matches the "Dark SU(3) Fig. 8" framing.
- **`SKILL.md`** — read for orientation (what the demo skill expects from a Dark SU(3) run) but DO NOT depend on it. WS-3 is exercising `/dark-matter-constraints` not `/dark-su3`.

Do NOT reuse:
- **`practitioner_script.md`** — that's the demo runbook for a different audience (the user reproducing a paper figure). WS-3 is a router playtest, not a demo. Different context.
- **`summary.schema.json`** — this is a DEMO-LEVEL schema for the dark-su3 skill's own output. The router-level schemas (`relic/v1`, `annihilation/v1`, `scattering/v1`) are WS-4 deliverables and live in `plugins/shared/schemas/`. Confusion between the two is exactly the kind of contract drift WS-1 was set up to catch.

The reuse is "borrow the model artifact; ignore the demo runbook." Anything beyond that risks coupling WS-3 to the demo skill's evolution, which is out of scope.

---

## 7. Risks (3-5 one-liners)

1. **Test-agent harness fidelity.** If the harness used to drive the playtest LLM doesn't faithfully replicate the live `/dark-matter-constraints` invocation surface (skill loading, prompt envelope, tool-call dispatch), WS-3 passes against the harness but fails against real Claude Code. Mitigation: pin the harness version + capture one real-Claude transcript per release as a "smoke" fixture.

2. **Canned-fixture realism gap.** The MadDM-stdout / DRAKE-Wolfram-stdout fixtures are hand-authored. If they diverge from real-tool output formats, WS-3's prose-level assertions (which depend on the agent successfully extracting values from those formats) succeed against the fixture and fail against real tools. Mitigation: WS-3 includes a "fixture-vs-reality parity" subsection per WS-4 §7.3 and surfaces drift as warnings.

3. **DRAKE detect-script side effects.** `/drake-install detect` invokes `wolframscript` which can be slow, can emit licensing prompts, and varies by host. Mitigation: WS-3 stubs `HEPPH_DRAKE_DETECT_CMD` for the four-branch fixtures and only runs the real detect script in a single end-to-end smoke variant, gated by `pytest -m smoke`.

4. **LLM nondeterminism flake rate.** Even with N=3 majority-rule and temperature=0, a 5% per-run flake rate gives ~14% per-scenario flake rate. CI green-rate matters. Mitigation: tune N upward (N=5 majority) for scenarios that show >2% flake in initial calibration; mark prose-level assertions as informational.

5. **Coupling to WS-2 fixture conventions.** WS-3's helper invocations re-use WS-2's fixture loaders / mocks. If WS-2's fixture conventions shift after WS-3 lands, WS-3 silently breaks. Mitigation: explicit import boundary in WS-3 plan-drafter task list, documented at top of `tests/test_dark_su3_playtest.py`.

---

## 8. Dependencies / sequencing

WS-3 depends on WS-4 + WS-2 having shipped: cannot author the playtest assertions without the rewritten SKILL.md (WS-4) and the helper modules (WS-4) and the test-agent harness conventions (WS-2). The brief says "WS-1 → WS-4 → (WS-2 ∥ WS-3)" — WS-3 starts when WS-4 is plan-finalized, can develop fixtures and golden artifacts in parallel with WS-4 implementation, but the assertion layer is locked in only after WS-4 SKILL.md hits its rewrite hash.

A v1.1 promotion (post-shipping) opens once a real Dark SU(3) MadDM run is captured: replace the canned MadDM-stdout fixture with the real output and re-run the playtest. If parity holds, WS-1 manifest's `audit_status` for the relevant rows can promote from `verified_against_synthetic` to `verified_against_real`. WS-3 is the natural carrier for that follow-up.
