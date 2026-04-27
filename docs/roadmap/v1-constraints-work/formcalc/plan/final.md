# `/formcalc` + `/formcalc-install` — Final Implementation Plan

**Synthesizer:** plan synthesizer
**Date:** 2026-04-19
**Inputs:** `brainstorm/final.md`, `plan/draft.md`, `plan/critique.md`, Manager cross-workstream decisions.
**Workstream branch:** `workstream-feyndiag-formcalc`
**Phase-B position:** stage 2 of 3 in `plugins/feynman-diagrams/`
(upstream: `/feynarts`; downstream: `/formcalc`).

This plan assumes **Phase-0 has landed on `main`**. All shared schemas,
shared install-helpers, new exit codes, and the promoted Wolfram helpers
are treated as pre-existing. This workstream authors **no shared schema**.

---

## 0. Worktree, branch, Phase-0 prerequisites

Create a sibling worktree `workstream-feyndiag-formcalc` off `main` using
the repo-standard pattern (see `docs/superpowers/workstream-sarah-spheno/`).
All edits in this plan land under:

- `plugins/hep-ph-toolkit/skills/formcalc-install/`
- `plugins/hep-ph-toolkit/skills/formcalc/`
- `plugins/feynman-diagrams/.claude-plugin/plugin.json` (skills list append)
- `.claude-plugin/marketplace.json` (version bump)

**Phase-0 artefacts treated as landed (this plan only consumes them):**

1. `plugins/shared/schemas/processspec.schema.json` — CANONICAL, authored
   in Phase-0. `/formcalc` reads it via `ProcessSpec.json` input symlink.
2. `plugins/shared/schemas/amp_reduced.meta.schema.json` — CANONICAL
   sidecar schema, authored in Phase-0. `/formcalc` writes against it;
   `/formcalc` reads against it.
3. `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` —
   symlink to the relocated model-building schema.
4. `plugins/shared/install-helpers/wolfram/{detect_wolfram.sh,
   check_wolfram_activation.sh, _activation_parse.py}` — promoted helpers.
5. `plugins/shared/install-helpers/atomic_write.sh` — promoted from
   `/spheno-build`'s tmp+fsync+rename+dir-fsync pattern.
6. `plugins/shared/install-helpers/_common.sh` additions:
   `HEPPH_NO_NETWORK`, `HEPPH_OFFLINE_CACHE_DIR`, `EXIT_NO_CMAKE=26`,
   `EXIT_NO_PYBIND=27`, `EXIT_FORM_BUILD=28`, `EXIT_LOOPTOOLS_BUILD=29`,
   `check_macos_sdk.sh`.

Pre-flight as first commit: assert all six items are present on `main`
and exit fatally with a user-facing note if any is missing. We never
stub or recreate shared contracts here.

**`<install-root>` is pinned to `$XDG_DATA_HOME/hep-ph-agents/formcalc-<ver>/`**
with fallback `$HOME/.local/share/hep-ph-agents/formcalc-<ver>/`. The
FormCalc Mathematica application installs to the Wolfram-standard
`$UserBaseDirectory/Applications/FormCalc-<ver>/` for auto-load. Config
key `form_binary` is the sole contract downstream reads; nothing
reconstructs the path.

---

## 1. Files (/formcalc-install, /formcalc)

### 1.1 `/formcalc-install` — installer skill

Under `plugins/hep-ph-toolkit/skills/formcalc-install/`:

- **`SKILL.md`** — contract, mirrors `/sarah-install`. Subcommand table:
  `detect` | `use-path <dir>` | `install [dir]`. Blocker codes table,
  config keys, `HEPPH_NO_NETWORK` contract, Apple-Silicon branch.
- **`scripts/install_formcalc.sh`** — Bash orchestrator. Sources
  `plugins/shared/install-helpers/_common.sh` and
  `plugins/shared/install-helpers/atomic_write.sh`.
- **`scripts/probe_formcalc.wls`** — `wolframscript` probe resolving
  `$UserBaseDirectory` and printing `$FormCalcVersion` post-`Needs`.
- **`scripts/build_looptools.sh`** — runs `./configure && make` in the
  FormCalc-bundled LoopTools tree. Apple-Silicon branch (`uname -m ==
  arm64`): glob `brew --prefix gcc@{13,14,15}` and `brew --prefix gcc`
  for `libquadmath.dylib`; absent → `--without-quad`; record
  `looptools_quad: false`. Failure exits `EXIT_LOOPTOOLS_BUILD=29`
  with blocker `LOOPTOOLS_BUILD_FAILED`.
- **`scripts/build_form.sh`** — downloads **FORM 4.3.1** release tarball
  from `https://www.nikhef.nl/~form/` (Vermaseren's hosted release,
  ships a generated `configure`). Runs `./configure --prefix=<install-root>
  && make`; installs binary at `<install-root>/form/<arch>-<os>/form`.
  Failure exits `EXIT_FORM_BUILD=28` with blocker `FORM_BUILD_FAILED`.
  No `autoreconf`, no `$PATH` symlink.
- **`scripts/smoke_test.wls`** — two-stage test. Stage 1:
  `Needs["FormCalc\`"]; Print[$FormCalcVersion]`. Stage 2: photon
  self-energy one-diagram amplitude via `CreateTopologies[0, 1 -> 1,
  ExcludeTopologies -> Internal]` → `CalcFeynAmp[..., FermionChains ->
  Weyl]`. Asserts `form.log` contains `Time = ` **and** the returned
  expression's head is `Amp`. Deterministic (no random seed).
- **`skill_env.yaml`** — pins: `formcalc=10.0`, `form=4.3.1`,
  `looptools=10.0` (bundled in FormCalc tarball). SHA256 placeholders
  allowed per `_common.sh` convention.
- **`tests/test_install_unit.py`** — arg parsing, config-merge,
  platform probe (mock `uname -m`, mock `brew --prefix gcc*`),
  offline-cache miss path, blocker-JSON conformance.
- **`tests/test_install_integration.py`** — gated on
  `HEPPH_RUN_NETWORK_TESTS=1`; end-to-end into a tmp
  `$UserBaseDirectory`.
- **`tests/fixtures/`** — pre-staged offline tarballs.

### 1.2 `/formcalc` — usage skill

Under `plugins/hep-ph-toolkit/skills/formcalc/`:

- **`SKILL.md`** — `reduce` subcommand; γ₅ fatal gate; state layout;
  cache rules; blocker table; references Phase-0 sidecar schema at
  `plugins/shared/schemas/amp_reduced.meta.schema.json`.
- **`scripts/run_formcalc.py`** — Python CLI entrypoint. Arg parse,
  path resolution, symlink creation (`input/FeynAmpList.m`,
  `input/ProcessSpec.json`), FeynArts-version validation (§1.3),
  cache-key computation, dispatch to `run_calcfeynamp.wls`, sidecar
  write.
- **`scripts/prepare_kinematics.py`** — ProcessSpec JSON →
  `kinematics.m` (`OnShell`, `Mandelstam`, `Neglect`). Pure string
  templating; golden-string unit test.
- **`scripts/gamma5_static_check.wls`** — exact algorithm (§1.3 below).
- **`scripts/run_calcfeynamp.wls`** — `<< FormCalc\`$FormCalcVersion`;
  `<< FeynAmpList.m`; `<< kinematics.m`; `CalcFeynAmp[..., FermionChains
  -> <cli>, Dimension -> <cli>]`; `Abbreviate` + inline; `Put` →
  `amp_reduced.m`. Sets `$FormCmd = config.form_binary` before the
  call. Emits `run/<ts>/summary.json`.
- **`scripts/parse_summary.py`** — counts PV heads (`B0i`, `C0i`,
  `D0i`), detects IR-divergent patterns (`B0[0,0,0]` etc.), produces
  `ir_flags.{ir_divergent, uv_regularized}` for the sidecar.
- **`scripts/cache_key.py`** — pure function per §5. Hashes
  `FeynAmpList.m` bytes, canonical JSON of `ProcessSpec.json`, CLI
  flags, and three tool versions.
- **`scripts/write_sidecar.py`** — assembles
  `amp_reduced.meta.json` matching the Phase-0 canonical schema
  (`schema_version: "amp_reduced.meta/v1"`, `pv_heads:
  "formcalc-native"` — literal string, not an array), validates
  against the schema via `jsonschema`, writes atomically.
- **`tests/test_run_formcalc.py`** — unit tests for CLI, cache-key
  stability, kinematics golden, sidecar-schema validation, γ₅ static
  check dispatcher, blocker emission.
- **`tests/test_ee_to_mumu_golden.py`** — integration, gated on
  `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`.
- **Fixtures** under `tests/fixtures/`:
  `ee_to_mumu/{FeynAmpList.m, FeynAmpList.meta.json, ProcessSpec.json,
  expected_meta.json}`, `chiral_amp/FeynAmpList.m`,
  `chiral_via_coupling/FeynAmpList.m`, `non_chiral_amp/FeynAmpList.m`.

### 1.3 Algorithm specifications

**γ₅ static check (exact).** In `gamma5_static_check.wls`:

```
held = Get["FeynAmpList.m"];  (* held at read *)
chiralHits = Cases[held,
  (ChiralityProjector | gamma5 |
   _Symbol ? (Context[#] === "System`" && (# === 6 || # === 7) &)),
  Infinity];
couplingAxialHits = Cases[held,
  Mat[DiracChain[6 | 7, ___]], Infinity];
hasChiral = Length[chiralHits] > 0 || Length[couplingAxialHits] > 0;
```

If `hasChiral === True` AND the dispatcher did not receive `--gamma5`,
emit fatal `FORMCALC_G5_SCHEME_REQUIRED` on stderr as single-line JSON
and exit non-zero. Regex-on-text is explicitly rejected.

**FeynArts version gate.** Before dispatching the driver,
`run_formcalc.py` reads `input/FeynAmpList.meta.json` (sibling sidecar
produced by `/feynarts`), asserts `feynarts_version` is in the
supported set `{"3.11"}` for v1. Mismatch → fatal
`FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` with `user_instruction`
pointing at `/feynarts-install`.

**PV-heads policy.** `/formcalc` emits FormCalc-native `A0i`, `B0i`,
`C0i`, `D0i` and records `"pv_heads": "formcalc-native"` in the
sidecar. `/formcalc` performs **no** renaming. `/formcalc` does the
B0i/C0i/D0i → PVB/PVC/PVD translation internally.

**Cache atomicity.** `.build_key` is written via the Phase-0
`atomic_write.sh` helper (tmp + `fsync` + `rename` + dir-fsync). Write
order: `amp_reduced.m` → `amp_reduced.meta.json` → `.build_key` last.
On the read side, cache hit requires all three artefacts to exist and
`.build_key` to match; missing output files force a miss even if
`.build_key` matches (guards against mid-run corruption).

---

## 2. Implementation sequence (~12–14 atomic commits)

1. **Phase-0 pre-flight + worktree.** Assert all six Phase-0 artefacts
   exist on `main`. Create worktree. First commit: empty scaffold
   directories with placeholder `SKILL.md` frontmatter only.

2. **`/formcalc-install` SKILL.md + orchestrator skeleton.** Write
   `SKILL.md` end-to-end; write `install_formcalc.sh` with `detect` /
   `use-path` subcommands fully implemented (no `install` yet).

3. **Probe + smoke-test `.wls` scripts.** `probe_formcalc.wls` +
   `smoke_test.wls` with exact assertions (§1.1). Unit test: run
   smoke against a committed mock `FormCalc.m` stub + mock FORM
   binary; assert `Time = ` detection.

4. **FORM build script.** `build_form.sh` with URL pin to
   `https://www.nikhef.nl/~form/` 4.3.1 release tarball. Unit test:
   mock `curl`; assert `--prefix` wiring and binary path.

5. **LoopTools build script + Apple-Silicon branch.** `build_looptools.sh`;
   `uname -m`-based arch detection; `gcc@{13,14,15}` glob for
   `libquadmath.dylib`. Unit test: mock `uname -m`, mock `brew --prefix`.

6. **`install` subcommand end-to-end.** Wire: wolfram probe → gfortran
   → `check_disk 3 5` → `HEPPH_NO_NETWORK` branch → three downloads →
   `verify_checksum` → extract → LoopTools → FORM → `init.m` $Path
   registration → smoke test → `config_merge` of nine keys.

7. **Installer integration test.** Gated on
   `HEPPH_RUN_NETWORK_TESTS=1`; tmp `$UserBaseDirectory`; asserts
   three version keys + `form_binary` resolves executable +
   `looptools_lib` exists.

8. **`/formcalc` SKILL.md + Python CLI skeleton.** `SKILL.md` +
   `run_formcalc.py` with arg parse, state-dir resolution, symlinks.
   Unit tests for CLI.

9. **`cache_key.py` + unit tests.** Pure-function computation;
   stability across reruns; sensitivity to each flag.

10. **`prepare_kinematics.py` + golden.** ProcessSpec JSON →
    `kinematics.m`. Golden-string byte match.

11. **γ₅ static check + FeynArts version gate.** Land both gates
    together in `run_formcalc.py` + `gamma5_static_check.wls`. Three
    fixture variants (chiral, chiral-via-coupling, non-chiral) drive
    the unit tests. Fixture: wrong `feynarts_version` sidecar.

12. **Driver + sidecar writer.** `run_calcfeynamp.wls` +
    `parse_summary.py` + `write_sidecar.py`. Sidecar matches Phase-0
    canonical schema exactly (`pv_heads: "formcalc-native"` literal).

13. **Cache flow + atomic write integration.** Wire
    `plugins/shared/install-helpers/atomic_write.sh` into
    `.build_key`. Unit test: delete `amp_reduced.m` with `.build_key`
    in place → next run is a miss.

14. **Plugin manifest + marketplace wiring.** Append skills to
    `plugins/feynman-diagrams/.claude-plugin/plugin.json`; bump
    `.claude-plugin/marketplace.json` version. Final commit.

---

## 3. Test plan

### 3.1 Unit (ungated — every push)

- **CLI:** unknown `--reg`, invalid `--gamma5`, missing `--process`.
- **Cache key:** stable across 10 recomputes; changes on every flag
  flip and every version change.
- **Kinematics golden:** ProcessSpec fixture → exact `kinematics.m`
  byte-match.
- **Sidecar schema round-trip:** synthetic driver output → validated
  against Phase-0 `amp_reduced.meta.schema.json`; six negative
  fixtures (one per required field missing) must fail.
- **γ₅ static check dispatcher:** Python handles child exit codes for
  chiral, chiral-via-coupling, non-chiral fixtures with and without
  `--gamma5`; matrix of 6 assertions.
- **FeynArts version gate:** fixture with `feynarts_version: "3.10"` →
  fatal `FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE`.
- **Blocker JSON:** every emission path conforms to the symlinked
  `blocker.schema.json`.
- **Installer platform probe:** mock `uname -m = arm64` + missing
  `libquadmath.dylib` → sets `looptools_quad: false`; does not abort.
- **Offline cache miss:** `HEPPH_NO_NETWORK=1` + empty cache → exact
  `FORMCALC_OFFLINE_CACHE_MISS` JSON, exit `EXIT_DOWNLOAD=12`.
- **Cache corruption:** delete `amp_reduced.m`, keep `.build_key`;
  next run is a miss.

### 3.2 Integration — gated

- **Installer end-to-end** (`HEPPH_RUN_NETWORK_TESTS=1`): full
  `install` into tmp `$UserBaseDirectory`; asserts `formcalc_path`,
  `form_binary` resolves executable, `looptools_lib` exists, three
  version keys written, `last_configured` stamped.
- **Offline install** (ungated, always run with pre-staged cache):
  `HEPPH_NO_NETWORK=1` + `$HEPPH_OFFLINE_CACHE_DIR` populated →
  installer completes without network calls.
- **LoopTools build** (`HEPPH_RUN_NETWORK_TESTS=1`): fresh extract +
  `make`; asserts `libooptools.a` artefact.
- **macOS-ARM branch** (`HEPPH_RUN_NETWORK_TESTS=1`, `darwin-arm64`
  only): full install; asserts `looptools_quad: false` recorded.
  Gracefully skipped on other hosts.
- **Smoke on mock install** (`HEPPH_RUN_WOLFRAM_TESTS=1`): `use-path`
  + committed mock `FormCalc.m` stub → smoke detects `Time = ` and
  `Head === Amp`.

### 3.3 QED golden — e⁺e⁻ → μ⁺μ⁻

Gated on `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`.

Committed fixtures:
`tests/fixtures/ee_to_mumu/{FeynAmpList.m, FeynAmpList.meta.json,
ProcessSpec.json}`. Pipeline: `/formcalc reduce ... --reg dimreg`.
Assertions:

1. `amp_reduced.m` loads via `Get[]` without error, is non-empty.
2. `amp_reduced.meta.json` validates against the Phase-0 sidecar
   schema; `pv_heads` field is exactly the string
   `"formcalc-native"`.
3. Test `.wls` helper squares the amplitude, averages over initial
   spins (factor `1/4`), sums over final spins, then applies the
   substitution rule `{EL^4 -> e^4, ME -> 0, MU -> 0}` and
   `FullSimplify[..., Assumptions -> {Element[costh, Reals]}]`. The
   assertion is exact symbolic equality to `e^4 (1 + costh^2)` via
   `PossibleZeroQ[expr - e^4 (1 + costh^2)]`.
4. **Negative control:** the same helper tested against `e^4 (1 +
   costh)^2` must fail — proves the assertion can fail.

---

## 4. Verification checklist

Before opening the PR, confirm:

- [ ] Branch `workstream-feyndiag-formcalc` clean; worktree isolated.
- [ ] **No** edits under `plugins/shared/` (all Phase-0 artefacts consumed as-is).
- [ ] **No** edits to `plugins/shared/install-helpers/_common.sh`.
- [ ] **No** new schema files authored anywhere — both
  `processspec.schema.json` and `amp_reduced.meta.schema.json` remain
  under `plugins/shared/schemas/`.
- [ ] **No** edits under `plugins/hep-ph-toolkit/skills/feynarts/` or
  `plugins/hep-ph-toolkit/skills/formcalc/`.
- [ ] `<install-root>` resolves to `$XDG_DATA_HOME/hep-ph-agents/
  formcalc-<ver>/` with `$HOME/.local/share/...` fallback.
- [ ] FORM binary lives at `<install-root>/form/<arch>-<os>/form`;
  no `$PATH` symlink; no shell rc modification.
- [ ] Three version keys (`formcalc_version`, `form_version`,
  `looptools_version`) written by `install`.
- [ ] γ₅ static check uses the exact `Cases[...]` + `Mat[DiracChain[6|7,
  ...]]` algorithm; regex-on-text is nowhere in the scripts.
- [ ] Sidecar writes `"pv_heads": "formcalc-native"` (string literal).
- [ ] FeynArts version gate fires fatally on `3.10` / `3.9` fixtures.
- [ ] `.build_key` written via `atomic_write.sh` (tmp+fsync+rename+dir-fsync).
- [ ] Cache miss reported when outputs are deleted but `.build_key`
  remains.
- [ ] FORM build failures exit `EXIT_FORM_BUILD=28`; LoopTools
  failures exit `EXIT_LOOPTOOLS_BUILD=29`. No reuse of
  `EXIT_SPHENO_MAKE=23`.
- [ ] QED golden passes, **including** the negative-control failure
  case.
- [ ] Every blocker emission conforms to the symlinked
  `blocker.schema.json` (enforced by unit test).
- [ ] `plugin.json` + `marketplace.json` version strings bumped.

---

## 5. Out of scope for v1

- **Fortran emission** (`WriteSquaredME`). Deferred to v1.1; a
  `--output-mode {symbolic,fortran}` flag lands then. Tree-level +
  `fortran` must reject with `FORMCALC_TREE_FORTRAN_REJECTED` to
  preserve the `/madgraph` boundary.
- **`verify` subcommand.** The e⁺e⁻ → μ⁺μ⁻ golden is the v1
  verification surface.
- **`cdr` / `thv` regulators as first-class.** Accepted by the parser,
  mapped to `dimreg` with sidecar caveat `FORMCALC_REG_UNVALIDATED`.
- **`paint` / diagram rendering.** Owned by `/feynarts`.
- **PV-head translation.** `/formcalc` emits FormCalc-native names;
  `/formcalc` owns the translation table keyed on
  `meta.formcalc_version`.
- **Collier backend** for LoopTools numeric evaluation. v1.1.
- **Adopting a pre-existing `form` on `$PATH`.** v1 ignores and uses
  its own binary; `FORM_VERSION_MISMATCH` is a recoverable caveat
  only.
- **`reference_only` fallback on missing FormCalc.** Forbidden —
  missing install is always `FORMCALC_PATH_INVALID` or
  `FORMCALC_SMOKE_TEST_FAILED` fatal.
- **Additional γ₅ schemes beyond `{naive, hv, bmhv, larin}`.** Parser
  enum-validates exactly those four.
- **FeynArts versions other than 3.11.** Any other value is fatal;
  expanding the set requires a SHARED.md matrix update and a new
  compatibility test, out of v1 scope.

---

**Word count:** ~1750.
