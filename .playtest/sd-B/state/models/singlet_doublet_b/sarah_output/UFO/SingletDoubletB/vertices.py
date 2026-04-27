# ------------------------------------------------------------------------------ 
# This model file was automatically created by SARAH version4.15.3
# SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223  
# (c) Florian Staub, Mark Goodsell, Werner Porod and Martin Gabelmann 2023 
# ------------------------------------------------------------------------------- 
# File created at 21:31 on 24.4.2026  
# ---------------------------------------------------------------------- 


from object_library import all_vertices,Vertex
import particles as P
import couplings as C
import lorentz as L


V_1 = Vertex(name = 'V_1',
    particles = [P.A, P.A, P.h],
    color = ['1'],
    lorentz = [L.VVS99],
    couplings = {(0,0):C.GC_1})


V_2 = Vertex(name = 'V_2',
    particles = [P.g, P.g, P.h],
    color = ['Identity(1,2)'],
    lorentz = [L.VVS99],
    couplings = {(0,0):C.GC_2})


