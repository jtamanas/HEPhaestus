#!/usr/bin/env python3
r"""
ew_anchor.py — LIKE-FOR-LIKE analytic magnitude anchor for the 2HDM+a loop-induced
spin-independent WIMP-nucleon cross section, computed from the SAME diagram set the
project's LoopTools chain advertises:

    run_eval.wls  loop_topologies = {"chargedHiggs_W_box", "mediator_triangle"}
    2hdm-a/SKILL.md & looptools/SKILL.md = "charged-Higgs/W box (A0H+W-) + mediator triangle"

This is the COMPLEMENT of hk_anchor.py (which computes the pseudoscalar x quark-loop
box -> gluon, a DISJOINT diagram set that is NOT in the LoopTools topology list).

PRIMARY REFERENCE for the diagrams here:
  T. Abe, M. Fujiwara, J. Hisano, Y. Shoji,
  "Maximum value of the spin-independent cross section in the THDM+a",
  JHEP 01 (2020) 114, arXiv:1910.09771.            <-- the 2HDM+a paper (EW box + triangle)
  building on the loop functions of
  T. Abe, M. Fujiwara, J. Hisano,
  "Loop corrections to dark matter direct detection in a pseudoscalar mediator DM model",
  JHEP 02 (2019) 028, arXiv:1810.01039.            <-- defines the triangle loop function

HONESTY / SCOPE (read ew_anchor_derivation.md sec.6, sec.7, sec.10 for the full statement):
  * The MEDIATOR TRIANGLE (chi chi -> h/H via the chi-chi-a-a loop closed by the
    phi-a-a trilinear, then phi-qqbar Yukawa) is computed RIGOROUSLY here from the
    pinned scalar potential.  AFH find it DOMINANT; we confirm h dominates (sec.5).
    Its size comes from an O(v) portal trilinear g_aah~350 GeV -- NOT a tanbeta blow-up
    (with c1=c2 the tanbeta factors cancel exactly; sec.4).
  * The A0-H+-W- electroweak BOX is an ESTIMATE, NOT a calculation: it needs the
    explicit 1910.09771 box function (Appendix, not cleanly machine-extractable).  We
    bound it at <=30% of the triangle.  Crucially this is the piece LoopTools computes
    RIGOROUSLY, so a live LoopTools sigma ~1.3-1.7x ABOVE the triangle anchor is
    EXPECTED (constructive box), not a discrepancy.
  * LIKE-FOR-LIKE is TOPOLOGY-LABEL ONLY: run_eval.wls is a stub (fp=fn=0) and the
    committed fixture amp_reduced.m is box-only (no h/H triangle visible).  "LoopTools
    includes the dominant triangle" is a physics inference pending verification of the
    real FeynArts amplitude.  See the operational validation window (derivation sec.10).

CONVENTIONS (match match_nucleon.py and the pinned benchmark exactly):
  sigma_SI^N = (4/pi) mu_N^2 f_N^2  [GeV^-2];  sigma[cm^2] = sigma[GeV^-2]*(hbar c)^2
  mu_N = m_chi m_N/(m_chi+m_N);  hbar c = 1.973269804e-14 GeV*cm.
  Dirac chi, vertex  i g_chi a chi-bar gamma5 chi  (no 1/2); chi-a ~ g_chi cos(theta),
  chi-A0 ~ g_chi sin(theta).  AFH use Majorana (i g_chi/2 ...) but with the SAME
  reduced coupling xi^chi_a = g_chi cos(theta); a residual Dirac/Majorana factor <=2
  in the loop normalisation is carried as an uncertainty (sec.8).
"""
from __future__ import annotations
import math
from scipy import integrate

# ---------------------------------------------------------------------------
# PINNED benchmark (GeV) — shared verbatim with the fixture-regen agent.
# ---------------------------------------------------------------------------
M_CHI = 100.0
M_A   = 400.0     # light pseudoscalar mediator a (mostly singlet)
M_A0  = 500.0     # heavy doublet pseudoscalar A0  (AFH "m_A")
M_HP  = 500.0     # charged Higgs H+-
M_H   = 500.0     # heavy CP-even H
M_HL  = 125.0     # SM-like h
M_W   = 80.379
M_Z   = 91.1876
M_T   = 173.0
M_B   = 4.18
V     = 246.0
VD    = 24.49
VU    = 244.78

TANB  = 10.0
BETA  = math.atan(TANB)            # 1.4711 rad
ALPHA = -0.0997                    # alignment: alpha = beta - pi/2, cos(beta-alpha)~0
SINT  = 0.35                       # a-A0 mixing sin(theta)
COST  = 0.9368
THETA = math.asin(SINT)
G_CHI = 1.0
S2W   = 1.0 - M_W**2 / M_Z**2      # = 0.2230
G2    = math.sqrt(4*math.pi/128.0) / math.sqrt(S2W)  # rough SU(2) g = e/sin_thetaW (used only in box estimate)

# Scalar-potential portal quartics (a0^2 |H_i|^2).  Pinned: lamP1 = lamP2 = 1.0.
# Identified with AFH's c1, c2 (the a0-Higgs-doublet quartics) — FLAGGED in sec.4.
C1 = 1.0   # lamP1  (a0^2 |H1|^2)
C2 = 1.0   # lamP2  (a0^2 |H2|^2)

# Nucleon scalar sigma-term form factors, preset "default_2018"
# (= micrOMEGAs lattice defaults = AFH 1810.01039 Table 4 = hk_anchor.py).
FF = {
    "p": dict(u=0.0153, d=0.0191, s=0.0447),
    "n": dict(u=0.0110, d=0.0273, s=0.0447),
}
for N in FF:
    FF[N]["G"] = 1.0 - (FF[N]["u"] + FF[N]["d"] + FF[N]["s"])  # f_TG

M_PROTON  = 0.93827208816
M_NEUTRON = 0.93956542052
HBAR_C_GEV_CM = 1.973269804e-14
GEV2_TO_CM2 = HBAR_C_GEV_CM ** 2          # 3.8937937e-28 cm^2 per GeV^-2

CB2 = math.cos(BETA) ** 2                  # = 1/(1+tanb^2)
SB2 = math.sin(BETA) ** 2                  # = tanb^2/(1+tanb^2)


# ---------------------------------------------------------------------------
# 1. Scalar trilinear couplings g_{phi a a}  (phi = h, H), from the pinned
#    potential, projected through the CP-even (alpha) and CP-odd (theta) mixings.
#    Form from AFH 1910.09771 Eq. (49):
#       g_aah = s_th^2 (2 m_a^2 + m_h^2 - 2 m_A0^2)/v
#               + 2 v c_th^2 (c1 cos^2 b + c2 sin^2 b)
#    The portal bracket (c1 cos^2b + c2 sin^2b) = (c1 + c2 tanb^2)/(1+tanb^2) is the
#    projection onto the SM (h) direction.  The orthogonal (H) direction picks the
#    combination (c2 - c1) s_b c_b, which VANISHES for c1 = c2 (our pinned point).
#    NOTE: with c1=c2 the SM bracket collapses to c2 (the tanb factors cancel) -> the
#    portal piece is 2v c_th^2 c2, an O(v) coupling of NATURAL EW size, NOT tanb-enhanced.
# ---------------------------------------------------------------------------
def g_phi_aa(m_phi, sm_like):
    geo = SINT**2 * (2*M_A**2 + m_phi**2 - 2*M_A0**2) / V
    if sm_like:
        port = 2*V*COST**2 * (C1*CB2 + C2*SB2)            # h: SM direction
    else:
        port = 2*V*COST**2 * (C2 - C1) * math.sin(BETA)*math.cos(BETA)  # H: orthogonal
    return geo + port, geo, port


# ---------------------------------------------------------------------------
# 2. Triangle loop function L(m_chi, m_med) = [ d B0(p^2, m_med^2, m_chi^2)/d p^2 ]_{p^2=m_chi^2}
#    Derived from scratch (ew_anchor_derivation.md sec.3) and verified to equal AFH
#    1810.01039 Eq. (3.36)'s [dB0/dp^2]:
#        L = INT_0^1 dx  x(1-x) / [ x m_med^2 + (1-x)^2 m_chi^2 ]      [GeV^-2]
#    (UV-finite; the doubled mediator propagator makes the box-like integral finite.)
# ---------------------------------------------------------------------------
def L_loop(m_chi, m_med):
    f = lambda x: x*(1.0 - x) / (x*m_med**2 + (1.0 - x)**2 * m_chi**2)
    val, _ = integrate.quad(f, 0.0, 1.0, epsabs=1e-14, epsrel=1e-12)
    return val


# ---------------------------------------------------------------------------
# 3. Effective scalar DM-Higgs coupling C_{phi chi chi}  (AFH 1810.01039 Eq. 3.36):
#    C_{phi chi chi} = -(m_chi/(4 pi)^2) [ g_{phi aa} (xi^chi_a)^2 L(m_chi,m_a)
#                                         + g_{phi A A}(xi^chi_A)^2 L(m_chi,m_A0)
#                                         + (mixed a-A term, sub-leading) ]
#    xi^chi_a = g_chi cos(theta),  xi^chi_A = g_chi sin(theta)   (AFH Eq. 2.18-2.19).
#    The mixed g_{phi aA} term is O(s_th c_th)/(m_A0^2-m_a^2) and numerically tiny;
#    omitted (folded into uncertainty).
# ---------------------------------------------------------------------------
XI_CHI_A = G_CHI * COST     # 0.9368
XI_CHI_A0 = G_CHI * SINT    # 0.35
PREF = 1.0 / (4.0*math.pi)**2

def C_phi_chichi(m_phi, sm_like):
    g_aa, _, _ = g_phi_aa(m_phi, sm_like)
    # g_{phi A0 A0}: doublet-pseudoscalar coupling.  For the heavy A0 the portal acts
    # through the same SM/orthogonal projection; we reuse the same projector (FLAG: the
    # A0-A0-phi geometric piece carries m_A0 not m_a).  A0-loop is sub-leading anyway.
    g_AA = g_aa if sm_like else g_phi_aa(m_phi, sm_like)[0]
    La  = L_loop(M_CHI, M_A)
    LA0 = L_loop(M_CHI, M_A0)
    c_a  = -(M_CHI*PREF) * g_aa * XI_CHI_A**2  * La
    c_A0 = -(M_CHI*PREF) * g_AA * XI_CHI_A0**2 * LA0
    return c_a + c_A0, c_a, c_A0


# ---------------------------------------------------------------------------
# 4. Aligned Type-II Yukawa rescalings xi_q^phi (phi-qbar-q = (m_q/v) xi_q^phi).
#    h:  up = cos(alpha)/sin(beta),  down = -sin(alpha)/cos(beta)
#    H:  up = sin(alpha)/sin(beta),  down =  cos(alpha)/cos(beta)
#    In alignment (alpha = beta - pi/2) xi_q^h ~ 1 (SM-like); xi_d^H ~ tanb, xi_u^H ~ -cotb.
# ---------------------------------------------------------------------------
CA, SA = math.cos(ALPHA), math.sin(ALPHA)
CB, SB = math.cos(BETA), math.sin(BETA)
XI_H = {"u": CA/SB, "d": -SA/CB}
XI_H_HEAVY = {"c": CA/SB, "b": -SA/CB, "t": CA/SB}
XI_HH = {"u": SA/SB, "d": CA/CB}
XI_HH_HEAVY = {"c": SA/SB, "b": CA/CB, "t": SA/SB}


def F_nucleon(N, xi_light, xi_heavy):
    """Scalar nucleon factor  F = sum_{u,d,s} f_Tq xi_q + (2/27) f_TG sum_{c,b,t} xi_Q."""
    f = FF[N]
    light = f["u"]*xi_light["u"] + f["d"]*xi_light["d"] + f["s"]*xi_light["d"]  # s is down-type
    heavy = (2.0/27.0)*f["G"]*(xi_heavy["c"] + xi_heavy["b"] + xi_heavy["t"])
    return light, heavy, light + heavy


# ---------------------------------------------------------------------------
# 5. Triangle DM-nucleon coupling (Higgs-portal form):
#       f_N^phi = C_{phi chi chi} (m_N/v) F_N^phi / m_phi^2         [GeV^-2]
#    coherent sum over phi = h, H.  (f_N = C_N/2 in AFH's sigma=(1/pi)mu^2|C_N|^2;
#    here we use the project's sigma=(4/pi)mu^2 f_N^2 directly.)
# ---------------------------------------------------------------------------
def triangle_fN(N):
    g_hchi, hc_a, hc_A0 = C_phi_chichi(M_HL, sm_like=True)
    g_Hchi, _, _        = C_phi_chichi(M_H,  sm_like=False)
    mN = M_PROTON if N == "p" else M_NEUTRON
    _, _, Fh = F_nucleon(N, XI_H,  XI_H_HEAVY)
    _, _, FH = F_nucleon(N, XI_HH, XI_HH_HEAVY)
    fN_h = g_hchi * (mN/V) * Fh / M_HL**2
    fN_H = g_Hchi * (mN/V) * FH / M_H**2
    return dict(fN=fN_h + fN_H, fN_h=fN_h, fN_H=fN_H,
                g_hchi=g_hchi, g_Hchi=g_Hchi, Fh=Fh, FH=FH)


# ---------------------------------------------------------------------------
# 6. EW A0-H+-W- box — ESTIMATE ONLY, NOT a real loop calc (derivation sec.6).
#    Topology note: chi couples ONLY to a/A0, so a genuine chi-q box rail must be a/A0;
#    the W/H+- enter via the gauge a-W-H+- vertex (~ g s_th/2 for a, g c_th/2 for A0)
#    dressing the quark side.  AFH find it sub-dominant to the O(v)-trilinear triangle.
#    We bound it at <=30% of the triangle f_N and carry it ONE-SIDED, NOT a central
#    value.  THIS IS THE PIECE LoopTools COMPUTES RIGOROUSLY (D0i/C0i/B0i in
#    amp_reduced.m): a live LoopTools sigma ~1.3-1.7x ABOVE the triangle is EXPECTED
#    (constructive box), not a discrepancy.  See the validation window (derivation sec.10).
# ---------------------------------------------------------------------------
def box_fN_estimate(N):
    tri = triangle_fN(N)
    return 0.30 * abs(tri["fN"])     # one-sided upper bound, same-ish sign unknown


# ---------------------------------------------------------------------------
def sigma_cm2(m_dm, fN, m_N):
    mu = m_dm * m_N / (m_dm + m_N)
    return (4.0/math.pi) * mu*mu * fN*fN * GEV2_TO_CM2, mu


def main():
    print("=" * 78)
    print("EW anchor (LIKE-FOR-LIKE): 2HDM+a charged-Higgs/W box + mediator triangle")
    print("  ref: Abe-Fujiwara-Hisano-Shoji 1910.09771 (JHEP 01(2020)114) + 1810.01039")
    print("=" * 78)
    g_haa, geo, port = g_phi_aa(M_HL, True)
    g_HAA, gH_geo, gH_port = g_phi_aa(M_H, False)
    print(f"\nTRILINEARS (from pinned potential, AFH 1910.09771 Eq.49):")
    print(f"  g_aah = {geo:+.2f}(geo) {port:+.2f}(portal) = {g_haa:+.2f} GeV "
          f"(portal = 2v c_th^2 c2: O(v), NOT tanb-enhanced; c1=c2 cancels tanb)")
    print(f"  g_aaH = {gH_geo:+.2f}(geo) {gH_port:+.2f}(portal) = {g_HAA:+.2f} GeV "
          f"(portal vanishes for c1=c2)")
    print(f"\nLOOP FUNCTIONS L = [dB0/dp^2]_{{p^2=m_chi^2}}  (AFH 1810.01039 Eq.3.36):")
    print(f"  L(m_chi,m_a={M_A:.0f}) = {L_loop(M_CHI,M_A):.4e} GeV^-2")
    print(f"  L(m_chi,m_A0={M_A0:.0f})= {L_loop(M_CHI,M_A0):.4e} GeV^-2")
    g_hchi, hc_a, hc_A0 = C_phi_chichi(M_HL, True)
    g_Hchi, _, _ = C_phi_chichi(M_H, False)
    print(f"\nEFFECTIVE DM-HIGGS SCALAR COUPLINGS (AFH Eq.3.36):")
    print(f"  g_hchi = {g_hchi:+.4e}  (a-loop {hc_a:+.3e} + A0-loop {hc_A0:+.3e})")
    print(f"  g_Hchi = {g_Hchi:+.4e}")
    print(f"  xi_q^h (alignment): up={XI_H['u']:.3f} down={XI_H['d']:.3f}  (SM-like ~1)")
    print(f"  xi_q^H: up={XI_HH['u']:.3f} down={XI_HH['d']:.3f}  (cot-b / tan-b)")

    print(f"\nCONTRIBUTION BREAKDOWN + sigma_SI:")
    out = {}
    for N, mN in (("p", M_PROTON), ("n", M_NEUTRON)):
        t = triangle_fN(N)
        sig_tot, mu = sigma_cm2(M_CHI, t["fN"], mN)
        sig_h, _    = sigma_cm2(M_CHI, t["fN_h"], mN)
        sig_H, _    = sigma_cm2(M_CHI, t["fN_H"], mN)
        box = box_fN_estimate(N)
        sig_with_box, _ = sigma_cm2(M_CHI, t["fN"] + math.copysign(box, t["fN"]), mN)
        out[N] = (sig_tot, sig_with_box)
        print(f"\n  --- nucleon {N} (m_N={mN:.5f}, mu={mu:.5f}) ---")
        print(f"    F_N^h={t['Fh']:.3f}  F_N^H={t['FH']:.3f} (tan-b enhanced)")
        print(f"    f_N(h-triangle) = {t['fN_h']:.4e} GeV^-2  -> sigma_h  = {sig_h:.3e} cm^2")
        print(f"    f_N(H-triangle) = {t['fN_H']:.4e} GeV^-2  -> sigma_H  = {sig_H:.3e} cm^2"
              f"  ({100*t['fN_H']/t['fN_h']:.1f}% of h in f_N)")
        print(f"    f_N(triangle tot)= {t['fN']:.4e} GeV^-2")
        print(f"    EW-box estimate |f_N| <= {box:.3e} (<=30% of triangle, FLAGGED)")
        print(f"    sigma_SI({N}) [triangle]      = {sig_tot:.3e} cm^2")
        print(f"    sigma_SI({N}) [triangle+box]  = {sig_with_box:.3e} cm^2 (upper)")

    print("\n" + "=" * 78)
    print("HEADLINE (triangle-dominated, h >> H; EW box = flagged estimate):")
    for N in ("p", "n"):
        print(f"  sigma_SI({N}) = {out[N][0]:.2e} cm^2  "
              f"(band ~{out[N][0]/3:.1e} - {out[N][0]*3:.1e}, factor ~3-5)")
    print("\n  >> Near/just below the neutrino floor; below current LZ/XENONnT.")
    print("  >> The from-scratch triangle derivation is the SOLE basis for this number.")
    print("     (Rescaling AFH's m_a~100 max by 1/m_a^4 -> ~1e-49 is a CRUDE BALLPARK")
    print("      ONLY, not an independent check: AFH max uses optimised couplings,")
    print("      1/m_a^4 ignores g_aah(m_a), and L is not ~1/m_a^2 at m_a~m_chi.)")
    print("\nCOVERAGE: matches LoopTools loop_topologies={chargedHiggs_W_box,")
    print("  mediator_triangle} at the LABEL level only.  run_eval.wls is a STUB (fp=fn=0);")
    print("  the fixture amp_reduced.m is BOX-ONLY (no h/H triangle).  Confirm the real")
    print("  FeynArts amplitude contains the triangle before comparing (derivation sec.7,10).")
    print("  Does NOT include the pseudoscalar x quark-loop box (that is hk_anchor.py).")
    print("  hk_anchor.py (~2e-54) is the WRONG-REGIME diagnostic floor (derivation sec.10).")


if __name__ == "__main__":
    main()
