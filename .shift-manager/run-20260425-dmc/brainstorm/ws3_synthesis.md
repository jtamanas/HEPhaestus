# WS-3 Synthesis — Dark SU(3) End-to-End Playtest (final design)

**Synthesizer:** WS-3 brainstorm synthesizer
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md` (374 lines, locked); `brainstorm/ws3_propose.md` (149 lines); `brainstorm/ws3_critique.md` (158 lines, ACCEPT-WITH-MAJOR-REVISIONS); listing of `plugins/hep-ph-demo/skills/dark-su3/` (`benchmarks/` contains README.md only — 672 bytes; no UFO; verified); WS-1 fixture `tests/fixtures/maddm/MadDM_results_synthetic.txt` (referenced via critic §2 unknown 2).

**Verdict on critique:** ACCEPT all 11 items in critic §4. The proposer's hybrid-only collapse, single-spectrum pick, N=3 majority-rule, UFO symlink (factually impossible — no UFO exists), and silent assumption that the harness can pin temperature all need rework. This synthesis lands those reworks. WS-3's mandate stays the same: integration-test the rewritten SKILL.md prose against the WS-4 helpers using a Dark SU(3) spectrum. The mandate just costs more than the proposal admitted, so the scope tier is split and the harness extension is in-scope.

---

## 1. Final scope tier

**Tiered playtest** (replaces proposer's single-tier hybrid). Three tiers, each with different budget, fixture, and gating semantics. WS-3 ships Tier-1 + Tier-2 in this run; Tier-3 is scaffolded only.

| Tier | Pytest mark | When | Helpers | Physics tools | Gates? |
|---|---|---|---|---|---|
| **1 — Dry-run** | (default — no mark) | Every PR / CI | Stubbed at subprocess boundary; argv captured | Stubbed at subprocess boundary | **YES — hard gate** |
| **2 — Hybrid** | `pytest -m integration` | On-demand (manual / nightly) | **Real** (invoked via SKILL.md `python …/scripts/<name>.py` strings) | Stubbed via canned fixture files | **YES — hard gate** |
| **3 — Smoke** | `pytest -m smoke` | Manual, dev-only | **Real** | **Real** `/maddm` + `/micromegas` + `/drake-install detect` (and `/drake` if installed) | Scaffolded (no gate yet) |

Why tier rather than collapse: Tier-1 is the only thing CI can run cheaply and reliably; Tier-2 verifies the helpers under realistic config-path / manifest-path conditions; Tier-3 is the path that promotes WS-1 manifest rows from `verified_against_synthetic` to `verified_against_real`. Tier-3 is left as scaffold-only because (a) running real `/maddm` for a Dark SU(3) point is 5–15 min per branch (within budget but unsuitable for CI on the Wolfram-licensing host variance), (b) the WS-1 audit promotion is a separate workstream's natural carrier.

**Lens conformance.** Tiers 1 and 2 keep helpers (real) and physics tools (stubbed) cleanly separated. Helpers are deterministic+model-agnostic by WS-4 construction → safe to run for real. Physics tools are stubbed via canned fixtures explicitly tagged synthetic (per the user-emphasized "fixtures encode beliefs about producer outputs" lens rule). Tier-3 closes the synthetic→real gap when invoked.

**Tier-1 mechanism.** A subprocess shim wraps `subprocess.run` for the four helper paths. Each invocation captures argv, returns a canned response keyed on argv. Behavioral assertions read the captured argv list. NO real helper code runs in Tier-1. NO LLM nondeterminism on helper paths in Tier-1 — only on the LLM's decision to invoke at all and with what args.

**Tier-2 mechanism.** Real helper subprocesses run. Canned fixture JSON/text files are pointed at via `--config`, `--json`, `--manifest`. Helpers exit with real codes. The LLM walks the SKILL.md against these real outputs. This is what the proposer called "hybrid."

---

## 2. Spectrum points (locked numbers)

Two spectrum points (replaces proposer's single point — addresses critic Decision 2 and Missing FM-B "Step 5 NOT firing when triggers absent").

### Point A — DRAKE-narrow (on-resonance)

| Quantity | Value | Role |
|---|---|---|
| `m_chi` | **100 GeV** | DM candidate mass |
| `m_med` | **199 GeV** | Vector mediator mass |
| `Δ/(2m_χ)` | **0.005** | Inside 5% Step-5 narrow-resonance window |
| `Γ_med/m_med` | **0.005** (declared in fixture README; α_dark ~ 0.06 implied) | Documents that the resonance IS narrow; not just inside the heuristic window |
| Coannihilator partner | **m_partner = 105 GeV**, same conserved dark-charge as χ | Inside 10% Step-3 Trigger A window |
| Expected routing | Step 1 → Step 2 (MadDM) → Step 3 fires Trigger A → Step 4 (micrOMEGAs) → Step 5 fires (narrow-res < 5%) → DRAKE branch decision per `detect_drake` | All routing branches exercised |

Document Γ in fixture README. The critic correctly notes "inside the 5% window" is the router's heuristic, not a physical narrow-res statement; pin Γ/m_med so the playtest is testing both the router heuristic AND a physically-narrow case.

### Point B — Off-resonance control (negative-trigger)

| Quantity | Value | Role |
|---|---|---|
| `m_chi` | **100 GeV** | DM candidate mass (same as A) |
| `m_med` | **230 GeV** | Vector mediator mass — far off resonance |
| `Δ/(2m_χ)` | **0.15** | OUTSIDE 5% Step-5 window AND outside 10% Step-3 Trigger A window for med |
| `Γ_med/m_med` | **0.005** (declared; same width as A — pure mass offset is the variable) | — |
| Coannihilator partner | **NONE** (drop the partner from this fixture) | No Step-3 Trigger A fires |
| Expected routing | Step 1 → Step 2 (MadDM) → Step 3 NO triggers → Step 4 NOT invoked → Step 5 NOT invoked → relic-only output (MadDM Ωh² only) | Verifies LLM does NOT over-invoke |

This is the trigger-negative test. Without Point B, the playtest only proves "Step 5 fires when triggers say so" — it cannot prove "Step 5 does NOT fire when triggers say not-to." Half a test. Point B closes it.

**Both points use the same UFO substrate** (§3) — only `m_med`, presence/absence of partner, and canned-output content differ. Two parameter cards, one model definition.

---

## 3. UFO substrate — empty-dir sentinel (Option B)

**Decision: empty-dir sentinel.** The critic's Option B. Concrete shape:

```
tests/fixtures/dark_su3_playtest/
  ufo/
    darkSU3/                       # EMPTY directory + README.md sentinel
      README.md                    # 1-paragraph: "synthetic sentinel for router playtest;
                                   #  no real UFO; never read by any real tool in Tier-1/Tier-2"
```

The sentinel directory is committed to git via `.gitkeep` (or the README satisfies the same role). `config.yaml` sets `models.darksu3.ufo_path` to point at this absolute path. `check_prereqs` only asserts the path EXISTS as a directory (per WS-4 §1.1 manifest dispatch type `path_or_bool`); it does NOT inspect contents. WS-3 helpers and the LLM never read the UFO contents in Tier-1 or Tier-2. In Tier-3 (real `/maddm`), the user must drop a real Dark SU(3) UFO into this dir — documented in the fixture README and in Tier-3 `pytest -m smoke` skip-message prose.

**Why not Option A (synthetic UFO).** ~150 LoC of UFO Python is real new scope for zero routing-test value. The router does not parse UFOs.

**Why not Option C (singlet-doublet rebrand).** Manager locked Dark SU(3); breaks Profumo Fig. 8 framing.

**Why not the proposer's symlink.** Critic verified `plugins/hep-ph-demo/skills/dark-su3/benchmarks/` contains only `README.md` (672 bytes) — there is no UFO to symlink. The README itself forbids committing numeric benchmarks for dark-su3. Symlink plan is factually impossible.

**Distinct concern (cited and dismissed):** the `benchmarks/README.md` says "plan gates MUST NOT inline numeric thresholds for dark-su3." WS-3 fixture content (Ωh² = 0.135 in canned MadDM stdout, etc.) is FIXTURE INPUT driving the router's rel-diff arithmetic, not a gate threshold ("the answer must be X"). Distinct categories. The WS-3 plan-drafter must call this out in the plan task description so a reviewer doesn't conflate the two.

---

## 4. Verification structure

**Hard / soft assertion split + retry budget on soft.** Replaces proposer's N=3 majority. Critic's Decision-4 counter-proposal, accepted.

### 4.1 Assertion classes

| Class | What it asserts | Retry semantics | Examples |
|---|---|---|---|
| **HARD** | The agent invoked helper X with args matching shape Y; helper exit code; merged-output table has exactly 4 rows; `--spec` flag present in invocation; named blocker code present | **Single-shot pass-required.** Fail on first try ⇒ test fails. NO retry. | `check_prereqs --model darksu3` was invoked; `extract_field` was called with `--schema-version relic/v1`; merged table has 4 observable rows; `CROSSCHECK_DISAGREEMENT` code is in transcript |
| **SOFT** | Specific phrasing in caveats; rationale prose mentions a concept; error-message wording | **Retry budget = 2** (3 attempts total). Pass on attempt K logged as `passed_on_attempt=K`. Soft assertions do NOT gate the test (informational). | Caveats section mentions the rel-diff value to ≥1 sig-fig; rationale prose explains DRAKE four-branch decision; SLHA-hint prose names the model class |

**Why this is statistically cleaner than N=3 majority.** A real bug fails the hard assertion every attempt regardless of N. A flake (paraphrase miss) fails the soft assertion in 1 of 3 attempts; the retry surfaces the flake rate as a logged metric (`passed_on_attempt`) so the team can decide whether to harden the prose or the assertion. N=3 majority hides the flake rate.

**Retry budget mechanism.** The harness wrapper records each attempt's hard-pass / soft-pass results and emits a structured event log. The pytest test fails iff any HARD assertion failed on attempt 1 OR all 3 attempts failed for a soft assertion that was at retry-3. Soft-assertion 3-of-3 fail logs as a warning, not a fail (because nondeterminism beyond 3-of-3 means real degradation, surface to dev for review but don't gate CI on prose-level flake).

**Temperature pinning.** Confirmed not possible — `claude` CLI exposes only `--model`. Critic-verified at `eval/harness/runners/claude_code.py` line 475. Synthesis accepts: temperature is best-effort, the hard/soft split + retry budget is the engineered response, NOT a coping mechanism for a missing flag.

### 4.2 What's hard vs soft per scenario

Per Point × Tier matrix (Tier-1 + Tier-2 each run both points; Tier-3 scaffolded only):

**HARD assertions (every scenario):**
1. **Step ordering invocation** — captured argv list shows helper invocations in expected order (check_prereqs → extract_field calls → detect_drake when applicable).
2. **Helper invocation arg shape** — `check_prereqs --model darksu3 --config <fixture>`; `extract_field` for `omega_h2` against `relic.json` with `--schema-version relic/v1`; same for `sigma_v_zero` / `annihilation/v1`; `detect_drake --config <fixture>` IFF Step 5 fired.
3. **Helper exit code** — every helper invocation returned exit 0 OR returned exit 1 with the specific contract-failure code expected for that scenario (NOT exit 2 — that's an internal error and should fail the test).
4. **Branch correctness** — given a fixture's `drake_path` setting + canned `detect_drake` output, the LLM hit the expected DRAKE branch (or didn't invoke DRAKE at all if Point B).
5. **Merged-output table structure** — exactly 4 observable rows (Ωh², σ_SI, σ_SD, ⟨σv⟩); DRAKE column present iff Point A; cells `—` for absent values; named blocker codes appear in Caveats section.
6. **Flag correctness** — Point A canned values (Ωh² MadDM=0.135, micrOMEGAs=0.118 → 14.4% rel-diff > 10%) MUST emit `CROSSCHECK_DISAGREEMENT`.
7. **`--spec` flag survives** — see §6 negative pre-flight (also covered there).
8. **No silent winner** — negative regex `(?i)(average of|we'll go with|ignore the disagreement|let's use the .* result)` MUST NOT match transcript; positive regex `(rel-diff|FLAG|ADJUDICATION REQUIRED|CROSSCHECK_DISAGREEMENT)` MUST appear when disagreement fixture is loaded (Point A only).

**SOFT assertions:**
- Caveats section contains rel-diff numeric value to ≥1 sig-fig.
- Rationale prose for DRAKE branch decision exists and references the four branches (paraphrase-tolerant via concept-keyword set).
- Step 3 spectrum analysis prose mentions Δ/(2m_χ) value or equivalent ratio.
- SLHA-hint handling: for Point A (Dark SU(3) simplified-model) the hint MUST be treated as informational, NOT fatal — soft because the prose carrying the judgment may paraphrase.

### 4.3 Golden artifacts

`golden/` is a **gate spec referenced by hard assertions, not a debug aid only.** Critic Gap A.

```
tests/fixtures/dark_su3_playtest/golden/
  expected_step_trace_v1.json       # Sequence of expected helper invocations + arg shapes (per point)
  expected_blockers_v1.json         # Map: scenario_id -> [blocker_codes_expected]
  expected_table_structure_v1.json  # Required table rows, columns, '—' cells per scenario
  expected_merged_table_pointA.md   # Pretty-printed reference for HUMAN diff (NOT a verbatim gate)
  expected_merged_table_pointB.md   # Same, for Point B
```

`_v1.json` versioning convention (per critic Gap A): if the WS-4 contract evolves, golden artifacts bump to `_v2.json` and the assertion code dispatches on schema_version. Eliminates silent drift between the test gate spec and the helpers under test.

### 4.4 Pass criterion (single sentence — critic §3 issue 5)

**WS-3 passes iff every HARD assertion across all scenarios (2 points × 4 DRAKE-branch fixtures for Point A + 1 fixture for Point B = 5 total scenarios) passes on attempt 1, AND no SOFT assertion fails 3-of-3 attempts (3-of-3 fail is an informational warning surfaced in test output).**

The 4 DRAKE-branch fixtures for Point A correspond to `configured` / `missing` / `activation_required` / unset — already in the proposer's design — and verify the four-branch detect_drake routing.

---

## 5. Negative-control fixture spec (concrete)

Critic Gap C. The proposer waved at "deliberately-broken SKILL.md fixture"; this synthesis pins the spec.

### 5.1 Path

```
tests/fixtures/dark_su3_playtest/negative_control/
  SKILL.md.broken                    # Modified copy of the live SKILL.md with one specific sabotage
  README.md                          # Documents the sabotage (which line(s) edited, what hard
                                     # assertion is expected to fail, and why)
```

### 5.2 Sabotage menu (parameterized)

The negative-control test is parameterized over a small set of sabotages. Each sabotage targets a distinct hard assertion:

| Sabotage ID | Edit to SKILL.md.broken | Expected hard-assertion fail |
|---|---|---|
| `NC-1` | Step 4b §2.1 prose with `--schema-version` arg removed from the `extract_field` invocation | "extract_field called with `--schema-version relic/v1`" — fails because LLM omits the flag |
| `NC-2` | Step 4b §2.1 prose mentions only `omega_h2` extract (annihilation `extract_field` invocation removed) | "extract_field called for sigma_v_zero" — fails (FM-1) |
| `NC-3` | Step 4b §2.1 prose's "do NOT silently average" sentence weakened to "you may use MadDM if disagreement < 20%" | No-silent-winner negative regex fires |
| `NC-4` | Invocation section (lines 20–35) collapses `--spec` flag out | `--spec` pre-flight (§6) blocks before any LLM run; gate fails at scenario load |

### 5.3 Env override

Harness reads `WS3_SKILL_OVERRIDE_PATH` env var. When set, the harness loads the override path INSTEAD of the live `plugins/constraints/skills/dark-matter-constraints/SKILL.md`. Default unset → live SKILL.md. Pytest parametrization sets the env var per sabotage and asserts the named hard assertion fails.

### 5.4 Parameterization shape

```python
@pytest.mark.parametrize("sabotage_id,expected_fail_assertion", [
    ("NC-1", "extract_field_schema_version_arg"),
    ("NC-2", "extract_field_sigma_v_zero_invocation"),
    ("NC-3", "no_silent_winner_negative_regex"),
    ("NC-4", "spec_flag_preflight"),
])
def test_negative_control(sabotage_id, expected_fail_assertion):
    os.environ["WS3_SKILL_OVERRIDE_PATH"] = f"<fixture>/negative_control/SKILL.md.broken_{sabotage_id}"
    result = run_playtest(point="A", drake_branch="configured")
    assert result.hard_assertions_failed == [expected_fail_assertion]
```

The negative-control suite is its own pytest module (`tests/test_dark_su3_negative_control.py`), parameterized over the 4 sabotages, runs Tier-1-only (no need to burn Tier-2 budget on sabotaged runs).

**This bell rings.** If the playtest is trivially passing (LLM ignores SKILL.md, makes plausible-looking output anyway), all 4 negative controls fail to fail — the meta-test catches that condition.

---

## 6. Harness-extension scope — IN WS-3

Critic Unknown 1. Decision: **in WS-3 scope, not deferred.** Costs more than the proposer admitted, but deferring it downgrades WS-3 to scaffolding-only and the run produces no actual gate. The harness extension is the load-bearing infra without which the playtest doesn't exist.

### 6.1 What exists already

`eval/harness/` contains `run.py`, `loader.py`, `graders.py`, `outcome.py`, `report.py`, `runners/{base.py, claude_code.py, reference.py}`. Drives `claude --model <name>` subprocesses; captures stdout/stderr; supports golden-output testing via `runners/reference.py`. Verified by critic.

### 6.2 What's missing — three components

**Component A — Helper-subprocess capture wrapper (~120 LoC).** Intercepts the four WS-4 helper invocations (`check_prereqs`, `detect_drake`, `extract_field`, `verify_router_field_contract`). Two modes:
- **Tier-1 (stub mode):** Every helper invocation goes through the wrapper, which captures argv and returns a canned response keyed on argv (canned response files in fixture dir).
- **Tier-2 (real mode):** Wrapper logs the argv but lets the real subprocess run; captures stdout / stderr / exit code into the event log.

The wrapper is a small Python module in `tests/dark_su3_playtest/` (alongside fixtures). Mode is set via `WS3_HELPER_MODE=stub|real` env var.

**Component B — Transcript-event-log parser (~150 LoC).** Reads the `claude` subprocess's transcript output (per `eval/harness/runners/claude_code.py` lines 442+ format), parses helper invocations, file reads, decision-tree branch decisions, and merged-output Markdown into a structured `TranscriptEventLog` dataclass. Hard / soft assertions run against this dataclass. Tightly coupled to the harness transcript format — critic §3 issue 4. Pinning the parser to the harness format is documented in the WS-3 plan.

**Component C — `--spec` pre-flight gate (~30 LoC).** Reads `plugins/constraints/skills/dark-matter-constraints/SKILL.md`, asserts `--spec` flag string is present at top-level invocation. Runs BEFORE any LLM invocation. If the flag is absent, the test fails with `WS3_SPEC_FLAG_MISSING` and skips downstream assertions. This is the WS-3-side resolution to critic §2 Unknown 3 (see §7 below for routing of the T7 gate question).

**Total harness extension: ~300 LoC.** In line with critic's "200–400 LoC" estimate.

### 6.3 Files

```
tests/dark_su3_playtest/
  conftest.py                        # pytest fixtures, env var management
  helper_subprocess_wrapper.py       # Component A
  transcript_event_log.py            # Component B
  preflight.py                       # Component C
  test_playtest_tier1.py             # Tier-1 hard/soft assertions, both points × DRAKE branches
  test_playtest_tier2.py             # Tier-2 (pytest -m integration); same shape, real helpers
  test_playtest_tier3_smoke.py       # Tier-3 (pytest -m smoke); real /maddm + /micromegas
  test_negative_control.py           # §5.4
```

### 6.4 Why not deferred

If WS-3 ships only fixtures + golden artifacts and defers the harness extension, no gate fires and the run produces no signal. WS-3's whole purpose is integration-testing the rewritten SKILL.md prose AGAINST the WS-4 helpers under realistic conditions. The harness extension IS the integration test. Defer it and you defer WS-3.

The cost (300 LoC + ~2 task-cycles) is real but manageable within WS-3's mandate. Plan-drafter splits the harness extension into ~3 dedicated tasks (one per component) so cycle budget is explicit.

---

## 7. 7-item adjudication

| # | Item (from prompt) | Decision | Rationale |
|---|---|---|---|
| 1 | Tier playtest (dry-run / hybrid / real) — don't collapse | **Tier-1 dry-run (CI default) + Tier-2 hybrid (`pytest -m integration`) + Tier-3 smoke scaffold (`pytest -m smoke`)** per §1 | Critic Decision-1: hybrid alone can't promote WS-1 audit rows AND is too expensive for CI. Tiers split the cost / fidelity tradeoff cleanly. Tier-3 scaffolded but ungated keeps the future promotion path open without burning cycles now. |
| 2 | Off-resonance Point B for trigger-negative testing | **Confirmed.** Point A: m_χ=100, m_med=199, partner=105, Γ/m_med=0.005. Point B: m_χ=100, m_med=230, no partner, Γ/m_med=0.005. Per §2. | Critic Decision-2: single point only proves "Step 5 fires when triggers say so" — half a test. Point B closes the trigger-negative side. Pinning Γ/m_med in fixture README documents the resonance is physically narrow, not just inside the heuristic window. |
| 3 | Empty-dir UFO sentinel — concrete shape | **`tests/fixtures/dark_su3_playtest/ufo/darkSU3/` directory + README.md sentinel; `check_prereqs` asserts dir exists; UFO contents never read in Tier-1/Tier-2.** Per §3. | Critic Decision-5 verified the proposer's symlink plan is impossible (no UFO in `plugins/hep-ph-demo/skills/dark-su3/benchmarks/`, only a README forbidding numeric benchmarks). Empty-dir is the cheapest correct answer; matches WS-1's synthetic-fixture convention. |
| 4 | Hard/soft assertion + retry budget (replace N=3 majority) | **HARD = single-shot pass-required (no retry); SOFT = retry budget 2 (3 attempts total), 3-of-3 fail logged as warning not gate.** Per §4. | Critic Decision-4: temperature pinning verified impossible (`claude` CLI exposes only `--model`). N=3 majority is a coping mechanism that hides flake rate and conflates real bugs with paraphrase misses. Hard/soft split surfaces the flake metric while keeping real-bug detection deterministic. |
| 5 | Negative-control fixture spec (path, env override, parameterization) | **Path: `tests/fixtures/dark_su3_playtest/negative_control/SKILL.md.broken_{NC-1..NC-4}`. Env override: `WS3_SKILL_OVERRIDE_PATH`. Parameterization: 4 sabotages × 1 hard-assertion-each pytest cases (Tier-1 only).** Per §5. | Critic Gap C: "negative control exists" is unverifiable without spec. Pinning the file path, env var, and per-sabotage expected-fail mapping makes the bell ring concretely. 4 sabotages cover the 4 most likely SKILL.md regressions. |
| 6 | T7 gate amendment ask vs WS-3 pre-flight | **WS-3 pre-flight (Component C, §6.2). Do NOT request WS-4 plan amendment.** Both `--spec` presence AND a `grep -F -- '--spec' SKILL.md` style check live in `tests/dark_su3_playtest/preflight.py`. | Critic Unknown 3: WS-4 plan is locked at 8 tasks / 5 cycles. Amending T7 to add the gate costs WS-4 plan rework (manager-level decision) and risks unblocking-cascading other WS-4 cycles. WS-3 owns the boundary check naturally — it's the integration test. WS-3 pre-flight catches `--spec` drop AT scenario load with `WS3_SPEC_FLAG_MISSING` before any LLM cost is paid. Cost of NOT amending T7: a future PR could land an SKILL.md edit that strips `--spec` and only WS-3 catches it (not the WS-4 unit-tests). Acceptable: WS-3 IS the integration boundary, that's exactly its job. |
| 7 | Harness-extension scope (in WS-3 or deferred) | **In WS-3 scope. ~300 LoC, ~3 dedicated tasks.** Per §6. | Critic Unknown 1: harness extension does not exist; WS-3 cannot ship gates without it. Deferring downgrades WS-3 to scaffolding-only and produces no signal in this run. The 300 LoC is below the critic's 200–400 estimate; manageable within WS-3's mandate. |

### 7.1 Plus the additional critic items folded in

The critic's §4 list runs to 11 items; the prompt asked for 7 explicit. The remaining 4 are folded into the synthesis above:
- **Item 8 (failure modes A–E added):** Helper-path drift (catches via Tier-1 argv assertion), default-observable preamble (Tier-1 hard assertion "table has exactly 4 rows"), Caveats section omitted (Tier-1 hard assertion "Caveats section exists"), `--spec` drop (Component C pre-flight per item 6), schema files not packaged (Tier-2 hard assertion "extract_field exit code != 2 (no internal error)"). All landed in §4.2 hard-assertion list.
- **Item 9 (reuse WS-1 `MadDM_results_synthetic.txt`):** Confirmed; Point A and Point B canned MadDM stdout fixtures are sed-patched copies of the WS-1 synthetic. Single source of truth for MadDM-format calibration.
- **Item 10 (Tier-1 stubs `HEPPH_DRAKE_DETECT_CMD`; real-detect Tier-3 only):** Confirmed; Tier-1 always sets `HEPPH_DRAKE_DETECT_CMD` to a deterministic stub. Tier-2 also stubs (canned-fixture mode). Tier-3 invokes the real `install.sh detect`.
- **Item 11 (pass criterion):** Confirmed and pinned in §4.4.

### 7.2 New issues from critic §3

- **Issue 1 (LLM agent system prompt):** Pinned. The harness invocation provides the rewritten `SKILL.md` content + the fixture `config.yaml` + the fixture `spec.yaml` + a minimal user-message envelope (`"Run /dark-matter-constraints for darksu3 with --spec spec.yaml"`). NO project memory, NO global CLAUDE.md, NO unrelated SKILL.md. Documented in `tests/dark_su3_playtest/conftest.py` prose.
- **Issue 2 (DRAKE detect side effects):** Confirmed; per item 10. Tier-1 always stubs.
- **Issue 3 (W4-D casing pin):** Confirmed; hard assertion uses literal `--key omega_h2` (lowercase, with underscore). NOT `OmegaH2` or any normalization.
- **Issue 4 (transcript parser format coupling):** Confirmed; Component B is locked to `eval/harness/runners/claude_code.py` line 442+ format AT the rewrite hash. Documented at the top of `transcript_event_log.py`. If the harness format evolves, the parser bumps to `_v2`.
- **Issue 5 (pass criterion):** Pinned per §4.4.

---

## 8. Out-of-scope and WS-4 amendment requests

### 8.1 No WS-4 plan amendment requested

WS-3 does NOT request the WS-4 T7 amendment that the critic raised as a possibility (`grep -F -- '--spec' SKILL.md` gate added to T7). Routing per item 6: WS-3 owns the boundary check via Component C pre-flight. WS-4 plan stays locked at 8 tasks / 5 cycles. No manager-level coordination cost.

The cost the synthesizer accepts in trade: a future PR landing an SKILL.md edit that strips `--spec` would be caught by WS-3 (the integration test), NOT by WS-4 unit tests. This is the correct division of labor — unit tests verify helper invariants, integration tests verify end-to-end prose contracts. WS-3 IS the integration test.

### 8.2 Out-of-scope (explicit)

- **Tier-3 gating.** Tier-3 ships as scaffold-only (`pytest -m smoke` infrastructure exists; tests skip if real `/maddm` or `/micromegas` aren't available). Promotion of WS-1 audit rows from `verified_against_synthetic` to `verified_against_real` is the natural carrier in a follow-up run, not WS-3 of this run.
- **Authoring a real Dark SU(3) UFO.** Empty-dir sentinel suffices. A real UFO is needed for Tier-3; deferred to that follow-up.
- **Multi-LLM playtests.** WS-3 uses the harness's existing Sonnet runner (`runners/claude_code.py`). Comparing routing behavior across Opus / Sonnet / Haiku is out of scope.
- **Live `wolframscript` integration.** Tier-3 only, scaffold only.
- **Real Wolfram-license host variability.** Tier-3 deferral covers it; Tier-1 / Tier-2 always stub `HEPPH_DRAKE_DETECT_CMD`.
- **Promotion of `read_maddm_output` / `read_drake_output` to helpers.** WS-4 §1.5 explicitly punts this; WS-3 surfaces evidence (in Tier-3 scaffolds) but does NOT itself promote.
- **Asymmetric-DM, multi-component DM, Sommerfeld-enhanced ⟨σv⟩ scenarios.** Not covered by Point A or Point B; Dark SU(3) is symmetric thermal relic.
- **WS-1 manifest re-verification.** WS-3 does NOT itself rewrite WS-1's manifest (per WS-4 §8). It surfaces drift in Tier-3 scaffolds for a follow-up.
- **CI-budget tuning.** Tier-1 is intended to be cheap (subprocess stubs, no real LLM calls if the harness runs in golden-replay mode). Calibrating the Tier-1 budget on real hardware is plan-drafter / impl work, not synthesis-binding.

### 8.3 What survives from the proposer

- **Hybrid scope concept** — survives as Tier-2.
- **Behavioral-assertions-over-structured-trace** — survives as the §4.2 HARD assertion class.
- **Golden artifacts as referenced gate spec** — survives, but with `_v1.json` versioning convention added.
- **Four DRAKE-branch fixtures for Point A** — survives.
- **Six failure-mode list** — survives, expanded to 11 (FM-A through FM-E from critic §1 issue 6 added).
- **Reuse `plugins/hep-ph-demo/skills/dark-su3/SKILL.md` for orientation only** — survives.
- **Don't reuse `practitioner_script.md` or `summary.schema.json`** — survives.

### 8.4 Closing routing-lens conformance check

WS-3 honors the routing lens at every layer:
- **Helpers** (real in Tier-2, stubbed in Tier-1) ARE deterministic + model-agnostic per WS-4 construction. WS-3 exercises them as black-box subprocess calls — it doesn't second-guess their logic.
- **Canned fixtures** (MadDM stdout text, micrOMEGAs JSONs, DRAKE Wolfram stdout) ARE explicitly tagged synthetic; documented in fixture READMEs as "encoding beliefs about producer outputs"; promoted to real-output via Tier-3 only.
- **LLM judgment** (rel-diff arithmetic, threshold judgment, model-class skip rules per WS-4 §2) is the SUBJECT under test, not the test mechanism. Behavioral assertions verify the LLM is exercising its judgment in the right places, not that it produces a specific judgment.
- **Empty-dir sentinel** matches the lens hard constraint: WS-3 cannot guarantee a real Dark SU(3) UFO works for any router-relevant question; the sentinel keeps UFO-content concerns OUT of the routing test, where they belong.

The synthesis is consistent with WS-4 synthesis §7.3 (WS-3 import boundary), the routing lens's hard constraint on model-agnosticism, and the critic's 11 items. The plan-drafter mechanically translates §1, §2, §3, §4, §5, §6 into tasks; the binding adjudications are §6 row 6 (no WS-4 amendment), §6 row 7 (harness in-scope), and §3 (empty-dir sentinel).
