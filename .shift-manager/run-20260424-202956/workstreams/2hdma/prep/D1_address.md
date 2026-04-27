# D1 — SKILL.md:252 $SARAH_PATH claim vs. invocation mismatch

**Status**: FIXED
**Severity**: minor (cosmetic)
**Round**: 2 (sonnet address)

## What was wrong
SKILL.md line 252 claimed `$SARAH_PATH is read from config.json (key: sarah_path)` but the `wolframscript` invocation directly used `<<SARAH\`` without actually reading or using `$SARAH_PATH`. The prose was misleading — the invocation relied on Wolfram's global `$Path` resolving SARAH.

## Fix applied
Rewrote the bash snippet to:
1. Read `SARAH_PATH` from `${XDG_CONFIG_HOME:-$HOME/.config}/hep-ph-agents/config.json` via `jq`.
2. Inject it into Wolfram's `$Path` via `AppendTo[$Path, "$SARAH_PATH"]` in the `wolframscript -code` argument.
3. Updated the prose to accurately describe the XDG config source.

The invocation now actually uses `$SARAH_PATH` as the prose claims.

## File changed
- `plugins/hep-ph-demo/skills/2hdm-a/SKILL.md` lines 247-253
