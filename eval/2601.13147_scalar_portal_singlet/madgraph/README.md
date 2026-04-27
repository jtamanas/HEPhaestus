# MadGraph UFO Model: Scalar Portal Singlet DM

**Paper:** arXiv:2601.13147 — Singlet Fermion DM + Real Scalar Higgs Portal

## Model Description

The `scalar_portal_singlet` UFO model implements the Lagrangian from Eq. (1)-(8) of
arXiv:2601.13147:

- **SM Higgs sector** extended with a real singlet scalar S
- **Dirac fermion DM** χ coupled to S via `L_DM = g_chi * S * chi_bar * chi`
- **Scalar portal** with coupling λ_hs and linear mixing μ_hs
- **Two CP-even mass eigenstates** h1 (SM-like), h2 (singlet-like) with mixing angle θ

## UFO Build Status

The `has_ufo` sentinel in `__init__.py` is currently set to `False`.
No UFO model is built; the analytical benchmarks (`benchmarks/test_benchmarks.py`)
ship independently and do not require MadGraph.

## Rebuild Recipe

To build the UFO model from FeynRules:

1. Install FeynRules 2.3+ in Mathematica (www.feynrules.phys.ucl.ac.be)
2. Open `feynrules/scalar_portal_singlet.fr` in Mathematica
3. Run the FeynRules `WriteUFO["scalar_portal_singlet"]` command
4. Move the resulting UFO directory to `scalar_portal_singlet/`
5. Set `has_ufo = True` in `__init__.py`

Optional NLOCT computation:
- Requires MadGraph 3.x with NLOCT plugin
- Run: `MG5_aMC> generate_nloct scalar_portal_singlet`

## Benchmark Param Cards

Jinja2 templates for MadGraph param cards at each benchmark:
- `templates/param_card_BP1.dat.j2`
- `templates/param_card_BP_mid.dat.j2`
- `templates/param_card_BP9.dat.j2`

Render with: `python3 templates/render.py <bp_name> <output_path>`

## run_comparison.py

`run_comparison.py` validates MadGraph cross-sections against the analytical
`sigma_pp_h2` reference. It requires `has_ufo = True` and is gated by a
`pytest.skip` if the UFO is not built.
