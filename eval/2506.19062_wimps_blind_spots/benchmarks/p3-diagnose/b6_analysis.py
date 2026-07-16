"""
b6_analysis.py — B6 per-channel box split scoring (VALIDATION / MEASUREMENT ONLY).

Reads the per-(leg,sector,channel) kernel extracts produced by b6_run_all.sh and
scores the four PRE-REGISTERED probes P-i..P-iv against the FROZEN AMENDMENT8R3
bars. NO kernel here; pure arithmetic on durable cours.json extracts. NO fix.

CHANNELS (routing done in b6_boson_filter.wls, by internal-boson mass in each
D0i): Wpure = pure W-W gauge box; Zpure = pure Z-Z gauge box; Yukawa = any box
with a Higgs leg (h/A/H±, incl. mixed W-H±, Z-h, Z-A, H±H±, hh, AA, hA).
WwithHp = the {W,H±} sub-class (subset of Yukawa; P-i alternative convention).

REMAINDER HANDLING (measured deviation, documented): the "remainder" filter
output (ALL D0i zeroed; only the 4 no-D0i finite terms kept) CANNOT be driven
through the kernel — run_eval_sd.wls aborts with a MathLink MLException on an
amplitude containing zero loop functions (measured, both sectors, logs under
runs/L*_*_remainder/driver.log). The remainder is instead DERIVED from
projection linearity: each channel filter zeros only non-matching D0i, so
filtered = pure + rem, and the D1 box cours (same amp, ALL D0i kept) =
W + Z + Y + rem. Hence, per (sector, leg):
    rem = (Wf + Zf + Yf - box_D1_sector) / 2 .
Cross-check: rem derived from db and from cb must agree (identical no-D0i term
structure) — reported as remainder_db_cb_agreement. The channel-sum closure
against the D1 box-total is then exact BY CONSTRUCTION of rem, so the honest
closure evidence is (a) the db/cb remainder agreement, (b) the smallness of
rem itself, and (c) D1's prior sector-sum-vs-full closure (0.18-0.64%).

FROZEN BARS (AMENDMENT8R3 R3; Hisano leg values cross-checked vs d4_analysis.json):
  P-i   : |C_scalar(Wpure)| < 5% of |C_scalar(box-total)| at BOTH legs.
  P-ii  : Zpure vs Hisano g_S class (box_H ~ -1.542e-13). |ratio| band [0.2,5].
          Hisano negative; ours positive = wrong-sign (World-B expectation).
  P-iii : (triangle + surviving Wpure) vs Hisano g_H class (tri_H ~ -2.073e-12).
          Band [0.2,5]; same sign logic.
  P-iv  : Yukawa boxes have NO Hisano analogue; if they carry the MAJORITY of
          the total magnitude excess, total-level FAIL-L3 reclassifies as
          candidate genuine model-difference (documented, not auto-cleared).
"""
from __future__ import annotations
import json
from pathlib import Path

DIAG = Path(__file__).resolve().parent
RUNS = Path("/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-scratch/runs")
LEGS = ["L2", "L3"]
SECTORS = ["db", "cb"]
CHANS = ["Wpure", "Zpure", "Yukawa", "WwithHp"]

P_I_BAR = 0.05
BAND = (0.2, 5.0)

# frozen Hisano leg-scaled class values (d4_analysis.json hisano_sectors;
# AMENDMENT8R3 anchor quotes: g_S -1.542e-13, g_H -2.073e-12)
HISANO = {
    "L2": {"tri_H": -2.073415536103058e-12, "box_H": -1.5424361678105703e-13},
    "L3": {"tri_H": -2.0746810640262234e-12, "box_H": -1.5416845222126134e-13},
}


def rd(leg, sec, chan):
    # prefer the committed copies next to this script; fall back to scratch runs
    p = DIAG / f"b6_{leg}_{sec}_{chan}_cours.json"
    if not p.exists():
        p = RUNS / f"{leg}_{sec}_{chan}" / "cours.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return {"re": d.get("C_scalar_full_re"), "im": d.get("C_scalar_full_im"),
            "compl": d.get("full_basis_completeness_rel_residual")}


def rd_existing(leg, sector_name):
    # committed D1 per-sector cours (directBox/crossedBox/triangle)
    p = DIAG / f"{leg}_{sector_name}_cours.json"
    return json.loads(p.read_text())["C_scalar_full_re"]


def sgn(x):
    return "+" if x > 0 else ("-" if x < 0 else "0")


def analyse():
    out = {"_desc": "B6 per-channel box split, scored vs frozen AMENDMENT8R3 "
                    "bars. MEASUREMENT ONLY. Channels routed by internal-boson "
                    "mass in each D0i (b6_boson_filter.wls).",
           "method": {
               "partition": "box-total (directBox+crossedBox) D0i split by "
                            "internal boson: Wpure={MassVWp} only, "
                            "Zpure={MassVZ} only, Yukawa=any {h,A,H±} in the "
                            "D0i args. D0i counts per sector: 11(W)+11(Z)+"
                            "121(Yukawa)=143 = total (exhaustive, "
                            "non-overlapping; NO W-Z mixed D0i exists).",
               "remainder": "derived from linearity, rem=(Wf+Zf+Yf-box_D1)/2 "
                            "per sector-leg; kernel cannot run a 0-loop-"
                            "function amp (MLException, measured).",
               "whp_convention": "W-H± mixed boxes route to Yukawa under the "
                                 "primary Higgs-dominant rule (the H± leg "
                                 "carries the quark Yukawa chirality flip); "
                                 "P-i is re-scored under the alternative "
                                 "any-W convention as a sensitivity.",
               "value_convention": "C_scalar_full_re (rotated-complete R_S_S "
                                   "read-off), same instrument as P3'/D1.",
           },
           "frozen_bars": {"P_i_frac": P_I_BAR, "band": BAND, "hisano": HISANO},
           "legs": {}}

    all_ok = True
    for leg in LEGS:
        raw = {c: {s: rd(leg, s, c) for s in SECTORS} for c in CHANS}
        if any(v is None for c in CHANS for v in raw[c].values()):
            out["legs"][leg] = {"status": "INCOMPLETE"}
            all_ok = False
            continue

        box_d1 = {"db": rd_existing(leg, "directBox"),
                  "cb": rd_existing(leg, "crossedBox")}
        rem_by_sec = {s: (raw["Wpure"][s]["re"] + raw["Zpure"][s]["re"]
                          + raw["Yukawa"][s]["re"] - box_d1[s]) / 2.0
                      for s in SECTORS}
        rem_agree_rel = (abs(rem_by_sec["db"] - rem_by_sec["cb"])
                         / max(abs(rem_by_sec["db"]), 1e-300))
        pure = {}
        for c in CHANS:
            pure[c] = {s: raw[c][s]["re"] - rem_by_sec[s] for s in SECTORS}
            pure[c]["sum"] = pure[c]["db"] + pure[c]["cb"]
        rem_tot = rem_by_sec["db"] + rem_by_sec["cb"]

        box_total = box_d1["db"] + box_d1["cb"]
        recon = (pure["Wpure"]["sum"] + pure["Zpure"]["sum"]
                 + pure["Yukawa"]["sum"] + rem_tot)
        triangle = rd_existing(leg, "triangle")
        our_total = triangle + box_total
        H = HISANO[leg]

        W = pure["Wpure"]["sum"]
        Z = pure["Zpure"]["sum"]
        Y = pure["Yukawa"]["sum"]
        WHp = pure["WwithHp"]["sum"]

        p_i_ratio = abs(W) / abs(box_total)
        p_i_alt = abs(W + WHp) / abs(box_total)
        r_ii = Z / H["box_H"]
        num_iii = triangle + W
        r_iii = num_iii / H["tri_H"]
        hisano_total = H["tri_H"] + H["box_H"]
        excess = our_total - hisano_total
        yuk_majority = abs(Y) > 0.5 * abs(excess)

        out["legs"][leg] = {
            "status": "COMPLETE",
            "raw_filtered_re": {c: {s: raw[c][s]["re"] for s in SECTORS}
                                for c in CHANS},
            "raw_filtered_im": {c: {s: raw[c][s]["im"] for s in SECTORS}
                                for c in CHANS},
            "completeness_rel_residual": {c: {s: raw[c][s]["compl"]
                                              for s in SECTORS} for c in CHANS},
            "remainder_derived": rem_by_sec,
            "remainder_db_cb_agreement_rel": rem_agree_rel,
            "pure_channels": {"Wpure": W, "Zpure": Z, "Yukawa": Y,
                              "WwithHp": WHp, "remainder": rem_tot},
            "signs": {"Wpure": sgn(W), "Zpure": sgn(Z), "Yukawa": sgn(Y),
                      "triangle": sgn(triangle)},
            "box_total_D1": box_total,
            "channel_sum_recon": recon,
            "closure_note": "recon==box_total_D1 by construction of rem; "
                            "independent evidence = remainder_db_cb_agreement "
                            "+ D1 sector-sum closure 0.18-0.64%",
            "triangle_class": triangle,
            "our_total_scalar": our_total,
            "P_i": {"W_channel": W, "box_total": box_total,
                    "ratio_W_over_box": p_i_ratio, "bar": P_I_BAR,
                    "PASS": p_i_ratio < P_I_BAR,
                    "alt_anyW_ratio": p_i_alt, "WwithHp": WHp},
            "P_ii": {"Z_channel": Z, "box_H_gS": H["box_H"], "ratio": r_ii,
                     "abs_ratio": abs(r_ii),
                     "in_band": BAND[0] <= abs(r_ii) <= BAND[1],
                     "our_sign": sgn(Z), "hisano_sign": "-",
                     "wrong_sign": Z > 0},
            "P_iii": {"triangle_plus_W": num_iii, "triangle_only": triangle,
                      "tri_H_gH": H["tri_H"], "ratio": r_iii,
                      "ratio_trionly": triangle / H["tri_H"],
                      "abs_ratio": abs(r_iii),
                      "in_band": BAND[0] <= abs(r_iii) <= BAND[1],
                      "our_sign": sgn(num_iii), "hisano_sign": "-",
                      "wrong_sign": num_iii > 0},
            "P_iv": {"Yukawa_channel": Y, "no_hisano_counterpart": True,
                     "frac_of_box_total": Y / box_total,
                     "excess_over_hisano": excess,
                     "frac_of_excess": Y / excess,
                     "carries_majority_of_excess": yuk_majority},
        }

    if all_ok:
        li = out["legs"]
        p_i = all(li[l]["P_i"]["PASS"] for l in LEGS)
        sign_pat = {l: {"W": li[l]["signs"]["Wpure"],
                        "Z": li[l]["signs"]["Zpure"],
                        "tri": li[l]["signs"]["triangle"],
                        "Yuk": li[l]["signs"]["Yukawa"]} for l in LEGS}
        p_ii_wsib = all(li[l]["P_ii"]["wrong_sign"] and li[l]["P_ii"]["in_band"]
                        for l in LEGS)
        p_iii_wsib = all(li[l]["P_iii"]["wrong_sign"] and li[l]["P_iii"]["in_band"]
                         for l in LEGS)
        out["verdict"] = {
            "P_i_PASS_both_legs": p_i,
            "P_i_ratios": {l: li[l]["P_i"]["ratio_W_over_box"] for l in LEGS},
            "P_ii_wrongsign_inband_both": p_ii_wsib,
            "P_iii_wrongsign_inband_both": p_iii_wsib,
            "P_iv_yukawa_majority": {l: li[l]["P_iv"]["carries_majority_of_excess"]
                                     for l in LEGS},
            "sign_pattern": sign_pat,
            "worldB_coherent": p_i and p_ii_wsib and p_iii_wsib,
            "note": "MEASUREMENT ONLY. World A/B ruling is the "
                    "manager+designer's call. World-B-coherent required "
                    "P-i PASS + P-ii/P-iii wrong-sign in-band.",
        }
    return out


if __name__ == "__main__":
    print(json.dumps(analyse(), indent=2))
