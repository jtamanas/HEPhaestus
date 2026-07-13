# DESIGN-ITEM4-AMENDMENT3 — retirement, production SI path, cancellation adjudication

Amends AMENDMENT2R1.md after PR #35 round 3 (head 5ac2fd1). Accepted as
established: rotation exactness 4.3e-16 (scale-relative); 256/256 rank, cond
6.1e3, identifiability 7.0e-13; completeness 3.12e-9 (named derivative dust,
worst contribution 9.6e-10); triangle fixture bit-identical; probeH crossing
symmetry — both Majorana crossings project ~0 scalar (−1.5e-14 / +5.5e-15,
opposite signs), the UNROTATED crossed pair projects the spurious −2.099e-7;
true C_scalar(d) = +1.66e-10 across three instruments; C_twist2 = 4.096e-9,
v-stable 3e-5; si_shift 100.1%; 3-op-on-rotated v-drift 10.4%; transfer
instrument honestly unmeasurable at v/10 (cond ~1/v² → 4.8e6, named refusal).

## Ruling 1 — 3-op fit RETIRED; full-basis is production; floor is twist-2 PLUS
gluon, not twist-2-only

**Retirement confirmed.** si_shift 100.1% fired the pre-registered clause; the
3-op fit is retired as the production SI extractor (it survives only as a
cross-instrument consistency probe). Production coefficients, per flavor:
- **C_scalar** = the full-basis (rotated-complete) fit's scalar⊗scalar
  coefficient, converted to the m_q-normalized O_S convention, at canonical v.
  New shipping guard replacing SD-SI-EXTRACTION-UNSTABLE: the three instruments
  (3-op-on-rotated, transfer R_S_S, forward R_S_S) must agree within
  max(1% relative, 6e-10 absolute — the rank-2 budget 3e-3 × the 2.1e-7
  triangle scale); else `SD-SI-CROSS-INSTRUMENT-DISAGREE`, Exit 3.
- **C_twist2** (C^(1), C^(2)) = the contracted twist-2 reference operators on
  the ROTATED amplitude (not the local dictionary — derivative content is out
  of local span by construction, per the ratified probe8 exemption).

**σ_SI propagation (replaces the C_scalar-dominated path).** The A5 contraction
stands verbatim, driver-side, `match_nucleon.py` byte-untouched:
f_N/m_N = Σ_{u,d,s} f_Tq C_q + (2/27) f_TG Σ_{c,b,t} C_Q
+ (3/4) m_χ Σ_q [q^N(2)+q̄^N(2)](C_q^(1)+C_q^(2)), with second moments at
**μ = m_Z**, Hisano 1104.0228 Eqs. (6)–(8) convention, values transcribed from
`eval/.../constants.py` (Q2_*, QBAR2_*, F_TG_*) with citations. The light-quark
scalar term uses the MEASURED C_q (≈0 is a value, not a zero by hand) with a
±6e-10 rank-2 band propagated into f_N. C_Q = the flavor-universal triangle
coefficient (A4) — NOT cancelled: its box partner is the two-loop gluon box,
declared out of scope. **Consequence: the floor is NOT twist-2-dominated by
default** — the gluon term carries full triangle strength (~1.28e-7 scale) and
is parametrically comparable to or larger than twist-2. Because the blind-spot
physics evidently cancels triangle against box in the light-quark sector, the
missing gluon-box partner is now the leading honesty caveat, no longer "inside
the anchor band": σ_SI ships as a TWO-VALUE BRACKET (with / without the C_G
term), sigma_provisional on both, until the Hisano pure-doublet anchor
adjudicates. A single unbracketed floor number before then is forbidden.

## Ruling 2 — Trigger (b) MOOT with its instrument; per-config kinematics stays
closed; replacement stability bar pre-registered

The 10.4% drift is a RELATIVE bar on a noise-scale coefficient measured by a
retired instrument: 10.4% of 1.66e-10 is 1.7e-11 absolute — below the rank-2
band and irrelevant to f_N. A trigger written when C_scalar was expected
O(1e-7) does not survive its anchor's retirement; the transfer instrument's
v/10 refusal is honest, not a failure. **Per-config kinematics does NOT
reopen.** Replacement trigger, pre-registered: it reopens if any production
coefficient contributing > 1% of |f_N| drifts > 1% relative under a velocity
change at which the instrument's own conditioning guards are green (cond <
1e4). Measured today: C_twist2 (the dominant measurable) v-stable to 3e-5 →
green. C_scalar is additionally bounded ABSOLUTELY: |ΔC_scalar| under any
green-guarded v change must stay < 6e-10, else reopen.

## Ruling 3 — Cancellation conditionally PHYSICAL; the STOP clause is
superseded; off-blind-spot falsifier pre-registered as the gate

The old "|C_scalar| < 1e-8 = construction error, STOP" was anchored on
−2.10e-7, now measured to be the instrument artifact; a clause cannot outlive
its anchor. Physics re-adjudication: at a blind spot the tree scalar coupling
cancels by parameter choice — the paper's own theme — and the measured
triangle-vs-box cancellation (to 7.9e-4, within the 3e-3 rank-2 noise of exact)
is credible as the loop-level continuation of that same structure, with the
crossing-symmetry sign agreement and three-instrument consistency as supporting
evidence. But an instrument that wrongly annihilates scalar content everywhere
would pass every one of those checks; only θ-dependence discriminates.
**Pre-registered falsifier (round-2 stage, blocking sigma_provisional
removal):** rerun the d-quark leg at θ = θ_bs/2 and θ = 2·θ_bs (canonical
θ_bs = −0.152), same masses, same pipeline. Predictions: (i) the canonical-θ
triangle fixture stays bit-identical (−1.2831509485455282e-7); (ii) at both
off-points |C_scalar_full| ≥ 0.1 × |C_scalar_triangle-only(θ)| — i.e. the
cancellation degrades from 1.3e-3 to ordinary O(1) partial cancellation.
**Outcomes:** prediction (ii) holds → the ≈0 blind-spot scalar is ratified as
physical. |C_scalar_full| < 1e-2 × triangle-only at BOTH off-points with all
guards green → the instrument manufactures the zero: construction error, STOP,
full audit of rotation + projection (the old clause reinstated with force).

## Ruling 4 — Implementer deviations: all three RATIFIED

(a) **Scale-relative rotation-exactness guard — RATIFIED.** The guard checks an
algebraic identity; per-config ratios on near-null denominators measure
rounding against zero (measured 4.4e-11 inflation at v/10 vs 8.5e-16
scale-relative). Uniform-norm statement is correct; 4.3e-16 has 4 digits of
headroom on the 1e-12 bar. Per-config raws stay in the sidecar.
(b) **probe8 derivative-class contribution bar — RATIFIED.** The exemption is
structural (any monomial containing a rank-1 momentum-insertion chain), not a
name list; the raw bar is unreachable in principle off the forward manifold;
contribution weighting (worst 9.6e-10) is the honest instrument statement; raw
0.189 ships in the sidecar; weight-bearing derivative content still trips the
driver's full completeness bar. All conditions already met in code.
(c) **Fixed |q| = √TEPS transfer, not velocity-scaled — RATIFIED with named
consequence.** √TEPS is the amplitude's own fixed T-scale; scaling it with v
kills the pseudoscalar excitation the instrument exists to provide (measured
cond 2.7e7). Accepted consequence: the transfer instrument is NOT a v-stability
probe — v-stability is owned by the Ruling-2 replacement bar, and the v/10
refusal is recorded as a named outcome, never retried by loosening cond.

## Ruling 5 — PR #35 MERGES as an honest-instruments milestone, refusal intact

The Exit[3] at SD-SI-EXTRACTION-UNSTABLE is CORRECT behavior until this
amendment's code lands: the pre-registration fired and the driver refused
rather than shipping a silently-retired fit. Merge criteria (all must hold at
the merge SHA): (1) this AMENDMENT3 committed under
`eval/2506.19062_wimps_blind_spots/` beside its predecessors; (2) no committed
text asserts −2.0973e-7 as physics (artifact framing only — round-3 claims this
done; reviewer spot-checks the grep); (3) suite green and byte-identity of
`run_eval.wls` / `run_eval_common.wl` / `match_nucleon.py` / 2HDM+a files
re-verified at the merge SHA; (4) a fresh reviewer confirms 1–3 (no
self-grading). No code change is required for merge; changing the refusal
before merge is FORBIDDEN. **Round-2 scope, in order:** (i) production
rewiring per Ruling 1 (full-basis promotion, cross-instrument guard, retire
SD-SI-EXTRACTION-UNSTABLE with history note); (ii) off-blind-spot falsifier
leg (Ruling 3) — gates everything downstream; (iii) per-flavor u/d/s runs +
cross-flavor guard (A4); (iv) nucleon contraction + two-value C_G bracket
(Ruling 1) + A-R3 unit test; (v) Hisano pure-doublet anchor, which also
adjudicates the rank-2 percent-level debt and the gluon bracket.
