# `/micromegas` — Implementation Plan (FINAL)

Author: plan-synthesizer agent
Date: 2026-04-19
Inputs reconciled: `plan/draft.md`, `plan/critique.md`, `brainstorm/final.md` (authoritative spec),
manager cross-workstream decisions, verified helpers at
`plugins/shared/install-helpers/_common.sh`, reference skills `/spheno-build` and `/sarah-install`.

This is the hand-off artefact for a coding agent working in an isolated git worktree.
No further exploration is required.

---

## 0. Worktree, branch, commit prefix, Phase-0 prereq

- **Branch:** `workstream-constraints-micromegas`
- **Worktree dir:** `../hep-ph-agents.worktrees/constraints-micromegas/`
- **Base:** `main` (after Phase-0 prep commit lands; see below)
- **Skill to use:** `superpowers:using-git-worktrees`. Never edit `main` directly.
- **Commit prefix:** `W7-mO:` (next free numeric slot per `git log --oneline -20`; W0–W6 used, sibling workstreams use `W7-dd:` and `W7-ht:`). Confirm next slot by running `git log --oneline -20` before first commit; if anyone else has landed a `W7` between plan time and start, bump to `W8-mO:`.
- **Commit-body convention:** no `Co-Authored-By:` lines unless the user explicitly requests them. Body ends with a single blank line.

### Phase-0 prep commit (prerequisite — NOT owned by this workstream)

The manager lands a `phase-0-constraints-shared-skeleton` commit on `main` **before** this workstream's Step 1. That commit creates all shared/contested artefacts so `/micromegas`, `/ddcalc`, and `/higgstools` do not race:

- `plugins/constraints/.claude-plugin/plugin.json` (skeleton, empty `skills: []`)
- `plugins/constraints/README.md`
- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — relative symlink → `../../../model-building/skills/_shared/blocker.schema.json`
- `plugins/shared/schemas/scattering.schema.json` — canonical (field list frozen, see manager decisions)
- `.claude-plugin/marketplace.json` entry for `constraints`
- `CLAUDE.md` Plugin Categories row for `Constraints`
- `_common.sh` additions: `HEPPH_NO_NETWORK` + `HEPPH_OFFLINE_CACHE_DIR` awareness in `download_with_retry`; exit codes `EXIT_NO_CMAKE=26`, `EXIT_NO_PYBIND=27`, `EXIT_FORM_BUILD=28`, `EXIT_LOOPTOOLS_BUILD=29`; a new helper `check_macos_sdk.sh`

**This workstream must not create, re-author, relocate, or marketplace-edit any of the above.** It only *consumes* them and *appends* its two skill entries to the existing `plugin.json`.

Before any work begins, assert Phase-0 has landed:

```
test -f plugins/shared/schemas/scattering.schema.json
test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json
test -f plugins/constraints/.claude-plugin/plugin.json
grep -q 'HEPPH_NO_NETWORK' plugins/shared/install-helpers/_common.sh
grep -q 'check_macos_sdk' plugins/shared/install-helpers/check_macos_sdk.sh 2>/dev/null \
  || test -f plugins/shared/install-helpers/check_macos_sdk.sh
```

If any fails → abort; surface to manager. Do not proceed.

---

## 1. Files to create (per-file plan; Phase-0 exclusions explicit)

All paths absolute from repo root `/Users/yianni/Projects/hep-ph-agents/`.

### 1.1 NOT created here (Phase-0 owned — consume only)

- `plugins/constraints/.claude-plugin/plugin.json` — only *append* entries for `micromegas-install` and `micromegas` to the existing `skills[]` array (Step 1). Sibling workstreams append theirs independently; merge strategy is lexical sort of `skills[]`.
- `plugins/constraints/README.md` — append a "Skills" row per new skill (Step 1). Do not rewrite.
- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — already a symlink. Consume via relative include from `scripts/_blocker.sh`.
- `plugins/shared/schemas/scattering.schema.json` — already authored. Consume for runtime validation in `write_summary.py` and tests. **Do not edit.**
- `.claude-plugin/marketplace.json`, `CLAUDE.md` — untouched.
- `plugins/shared/install-helpers/_common.sh` — untouched. Network-policy + cache logic already lives here; call `download_with_retry` as-is, trusting it honours `HEPPH_NO_NETWORK=1` and `HEPPH_OFFLINE_CACHE_DIR`.

### 1.2 `/micromegas-install` skill

Directory: `plugins/hep-ph-toolkit/skills/micromegas-install/`

| File | Purpose |
|---|---|
| `SKILL.md` | Full skill doc, `/spheno-build`-voice (imperative, table-heavy). Sections: When to invoke; Decision flow (ASCII, `/sarah-install`-style); Subcommands (`detect`, `use-path`, `install`); JSON status contract; CalcHEP handling (bundled + `--calchep-path`); `HEPPH_NO_NETWORK` handling; macOS build notes; Failure modes → blockers table; Config keys written; Version pin + override; Linkage. |
| `skill_env.yaml` | `micromegas_version: 6.0.5`, `micromegas_url: https://lapth.cnrs.fr/micromegas/downloadarea/micromegas_6.0.5.tgz`, `micromegas_sha256: TODO` (policy: warn-not-abort per `verify_checksum`), `seed: 42`. |
| `scripts/install_micromegas.sh` | Dispatcher: `install_micromegas.sh {detect\|use-path\|install} [args...]`. Sources `_common.sh` via the 4-levels-deep pattern documented at top of `_common.sh`. Exit codes: reuses shared `EXIT_*`; adds local 30=`EXIT_CALCHEP_BAD`, 31=`EXIT_MACOS_SDK`, 32=`EXIT_MICROMEGAS_SMOKE`, 33=`EXIT_BUILD_NET`, 34=`EXIT_PPPC_MISSING`. |
| `scripts/detect.sh` | Emits `{"status":"configured"\|"found"\|"missing",...}` to stdout. Probes via `config_get micromegas_path`; checks `$path/sources/` and `$path/CalcHEP_src/` exist; parses `$path/include/VERSION` (fallback: `grep -h 'version' $path/man/*.txt`). Exit 0 in all three states. |
| `scripts/use_path.sh` | Args: `<dir> [--calchep-path <dir>]`. Validates `$dir/sources/` + (bundled) `$dir/CalcHEP_src/getFlags`; if `--calchep-path`, instead validates `$calchep_path/getFlags` + `$calchep_path/../bin/s_calchep`. Runs smoke via `_smoke.sh`. Writes config via `config_merge`. Exit codes: 0 configured, 16 `MICROMEGAS_PATH_INVALID`, 30 `CALCHEP_PATH_INVALID`, 32 `MICROMEGAS_SMOKE_TEST_FAILED`. |
| `scripts/install_impl.sh` | Bundled install. Stages: (1) `check_disk 3 5`; (2) `download_with_retry` — already `HEPPH_NO_NETWORK`-aware per Phase-0; if it returns the new exit `EXIT_NO_NETWORK`, we repackage as fatal blocker `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`; on generic download failure → `MICROMEGAS_DOWNLOAD_FAILED`; (3) `verify_checksum` (TODO → warn); (4) extract to `${1:-$HOME/micrOMEGAs}/micromegas_6.0.5/`; (5) `source _macos_env.sh`; (6) `make -C "$path" -j"$(nproc 2>/dev/null \|\| sysctl -n hw.ncpu)"` inside a PATH-override sandbox that stubs `curl`/`wget`/`git` (see §1.2.bis); (7) `_smoke.sh`; (8) PPPC tables check at top-level `$path/Data/AtProduction_gammas.dat` (manual 6.0.5 layout, not `Data/pppc4dmid/`); (9) `config_merge` writes the five keys (§2 of brainstorm). |
| `scripts/_macos_env.sh` | Sources into installer on macOS. Calls Phase-0 `check_macos_sdk.sh`; exports `SDKROOT`, `FFLAGS=-ff2c` (when Homebrew gfortran detected via `gfortran --version \| grep -i Homebrew`), `LDFLAGS=-Wl,-ld_classic`, and `DYLD_LIBRARY_PATH="$path/lib:$DYLD_LIBRARY_PATH"` for smoke scope only (never echoed into user shell). On SDK mismatch → emit `MICROMEGAS_MACOS_SDK_MISMATCH` and exit 31. **TODO (v1.1 comment in file):** patch `CalcHEP_src/getFlags` for arm64 (currently falls back to x86_64 flags and fails on clang 15+). Document as known limitation in SKILL.md § macOS notes. |
| `scripts/_smoke.sh` | Compiles and runs `$path/MSSM/main.c`; asserts stdout matches regex `Omega h\^?2\s*=\s*[0-9.eE+-]+` with a finite positive parse (no numeric check). On failure → `MICROMEGAS_SMOKE_TEST_FAILED`, exit 32, stderr tail in `context.stdout_tail`. |
| `scripts/_blocker.sh` | Copy of `plugins/hep-ph-toolkit/skills/sarah-install/scripts/_blocker.sh` (not symlink — will diverge with mO-specific `context` fields like `attempted_url`, `sdkroot`). Emits one-line blocker JSON on stderr; best-effort validates via `jsonschema` when importable. |
| `scripts/_netguard.sh` | PATH-override sandbox used by Stage 6: prepends a temp dir with `curl`/`wget`/`git` stubs that `exit 42` and log `NETGUARD: <tool> <args>` to a file. `install_impl.sh` reads the log after `make`; any entry → promote to fatal `MICROMEGAS_BUILD_NEEDS_NETWORK` with `context.attempted_url` parsed from the log. |

Tests directory: `plugins/hep-ph-toolkit/skills/micromegas-install/tests/`

| File | Tier | Purpose |
|---|---|---|
| `test_detect_states.sh` | unit | stubs config via temp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`; asserts `missing`/`found`/`configured` JSON. |
| `test_use_path_validation.py` | unit | runs `use_path.sh` on fake dirs; asserts blocker codes `MICROMEGAS_PATH_INVALID`, `CALCHEP_PATH_INVALID`. |
| `test_no_network_policy.py` | unit | sets `HEPPH_NO_NETWORK=1` and empty `HEPPH_OFFLINE_CACHE_DIR`; runs `install_impl.sh`; asserts exit 12 + blocker `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`. |
| `test_netguard.sh` | unit | runs `_netguard.sh` wrapping a fake `make` that calls `curl http://x`; asserts log entry + `MICROMEGAS_BUILD_NEEDS_NETWORK` emission. |
| `test_macos_env.sh` | unit, Darwin-only (`[ "$(uname -s)" = Darwin ]` guard) | stubs `xcrun`; verifies exports. |
| `test_blocker_schema_valid.py` | unit | every `fixtures/blockers/*.json` validates against `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. |
| `test_install_offline.sh` | integration, `HEPPH_RUN_NETWORK_TESTS=1` | pre-stages tarball in cache, runs install under `HEPPH_NO_NETWORK=1`; asserts exit 0 + config keys + smoke passes. |

Fixtures: `tests/fixtures/fake_micromegas_tree/` with minimal `sources/`, `CalcHEP_src/getFlags`, `MSSM/main.c` stub; `tests/fixtures/blockers/*.json` one per code.

### 1.3 `/micromegas` skill

Directory: `plugins/hep-ph-toolkit/skills/micromegas/`

| File | Purpose |
|---|---|
| `SKILL.md` | `/spheno-build`-voice. Sections: When to invoke; Prerequisites (state from `/sarah-build`, `/spheno-build`, `/micromegas-install`); Subcommands (`relic`, `scatter`, `annihilate`, `indirect`, `--precompiled`); Inputs (positional model + `spec.yaml` + SLHA + UFO); DM candidate resolution (spec > CLI > auto-detect); Outputs (per-run dir, `summary.json`, `spectra.h5`, `report.md`); Scan mode schema; Recoverable vs fatal contract (brainstorm §2); Data contracts (UFO path, cache key, SLHA path, schema pointer to `plugins/shared/schemas/scattering.schema.json`); Cosmology + form-factor presets; Fixture and testing notes; Scripts reference table. |
| `templates/spec.yaml` | Annotated template. Mandatory `dm_candidate: { pdg, name, mass_gev }`; optional `halo: shm`, `nucleon_form_factors: default_2018`, `cosmology: standard_thermal`, `precompiled_project: null`. Field names match `plugins/shared/schemas/scattering.schema.json`. |
| `requirements.txt` | `h5py>=3.0`, `jsonschema>=4.17`, `pyyaml>=6.0`. |
| `scripts/run_micromegas.py` | CLI entry `run_micromegas.py <subcmd> <model> [flags...]`. Exit 0 success, 2 fatal (blocker on stderr), 3 recoverable (scan continues). |
| `scripts/resolve_dm_candidate.py` | Pure Python. `resolve(spec_dict, cli_pdg, auto_detect_flag, slha_masses, ufo_particles) -> (pdg, name, mass_gev, reason)`. Raises `DMResolutionError(code)` for the three fatal codes + `DM_CANDIDATE_AMBIGUOUS` recoverable. Zero-width `DECAY` block keeps a candidate; non-zero width disqualifies (brainstorm §2). |
| `scripts/parse_slha_mass_block.py` | Pure Python. `read_masses(path) -> {pdg: mass_gev}`. Importable function; reused by resolver tests. |
| `scripts/ufo_to_calchep.sh` | Wraps `newProject` + UFO import. Cache key: `sha256(tar(ufo_dir)) ++ micromegas_version ++ ufo_dialect`, where `ufo_dialect` is read from `$ufo_dir/__init__.py`'s `UFO_VERSION` attribute (fallback: `$ufo_dir/restrict_default.dat` presence → `"1.x"`). Cache at `$STATE_ROOT/models/<name>/micromegas_project/cache/<hash>/`. **Concurrency:** `flock -x "$STATE_ROOT/.locks/micromegas_cache_<hash>.lock"` around population (mirror `/ddcalc`'s `flock` discipline); directory fill is write-to-`<hash>.tmp` then atomic `mv`. Emits `UFO_CONVERT_FAILED` or `CALCHEP_CONVERTER_VERSION_SKEW`. |
| `scripts/main_c_template.py` | Pure-Python code generator — **no template engine**, just `textwrap.dedent` + f-strings. Public: `render(subcommand, spec, dm, halo) -> str`. Deterministic byte-for-byte output. Embeds `HEPPH_MICROMEGAS_SEED=42` in every driver. **Signature source of truth:** verify `darkOmega`, `nucleonAmplitudes`, `calcSpectrum` signatures by grepping `sources/ms_constructor.c` and `sources/*.h` in the Phase-0-installed 6.0.5 tarball before committing goldens. Document the verified C signatures in a comment header at the top of this file. |
| `scripts/build_project.sh` | `make main` inside cached project dir. On non-zero → `MICROMEGAS_PROJECT_BUILD_FAILED` with `make_log_tail` (40 lines) via `_make_log_parse.py` shim (copy from `/spheno-build`). |
| `scripts/run_point.py` | Single-point execution. Classifies stdout: success → parse; crash → `MICROMEGAS_RUNTIME_FAILURE` (recoverable); NaN/negative Ωh² → `OMEGA_UNCONVERGED` (recoverable). For `relic`: runs twice at `Beps=1e-4` and `1e-6`; if |Δ|/Ω > 20% → `RELIC_BEPS_SENSITIVE` recoverable. Seed `HEPPH_MICROMEGAS_SEED=42` passed through environment. |
| `scripts/parse_micromegas_out.py` | Pure Python. Regex table for `Omega h^2 =`, `Xf=`, channel rows, `sigma_v(v=0)=`, `sigma_SI(p)=`, `sigma_SI(n)=`, `sigma_SD(p)=`, `sigma_SD(n)=`. |
| `scripts/scan.py` | Sequential Cartesian product, axes `name=start:stop:step=s`. Mirrors `plugins/hep-ph-toolkit/skills/spheno-build/scripts/scan.py` grid-parsing exactly (import and reuse its `parse_axis` and `product_iter` — do not reimplement). Columns: `index, <params>, omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0, status, blocker_code, run_dir, timing_s`. |
| `scripts/write_summary.py` | Assembles `summary.json`, validates against `plugins/shared/schemas/scattering.schema.json` before writing. Field names snake_case with unit suffix per Phase-0 schema (`m_dm_gev`, `sigma_si_proton_cm2`, etc.). |
| `scripts/render_report.py` | String-builder (no jinja) → `report.md` with Planck comparison (`Ωh² = 0.120 ± 0.0012`, pull, pass/fail). |
| `scripts/regenerate_fixture.py` | Gated on `HEPPH_RUN_NETWORK_TESTS=1`. Runs the shipped `Singlet_DM/` benchmark project inside the installed micrOMEGAs tree (no SARAH/UFO round-trip) and captures its stdout, `summary.json`, and report. This is the mechanism that reproduces the golden (§3). |

Tests: `plugins/hep-ph-toolkit/skills/micromegas/tests/`

| File | Tier | Purpose |
|---|---|---|
| `test_resolve_dm_candidate.py` | unit | `test_spec_wins_over_cli`, `test_auto_detect_ambiguous_raises`, `test_charged_lsp_fatal`, `test_colored_lsp_fatal`, `test_zero_width_decay_keeps_candidate`. |
| `test_parse_slha_mass_block.py` | unit | standard SLHA parse + malformed-block error. |
| `test_parse_micromegas_out.py` | unit | parse singletDM stdout fixture, NaN → `OMEGA_UNCONVERGED`, channels sum to 1 ± 1e-6. |
| `test_main_c_template.py` | unit | byte-identical golden per subcommand (`relic`, `scatter`, `annihilate`, `indirect`); seed pinned to 42. |
| `test_summary_schema.py` | unit | validates fixture `summary_singletDM.json` against `plugins/shared/schemas/scattering.schema.json`; negative-sigma rejected; removing required `m_dm_gev` rejected. |
| `test_blocker_shape.py` | unit | iterate `fixtures/blockers/*.json`; each validates. |
| `test_scan_determinism.py` | unit | two invocations byte-identical CSV. |
| `test_beps_sensitivity.py` | unit | mocked `run_point` returns Ωh² differing 25% between `Beps` values → `RELIC_BEPS_SENSITIVE`. |
| `test_flock_cache.py` | unit | two parallel `ufo_to_calchep.sh` invocations on same hash; only one populates; other waits. |
| `test_ufo_conversion.py` | integration, gated | SARAH-emitted singletDM UFO → CalcHEP project smoke. |
| `test_singletdm_golden.py` | integration, gated | see §3 golden description. |

Fixtures: `tests/fixtures/` — `stdout_singletDM.txt`, `stdout_singletDM_nan.txt`, `slha_singletDM.spc`, `ufo_singletDM/` (stub), `main_c/{relic,scatter,annihilate,indirect}_singletDM.c`, `summary_singletDM.json`, `blockers/*.json` (one per code), `spec_singletDM.yaml`. Hard cap: 10 MB total; use `regenerate_fixture.py` pattern where needed.

---

## 2. Implementation sequence (10 atomic commits)

Atomicity rule (explicit): *a commit is atomic iff (a) every test that existed before the commit still passes, and (b) every test added in the commit passes. Tests authored for later commits are marked `pytest.mark.skipif(not _deps_available(), reason="...")` or `.sh` guarded.* Compressed from 12 to 10 to honour this.

**Commit 1 — Plugin wiring + `scattering.schema.json` consumer test.**
Append `micromegas-install` and `micromegas` entries to the Phase-0 `plugins/constraints/.claude-plugin/plugin.json` `skills[]` (lexical sort). Append skill rows to `plugins/constraints/README.md`. Add `test_scattering_schema_self.py` that only asserts the Phase-0 schema file parses + validates as Draft 2020-12 (no authoring). Commit: `W7-mO: wire micromegas skills into constraints plugin`.

**Commit 2 — `/micromegas-install` detect + use-path + blockers.**
Implement `install_micromegas.sh` dispatcher, `detect.sh`, `use_path.sh`, `_blocker.sh`, `_macos_env.sh`. Add tests `test_detect_states.sh`, `test_use_path_validation.py`, `test_macos_env.sh`, `test_blocker_schema_valid.py`. Commit: `W7-mO: /micromegas-install detect + use-path`.

**Commit 3 — `/micromegas-install` install + netguard + smoke.**
Implement `install_impl.sh`, `_smoke.sh`, `_netguard.sh`. Add `test_no_network_policy.py`, `test_netguard.sh`, and gated `test_install_offline.sh`. Commit: `W7-mO: /micromegas-install bundled install + netguard`.

**Commit 4 — `/micromegas-install` SKILL.md + skill_env.yaml.**
Full SKILL.md (includes arm64 CalcHEP TODO as documented limitation). Commit: `W7-mO: /micromegas-install SKILL.md + version pin`.

**Commit 5 — DM resolver + SLHA parser + parser + templates (pure-Python batch).**
Implement `resolve_dm_candidate.py`, `parse_slha_mass_block.py`, `parse_micromegas_out.py`, `main_c_template.py`, `write_summary.py`, `render_report.py`. Add all five resolver tests, SLHA test, parser tests, byte-identical template goldens, summary-schema tests, blocker-shape test. **No CLI yet** — all functions importable; tests drive them directly. Tree is green; CLI skippable placeholder. Commit: `W7-mO: pure-Python core (resolver, parsers, templates)`.

**Commit 6 — UFO→CalcHEP + project build + flock.**
Implement `ufo_to_calchep.sh`, `build_project.sh`, `_make_log_parse.py`. Unit tests: fake-make, cache-hit, version-skew blocker, `test_flock_cache.py`. Commit: `W7-mO: UFO to CalcHEP cache + flock concurrency`.

**Commit 7 — `run_point.py` + Beps probe + `run_micromegas.py` CLI.**
Implement `run_point.py` with double-`Beps` probe, `run_micromegas.py` dispatcher. `test_beps_sensitivity.py` green. CLI end-to-end callable (mocked micrOMEGAs binary in unit tier). Commit: `W7-mO: /micromegas CLI + Beps coannihilation probe`.

**Commit 8 — Scan mode.**
Implement `scan.py` importing from `/spheno-build/scripts/scan.py`. `test_scan_determinism.py` green. Commit: `W7-mO: /micromegas scan mode`.

**Commit 9 — `/micromegas` SKILL.md + `templates/spec.yaml` + `requirements.txt`.**
Full SKILL.md. Commit: `W7-mO: /micromegas SKILL.md + spec template`.

**Commit 10 — Golden fixture + integration tests + `regenerate_fixture.py`.**
Author gated `test_singletdm_golden.py` and `test_ufo_conversion.py`. `regenerate_fixture.py` runs the micrOMEGAs-shipped `Singlet_DM/` benchmark project with its default inputs (no arithmetic by us); the committed `summary_singletDM.json` reflects **the values micrOMEGAs itself produces** for the shipped benchmark. Assertion discipline: `test_singletdm_golden.py` compares integration-run output to the captured fixture with tolerance `rel ≤ 1e-3` on `omega_h2` and `rel ≤ 5e-3` on σ-fields (numerical reproducibility of the tool, not a physics claim). Commit: `W7-mO: singlet_DM golden via shipped benchmark + integration gates`.

Total: 10 atomic commits, each green-at-tree.

---

## 3. Test plan (unit + integration + golden)

### Unit tier (always on, no network, no make)

- `test_scattering_schema_self.py` — Phase-0 schema is valid Draft 2020-12.
- `test_detect_states.sh`, `test_use_path_validation.py`, `test_macos_env.sh` (Darwin guard), `test_blocker_schema_valid.py`, `test_no_network_policy.py`, `test_netguard.sh`.
- `test_resolve_dm_candidate.py` (5), `test_parse_slha_mass_block.py`, `test_parse_micromegas_out.py` (3), `test_main_c_template.py` (5 incl. seed pin), `test_summary_schema.py` (3), `test_blocker_shape.py`, `test_scan_determinism.py`, `test_beps_sensitivity.py`, `test_flock_cache.py`.

### Integration tier (gated on `HEPPH_RUN_NETWORK_TESTS=1`)

- `test_install_offline.sh` — offline rebuild from cached tarball.
- `test_ufo_conversion.py` — SARAH-emitted singletDM UFO → CalcHEP project (requires prior `/sarah-build` state on the runner).
- `test_singletdm_golden.py` — runs micrOMEGAs against the shipped `Singlet_DM/` benchmark project *and* via our pipeline; both must match the captured `summary_singletDM.json` within the tolerances above.

### Golden fixture — reproducibility against the shipped benchmark

- **Source:** `micromegas_6.0.5/Singlet_DM/` benchmark project, run with its default `main.c` inputs (unmodified).
- **Method:** `regenerate_fixture.py` runs the benchmark in the installed tree and captures stdout + parsed `summary.json`. The committed fixture *is* those captured values.
- **Assertion in CI:** the integration test reproduces the captured values within a small numerical tolerance. No independent arithmetic by us — the test confirms our pipeline agrees with the micrOMEGAs-shipped project, nothing more.
- **Why this matters:** the critique flagged the earlier `λ_hS=0.05 → Ωh²=0.118` assertion as physically wrong. Using the shipped benchmark removes our arithmetic from the golden and converts it to a pure reproducibility check against the tool.

**CI:** no changes to CI config in v1. Unit tier is the default; `HEPPH_RUN_NETWORK_TESTS=1` opts in locally.

---

## 4. Verification checklist (exact shell commands)

Run from repo root `/Users/yianni/Projects/hep-ph-agents/`:

- `python -m json.tool .claude-plugin/marketplace.json >/dev/null`
- `python -m json.tool plugins/constraints/.claude-plugin/plugin.json >/dev/null`
- `python -m json.tool plugins/shared/schemas/scattering.schema.json >/dev/null`
- `python -c "import jsonschema, json; jsonschema.Draft202012Validator.check_schema(json.load(open('plugins/shared/schemas/scattering.schema.json')))"`
- `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json && readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — must print `../../../model-building/skills/_shared/blocker.schema.json`.
- `grep -c '"name": "constraints"' .claude-plugin/marketplace.json` — ≥ 1.
- `grep -c '"micromegas"' plugins/constraints/.claude-plugin/plugin.json` — ≥ 2 (both skills).
- `pytest plugins/hep-ph-toolkit/skills/micromegas-install/tests/ -v`
- `pytest plugins/hep-ph-toolkit/skills/micromegas/tests/ -v`
- `bash plugins/hep-ph-toolkit/skills/micromegas-install/tests/test_detect_states.sh`
- `bash plugins/hep-ph-toolkit/skills/micromegas-install/scripts/install_micromegas.sh detect` — returns `{"status":"missing"}` on clean env, exit 0.
- `HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/empty bash plugins/hep-ph-toolkit/skills/micromegas-install/scripts/install_micromegas.sh install 2>&1 \| grep -q MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`
- `git log --oneline -1 \| grep -q '^[a-f0-9]* W7-mO:'` — commit prefix sanity.
- `git diff main --stat` — sanity check file inventory matches §1.

Integration gate (optional, developer machine with micrOMEGAs installable):

- `HEPPH_RUN_NETWORK_TESTS=1 pytest plugins/hep-ph-toolkit/skills/micromegas-install/tests/test_install_offline.sh -v`
- `HEPPH_RUN_NETWORK_TESTS=1 pytest plugins/hep-ph-toolkit/skills/micromegas/tests/test_singletdm_golden.py -v`

---

## 5. Out of scope for v1

Explicitly NOT implemented (per `brainstorm/final.md` §4 and manager rules):

- NREFT operator-basis σ (Anand–Fitzpatrick–Haxton). v1.1.
- Asymmetric DM / two-component `darkOmega2`. v1 refuses with fatal `MULTICOMPONENT_UNSUPPORTED`.
- Loop-level σ_SI (blind-spot paper Eqs. 9, 14, 23). Owned by Phase B `/looptools`.
- Non-standard cosmologies (early matter domination, entropy injection).
- `/micromegas all` composite subcommand. Orchestrator composes.
- `reference_only` blocker state / `MICROMEGAS_ANALYTIC_FALLBACK` / `--allow-analytic-fallback`. Manager-deleted.
- Concurrent scan parallelism (serial only in v1).
- micrOMEGAs 6.1.x (UFO 2.0). Re-pin is a v1.1 ticket gated on W3 emitting UFO 2.0.
- Halo presets beyond SHM; form-factor presets beyond `default_2018` and `A1`.
- Collier backend / Collier-based loop integrals.
- Relocating `blocker.schema.json` under `plugins/shared/schemas/` — manager-decided, stays where it is in v1.
- CI config changes.
- Authoring `plugin.json`, `README.md`, `marketplace.json`, `CLAUDE.md`, `scattering.schema.json`, or `_common.sh` additions — all Phase-0.
- Arm64 `CalcHEP_src/getFlags` patch — documented limitation, v1.1 ticket.

End of final plan.
