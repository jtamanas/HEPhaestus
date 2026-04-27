# bin/ — repo-vendored helpers

Shell helpers shared across plugins and install scripts. These scripts are
not plugins; they are low-level infrastructure invoked by SKILL.md prose,
install scripts, and other helpers.

---

## Lock helpers

All locking in this repo uses Python `fcntl.flock` with `LOCK_EX | LOCK_NB`
and a 50 ms poll loop. This convention applies to every script under `bin/`
and to `plugins/shared/install-helpers/_common.sh`.

**We do NOT use util-linux `flock(1)`** — macOS's Apple BSD base does not
ship it, and requiring `brew install util-linux` for one shell line is not
acceptable for a cross-platform tool.

**SCOPE.md line 38 override:** SCOPE.md calls for `fcntl.lockf` (POSIX
record locks, `fcntl(F_SETLK)`). We use `fcntl.flock` (the `flock(2)`
syscall) instead. Rationale: `fcntl.lockf` invokes POSIX record locks which
release on *any* fd close in the process (including unrelated ones), have
well-known footguns around re-entrancy, and are per-process rather than
per-open-file-description. `fcntl.flock` ties the lock to the *open file
description*, releases only when all fds referring to that OFD are closed,
and survives `exec` — making it safe for the lock-then-exec pattern used
here. This matches the convention used by all five existing in-tree
lock-using files.

---

### Public entry points

#### `bin/flock_run.sh [--fd N] <lock_file> <timeout_sec> -- <cmd...>`

Generic file-lock runner. Acquires an exclusive `fcntl.flock` on
`<lock_file>`, then `exec`s `<cmd...>` — the lock follows the open file
description through `exec` to the wrapped command, and is held until the
wrapped command exits.

**Path-form (default):** helper runs `mkdir -p` on the lock file's parent
directory and creates the file via `touch`. Safe to call from any working
directory.

**Fd-form (`--fd N`):** caller has already opened fd N (e.g.
`exec 200>"$lock_file"`). Helper acquires the flock on fd N instead of
opening a new fd. Caller must not close fd N before calling the helper.
`mkdir -p` is NOT called in fd-form.

**`<lock_file>`** is always required (for blocker JSON context), even in
fd-form.

**`<timeout_sec>`** must be a non-negative integer. `0` = non-blocking.

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Lock acquired; wrapped command exited 0. Helper process has been replaced by `exec`. |
| 1–123, 125–127 | Wrapped command's exit code, transparently propagated via `exec`. |
| **124** | Lock acquisition timed out. Matches GNU `timeout(1)`. Note: differs from `flock(1)`'s exit-1-on-timeout. If the wrapped command itself exits 124, the caller cannot distinguish it from a helper timeout — no known WS3 caller does this. |
| **125** | Internal error before `exec`: malformed args (`FLOCK_USAGE`), `mkdir -p` failed (`FLOCK_LOCKDIR_DENIED`), `--fd N` not open (`FLOCK_FD_INVALID`), `python3` missing (`FLOCK_PYTHON_MISSING`). |

**Blocker JSON shapes (stderr):**

```json
{"code":"FLOCK_TIMEOUT","mode":"fatal","message":"flock_run.sh: lock timeout","context":{"lock_file":"<path>","timeout_sec":<N>}}
{"code":"FLOCK_LOCKDIR_DENIED","mode":"fatal","message":"flock_run.sh: cannot create lock dir","context":{"lock_dir":"<path>","errno":"<N>"}}
{"code":"FLOCK_FD_INVALID","mode":"fatal","message":"flock_run.sh: fd <N> not open","context":{"fd":<N>}}
{"code":"FLOCK_PYTHON_MISSING","mode":"fatal","message":"flock_run.sh: python3 not on PATH","context":{}}
{"code":"FLOCK_USAGE","mode":"fatal","message":"flock_run.sh: <reason>","context":{}}
```

#### `bin/config_write_locked.sh <key1> <val1> [key2 val2 ...]`

Thin wrapper around `bin/flock_run.sh` for serializing writes to
`config.json`. Acquires the config lock, sets `HEPPH_CONFIG_LOCK_HELD=1`
(so `config_merge`'s inner Python lock noop-s, defeating nested-lock
deadlock), then invokes `config_merge` from `_common.sh`.

Retry-once semantics: if the first lock attempt times out (30 s), the
wrapper retries once (zero-sleep between attempts). On second timeout,
emits `CONFIG_LOCK_TIMEOUT` blocker JSON and exits 1 (not 124). Caller
sees exactly one JSON payload per double-timeout (first-attempt helper
JSON is discarded).

**Note:** `config_write_locked.sh` retains its historical
`${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus/.config.lock` path for
the lock file. This is intentional and NOT migrated to `$HEPPH_STATE_ROOT`
by WS3 — the config-lock has its own XDG-based convention.

---

### Lock-file path convention

All per-purpose lock files (except the config lock above) live under:

```
${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}/.locks/
```

Per-purpose filenames: `sarah_global.lock`, `micromegas_cache_<hash>.lock`.

**Why not `$REPO_ROOT/.shift-manager/locks/`:** each git worktree has its
own `.shift-manager/` directory. Two operators running `Start["TwoHdmAfix"]`
in different worktrees would each acquire their own separate file, neither
blocking the other, while both write to the same shared
`$SARAH_ROOT/Output/TwoHdmAfix/` tree. `HEPPH_STATE_ROOT` is per-machine,
so mutex semantics actually hold across worktrees.

**Bootstrap snippet (caller side):**

```bash
HEPPH_STATE_ROOT="${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}"
LOCK_DIR="$HEPPH_STATE_ROOT/.locks"
mkdir -p "$LOCK_DIR"      # helper also does this in path-form, but caller-side is explicit
LOCK_FILE="$LOCK_DIR/<purpose>.lock"
"$REPO_ROOT/bin/flock_run.sh" "$LOCK_FILE" <timeout> -- <cmd>
```

**Helper does NOT read `HEPPH_STATE_ROOT` itself.** Caller resolves the
lock path; the helper accepts an arbitrary path.

---

### Caveats

- **macOS NFS:** `fcntl.flock` on NFS is advisory-only on many kernel/NFS
  versions. Lock semantics may not hold cross-host. For single-machine use
  (all WS3 callers), behavior is correct on macOS 10.15+ and Linux.
- **Python 3.10+ required.** `fcntl` is a POSIX stdlib module. Windows is
  out of scope.
- **no stale-lockfile failure mode.** Do NOT `rm <lock_file>` to "fix" a
  stale lock. Lock files are never stale in the `flock(2)` model — the OS
  releases the lock when the last process holding it exits or closes the fd.
  If a timeout fires repeatedly, check `pgrep <wrapped-command>` before
  retrying.
- **Lock survives `exec`:** the flock is held by the open file description,
  not the process. `exec "$@"` replaces the helper's bash process with the
  wrapped command; the wrapped command inherits fd 9 (or N in fd-form) and
  holds the lock until it exits.
- **Bash 3.2 compat:** macOS ships bash 3.2. `export -f` is not supported;
  `config_write_locked.sh` re-sources `_common.sh` in the child bash
  process instead.
