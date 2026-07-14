"""
p3_compare.py — VALIDATION-ONLY P3 comparison harness (Ruling 4).

Brings OUR pipeline Wilson coefficients (C_ours, extracted independently and
saved to a durable JSON) and the Hisano 1104.0228 predictions (C_Hisano,
hisano_1104_0228.py) into ONE common convention, then reports, per axis and per
MS leg: C_ours, C_Hisano, ratio, and sign agreement.

It DELIBERATELY does NOT print a pass/fail verdict — the pre-registered bars
(|ratio| in [0.2,5] AND same sign at both legs on both axes) are adjudicated by
the design authority, not by this harness (Ruling 4).

CONVENTION BRIDGE (the trap)
----------------------------
Scalar (gH axis, DECISIVE):
  Hisano L ⊃ f_q m_q (chibar chi)(qbar q)  ⇒  coefficient of (chibar chi)(qbar q)
  is  C_scalar^Hisano = f_q * m_q.  Our pipeline's C_scalar (R_S_S, rotated) is
  the coefficient of that SAME operator in the amplitude.  So the ratio is
  formed directly on the (chibar chi)(qbar q) coefficient, in GeV^-2, with NO
  extra factor.  (We use Re(C_ours) — the amplitude carries a small imaginary
  part; an overall-i amplitude convention would swap Re<->Im, flagged below.)

Twist-2 (free second axis):
  Origin/main's C_twist2 is the coefficient of O_Tq = (chibar chi)(qbar
  gamma.P_chi q), a GeV^-3 quantity.  Hisano's g^(1,2)_q (GeV^-3) multiply
  (chibar id gamma chi)O/M and (chibar id id chi)O/M^2.  The DIMENSIONALLY
  CONSISTENT bridge is the static-limit matrix-element matching (spinor norm
  ubar u = 2m; chi at rest p=(M,0); quark at rest q=(m_q,0)):
     <O_Tq>      = (2M)(P_chi . <qbar gamma q>) = (2M)(p . 2q)      = 4 M^2 m_q
     <Hisano T1> = (1/M)(2 p^mu p^nu)(2 q_mu q_nu - g_munu m_q^2/2) = 3 M m_q^2
     <Hisano T2> = (1/M^2)(p^mu p^nu 2M)(2 q_mu q_nu - g_munu m_q^2/2) = 3 M m_q^2
  => amplitude equality  c_OTq * 4 M^2 m_q = (g1+g2) * 3 M m_q^2
  => c_OTq = (3/4)(g1+g2) m_q / M   (both sides GeV^-3, ratio dimensionless)
  CAVEAT (measured): the same bridge applied to the round-2 canonical
  cross-instrument pair (old-contraction 4.096e-9 vs contracted-instrument
  g_sum 5.643e-5 at m_chi=132.69) leaves a residual factor 2.75 — the fit
  kinematics sit at velocity ~0.3, not the exact static limit — so the twist-2
  ratio carries an O(3) operator-normalization uncertainty pending the item-4
  C^(1)/C^(2) split.  The raw g/M-convention juxtaposition (the historical
  ~100x "convention factor") is ALSO reported but labeled dimensional
  (GeV) — it is NOT a physics ratio.

EW inputs are read from the SAME SPheno spectrum that fed our amplitude (m_W,
m_Z, m_h, g_2, sin^2 theta_W via the amplitude's own ctw=m_W/m_Z), so any
residual difference is amplitude construction, not an input mismatch.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hisano_1104_0228 as H

M_D = 4.67e-3   # down-quark mass (GeV), matching the pipeline external quark


def ew_from_point(point: dict) -> tuple[H.EWInputs, dict]:
    """Build Hisano EW inputs from the spectrum, matching the amplitude's own
    conventions (on-shell sin^2 theta_W = 1-(m_W/m_Z)^2, g_2 = GAUGE:2)."""
    masses = point["masses"]
    params = point["params"]
    m_W = masses["24"]
    m_Z = masses["23"]
    m_h = masses["25"]
    g2 = params["GAUGE:2"]
    sw2 = 1.0 - (m_W / m_Z) ** 2          # on-shell (amplitude uses ctw=m_W/m_Z)
    alpha2 = g2 * g2 / (4.0 * math.pi)
    ew = H.EWInputs(m_W=m_W, m_Z=m_Z, m_h=m_h, sw2=sw2,
                    alpha_em=alpha2 * sw2)  # so ew.alpha2 == g2^2/4pi
    meta = {"m_W": m_W, "m_Z": m_Z, "m_h": m_h, "g2": g2, "sw2": sw2,
            "alpha2": alpha2}
    return ew, meta


def compare_leg(cours: dict, point: dict, m_chi: float) -> dict:
    ew, ewmeta = ew_from_point(point)
    n, Y, q = 2, 0.5, "d"          # pure doublet / Higgsino, down quark

    # ---- OURS ----
    C_scalar_ours = cours["C_scalar_full_re"]        # gH axis, rotated R_S_S
    C_twist2_ours = cours["C_twist2_re"]             # free axis, O_Tq

    # ---- HISANO ----
    C_scalar_his = H.C_scalar_hisano(m_chi, M_D, q, n, Y, ew)   # = f_q*m_q, GeV^-2
    f_q_val = H.C_Q_hisano(m_chi, q, n, Y, ew)                  # = f_q, GeV^-3
    g_sum, g_over_M = H.C_twist2_hisano(m_chi, q, n, Y, ew)     # (g1+g2), (g1+g2)/M

    def ratio(a, b):
        return a / b if b != 0 else float("inf")

    def sign_agree(a, b):
        return (a > 0) == (b > 0)

    return {
        "m_chi": m_chi,
        "ew_inputs": ewmeta,
        "scalar": {
            "axis": "gH (decisive)",
            "operator": "(chibar chi)(qbar q), coefficient in GeV^-2",
            "C_ours": C_scalar_ours,
            "C_ours_full_im": cours.get("C_scalar_full_im"),
            "C_hisano": C_scalar_his,
            "hisano_f_q_GeV^-3": f_q_val,
            "ratio_ours_over_hisano": ratio(C_scalar_ours, C_scalar_his),
            "sign_agree": sign_agree(C_scalar_ours, C_scalar_his),
        },
        "twist2": {
            "axis": "gT1+gT2 (free second axis)",
            "note": "ours=O_Tq single contracted coeff (origin/main, GeV^-3); "
                    "primary ratio uses the static-limit bridge "
                    "C_hisano_OTq_equiv = (3/4)(g1+g2) m_q/M (dimensionless "
                    "ratio, O(3) normalization caveat — see module docstring); "
                    "the g/M juxtaposition is dimensional (GeV), kept only for "
                    "continuity with the historical ~100x convention factor.",
            "C_ours": C_twist2_ours,
            "C_hisano_g_sum_GeV^-3": g_sum,
            "C_hisano_OTq_equiv_GeV^-3": 0.75 * g_sum * M_D / m_chi,
            "ratio_ours_over_hisano_OTq": ratio(C_twist2_ours,
                                                0.75 * g_sum * M_D / m_chi),
            "sign_agree": sign_agree(C_twist2_ours, g_sum),
            "C_hisano_g_over_M_GeV^-4_DIMENSIONAL": g_over_M,
            "ratio_ours_over_hisano_gM_DIMENSIONAL_GeV":
                ratio(C_twist2_ours, g_over_M),
        },
        "instrument": {
            "si_shift_rel": cours.get("si_shift_rel"),
            "full_basis_completeness_rel_residual":
                cours.get("full_basis_completeness_rel_residual"),
            "C_scalar_3op_re": cours.get("C_scalar_3op_re"),
            "C_chi_vector_re": cours.get("C_chi_vector_re"),
        },
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    # argv: legtag cours.json point.json  [legtag cours.json point.json ...]
    results = {}
    it = iter(argv)
    for tag, cpath, ppath in zip(it, it, it):
        cours = json.loads(Path(cpath).read_text())
        point = json.loads(Path(ppath).read_text())
        m_chi = point["m_dm_gev"]
        results[tag] = compare_leg(cours, point, m_chi)

    print("=" * 78)
    print("P3 comparison — MEASURED (verdict adjudicated by design authority, NOT here)")
    print("=" * 78)
    for tag, r in results.items():
        s = r["scalar"]; t = r["twist2"]
        print(f"\n[{tag}]  m_chi = {r['m_chi']:.3f} GeV   (m_h={r['ew_inputs']['m_h']:.2f}, "
              f"sw2={r['ew_inputs']['sw2']:.5f}, alpha2={r['ew_inputs']['alpha2']:.5f})")
        print(f"  SCALAR (gH): C_ours={s['C_ours']:+.5e}  C_Hisano={s['C_hisano']:+.5e}"
              f"  ratio={s['ratio_ours_over_hisano']:+.4g}  sign_agree={s['sign_agree']}")
        print(f"               (Hisano f_q={s['hisano_f_q_GeV^-3']:+.5e} GeV^-3, "
              f"ours Im={s['C_ours_full_im']:+.3e})")
        print(f"  TWIST2:      C_ours={t['C_ours']:+.5e}  "
              f"C_Hisano(OTq-equiv)={t['C_hisano_OTq_equiv_GeV^-3']:+.5e}"
              f"  ratio={t['ratio_ours_over_hisano_OTq']:+.4g}"
              f"  sign_agree={t['sign_agree']}")
        print(f"               (g_sum={t['C_hisano_g_sum_GeV^-3']:+.5e} GeV^-3; "
              f"dimensional g/M juxtaposition="
              f"{t['ratio_ours_over_hisano_gM_DIMENSIONAL_GeV']:+.4g} GeV)")
    outp = Path(argv[-1]).parent / "p3_comparison_results.json" if False else None
    print("\n" + json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    main()
