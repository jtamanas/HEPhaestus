# `/micromegas` — Implementation Plan (DRAFTER)

Author: plan-drafter agent
Date: 2026-04-19
Inputs: `../brainstorm/final.md` (authoritative), reference skills
`plugins/hep-ph-toolkit/skills/{spheno-build,sarah-install}/`, shared
blocker schema, `plugins/shared/install-helpers/_common.sh`.

This plan is hand-off for a coding agent working in an isolated git worktree.
No further exploration should be required.

---

## 0. Worktree + branch naming

- Branch: `workstream-constraints-micromegas`
- Worktree dir: `../hep-ph-agents.worktrees/constraints-micromegas/`
- Base: `main` (latest commit at plan time: `41f8b5d`)
- Use `/using-git-worktrees` skill. Never edit `main` directly.
- All commits prefixed `W-constraints-mO:` so sibling workstreams (`W-constraints-ddcalc`, `W-constraints-higgstools`) stay distinguishable in log.

---

## 1. Shared prerequisites (flag for coordination)

These files are also needed by the sibling `/ddcalc` and `/higgstools` workstreams. Implementer MUST check existence first; if present, **pick up — do not overwrite**. If absent, create.

| Path | Shared with | Action |
|---|---|---|
| `plugins/constraints/.claude-plugin/plugin.json` | ddcalc, higgstools | create if missing; extend `skills[]` array additively |
| `plugins/constraints/README.md` | ddcalc, higgstools | create skeleton; append section if exists |
| `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | all constraints skills | symlink (relative) to `../../../model-building/skills/_shared/blocker.schema.json`; if symlink exists, leave it |
| `plugins/shared/schemas/scattering.schema.json` | ddcalc, looptools | create only if missing; otherwise load, diff against §2.10 draft, and coordinate via a TODO note in the draft |
| `.claude-plugin/marketplace.json` | all | add `constraints` plugin entry idempotently (check `name == "constraints"` before inserting) |
| `CLAUDE.md` | all | add row `Constraints \| constraints \| ...` to the Plugin Categories table idempotently |

Guardrail: every create step must begin with `test -e <path> && echo "exists — picking up"` equivalent so sibling PRs land cleanly. Record which artefacts pre-existed in the commit body of Step 1.

---

## 2. Files to create (per-file plan)

All paths absolute.

### 2.1 Plugin scaffold

**`/Users/yianni/Projects/hep-ph-agents/plugins/constraints/.claude-plugin/plugin.json`**
Plugin manifest. Mirrors shape of `plugins/model-building/.claude-plugin/plugin.json`. Fields: `name="constraints"`, `description="DM phenomenology constraints — relic density, direct/indirect detection, Higgs measurements"`, `version="0.1.0"`, `skills[]` with entries for `micromegas-install` and `micromegas` (plus placeholders commented out for ddcalc/higgstools to aid sibling picks-up — if policy forbids, document in PR body instead).

**`/Users/yianni/Projects/hep-ph-agents/plugins/constraints/README.md`**
One-page plugin overview. Sections: Purpose, Skills (table), Install order (`/sarah-install` → `/spheno-install` → `/micromegas-install`), Cross-plugin data contracts pointer to `plugins/shared/schemas/scattering.schema.json`, Env vars table (`HEPPH_MICROMEGAS_VERSION`, `HEPPH_MICROMEGAS_SEED`, `HEPPH_NO_NETWORK`, `HEPPH_CACHE_DIR`, `HEPPH_RUN_NETWORK_TESTS`, `HEPPH_STATE_ROOT`).

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`**
Relative symlink → `../../../model-building/skills/_shared/blocker.schema.json`. Per final.md §6 Q5 default: avoid relocating the canonical copy in v1.

### 2.2 Shared schema

**`/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/scattering.schema.json`**
Full JSON Schema draft-2020-12 file implementing the key list in final.md §3 (`m_dm_gev`, σ_SI/SD per nucleon, `source`, `source_run`, `halo`, `nucleon_form_factors`, `cosmology`, `dm_candidate`, `relic`, `annihilation`, `indirect`). `required` = `["m_dm_gev","sigma_si_proton_cm2","source","source_run","dm_candidate"]`. All cross-section fields `{ "type":"number", "minimum":0 }`. `halo` sub-schema: preset string OR inline object with `rho_local_gev_cm3`, `v_0_km_s`, `v_esc_km_s`. `additionalProperties: true` (micromegas may add extras that ddcalc ignores). `$id: https://hep-ph-agents/schemas/scattering/v1`.

### 2.3 `/micromegas-install` skill

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/SKILL.md`**
Section headings (prose at impl time, voice = spheno-build SKILL.md):
- When to invoke
- Decision flow (ASCII diagram, mirrors sarah-install)
- Subcommands (`detect`, `use-path`, `install`)
- JSON status contract
- CalcHEP handling (bundled + `--calchep-path`)
- `HEPPH_NO_NETWORK` handling
- macOS build notes
- Failure modes → blockers (table from final.md §1)
- Config keys written
- Version pin and override
- Linkage

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/skill_env.yaml`**
Pins: `micromegas_version: 6.0.5`, `micromegas_url: https://lapth.cnrs.fr/micromegas/downloadarea/micromegas_6.0.5.tgz`, `micromegas_sha256: TODO`, `seed: 42`.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/install_micromegas.sh`**
Dispatcher. Usage: `install_micromegas.sh {detect|use-path|install} [args...]`. Sources `_common.sh` with the 4-levels-deep pattern. Stdout: status JSON for `detect`/`use-path`; info log on `install` success. Stderr: blockers JSON + `[mO-install]` log lines. Exit codes reuse shared set (`EXIT_*`) plus local 26=`EXIT_CALCHEP_BAD`, 27=`EXIT_MACOS_SDK`, 28=`EXIT_SMOKE`.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/detect.sh`**
Emits `{"status":"configured"|"found"|"missing",...}` to stdout. Probes `config.micromegas_path` (via `config_get`), checks `sources/` + `CalcHEP_src/` existence, runs `version_probe` (read `$path/VERSION` or parse `configure` header). Exit 0 in all three states.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/use_path.sh`**
Args: `<dir> [--calchep-path <dir>]`. Validates `sources/` directory; if `--calchep-path` given, validates `CalcHEP_src/getFlags` and `bin/s_calchep`. Runs smoke test (compile `MSSM/main.c`). Writes config via `config_merge`. Exit: 0 configured, 16 `MICROMEGAS_PATH_INVALID`, 26 `CALCHEP_PATH_INVALID`, 15 `MICROMEGAS_SMOKE_TEST_FAILED`.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/install_impl.sh`**
Full bundled install. Stages:
1. `check_disk 3 5`
2. Download under `HEPPH_NO_NETWORK` trap → `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY` (new fatal).
3. `download_with_retry` → `MICROMEGAS_DOWNLOAD_FAILED`.
4. `verify_checksum` (warn on TODO).
5. Extract to `${1:-$HOME/micrOMEGAs}/micromegas_6.0.5/`.
6. macOS env setup (`SDKROOT`, `FFLAGS`, `LDFLAGS`) — calls `_macos_env.sh`.
7. `make -C $path -j$(os.cpu_count)` with network trap (`MICROMEGAS_BUILD_NEEDS_NETWORK`).
8. Smoke test via `_smoke.sh`.
9. Check PPPC tables exist (`Data/pppc4dmid/*`) → `PPPC_TABLES_MISSING`.
10. `config_merge` writes the five keys from final.md §1.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/_macos_env.sh`**
Sources into the installer. Sets `SDKROOT`, `FFLAGS`, `LDFLAGS`, `DYLD_LIBRARY_PATH` per final.md §1. Emits `MICROMEGAS_MACOS_SDK_MISMATCH` if `xcrun --show-sdk-path` fails on macOS 14+.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/_smoke.sh`**
Compiles and runs `$path/MSSM/main.c`. Asserts stdout contains regex `Omega h\^?2\s*=\s*[0-9.eE+-]+` with finite positive parse. No numeric check. Exits 15 with `MICROMEGAS_SMOKE_TEST_FAILED` + stdout tail on failure.

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/scripts/_blocker.sh`**
Copy of `sarah-install/scripts/_blocker.sh` — emits single-line blocker JSON on stderr; validates before emit by piping through `jsonschema` if available (best-effort).

**Tests `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas-install/tests/`:**

- `test_detect_states.sh` — unit: stubs config file with temp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`; asserts JSON output for `missing`, `found`, `configured` paths.
- `test_use_path_validation.py` — pytest: invokes `use_path.sh` on fake dirs; asserts blocker codes `MICROMEGAS_PATH_INVALID`, `CALCHEP_PATH_INVALID`.
- `test_no_network_policy.py` — pytest: sets `HEPPH_NO_NETWORK=1`, empties `HEPPH_CACHE_DIR`, runs `install_impl.sh`; asserts `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY` emitted and exit 12.
- `test_macos_env.sh` — unit: stubs `xcrun` in PATH; verifies env exports. Skipped on Linux via `[ "$(uname -s)" = Darwin ]` guard.
- `test_blocker_schema_valid.py` — every fixture blocker validates against `blocker.schema.json`.
- (Integration, gated on `HEPPH_RUN_NETWORK_TESTS=1`) `test_install_offline.sh` — pre-stages tarball in cache, runs install with `HEPPH_NO_NETWORK=1`, asserts exit 0 + config keys present + smoke passes.

Fixtures: `tests/fixtures/fake_micromegas_tree/` — minimal `sources/`, `CalcHEP_src/getFlags`, `MSSM/main.c` stub for path-validation tests.

### 2.4 `/micromegas` skill

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas/SKILL.md`**
Section headings:
- When to invoke
- Prerequisites (state from `/sarah-build`, `/spheno-build`, `/micromegas-install`)
- Subcommands (`relic`, `scatter`, `annihilate`, `indirect`, with `--precompiled`)
- Inputs (positional model + spec.yaml + SLHA + UFO)
- DM candidate resolution (spec > CLI > auto-detect rule)
- Outputs (per-run dir layout, `summary.json` keys, `spectra.h5`, `report.md`)
- Scan mode (`scan_index.csv` schema)
- Recoverable vs fatal contract (table from final.md §2)
- Data contracts (UFO path, cache key, SLHA path, schema pointer)
- Cosmology + form-factor presets
- Fixture and testing notes
- Scripts reference (table)

**`/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas/templates/spec.yaml`**
Annotated YAML template. Keys: `model`, `dm_candidate: { pdg, name, mass_gev }` (mandatory), `halo: shm`, `nucleon_form_factors: default`, `cosmology: standard_thermal`, `precompiled_project: null`. Inline comments cite final.md §3.

**Scripts `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas/scripts/`:**

- `run_micromegas.py` — CLI entry. `run_micromegas.py <subcmd> <model> [flags...]`. Dispatches to subcommand handlers. Exit 0 on success, 2 on fatal blocker (blocker JSON on stderr), 3 on recoverable (in scan mode, continues).
- `resolve_dm_candidate.py` — pure Python. `resolve(spec_dict, cli_pdg, auto_detect_flag, slha_masses, ufo_particles) -> (pdg, name, mass, reason)`. Raises `DMResolutionError(code)` for `DM_CANDIDATE_AMBIGUOUS`, `DM_CANDIDATE_UNPHYSICAL`, `DM_CANDIDATE_COLOR_MISMATCH`.
- `parse_slha_mass_block.py` — pure Python. Reads `Block MASS` → `{pdg: mass_gev}`. Same semantics as `/spheno-build/scripts/parse_slha.py` but exported as importable function.
- `ufo_to_calchep.sh` — wraps micrOMEGAs `newProject` + UFO conversion. Args: `<ufo_dir> <project_dir>`. Cache key: `sha256(tar(ufo_dir)) || micromegas_version || ufo_dialect`. Cache at `$STATE_ROOT/models/<name>/micromegas_project/cache/<hash>/`. Emits `UFO_CONVERT_FAILED` or `CALCHEP_CONVERTER_VERSION_SKEW`.
- `main_c_template.py` — generates `main.c` driver. Public: `render(subcommand, spec, dm, halo) -> str`. Subcommand-specific templates for `relic`, `scatter`, `annihilate`, `indirect`. Deterministic byte-for-byte output for golden tests.
- `build_project.sh` — `make main` inside cached project dir. Emits `MICROMEGAS_PROJECT_BUILD_FAILED` on non-zero with `make_log_tail` (40 lines, via `_make_log_parse.py` shim).
- `run_point.py` — single-point execution. Copies `main.c`, `make main`, runs `./main` with SLHA path arg, classifies stdout: success → parse; crash → `MICROMEGAS_RUNTIME_FAILURE` (recoverable); NaN Ωh² → `OMEGA_UNCONVERGED` (recoverable). Calls Beps sensitivity probe for `relic` (runs twice at `Beps=1e-4` and `1e-6`; if delta>20%, emit `RELIC_BEPS_SENSITIVE`).
- `parse_micromegas_out.py` — pure Python. Parses micrOMEGAs stdout into `summary.json` field names per final.md §3. Uses regex table for `Omega h^2 =`, `Xf=`, `channel [ frac ]` rows, `sigma_v(v=0)=`, `sigma_SI(p)=`, `sigma_SI(n)=`, `sigma_SD(p)=`, `sigma_SD(n)=`.
- `scan.py` — sequential Cartesian product over `--scan name=start:stop:step=s` axes, identical semantics to `/spheno-build/scan.py`. Writes `scan_index.csv` with columns per final.md §2.
- `write_summary.py` — assembles `summary.json`, validates against `plugins/shared/schemas/scattering.schema.json` before writing. Asserts `additionalProperties` OK.
- `render_report.py` — jinja-free string builder → `report.md` with Planck comparison (`Ωh² = 0.120 ± 0.0012`, pull number, pass/fail).
- `regenerate_fixture.py` — post-fixture builder (see spheno-build parallel). Runs only when `HEPPH_RUN_NETWORK_TESTS=1`; rebuilds the golden `singletDM` outputs.

**Tests `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas/tests/`:**

- `test_resolve_dm_candidate.py`
  - `test_spec_wins_over_cli` — spec sets pdg=52; CLI sets 1000022; assert spec value returned.
  - `test_auto_detect_ambiguous_raises` — two Z2-odd states equal mass → `DM_CANDIDATE_AMBIGUOUS`.
  - `test_charged_lsp_fatal` — charged candidate → `DM_CANDIDATE_UNPHYSICAL`.
  - `test_colored_lsp_fatal` — color-triplet → `DM_CANDIDATE_COLOR_MISMATCH`.
  - `test_decay_width_used_not_presence` — non-zero DECAY width disqualifies; zero-width DECAY block keeps it (per final.md §2 critic §3).
- `test_parse_micromegas_out.py`
  - `test_parse_singletdm_stdout_fixture` — fixture `stdout_singletDM.txt` → expected dict.
  - `test_omega_nan_triggers_recoverable` — NaN in fixture → marks `OMEGA_UNCONVERGED`.
  - `test_channels_sum_to_one` — fractions sum with tolerance 1e-6.
- `test_main_c_template.py`
  - `test_relic_template_bytes_match_golden` — renders against `fixtures/main_c/relic_singletDM.c`.
  - `test_scatter_template_bytes_match_golden` — ditto for scatter.
  - `test_annihilate_template_bytes_match_golden`.
  - `test_indirect_template_bytes_match_golden`.
  - `test_seed_pinned_to_42` — rendered file contains `HEPPH_MICROMEGAS_SEED=42` path.
- `test_summary_schema.py`
  - `test_summary_validates_against_schema` — loads `fixtures/summary_singletDM.json`, validates.
  - `test_required_fields_enforced` — removes `m_dm_gev`; validator rejects.
  - `test_negative_sigma_rejected` — σ_SI = -1 rejected.
- `test_scattering_schema_self.py`
  - `test_schema_is_valid_draft_2020_12` — uses `jsonschema.Draft202012Validator.check_schema`.
- `test_blocker_shape.py`
  - `test_every_blocker_code_valid_schema` — iterate fixture blocker JSONs; validate each.
- `test_scan_determinism.py`
  - `test_scan_index_byte_identical_across_runs` — two invocations on same inputs produce identical CSV bytes.
- `test_beps_sensitivity.py`
  - `test_coannihilation_wall_detected` — stub `run_point` to return Ωh² differing 25% between Beps values; expect `RELIC_BEPS_SENSITIVE` recoverable.
- (Integration, gated on `HEPPH_RUN_NETWORK_TESTS=1`) `test_singletdm_golden.py` — full `/micromegas relic` + `/micromegas scatter` on singletDM; asserts Ωh²≈0.118±0.002 and σ_SI(p)≈1.1e-46 ±10%.

**Fixtures `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/micromegas/tests/fixtures/`:**

- `stdout_singletDM.txt` — captured micrOMEGAs stdout (trimmed, ~50 lines).
- `stdout_singletDM_nan.txt` — crafted variant with `Omega h^2 = nan`.
- `slha_singletDM.spc` — SPheno output for m_S=100 GeV, λ_hS=0.05 (generated once, committed).
- `ufo_singletDM/` — minimal UFO directory (particles.py, parameters.py, vertices.py stubs).
- `main_c/relic_singletDM.c`, `scatter_singletDM.c`, `annihilate_singletDM.c`, `indirect_singletDM.c` — golden generated drivers.
- `summary_singletDM.json` — golden summary for schema test.
- `blockers/*.json` — one file per blocker code above.
- `spec_singletDM.yaml` — spec driving the golden test.

Hard cap: 10 MB total. If a real UFO fixture exceeds, use a placeholder + `regenerate_fixture.py` pattern (like `/spheno-build`).

### 2.5 Repo-level edits

**`.claude-plugin/marketplace.json`** — append:
```
{
  "name": "constraints",
  "source": "./plugins/constraints",
  "description": "DM phenomenology constraints — relic density, direct/indirect detection, Higgs measurements",
  "version": "0.1.0",
  "tags": ["constraints", "dark-matter", "relic", "direct-detection", "micromegas"]
}
```

**`CLAUDE.md`** — insert table row after `Theory`:
```
| Constraints | `constraints` | DM relic/DD/ID and Higgs-signal constraints (micrOMEGAs, DDCalc, HiggsTools) |
```

---

## 3. Implementation sequence (step-by-step)

Each step is a commit candidate. Run test suite green before committing.

**Step 1 — Scaffold + marketplace registration.**
Create `plugins/constraints/.claude-plugin/plugin.json`, `plugins/constraints/README.md`, `plugins/hep-ph-toolkit/skills/_shared/` with symlinked `blocker.schema.json`. Append marketplace.json entry + CLAUDE.md row. Validate: `python -m json.tool .claude-plugin/marketplace.json && python -m json.tool plugins/constraints/.claude-plugin/plugin.json`. Commit: `W-constraints-mO: scaffold constraints plugin skeleton`.

**Step 2 — Shared scattering schema.**
Create `plugins/shared/schemas/scattering.schema.json` + first-use test `test_scattering_schema_self.py` (self-validity + one positive + one negative fixture). Commit: `W-constraints-mO: add scattering.schema.json shared contract`.

**Step 3 — `/micromegas-install` detect + use-path.**
Implement `install_micromegas.sh` dispatcher, `detect.sh`, `use_path.sh`, `_blocker.sh`, `_macos_env.sh`. Unit tests: `test_detect_states.sh`, `test_use_path_validation.py`, `test_macos_env.sh`, `test_blocker_schema_valid.py`. Commit: `W-constraints-mO: /micromegas-install detect + use-path`.

**Step 4 — `/micromegas-install` install subcommand.**
Implement `install_impl.sh`, `_smoke.sh`. Add `test_no_network_policy.py` (unit, mocked). Add integration `test_install_offline.sh` gated on `HEPPH_RUN_NETWORK_TESTS=1`. Commit: `W-constraints-mO: /micromegas-install bundled install + HEPPH_NO_NETWORK`.

**Step 5 — SKILL.md for `/micromegas-install`.**
Write full SKILL.md in spheno-build voice. Commit: `W-constraints-mO: /micromegas-install SKILL.md`.

**Step 6 — DM candidate resolver + SLHA parser.**
Implement `resolve_dm_candidate.py`, `parse_slha_mass_block.py`. All 5 resolver tests + SLHA fixture tests pass. Commit: `W-constraints-mO: DM candidate resolution + SLHA mass parser`.

**Step 7 — main.c templates + golden bytes.**
Implement `main_c_template.py`, commit 4 golden `.c` fixtures, 4 byte-identical tests pass. Commit: `W-constraints-mO: main.c template + goldens`.

**Step 8 — Output parser + summary writer.**
Implement `parse_micromegas_out.py`, `write_summary.py`, `render_report.py`. All parser + summary-schema tests pass. Commit: `W-constraints-mO: parse stdout + summary writer`.

**Step 9 — UFO→CalcHEP + project build.**
Implement `ufo_to_calchep.sh`, `build_project.sh` with cache-key logic. Unit tests: fake-make + cache-hit + version-skew blocker. Commit: `W-constraints-mO: UFO→CalcHEP conversion + project cache`.

**Step 10 — Run point + Beps sensitivity + recoverable handling.**
Implement `run_point.py` with double-run Beps probe. `test_beps_sensitivity.py` green. Commit: `W-constraints-mO: single-point run + Beps coannihilation probe`.

**Step 11 — Scan mode + determinism.**
Implement `scan.py` mirroring `/spheno-build/scan.py`. `test_scan_determinism.py` green. Commit: `W-constraints-mO: scan mode + deterministic index`.

**Step 12 — SKILL.md for `/micromegas`.**
Write full SKILL.md. Final integration test `test_singletdm_golden.py` authored (gated). Regenerate fixture script committed. Commit: `W-constraints-mO: /micromegas SKILL.md + golden integration test`.

Target: 12 atomic, independently reviewable commits.

---

## 4. Test plan

**Unit tests (always on, no network):**
- `test_scattering_schema_self.py`
- `test_detect_states.sh`
- `test_use_path_validation.py`
- `test_macos_env.sh` (Darwin only)
- `test_blocker_schema_valid.py`
- `test_no_network_policy.py`
- `test_resolve_dm_candidate.py` (5 functions)
- `test_parse_slha_mass_block.py`
- `test_main_c_template.py` (5 functions including seed pin)
- `test_parse_micromegas_out.py` (3 functions)
- `test_summary_schema.py` (3 functions)
- `test_blocker_shape.py`
- `test_scan_determinism.py`
- `test_beps_sensitivity.py` (mocked run_point)

**Integration tests (gated on `HEPPH_RUN_NETWORK_TESTS=1`):**
- `test_install_offline.sh` — offline rebuild from cached tarball.
- `test_install_online.sh` — full download + build on Linux and macOS.
- `test_ufo_conversion.py` — SARAH-emitted singletDM UFO → CalcHEP project.
- `test_singletdm_golden.py` — end-to-end relic + scatter, asserting Ωh²≈0.118±0.002 and σ_SI(p)≈1.1e-46±10%.

**Golden fixture (single benchmark):**
- Model: Singlet-scalar DM.
- Inputs: `m_S = 100 GeV`, `λ_hS = 0.05`, SHM halo, default form factors, standard thermal cosmology, seed 42.
- Expected: Ωh² = 0.118 ± 0.002; σ_SI(p) ≈ 1.1e-46 cm² ±10%.
- Invocation: `/micromegas relic singletDM` then `/micromegas scatter singletDM`, both against the committed `slha_singletDM.spc`.

**CI:** not touched in v1. Follow existing precedent — tests default to the unit tier; `HEPPH_RUN_NETWORK_TESTS=1` opts into the integration tier locally.

---

## 5. Verification checklist

Before declaring done, implementer runs (absolute paths assumed from repo root):

- `python -m json.tool .claude-plugin/marketplace.json`
- `python -m json.tool plugins/constraints/.claude-plugin/plugin.json`
- `python -m json.tool plugins/shared/schemas/scattering.schema.json`
- `python -c "import jsonschema, json; jsonschema.Draft202012Validator.check_schema(json.load(open('plugins/shared/schemas/scattering.schema.json')))"`
- `pytest plugins/hep-ph-toolkit/skills/micromegas-install/tests/ -v`
- `pytest plugins/hep-ph-toolkit/skills/micromegas/tests/ -v`
- `bash plugins/hep-ph-toolkit/skills/micromegas-install/tests/test_detect_states.sh`
- `bash plugins/hep-ph-toolkit/skills/micromegas-install/scripts/install_micromegas.sh detect` (returns `missing` on clean env; exit 0)
- `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json && readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` (symlink exists)
- `grep -c '"name": "constraints"' .claude-plugin/marketplace.json` ≥ 1
- `grep -c "Constraints" CLAUDE.md` ≥ 1
- `git diff main --stat` — sanity check which files changed.

Integration gate (optional):
- `HEPPH_RUN_NETWORK_TESTS=1 pytest plugins/hep-ph-toolkit/skills/micromegas/tests/test_singletdm_golden.py -v`

---

## 6. Out of scope for v1

Explicitly NOT implemented (per final.md §4):

- NREFT operator-basis σ (Anand–Fitzpatrick–Haxton). v1.1.
- Asymmetric DM / two-component `darkOmega2`. v1 refuses with `MULTICOMPONENT_UNSUPPORTED`.
- Loop-level σ_SI (blind-spot paper Eqs. 9, 14, 23). Owned by Phase B `/looptools`.
- Non-standard cosmologies (early matter domination, entropy injection).
- `/micromegas all` composite subcommand. Orchestrator composes.
- `reference_only` fallback / `--allow-analytic-fallback` — deleted by manager rule.
- Concurrent scan parallelism (serial only in v1).
- micrOMEGAs 6.1.x (UFO2) — re-pin is a v1.1 ticket contingent on W3 emitting UFO 2.0.
- Halo presets beyond SHM; form-factor presets beyond `default` and `A1`.
- Collier backend wiring, Collier-based loop integrals.
- Relocating `blocker.schema.json` under `plugins/shared/schemas/` (proposed but not blocking).
- CI config changes.

---

## 7. Critical constraints reminder for implementer

- **Worktree isolation** — branch `workstream-constraints-micromegas`; never edit `main` directly. Use `/using-git-worktrees` skill.
- **No tool installs during unit tests** — every network/download/make call must be mocked or stubbed in the unit tier. Only the `HEPPH_RUN_NETWORK_TESTS=1` tier may touch real tools.
- **Blocker JSON discipline** — every emitted blocker must validate against `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. Use `_blocker.sh` helper; include `test_blocker_shape.py` for every new code.
- **`reference_only` forbidden** in this skill even though the schema allows it — per manager rule.
- **Style** — SKILL.md voice matches `/spheno-build/SKILL.md` (imperative, table-heavy, minimal prose, uppercase blocker codes, reference-style linkage section at bottom).
- **Commit messages** — follow `W<n>: <verb> <subject>` convention observed in `git log`. Prefix used here: `W-constraints-mO: ...`. Keep bodies concise; no Co-Authored-By unless asked.
- **Idempotent scaffold** — every scaffold step must detect prior sibling-workstream artefacts and pick up rather than overwrite; record what was pre-existing in the commit body.
- **Seed pin** — `HEPPH_MICROMEGAS_SEED=42` baked into every generated `main.c` and echoed into `summary.json.source_run`.
- **macOS SDK** — `SDKROOT=$(xcrun --show-sdk-path)` before make; `FFLAGS=-ff2c`, `LDFLAGS=-Wl,-ld_classic` when Homebrew gfortran detected; `DYLD_LIBRARY_PATH` only for smoke test, never written to user shell.
- **Cache key** — `sha256(ufo_dir_tar) || micromegas_version || ufo_dialect` for UFO→CalcHEP; mismatch → `CALCHEP_CONVERTER_VERSION_SKEW`.
- **Serial scans only** — per-run project dir under `micromegas_runs/<TS>/project/`; top-level cache read-only across runs.

End of plan.
