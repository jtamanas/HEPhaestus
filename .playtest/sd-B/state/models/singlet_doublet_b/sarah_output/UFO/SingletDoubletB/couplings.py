from object_library import all_couplings,Coupling
from cmath import exp
import math
from function_library import complexconjugate,re,im,csc,sec,acsc,asec


GC_1=Coupling(name='GC_1',
    value='-(HPP1*complex(0,1))',
    order={'HIW':1})

GC_2=Coupling(name='GC_2',
    value='-(HGG1*complex(0,1))',
    order={'HIG':1})

