VERDICT: NEEDS-FIXES

GATE RESULTS:
- T1 sentinel/specs/canned/golden files exist: PASS — full tree present, distinct-categories disclaimer in README, .gitkeep + README.md only in ufo/darkSU3/.
- T1 numeric-anchored greps (`^m_chi:\s*100\b` etc): FAIL — spec_pointA.yaml nests `m_chi` under `dm_candidate:` so the line is `  m_chi: 100`. The plan-final's `^m_chi:` line-anchor never matches. Plan-defect (gate is unreachable as written), but the underlying values ARE correct per synthesis §2.
- T1 WS-1 reuse line-count diff: PASS — both sides emit 2 `Omega` lines.
- T2 Component A LoC ≤200, frozen dataclass, exact field set: PASS (186 LoC; frozen=True; fields = {helper_name,argv,returncode,stdout,stderr}). `slots=True` is silently dropped vs. plan-binding API code block; gate doesn't check slots so it passes. Frozen invariant verified by mutation attempt.
- T3 Component B LoC ≤180, importable, dataclass, parses fixture meta: PASS (132 LoC).
- T3 format-region SHA pin matches LIVE region: PASS (`2673250afa…` matches recomputed live hash).
- T3 import-time symbol-presence check: PASS-with-soft-fallback — works from repo root; falls back to `_parse_claude_json_output = None` on ModuleNotFoundError. Plan §3.1 said "MUST fail at module load". Acceptable per pre-flight #1 (content-SHA is the hard pin).
- T3 Component C `--spec` preflight + CLI exit codes + live SKILL.md passes: PASS (58 LoC).
- T4 RetryResult frozen + tier="tier3" widened, SKILL.md content-not-path, runnable assert_no_claude_md_leakage, claude-CLI session fixture, W4-D `--key omega_h2` pin: PASS.
- T4 5-scenario × Tier-1/Tier-2 matrix collects + passes: PASS (25 passed / 2 skipped).
- T5 four sabotage SKILL.md files exist + diff live + NC-3 retargeted (CROSSCHECK_DISAGREEMENT removed) + `--spec` removed in NC-4: PASS.
- T5 parametrize uses `in` form and retargeted NC-3 assertion: PASS.
- T5 bell-ring (WS3_FORCE_LIVE=1, all 4 cases PASSED): PASS.
- T5 Tier-3 smoke marker + binary-only skipif (UFO skipif retired): PASS.
- T5 positive scaffolding test_tier3_scaffolding_runs in CI: PASS.
- Diff stays in WS-3 territory: PASS — only `tests/dark_su3_playtest/`, `tests/fixtures/dark_su3_playtest/`, and a 4-line `pytest.ini` markers stanza. Zero edits to plugins/ or to /maddm, /micromegas, /drake.
- Model-agnosticism (lens): PASS for helpers — Components A/B/C are model-agnostic (they consume canned files / dict shape; no Dark-SU(3) string anywhere). Dark-SU(3)-specific data is confined to fixtures.
- Component B coupling target (harness_meta dict, NOT log-line regex): PASS — `parse_transcript(harness_meta: dict, ...)` reads `tool_uses`, `result_text`, `raw_answer` keys. No regex against `claude_code.py:442`.
- Negative-control bell-ring catches drift (deeper semantic gate): FAIL — see Plan-Defect 2.

PLAN-DEFECTS:
- D1 (plan T1 gate #2 grep pattern): `^m_chi:\s*100\b` is line-anchored but spec YAML nests m_chi under dm_candidate: so the matching line is `  m_chi: 100`. **Adjudication: ACCEPT as cycle-2 fix.** Either the gate must drop `^` (→ `\bm_chi:\s*100\b`) or the YAML must hoist the keys to top level. Recommend the former — the underlying data is correct.
- D2 (plan §3.1 module-load symbol check vs. graceful fallback): plan said MUST fail at module load; impl falls back to `None` on ModuleNotFoundError. **Adjudication: ACCEPT** — content-SHA pin (T3 gate #2) is the load-bearing protection; symbol check is belt-and-suspenders.
- D3 (slots=True declared in plan binding code blocks but not enforced by gate, dropped by impl): plan T2/T3 code-block API spec says `@dataclasses.dataclass(frozen=True, slots=True)`; impl uses `frozen=True` only. Frozen invariant holds. **Adjudication: ACCEPT** — implementer's Python 3.10 spec_from_file_location workaround (sys.modules pre-registration) is sound, but the cleaner fix is dropping slots=True since the gate doesn't enforce it. Frozen invariant is the load-bearing one and it holds.
- D4 (CRITICAL — negative-control suite is structurally tautological in Tier-1): The implementation builds a `_synthetic_harness_meta(scenario_id, envelope)` simulator that INSPECTS `envelope["skill_md_content"]` (i.e., the SKILL.md text) and conditionally emits `tool_uses` / `result_text` based on what it finds. NC-1 (`--schema-version` removed) → simulator drops `--schema-version` from synthesized command → assertion fires. NC-2 (sigma_v_zero invocation removed) → simulator's regex on Step 4b doesn't co-find `extract_field` + `annihilation/v1` → simulator drops the sigma_v_zero tool_use → assertion fires. NC-3 (CROSSCHECK_DISAGREEMENT removed) → `has_crosscheck_disagreement = "CROSSCHECK_DISAGREEMENT" in skill_content` is False → simulator omits the disagreement line → assertion fires. **Only NC-4 (`spec_flag_preflight`) is a real check** because it's a pre-LLM grep on the file, not a simulator round-trip. The bell-ring gate (WS3_FORCE_LIVE=1) similarly tests only the simulator's mirror of the live SKILL.md, not the LLM. Plan §1 said "Tier-1 dry-run + Tier-2 hybrid pytest bodies driving the rewritten WS-4 SKILL.md against the fixtures" — this binds Tier-1 to actually drive the LLM. The implementer's blocker #2 hint understated this. **Adjudication: REJECT — NEEDS-FIXES.** Cycle-2 must either (a) wire Tier-1 to invoke the real `claude` CLI with stubbed helper subprocess (the original design — `_invoke_skill` has a TODO branch for it), or (b) explicitly retire Tier-1 negative-control claims and run the NC suite at Tier-2 only with real LLM. Option (a) is what plan §3.T4 originally specified (see plan T4 "drive the rewritten WS-4 SKILL.md against the fixtures").

FIXES REQUIRED (NEEDS-FIXES):
1. Replace `_synthetic_harness_meta` with a real ClaudeCodeRunner invocation that consumes `harness_meta` from `last_meta` (the Component B coupling target). Helpers stay stubbed via `HelperSubprocessWrapper(mode="stub")` per plan §T2. This is the load-bearing fix — without it, Tier-1 has no signal and the entire negative-control + bell-ring story is illusory.
2. Fix plan T1 gate #2 grep: change `^m_chi:\s*100\b` (and m_med/partner-mass siblings) to `\bm_chi:\s*100\b` so they match the YAML-nested form. Equivalently: hoist keys, but the data is correct as-is.
3. After fix #1 lands, re-run the bell-ring on live SKILL.md and assert all 4 NC cases PASS *via real LLM execution* (not via simulator round-trip).
4. Optional cleanup: drop the dead `slots=True` reference in `helper_subprocess_wrapper.py` docstring (line 47–48) since the impl deliberately doesn't apply slots; the comment misleads future readers.
5. Optional: tighten the symbol-presence fallback in `transcript_event_log.py` to raise instead of setting `None` when invoked from repo root (detect via `pathlib.Path.cwd()` heuristic) so the soft fallback can't silently mask a harness rename in CI.

NITS:
- N/A (graduated to fixes above).
