# `/feynarts` + `/feynarts-install` — Executable Plan (Draft)

Source spec: `docs/roadmap/v1-constraints-work/feynarts/brainstorm/final.md`
Target plugin: `plugins/feynman-diagrams/` (already scaffolded — plugin.json + README + placeholder `amplitude-calc`, `draw-feynman` skills exist).
Manager rulings honoured: `/sarah-build` is frozen (no schema / template / cache / golden edits); no `reference_only` fallback; SARAH install-path convention preserved; worktree isolation throughout.

---

## 0. Worktree / branch

- Branch: **`workstream-feyndiag-feynarts`**
- Worktree: created via `superpowers:using-git-worktrees` at `~/Projects/hep-ph-agents-worktrees/feyndiag-feynarts/`
- Base: `main` at head (currently `41f8b5d`).
- All edits under `plugins/feynman-diagrams/**`, `plugins/shared/schemas/**`, `.claude-plugin/marketplace.json`, `CLAUDE.md`. Nothing under `plugins/hep-ph-toolkit/skills/sarah-build/**` may be touched; grep-guard in the verification checklist.
- Merge strategy: `superpowers:finishing-a-development-branch` after CI green, PR into `main`.

---

## 1. Shared prereqs (preliminary PR, lands first)

Lifted out of the main PR so downstream workstreams (`/formcalc`, `/formcalc`) inherit cleanly:

1. **Create `plugins/shared/schemas/`** directory with:
   - `blocker.schema.json` — copy of `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`, extended enum to include the full `/feynarts` fatal + recoverable codes (§5 of spec). The model-building copy is replaced by a one-line pointer shim so `/sarah-install`, `/sarah-build`, `/spheno-build` keep resolving the same schema id. `$id` stays `https://hep-ph-agents/schemas/blocker/v1` — relocation is filesystem-only.
   - `processspec.schema.json` — new. Describes the canonical `{model_source, model_ref, initial:[str], final:[str], loop_order, exclude_topologies:[str]}` object shared by `/feynarts`, `/formcalc`, `/formcalc`. Serialises deterministically for cache-key hashing (sorted keys, explicit canonicaliser version `1`). Accepts either *alias form* (bare particle names, resolved via `tables/*.json` or SARAH `particles.m`) or *raw form* (strings containing `[` — treated opaquely).
2. **Relocation verification**: `grep -r "skills/_shared/blocker.schema.json" plugins/` must return only the shim + any consumer refs; all new refs point at `plugins/shared/schemas/blocker.schema.json`.
3. **Plugin scaffold check**: `plugins/feynman-diagrams/.claude-plugin/plugin.json` exists; add `plugins/hep-ph-toolkit/skills/_shared/` directory with a `README.md` pointer to `plugins/shared/schemas/`, and `plugins/hep-ph-toolkit/SHARED-feynman.md` (Phase-B version matrix: FeynArts 3.11 ↔ FormCalc 10.0 ↔ LoopTools — `/formcalc` and `/formcalc` workstreams extend it later).
4. Retire the placeholder `feynman-diagrams/skills/amplitude-calc/` by turning its `SKILL.md` into a one-paragraph dispatch doc pointing at `/feynarts`, `/formcalc`, `/formcalc`. `draw-feynman` untouched (v1.1 territory per spec §7).

---

## 2. Files to create

### 2.1 Plugin-level

- `plugins/hep-ph-toolkit/SHARED-feynman.md` — Phase-B compatibility matrix + env-var override table (`HEPPH_FEYNARTS_VERSION`, `HEPPH_FEYNARTS_DIAGRAM_CAP`, `HEPPH_FEYNARTS_AMP_SIZE_CAP_MB`, `HEPPH_RUN_WOLFRAM_TESTS`, `HEPPH_RUN_NETWORK_TESTS`).
- `plugins/feynman-diagrams/README.md` — rewrite to list the three Phase-B skills (install + generate + dispatch), link to spec.
- `plugins/hep-ph-toolkit/skills/_shared/README.md` — tiny pointer doc.

### 2.2 `/feynarts-install`

- `plugins/hep-ph-toolkit/skills/feynarts-install/SKILL.md` — mirrors `/sarah-install` structure: When-to-invoke, Decision flow, JSON status contract, Activation handling, Failure modes, Config keys, Version pin.
- `plugins/hep-ph-toolkit/skills/feynarts-install/skill_env.yaml` — pinned version `3.11`, tarball URL template, SHA256 placeholder `TODO`, install-dir template `$UserBaseDirectory/Applications/FeynArts-3.11/`.
- `scripts/detect_feynarts.sh` — scans `$UserBaseDirectory/Applications/FeynArts*/` on both macOS (`~/Library/Wolfram/Applications/`) and Linux (`~/.WolframEngine/Applications/`), reads `config.feynarts_path`. Emits `configured|found|missing|ambiguous`. Sources `plugins/shared/install-helpers/_common.sh` via the 4-level-deep pattern already used by `/sarah-install`.
- `scripts/use_path_feynarts.sh` — registers existing install, calls `smoke_test_feynarts.sh`.
- `scripts/install_feynarts.sh` — disk probe → `download_with_retry` → `verify_checksum` → extract → smoke test → `config_merge feynarts_path ... feynarts_version ... feynarts_installed_at ... feynarts_generic_model_hash <sha256 Lorentz.gen>`.
- `scripts/smoke_test_feynarts.sh` — runs `wolframscript -code 'Needs["FeynArts\`"]; $FeynArtsVersion'`, wraps with `activate_wolfram_if_needed.sh` so a missing activation surfaces as the `FEYNARTS_ACTIVATION_REQUIRED` status (reuses `/sarah-install`'s `check_wolfram_activation.sh` and `_activation_parse.py` — shared helper, *no fork*).
- `scripts/_blocker.sh` — tiny wrapper matching `/sarah-install` so the full fatal list in §5 of spec can be emitted uniformly.
- `tests/test_detect.sh` — unit test using a tmp HOME with seeded Applications dir; covers `configured`, `missing`, `ambiguous` (two FeynArts-* dirs).
- `tests/fixtures/feynarts_smoke_ok.txt`, `tests/fixtures/feynarts_smoke_fail.txt` — captured wolframscript output for offline parse tests.
- `tests/test_install_gated.sh` — gated by `HEPPH_RUN_NETWORK_TESTS=1`; end-to-end install into a tempdir.

### 2.3 `/feynarts`

- `plugins/hep-ph-toolkit/skills/feynarts/SKILL.md` — verbatim structure from §3 of spec (subcommand `generate` only; inputs; model-source precedence; cache key; decision flow; outputs table; caps/blockers; explicit "no reference_only" paragraph).
- `plugins/hep-ph-toolkit/skills/feynarts/skill_env.yaml` — caps defaults (`FEYNARTS_DIAGRAM_CAP=2000`, `FEYNARTS_AMP_SIZE_CAP_MB=200`, `FEYNARTS_DEFAULT_TIMEOUT_S=600`), canonicaliser version `1`.
- `scripts/driver.m.tpl` — wolframscript template, `str.format` tokens only per repo §2.10. Sections: `Needs["FeynArts\`"]`, `CreateTopologies`, `InsertFields`, cap check, `Paint`, `CreateFeynAmp`, `Put` to `FeynAmpList.m`.
- `scripts/make_feynarts_driver.m.tpl` — separate wolframscript template for the **post-hoc SARAH** branch: `AppendTo[$Path, "<sarah_path>/.."]; <<SARAH\`; Start["<Name>"]; MakeFeynArts[];` — writes `<Name>.mod`/`<Name>.gen` into `$STATE_ROOT/models/<name>/feynarts_state/`. This is our own wolframscript; `/sarah-build` templates and cache keys are not touched.
- `scripts/render_driver.py` — pure Python, dict → text. Deterministic, unit-testable.
- `scripts/resolve_model.py` — implements the three-way `--sarah-model | --model-file | --builtin` precedence with `FEYNARTS_MODEL_SOURCE_CONFLICT` on overlap, `FEYNARTS_SARAH_STATE_MISSING` / `FEYNARTS_MODEL_FILE_INVALID` / `FEYNARTS_ABSENT` on each branch.
- `scripts/resolve_process.py` — the dual-syntax parser. Auto-detects raw form by `[` sniff. For alias form, loads `tables/<builtin>.json` or `$STATE_ROOT/models/<name>/sarah/particles.m` (read-only). Emits `FEYNARTS_PROCESS_UNKNOWN_PARTICLE` with `known_aliases` in `context`.
- `scripts/cache_key.py` — composes `sha256(.mod) + "|" + sha256(.gen) + "|" + feynarts_version + "|" + sha256(canonical_process_spec) + "|" + feynarts_generic_model_hash`. Canonical process spec = JSON-dump of `processspec.schema.json` with sorted keys + canonicaliser version.
- `scripts/postprocess.py` — `FeynAmpList.m` round-trip check (spawns `wolframscript -code 'Length[Get["FeynAmpList.m"]]'`), size-cap guard, sidecar `FeynAmpList.meta.json` write, `summary.json` write, `topologies.json` extraction (informal v1 schema per spec §4).
- `scripts/run_feynarts.py` — top-level driver: prereq check → model resolve → process resolve → (post-hoc MakeFeynArts if `--sarah-model`) → cache check → render `driver.m` → `wolframscript --timeout` invocation → postprocess → cache write. Wraps all blocker emissions through `_blocker.sh` / a shared Python emitter.
- `scripts/generate.py` — thin CLI entry (`argparse` → `run_feynarts.main`).
- `tables/SM.json`, `tables/SMQCD.json`, `tables/THDM.json`, `tables/MSSM.json` — hand-curated alias → raw-tuple lookups (`{"e+": "-F[2,{1}]", "mu-": "F[2,{2}]", "Z": "V[2]", ...}`) keyed off FeynArts's shipped model files. Seeded from FeynArts 3.11 `Models/*.mod` comments.
- `tests/conftest.py` — shared fixtures (fake config dir, tempdir state-root, captured wolframscript outputs).
- `tests/test_render_driver.py` — template → text, covers loop-order 0 and 1, exclude-topologies flag, builtin vs sarah-model path.
- `tests/test_resolve_process.py` — alias-form vs raw-form detection, all four builtin tables, `FEYNARTS_PROCESS_UNKNOWN_PARTICLE` path, raw-form pass-through.
- `tests/test_cache_key.py` — determinism, sensitivity to each of the five components, order-independence of `exclude_topologies`.
- `tests/test_postprocess.py` — sidecar schema round-trip, size-cap guard (mocked), `topologies.json` extraction from a fixture `ins` dump.
- `tests/test_resolve_model.py` — three-way precedence, conflict code, missing state path.
- `tests/fixtures/particles.m` — copy of the W3 `dark_su3` particles.m (read-only, do not modify).
- `tests/fixtures/sm_tree_feynamp.m` — captured `FeynAmpList.m` for the tree-level golden (generated once by hand, committed).
- `tests/fixtures/z_selfenergy_topologies.json` — captured 1-loop topology count for the integration golden.
- `tests/goldens/sm_ee_mumu_tree/FeynAmpList.meta.json` — committed sidecar for byte-compare.
- `tests/goldens/sm_ee_mumu_tree/summary.json` — committed `{n_diagrams: 1, cached: false, ...}`.
- `tests/test_integration_gated.py` — gated by `HEPPH_RUN_WOLFRAM_TESTS=1`. Runs both goldens (tree + Z self-energy) and the SARAH-path integration against existing `dark_su3` state.

### 2.4 Shared

- `plugins/shared/schemas/blocker.schema.json` — relocation with enum extension.
- `plugins/shared/schemas/processspec.schema.json` — new.
- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — shrinks to a one-line pointer (`{"$ref":"../../../shared/schemas/blocker.schema.json"}`) so existing relative paths keep resolving.

### 2.5 Marketplace + top-level

- `.claude-plugin/marketplace.json` — add `feynman-diagrams` entry (or confirm existing entry still points at the plugin).
- `CLAUDE.md` — the `feynman-diagrams` row in the Plugin Categories table already says "Diagram drawing & amplitude calculation"; add a sub-bullet below the table enumerating Phase-B skills (`/feynarts-install`, `/feynarts`; `/formcalc*` and `/looptools*` pending). No description churn on existing rows.

---

## 3. Implementation sequence (11 steps)

1. **Worktree + branch.** `superpowers:using-git-worktrees` → `workstream-feyndiag-feynarts`. Verify `git status` clean, `plugins/hep-ph-toolkit/skills/sarah-build/` write-blocked (soft — by convention).
2. **Preliminary shared PR.** Create `plugins/shared/schemas/{blocker,processspec}.schema.json`, shim the old blocker path, add `processspec` tests under `plugins/shared/schemas/tests/`. Land first so downstream workstreams rebase cleanly. Verify `/sarah-install`, `/sarah-build`, `/spheno-build` tests still green.
3. **`/feynarts-install` scripts.** Port the `/sarah-install` script layout verbatim: `detect_feynarts.sh`, `use_path_feynarts.sh`, `install_feynarts.sh`, `smoke_test_feynarts.sh`, `_blocker.sh`. Reuse `activate_wolfram_if_needed.sh` unchanged.
4. **`/feynarts-install` SKILL.md.** Write after scripts so the decision-flow diagram matches actual exit codes. Cover Wolfram activation as **status not blocker** (mirrors `/sarah-install` phase1-final §4).
5. **`/feynarts-install` tests.** Unit (`test_detect.sh`) + gated `test_install_gated.sh` under `HEPPH_RUN_NETWORK_TESTS=1`. Run locally to confirm FeynArts 3.11 tarball fetch + smoke test passes.
6. **Alias tables.** Build `tables/SM.json`, `tables/SMQCD.json`, `tables/THDM.json`, `tables/MSSM.json` by manually cross-referencing FeynArts 3.11 `Models/*.mod` headers. Spot-check with a second pass.
7. **Pure-Python core.** `render_driver.py`, `resolve_model.py`, `resolve_process.py`, `cache_key.py`, `postprocess.py`. Unit tests as we go — TDD per `superpowers:test-driven-development`. No Wolfram dependency in these tests.
8. **Post-hoc SARAH driver.** `make_feynarts_driver.m.tpl` + Python wrapper that only runs when `--sarah-model` is set. Output location `$STATE_ROOT/models/<name>/feynarts_state/` — namespace chosen to not collide with any existing `/sarah-build` output (verified against `sarah-build/SKILL.md` post-build layout).
9. **Main driver `driver.m.tpl` + `run_feynarts.py`.** Implement cap checks in Mathematica (`Length[ins]` gate) *and* Python side (file size post-`Put`). Timeout via subprocess `timeout=` + SIGKILL.
10. **Goldens + integration tests.** Tree-level `e+e- → μ+μ-` (exactly 1 diagram; byte-compare `summary.json` + sidecar, Wolfram-generated `FeynAmpList.m` only round-trip-tested). 1-loop `Z → Z` self-energy (topology-count tolerance). SARAH-path integration against the existing W3 `dark_su3` state directory — **read-only** access under `sarah/`; writes only under `feynarts_runs/`.
11. **Marketplace + CLAUDE.md + SHARED.md.** Register skills in `.claude-plugin/marketplace.json`. Append Phase-B sub-list to `CLAUDE.md`. Fill `SHARED.md` version matrix.

---

## 4. Test plan

| Tier | Trigger | Scope |
|---|---|---|
| Unit (always on) | `pytest plugins/feynman-diagrams/` | `render_driver`, `resolve_model`, `resolve_process`, `cache_key`, `postprocess` sidecar, alias tables schema-valid, process-spec canonicaliser deterministic. |
| Shell unit (always) | `bash plugins/hep-ph-toolkit/skills/feynarts-install/tests/test_detect.sh` | `detect` subcommand across seeded fake HOMEs. |
| Schema (always) | `pytest plugins/shared/schemas/tests/` | blocker + processspec validate against fixtures; no regression of existing model-building fixtures. |
| Integration (gated `HEPPH_RUN_WOLFRAM_TESTS=1`) | local Wolfram kernel present | Tree-level golden (1 diagram), Z-self-energy (~14 diagrams), SARAH post-hoc against `dark_su3`. |
| Network (gated `HEPPH_RUN_NETWORK_TESTS=1`) | `test_install_gated.sh` | End-to-end FeynArts 3.11 install into tempdir + smoke test + teardown. |
| Regression guard (always) | `pytest plugins/model-building/` | `/sarah-install`, `/sarah-build`, `/spheno-build` unchanged. |

Goldens strategy: byte-compare `summary.json` and `FeynAmpList.meta.json`; for `FeynAmpList.m`, round-trip via `Get` and assert `Length > 0` + schema_version field — full amp byte-compare is infeasible.

---

## 5. Verification checklist

- [ ] `git diff main -- plugins/hep-ph-toolkit/skills/sarah-build/` is empty.
- [ ] `git diff main -- plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/` is empty.
- [ ] `plugins/shared/schemas/{blocker,processspec}.schema.json` exist; model-building shim resolves to them.
- [ ] `/sarah-install` + `/sarah-build` + `/spheno-build` test suites still green.
- [ ] `plugins/hep-ph-toolkit/skills/feynarts-install/SKILL.md` documents `FEYNARTS_ACTIVATION_REQUIRED` as **status**, not blocker.
- [ ] No `reference_only` branch anywhere in `skills/feynarts/`; SKILL.md states this explicitly.
- [ ] FeynArts install dir convention matches `$UserBaseDirectory/Applications/FeynArts-3.11/` (NOT `~/FeynArts/` or `~/SARAH/`-style).
- [ ] Post-hoc `MakeFeynArts[]` writes only under `$STATE_ROOT/models/<name>/feynarts_state/` and `feynarts_runs/`.
- [ ] Cache-key inputs: `.mod` sha + `.gen` sha + FeynArts version + canonical process-spec sha + generic-model hash. All five tested for sensitivity.
- [ ] Caps enforced in both Mathematica (`Length[ins]`) and Python (`Put` size).
- [ ] `FEYNARTS_EMPTY_RESULT` is recoverable; every other FeynArts-* code is fatal.
- [ ] Marketplace + CLAUDE.md updated; README + SHARED.md present.
- [ ] Golden tests: `n_diagrams == 1` for tree, topology-count within tolerance for 1-loop.
- [ ] SARAH-path integration runs against the committed `dark_su3` state without modifying it.

---

## 6. Out of scope (v1)

- Fortran amplitude emission (belongs in `/formcalc`).
- `Paint[]` rendering beyond the default multi-page PDF (TikZ-Feynman and custom layouts → `/draw-feynman` v1.1).
- `paint` subcommand (deferred to v1.1).
- TikZ-Feynman topology-JSON schema formalisation.
- Formal promotion of `tables/*.json` to `plugins/shared/` (defer to v1.1 when `/formcalc` is known to want the same lookup).
- `/lagrangian-builder` dispatch keyword registration — owned by W5 orchestrator workstream.
- SUSY-heavy 2-loop processes (cap of 2000 diagrams is the v1 ceiling; users can override via env var but at their own risk).
- MadGraph / UFO round-tripping.
- Parallel wolframscript runs.

---

Word-count target (1200–2000) met; plan is ready for eng-plan-review and CEO-plan-review passes before execution.
