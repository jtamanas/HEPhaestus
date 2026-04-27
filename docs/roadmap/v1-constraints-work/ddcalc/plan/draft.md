# `/ddcalc` implementation plan (draft)

Drafter: plan-drafter agent
Date: 2026-04-19
Status: input to planner review / plan-eng-review
Authoritative spec: `docs/roadmap/v1-constraints-work/ddcalc/brainstorm/final.md`
Sibling spec (co-owned files): `docs/roadmap/v1-constraints-work/micromegas/brainstorm/final.md`

Scope: deliver two skills (`/ddcalc-install`, `/ddcalc`) inside the new
`plugins/constraints/` plugin, as a leaf consumer of scattering cross sections
produced by `/micromegas` (tree-level) and, later, `/formcalc` (loop-level).

---

## 0. Worktree / branch

- Branch name: `workstream-constraints-ddcalc`.
- Worktree path: `../hep-ph-agents-ddcalc` (per superpowers convention; invoke via
  `/superpowers:using-git-worktrees` before touching `plugins/`).
- No work happens on `main`. No edits outside the worktree once created.
- Rebase cadence: rebase on `main` once `/micromegas`'s prep PR has landed
  (marketplace entry + `plugins/shared/schemas/scattering.schema.json` skeleton
  + `plugins/constraints/.claude-plugin/plugin.json`). If still unlanded at
  implementation start, see §1 "coordination gate".

---

## 1. Shared prerequisites

### Coordination gate with `/micromegas` workstream

The `plugins/constraints/` skeleton, marketplace entry, `CLAUDE.md` table row,
and `plugins/shared/schemas/scattering.schema.json` are explicitly co-owned.
At worktree-creation time, check each of:

- `plugins/constraints/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` contains a `constraints` entry
- `CLAUDE.md` category table has a `constraints` row
- `plugins/shared/schemas/scattering.schema.json` exists and validates
- `plugins/hep-ph-toolkit/skills/_shared/` exists (overlay dir) — optional
- `plugins/shared/pvalue.py` exists (shared p-value helper)

Rules:

- **If all present:** treat as read-only inputs; do not modify schema field
  names without cross-workstream sync. Add `/ddcalc`-specific additions only
  as non-conflicting additive keys (e.g. `nreft_coefficients?`).
- **If absent:** create minimal viable stubs in this workstream, mark each
  created file with a header comment `# CREATED BY /ddcalc WORKSTREAM — to be
  reconciled with /micromegas before merge`, and flag in the PR description.
  Do **not** rename or relocate files the sibling workstream may already be
  editing in parallel.
- **If partially present:** adopt what exists verbatim; fill gaps per above.

### Other prerequisites

- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — reuse as the
  blocker contract (symlinked from `plugins/hep-ph-toolkit/skills/_shared/`
  per `/micromegas` final §6.5). The symlink itself is created by whichever
  workstream lands first; if absent, this workstream creates it.
- `plugins/shared/install-helpers/_common.sh` — sourced by
  `install_ddcalc.sh`; uses the 4-levels-deep sourcing pattern identical to
  `sarah-install/install_sarah.sh`.
- `gfortran` on `PATH` — validated via `EXIT_NO_GFORTRAN` (shared exit code).
- Python ≥ 3.10 (asserted in helpers).
- `git` (for `git apply --3way` during overlay install).

### Planning-phase resolutions required before implementation PR opens

Per brainstorm §7, five items must resolve before any `plugins/` edit:

1. Canonical DDCalc URL verified (`DDCALC_UPSTREAM_UNVERIFIED` cleared).
2. Real SHA256 of `DDCalc-2.2.0.tar.gz` recorded in `skill_env.yaml`.
3. `DDCalc_exampleC` version-print behaviour confirmed (banner patch y/n).
4. O'Hare 2021 CSV licence verified; `NOTICE` drafted.
5. Exact ν-floor curve used in 2506.19062 Fig. 6/7 identified.

Item 6 (overlay manifest) is NOT a gate — v1 ships native-only if it stalls.

---

## 2. Files to create (per-file plan)

Voice for every SKILL.md: match `sarah-install` / `spheno-build` — terse
header, `When to invoke`, decision flow, subcommands table, blockers table,
config keys table, linkage section. No marketing. Bullet-dense.

### `/ddcalc-install`

- `plugins/hep-ph-toolkit/skills/ddcalc-install/SKILL.md`
  - Subcommands: `detect`, `use-path <dir>`, `install [<dir>] [--with-overlay <spec>]`.
  - JSON status contract mirrors `sarah-install` (`missing`/`found`/`configured`).
  - Blocker table: `DDCALC_DOWNLOAD_FAILED`, `DDCALC_BUILD_FAILED`,
    `DDCALC_SMOKE_TEST_FAILED`, `DDCALC_PATH_INVALID`,
    `DDCALC_OVERLAY_APPLY_FAILED`, `GFORTRAN_ABSENT` (reuses `EXIT_NO_GFORTRAN`),
    `DDCALC_UPSTREAM_UNVERIFIED` (planning-phase only; never emitted at runtime).
  - Config keys written: `ddcalc_path`, `ddcalc_version`,
    `ddcalc_installed_at`, `ddcalc_experiment_set`,
    `ddcalc_experiment_overlay_sha`, `ddcalc_upstream_url`,
    `ddcalc_upstream_commit`.
  - HEPPH_NO_NETWORK behaviour documented (fail-closed with
    `user_instruction` pointing to `use-path`).
- `plugins/hep-ph-toolkit/skills/ddcalc-install/skill_env.yaml`
  - Pinned keys: `HEPPH_DDCALC_VERSION: 2.2.0`, `HEPPH_DDCALC_SHA256: <real>`,
    `HEPPH_DDCALC_URL: https://gitlab.com/ddcalc/ddcalc/-/archive/v2.2.0/...`
    (or mirror — pinned after URL-verification step).
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/install_ddcalc.sh`
  - Sources `_common.sh` via the 4-levels-deep pattern.
  - `check_disk 1`, `download_with_retry`, `verify_checksum` (no `TODO` path),
    `tar xf`, `cd build && make FFLAGS=... CFLAGS=... -j$(python3 -c ...)`,
    smoke-test via `DDCalc_exampleC`.
  - Supports offline cache: if `HEPPH_DDCALC_CACHE` or
    `$HEPPH_CACHE_DIR/DDCalc-2.2.0.tar.gz` exists, skip download.
  - Overlay hook: if `--with-overlay <name>` supplied, after base build
    succeeds, invoke `apply_overlay.sh <name>` then rebuild.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/detect_ddcalc.sh`
  - Mirrors `sarah-install/detect_*`: `configured` / `found` / `missing` JSON
    on stdout. No side effects.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/use_path.sh`
  - Validates `<dir>/include/DDCalc.h` and `<dir>/lib/libDDCalc.a`; runs smoke
    test; writes config.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/apply_overlay.sh`
  - Reads `overlays/<name>/manifest.yaml` (pinned upstream commit + patch list
    + table SHA256s). Aborts if current DDCalc checkout commit ≠ manifest's
    pinned commit. `git apply --3way` each patch; on reject, capture
    `.rej` paths into `context.patch_reject_files` and emit
    `DDCALC_OVERLAY_APPLY_FAILED`. Drops new efficiency tables into
    `data/experiments/<name>/`, verifies each SHA256. Re-invokes `make`.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/_smoke_test.sh`
  - Runs `bin/DDCalc_exampleC`, greps stdout for `DDCalc\s+v?([0-9.]+)`.
  - If stock 2.2.0 prints only the copyright banner, apply
    `patches/version_banner.patch` as part of the install step (decided in
    planning item 3).
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/_blocker.sh`
  - Copy of `sarah-install/_blocker.sh` (or shared; do not duplicate if
    `/micromegas` workstream has already promoted it to
    `plugins/shared/install-helpers/_blocker.sh`).
- `plugins/hep-ph-toolkit/skills/ddcalc-install/patches/version_banner.patch`
  - One-line patch to `src/DDCalc_util.f90` printing `DDCalc 2.2.0` at startup.
  - Included unconditionally; guarded by a sentinel in the smoke-test script.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/manifest.yaml`
  - Pinned upstream commit SHA (ddcalc main); list of `.patch` files; list of
    new efficiency tables with SHA256; `overlay_sha` = sha256 of concatenated
    manifest.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/patches/LZ_WS2024.patch`
  - Fortran module adding LZ 2024 WS exposure + efficiency constructor. Stub
    in this workstream; real content authored in overlay-publication PR per
    brainstorm §3.
- `...overlays/.../patches/XENONnT_2023.patch`, `PandaX_4T_2021.patch` — stubs.
- `...overlays/lz_xenonnt_pandax4t_2024/data/LZ_WS2024.eff` — efficiency table stub.
- `...overlays/lz_xenonnt_pandax4t_2024/NOTICE` — provenance + licence statement.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_detect_config.sh`
  - Mirror of `sarah-install`'s test; uses tmp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_offline_cache.sh`
  - `HEPPH_NO_NETWORK=1` + staged cached tarball → install must succeed.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_overlay_apply.py`
  - Fake upstream repo, apply overlay patch, assert `context.patch_reject_files` empty.
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/fixtures/ddcalc_example_banner.txt`
  - Captured `DDCalc_exampleC` output for smoke-test regex coverage.

### `/ddcalc`

- `plugins/hep-ph-toolkit/skills/ddcalc/SKILL.md`
  - Subcommands: `run`, `exclude`, `scan-summary` (no `marginalize-halo`).
  - Input schema reference: `plugins/shared/schemas/scattering.schema.json`.
  - Halo default: SHM (238, 544, 0.3), always set via `SetHalo`, echoed in output.
  - NREFT rejected via `DDCALC_NREFT_NOT_SUPPORTED`.
  - Blockers: `DDCALC_INPUT_INVALID`, `DDCALC_MASS_OUT_OF_RANGE` (recoverable),
    `DDCALC_DRIVER_FAILED`, `DDCALC_NREFT_NOT_SUPPORTED`, `DDCALC_OVERLAY_MISSING`.
  - No `DDCALC_REFERENCE_ONLY` code. No `HEPPH_ALLOW_REFERENCE` knob.
  - File lock on `$STATE_ROOT/.locks/ddcalc` (flock) — reserved for rebuild ops.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/run_ddcalc.py`
  - CLI entry: dispatches `run` / `exclude` / `scan-summary`.
  - Reads `--sigma-json`, validates against shared schema, builds an input for
    the DDCalc C driver, invokes via `subprocess`, parses stdout.
  - Writes `$STATE_ROOT/runs/ddcalc/<TS>/{result.json,report.md,driver.log}`.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/ddcalc_driver.c`
  - Small C shim linked against `libDDCalc.a`. Sets halo, loads experiments
    (native + overlay), calls `DDCalc_LogLikelihood` per experiment. Emits
    structured stdout lines parsed by `_parse_driver_stdout.py`. Compiled
    on first call; cached at `$STATE_ROOT/cache/ddcalc_driver/<sha>/driver`.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/_parse_driver_stdout.py`
  - Pure Python; no DDCalc dep. Parses into the `ddcalc_result/v1` schema.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/validate_scattering.py`
  - Wrapper around `jsonschema` against `plugins/shared/schemas/scattering.schema.json`.
  - Emits `DDCALC_INPUT_INVALID` with jsonschema error tail in `context`.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/halo.py`
  - SHM defaults; builds `SetHalo` args; echoed into `halo_used` output field.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/neutrino_fog.py`
  - Default: call DDCalc built-in via driver. Opt-in `--nu-floor ohare_2021`
    reads vendored CSV and interpolates. Emits `neutrino_fog` block with
    `source`, `definition`, `n_sigma_above_floor`, `in_fog`.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/scan_summary.py`
  - Reads upstream scan index (from `/spheno-build` or `/micromegas`),
    iterates sequentially, writes `ddcalc_scan.csv`. Never overwrites upstream
    artefacts. flock-guarded.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/exclude.py`
  - Thin wrapper emitting only the verdict JSON.
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/render_report.py`
  - Renders `report.md` from `result.json`. No external deps.
- `plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_ohare_2021.csv`
  - Vendored mass/σ curve from O'Hare PRL 127, 251802 (2021).
- `plugins/hep-ph-toolkit/skills/ddcalc/data/NOTICE`
  - Provenance, licence, exact figure reference. Resolved in planning item 4.
- `plugins/hep-ph-toolkit/skills/ddcalc/overlays/README.md`
  - Pointer to `ddcalc-install/overlays/`. No second copy of patches.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_schema_validate.py`
  - Covers happy path, missing required keys, NREFT key rejection, isospin-violating input.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_parse_driver_stdout.py`
  - Uses captured fixtures; no DDCalc dep.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_halo_echo.py`
  - Asserts SHM defaults land in `halo_used` byte-identical across runs.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_scan_summary_determinism.py`
  - Byte-identical `ddcalc_scan.csv` for a fixed input index.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_integration_xenon1t_golden.py`
  - Gated on `HEPPH_RUN_NETWORK_TESTS=1`. σ_SI = 1e-46 cm², m_DM = 100 GeV →
    XENON1T 2018 `excluded_90cl = true`; tolerance ±10 % on logL.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_micromegas_sample.json`
  - Valid scattering.schema.json sample emitted by `/micromegas`.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_looptools_sample.json`
  - Valid sample emitted by `/formcalc` (hand-authored v1 stub; identical
    verdict asserted in the round-trip test).
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/driver_stdout_xenon1t.txt`
  - Captured stdout from a real DDCalc run for unit-level parser coverage.
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/blocker_invalid_input.json`
  - Golden blocker JSON validating against `blocker.schema.json`.

### Shared surfaces (only if sibling has not authored them)

- `plugins/constraints/.claude-plugin/plugin.json` — minimal manifest with
  both skills listed.
- `.claude-plugin/marketplace.json` — add `constraints` plugin row.
- `CLAUDE.md` — add `| Constraints | constraints | Direct-detection, relic,
  Higgs-coupling constraints |` row to the category table.
- `plugins/shared/schemas/scattering.schema.json` — snake_case schema per
  brainstorm §2 (includes optional `nreft_coefficients` for forward-compat).
- `plugins/shared/pvalue.py` — shared chi2-to-p helper used by the driver.

---

## 3. Implementation sequence (11 steps)

1. **Planning-phase verifications (no code yet).** Run the "carried to
   planning" checklist in brainstorm §7: clone `gitlab.com/ddcalc/ddcalc`,
   confirm `v2.2.0` tag + commit SHA, compute tarball SHA256, confirm
   `DDCalc_exampleC` version-print behaviour, verify O'Hare 2021 licence,
   identify the exact ν-floor curve used in 2506.19062 Fig. 6/7. Record
   findings in `docs/roadmap/v1-constraints-work/ddcalc/plan/verifications.md`.
   **Gate:** none of these can be `TODO` when step 3 starts.

2. **Create worktree.** `/superpowers:using-git-worktrees`; branch
   `workstream-constraints-ddcalc`.

3. **Check coordination gate (§1).** Probe sibling artefacts. Open the PR
   description with a checklist declaring which files this workstream owns
   vs. inherits. Land `plugin.json` / `marketplace.json` / `CLAUDE.md` row /
   `scattering.schema.json` skeleton here **only** if absent.

4. **Scaffold `/ddcalc-install` install path (offline cacheable).** Author
   `install_ddcalc.sh`, `detect_ddcalc.sh`, `use_path.sh`, `_smoke_test.sh`,
   `_blocker.sh`, `skill_env.yaml` (with real SHA256 from step 1). Unit-test
   `detect` and `use-path` with tmp `HEPPH_STATE_ROOT`. Run the real install
   locally against `HEPPH_NO_NETWORK=1` + staged cache — prove it builds.

5. **Verify Apple-Silicon build quirks.** Exercise `FFLAGS="-std=legacy
   -fallow-invalid-boz -O2"` + `CFLAGS="-Wno-implicit-function-declaration"`
   on gfortran 13+ / clang 15+. If `DDCalc_exampleC` prints only the
   copyright banner, commit `patches/version_banner.patch` and wire it into
   `install_ddcalc.sh` pre-`make`.

6. **Author SKILL.md for `/ddcalc-install`** matching `sarah-install` voice.
   Include JSON status contract, blocker table, config-keys table, activation
   rules (there is no Wolfram analogue — overlay rebuild is the analogous
   structured-status case, but still a blocker not a status).

7. **Implement overlay-as-recompile mechanism.** Author `apply_overlay.sh`,
   `overlays/lz_xenonnt_pandax4t_2024/manifest.yaml`, stub patch files, and
   `NOTICE`. Unit-test against a fake upstream clone. Overlay manifest remains
   a stub until the external overlay-publication PR lands; the plumbing must
   be merge-ready without the Fortran content.

8. **Author `/ddcalc` driver + schema validator.** Write `ddcalc_driver.c`,
   `run_ddcalc.py`, `validate_scattering.py`, `halo.py`,
   `_parse_driver_stdout.py`. Unit-test the parser against captured stdout
   fixtures. Drive every code path with `blocker.schema.json`-validated
   blocker outputs.

9. **Wire `scan-summary` + `exclude` + `render_report`.** flock-guarded,
   serial, byte-deterministic CSV. Golden fixture for CSV byte-stability.

10. **Vendor `neutrino_fog_ohare_2021.csv` + `NOTICE`.** Only land once
    planning item 4 (licence) is resolved. Plumb `--nu-floor ohare_2021`
    through `neutrino_fog.py`.

11. **Integration golden.** σ_SI = 1e-46 cm², m_DM = 100 GeV → XENON1T 2018
    excluded_90cl=true. Gate on `HEPPH_RUN_NETWORK_TESTS=1`. If overlay
    manifest has real content, add LZ WS2024 p < 1e-6 assertion.

---

## 4. Test plan

**Unit (always on, `pytest` + `bash`):**
- Input-schema validation (happy / missing keys / NREFT rejection / isospin).
- `_parse_driver_stdout.py` against captured stdout fixtures.
- Halo-override round-trip (SHM defaults byte-identical in `halo_used`).
- `blocker.schema.json` conformance for every emitted blocker.
- `ddcalc_result/v1` conformance for every `result.json`.
- `scan-summary` determinism (byte-identical CSV).
- Overlay `apply_overlay.sh` against fake upstream (reject collection test).
- `detect` / `use-path` with tmp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`.

**Integration (`HEPPH_RUN_NETWORK_TESTS=1` gated):**
- Real `/ddcalc-install install` on clean `$HOME`.
- Offline install via `HEPPH_NO_NETWORK=1` + staged cache.
- Native experiment list probe.
- `/ddcalc run` on the `/micromegas` sample JSON emits `result.json`.

**Golden fixture (gated):**
- σ_SI_p = σ_SI_n = 1e-46 cm², σ_SD = 0, m_DM = 100 GeV → `verdict =
  "excluded"`, XENON1T 2018 `excluded_90cl=true`, `p_value < 1e-3`,
  tolerance ±10 % on logL.
- With overlay: LZ WS2024 `excluded_90cl=true`, `p_value < 1e-6`.

**Schema round-trip (always on):**
- `sigma_micromegas_sample.json` and `sigma_looptools_sample.json` both
  validate against `scattering.schema.json`, both produce identical `verdict`
  on `/ddcalc run`. Documents the "leaf consumer never auto-selects" rule.

**Concurrency:**
- Serial (matches `/spheno-build --scan`).
- flock file lock on `$STATE_ROOT/.locks/ddcalc` around any rebuild-dependent
  op. v1 has none, but the lock is reserved and exercised by a no-op test.

---

## 5. Verification checklist (before PR merge)

- [ ] All five "carried to planning" items from brainstorm §7 resolved and
      recorded in `plan/verifications.md`.
- [ ] `HEPPH_DDCALC_SHA256` is a real hex value (no `TODO`).
- [ ] `HEPPH_DDCALC_URL` points at the verified canonical upstream, not a
      personal fork.
- [ ] Worktree branch `workstream-constraints-ddcalc` only.
- [ ] Coordination gate (§1) checklist filled in PR description; no duplicate
      `scattering.schema.json` / `plugin.json` creation versus sibling.
- [ ] `plugins/shared/schemas/scattering.schema.json` is snake_case, carries
      an optional `nreft_coefficients` key, and field names match the draft
      in `/micromegas` final §3 byte-for-byte.
- [ ] Every blocker emitted by both skills validates against
      `blocker.schema.json`.
- [ ] Zero references to `HEPPH_ALLOW_REFERENCE` in this workstream.
- [ ] Zero references to `DDCALC_REFERENCE_ONLY`, `reference_only` status
      for DDCalc results, or any analytic Lewin-Smith path.
- [ ] Overlay mechanism works via `git apply --3way` + recompile; there is
      no data-file hot-swap code anywhere.
- [ ] `neutrino_fog.source` default is `"ddcalc_builtin_2.2.0"`.
- [ ] O'Hare CSV `NOTICE` names the paper, the figure, and the licence.
- [ ] SKILL.md voice matches `sarah-install` / `spheno-build`: terse header,
      subcommand tables, blocker tables, no marketing prose.
- [ ] `CLAUDE.md` category table row added (or verified pre-existing).
- [ ] `.claude-plugin/marketplace.json` entry added (or verified).
- [ ] Golden fixture test passes locally under `HEPPH_RUN_NETWORK_TESTS=1`.
- [ ] Unit tests pass with no env gates.
- [ ] `report.md` renders for happy-path and blocker cases.

---

## 6. Out of scope for v1

Deferred to v1.1 (or later) per brainstorm §2, §4, §7:

- **Halo marginalization.** `marginalize-halo` subcommand, SHM++ and
  Gaia-sausage presets, and any `--halo-uncertainty` propagation. v1 always
  uses SHM (238, 544, 0.3) and echoes it.
- **NREFT / Anand–Fitzpatrick–Haxton operator basis.** Schema reserves
  `nreft_coefficients` for forward-compat; presence is a fatal
  `DDCALC_NREFT_NOT_SUPPORTED` in v1.
- **CP-violating / non-standard form factors beyond the `default` preset.**
  `nucleon_form_factors` is echoed but not varied.
- **Sub-GeV DM / Migdal effect.** Masses below DDCalc's valid range emit a
  recoverable `DDCALC_MASS_OUT_OF_RANGE` with
  `context.suggested_tool = "DarkELF"` (or similar pointer).
- **Loop-level σ_SI (blind spots).** Owned by Phase B `/formcalc`. `/ddcalc`
  is a leaf consumer; it never auto-selects between tree and loop inputs.
- **`marginalize-halo` / `debug-dump`.** Folded into `run --debug`.
- **Parallel scans.** Serial only, matches `/spheno-build`.
- **Overlay hot-swap.** Explicitly rejected. Overlay = source patch + recompile.
- **Any analytic fallback.** `HEPPH_ALLOW_REFERENCE` is forbidden; removed
  blockers `DDCALC_REFERENCE_ONLY` must not reappear.
- **v1.1 overlay additions beyond `lz_xenonnt_pandax4t_2024`.** Each new
  overlay = new manifest under `ddcalc-install/overlays/<name>/` with its own
  pinned commit + SHA256 table, landed via a dedicated PR.

---

Word count target: ~1800. Sections 0–6 complete; no code; no `plugins/` edits
performed by this draft — all file paths are plan-only.
