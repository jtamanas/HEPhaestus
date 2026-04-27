# WS-2 Plan Critique — Router Test Harness

**Critic:** ws2-plan-critic
**Plan under review:** `plan/ws2_plan_draft.md` (586 lines, 10 tasks, 4-cycle binding / 5-cycle ceiling)
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws2_synthesis.md` (design canon, 42+1 tests, 10 adjudications); `plan/ws2_plan_draft.md`; `plan/ws4_plan_final.md` (helper paths, CLI shapes, T8 retrofit pattern, **5-cycle binding** envelope); `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (lines 37–48 paths convention).

---

## Verdict

**ACCEPT-WITH-CHANGES.** The plan transcribes the synthesis faithfully, gates are mechanically grep-able, and the 10-task decomposition is defensible. But three structural defects must be resolved before T1 starts:

1. **Cycle envelope is over-optimistic.** The plan claims 4 binding / 5 ceiling. WS-4 is binding 5 / ceiling 6. WS-2 cycle 1 (T1+T2+T3+T4) overlaps WS-4 cycle 1 (T1–T6 in parallel) — fine. But T5/T6/T7/T8 each gate on a specific WS-4 helper (T2/T3/T1+T4/T5 respectively), and T9 gates on WS-4 T7 (the 2-cycle opus-implementer task). T9 cannot start until WS-4 cycle 3 at earliest. T10 is one cycle after T9. **WS-2 minimum wall-clock is 4 cycles**, but only if WS-4 hits its critical path with zero retries. **Realistic envelope: 4 binding, 6 ceiling**, not 5.
2. **Document-of-decision posture for the 3 punted unknowns silently codifies whatever WS-4 ships in cycle 1**, including bugs. If WS-4 cycle 1 ships an exit code WS-3 then proves wrong, WS-2 caught nothing — the test merely pinned the bug. Stronger: `pytest.skip` with a marker until adjudicated, or an explicit `xfail(strict=True)` that flips when the decision lands.
3. **T1 opus assignment is over-budgeted.** The conftest is ~30 LoC of constants + 3 thin importlib wrappers. The "blast radius" the drafter cites (WS-1, WS-2, WS-4 T8) is a **naming-correctness** concern, not a judgment concern — a sonnet-implementer with a verbatim spec from synthesis §3.1 cannot get the names wrong. T10 is the better opus slot.

The 2-3 most consequential defects (in priority order) are #1 (cycle envelope), #4 (`test -f` pre-flight is necessary but not sufficient — does not catch CLI-shape drift), and #2 (document-of-decision dangerous when WS-4 cycle 1 might be wrong).

---

## Per-task review

### T1 — `tests/conftest.py` (opus-implementer)

**Defect: opus over-assignment.** Synthesis §3.1 spells out the three constants verbatim, §3.2 spells out the import statement, §3.3 enumerates three fixtures. There is no judgment to exercise. WS-1's `test_router_contract.py` lines 37–40 already prove the constant resolution works. **Recommend: sonnet-implementer**, with the conftest gates already in §T1 acceptance + a non-regression `pytest test_router_contract.py` run as the contract guard. Saves opus budget for T10.

**Gate audit:**
- Line 56 path-walk depth (`m._HERE.name == 'tests'`) is sound.
- Line 65 `pytest test_router_contract.py` non-regression run is the load-bearing gate.
- Line 67 `grep -E 'scope\s*=\s*"session"'` regex would match `scope="session"` and `scope = "session"` but not `scope=  "session"` (multiple spaces) — minor; sonnet would not produce that.
- Missing gate: assert `tests/__init__.py` already exists (synthesis §3.2: "both `tests/__init__.py` and `tests/conftest.py` exist; pytest auto-discovers"). The relative import `from .conftest import …` requires the package marker. Add: `test -f $DMC/tests/__init__.py`.

### T2 — `tests/oracle/threshold_arithmetic.py` (sonnet-implementer)

**OK.** The 8-line verbatim header is unambiguous; gate at line 84–91 enforces five canonical phrases. The "if T7 not landed, tag `verbatim-as-of-WS-4-T6-pending`" rule is a sound forward-compat tag. Synthesis §2 says "WS-4 T6" but synthesis §3.3 / §8.2 say WS-4 T7 (router SKILL.md rewrite). Plan transcribes "T6" — **typo carried from synthesis**. T7 is the SKILL.md rewrite task in `ws4_plan_final.md`. Fix in plan: change line 75 to "T7."

**Gate audit:** Line 99 `! grep -E "from.*scripts\.|import.*scripts\."` — the boundary check is one-directional (oracle does not import skill code). The reverse direction (skill code does not import oracle) lives in T10 gate 4. Both correct.

### T3 — Fixtures: `tests/fixtures/spectra/` (sonnet-implementer)

**OK.** The 4 JSON values are pinned to the synthesis §1.6 grid (0.10001/0.09999/0.0501/0.0499); the README is verbatim 3 lines per synthesis §5.2. The "`spectrum/v1` schema future-out-of-scope" gate at line 128 is a useful guard against scope creep.

**Gate audit:** Line 128 `! test -f "$REPO/plugins/shared/schemas/spectrum.schema.json"` — defensible **for this run**, but if a future run ships the schema, this gate becomes a tripwire. Consider adding a comment "T3 gate is a scope guard; remove when `spectrum/v1` lands" so it doesn't surprise future work.

### T4 — `tests/test_oracle_thresholds.py` (sonnet-implementer)

**OK.** Four tests, no equality-boundary case (synthesis §1.6 explicit). Float comparisons are fine: oracle is deterministic Python arithmetic on literal JSON values.

**Gate audit:** Line 148 `! grep -E "def test_oracle.*(boundary|equality|exact_at)"` is the right negative grep (synthesis D2). Line 154 docstring presence check via regex is sound. Acceptable.

### T5 — `tests/test_check_prereqs.py` (sonnet-implementer, depends on WS-4 T2)

**Defect: `test -f` pre-flight insufficient.** Line 174 checks the helper exists. But if WS-4 ships `check_prereqs.py` with a different CLI (e.g., `--cfg` instead of `--config`, or `--manifest-path` instead of `--manifest`), T5 tests will fail at runtime, not pre-flight. **Stronger pre-flight:**

```bash
test -f "$H" || { echo "BLOCK: WS-4 T2 not landed"; exit 1; }
# CLI-shape pre-flight:
for f in --config --model --manifest; do
  python "$H" --help 2>&1 | grep -F -- "$f" >/dev/null || \
    { echo "BLOCK: WS-4 T2 CLI drift — missing $f"; exit 1; }
done
```

Three lines of bash buy you a clean pre-flight signal vs a confusing test failure. WS-4 T2 acceptance gate already runs this exact loop, so nothing new is required from WS-4.

**Gate audit:** The 9-function name list is exactly synthesis §1.1. `grep -F "@pytest.mark.parametrize"` (line 190) is a topology check that catches whether parametrize was used (per synthesis §7 row 1 collapsing pairs 2/3 and 4/5). Could be tighter — assert `parametrize` appears at least 2 times — but `grep -F` returns 1 if any match exists, so the gate succeeds even if only one parametrize was used and the other pair was un-collapsed. **Recommend:** `test "$(grep -c '@pytest.mark.parametrize' "$T")" -ge 2`.

### T6 — `tests/test_detect_drake.py` (sonnet-implementer, depends on WS-4 T3)

**Same `test -f` insufficiency as T5.** Add CLI-shape pre-flight: `--config` and `--manifest` flags, and the documented `HEPPH_DRAKE_DETECT_CMD` env-var contract.

**Gate audit:** Line 240 `grep -F 'tmp_path' "$T" | grep -F "bin"` is a coupled grep — catches the case where the test uses `tmp_path/bin/install.sh` per critic N5. Line 241 `! grep -F '/drake-install/scripts/install.sh' "$T"` is the boundary guard. Both correct. The 7-stub list at line 213 mirrors synthesis §5.2 — fine.

**Defect:** synthesis §1.2 test 7 documents whichever WS-4 lands for the `drake_path`-set short-circuit; plan T6 line 244 grep-asserts `decision pending` + `WS-4 cycle 1 behavior`. But synthesis §8.2 item 1 names this as a **WS-4 cycle re-dispatch trigger** — meaning if WS-4 hasn't decided at WS-2 plan-draft time, WS-2 surfaces it. Plan §6.3 line 525 explicitly says "**Not a WS-4 re-dispatch trigger from WS-2 side**" — contradicts the synthesis. **Fix:** either upgrade plan §6.3 to mark this as a re-dispatch trigger if WS-4 cycle 1 hasn't decided, or downgrade synthesis §8.2 to "document-of-decision only." Pick one and resolve.

### T7 — `tests/test_extract_field.py` (sonnet-implementer, depends on WS-4 T1+T4)

**Same `test -f` insufficiency.** Add CLI-shape pre-flight: `--json`, `--key`, `--schema-version` (and optional `--schema-root` per WS-4 §9 item 2).

**Gate audit:**
- Line 296 grep on `MUST be intentionally rewritten, not deleted` is exactly synthesis §1.3 verbatim docstring — sound.
- Line 300 `grep -E "pytest\.approx\([^)]*rel\s*=\s*1e-9"` is the binding for critic D6 — sound.
- Line 306 `! grep -F "test_extract_field_default_schema_root" "$T"` is the negative guard — the dropped case 11 (synthesis §1.3 + §7 row 1).
- Missing gate: assert exactly 9 named test functions (or 9+1 if conditional pin lands). The plan greps for each name individually but never asserts the **count** — an over-eager implementer could ship 11 tests including the dropped case 11 under a different name. Add: `test "$(grep -cE '^def test_extract_field_' "$T")" -ge 9` and `-le 10`.

### T8 — `tests/test_verify_router_field_contract.py` (sonnet, depends on WS-4 T5)

**OK.** 10 functions, mutations inlined per critic N6, `pytest.warns` assertion per critic N3. Plan correctly notes WS-4 T8 retrofits WS-1; WS-2 T8 only writes new tests against the helper module.

**Gate audit:** Line 348 `! grep -F "def tmp_manifest" "$T"` and line 349 same against conftest is the right pair — catches the case where someone factored `tmp_manifest` back into conftest. Line 351 `COUNT=$(grep -c "tmp_path / [\"']m.json[\"']" "$T")` checks ≥4 inlinings — sound. Line 354 split into two greps (`grep -F "^SUMMARY "` then `grep -E '\\d\+/\\d\+/\\d\+'`) is OK but the second regex has triple-escapes that work only because of the heredoc context. Consider one combined grep: `grep -E "\\^SUMMARY \\\\d\\+/\\\\d\\+/\\\\d\\+\\$" "$T"`. Cosmetic.

### T9 — `tests/test_doc_vs_cli_parity.py` (sonnet, depends on T1+WS-4 T2/T3/T4/T5+T7)

**Defect: parser specification incomplete.** Plan line 396 `grep -E "(```bash|```)" "$T"` and line 397 `grep -F "split"` collectively assert that the test file mentions the fence delimiters and uses `split`. But synthesis §4.1 says "tokenize that string on whitespace" and "collect every token starting with `--` as a flag mention." The plan does not pin the parser implementation — Python `re`, `shlex.split`, or `str.split()` would all satisfy `grep -F "split"`. **Stronger:** the synthesis says "whole-fence-as-one-string" rule; the gate should assert that the test does NOT split on newlines (`grep -F "splitlines"` should be absent), since splitlines breaks the rule when invocations use line continuations. Add: `! grep -F "splitlines" "$T"`.

Also: synthesis §4.1 says "Identify code fences delimited by ` ```bash ` / ` ``` `" — but T7's rewritten SKILL.md may use ```` ```sh ```` or just ```` ``` ```` (no language tag). Plan does not specify which fence delimiters the parser must accept. **Fix:** add a sub-gate that asserts the parser handles both ```` ```bash ```` and ```` ``` ```` (no language tag); test against an inline fixture.

**Defect: doc-vs-CLI parity may run before T7 is finalized.** T7 is the WS-4 router SKILL.md rewrite (2 cycles in WS-4). T9 pre-flight at line 385 checks `grep -E 'python.*scripts/.*\.py' "$S"` — matches if T7 has even one direct-path invocation. But T7 in WS-4 is iterative; a partial T7 (cycle 2 of 2) could pass the pre-flight grep yet not yet land all four helper invocations. **Stronger:** the pre-flight should grep for all four helper filenames (`check_prereqs.py`, `detect_drake.py`, `extract_field.py`, `verify_router_field_contract.py`) in SKILL.md before T9 starts.

**Gate audit:** Line 401 `grep -F "helper_help_outputs"` confirms session-fixture is consumed (critic N4); line 403 `! grep -F "exit_code_parity"` is the synthesis §4 negative guard; both sound.

### T10 — Boundary audit + `run_tests.sh` (opus-reviewer)

**OK on opus-reviewer assignment** — this is the single load-bearing review pass. The 7 sub-gates are concrete:

1. **Real-tool runs:** Lines 427–428 grep for `subprocess.run("maddm"...)` etc. **Concrete and runnable.** But the grep regex is narrow — it catches `subprocess.run([..., "maddm", ...])` but misses `os.system("maddm ...")` or `subprocess.Popen(["maddm"])`. Broaden:

   ```bash
   ! grep -rE "(subprocess\.(run|call|check_call|check_output|Popen)|os\.system|os\.popen)" "$TESTS" --include="*.py" \
     | grep -E "(maddm|micromegas|wolframscript|drake)" -v # exception only via -E negation
   ```
   That's ugly. Cleaner: assert the exclusive whitelist — the only `subprocess.*` calls in tests should be invoking `sys.executable` (Python helper-as-CLI) or `bash` against fixture stub `.sh` files. Add a positive whitelist gate.

2. **LLM imports** (line 433): `grep -rE "(claude|anthropic|openai|llm)" -i` — broad enough.

3. **Conftest single-source** (lines 436–442): the loop greps each test file for `^_HERE\s*=` and `^_REPO_ROOT\s*=`. **Sound.**

4. **Oracle import boundary** (lines 445–446): the negative grep against `$DMC/scripts` directory catches the violation.

5. **Test count** (line 449): `pytest --collect-only -q | grep ... | wc -l` returns ≥42 ≤43. Acceptable.

6. **Whole-suite green:** runnable.

7. **`run_tests.sh`**: must exist, executable, exit 0.

**Missing concrete check:** "oracle leaking" was named in the user's mandate. T10 gates 4 covers oracle → skill code. But it does NOT cover **oracle leaking from tests**: `grep -r "from tests.oracle" "$DMC/tests"` should appear ONLY in `test_oracle_thresholds.py`. Add gate: `for f in $(ls $TESTS/test_*.py | grep -v test_oracle_thresholds); do ! grep -F "tests.oracle" "$f"; done`.

---

## Gate audit summary

| Task | Gate count | Concrete? | Defects |
|---|---|---|---|
| T1 | ~7 | Yes | Missing `tests/__init__.py` presence check |
| T2 | ~6 | Yes | Plan line 75 says "T6", should be "T7" |
| T3 | ~10 | Yes | Scope guard comment recommended |
| T4 | ~6 | Yes | None |
| T5 | ~12 | Yes | Add CLI-shape pre-flight; tighten parametrize count to ≥2 |
| T6 | ~14 | Yes | Add CLI-shape pre-flight; resolve §6.3 vs synthesis §8.2 contradiction |
| T7 | ~14 | Yes | Add CLI-shape pre-flight; assert function-count band [9,10] |
| T8 | ~10 | Yes | Cosmetic regex split |
| T9 | ~9 | Partial | Parser semantics under-specified; pre-flight needs all 4 helper greps |
| T10 | ~12 | Mostly | Broaden subprocess regex; add oracle-leak-from-tests check |

**~100 sub-gates total.** No gate trivially `wc -l > 0`. Coverage is high; the gaps are CLI-shape pre-flights and parser specification.

---

## Open issue adjudication

### Issue 1 — Cycle envelope

WS-2 critical path:
- T1 cycle 1 (independent)
- T2 cycle 1 (independent)
- T3 cycle 1 (independent)
- T4 cycle 1 (depends on T2+T3, mid-cycle)
- T5/T6/T7/T8 cycle 2 (each depends on a WS-4 helper that lands by WS-4 cycle 1)
- **T9 cycle ≥3** because WS-4 T7 is the only WS-4 task that takes 2 cycles (WS-4 cycles 2–3)
- T10 cycle 4 (depends on T1–T9)

If WS-4 hits its 5-cycle binding budget exactly, WS-2 hits 4 cycles. If WS-4 needs the 6-cycle ceiling (T7 retry), WS-2 cannot start T9 until WS-4 cycle 4, pushing WS-2 to 5 cycles. If WS-2 also needs a retry (e.g., T7's `extract_field` helper changes between cycle 1 and the WS-2 implementation, forcing a doc-of-decision rewrite per plan §6.3 trigger), WS-2 hits 6 cycles.

**Argued envelope: 4 binding, 6 ceiling** (not 5). The plan claims 5 ceiling; this is one cycle too tight. Reconcile by either committing to 6 ceiling explicitly or adding an explicit "if WS-4 hits its ceiling, WS-2 envelope extends by one cycle."

### Issue 2 — Document-of-decision posture (3 unknowns)

WS-2 currently asserts whatever WS-4 cycle-1 ships for:
- `detect_drake` `drake_path`-set short-circuit branch label
- `check_prereqs --model nonexistent_in_config` exit code
- `extract_field` float rendering precision (WS-2-owned via `pytest.approx(rel=1e-9)`)

The third is fine — it's a WS-2-owned binding decision per critic D6. The first two are dangerous: if WS-4 cycle 1 ships a wrong behavior, WS-2 codifies it as truth.

**Stronger posture:** mark these tests with `pytest.mark.xfail(strict=True, reason="WS-4 decision pending — see ws2_synthesis.md §8.2")` until WS-4 cycle 1 lands AND a manager-level decision-of-record exists in `state/MANAGER_DECISIONS.md`. When the decision lands, flip xfail to a normal test with a docstring referencing the decision-of-record.

This is more conservative than the plan's "doc-of-decision" posture and prevents WS-3 from inheriting a phantom contract. **Recommend this posture replace the plan's current §6.3 wording.**

### Issue 3 — T1 opus assignment

Synthesis §3 spec is so precise that no opus judgment is exercised in T1. Recommend **sonnet-implementer with the synthesis §3.1 table inline as a code-review checklist**. Saves opus for T10 and reduces cycle-1 contention.

### Issue 4 — Pre-flight `test -f` discipline

The plan's pre-flight is presence-only. It catches "WS-4 T2 not landed" but misses "WS-4 T2 landed with `--cfg` instead of `--config`." The proposed three-line CLI-shape pre-flight (above, in T5 review) costs nothing and surfaces drift cleanly. **Recommend: add CLI-shape pre-flights to T5/T6/T7/T9 (the four CLI-consuming tasks).**

### Issue 5 — Task count (T2 + T3 merge?)

The user's mandate asks whether T2 (oracle module) and T3 (spectra fixtures) could merge with T4 (consumer test). **No — keep separate.** T2 ships an importable Python module with a verbatim header that's grep-asserted independently. T3 ships JSON+README that get consumed by both T4 (oracle test, WS-2) and the future WS-3 LLM playtest. Merging would couple WS-2/WS-3 hand-off to T4 acceptance, which is wrong. Synthesis §6 explicit: "WS-2 ships the spectra fixtures; WS-3 consumes them."

The 10-task count is **defensible as-is** (acknowledging T10 was added beyond the synthesis's 9-task explicit list — it's the boundary-audit pass the synthesis names obliquely in §6). Plan is correct to make T10 a dedicated reviewer task.

### Issue 6 — Parser semantics for T9 doc-vs-CLI parity

Synthesis §4.1 is precise: "Identify code fences delimited by ` ```bash ` / ` ``` `. Treat each fence's contents as ONE string. Tokenize that string on whitespace. Collect every token starting with `--` as a flag mention."

The plan asserts only `grep -E "(```bash|```)"` and `grep -F "split"`. It does NOT assert:
- The parser does NOT call `splitlines()` (that would break the whole-fence-as-one-string rule).
- The parser handles fence-without-language-tag.
- The parser treats `--<flag>` substrings within longer tokens correctly (e.g., `--cmd=foo --bar` should yield `--cmd` and `--bar` after `=` splitting? Synthesis is silent — should pin via test-case fixture).

**Recommend: add a sub-gate inline fixture in T9 that exercises the parser against (a) a `bash`-tagged fence with a flag, (b) an untagged fence with a flag, (c) a flag with `=value` syntax — confirms parser yields the expected flag set.**

### Issue 7 — T10 boundary audit concreteness

The user's mandate names three boundary checks: real-tool runs, LLM imports, oracle leaking. Plan T10 covers them but the regex breadth varies. **Concrete checks recommended:**

```bash
# 1. Real-tool runs (positive whitelist instead of negative blacklist)
grep -rE "(subprocess\.(run|call|check_call|check_output|Popen)|os\.system|os\.popen|os\.exec)" \
  "$TESTS" --include="*.py" | \
  grep -vE "(sys\.executable|tmp_path|fixtures/.*\.sh|stub_)" && \
  { echo "BOUNDARY: real-tool invocation"; exit 1; } || echo "BOUNDARY OK: subprocess only via sys.executable or stub"

# 2. LLM imports (already concrete enough)
! grep -rE "(claude|anthropic|openai|llm)" "$TESTS" --include="*.py" -i

# 3. Oracle leaking — TWO directions
!grep -rE "from tests\.oracle|import tests\.oracle" "$DMC/scripts"  # skill code
for f in $(ls $TESTS/test_*.py | grep -v test_oracle_thresholds); do
  ! grep -F "tests.oracle" "$f"  # only the oracle test imports the oracle
done
```

Plan as drafted catches the obvious cases but leaves off the test-from-test oracle leak. Add the loop.

---

## Synthesizer must resolve

1. **Cycle envelope:** bind to **4 cycles, 6 ceiling** (not 5 ceiling). Add explicit clause: "WS-2 envelope extends one cycle if WS-4 hits its 6-cycle ceiling."
2. **T1 owner class:** downgrade from `opus-implementer` to `sonnet-implementer`. Spec is precise; no judgment.
3. **Document-of-decision posture:** replace with `pytest.mark.xfail(strict=True)` markers for the two WS-4-owned decisions (`detect_drake` short-circuit branch label; `check_prereqs --model nonexistent_in_config` exit code) until decision-of-record lands. Keep the float-precision binding (`pytest.approx(rel=1e-9)`) as-is — that's WS-2-owned.
4. **Plan §6.3 vs synthesis §8.2 contradiction:** §6.3 says these are NOT WS-4 re-dispatch triggers; §8.2 says they ARE. Pick one. **Recommend §8.2 wins** — the WS-2 plan-drafter must surface them as WS-4 re-dispatch triggers when authoring the test, not silently codify whatever lands.
5. **Pre-flight discipline:** add CLI-shape pre-flights to T5/T6/T7/T9 (`--help` greps for required flags). Three lines of bash per task; catches WS-4 helper-CLI drift cleanly.
6. **T9 parser semantics:** pin (a) `splitlines` forbidden, (b) untagged fences accepted, (c) inline parser fixture validates expected flag set on three canonical inputs.
7. **T10 boundary audit:** broaden subprocess regex (positive whitelist on `sys.executable`/stub); add oracle-leak-from-tests guard (only `test_oracle_thresholds.py` imports `tests.oracle`).

---

## Closing routing-lens conformance check

The plan respects the lens: WS-2 tests model-agnostic mechanical behavior; oracle is permitted exception (test infra, no skill-code import); doc-vs-CLI parity is mechanical; the four `spectra/` fixtures are data, not assertions. **Plan is lens-conformant.**

The defects are operational (cycle envelope, pre-flight depth, doc-of-decision conservatism), not philosophical. Accept-with-changes; the seven items above must be resolved before T1 starts.
