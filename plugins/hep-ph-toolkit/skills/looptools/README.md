# /looptools eval — design note (ADR)

## Decision: mechanism A (Wolfram + LoopTools MathLink) for v1

LoopTools is not a CLI that eats `amp_reduced.m`.  It is (a) a Fortran/C library
and (b) a MathLink/WSTP executable (`$PREFIX/bin/LoopTools`) that exposes
`A0i/B0i/C0i/D0i` as Wolfram functions.  FormCalc's reduced amplitude keeps
native PV heads (`pv_heads: formcalc-native`), which bind directly onto those
MathLink functions.

`/looptools eval` therefore mirrors `/formcalc`: a Python CLI
(`scripts/run_looptools.py`) prepares the numeric model point, dispatches a
`.wls` driver (`scripts/run_eval.wls`) via `wolframscript`, parses the emitted
numbers, matches to the nucleon σ, and writes `scattering/v1`.

- **A — Wolfram MathLink (chosen).** Ecosystem fit with the FormCalc/Wolfram
  upstream chain; reuses the formcalc wls-driver + Python-wrapper shape 1:1.
  Hard-depends on `looptools_mathlink_available == "true"` and a Wolfram kernel.
- **B — FormCalc Fortran codegen (deferred to v1.1).** `WriteSquaredME[]` →
  generated Fortran linked against `libooptools.a` → compiled binary.  No
  Wolfram at eval time, but a whole codegen/build pipeline.  Revisit only if the
  deployment target lacks a runtime Wolfram kernel.

## Decision: fixture-bypass for 2HDM+a DD

DD runs on the FeynArts/FormCalc output derived from the hand-crafted
`TwoHdmAfix` fixture (`plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/`),
exactly as relic density was unblocked — bypassing the `/sarah-build` renderer
(still unable to emit a correct Dirac-singlet PortalDM UFO).  The `/sarah-build`
renderer backport is separate, non-blocking debt.  Outputs stamp
`model_source: "hand_crafted_sarah_model"` + `model_fixture: ...`.

Physics gate cleared by the live SARAH kernel audit
(`/tmp/hephaestus-physics-gate-results.md`, verdict PASS): the χχ–a, a–q–q, and
A⁰H⁺W⁻ vertices the box needs are present and charge-conserving; the three
`Vertex::ChargeViolating` warnings are a benign SARAH self-check artifact.

## Decision: minimal owned physics in `match_nucleon.py`

`match_nucleon.py` owns ONLY the textbook σ = (4/π) μ² f² transport from
effective DM–nucleon couplings (GeV⁻²) to per-nucleon cross-sections (cm²).  The
risky quark→nucleon scalar form-factor contraction (α_q → f_N with σ-term
presets + the 2/27·f_TG heavy-quark gluon matching) is delegated to the FormCalc
side inside `run_eval.wls`, which is the right place to know the quark content
and is exercised only by the Tier-3 smoke.

## Test gating

- Tier-1 unit + Tier-2 integration run entirely against committed fixtures with
  the `wolframscript` subprocess stubbed by `tests/fixtures/eval_output.json`
  (env seam `HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT`).  No external tools.
- Tier-3 `tests/test_smoke.py` is double-gated (`@pytest.mark.smoke` +
  `HEPPH_RUN_WOLFRAM_TESTS=1` skipif, lazy driver import): committed-but-skipped.
  It is the ONLY real correctness check — it runs the real A⁰H⁺W⁻ box and
  asserts a finite, UV-finite, gauge-stable σ_SI.  **All fixture σ numbers are
  PROVISIONAL until this smoke replaces them on a tooled box.**
