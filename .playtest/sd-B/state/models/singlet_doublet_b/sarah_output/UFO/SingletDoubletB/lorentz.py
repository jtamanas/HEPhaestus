# ---------------------------------------------------------------------- 
# This model file was automatically created by SARAH version4.15.3
# SARAH References: arXiv:0806.0538, arXiv:0909.2863, arXiv:1002.0840   
# (c) Florian Staub, Mark Goodsell, Werner Porod and Martin Gabelmann 2023 
# ---------------------------------------------------------------------- 
# File created at 21:31 on 24.4.2026  
# ---------------------------------------------------------------------- 


from object_library import all_lorentz,Lorentz
from function_library import complexconjugate,re,im,csc,sec,acsc,asec


VVS99 = Lorentz(name='VVSpp',
spins=[3,3,1],
structure='P(1,2)*P(2,1)-P(-1,1)*P(-1,2)*Metric(1,2)')

VVS99p = Lorentz(name='VVSppDual',
spins=[3,3,1],
structure='P(-3,1)*P(-4,2)*Epsilon(1,2,-3,-4)')
