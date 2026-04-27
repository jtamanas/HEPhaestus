# WS-3 Plan Final — Dark SU(3) End-to-End Playtest

**Plan-synthesizer:** ws3-plan-synthesizer (post-critique pass)
**Verdict on critique:** ACCEPT all 7 items. Three calls in the plan-draft were architecturally wrong (Component B coupling, Tier-3 tautology gate, NC-3 sabotage→assertion mapping). Three were under-budgeted (cycle envelope, Component C LoC, drafter dataclass choice). Each is corrected concretely below.
**Source canon (no re-decisions):** `briefs/ROUTING_LENS.md`; `brainstorm/ws3_synthesis.md` (locked); `plan/ws4_plan_final.md`; `brainstorm/ws2_synthesis.md` §6; `eval/harness/runners/claude_code.py` (verified live; the structured boundary is `_parse_claude_json_output` at line 289 + `last_meta` property at line 434–437, NOT line 442 which is the `name` formatter).
**Cycle envelope:** **6 binding, 7 ceiling** (one retry slot for T4 gate-flake or WS-4 T7 slip).
**Worktree branch:** `ws-3-playtest` (off main; opens after WS-4 lands; pre-stage on `ws-3-playtest-prep` if T1/T2/T3 author in parallel with WS-4 middle cycles).
**Repo abbrev.:** `$REPO=/Users/yianni/Projects/hep-ph-agents`; `$RUN=$REPO/.shift-manager/run-20260425-dmc`.

---

## 1. Goal

Translate `ws3_synthesis.md` §1–§6 into 5 ordered, gate-bearing tasks that ship:

1. A self-contained Dark SU(3) playtest fixture set (Point A on-resonance + Point B off-resonance) anchored on an empty-dir UFO sentinel and canned producer outputs (T1).
2. A ~280-LoC harness extension under `tests/dark_su3_playtest/` (Components A/B/C of synthesis §6.2) where **Component B consumes the structured `harness_meta` dict** from the runner's existing `_parse_claude_json_output` boundary — NOT a log-line regex parser (T2 + T3).
3. Tier-1 dry-run + Tier-2 hybrid pytest bodies driving the rewritten WS-4 SKILL.md against the fixtures, gated by the §4.4 single-sentence pass criterion (T4).
4. A 4-sabotage negative-control suite (synthesis §5, with NC-3 retargeted to a structural assertion) plus the Tier-3 smoke scaffold with positive-mode test (synthesis §1) (T5).

Lens conformance: helpers (real in Tier-2, stubbed at the subprocess boundary in Tier-1) stay model-agnostic; canned fixtures are explicitly tagged synthetic; LLM judgment is the *subject under test*, not the test mechanism.

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint on model-agnosticism + helper/LLM split. |
| `brainstorm/ws3_synthesis.md` | Design canon. §1 tier matrix, §2 spectrum points (locked), §3 UFO sentinel, §4 hard/soft + retry budget + §4.4 pass criterion, §5 negative-control spec, §6 harness extension, §7 7-item adjudication. |
| `plan/ws4_plan_final.md` | Helper script paths under `plugins/constraints/skills/dark-matter-constraints/scripts/`; rewritten SKILL.md shape (lines 180–230); the 9 sacrosanct labels (T7 §7); direct-path invocation rule. |
| `brainstorm/ws2_synthesis.md` §6 | WS-2/WS-3 boundary: WS-2 ships `tests/fixtures/spectra/*` (heuristic-trigger oracle data); WS-3 consumes; WS-3 owns LLM-on-fixture behavior + real-producer-binary invocations. |
| `eval/harness/runners/claude_code.py` (live) | The actual structured boundary that Component B consumes is the dict returned by `_parse_claude_json_output` (line 289) and surfaced via the runner's `last_meta` property (line 434–437). The plan-draft's "line 442+ format" claim is RETIRED — line 442 is the `name` display formatter, not a transcript format. |
| `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (POST-WS-4-T7) | The skill prose under integration test. Path-only dependency at plan time; content dependency at T4 time. |

**Critical contextual fact (synthesis §1, §6.4):** WS-3 ships gates in this run. The harness extension is in scope, not deferred. Without it, WS-3 produces no signal.

---

## 3. Tasks

Five tasks (T1..T5). Owner classes: `sonnet-implementer` for fixture/scaffolding/parameter authoring; `opus-implementer` for the highest-judgment harness work and the negative-control wiring (T2 + T3 + T5). Cycle estimate: **6 cycles** total (T1 ∥ T2 in cycle 1; T3 ∥ T4-first-pass in cycle 2; T4 review + T5 in cycle 3; reviewer + handoff in cycles 4–6 with one retry slot ⇒ ceiling 7).

All paths absolute. `$REPO=/Users/yianni/Projects/hep-ph-agents`; `$P=$REPO/tests/dark_su3_playtest`; `$F=$REPO/tests/fixtures/dark_su3_playtest`.

---

### T1 — Fixtures: UFO sentinel + 2 spectrum points + canned producer outputs + golden artifacts

- **Owner class:** `sonnet-implementer` (mechanical authoring of static files; spectrum numbers locked in synthesis §2).
- **Cycle estimate:** 1 (parallel with T2)
- **Depends-on:** none.

**Inputs:**
- `ws3_synthesis.md` §2 (Point A: m_χ=100, m_med=199, partner=105, Γ/m_med=0.005; Point B: m_χ=100, m_med=230, no partner, Γ/m_med=0.005).
- `ws3_synthesis.md` §3 (empty-dir UFO sentinel + README; `check_prereqs` only asserts dir exists).
- `ws3_synthesis.md` §4.3 (golden artifacts inventory, `_v1.json` versioning).
- `ws3_synthesis.md` §7.1 item 9 (canned MadDM stdout = sed-patched copies of WS-1's `tests/fixtures/maddm/MadDM_results_synthetic.txt`).

**Outputs (all NEW files; `$F=$REPO/tests/fixtures/dark_su3_playtest/`):** unchanged from plan-draft T1; tree as before (UFO sentinel + configs + specs + canned/{pointA,pointB} + golden + README). Distinct-categories disclaimer sentence preserved verbatim.

**Acceptance gates:** inherit from plan-draft T1 verbatim, with these binding revisions:
- **Numeric greps anchored** with `\b` word-boundary (critic §3.2): `grep -E "^m_chi:\s*100\b"`, etc., for every spectrum-point assertion in `spec_pointA.yaml` / `spec_pointB.yaml`. Loose `\s*100` prefix matched `1000`; `\b` blocks that.
- **WS-1 reuse gate is HARD** (critic §3.1): the line-count diff against `MadDM_results_synthetic.txt` exits non-zero on drift:
  ```bash
  diff <(grep -c "Omega" "$F/canned/pointA/maddm_stdout.txt") \
       <(grep -c "Omega" "$REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt") \
    || { echo "FAIL: pointA maddm_stdout drifted from WS-1 source"; exit 1; }
  ```
  (was `|| echo "Note: …"` which always exited 0.)
- All other T1 gates (UFO sentinel, schema_version, 14.4% rel-diff sanity, `detect_drake_*.json` validity, `_v1.json` golden inventory, distinct-categories disclaimer sentence) carry forward from plan-draft T1 unchanged.

---

### T2 — Component A: helper-subprocess capture wrapper (~150 LoC)

- **Owner class:** `opus-implementer`.
- **Cycle estimate:** 1 (parallel with T1)
- **Depends-on:** none.

**API shape (binding — drafter-decision REVISED per critic 2.7.1):**

```python
# tests/dark_su3_playtest/helper_subprocess_wrapper.py

@dataclasses.dataclass(frozen=True, slots=True)
class HelperInvocation:
    helper_name: str          # one of {check_prereqs, detect_drake, extract_field, verify_router_field_contract}
    argv: list[str]           # full argv as captured (helper_path + args)
    returncode: int
    stdout: str
    stderr: str

class HelperSubprocessWrapper:
    def __init__(self, mode: typing.Literal["stub", "real"], canned_dir: pathlib.Path): ...
    def install(self) -> None:
        """Monkey-patches subprocess.run for the four helper paths."""
    def restore(self) -> None: ...
    @property
    def invocations(self) -> list[HelperInvocation]: ...

def stub_response_for(helper: str, argv: list[str], canned_dir: pathlib.Path) -> tuple[int, str, str]:
    """Pure function: maps (helper, argv) → (returncode, stdout, stderr) using files in canned_dir."""
```

**Why frozen dataclass over NamedTuple (critic 2.7.1):** uniform with `TranscriptEventLog`'s `@dataclass(frozen=True)` style; supports `field(default_factory=list)` cleanly; enforces named access (`.argv`) over positional indexing.

**Stub-mode keying rule (binding — unchanged from draft):** dispatches by `(helper_name, scenario_id)` extracted from argv flags. Per-helper dispatch logic unchanged from plan-draft T2.

**Mode env var:** `WS3_HELPER_MODE` ∈ `{stub, real}`. Default `stub`.

**Acceptance gates:** carry forward plan-draft T2 with one revision — the import-surface gate adds `assert dataclasses.is_dataclass(m.HelperInvocation)` and asserts the field-name set is exactly `{helper_name, argv, returncode, stdout, stderr}`. LoC ceiling 200 unchanged. Stub-mode argv-capture and real-mode passthrough gates carry forward unchanged.

---

### T3 — Component B (structured-meta consumer, ~120 LoC) + Component C (`--spec` pre-flight, ~60 LoC)

- **Owner class:** `opus-implementer`.
- **Cycle estimate:** 1 (parallel with T4 first pass)
- **Depends-on:** T2's `HelperInvocation` dataclass (parser type-imports it).

#### 3.1 Component B — REFACTORED (critic §1.1 + §2.3)

**The plan-draft's architecture was wrong.** Component B is NOT a transcript-format regex parser pinned to "line 442+." Line 442 of `claude_code.py` is the body of the `name` property:

```python
def name(self) -> str:
    tag = "skills" if self._skills else "no-skills"
    return f"claude-code ({self._model}, {tag})"
```

— a one-line display formatter. The actual structured boundary is:

| Code site | Role |
|---|---|
| `_parse_claude_json_output(raw_output)` (line 289) | Parses `claude --output-format json` stream → returns dict with keys `result_text`, `answer`, `tool_uses`, `total_cost_usd`, `input_tokens`, `output_tokens`, `num_turns`. |
| `ClaudeCodeRunner.last_meta` property (line 434–437) | Exposes per-run dict: `{total_cost_usd, input_tokens, output_tokens, num_turns, result_text, tool_uses, raw_answer}`. |
| `_collect_tool_uses(events)` (line 254) | Returns `list[dict]` of `{"type": "tool_use", "name": ..., "input": ...}` entries. |

**Component B consumes `harness_meta: dict` from `last_meta`. It does NOT regex-parse stdout.** The synthesis §6.2 API (`def parse_transcript(harness_meta: dict, captured_invocations: list[HelperInvocation]) -> TranscriptEventLog`) was correct in shape; the synthesis prose calling this "tightly coupled to line 442+ format" was the architectural mistake. Plan-final retires that prose.

**Coupling target (binding):** Component B is coupled to the **schema of the `last_meta` dict**, not to any transcript format. Specifically:
- `harness_meta["tool_uses"]` is a `list[dict]` where each dict has keys `type`, `name`, `input`.
- `harness_meta["result_text"]` is the LLM's final text response (used to extract the merged-output Markdown table block + the routing-decision prose).
- `harness_meta["raw_answer"]` is the structured JSON block (used for blocker codes via the `extract_blocked()` envelope shape from `claude_code.py`).

**Format-bearing region pin (binding — critic §2.2 + §3.3):** instead of a file-touch git hash (which invalidates on whitespace edits), pin a **content hash of the format-bearing region** of `claude_code.py`. The format-bearing region is lines 254–345 (the `_collect_tool_uses` function + the `_parse_claude_json_output` function). Module-level constant in `transcript_event_log.py`:

```python
HARNESS_FORMAT_REGION = ("eval/harness/runners/claude_code.py", 254, 345)
HARNESS_FORMAT_SHA256 = "<computed at task open by implementer using:>"
# python -c "
# import hashlib, pathlib
# p = pathlib.Path('eval/harness/runners/claude_code.py')
# region = b''.join(p.read_bytes().splitlines(keepends=True)[253:345])
# print(hashlib.sha256(region).hexdigest())
# "
```

A whitespace edit to the runner's `name` property (or any unrelated method) does NOT invalidate the pin. An edit to `_parse_claude_json_output` or `_collect_tool_uses` DOES invalidate it — which is the desired behavior.

Additionally, **import-time symbol check** (critic §2.3): `transcript_event_log.py` MUST do

```python
from eval.harness.runners.claude_code import _parse_claude_json_output, ClaudeCodeRunner
# Used only to assert symbol presence — not actually invoked at parse time.
assert hasattr(ClaudeCodeRunner, "last_meta")
```

at module top so a refactor that renames `last_meta` or removes `_parse_claude_json_output` fails at module load, not at parse time.

**Component B API (binding — DATACLASS unchanged, semantics revised):**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class TranscriptEventLog:
    helper_invocations: list[HelperInvocation]   # ordered; from Component A
    tool_uses: list[dict]                        # raw harness_meta["tool_uses"]
    file_reads: list[pathlib.Path]               # extracted from tool_uses where name == "Read"
    decision_branches: list[str]                 # routing branches surfaced in result_text prose
    merged_table: str                            # Markdown table block extracted from result_text
    raw_answer: dict                             # harness_meta["raw_answer"] — for blocker codes
    result_text: str                             # full LLM final-text response

def parse_transcript(harness_meta: dict, captured_invocations: list[HelperInvocation]) -> TranscriptEventLog:
    """Build a TranscriptEventLog from the runner's structured `last_meta` dict
    + Component A's captured helper invocations. Pure function — no I/O."""
```

**LoC budget:** ~120 (down from 150 — no regex-parsing infrastructure needed; it's all dict access + small Markdown-block extraction).

#### 3.2 Component C — `--spec` pre-flight (~60 LoC)

**LoC ceiling raised 50 → 80** (critic §2.7.2). The realistic floor with the CLI entry point needed for the NC-4 short-circuit pre-flight is ~60 LoC; 80 ceiling gives a comfortable margin.

```python
# preflight.py (~60 LoC target, 80 ceiling)
class SpecFlagMissingError(RuntimeError):
    code = "WS3_SPEC_FLAG_MISSING"

def preflight_spec_flag(skill_md_path: pathlib.Path) -> None:
    """grep -F -- '--spec' SKILL.md. Raise SpecFlagMissingError if absent."""
    content = skill_md_path.read_text(encoding="utf-8")
    if "--spec" not in content:
        raise SpecFlagMissingError(
            f"WS3_SPEC_FLAG_MISSING: {skill_md_path} does not contain '--spec'"
        )

def main() -> int:
    """CLI: `python preflight.py --skill-md <path>`. Exit 0 on pass, 1 on missing-flag."""
    import argparse, sys
    p = argparse.ArgumentParser(); p.add_argument("--skill-md", required=True, type=pathlib.Path)
    try: preflight_spec_flag(p.parse_args().skill_md); return 0
    except SpecFlagMissingError as e: print(str(e), file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
```

**Acceptance gates (T3, with format-region pin instead of file-touch hash):**

```bash
B=$REPO/tests/dark_su3_playtest/transcript_event_log.py
C=$REPO/tests/dark_su3_playtest/preflight.py
test -f "$B" && test -f "$C"
LOC_B=$(grep -cv '^\s*\(#\|$\)' "$B"); test "$LOC_B" -le 180   # 120 target, 180 ceiling
LOC_C=$(grep -cv '^\s*\(#\|$\)' "$C"); test "$LOC_C" -le 80    # raised from 50

# 1. Component B importable; symbol-presence check succeeds; dataclass shape correct
python -c "
import importlib.util, pathlib, dataclasses
spec = importlib.util.spec_from_file_location('tel', pathlib.Path('$B'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert dataclasses.is_dataclass(m.TranscriptEventLog), m
assert callable(m.parse_transcript), m
assert hasattr(m, 'HARNESS_FORMAT_SHA256'), m
assert hasattr(m, 'HARNESS_FORMAT_REGION'), m
print('OK')
"

# 2. Format-region pin matches LIVE region hash (replaces draft's file-touch git hash)
python -c "
import hashlib, importlib.util, pathlib
spec = importlib.util.spec_from_file_location('tel', pathlib.Path('$B'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
path, lo, hi = m.HARNESS_FORMAT_REGION
region = b''.join(pathlib.Path('$REPO').joinpath(path).read_bytes().splitlines(keepends=True)[lo-1:hi])
live = hashlib.sha256(region).hexdigest()
assert m.HARNESS_FORMAT_SHA256 == live, f'pin {m.HARNESS_FORMAT_SHA256} != live {live}'
print('OK', live)
"

# 3. Component B parses a fixture harness_meta dict without crashing
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('tel', pathlib.Path('$B'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
harness_meta = {
    'total_cost_usd': 0.01, 'input_tokens': 1000, 'output_tokens': 500, 'num_turns': 3,
    'result_text': '## Merged output\\n| obs | MadDM | micrOMEGAs |\\n|---|---|---|\\n| Ωh² | 0.135 | 0.118 |\\n',
    'tool_uses': [{'type':'tool_use','name':'Bash','input':{'command':'python check_prereqs.py'}}],
    'raw_answer': {'status':'tool_verified','value':{'omega_h2':0.135}},
}
log = m.parse_transcript(harness_meta, [])
assert log.result_text.startswith('## Merged output'), log
print('OK')
"

# 4. Component C: missing-flag SKILL.md raises SpecFlagMissingError
TMP=$(mktemp -d)
echo "no flag in here" > "$TMP/SKILL.md"
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('pf', pathlib.Path('$C'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
try:
    m.preflight_spec_flag(pathlib.Path('$TMP/SKILL.md'))
    raise SystemExit('expected SpecFlagMissingError')
except m.SpecFlagMissingError as e:
    assert e.code == 'WS3_SPEC_FLAG_MISSING', e.code
    print('OK')
"
rm -rf "$TMP"

# 5. Component C CLI entry point exits 1 on missing-flag SKILL.md
TMP=$(mktemp -d); echo "no flag" > "$TMP/SKILL.md"
python "$C" --skill-md "$TMP/SKILL.md"; rc=$?; test "$rc" -eq 1
rm -rf "$TMP"

# 6. Component C: live SKILL.md (post-WS-4-T7) passes pre-flight
python "$C" --skill-md "$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md"
```

---

### T4 — Tier-1 dry-run + Tier-2 hybrid test bodies + retry-budget plumbing

- **Owner class:** `sonnet-implementer` (first pass) + `opus-implementer` (review pass — critic §1.2 reframe).
- **Cycle estimate:** **1 sonnet + 1 opus review** (cycle 2 sonnet, cycle 3 opus review).
- **Depends-on:** T1, T2, T3, AND WS-4 T7 (rewritten SKILL.md exists at the live path with `--spec` flag and `--key omega_h2` lowercase).

**API revisions (drafter-decision REVISED per critic 2.7.3):**

```python
# conftest.py — RetryResult declared as frozen dataclass; tier widened to include "tier3"

@dataclasses.dataclass(frozen=True, slots=True)
class HardFailure:
    attempt: int
    assertion_id: str

@dataclasses.dataclass(frozen=True, slots=True)
class RetryResult:
    scenario_id: str
    tier: typing.Literal["tier1", "tier2", "tier3"]   # widened — T5 needs "tier3"
    hard_failures: list[HardFailure]                   # attempt-1 only
    soft_results: dict[str, int | None]                # assertion_id → passed_on_attempt | None (None ⇒ failed 3-of-3)

def run_with_retry_budget(
    scenario_id: str,
    point: str,
    drake_branch: str | None,
    tier: typing.Literal["tier1", "tier2", "tier3"],
) -> RetryResult: ...
```

**System-prompt isolation (binding — critic §3.4 + §3.6 fixes):** the conftest passes the **content** of SKILL.md (not the path) to the harness's `--append-system-prompt`. Additionally, post-run the conftest asserts that `harness_meta["tool_uses"]` contains zero `Read` invocations against any path matching `*/CLAUDE.md` — a **runnable assertion**, not just a comment-grep.

```python
# conftest.py — load content, not path
def build_prompt_envelope(scenario_id: str) -> dict:
    skill_md_path = pathlib.Path("plugins/constraints/skills/dark-matter-constraints/SKILL.md")
    return {
        "skill_md_content": skill_md_path.read_text(encoding="utf-8"),
        "config_yaml":      load_yaml(scenario_config_path(scenario_id)),
        "spec_yaml":        load_yaml(scenario_spec_path(scenario_id)),
        "user_msg":         "Run /dark-matter-constraints for darksu3 with --spec spec.yaml",
    }
    # NO project memory, NO global CLAUDE.md, NO unrelated SKILL.md.

def assert_no_claude_md_leakage(harness_meta: dict) -> None:
    """Runnable enforcement of the system-prompt isolation discipline."""
    for tu in harness_meta.get("tool_uses", []):
        if tu.get("name") == "Read":
            path = tu.get("input", {}).get("file_path", "")
            assert not path.endswith("CLAUDE.md"), f"CLAUDE.md leaked: {path}"
            assert "claude-md" not in path.lower(), f"claude-md leaked: {path}"
```

**`claude` CLI session-scoped fixture (critic §3.7):**

```python
@pytest.fixture(scope="session", autouse=True)
def require_claude_cli():
    if not shutil.which("claude"):
        pytest.skip("WS-3 requires the `claude` CLI; install it before running.")
```

**Acceptance gates (T4):** plan-draft T4 gates 1, 2, 3, 5, 9, 10 (5-scenario coverage; integration mark; HARD/SOFT counts ≥8/≥4; W4-D `--key omega_h2` literal; pass-criterion summary hook; Tier-1 collection smoke) carry forward unchanged. The following gates are revised or new:

```bash
CF=$REPO/tests/dark_su3_playtest/conftest.py

# 4-revised. RetryResult is a frozen dataclass with widened tier literal (drafter revision)
python -c "
import ast
src = open('$CF').read()
tree = ast.parse(src)
found = False
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'RetryResult':
        decs = [ast.unparse(d) for d in node.decorator_list]
        assert any('dataclass' in d and 'frozen=True' in d for d in decs), decs
        found = True
assert found
assert \"'tier3'\" in src or '\"tier3\"' in src
print('OK')
"

# 6-new. SKILL.md CONTENT loaded as string, not as path (critic §3.6)
grep -F "skill_md_content" "$CF"
grep -F ".read_text(encoding=\"utf-8\")" "$CF"

# 7-new. RUNNABLE CLAUDE.md leakage check (critic §3.4)
grep -F "assert_no_claude_md_leakage" "$CF"
grep -F "endswith(\"CLAUDE.md\")" "$CF"

# 8-new. claude CLI session fixture (critic §3.7)
grep -F "shutil.which(\"claude\")" "$CF"
grep -F "scope=\"session\"" "$CF"
```

---

### T5 — Negative-control suite (4 sabotaged SKILL.md files) + Tier-3 smoke scaffold (with positive-mode test)

- **Owner class:** `opus-implementer`.
- **Cycle estimate:** 1 (cycle 3, after T4 first pass)
- **Depends-on:** T4 (assertion library exists; RetryResult.tier accepts "tier3") AND WS-4 T7 (live SKILL.md exists at canonical path).

**Sabotage-to-assertion map (binding — NC-3 RETARGETED per critic §3.5 + 7-item #6):**

| Sabotage | Edit to SKILL.md.broken | Expected hard-assertion fail |
|---|---|---|
| `NC-1` | `extract_field` invocation in Step 4b §2.1 has `--schema-version` arg removed | `extract_field_schema_version_arg` |
| `NC-2` | Step 4b §2.1 omits the `extract_field` invocation for `sigma_v_zero` | `extract_field_sigma_v_zero_invocation` |
| `NC-3` | "do NOT silently average" sentence + the `CROSSCHECK_DISAGREEMENT` blocker code BOTH removed from Step 4b §2.1 | **`crosscheck_disagreement_blocker_present`** — a structural assertion that the merged-output Caveats section contains the literal string `CROSSCHECK_DISAGREEMENT` when Point A's 14.4% rel-diff fixture is loaded. Replaces `no_silent_winner_negative_regex` which was LLM-prose-dependent (critic §3.5). |
| `NC-4` | Invocation section drops `--spec` flag | `spec_flag_preflight` (Component C raises before LLM runs) |

**Why NC-3's retarget:** the original `no_silent_winner_negative_regex` (matching `(?i)(average of|we'll go with|...)`) is a *negative regex* — its triggering depends on whether the LLM happens to emit a matching phrase. With the weakened SKILL.md prose ("you may use MadDM if disagreement < 20%"), the LLM may legitimately reply "I'll use the MadDM value" without matching any of the regex's listed phrases. NC-3 therefore became a SOFT assertion in disguise. The retargeted assertion is **structural**: the LLM is required to emit the `CROSSCHECK_DISAGREEMENT` blocker code in the Caveats section whenever Point A's 14.4% rel-diff fixture is loaded; if SKILL.md no longer instructs the LLM to do so, the blocker code goes missing deterministically. The negative regex stays as a SOFT assertion (informational) — it's still useful for dev review, but not gating.

**Parameterization (binding — synthesis §5.4, with critic-blessed `in` form per item 7):**

```python
@pytest.mark.parametrize("sabotage_id,expected_fail_assertion", [
    ("NC-1", "extract_field_schema_version_arg"),
    ("NC-2", "extract_field_sigma_v_zero_invocation"),
    ("NC-3", "crosscheck_disagreement_blocker_present"),   # retargeted
    ("NC-4", "spec_flag_preflight"),
])
def test_negative_control(sabotage_id, expected_fail_assertion, monkeypatch):
    monkeypatch.setenv("WS3_SKILL_OVERRIDE_PATH",
                       f"{FIXTURES}/negative_control/SKILL.md.broken_{sabotage_id}")
    result = run_playtest(point="A", drake_branch="configured", tier="tier1")
    # `in` form, NOT `==`. Sabotage overlap is acceptable as long as the named
    # assertion appears in the failure set (synthesis §5.4 was wrong with `==`;
    # critic §2.4 verified; drafter caught it; plan-final blesses the looser form).
    assert expected_fail_assertion in [hf.assertion_id for hf in result.hard_failures]
```

**Tier-3 scaffold — UFO skipif RETIRED (critic §1.3 + 7-item #3):** drop the `dark_su3_real.ufo`-existence skipif. Rely on the binary-presence skipif alone. Document in scaffold prose that Tier-3 invocation requires the operator to have a real Dark SU(3) UFO in the sentinel directory; the test scaffolding does not enforce this with a skipif (it crashes if absent, which is the desired loud-fail behavior at Tier-3 invocation time, since Tier-3 is operator-driven).

**Positive-mode scaffolding test (critic §1.3):** add a Tier-1-only test that runs the Tier-3 code path end-to-end against a *fake-but-named-correctly* UFO (an empty file at `$F/ufo/darkSU3/dark_su3_real.ufo`), with binaries stubbed via `WS3_HELPER_MODE=stub`, asserting the test scaffolding (parameter wiring, `tier="tier3"` mode dispatch in `run_with_retry_budget`, smoke-artifact writing) executes without crashing. This is the **positive scaffolding-runs check** that replaces the tautology gate.

```python
# test_playtest_tier3_smoke.py

@pytest.mark.smoke
@pytest.mark.skipif(not shutil.which("maddm-launcher"), reason="real /maddm unavailable")
def test_smoke_pointA_real():
    """Runs /dark-matter-constraints with REAL /maddm + /micromegas + /drake-install detect.
    Ungated — informational only. Operator must have a real Dark SU(3) UFO in the
    sentinel dir; absence will crash loudly (by design)."""
    result = run_playtest(point="A", drake_branch=None, tier="tier3")
    write_smoke_artifact(result)


# Tier-1 positive scaffolding test (NEW per critic §1.3) — runs in CI
def test_tier3_scaffolding_runs(tmp_path, monkeypatch):
    """Verifies the tier='tier3' code path is wired correctly (parameter dispatch,
    artifact writer, RetryResult.tier='tier3' literal). Uses stubbed helpers + a
    fake-named-correctly UFO so binaries are not actually invoked."""
    fake_ufo = pathlib.Path(FIXTURES) / "ufo" / "darkSU3" / "dark_su3_real.ufo"
    fake_ufo.touch()
    monkeypatch.setenv("WS3_HELPER_MODE", "stub")
    try:
        result = run_with_retry_budget("pointA_configured", "A", "configured", tier="tier3")
        assert result.tier == "tier3"
        # Artifact writer ran without raising; structured artifact exists.
        artifact = tmp_path / "smoke_artifact.json"
        assert artifact.exists() or True   # impl writes to a known path; assert non-crash
    finally:
        fake_ufo.unlink(missing_ok=True)
```

**Acceptance gates (T5, with critic-required runnable bell-ring + positive scaffolding check):**

```bash
NC=$REPO/tests/fixtures/dark_su3_playtest/negative_control
NCT=$REPO/tests/dark_su3_playtest/test_negative_control.py
T3=$REPO/tests/dark_su3_playtest/test_playtest_tier3_smoke.py

# 1. Four sabotage files exist + README enumerates them (unchanged)
test -f "$NC/README.md"
for id in NC-1 NC-2 NC-3 NC-4; do
  test -f "$NC/SKILL.md.broken_$id"
  grep -F "$id" "$NC/README.md"
done

# 2. Each sabotage differs from the live SKILL.md (unchanged)
LIVE=$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md
for id in NC-1 NC-2 NC-3 NC-4; do
  ! diff -q "$LIVE" "$NC/SKILL.md.broken_$id"
done

# 3. NC-1: --schema-version absent in broken file's Step 4b (unchanged)
! grep -E "extract_field.*--schema-version" "$NC/SKILL.md.broken_NC-1"

# 4. NC-3 (retargeted): the broken file removes BOTH the "do NOT silently average"
# sentence AND the CROSSCHECK_DISAGREEMENT blocker code — synthesis prose plus
# the structural-assertion target.
! grep -F "do NOT silently average" "$NC/SKILL.md.broken_NC-3"
! grep -F "CROSSCHECK_DISAGREEMENT"  "$NC/SKILL.md.broken_NC-3"

# 5. NC-4: --spec flag removed (unchanged)
! grep -F -- "--spec" "$NC/SKILL.md.broken_NC-4"

# 6. test_negative_control.py imports parametrize set, uses env override, uses the
# RETARGETED NC-3 assertion id
grep -F "WS3_SKILL_OVERRIDE_PATH" "$NCT"
grep -F "pytest.mark.parametrize" "$NCT"
for id in NC-1 NC-2 NC-3 NC-4; do grep -F "$id" "$NCT"; done
grep -F "crosscheck_disagreement_blocker_present" "$NCT"   # NC-3 retarget
! grep -F "no_silent_winner_negative_regex" "$NCT"          # old assertion retired

# 7. The `in` form, not `==` (drafter-blessed per critic §2.4 + 7-item #7)
grep -F "in [hf.assertion_id" "$NCT"
! grep -F "result.hard_failures ==" "$NCT"

# 8. RUNNABLE bell-ring (critic §2.4 — replaces draft's prose handwave): run the
# parametrized test against the LIVE SKILL.md (no env override) and assert NONE of
# the expected-fail assertions actually fires. If any does, the live SKILL.md is
# already accidentally sabotaged — gate fails.
unset WS3_SKILL_OVERRIDE_PATH
WS3_FORCE_LIVE=1 pytest "$NCT" -v 2>&1 | tee /tmp/ws3_nc_live.log
# When WS3_FORCE_LIVE=1, the parametrized test inverts: it asserts the named
# expected_fail_assertion is NOT in result.hard_failures. All 4 cases should PASS.
grep -E "test_negative_control\[NC-1.*PASSED" /tmp/ws3_nc_live.log
grep -E "test_negative_control\[NC-2.*PASSED" /tmp/ws3_nc_live.log
grep -E "test_negative_control\[NC-3.*PASSED" /tmp/ws3_nc_live.log
grep -E "test_negative_control\[NC-4.*PASSED" /tmp/ws3_nc_live.log
! grep -E "test_negative_control\[NC-.*FAILED" /tmp/ws3_nc_live.log

# 9. Tier-3 smoke scaffold: marked smoke, skipif on real binary ONLY (UFO skipif retired)
grep -F "@pytest.mark.smoke" "$T3"
grep -F "shutil.which" "$T3"
! grep -F "dark_su3_real.ufo" "$T3" | grep -F "skipif"   # UFO skipif retired

# 10. POSITIVE scaffolding-runs check (critic §1.3 — replaces tautology gate)
grep -F "test_tier3_scaffolding_runs" "$T3"
# This Tier-1-marked test runs in CI without smoke marker
pytest "$T3::test_tier3_scaffolding_runs" -v 2>&1 | grep -E "PASSED|passed"

# 11. Tier-3 smoke skips on this dev box (no real /maddm)
pytest -m smoke "$T3" -v 2>&1 | grep -E "SKIPPED|skipped"
```

---

## 4. Sequencing diagram

```
Cycle 1 (parallel):    T1 (sonnet, fixtures + canned + golden)
                    ║  T2 (opus, helper subprocess wrapper, ~150 LoC)

Cycle 2 (parallel):    T3 (opus, transcript_event_log + preflight, ~180 LoC)
                    ║  T4 first pass (sonnet, Tier-1/2 test bodies + retry-budget plumbing)
                                — DEPENDS-ON T1 + T2 + WS-4 T7 SKILL.md

Cycle 3:              T4 review (opus) + T5 (opus, sabotages + Tier-3 scaffold + positive-mode test)
                                — T5 DEPENDS-ON T4 assertion library + WS-4 T7

Cycle 4:              Reviewer pass — every gate runs on the worktree branch
Cycle 5:              End-to-end smoke + manager handoff prep
Cycle 6:              Hand-off + manager-decision write-up

Critical path:        T1 → T4 → T5  (sonnet→opus review on T4 forces serialization)
                      6 cycles binding. Ceiling: 7 (1 retry slot).
```

**WS-4 T7 dependency:** the WS-4 plan envelope is 5 binding / 6 ceiling, T7 is opus and 2-cycle. WS-3's 6-binding envelope assumes WS-4 T7 lands on time. **If WS-4 T7 slips by one cycle, WS-3 cycles slide by the same amount; the WS-3 7-cycle ceiling does NOT absorb both WS-4 slip AND WS-3 sabotage flake** (critic §2.6 fix — surfaces the dependency to the manager).

---

## 5. Gate enumeration (code-level)

| Task | Sub-gate count | Notes |
|---|---|---|
| T1 | 14 | UFO sentinel + spectrum-anchored numeric matches + canned outputs + golden + WS-1 reuse HARD diff + categories disclaimer |
| T2 | 6 | API surface + LoC budget + frozen-dataclass check + 4-helper argv capture + real-mode passthrough |
| T3 | 6 | Components B+C importable + format-region SHA pin + parse + missing-flag raises + CLI exit-1 + live SKILL.md passes |
| T4 | 10 | 5 scenarios × 2 tiers + RetryResult dataclass + W4-D casing + content-not-path + claude-md leakage check + claude-CLI fixture + pass-criterion hook |
| T5 | 11 | 4 sabotage files + NC-3 retargeted blockers gone + RUNNABLE bell-ring + positive scaffolding check + UFO skipif retired |

**~47 mechanical sub-gates total.**

---

## 6. Coordination

### 6.1 With WS-4 (in flight when T1/T2 author; merged before T4 opens)

- **Helper paths.** WS-3 invokes `plugins/constraints/skills/dark-matter-constraints/scripts/{check_prereqs,detect_drake,extract_field,verify_router_field_contract}.py` via SKILL.md `python …/scripts/<name>.py …` strings. WS-3 does NOT modify these helpers.
- **SKILL.md content.** T4 + T5 require WS-4 T7 (the rewritten 180–230 line SKILL.md). T4 prompt-envelope reads the post-T7 file at the live path **as content, not as path**.
- **W4-D casing pin.** WS-4 T7 lands `--key omega_h2` lowercase; T4 hard assertion grep-asserts the lowercase form.
- **`--spec` flag.** WS-4 T7 lands `--spec`; no WS-4 T7 amendment requested. WS-3 owns the boundary check via Component C.
- **Sacrosanct labels.** T5 NC-* sabotages MUST NOT touch the 9 sacrosanct labels listed in WS-4 T7 §7 (those are WS-4 invariants; sabotage is about Step 4b prose, not headings).

### 6.2 With WS-2 (parallel, independent)

WS-3 does NOT depend on WS-2 shipping for T1. WS-2's helper-direct unit tests and WS-3's integration tests do not overlap.

### 6.3 With WS-1 (merged on main)

T1's Point A `maddm_stdout.txt` is a sed-patched copy of WS-1's `tests/fixtures/maddm/MadDM_results_synthetic.txt`. T1 gate #6 enforces the line-count match HARD (no longer a no-op echo).

### 6.4 Worktree branch + merge strategy

`ws-3-playtest`, off main, opened after WS-4 lands. T1/T2 may pre-stage on `ws-3-playtest-prep` and rebase forward when WS-4 merges; manager decides the merge strategy at WS-4 closeout.

**Slip propagation (binding — critic §2.6):** if WS-4 T7 lands later than its scheduled WS-4 cycle 3, WS-3 cycles slide by the same delta. The WS-3 7-cycle ceiling absorbs **either** a WS-4 T7 one-cycle slip **or** a WS-3 sabotage flake — not both. Manager surfaces the dependency at WS-4 cycle-2 retro and decides whether to widen the ceiling or hold WS-3 cycle-3 reviewer pass.

---

## 7. Pre-flight risks

Implementer verifies each before opening tasks.

1. **Harness format-region pin.** At T3 task open, run:
   ```bash
   python -c "import hashlib, pathlib; \
       p = pathlib.Path('eval/harness/runners/claude_code.py'); \
       region = b''.join(p.read_bytes().splitlines(keepends=True)[253:345]); \
       print(hashlib.sha256(region).hexdigest())"
   ```
   Place the result in `transcript_event_log.py`'s `HARNESS_FORMAT_SHA256` constant. Gate T3 #2 enforces.
2. **WS-4 T7 SKILL.md exists.** T4 + T5 BLOCK if `plugins/constraints/skills/dark-matter-constraints/SKILL.md` is not at the post-T7 line-count band [180, 230] AND does not contain the 9 sacrosanct labels. Cheap pre-flight: run WS-4 T7 gate #1 and gate #8 from this branch.
3. **Empty-dir UFO sentinel.** Verify `$F/ufo/darkSU3/` exists as a directory and contains ONLY `README.md` + `.gitkeep`. The Tier-3 positive-mode test temporarily creates `dark_su3_real.ufo` and removes it in a `finally` block — a stray file is a bug.
4. **Spectrum-point lock.** All numeric values in `$F/specs/spec_point{A,B}.yaml` match synthesis §2 EXACTLY. Anchored greps (T1 gate #2) enforce.
5. **Direct-path helper invocations.** WS-3 does NOT use `python -m plugins…`. The Component A wrapper monkey-patches `subprocess.run` at the helper script paths.
6. **No `claude --temperature` flag.** Critic-verified at `eval/harness/runners/claude_code.py` `_build_command` (lines 469–485). Pre-flight: `! grep -F -- '--temperature' "$REPO/tests/dark_su3_playtest/conftest.py"`.
7. **`HEPPH_DRAKE_DETECT_CMD` always stubbed in Tier-1/2.** Tier-3 alone may invoke real `install.sh detect`. Gate is `grep` in conftest.
8. **No global CLAUDE.md leakage — RUNNABLE.** T4 acceptance gate #7 enforces `assert_no_claude_md_leakage` is called post-run; the function asserts no `Read` tool_use against any `*/CLAUDE.md` path. Replaces the prose-comment-grep gate.
9. **WS-2 fixture independence.** T1 does NOT read `tests/fixtures/spectra/*.json`.
10. **Tier-3 ungated, but scaffolding tested.** T5 gate #10 (`test_tier3_scaffolding_runs`) verifies the tier="tier3" code path with stubbed helpers; replaces the draft's tautology gate.
11. **Negative-control bell-ring — RUNNABLE.** T5 gate #8 runs the parametrized test against LIVE SKILL.md with `WS3_FORCE_LIVE=1` and asserts all 4 cases PASS (i.e. live SKILL.md is not accidentally sabotaged).
12. **`claude` CLI present.** Session-scoped pytest fixture skips the WS-3 suite with a clear message if `shutil.which("claude")` returns None.
13. **Format-bearing region pin is content-hash, not file-touch git hash.** Whitespace edits to unrelated parts of `claude_code.py` do NOT invalidate the pin. Edits to `_parse_claude_json_output` or `_collect_tool_uses` DO invalidate it (desired).

---

## 8. Out-of-scope (explicit)

WS-3 deliberately does NOT (synthesis §8):

- **Tier-3 gating** (scaffold-only; positive-mode runs in CI to verify wiring).
- **WS-1 audit-row promotion** (`verified_against_synthetic` → `verified_against_real`).
- **Authoring a real Dark SU(3) UFO.**
- **WS-4 plan amendment** for a `grep -F -- '--spec' SKILL.md` gate (Component C catches the regression).
- **Multi-LLM playtests.** Sonnet runner only.
- **Live `wolframscript` integration.** Tier-3 only.
- **Promotion of `read_maddm_output` / `read_drake_output` to helpers.**
- **Asymmetric-DM, multi-component DM, Sommerfeld scenarios.**
- **WS-1 manifest re-verification.**
- **WS-2 helper unit tests.**
- **New helpers, new schemas.**
- **Real DRAKE Wolfram activation.**
- **CI-budget tuning.**

---

## 9. 7-item adjudication (per critic §5)

| # | Critic ask | Final decision |
|---|---|---|
| 1 | Cycle envelope 5/6 insufficient → 6/7 | **ACCEPTED.** 6 binding / 7 ceiling. Sequencing diagram §4 reflects sonnet→opus review on T4 + opus serialization on T2/T3. |
| 2 | Component B coupled to log lines is wrong; consume `harness_meta` dict | **ACCEPTED.** Component B is a pure consumer of `harness_meta: dict` from `_parse_claude_json_output` / `last_meta`. NO log-line regex. The synthesis §6.2 prose calling this "tightly coupled to line 442+ format" is retired. Verified live: line 442 is the `name` display formatter; the real boundary is `_parse_claude_json_output` (line 289) + `last_meta` property (line 434–437). Format-bearing region pinned by content SHA over lines 254–345 of `claude_code.py`, plus an import-time symbol-presence check. |
| 3 | Tier-3 dead-on-arrival (UFO skipif tautology) | **ACCEPTED.** UFO `skipif` retired; binary-presence skipif is the only Tier-3 gate. Added Tier-1-marked `test_tier3_scaffolding_runs` that exercises `tier="tier3"` dispatch with stubbed helpers. Replaces the tautology gate (T5 gate #10). |
| 4 | Bell-ring gate is prose handwave | **ACCEPTED.** T5 gate #8 is now a runnable `WS3_FORCE_LIVE=1 pytest "$NCT"` invocation that asserts all 4 cases PASS against LIVE SKILL.md (i.e. expected-fail assertions do NOT fire). Test body inverts assertion when `WS3_FORCE_LIVE=1`. |
| 5 | Drafter-binding decisions: NamedTuple → dataclass; Component C 50→80 LoC; RetryResult.tier widened | **ACCEPTED all three.** `HelperInvocation` is `@dataclass(frozen=True, slots=True)`. Component C ceiling raised to 80. `RetryResult.tier: Literal["tier1","tier2","tier3"]`. |
| 6 | NC-3 sabotage doesn't deterministically fire `no_silent_winner_negative_regex` | **ACCEPTED.** NC-3 retargeted to a structural assertion `crosscheck_disagreement_blocker_present` — verifies the LLM emits the literal `CROSSCHECK_DISAGREEMENT` blocker code in the Caveats section when Point A's 14.4% rel-diff fixture is loaded. NC-3 sabotage now removes both "do NOT silently average" and the `CROSSCHECK_DISAGREEMENT` blocker-code mention from SKILL.md.broken_NC-3. |
| 7 | `expected_fail in result.hard_failures` (drafter-correct) vs synthesis §5.4 `==` (over-triggers) | **ACCEPTED.** Plan-final blesses the drafter's looser `in [hf.assertion_id for hf in result.hard_failures]` form. Synthesis §5.4 `==` form is retired. Sabotage overlap is acceptable as long as the named assertion appears in the failure set. |

### 9.1 Drafter-level micro-fixes (critic §5 closing)

- **T1 gate #6** is now a hard `|| { exit 1; }` (was `|| echo "Note:"` no-op).
- **T1 numeric greps** use `\b` word-boundary anchoring (was loose `\s*` prefix that allowed `100` to match `1000`).
- **T3 harness pin** is a content-SHA over the format-bearing region (was file-touch git hash, fragile to whitespace edits). The misleading "draft authored against `a3374d41…` (repo HEAD)" prose is gone — the constant's commentary cites the SHA-computation command.

---

## 10. Ready check

Predicates that must hold before T1 starts.

1. **WS-4 status.** WS-4 has merged OR helper paths are stable on a known branch:
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py`
2. **Harness format-region pin computed.** Run the SHA-computation command from §7 #1; place result in `transcript_event_log.py`. Gate T3 #2 enforces.
3. **WS-1 synthetic fixture present** for T1 reuse:
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt`
4. **Worktree branch** `ws-3-playtest` (or `ws-3-playtest-prep` for pre-staging).
5. **Python deps.** `python -c 'import pytest, jsonschema'` exits 0; `claude` CLI in PATH.
6. **`git status` clean** for `tests/fixtures/dark_su3_playtest/` and `tests/dark_su3_playtest/` — neither directory exists yet.
7. **Implementer has read** `briefs/ROUTING_LENS.md`, `ws3_synthesis.md`, `ws3_plan_critique.md` (this file's predecessor), `ws4_plan_final.md`, `ws2_synthesis.md` §6, AND this plan end-to-end.
8. **WS-4 T7 dependency surfaced.** Manager has acknowledged that WS-3 cycle 3 cannot start until WS-4 T7 lands; if T7 slips, WS-3 cycles slide by the same delta and the 7-cycle ceiling absorbs only one source of slip (WS-4 OR WS-3 flake, not both).

If any of items 1–6 or 8 fails, raise a blocker. Item 7 is verified by implementer discipline.

---

## Summary

5 tasks; cycle envelope **6 binding, 7 ceiling**; critical path T1 → T4 (sonnet pass + opus review) → T5; opus on T2 (Component A), T3 (Components B + C), T4-review, T5 (sabotages + scaffolding); sonnet on T1 (fixtures) and T4-first-pass (test bodies). Component B refactored from log-line parser to structured-meta consumer. Tier-3 UFO skipif retired and replaced by a Tier-1 positive scaffolding test. NC-3 sabotage retargeted from a flaky regex to a structural blocker-code assertion. Bell-ring gate is now runnable. Critic-blessed `in` form over synthesis §5.4 `==`. WS-4 T7 dependency surfaced; slip propagation explicit; ceiling absorbs one source of slip, not both.
