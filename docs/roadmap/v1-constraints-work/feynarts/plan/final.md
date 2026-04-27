# `/feynarts` + `/feynarts-install` — Executable Plan (Final)

Source spec: `docs/roadmap/v1-constraints-work/feynarts/brainstorm/final.md`.
Critique consumed: `docs/roadmap/v1-constraints-work/feynarts/plan/critique.md`.
Manager overrides integrated in-line.

Target: `plugins/feynman-diagrams/`, extending the existing plugin with two
new skills (`/feynarts-install` and `/feynarts`) **alongside** the already-live
`amplitude-calc/` and `draw-feynman/` skills — neither is a placeholder and
neither is retired.

---

## 0. Worktree, branch, Phase-0 prereq

- Branch: **`workstream-feyndiag-feynarts`**, via
  `superpowers:using-git-worktrees` at
  `~/Projects/hep-ph-agents-worktrees/feyndiag-feynarts/`.
- Base: current `main` head (`41f8b5d`).
- Edits confined to `plugins/hep-ph-toolkit/skills/feynarts-install/**`,
  `plugins/hep-ph-toolkit/skills/feynarts/**`,
  `plugins/feynman-diagrams/.claude-plugin/plugin.json`,
  `plugins/feynman-diagrams/README.md`, `plugins/hep-ph-toolkit/SHARED-feynman.md`,
  and the symlink under `plugins/hep-ph-toolkit/skills/_shared/`. No edits
  under `plugins/hep-ph-toolkit/skills/**` or `plugins/shared/**`.
- Merge strategy: `superpowers:finishing-a-development-branch` once CI green.

**Phase-0 prereq (manager-owned, assumed landed before this workstream
starts).** Phase-0 is a separate PR that authors:

1. `plugins/shared/schemas/blocker.schema.json` — **symlinked** copy of
   `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. No relocation;
   the canonical schema stays in place to keep all 11 existing consumer refs
   working. Downstream plugins (including this one) point at the symlink.
2. `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — symlink to
   `../../../model-building/skills/_shared/blocker.schema.json`.
3. `plugins/shared/schemas/scattering.schema.json` — authored for Phase A's
   analytic-scattering workstream; `/feynarts` does not consume it, but the
   file exists.
4. **Canonical** `plugins/shared/schemas/processspec.schema.json` with the
   union schema that `/feynarts`, `/formcalc`, and `/formcalc` all consume:
   ```json
   {
     "schema_version": "processspec/v1",
     "particles": {
       "in":  [{"label": "e+",  "pdg": -11, "mass_symbol": "ME"}],
       "out": [{"label": "mu+", "pdg":  13, "mass_symbol": "MMU"}]
     },
     "loop_order": 0,
     "kinematic_limit": "general",
     "excludes": [],
     "mandelstam": {"s": "...", "t": "...", "u": "..."}
   }
   ```
   `/feynarts` writes the `particles`, `loop_order`, `kinematic_limit`,
   `excludes` fields. `mandelstam` is optional and populated by `/formcalc`
   downstream.
5. `plugins/shared/install-helpers/_common.sh` additions:
   `HEPPH_NO_NETWORK=1` offline-mode flag, new exit codes
   `EXIT_NO_MACOS_SDK=26`, `EXIT_FEYNARTS_PATH=27`,
   `EXIT_FEYNARTS_SMOKE=28`, `EXIT_FEYNARTS_AMBIGUOUS=29`, and a
   `check_macos_sdk.sh` helper.
6. `plugins/shared/install-helpers/wolfram/{detect_wolfram.sh,
   check_wolfram_activation.sh, _activation_parse.py}` — promoted from
   `sarah-install/scripts/` with thin backward-compat wrappers left in place
   so `/sarah-install` is untouched behaviourally. `/feynarts-install`
   consumes the promoted helpers via the shared path.
7. Marketplace + `CLAUDE.md` entries for `feynman-diagrams` confirmed
   present; `plugin.json` skills array confirmed to include `amplitude-calc`
   and `draw-feynman` already.

Verification before §2 begins: `readlink
plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` resolves;
`plugins/shared/schemas/processspec.schema.json` validates the example
above; `plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh`
is executable.

---

## 1. Files to create

### 1.1 `/feynarts-install`

| File | Purpose |
|---|---|
| `skills/feynarts-install/SKILL.md` | When-to-invoke, decision flow, JSON status contract, activation handling (status NOT blocker, mirroring `/sarah-install`), failure modes, config keys, version pin 3.11 |
| `skills/feynarts-install/skill_env.yaml` | `feynarts_version: 3.11`, tarball URL template, `sha256: TODO`, install dir `$UserBaseDirectory/Applications/FeynArts-3.11/` |
| `skills/feynarts-install/scripts/detect_feynarts.sh` | Scan `~/Library/Wolfram/Applications/` (macOS) + `~/.WolframEngine/Applications/` (Linux) + `config.feynarts_path`. Emits `configured\|found\|missing\|ambiguous` |
| `skills/feynarts-install/scripts/use_path_feynarts.sh` | Register existing install; run smoke test |
| `skills/feynarts-install/scripts/install_feynarts.sh` | Disk probe → `download_with_retry` → `verify_checksum` → extract → smoke → `config_merge feynarts_path feynarts_version feynarts_installed_at feynarts_generic_model_hash=sha256(Models/Lorentz.gen)` |
| `skills/feynarts-install/scripts/smoke_test_feynarts.sh` | `wolframscript -code 'Needs["FeynArts`"]; $FeynArtsVersion'`, wraps via the Phase-0 shared `check_wolfram_activation.sh` so missing activation becomes the `activation_required` status |
| `skills/feynarts-install/scripts/_blocker.sh` | Wrapper emitting blocker JSON conforming to the blocker schema, matching `/sarah-install`'s shape |
| `skills/feynarts-install/tests/test_detect.sh` | Unit test against tmp HOME with seeded Applications dirs; covers `configured`, `found`, `missing`, `ambiguous` |
| `skills/feynarts-install/tests/fixtures/feynarts_smoke_ok.txt` | Captured wolframscript stdout for offline parse |
| `skills/feynarts-install/tests/fixtures/feynarts_smoke_fail.txt` | Captured failure output |
| `skills/feynarts-install/tests/test_install_gated.sh` | End-to-end install to tempdir; gated by **`HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`** (both required; critique §8) |

All scripts source `plugins/shared/install-helpers/_common.sh` via the 4-level-deep pattern, and source `plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh` by absolute path derived from `$SCRIPT_DIR`.

### 1.2 `/feynarts`

| File | Purpose |
|---|---|
| `skills/feynarts/SKILL.md` | Single subcommand `generate`; inputs; model-source precedence; cache key; decision flow; outputs table; caps/blockers; "no reference_only" paragraph (explicitly) |
| `skills/feynarts/skill_env.yaml` | `FEYNARTS_DIAGRAM_CAP=2000`, `FEYNARTS_AMP_SIZE_CAP_MB=200`, `FEYNARTS_DEFAULT_TIMEOUT_S=600`, `canonicalizer_version=1`; annotated "chosen conservatively; will be raised in v1.1 if paper benchmarks need it" |
| `skills/feynarts/scripts/driver.m.tpl` | Main wolframscript template (see literal contents below) |
| `skills/feynarts/scripts/make_feynarts_driver.m.tpl` | Post-hoc SARAH `MakeFeynArts[]` template (literal contents below) |
| `skills/feynarts/scripts/render_driver.py` | Pure-Python dict → text renderer (`str.format` only) |
| `skills/feynarts/scripts/resolve_model.py` | Three-way precedence: `--sarah-model \| --model-file \| --builtin`; emits `FEYNARTS_MODEL_SOURCE_CONFLICT`, `FEYNARTS_SARAH_STATE_MISSING`, `FEYNARTS_MODEL_FILE_INVALID`, `FEYNARTS_ABSENT` |
| `skills/feynarts/scripts/resolve_process.py` | Dual-syntax parser: raw form auto-detected by `[` sniff; alias form uses `tables/<builtin>.json` or `$STATE_ROOT/models/<name>/sarah/particles.m` |
| `skills/feynarts/scripts/cache_key.py` | `sha256(.mod) \| sha256(.gen) \| feynarts_version \| sha256(canonical processspec JSON + loop_order + sorted excludes) \| feynarts_generic_model_hash` |
| `skills/feynarts/scripts/postprocess.py` | Round-trip `FeynAmpList.m` via `Get`; size-cap check; write `FeynAmpList.meta.json`, `summary.json`, `topologies.json` |
| `skills/feynarts/scripts/run_feynarts.py` | Top-level driver: prereqs → model resolve → process resolve → (optional post-hoc `MakeFeynArts[]`) → cache probe → render → wolframscript (with `timeout=`) → postprocess → cache write |
| `skills/feynarts/scripts/generate.py` | Thin `argparse` CLI wrapper |
| `skills/feynarts/tables/SM.json`, `SMQCD.json`, `THDM.json`, `MSSM.json` | Alias tables curated from each model's `M$ClassesDescription` entries (NOT file-header comments — critique §9) |
| `skills/feynarts/tests/conftest.py` | Shared pytest fixtures |
| `skills/feynarts/tests/test_render_driver.py` | Template → text; loop-order 0/1, excludes flag, builtin vs sarah paths |
| `skills/feynarts/tests/test_resolve_process.py` | Alias and raw form; all four builtin tables; unknown-particle path |
| `skills/feynarts/tests/test_cache_key.py` | Determinism + sensitivity to each of the five components |
| `skills/feynarts/tests/test_resolve_model.py` | Three-way precedence; conflict code; missing state |
| `skills/feynarts/tests/test_postprocess.py` | Sidecar schema; size-cap guard (mocked); `topologies.json` extraction |
| `skills/feynarts/tests/fixtures/sm_ee_mumu_FeynAmpList.m` | Tree-level golden |
| `skills/feynarts/tests/fixtures/z_selfenergy_topologies.json` | 1-loop topology count golden |
| `skills/feynarts/tests/goldens/sm_ee_mumu_tree/FeynAmpList.meta.json` | Committed sidecar for byte-compare |
| `skills/feynarts/tests/goldens/sm_ee_mumu_tree/summary.json` | Committed `{n_diagrams: 1, cached: false, ...}` |
| `skills/feynarts/tests/test_integration_gated.py` | `--builtin SM` integration, gated `HEPPH_RUN_WOLFRAM_TESTS=1` — **SARAH-independent** (critique §6) |

**No `dark_su3` SARAH-state fixture is committed and no SARAH-dependent
integration test is written in v1.** Integration goldens use FeynArts's
built-in SM, making them fully deterministic on any machine with a Wolfram
kernel and FeynArts 3.11. A SARAH-path integration test is deferred to v1.1.

### 1.3 Plugin-level

| File | Edit |
|---|---|
| `plugins/feynman-diagrams/.claude-plugin/plugin.json` | Append `"feynarts-install"` and `"feynarts"` to the skills array. **Do not remove** `"amplitude-calc"` or `"draw-feynman"` |
| `plugins/feynman-diagrams/README.md` | Add short section: Phase-B amplitude pipeline — `/feynarts-install`, `/feynarts`; existing `amplitude-calc` + `draw-feynman` docs untouched |
| `plugins/hep-ph-toolkit/SHARED-feynman.md` | New: version matrix (FeynArts 3.11 pinned; FormCalc 10.0 + LoopTools reserved for later workstreams); env-var overrides table; cross-plugin Wolfram helper reference |

### 1.4 Literal `driver.m.tpl` contents

```
Needs["FeynArts`"];
SetDirectory["{run_dir}"];
t   = CreateTopologies[{loop_order}, {n_in} -> {n_out}, ExcludeTopologies -> {{excludes_m}}];
ins = InsertFields[t, {process_tuple}, Model -> "{model_name}", GenericModel -> "Lorentz"];
nDiag = Length[ins];
If[nDiag == 0,
  Print["FEYNARTS_EMPTY_RESULT"]; Exit[0]];
If[nDiag > {diagram_cap},
  Print["FEYNARTS_TOO_MANY_DIAGRAMS ", nDiag]; Exit[2]];
Paint[ins, ColumnsXRows -> Automatic, DisplayFunction -> (Export["diagrams.pdf", #] &)];
amp = CreateFeynAmp[ins];
Put[{{"schema_version" -> 1, "feynarts_version" -> "{feynarts_version}",
     "model_hash" -> "{model_hash}", "amp" -> amp}}, "FeynAmpList.m"];
Print["FEYNARTS_OK ", nDiag];
Exit[0];
```

### 1.5 Literal `make_feynarts_driver.m.tpl` contents

```
SetDirectory["{feynarts_state_dir}"];
AppendTo[$Path, "{sarah_path}/.."];
Needs["SARAH`"];
Start["{model_name}"];
MakeFeynArts[];
Exit[0];
```

This is a complete, self-contained driver (manager override — not a stub).
`SetDirectory[...]` ensures `MakeFeynArts[]` writes
`<model_name>.mod`/`<model_name>.gen` into our owned
`$STATE_ROOT/models/<name>/feynarts_state/` namespace rather than a
SARAH-internal output dir.

---

## 2. Implementation sequence (13 atomic commits)

1. **C1 — Branch init.** Worktree + branch. Confirm Phase-0 landed: the
   four symlinks/files enumerated in §0 all resolve; `/sarah-install`,
   `/sarah-build`, `/spheno-build` test suites pass on tip of `main`.
2. **C2 — Install SKILL.md + skill_env.yaml.** Author the `feynarts-install`
   skill frame (no scripts yet); document the activation-as-status
   divergence and the `$UserBaseDirectory` convention.
3. **C3 — Install scripts.** `detect_feynarts.sh`, `use_path_feynarts.sh`,
   `install_feynarts.sh`, `smoke_test_feynarts.sh`, `_blocker.sh`. All
   source shared helpers via absolute paths derived from `$SCRIPT_DIR`.
4. **C4 — Install unit tests.** `test_detect.sh` covers four branches
   against seeded tmp HOMEs. All always-on.
5. **C5 — Install gated test.** `test_install_gated.sh` gated by
   `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1` (both). Runs
   locally end-to-end; CI skips.
6. **C6 — `/feynarts` SKILL.md + skill_env.yaml.** Full text with outputs
   table, blocker list, explicit "no `reference_only`" paragraph,
   cap-override env vars, canonicalizer version.
7. **C7 — Alias tables.** `tables/SM.json`, `SMQCD.json`, `THDM.json`,
   `MSSM.json` curated from each model's `M$ClassesDescription`. Validate
   each entry against FeynArts 3.11 `Models/` with a local probe. Schema:
   `{"<alias>": "<feynarts-tuple-string>", ...}`.
8. **C8 — Pure-Python core.** `render_driver.py`, `resolve_model.py`,
   `resolve_process.py`, `cache_key.py`, `postprocess.py`. TDD per
   `superpowers:test-driven-development`. Unit tests land with each module.
9. **C9 — Driver templates.** `driver.m.tpl` (§1.4) and
   `make_feynarts_driver.m.tpl` (§1.5) committed verbatim. Add renderer
   unit test proving that format-substitution produces the exact expected
   text for the tree-level golden.
10. **C10 — Top-level driver.** `run_feynarts.py` + `generate.py`. Timeout
    enforced at the subprocess layer via Python `subprocess.run(timeout=…)`
    with SIGKILL on expiry; diagram cap checked inside Mathematica via
    `Length[ins] > {diagram_cap}`; amp-size cap checked in Python after
    `Put` via `os.stat`.
11. **C11 — Goldens.** `tests/goldens/sm_ee_mumu_tree/{summary.json,
    FeynAmpList.meta.json}` committed. Test asserts byte-equal sidecars
    and `Length[Get["FeynAmpList.m"]] > 0` round-trip (full amp
    byte-compare is infeasible). Z self-energy golden: topology count
    within ±1 of the committed integer.
12. **C12 — Integration tests gated.** `test_integration_gated.py` runs
    both SM goldens behind `HEPPH_RUN_WOLFRAM_TESTS=1`. No SARAH
    dependency.
13. **C13 — Plugin wiring.** `plugin.json` skills array append;
    `README.md` section; `SHARED.md` new file. Grep-guard commit:
    `git diff main -- plugins/hep-ph-toolkit/skills/amplitude-calc/` is
    empty and same for `draw-feynman/`.

---

## 3. Test plan

| Tier | Trigger | Scope |
|---|---|---|
| Python unit (always) | `pytest plugins/hep-ph-toolkit/skills/feynarts/tests/` | `render_driver`, `resolve_model`, `resolve_process`, `cache_key`, `postprocess` — no Wolfram, no network |
| Shell unit (always) | `bash plugins/hep-ph-toolkit/skills/feynarts-install/tests/test_detect.sh` | `detect` subcommand against tmp HOMEs |
| Schema (always) | Validate tables + processspec fixtures against `plugins/shared/schemas/processspec.schema.json` | Canonicaliser determinism (sort keys, sort `excludes`) |
| Wolfram integration (gated `HEPPH_RUN_WOLFRAM_TESTS=1`) | Local Wolfram kernel + FeynArts 3.11 | Tree golden (`e+e-→μ+μ-`, `--builtin SM`, `n_diagrams == 1` exactly); Z self-energy (`Z→Z`, `--builtin SM --loop-order 1`, topology count matches golden ±0) |
| Install end-to-end (gated `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`) | Local Wolfram + network | FeynArts 3.11 tarball fetch → extract → smoke → teardown |
| Regression (always) | `pytest plugins/model-building/ plugins/hep-ph-demo/` | `/sarah-install`, `/sarah-build`, `/spheno-build`, `/install` unchanged |

Golden assertion invariants:

- Tree (`sm_ee_mumu_tree`):
  - `summary.json.n_diagrams == 1`
  - `summary.json.process == {"in": ["e+","e-"], "out": ["mu+","mu-"]}`
  - `summary.json.loop_order == 0`
  - `summary.json.cached in (true, false)`
  - `FeynAmpList.meta.json.schema_version == 1`
  - `FeynAmpList.meta.json.feynarts_version == "3.11"`
  - `Length[Get["FeynAmpList.m"][[-1]][[2]]] >= 1` via wolframscript round-trip
- Z self-energy:
  - `summary.json.n_diagrams` matches the committed fixture integer (no
    tolerance — FeynArts is deterministic).

Cap assertions (mocked integration, `test_postprocess.py`):

- Diagram cap: fixture `Length[ins] = 2001` triggers
  `FEYNARTS_TOO_MANY_DIAGRAMS` fatal; blocker JSON has
  `context.diagram_count == 2001` and `context.cap == 2000`.
- Amp-size cap: fixture `FeynAmpList.m` of 201 MB triggers
  `FEYNARTS_AMP_TOO_LARGE` fatal; blocker has
  `context.amp_size_mb == 201` and `context.cap == 200`;
  `FeynAmpList.m` remains on disk for inspection; no cache key written.
- Timeout: subprocess mock expiring at 601 s triggers `FEYNARTS_TIMEOUT`
  fatal with `context.timeout_s == 600` and
  `context.wall_clock_s >= 600`.

---

## 4. Verification checklist

- [ ] `git diff main -- plugins/model-building/` is empty.
- [ ] `git diff main -- plugins/shared/` is empty (Phase-0 owns it).
- [ ] `git diff main -- plugins/hep-ph-toolkit/skills/amplitude-calc/` is empty.
- [ ] `git diff main -- plugins/hep-ph-toolkit/skills/draw-feynman/` is empty.
- [ ] `plugin.json` skills array contains all four: `amplitude-calc`,
      `draw-feynman`, `feynarts-install`, `feynarts`.
- [ ] `readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
      resolves to the canonical `plugins/hep-ph-toolkit/skills/_shared/` path.
- [ ] `/sarah-install` + `/sarah-build` + `/spheno-build` test suites green.
- [ ] `/feynarts-install` SKILL.md: `FEYNARTS_ACTIVATION_REQUIRED` listed as
      **status, not blocker** with JSON shape example.
- [ ] `/feynarts` SKILL.md: explicit paragraph stating "no `reference_only`
      fallback".
- [ ] Install dir convention: `$UserBaseDirectory/Applications/FeynArts-3.11/`
      (NOT `~/FeynArts/`, NOT SARAH-style `~/SARAH/...`).
- [ ] Post-hoc `MakeFeynArts[]` writes only under
      `$STATE_ROOT/models/<name>/feynarts_state/` (verified by integration
      fixture filename list once v1.1 re-enables SARAH-path).
- [ ] Cache-key inputs: `.mod` sha + `.gen` sha + FeynArts version +
      canonicalised processspec sha + `Lorentz.gen` hash. All five tested
      for sensitivity in `test_cache_key.py`.
- [ ] Caps enforced at both Mathematica (`Length[ins]`) and Python
      (`os.stat` on `FeynAmpList.m`) layers; timeout at subprocess layer.
- [ ] `FEYNARTS_EMPTY_RESULT` recoverable; every other `FEYNARTS_*` code
      fatal.
- [ ] `README.md` + `SHARED.md` reference the two new skills; marketplace
      entry (Phase-0 authored) untouched.
- [ ] Tree golden: `n_diagrams == 1`. Z self-energy golden: topology count
      exact match.
- [ ] Install integration test gated by **both** `HEPPH_RUN_WOLFRAM_TESTS=1`
      **and** `HEPPH_RUN_NETWORK_TESTS=1`.
- [ ] No SARAH-state fixture committed; no SARAH-path integration test
      runs in v1.
- [ ] `driver.m.tpl` and `make_feynarts_driver.m.tpl` match the literal
      contents in §1.4 / §1.5 byte-for-byte (modulo `str.format` tokens).

---

## 5. Out of scope v1

- Fortran amplitude emission — owned by `/formcalc` (Phase-B stage 2).
- `Paint[]` customisation, TikZ-Feynman hand-off, `paint` subcommand —
  deferred to v1.1 alongside `/draw-feynman` evolution.
- SARAH-path integration tests — deferred to v1.1 once a minimal SARAH
  state fixture is worth committing. v1 is `--builtin SM` only for
  goldens.
- `/lagrangian-builder` dispatch keyword registration — W5 orchestrator
  workstream.
- Formal promotion of `tables/*.json` to `plugins/shared/` — revisit when
  `/formcalc` needs the same lookup.
- SUSY 2-loop processes, `MakeLaTeX[]`, `MakeCalcHEP[]`, `MakeWHIZARD[]`.
- Parallel wolframscript runs.
- Raising cap defaults above `(2000, 200 MB, 600 s)` — defaults chosen
  conservatively; users override via env var at their own risk; v1.1
  revisits once paper benchmarks demand it.
- MadGraph / UFO round-tripping for FeynArts models.
- `paint` sub-subcommand, multi-page layout customisation.
- Formalised `topologies.json` schema — v1 ships informally; formalised
  when `/draw-feynman` v1.1 lands and consumes it.

---

Plan obeys all manager rules: no schema relocations, no skill retirements,
Phase-0 helpers assumed landed, SARAH-independent goldens, literal
wolframscript contents, exact assertions for diagram count / amp size /
timeout, dual-gate for the install integration test. Ready for
`superpowers:executing-plans`.
