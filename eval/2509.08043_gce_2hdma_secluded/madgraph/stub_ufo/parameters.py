"""
Vendored stub for Bauer 2HDM+a UFO parameter list.

This is a STUB only — parameter values are placeholders.
The stub exists solely to make bauer_ufo_check.py CI-executable without
a full MadGraph5 + FeynRules installation.

Parameter names follow the LHC DM WG 2HDM+a public spec (Bauer:2017ota UFO).
Sourced from: arXiv:2509.08043, Section 3.2.6 (S0 E5=NOT_FOUND fallback).

For the actual Bauer UFO, see:
  https://feynrules.irmp.ucl.ac.be/wiki/DMSimpt (Pseudoscalar_2HDM model)
  or the LHC DM WG tools page.
"""


class _Param:
    """Minimal parameter descriptor (name + placeholder value)."""
    def __init__(self, name: str, value: float = 0.0):
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        return f"_Param(name={self.name!r}, value={self.value})"


# Vendored stub parameter list — names match EXPECTED_PARAMS in expected_ufo_params.py.
# Values are illustrative placeholders (set to BP-A anchor where applicable).
all_parameters = [
    _Param("MXD",     30.0),      # DM mass [GeV]
    _Param("MHA",     800.0),     # Heavy pseudoscalar mass [GeV]
    _Param("Mha",     50.0),      # Light pseudoscalar mass [GeV]
    _Param("tanbeta", 1.0),       # tan(beta)
    _Param("sinp",    0.09983),   # sin(theta) ~ sin(0.1) at BP-A
    _Param("yxd",     0.5),       # DM Yukawa coupling
    _Param("lam3",    1.0),       # trilinear lambda_3 [placeholder]
    _Param("lamP1",   1.0),       # portal lambda'_1 [placeholder]
    # Additional SM-sector parameters present in the full UFO (stubs):
    _Param("aS",      0.118),     # strong coupling
    _Param("aEWM1",   137.036),   # inverse electromagnetic coupling
    _Param("Gf",      1.1664e-5), # Fermi constant [GeV^-2]
    _Param("mZ",      91.1876),   # Z boson mass [GeV]
    _Param("mH",      125.25),    # Higgs mass [GeV]
    _Param("mb",      4.18),      # bottom quark mass [GeV]
    _Param("mt",      172.69),    # top quark mass [GeV]
]
