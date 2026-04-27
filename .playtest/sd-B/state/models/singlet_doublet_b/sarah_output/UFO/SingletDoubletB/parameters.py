# ----------------------------------------------------------------------
# This model file was automatically created by SARAH version4.15.3
# SARAH References: arXiv:0806.0538, arXiv:0909.2863, arXiv:1002.0840
# (c) Florian Staub, Mark Goodsell, Werner Porod and Martin Gabelmann 2023
# ----------------------------------------------------------------------
# File created at 21:31 on 24.4.2026
# ----------------------------------------------------------------------

from object_library import all_parameters,Parameter

from function_library import complexconjugate,re,im,csc,sec,acsc,asec
ZERO = Parameter(name='ZERO',
    nature='internal',
    type='real',
    value='0.0',
    texname='0')

Md1 = Parameter(name = 'Md1',
    nature = 'external',
    type = 'real',
    value = 0.0035,
    texname = 'M_{{d}_1}',
    lhablock = 'MASS',
    lhacode = [1])

Md2 = Parameter(name = 'Md2',
    nature = 'external',
    type = 'real',
    value = 0.104,
    texname = 'M_{{d}_2}',
    lhablock = 'MASS',
    lhacode = [3])

Md3 = Parameter(name = 'Md3',
    nature = 'external',
    type = 'real',
    value = 4.2,
    texname = 'M_{{d}_3}',
    lhablock = 'MASS',
    lhacode = [5])

Mu1 = Parameter(name = 'Mu1',
    nature = 'external',
    type = 'real',
    value = 0.0015,
    texname = 'M_{{u}_1}',
    lhablock = 'MASS',
    lhacode = [2])

Mu2 = Parameter(name = 'Mu2',
    nature = 'external',
    type = 'real',
    value = 1.27,
    texname = 'M_{{u}_2}',
    lhablock = 'MASS',
    lhacode = [4])

Mu3 = Parameter(name = 'Mu3',
    nature = 'external',
    type = 'real',
    value = 171.2,
    texname = 'M_{{u}_3}',
    lhablock = 'MASS',
    lhacode = [6])

Wu3 = Parameter(name = 'Wu3',
    nature = 'external',
    type = 'real',
    value = 1.51,
    texname = '\\Gamma_{{u}_3}',
    lhablock = 'DECAY',
    lhacode = [6])

Me1 = Parameter(name = 'Me1',
    nature = 'external',
    type = 'real',
    value = 0.000511,
    texname = 'M_{{e}_1}',
    lhablock = 'MASS',
    lhacode = [11])

Me2 = Parameter(name = 'Me2',
    nature = 'external',
    type = 'real',
    value = 0.105,
    texname = 'M_{{e}_2}',
    lhablock = 'MASS',
    lhacode = [13])

Me3 = Parameter(name = 'Me3',
    nature = 'external',
    type = 'real',
    value = 1.776,
    texname = 'M_{{e}_3}',
    lhablock = 'MASS',
    lhacode = [15])

MChi1 = Parameter(name = 'MChi1',
    nature = 'external',
    type = 'real',
    value = 100.,
    texname = 'M_{{Chi}_1}',
    lhablock = 'MASS',
    lhacode = [9958431])

WChi1 = Parameter(name = 'WChi1',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\Gamma_{{Chi}_1}',
    lhablock = 'DECAY',
    lhacode = [9958431])

MChi2 = Parameter(name = 'MChi2',
    nature = 'external',
    type = 'real',
    value = 100.,
    texname = 'M_{{Chi}_2}',
    lhablock = 'MASS',
    lhacode = [9956206])

WChi2 = Parameter(name = 'WChi2',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\Gamma_{{Chi}_2}',
    lhablock = 'DECAY',
    lhacode = [9956206])

MChi3 = Parameter(name = 'MChi3',
    nature = 'external',
    type = 'real',
    value = 100.,
    texname = 'M_{{Chi}_3}',
    lhablock = 'MASS',
    lhacode = [9979223])

WChi3 = Parameter(name = 'WChi3',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\Gamma_{{Chi}_3}',
    lhablock = 'DECAY',
    lhacode = [9979223])

MChiM = Parameter(name = 'MChiM',
    nature = 'external',
    type = 'real',
    value = 100.,
    texname = 'M_{ChiM}',
    lhablock = 'MASS',
    lhacode = [9984071])

WChiM = Parameter(name = 'WChiM',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\Gamma_{ChiM}',
    lhablock = 'DECAY',
    lhacode = [9984071])

Mh = Parameter(name = 'Mh',
    nature = 'external',
    type = 'real',
    value = 100.,
    texname = 'M_{h}',
    lhablock = 'MASS',
    lhacode = [25])

Wh = Parameter(name = 'Wh',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\Gamma_{h}',
    lhablock = 'DECAY',
    lhacode = [25])

MZ = Parameter(name = 'MZ',
    nature = 'external',
    type = 'real',
    value = 91.1876,
    texname = 'M_{Z}',
    lhablock = 'MASS',
    lhacode = [23])

WZ = Parameter(name = 'WZ',
    nature = 'external',
    type = 'real',
    value = 2.4952,
    texname = '\\Gamma_{Z}',
    lhablock = 'DECAY',
    lhacode = [23])

WWp = Parameter(name = 'WWp',
    nature = 'external',
    type = 'real',
    value = 2.141,
    texname = '\\Gamma_{W^+}',
    lhablock = 'DECAY',
    lhacode = [24])

aS = Parameter(name='aS',
    nature = 'external',
    type = 'real',
    value = 0.119,
    texname = '\\text{aS}',
    lhablock = 'SMINPUTS',
    lhacode = [3] )

aEWM1 = Parameter(name='aEWM1',
    nature = 'external',
    type = 'real',
    value = 137.035999679,
    texname = '\\text{aEWM1}',
    lhablock = 'SMINPUTS',
    lhacode = [1] )

Gf = Parameter(name='Gf',
    nature = 'external',
    type = 'real',
    value = 0.0000116639,
    texname = 'G_f',
    lhablock = 'SMINPUTS',
    lhacode = [2] )

G = Parameter(name='G',
    nature = 'internal',
    type = 'real',
    value = '2*cmath.sqrt(aS)*cmath.sqrt(cmath.pi)',
    texname = 'g_3')

el = Parameter(name='el',
    nature = 'internal',
    type = 'real',
    value = '2*cmath.sqrt(1/aEWM1)*cmath.sqrt(cmath.pi)',
    texname = '\\text{el}')

MWp = Parameter(name='MWp',
    nature = 'internal',
    type = 'real',
    value = 'cmath.sqrt(MZ**2/2. + cmath.sqrt(MZ**4/4. - (MZ**2*cmath.pi)/(cmath.sqrt(2)*aEWM1*Gf)))',
    texname = '\\text{MWp}')

TW = Parameter(name='TW',
    nature = 'internal',
    type = 'real',
    value = 'cmath.asin(cmath.sqrt(1 - MWp**2/MZ**2))',
    texname = '\\text{TW}')

g1 = Parameter(name='g1',
    nature = 'internal',
    type = 'real',
    value = 'el*1./cmath.cos(TW)',
    texname = 'g_1')

g2 = Parameter(name='g2',
    nature = 'internal',
    type = 'real',
    value = 'el*1./cmath.sin(TW)',
    texname = 'g_2')

vvSM = Parameter(name='vvSM',
    nature = 'internal',
    type = 'real',
    value = '2*cmath.sqrt(MWp**2/g2**2)',
    texname = '\\text{vvSM}')

Yu11 = Parameter(name='Yu11',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Mu1)/vvSM',
    texname = '\\text{Yu11}')

Yu12 = Parameter(name='Yu12',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu12}')

Yu13 = Parameter(name='Yu13',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu13}')

Yu21 = Parameter(name='Yu21',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu21}')

Yu22 = Parameter(name='Yu22',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Mu2)/vvSM',
    texname = '\\text{Yu22}')

Yu23 = Parameter(name='Yu23',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu23}')

Yu31 = Parameter(name='Yu31',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu31}')

Yu32 = Parameter(name='Yu32',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yu32}')

Yu33 = Parameter(name='Yu33',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Mu3)/vvSM',
    texname = '\\text{Yu33}')

Yd11 = Parameter(name='Yd11',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Md1)/vvSM',
    texname = '\\text{Yd11}')

Yd12 = Parameter(name='Yd12',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd12}')

Yd13 = Parameter(name='Yd13',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd13}')

Yd21 = Parameter(name='Yd21',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd21}')

Yd22 = Parameter(name='Yd22',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Md2)/vvSM',
    texname = '\\text{Yd22}')

Yd23 = Parameter(name='Yd23',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd23}')

Yd31 = Parameter(name='Yd31',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd31}')

Yd32 = Parameter(name='Yd32',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Yd32}')

Yd33 = Parameter(name='Yd33',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Md3)/vvSM',
    texname = '\\text{Yd33}')

Ye11 = Parameter(name='Ye11',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Me1)/vvSM',
    texname = '\\text{Ye11}')

Ye12 = Parameter(name='Ye12',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye12}')

Ye13 = Parameter(name='Ye13',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye13}')

Ye21 = Parameter(name='Ye21',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye21}')

Ye22 = Parameter(name='Ye22',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Me2)/vvSM',
    texname = '\\text{Ye22}')

Ye23 = Parameter(name='Ye23',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye23}')

Ye31 = Parameter(name='Ye31',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye31}')

Ye32 = Parameter(name='Ye32',
    nature = 'internal',
    type = 'complex',
    value = '0',
    texname = '\\text{Ye32}')

Ye33 = Parameter(name='Ye33',
    nature = 'internal',
    type = 'complex',
    value = '(cmath.sqrt(2)*Me3)/vvSM',
    texname = '\\text{Ye33}')

Lam = Parameter(name='Lam',
    nature = 'internal',
    type = 'complex',
    value = 'Mh**2/vvSM**2',
    texname = '\\text{Lam}')

HPP1 = Parameter(name='HPP1',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\text{HPP1}',
    lhablock = 'EFFHIGGSCOUPLINGS',
    lhacode = [25,22,22] )

HGG1 = Parameter(name='HGG1',
    nature = 'external',
    type = 'real',
    value = 0.,
    texname = '\\text{HGG1}',
    lhablock = 'EFFHIGGSCOUPLINGS',
    lhacode = [25,21,21] )

