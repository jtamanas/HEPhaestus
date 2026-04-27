## Verdict: APPROVE

## Test results

- `git diff --stat main..HEAD`: 4 files, all under `plugins/hep-ph-toolkit/skills/madgraph/**` (SKILL.md, references/generation.md, scripts/resolve_named_model.py, tests/test_resolve_named_model.py). No stray files.
- `pytest plugins/hep-ph-toolkit/skills/madgraph/tests/ -q`: **10 passed, 1 skipped** (skipped is the mg5_aMC-on-PATH integration test — expected).
- `resolve_named_model.py --help`: runs, prints usage, exits 0.
- Cross-plugin coupling: no `from plugins.`, no `from model_building`, no `sys.path` manipulation. Inline `json.loads(CONFIG_PATH.read_text())` — matches judgment-call #6 (explicitly documented in the source comment: "Inline config read — no cross-plugin import").
- `mg5_aMC -c` usage: **zero hits**. SKILL.md new subsection explicitly says "passed as a script-file, NOT via `-c`" and shows `mg5_aMC /tmp/dark_su3_run.mg5`. Tests include a guard test (`test_mg5_script_file_invocation_supported`) verifying the script-file contract.
- SKILL.md: new "Using a named hep-ph-agents model?" subsection is the **first** branch of the decision tree (lines 16-49), above "Install or configure MG5?". Good placement.
- XDG isolation: script reads `XDG_CONFIG_HOME`; all 6 substantive tests set `XDG_CONFIG_HOME=tmp_path` in env — no home-dir leakage.

## Findings

### Blocker: none

### Major: none

### Minor

- `--help` exit path at line 46 is cute-but-confusing (`sys.exit(0 if args and args[0] in ("-h","--help") else 3)`); given the preceding `if not args or ...` guard it's fine, but a plain `sys.exit(0)` branch + separate no-args branch would read cleaner. Non-blocking.
- `KNOWN_KEYS` set (line 25) is defined but never consulted for validation — any key string is accepted and returns exit 2 if absent. Fine for v1, but consider gating on `KNOWN_KEYS` later for typo-catching.
- Resolver's internal `resolve()` helper (line 29) is unused by `main()` (which re-reads config directly). Dead-ish code; low priority.

Ship it.
