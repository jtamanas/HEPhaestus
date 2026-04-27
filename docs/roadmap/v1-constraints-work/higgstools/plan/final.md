# /higgstools — Executable Plan (Final)

Synthesis of `draft.md` + `critique.md` under the brainstorm and under the
manager-imposed cross-workstream decisions. Legacy HB-5.10.2 + HS-2.6.2
Fortran is the v1 default path; unified C++ (`higgstools` v1.2) is opt-in
and skipped gracefully on macOS arm64 build failure. Two subcommands only:
`run` (single point or `--scan-dir`) and `aggregate` (collect-only). No
analytic fallback. SLHA2 is the only input.

---

## 0. Worktree, branch, Phase-0 prereq

- **Branch:** `workstream-constraints-higgstools`
- **Worktree root:** `~/Projects/hep-ph-agents-worktrees/constraints-higgstools/`
- Created via `superpowers:using-git-worktrees` from `main` **after Phase-0
  has landed on `main`**.

**Phase-0 prerequisites treated as DONE before step 1 of this plan:**

1. `plugins/constraints/` scaffold exists: `.claude-plugin/plugin.json`
   with all six skills (`higgstools`, `higgstools-install`, `micromegas`,
   `micromegas-install`, `ddcalc`, `ddcalc-install`), `README.md`,
   `SHARED.md`, and the canonical `_shared/blocker.schema.json` symlink to
   `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.
2. `plugins/shared/install-helpers/_common.sh` has:
   - `EXIT_NO_CMAKE=26`
   - `EXIT_NO_PYBIND=27`
   - `EXIT_FORM_BUILD=28` (reserved for sibling `/micromegas`)
   - `EXIT_LOOPTOOLS_BUILD=29` (reserved for sibling `/micromegas`)
3. `.claude-plugin/marketplace.json` has an entry for `constraints`.
4. `CLAUDE.md` plugin table mentions the `constraints` plugin row.

This plan does **not** edit `_common.sh` or create any
`plugins/constraints/` scaffold files. If any of the above is missing at
worktree-creation time, stop and coordinate with the manager — do not
attempt to land Phase-0 locally.

Sibling constraint workstreams (`/micromegas`, `/ddcalc`) run on their
own branches off the same Phase-0 base. No file in this plan collides
with theirs.

---

## 1. Files (higgstools-specific only)

All paths are under the worktree root. No edits to `plugins/shared/` or
`plugins/constraints/` top-level (Phase-0 owns those).

**Install skill** — `plugins/hep-ph-toolkit/skills/higgstools-install/`

- `SKILL.md` — mirrors `sarah-install/SKILL.md` structure: When-to-invoke,
  Decision flow (`detect` / `use-path` / `install`), JSON status
  contract, Failure modes → blockers, Config keys written, Version pin
  and override, Linkage. Explicit Apple Silicon caveat for unified
  backend. Documents that `aggregate` is collect-only.
- `skill_env.yaml` — pins: `HB_VERSION=5.10.2`, `HS_VERSION=2.6.2`,
  `HT_VERSION=1.2`, `HBDATASET_TAG=v1.7`, `HSDATASET_TAG=v1.1`, plus
  `hb_commit`, `hs_commit`, `hbdataset_commit`, `hsdataset_commit`
  fields (full SHAs recorded at scaffolding time via
  `git ls-remote`/`git rev-parse`).
- `scripts/install_higgstools.sh` — bash driver. Sources
  `plugins/shared/install-helpers/_common.sh` via the 4-levels-deep
  pattern. Implements `detect`, `use-path`, `install`. Legacy default;
  `--backend=unified` gated on `HEPPH_HIGGSTOOLS_BACKEND=unified`.
  Uses `check_disk 3`, `download_with_retry` (only for fallback
  tarball branch), `verify_checksum`, `config_merge`. Primary source
  acquisition is `git clone --depth 1 --branch <tag>` followed by
  `git rev-parse HEAD` compared against `hb_commit` / `hs_commit`.
- `scripts/detect_higgstools.sh` — idempotent probe emitting
  `configured` / `found` / `missing` JSON on stdout.
- `scripts/_blocker.sh` — one-liner emitter matching
  `sarah-install/scripts/_blocker.sh`.
- `scripts/smoke_test.sh` — runs HB's bundled `example_SM_vs_4thgen`,
  asserts `HBresult=1`; runs HS's bundled SM example, asserts finite
  chi² < 200; **caches `chi2_SM_ref`** to
  `$STATE_ROOT/cache/hs2_chi2_sm_ref.json` (install-time step).
- `scripts/cache_sm_reference.py` — small helper invoked by
  `smoke_test.sh` that parses HS's SM run output and writes the
  reference cache atomically.
- `tests/test_detect_config.sh` — unit: config + path parsing.
- `tests/test_install_args.py` — unit: argparse for `--backend`,
  env-var gating, dry-run path.
- `tests/test_sm_ref_cache.py` — asserts cache file shape and that
  downstream `run` refuses to proceed if cache is absent
  (`HIGGSTOOLS_SM_REF_MISSING`).

**Usage skill** — `plugins/hep-ph-toolkit/skills/higgstools/`

- `SKILL.md` — When-to-invoke, two subcommands, inputs (`--model`,
  `--slha`, `--dMh`, `--mode`, `--backend`, `--channels`,
  `--delta-chi2`, `--workers`, `--scan-dir`), data contract (SLHA2
  only), outputs (`result.json`, `per_channel.csv`, `report.md`,
  `input_dump.json`), exclusion conventions (HB-5: AND of per-channel
  `HBresult`; HS: Δχ² < 6.18 default), error modes, scan parallelism.
  Documents `aggregate` as **collect-only**: "reads a directory of
  per-point `result.json` files and emits a scan-summary CSV/JSON.
  Re-running HB/HS is the job of `run --scan-dir <dir>`."
- `scripts/run_higgstools.py` — CLI entry; dispatches `run` vs
  `aggregate`. `run` accepts `--scan-dir` to fan out across SLHAs.
- `scripts/slha_adapter.py` — parses SLHA2, extracts `MASS`, `HMIX`,
  decays, `HiggsBoundsInputHiggsCouplingsFermions`,
  `HiggsBoundsInputHiggsCouplingsBosons`. Fatal
  `HIGGSTOOLS_SLHA_MISSING_BLOCKS` with actionable but abstract
  `user_instruction`: "Re-run SPheno with `WriteHiggsBoundsBlocks=True`
  in the SARAH-generated `SPheno.m`." Falls back to legacy `HiggsBounds`
  block with warning; errors if both absent.
- `scripts/legacy_driver.py` — invokes HB-5/HS-2 Fortran binaries via
  subprocess; parses stdout into a uniform result dict; emits
  per-channel `HBresult` values.
- `scripts/unified_driver.py` — imports `Higgs.bounds`, `Higgs.signals`
  lazily; raises `HIGGSTOOLS_BACKEND_UNAVAILABLE` if the import fails
  under `HEPPH_HIGGSTOOLS_BACKEND=unified`.
- `scripts/exclusion.py` — `compute_hb_allowed(channels)` = `all(c.hb_result == 1
  for c in channels)`. `compute_hs_consistent(chi2_total, chi2_sm_ref,
  delta_chi2=6.18)` = `(chi2_total - chi2_sm_ref) < delta_chi2`.
- `scripts/p_value.py` — thin `scipy.stats.chi2.sf` wrapper. Takes
  `(chi2, ndf)` pairs **as already supplied by HS's native output**
  (`HiggsSignals_get_Peak_Chisq` returns `(chi2, ndf)`). No Python-side
  `len(channels)` computation of `ndf`.
- `scripts/aggregate.py` — collect-only. Walks a directory, joins
  per-point `result.json` files into `higgstools_index.csv` sorted by
  SPheno `index` column. Uses `multiprocessing.Pool` only for parsing,
  not for re-running HB/HS.
- `scripts/report.py` — renders `report.md` from `result.json`.
- `tests/fixtures/2hdm_type2_benchmark.slha` — **pre-run SPheno golden
  SLHA**, committed as-is (no Python synthesis). Parameters pinned in
  `SKILL.md` and in a header comment: `mh=125, mH=500, mA=450, mHp=500,
  tanb=5, sin(β-α)=0.999, m12^2=150^2 GeV^2`. Contains all HB input
  blocks including charged-Higgs couplings.
- `tests/fixtures/sm_benchmark.slha` — SM-like SLHA used by the
  install-time `chi2_SM_ref` cache step.
- `tests/fixtures/result_golden.json` — expected HB+HS result for the
  2HDM Type-II benchmark (`hb_allowed`, `obsratio_max` interval,
  `hs_consistent`).
- `tests/fixtures/scan_mini/` — 5 pre-populated per-point `result.json`
  files for the aggregate determinism test. No SLHAs here — aggregate
  only joins existing results.
- `tests/test_slha_adapter.py` — parses the 2HDM fixture; asserts
  couplings, masses, widths; exercises the missing-blocks fatal path.
- `tests/test_exclusion.py` — HB allowed/excluded on synthetic channel
  lists (all pass, one fails); Δχ² threshold edge cases.
- `tests/test_p_value.py` — `(chi2=10, ndf=5)` matches scipy to 1e-12.
- `tests/test_aggregate.py` — joins 3 fakes into one sorted CSV;
  determinism across `workers=1` vs `workers=4`.
- `tests/test_cli_args.py` — argparse: required `--model`, mutex
  `--mode`, env-var override for backend, `--delta-chi2` float,
  `--dMh` scalar and JSON object, `--scan-dir` semantics.
- `tests/test_blocker_shape.py` — every emitted blocker validates
  against the shared `blocker.schema.json`.
- `tests/test_charged_higgs_channels.py` — asserts H± channels fire
  for a 2HDM+a-style SLHA fixture and propagate to `per_channel.csv`.
- `tests/test_scope_invariants.py` — three grep-based invariants:
  - `no-cpv`: `grep -rn 'CPViolation\|complex_mixing\|cpv' scripts/`
    returns zero matches.
  - `no-native-backend`: `grep -rn '\--native\|native_input' scripts/`
    returns zero matches.
  - `no-unified-default`: grep ensures `--backend=unified` is never the
    argparse default and always requires the env-var gate.
  - Additional guard: `grep -n 'ndf *= *len(' scripts/p_value.py`
    returns zero matches (p-value df must come from HS native output).
- `tests/test_integration_install.py` — network-gated; full install
  including `chi2_SM_ref` cache creation.
- `tests/test_integration_legacy.py` — network-gated; full install +
  `run` on the 2HDM benchmark.
- `tests/test_integration_unified_skip.py` — network-gated; asserts
  unified driver emits `HIGGSTOOLS_BACKEND_UNAVAILABLE` when the
  Python module is absent, and (if present) succeeds.

---

## 2. Implementation sequence (~13 atomic commits)

Each step is a discrete commit. TDD discipline where feasible (steps
4, 5, 7, 8, 10). Follow `superpowers:test-driven-development`.

1. **Scaffold install skill.** Create `higgstools-install/` dir with
   empty `SKILL.md` stub, `skill_env.yaml` containing version tags and
   full commit SHAs (recorded via `git ls-remote
   gitlab.com/higgsbounds/higgsbounds 5.10.2` and the HS equivalent),
   empty `scripts/`, empty `tests/`. Commit.

2. **Scaffold usage skill.** Create `higgstools/` dir likewise with
   `SKILL.md` stub and empty `scripts/` / `tests/`. Commit.

3. **Install — detect + use-path.** TDD:
   `tests/test_detect_config.sh` first. Implement
   `detect_higgstools.sh` and the `use-path` branch of
   `install_higgstools.sh`. Writes `higgsbounds_path`,
   `higgssignals_path`, `higgstools_backend=legacy` via `config_merge`.

4. **Install — install subcommand (legacy, git-clone path).** TDD:
   `tests/test_install_args.py`. Then implement: disk check,
   gfortran toolchain check, `git clone --depth 1 --branch 5.10.2`
   for HB and `--branch 2.6.2` for HS, `git rev-parse HEAD` verified
   against `skill_env.yaml`. CMake build HB-5 then HS-2 (with
   `-DHiggsBounds_DIR=<hb-build>`). No GitLab archive tarballs in v1.
   Emit blocker codes on failure. Exit with `EXIT_NO_CMAKE=26` /
   `EXIT_NO_PYBIND=27` / `EXIT_NO_GFORTRAN=10` as appropriate (these
   codes are already in `_common.sh` from Phase-0).

5. **Install — smoke test + SM reference cache.** TDD:
   `tests/test_sm_ref_cache.py`. Implement `smoke_test.sh` +
   `cache_sm_reference.py`. Runs HB/HS bundled SM examples, asserts
   outputs in range, runs HS on `tests/fixtures/sm_benchmark.slha`,
   writes `chi2_SM_ref` atomically to
   `$STATE_ROOT/cache/hs2_chi2_sm_ref.json`. Fatal
   `HIGGSTOOLS_SM_REF_MISSING` if any downstream `run` invocation
   finds the cache absent.

6. **Install — unified backend opt-in (graceful skip).** Gated on
   `HEPPH_HIGGSTOOLS_BACKEND=unified` AND `--backend=unified`. Adds
   toolchain check (cmake ≥ 3.16, g++ ≥ 11, Eigen3, GSL, pybind11,
   Boost ≥ 1.74); `git clone --depth 1 --branch v1.7 hbdataset`;
   `git clone --depth 1 --branch v1.1 hsdataset` (SHAs verified);
   build `higgstools` v1.2 with `-DHiggsTools_BUILD_PYTHON=ON`;
   Python smoke test `import Higgs.bounds, Higgs.signals`. On **any
   build failure on macOS arm64**, emit warning + blocker of mode
   `recoverable` and continue — never fatal. Legacy install remains
   authoritative.

7. **Usage — SLHA adapter + exclusion math.** TDD: the committed
   `2hdm_type2_benchmark.slha` fixture first. Implement
   `slha_adapter.py` (required blocks, actionable `user_instruction`
   for missing blocks), `exclusion.py` (`hb_allowed` = AND of
   per-channel `HBresult`; `hs_consistent` = Δχ² vs cached SM ref),
   `p_value.py` (pure scipy wrapper; no df synthesis).

8. **Usage — legacy driver.** TDD: mock subprocess at the binary
   invocation level first. Implement `legacy_driver.py` parsing HB
   per-channel output (id, expref, obsratio, HBresult, reference) and
   HS native chi²/ndf fields. Produces `result.json`,
   `per_channel.csv`, `report.md`, `input_dump.json`. Integration
   test gated on `HEPPH_RUN_NETWORK_TESTS=1`.

9. **Usage — unified driver (opt-in).** Thin wrapper around
   `Higgs.bounds` / `Higgs.signals` Python bindings. Emits the same
   `result.json` schema as legacy (differentiated by `backend` and
   `dataset_version` fields). `test_integration_unified_skip` verifies
   graceful failure when the module is absent.

10. **Usage — run --scan-dir + aggregate collect-only.** TDD:
    `tests/test_aggregate.py` with pre-populated fixture results
    first. Implement `run --scan-dir` to fan out per-point
    evaluations under `multiprocessing.Pool`. Implement
    `aggregate.py` as a **pure collector** — reads existing
    `result.json` files, emits `higgstools_index.csv` sorted by
    `index`, byte-identical across worker counts. `aggregate` never
    invokes HB/HS.

11. **Blocker wiring + schema validation.** Every emit path flows
    through `_blocker.sh` or the Python equivalent.
    `test_blocker_shape.py` iterates every error code and asserts
    JSON-Schema validity against the canonical
    `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

12. **Charged-Higgs + scope-invariant tests.** Commit
    `test_charged_higgs_channels.py` (asserts H± channel IDs appear
    in `per_channel.csv` and `most_sensitive_channel` can point to a
    charged-Higgs row). Commit `test_scope_invariants.py` (three
    grep assertions plus the `ndf = len(` guard on `p_value.py`).

13. **Docs pass + W-verify.** Finalise both `SKILL.md` files with
    error tables, config-key tables, and Apple-Silicon caveat for the
    unified backend. Document the HS `chi2_SM_ref` install-time cache
    step and the `--delta-chi2` override. Run
    `superpowers:verification-before-completion`. Verify that
    `plugins/constraints/README.md` (Phase-0 artifact) correctly
    references both new skills — if not, open a small Phase-0 follow-up
    patch; do not author README content in this workstream.

---

## 3. Test plan

**Unit (no network, 10 tests):**

1. `test_detect_config.sh` — detect/use-path config-file parsing.
2. `test_install_args.py` — argparse + env-var gating for install.
3. `test_sm_ref_cache.py` — SM ref cache shape + absence → fatal.
4. `test_slha_adapter.py` — 2HDM Type-II fixture parses; missing-block
   fatal path emits exactly one `HIGGSTOOLS_SLHA_MISSING_BLOCKS`
   blocker with actionable `user_instruction`.
5. `test_exclusion.py` — `hb_allowed` AND-of-HBresult semantics;
   `hs_consistent` Δχ² threshold edges; `--delta-chi2` honoured.
6. `test_p_value.py` — `scipy` parity to 1e-12 at `(chi2=10, ndf=5)`.
7. `test_aggregate.py` — collect-only: joins 3 pre-populated results
   into one sorted CSV, byte-identical across worker counts.
8. `test_cli_args.py` — full argparse surface including `--scan-dir`
   and `--backend` precedence rules.
9. `test_blocker_shape.py` — every emitted blocker code validates
   against schema.
10. `test_charged_higgs_channels.py` — charged-Higgs dispatch fires on
    a 2HDM+a-style SLHA; `per_channel.csv` contains H± channel IDs.

Plus `test_scope_invariants.py` as a dedicated invariant suite:
`no-cpv`, `no-native-backend`, `no-unified-default`, and the
`ndf = len(...)` guard on `p_value.py`.

**Integration (gated on `HEPPH_RUN_NETWORK_TESTS=1`, 3 tests):**

11. `test_integration_install.py` — full legacy install, SM smoke
    test asserts `HBresult=1` and HS χ² finite < 200, SM ref cache
    populated.
12. `test_integration_legacy.py` — `/higgstools run` on the committed
    2HDM Type-II benchmark SLHA. Asserts `hb_allowed=False` and
    `obsratio_max ∈ [<lo>, <hi>]` at a concrete grid point tabulated
    in HB-5.10.2's manual (exact interval pinned in the test file
    from the manual's tabulated value, not from a figure contour).
13. `test_integration_unified_skip.py` — with
    `HEPPH_HIGGSTOOLS_BACKEND=unified` but the unified build absent,
    asserts a clean `HIGGSTOOLS_BACKEND_UNAVAILABLE` blocker; no
    Python traceback escapes to stderr.

**Golden:** `tests/fixtures/2hdm_type2_benchmark.slha` (pre-run
SPheno, capped at 100 KB) and `tests/fixtures/result_golden.json`.

---

## 4. Verification checklist (exact shell)

Run from the worktree root before marking the workstream done:

- [ ] `pytest plugins/hep-ph-toolkit/skills/higgstools -q` (unit tier)
      exits 0.
- [ ] `pytest plugins/hep-ph-toolkit/skills/higgstools-install -q`
      exits 0.
- [ ] `shellcheck plugins/hep-ph-toolkit/skills/higgstools-install/scripts/*.sh`
      passes.
- [ ] `ruff check plugins/hep-ph-toolkit/skills/higgstools` passes.
- [ ] `grep -rn 'ndf *= *len(' plugins/hep-ph-toolkit/skills/higgstools/scripts/p_value.py`
      returns no matches.
- [ ] `grep -rn 'CPViolation\|complex_mixing' plugins/hep-ph-toolkit/skills/higgstools/scripts/`
      returns no matches.
- [ ] `grep -rn '\-\-native\|native_input' plugins/hep-ph-toolkit/skills/higgstools/scripts/`
      returns no matches.
- [ ] `grep -rn 'archive/.*\.tar\.gz' plugins/hep-ph-toolkit/skills/higgstools-install/scripts/`
      returns no matches (no GitLab tarball archives).
- [ ] `skill_env.yaml` contains real commit SHAs for HB, HS (and
      datasets when unified is applicable); no `TODO`.
- [ ] `HEPPH_RUN_NETWORK_TESTS=1 pytest -m integration
      plugins/hep-ph-toolkit/skills/higgstools` passes on ubuntu-22.04.
- [ ] On macOS arm64, unified-backend build may fail — confirm the
      warning blocker path, not a fatal exit.
- [ ] `aggregate` emits byte-identical CSV for `--workers=1` vs
      `--workers=4` on `tests/fixtures/scan_mini/`.
- [ ] `chi2_SM_ref` cache present at
      `$STATE_ROOT/cache/hs2_chi2_sm_ref.json` after
      `/higgstools-install install`; `run` refuses gracefully if
      absent.
- [ ] `superpowers:verification-before-completion` invoked.

---

## 5. Out of scope (v1)

- **CPV / complex mixing matrices.** Deferred to v1.1. Enforced by
  `no-cpv` grep invariant.
- **`--native` literal-couplings CLI.** Dropped per manager decision.
  Enforced by `no-native-backend` grep invariant.
- **Unified C++ backend as default.** Opt-in only; gated on env-var
  plus flag plus successful build. Graceful skip on macOS arm64 build
  failure. Enforced by `no-unified-default` grep invariant.
- **`update-dataset` subcommand.** Deferred to v1.1 (bundled with
  unified-default promotion).
- **`HEPPH_HIGGSTOOLS_DATASET_OVERLAY`** (user-local limits). v1.1.
- **macOS-14 arm64 CI coverage for unified.** Legacy path expected to
  work; unified path explicitly unverified. v1 CI targets
  ubuntu-22.04 only.
- **GitLab archive tarballs.** Removed in v1 due to server-side
  regeneration instability; `git clone --depth 1` with pinned commit
  SHA is the only v1 source-acquisition mechanism.
- **`/sarah-build` CLI flag for `WriteHiggsBoundsBlocks`.** The
  `user_instruction` for missing-blocks is actionable but abstract:
  the user edits the SARAH `SPheno.m` model directive directly.
  Promoting this to a first-class `/sarah-build` option is a v1.1
  coordinated patch, not part of `/higgstools`.

Word count: ~1,720.
