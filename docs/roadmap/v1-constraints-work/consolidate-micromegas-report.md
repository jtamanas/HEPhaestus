# /micromegas-install consolidation report

**Date:** 2026-04-19
**Branch:** `main`
**Parent ref (pre-consolidation):** `4032f03`
**Head ref (post-consolidation):** `092f1e1`

## Scope

Two `/micromegas-install` skills lived side-by-side in the repo:

- `plugins/hep-ph-toolkit/skills/micromegas-install/` — v1 audited code; lead role (relic/SI/SD driver for `/micromegas`).
- `plugins/hep-ph-toolkit/skills/micromegas-install/` — v0 code; framed as the MadDM validator.

This consolidation folds the v0 monte-carlo-tools tree into the v1 constraints tree so a single canonical skill serves both roles.

## Before / after

**Before** (tracked files):

| Path | Files |
|------|-------|
| `plugins/hep-ph-toolkit/skills/micromegas-install/` | 1 SKILL.md, 8 scripts, 7 tests, 6 blocker fixtures, 1 fake tree |
| `plugins/hep-ph-toolkit/skills/micromegas-install/` | 1 SKILL.md, 4 scripts, 1 test, 1 fixture tree, 1 README |
| `plugins/monte-carlo-tools/.claude-plugin/plugin.json` | listed 6 skills (including micromegas-install) |

**After**:

| Path | Files |
|------|-------|
| `plugins/hep-ph-toolkit/skills/micromegas-install/` | 1 SKILL.md, **10** scripts (+check_toolchain, +validate), **9** tests (+test_validate_subcommand, +test_toolchain_check), 6 blocker fixtures, 1 fake tree |
| `plugins/hep-ph-toolkit/skills/micromegas-install/` | **removed** |
| `plugins/monte-carlo-tools/.claude-plugin/plugin.json` | lists 5 skills |

`git grep 'monte-carlo-tools/skills/micromegas-install'` returns empty in tracked source.

## Migration decisions

### Kept (from constraints v1)

These were part of the v1 audited contract and preserved verbatim:

- **Version pin `6.0.5`** (not the monte-carlo v0 default `6.2.3`). Rationale: v1 is gated on this pin; `/micromegas` SKILL.md and downstream fixtures reference 6.0.5.
- **5-key config contract**: `micromegas_path`, `micromegas_version`, `calchep_path`, `calchep_bundled`, `micromegas_installed_at`. The v0 version only wrote 3 keys; v1 adds `calchep_path` + `calchep_bundled` to support the external CalcHEP `--calchep-path` option.
- **`HEPPH_NO_NETWORK` + `HEPPH_OFFLINE_CACHE_DIR`** strict offline contract.
- **`_netguard.sh`** — PATH-sandbox detection of `curl`/`wget`/`git` during `make` → `MICROMEGAS_BUILD_NEEDS_NETWORK`.
- **`_macos_env.sh`** — `check_macos_sdk` integration + `MICROMEGAS_MACOS_SDK_MISMATCH`.
- **Dispatcher layout**: `install_micromegas.sh` → `detect.sh` / `use_path.sh` / `install_impl.sh`. (v0 had a single 430-line `install.sh`; v1's split is cleaner.)
- **PPPC tables check** at stage 8 of `install_impl.sh`.

### Migrated (from monte-carlo-tools v0)

New capabilities added to the v1 tree:

- **`scripts/check_toolchain.sh`** — cc/gfortran/gmake precondition with per-OS install hints (macOS / Debian / RHEL). X11 dev headers are warn-only. Wired into `install_impl.sh` at **stage 5.5** (after download, before `make`) so the `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY` test path stays reachable on hosts without a full toolchain. Skippable via `HEPPH_SKIP_TOOLCHAIN_CHECK=1` (mirrors `HEPPH_SKIP_DISK_CHECK=1`).
- **`scripts/validate.sh`** + `install_micromegas.sh validate` subcommand — read-only re-validation of the currently configured install. Asserts markers + runs light smoke. **Does not modify config** (tested explicitly).
- **LAPACK_ABSENT detection** — build-failure log-tail sniff on `install_impl.sh` with regex `lapack|liblapack|-llapack|dgesv|dgemm|dgetrf|dsyev`. Emits the specific `LAPACK_ABSENT` blocker with a per-OS install hint rather than the generic `MICROMEGAS_BUILD_FAILED`.
- **Zenodo mirror fallback** — in **network mode only** (offline mode remains strict cache-only per `HEPPH_NO_NETWORK` policy). If LAPTh fails twice, installer falls back to `https://zenodo.org/records/13376690/files/micromegas_6.1.15.tgz` and rewrites `install_dir` / `MICROMEGAS_VERSION` to match the fallback tarball's layout (`micromegas_6.1.15/`).
- **`--full-smoke` flag** on `install` — optional compile + run of the MSSM reference example after the mandatory light smoke. Adds ~5 min on first run; MSSM failures emit `MICROMEGAS_SMOKE_TEST_FAILED` with `context.mssm_smoke_log_tail`.
- **Dual-role SKILL.md** — top-level `description` mentions both roles; new "Roles" section explicitly documents lead-role (for `/micromegas`) and validator-role (for `/maddm` cross-checks) with reference to the project's DM-tool-roles memory.

### Dropped

Intentionally not carried over from the v0 tree:

- **v0 `install.sh` monolithic dispatcher**: replaced by the v1 four-way split (`install_micromegas.sh` + `detect.sh` + `use_path.sh` + `install_impl.sh` + new `validate.sh`).
- **v0 version pin 6.2.3** and its LAPTh URL variant (`https://lapth.cnrs.fr/micromegas/micromegas_${V}.tgz` without `/downloadarea/`). The v1 path is `/micromegas/downloadarea/...`; the v0 URL is kept only implicitly via the Zenodo fallback.
- **v0 `probe_micromegas.sh`** — v1 `_smoke.sh` already covers the marker + compile-stub flow; v0's `probe_version` strategy (MICROMEGAS_VERSION / README / basename) is a superset but not needed because v1 prefers `include/VERSION` + basename heuristic already in `detect.sh`.
- **v0 `test_detect.sh`** — fully redundant with existing v1 coverage in `test_detect_states.sh` + `test_use_path_validation.py`.
- **v0 fixture tree** at `tests/fixtures/micromegas_6.2.3/` — redundant with `tests/fixtures/fake_micromegas_tree/`.
- **v0 `_blocker.sh`** variant — uses bash `printf` + python-escape, less robust than v1's python-subprocess implementation with optional `jsonschema` validation.

## Cross-references checked

- **`/maddm` SKILL.md and scripts** — no references to `plugins/hep-ph-toolkit/skills/micromegas-install` path, none needed to be rewritten.
- **`/micromegas` SKILL.md** — already references `/micromegas-install` (skill name, not path); resolves to the consolidated constraints skill automatically.
- **`plugins/monte-carlo-tools/scripts/install-followup.sh`** — regex `^(drake-install|maddm-install|micromegas-install)$` matches by skill name; still works for the hook post-install prompt regardless of which plugin hosts the skill.
- **`docs/roadmap/`** — 16 historical doc references to `monte-carlo-tools/micromegas-install` remain in planning/brainstorming/impl writeups. These are historical records of the original proposal and are **intentionally not rewritten** — they document the repo at the time they were written.

## Test deltas

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| `pytest plugins/ --import-mode=importlib -q` | 846 passed | **856 passed** | **+10** |
| Skipped | 43 | 43 | 0 |
| Xfailed | 1 | 1 | 0 |
| Shell smoke (`test_detect_states.sh`, `test_netguard.sh`, `test_macos_env.sh`) | PASS | PASS | — |

New tests in `plugins/hep-ph-toolkit/skills/micromegas-install/tests/`:

- `test_toolchain_check.py` — 6 tests (CC/GFORTRAN/GNU_MAKE absence, all-present, make-as-GNU-make, X11 warn-only).
- `test_validate_subcommand.py` — 4 tests (no-config, missing-dir, missing-markers, read-only-on-valid-tree).

## Commits

Listed in order:

1. `3d49c93` — consolidate: merge MadDM-validator semantics into constraints/micromegas-install
2. `3431bb6` — consolidate: tests for validate subcommand + check_toolchain migration
3. `092f1e1` — consolidate: remove monte-carlo-tools/skills/micromegas-install
4. *(this commit)* — consolidate: write consolidation report

## Remaining TODOs

Not blocking the consolidation, but noted for follow-up:

- **`MICROMEGAS_SHA256 = "TODO"`** — still present in both `install_impl.sh` entries. Pre-v1 release must compute and pin the SHA256 of `micromegas_6.0.5.tgz` and the Zenodo `6.1.15` fallback tarball so `verify_checksum` tightens from warn → abort on mismatch.
- **Zenodo fallback version is stale by design** — pinned at `6.1.15`, not the latest. Should re-evaluate before v1 release.
- **v1.1 backlog:** arm64 CalcHEP_src/getFlags patch (documented under "macOS build notes" in SKILL.md); 6.1.x pin upgrade gated on W3 UFO 2.0 output; `/micromegas --scan` run_point.run() wiring.
- **Optional: add a dedicated `test_lapack_signature_detection.py`** that feeds a crafted make-log tail through a subprocess-level harness to assert `LAPACK_ABSENT` fires on the signature regex. Not added in this consolidation because the functionality is simple grep and the existing offline-cache / smoke tests exercise the error path mechanically; a unit test for the regex branch is low-marginal-value but would tighten coverage.
- **Optional: `/dark-matter-constraints` meta-skill** (still planned; see `project_dm_tool_roles.md` memory) should consume this consolidated install skill's `validate` subcommand before scheduling a MadDM + micrOMEGAs cross-check run.

## Constraints respected

- Did not touch `/maddm`, `/drake-install`, `/feynrules-install`, `/looptools-install`.
- Did not touch v1 constraint skills `ddcalc`, `higgstools`, `feynarts`, `formcalc`, `looptools`.
- Did not modify Phase-0 shared schemas/helpers (`plugins/shared/install-helpers/`, `plugins/hep-ph-toolkit/skills/_shared/`).
- Used `git rm -r`, never `rm -rf`.
- Worked on `main`; no force-push, no hook skipping, no config changes.
- All commits prefixed with `consolidate: `.
