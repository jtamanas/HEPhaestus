#!/usr/bin/env python3
"""D1 which-single-sector-flip analysis at both verdict legs."""
import json
DSC="/Users/yianni/.claude/jobs/c703354a/tmp/p3-diagnose-scratch/D1"
# Hisano C_scalar per leg (from campaign_bars.json)
HIS={"L2":-2.228e-12,"L3":-2.229e-12}
FULL_scalar={"L2":1.053e-11,"L3":1.1539e-11}   # campaign full Re(C_ours)
FULL_twist2={"L2":8.118e-12,"L3":5.183e-11}

def load(leg,sec):
    d=json.load(open(f"{DSC}/{leg}_{sec}/cours.json"))
    return d["C_scalar_full_re"], d["C_twist2_re"]

out={}
for leg in ["L2","L3"]:
    s={}; t={}
    for sec in ["triangle","directBox","crossedBox"]:
        s[sec],t[sec]=load(leg,sec)
    His=HIS[leg]
    sum_s=s["triangle"]+s["directBox"]+s["crossedBox"]
    sum_t=t["triangle"]+t["directBox"]+t["crossedBox"]
    # candidate flips: flip one sector's sign (subtract 2x its value)
    def assemble(flips):
        cs=sum(( -s[k] if k in flips else s[k]) for k in s)
        ct=sum(( -t[k] if k in flips else t[k]) for k in t)
        return cs,ct
    cands={
      "flip_triangle":["triangle"],
      "flip_directBox":["directBox"],
      "flip_crossedBox_S1":["crossedBox"],
      "flip_wholeBox_S2":["directBox","crossedBox"],
    }
    res={}
    for name,fl in cands.items():
        cs,ct=assemble(fl)
        ratio=cs/His
        res[name]={"C_scalar":cs,"ratio_vs_Hisano":ratio,"abs_ratio":abs(ratio),
                   "sign_agree_scalar":(cs>0)==(His>0),"in_[0.2,5]":0.2<=abs(ratio)<=5,
                   "twist2":ct,"twist2_sign_positive":ct>0,
                   "SATISFIES_ALL3":((cs>0)==(His>0)) and (0.2<=abs(ratio)<=5) and (ct>0)}
    out[leg]={"sectors_C_scalar":s,"sectors_C_twist2":t,
              "sum_C_scalar":sum_s,"full_C_scalar":FULL_scalar[leg],
              "sum_C_twist2":sum_t,"full_C_twist2":FULL_twist2[leg],
              "C_Hisano":His,"reconstruct_rel_err_scalar":abs(sum_s-FULL_scalar[leg])/abs(FULL_scalar[leg]),
              "flip_candidates":res}
print(json.dumps(out,indent=2))
print("\n=== SUMMARY: which single flip satisfies all 3, at BOTH legs ===")
for name in ["flip_triangle","flip_directBox","flip_crossedBox_S1","flip_wholeBox_S2"]:
    both=all(out[leg]["flip_candidates"][name]["SATISFIES_ALL3"] for leg in ["L2","L3"])
    r=[f"{leg}: scalar={out[leg]['flip_candidates'][name]['C_scalar']:+.3e} |ratio|={out[leg]['flip_candidates'][name]['abs_ratio']:.2f} signOK={out[leg]['flip_candidates'][name]['sign_agree_scalar']} t2+={out[leg]['flip_candidates'][name]['twist2_sign_positive']}" for leg in ['L2','L3']]
    print(f"{name}: BOTH_LEGS_ALL3={both}\n    "+"\n    ".join(r))
