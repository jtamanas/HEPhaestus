# WS-3 Plan Critique — Dark SU(3) End-to-End Playtest

**Critic:** ws3-plan-critic
**Verdict:** **REJECT-WITH-CHANGES.** The plan is structurally honest about what it owes (fixtures, three harness components, two test bodies, negative-control suite, Tier-3 scaffold) and its acceptance gates are mechanical and runnable. But it underbudgets the cycle envelope by at least one cycle, pins the harness coupling at the wrong line and the wrong commit, and bakes a brittleness into Component B that the synthesis itself flagged as the load-bearing risk. Three of the six "binding decisions where synthesis was silent" are wrong calls. Tier-3 is dead-on-arrival as scaffolded. None of these are show-stoppers; all are fixable in a synthesizer pass + drafter rev. Cycle envelope must move from **5 binding / 6 ceiling** to **6 binding / 7 ceiling**.

---

## 1. Three most consequential defects

### 1.1 Harness commit pin cites a line that does not bear transcript format

The plan (T3 §Inputs, T3 §Pinned harness commit hash, ws3_synthesis.md §6.2 Component B) repeatedly claims Component B is "tightly coupled to `eval/harness/runners/claude_code.py` line 442+ format." This is false. Line 442 of the live runner reads:

```python
return f"claude-code ({self._model}, {tag})"
```

It is the body of the `name` property — a one-line formatter for the runner's display name. There is no transcript format at line 442. The actual transcript-bearing code is:

- **Line 258** — module-level docstring describing the `messages as objects of the form::` shape (the stream-json event protocol).
- **Lines 312–320** — `events = json.loads(raw_output)` / `events.append(json.loads(line))` — the actual event-stream parsing the parser would couple to.
- **Lines 375–391** — `subprocess.run(...)` invocation and `_parse_claude_json_output(result.stdout)` — the entry point Component B would mirror.

The synthesis cited "line 475" for the `--temperature` non-flag check (which is what is at line 475 — the `--model` line in `_build_command`), and the drafter inherited "line 442+" without verifying. The whole transcript-format pin is the wrong anchor. Component B will not break "if line 442 reformats" — it will break if any of (258 docstring contract, 312–320 event-stream parsing, 375 subprocess interface, the schema at `--output-format json`) changes. **The pin is performative, not load-bearing.** Replace the line citation with: pin the parser to the **module-level event shape contract** (the `events` dataclass / dict keys) plus the `_parse_claude_json_output` return shape, and gate by importing the runner's symbols at parser-import time so a refactor that renames or restructures those symbols fails at module load, not at runtime parse.

Additionally, the drafter's "Live HEAD at this draft's authoring is `a3374d41195ff455d61271a3b0203854e21c38a6`" is the **repo HEAD** at draft time. The most recent commit that actually touches `eval/harness/runners/claude_code.py` is **`63bccde` (`README onboarding + eval harness refinements`)**, not `a3374d41`. The placeholder gate (T3 #2) requires `git log -1 --format=%H -- eval/harness/runners/claude_code.py` — that returns `63bccde…`, NOT the repo HEAD. Whichever value the implementer puts in the constant, the comment "draft authored against `a3374d41…`" is misleading prose that should be corrected.

**Synthesizer/drafter must fix:**
- Replace the "line 442+" coupling phrase with a concrete coupling description that names what actually carries transcript format.
- Pin against `git log -1 --format=%H -- eval/harness/runners/claude_code.py` (file-touch HEAD), not the whole-repo HEAD. The current `63bccde…` value is what the constant must match at task open.

### 1.2 5-cycle envelope is single-margin and almost certainly insufficient

The drafter assigns:

- Cycle 1: T1 (sonnet) + T2 (opus) + T3 (opus) — three tasks in parallel.
- Cycle 2: T4 (sonnet, 5 scenarios × 2 tiers + retry budget + assertion library + system-prompt isolation).
- Cycle 3: T5 (opus, 4 sabotaged SKILL.md + Tier-3 scaffold).
- Cycle 4: reviewer pass.
- Cycle 5: hand-off.

That's **1 cycle each** for T2, T3, T5 — all opus tasks. Three issues:

1. **T2 + T3 in parallel for opus.** "opus-implementer" is presented as a class but in practice the manager dispatches one opus subagent at a time. T2 (subprocess monkey-patching with stub/real modes for 4 helpers) and T3 (event-stream parser + pre-flight) are not concurrently buildable by one opus. Cycle 1 implicitly assumes serialization → 2 cycles for T2+T3, not 1.
2. **No sonnet→opus review iteration on T4.** T4 is owned by sonnet, but T4 wires together everything T2/T3 produced AND embeds the §4.4 pass criterion AND the system-prompt isolation discipline AND the W4-D casing pin. The synthesis explicitly says "the LLM judgment is the SUBJECT under test"; the test plumbing IS the LLM judgment plumbing. A sonnet first pass that opus reviews and corrects is the realistic shape — that is 1 cycle of impl + 1 cycle of review on T4, not 1.
3. **T5 sabotages assume T4 assertion library is correct.** If T4 ships assertion IDs that don't match T5's parameterize map (`extract_field_schema_version_arg`, `extract_field_sigma_v_zero_invocation`, `no_silent_winner_negative_regex`, `spec_flag_preflight`), T5 fails on first run. T5 cycle 3 then needs a T4 patch — a hidden dependency that consumes the retry slot.

**The single retry slot (cycle 6 ceiling) is consumed by item 3 alone in a typical run.** Realistic cycle envelope:

| Cycle | Work |
|---|---|
| 1 | T1 (sonnet) + T2 (opus) parallel |
| 2 | T3 (opus) + T4 first pass (sonnet) parallel |
| 3 | T4 review (opus) + T5 first pass (opus) |
| 4 | T5 review + reviewer cross-cut |
| 5 | reviewer pass on every gate, end-to-end smoke |
| 6 | hand-off + manager-decision write-up |

**Move the envelope to 6 binding / 7 ceiling.** Keep 1 retry slot for T4 OR T5 gate-flake.

### 1.3 Tier-3 is dead-on-arrival as scaffolded

T5's Tier-3 smoke test has TWO `skipif` markers:

```python
@pytest.mark.skipif(not shutil.which("maddm-launcher"), reason="real /maddm unavailable")
@pytest.mark.skipif(not (FIXTURES/"ufo/darkSU3/dark_su3_real.ufo").exists(), …)
```

The empty-dir UFO sentinel (T1 §3 binding) is committed to git as "ONLY `README.md` + `.gitkeep`." Pre-flight risk #3 explicitly enforces that no `.py` files exist there. **Therefore `dark_su3_real.ufo` does not, cannot, and will not exist in the committed repo.** Tier-3 is permanently skipped on any host that doesn't manually drop a real UFO into the sentinel dir — and the synthesis explicitly says the user must do this at Tier-3 invocation time.

This is fine *as a contract* but the plan does not surface it. Two consequences:

1. **Gate T5 #7** (`pytest -m smoke "$T3" -v 2>&1 | grep -E "SKIPPED|skipped"`) passes trivially on every host forever, including hosts that have a real `/maddm` binary but where the operator forgot to drop a UFO. This gate cannot distinguish "Tier-3 ungated by design" from "Tier-3 silently broken by accident." It is a tautology gate.
2. **No test of the Tier-3 smoke test's own correctness.** If `run_playtest(point="A", drake_branch=None, tier="tier3")` raises a TypeError because `tier="tier3"` is not a known mode (T4 only specifies `tier="tier1"|"tier2"`), no one will know until a year from now when somebody drops a real UFO and runs `pytest -m smoke`.

**Fix:** add a single positive-mode test that runs `test_smoke_pointA_real` against an *intentionally* fake-but-named-correctly UFO file (an empty file named `dark_su3_real.ufo`) and asserts the test scaffolding (parameter wiring, `tier="tier3"` mode dispatch, artifact writing) executes — even though the real binaries are absent. The double-skipif then short-circuits at the binary check, but the artifact-writing path is exercised. Otherwise, retire the `dark_su3_real.ufo` skipif and rely on the binary-presence skipif alone, accepting that Tier-3 at scaffold time tests nothing.

---

## 2. Stress-test on the seven prompt items

### 2.1 5 cycles for 5 tasks (item 1)

Covered in §1.2. **Verdict: insufficient. Move to 6 binding / 7 ceiling.**

The drafter's argument that "T2 + T3 build in parallel because both opus" elides that opus is a model class, not an actor count — the manager dispatches one opus subagent per task slot. The proposer's read of "opus on T2 and T3 simultaneously" requires the manager to spin up two opus instances on the same cycle, which the WS-4 plan (also 5 cycles) handles by serializing T7's two cycles. Apply the same discipline here.

### 2.2 Harness commit hash pinning (item 2)

Covered in §1.1. **Verdict: pin is mis-anchored AND fragile.**

A future-commit-reformats-harness hard fail is **desirable in principle, fragile in practice**:
- Desirable: forces a deliberate re-read of the format before the parser is allowed to run.
- Fragile: any whitespace-only commit, comment edit, or unrelated method addition to `claude_code.py` invalidates the pin and blocks WS-3 tests until a developer manually bumps the constant — even though the format is unchanged.

Mitigation: pin to a **content hash of the format-bearing region** (e.g. `hashlib.sha256(b"".join(open(runner_py).readlines()[256:325]))`) where 256:325 is the `messages as objects of the form::` docstring + the `events` parsing block. A whitespace edit to an unrelated method does not invalidate that. **Recommended over the file-level git hash.**

### 2.3 T3 transcript parser coupling (item 3)

**Strong recommendation: T3 should NOT couple to log lines. It should couple to a stable structured-data boundary.**

The synthesis acknowledges (§6.2 Component B) "tightly coupled to claude_code.py line 442+ format" as a known cost. The drafter inherited that without pushing back. But:

- The runner already calls `_parse_claude_json_output(result.stdout)` (line 391) which returns a parsed dict. **The structured boundary already exists.** Component B should consume the runner's parsed output, not re-parse the raw transcript.
- The runner's `last_meta` property (line 434–437) exposes per-run metadata as a dict. **That is the format-as-data file.** Component B can read `last_meta` directly.
- The harness already supports `--output-format json` (line 474). **The output is structured.**

If the harness format ever changes, the parser's contract is "the dict returned by `_parse_claude_json_output` has these keys." That's what to pin. The line 442+ coupling is a phantom — there is no log-line transcript in the runner that the parser must reverse-engineer.

**Plan correction:** Component B accepts `harness_meta: dict` (already specified in the API!) and `captured_invocations: list[HelperInvocation]` (already specified). The function body should NOT regex-parse stdout. The "tightly coupled to line 442+" phrase in T3 §Inputs and the synthesis §6.2 should be struck. The actual coupling is to the schema of `harness_meta` (what keys it contains) and to the `HelperInvocation` NamedTuple from Component A.

This is the single largest improvement available to the plan: **the parser is not "tightly coupled to a log format." It consumes structured data. The synthesis was wrong about the architecture.**

### 2.4 T5 negative-control sabotages (item 4)

**The bell-ring gate is specified in prose, not as runnable code. Demand a runnable gate.**

T5 gate #8 reads:

```bash
pytest "$NCT" -v --no-override 2>&1 | head   # Implementer adds a --no-override flag for this self-check
```

This is **a head-of-output stub, not an assertion.** The "Implementer adds a --no-override flag for this self-check" handwaves the entire bell-ring discipline. The gate must:

1. Run the parametrized test against the LIVE SKILL.md (no env override set).
2. Assert that for each of NC-1..NC-4, the *expected* assertion does NOT fail (i.e. the live SKILL.md is not accidentally sabotaged).
3. Exit non-zero if any expected-fail assertion DOES fail against the live file.

A correct gate:

```bash
WS3_SKILL_OVERRIDE_PATH= pytest "$NCT" -v 2>&1 | tee /tmp/nc_live.log
# All 4 negative-control tests should ITSELF FAIL when run against live SKILL.md, because
# the assertion they expect to fail is NOT failing on live SKILL.md.
grep -c "FAILED" /tmp/nc_live.log | xargs -I{} test {} -eq 4
```

(Or invert: run with `WS3_FORCE_LIVE=1`, assert none of the expected_fail_assertion strings appear in the output.) The drafter punted; the synthesizer must require runnable code here.

**Sabotage-overlap concern.** The sabotage-to-assertion map is one-to-one in the table, but the actual edit lines are not isolated:

- NC-1 (drop `--schema-version`) and NC-2 (drop `extract_field` for `sigma_v_zero`) both edit Step 4b §2.1 prose. If NC-2's edit accidentally also drops the `--schema-version` line for the *remaining* `extract_field` invocation, NC-2's run fails BOTH `extract_field_schema_version_arg` AND `extract_field_sigma_v_zero_invocation`. The parameterize then reports `result.hard_failures` as `[("attempt", "extract_field_schema_version_arg"), ("attempt", "extract_field_sigma_v_zero_invocation")]`, and the synthesis §5.4 assertion `assert result.hard_assertions_failed == [expected_fail_assertion]` (exact-list-match) FAILS for NC-2 — the test is over-sensitive.

The plan inherits the synthesis's exact-equal assertion shape. **Fix:** loosen to `assert expected_fail_assertion in result.hard_failures`, and document in the README that overlap is acceptable as long as the *named* assertion is in the failure set. The drafter's parameterize shape (T5 §Parameterization) already uses the looser `in` form — but the synthesis §5.4 example used `==`. The drafter caught this; the synthesizer should explicitly bless the looser form so reviewers don't push back.

### 2.5 Tier-3 skipif markers (item 5)

Covered in §1.3. **Verdict: Tier-3 is dead-on-arrival.** Acceptable as scaffolding-only IF the plan calls this out explicitly and IF gate #7 is replaced or supplemented.

### 2.6 WS-4 dependencies (item 6)

The drafter identifies WS-4 T7 as the dependency for T4 + T5. WS-4's plan reserves T7 for cycles 2–3 (it's the only 2-cycle task; opus owner). **Buffer analysis:**

- WS-4 T7 lands at end of cycle 3 in the WS-4 envelope.
- WS-3 T1/T2/T3 can run cycles 1–2 in parallel with WS-4.
- WS-3 T4 cannot start until end of cycle 3 (when T7 lands).
- That gives WS-3 cycles 4–5 for T4 + T5, plus cycle 6 for reviewer/handoff.

The plan says "T4 opens the moment T7 lands." If T7 slips by one cycle (a real risk: the WS-4 plan's own retry slot is for T7), WS-3 T4 starts in cycle 4 instead of cycle 3, and WS-3's 5-cycle envelope is blown. **Buffer: zero.** The 6-cycle ceiling absorbs exactly one slip — the WS-4 T7 slip OR a WS-3 sabotage flake, not both.

**Fix:** explicit dependency call-out in the plan §6.4 should state: *if WS-4 T7 lands later than WS-4 cycle 3, WS-3 cycles slide by the same amount; the WS-3 6-cycle ceiling does NOT absorb WS-4 slip.* Manager must coordinate.

### 2.7 Pinned decisions vs synthesis silence (item 7)

The drafter made 6 binding decisions where synthesis was silent. Three are wrong calls:

#### 2.7.1 HelperSubprocessWrapper `HelperInvocation` as NamedTuple (T2 API shape) — WRONG

```python
class HelperInvocation(typing.NamedTuple):
    helper_name: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
```

NamedTuple has three problems for this use case:

1. **List field default.** `argv: list[str]` cannot have a sensible default in a NamedTuple without `typing.NamedTuple` inheritance gymnastics. A `dataclass(frozen=True)` handles `field(default_factory=list)` cleanly.
2. **Mutability semantics.** Hard assertions read `.argv` and may slice / mutate for log-formatting. NamedTuple's tuple-shape encourages positional access (`inv[1]`) which scatters in the assertion code; dataclass enforces named access.
3. **Compatibility with Component B.** T3 specifies `TranscriptEventLog` as `@dataclass(frozen=True)` and expects to pass `helper_invocations: list[HelperInvocation]` into it. Mixing a NamedTuple list inside a dataclass is fine but reads inconsistently. Make the whole layer dataclasses.

**Recommend:** `@dataclass(frozen=True, slots=True)` for `HelperInvocation`, matching T3's `TranscriptEventLog` style. Drafter inherits the API from synthesis §6.2 which only specified shape, not Python class form — the choice is open.

#### 2.7.2 LoC ceilings (200 / 200 / 50) for Components A / B / C — Component C ceiling too tight

T3 acceptance gate enforces `LOC_C <= 50`. Component C must:

1. Accept `skill_md_path: pathlib.Path`.
2. Open and read SKILL.md (~3 LoC including encoding).
3. `grep -F -- '--spec'` equivalent (e.g. `if "--spec" not in content`).
4. Define `class SpecFlagMissingError(RuntimeError)` with `code = "WS3_SPEC_FLAG_MISSING"` (~3 LoC).
5. Module docstring + imports (~5–10 LoC).
6. Module-level `if __name__ == "__main__":` guard for CLI invocation (T6 NC-4 sabotage runs Component C as a CLI to short-circuit before any LLM cost — synthesis §6.2 — adds ~5 LoC).
7. Argparse for the CLI surface (~10 LoC if `--skill-md-path` flag is exposed).
8. Optional: better error message that quotes the line where `--spec` should appear (~5 LoC).

50 LoC counted as `grep -cv '^\s*\(#\|$\)'` (drafter's gate) excludes blank/comment lines but counts every other line. The minimum viable Component C is ~25 LoC of code (no argparse, no CLI). With the CLI surface needed for the NC-4 short-circuit (synthesis §6.2 says C runs BEFORE LLM invocation; that means there must be an entry point), the realistic floor is **~60–80 LoC**. The 50 ceiling forces the implementer to either (a) skip the CLI and lose the NC-4 short-circuit pre-flight, or (b) cheat the LoC count. **Raise to 80.**

#### 2.7.3 `run_with_retry_budget` API in conftest — under-specified

T4 specifies:

```python
def run_with_retry_budget(scenario_id: str, point: str, drake_branch: str | None,
                          tier: typing.Literal["tier1", "tier2"]) -> RetryResult:
```

But:

- The function returns `RetryResult` which is never declared as a dataclass.
- `RetryResult.hard_failures: list[(attempt, assertion_id)]` — drafter writes "(attempt, assertion_id)" as a tuple-shape comment but never says whether it's a NamedTuple, dataclass, or raw tuple. Same architecture-decision issue as 2.7.1.
- `tier: typing.Literal["tier1", "tier2"]` — what about Tier-3? T5 calls `run_playtest(point="A", drake_branch=None, tier="tier3")`. The retry-budget API rejects that literal at type-check time. The drafter inherited a 2-tier API where T5 needs 3 tiers.

**Fix:** declare `@dataclass(frozen=True) class RetryResult` with explicit fields; widen `tier` literal to include `"tier3"` OR carve out a separate `run_smoke()` function for Tier-3.

#### 2.7.4 Decisions that ARE correct

- **Stub-mode keying rule** (T2 §Stub-mode keying rule): scenario inferred from config-path leaf — clean, deterministic, doesn't require keying on argv-position.
- **Tier-3 skipif requires real binary AND real UFO**: correct conjunction (a real `/maddm` without a UFO would crash midway; the AND prevents that).
- **Owner classes**: T2/T3/T5 to opus, T1/T4 to sonnet — defensible given subprocess monkey-patching and sabotage-with-bell-ring are the highest-judgment slots.

---

## 3. Other defects worth surfacing

### 3.1 T1 acceptance gate #6 is a false-positive trap

```bash
diff <(grep -c "Omega" "$F/canned/pointA/maddm_stdout.txt") \
     <(grep -c "Omega" "$REPO/.../tests/fixtures/maddm/MadDM_results_synthetic.txt") \
  || echo "Note: shapes differ; verify that pointA is sed-patched from the WS-1 base"
```

`echo "Note: …"` — this gate **prints a note and continues with exit 0**. The `||` only fires on diff failure, but `echo` always exits 0. The intended assertion ("the Point A maddm_stdout count of `Omega` lines matches the WS-1 source") is silently downgraded to "we noticed it differs, but the gate passes anyway." Either (a) make the gate hard with `diff … || exit 1`, or (b) drop the gate and rely on T1 implementer discipline + WS-1 fixture review. **Pick one.**

### 3.2 T1 spec_pointA.yaml gate is an exact-string match that brittleness spectrum-syntax decisions

```bash
grep -E "m_chi:\s*100" "$F/specs/spec_pointA.yaml"
```

If the spec file uses `m_chi: 100.0` or `m_chi:100` (no space), the regex `m_chi:\s*100` matches both (`\s*` allows zero whitespace, `100` is a prefix of `100.0`). But it also matches `m_chi: 1000`. **Fix:** anchor the value: `grep -E "^m_chi:\s*100\s*(#|$)"` or `grep -E "m_chi:\s*100\b"`. Same applies to all other numeric grep gates in T1.

### 3.3 T3 gate #2 file-touch HEAD vs repo HEAD

`git log -1 --format=%H -- eval/harness/runners/claude_code.py` returns the most recent commit that touched **the file**, which is `63bccde…`. The drafter's draft-time prose cites the **repo** HEAD as `a3374d41…`. Reviewer reading the constant in the parser will be confused: the comment says one hash, the gate enforces another. **Fix:** have the constant's docstring cite the file-touch HEAD explicitly with the command that produced it.

### 3.4 The "system-prompt isolation" comment-as-gate is weak

T4 acceptance gate #8:

```bash
grep -F "NO project memory" "$CF"
grep -F "NO global CLAUDE.md" "$CF"
```

This asserts a comment exists in conftest.py. It does NOT assert that the harness invocation actually omits project memory and global CLAUDE.md. A comment can lie. **Fix:** the gate must assert the harness invocation's `--append-system-prompt` (line 477 of `claude_code.py`) is set to the fixture-only system prompt and that no `CLAUDE.md` reads are observed in the captured `harness_meta.tool_uses`. Concretely, parse `harness_meta` post-run, assert `tool_uses` contains zero `Read` calls against absolute paths matching `*/CLAUDE.md`. That's a runnable assertion; the comment-grep is a docstring discipline check.

### 3.5 NC-3 sabotage wording is ambiguous

> NC-3: "do NOT silently average" weakened to "you may use MadDM if disagreement < 20%"

The synthesis §5.2 names this verbatim. But the assertion `no_silent_winner_negative_regex` (synthesis §4.2 hard #8) is:

```
(?i)(average of|we'll go with|ignore the disagreement|let's use the .* result)
```

NC-3's weakened prose ("you may use MadDM if disagreement < 20%") does NOT match the negative regex above — none of "average of", "we'll go with", "ignore the disagreement", "let's use the … result" appear. **The sabotage doesn't trigger its named assertion.** The LLM, given the weakened SKILL.md, may legitimately respond "I'll use the MadDM value because the disagreement is 14.4% which is under the 20% threshold prose says is OK" — that prose contains "use the MadDM" which matches `let's use the .* result` only if the model uses the word "let's" or "go with." Whether NC-3 actually fires the negative regex is **LLM-prose-dependent**, which makes it a SOFT assertion in disguise.

**Fix:** either (a) NC-3 sabotage edits the prose more aggressively so the LLM is more likely to emit the regex-matching phrasing, or (b) NC-3's named expected-fail assertion is changed to a hard structural assertion (e.g. "merged-output table has fewer than 4 rows" or "Caveats section omits CROSSCHECK_DISAGREEMENT") that the prose change actually causes deterministically.

### 3.6 T4 §LLM agent system-prompt isolation references a path, not content

```python
PROMPT_ENVELOPE = {
    "skill_md": pathlib.Path("plugins/constraints/skills/dark-matter-constraints/SKILL.md"),
    …
}
```

This is a **path**. The harness invocation needs the **content** as a `--append-system-prompt` string. The conftest must read the file and pass content. Drafter's prose-level dict obscures this. Trivial to fix; flag it so the implementer doesn't ship a runner that passes paths to the CLI as if they were prompts.

### 3.7 No assertion on `claude` CLI presence

§9 ready-check item 5: `which claude`. But this is a documentation check, not a gate. If the test infrastructure runs on a CI host that lacks `claude`, the entire WS-3 suite fails opaquely. **Fix:** add a session-scoped pytest fixture that asserts `shutil.which("claude")` early, with a clear skip message that says "WS-3 requires the `claude` CLI; install it before running."

---

## 4. What is good

To balance: most of the plan is sound.

1. **Acceptance gates are runnable.** Every gate has bash code or python -c; no `wc -l > 0` claims of done.
2. **Owner classes are defensible.** Opus on T2/T3/T5 reflects the load-bearing-ness of subprocess monkey-patching and sabotage-with-bell-ring; sonnet on T1/T4 reflects mechanical authoring.
3. **Tiered scope** preserved from synthesis §1 cleanly translates to T1/T4/T5.
4. **WS-2 boundary** §6.2 is correct: WS-3 does not depend on WS-2 shipping for T1.
5. **Pre-flight risks §7** (1–11) are concrete and runnable.
6. **Distinct-categories disclaimer** (T1 §3 binding sentence) is exactly what synthesis §3 demanded; the dark-su3 benchmark README's prohibition is correctly carved out from fixture-input.
7. **Sequencing diagram §4** is honest about the WS-4 dependency; the warning that WS-4 T7 must land before T4 opens is surfaced.
8. **No phantom dependencies on WS-2.** The plan correctly notes WS-2 fixtures are documentation-only references for spec-field naming.

---

## 5. Summary of fixes the synthesizer must adjudicate

1. **Cycle envelope: 5 → 6 binding, 6 → 7 ceiling.** Acknowledge sonnet→opus review iteration on T4 + T2/T3 opus serialization.
2. **Component B coupling: replace "line 442+ format" with "the structured `harness_meta` dict shape from `_parse_claude_json_output`" and drop log-line parsing.** The architecture is already structured; the synthesis was wrong about it.
3. **Tier-3 scaffold: either replace the tautology gate (T5 #7) with a positive scaffolding-runs check, or explicitly retire the UFO skipif and document Tier-3 as binary-only.**
4. **Bell-ring gate (T5 #8): replace prose-handwave with runnable assertion that runs the parametrized test against the LIVE SKILL.md and checks no expected-fail assertion fires.**
5. **`HelperInvocation` should be `@dataclass(frozen=True)`, not NamedTuple; widen `RetryResult.tier` Literal to include `"tier3"` or carve out `run_smoke()`.**
6. **Component C LoC ceiling: 50 → 80.** Accommodates CLI entry point needed for NC-4 short-circuit.
7. **NC-3 sabotage: pick a structural assertion as the named expected-fail, not the LLM-prose-dependent `no_silent_winner_negative_regex`.**

Plus three drafter-level micro-fixes that don't need synthesizer adjudication:

- T1 gate #6 `echo "Note:"` is a false-positive trap; make it `|| exit 1` or drop.
- T1 numeric greps must use `\b` or `^…$` anchoring (`m_chi:\s*100\b`).
- T3 harness-pin gate must use file-touch HEAD (`63bccde…` at draft time), not repo HEAD; comment in `transcript_event_log.py` should reflect this.

---

## 6. Lens conformance

The plan honors the routing lens at every layer: helpers stay model-agnostic (the wrapper exercises them as black-box subprocess calls), canned fixtures are tagged synthetic with explicit role-as-belief disclaimer, LLM judgment is the SUBJECT under test, the empty-dir UFO sentinel keeps UFO-content concerns out of the routing test. No physics in any assertion. Lens-conformant.

The only lens-relevant defect is the §3.4 system-prompt isolation gate: a comment-grep does not actually enforce that the harness omits global CLAUDE.md. The lens wants the LLM judging on **just the SKILL.md prose under test**, not on memory-leaked context. The plan asserts the discipline in prose; it must also enforce the discipline in code (zero CLAUDE.md reads in `harness_meta.tool_uses`).

---

## Closing

Reject-with-changes. None of the defects are show-stoppers. The cycle envelope must move to 6/7. The Component B re-architecture (drop the log-line coupling, lean on `harness_meta`) is the single-largest improvement available. The bell-ring gate, NC-3 sabotage, Tier-3 tautology gate, and Component C LoC ceiling are concrete fixes. The drafter's six binding decisions are 4-of-6 correct; the synthesizer should bless the dataclass conversion, the LoC raise, and the RetryResult.tier widening in the next pass.
