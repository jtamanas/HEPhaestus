# DESIGN-ITEM4 — Box treatment + per-flavor floor assembly (STEP3-DESIGN amendment)

Reviewer: physics-design review agent (Fable), Jul 2026. Amends STEP3-DESIGN.md
after the verified item-3 diagnosis (kinematics-invest/FINDINGS.md +
kinvest-verify/VERIFY.md, both under the c703354a job scratch): the 0.995
completeness residual / ‖M‖~1.4e28 is a **Gram-determinant spurious pole in the
PV tensor reduction of the all-massive boxes at the degenerate DD point**
(scalar dd0 finite and flat; dd11/dd22/dd33 ∝ 1/T; zero massless internal box
lines — VERIFY.md V_gram table). Decisions below are decisions. Unchanged
STEP3-DESIGN decisions (γ5=naive+G1a/G1b, 1PI-core scope, parallel driver,
anchor set 5a–e) are not restated.

---

## Decision A1 — Box treatment: **(a) symbolic small-momentum expansion, with a
head-level numeric cross-check; NOT extrapolation**

**Decision.** Adopt the Hisano–Ishiwata–Nagata-lineage small-momentum (DD-limit)
expansion, realized as a **symbolic expansion of the FormCalc box amplitude
inside Mathematica**, producing operator coefficients multiplying **scalar-class
loop functions only** (B0/C0/D0 and their mass-derivatives), which LoopTools
then evaluates. Option (b) — numeric D0i at non-degenerate kinematics +
Richardson extrapolation — is **rejected as the production path** and demoted to
a per-head validation role (A1-V below).

**Why (a), against the Gram evidence:**
1. The disease is in the numeric tensor *reduction*, not the integrals: dd0 is
   flat to 8 digits across T=−1e-4..−100 while dd11 rides 1/Gram(∝T) with
   constant mantissa over 6 decades and **no plateau** (VERIFY.md). Any
   extrapolation toward the DD point therefore extrapolates along a diverging
   quantity; there is nothing to Richardson against.
2. The cancellation is numerically unpayable. The assembled box coefficient
   scale is ~1e28 at T=−1e-4 and still ~1e22 at T=−100 (FINDINGS.md E2), vs a
   physical target ~1e-7: recovering the finite amplitude from the tensor-head
   assembly requires 25–35 digits of cancellation between coefficients and the
   compensating chain kinematics — beyond double precision at *every* T in the
   sweep, so (b) fails even off the degenerate point.
3. In the DD limit the external momenta span a **rank-1** space (all four ∝
   u=(1,0,0,0)), so the tensor decomposition on {g^μν, u^μu^ν} has a
   non-degenerate 1×1 "Gram" (u²=1). The 1/Gram of the standard 3-momentum PV
   basis is an artifact of decomposing on a basis that collapses; done
   symbolically on the rank-1 basis the cancellation never has to happen
   numerically. This is precisely the reorganisation Hisano et al.
   (arXiv:1004.4090, 1104.0228) perform before quoting finite loop functions.

**Concrete realization.** New Wolfram module `sd_dd_expansion.wl` (sibling of
`sd_projection.wl`, loaded by `run_eval_sd.wls`):
1. Ingest the box terms {1,4,8,10} of `amp_reduced.m` (the D0i-carrying terms;
   triangle terms 2,3,5,6,7,9 pass through untouched — triangle-only
   C_scalar=−1.28e-7 is already stable, FINDINGS.md E1).
2. Substitute the DD kinematics symbolically (k1=k3, k2=k4, both ∝ u; T→0,
   S→(mχ+mq)²) **at the tensor level**: rewrite every tensor D0i/C0i head via
   the rank-1 Lorentz decomposition into scalar integrals D0/C0/B0 at the DD
   masses and their derivatives ∂D0/∂m_i², ∂D0/∂S. `[VERIFY: the rank-1
   reduction must be derived once, symbolically, in the module's test — check
   it reproduces LoopTools' own Dget tensor components at 3 non-degenerate
   points, see A1-V. Confirm whether O(v) terms are needed for the twist-2
   coefficients — they are (twist-2 is the O(v) structure): expand to first
   subleading order in the DM–quark relative momentum, not strictly v=0.]`
3. Evaluate the resulting scalar heads via **LoopTools MathLink** (D0, C0, B0 —
   standard, stable: dd0 evidence). Mass/invariant derivatives are evaluated as
   central finite differences of the *scalar* integrals in the mass arguments
   (masses do not enter the momentum Gram matrix; step-halving convergence
   check required, tolerance 1e-6 relative, loud failure
   `SD-DD-DERIVATIVE-NONCONVERGENT`).
4. Structural guard: after expansion, assert the evaluable amplitude contains
   **no tensor D0i/C0i heads** (only scalar-class calls + finite differences);
   any survivor → loud `SD-DD-EXPANSION-INCOMPLETE`, exit 3.

**A1-V — validation that proves the choice (committed, gated
`HEPPH_RUN_WOLFRAM_TESTS=1`):**
- **Head-level (a)-vs-(b) cross-check:** for each distinct box mass signature
  (the χ±/W/W signature at minimum; all 4 box terms' signatures ideally), the
  expansion's prediction for the *tensor components* must agree with LoopTools'
  direct Dget/D0i at **3 non-degenerate kinematic points** (|T| ∈ {1, 10, 100}
  GeV², Gram = O(1), where both sides are stable) to **1e-6 relative** — same
  integrals, so tool-precision agreement, not a physics band.
- **Triangle continuity:** the full (triangle + expanded-box) run's
  triangle-only C_scalar must reproduce −1.28e-7 (the item-3 value) to 1e-10
  relative when boxes are switched off — proves the expansion touched nothing
  it shouldn't.

## Decision A2 — Norms ruling: transcribed closed-form loop functions

**Ruling (the crux):** transcribing published closed-form loop functions
(Hisano 1104.0228 gH/gAV/gT1/gT2, pure-doublet W-box functions) into the
**production path is FORBIDDEN** — it is exactly the "reimplemented physics"
the norm bans (`looptools/SKILL.md:18` "reimplements no physics"; the retired
`loop_functions/passarino_veltman.py` was killed for precisely this, roadmap
§(iv)). A number produced by a transcribed gH is untraceable to a tool.

Transcribing them into the **validation/anchor path is SANCTIONED** — that is
the existing analytic-anchor pattern (the 2HDM+a C_hχχ=−7.57e-4 vs analytic
−5.41e-4 anchor, SKILL.md:244-254). Placement: under
`eval/2506.19062_wimps_blind_spots/benchmarks/` (or `loop_functions/`, which is
already declared reference/cross-check-only), imported **only** by gated anchor
tests, never by `run_eval_sd.wls` or anything in `plugins/`. Each transcription
cites paper + equation number in-line.

The A1 symbolic expansion itself does **not** violate the norm: it manipulates
FormCalc's own amplitude artifact (amplitude algebra = FormCalc's domain, done
on FormCalc's output in the same Mathematica session) and delegates every
integral *evaluation* to LoopTools. The boundary: we may reorganise *which*
LoopTools calls are made; we may not replace a LoopTools evaluation with a
hand-coded number.

## Decision A3 — Where the expansion lives

**Decision: eval-side module + persisted sidecar artifact; no new pipeline
stage.** `plugins/hep-ph-toolkit/skills/looptools/scripts/sd_dd_expansion.wl`,
loaded by `run_eval_sd.wls` next to `sd_projection.wl`. No new step between
/formcalc reduce and /looptools eval: the artifact chain stays
`FeynAmpList.m → amp_reduced.m → scattering/v1`, satisfying "every number
traced to a tool artifact" (roadmap §iv) because the driver **persists the
expanded amplitude** as `amp_dd.m` beside `eval_output.json` (wrapped
association incl. expansion metadata: per-term head census before/after, O(v)
order, derivative step sizes) — reviewable, cacheable, but not a new interface.

Byte-untouched: `run_eval.wls`, `run_eval_common.wl` (if a shared-plumbing edit
proves unavoidable, the 2HDM+a golden test must pass byte-identically — same
bar as STEP3-DESIGN Decision 4), `match_nucleon.py` core, everything 2HDM+a.
`sd_projection.wl` changes only additively (A5: second twist-2 reference op).

## Decision A4 — Per-flavor runs + gluon C_G

**Confirmed: exactly 3 external runs** — u = `F[3,{1}]`, d = `F[4,{1}]`,
s = `F[4,{2}]` (STEP3-DESIGN Decision 3), each χ1-pinned through the same
generate→reduce chain. **One driver invocation consumes all three**: extend
`run_eval_sd.wls` (via `run_looptools.py --model singlet_doublet`) to accept 3
amp paths and loop internally — nucleon matching needs all flavors at once and
stays driver-side (Decision 3.3); one Wolfram session, one output artifact.
Flavor-universal sharing: the IRR-2 triangle coefficient C_hχχ/m_h² is
extracted per run and asserted equal across flavors to <1e-6 relative
(STEP3-DESIGN's free consistency guard, now load-bearing).

**Gluon C_G — reconciliation.** The census contains **no closed heavy-quark
loops feeding C_G**: the SD model has no colored BSM states, and the 1PI core's
quark-side triangles (IRR-1) are external-light-quark line dressings, not
c/b/t loops. The c,b,t "triangle" content is the **SM matching**
h → Q̄Q → gg, which is the standard SVZ heavy-quark theorem and is applied at
the **nucleon level**, not diagram level:
  C_G-side contribution to f_N = (2/27) f_TG · Σ_{Q=c,b,t} C_Q,
with C_Q = the flavor-universal h-exchange triangle coefficient (the m_q-
normalized scalar operator makes C_Q flavor-blind — same C_hχχ/m_h² as light
quarks). No heavy-flavor external runs. **Declared out of scope (sidecar
caveat, not silence):** the two-loop W-box gluon contribution (Hisano
1104.0228 §gluon) — parametrically α_s/π × box, inside the ×3–5 anchor bands;
and external-b/c box twist-2 pieces beyond PDF moments. `[VERIFY: paper
2506.19062's own C_G prescription — if their Fig. 1 includes the two-loop
gluon box, note it when judging the ×3 band.]`

## Decision A5 — Nucleon matching extension

**Formula set** (Hisano-lineage; m_q-normalized scalar operators C_q for
m_q χ̄χ q̄q, twist-2 C_q^(1), C_q^(2); all per-nucleon N=p,n):

  f_N/m_N = Σ_{q=u,d,s} f_Tq^N C_q
          + (2/27) f_TG^N Σ_{Q=c,b,t} C_Q
          + (3/4) m_χ Σ_{q=u,d,s,c,b} [q^N(2) + q̄^N(2)] (C_q^(1) + C_q^(2))

  σ_SI^N = (4/π) μ_N² f_N²   (μ_N = m_χ m_N/(m_χ+m_N))

`[VERIFY: the (3/4) m_χ (C^(1)+C^(2)) twist-2 contraction normalization against
Hisano et al. 1104.0228 Eqs. (6)–(8) exactly — the split between g^(1)/g^(2)
conventions differs across the lineage papers; pin one convention and cite the
equation in the code comment.]`

**What extends vs what is new:**
- `match_nucleon.py` — **byte-untouched.** It takes f_p, f_n (GeV⁻²) and owns
  only (4/π)μ²f²; the contraction above is driver-side per the run_eval.wls
  :247-259 pattern (its module docstring says exactly this division).
- `run_eval_sd.wls` — new driver-side contraction block: form-factor preset
  table extended with the twist-2 moments (values transcribed from
  `eval/.../constants.py` Q2_*, QBAR2_*, F_TG_P with citations — these are
  measured data, not physics reimplementation) → emits f_p, f_n and full
  σ_SI in a `scattering/v1`-compatible JSON (upgrading the current
  `looptools_sd_coefficients/v1` no-σ schema).
- `sd_projection.wl` — additive: a **second twist-2 reference operator** so
  C^(1) and C^(2) are separately resolved (they contract identically into f_N
  above but the split is needed for the anchor comparisons); requires the O(v)
  expansion order of A1 step 2.

**Guard placement (final):** per-coefficient UV/scale residue stays where it is
(`run_eval_sd.wls` post-projection, thresholds 1e-10/1e-6), now evaluated on
the expanded amplitude. The **Gram monitor** lives in two places only:
(i) the A1-V head-level cross-check (asserts Gram=O(1) at its 3 points);
(ii) a production assert that the evaluable amplitude carries **zero** numeric
tensor-reduction calls (`SD-DD-EXPANSION-INCOMPLETE`) — the production path
never computes near a Gram zero, so it monitors by construction, not by value.

## Decision A6 — Acceptance for the FIRST floor number (canonical point + 2 masses)

Internal (per point, all must pass, else no number ships):
- UV residue < 1e-10 rel, scale residue < 1e-6 rel per projected coefficient.
- Completeness residual **< 1e-4** ($completenessTol — now expected genuinely
  small since the 1e28 artifact is gone; if it lands in [1e-4, 1e-2] that is a
  finding, not a tolerance to loosen).
- A1-V head-level cross-check green (1e-6 rel at 3 non-degenerate points);
  triangle-continuity green (−1.28e-7 reproduced, 1e-10 rel).
- Velocity-stability: C_scalar, C_twist2 stable to <1% under sample-velocity
  scaling ε → ε/10 in `sd_projection.wl` (the E3 sweep, now required to PASS).
- C_hχχ cross-flavor agreement < 1e-6 rel; C_chi_vector ≈ 0 (Majorana
  diagnostic, < 1e-6 of C_scalar).

External anchors (STEP3-DESIGN Decision 5, bands unchanged):
- **Hisano pure-doublet limit** (MS→large): σ_SI vs 1004.4090/1104.0228
  pure-Higgsino EW value, O(few×10⁻⁴⁹–10⁻⁴⁸ cm²) `[VERIFY exact table value at
  the chosen m_χ]`, within **×5**; triangle–box interference **sign** must
  match (this is guard G1b).
- **Fig. 1 of 2506.19062**: floor within **×3** pointwise at ≥3 masses
  spanning the plotted range (canonical 132.69 GeV + 2 more).

**Provisional policy:** `sigma_provisional: true` on every emitted σ_SI until
STEP3-DESIGN 5(a)–(e) are ALL green (Fig. 1 overlay, Hisano limit, blind-spot
continuity θ-scan, decoupling power law, internal set). The first floor number
is a milestone, not a release; the flag drops only with the full anchor set.

## Decision A7 — Risk register refresh (top 3 of THIS plan)

- **A-R1 — expansion algebra error** (wrong rank-1 decomposition, dropped O(v)
  term that feeds twist-2, sign slip in a derivative): produces a finite,
  smooth, wrong floor with perfect UV diagnostics. **Guard:** A1-V head-level
  1e-6 cross-check vs LoopTools tensor components at non-degenerate points is a
  *committed gated test per box mass signature*, not a one-off; plus the
  Hisano-limit anchor (independent lineage).
- **A-R2 — velocity/kinematics contamination survives the fix**: coefficients
  are DD-limit but chains are still sampled at v~0.3 off-axis configs
  (`sd_projection.wl` $chiDirs), so O(v) chain content can leak scalar↔twist-2
  even with finite coefficients. **Guard:** the ε→ε/10 velocity-stability
  acceptance bar (A6) — a >1% drift is a loud stop; plus the R2 cross-talk
  fixture extended with a box-like (expanded-head) fixture.
- **A-R3 — heavy-quark/gluon double counting or omission**: summing u,d,s into
  the 2/27 gluon term (double count) or dropping a heavy flavor (omission)
  shifts f_N by O(10–30%) and passes every internal check. **Guard:** a
  Tier-2 contraction unit test with synthetic C's where f_N is hand-computable
  (asserts exactly {c,b,t} in the gluon sum, exactly {u,d,s} in f_Tq, exactly
  {u,d,s,c,b} in twist-2), committed red-first.

---

## Build order (delta to STEP3-DESIGN's; one owner per stage)
1. `sd_dd_expansion.wl` + A1-V head-level cross-check tests (red first).
2. Wire into `run_eval_sd.wls` (single-flavor d), re-run real leg: expect
   completeness < 1e-4 and finite C's; triangle-continuity test.
3. Per-flavor u,d,s runs + 3-amp driver invocation + cross-flavor guard.
4. Driver-side nucleon contraction (A5) + A-R3 unit test + scattering/v1
   emission (provisional).
5. Anchors: Hisano-limit transcription (A2 placement) + Fig. 1 overlay at 3
   masses; then the STEP3 5(c)/(d) scans.
