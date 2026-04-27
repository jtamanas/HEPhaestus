## Verdict: APPROVE-WITH-FIXES

## Test results
- pytest: 16 passed, 1 skipped in 0.04s
- bash: PASS=6 FAIL=0 SKIP=0 (detect_config.sh)

## Findings

### Blocker
- none

### Major
- `_activation_parse.py` uses an unescaped case-insensitive `license` regex in `ACTIVATION_PATTERNS`. This is exactly the "wildly over-broad" failure mode: any Wolfram banner mentioning "BSD license" or a copyright notice will be classified as `activation_required`. Tighten to something like `no\s+valid\s+license|license\s+(not\s+found|expired|required|invalid)`. All other patterns (`activate`, `wolfram\s+id`, `not\s+activated`, `activation\s+required`, `no\s+valid\s+password`) look fine.

### Minor
- `ACTIVATION_PATTERNS` carries a `TODO(W1-Day1)` to replace provisional patterns with real wolframscript output. Fixture `tests/fixtures/wolfram_activation_prompt.txt` appears to be a placeholder — schedule the real-output capture before W1 closes.
- `install --help` isn't wired; unknown subcommands fall through to the top-level usage banner. Works, but a first-class `--help` flag on each subcommand would be friendlier. Not required.

### Nit
- Subcommand JSON outputs are consistent single-line JSON (confirmed: `detect` → `{"status":"missing"}`; `use-path /nonexistent` → `SARAH_PATH_INVALID` fatal blocker; bare invocation prints usage). `emit_blocker` produces valid single-line JSON with all four required fields `{code, mode, message, user_instruction}`.
- SKILL.md frontmatter is well-formed (`name`, `description`) and body is substantive with a decision flow diagram in the first 40 lines — not a stub.
- Scope is clean: diff touches only `plugins/hep-ph-toolkit/skills/sarah-install/**` (11 files, +1041/-4). No stray files.
- Test isolation confirmed: `test_detect_config.sh` exports both `HEPPH_STATE_ROOT` and `XDG_CONFIG_HOME` to tempdirs; pytest tests operate on pure functions + `tmp_path` — real user config is untouched.
