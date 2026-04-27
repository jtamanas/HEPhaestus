# `/feynarts` — Proposal (Proposer)

**Role:** First stage of Phase B (`/feynarts` → `/formcalc` → `/formcalc`). Consumes a SARAH-emitted FeynArts model file plus a process specification, emits diagram PDFs + a symbolic amplitude `.m` artifact for `/formcalc`.

---

## 0. Upstream reality check

Grep of `plugins/` for `FeynArts` / `MakeFeynArts`:

- `plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md §Non-goals (v1)` — explicitly lists `MakeFeynArts[]` as **not** emitted.
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md:277` — same non-goal.

So **SARAH does not yet emit FeynArts output** in our stack. This must be added, and the natural home is a small extension to `/sarah-build` (add `feynarts` to `outputs:`) rather than a separate converter. See §3 for the contract.

---

## 1. `/feynarts-install`

### Upstream + version pin

- URL: `https://feynarts.de/FeynArts-<VERSION>.tar.gz` (legacy archive; FeynArts is distributed as a tarball of Mathematica `.m` / Paclet-style sources, not a real Paclet yet).
- Pin: **FeynArts 3.11** (current stable, 2023). Override via `HEPPH_FEYNARTS_VERSION`.
- SHA256: `TODO` placeholder per `verify_checksum` convention in `plugins/shared/install-helpers/_common.sh`.

### Install location — three candidates + recommendation

| Candidate | Pro | Con |
|---|---|---|
| `$UserBaseDirectory/Applications/FeynArts` (Mathematica user apps dir) | Auto-discovered by `Needs["FeynArts`"]`; plays well with other Mathematica users on the host | Not sandboxed to this repo; cross-project contamination |
| `$STATE_ROOT/apps/FeynArts-3.11/` (repo-local, mirrors SARAH) | Matches `/sarah-install` pattern (explicit `$Path` append); reproducible | Must register `$Path` ourselves |
| `~/FeynArts/FeynArts-3.11/` (home-dir, mirrors SARAH default) | Consistent with `/sarah-install` default (`~/SARAH`) | Same as above |

**Recommendation:** mirror `/sarah-install` exactly — default install to `~/FeynArts/FeynArts-3.11/`, record absolute path in `config.feynarts_path`, register via `AppendTo[$Path, "<feynarts_path>/.."]` in every `wolframscript` invocation. This keeps the install-path convention homogeneous across all Mathematica skills (`/sarah-install`, `/feynarts-install`, `/formcalc-install`, `/formcalc-install`).

### Conflict with `/sarah-install`

`/sarah-install` does **not** install FeynArts today. SARAH ships with `MakeFeynArts[]` but that command only emits a model file; it does **not** bundle the FeynArts engine. So there is no collision — `/sarah-install` produces `.mod` files, `/feynarts-install` provides the runtime that consumes them.

### Subcommands (identical shape to `/sarah-install`)

- `/feynarts-install detect` — emits JSON `{"status":"configured"|"found"|"missing", ...}` on stdout.
- `/feynarts-install use-path <dir>` — register existing FeynArts directory; smoke test `Needs["FeynArts`"]; $FeynArtsVersion`.
- `/feynarts-install install [dir]` — download + extract + probe. Default `dir=~/FeynArts/FeynArts-3.11`.

### Config keys written

| Key | Value |
|---|---|
| `feynarts_path` | Absolute path to dir containing `FeynArts.m` |
| `feynarts_version` | e.g. `"3.11"` |
| `feynarts_installed_at` | UTC ISO 8601 |

Reads `wolfram_engine_path` (shared with SARAH).

### Failure modes → blockers

| Code | Mode | Trigger |
|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | fatal | `wolfram_engine_path` not set |
| `FEYNARTS_DOWNLOAD_FAILED` | fatal | `curl` failed twice |
| `FEYNARTS_SMOKE_TEST_FAILED` | fatal | `Needs["FeynArts`"]` returns `$Failed` |
| `FEYNARTS_PATH_INVALID` | fatal | `use-path <dir>` has no `FeynArts.m` |

All emitted to stderr per `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

---

## 2. `/feynarts` (the skill)

### Inputs

```
scripts/run_feynarts.py <model_name> \
    --process '{F[1],-F[1]} -> {V[1],V[1]}' \
    --loop-order 0|1 \
    [--exclude-particles V[3]] \
    [--topologies WFCorrections|SelfEnergies|All] \
    [--output-dir <dir>]
```

- `<model_name>` — existing model from `$STATE_ROOT/models/<name>/` (same canonical name used by `/sarah-build`).
- `--process` — FeynArts process spec string, passed through verbatim.
- `--loop-order` — 0 (tree) or 1 (one-loop). v1 caps at 1.

### Decision flow

```
1. Validate prereqs
     feynarts_path set?              else FEYNARTS_ABSENT (fatal)
     wolfram_engine_path set?         else WOLFRAM_KERNEL_ABSENT (fatal)
     $STATE_ROOT/models/<name>/feynarts/<Name>.mod exists?
                                      else FEYNARTS_MODEL_MISSING (fatal — prompts `/sarah-build --output feynarts`)
2. Cache check
     key = sha256(<Name>.mod bytes) + "=" + feynarts_version
           + "|" + sha256(process-spec-string + loop-order)
     stored at $STATE_ROOT/models/<name>/feynarts_runs/<hash>/.key
     hit → skip wolframscript, return {"status":"cached"}
3. Render FeynArts driver .m from templates/driver.m.tmpl
     inserts: model name, process tuple, loop order, output paths
4. Invoke wolframscript
     AppendTo[$Path, "<feynarts_path>/.."];
     Needs["FeynArts`"];
     t = CreateTopologies[<loop>, nIn -> nOut, ExcludeTopologies -> ...];
     ins = InsertFields[t, <process>, Model -> "<Name>", GenericModel -> "Lorentz"];
     Paint[ins, ColumnsXRows -> {4,4}, DisplayFunction -> (Export["diagrams.pdf", #]&)];
     amp = CreateFeynAmp[ins];
     Put[amp, "amplitude.m"];
5. Post-process
     Assert diagrams.pdf exists                    else FEYNARTS_PAINT_FAILED
     Assert amplitude.m parses as valid Mma expr   else FEYNARTS_AMP_INVALID
     Count diagrams (parse Length[ins]); log summary.
6. Write summary.json + cache key, update config.
```

### Outputs

```
$STATE_ROOT/models/<name>/feynarts_runs/<process-hash>/
├── driver.m                # rendered input
├── diagrams.pdf            # Paint[] output
├── amplitude.m             # Put[amp, ...] — consumed by /formcalc
├── feynarts.log            # wolframscript stdout+stderr
├── summary.json            # { n_topologies, n_diagrams, process, loop_order, ... }
└── .key                    # cache key
```

Config: `config.models[<name>].feynarts_runs[<process-hash>] = {path, amplitude, diagrams, built_at}`.

### Failure modes → blockers

| Code | Mode | Trigger |
|---|---|---|
| `FEYNARTS_ABSENT` | fatal | `feynarts_path` not in config |
| `FEYNARTS_MODEL_MISSING` | fatal | No `.mod` file for model — user must rerun `/sarah-build` with `outputs: [..., feynarts]` |
| `FEYNARTS_PROCESS_INVALID` | fatal | FeynArts log contains `InsertFields::nofields` or malformed process tuple |
| `FEYNARTS_PAINT_FAILED` | fatal | `Paint[]` threw or PDF not produced |
| `FEYNARTS_AMP_INVALID` | fatal | `amplitude.m` missing or fails `Get` round-trip |
| `FEYNARTS_EMPTY_RESULT` | recoverable | `Length[ins] == 0` (no diagrams; process kinematically absent from model). Scan-friendly: record and continue. |

---

## 3. Integration

### Upstream: extend `/sarah-build`

Add `feynarts` to the permitted `outputs:` list in `modelspec.schema.json`. In `run_sarah.py`, when `feynarts` is requested, append `MakeFeynArts[];` to the wolframscript program. SARAH emits `<Name>.mod` + `<Name>.gen` under `sarah_output/FeynArts/`; we symlink to `$STATE_ROOT/models/<name>/feynarts/`. Cache-key extension: include the output list so flipping it invalidates cache.

**Ownership decision:** FeynArts model **generation** (`.mod`/`.gen`) is owned by `/sarah-build` (SARAH is the model authority). FeynArts model **consumption** (CreateTopologies / InsertFields / Paint / CreateFeynAmp) is owned by `/feynarts`. Clean seam.

### Downstream: `/formcalc` contract

FormCalc ingests a FeynArts `FeynAmp`/`FeynAmpList` expression. The canonical handoff is `Get["amplitude.m"]` where the file contains the output of `CreateFeynAmp[ins]` (head `FeynAmpList`). `/formcalc` will `Needs["FormCalc`"]; amps = Get["amplitude.m"]; result = CalcFeynAmp[amps]`. So our emitted artifact is exactly what FormCalc expects — no format conversion.

### Phase-B orchestration

`/lagrangian-builder` already has the orchestrator scaffold. Add a Phase-B branch: when user asks for "one-loop amplitude" or similar, dispatch `/sarah-build --output feynarts` → `/feynarts` → `/formcalc` → `/formcalc`.

---

## 4. Plugin placement

**Recommendation: `plugins/model-building/`.**

Rationale:

- `/feynarts` operates on the symbolic-model layer (Lagrangian → diagrams → amplitudes), which is the same layer as `/sarah-build` and `/lagrangian-builder`. It is **not** a "constraint" (no experimental limit is being applied) — the constraint skills (`/micromegas`, `/ddcalc`, `/higgstools`) are SLHA/UFO consumers downstream of physics-observable computation.
- Data-locality: `/feynarts` reads `$STATE_ROOT/models/<name>/feynarts/` which is written by `/sarah-build`. Co-locating them simplifies path conventions and testing fixtures.
- `plugins/feynman-diagrams/` is tempting but that plugin is positioned for user-facing diagram drawing (TikZ-Feynman per `CLAUDE.md`), not for the FeynArts/FormCalc/LoopTools amplitude pipeline. Keep the pipeline clustered in `model-building`; if the diagram-drawing plugin wants to consume `/feynarts` output for rendering, it can do so via the state-root contract.
- Counter-argument (for the critic): as the Mathematica-stack pipeline grows (`/feynarts` + `/formcalc` + `/formcalc`), `plugins/model-building/` may become overloaded. A future `plugins/amplitude-tools/` split is reasonable. For v1, ship in `model-building`.

---

## 5. Open questions for the critic

1. **SARAH-side MakeFeynArts quirks.** SARAH's FeynArts output sometimes requires `LoadModel` from a GenericModel (`Lorentz.gen`) that ships inside FeynArts itself. If the user supplies a custom `feynarts_path`, does our driver need to copy / version-lock the GenericModel? Or do we trust `feynarts_path` to always supply a compatible `Lorentz.gen`?

2. **Process-spec ergonomics.** FeynArts syntax `{F[1],-F[1]} -> {V[1],V[1]}` is impenetrable to most users. Should `/feynarts` accept a friendlier alias (e.g. `e+ e- -> Z Z`) and translate via the SARAH particle table written into `summary.json` by `/sarah-build`? This trades off translation-layer complexity against forcing the user to learn FeynArts indexing.

3. **Cache granularity + memory.** One-loop amplitude generation for a moderately large BSM model (e.g. 2HDM+a with 40 states) can produce thousands of diagrams and amplitude `.m` files of 50–500 MB. Do we cache on `(model, process, loop-order)` as proposed, or introduce per-topology caching? What's the hard cap on amplitude-file size before we refuse and emit a `FEYNARTS_AMP_TOO_LARGE` blocker?

4. **Reference-only fallback.** Per `blocker.schema.json`'s `reference_only` branch and the memory note "Augment not replace" — should `/feynarts` have any reference fallback (e.g. textbook SM amplitude for `ee -> ZZ`) when Wolfram activation is missing, or is hard-blocking always correct here? Lean: hard-block.

5. **Diagram-PDF paint layout.** `Paint[]`'s `ColumnsXRows` is process-dependent (tree-level 2→2 vs one-loop 2→2 with 200 diagrams). Do we auto-compute layout based on `Length[ins]`, accept a `--layout` flag, or emit one PDF per topology class?
