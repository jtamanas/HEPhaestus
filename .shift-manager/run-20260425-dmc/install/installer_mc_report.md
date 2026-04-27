# Track 2 — micrOMEGAs + DDCalc install report

Run: `run-20260425-dmc`
Track: `installer-micromegas-ddcalc`
Host: macOS 15.x (Darwin 25.4.0), arm64 (Apple Silicon)
Toolchain: gfortran (Homebrew GCC 15.2.0_1) 15.2.0; Apple clang 21.0.0
Wall: ~1 minute total (both tools failed/succeeded fast)

---

## Summary

| Tool | Status | Path | Version |
|---|---|---|---|
| micrOMEGAs 6.0.5 | **FAILED** (build) | (none — no config write) | n/a — Zenodo fallback fetched 6.1.15 instead of 6.0.5; build then failed |
| DDCalc 2.2.0 | **INSTALLED_WITH_WARNINGS** | `/Users/yianni/.local/share/hep-ph-agents/tools/DDCalc` | `2.2.0` (config field polluted — see defect MD-D1) |

---

## Disk

| Stage | Free under `$HOME` |
|---|---|
| Pre-flight | 7.0 GiB |
| After micrOMEGAs failure | 6.8 GiB |
| After DDCalc install | 6.8 GiB |

micrOMEGAs failure consumed ~150 MB of half-built tree at `/Users/yianni/micrOMEGAs/micromegas_6.1.15/`. Tarball `/tmp/micromegas_6.0.5.tgz` (33 MB) still present. Disk margin remained healthy throughout — the original concern about "tight margin → don't proceed to DDCalc on smoke fail" was not relevant because the failure happened well before smoke and consumed minimal space.

---

## micrOMEGAs — FAILED

### Status
- Pre-flight (disk, gfortran, gmake, cc) passed.
- LAPTh primary URL `https://lapth.cnrs.fr/micromegas/downloadarea/micromegas_6.0.5.tgz` **failed on attempt 1** (exact error not retained — installer rotated to fallback after 2 retries).
- Zenodo fallback succeeded: downloaded `micromegas_6.1.15.tgz` from `https://zenodo.org/records/13376690/files/micromegas_6.1.15.tgz`. **Fallback pin diverges from intended 6.0.5 pin.**
- Tarball SHA256 (`micromegas_6.1.15.tgz`, saved as `/tmp/micromegas_6.0.5.tgz` per installer naming): `a8d13209fb2312875c7e17551514f7335428a2b65b85c7777f16175fcd49d9b2`
- Skill_env pinned SHA256 was `TODO` — verify_checksum warned, did not abort.
- Extraction OK to `/Users/yianni/micrOMEGAs/micromegas_6.1.15/`.
- macOS env helper sourced (`SDKROOT` set, `FFLAGS=-ff2c`, `LDFLAGS=-Wl,-ld_classic`).
- `make -j8` **failed (rc=2)** during CalcHEP_src link of `bin/plot_view`.

### Root cause
This is the exact known limitation flagged in `plugins/constraints/skills/micromegas-install/SKILL.md` lines 242–244:

> **Known limitation (v1.1):** `CalcHEP_src/getFlags` emits x86_64 flags on arm64 systems when using clang 15+, which causes build failures.

Linker error tail (verbatim from blocker JSON `context.make_log_tail`):

```
Undefined symbols for architecture arm64:
  "_f_printf", referenced from: _writetable0 in serv.a[3](file_scr.o) ...
  "_nextFileName", referenced from: _plot_Nar in serv.a[14](plot.o) ...
  "_pathtocalchep", referenced from: _main in view_tab-b98389.o ...
  "_sortie", referenced from: _m_alloc in serv.a[2](getmem.o) ...
  "_trim", referenced from: _plot_Nar in serv.a[14](plot.o) ...
ld: symbol(s) not found for architecture arm64
clang: error: linker command failed with exit code 1
make[3]: *** [../../bin/plot_view] Error 1
```

Symptom matches the SKILL.md description: CalcHEP's bundled `getFlags` script is producing an architecture mismatch between the static archive (`serv.a` built for one arch) and the executable link target (arm64). The CalcHEP getFlags fix is documented as a v1.1 ticket on the skill itself.

The blocker raised by the installer was the generic `MICROMEGAS_BUILD_FAILED` (exit 2). The installer did **not** pattern-match this to `LAPACK_ABSENT` because the regex (`lapack|liblapack|...`) doesn't catch the arch-mismatch signature — correctly so; it isn't a LAPACK problem.

### Smoke test
**Not exercised** — install never reached `_smoke.sh`. No `--full-smoke` MSSM run was attempted.

### Config keys written
**None.** `install_impl.sh` reaches `config_merge` only on success; no `micromegas_path` / `micromegas_version` etc. were written. Pre-existing config keys (madgraph, sarah, etc.) untouched.

### Suggested workaround for `/dark-matter-constraints` step 4
Per SKILL.md the recommended workaround is:
> Workaround: compile on an x86_64 machine or provide a pre-patched CalcHEP via `--calchep-path`.

A v1.1 fix to `CalcHEP_src/getFlags` is the proper remediation. Until then, `/dark-matter-constraints` cross-check via `/micromegas` is **NOT exercisable** on this Apple Silicon host through the auto-install path.

Possible v1.1 patch direction (for skill-author info, not a request to apply now): `getFlags` likely uses a `uname -m` or hard-codes `-arch x86_64`; either bypass it with `make HOSTTYPE=arm64 CC=clang FC=gfortran` overrides or vendor a small patch under `plugins/constraints/skills/micromegas-install/patches/`. Suggest a `make CALCHEP_TARGET_ARCH=arm64` or simply drop the `plot_view`/X11 GUI subtargets on arm64 — relic/SI/SD do not need them.

---

## DDCalc — INSTALLED_WITH_WARNINGS

### Status
- gfortran present (precondition met).
- Disk check (2 GB min, 4 GB warn): warned (low disk) — proceeded.
- macOS SDK probe: `LDFLAGS=-Wl,-ld_classic`, `SDKROOT=/Applications/Xcode.app/.../MacOSX.sdk`. OK.
- Download from primary URL `https://github.com/GambitBSM/DDCalc/archive/refs/tags/v2.2.0.tar.gz` succeeded on attempt 1.
- SHA256 verified against pinned `b12d63f7baafc6ee43e090fa3d1df15d194bddb453b3d5173e895fb3ac517847` — **OK**.
- Version banner patch applied.
- `make lib FC=gfortran FFLAGS="-std=legacy -fallow-invalid-boz -O2" CFLAGS="-Wno-implicit-function-declaration"` — succeeded.
- Smoke test: `libDDCalc.a` size 414288 bytes — passes `> 10000` byte threshold. (No `DDCalc_test` binary built; lib-size-only smoke is the documented fallback path.)

### Install path
`/Users/yianni/.local/share/hep-ph-agents/tools/DDCalc`
- `lib/libDDCalc.a` — 414,288 bytes
- `include/` — populated
- `data/` — populated
- Experiment subtrees present: `LZ`, `DARWIN`, `CRESST-II`, `CRESST-III`, `CDMSlite`, `DarkSide`, `DarkSide_50_S2`, `PICO-500`, `SDFF`, `Wbar`, `Halos`.

### Config keys written
- `ddcalc_path` = `/Users/yianni/.local/share/hep-ph-agents/tools/DDCalc`
- `ddcalc_version` = **POLLUTED** (see defect MD-D1)
- `ddcalc_installed_at` = `2026-04-25T20:08:53Z`
- `ddcalc_upstream_url` = `https://github.com/GambitBSM/DDCalc/archive/refs/tags/v2.2.0.tar.gz`
- `ddcalc_upstream_commit` = `9364c02dca3d23e75558e3238229a6fa41a8ec1a`
- `ddcalc_experiment_set` = `native`

### Smoke assertions
- `libDDCalc.a` exists at expected path: PASS
- `libDDCalc.a` size > 10000 bytes (414288): PASS
- `DDCalc_test` runtime check: SKIPPED (binary not produced by `make lib`)

---

## Defects surfaced (logged, not patched per directive)

### MD-M1 (micrOMEGAs, severity: blocker on arm64)
The known v1.1 limitation (`CalcHEP_src/getFlags` arm64 / clang 15+ link mismatch) is **active** and blocks the entire macOS-arm64 install path through this skill. Recommendation: prioritize the v1.1 fix; without it `/micromegas` and the MadDM-cross-check leg of `/dark-matter-constraints` are unreachable on this platform.

### MD-M2 (micrOMEGAs, severity: pin drift / silent version downgrade-upgrade)
LAPTh `https://lapth.cnrs.fr/micromegas/downloadarea/micromegas_6.0.5.tgz` failed on first try (could be transient or genuine 404 — installer log doesn't preserve curl exit code or HTTP status; only `WARN: LAPTh download failed` is recorded). Zenodo fallback then served `6.1.15`, not `6.0.5`. The installer's behaviour (warn + continue) matches the documented contract, but the dropped curl error string makes triage harder. Suggestion: capture and tee curl exit/HTTP-status into the log when LAPTh fails, before falling through. (Not a blocker.)

### MD-M3 (micrOMEGAs skill_env, severity: housekeeping)
`micromegas_sha256` is still `TODO` in `plugins/constraints/skills/micromegas-install/skill_env.yaml`. Computed today: `a8d13209fb2312875c7e17551514f7335428a2b65b85c7777f16175fcd49d9b2` for the **6.1.15 Zenodo fallback** (saved under filename `micromegas_6.0.5.tgz` per installer dest naming — independent of contents). The 6.0.5 LAPTh tarball couldn't be checksummed today (download failed). When LAPTh comes back up, both pins should be filled in.

### MD-D1 (DDCalc installer, severity: cosmetic but user-visible — config corruption)
`install_ddcalc.sh` at line 151 captures the smoke-test stdout into `DETECTED_VERSION`:
```
DETECTED_VERSION="$(bash "$SCRIPT_DIR/_smoke_test.sh" "$INSTALL_DIR" 2>&1)" || ...
```
But `_smoke_test.sh` `log "..."` writes to stdout (not stderr), so `DETECTED_VERSION` becomes a 2-line string:
```
[ddcalc-smoke] DDCalc library smoke test passed (no test binary; lib size=  414288 bytes).
2.2.0
```
This polluted value is then `config_merge`d as `ddcalc_version`. Result: `config.json` has `ddcalc_version` containing the literal log line plus newline plus `2.2.0`. Downstream code that does string-equality or version-parsing on `config.ddcalc_version` will likely break.

Suggested fix (NOT applied per "do not edit *-install scripts" directive):
- Either redirect `log` in `_common.sh` to stderr (cleanest; benefits all installers), or
- In `_smoke_test.sh` route the `log "..."` call before `echo "2.2.0"` to stderr (`log "..." >&2`), or
- In `install_ddcalc.sh` filter: `DETECTED_VERSION="$(bash "$SCRIPT_DIR/_smoke_test.sh" "$INSTALL_DIR" | tail -1)"`.

Pick whichever the skill author prefers. The DDCalc *install itself* is fine — `libDDCalc.a` builds and validates — so leaving the polluted config field in place doesn't risk anything load-bearing right now (no skill currently parses `ddcalc_version`). Track 2 leaves it as-is to honor the no-edit constraint.

### MD-D2 (DDCalc skill_env, severity: housekeeping)
`HEPPH_DDCALC_SHA256` was concrete and verified — no TODO here. Good.

---

## Updated `~/.config/hep-ph-agents/config.json` keys

Keys written this run (DDCalc only):
- `ddcalc_path`
- `ddcalc_version` (polluted — see MD-D1)
- `ddcalc_installed_at`
- `ddcalc_upstream_url`
- `ddcalc_upstream_commit`
- `ddcalc_experiment_set`
- `last_configured` (auto-bumped by `config_merge`)

Keys NOT written (because micrOMEGAs failed):
- `micromegas_path`, `micromegas_version`, `calchep_path`, `calchep_bundled`, `micromegas_installed_at` — all absent.

All previously-written keys (madgraph, maddm, sarah, spheno, models.*) untouched.

---

## Recommendation to manager: `/dark-matter-constraints` step 4 readiness

**NOT end-to-end exercisable on this host.** Specifically:

- **MadDM (primary DM driver)** — config has `maddm_path` and `madgraph_path` from prior runs; this leg is OK.
- **micrOMEGAs cross-check (validator role)** — **BLOCKED** by MD-M1 (CalcHEP arm64 getFlags). Step 4's whole purpose is "compute Ωh², σ_SI, σ_SD with both tools and reconcile." Without micrOMEGAs we have no second opinion.
- **DDCalc (direct-detection likelihood library)** — INSTALLED. The σ_SI/σ_SD numbers from MadDM can be run through DDCalc's experiment likelihoods, so step 4's DD-likelihood sub-leg works.

So the manager has two options:
1. **Defer step 4's micrOMEGAs cross-check** until the v1.1 CalcHEP arm64 fix lands, and have `/dark-matter-constraints` mark the cross-check as `SKIPPED_PLATFORM_BLOCKED` while still running MadDM + DDCalc end-to-end. This keeps the relic + DD path live.
2. **Hand-stage a working micrOMEGAs** via `/micromegas-install use-path <dir>` — would require a binary built elsewhere (x86_64 host or pre-patched CalcHEP). Not feasible from inside this run.

**Recommended:** option 1. Track 3's LoopTools+FeynArts install (running in parallel) does not depend on micrOMEGAs, so a downstream Profumo-paper reproduction pass remains viable for the LoopTools-driven BSM-Higgs portions of the DM workflow even with micrOMEGAs blocked.

---

## Logs

- micrOMEGAs streaming log: `.shift-manager/run-20260425-dmc/install/installers/installer_mc.log` (262 lines)
- DDCalc streaming log: `.shift-manager/run-20260425-dmc/install/installers/installer_ddcalc.log`
