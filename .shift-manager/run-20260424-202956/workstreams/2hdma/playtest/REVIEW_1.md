# 2HDM+a PT1 Review (minimal)

Verdict: ACCEPT-FAIL-WITH-FIX-AUTHORIZED

1. verdict.md: YES — verdict is FAIL; both issues listed. 2hdma-001 (patcher_regex_bug) named as blocker in Root Cause section; 2hdma-003 (omega_outside_band) named as Warning with Omega h^2=10.494 vs band [9.95, 10.36] (+3.4%).

2. Ωh² reported: 10.494  (target 10.15 ± 2%)

3. 2hdma-001: fix_scope=patcher (fix_owner_hint="patcher"), auto_fixable=not marked (no auto_fixable field; fix_attempts shows manual workaround only), bug at patch_paramcard.py _set_block_value() regex `^\s*<idx>\s+(?!\d)` (explicit file: patch_paramcard.py; no line number recorded in issues.jsonl)

4. 2hdma-003: downstream of 2hdma-001 — description states deviation traces to ZAMIX not set correctly by the patcher (same root cause); wrong ZAMIX causes singlet-dominated Ah2, suppresses b-quark Yukawa, shifts relic density outside band

Phase 2 decision: GO (fix 2hdma-001 first, then re-check 003)

Manager actions:
- Fix patch_paramcard.py regex `(?!\d)` lookahead bug (2hdma-001, blocker)
- Re-run PT1 from scratch (fresh MG5 card) without manual workaround to verify DMSECTOR/PHASES/ZAMIX set correctly
- Confirm 2hdma-003 resolves as downstream once ZAMIX is correctly written (expect bbx>=30% restored)
- Log 2hdma-002 (flock/macOS) and 2hdma-004 (launch script form) as non-blocking skill_prose fixes
