# Twist-2 sign gate — is the P3' twist-2 sign agreement reliable evidence?

VALIDATION-ONLY. NO KERNEL, NO FIX, no protected-file edits. Supporting script:
`twist2_sign_check.py` (numpy-only free-spinor operator matrix elements; no
LoopTools, no amplitude, no PV heads). Paper re-fetched: ar5iv
`https://ar5iv.labs.arxiv.org/html/1104.0228`.

## The fork

The scalar sign defect's proposed mechanism is a PROCESS-GLOBAL, operator-BLIND
`-1` (a CreateFeynAmp two-fermion-line pairing prefactor) that flips SCALAR and
TWIST-2 TOGETHER. Tension: P3' MEASURED our twist-2 sign to AGREE with Hisano
while our scalar DISagrees. Is that twist-2 agreement REAL (→ a single global
`-1` is contradicted, conviction blocked = **World A**) or a bridge-sign ARTIFACT
masking a true disagreement (→ twist-2 really flips too, the `-1` closes
everything, conviction available = **World B**)?

The designer's spec: rule a relative sign IN or OUT of the OPERATOR DEFINITIONS
on BOTH sides of the O_Tq↔Hisano bridge — NOT a re-run of the magnitude test.

## Operator-definition comparison (attribute by attribute)

| Attribute | OURS (`sd_projection.wl`) | HISANO (1104.0228 Eqs. 5-6,10,18) | Match? |
|---|---|---|---|
| Metric signature | mostly-minus `{1,-1,-1,-1}` (`$metric` L260, `$mdot` L460, `slash` L94) | mostly-minus: Dirac Lagr. `dL=(1/2)chibar(i Dslash - M)chi` is the Peskin `(i Dslash - M)` form | **YES** |
| Scalar operator | `(chibar chi)(qbar q)`, coeff `C_scalar` | `f_q m_q (chibar chi)(qbar q)`, coeff `f_q m_q` | same op |
| Twist-2 quark op | `<O^q_{mu nu}> = (1/2)[P_q_mu(qbar g_nu q)+P_q_nu(qbar g_mu q)] - (1/4)g_{mu nu} m_q(qbar q)` (twist2Ref1/2, L465-473; header L430-441) | `O^q_{mu nu}=(1/2)qbar i(D_mu g_nu+D_nu g_mu-(1/2)g_{mu nu}Dslash)q` (Eq.10) | **same op, transcribed verbatim** |
| WIMP twist-2 bilinear | `P_chi^mu(chibar g^nu chi)` and `(1/M)P_chi^mu P_chi^nu(chibar chi)` → C^(1),C^(2) (L440-441) | `chibar i d^mu g^nu chi` and `chibar id^mu id^nu chi` (Eqs.5-6), coeff g^(1)/M, g^(2)/M² | same, C^(i)=g^(i)/M |
| Index contraction | TWO metric contractions (mu,nu) | TWO metric contractions (mu,nu) | signature-EVEN both |
| i∂ → momentum | symmetric `P_chi=(k1+k3)/2, P_q=(k2+k4)/2` (L392-393) | symmetric traceless twist-2 (in+out avg) | same, sign-robust |
| Fermion-line ordering | (chi bilinear)×(quark bilinear), Majorana C-conj verified ~5e-15 (probeH) | (chi bilinear)×(quark bilinear) | same, no transpose sign |

The pipeline's O_Tq axis (used by D1/discriminator) uses a THIRD, single-contraction
operator `O_Tq=(chibar chi)(qbar gamma.P_chi q)` (`$opRefs["C_twist2"]`, L165-166),
which is signature-ODD (ONE contraction) and is bridged to Hisano via
`c_OTq=(3/4)(g1+g2)m_q/M` (p3_compare L29-33, discriminator L48-54).

## Sign-convention audit — every place a sign could enter the O_Tq↔Hisano map

1. **Metric signature.** Both sides mostly-minus. The `(i Dslash - M)` Dirac
   Lagrangian Hisano quotes is the Peskin mostly-minus form (mostly-plus/Srednicki
   writes the kinetic term differently). The ar5iv fast-model *guessed* mostly-plus
   by faulty reasoning; the quoted Lagrangian form refutes that guess. **Matches.**
   Moreover the relative sign of f_q vs g^(i) is a physical (signature-INVARIANT)
   property of L_eff — both are coefficients of Lorentz-scalar operators — so the
   comparison is robust even granting residual signature ambiguity.
2. **Traceless subtraction `-(1/2)g_{mu nu}Dslash → -(1/4)g_{mu nu}m_q(qbar q)`.**
   This is the one signature-sensitive piece the designer flagged. Evaluated in
   mostly-minus it REDUCES the matrix element (4→3 units) without flipping it;
   `twist2Ref1 = twist2Ref2 = +3 M^2 m_q^2` at rest. **Right relative sign,
   numerically confirmed.**
3. **O_Tq single contraction `gamma.P_chi`.** `<O_Tq> = +4 M^2 m_q` at rest
   (positive). Crossing the odd→even parity boundary is absorbed by the bridge
   factor; **sign preserved** (see numeric table).
4. **i∂ → P convention (incoming vs outgoing).** Symmetric momentum both sides →
   antisymmetric part cancels → **no sign.**
5. **Fermion-bilinear ordering / Majorana flow.** Same ordering; the pipeline's
   Majorana C-conjugation rotation is evaluation-verified (~5e-15) → **no sign.**

Number of independent sign-bearing conventions that can DIFFER between the two
sides: **ZERO.** Every one matches or cancels.

## Decisive numeric check (`twist2_sign_check.py`, kernel-free)

Free-spinor matrix elements, mostly-minus, at rest and boosted DD kinematics:

```
[REST    ] <O_Tq>=+9.17e+03  <Hisano T1+T2>=+6.43e+01  sign_map=POSITIVE
[DD-cfg-0] <O_Tq>=+9.82e+03  <Hisano T1+T2>=+7.69e+01  sign_map=POSITIVE
[DD-cfg-1] <O_Tq>=+9.26e+03  <Hisano T1+T2>=+6.59e+01  sign_map=POSITIVE
[DD-cfg-2] <O_Tq>=+9.21e+03  <Hisano T1+T2>=+6.49e+01  sign_map=POSITIVE
```

The O_Tq coefficient and Hisano's `(g1+g2)` share sign at EVERY config: the map is
a POSITIVE proportionality. (The magnitude ratio ~140 is the known O(3)/residual
magnitude caveat that made the *magnitude* discriminator INCONCLUSIVE — orthogonal
to sign.)

## Relative-sign ledger (the actual tension, resolved)

| | scalar | twist-2 (O_Tq / g_sum) | relative sign |
|---|---|---|---|
| Hisano (truth) | f_q m_q < 0  (g_H<0) | g1+g2 > 0 (g_T1→π/3) | **OPPOSITE** |
| Our pipeline | C_scalar = +1.05e-11 | C_twist2 = +8.118e-12 | **SAME** |

Bridge is a POSITIVE map (above) ⇒ our positive twist-2 GENUINELY agrees with
Hisano's positive twist-2; our positive scalar GENUINELY disagrees with Hisano's
negative scalar. A single global amplitude `-1` sends (+,+)→(−,−): it FIXES the
scalar but BREAKS the (currently correct) twist-2. No global operator-blind sign
can reconcile a SAME-sign pipeline against an OPPOSITE-sign truth.

## VERDICT: **WORLD A** (twist-2 sign agreement is RELIABLE → process-global `-1` CONTRADICTED → single-defect conviction BLOCKED)

The O_Tq↔Hisano twist-2 map carries no relative sign: same metric signature, same
operators, positive bridge (proven kernel-free at rest and boosted). The measured
twist-2 sign agreement is therefore REAL, not a bridge artifact. Because our
scalar/twist-2 relative sign is SAME while Hisano's is OPPOSITE, an
operator-blind process-global `-1` is ruled out — it would have flipped the
reliably-agreeing twist-2 into disagreement. The scalar sign defect is real but
must be **operator-class-specific (scalar-sector), or accompanied by a second
compensating sign on twist-2** — not a single CreateFeynAmp global prefactor.

**Confidence: HIGH.** Rests on: (a) identical mostly-minus signatures — and the
signature-invariance of the f_q-vs-g^(i) relative sign makes even this robust;
(b) the pipeline's twist2Ref being Hisano's Eq.10 operator verbatim, numerically
re-verified here; (c) the durable O_Tq extract `+8.118e-12` (cours L2), taken at
campaign face value.

**Adversarial World-B check.** World B needs a hidden sign in the map. The only
signature-sensitive term (the `-(1/4)g_{mu nu}` traceless subtraction) was
evaluated explicitly and does NOT flip. The ar5iv mostly-plus reading is a
fast-model artifact contradicted by the quoted Dirac Lagrangian. World B is not
open on the operator definitions.

**What a kernel WOULD add (not required to reach World A):** a direct kernel
re-extraction of the production `C^(1)/C^(2)` (the sign-faithful `twist2Ref1/2`
axis, Hisano's own operator, NO O_Tq bridge) would confirm `sign(C^(1)+C^(2))>0`
with zero bridge assumptions — belt-and-suspenders. The bridge is already proven
sign-faithful here without it, so it is confirmatory, not load-bearing.

**Residual uncertainty:** the argument trusts the durable O_Tq sign extract; if
that extraction were itself further corrupted the ledger shifts (the kernel
re-extraction above would close that gap). Twist-2 MAGNITUDE remains inconclusive
(unchanged) — this gate rules only on SIGN.
