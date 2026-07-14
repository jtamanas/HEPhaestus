> Settled design for step 3 of [LOOP-FLOOR-ROADMAP.md](LOOP-FLOOR-ROADMAP.md). The four `[VERIFY]` flags below are the implementer's checklist.

# STEP-3 DESIGN — SD one-loop σ_SI floor: eval layer + matching (reviewed design)

Reviewer: physics-design review agent (Fable). Inputs: LOOP-FLOOR-ROADMAP.md,
loopset-step1/{STEP1,DIAGRAM-CENSUS}.md, loopset-step2/STEP2.md,
looptools SKILL.md + run_eval.wls + match_nucleon.py, formcalc
run_calcfeynamp.wls, eval/.../cross_sections/si_one_loop.py + loop_functions/.
Every claim is cited to a file or paper, or flagged `[VERIFY]`.

---

## Decision 1 — γ5 scheme: **naive anticommuting γ5 (NDR), signed off for the floor**, with two mandatory guards

**Decision.** Reduce the physical floor with `--gamma5 naive`. Do **not**
attempt HV/BMHV in FormCalc 9.10.

**Why this is defensible physics, not convenience:**

1. **The amplitude set contains no closed fermion loops.** The 1PI core
   (DIAGRAM-CENSUS.md, IRR-1..4) consists of open fermion chains only: the
   triangles dress the external χ line (χ/χ± in loop, IRR-2) or the external
   quark line (IRR-1); the boxes are two open chains (χ/χ± line, u/d line)
   joined by W/H±/Z/h exchange. The γ5 scheme ambiguity that NDR cannot handle
   is the trace of γ5 with ≥4 γ-matrices in a **closed** loop (the
   anomaly-sensitive configuration); open chains evaluated between external
   spinors are NDR-safe at one loop up to evanescent (O(ε)·finite) terms that
   enter only at two loops. Standard reference: Jezabek/Larin discussions of
   NDR validity; the practical criterion (no odd-γ5 closed traces) is checkable
   statically. `[VERIFY: run a static scan of loop1_irr_chi1/FeynAmpList.m
   confirming every fermion loop line attaches to external legs — extend
   gamma5_static_check.wls to classify closed vs open chains.]`
2. **The target operators are parity-even** (scalar χ̄χ q̄q, twist-2, gluon —
   si_one_loop.py:14-18). Scheme-dependent γ5-odd pieces project out of the SI
   floor; they matter for σ_SD, which is out of scope (SKILL.md "σ_SD null in v1").
3. **Hisano-style precedent.** The Hisano–Ishiwata–Nagata EW box/triangle DD
   calculations (arXiv:1004.4090, 1104.0228), which this floor reproduces, are
   done in ordinary dim. reg. with anticommuting γ5; the paper's Eq. (34)-(37)
   loop functions (mirrored in loop_functions/box_integrals.py) come from that
   lineage. A factor-few floor validation does not resolve scheme differences,
   which are parametrically α/π corrections to the floor itself.
4. **FormCalc 9.10 reality.** FormCalc/FORM natively computes with
   anticommuting γ5 (NDR); it has no complete BMHV implementation. More
   importantly, **the toolkit's `--gamma5 hv|bmhv|larin` flags are cosmetic
   today**: `run_formcalc.py:48-49` accepts them and they enter the cache key,
   but `run_calcfeynamp.wls:120-123` invokes `CalcFeynAmp` with only
   `FermionChains` and `Dimension` — the scheme is never forwarded. Every
   reduction so far, whatever the flag, was naive-γ5.

**Mandatory guards (the caveat trail):**

- **G1a (refuse-to-lie):** until a scheme is actually wired through,
  `run_formcalc.py` must hard-error on `--gamma5 hv|bmhv|larin`
  (`FORMCALC_G5_SCHEME_UNIMPLEMENTED`) instead of silently producing a
  naive-γ5 result stamped "hv". This is the repo's silent-failures-loud norm
  (cf. STEP1.md Blocker B) applied to physics metadata.
- **G1b (chirality anchor):** one W-box coefficient must be checked against the
  hand analytic Hisano g₂⁴ structure (sign and magnitude) at the benchmark
  point before any scan — a wrong PL/PR ordering is exactly the error naive γ5
  cannot self-detect. Folded into Decision 5 anchor (b).

---

## Decision 2 — Reduction scope: **4-diagram 1PI core only**, consistency enforced numerically, not assumed

**Decision.** The floor is computed from the 1PI core (IRR-2 triangle +
IRR-3/IRR-4 boxes; IRR-1 retained in the reduction but expected to project out
— see Decision 3). The 11 tadpole/self-energy/WF topologies of the 15-topology
set are **dropped**, under these stated conditions:

- **Scheme under which dropping is consistent:** on-shell renormalization of
  masses and fields (unit-residue, diagonal on-shell external legs) plus a
  tadpole scheme in which tadpole diagrams are cancelled point-by-point by the
  tadpole counterterm. Under on-shell field renormalization the off-diagonal
  χ1→χj external-leg self-energy followed by the tree h χj χ1 vertex — the one
  reducible class that is *not* proportional to the vanishing tree h χ1 χ1
  coupling and is parametrically the same order as IRR-2 — is absorbed by the
  LSZ/on-shell conditions. Mediator-leg self-energies and tadpoles renormalize
  the tree exchange and vanish with it at the blind spot
  (DIAGRAM-CENSUS.md:98-99).
- **The catch, stated honestly:** the loop-induced hχχ vertex (IRR-2) can be
  UV-divergent in general, with the divergence absorbed by the coupling/mixing
  counterterm. At the blind spot the *tree* coupling vanishes but the
  *counterterm* need not, so "1PI core alone" is only consistent if the
  projected Wilson coefficients come out UV-finite at the blind spot.
  **Do not assert this — measure it.**
- **Enforcement (load-bearing, unlike 2HDM+a):** run_eval.wls:262-272 notes its
  setdelta/setmudim residue tests are trivially zero for the 2HDM+a triangle.
  For SD they must be load-bearing: the reduced core carries divergent B0i
  heads (11 distinct, STEP2.md), so the SD driver asserts, per projected
  coefficient (C_q, C^(2)_q, C_G-feeding pieces), setdelta-residue < 1e-10
  relative and setmudim-residue < 1e-6 relative. **A failure falsifies this
  scope decision loudly** (`LOOPTOOLS_AMPLITUDE_NONFINITE`) and mandates
  extending scope to the 15-topology set with explicit counterterms. This is
  the red-first test the roadmap norm (iv) requires.
- **Gauge:** amplitudes are generated in Feynman gauge with eaten Goldstones at
  m_Z/m_W (STEP2.md subtask 3). Keep that (it is what the FeynArts state
  produces); the boxes + loop-vertex at the blind spot form the
  Hisano gauge-invariant EW subset `[VERIFY: not proven for this model —
  mitigated by anchor (b) of Decision 5; a Rξ variation is deferred, declared
  in the sidecar as gauge_check: deferred, not silently stamped 0.0 as
  run_eval.wls:285 does today]`.

---

## Decision 3 — Operator basis, diagram→operator map, projection architecture

**Basis** (paper Eq. (9), already encoded in si_one_loop.py:33-99 — the
*decomposition* is reused, its pure-Python numerics retired per roadmap (iv)):

| Operator | Coefficient | Fed by | Nucleon piece |
|---|---|---|---|
| m_q χ̄χ q̄q (q=u,d,s) | C_q | IRR-2 triangle (via h exchange, all q universally) + IRR-3/4 boxes (per-flavor) | f_Tq |
| twist-2 q̄(γ∂)q (q=u,d,s,+c,b via PDFs) | C^(1)_q, C^(2)_q | IRR-3/4 boxes only | (3/4)(q(2)+q̄(2)) |
| α_s χ̄χ GG | C_G | heavy-quark (c,b,t) scalar C_Q via 2/27·f_TG (leading); full 2-loop gluon box out of scope | (2/27) f_TG |

**Reconciling amplitude census vs operator needs — per-flavor runs are
required.** The step-1/2 amplitude has external F[4] (down-type) only; F[3]
is internal (DIAGRAM-CENSUS.md:78-81). But the boxes' Wilson coefficients are
flavor-dependent (the W box for an external d has an internal u and weight
V_ud g₂⁴; for an external u it has an internal d; Z/h pieces differ by
couplings), so one down-quark run cannot supply C_u. **Decision: three
amplitude runs** — externals `F[3,{1}]` (u), `F[4,{1}]` (d), `F[4,{2}]` (s) —
each χ1-pinned, each through the same generate→reduce→eval chain. The IRR-2
triangle piece needs only one run (the loop-induced C_hχχ/m_h² is
quark-flavor-blind, same factorization as run_eval.wls:45-59) and the other
two runs cross-check it: extract C_hχχ from each flavor run and assert
agreement to <1e-6 relative (free consistency guard). c,b enter only via
twist-2 PDF moments and the 2/27 gluon matching at the nucleon level
(si_one_loop.py:91-96 pattern), not via new amplitude runs.

**Projection architecture — chain-coefficient level, in Mathematica, post-Get
of amp_reduced.m (the SD driver), NOT the 2HDM+a spin-summed collapse.** The
2HDM+a projection (run_eval.wls:30-44) substitutes rest-frame numbers for all
Weyl chains F1..F16 and spin-sums; at a single static point the scalar and
twist-2 operators are **degenerate** (both reduce to c-numbers ∝ m_χ m_q), so
that method cannot separate C_q from C^(2)_q — acceptable for 2HDM+a only
because boxes were excluded from f_N (run_eval.wls:61-65); fatal here because
the boxes ARE the floor. Instead:

1. FormCalc output is already organized as Σ_i c_i(S,T,U; PV) · Mat[F_i];
   keep the c_i **symbolic in the chains**, substitute the numeric point +
   PV evaluation into the c_i only.
2. Identify the scalar operator with the (F-chain) combination ∝ ū_χu_χ ūqu_q
   and twist-2 with the kslash-inserted chains (F5–F8 and momentum-dependent
   pieces), expanding to leading order in the DM–quark relative momentum
   (static expansion around T=−TEPS, S=(m_χ+m_q)², per run_eval.wls:24 and
   pv_eval.m kinematics). Numerically this is a solve: evaluate the amplitude
   on a small set of independent chain-value assignments (basis vectors in
   F-space) and invert for the operator coefficients — cheap, and it reuses
   the validated evalTerm/SumOver machinery (run_eval.wls:225-232).
3. Nucleon matching stays in the driver following the run_eval.wls:247-259
   pattern, generalized to the SD Higgs sector (single h, y_h1/y_h2 portal —
   replaces ZH/vu/vd), then σ via the untouched match_nucleon.py coherent
   formula. Extend the driver-side matching with the twist-2 and 2/27-gluon
   contractions (constants already exist: Q2_*, QBAR2_*, F_TG_P in
   eval/.../constants.py, per roadmap (iii).3).
4. **Majorana χ:** FeynArts/FormCalc handle Majorana fermion flow natively
   (Denner et al. rules); the crossed box IRR-4 is that physics and is already
   in the amplitude — the projection must NOT add symmetry factors by hand.
   The Dirac-specific normalization in the 2HDM+a projection (F1=F4=m_χ etc.)
   is re-derived for self-conjugate χ (χ̄χ normalization differs by the
   standard factor-2 convention). `[VERIFY: fixture test in Decision 6 R2
   catches a wrong factor here.]`
5. **SumOver:** internal χ-eigenstate and generation sums evaluated exactly
   via the existing iterator machinery (run_eval.wls:227-229). No gen-1
   pinning (that was step-2 finiteness evidence only, STEP2.md:107-111).

---

## Decision 4 — Symbol binding: **parallel `run_eval_sd.wls` + shared common include; binding map as data inside it**

**Decision.** Do not make run_eval.wls model-generic. Create
`scripts/run_eval_sd.wls` alongside it, and factor the genuinely model-blind
plumbing (arg parsing, FormCalc/LoopTools Install + C0i self-test
(run_eval.wls:100-117), unbound-binding guard scaffold (158-192), evalTerm/
SumOver engine, JSON emission) into a shared `run_eval_common.wl` include.

**Why parallel, not generic:** the model-specific surface is not just symbol
names — it is the projection physics (Dirac+up vs Majorana+down, Decision 3),
the Higgs-sector nucleon matching, and the diagnostic set. A "data-driven
binding spec" would generalize the easy 30% and leave the hard 70% branchy.
Meanwhile the 2HDM+a driver is the toolkit's only EW-anchor-validated chain
(SKILL.md:244-254); its golden test pins bytes-level behavior. Blast radius of
editing it: the flagship validation. Blast radius of a parallel driver: zero.
Drift risk is contained by making the common include real (shared code, not
copy-paste) — drift in shared plumbing then breaks both test suites loudly.
`run_looptools.py` dispatches on a `--model {2hdma|singlet_doublet}` flag (or
meta-derived model id), defaulting to the current behavior.

**SD binding map** (SLHA blocks → amplitude symbols; from STEP2.md:131-141 —
the SD SLHA `runs/2026-07-11T1554Z-aee644cc/SPheno.spc` carries all blocks):

| Amplitude symbol | Source |
|---|---|
| MassFChi[1..3] | SD PDG masses (χ1 = 9958431; χ2, χ3 codes from ParticleNamesFeynArts.dat) |
| MassFChiM | PDG 9984071 (χ±) |
| Masshh | PDG 25 |
| MassAh, MassHp (eaten Goldstones) | m_Z (23), m_W (24) — Feynman gauge, matching generation (STEP2.md:58-59) |
| MassVWp, MassVZ | PDG 24, 23 |
| MassFu[1..3], MassFd[1..3] | PDG 2,4,6 / 1,3,5; light quarks from the PDG defaults already in run_eval.wls:78 if absent from SLHA |
| ZN | ZNMIX block (3×3 neutralino mixing; check SPheno phase convention vs FeynArts state `[VERIFY]`) |
| UM, UP | UMMIX / UPMIX |
| ZDL, ZDR | UDLMIX / UDRMIX (≈ identity; bind, don't assume) |
| Yu, Yd | Yu / Yd blocks |
| yh1, yh2 | the SD portal-Yukawa block in the SPheno output (block name per SARAH SingletDoublet output `[VERIFY exact block name from the SLHA]`) |
| g1, g2 | GAUGE block |
| PhaseFS | PHASES block |
| vd/vu analogue | HMIX (SM vev) |

The existing unbound-parameter guard pattern (exit 3 +
`UNBOUND-MODEL-PARAMETERS`, run_eval.wls:185-192) is reused verbatim with the
SD bindGuard list — the guard the step-2 tranche added already enumerates
exactly the coverage this map must achieve (roadmap iii-c). The 20-name list
from the SD run is the 2HDM+a-side complement; the table above is its SD-side
inverse and is checked at runtime, not trusted from this document.

---

## Decision 5 — Validation plan: three anchors + two structural checks, quantitative bands

Acceptance is staged; the floor is `sigma_provisional: true` until (a)–(c) all
pass (mirrors the 2HDM+a anchor discipline, SKILL.md:244-254).

- **(a) Fig. 1 of arXiv:2506.19062** (primary): reproduce the one-loop floor
  curve at ≥3 masses spanning the plotted range (digitized curve). Band:
  **within ×3** of the paper curve pointwise. (The 2HDM+a anchor band is
  ×3–5; the paper curve is this exact model, so the tighter end applies.)
- **(b) Hisano pure-doublet limit** (independent lineage): at MS→large,
  θ-decoupled (pure-doublet/Higgsino-like χ), compare σ_SI against
  Hisano–Ishiwata–Nagata EW box+triangle results (arXiv:1004.4090/1104.0228,
  O(few×10⁻⁴⁹–10⁻⁴⁸ cm²) `[VERIFY exact number at chosen m_χ from the paper
  table]`). Band: **within ×5** (different σ-term inputs + NLO QCD in their
  later works justify the looser band). This anchor is also the γ5/chirality
  sign check (Decision 1, G1b): the interference sign between triangle and box
  pieces must match. [AMENDMENT5R1 R5(e): G1b must be evaluated on ROTATED
  sector readings — the unrotated triangle value is a crossing artifact
  (regression pin only), so an unrotated-lineage interference sign would
  compare an artifact against physics.]
- **(c) Blind-spot continuity + tree-dominance crossover:** on a θ scan
  through the blind spot (repo benchmark θ=−0.152, hephaestus memory / merged
  PR #2): tree σ_SI must dip ≥4 orders below its off-blind-spot value while
  total (tree+loop) σ_SI stays finite and **varies by <50%** across the dip
  (the loop floor is locally θ-smooth); far from the blind spot, tree must
  dominate loop by the expected (16π²)² parametric.
- **(d) Decoupling (structural):** with fixed singlet mass, raise MPsi over
  one decade; the floor must fall monotonically and vanish in the
  mixing→0 limit — fit the power law and assert the exponent is negative and
  stable `[VERIFY expected exponent against paper §結果 / Hisano scaling
  before hard-coding a value]`. Catches sign/normalization errors that a
  single-point anchor cannot.
- **(e) Internal (per point, load-bearing):** setdelta/setmudim residues per
  projected coefficient (Decision 2 bands); TEPS-independence of every
  coefficient across T=−1e-4..−1e2 (run_eval.wls:24-28 pattern); C_hχχ
  cross-flavor agreement <1e-6 (Decision 3); 505-head finiteness regression
  vs pv_eval.json.

Red-first, per roadmap (iv): each of (a)–(e) lands as a failing gated test
(`HEPPH_RUN_WOLFRAM_TESTS=1`) before the driver work that turns it green.

---

## Decision 6 — Risk register: the 3 likeliest wrong-but-plausible floors

- **R1 — γ5/chirality metadata lies.** The scheme flag is not forwarded to
  CalcFeynAmp (run_calcfeynamp.wls:120-123): a future run stamped `hv` would
  be naive-γ5 with a validated-looking sidecar, and a PL/PR sign slip in the W
  box flips triangle-box interference — a factor-few-wrong floor with perfect
  finiteness diagnostics. **Guard:** G1a hard-error on unimplemented schemes +
  anchor (b) sign check as a committed test, not a one-off.
- **R2 — projection cross-talk (scalar ↔ twist-2).** A static-point spin-summed
  projection (the 2HDM+a shortcut) silently folds twist-2 into the scalar
  coefficient; the floor comes out O(1) wrong and still passes finiteness,
  UV, and TEPS checks. **Guard:** a fixture test injecting two synthetic
  amp_reduced.m files with known pure-scalar and pure-twist-2 content
  (hand-built chains); the projector must recover each coefficient to <1% with
  cross-talk <1% — committed as a Tier-2 test (no Wolfram tools needed if the
  fixture is pre-reduced; else Tier-3 gated). Majorana normalization (Decision
  3.4) is verified by the same fixture.
- **R3 — SumOver mishandling.** Dropping internal χ2/χ3 eigenstate sums
  (step-2 pinned gen-1) or double counting a generation yields a finite,
  smooth, wrong floor — the loop-induced hχχ vertex is typically *dominated*
  by heavier eigenstates in the loop. **Guard:** (i) an accounting assert —
  the number of evaluated terms equals the product of SumOver ranges per term
  (evalTerm already knows the iterators, run_eval.wls:227); (ii) a
  pinned-vs-summed comparison at the benchmark that must differ by >10%
  (if pinning changes nothing, the sums were silently dropped).

Honorable mention (tracked, not top-3): Goldstone/gauge treatment — wrong
Ah/Hp masses relative to the Feynman-gauge generation would be silent;
mitigated by binding them to m_Z/m_W in the bindGuard (Decision 4) so a
mismatch is a loud unbound/wrong-value failure, and by anchor (b).

---

## Build order (one owner per stage)

1. G1a refuse-to-lie fix + static closed-chain γ5 check (small, formcalc skill).
2. `run_eval_common.wl` extraction + byte-identical 2HDM+a golden re-run
   (protects the validated chain before anything SD lands).
3. `run_eval_sd.wls`: binding map + Majorana/down projection + R2 fixture test
   (red first).
4. Per-flavor runs (u,d,s) + driver-side twist-2/gluon nucleon matching +
   internal checks (e).
5. Anchors (a)–(d) as gated tests; only then a θ/mass scan and the Fig. 1
   overlay, `sigma_provisional` until all green.
