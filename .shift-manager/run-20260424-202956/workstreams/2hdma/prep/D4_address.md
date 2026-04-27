# D4 — p7.md false claim about main_sha.txt

**Status**: FIXED
**Severity**: trivial (doc lie)
**Round**: 2 (sonnet address)

## What was wrong
`p7.md` line 8 stated:
> `git_sha_pre_run = a05f274 (read from .shift-manager/scoping/main_sha.txt, matches plan)`

This is false. The file `.shift-manager/run-20260424-202956/scoping/main_sha.txt` does not exist on disk. The value `a05f274` came from the hardcoded fallback `PRE_RUN_SHA_FALLBACK = "a05f274"` in `capture_env.py`.

## Fix applied
Corrected p7.md line 8 to truthfully state:
> `git_sha_pre_run = a05f274 (captured via `git rev-parse main` fallback; .shift-manager/scoping/main_sha.txt does not exist — fallback PRE_RUN_SHA_FALLBACK used as documented in capture_env.py)`

## File changed
- `.shift-manager/run-20260424-202956/workstreams/2hdma/prep/p7.md`
