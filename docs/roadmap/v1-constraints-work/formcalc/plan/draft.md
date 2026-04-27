# `/formcalc` + `/formcalc-install` — Implementation Plan (Draft)

**Author:** plan drafter
**Date:** 2026-04-19
**Input spec:** `docs/roadmap/v1-constraints-work/formcalc/brainstorm/final.md`
**Phase:** B, stage 2 of 3 in `plugins/feynman-diagrams/` (upstream: `/feynarts`; downstream: `/formcalc`).
**Workstream branch:** `workstream-feyndiag-formcalc`

---

## 0. Worktree / branch

Branch name: **`workstream-feyndiag-formcalc`** off `main`, created via the
repo-standard worktree pattern (see `docs/superpowers/workstream-sarah-spheno/`
for examples of parallel isolation). The worktree lives in a sibling directory
so simultaneous work on `/feynarts` and `/formcalc` never stomps `plugins/`
files here.

All edits in this plan land under:

- `plugins/hep-ph-toolkit/skills/formcalc-install/`
- `plugins/hep-ph-toolkit/skills/formcalc/`
- `plugins/hep-ph-toolkit/skills/_shared/amp_reduced.meta.schema.json` (new)
- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` (known-codes enum extension only — no structural change)
- `plugins/feynman-diagrams/.claude-plugin/plugin.json` (skills list bump)
- `.claude-plugin/marketplace.json` (version bump)

No edits to `/feynarts` or `/formcalc` directories. No edits to
`plugins/shared/install-helpers/_common.sh` (shared contract owned by W0).

---

## 1. Shared prereqs (established by sibling workstreams before this plan executes)

Phase B is sequential: `/feynarts` ships first, `/formcalc` second,
`/formcalc` third. This plan therefore **assumes** the following exist on
`main` at the point it begins:

1. `plugins/feynman-diagrams/.claude-plugin/plugin.json` — plugin manifest
   already declares the plugin; this plan only appends skills to its `skills`
   list.
2. `plugins/feynman-diagrams/README.md` — plugin README.
3. `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json` —
   written by `/feynarts`, consumed here (cache-key input, kinematics input).
4. `plugins/hep-ph-toolkit/skills/feynarts/` — `FeynAmpList.m` emission
   contract frozen (see `/feynarts` final §4). We consume `FeynAmpList.m` and
   `FeynAmpList.meta.json` via symlink into our run dir.
5. `plugins/hep-ph-toolkit/SHARED-feynman.md` — Phase-B compatibility matrix pin
   (FeynArts 3.11 ↔ FormCalc 10.0 ↔ LoopTools). This plan writes its
   `formcalc_version` + `form_version` rows there.
6. `plugins/shared/install-helpers/_common.sh` — use as-is; exit codes
   `EXIT_NO_DISK=11 EXIT_DOWNLOAD=12 EXIT_CHECKSUM=13 EXIT_EXTRACT=14
   EXIT_SMOKE=15 EXIT_BAD_PATH=16 EXIT_NO_WOLFRAM=20 EXIT_SPHENO_MAKE=23`
   cover every code used below (we reuse `EXIT_SPHENO_MAKE=23` generically
   for LoopTools/FORM build failures; no new shared exit codes needed).
7. Wolfram-activation helpers
   (`plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh`
   + `_activation_parse.py`) are reused verbatim.

If any of (1)–(5) is absent at start, the first step of this plan is to
block with a pre-flight note — we do **not** create those files here; they
are the `/feynarts` workstream's deliverable.

---

## 2. Files to create

**Installer skill (`plugins/hep-ph-toolkit/skills/formcalc-install/`):**

- `SKILL.md` — invocation contract, subcommand table, blocker codes, config
  keys; mirrors `/sarah-install` SKILL.md shape.
- `scripts/install_formcalc.sh` — Bash orchestrator: `detect | use-path |
  install`. Sources `_common.sh`.
- `scripts/probe_formcalc.wls` — one-shot `wolframscript` probe:
  `Needs["FormCalc`"]; Print[$FormCalcVersion]`; also resolves
  `$UserBaseDirectory`.
- `scripts/build_looptools.sh` — runs `./configure && make` in extracted
  LoopTools tree under `$UserBaseDirectory/Applications/FormCalc-<ver>/LoopTools/`.
  Apple-Silicon branch: probe `libquadmath.dylib` under `brew --prefix gcc`;
  if absent, pass `--without-quad` and record `looptools_quad: false`.
- `scripts/build_form.sh` — downloads FORM 4.3.1 tarball from
  `github.com/vermaseren/form/archive/refs/tags/v4.3.1.tar.gz`, runs
  `autoreconf -i && ./configure --prefix=... && make`, places binary at
  `<install-root>/form/<arch>-<os>/form` (no `$PATH` symlink).
- `scripts/smoke_test.wls` — stage-1 load + stage-2 FORM round-trip on a
  one-diagram QED amplitude; asserts `form.log` contains `Time = `.
- `skill_env.yaml` — pinned versions: `formcalc=10.0`, `form=4.3.1`,
  `looptools=10.0` (bundled); SHA256 placeholders per `_common.sh` convention.
- `tests/test_install_unit.py` — arg parsing, config-merge, platform probe
  (mock `brew`), offline-cache miss path, blocker-JSON schema conformance.
- `tests/test_install_integration.py` — gated on
  `HEPPH_RUN_NETWORK_TESTS=1`; end-to-end install into a tmp
  `$UserBaseDirectory`.
- `tests/fixtures/` — pre-staged tarballs for `HEPPH_NO_NETWORK=1` tests.

**Usage skill (`plugins/hep-ph-toolkit/skills/formcalc/`):**

- `SKILL.md` — `reduce` subcommand contract, γ₅ enforcement, state layout,
  cache rules, blocker table, sidecar schema reference.
- `scripts/run_formcalc.py` — Python CLI entrypoint: parses args, resolves
  paths, computes cache key, dispatches to `run_calcfeynamp.wls`, writes
  sidecar. (Python — matches `/spheno-build` shape.)
- `scripts/prepare_kinematics.py` — reads `ProcessSpec.json`, renders
  `kinematics.m` (`OnShell`, `Mandelstam`, `Neglect` assignments). Template
  uses `str.format` per repo convention.
- `scripts/run_calcfeynamp.wls` — wolframscript driver: `<< FormCalc`;
  `<< FeynAmpList.m`; apply `CalcFeynAmp` with `FermionChains` +
  regulator options; `Abbreviate` + inline abbreviations; `Put` →
  `amp_reduced.m`. Also emits `run/<ts>/summary.json` (PV-head inventory,
  timings). Reads `form_binary` from config and calls
  `SetEnvironment["FORM" -> ...]` (and/or `$FormCmd = ...`; smoke test
  picks the correct lever).
- `scripts/gamma5_static_check.wls` — pre-`CalcFeynAmp` symbolic pass over
  `FeynAmpList.m` counting γ₅-sensitive `DiracTrace`/`FermionChains`
  occurrences. Exits non-zero + emits `FORMCALC_G5_SCHEME_REQUIRED` when
  count > 0 and `--gamma5` absent. **Fatal; no default.**
- `scripts/parse_summary.py` — post-run parser: counts `B0i`/`C0i`/`D0i`,
  detects IR-divergent patterns (`B0[0,0,0]` etc.) → `FORMCALC_IR_DIVERGENT`
  recoverable flag in sidecar `ir_flags`.
- `scripts/cache_key.py` — content-addressed cache key computer per §5 of
  spec. Pure-function; unit-testable.
- `tests/test_run_formcalc.py` — unit tests: CLI parser, kinematics
  renderer (golden string match), cache-key stability, sidecar JSON schema
  validity, γ₅ static check logic with fixture FeynAmpList inputs, blocker
  emission fixtures.
- `tests/test_ee_to_mumu_golden.py` — integration golden gated on
  `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_SLOW_TESTS=1`.
- `tests/fixtures/ee_to_mumu/FeynAmpList.m` — committed fixture (committed
  by `/feynarts` workstream or regenerated here via a one-shot helper).
- `tests/fixtures/ee_to_mumu/ProcessSpec.json` — committed.
- `tests/fixtures/ee_to_mumu/expected_meta.json` — committed (timestamps
  stripped).
- `tests/fixtures/chiral_amp/FeynAmpList.m` — small chiral-trace fixture
  for the γ₅-required unit test.
- `tests/fixtures/non_chiral_amp/FeynAmpList.m` — non-chiral fixture that
  passes γ₅ static check with no flag.

**Shared contract file (new, under `_shared/`):**

- `plugins/hep-ph-toolkit/skills/_shared/amp_reduced.meta.schema.json` —
  JSON Schema for the sidecar per spec §3.2. `/formcalc` writes; `/formcalc`
  reads. Shape pinned by spec.

**Blocker-schema enum extension:**

- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — append to
  the known-codes enum (docstring inside the `code` description). Codes
  added: `FORMCALC_DOWNLOAD_FAILED`, `FORMCALC_SMOKE_TEST_FAILED`,
  `FORMCALC_PATH_INVALID`, `FORM_DOWNLOAD_FAILED`, `FORM_BUILD_FAILED`,
  `FORM_VERSION_MISMATCH` (recoverable), `LOOPTOOLS_BUILD_FAILED`,
  `LOOPTOOLS_QUADMATH_ABSENT`, `FORMCALC_OFFLINE_CACHE_MISS`,
  `FORMCALC_INPUT_MISSING`, `FORMCALC_G5_SCHEME_REQUIRED`,
  `FORMCALC_KERNEL_ERROR`, `FORM_EXECUTION_FAILED`, `FORMCALC_NO_OUTPUT`,
  `FORMCALC_IR_DIVERGENT` (recoverable), `FORMCALC_REG_UNVALIDATED`
  (recoverable). No `reference_only` use anywhere.

---

## 3. Implementation sequence (10 steps)

**Step 1 — Worktree + pre-flight.**
Create `workstream-feyndiag-formcalc` worktree. Confirm assumptions in §1
hold on `main`; if `/feynarts` has not merged `processspec.schema.json`,
stop and surface that blocker to the user — do not stub our own copy.

**Step 2 — Scaffold skill directories + SKILL.md stubs.**
Create both skill directories with `SKILL.md` stubs (name, description
frontmatter only). Land as an empty-scaffold PR first to keep the review
diff small.

**Step 3 — Extend blocker-schema known-codes enum.**
Edit `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` to append
the §2 codes to the description strings (no structural change; enum is
documented, not hard-validated). Commit + unit test that every new code is
referenced from at least one SKILL.md.

**Step 4 — Write `amp_reduced.meta.schema.json`.**
Schema version 1. Required fields: `schema_version`, `producer`,
`formcalc_version`, `form_version`, `looptools_version`, `process_id`,
`gamma5`, `regularization`, `fermion_chain`, `abbreviations_inlined`,
`pv_heads` (array), `kinematic_limit`, `ir_flags` (array), `caveats`
(array). Commit with a unit test that validates the spec §3.2 example.

**Step 5 — Implement `/formcalc-install` installer skill.**
Order inside the installer:
1. `detect` — scan `$UserBaseDirectory/Applications/FormCalc-*/` + config;
   emit `{status, path, version}` JSON.
2. `use-path <dir>` — validate `<dir>/FormCalc.m`, run smoke probe, write
   config. Emits `FORMCALC_PATH_INVALID` or `FORMCALC_SMOKE_TEST_FAILED`.
3. `install` — sequence: wolfram probe → gfortran probe → disk check (≥3
   GB) → `HEPPH_NO_NETWORK` branch → three downloads (FormCalc, FORM;
   LoopTools comes bundled inside the FormCalc tarball per spec §1.1) →
   checksum → extract → LoopTools `make` (with Apple-Silicon quad branch)
   → FORM `configure && make` into `<install-root>/form/<arch>-<os>/` →
   register `$Path` via `init.m` → smoke test → `config_merge` the nine
   keys from spec §1.7. Exit codes mapped to `_common.sh` values.

**Step 6 — Implement the installer integration smoke test.**
Write `scripts/smoke_test.wls` performing both stages (kernel load +
one-diagram FORM round-trip). Assert `form.log` contains `Time = `. Wire
into `install` + `use-path` paths.

**Step 7 — Implement `/formcalc` usage skill core.**
Order:
1. `scripts/run_formcalc.py` — CLI skeleton: arg parse (`--reg`,
   `--gamma5`, `--fermion-chain`, `--force`, `--process`,
   `<model_name>`), state-dir resolution, symlink creation for
   `FeynAmpList.m` + `ProcessSpec.json`.
2. `scripts/cache_key.py` — pure-function key per spec §5; unit tested in
   isolation before wiring.
3. `scripts/prepare_kinematics.py` — ProcessSpec → `kinematics.m` renderer
   with a golden-string unit test.
4. `scripts/gamma5_static_check.wls` — γ₅ trace counter; this step must
   land **before** the driver can be invoked end-to-end, because the
   γ₅-required check is fatal and runs first.
5. `scripts/run_calcfeynamp.wls` — CalcFeynAmp + Abbreviate driver;
   inlines abbreviations; `Put` → `amp_reduced.m`; writes
   `run/<ts>/summary.json`.
6. `scripts/parse_summary.py` — classifies PV heads, IR flags, caveats;
   writes the sidecar `amp_reduced.meta.json` with all required fields
   populated from config + CLI + driver output.
7. Cache flow: hit = log `cache hit` + exit 0; miss = run pipeline; write
   `.build_key` last, atomically.

**Step 8 — γ₅ enforcement end-to-end.**
Verify the gate: chiral FeynAmpList + no `--gamma5` → fatal JSON on stderr
conforming to `blocker.schema.json`, exit code per `_common.sh`. Non-chiral
input + no `--gamma5` → runs fine. Chiral input + `--gamma5 naive` → runs
and writes `gamma5: "naive"` into sidecar + cache key. This step is
implemented as its own commit with a fixture-driven unit test so the gate
is auditable in isolation.

**Step 9 — Tests.**
Implement the full matrix in §4 (below). Unit tests land first and run on
every push. Integration tests are gated on the three env vars from spec §6.

**Step 10 — Plugin manifest + marketplace wiring.**
Append the two skill entries to
`plugins/feynman-diagrams/.claude-plugin/plugin.json`; bump
`.claude-plugin/marketplace.json` version string. Final commit in the PR.

---

## 4. Test plan

### 4.1 Unit (always run — no env-var gating)

- `test_run_formcalc.py::test_cli_rejects_unknown_reg` — invalid
  `--reg foo` → non-zero exit, usage message.
- `test_run_formcalc.py::test_gamma5_required_enum` — `--gamma5` accepts
  exactly `{naive,hv,bmhv,larin}`.
- `test_run_formcalc.py::test_cache_key_stable_across_reruns` — given the
  same (FeynAmpList, ProcessSpec, flags, versions), key is byte-identical
  across 10 recomputes.
- `test_run_formcalc.py::test_cache_key_changes_on_flag_change` — flipping
  `--gamma5 naive` → `--gamma5 hv` changes the key.
- `test_run_formcalc.py::test_prepare_kinematics_golden` — chi-N fixture
  renders to exact `kinematics.m` byte-string.
- `test_run_formcalc.py::test_sidecar_schema_roundtrip` — write sidecar
  from fake-driver output, validate against
  `amp_reduced.meta.schema.json`.
- `test_run_formcalc.py::test_gamma5_static_check_chiral_fixture` — load
  `tests/fixtures/chiral_amp/FeynAmpList.m`, confirm static check flags
  it (integration-gated variant of this also lives in the wolfram-gated
  tier since the static check itself uses `wolframscript`; the unit tier
  exercises the Python dispatcher's handling of the child-process exit
  code via a mock).
- `test_run_formcalc.py::test_blocker_json_validity` — every blocker
  emission path produces single-line JSON conforming to
  `blocker.schema.json`.
- `test_install_unit.py::test_platform_probe_arm_mac_without_brew_gcc` —
  mock `brew --prefix gcc` failure; installer sets
  `looptools_quad: false` and does not abort.
- `test_install_unit.py::test_offline_cache_miss_fatal` — set
  `HEPPH_NO_NETWORK=1` with empty cache → exact
  `FORMCALC_OFFLINE_CACHE_MISS` blocker JSON.
- `test_meta_schema.py::test_example_from_spec_validates` — spec §3.2
  example validates; six negative fixtures (missing each required field)
  fail.

### 4.2 Integration — gated

Gates: `HEPPH_RUN_WOLFRAM_TESTS=1`, `HEPPH_RUN_NETWORK_TESTS=1`,
`HEPPH_RUN_SLOW_TESTS=1`. Tests are skipped when their gate is unset.

- **Installer end-to-end** (`NETWORK`): `install` against tmp
  `$UserBaseDirectory`; asserts `formcalc_path`, `form_binary`,
  `looptools_lib` all resolve and all three version keys are written.
- **Offline install** (no gate, always run): `HEPPH_NO_NETWORK=1` with
  pre-staged tarballs in `$HEPPH_OFFLINE_CACHE`; installer completes
  without `curl`. This exercises the offline path without needing the
  network gate.
- **Smoke test on existing install** (`WOLFRAM`): `use-path <existing>`
  against a committed mock `FormCalc.m` stub + mock FORM binary;
  confirms the smoke `.wls` detects the `Time = ` marker.
- **LoopTools build** (`NETWORK + SLOW`): fresh extract → `make`; asserts
  `libooptools.a` artefact.
- **e⁺e⁻ → μ⁺μ⁻ tree golden** (`WOLFRAM + SLOW`): pipeline from
  committed `FeynAmpList.m` fixture → `/formcalc reduce --reg dimreg` →
  assertions per spec §6.2:
  1. `amp_reduced.m` loads via `Get`.
  2. `amp_reduced.meta.json` validates against the sidecar schema.
  3. A test `.wls` helper squares, sums final / averages initial spins
     in the `s ≫ m_e, m_μ` limit, and `Simplify`s to
     `e^4 (1 + Cos[θ]^2)`. Tolerance: exact symbolic equality after
     `Simplify`.

### 4.3 macOS / Apple-Silicon branch (`NETWORK + SLOW`, CI-host-gated)

- On `darwin-arm64` runners only: full install; asserts
  `looptools_quad: false` present in config. Gracefully skipped on
  non-Apple-Silicon.

---

## 5. Verification checklist

Before opening the PR, confirm:

- [ ] Branch is `workstream-feyndiag-formcalc` and worktree is clean.
- [ ] No edits under `plugins/shared/install-helpers/`.
- [ ] No edits under `plugins/hep-ph-toolkit/skills/feynarts/`.
- [ ] No edits under `plugins/hep-ph-toolkit/skills/looptools*/`.
- [ ] `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json`
      untouched (we only read it).
- [ ] New blocker codes appear only in the `description` of the enum —
      no `reference_only` invocation anywhere.
- [ ] FORM binary lives at `<install-root>/form/<arch>-<os>/form`; no
      symlink into `~/.local/bin`; no `$PATH` modification in
      `config.json`.
- [ ] Three independent version keys (`formcalc_version`,
      `form_version`, `looptools_version`) written by `install`.
- [ ] γ₅ static check exits non-zero + fatal JSON when chiral traces
      present and `--gamma5` absent. No silent default anywhere.
- [ ] `.build_key` written only after the full pipeline succeeds;
      partial failures do not poison the cache.
- [ ] Sidecar `amp_reduced.meta.json` validates against the committed
      schema for the e⁺e⁻ → μ⁺μ⁻ golden.
- [ ] Every blocker emission path conforms to
      `blocker.schema.json` — checked by a unit test.
- [ ] `plugin.json` and `marketplace.json` version strings bumped.
- [ ] README / SHARED.md Phase-B version matrix row updated.
- [ ] All unit tests pass locally; integration tests pass under all
      three env-var gates on the CI host that has them.

---

## 6. Out of scope (v1)

- **Fortran emission** (`WriteSquaredME` and friends). Tracked as v1.1;
  an `--output-mode {symbolic,fortran}` flag will be added then. Tree +
  `fortran` must reject with `FORMCALC_TREE_FORTRAN_REJECTED` to preserve
  the `/madgraph` boundary (per spec §7 item 8).
- **γ₅ schemes beyond `{naive, hv, bmhv, larin}`.** The flag enum
  validates exactly those four; anything else is a CLI parse error.
- **`verify` subcommand.** Deferred; the e⁺e⁻ → μ⁺μ⁻ golden is the
  v1 verification surface.
- **`cdr`/`thv` regulators as first-class.** Accepted by the parser,
  mapped to `dimreg` with a `FORMCALC_REG_UNVALIDATED` recoverable
  caveat in the sidecar. No dedicated golden.
- **`paint` / diagram rendering.** Owned by `/feynarts`; `/formcalc`
  neither reads nor writes `diagrams.pdf`.
- **PV-head translation to LoopTools names.** `/formcalc` emits
  `A0i`/`B0i`/`C0i`/`D0i` (FormCalc-native); translation to `PVA`/`PVB`
  is `/formcalc`'s responsibility per manager decision (spec §3.2).
- **Collier backend** for LoopTools numeric evaluation. Deferred to
  v1.1 per the `/formcalc` scope lock.
- **Pre-existing `form` on `$PATH` adoption.** v1 policy: ignore and use
  our own binary. Revisit only if users complain about disk footprint
  (spec §7 item 6).
- **`reference_only` fallback on missing FormCalc.** Forbidden — missing
  install is always `FORMCALC_PATH_INVALID` / `FORMCALC_SMOKE_TEST_FAILED`
  fatal.
