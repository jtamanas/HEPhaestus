# W2 `/spheno-install` Review — R1

## Verdict: APPROVE

## Test results
- pytest: 13 passed in 0.01s (`plugins/hep-ph-toolkit/skills/spheno-install/tests/`)
- bash (detect_derive_src): 5 passed, 0 failed
- bash (version_mismatch): 2 passed, 0 failed

## Findings

### Blocker
- none

### Major
- none

### Minor
- `SPHENO_SHA256="TODO"` at line 37 — script documents that `verify_checksum` warns-not-aborts for TODO and must be updated pre-v1. Known pre-v1 placeholder; fine to land but track for v1 cut.
- `test_make_log_tail.py` has no `HEPPH_STATE_ROOT` / `XDG_CONFIG_HOME` isolation, but it is a pure unit test against fixture log strings and never touches config state — no isolation needed. No action required.

### Nit
- `fixtures/` and `__pycache__` sit alongside tests; consider `.gitignore` entry for `__pycache__` under this skill if not already covered globally.

## Check-by-check

1. **Scope** — diff touches only `plugins/hep-ph-toolkit/skills/spheno-install/**` (9 files, 1267+ lines). Clean.
2. **Dual-key writes** — `_record_install` writes both `spheno_path` and `spheno_src_path` atomically (lines 108–114); `use-path` binary form derives src and records both (lines 177–184); `use-path` source form records both (lines 196–207). Every success path writes both keys. **Yes.**
3. **`use-path` dual form** — Case 1 binary (`-x "$path"` and basename `SPheno`, lines ~168–184); Case 2 source tree (`-d "$path"` with `Makefile`, lines 196–207); explicit error message for neither. **Both forms handled.**
4. **Version-mismatch policy** — lines 228–241: on mismatch, logs "Installing fresh alongside", emits `action:"installing_fresh_alongside"` announcement, installs into a new versioned subdir and updates both keys. Install-fresh-alongside, not warn-and-continue.
5. **Source tree retained** — zero `rm -rf` or `rm -r` in `install_spheno.sh`. Source tree is not deleted post-build.
6. **SKILL.md substantive** — first 40 lines define three modes (detect/use-path/install), decision flow, and invocation triggers. Not a stub.

Ready to merge.
