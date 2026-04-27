# WS-4 Plan Critique — Refactor: helpers + SKILL.md rewrite

**Critic:** ws4-plan-critic
**Plan under review:** `plan/ws4_plan_draft.md` (734 lines, 8 tasks)
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md`; `plan/ws4_plan_draft.md`; `plan/ws1_plan_final.md`; `plugins/constraints/skills/dark-matter-constraints/SKILL.md`; `plugins/constraints/skills/micromegas/SKILL.md` (lines 99/207/226 region); `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (line 164); `plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 84–86); `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (lines 100–142); `plugins/monte-carlo-tools/skills/drake-install/tests/test_detect.sh` (existing convention); `plugins/constraints/skills/micromegas/tests/` (pytest convention).

---

## 1. Verdict

**ACCEPT-WITH-CHANGES.** The plan is mostly sound, transcribes synthesis §1–§8 with high fidelity, and gates are runnable and specific (the T4 row-by-row exit grid and T7 git-blob preserve-verbatim are particular strengths). But three structural defects need synthesizer resolution before implementer dispatch: (a) the WS-1 BLOCK semantics on T5/T8 are too binary and wedge the run if WS-1 needs-fixes; (b) the W4-D defer-to-T7 punt is correct but T6's gate is silent on it (need a positive assertion that W4-D has landed somewhere); (c) the cycle-envelope hedge "4 or 8" is unbinding and must be committed.

Eight tasks is the right count. Cutting further would conflate independent risk surfaces; splitting further would drop below cycle granularity. T4 and T7 are correctly opus-routed; T5 should be reconsidered (see §2 T5).

---

## 2. Per-task review (T1–T8)

### T1 — Schemas (relic + annihilation + 4 fixtures)

**Status:** Strong. ACCEPT.

- Cycle 1, sonnet: correct. JSON bodies are verbatim from synthesis §5.
- Gates exercise: parse, `$schema`, `$id` pin, `additionalProperties:false`, `schema_version` const, v→0 description string, oneOf [null, number], jsonschema cross-validation positive AND negative.
- The cross-validation gate in §T1 acceptance gate #7 is properly two-directional — positive fixtures validate, negative fixtures fail. This is the hardest single gate to get right in the plan and it's done correctly.
- **Minor nit:** the negative fixtures (`relic_invalid_extra_field.json`, `annihilation_invalid_negative.json`) need their failure modes named in synthesizer notes. "Invalid extra field" tests `additionalProperties:false`; "negative" tests `minimum:0` on `omega_h2` or `sigma_v_zero`. Implementer can infer, but adding a one-line comment to each fixture would prevent the implementer from making them invalid for a different reason than intended.
- **Could split?** No — schemas + their fixtures form a single coherent unit. Splitting buys nothing.

### T2 — `check_prereqs.py`

**Status:** ACCEPT.

- Cycle 1, sonnet: correct. ~120 LoC argparse + manifest dispatch.
- Gates exercise happy + blocker + internal-error paths and check the JSON shape.
- Subtle: gate uses `sed -i.bak` which works on macOS but creates a `.bak` file. Not a defect, just noisy.
- **Missing gate:** no test for the `SLHA_MISSING_HINT` hint blocker. Synthesis §1.1 calls it out as the one model-aware nuance. Add a row that fabricates a config WITHOUT `latest_slha` and asserts the JSON contains a hint blocker (not a hard blocker). Synthesizer must resolve.
- **Note on `__init__.py`.** T2 outputs include `scripts/__init__.py` (empty). Synthesis §1 explicitly says helpers are invoked via direct path because no `__init__.py` chain exists. Adding `__init__.py` here is harmless but inconsistent — it implies the dir is a package, which it isn't (parent dirs lack `__init__.py`). The implementer is reading this for `importlib`-loadability but that's not how `spec_from_file_location` works (it doesn't need `__init__.py`). Drop the `__init__.py` output. Synthesizer must resolve.

### T3 — `detect_drake.py`

**Status:** ACCEPT.

- Cycle 1, sonnet: correct.
- Gate cleverly stubs the detect command via `HEPPH_DRAKE_DETECT_CMD` env var across 5 status branches. Good.
- **Defect:** the `printf '#!/bin/bash\nprintf %%s %q\n' "$OUT" > "$STUB"` line in the gate is fragile — `%q` quoting interacts badly with multi-line shell heredocs, and on a JSON string with double quotes the `printf %s %q` path is hard to predict. Replace with `cat <<EOF > "$STUB"` heredoc form. Implementer concern, not a fail.
- The `unparseable` branch is critical (it's the synthesis-§1.2 drift path) and it IS gated. Good.

### T4 — `extract_field.py` (LOAD-BEARING)

**Status:** ACCEPT. Linchpin; opus-routing correct.

- 7-row exit grid each gated row-by-row. This is exactly right.
- **Defect:** Row 5's gate (schema-`$id` self-check) uses `--schema-root "$TMP/badroot"` containing only `relic.schema.json`. But `extract_field` may try to load `annihilation.schema.json` or `scattering.schema.json` first depending on dispatch order. Synthesizer must lock that the `--schema-version <id>` arg deterministically picks the schema file (e.g. `<schema-root>/<basename>.schema.json` where basename is the prefix of `<id>` before `/`). Otherwise the implementer is free to do `os.listdir(schema_root)` and match — which works for the gate but is non-deterministic.
- **Missing gate:** no `present-null AND schema disallows null` case. If a future schema removes `oneOf [null,...]`, present-null should fall to `SCHEMA_MISMATCH` (row 6), not row 1 or row 2. Add a gate.
- **Could T4 be sonnet?** The plan routes to opus citing "load-bearing primitive." I disagree mildly: the spec is fully nailed in synthesis §1.3; sonnet can transcribe. But the plan-drafter's caution is reasonable — getting null-vs-absent wrong silently breaks every router invocation. Accept opus.

### T5 — `verify_router_field_contract.py`

**Status:** ACCEPT-WITH-CHANGES.

- Cycle 2, opus: drafter argues "4-branch dispatch + 6 drift codes." Reasonable but inflated.
- **Re-route candidate.** Sonnet can author this if the spec is precise — and it is, in synthesis §1.4 + WS-1 plan §5. The drift-classification ladder is enumeration, not judgment. The 4 branches are: `agent_parsed` → regex over fixture; `summary_json` → JSON pointer + jsonschema; `stdout_regex` → regex over symlinked stdout fixture; `install_detect_json` → enum subset check (only enum value, not output_field row, but T5's `verify` covers both). Each is mechanical. **Synthesizer must resolve:** sonnet vs opus for T5.
- **Defect — WS-1 BLOCK indefinite.** T5 BLOCKS on WS-1 main merge. Plan §6.1 says "If WS-1 has not landed, T5/T8 BLOCK." But WS-1 may NEEDS-FIXES for an unrelated reason (e.g. T4 audit prose) and stay unmerged for cycles. The right shape is: T5 starts at the FIRST cycle where WS-1's manifest+test files exist on the WS-4 worktree's base (whether that's main or a WS-1 branch); manager re-dispatches on WS-1 merge events, NOT continuously. Synthesizer must specify the unblocking signal precisely.
- **Defect — importable surface gate.** Gate uses `importlib.util.spec_from_file_location` and asserts `r.ok / r.xfail / r.fail` are present. Good. But doesn't assert the dataclass `VerifyResult` is the shape synthesis §1.4 specifies. The wrapper test (T8) imports the function and uses `.ok / .xfail / .fail` lists — gate this in T5 directly so T8's shape can be trusted.

### T6 — Producer SKILL.md edits (W4-A / W4-C / docs portion of W4-E)

**Status:** ACCEPT-WITH-CHANGES.

- Cycle 1, sonnet: correct. Mechanical search-and-replace.
- **Defect — W4-D defer.** T6 explicitly defers W4-D to T7 to avoid edit collision. This is the right call (§3 below adjudicates), but T6 has NO gate that checks "W4-D landed somewhere." T7's gate #5 (`grep -F "omega_h2" "$S"`) is the safety net. Synthesizer must explicitly tag W4-D as a T7 deliverable so the WS-4 reviewer doesn't lose it between tasks.
- **Defect — `COUNT_XF` gate.** Line 426: `test "$COUNT_XF" -le 1   # at most one mention (the back-compat note)`. But synthesis §4 W4-C says "plus a one-sentence backward-compat note" — meaning `sigmav_xf` SHOULD appear once in the back-compat note. The gate `<=1` allows 0 or 1, but should require EXACTLY 1: too few means the back-compat note was dropped (silently breaking users still using `sigmav_xf`); too many means the canonical name wasn't replaced. Tighten to `test "$COUNT_XF" -eq 1`.
- **Missing positive content gate for W4-A Edit 3.** Gate uses `grep -E "steady.state|legacy" -i "$MM"`. Soft. Should also assert a phrase from the proposer §5 wording (synthesis §4 says "verbatim per proposer §5 W4-A Edit 3"). Synthesizer must surface proposer's exact phrase so the gate can assert it (e.g. `grep -F "post-W4-B steady state"` or whatever the canonical phrase is).

### T7 — Router SKILL.md rewrite (HIGHEST JUDGMENT)

**Status:** ACCEPT.

- Cycle 2, opus: correct. The single highest-judgment task in WS-4.
- Gate #2 (preserve-verbatim via `git show HEAD:`) is the cleverest gate in the whole plan. Solid. But:
  - **Edge case:** if T7 runs in a worktree where `HEAD` is not the same as the synthesis-time hash, gate #2 reads the wrong baseline. Gate #2 must run in a worktree whose `HEAD` is the pre-T7 state. This is the implicit contract; needs to be explicit. Synthesizer: spell out "T7 implementer creates a checkpoint commit BEFORE editing, so `git show HEAD~1:` gives the pre-edit content; or use `git stash` → diff → restore." Without this discipline, gate #2 can silently pass on garbage.
- Gate #3 substring-tests synthesis §2.1 verbatim. Good. Note: the synthesis Step 4b block uses `python "$REPO_ROOT/...` with curly bash quoting — when extracted from synthesis with regex, whitespace can drift. The substring assertion handles it but only if synthesis §2.1's exact prose is preserved. Implementer must NOT reflow.
- Gate #4 grep-asserts `python -m plugins` is absent. Good (locks synthesis §6 row 1).
- **Missing smoke gate:** WS-3 will exercise the rewritten SKILL.md prose end-to-end. If T7 changes the routing semantics (e.g. inverts a decision-tree branch), WS-3 fails. Add a "routing-semantics preservation" gate: list the decision-tree branches that must survive (Step 1 outcome → Step 2 vs blocker; Step 5a outcome → which branch). Spot-check by grep-asserting the literal branch labels survive verbatim. Synthesizer must list which branch labels are sacrosanct.

### T8 — `install.sh` 5-line bash + WS-1 test retrofit

**Status:** ACCEPT-WITH-CHANGES.

- Cycle 1, sonnet: correct.
- **W4-E unit-test fixture location.** Plan picks `plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh`. Verified: the directory `drake-install/tests/` exists and contains `test_detect.sh` + `fixtures/` already. Bash test is the right form (matches existing convention in that skill). pytest+subprocess.run would be inconsistent with this skill's existing tests. **ACCEPT bash form.**
- **Defect — bash-test fakes/mocks.** T8's gate runs `"$TS"` and asserts exit 0. But what does `test_cmd_detect_activation.sh` actually do? It needs to: (a) fake `wolfram_path` to return a path, (b) fake `is_drake_dir` to return true, (c) fake `run_smoke` to emit `{"status":"activation_required",...}`, then (d) call `cmd_detect` and grep stdout for `activation_required`. Synthesizer must specify the test's body shape, not just its filename. The plan punts this to the implementer — too much rope.
- **Defect — `pytest "$TR"` gates assume pytest discovery works.** No `conftest.py` is shipped. WS-1's plan §6 risk #2 already calls this out — implementer must verify `pytest` runs from repo root in the harness env. T8 should inherit that assumption explicitly.
- The `! grep -F 'jsonschema.Draft202012Validator' "$TR"` gate (line 576) is brittle: a comment string mentioning that class would fail the gate. Tighten to `! grep -E 'jsonschema\.Draft202012Validator\(.+\)\.validate'` (assert the call form, not the bare name).

---

## 3. Gate audit

| Concern | Status | Action |
|---|---|---|
| `extract_field` 7-row exit grid | All 7 rows gated | Add 8th row: present-null AND schema disallows null → SCHEMA_MISMATCH |
| Schema cross-validation positive+negative | Concrete fixtures pinned | Tag failure modes (extra-field for relic, negative for annihilation) |
| SKILL.md preserve-verbatim "byte-for-byte" | Uses `git show HEAD:` substring-equality | Specify HEAD-baseline discipline (pre-edit checkpoint) |
| W4-E bash test distinguishes 3 statuses | Plan punts to implementer | Synthesizer specifies fake/mock shape |
| W4-D landed | T7 gate #5 | Explicitly tag W4-D as T7-owned in plan §3 (currently buried in §Pre-flight item 3) |
| `sigmav_xf` count | `<=1` | Tighten to `==1` |
| W4-A Edit 3 wording | Soft `grep -i "steady.state\|legacy"` | Synthesizer surfaces proposer's exact phrase |
| Importable surface dataclass shape | T5 gate checks `.ok / .xfail / .fail` | Add gate asserting the dataclass type, not just attribute presence |
| SLHA_MISSING_HINT path in `check_prereqs` | Ungated | Add hint-blocker gate |
| Routing-semantics preservation in T7 | No explicit gate | Add: list sacrosanct branch labels and grep them |

---

## 4. Open-issue adjudications (3 items)

### 4.1 W4-D placement (deferred into T7 vs separate edit task)

**Decision: DEFER TO T7. CONFIRMED.**

The drafter's reasoning is correct: W4-D is a 1-line edit at line ~213 of the file being rewritten in T7. Running W4-D as a standalone T6 sub-task creates an edit-collision risk (T6 edits line 213, T7 rewrites the file and may or may not preserve the edit). The clean shape is: T7 incorporates W4-D as a non-negotiable element of the rewrite, gated by `grep -F "omega_h2" "$S"` in T7 acceptance gate #5.

**But** synthesizer must add explicit language in T7's "Authoring discipline" section: "W4-D MUST land at Step 5 Branch 2: name DRAKE's Ωh² field as `omega_h2` and route comparison through `extract_field --schema-version relic/v1`." Currently this is buried at item #4 of the discipline list and easy to miss. Promote it to a dedicated step.

### 4.2 W4-E unit-test fixture location and form

**Decision: BASH FORM at `drake-install/tests/test_cmd_detect_activation.sh`. CONFIRMED.**

Verified: `drake-install/tests/` exists with `test_detect.sh` (existing bash convention) + `fixtures/`. Adding a sibling `test_cmd_detect_activation.sh` matches local convention. pytest+subprocess.run would diverge from the convention used in this same skill. Bash test reliably distinguishes the three statuses by shelling `cmd_detect` with stubbed `run_smoke` and grep-checking the JSON output.

**But** synthesizer must specify the test's body shape (not just filename):

1. Source `install.sh` to bring `cmd_detect` into scope.
2. Stub `run_smoke` as a shell function emitting `{"status":"activation_required","path":"…"}`.
3. Stub `wolfram_path` to echo a path; stub `is_drake_dir` to return 0; stub `config_get drake_path` to echo a fake dir.
4. Call `cmd_detect`; capture stdout; assert grep matches `"status":"activation_required"`.
5. Repeat for `status:"ok"` (expect `configured`) and the fall-through case (expect `found`).

Without this body spec, the implementer ships a half-test.

### 4.3 Cycle envelope (4 parallel vs 8 sequential)

**Decision: BIND TO 5 CYCLES.** Not 4 (drafter's optimistic), not 8 (drafter's pessimistic).

Rationale:
- **Cycle 1 (parallel):** T1 + T2 + T3 + T6 (sonnet ×4 in parallel) AND T4 begins (opus). T5 begins ONLY if WS-1 is on main; otherwise T5 starts cycle 2.
- **Cycle 2:** T4 finishes; T5 finishes (if started cycle 1).
- **Cycle 3 (opus):** T7 begins. (If T5 didn't start cycle 1, it runs in parallel here.)
- **Cycle 4:** T7 finishes.
- **Cycle 5 (sonnet):** T8.

The drafter's "4 cycles" assumes T7 lands in 1 cycle, which contradicts T7's own 2-cycle estimate. The drafter's "8 cycles strictly sequential" ignores the four genuinely-parallel sonnet tracks. **Five cycles is the binding budget.** If WS-1 doesn't land before cycle 1, add 1 cycle for T5 deferral → **6-cycle ceiling**.

---

## 5. WS-1 coordination strategy refinements

The drafter's "BLOCK on WS-1 merge to main" is too binary. Concrete refinements:

1. **Unblocking signal is file presence, not branch state.** T5 needs `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` and `…/contracts/router_contract.schema.json` and `…/tests/fixtures/` AND `…/tests/test_router_contract.py` to exist. T8 needs all of T5's prereqs + `…/tests/test_router_contract.py` with the WS-1-shipped inline dispatch shape. **Manager checks file presence on each cycle dispatch; does NOT poll WS-1's branch state.**

2. **If WS-1 NEEDS-FIXES on review.** Manager re-dispatches WS-1 fixes; WS-4's T1–T4, T6 continue independently (no WS-1 dependency). T5/T8 stay BLOCKED. WS-4 cycle envelope absorbs the wait — see §4.3 binding.

3. **`git log --oneline` check is fragile.** The drafter's check `git log --oneline plugins/.../router_contract.json` returns nothing if WS-1 is on a feature branch not yet merged into WS-4's worktree base. Replace with: `test -f <path>` for each of the four required files. If absent, BLOCK; if present, proceed regardless of branch.

4. **WS-1 test path drift.** WS-1 plan §3 T3 fixes path at `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`. T8's import statement is hardcoded to this path. If WS-1 ships a different path (e.g. `tests/contracts/test_router_contract.py`), T8 breaks. **Synthesizer must require T8 implementer to verify the WS-1 path before authoring the import line; if drift, surface immediately rather than auto-relocating.**

5. **Stub-and-refactor option.** Drafter rejects writing a stub helper. **CONFIRMED** — this is the right call. Stubbing creates two-sources-of-truth and exactly the dispatch-in-two-places sin synthesis §7.1 forbids. T5/T8 stay binary BLOCKED; manager waits.

---

## 6. Owner-class and routing audit

| Task | Plan | Critique | Final |
|---|---|---|---|
| T1 (schemas) | sonnet | Confirmed | sonnet |
| T2 (`check_prereqs`) | sonnet | Confirmed | sonnet |
| T3 (`detect_drake`) | sonnet | Confirmed | sonnet |
| T4 (`extract_field`) | opus | Confirmed (mild dissent — sonnet could) | opus |
| T5 (`verify_router_field_contract`) | opus | **Reconsider** — synthesis §1.4 spec is precise | sonnet (with opus fallback if cycle-1 fails) |
| T6 (producer edits) | sonnet | Confirmed | sonnet |
| T7 (SKILL.md rewrite) | opus | Confirmed | opus |
| T8 (bash + retrofit) | sonnet | Confirmed | sonnet |

Net: **opus tasks 2 (T4, T7).** Down from drafter's 3 (T4, T5, T7). Saves ~1 cycle of opus capacity for T7 fallback.

---

## 7. Out-of-scope leakage check

Verified clean:
- ✅ No WS-2 work (WS-1 retrofit is in-scope per synthesis §7.1; net-new tests are not).
- ✅ No WS-3 work (no real-tool runs).
- ✅ No marketplace edits.
- ✅ No `scattering.schema.json` modifications.
- ✅ No `compare_dm` helper (LLM-only per §6 row 8).
- ✅ No router-level Python orchestrator (lens "Non-goals").

The plan correctly stays inside the WS-4 perimeter. §8 of the plan enumerates non-goals matching synthesis §8 verbatim.

---

## 8. Pre-flight risks audit

The drafter's 10 risks are mostly complete. **Missing:**

1. **Worktree strategy.** Plan never names where WS-4 runs. Synthesizer must specify: WS-4 runs in its own worktree at branch `ws-4-refactor` rooted off main (or off WS-1's branch if WS-1 hasn't merged). Without this, multiple subagents collide on the same files.
2. **T7 routing-semantics smoke gate.** Already flagged in §2 T7. Add a list of branch labels that must survive verbatim.
3. **`importlib.util.spec_from_file_location` convention.** Synthesis §7.1 explains why (hyphen in dir name). The plan inherits without restating. T8's exact import block (plan §6.1) is correct but should reference an existing convention if one exists in repo. Implementer must verify by `grep -r "spec_from_file_location" plugins/` whether this pattern is already used elsewhere; if not, this is the first use and AUDIT-style documentation is warranted (one paragraph in WS-4's run-dir report).

---

## 9. Implementer-readiness

A sonnet picking up T1–T3, T6, T8 can execute. Ambiguous spots:

- T4 row 5 schema dispatch (synthesizer must lock `<schema-root>/<basename>.schema.json` mapping).
- T6 W4-A Edit 3 phrase (synthesizer must surface the canonical wording).
- T7 W4-D embedding (already adjudicated; needs promotion in discipline list).
- T7 routing-semantics preservation (synthesizer must list sacrosanct branch labels).
- T8 bash test body (synthesizer must specify the 5-step shape per §4.2).
- T5 sonnet vs opus (synthesizer must pick).

No "TBD" or "implementer reconciles" hedges in the plan body itself, but several gates are softer than they should be (W4-A Edit 3, `sigmav_xf` count, W4-E test body).

---

## 10. Synthesizer must resolve

Numbered. Each is a binding decision the synthesizer owes the next layer.

1. **T5 owner class:** sonnet or opus? Critic recommends sonnet (with opus fallback if cycle-1 fails).
2. **T4 row 5 schema dispatch:** lock `<schema-root>/<basename>.schema.json` mapping rule (basename = prefix of `<schema-version>` before `/`).
3. **T6 W4-A Edit 3 canonical phrase:** surface proposer §5 W4-A Edit 3 verbatim wording so the gate can `grep -F` the exact phrase, not a soft regex.
4. **T8 bash test body shape:** specify the 5-step `test_cmd_detect_activation.sh` shape per §4.2 (source install.sh; stub run_smoke / wolfram_path / is_drake_dir / config_get; call cmd_detect; assert across three status branches).
5. **T7 routing-semantics preservation:** enumerate the decision-tree branch labels that must survive verbatim across the rewrite (e.g. "Step 5 Branch 1 — DRAKE unset", "Step 5 Branch 2 — DRAKE detected"). Add as gate #8 to T7.
6. **WS-1 BLOCK semantics:** replace `git log --oneline` check with `test -f` on the four required artifacts. T5/T8 BLOCK on file presence, not branch state. WS-4 cycle envelope absorbs the wait per §4.3.
7. **Cycle envelope:** bind to **5 cycles** (6 if WS-1 missing at cycle 1). Drafter's "4 or 8" punt resolved.
8. **T2 `__init__.py` removal:** drop the empty `scripts/__init__.py` output — `spec_from_file_location` doesn't need it and the dir isn't a package.
9. **W4-D promotion in T7 discipline:** elevate W4-D from item #4 of T7's authoring-discipline list to a top-level numbered step so the implementer cannot miss it.
10. **`sigmav_xf` count gate:** tighten T6 from `<=1` to `==1` (back-compat note must exist; canonical replacement must land).

Resolving these 10 items closes WS-4's plan defects and unblocks implementer dispatch.

---

## Closing note

The plan does the hard work right: row-by-row gates on the load-bearing primitive (T4), `git show HEAD:` preserve-verbatim on the rewrite (T7), explicit non-goals reflecting synthesis §8, owner-class routing that mostly matches judgment density. The defects are concentrated in coordination-with-WS-1 (binary BLOCK semantics), in three soft gates that need tightening, and in one cycle-envelope hedge that needs committing. With the 10 items in §10 resolved, this is implementer-ready.
