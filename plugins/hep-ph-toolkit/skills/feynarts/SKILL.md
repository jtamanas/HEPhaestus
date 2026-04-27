---
name: feynarts
description: Generate Feynman diagrams and amplitudes using FeynArts 3.11. Supports built-in models (SM, SMQCD, THDM, MSSM) and SARAH-generated models. Outputs FeynAmpList.m, diagrams.pdf, topologies.json, and metadata sidecar.
---

## When to invoke

Use `/feynarts generate` to generate Feynman diagrams and compute the amplitude
list for a specified process and model.  Prerequisites:

1. `/feynarts-install` must have run successfully (`feynarts_path` in config).
2. Wolfram Engine must be activated.
3. For SARAH-generated models: the model must have been built with `/sarah-build`
   first.

---

## Subcommands

### `generate`

Generate diagrams and amplitudes.

```
/feynarts generate \
  --process "e+ e- -> mu+ mu-" \
  --model SM \
  [--loop-order 0] \
  [--excludes "Tadpoles,SelfEnergies"] \
  [--sarah-model <name>] \
  [--model-file <path>] \
  [--output-dir <dir>] \
  [--force]
```

---

## Process specification

Two syntaxes are accepted:

### Alias form (default)

```
--process "e+ e- -> mu+ mu-"
```

Particle names are resolved using `tables/<model>.json` (for built-in models)
or `$STATE_ROOT/models/<name>/sarah/particles.m` (for SARAH models).

Examples:
```
--process "e+ e- -> mu+ mu-"        # SM tree-level
--process "Z -> Z"                   # self-energy (loop)
--process "g g -> t tbar"            # SMQCD
--process "H -> b bbar"              # THDM/MSSM
```

### Raw FeynArts tuple form

Auto-detected when the particle string begins with `{` or `[{`:

```
--process "{{-F[2,{1}],F[2,{1}]},{-F[2,{2}],F[2,{2}]}}"
--process "[{-F[2,{1}],F[2,{1}]},{-F[2,{2}],F[2,{2}]}]"
```

Both forms are accepted.  The `{...}` form is native FeynArts Mathematica list
syntax; the `[{...}]` form wraps it in a JSON-style array bracket for
readability.  The string is passed verbatim to `InsertFields[]` after stripping
the outer `[` / `]` if present.

---

## Model source precedence

Exactly one of `--sarah-model`, `--model-file`, or `--model` (built-in) must be
specified.  Providing more than one is a fatal error (`FEYNARTS_MODEL_SOURCE_CONFLICT`).

| Flag | Model source | `.mod`/`.gen` location |
|---|---|---|
| `--model <name>` | FeynArts built-in (SM, SMQCD, THDM, MSSM) | FeynArts package `Models/` dir |
| `--sarah-model <name>` | Post-hoc SARAH `MakeFeynArts[]` | `$STATE_ROOT/models/<name>/feynarts_state/` |
| `--model-file <path>` | User-supplied `.mod`/`.gen` pair | User-supplied path |

### Post-hoc SARAH `MakeFeynArts[]`

When `--sarah-model <name>` is used, `/feynarts` invokes a separate
`make_feynarts_driver.m.tpl` script that:
1. Runs `SARAH`'s `MakeFeynArts[]` in an isolated `feynarts_state/` directory
   under `$STATE_ROOT/models/<name>/`.
2. Writes `<model_name>.mod` and `<model_name>.gen` there.

This is a post-hoc step that runs in a separate Wolfram session from
`/sarah-build`.  It does NOT modify the SARAH state created by `/sarah-build`.

---

## Outputs

| File | Description |
|---|---|
| `FeynAmpList.m` | FeynArts amplitude list; loadable with `Get["FeynAmpList.m"]` |
| `FeynAmpList.meta.json` | Sidecar conforming to `processspec/v1`: `schema_version`, `feynarts_version`, `model_hash`, `n_diagrams`, embedded `processspec` object |
| `diagrams.pdf` | Rendered diagram pages (via `Paint[]`) |
| `topologies.json` | Topology summary: `{n_topologies, note}` — **v1: `n_topologies` is a heuristic estimate, not extracted from Wolfram** (see note below) |
| `summary.json` | `{n_diagrams, process, loop_order, model, cached, wall_clock_s}` |

**Note on `topologies.json` in v1:** The `n_topologies` field is produced by a
heuristic estimator (`_estimate_n_topologies` in `postprocess.py`) that does
**not** perform a Wolfram `TopologyList[]` round-trip.  The value may differ from
the actual FeynArts topology count on a live Wolfram run.  Exact topology
extraction is planned for v1.1.

All outputs are written to `--output-dir` (default: `$PWD/feynarts_output/`).

---

## Caps and blockers

| Code | Mode | Trigger | Context fields |
|---|---|---|---|
| `FEYNARTS_TOO_MANY_DIAGRAMS` | `fatal` | `Length[ins] > 2000` before `CreateFeynAmp` | `diagram_count`, `cap` |
| `FEYNARTS_AMP_TOO_LARGE` | `fatal` | `FeynAmpList.m` size > 200 MB after `Put` | `amp_size_mb`, `cap` |
| `FEYNARTS_TIMEOUT` | `fatal` | wall-clock > 600 s (SIGKILL) | `timeout_s`, `wall_clock_s` |
| `FEYNARTS_EMPTY_RESULT` | **recoverable** | `Length[ins] == 0` | `message` |
| `FEYNARTS_MODEL_SOURCE_CONFLICT` | `fatal` | >1 of `--model`/`--sarah-model`/`--model-file` | `flags_provided` |
| `FEYNARTS_SARAH_STATE_MISSING` | `fatal` | `--sarah-model` but state dir absent | `model_name`, `state_dir` |
| `FEYNARTS_MODEL_FILE_INVALID` | `fatal` | `--model-file` path has no `.mod` file | `path` |
| `FEYNARTS_ABSENT` | `fatal` | `feynarts_path` not in config / FeynArts.m missing | — |
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | `wolfram_engine_path` not set | — |

### Known limitation: SIGKILL on timeout (macOS, v1)

`FEYNARTS_TIMEOUT` is raised when `subprocess.run(timeout=)` expires.  On macOS,
Python's `subprocess` does not reliably deliver `SIGKILL` to the Wolfram kernel
child process — the kernel can linger as an orphan after the Python timeout.
The v1 implementation adds a best-effort `proc.kill()` call in the handler, but
a full fix (psutil-based process-tree kill) is deferred to v1.1.

### `FEYNARTS_EMPTY_RESULT` is recoverable

This code is returned when FeynArts finds no diagrams for the given process and
topology filters.  It is **not fatal** — the caller can broaden topology filters
or change the process.  All other `FEYNARTS_*` codes are fatal.

---

## No `reference_only` fallback

**This skill does not implement a `reference_only` mode and will never fall back
to analytic results.**  If the Wolfram kernel is absent or FeynArts is not
installed, the skill emits `FEYNARTS_ABSENT` or `WOLFRAM_KERNEL_ABSENT` and
halts.  The caller must ensure prerequisites are met via `/feynarts-install`
before invoking `/feynarts generate`.

Rationale: analytic fallbacks would silently produce inconsistent results (sign
conventions, gauge choices, renormalisation scheme) that downstream tools
(`/formcalc`, LoopTools) would consume without warning.  Hard failures are
safer than silent approximations.

---

## Cache

Results are cached under `$STATE_ROOT/cache/feynarts/<cache_key>/`.

Cache key is `sha256` of the concatenation of:
1. SHA256 of `<model>.mod`
2. SHA256 of `<model>.gen`
3. FeynArts version string
4. SHA256 of canonical processspec JSON (sorted keys, sorted `excludes`)
5. `feynarts_generic_model_hash` (`sha256(Models/Lorentz.gen)`)

If all five match, the cached `FeynAmpList.m` and sidecars are copied to the
output directory without re-running Mathematica.  `summary.json.cached == true`.

Cap overrides (env vars) invalidate the cached result only if the cap values
actually change the output (caps are not part of the cache key — they are
enforced post-run).

---

## Env-var overrides

| Variable | Default | Purpose |
|---|---|---|
| `FEYNARTS_DIAGRAM_CAP` | `2000` | Override diagram count cap |
| `FEYNARTS_AMP_SIZE_CAP_MB` | `200` | Override amp-file size cap (MB) |
| `FEYNARTS_DEFAULT_TIMEOUT_S` | `600` | Override wolframscript timeout (seconds) |
| `HEPPH_FEYNARTS_STATE_ROOT` | `~/.local/share/hephaestus` | State root for cache + model states |

Caps are chosen conservatively for v1; they will be raised in v1.1 if paper
benchmarks require it.

---

## Linkage

- Shared helpers: `plugins/shared/install-helpers/_common.sh`
- Wolfram helpers: `plugins/shared/install-helpers/wolfram/`
- Process schema: `plugins/shared/schemas/processspec.schema.json`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-feynman.md`
- Install prereq: `/feynarts-install`
- Downstream consumers: `/formcalc` (Phase-B stage 2)
