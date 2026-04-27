# HiggsTools install workarounds

A catalogue of sharp edges surfaced during the WS-E playtest
(`dsu3-pt2/ws-e-r1-20260425`) and fixed or mitigated in tier-1.
Every entry lists: **symptom**, **cause**, **fix/workaround**, and the
**FU-id** that tracks or closed it.

Mirrors the style of
`plugins/hep-ph-toolkit/skills/micromegas-install/references/micromegas-workarounds.md`.

---

## 1. cmake 4.x incompatibility with `cmake_minimum_required < 3.5`

- **FU-id:** FU-wse-1

- **Symptom:** cmake ≥ 4.0 (e.g. 4.3.1) aborts the HiggsBounds or
  HiggsSignals build with:

  ```
  CMake Error: CMake's compatibility range is 3.5+.
  Compatibility range has not been specified for this project.
  ```

  HiggsBounds 5.10.2 declares `cmake_minimum_required(VERSION 3.1)` and
  HiggsSignals 2.6.2 declares `cmake_minimum_required(VERSION 3.3)` —
  both below the 3.5 floor that cmake 4.x enforces unless explicitly
  overridden.

- **Cause:** cmake 4.0 dropped forward-compatibility support for
  projects that do not specify `cmake_minimum_required` ≥ 3.5. The
  HB/HS CMakeLists.txt files are upstream code that hasn't been updated.

- **Fix:** Pass `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` on every cmake
  invocation when building HB-5 and HS-2:

  ```bash
  cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
           -DHiggsBounds_DIR=<hb-build>   # HS only
  ```

  This flag is the documented cmake escape hatch for exactly this
  situation. **It must be vendored into `install_higgstools.sh`** so
  that a fresh install on a cmake 4.x host succeeds without a manual
  workaround. The WS-E playtest applied it manually at run time (not
  committed); the tier-1 task `cmake4-compat` captures the script
  patch.

- **Upstream status:** Not yet fixed in HiggsBounds or HiggsSignals
  source. Until an upstream release bumps the `cmake_minimum_required`
  line, the flag is mandatory on cmake ≥ 4.0 hosts.

---

## 2. Stock `smoke_test.sh` broken — binary requires 6 args, script passes 1

- **FU-id:** FU-wse-2

- **Symptom:** Running `smoke_test.sh` after a fresh install exits
  non-zero with:

  ```
  HiggsSignals: Wrong number of arguments!
  Usage: HiggsSignals <expdata> <pdf> <whichinput> <nHzero> <nHplus> <prefix>
  ```

  No HiggsBounds or HiggsSignals result is written. The blocker
  `HIGGSTOOLS_SMOKE_TEST_FAILED` fires, even though both binaries are
  fully functional.

- **Cause:** `smoke_test.sh` (lines 88–142 on main) invokes
  `HiggsSignals "$SM_SLHA"` — a single positional argument. The HS 2.6.2
  binary requires exactly six: `<expdata> <pdf> <whichinput> <nHzero>
  <nHplus> <prefix>`. The script was written against an older calling
  convention.

- **Canonical surrogate (current practice):** Build and run the
  `HS_SM_LHCRun1` example program shipped in the HS source tree:

  ```bash
  cd ~/HiggsSignals-2.6.2/example_programs
  make HS_SM_LHCRun1
  ./HS_SM_LHCRun1 mh=125.1
  ```

  Reference output: χ²=20.593 at mh=125.1 GeV (SM, pdf=2).
  The SM-reference chi² cache at
  `~/.local/share/hephaestus/cache/hs2_chi2_sm_ref.json` is written
  by `scripts/cache_sm_reference.py` using this surrogate output.
  The WS-E playtest cached:

  ```json
  {
    "chi2_sm_ref": 20.593,
    "ndf": 10,
    "hb_version": "5.10.2",
    "hs_version": "2.6.2",
    "mh_gev": 125.1,
    "source": "HS_SM_LHCRun1"
  }
  ```

  Until `smoke_test.sh` is fixed upstream, treat `HS_SM_LHCRun1` +
  `cache_sm_reference.py` as the canonical smoke path. The chi²
  cache is what `/higgstools run` actually consumes; the HS binary call
  in `smoke_test.sh` is redundant once the cache is written.

- **Permanent fix:** Update `smoke_test.sh` to call the binary with all
  six arguments, or replace the inline invocation with a call to
  `cache_sm_reference.py` which already handles the arg list correctly.
  Tracked as follow-up `higgstools-smoke-fix`.

---

## 3. Backend choice: legacy (default) vs unified

- **FU-id:** FU-wse-3 (decision, not a bug)

- **Default:** The WS-E playtest landed on the **legacy backend
  (HB-5.10.2 + HS-2.6.2 Fortran)**. Unified C++ is opt-in via
  `--backend=unified` + `HEPPH_HIGGSTOOLS_BACKEND=unified`.

- **Why legacy is default:** The unified C++ build is unverified on
  macOS arm64 (Eigen/Boost ABI issues); CI targets ubuntu-22.04. On
  macOS arm64 build failure the skill emits recoverable
  `HIGGSTOOLS_BACKEND_UNAVAILABLE` and falls back to legacy.

- **Confirm your backend:** Check `config.json` for
  `"higgstools_backend": "legacy"`. Both backends emit the same
  `result.json` schema.
