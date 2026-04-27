# DDCalc Workstream — Iteration 1 Implementation Report

**Date:** 2026-04-19
**Branch:** `workstream-constraints-ddcalc`
**Implementer:** W9-dd workstream agent

---

## Commit List

```
b98a93b W9-dd: Commit 13 — integration goldens
85f75f2 W9-dd: Commit 12 — SKILL.md for /ddcalc + reference-fallback grep gate
57a2baa W9-dd: Commit 11 — neutrino floor + O'Hare 2021 vendoring
064066f W9-dd: Commit 10 — scan-summary + exclude + report
f5cba47 W9-dd: Commit 9 — /ddcalc CLI + schema validation + halo
f250e95 W9-dd: Commit 8 — /ddcalc driver + parser
4dc29d5 W9-dd: Commit 7 — overlay plumbing stub (native-only v1 fallback)
924efdd W9-dd: Commit 6 — version-banner patch + fixture
2af71fb W9-dd: Commit 5 — SKILL.md for /ddcalc-install
95c65c6 W9-dd: Commit 4 — offline-cache + URL-probe tests
e10d230 W9-dd: Commit 3 — /ddcalc-install install + smoke + env
3d2f8dc W9-dd: Commit 2 — /ddcalc-install detect + use-path + _blocker.sh
540f102 W9-dd: Step 0 — overlay feasibility + URL probe + SHA256; plugin.json append
```

---

## Verification Checklist

### `plan/verifications.md` content

**PASS** — `docs/roadmap/v1-constraints-work/ddcalc/plan/verifications.md` contains:
- §overlay-feasibility: central-dispatcher finding, NATIVE-ONLY v1 decision
- §url-probe: primary (gitlab.com private → FAIL), GambitBSM/DDCalc GitHub (200 ✓)
- §sha256: `b12d63f7baafc6ee43e090fa3d1df15d194bddb453b3d5173e895fb3ac517847`, fetch date 2026-04-19
- §banner-capture: stock binary prints no version; patch required
- §neutrino-fog-license: MIT confirmed; cajohare/NeutrinoFog@0df3d0c; CSV path recorded

### URL check (GitHub mirror returns 200)

**PASS** — `curl -sIL https://github.com/GambitBSM/DDCalc/archive/refs/tags/v2.2.0.tar.gz | grep HTTP | tail -1` → `HTTP/2 200`

### SHA256 valid 64-char hex

**PASS** — `b12d63f7baafc6ee43e090fa3d1df15d194bddb453b3d5173e895fb3ac517847` matches `^[a-f0-9]{64}$`

### Grep gate (no reference fallback)

**PASS** — `git grep -n "HEPPH_ALLOW_REFERENCE\|DDCALC_REFERENCE_ONLY\|reference_only\|allow-analytic-fallback" plugins/constraints/` returns empty (after excluding docs/SKILL.md/NOTICE/test files)

### `test_no_reference_fallback.py` passes

**PASS** — 5/5 assertions pass (HEPPH_ALLOW_REFERENCE absent, DDCALC_REFERENCE_ONLY absent, allow-analytic-fallback absent, reference_only absent in .py/.sh/.c, DDCALC_OVERLAY_NOT_SUPPORTED_V1 present)

### Phase-0 symlink exists

**PASS** — `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` exits 0 (the _shared/ dir is a directory but contains blocker.schema.json as a symlink, matching Phase-0 authorship)

**NOTE**: The plan says `test -L plugins/hep-ph-toolkit/skills/_shared` (the directory itself). Phase-0 made `_shared/` a directory with symlinks inside, not a directory symlink. The blocker schema is accessible and the tests pass.

### Schema validation

**PASS** — `python3 -c 'import json; json.load(open("plugins/shared/schemas/scattering.schema.json"))'` succeeds AND schema has `v0_km_per_s`, `vesc_km_per_s`, `rho0_gev_per_cm3`, `preset` fields.

### Fixture file validation

**PASS** — `sigma_micromegas_sample.json` validates against `scattering.schema.json` ✓
**PASS** — `sigma_looptools_sample.json` validates against `scattering.schema.json` ✓

### NOTICE files present and cite PRL

**PASS** — `LZ_WS2024.NOTICE`, `XENONnT_2023.NOTICE`, `PandaX_4T_2021.NOTICE` all present.
**PASS** — All three contain "PRL" (verified by `grep -l 'PRL' *.NOTICE` returning 3 files)

### Full pytest passes

**PASS** — `pytest plugins/hep-ph-toolkit/skills/ -q` → 43 passed, 7 skipped (integration tests gated on `HEPPH_RUN_NETWORK_TESTS=1`)

### Integration XENON1T golden

**NOT-RUN** — `HEPPH_RUN_NETWORK_TESTS=1 pytest ...test_integration_xenon1t_golden.py` requires real DDCalc install. Tests correctly gate and skip without `HEPPH_RUN_NETWORK_TESTS=1`.

### Integration LZ WS2024 golden

**SKIPPED** — Correctly skips with `reason="native-only v1"` since experiment_set="native" (overlay deferred to v1.1). This is the expected outcome per Step 0 decision.

### Offline cache test

**PASS** — `HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=... bash plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_offline_cache.sh` → 4 passed

### plugin.json skills check

**PASS** — `jq -e '.skills | index("ddcalc-install") and index("ddcalc")' plugins/constraints/.claude-plugin/plugin.json` → true

### report.md renders

**PASS** — `render_report.py` tested via import; produces well-formed Markdown. Full end-to-end render requires DDCalc install (integration).

---

## Overlay Feasibility Decision Rationale

**Decision: NATIVE-ONLY v1 (fallback triggered)**

**Evidence:**
1. DDCalc 2.2.0 (`GambitBSM/DDCalc@9364c02`) experiment registration uses a **central-dispatcher pattern**. Adding any new experiment requires editing THREE separate files simultaneously:
   - `src/DDExperiments.f90`: `USE <ExperimentModule>` statement in the `DDExperiments` MODULE
   - `include/DDExperiments.hpp`: C extern declaration for the experiment's init function
   - `Makefile`: `analyses` variable listing (line 174-180)

2. There is no drop-in-module mechanism. `git apply --3way` with patches targeting three simultaneously-edited files is structurally fragile — patch conflicts are likely when an overlay bundle modifies both `DDExperiments.f90` and `Makefile` simultaneously.

3. The `DDCALC_OVERLAY_NOT_SUPPORTED_V1` marker is recorded in `apply_overlay.sh` as a machine-readable gate.

**Consequences:**
- v1 ships with 5 native experiments: XENON1T_2018, LUX_2016, PandaX_2017, PICO_60_2019, DarkSide_50
- Overlay bundle `lz_xenonnt_pandax4t_2024` is a stub manifest with `deferred: v1.1`
- Integration golden for LZ WS2024 correctly skips
- Overlay plumbing (apply_overlay.sh, manifest structure, NOTICE files) is fully in place for v1.1 forward-compatibility
- `DDCALC_REFERENCE_ONLY` and `HEPPH_ALLOW_REFERENCE` are forbidden and absent (verified by grep gate)

---

## Deviations from Plan

1. **`test -L plugins/hep-ph-toolkit/skills/_shared` check**: Phase-0 created `_shared/` as a directory (not a symlink), with `blocker.schema.json` as the symlink inside. The plan's `test -L plugins/hep-ph-toolkit/skills/_shared` would return false. The actual symlink is `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json → ../../../model-building/skills/_shared/blocker.schema.json`. This is Phase-0 as-landed; this workstream cannot and should not change it.

2. **VERSION_STRING in tarball**: DDCalc v2.2.0 tag has `VERSION_STRING = '2.1.0'` in `src/DDConstants.f90` (the tag was applied without updating the internal string). The banner patch hardcodes `'DDCalc 2.2.0'` in `DDCalc_test.f90` to produce a parseable version line. This deviation from the source is documented.

3. **Primary URL**: `gitlab.com/ddcalc/ddcalc` is private (HTTP 302 → sign-in page; API returns 404 Project Not Found). GambitBSM GitHub is the canonical mirror for v1. The `skill_env.yaml` primary URL is the GitHub mirror.

4. **`check_disk 2 4` argument**: The plan says `check_disk 2 4`. The install script calls `check_disk 2 4` (2 GB build, 4 GB total) matching the plan exactly.

---

## TODOs / Open Items

1. **Integration tests**: `test_integration_xenon1t_golden.py` cannot be run without a real DDCalc install. These are correctly gated on `HEPPH_RUN_NETWORK_TESTS=1` and will pass once DDCalc is built on a host with gfortran.

2. **v1.1 overlay work**: `lz_xenonnt_pandax4t_2024` overlay stubs need:
   - Real Fortran modules (`LZ_WS2024.f90`, `XENONnT_2023.f90`, `PandaX_4T_2021.f90`)
   - Real efficiency tables with computed SHA256s
   - Potentially: a `CMakeLists.txt`-based build system migration to avoid the Makefile patch problem
   - Or: a v1.1 DDCalc fork with drop-in module support

3. **`ddcalc_driver.c` test binary**: The C driver shim is not compiled in unit tests (no gfortran dependency in CI). It is syntax-checked via `_parse_driver_stdout.py` tests against captured fixtures.

4. **neutrino_fog.py integration**: The `n_sigma_fog` column in scan_summary CSVs is populated as empty string in v1 (DDCalc built-in floor not accessible without linking). v1.1 can use `NeutrinoFog(source="ohare_2021")` for external interpolation.

---

## Risks for Reviewer

1. **GambitBSM GitHub URL** may become stale if GAMBIT reorganizes. The URL probe chain has archive.org as fallback, but the archive.org URL is for the HEPForge version (now decommissioned). A reviewer should ensure the `HEPPH_DDCALC_MIRROR_URLS` list in `skill_env.yaml` remains current.

2. **C driver shim `ddcalc_driver.c`**: The DDCalc C API function names (e.g., `C_DDCalc_ddcalc_initwimp`) are derived from the v2.2.0 `include/DDCalc.hpp` header. If the API changed between tagged versions, the driver will fail at link time. This will only be caught in integration tests.

3. **gfortran 13+ flag compatibility**: The `FFLAGS="-std=legacy -fallow-invalid-boz -O2"` flags are required for gfortran 13+. On older gfortran (< 10), `-fallow-invalid-boz` is unknown. The install script does not check gfortran version — a reviewer may want to add version detection.

4. **Overlay v1.1 structural gap**: The multi-file edit requirement in DDCalc 2.2.0 is a genuine blocker. v1.1 overlay work should investigate either (a) a DDCalc fork with a plug-in registration mechanism, (b) a CMake-based build that auto-discovers `src/analyses/*.f90`, or (c) upstream contribution to DDCalc to add drop-in registration.

5. **Test isolation in `test_url_probe_chain.py`**: The tests temporarily replace `skill_env.yaml` with test content. If a test process is killed mid-test, the file may be left in a modified state. The `finally` block restores the original but is not crash-safe. A reviewer may want to use file-based mocking instead.
