---
name: looptools
version: 1
description: Numerically evaluate a FormCalc-reduced one-loop amplitude with LoopTools 2.16 (Passarino-Veltman integrals via the Wolfram/LoopTools MathLink) and emit a scattering/v1 JSON (σ_SI, σ_SD) for direct detection. Unblocks the 2HDM+a loop-only DD path. Self-heals via _shared/installs/looptools preflight.
subcommands:
  - eval
---

# /looptools

Numerical-evaluation leaf of the loop-induced direct-detection (DD) subchain.
`/looptools eval` takes FormCalc's analytically-reduced amplitude
(`amp_reduced.m`, still carrying symbolic Passarino-Veltman heads), substitutes a
numerical model point, **numerically evaluates the PV integrals via LoopTools**,
matches onto the nucleon σ_SI/σ_SD, and emits a `scattering/v1` JSON that
`/ddcalc` already consumes.

It reimplements **no physics**: PV integral evaluation is delegated to LoopTools;
the amplitude is delegated to FormCalc; the only owned logic is (a) parameter-
point substitution, (b) the minimal amplitude → nucleon-σ transport, and (c) JSON
emission + schema validation.

```
SARAH fixture (TwoHdmAfix)
  → /feynarts generate  → FeynAmpList.m
  → /formcalc reduce     → amp_reduced.m (+ meta, PV heads A0i/B0i/C0i/D0i)
  → /looptools eval      → scattering/v1 JSON (σ_SI, σ_SD)          [THIS SKILL]
  → /ddcalc run          → ddcalc_result/v1 (exclusion verdict)
```

For 2HDM+a the mediator `a` is CP-odd, so tree-level SI scattering is
CP-forbidden (`σ_SI_tree ≈ 0`); the leading DD signal is the **one-loop
charged-Higgs/W box + mediator triangle**.

---

## When to invoke

Use `/looptools eval` after `/formcalc reduce`, when:

1. `/formcalc reduce` has produced `amp_reduced.m` + `amp_reduced.meta.json`
   (with `pv_heads: formcalc-native`).
2. LoopTools is installed with the MathLink binary — see `## Preflight: LoopTools`.
3. A Wolfram kernel is available — see `## Preflight: Wolfram`.
4. A model point (SLHA / param_card) is available (`--point`).

---

## Preflight: LoopTools

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh

- **exit 0** → LoopTools is installed and registered in config; proceed.
- **exit non-zero** → LoopTools is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md` into context and
  follow it. When the install completes, re-run `detect.sh` before proceeding. If
  it still fails, halt with the blocker code from the install reference.

Mechanism A additionally requires the LoopTools **MathLink** binary
(`$PREFIX/bin/LoopTools`): the install reference records
`looptools_mathlink_available` in config. If it is not `"true"`, `/looptools
eval` halts with `LOOPTOOLS_MATHLINK_UNAVAILABLE` (no analytic fallback).

---

## Preflight: FormCalc

`/looptools eval` consumes FormCalc output and the driver loads `FormCalc`` at
eval time. Run:

    bash plugins/hep-ph-toolkit/_shared/installs/formcalc/detect.sh

- **exit 0** → proceed.
- **exit non-zero** → load `_shared/installs/formcalc/INSTALL.md`, follow it,
  re-run, and halt with the install blocker if it still fails.

---

## Preflight: Wolfram

Mechanism A needs a Wolfram kernel to drive the LoopTools MathLink. If
`config.wolfram_engine_path` is unset and `wolframscript` is not on `PATH`,
`/looptools eval` halts with `WOLFRAM_KERNEL_ABSENT`
(activate with `wolframscript --activate`).

---

## Subcommands

### `eval`

```
/looptools eval \
  --amp-reduced  <path/to/amp_reduced.m> \
  --point        <path/to/model_point.slha> \
  --output-dir   <dir> \
  [--form-factors {default_2018|A1}]   default: default_2018 \
  [--dm-pdg <int>]                      default: 9989932 (TwoHdmAfix chi) \
  [--force]
```

`amp_reduced.meta.json` is read from the same directory as `--amp-reduced`.

---

## Options

```
--amp-reduced PATH    FormCalc-reduced amplitude (amp_reduced.m). Required.
--point PATH          Model point as SLHA / param_card. Required.
--output-dir DIR      Output directory (default: ./looptools_output/).
--form-factors PRESET Nucleon σ-term preset: default_2018 (default) | A1.
--dm-pdg INT          DM PDG id override (default 9989932 = TwoHdmAfix chi).
--force               Ignore the cache and re-evaluate.
```

---

## Outputs

| File | Description |
|---|---|
| `scattering.json` | `scattering/v1` document (σ_SI/σ_SD); consumed by `/ddcalc run --sigma-json` |
| `run/<ts>/summary.json` | Run receipt: `{n_diagrams, wall_clock_s, cached, looptools_version, n_pv_calls, point_id}` |
| `run/<ts>/eval_output.json` | Raw driver output (looptools_eval_output/v1) |
| `run/<ts>/point.json` | The numeric model point handed to the driver |
| `.build_key` | Cache token (written last, atomically) |

All outputs are written to `--output-dir` (default `$PWD/looptools_output/`).

---

## State layout

```
<output-dir>/
  scattering.json              (scattering/v1 — the physics result)
  .build_key                   (cache token — written last via atomic_write.sh)
  run/<ts>/
    point.json                 (numeric model point → driver)
    eval_output.json           (raw driver output — looptools_eval_output/v1)
    summary.json               (run receipt)
```

---

## Cache

Cache key = `sha256` of:
1. SHA256 of `amp_reduced.m` bytes
2. Canonical JSON of the numeric model point (sorted keys)
3. `--form-factors` preset
4. `looptools_version` from config
5. `wolfram_version` from config
6. `canonicalizer_version` (bump when the hash function changes)

Cache hit requires `scattering.json` and `.build_key` present and `.build_key`
matching. Deleting `scattering.json` with `.build_key` in place forces a miss.

---

## Recoverable vs fatal contract

| Code | Mode | Trigger | Context |
|---|---|---|---|
| `LOOPTOOLS_INPUT_MISSING` | fatal | `amp_reduced.m` / `amp_reduced.meta.json` / model point absent | `missing` |
| `LOOPTOOLS_NOT_CONFIGURED` | fatal | `config.looptools_path` unset/invalid after preflight | `path` |
| `LOOPTOOLS_MATHLINK_UNAVAILABLE` | fatal | `looptools_mathlink_available != "true"` (mechanism A needs it) | — |
| `WOLFRAM_KERNEL_ABSENT` | fatal | `wolfram_engine_path` unset and `wolframscript` absent | — |
| `LOOPTOOLS_META_INCOMPATIBLE` | fatal | `amp_reduced.meta.json` `pv_heads != "formcalc-native"` | `found`, `expected` |
| `LOOPTOOLS_DRIVER_FAILED` | fatal | `run_eval.wls` exited non-zero or emitted malformed output | `exit_code` |
| `LOOPTOOLS_AMPLITUDE_NONFINITE` | recoverable | amplitude NaN/Inf or residual UV pole / gauge dependence (not cancelled) | `point_id` |
| `LOOPTOOLS_SCHEMA_INVALID` | fatal | emitted `scattering/v1` fails validation | `errors` |
| `LOOPTOOLS_MASS_DEGENERATE` | recoverable | PV evaluation hits a Gram/Landau threshold singularity at this point | `point_id` |

Install-time codes (`LOOPTOOLS_DOWNLOAD/CONFIGURE/BUILD/SMOKE_TEST_FAILED`,
`GFORTRAN_ABSENT`) live in `_shared/installs/looptools/` and are distinct from
these runtime codes.

---

## No `reference_only` fallback

This skill does not fall back to analytic results. Missing install → hard
blocker (`LOOPTOOLS_NOT_CONFIGURED` / `LOOPTOOLS_MATHLINK_UNAVAILABLE` /
`WOLFRAM_KERNEL_ABSENT`), never a silent analytic approximation. Per manager
rule, hard failures are safer than silent approximations.

---

## Physics scope (v1)

**In scope.**
- Mechanism A: Wolfram + LoopTools MathLink numerical PV evaluation (see
  `README.md` ADR). FormCalc-native PV heads (A0i/B0i/C0i/D0i).
- 2HDM+a loop-only DD: charged-Higgs/W box (A⁰H⁺W⁻) + mediator triangle, with
  CP-forbidden tree SI. σ_SI per nucleon (proton, neutron).
- Nucleon σ-term presets `default_2018` (default) / `A1`.
- fixture-bypass: runs on the hand-crafted `TwoHdmAfix` SARAH fixture, stamped
  `model_source: hand_crafted_sarah_model` (mirrors how relic was unblocked).

**Out of scope (deferred).**
- σ_SD: emitted `null` in v1 (the box is predominantly SI; SD is sub-leading and
  not half-validated). The schema allows null; a driver supplying SD couplings is
  matched with the same coherent formula and labelled provisional.
- Mechanism B (FormCalc Fortran codegen, no Wolfram at eval time) — v1.1.
- Live `/sarah-build` renderer UFO for the loop chain — separate, non-blocking
  debt (renderer backport).
- NREFT operators; multi-component DM combination.

The amplitude → σ matching owned in Python is the textbook coherent formula
σ = (4/π) μ² f²; the risky quark→nucleon form-factor contraction is delegated to
`run_eval.wls` (FormCalc side) and validated only by the Tier-3 smoke.

---

## Scripts reference

| Script | Role |
|---|---|
| `scripts/run_looptools.py` | CLI entry (`eval`): preflight, gates, cache, dispatch, emit |
| `scripts/cache_key.py` | SHA256 cache key (amp bytes + point + versions) |
| `scripts/prepare_point.py` | SLHA/param_card → numeric substitution dict + DM mass |
| `scripts/run_eval.wls` | 2HDM+a model driver — real numerical PV core (binds the amplitude symbols, Dirac+up-quark scalar projection, Higgs-portal nucleon matching → effective couplings) |
| `scripts/run_eval_common.wl` | Model-AGNOSTIC plumbing `Get[]`ed by the driver: argv contract, FormCalc + LoopTools Install/ltini load + C0i self-test, the `evalTermCommon` SumOver/IndexSum engine, the `emitUnboundGuard` (UNBOUND-MODEL-PARAMETERS + Exit[3]) guard, and `writeEvalOutput`. Shared with the future `run_eval_sd.wls`; its header documents the driver contract. |
| `scripts/parse_eval_output.py` | Driver output → Python dict + finiteness gate |
| `scripts/match_nucleon.py` | Effective DM–nucleon couplings → σ_SI/σ_SD (owned transport) |
| `scripts/emit_scattering.py` | Assemble + validate `scattering/v1` |

---

## Fixture and testing notes

- **Tier-1 unit + Tier-2 integration** run entirely against committed fixtures
  with the `wolframscript` subprocess **stubbed** by
  `tests/fixtures/eval_output.json` (env seam `HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT`).
  No external tools: `pytest` and `pytest -m integration` are green tool-less.
- **Tier-3 `tests/test_smoke.py`** is double-gated (`@pytest.mark.smoke` +
  `HEPPH_RUN_WOLFRAM_TESTS=1` skipif, lazy driver import): committed-but-skipped.
  It runs the **real** A⁰H⁺W⁻ box and asserts a finite, UV-finite, gauge-stable
  σ_SI — the audit's "step 2" end-to-end closure.
- **The σ numbers are real and EW-anchor-validated at a single benchmark
  point**, not provisional: `run_eval.wls` computes them on a tooled box
  (Wolfram Engine 14.3 + FormCalc 9.10 + LoopTools 2.16, with FeynArts upstream
  on WE 13.3), giving σ_SI(p)=1.18e-48, σ_SI(n)=1.21e-48 cm² with the triangle
  coupling C_hχχ=−7.57e-4 matching the independent analytic EW box+triangle
  anchor (−5.41e-4) to ~40% (inside its ×3–5 band). Caveats: it is **one
  benchmark point** (not a scan); the pseudoscalar-quark **box is not folded
  into f_N** (≤1.7× upward if folded later); σ_SD is null in v1. The committed
  `scattering_golden.json` carries `sigma_provisional: true` to flag exactly
  these (single point + box-matching deferred) — not that the transport is fake.
  The Tier-3 smoke is the end-to-end hardening gate: gated off by default
  (`HEPPH_RUN_WOLFRAM_TESTS=1`) but green on a tooled box.

---

## Linkage

- Output schema: `plugins/shared/schemas/scattering.schema.json` (`source: looptools`)
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Runner-spec loader: `plugins/shared/runner_spec_loader.py`
- Atomic-write helper: `plugins/shared/install-helpers/atomic_write.sh`
- Install prereq: `_shared/installs/looptools/INSTALL.md`
- Upstream: `/formcalc` (provides `amp_reduced.m` + `amp_reduced.meta.json`)
- Downstream: `/ddcalc` (`run --sigma-json` consumes `scattering/v1`)
- Router: `/dark-matter-constraints` Step 2 loop-only DD sub-branch
