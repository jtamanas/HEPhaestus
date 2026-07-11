# One-loop σ_SI floor overlay — build plan (singlet-doublet)

Target: reproduce the Hisano-style one-loop σ_SI "floor" of Fig. 1 of
arXiv:2506.19062 for the singlet-doublet model — the residual scattering
that survives where the tree-level scalar coupling is suppressed (blind
spots). This is multi-session work; this doc is the plan, not a claim of
completion. The cheap groundwork (model wiring + smoke) is done; the loop
chain is not.

## (i) Current validated chain and its anchor

The only *validated* loop-induced DD chain today is the 2HDM+a one, owned by
`/looptools` (`plugins/hep-ph-toolkit/skills/looptools/SKILL.md`):

    /feynarts generate (WE 13.3) -> FeynAmpList.m
      -> /formcalc reduce         -> amp_reduced.m (symbolic PV heads)
      -> /looptools eval          -> scattering/v1 JSON (LoopTools 2.16 PV)
      -> match_nucleon.py         -> coherent σ_SI = (4/π) μ² f²

- Physics owned in Python is only the **coherent nucleon transport**
  (`scripts/match_nucleon.py`); all PV integrals are delegated to LoopTools,
  the amplitude to FormCalc. The skill "reimplements no physics."
- **Anchor** (SKILL.md:244-248): the 2HDM+a A⁰H⁺W⁻ box + mediator triangle
  gives σ_SI(p)=1.18e-48, σ_SI(n)=1.21e-48 cm² at **one** benchmark point,
  triangle coupling C_hχχ=−7.57e-4 matching an independent analytic EW
  box+triangle anchor (−5.41e-4) to ~40% (inside its ×3–5 band). Tooled on
  WE 14.3 + FormCalc 9.10 + LoopTools 2.16, FeynArts upstream on WE 13.3.
- Scope caveats carried by that anchor: single point (no scan); the
  pseudoscalar–quark **box is not folded into f_N** (≤1.7× if folded later);
  σ_SD null in v1. `scattering_golden.json` flags this via
  `sigma_provisional: true`.

This chain is coherent-scalar-SI only and is 2HDM+a-specific. It does not yet
produce a singlet-doublet floor.

## (ii) What exists now

**SD FeynArts model — WIRED (this session).** SARAH's `MakeFeynArts[]` output
`/Users/yianni/SARAH/SARAH-4.15.3/Output/SingletDoublet/EWSB/FeynArts/SingletDoubletEWSB.mod`
is now registered at
`~/.local/share/hephaestus/models/singlet_doublet/feynarts_state/singlet_doublet.mod`
(+ `PROVENANCE.txt`, `ParticleNamesFeynArts.dat`, substitutions). Fields:
χ (FChi)=`F[5]`, down-quark (Fd)=`F[4]`, CP-even scalars=`S[1]`. A toolkit
smoke (`run_feynarts.run` → same driver + WE 13.3 kernel) of the tree process
`F[5] F[4] -> F[5] F[4]` generated **1 diagram** — the t-channel scalar
(S[Generic]) exchange — with real `FeynAmpList.m` / `diagrams.pdf`.

  - **Known blocker (do not "fix" blind):** the `--sarah-model` bootstrap is
    broken. In `run_feynarts.py:189` `resolve_model()` raises
    `FEYNARTS_SARAH_STATE_MISSING` (`resolve_model.py:102`) *before* step-4
    `_run_make_feynarts()` (`run_feynarts.py:221`) can create the state — so a
    first-ever SARAH model can never self-bootstrap. Also `make_feynarts_driver.m.tpl`
    calls `Start["singlet_doublet"]`, but the SARAH model name is
    `SingletDoublet` (name-mapping gap). We sidestepped both by registering the
    `.mod` directly and driving via `--model-file`; a proper fix (reorder +
    name map) is a prerequisite for a hands-off SD chain.

**Loop-operator scaffolding — UNWIRED, UNTESTED.**
`cross_sections/si_one_loop.py` + `loop_functions/{passarino_veltman,box_integrals}.py`
(836 LoC total). Exact gaps:

  1. **No Wilson-coefficient computation from the model.**
     `sigma_SI_one_loop_SD()` (`si_one_loop.py:33`) *takes* C_triangle,
     C1/C5/C6_box, CG_box, C_q_EW, … as **arguments**. Nothing computes them
     from the SD spectrum/couplings — there is no FeynArts→FormCalc→LoopTools
     bridge feeding this function. It is a nucleon-transport shell with no
     model input. `triangle_coefficient_SD()` (`si_one_loop.py:165`) is a
     hand-typed analytic guess, not a tool artifact.
  2. **Zero callers, zero tests.** No module imports `si_one_loop`; the only
     references are its own internal `from ..loop_functions...` imports
     (`si_one_loop.py:183,215`; `box_integrals.py:11`). No `test_*.py`
     references the loop functions. The relative imports also make the modules
     un-runnable as scripts.
  3. **Convention caveats — collides with the toolkit norm.**
     `passarino_veltman.py` is a **pure-Python analytic PV** implementation in
     the q²→0 limit (its own docstring, lines 8-10, says "should be
     cross-checked against LoopTools" — never done). B0 uses an MSbar scheme
     with μ=√(m₁m₂) (`passarino_veltman.py:15-45`). The validated chain
     forbids exactly this: LoopTools owns PV, nothing is reimplemented. Any
     number from this scaffolding is presently untraceable to a tool.

## (iii) Four-step plan

1. **Amplitude definition.** Fix the SD process set for the SI floor: tree
   `F[5] F[4] -> F[5] F[4]` (blind-spot suppressed) plus the one-loop set
   (triangle: χ_j in loop + h mediator; box: χ/scalar box; W/Z EW loops).
   Generate via the wired model (`--model-file` today; `--sarah-model` once the
   bootstrap blocker above is fixed). Loop order 1, real `FeynAmpList.m`.
2. **FormCalc reduction.** `/formcalc reduce` → `amp_reduced.m` carrying
   symbolic A0i/B0i/C0i/D0i heads. No analytic hand-reduction. This retires
   the pure-Python `passarino_veltman.py`/`box_integrals.py` in favour of
   LoopTools-evaluated heads.
3. **Nucleon matching extension.** `match_nucleon.py` owns the *coherent
   scalar* transport only. The SD floor additionally needs **twist-2** and
   **gluon** operators (`si_one_loop.py:90-96`: the (3/4)(q²+q̄²) twist-2 sum
   and the (2/27)f_TG gluon term). Extend `match_nucleon.py` with these
   contractions (form factors already in `constants.py`: `Q2_*`, `QBAR2_*`,
   `F_TG_P`), fed by LoopTools-evaluated coefficients — not the shell's scalar
   arguments.
4. **Validation.** Anchor the SD floor to the paper's Fig. 1 curve and to a
   Hisano-style analytic cross-check at ≥1 blind-spot point (χ mass where the
   tree scalar coupling → 0, so σ_SI is loop-dominated). Reuse the 2HDM+a
   pattern: match the LoopTools number to an independent analytic anchor within
   its stated band before trusting a scan. **Validation anchor = Fig. 1 of
   arXiv:2506.19062 (SD one-loop σ_SI floor) + Hisano box/triangle analytic.**

## (iv) Norms (non-negotiable)

- **No analytic-approximation shortcuts.** PV integrals via LoopTools;
  amplitude via FormCalc. The pure-Python `loop_functions/` are reference/
  cross-check only and must be retired from the production path (per the
  `/looptools` "reimplements no physics" rule and its `FEYNARTS_ABSENT` /
  no-`reference_only` policy).
- **Every number traced to a tool artifact.** σ_SI values must derive from a
  committed `FeynAmpList.m` → `amp_reduced.m` → `scattering/v1` chain, not from
  hand-typed coefficients. Flag single-point results `sigma_provisional: true`
  until a scan + independent anchor exist.
- **Red-first tests.** Each step lands a failing test first (amplitude count,
  UV-finiteness/gauge-stability of the reduced amp, twist-2+gluon transport vs
  a fixture, floor value vs the Fig. 1 anchor), gated like the existing
  `looptools/tests/test_smoke.py` (`HEPPH_RUN_WOLFRAM_TESTS=1`) for the tooled
  legs.
