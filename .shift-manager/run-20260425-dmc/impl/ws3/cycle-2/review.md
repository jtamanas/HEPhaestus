VERDICT: NEEDS-FIXES

GATE RESULTS:
- Fix #1 (real-LLM replacement of synthetic): PASS structurally — `_run_real_claude` (conftest.py:407) calls real `claude -p` subprocess, parses stdout via `_parse_claude_json_output` from `eval.harness.runners.claude_code` (the Component B coupling target), and shapes `harness_meta` with the same keys as `ClaudeCodeRunner.last_meta` (plus `raw_answer`). Synthetic path is correctly gated to `tier=tier1 AND not WS3_FORCE_LIVE`. Note: `_run_real_claude` mirrors `ClaudeCodeRunner._build_command` but OMITS `--model`, `--max-budget-usd`, and `--plugin-dir`. The missing `--plugin-dir` is potentially load-bearing — see escalation adjudication.
- Fix #2 (grep): PASS — `test_t1_fixture_spec_pointA/B_numeric_anchors` use `\bm_chi:\s*100\b` (word-boundary), match the YAML-nested form correctly.
- Fix #3 (bell-ring 4/4 vs 2/4): NOT ACCEPTED — see escalation adjudication. Implementer's diagnostic framing is wrong, and no live transcript was attached as evidence.
- Fix #4 (slots=True docstring): PASS — `helper_subprocess_wrapper.py:43-50` now correctly explains why `slots=True` is omitted (Python 3.10 importlib bug); no misleading reference left.
- Fix #5 (transcript_event_log fallback): PASS — `transcript_event_log.py:55-85` raises `ImportError` when at repo root and harness module is unimportable; only falls back to `None` when not at repo root.
- Diff territory: PASS — all changes confined to `tests/dark_su3_playtest/` and `tests/fixtures/dark_su3_playtest/`. Zero edits to `plugins/`, `/maddm`, `/micromegas`, `/drake`, or `eval/harness/`.
- Model-agnosticism: PASS — `_run_real_claude` and Component B are pure dict/string consumers; no Dark-SU(3) hardcoding. Helper wrapper / parsers contain only generic field names. Dark-SU(3)-specific data lives in fixtures only.

BELL-RING ESCALATION ADJUDICATION:

Step 4b prose review (live `plugins/constraints/skills/dark-matter-constraints/SKILL.md` lines 91–123):

> | ⟨σv⟩(v→0) | `sigmav_total` | `sigma_v_zero` | > 10% relative | **FLAG to user** |  (line 96)
>
> ### Step 4b — Disagreement comparison (LLM-driven, calls `extract_field`)
> ...
> 2. **micrOMEGAs side.** Run:
>        python "$REPO_ROOT/plugins/.../extract_field.py" \
>            --json "<mo_run>/<file>" --key "<canonical_name>" --schema-version "<id>"
>    Use `relic.json` + `relic/v1` for Ωh², `annihilation.json` + `annihilation/v1`
>    for ⟨σv⟩(v→0), `summary.json` + `scattering/v1` for σ_SI/σ_SD.

Defect real or implementer error: IMPLEMENTER ERROR. Step 4b prose IS imperative, names the literal `--schema-version` flag, names the literal `sigma_v_zero` canonical key, and pairs them with the literal `annihilation/v1` schema id for the ⟨σv⟩ row. The implementer's claim that "live SKILL.md doesn't make LLM emit `extract_field.py` invocations with `--schema-version` / `sigma_v_zero`" is not supported by the prose itself.

Required action: WS-3 cycle-3 must (a) attach the actual live transcript (claude --output-format json stdout), (b) re-diagnose WHY NC-1/NC-2 fail under WS3_FORCE_LIVE=1, and (c) fix the real cause. Most likely root causes to check first:
  1. `_run_real_claude` omits `--plugin-dir` — without it, `/maddm` and `/micromegas` slash-commands at SKILL.md Steps 2–3 cannot dispatch, and the LLM may emit `MICROMEGAS_MISSING` (recoverable) and never reach Step 4b's micrOMEGAs side. If micrOMEGAs is skipped, no `extract_field` cross-check call is made and NC-1/NC-2 fail by absence, NOT by SKILL.md defect.
  2. Helper subprocess wrapper installs `subprocess.run` patch in the harness's parent process, but `claude -p` runs in a child process — the wrapper does NOT intercept helper calls made by the LLM inside the claude subprocess. This is fine for the assertion (assertion reads `harness_meta["tool_uses"]` from claude's JSON stream, not `wrapper.invocations`), but it means the LLM is invoking REAL `extract_field.py` against fixture paths that may not exist on disk → it likely fails → LLM may abandon Step 4b. Verify: do the fixture paths referenced in config.yaml actually contain real `relic.json` / `annihilation.json` at locations the LLM can resolve?
  3. The fixture `config_pointA_configured.yaml` may not point to `<mo_run>` directories with real canned files, or the canned filenames don't match what the LLM constructs from the prose.

Until the live transcript is captured and root cause is identified, cycle-1 fix #3 ("after fix #1 lands, re-run the bell-ring on live SKILL.md and assert all 4 NC cases PASS via real LLM execution") remains unmet.

PLAN-DEFECTS:
- D5 (NEW, contingent): If root cause analysis confirms `--plugin-dir` is required for the LLM to reach Step 4b, plan §T4 binding for `_run_real_claude` is missing the plugin-dir flag. Plan-final §T4 §3.6 only specified "skill_md_content as system prompt"; this is insufficient when the skill's internal logic dispatches to other slash-commands. **Adjudication deferred** until cycle-3 transcript evidence.

FIXES REQUIRED (NEEDS-FIXES):
1. Capture and commit the live `claude --output-format json` stdout from a WS3_FORCE_LIVE=1 Tier-1 run of `pointA_configured` and attach to cycle-3 dir as `live_transcript_pointA_configured.json`. Without this, no further adjudication is possible.
2. Inspect the captured transcript: which step does the LLM actually reach? Does it emit `MICROMEGAS_MISSING`, `MADDM_MISSING`, `UFO_MISSING`, or another blocker before Step 4b? Does it emit any `extract_field` Bash tool_use, and if so with what args?
3. Based on diagnosis, EITHER:
   (a) If LLM never reaches Step 4b due to missing `--plugin-dir` or missing fixture paths: fix `_run_real_claude` to pass `--plugin-dir` and ensure config fixtures point at real canned dirs, so the LLM CAN reach Step 4b. Re-run; expect 4/4 PASS.
   (b) If LLM reaches Step 4b but emits `extract_field` with different args (e.g., omits `--schema-version` due to argv-quoting) or omits the call entirely: this IS a SKILL.md defect; escalate to WS-4 with a concrete reproduction (transcript snippet showing what the LLM actually emitted vs. what Step 4b instructed). WS-3 verdict can then be PASS-WITH-NITS conditional on WS-4 cycle-2.
   (c) If LLM emits `extract_field` correctly but assertion regex misses it: assertion bug — fix in WS-3.
4. Do NOT escalate to WS-4 without evidence. The current escalation reasoning rests on a false reading of the SKILL.md prose.

NITS:
- `_run_real_claude` could share a single helper with `ClaudeCodeRunner._build_command` to avoid drift. Currently it duplicates the cmd construction.
- `RuntimeError` on `claude` subprocess failure (`_run_real_claude:469`) loses `result.stdout` if rc≠0 and stdout is non-empty (the path takes only the rc=0-or-stdout path). Edge case but harmless.

MERGE READINESS:
- WS-3 ready to merge as-is: NO. Cycle-1 fix #3 is unmet. The harness now has a real-LLM path (cycle-2 fix #1 PASS), but the bell-ring evidence does not yet support either a clean PASS or a verified WS-4 defect handoff. One more cycle is required to capture and diagnose the live transcript before WS-3 can land.
