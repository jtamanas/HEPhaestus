# REVIEW_2 — 2HDM+a Phase 0 (prep), Round 2

**Verdict**: ACCEPT

## Per-defect status

### D1 (cosmetic) — VERIFIED
`plugins/hep-ph-demo/skills/2hdm-a/SKILL.md` L243-247 now contains the preamble:
```bash
SARAH_PATH=$(jq -r '.sarah_path' "${XDG_CONFIG_HOME:-$HOME/.config}/hep-ph-agents/config.json")
flock -x -w 120 .../sarah.lock \
  wolframscript -code "AppendTo[\$Path, \"$SARAH_PATH\"]; <<SARAH\`; Start[\"TwoHdmAfix\"]; MakeUFO[]; Quit[]"
```
Reads `sarah_path` from XDG config via `jq`, injects via `AppendTo[$Path, ...]` (bash expands `$SARAH_PATH` inside the double-quoted `-code` arg before wolframscript sees it; the `\$Path` and `\`` are correctly escaped from Mathematica). Shallow runnable check OK — bash quoting is sound.

### D2 (minor) — VERIFIED
`capture_env.py` L94-117 defines `_strip_styleform()`; L134 calls it on each non-banner line. env.json L55: `"sarah_version": "4.15.3"` — no `StyleForm[...]` wrapper. Helper extracts the last version-token-shaped first-arg of any `StyleForm[…]` occurrence and falls back to wholesale stripping.

### D3 (blocker) — VERIFIED
`capture_env.py` L58-73 implements `_find_config_path()` with XDG-first ordering: `$XDG_CONFIG_HOME/hep-ph-agents/config.json` → `~/.config/hep-ph-agents/config.json` → repo-root `config.json` (legacy fallback). env.json confirms:
- L51: `"_config_source": "/Users/yianni/.config/hep-ph-agents/config.json"` (XDG hit)
- L56: `"mg5_version": "3.5.6"` ✓
- L57: `"maddm_version": "3.2.13"` ✓

### D4 (trivial) — VERIFIED
`.shift-manager/.../workstreams/2hdma/prep/p7.md` L8 now truthfully says: `git_sha_pre_run = a05f274 (captured via git rev-parse main fallback; .shift-manager/scoping/main_sha.txt does not exist — fallback PRE_RUN_SHA_FALLBACK used as documented in capture_env.py)`. The "main_sha.txt was read" lie is gone.

## Scope-guard verdict — PASS

`git diff 4436b64..HEAD --name-only` on branch tip `2c9dd31`:
- `demo_output/2hdm-a/playtest_log/env.json` — allowed
- `plugins/hep-ph-demo/skills/2hdm-a/SKILL.md` — allowed
- `plugins/hep-ph-demo/skills/2hdm-a/scripts/capture_env.py` — allowed

D4 commit `903fbb8` lives on `main` (parent worktree), touches only `.shift-manager/run-20260424-202956/workstreams/2hdma/**` and `.shift-manager/.../state/2hdma-tries.json` — both inside allowed prefixes. No scope violations.

## Non-blocking notes
- D1 wolframscript invocation: bash variable expansion confirmed by inspection. Not executed live, but no quoting bugs visible. If `jq` is missing or the key is absent, `SARAH_PATH` will be empty/`null` and the `AppendTo` will silently load nothing — recommend a `[ -n "$SARAH_PATH" ] || { echo "SARAH_PATH unset"; exit 1; }` assertion in a future polish pass. Non-blocking for prep gate.
- `capture_env.py` regression check: prior probe order (config-key → resolved binary → system PATH) preserved for both `get_mg5_version` and `get_maddm_version`. `_strip_styleform` is additive (only invoked on the SARAH version line). No behavioral regression.

## Green-light
**ACCEPT.** Phase 1 dispatch authorized at branch tip `2c9dd31bb26c27e343bb9115cb4d94dfa713b300`.
