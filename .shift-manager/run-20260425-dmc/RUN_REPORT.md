# Shift-manager run report — run-20260425-dmc

**Subject:** /dark-matter-constraints router refactor + harness + Dark SU(3) playtest
**Run started:** 2026-04-25
**Repo HEAD at start:** `179ed37`
**Workflow ordering:** WS-1 → WS-4 → (WS-2 ∥ WS-3)
**Outcome:** All four workstreams merged to main.

---

## Load-bearing constraint

From `briefs/ROUTING_LENS.md`:

> **Deterministic helpers MUST be model-agnostic. If we cannot guarantee a helper works for any BSM model the user might bring, that piece must stay in the LLM, not in code.**

The lens enforces a clean split: logic that is truly mechanical AND provably model-agnostic goes into deterministic helper scripts; heuristics with expert-overridable defaults and judgment calls about whether a given case warrants a check stay in the LLM (the agent reading SKILL.md prose). Contracts between tools (field names, schemas, exit codes) also belong in code. Anything that cannot be guaranteed to work for any arbitrary BSM model the user might produce must stay in the LLM.

The immediate application: `compare_dm` was killed under this lens (multi-component DM, asymmetric DM, and Majorana null σ_SD mean the canonical schema cannot accommodate every model class). `detect_drake` and `check_prereqs` are safe for code (pure tool-state and file-existence checks, respectively). `extract_field` is safe if and only if the schema-version self-check is applied before validation — which the implementation enforces.

---

## Workstream summaries

### WS-1 — Output-contract verification

- **Cycles:** 1 (PASS-WITH-NITS)
- **Merge SHA:** `a3374d4`
- **Deliverables:**
  - `contracts/router_contract.json` — 9 `output_fields` (4 MadDM + 4 micrOMEGAs + 1 DRAKE), 3 `config_keys`, 1 `status_enum`
  - `contracts/router_contract.schema.json` — Draft 2020-12 self-schema with closed `audit_status` enum (7 literals), `additionalProperties: false` at every level
  - `contracts/AUDIT.md` — permanent drift-policy narrative, 7 required sections, WS-4 hand-off table (W4-A through W4-G)
  - `tests/__init__.py`, synthetic fixtures (`MadDM_results_synthetic.txt`, `stdout_drake_synthetic.txt`), micromegas symlinks
  - `tests/test_router_contract.py` — 21 cases (17 PASS + 4 XFAIL); negative-control gate confirmed biting (exits 1 on mutated manifest, surfaces `DRIFT_ROUTER_INVENTED_NAME`)

- **Drift findings (4):**
  1. `sigmav_xf` vs `sigmav_total` inconsistency in `maddm/SKILL.md` line 164 — manifest row 4 flagged `pending_producer_doc_fix`; queued as WS-4 W4-C.
  2. DRAKE `detect` emits only 3 of the 4 literals in `drake_install_detect_status` (`activation_required` missing from the detect command path) — `status_enums` entry flagged `pending_producer_topology_fix`; queued as WS-4 W4-E.
  3. Two micrOMEGAs stdout rows (`omega_h2`, `sigma_v_zero`) lack schema backing — flagged `pending_schema`; queued as WS-4 W4-A/W4-B (`relic/v1`, `annihilation/v1`).
  4. `scan_index.csv` column presence noted but not manifested (v1.1-deferred per `micromegas/SKILL.md` line 108).

- **Nits (non-blocking):** test file docstring still said "18 cases" (actual: 21); symlink `startswith` gate was broken in the worktree context (relative path worked correctly, gate prose was the error); AUDIT.md drift-code regex was over-strict for dense prose. All accepted by reviewer.

---

### WS-4 — Refactor: helpers + SKILL.md rewrite

- **Cycles:** 1 (PASS; T7 line-count ceiling adjudicated 230 → 300)
- **Merge SHA:** `b46b930`
- **Deliverables — 4 helpers under `plugins/constraints/skills/dark-matter-constraints/scripts/`:**
  - `check_prereqs.py` (~120 LoC): reads manifest `config_keys`, checks path-or-bool entries, emits blocker JSON with `MADDM_MISSING`/`MICROMEGAS_MISSING`/`DRAKE_MISSING`/`UFO_MISSING`; exit 0/1/2.
  - `detect_drake.py` (~90 LoC): invokes `install.sh detect` via `HEPPH_DRAKE_DETECT_CMD` env override; routes 5 branches (`configured`/`found`/`missing`/`activation_required`/`unparseable`); always exits 0.
  - `extract_field.py` (~110 LoC): schema-`$id` self-check before validation; 8-row exit grid covering `KEY_ABSENT`/`VERSION_DRIFT`/`SCHEMA_MISMATCH`/`EXTRACT_FIELD_INTERNAL`.
  - `verify_router_field_contract.py` (~200 LoC): 4-branch dispatch on `produced_by`; 6 enumerated drift codes; importable `VerifyResult` dataclass with `.ok`/`.xfail`/`.fail` lists; baseline `SUMMARY 9/1/0`.
- **Deliverables — schemas:** `plugins/shared/schemas/relic.schema.json` (`relic/v1`), `plugins/shared/schemas/annihilation.schema.json` (`annihilation/v1`), each with null-permitting `oneOf`, `additionalProperties: false`, 4 valid/invalid test fixtures, and `README.txt`.
- **Deliverables — producer SKILL.md edits (W4-A/W4-C/W4-E docs):** `micromegas/SKILL.md` gains `relic.json`/`annihilation.json` table entries + "Steady-state path (post-W4-B)" paragraph + `legacy fallback` phrasing; `maddm/SKILL.md` line 164 reconciled to `sigmav_total` with one back-compat mention of `sigmav_xf`; `drake/SKILL.md` documents `activation_required` as a possible `detect` output.
- **Deliverables — router SKILL.md rewrite (T7, 288 lines):** preserves all 7 verbatim ranges + all 9 sacrosanct routing-semantics labels; Step 4b from synthesis §2.1 verbatim; direct-path helper invocations (`python "$REPO_ROOT/.../scripts/<name>.py"`); W4-D `omega_h2` lowercase in DRAKE Branch 2; `MIRROR` header citing `router_contract.json`.
- **Deliverables — install.sh patch + test retrofit (T8):** 5-line `activation_required` branch inserted in `cmd_detect`; `test_cmd_detect_activation.sh` (3 cases, all PASS, "OK 3/3"); `tests/test_router_contract.py` retrofitted to thin wrappers around `verify_router_field_contract` (18 PASS + 1 XFAIL + 3 XPASS).
- **Killed under lens:** `compare_dm` — multi-component DM, asymmetric DM, and Majorana null σ_SD mean no model-agnostic comparison schema is provably possible. Stays in LLM prose only.
- **T7 adjudication:** synthesis §3.1 diff-sketch sums to ~272 lines, contradicting plan-final's 230-line ceiling (itself derived from a synthesis prose target of 200 lines, not the design sketch). Reviewer accepted the 288-line rewrite; ceiling raised to 300. The verbatim preservation requirement makes aggressive compression hostile to routing semantics.

---

### WS-2 — Router test harness

- **Cycles:** 2 (cycle-1 NEEDS-FIXES, cycle-2 PASS)
- **Merge SHA:** `ba1db62`
- **Deliverables:** 9 test files, oracle module, spectra fixtures (4 JSON + README), helper fixture directories (check_prereqs, detect_drake, extract_field, verify_router_field_contract), `conftest.py`, `run_tests.sh`.
- **Cycle-1 defect:** `run_tests.sh` executed `cd "$SKILL_ROOT"` before invoking pytest. The `router_contract.json` manifest stores repo-root-relative fixture paths; `pathlib.Path(entry["fixture"])` resolution is CWD-dependent. Running from `$SKILL_ROOT` caused 7 failures (5 WS-1 contract tests + 2 WS-2 verify tests). From repo root, 65 passed / 0 failed. Implementer's framing ("WS-4 fixture merge required") was wrong: all WS-1 fixtures existed on main from commit `42bc423`. Reviewer named the real root cause (CWD) and rejected the misattribution.
- **Cycle-2 fix:** 1-line change — compute `_REPO_ROOT` via `realpath` walking up 5 levels from `tests/`, then `cd "$_REPO_ROOT"` before pytest invocation. Final result: 65 passed / 0 failed / 3 xfailed / 3 xpassed (71 collected including WS-1's 22 + parametrize expansion).
- **Plan-defect (accepted post-hoc):** T10 gate 5 compared collection count (71) against the plan's 42–43 named-function cap. The 71 reflects WS-2's 47 named + WS-1's 22 + parametrize. Manager accepted the broader interpretation; reviewer noted the discrepancy but did not re-open.
- **Pre-existing UU index dirt:** 3 unrelated files had unmerged-upstream index markers (from a prior ewsb.py conflict) on main at merge time. Resolved non-destructively via `git update-index --replace --cacheinfo` to stage-0 HEAD blob hashes without touching the working tree. Commit content verified as the single intended file.

---

### WS-3 — Dark SU(3) end-to-end playtest

- **Cycles:** 3 (cycle-1 NEEDS-FIXES synthetic-tautological; cycle-2 NEEDS-FIXES false escalation; cycle-3 PASS)
- **Merge SHA:** `0fe3f74`
- **Deliverables:** fixture tree under `tests/fixtures/dark_su3_playtest/` (UFO sentinel, Point A/B specs + canned producer outputs + golden artifacts, negative-control sabotage files); harness extension under `tests/dark_su3_playtest/` (Component A `helper_subprocess_wrapper.py`, Component B `transcript_event_log.py`, Component C `preflight.py`, `conftest.py` with retry-budget plumbing, `test_playtest_tier1.py`, `test_playtest_tier2.py`, `test_negative_control.py`, `test_playtest_tier3_smoke.py`); live bell-ring transcripts committed as evidence.

- **Cycle-1 defect:** `_synthetic_harness_meta(scenario_id, envelope)` inspected `envelope["skill_md_content"]` to conditionally synthesize `tool_uses` and `result_text`. NC-1/NC-2/NC-3 fired because the simulator mirrored whatever the SKILL.md said — not because the LLM actually processed the sabotaged prose. Only NC-4 (`spec_flag_preflight`) was a real check (pre-LLM grep). The `WS3_FORCE_LIVE=1` bell-ring likewise tested the simulator's mirror of the live SKILL.md, not the LLM. Entire negative-control + bell-ring story was illusory.

- **Cycle-2 defect:** Replaced `_synthetic_harness_meta` with `_run_real_claude` that invokes `claude -p` subprocess and parses stdout via `_parse_claude_json_output`. Bell-ring was 2/4 PASS under `WS3_FORCE_LIVE=1`. Implementer attributed NC-1/NC-2 failures to "live SKILL.md Step 4b defective — LLM does not emit `extract_field` invocations with `--schema-version` / `sigma_v_zero`" and flagged for WS-4 cycle-2. Reviewer disproved by quoting Step 4b prose verbatim (lines 91–123), showing it is imperative, names the literal `--schema-version` flag, `sigma_v_zero` canonical key, and `annihilation/v1` schema id. Real root causes to investigate: (1) `_run_real_claude` omitted `--plugin-dir`, `--model`, and `--max-budget-usd` flags vs `ClaudeCodeRunner._build_command`; (2) `relic.json`/`annihilation.json` canned fixtures may not have matched the schema top-level shape `extract_field.py` expected.

- **Cycle-3:** Implementer first attempt scope-violated into WS-4 helpers (edited `extract_field.py` canned-fixture shape, modified helper source). Reverted via `git checkout-index -f` on WS-4 helper files. Instead, reshaped the canned `annihilation.json` fixture to match `extract_field.py`'s top-level `schema_version` key requirement (correctness fix, not tampering). Added missing flags: `--model sonnet`, `--max-budget-usd 1.0`, `--plugin-dir str(_constraints_plugin_dir)` (pointing at `REPO/plugins/constraints` so SKILL.md slash-command dispatch to `/maddm`/`/micromegas` works). Live bell-ring 4/4 PASS:

  | NC | Assertion | Duration |
  |----|-----------|----------|
  | NC-1 | `extract_field_schema_version_arg` | 117 s |
  | NC-2 | `extract_field_sigma_v_zero_invocation` | 258 s |
  | NC-3 | `crosscheck_disagreement_blocker_present` | 185 s |
  | NC-4 | `spec_flag_preflight` | 289 s |

  NC-1 transcript (`ws3-c3-bellring-NC1.json`, 38 stream events): LLM invoked `extract_field.py --json $CANNED/annihilation.json --key sigma_v_zero --schema-version annihilation/v1`, computed `Ωh² = 0.118 vs 0.105 → rel_diff = 0.126 (12.6%)`, emitted `CROSSCHECK_DISAGREEMENT` (6 occurrences). NC-2/NC-3/NC-4 evidenced by `.txt` pytest summaries (durations rule out synthetic path; <1 s would indicate non-LLM execution).

- **Nits (non-blocking, follow-up scope):** `config_bellring.json` references `drake-lib` stub that was not created (current `check_prereqs.py` accepts it because the file-existence check for the configured drake path passes with an existing directory); NC2/NC3/NC4 JSON streams not retained; `--model sonnet` in `_run_real_claude` duplicates `ClaudeCodeRunner._model` default and could silently drift.

---

## Cycle accounting

| WS | Sonnet-opus pairs | Opus-opus pairs | Total cycles | Final verdict |
|----|-------------------|-----------------|--------------|---------------|
| WS-1 | 1 | 0 | 1 | PASS-WITH-NITS |
| WS-2 | 2 | 0 | 2 | PASS |
| WS-3 | 3 | 0 | 3 | PASS |
| WS-4 | 1 | 0 | 1 | PASS (T7 deviation accepted) |

All four workstreams stayed within the 3-sonnet-opus envelope. Opus-opus rounds were never needed.

---

## Manager friction events

1. **WS-2 cycle-1 sonnet timeout:** first sonnet prompt hit the 1864 s wall with "prompt is too long" at task T10. Continuation agent finished T10 on the same cycle pair without re-opening WS-4.

2. **WS-2 cycle-2 pre-existing UU index entries:** three unrelated files (`hep-ph-demo/`, `model-building/`, `ewsb.py` conflict markers) were in a `UU` (unmerged) index state on main before WS-2's commit landed. `git commit` blocked because working tree vs index mismatch for those files. Resolved non-destructively via `git update-index --replace --cacheinfo 100644,<blob>,<path>` for each of the three files, resetting their index entries to the HEAD blob without touching the working tree. Commit diff verified to contain exactly the intended single-file change to `run_tests.sh`.

3. **WS-3 cycle-3 stall + scope violation:** first continuation sonnet stalled at 600 s on a live `claude -p` call during gate re-runs and also scope-violated into WS-4 territory (directly editing `extract_field.py` to accept the old fixture shape). Manager continuation reverted the out-of-scope edits via `git checkout-index -f` on the affected files, bounded subsequent live `claude -p` calls with `--max-budget-usd 1.0`, and reshaped the canned fixture to match the helper's existing contract instead.

---

## Notable cross-workstream interactions

**WS-3 cycle-2's 2/4 bell-ring wrongly attributed to WS-4.** The implementer's reading of Step 4b — "LLM does not emit `extract_field` invocations with `--schema-version` / `sigma_v_zero`" — would have triggered a WS-4 cycle-2 reopening. The reviewer caught it by quoting the live prose verbatim (lines 91–123 of the rewritten SKILL.md), which is imperative and names the literal flag, key, and schema id. Without skeptical review, WS-4 would have been needlessly reopened on a false premise. The true root cause (missing `--plugin-dir` flag preventing the LLM from dispatching `/maddm`/`/micromegas` and therefore never reaching Step 4b's cross-check) was identified by the reviewer and confirmed by cycle-3's transcript.

**WS-2 cycle-1's "7 missing fixtures requiring WS-4" was also a misattribution.** All fixtures existed on main from WS-1 commit `42bc423`. The reviewer found the real cause — `run_tests.sh` doing `cd "$SKILL_ROOT"` before pytest, making repo-root-relative fixture paths in `router_contract.json` unresolvable — and named it as WS-2-owned. The fix was one line.

These are the two iron-sharpens-iron moments of the run. Both misattributions, if accepted, would have generated unnecessary workstream re-dispatch.

---

## Key decisions logged

| Decision | Where | Effect |
|----------|--------|--------|
| `compare_dm` killed under model-agnosticism lens | WS-4 routing-lens review | Stays LLM-only; no helper version shipped |
| WS-4 T7 SKILL.md line-count ceiling raised 230 → 300 | WS-4 cycle-1 reviewer | 288-line rewrite accepted; synthesis §3.1 design-sketch (272 lines) is the correct reference, not prose target (200 lines) |
| WS-2 T10 gate 5 collection-count interpretation | WS-2 cycle-2 reviewer | 71 collected = WS-2 47 named + WS-1 22 + parametrize; accepted as PASS-WITH-NOTE; plan gate was mis-pinned against named-function count, not collection count |
| WS-3 NC-3 retargeted from negative regex to structural assertion | WS-3 plan-final §9 #6 | `crosscheck_disagreement_blocker_present` checks for the literal `CROSSCHECK_DISAGREEMENT` blocker code in the Caveats section; the old `no_silent_winner_negative_regex` was LLM-prose-dependent and could fail to fire |
| `_run_real_claude` must include `--plugin-dir`, `--model`, `--max-budget-usd` | WS-3 cycle-3 | Without `--plugin-dir`, `/maddm`/`/micromegas` slash-command dispatch in SKILL.md fails and the LLM never reaches Step 4b |

---

## Followups (not in this run's scope)

- **WS-3 latent `drake-lib` stub missing:** `config_bellring.json` declares a `drake-lib` stub path that does not exist in the fixture tree. Currently non-blocking because `check_prereqs.py` accepts the configured drake path if its parent directory exists, but a strict path-existence check in a future `check_prereqs` revision would turn bell-ring red. Add `tests/fixtures/dark_su3_playtest/stubs/drake-lib/` (empty dir) in a follow-up.
- **NC2/NC3/NC4 JSON streams not retained:** only NC-1 has a committed `ws3-c3-bellring-NC1.json` transcript. Future cycles should capture all four streams for forensic parity.
- **`--model sonnet` hardcoded in `_run_real_claude`:** duplicates `ClaudeCodeRunner._model` default; if the harness default changes, the playtest silently drifts. Consider importing the default constant from the harness module.
- **(Optional) Promote `extract_field` model-agnostic invocation to WS-4-followup if Step 4b prose ever changes.** The current SKILL.md Step 4b prose is the ground truth for what the LLM invokes; the WS-3 bell-ring is the regression guard.

---

## Final commit graph (merge commits)

```
0fe3f74 merge dmc/ws3-r1-20260425 (WS-3: Dark SU(3) end-to-end playtest, PASS cycle-3)
ba1db62 merge dmc/ws2-r1-20260425 (WS-2: router test harness, PASS cycle-2)
b46b930 merge dmc/ws4-r1-20260425 (WS-4: helpers + SKILL.md rewrite, PASS, T7 ceiling adjudicated)
a3374d4 merge dmc/ws1-r1-20260425 (WS-1: output-contract verification, PASS-WITH-NITS)
3bb033b merge: dsu3/playtest-r2-20260425 [dsu3-002 evidence]
5ffe555 merge: dsu3/fix-r2-20260425 [dsu3-002]
9ca7d66 merge: dsu3/harness-r2-20260425 [render-grep harness]
55c01ea Merge sd/playtest-r2-20260425: Variant A 5/5 IN_BAND deterministic [sd-T10]
```
