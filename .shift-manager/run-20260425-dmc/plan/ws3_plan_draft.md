# WS-3 Plan Draft — Dark SU(3) End-to-End Playtest

**Plan-drafter:** ws3-plan-drafter
**Source canon (no re-decisions):** `briefs/ROUTING_LENS.md`; `brainstorm/ws3_synthesis.md` (locked); `plan/ws4_plan_final.md` (helper paths + SKILL.md shape); `brainstorm/ws2_synthesis.md` §6 (WS-2/WS-3 boundary).
**Cycle envelope:** **5 cycles, 6 ceiling** (1 retry slot for T4 gate-flake or T5 negative-control suite).
**Worktree branch:** `ws-3-playtest` (off main; opens after WS-4 lands).
**Repo abbrev.:** `$REPO=/Users/yianni/Projects/hep-ph-agents`; `$RUN=$REPO/.shift-manager/run-20260425-dmc`.

---

## 1. Goal

Translate `ws3_synthesis.md` §1–§6 into 5 ordered, gate-bearing tasks that ship:

1. A self-contained Dark SU(3) playtest fixture set (Point A on-resonance + Point B off-resonance) anchored on an empty-dir UFO sentinel and canned producer outputs (T1).
2. A ~300-LoC harness extension under `tests/dark_su3_playtest/` (Components A/B/C of synthesis §6.2) that captures helper subprocess calls, parses the harness transcript, and pre-flights `--spec` (T2 + T3).
3. Tier-1 dry-run + Tier-2 hybrid pytest bodies driving the rewritten WS-4 SKILL.md against the fixtures, gated by the §4.4 single-sentence pass criterion (T4).
4. A 4-sabotage negative-control suite (synthesis §5) plus the Tier-3 smoke scaffold (ungated; synthesis §1) (T5).

Lens conformance: helpers (real in Tier-2, stubbed at the subprocess boundary in Tier-1) stay model-agnostic; canned fixtures are explicitly tagged synthetic; LLM judgment is the *subject under test*, not the test mechanism.

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint on model-agnosticism + helper/LLM split. |
| `brainstorm/ws3_synthesis.md` | Design canon. §1 tier matrix, §2 spectrum points (locked), §3 UFO sentinel, §4 hard/soft + retry budget + §4.4 pass criterion, §5 negative-control spec, §6 harness extension, §7 7-item adjudication. |
| `plan/ws4_plan_final.md` | Helper script paths under `plugins/constraints/skills/dark-matter-constraints/scripts/`; rewritten SKILL.md shape (lines 180–230); the 9 sacrosanct labels (T7 §7); direct-path invocation rule. |
| `brainstorm/ws2_synthesis.md` §6 | WS-2/WS-3 boundary: WS-2 ships `tests/fixtures/spectra/*` (heuristic-trigger oracle data); WS-3 consumes; WS-3 owns LLM-on-fixture behavior + real-producer-binary invocations. |
| `eval/harness/runners/claude_code.py` (lines 442+) | Transcript format Component B parses. **Pin commit:** `<HARNESS_COMMIT_HASH_PLACEHOLDER>` (current main HEAD when T2 starts; implementer fills in at task open). Live HEAD at this draft's authoring is `a3374d41195ff455d61271a3b0203854e21c38a6`. |
| `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (POST-WS-4-T7) | The skill prose under integration test. Path-only dependency at plan time; content dependency at T4 time. |

**Critical contextual fact (synthesis §1, §6.4):** WS-3 ships gates in this run. The harness extension is in scope, not deferred. Without it, WS-3 produces no signal.

---

## 3. Tasks

Five tasks (T1..T5). Owner classes: `sonnet-implementer` for fixture/scaffolding/parameter authoring; `opus-implementer` for the highest-judgment harness work and the negative-control wiring (T2 + T5). Cycle estimate: **5 cycles** total (1 + 1 + 1 + 1 + 1), one retry slot ⇒ ceiling 6.

All paths absolute. `$REPO=/Users/yianni/Projects/hep-ph-agents`; `$P=$REPO/tests/dark_su3_playtest`; `$F=$REPO/tests/fixtures/dark_su3_playtest`.

---

### T1 — Fixtures: UFO sentinel + 2 spectrum points + canned producer outputs + golden artifacts

- **Owner class:** `sonnet-implementer` (mechanical authoring of static files; spectrum numbers locked in synthesis §2).
- **Cycle estimate:** 1
- **Depends-on:** none (parallel with T2).

**Inputs:**
- `ws3_synthesis.md` §2 (Point A: m_χ=100, m_med=199, partner=105, Γ/m_med=0.005; Point B: m_χ=100, m_med=230, no partner, Γ/m_med=0.005).
- `ws3_synthesis.md` §3 (empty-dir UFO sentinel + README; `check_prereqs` only asserts dir exists).
- `ws3_synthesis.md` §4.3 (golden artifacts inventory, `_v1.json` versioning).
- `ws3_synthesis.md` §7.1 item 9 (canned MadDM stdout = sed-patched copies of WS-1's `tests/fixtures/maddm/MadDM_results_synthetic.txt`).
- WS-1 fixture `$REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt` (re-used as base).
- `plugins/shared/schemas/relic.schema.json` + `annihilation.schema.json` (WS-4 T1 — referenced for canned `relic.json` / `annihilation.json` body shape).

**Outputs (all NEW files; `$F=$REPO/tests/fixtures/dark_su3_playtest/`):**

```
$F/ufo/darkSU3/
  README.md                          # Sentinel; documents synthetic role; never read by Tier-1/2
  .gitkeep                           # Keep empty dir under git

$F/configs/
  config_pointA.yaml                 # models.darksu3.ufo_path → $F/ufo/darkSU3; drake_path → $F/canned/drake_pointA/
  config_pointB.yaml                 # Same UFO; drake_path absent (Point B doesn't fire Step 5)

$F/specs/
  spec_pointA.yaml                   # m_chi:100, m_med:199, partner:105, Gamma_over_m:0.005
  spec_pointB.yaml                   # m_chi:100, m_med:230, no partner, Gamma_over_m:0.005

$F/canned/
  pointA/
    maddm_stdout.txt                 # sed-patched copy of WS-1 MadDM_results_synthetic.txt; Ωh²=0.135
    micromegas_summary.json          # Ωh²=0.118, σ_SI=2.1e-46, σ_SD=4.0e-42 (drives 14.4% rel-diff)
    micromegas_relic.json            # schema_version: relic/v1, omega_h2: 0.118
    micromegas_annihilation.json     # schema_version: annihilation/v1, sigma_v_zero: 2.5e-26
    drake_stdout.txt                 # Synthetic DRAKE narrow-resonance numeric output
    detect_drake_configured.json     # status:"configured", path, version (Branch fixture 1)
    detect_drake_found.json          # status:"found", path (Branch fixture 2)
    detect_drake_missing.json        # status:"missing" (Branch fixture 3)
    detect_drake_activation.json     # status:"activation_required" (Branch fixture 4)
  pointB/
    maddm_stdout.txt                 # Off-resonance MadDM stdout; relic-only fixture
    # NO micromegas, NO drake outputs — Point B's expected route never reaches them
  README.md                          # Names each canned file's role + role-as-belief disclaimer

$F/golden/
  expected_step_trace_v1.json        # Per scenario: ordered list of [helper, argv-shape] tuples
  expected_blockers_v1.json          # Per scenario: list of expected blocker codes
  expected_table_structure_v1.json   # Per scenario: 4 rows + columns + which cells are '—'
  expected_merged_table_pointA.md    # Human-readable reference (NOT a verbatim gate)
  expected_merged_table_pointB.md    # Same, for Point B
  README.md                          # Versioning convention (_v1 → _v2 on contract change)

$F/README.md                         # Fixture-set landing doc; declares synthetic provenance per
                                     # routing-lens "fixtures encode beliefs about producer outputs"
```

**Sentinel content (§3 binding):** `$F/ufo/darkSU3/README.md` is one paragraph stating "synthetic sentinel for the WS-3 router playtest; NO real UFO; never read by any tool in Tier-1 or Tier-2; if Tier-3 is run, drop a real Dark SU(3) UFO into this directory before invoking `pytest -m smoke`."

**Distinct-categories disclaimer (§3 binding — call out for reviewers):** `$F/README.md` MUST contain the verbatim sentence:

> The numeric values in `canned/` (`Ωh² = 0.135` etc.) are FIXTURE INPUT driving the router's rel-diff arithmetic, NOT gate thresholds. The `plugins/hep-ph-demo/skills/dark-su3/benchmarks/README.md` prohibition on inlining numeric thresholds for `dark-su3` applies to plan gates, not to test fixtures.

**Acceptance gates (mechanical):**

```bash
F=$REPO/tests/fixtures/dark_su3_playtest

# 1. UFO sentinel: directory exists, README + .gitkeep present, no UFO source files
test -d "$F/ufo/darkSU3"
test -f "$F/ufo/darkSU3/README.md"
test -f "$F/ufo/darkSU3/.gitkeep"
! ls "$F/ufo/darkSU3"/*.py 2>/dev/null
grep -F "synthetic sentinel" "$F/ufo/darkSU3/README.md"
grep -F "never read by any tool in Tier-1 or Tier-2" "$F/ufo/darkSU3/README.md"

# 2. Spectrum points: locked numeric values (synthesis §2)
grep -E "m_chi:\s*100" "$F/specs/spec_pointA.yaml"
grep -E "m_med:\s*199" "$F/specs/spec_pointA.yaml"
grep -E "partner:\s*105" "$F/specs/spec_pointA.yaml"
grep -E "Gamma_over_m:\s*0\.005" "$F/specs/spec_pointA.yaml"
grep -E "m_med:\s*230" "$F/specs/spec_pointB.yaml"
! grep -E "partner:\s*[0-9]" "$F/specs/spec_pointB.yaml"   # Point B has no partner

# 3. Canned outputs: Point A drives 14.4% rel-diff; Point B is relic-only
python -c "
import json
relic = json.load(open('$F/canned/pointA/micromegas_relic.json'))
assert relic['schema_version'] == 'relic/v1', relic
assert abs(relic['omega_h2'] - 0.118) < 1e-9, relic
import re
maddm = open('$F/canned/pointA/maddm_stdout.txt').read()
m = re.search(r'Omega.*h\^?2.*=\s*([0-9.]+)', maddm)
assert m and abs(float(m.group(1)) - 0.135) < 1e-9, m
# 14.4% rel-diff sanity
assert abs((0.135 - 0.118)/0.118 - 0.144) < 0.005
print('OK')
"
! test -e "$F/canned/pointB/micromegas_summary.json"   # Point B: relic-only
! test -e "$F/canned/pointB/drake_stdout.txt"

# 4. detect_drake fixtures: 4 branches, valid JSON each
for b in configured found missing activation; do
  python -c "import json; d=json.load(open('$F/canned/pointA/detect_drake_${b}.json')); assert 'status' in d, d"
done

# 5. Golden artifacts: _v1 suffix; expected_step_trace covers both points × all scenarios
test -f "$F/golden/expected_step_trace_v1.json"
test -f "$F/golden/expected_blockers_v1.json"
test -f "$F/golden/expected_table_structure_v1.json"
python -c "
import json
trace = json.load(open('$F/golden/expected_step_trace_v1.json'))
# 5 scenarios per §4.4: 4 DRAKE branches for Point A + 1 for Point B
assert len(trace) >= 5, trace
ids = {s['scenario_id'] for s in trace}
assert {'pointA_configured','pointA_found','pointA_missing','pointA_activation','pointB'} <= ids, ids
print('OK', len(trace))
"

# 6. WS-1 reuse: Point A maddm_stdout is a derivative of WS-1 synthetic (synthesis §7.1 item 9)
diff <(grep -c "Omega" "$F/canned/pointA/maddm_stdout.txt") \
     <(grep -c "Omega" "$REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt") \
  || echo "Note: shapes differ; verify that pointA is sed-patched from the WS-1 base"

# 7. Distinct-categories disclaimer (binding §3)
grep -F "FIXTURE INPUT driving the router's rel-diff arithmetic, NOT gate thresholds" "$F/README.md"
```

---

### T2 — Component A: helper-subprocess capture wrapper (~150 LoC)

- **Owner class:** `opus-implementer` (subprocess monkey-patching is mode-bearing infra; single bug here corrupts every Tier-1/2 assertion downstream).
- **Cycle estimate:** 1
- **Depends-on:** none (parallel with T1; T2 only needs the helper *paths* to exist, which WS-4 has already shipped).

**Inputs:**
- `ws3_synthesis.md` §6.2 Component A spec (~120–150 LoC; two modes — stub / real; mode set via `WS3_HELPER_MODE=stub|real`).
- `ws3_synthesis.md` §1 mechanism notes (Tier-1 captures argv + returns canned response keyed on argv; Tier-2 logs argv + lets real subprocess run; both modes write to the structured event log).
- WS-4 helper paths: `plugins/constraints/skills/dark-matter-constraints/scripts/{check_prereqs,detect_drake,extract_field,verify_router_field_contract}.py`.

**Outputs (NEW files):**

```
$P=$REPO/tests/dark_su3_playtest/
$P/__init__.py                        # Empty; package marker
$P/helper_subprocess_wrapper.py       # ~150 LoC — Component A
```

**API shape (binding):** the module exports

```python
# tests/dark_su3_playtest/helper_subprocess_wrapper.py
class HelperInvocation(typing.NamedTuple):
    helper_name: str          # one of {check_prereqs, detect_drake, extract_field, verify_router_field_contract}
    argv: list[str]           # full argv as captured (helper_path + args)
    returncode: int
    stdout: str
    stderr: str

class HelperSubprocessWrapper:
    def __init__(self, mode: typing.Literal["stub", "real"], canned_dir: pathlib.Path):
        ...
    def install(self) -> None:
        """Monkey-patches subprocess.run for the four helper paths."""
    def restore(self) -> None: ...
    @property
    def invocations(self) -> list[HelperInvocation]: ...

def stub_response_for(helper: str, argv: list[str], canned_dir: pathlib.Path) -> tuple[int, str, str]:
    """Pure function: maps (helper, argv) → (returncode, stdout, stderr) using files in canned_dir."""
```

**Stub-mode keying rule (binding):** the `stub_response_for` function dispatches by `(helper_name, scenario_id)` extracted from argv flags. Concretely:
- `check_prereqs --config <path> --model <name>` → look up `canned_dir/check_prereqs_<model>_<scenario>.json` (scenario inferred from config path leaf).
- `detect_drake --config <path>` → look up `canned_dir/detect_drake_<branch>.json` (branch inferred from config's `drake_path` value).
- `extract_field --json <path> --key <k> --schema-version <v>` → echo back the key from the JSON file (real read of canned JSON; no fabrication).
- `verify_router_field_contract` (no args) → return baseline `SUMMARY 14/4/0` shape.

**Real-mode shape:** wrapper logs argv + delegates to `subprocess.run(argv, capture_output=True, text=True)`; appends `HelperInvocation` to the log; returns the real `CompletedProcess`-equivalent.

**Mode env var:** `WS3_HELPER_MODE` ∈ `{stub, real}`. Default `stub`. Tier-1 always sets `stub`; Tier-2 sets `real`.

**Acceptance gates:**

```bash
W=$REPO/tests/dark_su3_playtest/helper_subprocess_wrapper.py
test -f "$W"
LOC=$(grep -cv '^\s*\(#\|$\)' "$W"); test "$LOC" -le 200   # ~150 LoC budget; 200 ceiling

# 1. Importable + API surface
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('hsw', pathlib.Path('$W'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert hasattr(m, 'HelperSubprocessWrapper'), m
assert hasattr(m, 'HelperInvocation'), m
assert hasattr(m, 'stub_response_for'), m
print('OK')
"

# 2. Stub mode: argv capture works for all 4 helpers
python - <<'EOF'
import importlib.util, pathlib, os
os.environ['WS3_HELPER_MODE'] = 'stub'
spec = importlib.util.spec_from_file_location('hsw', '$W')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
canned = pathlib.Path('$REPO/tests/fixtures/dark_su3_playtest/canned/pointA')
w = m.HelperSubprocessWrapper(mode='stub', canned_dir=canned)
w.install()
import subprocess
helpers = ['check_prereqs', 'detect_drake', 'extract_field', 'verify_router_field_contract']
for h in helpers:
    p = f'$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/{h}.py'
    subprocess.run(['python', p, '--help'], capture_output=True)
w.restore()
assert len(w.invocations) == 4, w.invocations
assert {i.helper_name for i in w.invocations} == set(helpers), w.invocations
print('OK 4/4 helpers captured')
EOF

# 3. Real mode: real subprocess actually runs (reuse WS-4-shipped --help)
WS3_HELPER_MODE=real python - <<'EOF'
# similar to above but mode='real'; assert returncode == 0 for --help
EOF
```

---

### T3 — Component B (transcript-event-log parser, ~150 LoC) + Component C (`--spec` pre-flight, ~30 LoC)

- **Owner class:** `opus-implementer` (Component B is tightly coupled to harness format; mistakes here create silent correctness bugs in every Tier-1/2 assertion).
- **Cycle estimate:** 1
- **Depends-on:** none (parser builds on `eval/harness/runners/claude_code.py` line 442+ format which is already on main; pre-flight reads SKILL.md whose path is fixed regardless of WS-4 content).

**Inputs:**
- `ws3_synthesis.md` §6.2 Component B + Component C specs.
- `ws3_synthesis.md` §7.2 Issue 4 (parser pinned to harness format AT a specific commit; documented in module top-of-file).
- `eval/harness/runners/claude_code.py` lines 442+ (transcript / metadata format).
- `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (target of Component C grep).

**Pinned harness commit hash (binding for Component B coupling):**

```
HARNESS_COMMIT_HASH = "<HARNESS_COMMIT_HASH_PLACEHOLDER>"
# Implementer fills in with $(git rev-parse HEAD) at task open.
# Authored at draft time against: a3374d41195ff455d61271a3b0203854e21c38a6
```

A module-level constant `HARNESS_COMMIT_HASH` in `transcript_event_log.py` MUST match the result of:

```bash
cd $REPO && git log -1 --format=%H -- eval/harness/runners/claude_code.py
```

at task-open time. Gate #4 below asserts this. If the harness format evolves, the parser bumps to `_v2.py` and the constant updates.

**Outputs (NEW files):**

```
$P/transcript_event_log.py            # ~150 LoC — Component B
$P/preflight.py                       # ~30 LoC — Component C
```

**Component B API (binding):**

```python
@dataclass(frozen=True)
class TranscriptEventLog:
    helper_invocations: list[HelperInvocation]   # ordered; reused from Component A
    file_reads: list[pathlib.Path]               # any file the LLM read
    decision_branches: list[str]                 # routing decisions surfaced in transcript prose
    merged_table: str                            # the rendered Markdown table block
    raw_transcript: str                          # full subprocess stdout for debug

def parse_transcript(harness_meta: dict, captured_invocations: list[HelperInvocation]) -> TranscriptEventLog:
    """Read claude_code.py line 442+ format from harness_meta; merge with captured invocations; return log."""
```

**Component C API (binding):**

```python
class SpecFlagMissingError(RuntimeError):
    code = "WS3_SPEC_FLAG_MISSING"

def preflight_spec_flag(skill_md_path: pathlib.Path) -> None:
    """grep -F -- '--spec' SKILL.md. Raise SpecFlagMissingError if absent.
    Runs BEFORE any LLM invocation; failure short-circuits the test."""
```

**Acceptance gates:**

```bash
B=$REPO/tests/dark_su3_playtest/transcript_event_log.py
C=$REPO/tests/dark_su3_playtest/preflight.py
test -f "$B" && test -f "$C"
LOC_B=$(grep -cv '^\s*\(#\|$\)' "$B"); test "$LOC_B" -le 200
LOC_C=$(grep -cv '^\s*\(#\|$\)' "$C"); test "$LOC_C" -le 50

# 1. Component B importable + dataclass + parse function
python -c "
import importlib.util, pathlib, dataclasses
spec = importlib.util.spec_from_file_location('tel', pathlib.Path('$B'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert dataclasses.is_dataclass(m.TranscriptEventLog), m
assert callable(m.parse_transcript), m
assert hasattr(m, 'HARNESS_COMMIT_HASH'), m
print('OK')
"

# 2. Harness commit hash pin matches main HEAD on the runner
PIN=$(python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('tel', pathlib.Path('$B'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.HARNESS_COMMIT_HASH)
")
LIVE=$(cd $REPO && git log -1 --format=%H -- eval/harness/runners/claude_code.py)
test "$PIN" = "$LIVE"   # If the harness moved, parser bumps to _v2

# 3. Component C: missing-flag SKILL.md raises SpecFlagMissingError
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

# 4. Component C: live SKILL.md (post-WS-4-T7) passes pre-flight
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('pf', pathlib.Path('$C'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.preflight_spec_flag(pathlib.Path('$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md'))
print('OK')
"

# 5. Component B parses a fixture transcript without crashing
# (golden transcript fixture authored as part of T1 if needed; otherwise dry run)
```

---

### T4 — Tier-1 dry-run + Tier-2 hybrid test bodies + retry-budget plumbing

- **Owner class:** `sonnet-implementer` (test-body authoring is mechanical once T1/T2/T3 land; the hard/soft assertion classes from synthesis §4 are precise).
- **Cycle estimate:** 1
- **Depends-on:** T1 (fixtures, golden artifacts, canned outputs) AND T2 (Component A) AND T3 (Components B + C). Coordinated with WS-4 T7 (rewritten SKILL.md) — the SKILL.md must exist before T4 runs end-to-end.

**Inputs:**
- `ws3_synthesis.md` §4.1 (HARD = single-shot pass-required; SOFT = retry budget 2 / 3 attempts total; 3-of-3 soft fail logged as warning).
- `ws3_synthesis.md` §4.2 (8 hard assertions + 4 soft assertions, enumerated).
- `ws3_synthesis.md` §4.3 (golden artifacts as gate spec, `_v1.json` versioning).
- `ws3_synthesis.md` §4.4 (single-sentence pass criterion).
- `ws3_synthesis.md` §7.2 Issue 1 (LLM agent system prompt — pinned: rewritten SKILL.md + fixture config.yaml + spec.yaml + minimal user-message envelope; NO project memory; NO global CLAUDE.md; NO unrelated SKILL.md).
- `ws3_synthesis.md` §7.2 Issue 3 (W4-D casing pin: literal `--key omega_h2` lowercase).

**Outputs (NEW files):**

```
$P/conftest.py                        # pytest fixtures, env var management, retry-budget runner
$P/test_playtest_tier1.py             # Tier-1 (default — runs in CI)
$P/test_playtest_tier2.py             # Tier-2 (pytest -m integration)
$P/_assertions.py                     # Shared HARD/SOFT assertion library (~80 LoC)
$P/README.md                          # Tier table + scenario inventory + how to run
```

**Test-matrix (binding — synthesis §4.4):**

| Scenario ID | Point | DRAKE branch | Hard assertions | Soft assertions |
|---|---|---|---|---|
| `pointA_configured` | A | `configured` | All 8 from §4.2 | All 4 from §4.2 |
| `pointA_found` | A | `found` | Steps 1–8 (DRAKE branch differs) | All 4 |
| `pointA_missing` | A | `missing` | Steps 1–8 + DRAKE_MISSING blocker | All 4 |
| `pointA_activation` | A | `activation_required` | Steps 1–8 + DRAKE_ACTIVATION_REQUIRED blocker | All 4 |
| `pointB` | B | (Step 5 NOT invoked) | Step 4 NOT invoked, Step 5 NOT invoked, table has 1 row populated, 3 rows `—` | Caveats prose names "off-resonance" or equivalent |

5 scenarios × Tier-1 + 5 scenarios × Tier-2 = 10 test-IDs. Each test runs ≥1 LLM attempt.

**Retry-budget mechanism (binding — synthesis §4.1):**

```python
# $P/conftest.py
def run_with_retry_budget(scenario_id: str, point: str, drake_branch: str | None,
                          tier: typing.Literal["tier1", "tier2"]) -> RetryResult:
    """
    Runs the playtest up to 3 attempts. Stops early if all hard assertions pass on attempt 1
    AND all soft assertions pass on attempt 1.

    Returns RetryResult with:
      hard_failures: list[(attempt, assertion_id)]   # attempt 1 only; later attempts not counted
      soft_results:  dict[assertion_id, passed_on_attempt | None]   # None ⇒ failed 3-of-3
    """
```

A test fails iff `len(hard_failures) > 0`. A 3-of-3 soft fail is logged via `pytest.warns(UserWarning, match=...)` shape and surfaces as a warning — does NOT gate.

**Pass criterion enforcement (binding — synthesis §4.4):** the test module's `pytest_terminal_summary` hook prints:

```
WS-3 PLAYTEST SUMMARY
  Hard: <n_pass>/<n_total> on attempt 1
  Soft: <n_pass>/<n_total> (passed_on_attempt distribution: {1: X, 2: Y, 3: Z, fail: W})
  Pass criterion: <PASS | FAIL>
```

PASS iff every hard assertion across the 5 scenarios passes on attempt 1 AND no soft assertion failed 3-of-3.

**LLM agent system-prompt isolation (binding — synthesis §7.2 Issue 1):**

```python
# In conftest.py — documented inline
PROMPT_ENVELOPE = {
    "skill_md": pathlib.Path("plugins/constraints/skills/dark-matter-constraints/SKILL.md"),
    "config":   "<scenario fixture config.yaml>",
    "spec":     "<scenario fixture spec.yaml>",
    "user_msg": "Run /dark-matter-constraints for darksu3 with --spec spec.yaml",
}
# Explicitly NO project memory, NO global CLAUDE.md, NO unrelated SKILL.md.
```

**Acceptance gates:**

```bash
T1=$REPO/tests/dark_su3_playtest/test_playtest_tier1.py
T2=$REPO/tests/dark_su3_playtest/test_playtest_tier2.py
A=$REPO/tests/dark_su3_playtest/_assertions.py
CF=$REPO/tests/dark_su3_playtest/conftest.py
test -f "$T1" && test -f "$T2" && test -f "$A" && test -f "$CF"

# 1. Test count: 5 scenario test functions per tier (parametrize OK)
python -c "
import re
for f in ['$T1','$T2']:
    src = open(f).read()
    ids = set(re.findall(r'(pointA_configured|pointA_found|pointA_missing|pointA_activation|pointB)', src))
    assert ids == {'pointA_configured','pointA_found','pointA_missing','pointA_activation','pointB'}, (f, ids)
print('OK')
"

# 2. Tier-2 marked with @pytest.mark.integration
grep -F "@pytest.mark.integration" "$T2"

# 3. Hard/soft assertion library exports both classes (synthesis §4.2)
python -c "
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location('a', pathlib.Path('$A'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert hasattr(m, 'HARD_ASSERTIONS') and len(m.HARD_ASSERTIONS) >= 8, m.HARD_ASSERTIONS
assert hasattr(m, 'SOFT_ASSERTIONS') and len(m.SOFT_ASSERTIONS) >= 4, m.SOFT_ASSERTIONS
print('OK', len(m.HARD_ASSERTIONS), len(m.SOFT_ASSERTIONS))
"

# 4. Retry-budget API in conftest
grep -F "run_with_retry_budget" "$CF"
grep -F "passed_on_attempt"     "$CF"

# 5. W4-D casing pin (synthesis §7.2 Issue 3): literal --key omega_h2 lowercase
grep -F -- "--key omega_h2" "$A"
! grep -F -- "--key OmegaH2" "$A"
! grep -F -- "--key omegaH2" "$A"

# 6. Tier-1 actually runs in stub mode (smoke — does not require a real LLM run; the
# wrapper is deterministic so a no-LLM golden replay is feasible if harness supports
# it; otherwise this gate is degraded to a collection-only check):
pytest --collect-only "$T1" -q | grep -E "test_.*\[pointA_configured\]"

# 7. Pass-criterion summary hook installed
grep -F "pytest_terminal_summary" "$CF"
grep -F "Pass criterion:" "$CF"

# 8. System-prompt isolation comment present (synthesis §7.2 Issue 1)
grep -F "NO project memory" "$CF"
grep -F "NO global CLAUDE.md" "$CF"
```

---

### T5 — Negative-control suite (4 sabotaged SKILL.md files) + Tier-3 smoke scaffold

- **Owner class:** `opus-implementer` (sabotage authoring requires reading the rewritten SKILL.md and selectively breaking specific lines to fail specific named hard assertions; mistakes here cause the meta-test to silently pass).
- **Cycle estimate:** 1
- **Depends-on:** T4 (the assertion library is what the negative-control parameters reference) AND WS-4 T7 (the rewritten SKILL.md is what gets sabotaged).

**Inputs:**
- `ws3_synthesis.md` §5 (4-sabotage menu, env override, parameterization shape).
- `ws3_synthesis.md` §1 Tier-3 row (real `/maddm` + `/micromegas` + `/drake-install detect`; ungated; `pytest -m smoke`).
- `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (POST-WS-4-T7 — source for sabotage edits).

**Outputs (NEW files):**

```
$F/negative_control/
  README.md                            # Sabotage menu table; what fails and why
  SKILL.md.broken_NC-1                 # Step 4b loses --schema-version flag
  SKILL.md.broken_NC-2                 # Step 4b loses sigma_v_zero extract_field invocation
  SKILL.md.broken_NC-3                 # "do NOT silently average" weakened to "may use MadDM if disagreement < 20%"
  SKILL.md.broken_NC-4                 # Invocation section drops --spec flag

$P/test_negative_control.py            # Parametrized over 4 sabotages; Tier-1 only
$P/test_playtest_tier3_smoke.py        # @pytest.mark.smoke; skips if real /maddm or /micromegas unavailable
```

**Sabotage-to-assertion map (binding — synthesis §5.2):**

| Sabotage | Edit | Expected hard-assertion fail |
|---|---|---|
| `NC-1` | `extract_field` invocation in Step 4b §2.1 has `--schema-version` arg removed | `extract_field_schema_version_arg` |
| `NC-2` | Step 4b §2.1 omits the `extract_field` invocation for `sigma_v_zero` | `extract_field_sigma_v_zero_invocation` |
| `NC-3` | "do NOT silently average" weakened (synthesis §5.2 wording) | `no_silent_winner_negative_regex` |
| `NC-4` | Invocation section (lines 20–35 of post-WS-4-T7 SKILL.md) drops `--spec` | `spec_flag_preflight` (Component C raises before LLM runs) |

**Env override (binding — synthesis §5.3):** `WS3_SKILL_OVERRIDE_PATH`. When set, harness loads the override path INSTEAD of the live SKILL.md. Default unset ⇒ live SKILL.md.

**Parameterization (binding — synthesis §5.4):**

```python
@pytest.mark.parametrize("sabotage_id,expected_fail_assertion", [
    ("NC-1", "extract_field_schema_version_arg"),
    ("NC-2", "extract_field_sigma_v_zero_invocation"),
    ("NC-3", "no_silent_winner_negative_regex"),
    ("NC-4", "spec_flag_preflight"),
])
def test_negative_control(sabotage_id, expected_fail_assertion, monkeypatch):
    monkeypatch.setenv("WS3_SKILL_OVERRIDE_PATH",
                       f"{FIXTURES}/negative_control/SKILL.md.broken_{sabotage_id}")
    result = run_playtest(point="A", drake_branch="configured", tier="tier1")
    assert expected_fail_assertion in [a for _, a in result.hard_failures]
```

**Tier-3 scaffold (binding — synthesis §1):**

```python
# test_playtest_tier3_smoke.py
@pytest.mark.smoke
@pytest.mark.skipif(not shutil.which("maddm-launcher"), reason="real /maddm unavailable")
@pytest.mark.skipif(not (FIXTURES/"ufo/darkSU3/dark_su3_real.ufo").exists(),
                    reason="real Dark SU(3) UFO not dropped into sentinel dir; see $F/ufo/darkSU3/README.md")
def test_smoke_pointA_real():
    """Runs /dark-matter-constraints with REAL /maddm + /micromegas + /drake-install detect.
    Ungated — informational only. Will be promoted to a gate in a follow-up shift."""
    result = run_playtest(point="A", drake_branch=None, tier="tier3")
    # No assertions; just write a structured artifact for human review
    write_smoke_artifact(result)
```

**Acceptance gates:**

```bash
NC=$REPO/tests/fixtures/dark_su3_playtest/negative_control
NCT=$REPO/tests/dark_su3_playtest/test_negative_control.py
T3=$REPO/tests/dark_su3_playtest/test_playtest_tier3_smoke.py

# 1. Four sabotage files exist + README enumerates them
test -f "$NC/README.md"
for id in NC-1 NC-2 NC-3 NC-4; do
  test -f "$NC/SKILL.md.broken_$id"
  grep -F "$id" "$NC/README.md"
done

# 2. Each sabotage actually differs from the live SKILL.md
LIVE=$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md
for id in NC-1 NC-2 NC-3 NC-4; do
  ! diff -q "$LIVE" "$NC/SKILL.md.broken_$id"   # MUST differ
done

# 3. NC-1: --schema-version absent in the broken file's Step 4b
! grep -F -- "--schema-version" "$NC/SKILL.md.broken_NC-1" | grep -F "extract_field" 2>/dev/null
# (Implementer ensures the broken Step 4b does not pair extract_field with --schema-version)

# 4. NC-4: --spec flag removed
! grep -F -- "--spec" "$NC/SKILL.md.broken_NC-4"

# 5. test_negative_control.py imports the parametrize set; uses env override
grep -F "WS3_SKILL_OVERRIDE_PATH" "$NCT"
grep -F "pytest.mark.parametrize" "$NCT"
for id in NC-1 NC-2 NC-3 NC-4; do grep -F "$id" "$NCT"; done

# 6. Tier-3 scaffold marked @pytest.mark.smoke and skipif-gated on real binaries + UFO
grep -F "@pytest.mark.smoke" "$T3"
grep -F "shutil.which" "$T3"
grep -F "real Dark SU(3) UFO not dropped" "$T3"

# 7. Tier-3 actually skips on this dev box (no real /maddm)
pytest -m smoke "$T3" -v 2>&1 | grep -E "SKIPPED|skipped"

# 8. Bell-rings: running the negative-control test against the LIVE SKILL.md (no override)
# must NOT trigger any expected failure (i.e. live SKILL.md is not accidentally sabotaged)
pytest "$NCT" -v --no-override 2>&1 | head   # Implementer adds a --no-override flag for this self-check
```

---

## 4. Sequencing diagram

```
Cycle 1 (parallel):    T1 (sonnet, fixtures + canned + golden)
                    ║  T2 (opus, helper subprocess wrapper, ~150 LoC)
                    ║  T3 (opus, transcript parser + spec pre-flight, ~180 LoC)
Cycle 2:              T4 (sonnet, Tier-1/2 test bodies + retry-budget plumbing)
                                — DEPENDS-ON T1 + T2 + T3 + WS-4 T7
Cycle 3:              T5 (opus, 4 sabotaged SKILL.md + Tier-3 scaffold)
                                — DEPENDS-ON T4 + WS-4 T7
Cycle 4:              Reviewer pass — every gate runs on the worktree branch
Cycle 5:              Hand-off + manager-decision write-up

Critical path:        T2 → T4 → T5  (1+1+1 = 3 cycles of work, plus T1+T3 parallel)
                      With reviewer + handoff: 5 cycles total. Ceiling: 6 (1 retry slot for T4 or T5).
```

**WS-4 dependency:** T4 and T5 cannot start until WS-4 T7 (rewritten SKILL.md) lands. Practically, T1/T2/T3 can be authored in parallel with WS-4's middle cycles; T4 opens the moment T7 lands.

---

## 5. Gate enumeration (code-level)

Each task's **Acceptance gates** block above is the canonical, runnable, code-level gate spec.

| Task | Sub-gate count | Notes |
|---|---|---|
| T1 | ~14 | UFO sentinel + spectrum locked numbers + canned outputs + golden artifacts + WS-1 reuse + categories disclaimer |
| T2 | ~6 | API surface + LoC budget + 4-helper argv capture in stub mode + real-mode passthrough |
| T3 | ~7 | Component B importable + harness-commit pin matches HEAD + Component C live SKILL.md passes + missing-flag raises |
| T4 | ~10 | 5 scenarios × 2 tiers + retry-budget API + W4-D casing pin + system-prompt isolation + pass-criterion hook |
| T5 | ~10 | 4 sabotage files exist + each differs from live + NC-1/NC-4 specific edits + parametrize + Tier-3 skipif |

**~47 mechanical sub-gates total.** No `wc -l > 0` claims; every gate has a content assertion.

---

## 6. Coordination

### 6.1 With WS-4 (in flight when T1/T2/T3 author; merged before T4 opens)

- **Helper paths.** WS-3 invokes `plugins/constraints/skills/dark-matter-constraints/scripts/{check_prereqs,detect_drake,extract_field,verify_router_field_contract}.py` via SKILL.md `python …/scripts/<name>.py …` strings (synthesis §1 mechanism). WS-3 does NOT modify these helpers.
- **SKILL.md content.** T4 + T5 require WS-4 T7 (the rewritten 180–230 line SKILL.md). T4 system-prompt isolation references the post-T7 file at the live path.
- **W4-D casing pin (synthesis §7.2 Issue 3).** WS-4 T7 lands `--key omega_h2` lowercase in the DRAKE branch; T4 hard assertion grep-asserts the lowercase form.
- **`--spec` flag.** WS-4 T7 lands `--spec` as a top-level invocation flag (no WS-4 T7 amendment requested per synthesis §7 row 6 + §8.1 — WS-3 owns the boundary check via Component C).
- **Sacrosanct labels.** T5 NC-* sabotages must NOT touch the 9 sacrosanct labels listed in WS-4 T7 §7 (those are WS-4 invariants; sabotage is about Step 4b prose, not headings).

### 6.2 With WS-2 (parallel, independent)

- WS-2 ships `tests/fixtures/spectra/{near_threshold_10pct,safe_above_10pct,near_resonance_5pct,safe_above_5pct}.json` + README. These are CONSUMED by WS-3 only insofar as the spectrum semantics (`mass_gap_fraction` etc.) inform `$F/specs/spec_pointA.yaml` field naming. WS-3 does NOT depend on WS-2 shipping for T1.
- WS-2's helper-direct unit tests (~42 functions) and WS-3's integration tests do NOT overlap; WS-2/WS-3 boundary holds (`ws2_synthesis.md` §6).

### 6.3 With WS-1 (merged on main)

- T1's Point A `maddm_stdout.txt` is a sed-patched copy of WS-1's `tests/fixtures/maddm/MadDM_results_synthetic.txt` (synthesis §7.1 item 9). Single source of truth for MadDM-format calibration.

### 6.4 Worktree branch

`ws-3-playtest`, off main, opened after WS-4 lands. T1/T2/T3 may pre-stage on a `ws-3-playtest-prep` branch and rebase forward when WS-4 merges; manager decides the merge strategy at WS-4 closeout.

---

## 7. Pre-flight risks

Implementer verifies each before opening tasks.

1. **Harness commit hash pinning.** Resolve `<HARNESS_COMMIT_HASH_PLACEHOLDER>` to `git log -1 --format=%H -- eval/harness/runners/claude_code.py` AT T3 task open. Update `transcript_event_log.py` `HARNESS_COMMIT_HASH` constant. Gate #4 of T3 enforces.
2. **WS-4 T7 SKILL.md exists.** T4 + T5 BLOCK if `plugins/constraints/skills/dark-matter-constraints/SKILL.md` is not at the post-T7 line-count band [180, 230] AND does not contain the 9 sacrosanct labels. Cheap pre-flight: run WS-4 T7 gate #1 and gate #8 from this branch.
3. **Empty-dir UFO sentinel.** Verify `$F/ufo/darkSU3/` exists as a directory and contains ONLY `README.md` + `.gitkeep`. Any stray `.py` file means a real UFO leaked in (Tier-1/2 must not touch UFO content).
4. **Spectrum-point lock.** All numeric values in `$F/specs/spec_point{A,B}.yaml` match synthesis §2 EXACTLY. Implementer does not "round" or "adjust." Gate T1#2 enforces.
5. **Direct-path helper invocations.** Following WS-4 §6 row 1, WS-3 does NOT use `python -m plugins…`. The Component A wrapper monkey-patches `subprocess.run` at the helper script paths.
6. **No `claude --temperature` flag.** Critic-verified at `eval/harness/runners/claude_code.py` line 475 (now line 469–485 in our local read). T4 retry-budget plumbing is the engineered response. Pre-flight asserts no `--temperature` token appears in the conftest's CLI builder.
7. **`HEPPH_DRAKE_DETECT_CMD` always stubbed in Tier-1/2.** Synthesis §7.1 item 10. Tier-3 alone may invoke real `install.sh detect`. Gate is `grep` in conftest for the env-var setup.
8. **No global CLAUDE.md leakage.** T4 system-prompt isolation comment ("NO project memory, NO global CLAUDE.md") MUST be honored — the prompt envelope passes ONLY the rewritten SKILL.md + fixture config + spec + minimal user message.
9. **WS-2 fixture independence.** T1 does NOT read `tests/fixtures/spectra/*.json`. The `$F/specs/spec_pointA.yaml` carries the spectrum (mass_gap, partner) values directly; cross-referencing WS-2's fixtures for naming is documentation-only.
10. **Tier-3 ungated.** Gate T5#7 asserts Tier-3 SKIPS on a CI-shaped host. Promotion to a gate is deferred to a future shift.
11. **Negative-control bell-ring.** Gate T5#8 asserts the parametrized test, run against the live (non-overridden) SKILL.md, does NOT report any expected failure — i.e. the live SKILL.md is not accidentally already sabotaged.

---

## 8. Out-of-scope (explicit)

WS-3 deliberately does NOT (synthesis §8):

- **Tier-3 gating.** Tier-3 ships as scaffold only.
- **WS-1 audit-row promotion.** `verified_against_synthetic` → `verified_against_real` is a follow-up shift's natural carrier.
- **Authoring a real Dark SU(3) UFO.** Empty-dir sentinel suffices; real UFO is dropped at Tier-3 invocation time.
- **WS-4 plan amendment** for a `grep -F -- '--spec' SKILL.md` gate (synthesis §7 row 6 + §8.1 — Component C catches the regression naturally).
- **Multi-LLM playtests.** Use the harness's existing Sonnet runner only.
- **Live `wolframscript` integration.** Tier-3 only.
- **Real Wolfram-license host variability.** Tier-3 deferral covers it.
- **Promotion of `read_maddm_output` / `read_drake_output` to helpers.** WS-4 §1.5 punts; WS-3 surfaces evidence in Tier-3 scaffolds but does NOT promote.
- **Asymmetric-DM, multi-component DM, Sommerfeld scenarios.** Not covered by Point A or Point B.
- **WS-1 manifest re-verification.** WS-3 surfaces drift in Tier-3 scaffolds; does NOT rewrite the manifest.
- **WS-2 helper unit tests.** WS-2's territory.
- **New helpers, new schemas.** WS-4's territory.
- **Real DRAKE Wolfram activation.** Deferred to a future shift.
- **CI-budget tuning.** Tier-1 calibration is impl-time work, not synthesis-binding.

---

## 9. Ready check

Predicates that must hold before T1 starts.

1. **WS-4 status.** Either WS-4 has merged (preferred), OR WS-4's helper paths are stable on a known branch and the implementer has read access:
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py`
2. **Harness format.** `eval/harness/runners/claude_code.py` exists and has the line-442+ format the synthesis pinned. Implementer captures HEAD commit hash.
3. **WS-1 synthetic fixture present** for T1 reuse (synthesis §7.1 item 9):
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt`
4. **Worktree branch** `ws-3-playtest` created (or `ws-3-playtest-prep` for pre-staging).
5. **Python deps.** `python -c 'import pytest, jsonschema'` exits 0; `claude` CLI in PATH (`which claude`).
6. **`git status` clean** for `tests/fixtures/dark_su3_playtest/` and `tests/dark_su3_playtest/` — neither directory exists yet (T1/T2 first to create).
7. **Implementer has read** `briefs/ROUTING_LENS.md`, `ws3_synthesis.md`, `ws4_plan_final.md`, `ws2_synthesis.md` §6, AND this plan end-to-end. No partial reads.

If any of items 1–6 fails, raise a blocker. Item 7 is verified by implementer discipline.

---

## Summary

5 tasks; cycle envelope **5 binding, 6 ceiling**; critical path T2 → T4 → T5; opus on T2 (helper subprocess wrapper), T3 (transcript parser + spec pre-flight), T5 (negative-control suite); sonnet on T1 (fixtures + golden) and T4 (test bodies + retry plumbing); WS-4 dependency on T7 SKILL.md content (T4/T5 only); harness-commit hash pinned via module constant in `transcript_event_log.py`; WS-2 fixture independence preserved; Tier-3 ungated.
