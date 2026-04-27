---
name: spheno-build
description: Compile a model-specific SPheno binary from SARAH output and run spectrum / RGE calculations.
---

# /spheno-build

Compile a model-specific SPheno binary from SARAH output, run it on a LesHouches input card,
and produce an SLHA mass spectrum. Scan-friendly with deterministic recoverable-failure handling.

---

## When to invoke

Invoke `/spheno-build` after `/sarah-build` has produced SARAH output for the named model.
Prerequisites (checked before doing any work):
- `config.spheno_src_path` set (by `/spheno-install`).
- `$STATE_ROOT/models/<name>/sarah_output/SPheno/<SarahName>/` exists (produced by `/sarah-build`).
- `gfortran` available in PATH.

If either prereq is missing the skill emits a fatal blocker and stops.

---

## Compile stage (cached)

```
scripts/compile_model.py <model_name> [--force]
```

Algorithm:
1. Derive `sarah_name` from `model_name` using `_shared/sarah_name.py`.
2. Compute cache key: `sha256(spec.yaml) + "=" + sarah_version + "+" + spheno_version`.
   Key is stored at `$STATE_ROOT/models/<name>/spheno_bin/.build_key`.
3. If key matches AND binary exists AND `--force` not given: skip compile (return immediately).
4. Copy `$STATE_ROOT/models/<name>/sarah_output/SPheno/<SarahName>/` into `<spheno_src_path>/<SarahName>/`.
5. **Post-SARAH patches** (applied to the copied tree, before `make`). See "Post-SARAH patches on Darwin" below.
6. Run `make -C <spheno_src_path> Model=<SarahName> -j<cpu_count>` (uses `os.cpu_count()`; NOT `nproc` — macOS lacks it).
7. Capture stdout+stderr to `$STATE_ROOT/models/<name>/spheno_bin/make.log`.
8. On failure: emit `SPHENO_COMPILE_FAILED` fatal blocker with `context.make_log_tail` (last 40 lines).
9. Move binary from `<spheno_src_path>/bin/SPheno<SarahName>` to `$STATE_ROOT/models/<name>/spheno_bin/SPheno<SarahName>`.
10. Write cache key.

Cache miss → `--force` bypasses the key check and forces a full recompile.
Cache hit confirmed by the absence of `make` invocation in captured stderr.

### Post-SARAH patches

SARAH's emitted SPheno model tree has three known rough edges that break the downstream `make`.
`compile_model.py` applies three small, idempotent post-copytree fixes so the build succeeds:

| Helper | What it does | Why it's needed |
|---|---|---|
| `_patch_darwin_ar(spheno_model_src)` | Rewrites `ar -ruc -U` → `ar -ruc` on lines 90 and 94 of the per-model `Makefile`. | Xcode's `ar` on Darwin does not accept `-U`. `SPheno-4.0.5/src/Makefile` already branches on `uname -s` (uses `-ruc` on Darwin), but the per-model Makefile SARAH emits does **not** branch and always emits `-U`. No-op on Linux — `-U` is legitimate there. |
| `_dedupe_model_data_decls(spheno_model_src, sarah_name)` | Strips standalone `Real(dp) :: <name>` lines in `Model_Data_<Model>.f90` when `<name>` already appears in an earlier grouped declaration (e.g. `Real(dp) :: g1,g2,g3,MS,MPsi,...`) in the module-spec part (before `Contains`). | SARAH can emit a BSM parameter both in the "RGE-running" grouped declaration and as a later standalone line inside the same module — gfortran rejects the redeclaration. Dedupe is scoped to the module spec part only, so per-subroutine scopes (e.g. `RGEAlphaS`'s own `Real(dp) :: nQuark`) are left untouched. |
| `_patch_notparallel(spheno_model_src)` | Inserts `.NOTPARALLEL:` (with a sentinel marker) at the top of the per-model `Makefile`. | The per-model Makefile lists archive members as prerequisites without declaring inter-file Fortran `.mod` dependencies. With `make -jN`, `RGEs_<Model>.f90` etc. can start compiling before `Model_Data_<Model>.mod` has been written to `../include`, and fail with "Cannot open module file". `.NOTPARALLEL:` serializes only this Makefile's targets — the parent `src/libSPheno.a` build keeps its parallel speedup. |

All three helpers are idempotent and safe to re-run after a cache hit. Two were added while debugging
the singlet-doublet demo on macOS; see `demo_output/singlet-doublet/report.md` (2026-04-21) for the
original A/B diagnosis, and the compile-time race (`_patch_notparallel`) that surfaced once A and B
were cleared.

If a future model trips a *different* SARAH emission bug, add another `_patch_*` helper next to
these rather than expanding one of them — each helper should do one thing so it can stay idempotent
and independently testable.

---

## Run stage (single point)

```
scripts/run_spheno.py <model_name> [--params k=v,...] [--input-card <path>]
```

Invocation signature (per spec §5):
```
$STATE_ROOT/models/<name>/spheno_bin/SPheno<SarahName>  <out_dir>/LesHouches.in  <out_dir>/SPheno.spc
```
Two positional arguments only. No shell redirection.

If `--input-card` is provided, the card is copied verbatim into the run directory — no templating applied.
Otherwise, `leshouches_template.py` generates the card from `spec.parameters` defaults, optionally
patched by `--params`.

Output files written to `$STATE_ROOT/models/<name>/runs/<TS>-<HASH>/`, where
`<TS>` is `YYYY-MM-DDTHHMMZ` (minute-resolution UTC) and `<HASH>` is an
8-character blake2b hash of the override set (salted if the exact
timestamp + overrides combination would collide):
- `LesHouches.in` — input card used.
- `SPheno.spc` — raw SLHA output.
- `summary.json` — parsed masses, widths, problems, mixing, spinfo_warnings.

The hash suffix guarantees that multiple runs inside the same UTC minute
never reuse a `run_dir` and overwrite one another's `SPheno.spc`.

---

## Scan mode

```
scripts/run_spheno.py <model_name> --scan MpsiD=200:1000:step=100 --scan gD=0.5:2.5:step=0.5
```

Each `--scan` argument specifies one axis: `name=start:stop:step=s`.
The Cartesian product of all axes is computed; `scan.py` runs each point sequentially.

Output directory: `$STATE_ROOT/models/<name>/runs/scan_<TS>/`

`scan_index.csv` columns: `index`, `<param1>`, `<param2>`, ..., `status`, `blocker_code`, `slha_path`, `timing_s`.

Scan continues past recoverable failures. Fatal failures (no output file) mark the row `status=error`
and continue. Only a SPheno crash on a point with no `.spc` is classified as error.

Determinism: grid values are computed by `numpy`-free arithmetic (`arange`-equivalent using
`range` + step), then sorted lexicographically by parameter name to ensure a stable ordering.
Given identical inputs, `scan_index.csv` is byte-identical across runs.

---

## Recoverable vs fatal contract

| Condition | Blocker code | Mode |
|-----------|-------------|------|
| Exit ≠ 0 or `SPheno.spc` absent | `SPHENO_NO_OUTPUT` | **fatal** |
| `Block PROBLEM` code 1/2/3 present | `SPHENO_SPECTRUM_PROBLEM` | **recoverable** |
| `Block SPINFO` item 4 present | `SPHENO_RGE_NONCONVERGENT` | **recoverable** |
| Clean `Block MASS` present | success | — |
| `spheno_src_path` absent | `SPHENO_PATH_INVALID` | **fatal** |
| SARAH output tree missing | `SPHENO_COMPILE_FAILED` (compile stage) | **fatal** |

Recoverable blockers let scans continue. A row with a recoverable condition is recorded in
`scan_index.csv` with `status=recoverable` and the corresponding `blocker_code`.

Blockers are emitted as single-line JSON to **stderr** conforming to `_shared/blocker.schema.json`.

---

## LesHouches input generation

`scripts/leshouches_template.py build(spec, overrides)` produces a LesHouches input string with:

- `Block MODSEL`: `1  0` (non-SUSY; only supported case in v1).
- `Block SMINPUTS`: PDG 2020 defaults (hardcoded: alpha_em^-1 = 127.934, G_F, alpha_s(MZ), MZ, m_b, m_t, m_tau).
- `Block MINPAR`: one row per `spec.parameters`, in **declaration order** (index 1..N), using `default` values or `overrides` values if provided.
- `Block SPHENOINPUT`: copied verbatim from `$STATE_ROOT/models/<name>/sarah_output/SPheno/<Model>/Input_Files/LesHouches.in.<Model>` (SPHENOINPUT block only).

`patch_minpar(text, params)` replaces MINPAR entries by name-indexed lookup, leaving other entries unchanged.

---

## Config keys written

After a successful single-point run:

| Key | Value |
|-----|-------|
| `config.models[<name>].spheno_bin` | Path to compiled binary |
| `config.models[<name>].latest_slha` | Path to most recent `SPheno.spc` |
| `config.models[<name>].latest_run` | Run directory name (`YYYY-MM-DDTHHMMZ-<8 hex>`) |
| `config.models[<name>].spheno_built_at` | Compile completion timestamp |

---

## Fixture and testing notes

Unit tests use `HEPPH_STATE_ROOT` and `XDG_CONFIG_HOME` pointed at temporary directories.
Integration tests that require a real SPheno binary and gfortran are gated on
`HEPPH_RUN_NETWORK_TESTS=1` or the presence of both `gfortran` and the `SPheno` binary.

The SARAH-output fixture at `tests/fixtures/sarah_output_darksu3.tar.gz` is a committed
placeholder (pre-W3). After W3 merges, the manager re-dispatches using `scripts/regenerate_fixture.py`
to replace it with real SARAH output. Fixture size hard cap: 10 MB gzipped.

---

## Scripts reference

| Script | Purpose |
|--------|---------|
| `scripts/run_spheno.py` | CLI entry point; dispatches compile + run/scan |
| `scripts/dispatcher.py` | Backend-agnostic spectrum dispatch (spheno vs. analytic) |
| `scripts/backends/spheno.py` | SPheno backend wrapper (wraps `run_point.run`) |
| `scripts/backends/analytic.py` | Analytic backend (calls registered Python module) |
| `scripts/analytic_models/` | Registered analytic modules (`singlet_doublet`, …) |
| `scripts/slha_writer.py` | Render analytic result dict → SLHA text |
| `scripts/compile_model.py` | Stage 1: copy SARAH output, run make, cache binary |
| `scripts/run_point.py` | Stage 2: single-point SPheno invocation + classification |
| `scripts/parse_slha.py` | Stage 3: SLHA → summary.json |
| `scripts/leshouches_template.py` | LesHouches input card generation |
| `scripts/scan.py` | Sequential Cartesian-product scan |
| `scripts/regenerate_fixture.py` | Post-W3: rebuild sarah_output_darksu3.tar.gz |

---

## Spectrum backends

`/spheno-build` dispatches spectrum computation to one of two backends,
selected by the ModelSpec field `backends.spectrum`. The default is
`spheno` when `outputs` contains `"spheno"`; otherwise `analytic`. An
explicit `backends.spectrum` value overrides both defaults. Classification
is backend-scoped: `SPHENO_*` codes for the spheno path, `ANALYTIC_*` for
the analytic path.

### Backend inventory

| Backend | Entry class | Module | First consumer | Classification prefix |
|---|---|---|---|---|
| `spheno` | `SphenoBackend` | `scripts/backends/spheno.py` | every SARAH-clean model | `SPHENO_*` |
| `analytic` | `AnalyticBackend` | `scripts/backends/analytic.py` | `singlet_doublet` | `ANALYTIC_*` |

Both conform to the `SpectrumBackend` Protocol at `scripts/backends/__init__.py:25–35`.
`BackendResult` (same file, lines 15–22) keys: `status`, `blocker_code`,
`slha_path`, `summary`, `cache_hit`, `backend`, `timing_s`.

### Dispatcher

`scripts/dispatcher.py` is the single routing point. Public entry:
`dispatch(model_name, spec, params, out_dir, config, backend_factory=None) -> dict`.

Selection rule (`_resolve_backend_name`, lines 31–36):

1. If `spec['backends']['spectrum']` is set, use it verbatim.
2. Else if `"spheno" in spec['outputs']`, use `spheno`.
3. Else `analytic`.

Backends are instantiated lazily via `_load_backend`
(`spec_from_file_location`, lines 39–48). Tests inject fakes through the
`backend_factory` kwarg. Both `run_spheno.py` and `scan.py` call
`dispatch()`; neither imports a backend class directly.

### Choosing a backend

| Symptom | Backend | Notes |
|---|---|---|
| SARAH-clean BSM extension; need RGE running, loop-level Higgs, decay widths | `spheno` | Default when `outputs` includes `spheno`. |
| `/sarah-build` emits `CheckModelFiles::MissingParameter` or `Param.$Failed` on a rank-1 Dirac sub-block | `analytic` | See `/sarah-build` SKILL.md Gotcha #6. |

Other triggers (closed-form tree-level spectra, UFO-only consumers) are
covered by Gotcha #6's Response list. Spec-level coherence between
`outputs` and `backends.spectrum` is enforced by `/sarah-build`'s
`validate_spec._validate_backends`.

### When to enable RGE running (turn on the spheno backend)

SPheno's value over an analytic diagonalisation is almost entirely in
what happens **between the input scale and the observable scale**: RGE
running of couplings, loop corrections to masses, threshold matching,
and decay-width generation. If none of those apply to your model and
your observable, the spheno backend is cost without value — a few
minutes of Fortran compile and a multi-step failure surface for
arithmetic a NumPy eigensolve does in microseconds.

**Most demo benchmarks don't need RGE running.** Profumo's three models
(singlet-doublet, 2HDM+a, dark SU(3)) all take EWSB-scale Lagrangian
parameters as inputs, have closed-form or parameterised mass spectra,
and feed a tree-level relic-density computation in MadDM. The
`singlet_doublet` spec is `spheno`-backed by default (its SARAH → SPheno
path is verified end-to-end — tree SI blind-spot model; commit
`1fb8ad8`), with the analytic 3×3 diagonalisation available as an opt-in
fast path. `two_hdm_a` and `dark_su3` still declare
`backends.spectrum: analytic` with `outputs: [ufo]` and route to
`analytic_models.stub_unimplemented` — their SPheno paths are blocked on
separate, unrelated bugs (SARAH `RecursionLimit` for 2hdm_a; the missing
`/dark-matter-constraints` skill for dark_su3).

Flip back to spheno when **at least one** of the following is true:

- **High-scale inputs.** The spec defines couplings at a scale above
  EWSB (GUT-scale unification, SUSY-breaking mediation scale, a
  messenger scale) and the observable lives at or below EWSB. Running
  down is the point of the calculation.
- **Loop-level spectrum sensitivity.** The observable depends on a
  mass eigenvalue that shifts meaningfully under 1-loop or 2-loop
  corrections — canonically the MSSM Higgs mass, but also any scenario
  where tree-level m_h or m_χ sits in a phenomenologically fragile
  window and the loop correction is O(10 GeV) or more.
- **Intermediate thresholds.** A heavy state integrated out between the
  input scale and EWSB requires matching corrections that a single
  diagonalisation cannot express.
- **Decay widths or flavour / EW precision observables.** SPheno emits
  partial widths for every two- and three-body decay and computes
  flavour observables (b → sγ, Bs → μμ, g-2, Δρ, …) from the running
  spectrum. An analytic module returns mass + mixing only; decay widths
  must be supplied elsewhere or via MadGraph's internal width
  computation.
- **Unitarity / vacuum-stability checks at arbitrary scale.** Need the
  running quartics, not the tree-level ones.

If none of these apply, leave `backends.spectrum: analytic` and either
write the analytic module (see below) or use
`analytic_models.stub_unimplemented` to signal a `BLOCKED` state
explicitly rather than silently falling through to a spheno compile.

### Authoring an analytic module

#### Interface contract

An analytic module is a single `.py` file that exposes one free function:

```
def compute(spec: dict, params: dict) -> dict
```

Return-dict keys:

| Key | Type | Required | Semantics |
|---|---|---|---|
| `masses` | `dict[int, float]` | yes | PDG id → mass in GeV. Empty after a successful `compute()` → fatal `ANALYTIC_INTERNAL_ERROR`. |
| `mixing` | `dict[str, dict[tuple[int,int], float]]` | optional | Mixing-block names keyed by 1-indexed `(row, col)`. Names recognised by `parse_slha.parse` are whitelisted at `parse_slha.py:47–53` (SLHA-standard `NMIX`, `UMIX`, `VMIX`, `STOPMIX`, `SBOTMIX`, `STAUMIX`, `ALPHA`, `HMIX`, `GAUGE`, `MSOFT`, plus SARAH-emitted `ZNMIX`, `UMMIX`, `UPMIX`, and imaginary counterparts `IMZNMIX`, `IMUMMIX`, `IMUPMIX`). Names outside the whitelist parse as flat `{index: float}` dicts, not two-index matrices. |
| `minpar` | `list[tuple[int, float, str]]` | optional | If absent, `slha_writer` echoes `params` in insertion order. |
| `problem` | `list[int]` | optional | Non-empty → recoverable `ANALYTIC_SPECTRUM_PROBLEM`. |

Raise `ValueError` for an invalid parameter range → recoverable
`ANALYTIC_INVALID_PARAMS`. Raise `numpy.linalg.LinAlgError` for a
diagonalisation failure → recoverable `ANALYTIC_SPECTRUM_PROBLEM`. Any
other exception → fatal `ANALYTIC_INTERNAL_ERROR` with `context.params`.

Classification order inside `AnalyticBackend.compute`
(`backends/analytic.py:114–183`): module-missing → `ValueError` →
`numpy.linalg.LinAlgError` → any other `Exception` → (post-compute)
non-empty `problem` list → empty `masses`. A module that returns both a
non-empty `problem` and empty `masses` is classified `ANALYTIC_SPECTRUM_PROBLEM`
(recoverable) before the empty-masses check runs.

#### Location and discovery

Modules live at `scripts/analytic_models/<name>.py`. `_resolve_module`
(`backends/analytic.py:64–80`) resolves in two branches:

- **Explicit branch** — `spec['backends']['analytic_module']` set to a
  dotted name. Consult `analytic_models.REGISTRY` for the trailing key;
  if absent, fall back to `importlib.import_module` on the dotted path
  (escape hatch for out-of-tree modules).
- **Implicit branch** — `backends.analytic_module` absent. Only
  `REGISTRY[model_name]` is consulted; no `importlib` fallback.

Miss in either branch → fatal `ANALYTIC_MODULE_MISSING` blocker with
`context.model`.

`analytic_models/__init__.py` builds the REGISTRY via a `_load("name")`
helper (`spec_from_file_location`, returns `None` on missing file) and
then filters `None` values out of the dict literal. Registering a new
module therefore requires two lines: a top-level
`new_name = _load("new_name")` assignment and a `"new_name": new_name`
entry in the dict literal. A filename typo makes `_load` return `None`
and the module drops silently from `REGISTRY`; the dispatcher then raises
`ANALYTIC_MODULE_MISSING` with no indication that the source file exists.

Sibling helpers (e.g. `_common.py`) are loaded inside each module via
`spec_from_file_location` — the package is imported dynamically and
`analytic_models/` is not on `sys.path`. See
`analytic_models/singlet_doublet.py:27–33` for the canonical pattern.

`_common.py` shadows its hardcoded PDG-default constants with values
from `eval/2506.19062_wimps_blind_spots/constants.py` at import time
**when that tree is present in the repo** (`_common.py:23–49`). A module
that imports `V_H` (or any shadowed name) from `_common` therefore sees
different numerics depending on whether `eval/` is checked out. A
CI test (`tests/test_analytic_singlet_doublet.py`) asserts byte-equivalence
between the two sources.

The bundled `stub_unimplemented` module is a registered placeholder whose
`compute()` raises `RuntimeError`. Per the classification rules above,
that becomes fatal `ANALYTIC_INTERNAL_ERROR` — not `ANALYTIC_MODULE_MISSING`
as the module's own docstring claims. Treat `stub_unimplemented` as a
"module resolves, physics fails" marker, not a "module missing" marker.

#### SLHA output

`slha_writer.render(result, spec, params)` emits a
`parse_slha.parse`-compatible SLHA string with, in order:
`Block MODSEL` (`1 0`, non-SUSY), `Block SMINPUTS`, `Block SPINFO`
(`hephaestus analytic` / `WS-A` watermark), `Block MINPAR` (from
`params` or `result['minpar']`), `Block PROBLEM` if
`result['problem']` is non-empty, `Block MASS`, and one `Block <Name>`
per entry in `result['mixing']`.

The `SMINPUTS` block is byte-identical to `slha_writer._SMINPUTS`
(`slha_writer.py:20–29`), which is in turn a copy of
`leshouches_template._SMINPUTS_LINES` (`leshouches_template.py:23–32`) so
that analytic-backend SLHA and spheno-backend LesHouches cards agree on
SM input values.

`AnalyticBackend.compute` writes three files to `out_dir`:
`SPheno.spc` (rendered SLHA), `LesHouches.in` (traceability echo via
`leshouches_template.build`), and `summary.json` (built by re-parsing
`SPheno.spc` through `parse_slha.parse`). Any `diagnostics` key a module
returns is ignored by `slha_writer.render` and does not survive the
parse-round-trip into `summary.json`.

`parse_slha.py` has been extended to recognise the SARAH-emitted mixing
block names listed above; an analytic module that uses block names
outside the whitelist gets flat single-index parsing from the consumer.

A `.spectrum_key` marker is written at `<model_dir>/.spectrum_key` after
each analytic run (`backends/analytic.py:40–61`). The file is a JSON
object of the form `{"analytic": {"key": "<p_hash>+<mod_hash>", "built_at": "<iso8601>"}}`,
where `p_hash = sha256(json.dumps(params, sort_keys=True, separators=(",", ":")))`
and `mod_hash = sha256(<analytic module bytes>)`. The marker is
traceability-only — no code reads it back to short-circuit a re-compute.

#### Blocker codes

| Code | Mode | Raised when |
|---|---|---|
| `ANALYTIC_MODULE_MISSING` | fatal | `_resolve_module` returns `None` in both the explicit and implicit branches. |
| `ANALYTIC_INVALID_PARAMS` | recoverable | Module raises `ValueError`. `context.params` attached. |
| `ANALYTIC_SPECTRUM_PROBLEM` | recoverable | Module raises `numpy.linalg.LinAlgError`, or returns non-empty `problem`. |
| `ANALYTIC_INTERNAL_ERROR` | fatal | Any other exception during `compute()`, or empty `masses` in a returned result. |

Schema source: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.
Wire format: single-line JSON on stderr, identical to the `SPHENO_*`
family.

#### Physics ship-gate (pattern used by `singlet_doublet`)

The `singlet_doublet` module ships with a paired test at
`tests/test_singlet_doublet_blind_spot.py` that asserts an independent
physics invariant at a precomputed reference point:

- **Invariant.** Eq. (8) of arXiv:2506.19062 — the direct-detection
  blind-spot condition `m_χ₁ + MPsi · sin(2θ) = 0` at
  `θ = arctan2(yh2, yh1)`. Independent of the module under test: any
  sign flip or basis-ordering error in the module surfaces as a
  non-zero residual.
- **Reference point.** `_MS_ZERO = 433.01270189221924`, the `MS` value
  satisfying the blind-spot condition at `MPsi=500`, `θ=-π/6`, `y=1`.
  Precomputed via `scipy.optimize.brentq` against
  `eval/2506.19062_wimps_blind_spots/models/singlet_doublet.diagonalize`
  — a separate codebase. Regeneration parameters are recorded in the
  test's module docstring (`test_singlet_doublet_blind_spot.py:25–28`);
  residual at authoring was `1.137e-16`.
- **Tolerance.** `|residual| / MPsi < 1e-9` (safely above `float64`
  diagonalisation noise).
- **Defence-in-depth.** A second test
  (`test_matches_eval_diagonalize_bytewise`) asserts the module's
  `m_χ₁` matches `eval`'s to `1e-10` at the same point.

The pattern (independent-codebase reference + closed-form invariant +
tight tolerance) is recommended when a second analytic module lands.
It is a pattern, not a requirement — `stub_unimplemented.py` is a
registered analytic module with no such test.

### Cross-references

- `/sarah-build` SKILL.md, Gotcha #6 (Rank-1 Dirac sub-blocks and silent
  parameter degradation) — canonical motivating case for choosing
  `analytic` over `spheno`.
- `sarah-build/scripts/validate_spec.py` `_validate_backends` — enforces
  `outputs` ↔ `backends.spectrum` coherence at spec-validation time.
- arXiv:2506.19062 — physics paper behind the `singlet_doublet`
  ship-gate (Eq. 3 mass matrix, Eq. 8 blind-spot invariant).
