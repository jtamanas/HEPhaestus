# ---------------------------------------------------------------------- 
# This model file was automatically created by SARAH version4.15.3
# SARAH References: arXiv:0806.0538, arXiv:0909.2863, arXiv:1002.0840   
# (c) Florian Staub, Mark Goodsell, Werner Porod and Martin Gabelmann 2023 
# ---------------------------------------------------------------------- 
# File created at 21:31 on 24.4.2026  
# ---------------------------------------------------------------------- 


from __future__ import division
from object_library import all_particles,Particle
import parameters as Param


nu1 = Particle(pdg_code =12,
    name = 'nu1' ,
    antiname = 'nu1bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = 0 ,
    texname = '{\\nu}_1' ,
    antitexname = '{\\bar{\\nu}}_1' )

nu1bar = nu1.anti()


nu2 = Particle(pdg_code =14,
    name = 'nu2' ,
    antiname = 'nu2bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = 0 ,
    texname = '{\\nu}_2' ,
    antitexname = '{\\bar{\\nu}}_2' )

nu2bar = nu2.anti()


nu3 = Particle(pdg_code =16,
    name = 'nu3' ,
    antiname = 'nu3bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = 0 ,
    texname = '{\\nu}_3' ,
    antitexname = '{\\bar{\\nu}}_3' )

nu3bar = nu3.anti()


d1 = Particle(pdg_code =1,
    name = 'd1' ,
    antiname = 'd1bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Md1 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1/3 ,
    texname = '{d}_1' ,
    antitexname = '{\\bar{d}}_1' )

d1bar = d1.anti()


d2 = Particle(pdg_code =3,
    name = 'd2' ,
    antiname = 'd2bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Md2 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1/3 ,
    texname = '{d}_2' ,
    antitexname = '{\\bar{d}}_2' )

d2bar = d2.anti()


d3 = Particle(pdg_code =5,
    name = 'd3' ,
    antiname = 'd3bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Md3 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1/3 ,
    texname = '{d}_3' ,
    antitexname = '{\\bar{d}}_3' )

d3bar = d3.anti()


u1 = Particle(pdg_code =2,
    name = 'u1' ,
    antiname = 'u1bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Mu1 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = 2/3 ,
    texname = '{u}_1' ,
    antitexname = '{\\bar{u}}_1' )

u1bar = u1.anti()


u2 = Particle(pdg_code =4,
    name = 'u2' ,
    antiname = 'u2bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Mu2 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = 2/3 ,
    texname = '{u}_2' ,
    antitexname = '{\\bar{u}}_2' )

u2bar = u2.anti()


u3 = Particle(pdg_code =6,
    name = 'u3' ,
    antiname = 'u3bar' ,
    spin = 2 ,
    color = 3 ,
    mass = Param.Mu3 ,
    width = Param.Wu3 ,
    line = 'straight' ,
    charge = 2/3 ,
    texname = '{u}_3' ,
    antitexname = '{\\bar{u}}_3' )

u3bar = u3.anti()


e1 = Particle(pdg_code =11,
    name = 'e1' ,
    antiname = 'e1bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.Me1 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1 ,
    texname = '{e}_1' ,
    antitexname = '{\\bar{e}}_1' )

e1bar = e1.anti()


e2 = Particle(pdg_code =13,
    name = 'e2' ,
    antiname = 'e2bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.Me2 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1 ,
    texname = '{e}_2' ,
    antitexname = '{\\bar{e}}_2' )

e2bar = e2.anti()


e3 = Particle(pdg_code =15,
    name = 'e3' ,
    antiname = 'e3bar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.Me3 ,
    width = Param.ZERO ,
    line = 'straight' ,
    charge = -1 ,
    texname = '{e}_3' ,
    antitexname = '{\\bar{e}}_3' )

e3bar = e3.anti()


Chi1 = Particle(pdg_code =9958431,
    name = 'Chi1' ,
    antiname = 'Chi1' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.MChi1 ,
    width = Param.WChi1 ,
    line = 'swavy' ,
    charge = 0 ,
    texname = '{Chi}_1' ,
    antitexname = '{Chi}_1' )

Chi2 = Particle(pdg_code =9956206,
    name = 'Chi2' ,
    antiname = 'Chi2' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.MChi2 ,
    width = Param.WChi2 ,
    line = 'swavy' ,
    charge = 0 ,
    texname = '{Chi}_2' ,
    antitexname = '{Chi}_2' )

Chi3 = Particle(pdg_code =9979223,
    name = 'Chi3' ,
    antiname = 'Chi3' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.MChi3 ,
    width = Param.WChi3 ,
    line = 'swavy' ,
    charge = 0 ,
    texname = '{Chi}_3' ,
    antitexname = '{Chi}_3' )

ChiM = Particle(pdg_code =9984071,
    name = 'ChiM' ,
    antiname = 'ChiMbar' ,
    spin = 2 ,
    color = 1 ,
    mass = Param.MChiM ,
    width = Param.WChiM ,
    line = 'swavy' ,
    charge = -1 ,
    texname = 'ChiM' ,
    antitexname = '\\bar{ChiM}' )

ChiMbar = ChiM.anti()


Hp = Particle(pdg_code =999900,
    name = 'Hp' ,
    antiname = 'Hpc' ,
    spin = 1 ,
    color = 1 ,
    mass = Param.MHp ,
    width = Param.ZERO,
    goldstone = True ,
    line = 'dashed' ,
    charge = 1 ,
    texname = 'H^+' ,
    antitexname = 'H^-' )

Hpc = Hp.anti()


Ah = Particle(pdg_code =999901,
    name = 'Ah' ,
    antiname = 'Ah' ,
    spin = 1 ,
    color = 1 ,
    mass = Param.MAh ,
    width = Param.ZERO,
    goldstone = True ,
    line = 'dashed' ,
    charge = 0 ,
    texname = 'A^0' ,
    antitexname = 'A^0' )

h = Particle(pdg_code =25,
    name = 'h' ,
    antiname = 'h' ,
    spin = 1 ,
    color = 1 ,
    mass = Param.Mh ,
    width = Param.Wh ,
    line = 'dashed' ,
    charge = 0 ,
    texname = 'h' ,
    antitexname = 'h' )

g = Particle(pdg_code =21,
    name = 'g' ,
    antiname = 'g' ,
    spin = 3 ,
    color = 8 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    line = 'wavy' ,
    charge = 0 ,
    texname = 'g' ,
    antitexname = 'g' )

A = Particle(pdg_code =22,
    name = 'A' ,
    antiname = 'A' ,
    spin = 3 ,
    color = 1 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    line = 'wavy' ,
    charge = 0 ,
    texname = '\\gamma' ,
    antitexname = '\\gamma' )

Z = Particle(pdg_code =23,
    name = 'Z' ,
    antiname = 'Z' ,
    spin = 3 ,
    color = 1 ,
    mass = Param.MZ ,
    width = Param.WZ ,
    line = 'wavy' ,
    charge = 0 ,
    texname = 'Z' ,
    antitexname = 'Z' )

Wp = Particle(pdg_code =24,
    name = 'Wp' ,
    antiname = 'Wpc' ,
    spin = 3 ,
    color = 1 ,
    mass = Param.MWp ,
    width = Param.WWp ,
    line = 'wavy' ,
    charge = 1 ,
    texname = 'W^+' ,
    antitexname = 'W^-' )

Wpc = Wp.anti()


gG = Particle(pdg_code =999902,
    name = 'gG' ,
    antiname = 'gGc' ,
    spin = -1 ,
    color = 8 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    propagating = False,
    line = 'dotted' ,
    charge = 0 ,
    texname = '\\eta^G' ,
    antitexname = '\\bar{\\eta^G}' )

gGc = gG.anti()


gA = Particle(pdg_code =999903,
    name = 'gA' ,
    antiname = 'gAc' ,
    spin = -1 ,
    color = 1 ,
    mass = Param.ZERO ,
    width = Param.ZERO ,
    propagating = False,
    line = 'dotted' ,
    charge = 0 ,
    texname = '\\eta^{\\gamma}' ,
    antitexname = '\\bar{\\eta^{\\gamma}}' )

gAc = gA.anti()


gZ = Particle(pdg_code =999904,
    name = 'gZ' ,
    antiname = 'gZc' ,
    spin = -1 ,
    color = 1 ,
    mass = Param.MgZ ,
    width = Param.WZ ,
    propagating = False,
    line = 'dotted' ,
    charge = 0 ,
    texname = '\\eta^Z' ,
    antitexname = '\\bar{\\eta^Z}' )

gZc = gZ.anti()


gWp = Particle(pdg_code =999905,
    name = 'gWp' ,
    antiname = 'gWpc' ,
    spin = -1 ,
    color = 1 ,
    mass = Param.MgWp ,
    width = Param.WWp ,
    propagating = False,
    line = 'dotted' ,
    charge = 1 ,
    texname = '\\eta^+' ,
    antitexname = '\\bar{\\eta^+}' )

gWpc = gWp.anti()


gWC = Particle(pdg_code =999906,
    name = 'gWC' ,
    antiname = 'gWCc' ,
    spin = -1 ,
    color = 1 ,
    mass = Param.MgWC ,
    width = Param.WWp ,
    propagating = False,
    line = 'dotted' ,
    charge = -1 ,
    texname = '\\eta^-' ,
    antitexname = '\\bar{\\eta^-}' )

gWCc = gWC.anti()


