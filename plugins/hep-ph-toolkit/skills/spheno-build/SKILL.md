---
name: spheno-build
description: Compile a model-specific SPheno binary from SARAH output and run spectrum / RGE calculations.
---

# /spheno-build

Compile a model-specific SPheno binary from SARAH output, run it on a LesHouches
input card, and produce an SLHA mass spectrum. Scan-friendly with deterministic
recoverable-failure handling.

## When to invoke

Invoke after `/sarah-build` has produced SARAH output for the named model.
Prerequisites, checked before any work:

- SPheno installed (see `## Preflight: SPheno`).
- `$STATE_ROOT/models/<name>/sarah_output/SPheno/<SarahName>/` exists (produced by `/sarah-build`).
- `gfortran` on PATH.

If any prereq is missing the skill emits a fatal blocker and stops.

## Preflight: SPheno

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/spheno/detect.sh

- **exit 0** → SPheno is installed and registered in config; proceed.
- **exit non-zero** → SPheno is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/spheno/INSTALL.md` into context and
  follow it. When the install completes, re-run `detect.sh` before proceeding.
  If it still fails, halt with the blocker code from the install reference.

## Compile stage (cached)

```
scripts/compile_model.py <model_name> [--force]
```

1. Derive `sarah_name` from `model_name` via `_shared/sarah_name.py`.
2. Cache key: `sha256(spec.yaml) + "=" + sarah_version + "+" + spheno_version`,
   stored at `$STATE_ROOT/models/<name>/spheno_bin/.build_key`.
3. If key matches AND binary exists AND no `--force`: skip compile.
4. Copy `$STATE_ROOT/models/<name>/sarah_output/SPheno/<SarahName>/` into
   `<spheno_src_path>/<SarahName>/`.
5. **Post-SARAH patches** (applied to the copied tree, before `make`; see below).
6. `make -C <spheno_src_path> Model=<SarahName> -j<cpu_count>` (`os.cpu_count()`,
   NOT `nproc` — macOS lacks it).
7. Capture stdout+stderr to `$STATE_ROOT/models/<name>/spheno_bin/make.log`.
8. On failure: emit `SPHENO_COMPILE_FAILED` fatal blocker with
   `context.make_log_tail` (last 40 lines).
9. Move binary `<spheno_src_path>/bin/SPheno<SarahName>` →
   `$STATE_ROOT/models/<name>/spheno_bin/SPheno<SarahName>`.
10. Write cache key.

`--force` bypasses the key check and forces a full recompile. A cache hit is
confirmed by the absence of a `make` invocation in captured stderr.

### Post-SARAH patches

SARAH's emitted SPheno model tree has three known rough edges that break the
downstream `make`. `compile_model.py` applies three small, idempotent
post-copytree fixes (safe to re-run after a cache hit):

| Helper | What it does | Why it's needed |
|---|---|---|
| `_patch_darwin_ar(spheno_model_src)` | Rewrites `ar -ruc -U` → `ar -ruc` on lines 90 and 94 of the per-model `Makefile`. | Xcode's `ar` on Darwin does not accept `-U`. `SPheno-4.0.5/src/Makefile` branches on `uname -s`, but the per-model Makefile SARAH emits does **not** and always emits `-U`. No-op on Linux — `-U` is legitimate there. |
| `_dedupe_model_data_decls(spheno_model_src, sarah_name)` | Strips standalone `Real(dp) :: <name>` lines in `Model_Data_<Model>.f90` when `<name>` already appears in an earlier grouped declaration in the module-spec part (before `Contains`). | SARAH can emit a BSM parameter both in the grouped "RGE-running" declaration and as a later standalone line in the same module — gfortran rejects the redeclaration. Scoped to the module spec part only, so per-subroutine scopes (`RGEAlphaS`'s own `Real(dp) :: nQuark`) are left untouched. |
| `_patch_notparallel(spheno_model_src)` | Inserts `.NOTPARALLEL:` (with a sentinel marker) at the top of the per-model `Makefile`. | The per-model Makefile lists archive members as prerequisites without declaring inter-file Fortran `.mod` dependencies. Under `make -jN`, `RGEs_<Model>.f90` can start compiling before `Model_Data_<Model>.mod` is written to `../include` and fail with "Cannot open module file". `.NOTPARALLEL:` serializes only this Makefile's targets; the parent `src/libSPheno.a` build keeps its parallel speedup. |

Two of these were added while debugging the singlet-doublet demo on macOS
(`demo_output/singlet-doublet/report.md`, 2026-04-21, has the A/B diagnosis and
the compile-time race that surfaced once A and B were cleared). If a future
model trips a *different* SARAH emission bug, add another `_patch_*` helper next
to these rather than expanding one — each helper does one thing so it stays
idempotent and independently testable.

The rank-1 Dirac mass patches (`_patch_rank1_dirac_mass`, `_patch_phasefs_init`)
that let the singlet-doublet SPheno tree compile and give a physical spectrum
are documented in
`sarah-build/references/sarah-workarounds.md` §16–17.

## Run stage (single point)

```
scripts/run_spheno.py <model_name> [--params k=v,...] [--input-card <path>]
```

Invocation signature (spec §5): two positional arguments only, no shell
redirection:

```
$STATE_ROOT/models/<name>/spheno_bin/SPheno<SarahName>  <out_dir>/LesHouches.in  <out_dir>/SPheno.spc
```

With `--input-card`, the card is copied verbatim into the run directory (no
templating). Otherwise `leshouches_template.py` generates it from
`spec.parameters` defaults, optionally patched by `--params`.

Output → `$STATE_ROOT/models/<name>/runs/<TS>-<HASH>/`, where `<TS>` is
`YYYY-MM-DDTHHMMZ` (minute-resolution UTC) and `<HASH>` is an 8-char blake2b
hash of the override set (salted on exact timestamp+overrides collision):

- `LesHouches.in` — input card used.
- `SPheno.spc` — raw SLHA output.
- `summary.json` — parsed masses, widths, problems, mixing, spinfo_warnings.

The hash suffix guarantees multiple runs inside the same UTC minute never reuse
a `run_dir` and overwrite one another's `SPheno.spc`.

## Scan mode

```
scripts/run_spheno.py <model_name> --scan MpsiD=200:1000:step=100 --scan gD=0.5:2.5:step=0.5
```

Each `--scan` argument is one axis: `name=start:stop:step=s`. The Cartesian
product of all axes is computed; `scan.py` runs each point sequentially. Output
→ `$STATE_ROOT/models/<name>/runs/scan_<TS>/`; `scan_index.csv` columns:
`index`, `<param1>`, `<param2>`, …, `status`, `blocker_code`, `slha_path`,
`timing_s`.

Scans continue past recoverable failures. Only a SPheno crash on a point with no
`.spc` is `status=error`. Determinism: grid values via `numpy`-free arithmetic
(`range` + step), sorted lexicographically by parameter name, so `scan_index.csv`
is byte-identical across runs given identical inputs.

## Recoverable vs fatal contract

| Condition | Blocker code | Mode |
|-----------|-------------|------|
| Exit ≠ 0 or `SPheno.spc` absent | `SPHENO_NO_OUTPUT` | **fatal** |
| `Block PROBLEM` code 1/2/3 present | `SPHENO_SPECTRUM_PROBLEM` | **recoverable** |
| `Block SPINFO` item 4 present | `SPHENO_RGE_NONCONVERGENT` | **recoverable** |
| Clean `Block MASS` present | success | — |
| `spheno_src_path` absent | `SPHENO_PATH_INVALID` | **fatal** |
| SARAH output tree missing | `SPHENO_COMPILE_FAILED` (compile stage) | **fatal** |

Recoverable blockers let scans continue (`status=recoverable` + the
`blocker_code` in `scan_index.csv`). Blockers are single-line JSON on **stderr**
conforming to `_shared/blocker.schema.json`.

## LesHouches input generation

`scripts/leshouches_template.py build(spec, overrides)` produces a LesHouches
input string with:

- `Block MODSEL`: `1  0` (non-SUSY; only supported case in v1).
- `Block SMINPUTS`: PDG 2020 defaults (hardcoded: alpha_em^-1 = 127.934, G_F, alpha_s(MZ), MZ, m_b, m_t, m_tau).
- `Block MINPAR`: one row per `spec.parameters`, in **declaration order** (index 1..N), using `default` or `overrides` values.
- `Block SPHENOINPUT`: copied verbatim from `sarah_output/SPheno/<Model>/Input_Files/LesHouches.in.<Model>` (SPHENOINPUT block only).

`patch_minpar(text, params)` replaces MINPAR entries by name-indexed lookup,
leaving other entries unchanged.

## Config keys written

After a successful single-point run:

| Key | Value |
|-----|-------|
| `config.models[<name>].spheno_bin` | Path to compiled binary |
| `config.models[<name>].latest_slha` | Path to most recent `SPheno.spc` |
| `config.models[<name>].latest_run` | Run directory name (`YYYY-MM-DDTHHMMZ-<8 hex>`) |
| `config.models[<name>].spheno_built_at` | Compile completion timestamp |

## Fixture and testing notes

Unit tests use `HEPPH_STATE_ROOT` and `XDG_CONFIG_HOME` pointed at temp
directories. Integration tests needing a real SPheno binary and gfortran are
gated on `HEPPH_RUN_NETWORK_TESTS=1` or the presence of both `gfortran` and the
`SPheno` binary. The SARAH-output fixture at
`tests/fixtures/sarah_output_darksu3.tar.gz` is a committed placeholder (pre-W3);
after W3 merges, the manager re-dispatches `scripts/regenerate_fixture.py` to
replace it with real SARAH output. Fixture size hard cap: 10 MB gzipped.

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

## Spectrum backends

`/spheno-build` dispatches spectrum computation to one of two backends via the
single routing point `scripts/dispatcher.py` (public entry
`dispatch(model_name, spec, params, out_dir, config, backend_factory=None) -> dict`).
Classification is backend-scoped: `SPHENO_*` codes for the spheno path,
`ANALYTIC_*` for the analytic path.

| Backend | Entry class | Module | First consumer | Prefix |
|---|---|---|---|---|
| `spheno` | `SphenoBackend` | `scripts/backends/spheno.py` | every SARAH-clean model | `SPHENO_*` |
| `analytic` | `AnalyticBackend` | `scripts/backends/analytic.py` | `singlet_doublet` | `ANALYTIC_*` |

Both conform to the `SpectrumBackend` Protocol at `backends/__init__.py:25–35`;
`BackendResult` (same file, 15–22) keys: `status`, `blocker_code`, `slha_path`,
`summary`, `cache_hit`, `backend`, `timing_s`. Backends load lazily via
`_load_backend`; tests inject fakes through `backend_factory`. Both
`run_spheno.py` and `scan.py` call `dispatch()`; neither imports a backend class
directly.

**Selection rule** (`_resolve_backend_name`, dispatcher lines 31–36):

1. If `spec['backends']['spectrum']` is set, use it verbatim.
2. Else if `"spheno" in spec['outputs']`, use `spheno`.
3. Else `analytic`.

Spec-level coherence between `outputs` and `backends.spectrum` is enforced by
`/sarah-build`'s `validate_spec._validate_backends`.

### Choosing a backend

| Symptom | Backend |
|---|---|
| SARAH-clean BSM extension; need RGE running, loop-level Higgs, decay widths | `spheno` (default when `outputs` includes `spheno`) |
| `/sarah-build` emits `CheckModelFiles::MissingParameter` or `Param.$Failed` on a rank-1 Dirac sub-block | `analytic` — see `sarah-build/references/authoring-gotchas.md` §6 |

**When to enable RGE running (turn on the spheno backend).** SPheno's value over
an analytic diagonalisation is almost entirely in what happens *between the input
scale and the observable scale* — RGE running, loop corrections to masses,
threshold matching, decay-width generation. If none of those apply, the spheno
backend is cost without value: a Fortran compile and a multi-step failure surface
for arithmetic a NumPy eigensolve does in microseconds. **Most demo benchmarks
don't need it** — Profumo's three models take EWSB-scale Lagrangian inputs, have
closed-form spectra, and feed a tree-level MadDM relic computation.
`singlet_doublet` is nonetheless `spheno`-backed by default (its SARAH → SPheno
path is verified end-to-end; commit `1fb8ad8`), with the analytic 3×3
diagonalisation as an opt-in fast path; `two_hdm_a` and `dark_su3` declare
`backends.spectrum: analytic` with `outputs: [ufo]` and route to
`analytic_models.stub_unimplemented` (their SPheno paths are blocked on unrelated
bugs — SARAH `RecursionLimit` for 2hdm_a; the missing `/dark-matter-constraints`
skill for dark_su3).

Flip to `spheno` when **at least one** is true: high-scale inputs (couplings
defined above EWSB, observable at/below it — running down is the point);
loop-level spectrum sensitivity (a mass eigenvalue shifts meaningfully under
1–2-loop corrections — canonically the MSSM Higgs, or any tree-level mass in a
fragile window with an O(10 GeV) correction); intermediate thresholds (a heavy
state integrated out needs matching a single diagonalisation cannot express);
decay widths or flavour / EW-precision observables (SPheno emits partial widths
and computes b→sγ, Bs→μμ, g-2, Δρ, … from the running spectrum — an analytic
module returns mass + mixing only); unitarity / vacuum-stability checks at
arbitrary scale (need running quartics, not tree-level). If none apply, leave
`analytic` and either write the module or use `analytic_models.stub_unimplemented`
to signal `BLOCKED` explicitly rather than silently falling into a spheno compile.

### Authoring an analytic module

Writing a new analytic module — the `compute(spec, params) -> dict` interface
contract, module discovery/registration, SLHA output, blocker codes, and the
`singlet_doublet` physics ship-gate pattern — is in
[`references/analytic-backend.md`](references/analytic-backend.md). For invoking
the analytic backend as a route around a failing SPheno compile (from a spec or
an out-of-tree driver), see
[`references/analytic-bypass-recipe.md`](references/analytic-bypass-recipe.md).

### Cross-references

- `sarah-build/references/authoring-gotchas.md` §6 (Rank-1 Dirac sub-blocks and
  silent parameter degradation) — canonical motivating case for choosing
  `analytic` over `spheno`.
- `sarah-build/scripts/validate_spec.py` `_validate_backends` — enforces
  `outputs` ↔ `backends.spectrum` coherence at spec-validation time.
- arXiv:2506.19062 — physics paper behind the `singlet_doublet` ship-gate
  (Eq. 3 mass matrix, Eq. 8 blind-spot invariant).
