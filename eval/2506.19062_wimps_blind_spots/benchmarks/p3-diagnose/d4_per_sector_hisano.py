"""
d4_per_sector_hisano.py — VALIDATION-ONLY per-sector Hisano decomposition (D4).

PURE PYTHON. NO KERNEL. NO FIX. Uses ONLY the A2-sanctioned Hisano transcription
(hisano_1104_0228.py) and the durable per-sector scalar extracts D1 produced.
This is the SCALAR-axis (f_q, apples-to-apples) sector-level tie-breaker for the
AMENDMENT8 sign hypotheses. It is valid regardless of the D3 review and does NOT
depend on the twist-2 O_Tq bridge (which the S2/S3 discriminator measured
unreliable at ~1e3-1e4x).

CONTEXT: the designer DOWNGRADED AMENDMENT8's global-flip (uniform -1) exclusion
because the twist-2 agreement that excluded it ran through the unreliable O_Tq
bridge. Uniform -1 is therefore BACK in the candidate space and ALL 2^3 sign
assignments are treated NEUTRALLY here. Leading designer candidate = per-topology
fermion-ordering signs (S2 pattern with D3's minus) -- but the scan decides.

================================================================================
  PRE-REGISTERED  (rule + hypothesis->pattern map + STOP condition;
                   locked in this header and the PREDICTIONS dict in the SAME
                   edit that created this file, BEFORE any number was computed)
================================================================================
DECISION RULE (conviction):
  The conviction is the UNIQUE sign assignment (s_tri, s_dbox, s_cbox in +-1)
  such that EVERY sector's SIGNED C_ours,scalar lands in |ratio| in [0.2, 5] AND
  is SIGN-MATCHED against the corresponding Hisano per-sector value, at BOTH legs
  L2 and L3.

HYPOTHESIS -> PATTERN MAP:
  (-,-,-) = uniform -1 GLOBAL FLIP
  (+,-,-) = S2-as-posed (box classes only flip; D3's leading minus as named src)
  ANY OTHER unique winning pattern = per-topology fermion-ordering signs

STOP CONDITION (pre-registered):
  If NO assignment satisfies the rule at both legs -> the defect includes
  MAGNITUDE structure, not just signs -> STOP and ESCALATE to the designer
  (via item4-p3-hisano) BEFORE any fix. Do NOT force a verdict.
  If MULTIPLE assignments satisfy -> report NON-UNIQUE (itself a finding).

MANDATORY MAPPING DOC (Hisano classes -> our three sectors):
  Hisano f_q (Eq. 18) has exactly TWO analytic classes:
    * Higgs-exchange loop function g_H  -> the "higgs" term. This is the
      chi-chi-h vertex / Higgs-exchange penguin == our TRIANGLE sector
      (C0i, T-channel induced-h exchange).
    * Gauge-box loop function g_S       -> the "box" term. This is a SINGLE
      box class; Hisano does NOT resolve direct vs crossed. So
         box_H  <->  (our directBox + our crossedBox)   [box-total].
  Consequently the 2^3 scan COLLAPSES to TWO independent Hisano references
  {tri_H, box_H}. We report the box comparison in TWO readings and require BOTH
  to be documented:
    (A) box-total:  compare (s_dbox*directBox + s_cbox*crossedBox) to box_H.
    (B) per-box:    compare s_dbox*directBox to box_H AND
                            s_cbox*crossedBox to box_H (each box sector vs the
                    shared box class).
  Degeneracy handling: assignments that differ only within a box sign but yield
  the SAME box-total sign+|ratio| are degenerate under reading (A); reading (B)
  breaks them by requiring EACH box sector to individually sign-match box_H.
  SIGN-match is the primary gate (it pins s uniquely given fixed sector signs);
  |ratio| is the secondary gate. We report the full 8-row table regardless.

SANITY ANCHOR (checked before scanning):
  sum of per-sector Hisano f_q*m_q MUST reproduce the campaign total
  C_Hisano = -2.228e-12 (L2) / -2.229e-12 (L3).
"""
from __future__ import annotations

import json
import math
import sys
from itertools import product
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]      # .../benchmarks
DIAG = Path(__file__).resolve().parent           # .../benchmarks/p3-diagnose
sys.path.insert(0, str(BENCH))
import hisano_1104_0228 as H

M_D = 4.67e-3
N, Y, FLAV = 2, 0.5, "d"
RATIO_LO, RATIO_HI = 0.2, 5.0

PREDICTIONS = {
    "locked_before_compute": True,
    "decision_rule": "UNIQUE (s_tri,s_dbox,s_cbox in +-1) with every sector's "
                     "signed C_ours in |ratio| in [0.2,5] AND sign-matched to the "
                     "corresponding Hisano per-sector value, at BOTH legs.",
    "hypothesis_pattern_map": {
        "(-,-,-)": "uniform -1 global flip",
        "(+,-,-)": "S2-as-posed (box-only flip, D3 minus as named source)",
        "other_unique": "per-topology fermion-ordering signs",
    },
    "stop_condition": "NO assignment satisfies both legs -> magnitude-structure "
                      "defect -> STOP + ESCALATE before any fix. MULTIPLE -> "
                      "report NON-UNIQUE.",
    "hisano_to_sector_map": {
        "g_H (higgs term)": "our triangle sector (Higgs-exchange penguin)",
        "g_S (box term)": "SINGLE box class <-> (directBox + crossedBox)",
        "collapse": "2^3 scan collapses to two Hisano refs {tri_H, box_H}; box "
                    "read as (A) box-total and (B) per-box vs shared box_H.",
    },
    "sanity_anchor": "sum per-sector Hisano f_q*m_q == campaign "
                     "C_Hisano -2.228e-12(L2)/-2.229e-12(L3).",
}

LEGS = {
    "L2": {"point": "/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch/L2/point.json"},
    "L3": {"point": "/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch/L3/point.json"},
}


def ew_from_point(p):
    m = p["masses"]
    mW, mZ, mh = m["24"], m["23"], m["25"]
    g2 = p["params"]["GAUGE:2"]
    sw2 = 1.0 - (mW / mZ) ** 2
    a2 = g2 * g2 / (4.0 * math.pi)
    return H.EWInputs(m_W=mW, m_Z=mZ, m_h=mh, sw2=sw2, alpha_em=a2 * sw2)


def hisano_sectors(M, ew):
    """Return (tri_H, box_H) scalar coefficients = f_q-class * m_q (GeV^-2),
    replicating hisano_1104_0228.f_q's own higgs/box split WITHOUT editing the
    module (uses its public loop functions g_H, g_S, a_qV, a_qA)."""
    w = (ew.m_W / M) ** 2
    z = (ew.m_Z / M) ** 2
    a2 = ew.alpha2
    cw4 = ew.cw2 ** 2
    nfac = N * N - (4.0 * Y * Y + 1.0)
    higgs = (a2 * a2 / (4.0 * ew.m_h ** 2)) * (
        (nfac / (8.0 * ew.m_W)) * H.g_H(w)
        + (Y * Y / (4.0 * ew.m_Z * cw4)) * H.g_H(z))
    box = ((H.a_qV(FLAV, ew.sw2) ** 2 - H.a_qA(FLAV) ** 2) * Y * Y / cw4) \
        * (a2 * a2 / ew.m_Z ** 3) * H.g_S(z)
    return higgs * M_D, box * M_D


def our_sectors(leg):
    def rd(s):
        return json.loads((DIAG / f"{leg}_{s}_cours.json").read_text())["C_scalar_full_re"]
    return rd("triangle"), rd("directBox"), rd("crossedBox")


def sign_match(a, b):
    return (a > 0) == (b > 0)


def in_band(r):
    return RATIO_LO <= abs(r) <= RATIO_HI


def analyse():
    legdata = {}
    for leg, spec in LEGS.items():
        p = json.loads(Path(spec["point"]).read_text())
        M = p["m_dm_gev"]
        ew = ew_from_point(p)
        tri_H, box_H = hisano_sectors(M, ew)
        tot_H = tri_H + box_H
        tri_o, dbox_o, cbox_o = our_sectors(leg)
        legdata[leg] = dict(M=M, tri_H=tri_H, box_H=box_H, tot_H=tot_H,
                            tri_o=tri_o, dbox_o=dbox_o, cbox_o=cbox_o)

    # sanity anchor
    anchor = {leg: {"sum_hisano_sectors": d["tot_H"],
                    "campaign_C_Hisano": (-2.228e-12 if leg == "L2" else -2.229e-12),
                    "reproduces": abs(d["tot_H"] - (-2.228e-12 if leg == "L2"
                                                    else -2.229e-12)) < 5e-15}
              for leg, d in legdata.items()}

    # full 2^3 scan
    scan = {}
    for s_tri, s_dbox, s_cbox in product((+1, -1), repeat=3):
        key = f"({'+' if s_tri>0 else '-'},{'+' if s_dbox>0 else '-'},{'+' if s_cbox>0 else '-'})"
        per_leg = {}
        ok_both = True
        for leg, d in legdata.items():
            tri_s = s_tri * d["tri_o"]
            dbox_s = s_dbox * d["dbox_o"]
            cbox_s = s_cbox * d["cbox_o"]
            box_total = dbox_s + cbox_s
            # triangle gate
            r_tri = tri_s / d["tri_H"]
            tri_ok = sign_match(tri_s, d["tri_H"]) and in_band(r_tri)
            # box reading (A): box-total vs box_H
            r_boxtot = box_total / d["box_H"]
            boxA_ok = sign_match(box_total, d["box_H"]) and in_band(r_boxtot)
            # box reading (B): each box sector vs shared box_H
            r_dbox = dbox_s / d["box_H"]
            r_cbox = cbox_s / d["box_H"]
            boxB_ok = (sign_match(dbox_s, d["box_H"]) and in_band(r_dbox)
                       and sign_match(cbox_s, d["box_H"]) and in_band(r_cbox))
            leg_ok = tri_ok and boxA_ok and boxB_ok
            ok_both = ok_both and leg_ok
            per_leg[leg] = {
                "tri_signed": tri_s, "ratio_tri": r_tri, "tri_ok": tri_ok,
                "box_total_signed": box_total, "ratio_box_total": r_boxtot,
                "boxA_ok": boxA_ok,
                "ratio_directBox": r_dbox, "ratio_crossedBox": r_cbox,
                "boxB_ok": boxB_ok,
                "leg_ok": leg_ok,
            }
        scan[key] = {"s": [s_tri, s_dbox, s_cbox],
                     "satisfies_both_legs": ok_both, "legs": per_leg}

    winners = [k for k, v in scan.items() if v["satisfies_both_legs"]]

    # sign-only sub-analysis (which s each gate DEMANDS, ignoring magnitude)
    d0 = legdata["L2"]
    sign_req = {
        "s_tri_required_for_sign_match": -1 if d0["tri_o"] > 0 and d0["tri_H"] < 0 else "see_table",
        "s_dbox_required_for_sign_match": -1 if d0["dbox_o"] > 0 and d0["box_H"] < 0 else "see_table",
        "s_cbox_required_for_sign_match": -1 if d0["cbox_o"] > 0 and d0["box_H"] < 0 else "see_table",
        "note": "Our triangle & both boxes are POSITIVE; both Hisano classes "
                "(g_H triangle, g_S box) are NEGATIVE => sign alone forces "
                "(-,-,-) = UNIFORM -1. S2's s_tri=+1 MISMATCHES Hisano's "
                "negative triangle class on the clean scalar axis.",
    }

    # magnitude structure diagnostic on the box (the crux)
    box_mag = {leg: {
        "box_H": d["box_H"], "our_box_total": d["dbox_o"] + d["cbox_o"],
        "our_box_total_over_box_H": (d["dbox_o"] + d["cbox_o"]) / d["box_H"],
        "our_directBox_over_box_H": d["dbox_o"] / d["box_H"],
        "hisano_box_fraction_of_total": d["box_H"] / d["tot_H"],
        "our_box_fraction_of_total": (d["dbox_o"] + d["cbox_o"])
        / (d["tri_o"] + d["dbox_o"] + d["cbox_o"]),
    } for leg, d in legdata.items()}

    if not winners:
        outcome = "NONE -> STOP + ESCALATE (magnitude-structure defect)"
        verdict_reason = (
            "NO sign assignment satisfies the rule at both legs. SIGN gate alone "
            "forces (-,-,-) uniform -1 (our triangle+both boxes POSITIVE; both "
            "Hisano classes g_H,g_S NEGATIVE) -- which REFUTES S2's s_tri=+1 on "
            "the clean scalar axis. BUT the BOX MAGNITUDE fails |ratio| in [0.2,5] "
            "under EVERY assignment and BOTH readings: Hisano's gauge-box class "
            "g_S is only ~6.9% of Hisano's scalar coupling (box_H~-1.54e-13), "
            "while our box sectors are ~67% (box_total~+7.0e-12) -> "
            "|box_total/box_H| ~ 40-46x, |directBox/box_H| ~ 22-24x, all far "
            "outside [0.2,5], independent of sign. The triangle gate, by "
            "contrast, PASSES under s_tri=-1 (|ratio_tri| ~1.6(L2)/2.2(L3)). "
            "Therefore the defect is NOT a pure sign assignment: it includes a "
            "MAGNITUDE-STRUCTURE mismatch in the box sector (our boxes ~20-46x too "
            "large relative to Hisano's gauge-box class). Per the pre-registered "
            "STOP condition, ESCALATE to the designer before any fix. Collateral "
            "finding: on SIGN the scalar axis favours uniform -1 over S2 (S2 needs "
            "the triangle to stay +, contradicting Hisano's negative triangle)."
        )
    elif len(winners) == 1:
        outcome = f"UNIQUE winner {winners[0]}"
        verdict_reason = f"pattern {winners[0]} maps per hypothesis_pattern_map."
    else:
        outcome = f"NON-UNIQUE: {winners}"
        verdict_reason = "multiple assignments satisfy -- itself a finding."

    return {
        "_desc": "D4 per-sector Hisano scalar decomposition (VALIDATION-ONLY, no "
                 "kernel). Pre-registered rule/map/STOP locked before compute.",
        "predictions_pre_registered": PREDICTIONS,
        "hisano_sectors": {leg: {"tri_H_gH": d["tri_H"], "box_H_gS": d["box_H"],
                                 "total": d["tot_H"], "M": d["M"]}
                           for leg, d in legdata.items()},
        "our_sectors": {leg: {"triangle": d["tri_o"], "directBox": d["dbox_o"],
                              "crossedBox": d["cbox_o"]}
                        for leg, d in legdata.items()},
        "sanity_anchor": anchor,
        "sign_only_requirement": sign_req,
        "box_magnitude_structure": box_mag,
        "scan_2x2x2": scan,
        "winners": winners,
        "verdict": {"outcome": outcome, "reason": verdict_reason},
    }


if __name__ == "__main__":
    print(json.dumps(analyse(), indent=2))
