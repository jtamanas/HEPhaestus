# SPheno — Install Reference

Reference doc for installing **SPheno** (Spectrum calculator for HEP)
from source with gfortran. Driven by `detect.sh` and `install.sh` in
this directory; consumed by the `spheno-build` runner skill's preflight
and by `/install`.

Three install modes are provided: **detect**, **use-path**, and **install**.

## Version pin

`detect.sh` pins SPheno to **4.0.5**. Override with
`HEPPH_SPHENO_VERSION=x.y.z`. When this pin bumps, `install.sh` must
remove or migrate the previous install tree
(e.g. `~/SPheno/SPheno-4.0.5` → `~/SPheno/SPheno-<new>`); the new
version is only written to `config.json` after the new install
verifies, so a half-finished upgrade does not leave the config
pointing at a stale binary.

## Disk footprint

- **Tarball:** ~10 MB (SPheno-4.0.5 from HEPForge)
- **Installed tree:** ~69 MB at `~/SPheno/SPheno-4.0.5`
- **Build-time peak (transient):** ~150 MB during `make`
- **Measured 2026-04-25 on macOS arm64.** Source: du measured 2026-04-25.

---

## Decision flow

```
SPheno install
    │
    ├─ detect         Check current state. Returns one of:
    │                   {"status":"missing"}
    │                   {"status":"found","path":"<p>"}
    │                   {"status":"configured","path":"<p>","src_path":"<s>","version":"<v>"}
    │
    ├─ use-path <p>   Accept a user-supplied path (binary OR source tree).
    │                 Validates the path, runs smoke test, records both
    │                 spheno_path and spheno_src_path in config.
    │
    └─ install [dir]  Full auto-install from HEPForge. Downloads tarball,
                      runs make, retains source tree, records both keys.
                      Default parent: ~/SPheno/SPheno-<version>
                      Override: HEPPH_SPHENO_VERSION=x.y.z
```

---

## gfortran precondition

`gfortran` must be present on `$PATH` before `install` runs. Checked by
`check_gfortran.sh`.

| OS | Command to install gfortran |
|----|----------------------------|
| macOS | `brew install gcc` |
| Debian/Ubuntu | `sudo apt-get install -y gfortran` |
| RHEL/CentOS | `sudo yum install -y gcc-gfortran` |

If absent, a `GFORTRAN_ABSENT` fatal blocker is emitted with the
per-OS `user_instruction` before exiting.

---

## Dual-key rationale: `spheno_path` + `spheno_src_path`

hep-ph-demo installs record only `spheno_path` (the compiled binary). W2
extends this by also recording **`spheno_src_path`** (the directory containing
`Makefile`). Rationale:

- `/spheno-build` needs the source tree to compile model-specific modules
  (e.g. `make Model=DarkSU3`). The binary alone is insufficient.
- We retain the source directory after `make` so it is always available.
- Both keys are always written together as an atomic `config_merge` call.

Config keys written:

| Key | Value |
|-----|-------|
| `spheno_path` | Absolute path to the `bin/SPheno` binary |
| `spheno_src_path` | Absolute path to the source root (contains `Makefile`) |
| `spheno_version` | Detected version string (e.g. `4.0.5`) |
| `spheno_installed_at` | UTC ISO 8601 timestamp |

---

## `use-path` subcommand — accepts binary OR source tree

Signature: `install_spheno.sh use-path <path>`

Behavior depends on what `<path>` resolves to:

### Case 1: executable file named `SPheno` (binary form)

```
<path> → executable file, basename == SPheno
```

- Records `spheno_path = <path>`.
- Derives `spheno_src_path = dirname(dirname(<path>))`.
- Asserts `$spheno_src_path/Makefile` exists; if not, emits
  `SPHENO_PATH_INVALID` fatal blocker (`SPHENO_SRC_MISSING` semantic).

### Case 2: directory with `Makefile` (source tree form)

```
<path> → directory, <path>/Makefile exists
```

- Records `spheno_src_path = <path>`.
- Derives `spheno_path = <path>/bin/SPheno`.
- Asserts that binary is executable; if not, emits `SPHENO_PATH_INVALID`
  fatal blocker with instruction to run `make` first.

### Neither case: fatal blocker

If `<path>` does not match either case, emits `SPHENO_PATH_INVALID` fatal
blocker with a clear error message and suggestion.

---

## Detect existing hep-ph-demo install

If `spheno_path` was written by hep-ph-demo (binary only, no `spheno_src_path`):

1. `detect` derives `spheno_src_path = dirname(dirname(spheno_path))` at
   runtime.
2. If `Makefile` is present there, reports the derived `src_path` in the JSON
   output.
3. Persists the derived `spheno_src_path` into config via `config_merge` so
   downstream skills like `/spheno-build` can read it without requiring a
   separate `use-path` invocation. The value is trivially recomputable from
   `spheno_path`, so writing it is a caching promotion, not new information.
   This is a behavior change from earlier releases (which kept detect
   strictly read-only); `spheno_version` is still NOT persisted by `detect`,
   so `cmd_install`'s version-mismatch check continues to re-probe the
   binary fresh on every invocation.

If `spheno_src_path` is already in config but its `Makefile` has disappeared
(user deleted the tree or relocated it), `detect` treats it as missing and
falls through to the derive step — a stale config path is not surfaced as
"configured."

---

## Version-mismatch → install fresh alongside

If `detect` finds an existing `spheno_path` whose version does not match the
current pin (`HEPPH_SPHENO_VERSION`, default `4.0.5`):

1. Emits a status line on stdout:
   ```json
   {
     "status": "version_mismatch",
     "existing_path": "<p>",
     "existing_version": "<v>",
     "pin": "<pin>",
     "action": "installing_fresh_alongside"
   }
   ```
2. Proceeds with a fresh install to `$HOME/SPheno-<pin>/` (never overwrites
   the existing install).
3. After the fresh install succeeds, updates both `spheno_path` and
   `spheno_src_path` to point to the new install. The old install remains on
   disk untouched.

This policy is adopted from phase1-final §8 Issue 10 / phase2-plan-final
§W2 item 6.

---

## Failure modes → blockers

All blockers are emitted on stderr as single-line JSON per
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Cause | `user_instruction` |
|------|------|-------|-------------------|
| `GFORTRAN_ABSENT` | fatal | `gfortran` not on PATH | per-OS install command |
| `SPHENO_DOWNLOAD_FAILED` | fatal | curl failed twice | check internet connection |
| `SPHENO_BASE_BUILD_FAILED` | fatal | `make` exited non-zero | see `make_log_tail` in `context` |
| `SPHENO_PATH_INVALID` | fatal | `use-path` argument invalid | see message for guidance |

### `SPHENO_BASE_BUILD_FAILED` context

When `make` fails, `_make_log_parse.py` is invoked on the full make
log. The blocker `context` object contains:

```json
{
  "make_log_tail": "<last 40 lines of make output, newline-joined>",
  "likely_cause": "lapack | generic"
}
```

If `likely_cause == "lapack"`, the user should install LAPACK development
libraries (`brew install lapack` on macOS; `sudo apt-get install liblapack-dev`
on Debian/Ubuntu).

---

## Env-var overrides

| Variable | Purpose | Default |
|----------|---------|---------|
| `HEPPH_SPHENO_VERSION` | Pin a specific SPheno release | `4.0.5` |
| `XDG_CONFIG_HOME` | Override config directory (test isolation) | `~/.config` |
| `HEPPH_STATE_ROOT` | Override per-model state root (test isolation) | `~/.local/share/hephaestus` |

See `plugins/hep-ph-toolkit/SHARED-model-building.md` for the full env-var table.

---

## Scripts

| File | Purpose |
|------|---------|
| `install.sh` | Main entry point (detect / use-path / install) |
| `check_gfortran.sh` | Checks for gfortran; emits `GFORTRAN_ABSENT` if missing |
| `_blocker.sh` | `emit_blocker` / `emit_blocker_with_context` bash helpers |
| `_make_log_parse.py` | Parses make.log; returns `SPHENO_BASE_BUILD_FAILED` blocker dict |

## Tests

| File | Type |
|------|------|
| `tests/test_detect_derive_src.sh` | Bash smoke: detect + use-path (binary + dir forms) |
| `tests/test_make_log_tail.py` | Python unit: last-40-lines tail + LAPACK detection |
| `tests/test_version_mismatch.sh` | Bash smoke: version mismatch → install-fresh-alongside |

Run:
```bash
# All Python unit tests:
python3 -m pytest plugins/hep-ph-toolkit/_shared/installs/spheno/tests/ -v

# Bash smoke tests (test isolation via tmp envs):
bash plugins/hep-ph-toolkit/_shared/installs/spheno/tests/test_detect_derive_src.sh
bash plugins/hep-ph-toolkit/_shared/installs/spheno/tests/test_version_mismatch.sh
```

---

## JSON status contract

| `status` | Meaning |
|----------|---------|
| `missing` | No SPheno install found anywhere |
| `found` | Binary found by scanning but not in config |
| `configured` | `spheno_path` (and optionally `spheno_src_path`) set in config |
| `version_mismatch` | Existing install is at a different version than the pin |
| `installed` | Fresh install completed successfully |
