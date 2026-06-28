#!/usr/bin/env python3
r"""
hk_anchor.py — INDEPENDENT analytic anchor for the loop-induced spin-independent
WIMP-nucleon cross section of the 2HDM+a benchmark point, computed WITHOUT
FeynArts/FormCalc/LoopTools (closed-form one-loop box + heavy-quark gluon
matching). See hk_anchor_derivation.md for the full derivation and references.

SCOPE / COVERAGE (read this):
  This computes ONLY the "mediator x quark-loop" contribution to spin-independent
  (SI) scattering: the box diagram with two pseudoscalar mediators `a` and one
  Standard-Model quark, which generates the scalar DM-quark operator
  (chi-bar chi)(q-bar q); the heavy quarks (c,b,t) are then matched onto the
  DM-gluon operator via the trace-anomaly / heavy-quark expansion
  m_Q (Q-bar Q) -> -(alpha_s/12 pi) G G  ==>  f_Q^N = (2/27) f_TG^N.
  This is the Haisch-Kahlhoefer-style leading estimate (Arcadi, Lindner, Queiroz,
  Rodejohann, Vogl, arXiv:1711.02110 Eq. (1.11)-(1.12); Abe-Fujiwara-Hisano
  arXiv:1810.01039 C_q^box / C_G^tri).

  It DOES NOT include:
    - the electroweak A0-H+-W- charged-Higgs/W box (a separate, genuinely
      electroweak contribution), and
    - the "triangle" diagrams (effective h/H-chi-chi vertex x Higgs Yukawa),
      which Abe-Fujiwara-Hisano find DOMINANT but which depend on the scalar
      trilinear couplings g_haa, g_Haa (i.e. potential parameters c1,c2 / lamP)
      and the a-A0 mixing angle theta and heavy-pseudoscalar mass m_A0 — NONE of
      which are fixed by this benchmark's SLHA.  The benchmark therefore only
      pins down the minimal single-pseudoscalar simplified model, for which the
      box below is the well-defined leading piece.

CONVENTIONS (match the project / SKILL.md reference Lagrangian):
  DM-mediator:   L ⊃ i g_chi a (chi-bar gamma5 chi)              (no 1/2)
  quark-mediator:L ⊃ i (m_q/v) xi_q a (q-bar gamma5 q)
  with xi_q the aligned 2HDM+a Type-II scaling:
     up-type  (u,c,t): xi = cot(beta)          (= 1/tanbeta)
     down-type(d,s,b): xi = tan(beta)
  We work in the simplified-model limit (a-A0 mixing folded into g_chi, xi:
  sin(theta) -> 1), consistent with the hand-crafted SARAH model
  (vertex "i g_chi a chi-bar chi", "(m_q/v) xi_q a q-bar i gamma5 q") and with the
  prompt's stated convention.  The CP-EVEN mixing alpha (FRALPHA=1.0) does not
  enter the pseudoscalar-mediated box.

CROSS-SECTION CONVENTION (match match_nucleon.py exactly):
  sigma_SI^N = (4/pi) mu_N^2 f_N^2  [GeV^-2],  sigma[cm^2] = sigma[GeV^-2]*(hbar c)^2
  mu_N = m_chi m_N/(m_chi+m_N);  (hbar c) = 0.1973269804 GeV fm.
"""
from __future__ import annotations
import math
import numpy as np
from scipy import integrate

# ---------------------------------------------------------------------------
# Inputs (from tests/fixtures/two_hdm_a_point.slha unless noted)
# ---------------------------------------------------------------------------
M_CHI = 100.0     # GeV, Dirac singlet DM
M_A   = 400.0     # GeV, pseudoscalar mediator a (PDG 36)
M_HP  = 500.0     # GeV, charged Higgs (only used for the EW-box size estimate)
M_W   = 80.379    # GeV
TANB  = 10.0
G_CHI = 1.0
VEV   = 246.0     # GeV, Higgs vev (Arcadi/AFH use v ~= 246 GeV)

COTB = 1.0 / TANB

# Quark masses (GeV). t,b from the SLHA; lighter quarks standard (PDG MSbar-ish).
QUARKS = {
    #          mass     type      heavy?  (heavy => 2/27 f_TG gluon matching)
    "u": dict(m=2.2e-3, up=True,  heavy=False),
    "d": dict(m=4.7e-3, up=False, heavy=False),
    "s": dict(m=0.095,  up=False, heavy=False),
    "c": dict(m=1.27,   up=True,  heavy=True),
    "b": dict(m=4.18,   up=False, heavy=True),
    "t": dict(m=173.0,  up=True,  heavy=True),
}

# Nucleon scalar form factors, preset "default_2018"
# (== micrOMEGAs built-in lattice defaults == Abe-Fujiwara-Hisano arXiv:1810.01039
#  Table 4).  f_TG = 1 - sum_{u,d,s} f_Tq.
FF = {
    "p": dict(f_Tu=0.0153, f_Td=0.0191, f_Ts=0.0447),
    "n": dict(f_Tu=0.0110, f_Td=0.0273, f_Ts=0.0447),
}
for N in FF:
    FF[N]["f_TG"] = 1.0 - (FF[N]["f_Tu"] + FF[N]["f_Td"] + FF[N]["f_Ts"])

M_PROTON  = 0.93827208816   # GeV (match match_nucleon.py)
M_NEUTRON = 0.93956542052
HBAR_C_GEV_CM = 1.973269804e-14
GEV2_TO_CM2 = HBAR_C_GEV_CM ** 2     # 3.8937937e-28 cm^2 per GeV^-2


# ---------------------------------------------------------------------------
# Box loop function J_total(m_chi, m_Q, m_a) = J_cross - J_uncross
#   (Feynman-parameter form derived in hk_anchor_derivation.md).
#   uncrossed:  use (x m_chi - y m_Q)^2,  Delta_- = (x m_chi - y m_Q)^2 + s m_a^2
#   crossed:    use (x m_chi + y m_Q)^2,  Delta_+ = (x m_chi + y m_Q)^2 + s m_a^2
#   integrand_*  =  s * [ (x m_chi -+ y m_Q)^2 / Delta^2  -  1/(2 Delta) ]
#   with s = 1 - x - y over the simplex 0<=x, 0<=y, x+y<=1.
#   J_total -> 0 as m_Q -> 0 (chirality flip), the key physical check.
#   Effective scalar Wilson coeff:  alpha_Q = (g_chi^2 c_Q^2 / 16 pi^2) J_total,
#   c_Q = (m_Q/v) xi_Q  is the coefficient of (chi-bar chi)(Q-bar Q).
# ---------------------------------------------------------------------------
def _J_one(mchi, mQ, ma, sign):
    """sign=-1 -> uncrossed (x mchi - y mQ); sign=+1 -> crossed (x mchi + y mQ)."""
    ma2 = ma * ma

    def integrand(y, x):
        s = 1.0 - x - y
        if s <= 0.0:
            return 0.0
        base = x * mchi + sign * y * mQ
        b2 = base * base
        Delta = b2 + s * ma2
        return s * (b2 / (Delta * Delta) - 1.0 / (2.0 * Delta))

    # integrate y in [0, 1-x], x in [0,1]
    val, _ = integrate.dblquad(integrand, 0.0, 1.0,
                               lambda x: 0.0, lambda x: 1.0 - x,
                               epsabs=1e-12, epsrel=1e-10)
    return val


def J_total(mchi, mQ, ma):
    J_uncross = _J_one(mchi, mQ, ma, sign=-1.0)
    J_cross = _J_one(mchi, mQ, ma, sign=+1.0)
    return J_cross - J_uncross, J_uncross, J_cross


# ---------------------------------------------------------------------------
# Assemble f_N and sigma
# ---------------------------------------------------------------------------
def alpha_Q(name):
    """Scalar Wilson coefficient alpha_Q [GeV^-2] of (chi-bar chi)(Q-bar Q)."""
    q = QUARKS[name]
    mQ = q["m"]
    xi = COTB if q["up"] else TANB
    cQ = (mQ / VEV) * xi
    Jt, _, _ = J_total(M_CHI, mQ, M_A)
    a = (G_CHI ** 2 * cQ ** 2 / (16.0 * math.pi ** 2)) * Jt
    return a, Jt, xi, cQ


def f_nucleon(N):
    """Effective DM-nucleon coupling f_N [GeV^-2] (sigma=(4/pi) mu^2 f_N^2)."""
    mN = M_PROTON if N == "p" else M_NEUTRON
    ff = FF[N]
    total = 0.0
    rows = []
    for name, q in QUARKS.items():
        a, Jt, xi, cQ = alpha_Q(name)
        mQ = q["m"]
        if q["heavy"]:
            ffac = (2.0 / 27.0) * ff["f_TG"]      # heavy-quark gluon matching
        else:
            key = "f_Tu" if q["up"] else ("f_Td" if name == "d" else "f_Ts")
            # u uses f_Tu; d uses f_Td; s uses f_Ts
            key = "f_Tu" if name == "u" else ("f_Td" if name == "d" else "f_Ts")
            ffac = ff[key]
        contrib = mN * ffac * (a / mQ)            # = mN * ffac * alpha_Q/m_Q
        total += contrib
        rows.append((name, mQ, xi, cQ, Jt, a, ffac, contrib))
    return total, rows


def sigma_cm2(m_dm, f_N, m_N):
    mu = m_dm * m_N / (m_dm + m_N)
    sigma_gev2 = (4.0 / math.pi) * mu * mu * f_N * f_N
    return sigma_gev2 * GEV2_TO_CM2, mu


# ---------------------------------------------------------------------------
# Rough EW A0-H+-W- box size estimate (coverage honesty, NOT a real calc).
#   Naive dimensional estimate of an electroweak box generating f_N:
#   f_EW ~ (g2^2/16pi^2)^2 * g_chi * m_N * (something/M_heavy^2).  We give only a
#   crude order-of-magnitude band in the writeup; here we expose the inputs.
# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("HK-style analytic anchor: 2HDM+a loop-induced SI cross section")
    print("=" * 72)
    print(f"Mchi={M_CHI}  Ma={M_A}  MHp={M_HP}  tanb={TANB}  gchi={G_CHI}  v={VEV}")
    print(f"cotb={COTB}  (xi_up=cotb={COTB}, xi_down=tanb={TANB})")
    print()
    print("Per-quark box (alpha_Q = coeff of (chi-bar chi)(Q-bar Q)):")
    print(f"  {'q':>2} {'m_Q[GeV]':>9} {'xi':>6} {'c_Q':>10} "
          f"{'J_total[GeV^-2]':>16} {'alpha_Q[GeV^-2]':>16}")
    for name in QUARKS:
        a, Jt, xi, cQ = alpha_Q(name)
        print(f"  {name:>2} {QUARKS[name]['m']:>9.4g} {xi:>6.3g} {cQ:>10.4g} "
              f"{Jt:>16.6e} {a:>16.6e}")
    print()
    central = {}
    for N, mN in (("p", M_PROTON), ("n", M_NEUTRON)):
        f_N, rows = f_nucleon(N)
        sig, mu = sigma_cm2(M_CHI, f_N, mN)
        central[N] = sig
        print(f"--- nucleon {N} (m_N={mN:.5f}, mu={mu:.5f} GeV) ---")
        print(f"  {'q':>2} {'f-factor':>10} {'contrib to f_N[GeV^-2]':>24}")
        for (name, mQ, xi, cQ, Jt, a, ffac, contrib) in rows:
            print(f"  {name:>2} {ffac:>10.5f} {contrib:>24.6e}")
        print(f"  f_{N} = {f_N:.6e} GeV^-2  "
              f"(bottom-dominated; top ~16x smaller via cot-beta)")
        print(f"  sigma_SI({N}) = {sig:.4e} cm^2")
        print()

    # ---- sensitivity / uncertainty band -----------------------------------
    print("Sensitivity (recompute proton sigma under variations):")
    base_mb = QUARKS["b"]["m"]
    base_mc = QUARKS["c"]["m"]
    # (a) MSbar running bottom mass m_b(mu~100 GeV) ~= 2.8 GeV instead of 4.18.
    QUARKS["b"]["m"] = 2.8
    f_run, _ = f_nucleon("p")
    s_run, _ = sigma_cm2(M_CHI, f_run, M_PROTON)
    QUARKS["b"]["m"] = base_mb
    # (b) drop charm+light (pure b+t, isolate heavy-down + top)
    print(f"  central  sigma_SI(p)            = {central['p']:.3e} cm^2")
    print(f"  m_b->2.8 (MSbar @100GeV)        = {s_run:.3e} cm^2  "
          f"(x{s_run/central['p']:.2f})")
    print("  + naive 2/27 heavy-quark match vs full 2-loop C_G^box (AFH): O(2-3)")
    print("  => quote sigma_SI ~ 2e-54 cm^2, reliable to a factor of ~5")
    print()
    print("COVERAGE: mediator(a) x quark-loop box ONLY (-> gluon/quark scalar op).")
    print("  NOT included: EW A0-H+-W- box; triangle (h/H-chi-chi x Yukawa, AFH-")
    print("  dominant) — both need params (theta, m_A0, g_haa/g_Haa) NOT in the SLHA.")


if __name__ == "__main__":
    main()
