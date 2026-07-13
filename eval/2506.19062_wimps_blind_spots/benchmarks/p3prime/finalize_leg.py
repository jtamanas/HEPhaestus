#!/usr/bin/env python3
"""Finalize a P3' leg: LOOP-level SPheno spectrum -> point.json -> sidecar JSON.

Usage: finalize_leg.py <legname> <legdir> <MS> <y> <theta> <fraction_bar_desc>
Writes into <legdir>:  LesHouches.in.SingletDoublet, SPheno.spc.SingletDoublet,
point.json, sidecar.json.  Prints the sidecar to stdout.
"""
import subprocess, sys, math, json, re
from pathlib import Path

WT="/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-worktree"
sys.path.insert(0, f"{WT}/plugins/hep-ph-toolkit/skills/looptools/scripts")
sys.path.insert(0, f"{WT}/eval/2506.19062_wimps_blind_spots/models")
sys.path.insert(0, f"{WT}/eval/2506.19062_wimps_blind_spots")
import prepare_point as pp
import singlet_doublet as sd
from constants import V_H, M_H

BIN="/Users/yianni/.local/share/hephaestus/models/singlet_doublet/spheno_bin/SPhenoSingletDoublet"
DM_PDG=9958431
G_CLEAN=4.8e-10*V_H*M_H**2   # tree g_hchichi at which tree Higgs-exch DD == Hisano loop floor

TEMPLATE=Path("/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch/run_leg.py").read_text()
# reuse the TEMPLATE + parse_blocks from run_leg by import
sys.path.insert(0,"/Users/yianni/.claude/jobs/c703354a/tmp/p3prime-scratch")
import run_leg

def main():
    leg,legdir,MS,y,theta,bar=sys.argv[1],Path(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
    MPsi=500.0; mD=MPsi
    yh1=y*math.cos(theta); yh2=y*math.sin(theta)
    legdir.mkdir(parents=True,exist_ok=True)
    inp=run_leg.TEMPLATE.format(MS=MS,MPsi=MPsi,yh1=yh1,yh2=yh2,flag55=1)
    (legdir/"LesHouches.in.SingletDoublet").write_text(inp)
    spc=legdir/"SPheno.spc.SingletDoublet"
    if spc.exists(): spc.unlink()
    p=subprocess.run([BIN,"LesHouches.in.SingletDoublet"],cwd=legdir,capture_output=True,text=True,timeout=1200)
    if not spc.exists():
        print(json.dumps({"leg":leg,"status":"NO_SPECTRUM (loop refusal)","MS":MS,"y":y,"theta":theta,
                          "spheno_stdout_tail":p.stdout[-500:]},indent=2)); sys.exit(2)
    txt=spc.read_text(); b=run_leg.parse_blocks(txt)
    mass=b["MASS"]; m_h=mass.get((25,))
    def amp2(blk,i,j): v=b.get(blk,{}).get((i,j),0.0); return v*v
    zn="ZNMIX"; imzn="IMZNMIX"
    singlet_col=max((1,2,3),key=lambda c:amp2(zn,3,c)+amp2(imzn,3,c))
    frac=amp2(zn,1,singlet_col)+amp2(imzn,1,singlet_col)
    tach=[m.group(0).strip() for m in re.finditer(r'(?im)^\s*[34]\s+.*(tachyon|negative mass).*$',txt)]
    # residual tree scalar coupling (Eq.7 analytic) + exact mixing-based, at this point
    coup7=sd.coupling_h_chi1chi1(MS,mD,y,theta)
    y1c,y2c=sd.y1_y2_from_y_theta(y,theta); m_tree,U=sd.diagonalize(MS,mD,y1c,y2c)
    coup_mix=sd.coupling_h_chi_ij_mixing(y1c,y2c,U,0,0)
    # blind spot proximity
    theta_bs=-math.pi/4  # decoupled-regime Eq.8 blind spot (m_chi1->mD): sin2theta=-1
    # point.json via prepare_point
    point=pp.prepare_point(spc,dm_pdg=DM_PDG)
    (legdir/"point.json").write_text(json.dumps(point,indent=2))
    m_h_physical = (m_h is not None) and (100.0 <= m_h <= 135.0)
    sidecar={
      "leg":leg,"role":bar,
      "status":"OK","note_pinned_quantity":"MEASURED singlet fraction |N_singlet|^2 of chi1 from SPheno ZNMIX/IMZNMIX",
      "MS_gev":MS,"MPsi_gev":MPsi,"m_chi_gev":MPsi,
      "portal_y":y,"theta_rad":theta,"yh1":yh1,"yh2":yh2,
      "theta_derivation":("held at canonical theta=-0.152 (Eq.8 blind spot of the ORIGINAL m_chi1=150 "
                          "benchmark); NOT the decoupled-regime blind spot theta=-pi/4=-0.7854 (where "
                          "m_chi1->mD forces sin2theta=-1). See protocol-conflict flag."),
      "measured_singlet_fraction_chi1":frac,"singlet_gauge_column":singlet_col,
      "fraction_bar":bar,
      "FChi1_gev":mass.get((9958431,)),"FChi2_gev":mass.get((9956206,)),
      "FChi3_singlet_gev":mass.get((9979223,)),"FChiM_charged_gev":mass.get((9984071,)),
      "splitting_chi2_chi1_gev":(mass.get((9956206,))-mass.get((9958431,))),
      "m_h_gev":m_h,"m_h_physical":m_h_physical,
      "loop_spectrum":{"flag55":1,"flag56_twoloopHiggs":1,"non_tachyonic":(not tach and m_h and m_h>0),
                       "tachyon_lines":tach},
      "residual_tree_scalar_coupling":{
        "g_h_chi1chi1_Eq7":coup7,"g_h_chi1chi1_mixing":coup_mix,
        "tree_DD_over_loop_floor_ratio":abs(coup7)/G_CLEAN,
        "g_clean_threshold":G_CLEAN,
        "label":"SIGMA-LEVEL CONTEXT ONLY (6R3)",
        "interpretation":("The projected amplitude amp_reduced.m is LOOP-ONLY (1PI core: "
          "32 one-loop diagrams, B0i/C0i/D0i heads, all Den[T,m^2] are penguin mediator "
          "propagators, NO bare tree term). So this tree coupling is NOT in C_ours and is "
          "NOT a contamination bar. It is context for the PHYSICAL sigma_SI only. The real "
          "verdict-leg bar rides the singlet FRACTION (cleanliness bar, 6R1 R2 / 6R3).")},
      "blind_spot":{"theta_bs_decoupled_rad":theta_bs,"delta_theta_from_bs":theta-theta_bs,
                    "at_blind_spot":abs(theta-theta_bs)<1e-3,
                    "comment":"NOT at the decoupled blind spot; fraction and tree coupling are the SAME order parameter (both ~0 only at theta=-pi/4)."},
      "ZNMIX":{f"{i},{j}":b[zn].get((i,j)) for i in(1,2,3) for j in(1,2,3)},
      "IMZNMIX":{f"{i},{j}":b[imzn].get((i,j)) for i in(1,2,3) for j in(1,2,3)},
      "spectrum_path":str(spc),"point_json_path":str(legdir/"point.json"),
      "m_dm_gev":point["m_dm_gev"],"dm_pdg":DM_PDG,
    }
    (legdir/"sidecar.json").write_text(json.dumps(sidecar,indent=2))
    print(json.dumps(sidecar,indent=2))

if __name__=="__main__": main()
