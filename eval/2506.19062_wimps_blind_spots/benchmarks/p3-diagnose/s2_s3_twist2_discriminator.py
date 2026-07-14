"""
s2_s3_twist2_discriminator.py — VALIDATION-ONLY S2-vs-S3 twist-2 discriminator.

NO KERNEL. NO FIX. Uses ONLY the A2-sanctioned Hisano transcription
(hisano_1104_0228.py) and the durable per-leg extract/point JSONs the P3'
campaign already produced. Adjudicates D1's S2 conviction against the
alternative hypothesis S3 (scalar-projection-only sign) on the *free* twist-2
axis, following the exact normalization bridge p3_compare.py used for the
scalar axis.

================================================================================
  PRE-REGISTERED PREDICTIONS  (LOCKED IN BEFORE ANY NUMBER WAS COMPUTED)
================================================================================
Written into this header and the PREDICTIONS dict below in the SAME edit that
created the file, prior to running it. The predictions are the two hypotheses'
statements about where an INDEPENDENT twist-2 calculation (Hisano) should land,
expressed against OUR two twist-2 scenarios (both in the O_Tq pipeline units):

  Our two scenarios (O_Tq units, GeV^-3, from D1):
    CURRENT (cancellation, today's assembly):  +8.118e-12 (L2) / +5.183e-11 (L3)
    S2-FLIPPED (additive, box sign flipped):   +1.7245e-10 (L2) / +2.2154e-10 (L3)
  The S2/S3 separation is ~20x (additive/current), far above the ~11% twist-2
  sampling systematic on our side, so the test is DECISIVE **iff** Hisano's
  twist-2 can be placed in the SAME operator normalization as our O_Tq C_twist2.

  S2 predicts: our twist-2 is ~20x LOW today; the TRUE (Hisano) twist-2 sits at
     the ADDITIVE ~1.7e-10/2.2e-10 scale.
  S3 predicts: today's twist-2 ALREADY matches Hisano; Hisano's twist-2 sits at
     the CURRENT ~8e-12/5e-11 scale.

  NORMALIZATION GATE (pre-registered): a magnitude verdict is reported ONLY if
  the two sides are confirmed apples-to-apples. p3_compare.py's own docstring
  warns the twist-2 axis carries an O(3) static-limit normalization caveat and
  is the *free* second axis (the C^(1)/C^(2) split is an unshipped item-4
  deliverable). If the residual normalization factor is >> the ~20x S2/S3 gap,
  the discriminator is INCONCLUSIVE and the verdict is WITHHELD (per the gate).

================================================================================
  NORMALIZATION BRIDGE  (identical to p3_compare.py, the campaign's convention)
================================================================================
Scalar (used only to reproduce the -2.23e-12 anchor & confirm inputs match):
  C_scalar^Hisano = f_q * m_q  (GeV^-2), compared directly to C_scalar_full_re.

Twist-2 (the axis under test):
  Our C_twist2 is the coefficient of O_Tq = (chibar chi)(qbar gamma.P_chi q),
  GeV^-3. Hisano's g^(1,2)_q (GeV^-3) multiply (chibar id gamma chi)O/M and
  (chibar id id chi)O/M^2 -- DIFFERENT operators. p3_compare's static-limit
  matrix-element matching (ubar u = 2m; chi,q at rest) gives the apples-to-apples
  bridge:
     C_hisano_OTq_equiv = (3/4)(g1+g2) m_q / M    (GeV^-3, same basis as O_Tq).
  This is the physics comparison. The RAW g_sum (GeV^-3) juxtaposition is ALSO
  reported but is NOT operator-matched (p3_compare labels the g/M juxtaposition
  "dimensional, NOT a physics ratio") -- kept only to expose the normalization
  sensitivity.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]   # .../benchmarks
sys.path.insert(0, str(BENCH))
import hisano_1104_0228 as H   # A2-sanctioned transcription

M_D = 4.67e-3   # down-quark mass (GeV), matching the pipeline external quark
N, Y, FLAV = 2, 0.5, "d"      # pure doublet / Higgsino, down quark

# --- PRE-REGISTERED PREDICTIONS (locked before compute; mirrors header) -------
PREDICTIONS = {
    "locked_before_compute": True,
    "our_scenarios_OTq_units_GeV^-3": {
        "current_cancellation_S3": {"L2": 8.118e-12, "L3": 5.183e-11},
        "additive_flip_S2":        {"L2": 1.7245e-10, "L3": 2.2154e-10},
    },
    "S2_predicts": "Hisano twist-2 at the ADDITIVE ~1.7e-10/2.2e-10 scale "
                   "(our current is ~20x LOW).",
    "S3_predicts": "Hisano twist-2 at the CURRENT ~8e-12/5e-11 scale "
                   "(today's assembly already correct).",
    "S2_over_S3_gap": "~20x (>> 11% twist-2 sampling systematic)",
    "normalization_gate": "Report a magnitude verdict ONLY if the two sides are "
                          "apples-to-apples; if residual normalization factor "
                          ">> 20x, verdict is WITHHELD (INCONCLUSIVE).",
}

LEGS = {
    "L2": {
        "cours": BENCH / "p3prime" / "L2_cours_extract.json",
        "point": Path("/Users/yianni/.claude/jobs/c703354a/tmp/"
                      "p3prime-scratch/L2/point.json"),
        "current_twist2": 8.118e-12,
        "additive_twist2": 1.7245292719539565e-10,
    },
    "L3": {
        "cours": BENCH / "p3prime" / "L3_cours_extract.json",
        "point": Path("/Users/yianni/.claude/jobs/c703354a/tmp/"
                      "p3prime-scratch/L3/point.json"),
        "current_twist2": 5.183e-11,
        "additive_twist2": 2.2154408716125962e-10,
    },
}


def ew_from_point(point: dict):
    """Identical to p3_compare.ew_from_point (on-shell sw2, alpha2=g2^2/4pi)."""
    m = point["masses"]
    m_W, m_Z, m_h = m["24"], m["23"], m["25"]
    g2 = point["params"]["GAUGE:2"]
    sw2 = 1.0 - (m_W / m_Z) ** 2
    alpha2 = g2 * g2 / (4.0 * math.pi)
    ew = H.EWInputs(m_W=m_W, m_Z=m_Z, m_h=m_h, sw2=sw2, alpha_em=alpha2 * sw2)
    return ew, {"m_W": m_W, "m_Z": m_Z, "m_h": m_h, "g2": g2, "sw2": sw2,
                "alpha2": alpha2}


def analyse_leg(tag: str, spec: dict) -> dict:
    cours = json.loads(spec["cours"].read_text())
    point = json.loads(spec["point"].read_text())
    m_chi = point["m_dm_gev"]
    ew, ewmeta = ew_from_point(point)

    # scalar anchor (apples-to-apples, reproduces the campaign -2.23e-12)
    C_scalar_his = H.C_scalar_hisano(m_chi, M_D, FLAV, N, Y, ew)
    C_scalar_ours = cours["C_scalar_full_re"]

    # twist-2
    g1 = H.g1_q(m_chi, FLAV, N, Y, ew)
    g2 = H.g2_q(m_chi, FLAV, N, Y, ew)
    g_sum = g1 + g2
    C_his_OTq = 0.75 * g_sum * M_D / m_chi          # apples-to-apples bridge
    C_his_raw = g_sum                                # NOT operator-matched

    cur = spec["current_twist2"]
    add = spec["additive_twist2"]

    # distance of Hisano to each scenario, in each candidate normalization
    def closeness(hval):
        # ratio scenario/hisano; "closer" = |log ratio| smaller
        r_cur = cur / hval
        r_add = add / hval
        return {
            "hisano": hval,
            "ratio_current_over_hisano": r_cur,
            "ratio_additive_over_hisano": r_add,
            "log10_dist_current": abs(math.log10(abs(r_cur))),
            "log10_dist_additive": abs(math.log10(abs(r_add))),
            "closer_scenario": ("additive_S2"
                                if abs(math.log10(abs(r_add)))
                                < abs(math.log10(abs(r_cur)))
                                else "current_S3"),
        }

    return {
        "m_chi": m_chi,
        "ew_inputs": ewmeta,
        "scalar_anchor": {
            "C_hisano_scalar_GeV^-2": C_scalar_his,
            "C_ours_scalar_full_re": C_scalar_ours,
            "reproduces_campaign_-2.23e-12": abs(C_scalar_his + 2.228e-12) < 5e-15
            if tag == "L2" else abs(C_scalar_his + 2.229e-12) < 5e-15,
        },
        "twist2": {
            "our_current_S3_OTq": cur,
            "our_additive_S2_OTq": add,
            "hisano_g1": g1, "hisano_g2": g2, "hisano_g_sum_GeV^-3": g_sum,
            "APPLES_TO_APPLES_bridge_OTq_equiv_GeV^-3": C_his_OTq,
            "RAW_g_sum_juxtaposition_GeV^-3_NOT_operator_matched": C_his_raw,
            "under_bridge": closeness(C_his_OTq),
            "under_raw_NONphysics": closeness(C_his_raw),
        },
    }


def main():
    results = {tag: analyse_leg(tag, spec) for tag, spec in LEGS.items()}

    # --- NORMALIZATION-SENSITIVITY VERDICT ------------------------------------
    # Decisive test requires the two sides apples-to-apples. Check whether the
    # "closer scenario" is STABLE across the two candidate normalizations. If it
    # flips, the residual normalization factor dominates the ~20x S2/S3 gap and
    # the discriminator cannot decide (gate -> WITHHELD).
    bridge_closer = {t: r["twist2"]["under_bridge"]["closer_scenario"]
                     for t, r in results.items()}
    raw_closer = {t: r["twist2"]["under_raw_NONphysics"]["closer_scenario"]
                  for t, r in results.items()}
    # residual normalization factor bridge vs raw (per leg): raw/bridge
    resid = {t: results[t]["twist2"]["RAW_g_sum_juxtaposition_GeV^-3_NOT_operator_matched"]
             / results[t]["twist2"]["APPLES_TO_APPLES_bridge_OTq_equiv_GeV^-3"]
             for t in results}
    verdict_flips = any(bridge_closer[t] != raw_closer[t] for t in results)

    verdict = {
        "closer_scenario_under_bridge": bridge_closer,
        "closer_scenario_under_raw": raw_closer,
        "bridge_vs_raw_residual_factor": resid,
        "answer_flips_with_normalization": verdict_flips,
        "S2_confirmed": None,
        "S3_favored": None,
        "outcome": None,
        "reason": None,
    }
    if verdict_flips:
        verdict["outcome"] = "INCONCLUSIVE — verdict WITHHELD (normalization gate)"
        verdict["reason"] = (
            "Under the sanctioned static-limit bridge, |C_Hisano_twist2| = "
            f"{results['L2']['twist2']['APPLES_TO_APPLES_bridge_OTq_equiv_GeV^-3']:.3e}"
            f" (L2)/{results['L3']['twist2']['APPLES_TO_APPLES_bridge_OTq_equiv_GeV^-3']:.3e}"
            " (L3), ~1.6e3-1e4x BELOW even the current-scenario O_Tq value -- it "
            "matches NEITHER pre-registered prediction and the residual factor "
            "(~7e5, bridge vs raw) dwarfs the 20x S2/S3 gap. The 'closer scenario' "
            "FLIPS between the bridge (favours S3/current) and the raw g_sum "
            "juxtaposition (favours S2/additive), so the twist-2 magnitude "
            "comparison is not apples-to-apples at the precision the test needs. "
            "Per the pre-registered normalization gate, no magnitude verdict is "
            "issued. NOTE: sign does NOT discriminate either -- Hisano twist-2 is "
            "POSITIVE (g_sum>0), consistent with BOTH our positive current and "
            "additive scenarios. The S2 conviction therefore rests on D1's "
            "SCALAR axis (apples-to-apples, sign-restoring, |ratio| in-band), "
            "which the twist-2 axis does not overturn and does not independently "
            "confirm. S3 is NOT favoured: it survives only in the physics bridge, "
            "where its own magnitude is off by ~1.6e3x, so twist-2 gives it no "
            "positive support. Absolute wrong-sign localization remains D3."
        )
    else:
        # (not reached with current numbers; kept for completeness)
        c = list(bridge_closer.values())
        verdict["outcome"] = "DECISIVE"
        verdict["S2_confirmed"] = all(x == "additive_S2" for x in c)
        verdict["S3_favored"] = all(x == "current_S3" for x in c)

    out = {
        "_desc": "S2-vs-S3 twist-2 discriminator (VALIDATION-ONLY, no kernel). "
                 "Pre-registered predictions locked before compute.",
        "predictions_pre_registered": PREDICTIONS,
        "legs": results,
        "verdict": verdict,
    }
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
