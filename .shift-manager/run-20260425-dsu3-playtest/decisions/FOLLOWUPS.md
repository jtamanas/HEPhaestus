# FOLLOWUPS — run-20260425-dsu3-playtest

Append-only. Each WS logs follow-up items here per §6.2 schema.

---

## WS-A follow-up items

```yaml
- id: FU-wsa-01
  ws_origin: ws-a
  cycle_origin: 1
  filed_at: 2026-04-25T12:00:00-07:00
  title: "run_tests.sh uses python -m pytest (broken on this pyenv)"
  category: test
  severity: minor
  status: open
  evidence_pointer: ".shift-manager/run-20260425-dmc/playtest/playtester_cycle1_report.md bug #7"
  proposed_resolution: >
    run_tests.sh line 106: change `python -m pytest` to `pytest` (the binary works;
    `python -m pytest` fails because the py module has a broken `path` attribute on
    this pyenv installation). OR: the test acceptance gate should call `pytest`
    directly rather than via `python -m pytest`.

- id: FU-wsa-02
  ws_origin: ws-a
  cycle_origin: 1
  filed_at: 2026-04-25T12:00:00-07:00
  title: "manifest_minimal.json not updated to v1.1 schema_version"
  category: test
  severity: minor
  status: open
  evidence_pointer: "plugins/constraints/skills/dark-matter-constraints/tests/fixtures/helpers/check_prereqs/manifest_minimal.json"
  proposed_resolution: >
    manifest_minimal.json still declares schema_version: router_contract/v1 and lacks
    severity fields in config_keys. It is used only for unit test isolation (not
    validated against the self-schema). Future: bump to v1.1 and add severity
    annotations so it reflects the live contract exactly.

- id: FU-wsa-03
  ws_origin: ws-a
  cycle_origin: 1
  filed_at: 2026-04-25T12:00:00-07:00
  title: "darkSU3 stub UFO files are placeholders — not a real UFO"
  category: upstream
  severity: major
  status: open
  evidence_pointer: "tests/fixtures/dark_su3_playtest/ufo/darkSU3/particles.py"
  proposed_resolution: >
    The stub files (particles.py, vertices.py, __init__.py) created in commit A3
    satisfy the sentinel check but do not produce a working UFO. MadGraph will still
    fail on dt1 color tensor NameErrors if asked to load this UFO. The real fix is
    tracked in decisions/dark_su3_ufo_followup.md (WS-L, scoped out of this run).
    A future run must either regenerate the UFO via SARAH with a post-build patch,
    or implement analytic_models.dark_su3.

- id: FU-wsa-04
  ws_origin: ws-a
  cycle_origin: 1
  filed_at: 2026-04-25T12:00:00-07:00
  title: "3 XPASS tests in test_router_contract.py should be promoted"
  category: contract
  severity: minor
  status: open
  evidence_pointer: "plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py"
  proposed_resolution: >
    test_pending_schema_micromegas_omega_h2, test_pending_schema_micromegas_sigma_v_zero,
    and test_drake_install_detect_documents_subset are marked xfail(strict=False) but
    are now XPASSing, which means WS-4 delivered the underlying requirements. These
    tests should be promoted to normal PASS tests (remove xfail markers) and the
    corresponding pending_ audit_status rows should be promoted to schema_pinned or
    verified_in_writer_skill.
```

---

## WS-B follow-up items

```yaml
- id: FU-wsb-01
  ws_origin: ws-b
  cycle_origin: 1
  filed_at: 2026-04-25T23:08:00-07:00
  title: "_smoke.sh regex only matches micrOMEGAs 5.x 'Omega h^2 =' format, breaks on 6.x 'Omega=' format"
  category: bug
  severity: major
  status: open
  evidence_pointer: "plugins/constraints/skills/micromegas-install/scripts/_smoke.sh (fixed in ws-b commit db36080)"
  proposed_resolution: >
    Fix already committed to dsu3-pt2/ws-b-r1-20260425. Merge to main so future
    installs against real 6.0.5 binaries pass the smoke test. The secondary pattern
    r'Omega\s*=\s*([0-9eE.+\-]+)' should become the primary for 6.x and the legacy
    h^2 pattern retained as fallback.

- id: FU-wsb-02
  ws_origin: ws-b
  cycle_origin: 1
  filed_at: 2026-04-25T23:10:00-07:00
  title: "_smoke.sh runs MSSM binary without required SLHA argument, causing immediate failure on real 6.0.5 install"
  category: bug
  severity: major
  status: open
  evidence_pointer: "plugins/constraints/skills/micromegas-install/scripts/_smoke.sh (fixed in ws-b commit db36080)"
  proposed_resolution: >
    Fix already committed to dsu3-pt2/ws-b-r1-20260425. The _run_main() helper
    detects 'argument'/'usage' in first 3 lines of no-arg run, then re-invokes
    with MSSM/input.slha (preferred) or work/lanhep/suspect2_lha.out (fallback).
    Merge to main before any other WS exercises real 6.0.5 smoke test.

- id: FU-wsb-03
  ws_origin: ws-b
  cycle_origin: 1
  filed_at: 2026-04-25T23:15:00-07:00
  title: "bin/config_write_locked.sh created in WS-B worktree must be propagated to main for WS-C/D/E"
  category: cross-ws
  severity: major
  status: open
  evidence_pointer: "bin/config_write_locked.sh committed at db36080 in dsu3-pt2/ws-b-r1-20260425"
  proposed_resolution: >
    Merge dsu3-pt2/ws-b-r1-20260425 to main (or cherry-pick the bin/
    creation commit) before WS-C, WS-D, and WS-E begin. All Wave-1 install
    workstreams must use this locked wrapper for config writes. Alternatively,
    WS-C/D/E can cherry-pick commit db36080 into their own worktrees as a
    prerequisite.
```

---

## WS-F follow-up items

```yaml
- id: FU-wsf-01
  ws_origin: ws-f
  cycle_origin: 1
  filed_at: 2026-04-25T19:30:00-07:00
  title: "Dark SU(3) UFO dt1 color tensor blocker — MadDM/MG5 cannot load Dark SU(3) UFO"
  category: upstream
  severity: minor
  status: scoped-out
  evidence_pointer: "playtest/ws-f/work/maddm_sd_run_c3/mg5_c3_run.log; decisions/dark_su3_ufo_followup.md"
  proposed_resolution: >
    Expected failure; WS-L (UFO repair) was excised from this run per scope_final §7.
    Deferred to future sarah-build/dark-su3-confining-sectors run.

- id: FU-wsf-02
  ws_origin: ws-f
  cycle_origin: 2
  filed_at: 2026-04-25T19:30:00-07:00
  title: "Destructive-command guard (dcg) blocked rm -rf of mg5out residue, halting cycle-2"
  category: helper
  severity: major
  status: open
  evidence_pointer: "playtest/ws-f/work/maddm_sd_run_wsc_f/mg5out/ (residue present)"
  proposed_resolution: >
    Future WS-F cycle should use /tmp workspace strategy (as cycle-3 did) to avoid
    needing to delete residue. Alternatively, manager can pre-delete the residue dir
    before dispatching the agent, eliminating the guard conflict.

- id: FU-wsf-03
  ws_origin: ws-f
  cycle_origin: 3
  filed_at: 2026-04-25T19:30:00-07:00
  title: "MadDM_results.txt produced in /tmp but not copied to playtest tree — ephemeral loss"
  category: producer
  severity: major
  status: open
  evidence_pointer: "playtest/ws-f/work/maddm_sd_run_c3/maddm_c3_direct_run.log (Omega h^2 = 1.2000e-01 visible)"
  proposed_resolution: >
    WS-F cycle-4: re-run MadDM in /tmp, immediately cp MadDM_results.txt to
    playtest/ws-f/run_01/MadDM_results.txt (create dir), write state/ws-f.complete.
    The SLHA is already pinned; MadDM compile artifacts are already in /tmp from
    cycle-3 (may survive if /tmp not cleared). Estimated wall-clock: 15-30 min.

- id: FU-wsf-04
  ws_origin: ws-f
  cycle_origin: 3
  filed_at: 2026-04-25T19:30:00-07:00
  title: "Cycle-3 agent stalled after SLHA pin write — did not write sentinel, log, or commit"
  category: helper
  severity: major
  status: open
  evidence_pointer: "state/ws-f.partial (written retroactively by ws-f-finalize)"
  proposed_resolution: >
    Root cause is likely token budget exhaustion or context loss after long MadDM
    process generation run. Future impl agents for compute-heavy WS should write
    intermediate sentinels (e.g., state/ws-f.slha-pinned) before launching MadDM,
    so that a stall after MadDM still preserves the SLHA-pin partial win.
    Consider adding a mid-WS checkpoint protocol to scope_final §5.1 brief template.
```

---

## WS-G follow-up items

```yaml
- id: FU-wsg-01
  ws_origin: ws-g
  cycle_origin: 1
  filed_at: 2026-04-25T23:46:00-07:00
  title: "singlet_doublet SARAH output missing CalcHEP files — micrOMEGAs requires .mdl model files"
  category: upstream
  severity: major
  status: open
  evidence_pointer: "find /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/sarah_output/ -name '*.mdl' → empty"
  proposed_resolution: >
    Re-run SARAH for singlet_doublet model with CalcHEP output enabled
    (add `WriteCalcHEP[]` or equivalent to the SARAH model configuration).
    The resulting prtcls1.mdl + lgrng1.mdl + vars1.mdl + func1.mdl files should be
    placed in the micrOMEGAs project work/models/ directory, enabling proper micrOMEGAs
    computation with the full singlet-doublet fermion DM matrix elements.
    Alternatively, use the LanHEP UFO importer (bundled as source in
    micrOMEGAs/Packages/LanHEP/) — compile LanHEP and run the UFO->CalcHEP conversion.
    The proxy-model results from WS-G cycle-1 provide the mass ordering and leading-order
    channel structure but should be replaced by proper singlet-doublet matrix elements.

- id: FU-wsg-02
  ws_origin: ws-g
  cycle_origin: 1
  filed_at: 2026-04-25T23:50:00-07:00
  title: "vSigmaA(T=0) returns NaN in micrOMEGAs 6.0.5 — use calcSpectrum instead for sigma_v at v=0"
  category: helper
  severity: minor
  status: open
  evidence_pointer: "/Users/yianni/micrOMEGAs/micromegas_6.0.5/SingletDM/ws_g_driver.c (comment in annihilation section)"
  proposed_resolution: >
    Document in SKILL.md that vSigmaA(0.0, ...) may return NaN in 6.0.5.
    The correct approach for sigma_v at v=0 is calcSpectrum(key, ...) which is
    designed for this purpose and returns a finite value. Update main_c_template.py
    to use calcSpectrum for the annihilate subcommand instead of vSigmaA(0.0,...).
```

---

## WS-H follow-up items

```yaml
- id: FU-WS-H-1
  ws_origin: ws-h
  cycle_origin: 1
  filed_at: 2026-04-25T10:45:00-07:00
  title: "DRAKE acceptance regex does not match actual wolframscript stdout format"
  category: contract
  severity: major
  status: open
  evidence_pointer: ".shift-manager/run-20260425-dsu3-playtest/playtest/ws-h.md"
  proposed_resolution: >
    The scope acceptance regex Omega[\s_]*[hH]\^?2[^=]*=\s*[0-9] was written for an
    aspirational SKILL.md output description ("look for Omega h^2 or OmegaH2"). DRAKE's
    actual wolframscript stdout uses Oh2_nBE format inside Stylef[...] wrappers (unevaluated
    in non-interactive mode) and MatrixForm[...] tables. Fix options: (a) Update scope regex
    to match MatrixForm pattern, e.g. Oh2nBE,\s*([\d.]+); (b) Patch test.wls to add a
    plain Print["Omega h^2 = " <> ToString[Oh2nBE]] line after the Stylef; (c) Accept the
    MatrixForm line and parse numerically. Option (b) is minimally invasive and preserves
    DRAKE's existing output while adding a parseable line.
```

---

## WS-J follow-up items

```yaml
- id: FU-wsj-01
  ws_origin: ws-j
  cycle_origin: 2
  filed_at: 2026-04-25T00:26:00-07:00
  title: "slha_adapter._parse_coupling_block PDG-triplet format not supported"
  category: skill
  severity: major
  status: open
  evidence_pointer: "plugins/constraints/skills/higgstools/scripts/slha_adapter.py line 128"
  proposed_resolution: >
    Add format detection: if parts[0] is a float (coupling value) → PDG-triplet format
    (HiggsBoundsInputHiggsCouplingsX FeynHiggs style); if int → row-index format (SPheno
    WriteHiggsBoundsBlocks style). Parser currently only handles row-index format and
    raises ValueError on float col[0], silently skipping all rows → empty coupling dict
    → SlhaMissingBlocksError. Both formats are valid SLHA per HiggsBounds manual.

- id: FU-wsj-02
  ws_origin: ws-j
  cycle_origin: 2
  filed_at: 2026-04-25T00:26:00-07:00
  title: "legacy_driver.run_higgsbounds calling convention missing whichinput arg"
  category: skill
  severity: major
  status: open
  evidence_pointer: "plugins/constraints/skills/higgstools/scripts/legacy_driver.py line 192"
  proposed_resolution: >
    legacy_driver.py line 192: cmd = [hb_bin, "LandH", str(n_neutral), str(n_charged), slha_file]
    is missing the "whichinput" argument. HB-5 binary expects:
    HiggsBounds <whichanalyses> <whichinput> <nHneut> <nHplus> <prefix>
    For SLHA input: cmd = [hb_bin, "LandH", "SLHA", str(n_neutral), str(n_charged), slha_stem]
    Additionally, slha_file must be a stem (path without .N extension) not a full file path.
    Consider using the compiled HBwithSLHA example program which handles SLHA natively.

- id: FU-wsj-03
  ws_origin: ws-j
  cycle_origin: 2
  filed_at: 2026-04-25T00:26:00-07:00
  title: "2HDM+a SPheno binary not built — WS-J cannot test 2HDM+a specifically"
  category: install
  severity: minor
  status: open
  evidence_pointer: "~/.config/hep-ph-agents/config.json models.two_hdm_a (no spheno_bin or latest_slha keys)"
  proposed_resolution: >
    Run /spheno-build for model two_hdm_a to generate SPheno binary and spectrum output.
    Requires SARAH to generate SPheno code (sarah_output/ exists) and then compile
    SPheno with the 2HDM+a model module. This will produce runs/<ts>/SPheno.spc with
    HiggsBoundsInputHiggsCouplingsX blocks if WriteHiggsBoundsBlocks=True in SPheno.m.
```

---

## WS-I follow-up items

```yaml
- id: FU-wsi-01
  ws_origin: ws-i
  cycle_origin: 1
  filed_at: 2026-04-25T17:18:00-07:00
  title: "LZ_2022 experiment not in DDCalc v1 native set; overlay deferred to v1.1"
  category: install
  severity: major
  status: open
  evidence_pointer: "plugins/constraints/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/manifest.yaml"
  proposed_resolution: >
    Implement DDCalc v1.1 overlay bundle with LZ_WS2024, XENONnT_2023, PandaX_4T_2021.
    Manifest exists as stub. Requires resolving multi-file DDCalc registration pattern
    (DDExperiments.f90, DDExperiments.hpp, Makefile) and computing real eff_sha256 values.
    Brief's "LZ_2022" reference may conflate arXiv:2207.03764 with DDCalc experiment name;
    clarify naming convention when implementing overlay.

- id: FU-wsi-02
  ws_origin: ws-i
  cycle_origin: 1
  filed_at: 2026-04-25T17:18:00-07:00
  title: "ddcalc-install Apple Silicon: -lgfortran linker path not set"
  category: install
  severity: minor
  status: open
  evidence_pointer: ".shift-manager/run-20260425-dsu3-playtest/playtest/ws-i/cycle-1-log.md §driver-compile-gfortran-not-found"
  proposed_resolution: >
    In ddcalc-install apply_overlay.sh and any compile step: add
    -L$(gfortran -print-file-name=libgfortran.a | xargs dirname) to LDFLAGS
    when on Apple Silicon (uname -m == arm64 and gfortran is Homebrew GCC).
    WS-D's ddcalc_driver.c build command should document this flag requirement.

- id: FU-wsi-03
  ws_origin: ws-i
  cycle_origin: 1
  filed_at: 2026-04-25T17:18:00-07:00
  title: "WS-I should re-run with real micrOMEGAs scattering/v1 output once WS-G completes"
  category: producer
  severity: minor
  status: open
  evidence_pointer: ".shift-manager/run-20260425-dsu3-playtest/state/ws-g.complete (does not yet exist)"
  proposed_resolution: >
    After WS-G produces playtest/ws-g/scattering_singletDoublet.json (scattering/v1),
    re-run: python3 run_ddcalc.py run --sigma-json <ws-g-output>.
    Synthetic sigma_SI=5e-46 cm^2 used in cycle-1 is physically reasonable
    (Higgs-portal tree level, MS=150 GeV, yh1=1) but not micrOMEGAs-computed.
```
