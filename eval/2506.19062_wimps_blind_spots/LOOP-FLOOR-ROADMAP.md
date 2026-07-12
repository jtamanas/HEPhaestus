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
`F[5] F[4] -> F[5] F[4]` generated **1 topology** with real `FeynAmpList.m` /
`diagrams.pdf`. **Correction to the earlier shorthand:** that single t-channel
topology is *not* purely scalar. At Classes level it carries **two** generic
insertions — scalar (h `S[1]`, A `S[2]`) **and** Z (`V[2]`) exchange (confirmed
by the step-1 census, `loopset-step1/STEP1.md`). Only the **scalar-h** piece is
the coherent-SI coupling that vanishes at the blind spot; the Z (axial/vector)
and pseudoscalar-A insertions survive there. "Tree is blind-spot suppressed" is
therefore shorthand for "the tree *scalar-h* coupling is suppressed", not the
whole tree amplitude.

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
   `F[5] F[4] -> F[5] F[4]` (scalar-h insertion blind-spot suppressed; Z + A
   insertions survive — see §(ii) correction) plus the one-loop set
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

## (iii-b) Step-2 pending decisions

Open choices that gate the FormCalc reduction leg (step (iii).2), surfaced by
the step-1 diagram census (`loopset-step1/STEP1.md`) and the FormCalc-leg
repair (`formcalc-fix/`). Decide these before committing a floor number:

1. **γ₅ scheme sign-off.** The W-box chiral structure (W + up-quark internal
   lines, χ± = `F[6]`) is renormalisation-scheme-sensitive. `naive` γ₅ is
   smoke-only (anticommuting, ignores the reading-point ambiguity); the
   physical floor should be argued in **`hv`/`bmhv`** (’t Hooft–Veltman /
   Breitenlohner–Maison–’t Hooft–Veltman) for the chiral traces. Pending:
   pick the scheme and justify the box's reading-point convention. The step-1
   1PI-core reduction that seeded `formcalc-fix/` used `--gamma5 naive` and is
   evidence-only, not a physics claim.
2. **Reduction scope.** The census gives three nested sets: the **4-diagram
   1PI core** (2 triangles + 2 boxes; what step-1 reduced), vs the **15-topology
   SD-surviving set** (adds self-energies, WF corrections, tadpoles), vs the 99
   bare topologies. The SI floor minimally needs IRR-2 (loop hχχ triangle) +
   IRR-3/IRR-4 (EW boxes); IRR-1 (quark-side triangle) is mostly
   blind-spot-vanishing except its gluon content (feeds the f_TG operator in
   step-3 transport). Pending: reduce the 4-diagram core first, then decide
   whether self-energy/WF/tadpole renormalisation pieces are needed for a
   UV-finite, gauge-stable floor.
3. **External-state pinning.** Step-1 counts use **class-level** `F[5]`/`F[4]`
   (summed over 3 neutralino eigenstates + down generations). The physical χ₁
   floor should pin **`F[5,{1}]`** (lightest neutralino) and a definite quark
   generation, not the class-level sum. Pending: pin externals to `F[5,{1}]`
   and a down-type generation before extracting a per-point σ_SI.

## (iii-c) Step-2 status (done) + what step 3 needs

**Step-2 status — DONE (evidence, not a physics claim).** Full account in the
runner log `loopset-step2/STEP2.md` (ran against shared checkout main=283f046).
Roadmap evidence only — **no σ_SI numbers** (SD nucleon matching does not exist
yet, so any σ would be untraceable). Summary:

- **χ₁-pinned 1PI core reduced.** Externals pinned to `F[5,{1}]` (χ₁, the
  step-(iii-b).3 pending item) via `/feynarts`; the diagram set is structurally
  identical to the class-level step-1 census (4 diagrams: 2 tri + 2 box), with
  only the two external-neutralino `SumOver` factors dropping. `/formcalc reduce
  --gamma5 naive` succeeded on the χ₁-pinned 1PI core → `reduce_chi1/amp_reduced.m`
  (107 KB) carrying genuine symbolic PV heads (B0i×23, C0i×319, D0i×286).
  **γ₅ = naive is evidence-only; sign-off pending** (step-(iii-b).1: the W-boxes +
  chiral/pseudoscalar content argue for `hv`/`bmhv`).
- **All 505 distinct PV heads finite** by direct MathLink evaluation
  (`pv_eval.json`): PV integrals depend only on masses + momentum invariants, so
  they were evaluated decoupled from the (non-applicable) nucleon matching —
  505/505 finite complex numbers at the benchmark point (χ₁=132.69 GeV). This
  demonstrates the SD 1PI core's loop integrals are well-defined and numerically
  evaluable; it is **finiteness evidence only** (no effective coupling, no σ).
- **`/looptools eval` blocked on 2HDM+a hardcoding.** `run_eval.wls` is
  specialised to the 2HDM+a (`TwoHdmAfix`) model: it looks masses up by 2HDM+a
  PDG codes (all `Missing` against the SD SLHA) and substitutes 2HDM+a couplings
  (`gchi, lamP, lam1..8, vu, vd, ZA/ZH/ZP`, all `$Failed`), and its scalar
  projection assumes Dirac DM + up-quark. The SD amplitude therefore cannot be
  consumed — the core step-3 gap, not a physics failure of the SD amplitude.
  **Now a guided error, not a crash:** this tranche hardened the two looptools
  loud-failure gaps (STEP2.md friction 2) — a missing/empty/garbage
  `eval_output.json` yields a structured `LOOPTOOLS_EVAL_NO_OUTPUT` blocker
  (never a raw `JSONDecodeError`), and `run_eval.wls` now detects unbound
  `$Failed`/`Missing` bindings **before** the MathLink call and names the 20
  unbound SD symbols in `context.unbound_symbols` (verified on the real SD point:
  `run_eval.wls` exits 3 with the `UNBOUND-MODEL-PARAMETERS` marker → the wrapper
  emits `LOOPTOOLS_EVAL_NO_OUTPUT` cause `unbound_model_parameters`).

**Step-3 design — settled, see [`STEP3-DESIGN.md`](STEP3-DESIGN.md)** (reviewed;
γ₅ = naive signed off with the refuse-to-lie guard, 4-diagram 1PI-core scope,
chain-level projection, parallel `run_eval_sd.wls`, three-anchor validation).
The build order and per-decision rationale live there; the list below is the
capability checklist it elaborates.

**What step 3 needs** (from `STEP2.md` "What step 3 needs" — the SD eval layer
that generalises `run_eval.wls` off `TwoHdmAfix`):

1. **SD symbol-binding map.** Bind SD SLHA blocks to amplitude symbols:
   `ZNMIX→ZN`, `UMMIX/UPMIX→UM/UP`, `UDLMIX/UDRMIX→ZDL/ZDR`, `Yu/Yd`,
   `PHASES→PhaseFS`, `GAUGE→g1/g2`, `HMIX`, plus `yh1/yh2` (SD Higgs-portal
   Yukawas). The SD SLHA already carries all these blocks. Mediator/scalar masses
   by **SD** PDG codes (h=25, χ±=9984071, χ₁=9958431, …), plus a decision on the
   eaten-Goldstone (Ah/Hp) mass/gauge treatment. (The new loud-failure guard
   already enumerates exactly which symbols this map must cover.)
2. **Majorana-χ + down-quark scalar projection.** The current projection is
   Dirac + up-quark; SD is a Majorana χ scattering off a down-type quark.
3. **SD nucleon matching.** Through the SD Higgs sector (`yh1/yh2`,
   down-type-quark coupling), replacing the `ZH/vu/vd` 2HDM+a formula.
4. **`SumOver` handling.** Handle the internal generation/eigenstate sums
   properly rather than pinning gen-1 (gen-1 pinning was used only for the
   finiteness scan).
5. **γ₅ scheme sign-off.** Settled → **naive (NDR)**, see `STEP3-DESIGN.md`
   Decision 1. `/formcalc` now hard-errors on `hv`/`bmhv`/`larin`
   (`FORMCALC_G5_SCHEME_UNIMPLEMENTED`) since no scheme is forwarded to
   CalcFeynAmp; the naive == FormCalc-9.10-NDR-default equivalence is recorded in
   the sidecar caveats (refuse-to-lie guard, R1).

### Step-3 build-order item 3 — `run_eval_sd.wls` (PARTIAL, honest)

Landed (`scripts/run_eval_sd.wls`, `sd_projection.wl`, `run_projection_sd.wls`;
`run_looptools.py` `--model {2hdma|singlet_doublet}` dispatch):

- **SD binding map — DONE & runtime-verified.** All ~27 SD amplitude symbols bind
  from the real SD SPheno spectrum (no `UNBOUND-MODEL-PARAMETERS` fired on the
  canonical point). Two `[VERIFY]` flags resolved against the SLHA: **ZN =
  ZNMIX + I·IMZNMIX** (the SD neutralino mixing is genuinely complex — binding
  from `ZNMIX` alone would zero χ₂'s coupling, whose `ZNMIX` row is 0 but
  `IMZNMIX` row is not); **yh1/yh2 from `BSMPARAMS`(3,4)** (running values at Q,
  consistent with Yu/Yd/GAUGE), MINPAR(3,4) documented fallback. Goldstones
  `MassAh→m_Z`, `MassHp→m_W` (Feynman gauge).
- **Majorana-χ + down-quark projection — REWORKED (PR #31 review F1/F2 resolved,
  branch `sd-projection-solve`).** The PR #31 hard-coded block map
  (`{F1..F4}`=scalar, `{F5..F8}`=twist-2) was proven **wrong** against the real
  Abbr[] table (the PR #32 self-contained artifact): the real SD chains are
  F1,F4=χ-scalar; F2,F3=quark-scalar; F13,F14=χ-vector; F15,F16=quark-vector
  (twist-2); F5–F12,F17,F18=mixed Fierz — 18 chains, not 16. Moreover the real
  amplitude is **bilinear** in the chains (F_a·F_b products), so PR #31's linear
  `Coefficient[]` extraction was structurally invalid (silently non-numeric on
  live data). Replaced by the Decision-3.2 **numerical spinor-basis solve**:
  every chain is read from its actual WeylChain definition, evaluated on an
  explicit off-axis spinor basis (80 configs), and least-squares-solved against
  reference operator matrix elements {scalar, quark-twist-2, χ-vector
  (Majorana diagnostic)}. **Completeness guard** (F2): the fit residual
  ‖M − Σ c_op·O_op‖/‖M‖ must be < 1e-4 or the projection fails loudly
  (`SD-PROJECTION-INCOMPLETE`); structurally unrecognized chains fail-fast
  (`UNRECOGNIZED-CHAIN-STRUCTURE`, named). Per-coefficient setdelta/setmudim
  UV-residue guard re-projects the full amplitude (Decision 2, load-bearing).
- **R2 cross-talk fixture — REBUILT non-circularly** (Decision 6 R2): fixtures
  now carry REAL FormCalc WeylChain definitions (verbatim from the SD artifact),
  bilinear amplitudes, and known content — pure-scalar (C_scalar=19),
  pure-twist-2 via F15/F16 (C_twist2=60; this fixture FAILS under the old block
  map by construction), mixed, and a red-first **adversarial** fixture with a
  deliberately unrecognizable rank-2 chain that must TRIP the loud guard.
- **Gated real SD eval on the self-contained artifact — first real execution of
  the projection path.** Exposed and fixed 3 root causes PR #31 could never
  reach (its guard fired earlier): (1) `evalTermCommon` left `Sum[body]`
  unevaluated for terms with no internal SumOver (held-rule leak, shared-include
  fix, 2HDM+a path unchanged); (2) external-generation `SumOver[i,3,External]`
  factors unhandled — now pinned to gen 1 (down) via the `override` seam,
  internal sums still exact; (3) `g3` (QCD coupling, used by the real amp's
  Subexpr) was never bound — now bound from `GAUGE:3`.
  **Outcome (real leg, canonical point): loud failure at the NEW completeness
  guard** — `SD-PROJECTION-INCOMPLETE completeness_rel_residual=0.995` (exit 3,
  no JSON). The projection path executed end-to-end on live data for the first
  time and the guard worked as designed: nothing ships. The residual is an
  **UNIDENTIFIED projection/kinematics artifact, not identified physics** (PR
  #33 adversarial review, falsifying this PR's earlier σ_SD interpretation):
  adding the exact axial-axial operator to the span moves the residual only
  0.99506 → 0.99154, and the full Fierz-complete parity-odd/tensor contraction
  set reaches only 0.98780 — no bilinear-squared operator set spans it, and the
  SI-diagonal content ALONE is un-spanned (0.980). Corroborating anomalies:
  ‖M‖ ≈ 1.4e28 vs a physically-normalised ~1e-7 expectation, with 105
  `lambda(p1,p2,p3) < 0, unphysical configuration` LoopTools warnings at the
  static point. Review hypothesis: a **kinematic inconsistency** — the PV
  coefficients c_i are frozen at the static point (S=(mχ+mq)², T=−1e-4 inside
  `mkNum`) while the chains are evaluated at v~0.3 off-axis configs, so
  M(config)=Σ c_static·F_offaxis is not a faithful matrix element at any single
  kinematic point (Decision 3.2 intends a leading static expansion; the
  implementation mixes v=0 coefficients with finite-v chains). The same solve
  recovers the clean R2 fixtures exactly (~1e-16), so the failure is specific
  to the real Mnum's construction, not the projector algebra.

**MANDATORY NEXT (before item 4 proceeds):** resolve the ‖M‖ scale anomaly and
the static-coefficient / off-axis-chain kinematic inconsistency (make the
projection kinematics self-consistent), then re-run the real leg. Item 4 must
NOT build on any interpretation of the current residual.

WIP / next (item 4, blocked on the above): per-flavor (u,d,s) external runs,
C^(1)/C^(2) twist-2 moment split, driver-side twist-2 + 2/27-gluon nucleon
matching through the SD Higgs sector → σ_SI, anchors (a)–(e), Rξ variation.

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
