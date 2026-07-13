#!/usr/bin/env python3
"""D2 crossing-sign identity summary from the D1 sector projections."""
import json
DSC="/Users/yianni/.claude/jobs/c703354a/tmp/p3-diagnose-scratch/D1"
def g(leg,sec): return json.load(open(f"{DSC}/{leg}_{sec}/cours.json"))
out={"_desc":"D2 machine crossing-sign check on the direct/crossed box sectors "
     "(same discipline as the Fierz/rotation guard). eta = crossed/direct per "
     "operator; rotation_exactness = projector Majorana crossing-rotation residual.",
     "legs":{}}
for leg in ["L2","L3"]:
    tr,db,xb=g(leg,"triangle"),g(leg,"directBox"),g(leg,"crossedBox")
    ds,xs=db["C_scalar_full_re"],xb["C_scalar_full_re"]
    dt,xt=db["C_twist2_re"],xb["C_twist2_re"]
    out["legs"][leg]={
      "eta_scalar_crossed_over_direct":xs/ds,
      "eta_twist2_crossed_over_direct":xt/dt,
      "direct_crossed_same_sign_scalar":(ds>0)==(xs>0),
      "direct_crossed_same_sign_twist2":(dt>0)==(xt>0),
      "box_total_scalar":ds+xs,"triangle_scalar":tr["C_scalar_full_re"],
      "box_over_triangle_scalar":(ds+xs)/tr["C_scalar_full_re"],
      "rotation_exactness_max":{"triangle":tr["rotation_exactness_max"],
        "directBox":db["rotation_exactness_max"],"crossedBox":xb["rotation_exactness_max"]},
    }
out["verdict"]={
  "S1_crossed_vs_direct_box_sign":"CLEARED",
  "S1_reasoning":("Direct and crossed boxes are SAME-SIGN and additive at both legs "
    "(eta_scalar=+0.94, eta_twist2=+1.70; box/tri~+1.5..2.1). A crossed-vs-direct "
    "fermion-flow sign error (S1) would make them OPPOSITE-sign / near-cancelling "
    "(box_total ~ 0). Not observed. The projector's Majorana crossing-rotation is "
    "exact (~5e-16) on the crossed box, so the crossed monomials are well-formed "
    "crossings. Corroborates D1, where flipping the crossed box ALONE fails to "
    "restore the Hisano sign."),
  "S2_triangle_vs_box_relative_sign":"CONVICTED (from D1; consistent with D2)",
  "S2_reasoning":("D1: flipping the WHOLE box relative to the triangle is the unique "
    "single-sector flip that restores sign-agreement + |ratio| in [0.2,5] + twist-2 "
    "in-band at BOTH verdict legs. The box sector enters the assembled amplitude with "
    "the wrong OVERALL sign relative to the induced-h-exchange triangle penguins. "
    "Since |box|>|triangle| and Hisano<0, the wrong sign sits on the BOX side "
    "(flip box -> L2 -3.66e-12 |r|1.64, L3 -2.36e-12 |r|1.06). This is a relative "
    "ASSEMBLY sign between the C0i/T-channel triangle sector and the D0i box sector "
    "-- NOT a crossing sign (S1) and NOT a projector/rotation sign (rotation exact)."),
  "absolute_sign_caveat":("Pinning which sector carries the wrong ABSOLUTE sign against "
    "an EXTERNAL reference (vs the internal triangle-vs-box relative sign measured here) "
    "is D3's synthetic external-sign control -- NOT owned by D1/D2. D1/D2 settle the "
    "S1-vs-S2 discrimination: S1 excluded, S2 is the sufficient single fix."),
  "next":"D3 (synthetic external-sign control) to pin the absolute wrong-sign sector, then the fix + L2/L3 re-run."}
print(json.dumps(out,indent=2))
