# Track 3 Installer Report — installer_mathematica

**Run:** `run-20260425-dmc`
**Track:** 3 (Mathematica/Fortran chain — LoopTools + FeynArts)
**Date (UTC):** 2026-04-25
**Wall time:** ~6 min (well under 30 min budget)

---

## Pre-flight

| Check | Value |
|---|---|
| `df -h $HOME` (start) | 7.0 GiB free / 228 GiB total (97% used) |
| `df -h $HOME` (end) | 6.6 GiB free (~400 MB consumed by both tools + tarball cache) |
| `wolframscript` | `/usr/local/bin/wolframscript`, WolframScript 1.13.0 (drives Wolfram Engine 14.3.0) |
| `gfortran` | `/opt/homebrew/bin/gfortran`, GNU Fortran (Homebrew GCC 15.2.0_1) 15.2.0 |
| `$UserBaseDirectory` (resolved via `wolframscript -code 'Print[$UserBaseDirectory]'`) | `/Users/yianni/Library/WolframEngine` |

Note on `$UserBaseDirectory`: the manager scout expected `~/Library/Wolfram/`, but Wolfram **Engine** 14.3 (vs full Mathematica) uses `~/Library/WolframEngine`. The actual install ended up at `~/Library/WolframEngine/Applications/FeynArts-3.11/` — consistent with the SKILL.md note about the Linux Wolfram-Engine path convention, just on macOS.

---

## Tool 1: LoopTools 2.16 — INSTALLED_WITH_WARNINGS

| Field | Value |
|---|---|
| Status | INSTALLED_WITH_WARNINGS (light smoke OK; full smoke parser bug, numbers verified manually) |
| Install path | `/Users/yianni/LoopTools/LoopTools-2.16` |
| Source path | `/Users/yianni/LoopTools/LoopTools-2.16` (retained, same prefix) |
| Version | 2.16 (release date 2024-11-02) |
| Tarball URL | `https://feynarts.de/looptools/LoopTools-2.16.tar.gz` |
| Tarball SHA256 (computed) | `4113467575db3a14405d62d9e516b3b90410b73ea8d20c8eb8d70a30fc5cc9cb` |
| skill_env.yaml SHA256 | `TODO` (placeholder; see TODOs below) |
| Light smoke (`probe_looptools.sh`) | PASS — `lib/libooptools.a` (2.7 MB), `bin/lt` (2.0 MB), `include/looptools.h`, `include/clooptools.h` all present |
| Full smoke (`probe_looptools.sh --full-smoke`) | FAIL (parser bug — see below); numerical values verified manually OK |
| MathLink available | `false` (no Mathematica kernel found at configure time; `make lib` only) |

### Full-smoke failure detail

The B0 test program built successfully and produced the **exact expected numerical output**:
```
B0_SMOKE      -4.4059328       2.7041431
```
This matches the spec's expected `(-4.40593283, 2.7041431)` to 7 decimals.

The probe script reports `FAIL` because of a **shell-redirection bug in `probe_looptools.sh` lines 109–123**: the heredoc `python3 - <<'PY'` rebinds python3's stdin to the heredoc body, which then collides with the upstream `printf | python3` pipe — so python3 reads no captured output and the regex never matches. Verified by running the same regex manually on the real binary stdout: it matches and the tolerance check passes.

**This is a probe script bug, not a LoopTools build problem.** Per manager constraints we did not edit the skill. Logged as a TODO below. The light smoke (file-presence) is what `install` runs by default and that succeeded.

### Config keys written (LoopTools)

```json
{
  "looptools_path": "/Users/yianni/LoopTools/LoopTools-2.16",
  "looptools_src_path": "/Users/yianni/LoopTools/LoopTools-2.16",
  "looptools_version": "2.16",
  "looptools_gfortran_path": "/opt/homebrew/bin/gfortran",
  "looptools_gfortran_version": "GNU Fortran (Homebrew GCC 15.2.0_1) 15.2.0",
  "looptools_mathlink_available": "false",
  "looptools_installed_at": "2026-04-25T20:08:54Z"
}
```

`looptools_gfortran_version` recorded as required for downstream compiler-coherence checks (FormCalc/SPheno will read this).

---

## Tool 2: FeynArts 3.11 — INSTALLED_WITH_WARNINGS

| Field | Value |
|---|---|
| Status | INSTALLED_WITH_WARNINGS (smoke passed; required two skill-script workarounds) |
| Install path | `/Users/yianni/Library/WolframEngine/Applications/FeynArts-3.11` |
| Version | 3.11 (confirmed by smoke test reading `$FeynArts\`$Version`) |
| Tarball URL | `https://www.feynarts.de/FeynArts-3.11.tar.gz` |
| Tarball SHA256 (computed) | `790e500ca7160614f98f0e78f572d132befa0b488ba73ccb3b91b8374376fd57` |
| skill_env.yaml SHA256 | `TODO` (bypassed via `HEPPH_FEYNARTS_SKIP_SHA256=1` per manager guidance) |
| Smoke test (`smoke_test_feynarts.sh`) | PASS — `{"status":"ok","version":"3.11"}` |
| `Lorentz.gen` SHA256 | `5415eb36c8024136c8b4befcc4bd3434cb38a76dc88182e3137254a1bd194657` |

### Skill-script bugs encountered (not edited; worked around)

Both bugs are in the FeynArts install scripts. They cascade through three scripts (`install_feynarts.sh`, `use_path_feynarts.sh`, `smoke_test_feynarts.sh`), all of which have the same root cause.

**Bug 1: `SCRIPT_DIR` clobber via sourcing.** After `. "$DETECT_WOLFRAM"` (line 21 of install_feynarts.sh), the script's own `SCRIPT_DIR` variable gets overwritten by detect_wolfram.sh's `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`. The next line `. "$SCRIPT_DIR/_blocker.sh"` then tries to load `_blocker.sh` from `plugins/shared/install-helpers/wolfram/` instead of from `feynarts-install/scripts/`. Same issue with the later invocations of `use_path_feynarts.sh` and `smoke_test_feynarts.sh`.

**Workaround:** created two symlinks (NOT skill edits) so the wrong-but-deterministic resolved paths point to the real files:
- `plugins/shared/install-helpers/wolfram/_blocker.sh` -> `plugins/feynman-diagrams/skills/feynarts-install/scripts/_blocker.sh`
- `plugins/shared/install-helpers/wolfram/smoke_test_feynarts.sh` -> `plugins/feynman-diagrams/skills/feynarts-install/scripts/smoke_test_feynarts.sh`

**Bug 2: `$UserBaseDirectory` newline-collapse produces bogus path `~/Library/WolframEngineNull/`.** Line 46 of install_feynarts.sh:
```bash
USER_BASE_DIR="$("$WS" -code 'Print[$UserBaseDirectory]' 2>/dev/null | tr -d '\n\r' || true)"
```
`Print[$UserBaseDirectory]` writes `/Users/yianni/Library/WolframEngine\nNull\n` to stdout (because `Print` returns `Null` and wolframscript prints that too). `tr -d '\n\r'` concatenates them → `/Users/yianni/Library/WolframEngineNull`. The script then extracted the tarball into `/Users/yianni/Library/WolframEngineNull/Applications/FeynArts-3.11/`.

**Workaround:** moved the extracted tree to the correct path:
```bash
mv /Users/yianni/Library/WolframEngineNull/Applications/FeynArts-3.11 /Users/yianni/Library/WolframEngine/Applications/FeynArts-3.11
rmdir /Users/yianni/Library/WolframEngineNull/Applications /Users/yianni/Library/WolframEngineNull
```
Then registered the install by invoking `use_path_feynarts.sh` (which still hit Bug 1, so I bypassed by running `smoke_test_feynarts.sh` directly — it passed — and writing the four config keys via the `config_merge` helper from `_common.sh`). All four required keys are present and correct.

The right fix in the script would be to use `wolframscript -code 'WriteString[$Output, $UserBaseDirectory]'` (no trailing `Null`) or `wolframscript -code '$UserBaseDirectory' -format Text` (clean string output). Logged as TODO.

### Config keys written (FeynArts)

```json
{
  "feynarts_path": "/Users/yianni/Library/WolframEngine/Applications/FeynArts-3.11",
  "feynarts_version": "3.11",
  "feynarts_installed_at": "2026-04-25T20:12:10Z",
  "feynarts_generic_model_hash": "5415eb36c8024136c8b4befcc4bd3434cb38a76dc88182e3137254a1bd194657"
}
```

### Smoke test detail

```
[smoke_test_feynarts] Running FeynArts smoke test (path=/Users/yianni/Library/WolframEngine/Applications/FeynArts-3.11)...
[smoke_test_feynarts] FeynArts smoke test passed: version=3.11
{"status":"ok","version":"3.11"}
```

Wolfram Engine activation is OK (no `activation_required` returned). FeynArts loads cleanly via `Needs["FeynArts\`"]`.

---

## TODOs surfaced (skill-level, not in scope this run)

1. **`probe_looptools.sh` heredoc/pipe parser bug** (full smoke). Affects the `--full-smoke` mode; `install` only runs light smoke by default so it doesn't surface there. Fix: capture the upstream output to a temp file and feed it to python3 as an arg, or rewrite the python check inline without heredoc-stdin collision. File: `plugins/model-building/skills/looptools-install/scripts/probe_looptools.sh:109-123`.

2. **`install_feynarts.sh` `$UserBaseDirectory` newline-collapse**. File: `plugins/feynman-diagrams/skills/feynarts-install/scripts/install_feynarts.sh:46`. Replace `Print[...] | tr -d '\n\r'` with a clean output form.

3. **`SCRIPT_DIR` clobber in FeynArts install scripts**. Three scripts share the issue. Fix: snapshot `SCRIPT_DIR` to a different name (`MY_SCRIPT_DIR`) before sourcing helpers that also set `SCRIPT_DIR`. Files: `install_feynarts.sh`, `use_path_feynarts.sh`, `smoke_test_feynarts.sh`. (My symlink workaround leaves the symlinks in `plugins/shared/install-helpers/wolfram/` — these can be removed once the scripts are fixed.)

4. **SHA256 pinning** for both tools' `skill_env.yaml`. Computed values from this run:
   - LoopTools 2.16: `4113467575db3a14405d62d9e516b3b90410b73ea8d20c8eb8d70a30fc5cc9cb`
   - FeynArts 3.11: `790e500ca7160614f98f0e78f572d132befa0b488ba73ccb3b91b8374376fd57`

---

## Recommendation: state of the DD chain

The full DD chain is **FeynArts → FormCalc → Package-X → DDCalc**.

| Link | State after this run |
|---|---|
| FeynArts | INSTALLED, smoke passes |
| FormCalc | DEFERRED (manager: ~3 GB build needs more disk than Track 2 leaves) |
| Package-X | DEFERRED (`UPSTREAM_UNREACHABLE_2026_04` per its skill_env.yaml) |
| DDCalc | being installed by Track 2 in parallel |

**The chain is not yet runnable end-to-end** — FormCalc and Package-X are still missing and they sit between FeynArts and DDCalc. Realistically, what we got from Track 3 is:

- LoopTools is the **prerequisite** for the Profumo 2HDM+a paper Fortran build (per `looptools-install/SKILL.md`). It's now in place with `looptools_gfortran_version` recorded for compiler-coherence checks when FormCalc eventually arrives.
- FeynArts gives us the **diagram-generation** front-end of the chain. Anything that only needs `CreateTopologies / CreateFeynAmp` can run today (e.g., generating Feynman diagrams, exporting amplitude lists). The amplitude-to-numerics handoff still requires FormCalc.
- The next gating decision is **disk capacity for FormCalc**. Once Track 2 frees its working set or disk is expanded, FormCalc can be re-attempted; once FormCalc is in place and the Package-X upstream is reachable again, the chain closes.

So: **Track 3 unblocks the upstream half of the chain (diagram generation) and pre-positions LoopTools for the Profumo paper, but does not by itself make DD runnable.** This matches the manager's expectation.

---

## Constraints honored

- No worktree, no commits, no skill edits (only symlinks added under `plugins/shared/install-helpers/wolfram/` as workarounds, and one filesystem move under `~/Library/WolframEngine/`).
- No `sudo` invoked.
- No out-of-scope installs (FormCalc/Package-X not attempted).
- Track 2 working paths untouched.
- Total wall time well under 30 min budget.

## Artifacts

- Install log: `.shift-manager/run-20260425-dmc/install/installers/installer_mathematica.log`
- This report: `.shift-manager/run-20260425-dmc/install/installer_mathematica_report.md`
- Workaround symlinks (remove once skill bug 3 is fixed):
  - `plugins/shared/install-helpers/wolfram/_blocker.sh`
  - `plugins/shared/install-helpers/wolfram/smoke_test_feynarts.sh`
- Tarball cache (can be cleaned): `/tmp/looptools-2.16.tar.gz`, `/tmp/feynarts-3.11.tar.gz`
