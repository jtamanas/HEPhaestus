# t12-impl: config_write_locked.sh merge + _common.sh wire-in

Date: 2026-04-26
Branch: tier1/t12-config-write-lock-r1-20260426

## 3-Variant Comparison

| Aspect            | WS-B (flock+mkdir)                        | WS-D (fcntl.flock Python)                   | WS-E (shlock+link PID)                 |
|-------------------|-------------------------------------------|---------------------------------------------|----------------------------------------|
| Lock primitive    | flock(1) CLI + mkdir atomic fallback      | Python fcntl.flock (kernel byte-range)       | shlock(1) + noclobber fallback         |
| Platform          | macOS (no flock) falls back to mkdir      | macOS + Linux (best portability)            | macOS shlock, no Linux path            |
| Retry             | Yes (retry once, structured)              | Yes but in Python; single attempt in bash   | Yes (WS-E retry-once scaffolding)      |
| Key injection     | Clean passthrough — no auto-injected keys | Auto-injects last_configured + python       | Clean passthrough                      |
| Config merge      | Delegates to config_merge                 | Re-implements read/write in Python          | Delegates to config_merge              |
| Sub-process lock  | bash flock subprocess can't re-enter      | Python holds lock; no bash caller re-entry  | shlock is PID-keyed; re-entrant OK     |
| Correctness issue | flock CLI not on macOS system bash        | Nested call would deadlock (same file)      | shlock not on Linux                    |

## Merged Design Rationale

**Lock core: WS-D's fcntl.flock**
- True kernel byte-range exclusive lock via Python `fcntl` module
- Works on both macOS and Linux without requiring flock(1) or shlock(1) CLI tools
- Non-blocking (LOCK_NB) with 50ms poll loop → no SIGALRM complications

**Scaffolding: WS-E's retry-once**
- Clean bash structure: `_try_locked_write` returns 99 on timeout
- Outer caller retries once, then emits structured JSON error and exits 1

**Key handling: WS-B's clean passthrough**
- Wrapper does NOT inject `last_configured` or `python` keys
- Those belong in `config_merge` which already injects them
- WS-D's auto-injection was a scope leak (double-injection on direct calls)

**Nested deadlock fix (new in t12)**
- Wrapper acquires lock on fd 9 (bash `exec 9>`) then calls `config_merge`
- `config_merge` also tries to acquire the lock (lock wired in by this PR)
- Solution: wrapper sets `HEPPH_CONFIG_LOCK_HELD=1`; `config_merge` checks
  this env var and skips its inner acquisition

## _common.sh Wire-In Approach

Lines edited: ~163-235 (config_merge function body)

Changes:
1. Added `_lock_file="$CONFIG_DIR/.config.lock"` + `touch` before the Python call
2. Passed `$_lock_file` as `sys.argv[3]` to the Python heredoc
3. Added `import fcntl, time` to the Python imports
4. Added lock discipline block: if `HEPPH_CONFIG_LOCK_HELD != "1"`, acquire
   `fcntl.flock(LOCK_EX|LOCK_NB)` with 30s poll loop; wrap read-modify-write
   in try/finally that releases the lock

This means ALL `config_merge` callers (direct or via wrapper) are now serialized.
Direct callers acquire the lock themselves. Wrapper callers pass the held-flag.

## Smoke Test Details

Script: `bin/_smoke_config_write_locked.sh`

Method:
- Creates isolated XDG_CONFIG_HOME in tmpdir
- Spawns 4 concurrent background processes, each calling the wrapper with a
  distinct key (smoke_key_a/b/c/d)
- Waits for all 4 PIDs
- Reads config.json, verifies all 4 keys present

Result: PASS — 0 lost updates
All 4 keys (smoke_key_a, b, c, d) present in final config.json.

## Files Changed

- `bin/config_write_locked.sh` — new, 107 lines, fcntl.flock core + retry-once
- `bin/_smoke_config_write_locked.sh` — new, smoke test script
- `plugins/shared/install-helpers/_common.sh` — config_merge lock wire-in (~+30 lines)
- `.shift-manager/run-20260426-tier1-fixes/state/t12.complete` — sentinel
- `.shift-manager/run-20260426-tier1-fixes/impl/t12-impl.md` — this log
