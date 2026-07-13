"""
hisano_1104_0228.py — VALIDATION-ONLY transcription of the Hisano-Ishiwata-Nagata
effective-coupling formulae for an electroweak-interacting Majorana WIMP.

================================================================================
   *** VALIDATION-ONLY / A2-SANCTIONED EXTERNAL REFERENCE — NEVER A PRODUCTION PATH ***
================================================================================
This module is the *independent external lineage* used to adjudicate P3
(DESIGN-ITEM4-AMENDMENT5R1.md, Ruling 4).  It is an ANALYTIC TRANSCRIPTION of a
published paper.  The item-4 production ban on analytic transcriptions is
ABSOLUTE: nothing in this file, and nothing that imports it, may ever feed the
production Wilson-coefficient path (run_eval_sd.wls / sd_projection.wl) or a
shipped cross section.  It lives under benchmarks/ precisely so the import graph
makes that impossible.  Its only job: given OUR pipeline's own inputs
(M=m_chi, m_W, m_Z, m_h, g_2, sin^2 theta_W, m_q), predict what an independent
one-loop calculation says the pure-doublet (Higgsino-like) scalar and twist-2
quark Wilson coefficients should be, so P3 can form a ratio against our pipeline.

SOURCE
------
J. Hisano, K. Ishiwata, N. Nagata,
"Gluon contribution to the dark matter direct detection",
Phys. Rev. D 82, 115007 (2010)  [arXiv:1007.2601]  (long paper, full formulae),
and its Phys. Lett. B companion arXiv:1104.0228 (Phys.Lett.B706:208-212, 2011).
Equation numbers below refer to the arXiv:1104.0228 numbering as rendered at
https://ar5iv.labs.arxiv.org/html/1104.0228 (cross-checked, three independent
fetches, 2026-07-13).  Where 1104.0228 defers to the long paper for a loop
function, that is noted inline.

THE PHYSICS SETTING (why this is the right external anchor for P3)
-----------------------------------------------------------------
Hisano et al. treat a Majorana WIMP chi^0 that is the neutral component of an
SU(2)_L multiplet with isospin (dimension) n and hypercharge Y, interacting with
the SM ONLY through electroweak gauge / Higgs loops (the tree-level scalar
coupling vanishes — exactly the item-4 "blind spot").  The remaining scattering
is the ONE-LOOP floor.  A pure Higgsino / pure-electroweak-doublet is n=2, Y=1/2
(so n^2 - (4 Y^2 + 1) = 4 - 2 = 2).  In the singlet-doublet model at MS >> MPsi
the DM (chi1) is a nearly pure Y=1/2 doublet, so this is precisely Hisano's
regime — the P3 comparison point.

================================================================================
   CONVENTIONS (read before trusting any number this file returns)
================================================================================
Effective Lagrangian (1104.0228 Eqs. 5-7):

  L_eff = sum_q [ d_q (chibar gamma^mu gamma5 chi)(qbar gamma_mu gamma5 q)      # axial (SD) - not us
                + f_q m_q (chibar chi)(qbar q)                                  # SCALAR (our gH axis)
                + (g^(1)_q / M) (chibar i d^mu gamma^nu chi) O^q_{mu nu}         # twist-2
                + (g^(2)_q / M^2)(chibar i d^mu i d^nu chi) O^q_{mu nu} ]        # twist-2
        + f_G (chibar chi) G^a_{mu nu} G^{a mu nu}                              # gluon (nucleon-level only)

  * SCALAR OPERATOR NORMALIZATION (THE decisive convention for P3):
    the coefficient of the operator (chibar chi)(qbar q) is  f_q * m_q  --- NOT
    f_q alone.  f_q (Eq. 18) carries mass dimension -3; f_q*m_q has dimension -2,
    which is the dimension of a 2->2 scattering-amplitude operator coefficient.
    => C_scalar^Hisano  ==  f_q * m_q   (this is what our pipeline's C_scalar,
       the coefficient of (chibar_chi chi)(qbar_q q) in the amplitude, measures).
    Our pipeline also reports C_Q := C_scalar / m_q (AMENDMENT5R1 R2); that
    "per-quark-mass" reading maps DIRECTLY onto Hisano's f_q.

  * M == m_chi (WIMP mass).  The twist-2 operators carry explicit 1/M, 1/M^2.

  * O^q_{mu nu} (Eq. 10) = (1/2) qbar i (D_mu gamma_nu + D_nu gamma_mu
                                          - (1/2) g_{mu nu} Dslash) q   (twist-2,
    traceless symmetric quark energy-momentum operator; covariant derivative
    D_mu = d_mu - i g ... with the standard SM sign).

  * Majorana WIMP: chi = chi^c.  Hisano's operator coefficients are quoted for
    this self-conjugate normalization; no extra 1/2 symmetry factor is applied
    here beyond what the paper's coefficients already carry.

  * Quark masses: light-quark masses are neglected in the LOOP (Sec. 4.1, "we
    ignore the mass of quarks except the top"); the m_q that multiplies the
    scalar operator is the external-current mass factor.  The paper's numerics
    use MSbar masses and evaluate PDFs / second moments at mu = m_Z.

  * alpha_2 = g_2^2 / (4 pi)  (SU(2)_L; Eq. 18 context).

  * Sign convention: f_q as printed in Eq. 18 (g_H(x) is NEGATIVE over the
    relevant range, so the Higgs-exchange piece of f_q is negative).  We carry
    the paper's sign verbatim and let P3 compare signs.

TWIST-2 CONVENTION TRAP (flagged by the design authority)
---------------------------------------------------------
Our rounds have quoted the twist-2 axis in two different conventions that differ
by ~100 (this is CONVENTION, not a discrepancy): an "old contraction" ~4.096e-9
and the Hisano-normalized  C^(i) = g^(i)/m_chi  giving ~4.2525e-7.  The combined
Hisano twist-2 Wilson coefficient in the g/M convention is therefore
    C_twist2^Hisano(g/M convention) = (g^(1)_q + g^(2)_q) / M.
This module returns BOTH the bare (g^(1)+g^(2)) and the /M form so the caller can
state which convention a given ratio is in.  NOTE: on origin/main the pipeline's
`C_twist2` is a SINGLE contracted twist-2 operator coefficient (O_Tq); the
C^(1)/C^(2) split is an item-4 deliverable, so the twist-2 axis carries an
operator-normalization caveat and is the *free* second axis (scalar gH is the
decisive one) per Ruling 4.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Default electroweak inputs.  For the P3 comparison these are OVERRIDDEN with
# the values the SPheno spectrum feeds our own amplitude (so any residual
# difference is amplitude construction, not an input mismatch).  The defaults
# here reproduce the paper's numerical setting for the self-check.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EWInputs:
    m_W: float = 80.377        # GeV
    m_Z: float = 91.1876       # GeV
    m_h: float = 125.25        # GeV (paper uses ~115-125; self-check uses 125)
    sw2: float = 0.23122       # sin^2 theta_W
    alpha_em: float = 1.0 / 137.036

    @property
    def cw2(self) -> float:
        return 1.0 - self.sw2

    @property
    def alpha2(self) -> float:
        # alpha_2 = g_2^2/4pi = alpha_em / sin^2 theta_W
        return self.alpha_em / self.sw2


# ---------------------------------------------------------------------------
# Loop functions (1104.0228 Eq. 33).  Argument x = m_V^2 / M^2, V in {W,Z}.
# b_x = sqrt(1 - x/4).  arctan(2 b_x / sqrt(x)) -> pi/2 as x -> 0.
# These are transcribed VERBATIM from Eq. 33.
# ---------------------------------------------------------------------------
def b_x(x: float) -> float:
    return math.sqrt(1.0 - x / 4.0)


def _atan(x: float) -> float:
    return math.atan(2.0 * b_x(x) / math.sqrt(x))


def g_H(x: float) -> float:
    """Eq. 33: scalar (Higgs-exchange) loop function.  g_H(x->0) -> -2 pi."""
    bx = b_x(x)
    return (-(2.0 / bx) * (2.0 + 2.0 * x - x * x) * _atan(x)
            + 2.0 * math.sqrt(x) * (2.0 - x * math.log(x)))


def g_S(x: float) -> float:
    """Eq. 33: scalar (gauge-box) loop function.  g_S(x->0) -> pi/2."""
    bx = b_x(x)
    return ((1.0 / (4.0 * bx)) * (4.0 - 2.0 * x + x * x) * _atan(x)
            + 0.25 * math.sqrt(x) * (2.0 - x * math.log(x)))


def g_T1(x: float) -> float:
    """Eq. 33: twist-2 loop function #1.  b_x is in the DENOMINATOR of term 1
    (confirmed against the source).  g_T1(x->0) -> pi/3."""
    bx = b_x(x)
    return ((1.0 / (3.0 * bx)) * (2.0 + x * x) * _atan(x)
            + (1.0 / 12.0) * math.sqrt(x)
            * (1.0 - 2.0 * x - x * (2.0 - x) * math.log(x)))


def g_T2(x: float) -> float:
    """Eq. 33: twist-2 loop function #2.  g_T2(x->0) -> 0."""
    bx = b_x(x)
    return ((1.0 / (4.0 * bx)) * x * (2.0 - 4.0 * x + x * x) * _atan(x)
            - 0.25 * math.sqrt(x)
            * (1.0 - 2.0 * x - x * (2.0 - x) * math.log(x)))


# ---------------------------------------------------------------------------
# Quark electroweak couplings (1104.0228 Eq. 22)
#   a_q^V = (1/2) T3_q - Q_q sin^2 theta_W
#   a_q^A = -(1/2) T3_q
# ---------------------------------------------------------------------------
# (T3, Q) per quark flavour
QUARK_QN = {
    "u": (+0.5, +2.0 / 3.0),
    "d": (-0.5, -1.0 / 3.0),
    "s": (-0.5, -1.0 / 3.0),
    "c": (+0.5, +2.0 / 3.0),
    "b": (-0.5, -1.0 / 3.0),
    "t": (+0.5, +2.0 / 3.0),
}


def a_qV(flavour: str, sw2: float) -> float:
    T3, Q = QUARK_QN[flavour]
    return 0.5 * T3 - Q * sw2


def a_qA(flavour: str) -> float:
    T3, _ = QUARK_QN[flavour]
    return -0.5 * T3


# ---------------------------------------------------------------------------
# Scalar coefficient f_q  (1104.0228 Eq. 18)
#
#  f_q = (alpha2^2 / 4 m_h^2) [ (n^2-(4Y^2+1))/(8 m_W) g_H(w)
#                              + Y^2/(4 m_Z cos^4 theta_W) g_H(z) ]
#      + ((a_q^V)^2 - (a_q^A)^2) Y^2/cos^4 theta_W (alpha2^2 / m_Z^3) g_S(z)
#
#  w = m_W^2/M^2 , z = m_Z^2/M^2 .  Dimension of f_q is GeV^-3.
# ---------------------------------------------------------------------------
def f_q(M: float, flavour: str, n: int, Y: float, ew: EWInputs) -> float:
    w = (ew.m_W / M) ** 2
    z = (ew.m_Z / M) ** 2
    a2 = ew.alpha2
    cw4 = ew.cw2 ** 2
    nfac = n * n - (4.0 * Y * Y + 1.0)   # = 2 for a pure doublet (n=2, Y=1/2)

    higgs = (a2 * a2 / (4.0 * ew.m_h ** 2)) * (
        (nfac / (8.0 * ew.m_W)) * g_H(w)
        + (Y * Y / (4.0 * ew.m_Z * cw4)) * g_H(z)
    )
    box = ((a_qV(flavour, ew.sw2) ** 2 - a_qA(flavour) ** 2)
           * Y * Y / cw4) * (a2 * a2 / ew.m_Z ** 3) * g_S(z)
    return higgs + box


# ---------------------------------------------------------------------------
# Twist-2 coefficients g^(1)_q, g^(2)_q  (1104.0228 Eqs. 20, 21).  GeV^-3.
#
#  g^(i)_q = (n^2-(4Y^2+1))/8 (alpha2^2/m_W^3) g_Ti(w)
#          + 2((a_q^V)^2+(a_q^A)^2) Y^2/cos^4 theta_W (alpha2^2/m_Z^3) g_Ti(z)
# ---------------------------------------------------------------------------
def _g_twist(M: float, flavour: str, n: int, Y: float, ew: EWInputs, gT) -> float:
    w = (ew.m_W / M) ** 2
    z = (ew.m_Z / M) ** 2
    a2 = ew.alpha2
    cw4 = ew.cw2 ** 2
    nfac = n * n - (4.0 * Y * Y + 1.0)
    Wpart = (nfac / 8.0) * (a2 * a2 / ew.m_W ** 3) * gT(w)
    Zpart = (2.0 * (a_qV(flavour, ew.sw2) ** 2 + a_qA(flavour) ** 2)
             * Y * Y / cw4) * (a2 * a2 / ew.m_Z ** 3) * gT(z)
    return Wpart + Zpart


def g1_q(M, flavour, n, Y, ew):
    return _g_twist(M, flavour, n, Y, ew, g_T1)


def g2_q(M, flavour, n, Y, ew):
    return _g_twist(M, flavour, n, Y, ew, g_T2)


# ---------------------------------------------------------------------------
# P3 COMPARISON QUANTITIES  (brought to the operator conventions our pipeline
# reports, so a ratio is apples-to-apples).
# ---------------------------------------------------------------------------
def C_scalar_hisano(M: float, mq: float, flavour: str, n: int, Y: float,
                    ew: EWInputs) -> float:
    """Coefficient of (chibar chi)(qbar q) == f_q * m_q  (GeV^-2).
    Compare DIRECTLY to our pipeline's C_scalar (R_S_S)."""
    return f_q(M, flavour, n, Y, ew) * mq


def C_Q_hisano(M: float, flavour: str, n: int, Y: float, ew: EWInputs) -> float:
    """Per-quark-mass scalar reading == f_q (GeV^-3).  Compare to our C_Q =
    C_scalar/m_q (AMENDMENT5R1 R2)."""
    return f_q(M, flavour, n, Y, ew)


def C_twist2_hisano(M: float, flavour: str, n: int, Y: float, ew: EWInputs):
    """Return (g1+g2, (g1+g2)/M) — bare and g/M convention.  The g/M form is the
    Hisano-normalized C^(1,2)=g^(i)/m_chi combined twist-2 coefficient
    (the ~4.2525e-7 lineage)."""
    g1 = g1_q(M, flavour, n, Y, ew)
    g2 = g2_q(M, flavour, n, Y, ew)
    return (g1 + g2), (g1 + g2) / M


# ---------------------------------------------------------------------------
# Nucleon-level spin-independent cross section (1104.0228 Eqs. 11-12) — used
# ONLY by the self-check (never a shipped number).  The 2-loop gluon term f_G
# (Eqs. 24-32, Appendices A/B) is NOT transcribed here; the self-check omits it
# and flags that omission (the paper's own point is that the gluon term brings
# the Higgsino to the LOW end of its quoted range).
# ---------------------------------------------------------------------------
def sigma_SI_scalar_twist2(M: float, n: int, Y: float, ew: EWInputs,
                           include_twist2: bool = True) -> float:
    """SI WIMP-proton cross section in cm^2 from the SCALAR + TWIST-2 quark
    operators only (no 2-loop gluon).  Standard nucleon matching:
       f_N/m_N = sum_q f_q f_Tq + sum_q (3/4)(q(2)+qbar(2))(g1_q+g2_q)
       sigma_SI = (4/pi) m_R^2 |f_N|^2 .
    Order-of-magnitude self-check against the paper's O(10^-46..-48) cm^2."""
    # proton mass fractions f_Tq and second moments (from eval/constants.py)
    f_Tq = {"u": 0.0153, "d": 0.0191, "s": 0.0447}
    q2 = {"u": 0.22 + 0.034, "d": 0.11 + 0.036, "s": 0.026 + 0.026,
          "c": 0.019 + 0.019, "b": 0.012 + 0.012}
    m_N = 0.93827
    fN_over_mN = 0.0
    for q in ("u", "d", "s"):
        fN_over_mN += f_q(M, q, n, Y, ew) * f_Tq[q]
    if include_twist2:
        for q in ("u", "d", "s", "c", "b"):
            g1 = g1_q(M, q, n, Y, ew)
            g2 = g2_q(M, q, n, Y, ew)
            fN_over_mN += 0.75 * q2[q] * (g1 + g2)
    fN = fN_over_mN * m_N
    m_R = M * m_N / (M + m_N)
    sigma_gev = (4.0 / math.pi) * m_R ** 2 * fN ** 2   # GeV^-2
    return sigma_gev * 3.8937966e-28                   # -> cm^2


# ---------------------------------------------------------------------------
# SELF-CHECK  (mandatory, per Ruling 4 step 2).  Must pass BEFORE any P3
# comparison is formed.  Two independent reproductions of paper-stated facts:
#   (1) the Eq.-33 loop-function analytic limits x->0 (arctan -> pi/2), which
#       underpin the paper's Fig.-4 statement that sigma_SI becomes nearly
#       WIMP-mass-independent above ~1 TeV (prefactors are M-independent, so
#       f_q, g^(i)_q -> constants as M->infty);
#   (2) the pure-Higgsino sigma_SI landing inside the paper's abstract-quoted
#       range O(10^-46..-48) cm^2 (scalar+twist-2, gluon omitted & flagged).
# ---------------------------------------------------------------------------
def selfcheck(verbose: bool = True) -> dict:
    out = {}
    # (1) analytic limits of the loop functions
    xs = 1.0e-7
    lim = {
        "g_H": (g_H(xs), -2.0 * math.pi),        # -> -2 pi
        "g_S": (g_S(xs), math.pi / 2.0),         # -> pi/2
        "g_T1": (g_T1(xs), math.pi / 3.0),       # -> pi/3
        "g_T2": (g_T2(xs), 0.0),                 # -> 0
    }
    limits_ok = True
    for name, (got, want) in lim.items():
        # relative tol for nonzero limits; absolute floor 2e-3 for the g_T2 -> 0
        # limit (its residual at x=1e-7 is the O(sqrt(x) log x) tail, ~8e-5).
        ok = abs(got - want) < max(5.0e-3 * abs(want), 2.0e-3)
        limits_ok = limits_ok and ok
        if verbose:
            print(f"  limit {name}(x->0) = {got:+.6f}  (paper Eq.33 -> {want:+.6f})"
                  f"  {'OK' if ok else 'FAIL'}")
    out["loop_function_limits_ok"] = limits_ok
    out["loop_function_limits"] = {k: {"computed": v[0], "analytic": v[1]}
                                   for k, v in lim.items()}

    # mass-independence: f_q at 1 TeV vs 10 TeV should agree to a few % (Fig 4)
    ew = EWInputs()
    fq1 = f_q(1000.0, "d", 2, 0.5, ew)
    fq10 = f_q(10000.0, "d", 2, 0.5, ew)
    mass_indep = abs(fq10 - fq1) / abs(fq1)
    out["f_q_mass_independence_reldiff_1to10TeV"] = mass_indep
    if verbose:
        print(f"  f_d(1TeV)={fq1:.4e}  f_d(10TeV)={fq10:.4e}  reldiff={mass_indep:.3%}"
              f"  (Fig.4: ~mass-independent above 1 TeV)")

    # (2) Higgsino sigma_SI in the paper's quoted range
    sig = sigma_SI_scalar_twist2(1000.0, 2, 0.5, ew)
    in_range = 1e-49 <= sig <= 1e-45
    out["sigma_SI_higgsino_1TeV_cm2_no_gluon"] = sig
    out["sigma_SI_in_paper_range"] = in_range
    if verbose:
        print(f"  sigma_SI(Higgsino,1TeV, scalar+twist2, NO gluon) = {sig:.3e} cm^2"
              f"  (paper abstract: O(10^-46..-48) cm^2)  {'OK' if in_range else 'FAIL'}")

    out["passed"] = bool(limits_ok and in_range)
    return out


if __name__ == "__main__":
    print("Hisano 1104.0228 transcription self-check (VALIDATION-ONLY):")
    res = selfcheck()
    print("SELF-CHECK", "PASSED" if res["passed"] else "FAILED")
