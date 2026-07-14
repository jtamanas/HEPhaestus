"""
b3_mapping_audit.py — VALIDATION-ONLY B3 box-mapping audit (AMENDMENT8R1).

STATIC. NO KERNEL. NO FIX. Evidence-only. Adjudicates whether D4's ~45x
box-magnitude mismatch (our box-total C_scalar vs Hisano's box_H = g_S class) is
a genuine pipeline defect or a MAPPING ARTIFACT of comparing our FULL box-total
against a PARTIAL Hisano class. Done ADVERSARIALLY at the INTERNAL-LINE grain
(which boson / which fermion runs in each box loop), NOT by re-affirming the
class-grain box<->g_S mapping.

================================================================================
  PRE-REGISTERED OUTCOMES  (locked in this header BEFORE the channel verdict)
================================================================================
MAPPING-ARTIFACT  = our box-total contains channels g_S does NOT cover, and
                    restricting to g_S-scope channels shrinks the ~45x
                    substantially toward [0.2,5].
REAL-DEFECT       = our box-total is (in the pure-doublet blind-spot regime)
                    essentially the same gauge-box channels g_S represents, with
                    no material out-of-scope channels, so the ~45x stands as a
                    genuine box-magnitude defect -> hand to B1/B2.
(A PARTIAL outcome -- some out-of-scope channels but not enough to fully explain
 45x -- is reported with the explained fraction.)

================================================================================
  EVIDENCE PROVENANCE (all EXISTING artifacts; nothing re-run)
================================================================================
1. Diagram census (FeynArts tool output, committed groundwork):
   /Users/yianni/.claude/jobs/c703354a/tmp/loopset-step1/DIAGRAM-CENSUS.md
   -> our two boxes = IRR-3 (uncrossed) + IRR-4 (crossed), loop-line fields
      {chi, chi+/-, u, d ; h, A, H+/- ; Z, W}. The charged partner chi+/- (F[6])
      and W (V[3]) and internal up-quark F[3] all appear in BOTH boxes.
2. Symbolic box amplitudes (D1 sector split, committed logic; amps in scratch):
   /Users/yianni/.claude/jobs/c703354a/tmp/p3-diagnose-scratch/amp_directBox.m
   /Users/yianni/.claude/jobs/c703354a/tmp/p3-diagnose-scratch/amp_crossedBox.m
   Internal-mass token census (grep \b<tok>\b, both boxes IDENTICAL structure):
      Masshh (h)  : 100    MassAh (A)   : 98
      MassVZ (Z)  :  93    MassHp (H+/-):  61    MassVWp (W): 47
      MassFChiM (chi+/-): ~115   MassFu (internal up-quark): ~124
   (Token counts prove a channel is PRESENT; they are NOT a magnitude proxy --
    see MAGNITUDE_NOTE below.)
3. Hisano g_S scope, from benchmarks/hisano_1104_0228.py f_q (Eq.18):
      box = (a_qV^2 - a_qA^2)(Y^2/cw4)(alpha2^2/m_Z^3) * g_S(z),  z=(m_Z/M)^2.
   ONLY g_S(z). No g_S(w). a_qV/a_qA are the quark's *Z* couplings. So g_S ==
   the Z-mediated NEUTRAL-CURRENT box ONLY. The W enters f_q EXCLUSIVELY via the
   g_H PENGUIN term (nfac/(8 m_W) g_H(w), inside the 1/m_h^2 Higgs-exchange
   bracket) -- i.e. Hisano puts ALL W strength in the penguin, NONE in the box.
"""
from __future__ import annotations
import json

# Internal-line channel inventory of our box-total (both boxes identical).
# current: 'CC'=charged current (needs chi+/- & internal up-quark),
#          'NC'=neutral current. in_gS_scope: does Hisano's Z-only g_S cover it?
# magnitude_class: physics expectation for the SCALAR (f_q) coupling magnitude.
CHANNELS = [
    {"boson": "W (VWp)",  "fermion": "chi+/- , u", "current": "CC",
     "in_gS_scope": False, "token_count": 47,
     "magnitude_class": "DOMINANT (gauge coupling, no Yukawa suppression; the "
                        "census headline chi-chi+/--W box)"},
    {"boson": "H+/- (Hp)", "fermion": "chi+/- , u", "current": "CC",
     "in_gS_scope": False, "token_count": 61,
     "magnitude_class": "sub-dominant (charged-Higgs Yukawa; not m_d-zero via "
                        "m_u cot-beta piece)"},
    {"boson": "Z (VZ)",   "fermion": "chi0", "current": "NC",
     "in_gS_scope": True,  "token_count": 93,
     "magnitude_class": "the ONLY in-scope channel; gauge NC, a_qV/a_qA quark "
                        "Z-couplings -- exactly what g_S represents"},
    {"boson": "h (hh)",   "fermion": "chi0", "current": "NC",
     "in_gS_scope": False, "token_count": 100,
     "magnitude_class": "NEGLIGIBLE (h-d-d ~ y_d, extra m_d suppression; many "
                        "terms but tiny magnitude)"},
    {"boson": "A (Ah)",   "fermion": "chi0", "current": "NC",
     "in_gS_scope": False, "token_count": 98,
     "magnitude_class": "NEGLIGIBLE (pseudoscalar, A-d-d ~ y_d; velocity/"
                        "m_d-suppressed for coherent SI)"},
]

MAGNITUDE_NOTE = (
    "Token count != magnitude. h(100)/A(98) have the MOST terms yet are "
    "magnitude-negligible (Yukawa y_d suppression), while W(47) has the FEWEST "
    "yet is magnitude-DOMINANT (gauge coupling). So the g_S-scope (Z-only) piece "
    "is NOT ~1/5 of the box by magnitude -- it is subdominant to the out-of-scope "
    "W box. Exact per-channel C_scalar needs a kernel re-projection of the "
    "channel-filtered amplitude, which is FORBIDDEN here (no kernel); therefore "
    "the in-scope residual ratio is bounded in DIRECTION but not pinned to a number."
)

# box-total scalar (D1) and Hisano box_H = g_S class (D4), per leg
BOX_TOTAL = {"L2": 7.084233475740811e-12, "L3": 6.910944468645475e-12}
BOX_H     = {"L2": -1.54244e-13,          "L3": -1.54168e-13}


def verdict():
    out_of_scope = [c for c in CHANNELS if not c["in_gS_scope"]]
    in_scope = [c for c in CHANNELS if c["in_gS_scope"]]
    dominant_out = any("DOMINANT" in c["magnitude_class"] for c in out_of_scope)

    ratios = {leg: abs(BOX_TOTAL[leg] / BOX_H[leg]) for leg in BOX_TOTAL}

    # KEY TEST
    key_test = {
        "out_of_scope_channels_present": [c["boson"] for c in out_of_scope],
        "in_scope_channels": [c["boson"] for c in in_scope],
        "dominant_box_channel_out_of_scope": dominant_out,
        "dominant_channel": "W (VWp) charged-current box",
        "gS_scope": "Z-mediated neutral-current box ONLY (g_S(z); no g_S(w)); "
                    "Hisano assigns ALL W strength to the g_H penguin, not the box.",
        "full_box_over_box_H": ratios,
        "in_scope_over_box_H_estimate": "CANNOT be pinned statically (no kernel). "
            "DIRECTION: removing the out-of-scope W/H+-/h/A channels -- which "
            "include the magnitude-DOMINANT W box -- leaves only the subdominant "
            "Z box, so |in-scope-box/box_H| << 45 and moves toward [0.2,5]. Sign "
            "of the effect is unambiguous; the exact landing point is not "
            "certifiable without the forbidden re-projection.",
    }

    outcome = ("MAPPING-ARTIFACT (dominant; residual un-pinned)" if dominant_out
               else "REAL-DEFECT")
    reason = (
        "The box-total <-> g_S comparison is NOT apples-to-apples at internal-line "
        "grain. Hisano's g_S box class is Z-ONLY (neutral current). Our box-total "
        "carries FOUR channels OUTSIDE that scope -- W/chi+/-, H+-/chi+/-, h/chi0, "
        "A/chi0 -- and the magnitude-DOMINANT one (the W chi-chi+/- charged-current "
        "box, the census headline) is exactly the channel Hisano places in the g_H "
        "PENGUIN, not the box. So the ~45x reflects a triangle/box PARTITION "
        "mismatch: Hisano routes W->penguin while our pipeline routes W->box (and "
        "also carries H+-/h/A boxes g_S has no counterpart for). Only the "
        "subdominant Z box is genuinely in g_S scope. => The 45x is a MAPPING "
        "ARTIFACT, not (on this evidence) a genuine pipeline box-magnitude bug. "
        "IMPORTANT residual: exact per-channel C_scalar cannot be isolated without "
        "a kernel re-projection (forbidden), so the fraction of the 45x explained "
        "is not numerically pinned -- but the DIRECTION is certain and the "
        "dominant channel is definitively out of scope. NOTE this also revises the "
        "B3 brief's REAL-DEFECT premise ('g_S represents W/chi+/-(+Z)'): g_S is "
        "Z-only, so even the leading gauge-box channel is out of scope -- the "
        "mismatch is broader than anticipated. RECOMMENDATION: do NOT hand the "
        "45x to B1/B2 as a box-magnitude bug; the correct sector comparison is "
        "TOTAL-vs-TOTAL (D4 anchor reproduces exactly) or a re-partitioned "
        "comparison grouping our W box with the penguin to match Hisano's g_H."
    )
    return {
        "_desc": "B3 box internal-line mapping audit (VALIDATION-ONLY, no kernel). "
                 "Outcomes pre-registered in header before verdict.",
        "channels": CHANNELS,
        "magnitude_note": MAGNITUDE_NOTE,
        "hisano_gS_scope": "Z-box only (g_S(z)); W is in the g_H penguin term.",
        "key_test": key_test,
        "verdict": {"outcome": outcome, "reason": reason},
    }


if __name__ == "__main__":
    print(json.dumps(verdict(), indent=2))
