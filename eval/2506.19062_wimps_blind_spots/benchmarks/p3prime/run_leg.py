#!/usr/bin/env python3
"""P3' SPheno loop-spectrum harness.

Generates a LesHouches.in.SingletDoublet with LOOP-level masses (flag 55=1,
two-loop Higgs flag 56=1), runs SPhenoSingletDoublet, and reports:
  m_h, tachyon status (from SPINFO + any negative m^2), FChi masses,
  singlet fraction of chi1 = |ZN(1,s)|^2 + |IMZN(1,s)|^2 where s is the
  gauge column that dominates the heavy singlet neutralino chi3.

Usage: run_leg.py <outdir> <MS> <y> <theta> [--tree]
Prints a JSON blob to stdout.
"""
import subprocess, sys, math, json, os, re
from pathlib import Path

BIN = "/Users/yianni/.local/share/hephaestus/models/singlet_doublet/spheno_bin/SPhenoSingletDoublet"

TEMPLATE = """Block MODSEL
   1   0   # non-SUSY (v1)

Block SMINPUTS
   1   1.279340000E+02   # alpha_em^{{-1}}(MZ)
   2   1.166380000E-05   # G_F [GeV^-2]
   3   1.184000000E-01   # alpha_s(MZ)
   4   9.118760000E+01   # MZ [GeV]
   5   4.180000000E+00   # m_b(m_b) [GeV]
   6   1.734000000E+02   # m_t [GeV]
   7   1.776820000E+00   # m_tau [GeV]

Block GAUGEIN
   1   4.626000000E-01   # g1(M_Z)
   2   6.488000000E-01   # g2(M_Z)
   3   1.219780000E+00   # g3(M_Z)

Block HMIXIN
   3   2.462195140E+02   # vvSM

Block SMIN
   1  -7.828282000E+03   # m2SMIN
   2   2.587500000E-01   # LamIN

Block MINPAR
   1   {MS:.6E}   # MS
   2   {MPsi:.6E}   # MPsi
   3   {yh1:.7E}   # yh1
   4   {yh2:.7E}   # yh2

Block BSMPARAMSIN
   1   {MS:.6E}   # MS
   2   {MPsi:.6E}   # MPsi
   3   {yh1:.7E}   # yh1
   4   {yh2:.7E}   # yh2

Block SPhenoInput
  1 -1   # error level
 55  {flag55}   # 1=loop-corrected masses, 0=tree
 56  1   # two-loop Higgs masses
 52  1   # write spectrum even if tachyonic (so we can DETECT the tachyon)
"""

def parse_blocks(text):
    blocks={}; cur=None; indecay=False
    for raw in text.splitlines():
        line=raw.split("#",1)[0].rstrip()
        if not line.strip(): continue
        head=line.strip().upper()
        if head.startswith("BLOCK"):
            cur=line.split()[1].upper(); indecay=False; blocks.setdefault(cur,{}); continue
        if head.startswith("DECAY"): cur=None; indecay=True; continue
        if cur is None or indecay: continue
        toks=line.split()
        try: val=float(toks[-1])
        except: continue
        try: idx=tuple(int(t) for t in toks[:-1])
        except: continue
        blocks[cur][idx]=val
    return blocks

def main():
    outdir=Path(sys.argv[1]); MS=float(sys.argv[2]); y=float(sys.argv[3]); theta=float(sys.argv[4])
    tree="--tree" in sys.argv[5:]
    MPsi=500.0
    yh1=y*math.cos(theta); yh2=y*math.sin(theta)
    outdir.mkdir(parents=True,exist_ok=True)
    inp=TEMPLATE.format(MS=MS,MPsi=MPsi,yh1=yh1,yh2=yh2,flag55=(0 if tree else 1))
    (outdir/"LesHouches.in.SingletDoublet").write_text(inp)
    spc_pre=outdir/"SPheno.spc.SingletDoublet"
    if spc_pre.exists(): spc_pre.unlink()  # avoid stale-spectrum reuse on SPheno failure
    p=subprocess.run([BIN,"LesHouches.in.SingletDoublet"],cwd=outdir,
                     capture_output=True,text=True,timeout=1200)
    spc=outdir/"SPheno.spc.SingletDoublet"
    res={"MS":MS,"y":y,"theta":theta,"yh1":yh1,"yh2":yh2,"flag55":(0 if tree else 1),
         "spheno_rc":p.returncode,"stdout_tail":p.stdout[-800:],"stderr_tail":p.stderr[-800:]}
    if not spc.exists():
        res["status"]="NO_SPECTRUM"; print(json.dumps(res,indent=2)); return
    txt=spc.read_text()
    b=parse_blocks(txt)
    # tachyon detection: SPINFO block error/warn lines mentioning tachyon/negative, or any neg m^2
    tach=[]
    for m in re.finditer(r'(?im)^\s*[34]\s+.*(tachyon|negative mass).*$',txt):
        tach.append(m.group(0).strip())
    mass=b.get("MASS",{})
    m_h=mass.get((25,))
    fchi={pdg:mass.get((pdg,)) for pdg in (9958431,9956206,9979223,9984071)}
    # any negative/complex handled by SPheno as writing but tach flagged; also flag tiny/neg m_h
    zn=b.get("ZNMIX",{}); imzn=b.get("IMZNMIX",{})
    # identify singlet column = argmax over col c of |ZN(3,c)|^2+|IMZN(3,c)|^2 (chi3 = heavy singlet)
    def amp2(blk,i,j):
        v=blk.get((i,j),0.0); return v*v
    singlet_col=None; best=-1
    for c in (1,2,3):
        w=amp2(zn,3,c)+amp2(imzn,3,c)
        if w>best: best=w; singlet_col=c
    frac_chi1=amp2(zn,1,singlet_col)+amp2(imzn,1,singlet_col)
    # row-1 norm check
    norm1=sum(amp2(zn,1,c)+amp2(imzn,1,c) for c in (1,2,3))
    res.update({
        "status":"OK",
        "m_h":m_h,
        "tachyon_lines":tach,
        "tachyonic":bool(tach) or (m_h is not None and m_h<=0),
        "FChi1":fchi[9958431],"FChi2":fchi[9956206],"FChi3":fchi[9979223],"FChiM":fchi[9984071],
        "splitting_chi2_chi1":(fchi[9956206]-fchi[9958431]) if fchi[9956206] and fchi[9958431] else None,
        "singlet_col":singlet_col,"singlet_frac_chi1":frac_chi1,"row1_norm":norm1,
        "ZNMIX":{f"{i},{j}":zn.get((i,j)) for i in (1,2,3) for j in (1,2,3)},
        "IMZNMIX":{f"{i},{j}":imzn.get((i,j)) for i in (1,2,3) for j in (1,2,3)},
    })
    print(json.dumps(res,indent=2))

if __name__=="__main__": main()
