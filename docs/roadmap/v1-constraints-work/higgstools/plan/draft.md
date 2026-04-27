# /higgstools — Executable Plan (Draft)

Converts `brainstorm/final.md` into a step-by-step workstream for one
implementer. Legacy HB-5.10.2 + HS-2.6.2 Fortran is the v1 default path.
Unified C++ (`higgstools` v1.2) is opt-in via `HEPPH_HIGGSTOOLS_BACKEND=unified`.
Two subcommands only: `run`, `aggregate`. No analytic fallback.

---

## 0. Worktree / branch

- **Branch:** `workstream-constraints-higgstools`
- **Worktree root:** `~/Projects/hep-ph-agents-worktrees/constraints-higgstools/`
- Created via `superpowers:using-git-worktrees` from `main`. All edits confined
  to the worktree; no writes to the primary checkout while this workstream is
  in flight. Sibling constraint workstreams (`/micromegas`, `/ddcalc`) run on
  their own branches and merge independently; conflicts in
  `plugins/constraints/.claude-plugin/plugin.json` are resolved at merge time,
  not during development.

---

## 1. Shared prereqs

These files may already exist from sibling constraint workstreams. The
implementer MUST check before creating; **touch only if absent**.

| Path | Owner | Create-if-absent? |
|---|---|---|
| `plugins/constraints/.claude-plugin/plugin.json` | first constraint ws to land | Yes — manifest listing `higgstools`, `higgstools-install`, `micromegas`, `micromegas-install`, `ddcalc`, `ddcalc-install` skills (empty `skills` list is fine; added by each ws in its own commit). |
| `plugins/constraints/README.md` | first constraint ws | Yes — one-paragraph index. |
| `plugins/constraints/SHARED.md` | first constraint ws | Yes — documents the cross-plugin contract: the constraints plugin reads `config.models[<name>].latest_slha` written by `/spheno-build` in `model-building`, via the shared `~/.config/hep-ph-agents/config.json`. Matches brainstorm §3 cross-plugin note. |
| `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | first constraint ws | **Do not duplicate.** Symlink or one-line Python import pointing at `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. Preferred: import path added to `sys.path` in each skill's test conftest. Decision: keep the canonical schema under `model-building` for v1; promote to `plugins/shared/schemas/` in a later W0 pass. |
| `plugins/shared/install-helpers/_common.sh` | **W0 only** | See §3 step 1 for the `EXIT_NO_CMAKE=26` / `EXIT_NO_PYBIND=27` coordination. |
| `.claude-plugin/marketplace.json` | W0 | Add an entry for `constraints` plugin if not present; otherwise no-op. |

If another sibling workstream has already created any of these, the implementer
**rebases onto `main`** rather than duplicating. No file in step 1 is
`higgstools`-specific.

---

## 2. Files to create

All paths are under the worktree root.

**Install skill** — `plugins/hep-ph-toolkit/skills/higgstools-install/`
- `SKILL.md` — mirrors `sarah-install/SKILL.md` structure: When-to-invoke,
  Decision flow (`detect` / `use-path` / `install`), JSON status contract,
  Failure modes → blockers, Config keys written, Version pin and override,
  Linkage.
- `skill_env.yaml` — pins: `HB_VERSION=5.10.2`, `HS_VERSION=2.6.2`,
  `HT_VERSION=1.2`, `HBDATASET_TAG=v1.7`, `HSDATASET_TAG=v1.1`;
  SHA256 fields for `higgsbounds-5.10.2.tar.gz` and
  `higgssignals-2.6.2.tar.gz` (`TODO` permitted only through the scaffolding
  commit; must be replaced with real hashes before the W-verify gate — see §3
  step 2).
- `scripts/install_higgstools.sh` — bash driver. Sources
  `plugins/shared/install-helpers/_common.sh` via the 4-levels-deep pattern
  documented at the top of `_common.sh`. Implements `detect`, `use-path`,
  `install` (legacy default; `--backend=unified` gated on env var). Uses
  `check_disk 3`, `download_with_retry`, `verify_checksum`, `config_merge`.
- `scripts/detect_higgstools.sh` — idempotent state probe. Returns one of
  `configured` / `found` / `missing` JSON on stdout.
- `scripts/_blocker.sh` — one-liner emitter matching
  `model-building/skills/sarah-install/scripts/_blocker.sh`.
- `scripts/smoke_test.sh` — runs HB's bundled `example_SM_vs_4thgen` and HS's
  bundled SM example, asserts `HBresult=1` and chi² finite < 200.
- `tests/test_detect_config.sh` — unit: config + path parsing (no network).
- `tests/test_install_args.py` — unit: argparse for `--backend`, env-var
  gating, dry-run path.

**Usage skill** — `plugins/hep-ph-toolkit/skills/higgstools/`
- `SKILL.md` — When-to-invoke, two subcommands (`run`, `aggregate`), inputs
  (`--model`, `--slha`, `--dMh`, `--mode`, `--backend`, `--channels`,
  `--delta-chi2`, `--workers`), data contract (SLHA2 is the schema; no
  intermediate JSON), outputs (`result.json`, `per_channel.csv`, `report.md`,
  `input_dump.json`), exclusion conventions (HB-5 obsratio, HS Δχ² < 6.18),
  error modes, scan parallelism.
- `scripts/run_higgstools.py` — CLI entry. Dispatches `run` vs `aggregate`.
- `scripts/slha_adapter.py` — parses SLHA2, extracts `MASS`, `HMIX`, decays,
  `HiggsBoundsInputHiggsCouplingsFermions`, `HiggsBoundsInputHiggsCouplingsBosons`.
  Fatal `HIGGSTOOLS_SLHA_MISSING_BLOCKS` on missing blocks (with
  `user_instruction` to rerun `/sarah-build` with `WriteHiggsBoundsBlocks=True`).
  Fallback path: accept legacy `HiggsBounds` block with warning; **error if
  both absent** — no synthesis.
- `scripts/legacy_driver.py` — invokes HB-5/HS-2 Fortran binaries via
  subprocess, parses stdout into a uniform result dict. Writes the Fortran
  input files the binaries expect (`MHall_uncertainties.dat`, etc.).
- `scripts/unified_driver.py` — imports `Higgs.bounds`, `Higgs.signals`;
  gated behind env var; raises `HIGGSTOOLS_BACKEND_UNAVAILABLE` if
  `HEPPH_HIGGSTOOLS_BACKEND=unified` but the module is absent.
- `scripts/exclusion.py` — `compute_hb_allowed(obsratio_max)`,
  `compute_hs_consistent(chi2_total, chi2_sm_ref, delta_chi2=6.18)`.
- `scripts/pvalue.py` — `scipy.stats.chi2.sf` wrapper for
  `p_value_rates` / `p_value_masses`.
- `scripts/aggregate.py` — walks a `scan_<TS>/` directory, joins per-point
  `result.json` into `higgstools_index.csv` sorted by SPheno `index` column.
  Uses `multiprocessing.Pool(os.cpu_count() or HEPPH_HIGGSTOOLS_WORKERS)`.
- `scripts/report.py` — renders `report.md` from `result.json`.
- `tests/fixtures/2HDM-II-benchmark.slha` — 2HDM Type-II benchmark at
  `(m_A=400, tanβ=10, cos(β-α)=0.1)`. Adapted from HB-5.10.2
  `example_data/`. Hard-capped at 100 KB.
- `tests/fixtures/result_golden.json` — expected HB-excluded result for the
  above SLHA (`hb_allowed=False`, obsratio within ±5% of HB manual Fig. 7).
- `tests/fixtures/scan_mini/` — 5 fake per-point `result.json` files for the
  aggregate determinism test.
- `tests/test_slha_adapter.py` — parses the 2HDM fixture; asserts
  couplings, masses, widths, and missing-block fatal path.
- `tests/test_exclusion.py` — obsratio 0.7 → allowed; 1.3 → excluded; Δχ²
  threshold edge cases.
- `tests/test_pvalue.py` — `(chi2=10, ndf=5)` matches scipy to 1e-12.
- `tests/test_aggregate.py` — joins 3 fakes into one sorted CSV; determinism
  across `workers=1` vs `workers=4`.
- `tests/test_cli_args.py` — argparse surface: required `--model`, mutex
  `--mode`, env-var override for backend, schema-valid blocker on bad input.
- `tests/test_blocker_shape.py` — every emitted blocker validates against
  `blocker.schema.json`.
- `tests/test_integration_legacy.py` — network-gated; full install + run on
  the 2HDM benchmark.
- `tests/test_integration_unified_skip.py` — network-gated; asserts
  unified-backend driver emits `HIGGSTOOLS_BACKEND_UNAVAILABLE` when the
  Python module is absent, and succeeds when it is present.

---

## 3. Implementation sequence

Each step is a discrete commit. TDD discipline: test before implementation
where feasible (steps 4, 5, 6, 8). Follow `superpowers:test-driven-development`.

1. **Coordinate W0 exit codes.** Open a W0 patch request to add
   `EXIT_NO_CMAKE=26` and `EXIT_NO_PYBIND=27` to
   `plugins/shared/install-helpers/_common.sh` (after `EXIT_NO_LAPACK=25`).
   If that patch is already merged at branch-creation time, no-op. If not,
   leave a TODO in `install_higgstools.sh` referencing
   `EXIT_GENERIC=1` with a code-comment marker
   `# TODO(W0): replace with EXIT_NO_CMAKE once _common.sh patch lands`.
   This is the **only** step that may touch `plugins/shared/`.

2. **Scaffold + pin hashes.** Create the two skill dirs with `SKILL.md`,
   `skill_env.yaml`, empty `scripts/`, empty `tests/`. Download both
   tarballs locally (outside the worktree), compute `sha256sum`, paste real
   values into `skill_env.yaml`. Verify both URLs resolve on
   `gitlab.com/higgsbounds/{higgsbounds,higgssignals}`. Commit.

3. **Create shared prereqs** (§1) only for those that do not exist.
   Single commit, no skill code yet.

4. **Install skill — detect + use-path.** TDD:
   `tests/test_detect_config.sh` first. Implement `detect_higgstools.sh`
   and `use-path` branch of `install_higgstools.sh`. Write
   `higgsbounds_path`, `higgssignals_path` via `config_merge`.

5. **Install skill — install subcommand (legacy).** TDD:
   `tests/test_install_args.py` first for argparse + env-var gating. Then
   the bash install flow: disk check, download, checksum, extract, `cmake`
   HB-5, `cmake` HS-2 with `-DHiggsBounds_DIR=<hb-build>`, smoke test
   (bundled SM examples). Emit blocker codes per brainstorm §1.2.

6. **Install skill — unified backend path.** Gated on
   `HEPPH_HIGGSTOOLS_BACKEND=unified` AND `--backend=unified` flag. Adds
   toolchain check (cmake ≥ 3.16, g++ ≥ 11, Eigen3, GSL, pybind11, Boost ≥
   1.74); `git clone --depth 1 --branch v1.7 hbdataset` and `v1.1 hsdataset`;
   build `higgstools` v1.2 with `-DHiggsTools_BUILD_PYTHON=ON`; Python smoke
   test. SKILL.md includes explicit Apple Silicon caveat from brainstorm §1.

7. **Usage skill — SLHA adapter + exclusion math.** TDD: golden 2HDM
   fixture first. `slha_adapter.py` parses required blocks, raises
   `HIGGSTOOLS_SLHA_MISSING_BLOCKS` otherwise. `exclusion.py` and
   `pvalue.py` are pure functions with unit tests.

8. **Usage skill — legacy driver.** TDD: mock subprocess at the level of
   the Fortran binary invocation; then implement `legacy_driver.py` against
   the real HB-5/HS-2 binaries. Integration test gated on
   `HEPPH_RUN_NETWORK_TESTS=1`. Produce `result.json`, `per_channel.csv`,
   `report.md`, `input_dump.json` — field-by-field match to brainstorm §2.

9. **Usage skill — unified driver (opt-in).** Thin wrapper around
   `Higgs.bounds` / `Higgs.signals` Python bindings. Emits identical
   `result.json` schema as legacy (same `backend` and `dataset_version`
   fields distinguish them). Test_integration_unified_skip verifies
   graceful failure when unavailable.

10. **Aggregate subcommand.** Walks `scan_<TS>/`, parallelises per-point
    runs, emits `higgstools_index.csv` sorted by `index`, byte-identical
    across worker counts. Snapshots dataset version into each
    `input_dump.json` per brainstorm §7.

11. **Blocker wiring + schema validation test.** Every emit path passes
    through `_blocker.sh` or the Python equivalent; `test_blocker_shape.py`
    iterates every error code and asserts JSON-Schema validity.

12. **Docs pass.** Finalise SKILL.md for both skills; add the two-sentence
    CP-conservation caveat (v1.1 backlog note); update
    `plugins/constraints/README.md` to list the new skills. Run the
    `superpowers:verification-before-completion` checklist (§5 below).

---

## 4. Test plan

**Unit (no network, 5 tests):**
1. `test_blocker_shape.py` — every emitted blocker validates against
   `blocker.schema.json`.
2. `test_cli_args.py` — argparse: required/mutex args, env-var
   `HEPPH_HIGGSTOOLS_BACKEND` overrides config, `--delta-chi2` parsed as
   float, `--dMh` accepts scalar and JSON object.
3. `test_slha_adapter.py` — missing-block fatal path: a synthetic SLHA
   without `HiggsBoundsInputHiggsCouplingsFermions` produces exactly one
   stderr blocker with `code=HIGGSTOOLS_SLHA_MISSING_BLOCKS` and an actionable
   `user_instruction`.
4. `test_pvalue.py` — `(chi2=10, ndf=5)` matches `scipy.stats.chi2.sf` to
   1e-12; edge cases `ndf=0`, `chi2=0`.
5. `test_exclusion.py` — HB allowed at `obsratio=0.7`, excluded at `1.3`;
   HS consistent at `Δχ²=6.0`, inconsistent at `6.2`; `--delta-chi2`
   override honoured.

**Integration (gated on `HEPPH_RUN_NETWORK_TESTS=1`, 3 tests):**
6. `test_integration_install.py` — full install of legacy HB-5.10.2 +
   HS-2.6.2, SM smoke test asserts `HBresult=1` and HS chi² finite.
7. `test_integration_legacy.py` — runs `/higgstools run` against the
   2HDM Type-II benchmark SLHA (`(m_A=400, tanβ=10, cos(β-α)=0.1)`);
   asserts `hb_allowed=False` and `obsratio_max` within ±5% of HB manual
   Fig. 7 quoted value.
8. `test_integration_unified_skip.py` — with
   `HEPPH_HIGGSTOOLS_BACKEND=unified` but the unified build absent,
   asserts a clean `HIGGSTOOLS_BACKEND_UNAVAILABLE` blocker (no Python
   traceback escapes to stderr).

---

## 5. Verification checklist

Before marking the workstream done:
- [ ] All 5 unit tests pass under `pytest plugins/hep-ph-toolkit/skills/higgstools`.
- [ ] Both install scripts pass `shellcheck`.
- [ ] Python scripts pass `ruff` (repo default config) and `mypy --strict`
      where type hints are present.
- [ ] `skill_env.yaml` contains real SHA256 values (no `TODO`).
- [ ] `SKILL.md` for both skills contains the brainstorm §1.2 and §2 error
      tables verbatim.
- [ ] `plugins/constraints/SHARED.md` documents the cross-plugin SLHA
      contract.
- [ ] `test_integration_legacy.py` passes in a one-shot CI run on
      `ubuntu-22.04` with `HEPPH_RUN_NETWORK_TESTS=1` (macOS arm64 is
      **not** required for v1 — see brainstorm §1).
- [ ] `aggregate` produces byte-identical `higgstools_index.csv` for
      `workers=1` vs `workers=4` on the 5-point fixture.
- [ ] No call-site in any script performs an analytic fallback; every error
      path either returns a real tool result or emits a fatal blocker.
- [ ] No `reference_only` exits.
- [ ] `superpowers:verification-before-completion` skill invoked before
      claiming done.

---

## 6. Out of scope (v1)

- **CPV / complex mixing matrices.** Deferred to v1.1. SKILL.md states this
  explicitly with a one-line backlog pointer.
- **`--native` input path.** Dropped per manager decision. No literal
  couplings-on-the-CLI interface; SLHA2 is the only input.
- **Unified C++ backend as default.** Opt-in only for v1. Promotion to
  default tracked as a v1.1 milestone gated on CI-green on ubuntu-22.04
  **and** macOS-14 arm64.
- **`update-dataset` subcommand.** Deferred to v1.1 (bundled with unified
  backend promotion).
- **HEPPH_HIGGSTOOLS_DATASET_OVERLAY** (user-local limits). v1.1 backlog.
- **macOS-14 arm64 CI coverage.** Legacy path is expected to work; unified
  path is explicitly unverified. v1 CI targets ubuntu-22.04 only.

Word count: ~1,720.
