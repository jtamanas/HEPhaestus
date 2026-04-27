# WS-2 Critique — Router Test Harness

**Critic:** ws2-brainstorm-critic
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md` (helper specs); `plan/ws4_plan_final.md` (locked T2/T3/T4/T5 acceptance gates); `brainstorm/ws2_propose.md` (391 lines, ~53 cases); `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (WS-1 merged, 487 lines); `tests/fixtures/` ls confirmed (maddm/, micromegas/, drake/).

---

## Verdict

**ACCEPT-WITH-CHANGES.** The proposal is structurally sound and lens-conformant, but it has three real defects: (a) genuine padding in `check_prereqs` and `extract_field` test inventories that inflates ~53 cases when ~38 would do the same work; (b) the oracle script is acceptable test infrastructure but the proposer's framing is sloppy and one of its five cases re-implements what it claims to be testing; (c) the `activation_required` env-var fake strategy is correct but the proposer doesn't justify it against the obvious alternative (`monkeypatch` + `subprocess.run` mock), which an implementer reading the proposal will second-guess. Also: a missed coordination with WS-1's existing `_HERE`/`_REPO_ROOT` constants (proposer's renaming dodge is half a solution).

The synthesizer must resolve six items below. None are fatal; all are tractable in synthesis.

---

## Per-decision rebuttal

### D1 — Test count: **Padded.**

The user is right to flag ~53. Going helper-by-helper:

**`check_prereqs.py` 12 cases — cuts to 9.**
- Cases 1–7 (happy + 5 blocker codes + SLHA hint) are load-bearing. Each exercises a unique manifest dispatch branch.
- Case 8 (`--model nonexistent_in_config`) is **legitimate** — it's not over-spec, it's a contract pin (the synthesis is silent; pinning is correct).
- Case 9 (unparseable manifest) and case 10 (config = directory) are both "internal-error rows." The user's question is sharp: what's an internal error in a path-existence check? Both ARE internal errors — exit-2 territory per the synthesis grid. Unparseable manifest is unambiguously exit-2 (helper can't read its own contract). `--config` is a directory means `json.load` raises `IsADirectoryError`. Both legit. **Keep both.**
- Case 11 (`checked` array structure) is structural: it pins the JSON schema of the helper's output. **Keep.**
- Case 12 (multiple blockers aggregated) is good but the "ordering deterministic" sub-assertion is over-spec. The helper's blocker order isn't pinned anywhere in the synthesis. Drop the ordering claim; just assert both blocker codes appear. **Keep with modification.**

The padding is in cases I-have-no-objection-to-but-should-be-collapsed. **Specifically:** cases 4 (drake_path absent / key missing) and 5 (drake_path present but bogus) can be one parametrized test (`@pytest.mark.parametrize("setup,expected_code", [...])`). Same for cases 2/3 (maddm/micromegas missing — same shape). That gets `check_prereqs` to **8 named tests + 2 parametrize bodies = 9 functions**, covering 12 cases of behavior. **Action: collapse via parametrize.**

**`extract_field.py` 12 cases — cuts to 9.**
- Cases 1–8 mirror the WS-4 plan T4 8-row matrix verbatim. **Keep all 8.**
- Case 10 (stdout includes `source_file`/`key`/`schema_version`) is structural. **Keep.**
- Case 11 (default-schema-root resolution) is **spurious**. The synthesis (§1.3) already pins the resolution rule; the WS-4 plan T4 acceptance gate already exercises it via the cross-schema sanity check. WS-2 retesting it is a copy of the WS-4 gate, which §8.1 of the proposal explicitly forbids ("WS-2 does NOT mirror the WS-4 plan's gate code"). **Drop.**
- Case 12 (nested-pointer-out-of-scope pin) is **defensible but borderline**. The argument: a future `--json-pointer` flag could break the v1 contract by silently accepting `channel_fractions.bb` as a JSON pointer, which the v1 user expects to fail with `KEY_ABSENT`. Pinning v1 behavior (literal-string-as-key ⇒ KEY_ABSENT) is forward-compat insurance. **Keep IF the proposer commits the case docstring explicitly says "this pins v1; if v1.1 adds `--json-pointer` this test must be intentionally rewritten, not deleted."** Otherwise drop.
- Case 9 (disallowed-null on scattering/v1) duplicates row 6 (`SCHEMA_MISMATCH`). The fixture is different (scattering vs relic) but the assertion is identical. **Defensible** — it cross-validates against `scattering.schema.json` which WS-4 T1 doesn't author. **Keep.**

Net: 8 (table rows) + 1 (source_file structural) = 9. Add case 12 only if the proposer adds the forward-compat docstring. **Action: drop case 11; case 12 conditional.**

**`detect_drake.py` 8 cases — keep 8.** All eight cover distinct branches; case 7 (drake_path-set short-circuit) and case 8 (default-cmd path) are the synthesizer-must-resolve unknowns, NOT padding. Test inventory correctly reflects that uncertainty. **No cuts.**

One nit: case 6 (`status:"frobbed"` not in manifest's enum literals) reads like it duplicates case 5 (non-JSON). They're actually distinct — case 5 tests JSON-parse-failure; case 6 tests valid-JSON-but-unknown-literal-against-manifest. Different code paths in the helper. **Keep both.** Synthesizer should add one sentence to the proposal making the distinction explicit so the implementer doesn't merge them.

**`verify_router_field_contract.py` 10 cases — keep 10.** Six cases (3–7 + 10) cover the six drift codes from the §3 ladder. Cases 1, 2, 8, 9 cover baseline + structural + dataclass-surface. None redundant; the WS-1 retrofit (T8) doesn't replace these because T8 exercises the helper against the SHIPPED manifest, while WS-2 here exercises against MUTATED manifests. **Keep.**

**Net test count: 9 + 8 + 9 + 10 + (oracle 4, see D2) + (doc-vs-CLI 2, see D5) = 42**, not 53. The proposer's 53 inflates the apparent surface ~25%.

### D2 — Trigger-boundary oracle script: **Acceptable test infra, but trim and reframe.**

The proposer's framing is muddled. The user's three counter-arguments:

- *"The lens says heuristic thresholds stay LLM-side. An oracle script that computes the threshold IS the helper, just renamed."* — **This is wrong** if the oracle is in `tests/oracle/` and never imported by skill code. The lens prohibits putting threshold arithmetic in **skill code** (router-side). It does NOT prohibit the test harness encoding what the threshold IS for the purpose of asserting LLM behavior on synthetic spectra. Test code is allowed to do arithmetic about what the LLM should do — that's how every LLM-eval framework on earth works.
- *"Just document the test cases in markdown; no executable oracle."* — **Worse.** Markdown isn't testable. The oracle's job is to prevent the SKILL.md prose drifting from "10%" to "10 percent rounded to 0.1" without anyone noticing. A markdown doc can't catch that drift; an executed test on a fixture can.
- *"The oracle is fine because it's TEST infrastructure, not router infrastructure."* — **This is the right framing.** The proposer SAYS this in §2 ("with a header comment that says: 'This script is a test-only reference...'") but doesn't lead with it. The synthesizer should re-anchor: the oracle is allowed because (a) it lives at `tests/oracle/`, (b) it has a header comment forbidding skill-code import, (c) WS-3 will use the oracle's outputs as ground truth when judging LLM behavior on the spectrum fixtures.

**However**, the proposer's 5 oracle cases over-specify. Specifically:
- `test_oracle_threshold_above_fires` and `test_oracle_threshold_below_does_not_fire` — load-bearing pair. **Keep.**
- `test_oracle_threshold_exactly_at_default_fires` — the proposer admits "open contract; argue ≥ vs >, document the choice." This is a **decision the oracle is making about LLM behavior**. The lens says the LLM owns the heuristic; the oracle documenting "at exactly 0.10 we fire (use ≥)" is the oracle ASSERTING what the LLM should do. That assertion belongs in the SKILL.md prose, not in the oracle. **Drop**, OR move to a SKILL.md prose sentence ("the threshold is `>= 0.10`") and assert in oracle that comments match.
- `test_oracle_resonance_5pct_above/below_fires/does_not_fire` — same pair pattern as 10%. **Keep both.**

**Net oracle: 4 cases**, not 5. And the proposer must add a sentence: "the oracle does not adjudicate the equality boundary; SKILL.md prose does, and a separate doc-vs-oracle test (see D5) asserts the prose's `>=` matches the oracle's `>=`."

The proposer's call is defensible. **Action: trim to 4 oracle cases, sharpen the framing in §2's first paragraph.**

### D3 — `activation_required` fake strategy: **Env var is correct; justify against alternatives.**

The user's three alternatives:
- **`HEPPH_DRAKE_DETECT_CMD` env var pointing at a stub bash script.** Proposer's choice. The synthesis §1.2 explicitly named this var.
- **`subprocess.run` monkeypatching in pytest.** Cleaner-looking; `monkeypatch.setattr(subprocess, "run", lambda *a, **kw: CompletedProcess(...))`.
- **Real fixture filesystem with all the right files arranged.** Provokes each state via filesystem state.

The env var wins. Reasons:
1. **It's the helper's documented test interface.** WS-4 T3 acceptance gate uses it (verified). If the helper changes how it dispatches to detect, the env var contract is what gets updated, and WS-2's tests find out by failing — that's the right feedback loop. `monkeypatch` of `subprocess.run` couples WS-2 tests to `detect_drake.py`'s internal use of `subprocess`; if T3 implementer uses `os.popen` or a `shutil.which` shim, monkeypatching breaks even though the helper still works.
2. **It tests the CLI surface end-to-end.** Including JSON parsing, exit-code dispatch, and the env-var hookup. Monkeypatching skips two of those three layers.
3. **The proposer's "awkward dependency injection" objection is a tooling preference, not a defect.** Env-var-driven test injection is standard for helpers that shell out (cf. `GIT_*` env vars, every Cobra-based CLI's testing convention).
4. **Real fixture filesystem can't provoke `activation_required`.** That state requires Wolfram refusing to activate, which is uncontrollable. The proposer's §8.3 argument is correct: stub at the JSON-stdout boundary because that's where the contract lives.

**The synthesizer should `--help` the implementer with one extra paragraph in §4.1 of the proposal:** "We considered `monkeypatch` of `subprocess.run` and rejected it because it couples test code to the helper's internal subprocess-invocation machinery, which the synthesis does not pin. The env var is the documented test interface."

But: **WS-4 T3 has not yet committed.** The proposer should re-verify after T3 lands (§8.1 of the proposal acknowledges this; correct posture).

### D4 — Test layout: **Mostly fine; one defect.**

Single `tests/` dir is correct. WS-1 already established it; bifurcating into `tests_helpers/` would break `pytest tests/` discovery and require a second `conftest.py`. **Accept layout.**

The proposer's collision-avoidance posture (renaming `_HERE`/`_REPO_ROOT`/`_DEFAULT_MANIFEST` to `_TESTS_DIR`/`_REPO`/`_MANIFEST_PATH`) is **half a solution**. The right move is:

- `conftest.py` exports the canonical names (`_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST` — match WS-1's spelling).
- WS-4 T8 retrofit replaces the WS-1 module-level constants with `from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST` (or imports via fixture).
- WS-2 introduces no shadowing.

The proposer's renaming dodge keeps the constants in two places forever; that's the bug. **Action: synthesizer must direct WS-2 to use canonical names in conftest and write a 1-line note that WS-4 T8 retrofit will adopt them. WS-2 doesn't modify `test_router_contract.py` (proposer §8.4 correct), but conftest is shared.**

The "could collide with WS-1's xfail patterns" worry is overblown. WS-1's xfails are decorator-driven, not fixture-driven; conftest fixtures don't shadow `pytest.mark.xfail`. **Accept.**

### D5 — Doc-vs-CLI parity test: **Underspecified.**

The proposer gives 6 cases worth of prose but only 2 named tests. The user's question is exactly right: WHAT does the test assert?

The proposer's bidirectional approach (Direction A: helper→doc; Direction B: doc→helper) is **correct** but the spec is too loose. Specifically:

- **What "mention in SKILL.md" means.** The proposer says "extract every line matching `python .*/scripts/<helper_basename>`." This breaks if SKILL.md uses a multi-line code fence with `\` continuations. The proposer hedges ("allow trailing `\` continuation") but doesn't pin the parse. **Synthesizer must pin: parse code fences (lines between ` ```bash ` and ` ``` `), tokenize on whitespace, collect all `--<flag>` tokens.** Don't try to be clever about line continuations; just parse the whole fence as one string.
- **Path drift.** The user's question: "if the path drifts, the test should catch it. Is that captured?" — **Not explicitly.** The proposer's tests check flag parity, not path parity. If SKILL.md says `python .../scripts/check_prereq.py` (typo) and the helper file is `check_prereqs.py`, the proposer's test would fail to find any invocation block for `check_prereqs.py` and silently pass Direction A (it has no flag-mention requirements to check). **Synthesizer must add: a third assertion that for each helper file at `scripts/*.py`, at least ONE invocation block in SKILL.md references its filename.** That catches path drift.
- **Exit-code parity.** Proposer waves it off ("most argparse helpers don't print exit codes in --help by default"). Correct call; argparse doesn't, and synthesizing exit-code parity would require the helper to overload `--help`. Skip.

**Action: synthesizer must specify (a) code-fence parsing rule, (b) path-drift assertion, (c) keep flag set-equality bidirectionally.**

### D6 — Synthesis-was-silent unknowns: **Punt to "test what WS-4 ships."**

The user asks: should WS-2 plan punt these or bind them now?

All three are WS-4 implementation details:
1. `detect_drake` short-circuit when `drake_path` set — synthesis §1.2 doesn't pin the branch label semantics for this case.
2. `check_prereqs --model nonexistent_in_config` exit code — synthesis §1.1 silent on whether this is exit-1 or exit-2.
3. `extract_field` float rendering precision — synthesis §1.3 silent on `repr(float)` vs `f"{x:.6e}"`.

**Punt is correct for all three.** Reasoning: WS-4 has 8 task gates locked; WS-2 binding behavior here would create a phantom dependency where WS-4's implementer is constrained by WS-2's plan, which is the wrong direction. The clean posture: WS-2 writes the test as documentation-of-decision (proposer's wording, §8.6 — correct). The test's docstring says "this assertion pins whatever WS-4 lands; if WS-4 changes behavior, this test must be intentionally rewritten."

**Caveat for #3 (float precision).** If WS-4's T4 implementer chooses fixed precision and WS-2 asserts exact equality, every test becomes flaky on locale/platform differences. **Synthesizer must add one bullet: WS-2 uses `pytest.approx(value, rel=1e-9)` for float comparisons, never `==`.** That's a binding decision WS-2 can make without binding WS-4.

---

## New issues (not in the proposer's frame)

### N1 — `oracle/threshold_arithmetic.py` is at risk of becoming the de facto LLM-spec.

The proposer puts a Python script at `tests/oracle/threshold_arithmetic.py` mirroring the LLM's 10%/5% arithmetic. If WS-3's playtest fails because the LLM computed `0.10` differently than the oracle, what happens? Two possibilities:

(a) The LLM is wrong; SKILL.md prose drifted. Fix the prose; oracle wins.
(b) The oracle is wrong; SKILL.md prose is correct but the oracle's interpretation drifted. Fix the oracle; prose wins.

Neither is automatically right. **Synthesizer must add a tiebreaker rule:** the oracle's docstring must include the exact SKILL.md sentence(s) it claims to encode (verbatim). If WS-3 surfaces an oracle-vs-prose disagreement, the rule is: prose is the source of truth; oracle is the lossy encoding. Rewrite the oracle, not the prose.

This is a 5-line fix to the proposer's §2 plan.

### N2 — The `spectra/` fixtures don't have a documented schema.

The proposer ships `near_threshold_10pct.json` with a `mass_gap_fraction: 0.10001` field. But there's no schema for these fixture files. WS-3 consuming them will need to know the field name. If WS-3's playtest inadvertently uses `mass_gap_pct` or `gap_fraction`, the LLM may parse them inconsistently.

**Synthesizer must add:** ship a `tests/fixtures/spectra/README.md` (lowercase, three lines) that names each field and its meaning. Or — better — make the spectrum fixtures **JSON Schema-pinned** with a tiny `spectrum/v1` schema in `plugins/shared/schemas/` (out of scope for WS-2; flag as future). For now, the README is sufficient.

### N3 — `verify_router_field_contract` test 6 (undocumented field) uses a soft warning channel.

WS-1's `test_router_contract.py` already has `test_no_undocumented_fields_in_fixtures` emitting `warnings.warn`, not asserting. The proposer's test 6 says "assert via the `xfail`/warnings channel." This is ambiguous: pytest doesn't fail on warnings by default. **Synthesizer must pin:** WS-2 test 6 either (a) uses `pytest.warns(UserWarning, match=r"DRIFT_PRESENT_BUT_UNDOCUMENTED")` to assert the warning fires, OR (b) drops the test because WS-1 already covers it. **Option (a) preferred** — it adds a real assertion against the warning emission, which WS-1 doesn't have.

### N4 — `test_doc_vs_cli_parity.py` should be in conftest as a session-scoped fixture, not re-`subprocess.run`-ing per test.

Running `--help` four times (once per helper) in a parametrized test is fine. But if the proposer's bidirectional Direction A and Direction B are split into two test files or two tests, that's 8 `subprocess.run` calls. **Synthesizer must specify:** the `--help` outputs are captured once in a session-scoped fixture (`conftest.helper_help_outputs`) and the two direction tests parametrize over it. Saves time and pins the surface.

### N5 — Proposer's "no real-tool runs" boundary leaks at the edges.

§4.3 of the proposal asserts WS-2 runs no MadDM/micrOMEGAs/DRAKE. Correct. But test 8 of `detect_drake` ("`HEPPH_DRAKE_DETECT_CMD` unset ⇒ helper invokes the real `drake-install/scripts/install.sh detect` path, but with a fake `$PATH`") is a partial real-tool exercise — it invokes `install.sh` (real) and relies on `wolframscript` being missing from the fake `$PATH`. That's not a violation of "no real-tool runs" in spirit (no Wolfram Engine starts), but it IS a partial integration with `install.sh`. **Synthesizer should narrow:** test 8 stubs `install.sh` itself via a tmp-`$PATH` shim so `install.sh` resolves to a no-op script, OR drops test 8 and lets WS-3 cover the default-command path. The proposer's framing leaves an ambiguity an implementer might trip on.

### N6 — Conftest `tmp_manifest` fixture is over-engineered for the test count.

The proposer's `tmp_manifest(monkeypatch, request)` fixture takes a "jq-style mutation passed via parametrize." Across the 10 `verify_router_field_contract` tests, only 4 (cases 3, 4, 5, 6) actually need a mutated manifest. The fixture machinery for parametrized jq mutations is more code than just inlining the mutation in each test. **Synthesizer should consider:** drop the `tmp_manifest` fixture; have each of the 4 mutation tests do its own `tmp_path / "m.json"` write. Less infrastructure, easier to read. This is a style call; the synthesizer can rule either way, but the proposer's fixture is solving a problem of scale that doesn't exist at 4 cases.

---

## Synthesizer must resolve

1. **Test count cuts (D1).** Collapse `check_prereqs` 12→9 via parametrize for paired blocker codes. Drop `extract_field` case 11 (default-schema-root); make case 12 (nested-pointer pin) conditional on a forward-compat docstring. **Net: ~42 cases, not 53.**
2. **Oracle script (D2 + N1).** Trim to 4 cases (drop "exactly at boundary"). Anchor framing as test-only infra in the FIRST sentence of §2. Add a tiebreaker rule: SKILL.md prose is source of truth; oracle is lossy encoding; verbatim prose sentence in oracle docstring.
3. **Activation-required fake (D3).** Keep env var. Add one paragraph justifying against `monkeypatch`/`subprocess.run` mock. Re-verify after WS-4 T3 lands.
4. **Conftest sharing (D4).** Use canonical names (`_HERE`, `_REPO_ROOT`, `_DEFAULT_MANIFEST`) in `conftest.py`. Note in plan that WS-4 T8's retrofit will import from conftest. Drop the renaming dodge.
5. **Doc-vs-CLI parity (D5).** Pin code-fence parsing (parse whole fence as one string), add path-drift assertion (each helper file referenced ≥1× in SKILL.md), keep bidirectional flag-set equality, skip exit-code parity. Capture `--help` once per session via fixture (N4).
6. **Punted unknowns (D6).** Document-of-decision posture for all three. Bind float comparisons to `pytest.approx(rel=1e-9)`.
7. **Spectrum fixtures (N2).** Ship a 3-line `tests/fixtures/spectra/README.md` naming the fields. Flag a future `spectrum/v1` schema as out-of-scope follow-up.
8. **Undocumented-field test (N3).** Use `pytest.warns(UserWarning, match=r"DRIFT_PRESENT_BUT_UNDOCUMENTED")` to assert the warning fires.
9. **`detect_drake` test 8 (N5).** Either stub `install.sh` via tmp-`$PATH` shim (no real install.sh invocation) or drop and defer to WS-3. Resolve the "no-real-tool-runs" boundary explicitly.
10. **`tmp_manifest` fixture (N6).** Inline mutations into the 4 needing tests, not a parametrize fixture. Or rule the fixture in; either way be explicit so the implementer doesn't half-implement it.

---

## Closing routing-lens conformance check

The proposal does NOT violate the lens. The oracle script is borderline but on the right side: it is test infrastructure, not skill code; the SKILL.md prose remains the source of truth for the heuristic; the LLM still owns the trigger judgment at runtime. The 4 helper test files exercise mechanical behavior of model-agnostic helpers; no test asserts physics. The doc-vs-CLI parity test catches drift between two artifacts that are both contract-bound, which is exactly what code-side tests should do.

The eight changes above are tractable in synthesis without breaking proposer's overall shape. ACCEPT-WITH-CHANGES.
