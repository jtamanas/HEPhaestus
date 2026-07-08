# Authoring an analytic module

Deep reference for the `analytic` spectrum backend, reached from
`/spheno-build` SKILL.md § "Spectrum backends" when a model routes around
SPheno. For the invocation recipe (how to *use* the analytic backend from a
spec or an out-of-tree driver), see
[`analytic-bypass-recipe.md`](analytic-bypass-recipe.md); this file is how to
*write* one.

## Interface contract

An analytic module is a single `.py` file that exposes one free function:

```python
def compute(spec: dict, params: dict) -> dict
```

Return-dict keys:

| Key | Type | Required | Semantics |
|---|---|---|---|
| `masses` | `dict[int, float]` | yes | PDG id → mass in GeV. Empty after a successful `compute()` → fatal `ANALYTIC_INTERNAL_ERROR`. |
| `mixing` | `dict[str, dict[tuple[int,int], float]]` | optional | Mixing-block names keyed by 1-indexed `(row, col)`. Names recognised by `parse_slha.parse` are whitelisted at `parse_slha.py:47–53` (SLHA-standard `NMIX`, `UMIX`, `VMIX`, `STOPMIX`, `SBOTMIX`, `STAUMIX`, `ALPHA`, `HMIX`, `GAUGE`, `MSOFT`, plus SARAH-emitted `ZNMIX`, `UMMIX`, `UPMIX`, and imaginary counterparts `IMZNMIX`, `IMUMMIX`, `IMUPMIX`). Names outside the whitelist parse as flat `{index: float}` dicts, not two-index matrices. |
| `minpar` | `list[tuple[int, float, str]]` | optional | If absent, `slha_writer` echoes `params` in insertion order. |
| `problem` | `list[int]` | optional | Non-empty → recoverable `ANALYTIC_SPECTRUM_PROBLEM`. |

**Majorana phase contract.** `Block MASS` carries `|m|`, so for every Majorana
mixing matrix the module must emit rows satisfying `ZN·M·ZNᵀ = diag(+|m|)`: a
row whose eigenvalue is **negative** must be carried in the `IM*` block (row
× i) with the real-block row zero — exactly what SARAH's generated SPheno does
(`CalculateMFChi`: `ZN(i1,:) = (0,1)*ZNa(i1,:)` for `Eig < 0`). Emitting `|m|`
with a purely real matrix is internally inconsistent and silently corrupts
every vertex linear in that row (at the singlet-doublet canonical point: relic
0.0717 with a spurious 92% χ₁χ₁→Zh instead of the correct 0.2916 — found and
fixed 2026-07-06).

**Mass-matrix sign contract.** The matrix the module diagonalises must be
SARAH's, not the paper's: SU(2)-epsilon contractions put relative minus signs
on some entries (singlet-doublet: `−yh2·v/√2` and `−MPsi`, per the generated
`CalculateMFChi`), and the UFO vertices were generated from the same
Lagrangian. Diagonalising a differently-signed but "equivalent-looking" matrix
produces eigenvector rows with wrong component signs — internally inconsistent
cards whose symptoms at the singlet-doublet point were a spurious σ_SI blind
spot at θ = ±π/4 instead of the true θ = −0.152 (paper Eq. 8) and a relic
biased to 0.242 instead of 0.2916 even at θ = 0 (χ₂/χ₃ t-channel interference
is odd in the column-2 sign; σ_SI is even in it and cannot catch this).
Transcribe the matrix from the generated Fortran, never from the paper. See
`analytic_models/singlet_doublet.py` for the reference implementation of both
contracts.

**Quark-sector Higgs–Yukawa sign contract.** The SM Higgs couples to *every*
quark with the **same sign**: mass and coupling both descend from the one Yukawa
term `L ⊃ −(Y_q/√2)(v+h) q̄q`, giving `g_hqq = −m_q/v` for all flavors (up and
down alike). The ModelSpec Lagrangian must therefore carry the up-Yukawa in its
canonical sign-matched form `−Yu H.u.q` (leading minus present), matching the
down-type `Yd conj[H].d.q`; dropping that leading minus makes the SARAH export
emit up-type `+m_q/v` against down-type `−m_q/v`. With that *relative* sign the
coherent nucleon scalar sum `A_N ∝ Σ_q (g_hqq/m_q) m_N f_Tq` degrades to a
`(f_Tu − f_Td − …)` near-cancellation: tree σ_SI collapses by ~200× and the
proton/neutron amplitudes split (opposite-sign p/n), faking isospin violation.
Because for Majorana DM the only tree SI operator is scalar Higgs exchange,
there is no second amplitude to cancel against — a large or opposite-sign p/n is
never physics, it is this broken model. The relic is UNAFFECTED (the h-quark
scalar vertices enter χ₁χ₁ annihilation squared / not at all), so a correct
Ωh² does not catch it. *Violation example* (singlet-doublet canonical point,
θ=0): σ_SI(p) 3.71e-47 cm² with p/n 8.17 instead of the correct ~7.6e-45 cm²
with p/n 0.97. Fixed at the ModelSpec level (`−Yu H.u.q` restored in three
specs); see the σ_SI adjudication VERDICT §2/§6/§7 and
`skills/singlet-doublet/benchmarks/canonical-2026/expectations.json`. This is a
sibling of the PR #1 SARAH-quark-sector bug class (wrong *sign* here, silent
*zero* there).

Raise `ValueError` for an invalid parameter range → recoverable
`ANALYTIC_INVALID_PARAMS`. Raise `numpy.linalg.LinAlgError` for a
diagonalisation failure → recoverable `ANALYTIC_SPECTRUM_PROBLEM`. Any other
exception → fatal `ANALYTIC_INTERNAL_ERROR` with `context.params`.

Classification order inside `AnalyticBackend.compute`
(`backends/analytic.py:114–183`): module-missing → `ValueError` →
`numpy.linalg.LinAlgError` → any other `Exception` → (post-compute) non-empty
`problem` list → empty `masses`. A module that returns both a non-empty
`problem` and empty `masses` is classified `ANALYTIC_SPECTRUM_PROBLEM`
(recoverable) before the empty-masses check runs.

## Location and discovery

Modules live at `scripts/analytic_models/<name>.py`. `_resolve_module`
(`backends/analytic.py:64–80`) resolves in two branches:

- **Explicit branch** — `spec['backends']['analytic_module']` set to a dotted
  name. Consult `analytic_models.REGISTRY` for the trailing key; if absent, fall
  back to `importlib.import_module` on the dotted path (escape hatch for
  out-of-tree modules).
- **Implicit branch** — `backends.analytic_module` absent. Only
  `REGISTRY[model_name]` is consulted; no `importlib` fallback.

Miss in either branch → fatal `ANALYTIC_MODULE_MISSING` blocker with
`context.model`.

`analytic_models/__init__.py` builds the REGISTRY via a `_load("name")` helper
(`spec_from_file_location`, returns `None` on missing file) and filters `None`
values out of the dict literal. Registering a new module therefore requires two
lines: a top-level `new_name = _load("new_name")` assignment and a
`"new_name": new_name` entry in the dict literal. A filename typo makes `_load`
return `None` and the module drops silently from `REGISTRY`; the dispatcher then
raises `ANALYTIC_MODULE_MISSING` with no indication that the source file exists.

Sibling helpers (e.g. `_common.py`) are loaded inside each module via
`spec_from_file_location` — the package is imported dynamically and
`analytic_models/` is not on `sys.path`. See
`analytic_models/singlet_doublet.py:27–33` for the canonical pattern.

`_common.py` shadows its hardcoded PDG-default constants with values from
`eval/2506.19062_wimps_blind_spots/constants.py` at import time **when that tree
is present in the repo** (`_common.py:23–49`). A module that imports `V_H` (or
any shadowed name) from `_common` therefore sees different numerics depending on
whether `eval/` is checked out. A CI test
(`tests/test_analytic_singlet_doublet.py`) asserts byte-equivalence between the
two sources.

The bundled `stub_unimplemented` module is a registered placeholder whose
`compute()` raises `RuntimeError`. Per the classification rules above, that
becomes fatal `ANALYTIC_INTERNAL_ERROR` — not `ANALYTIC_MODULE_MISSING` as the
module's own docstring claims. Treat `stub_unimplemented` as a "module resolves,
physics fails" marker, not a "module missing" marker.

## SLHA output

`slha_writer.render(result, spec, params)` emits a `parse_slha.parse`-compatible
SLHA string with, in order: `Block MODSEL` (`1 0`, non-SUSY), `Block SMINPUTS`,
`Block SPINFO` (`hephaestus analytic` / `WS-A` watermark), `Block MINPAR` (from
`params` or `result['minpar']`), `Block PROBLEM` if `result['problem']` is
non-empty, `Block MASS`, and one `Block <Name>` per entry in `result['mixing']`.

The `SMINPUTS` block is byte-identical to `slha_writer._SMINPUTS`
(`slha_writer.py:20–29`), itself a copy of `leshouches_template._SMINPUTS_LINES`
(`leshouches_template.py:23–32`) so that analytic-backend SLHA and
spheno-backend LesHouches cards agree on SM input values.

`AnalyticBackend.compute` writes three files to `out_dir`: `SPheno.spc`
(rendered SLHA), `LesHouches.in` (traceability echo via
`leshouches_template.build`), and `summary.json` (built by re-parsing
`SPheno.spc` through `parse_slha.parse`). Any `diagnostics` key a module returns
is ignored by `slha_writer.render` and does not survive the parse-round-trip
into `summary.json`.

`parse_slha.py` recognises the SARAH-emitted mixing block names listed above; an
analytic module that uses block names outside the whitelist gets flat
single-index parsing from the consumer.

A `.spectrum_key` marker is written at `<model_dir>/.spectrum_key` after each
analytic run (`backends/analytic.py:40–61`), a JSON object
`{"analytic": {"key": "<p_hash>+<mod_hash>", "built_at": "<iso8601>"}}` where
`p_hash = sha256(json.dumps(params, sort_keys=True, separators=(",", ":")))` and
`mod_hash = sha256(<analytic module bytes>)`. Traceability-only — no code reads
it back to short-circuit a re-compute.

## Blocker codes

| Code | Mode | Raised when |
|---|---|---|
| `ANALYTIC_MODULE_MISSING` | fatal | `_resolve_module` returns `None` in both branches. |
| `ANALYTIC_INVALID_PARAMS` | recoverable | Module raises `ValueError`. `context.params` attached. |
| `ANALYTIC_SPECTRUM_PROBLEM` | recoverable | Module raises `numpy.linalg.LinAlgError`, or returns non-empty `problem`. |
| `ANALYTIC_INTERNAL_ERROR` | fatal | Any other exception during `compute()`, or empty `masses` in a returned result. |

Schema source: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. Wire
format: single-line JSON on stderr, identical to the `SPHENO_*` family.

## Physics ship-gate (pattern used by `singlet_doublet`)

The `singlet_doublet` module ships with a paired test at
`tests/test_singlet_doublet_blind_spot.py` that asserts an independent physics
invariant at a precomputed reference point:

- **Invariant.** Eq. (8) of arXiv:2506.19062 — the direct-detection blind-spot
  condition `m_χ₁ + MPsi · sin(2θ) = 0` at `θ = arctan2(yh2, yh1)`. Independent
  of the module under test: any sign flip or basis-ordering error surfaces as a
  non-zero residual.
- **Reference point.** `_MS_ZERO = 433.01270189221924`, the `MS` value
  satisfying the blind-spot condition at `MPsi=500`, `θ=-π/6`, `y=1`. Precomputed
  via `scipy.optimize.brentq` against
  `eval/2506.19062_wimps_blind_spots/models/singlet_doublet.diagonalize` — a
  separate codebase. Regeneration parameters are in the test's module docstring
  (`test_singlet_doublet_blind_spot.py:25–28`); residual at authoring was
  `1.137e-16`.
- **Tolerance.** `|residual| / MPsi < 1e-9` (safely above `float64`
  diagonalisation noise).
- **Defence-in-depth.** A second test (`test_matches_eval_diagonalize_bytewise`)
  asserts the module's `m_χ₁` matches `eval`'s to `1e-10` at the same point.

The pattern (independent-codebase reference + closed-form invariant + tight
tolerance) is recommended when a second analytic module lands. It is a pattern,
not a requirement — `stub_unimplemented.py` is a registered analytic module with
no such test.
