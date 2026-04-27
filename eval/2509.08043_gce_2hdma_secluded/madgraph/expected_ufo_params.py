"""
Expected UFO parameter names for the Bauer 2HDM+a UFO model.
arXiv:2509.08043, Section 3.2.6: "using the 2HDM Universal FeynRules Output (UFO)
from Ref. [Bauer:2017ota]".

S0 E5=NOT_FOUND: the paper gives no SHA or FeynRules version tag.
Fallback decision (plan BL7 route 2): use vendored stub with LHC DM WG 2HDM+a
parameter names. See madgraph/README.md for details.

Parameter names follow the LHC DM WG 2HDM+a public specification
(as used by Bauer et al. UFO, Pseudoscalar_2HDM model):
  MXD      — DM mass (Dirac fermion χ)
  MHA      — heavy pseudoscalar mass (A)
  Mha      — light pseudoscalar mass (a)
  tanbeta  — tan(β), ratio of Higgs VEVs
  sinp     — sin(θ), pseudoscalar mixing angle
  yxd      — overall DM Yukawa coupling y_χ
  lam3     — trilinear coupling λ_3
  lamP1    — portal coupling λ'_1
"""

EXPECTED_PARAMS = frozenset({
    "MXD",
    "MHA",
    "Mha",
    "tanbeta",
    "sinp",
    "yxd",
    "lam3",
    "lamP1",
})

PINNED_VERSION = "Bauer-2HDM+a-stub-v1"

# SHA-256 of madgraph/stub_ufo/parameters.py (computed after commit)
# Updated by the round-2 fixer after stub_ufo/parameters.py is committed.
PINNED_SHA = "421eb116b7416d42ff3a4106167414faa0b2f918a5214f8690c4ca6133085f48"
