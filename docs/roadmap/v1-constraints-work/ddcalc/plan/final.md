# `/ddcalc` implementation plan (FINAL)

Synthesizer: plan-synthesizer agent
Date: 2026-04-19
Status: authoritative input to implementation
Supersedes: `plan/draft.md` + `plan/critique.md`
Spec: `brainstorm/final.md`
Co-owned cross-workstream contracts: Phase-0 prep commit (manager-owned).

Scope: deliver `/ddcalc-install` + `/ddcalc` inside `plugins/constraints/` as a
leaf consumer of `scattering.schema.json`. All draft items were retained except
where a critique finding overrides them; all five critique blockers plus both
majors and all minors are folded in.

---

## 0. Worktree, branch, Phase-0 prereq

- Branch: `workstream-constraints-ddcalc`. Invoke
  `/superpowers:using-git-worktrees` before creating.
- Worktree path: `../hep-ph-agents-ddcalc`. No edits on `main`, no edits
  outside the worktree.
- **Phase-0 is assumed landed** before this workstream's Step 0 runs. Phase-0
  authors (per the `/micromegas` plan, manager-owned):
  - `plugins/constraints/.claude-plugin/plugin.json` (manifest — this
    workstream adds `ddcalc-install` and `ddcalc` to its `skills` array in a
    small edit, nothing else)
  - `plugins/constraints/README.md`
  - `plugins/hep-ph-toolkit/skills/_shared/` symlink to
    `plugins/hep-ph-toolkit/skills/_shared/` (blocker schema)
  - `plugins/shared/schemas/scattering.schema.json` (CANONICAL — not
    re-authored here; field names consumed verbatim)
  - `.claude-plugin/marketplace.json` `constraints` row + `CLAUDE.md`
    category-table row
  - `plugins/shared/install-helpers/_common.sh` additions:
    `HEPPH_NO_NETWORK`, `HEPPH_OFFLINE_CACHE_DIR`, `EXIT_NO_CMAKE=26`,
    `EXIT_NO_PYBIND=27`, `EXIT_FORM_BUILD=28`, `EXIT_LOOPTOOLS_BUILD=29`,
    and `plugins/shared/install-helpers/check_macos_sdk.sh`
  - `plugins/shared/pvalue.py`
- If Phase-0 has not landed at branch-creation time, **halt**. This
  workstream does not stub any Phase-0 artefact — the draft's "create stubs
  with header comments" rule is withdrawn per critique §5.
- Rebase cadence: rebase on `main` on Phase-0 land; rebase again before PR
  open.

Canonical field names consumed from Phase-0's `scattering.schema.json`
(synthesizer RULING — this is the schema this plan targets):

```
schema_version: "scattering/v1"
m_dm_gev, sigma_si_proton_cm2, sigma_si_neutron_cm2,
sigma_sd_proton_cm2, sigma_sd_neutron_cm2
source: "micromegas"|"looptools", source_run
halo: { model, v0_km_per_s, vesc_km_per_s, rho0_gev_per_cm3 }
nucleon_form_factors: { preset: "default_2018"|"A1" }
```

The draft's unit-suffix inconsistency (`v0_kms` vs `v0_km_per_s`) is resolved
by adopting Phase-0's `*_km_per_s` / `*_gev_per_cm3` form verbatim, including
in `halo_used` output and `halo.py`. This fixes critique §5.

---

## 1. Files to create (`/ddcalc` only; Phase-0 files excluded)

Voice for every SKILL.md: `sarah-install` / `spheno-build` discipline — terse
header, `When to invoke`, decision flow, subcommands table, blockers table,
config-keys table, linkage section. No marketing.

### `/ddcalc-install`

- `plugins/hep-ph-toolkit/skills/ddcalc-install/SKILL.md`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/skill_env.yaml` — `HEPPH_DDCALC_VERSION=2.2.0`, real SHA256, primary+mirror URL list, `HEPPH_DDCALC_FETCH_DATE`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/install_ddcalc.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/detect_ddcalc.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/use_path.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/apply_overlay.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/_smoke_test.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/_probe_url.sh` — primary→mirror→archive.org chain; first 200 wins; records into `plan/verifications.md` at author time
- `plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/_blocker.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/patches/version_banner.patch` — iff Step 0 finds the stock binary only prints the copyright banner
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/manifest.yaml` — pinned upstream commit SHA, patch list, efficiency-table SHA256 list, `overlay_sha`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/patches/{LZ_WS2024,XENONnT_2023,PandaX_4T_2021}.patch` — stubs (body authored in the separate overlay-publication PR; plumbing merge-ready without them)
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/data/{LZ_WS2024,XENONnT_2023,PandaX_4T_2021}.eff` — stubs
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/LZ_WS2024.NOTICE`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/XENONnT_2023.NOTICE`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/PandaX_4T_2021.NOTICE`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/ATTRIBUTIONS.md`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_detect_config.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_offline_cache.sh`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_overlay_apply.py` — fake-upstream reject-file collection test
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_url_probe_chain.py`
- `plugins/hep-ph-toolkit/skills/ddcalc-install/tests/fixtures/ddcalc_example_banner.txt`

### `/ddcalc`

- `plugins/hep-ph-toolkit/skills/ddcalc/SKILL.md`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/run_ddcalc.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/ddcalc_driver.c` — small C shim linked against `libDDCalc.a`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/_parse_driver_stdout.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/validate_scattering.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/halo.py` — `*_km_per_s` / `*_gev_per_cm3` fields only
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/neutrino_fog.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/scan_summary.py` — flock-guarded, serial
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/exclude.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/scripts/render_report.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_ohare_2021.csv`
- `plugins/hep-ph-toolkit/skills/ddcalc/data/NOTICE` — O'Hare 2021 citation + licence + exact figure ref
- `plugins/hep-ph-toolkit/skills/ddcalc/overlays/README.md` — pointer into `ddcalc-install/overlays/`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_schema_validate.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_parse_driver_stdout.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_halo_echo.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_scan_summary_determinism.py`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_no_reference_fallback.py` — unit-level grep gate (critique §7)
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_integration_xenon1t_golden.py` — `HEPPH_RUN_NETWORK_TESTS=1` gated
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/test_integration_lz_ws2024_golden.py` — gated + skipped if overlay absent
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_micromegas_sample.json`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_looptools_sample.json`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/driver_stdout_xenon1t.txt`
- `plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/blocker_invalid_input.json`

Phase-0 plugin.json edit (small, part of this workstream's PR): add
`ddcalc-install` and `ddcalc` to the `skills` array.

---

## 2. Implementation sequence (13 atomic commits)

**Step 0 — Overlay feasibility verification (BLOCKING; no code commits).**
Clone `gitlab.com/ddcalc/ddcalc` at v2.2.0. Build locally on the dev host
under the SDK/LDFLAGS env of §0. Enumerate `src/experiments/` file tree.
Identify the experiment-registration mechanism: central dispatcher (table
editing required in every overlay patch) vs. drop-in module (new file only).
Record findings in
`docs/roadmap/v1-constraints-work/ddcalc/plan/verifications.md`
under `§overlay-feasibility`. Also record, in the same file:

- URL probe chain output (`_probe_url.sh` dry-run against primary + mirror +
  archive.org; critique §2)
- Tarball SHA256 via
  `curl -L "$HEPPH_DDCALC_URL" -o /tmp/ddcalc.tgz && shasum -a 256 /tmp/ddcalc.tgz`
  with explicit fetch date (critique §3)
- `DDCalc_exampleC` banner capture (for §7 of this plan / brainstorm Q3)
- `github.com/cajohare/NeutrinoFog` LICENSE via `curl` + pinned commit SHA
  + CSV path within repo (critique §6)
- Exact ν-floor curve used in 2506.19062 Fig. 6/7

**Decision gate.** If overlay registration is drop-in-module-compatible,
proceed with overlay-enabled v1 (steps 1–13 full). If it is central-dispatcher
or otherwise structurally fragile for `git apply --3way`, fall back to
**native-only v1**: step 7 becomes a no-op stub (manifest documents the
deferral), step 13 drops the LZ WS2024 assertion, and `/ddcalc run` emits
`status: "reference_only"` (per Phase-0 schema) when a user requests a
post-2022 experiment. Overlay work moves to v1.1 backlog. This matches
brainstorm §3's escape hatch.

**Commit 1 — Worktree + Phase-0 plumbing edit.** Create the branch. Add
`ddcalc-install` and `ddcalc` to the Phase-0 `plugin.json` `skills` array.
Nothing else.

**Commit 2 — `/ddcalc-install` detect + use-path + `_blocker.sh`.**
`detect_ddcalc.sh`, `use_path.sh`, `_blocker.sh`, `test_detect_config.sh`.
Unit-test with tmp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`.

**Commit 3 — `/ddcalc-install` install + smoke + env.**
`install_ddcalc.sh`, `skill_env.yaml` (real SHA256, URL probe chain,
fetch-date), `_smoke_test.sh`, `_probe_url.sh`. `check_disk 2 4` (critique
§8). `LDFLAGS="-Wl,-ld_classic"`, `SDKROOT="$(xcrun --show-sdk-path)"`,
`FFLAGS="-std=legacy -fallow-invalid-boz -O2"`,
`CFLAGS="-Wno-implicit-function-declaration"`. macOS-SDK check reuses
Phase-0's `check_macos_sdk.sh`.

**Commit 4 — Offline-cache + URL-probe tests.** `test_offline_cache.sh`
(`HEPPH_NO_NETWORK=1` + staged cached tarball → install succeeds);
`test_url_probe_chain.py` (mocks 404+200 sequence, asserts first-200-wins
and `ddcalc_upstream_url` config write).

**Commit 5 — SKILL.md for `/ddcalc-install`.** Blocker table
(`DDCALC_DOWNLOAD_FAILED`, `DDCALC_BUILD_FAILED`,
`DDCALC_SMOKE_TEST_FAILED`, `DDCALC_PATH_INVALID`,
`DDCALC_OVERLAY_APPLY_FAILED`, `DDCALC_UPSTREAM_UNREACHABLE`,
`DDCALC_MACOS_SDK_MISMATCH`, `GFORTRAN_ABSENT` reusing `EXIT_NO_GFORTRAN`,
`DDCALC_UPSTREAM_UNVERIFIED` planning-phase only). Config-keys table:
`ddcalc_path`, `ddcalc_version`, `ddcalc_installed_at`,
`ddcalc_experiment_set`, `ddcalc_experiment_overlay_sha`,
`ddcalc_upstream_url`, `ddcalc_upstream_commit`. `HEPPH_NO_NETWORK`
fail-closed behaviour documented.

**Commit 6 — Version-banner patch (iff Step 0 required).**
`patches/version_banner.patch` + installer wiring + fixture
`ddcalc_example_banner.txt`. Omitted if Step 0 showed the stock binary
already prints a parseable version line.

**Commit 7 — Overlay plumbing.** `apply_overlay.sh` + overlay
`manifest.yaml` (pinned upstream commit SHA; patch list; efficiency-table
SHA256 list; `overlay_sha`) + stub patch/efficiency files +
**three per-experiment NOTICE files** (`LZ_WS2024.NOTICE`,
`XENONnT_2023.NOTICE`, `PandaX_4T_2021.NOTICE`) + aggregate
`ATTRIBUTIONS.md`. `test_overlay_apply.py` against fake upstream clone
asserts `context.patch_reject_files` empty path + non-empty path both
trip the expected code. If Step 0 chose native-only v1, this commit is a
stub manifest + NOTICE with `deferred: v1.1`.

**Commit 8 — `/ddcalc` driver + parser.** `ddcalc_driver.c` (links
`libDDCalc.a`; loads native + overlay experiments; calls
`DDCalc_LogLikelihood` per experiment; emits structured stdout) +
`_parse_driver_stdout.py` + build/cache machinery under
`$STATE_ROOT/cache/ddcalc_driver/<sha>/driver` +
`test_parse_driver_stdout.py` using captured fixture.

**Commit 9 — `/ddcalc` CLI + schema + halo.** `run_ddcalc.py`,
`validate_scattering.py` (jsonschema against Phase-0 schema; tail of
error into `context`; emits `DDCALC_INPUT_INVALID`), `halo.py` (SHM
defaults `v0_km_per_s=238`, `vesc_km_per_s=544`, `rho0_gev_per_cm3=0.3`;
echoed byte-identical into `halo_used`). `test_schema_validate.py`,
`test_halo_echo.py`.

**Commit 10 — `scan-summary` + `exclude` + report.**
`scan_summary.py` (flock-guarded on `$STATE_ROOT/.locks/ddcalc`; serial;
byte-deterministic CSV), `exclude.py`, `render_report.py`.
`test_scan_summary_determinism.py` (golden CSV).

**Commit 11 — ν-floor + O'Hare vendoring.** Only if Step 0's licence
check produces MIT/CC0/CC-BY. `neutrino_fog.py` (default
`"ddcalc_builtin_2.2.0"`; opt-in `--nu-floor ohare_2021`), vendored CSV,
`data/NOTICE` citing PRL 127, 251802 (2021) + `cajohare/NeutrinoFog`
commit SHA + exact CSV path within that repo + LICENSE file verbatim.
If licence check fails, ship DDCalc built-in only; mark `--nu-floor
ohare_2021` deferred to v1.1 in the SKILL.md.

**Commit 12 — SKILL.md for `/ddcalc` + reference-fallback grep gate.**
SKILL.md with subcommand table (`run`, `exclude`, `scan-summary`) +
blocker table (`DDCALC_INPUT_INVALID`, `DDCALC_MASS_OUT_OF_RANGE`
recoverable, `DDCALC_DRIVER_FAILED`, `DDCALC_NREFT_NOT_SUPPORTED`,
`DDCALC_OVERLAY_MISSING`) + schema pointer to Phase-0 file +
`test_no_reference_fallback.py` (grep-as-unit-test for
`HEPPH_ALLOW_REFERENCE`, `DDCALC_REFERENCE_ONLY`, `reference_only`,
`allow-analytic-fallback`).

**Commit 13 — Integration goldens.** `test_integration_xenon1t_golden.py`
(σ_SI = 1e-46 cm², m_DM = 100 GeV → XENON1T 2018
`excluded_90cl=true`, `p_value < 1e-3`, ±10 % on logL) gated on
`HEPPH_RUN_NETWORK_TESTS=1`. `test_integration_lz_ws2024_golden.py`
(same σ/m, asserts LZ WS2024 `excluded_90cl=true`,
`p_value < 1e-6`); skipped when no overlay is configured or when Step 0
selected native-only v1. Schema round-trip fixture
(`sigma_micromegas_sample.json` + `sigma_looptools_sample.json` both
produce byte-identical `verdict`).

---

## 3. Test plan

**Unit (always, `pytest` + `bash`; no env gates):**

- Schema validation: happy path, missing required key, `nreft_coefficients`
  rejection, isospin-violating input, halo fields in
  `*_km_per_s`/`*_gev_per_cm3` form.
- `_parse_driver_stdout.py` against captured stdout fixtures
  (`driver_stdout_xenon1t.txt`).
- Halo override: SHM default echoes byte-identical in `halo_used`; custom
  halo round-trips.
- Blocker output: every blocker validates against
  `blocker.schema.json`.
- Output conforms to `ddcalc_result/v1`.
- Scan-summary byte-identical CSV on fixed input index.
- Overlay `apply_overlay.sh` against fake upstream: happy (no rejects) +
  reject path (`context.patch_reject_files` populated).
- URL probe chain first-200-wins.
- `detect` / `use-path` with tmp `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME`.
- `test_no_reference_fallback.py` (grep gate).

**Integration (`HEPPH_RUN_NETWORK_TESTS=1` gated):**

- Real `/ddcalc-install install` on clean `$HOME`.
- Offline install via `HEPPH_NO_NETWORK=1` + staged cache.
- Native experiment list enumerated.
- `/ddcalc run` on `sigma_micromegas_sample.json` emits `result.json`.

**Golden (gated):**

- σ_SI_p = σ_SI_n = 1e-46 cm², σ_SD = 0, m_DM = 100 GeV → `verdict =
  "excluded"`, XENON1T 2018 `excluded_90cl = true`, `p_value < 1e-3`,
  tolerance ±10 % on logL (always).
- Same σ/m, LZ WS2024 `excluded_90cl = true`, `p_value < 1e-6`
  (overlay present only; skipped in native-only v1 fallback).

**Concurrency:** serial execution; flock on
`$STATE_ROOT/.locks/ddcalc` around any rebuild-dependent op (none in v1;
lock reserved + no-op-exercised).

---

## 4. Verification checklist (exact shell commands)

- [ ] `plan/verifications.md` contains: overlay-feasibility finding, URL
      probe output, SHA256, fetch-date, O'Hare LICENSE, CSV path.
- [ ] `curl -sI "$(python3 -c 'import yaml;print(yaml.safe_load(open("plugins/hep-ph-toolkit/skills/ddcalc-install/skill_env.yaml"))["HEPPH_DDCALC_URL"])')" | head -1 | grep -q '200'`
- [ ] `grep -Eq '^[a-f0-9]{64}$' <(python3 -c 'import yaml;print(yaml.safe_load(open("plugins/hep-ph-toolkit/skills/ddcalc-install/skill_env.yaml"))["HEPPH_DDCALC_SHA256"])')`
- [ ] `git grep -n "HEPPH_ALLOW_REFERENCE\|DDCALC_REFERENCE_ONLY\|reference_only\|allow-analytic-fallback" plugins/constraints/` returns empty.
- [ ] `pytest plugins/hep-ph-toolkit/skills/ddcalc/tests/test_no_reference_fallback.py` passes.
- [ ] `test -L plugins/hep-ph-toolkit/skills/_shared` (Phase-0 symlink exists).
- [ ] `python3 -c 'import json;json.load(open("plugins/shared/schemas/scattering.schema.json"))'` succeeds AND schema has `v0_km_per_s`, `vesc_km_per_s`, `rho0_gev_per_cm3`, `preset` fields exactly.
- [ ] `python3 -m jsonschema -i plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_micromegas_sample.json plugins/shared/schemas/scattering.schema.json` exits 0.
- [ ] `python3 -m jsonschema -i plugins/hep-ph-toolkit/skills/ddcalc/tests/fixtures/sigma_looptools_sample.json plugins/shared/schemas/scattering.schema.json` exits 0.
- [ ] `ls plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/{LZ_WS2024,XENONnT_2023,PandaX_4T_2021}.NOTICE` all present.
- [ ] `grep -l 'PRL' plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/lz_xenonnt_pandax4t_2024/*.NOTICE` returns all three.
- [ ] `pytest plugins/hep-ph-toolkit/skills/` passes with no env gates.
- [ ] `HEPPH_RUN_NETWORK_TESTS=1 pytest plugins/hep-ph-toolkit/skills/ddcalc/tests/test_integration_xenon1t_golden.py` passes.
- [ ] `HEPPH_RUN_NETWORK_TESTS=1 pytest plugins/hep-ph-toolkit/skills/ddcalc/tests/test_integration_lz_ws2024_golden.py` passes OR skips with `reason="native-only v1"`.
- [ ] `HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/cache bash plugins/hep-ph-toolkit/skills/ddcalc-install/tests/test_offline_cache.sh` passes.
- [ ] `jq -e '.skills | index("ddcalc-install") and index("ddcalc")' plugins/constraints/.claude-plugin/plugin.json` non-null.
- [ ] `report.md` renders for happy-path + blocker cases.

---

## 5. Out of scope for v1

Deferred to v1.1 or later:

- Halo marginalization (`marginalize-halo`, SHM++, Gaia-sausage,
  `--halo-uncertainty`). v1 always uses SHM (238, 544, 0.3) and echoes it.
- NREFT / Anand–Fitzpatrick–Haxton operator basis. Schema's
  `nreft_coefficients` key (when Phase-0 reserves it) is a fatal
  `DDCALC_NREFT_NOT_SUPPORTED` in v1.
- Non-default nucleon form factors beyond the Phase-0 `preset` enum.
- Sub-GeV DM / Migdal. `DDCALC_MASS_OUT_OF_RANGE` recoverable;
  `context.suggested_tool = "DarkELF"`.
- Loop-level σ (Phase B `/formcalc`). `/ddcalc` is a leaf consumer; never
  auto-selects between `micromegas` and `looptools` sources.
- `marginalize-halo`, `debug-dump` subcommands. `debug-dump` folded into
  `run --debug`.
- Parallel scans. Serial matches `/spheno-build --scan`.
- Overlay hot-swap. Rejected by brainstorm §3; overlays are source-patch +
  recompile only.
- **Any analytic fallback.** `HEPPH_ALLOW_REFERENCE` and
  `DDCALC_REFERENCE_ONLY` are forbidden; grep-gate enforced by unit test.
- Overlays beyond `lz_xenonnt_pandax4t_2024`. Each new overlay = new
  manifest + pinned commit SHA + efficiency-table SHA list + per-experiment
  NOTICE, landed via a dedicated PR.
- If Step 0 triggers the native-only v1 fallback: overlay plumbing itself
  is deferred to v1.1; the skill ships with native experiments only and
  emits `reference_only` status when a user requests a post-2022
  experiment (no blocker — just a pointer to v1.1 overlay work).
- O'Hare 2021 ν-floor is v1.1 if Step 0's LICENSE check fails; DDCalc
  built-in remains the default regardless.

---

Word count: ~1920.
