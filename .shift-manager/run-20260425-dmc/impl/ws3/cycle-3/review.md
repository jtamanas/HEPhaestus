VERDICT: PASS

GATE RESULTS:
- Scope reversion (no plugins/ edits): PASS — `git diff 35f6e7d^..35f6e7d` touches only `tests/dark_su3_playtest/` and `tests/fixtures/dark_su3_playtest/` (13 files, 229+/29-). No commit on the WS-3 branch (a53d2bc..35f6e7d) modifies `plugins/`. The 39 plugin deletions visible in `main..35f6e7d` come from main advancing past merge-base `b46b930` via WS-2 (legitimate test relocation), not from this branch.
- Flag fix shape matches _build_command: PASS — `_run_real_claude` in `tests/dark_su3_playtest/conftest.py` lines 490-500 builds: `["claude","-p",prompt,"--output-format","json","--model","sonnet","--permission-mode","bypassPermissions","--append-system-prompt",skill_md_content,"--max-budget-usd","1.0","--no-session-persistence","--plugin-dir",str(_constraints_plugin_dir)]`. Mirrors `ClaudeCodeRunner._build_command` (eval/harness/runners/claude_code.py:469-485) exactly, with `--plugin-dir` pointing at `REPO/plugins/constraints` so SKILL.md slash-command dispatch works.
- Bell-ring NC-1 transcript shows real LLM behavior: PASS — `ws3-c3-bellring-NC1.json` (38 stream events, 45 `tool_use_id` records, 25 "sonnet" mentions) shows the model invoking `extract_field.py --json $CANNED/annihilation.json --key sigma_v_zero --schema-version annihilation/v1`, then computing `Ωh² = 0.118 vs 0.105 → rel_diff = 0.126` (12.6%, count=10 in transcript), and emitting `CROSSCHECK_DISAGREEMENT` (count=6). All three load-bearing claims verified verbatim.
- Bell-ring NC-2/NC-3/NC-4 transcripts plausible: PASS — Single PASS each, durations 258s/185s/289s consistent with real claude CLI roundtrips (synthetic harness completes in <1s). Test IDs match cycle intent: `extract_field_sigma_v_zero_invocation`, `crosscheck_disagreement_blocker_present` (NC-3 retargeted per plan-final §9 #6), `spec_flag_preflight`.
- Canned fixture reshape consistent with extract_field.py contract: PASS — `extract_field.py:96` reads `data.get("schema_version", "")` at top level. New shape (`{"schema_version":"annihilation/v1","sigma_v_zero":2.31e-26,...}`) matches contract; old `_fixture_meta.schema_version` shape would have caused VERSION_DRIFT. Reshape is correctness, not tampering.
- Model-agnosticism preserved: PASS — Helper invocation paths in transcript use `--key sigma_v_zero --schema-version annihilation/v1` (canonical schema names), not darksu3-specific keys. Fixtures live under `dark_su3_playtest/` namespace as required; SKILL.md and helpers untouched.

PLAN-DEFECTS:
- None.

NITS:
- `config_bellring.json` references `tests/fixtures/dark_su3_playtest/stubs/drake-lib` but only maddm-launcher and micromegas-lib stubs were added in this commit; if `check_prereqs` ever resolves DRAKE strictly, bell-ring goes red. Non-blocking for cycle-3 (current 4/4 PASS proves `check_prereqs.py` accepts the missing-but-declared path); flag for WS-4 retest.
- NC2/3/4 keep only `.txt` pytest summary; only NC1 saved the JSON stream. Future cycles should keep all four streams for forensic parity, though one stream is sufficient evidence for this cycle.
- The hardcoded `--model sonnet` in `_run_real_claude` duplicates `ClaudeCodeRunner._model` default; if the harness default changes, the playtest silently drifts. Consider importing the default constant.

MERGE READINESS: yes
