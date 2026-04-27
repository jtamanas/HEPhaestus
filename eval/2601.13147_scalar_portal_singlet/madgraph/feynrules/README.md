# FeynRules Model: Scalar Portal Singlet DM

## File

`scalar_portal_singlet.fr` — FeynRules 2.3 source for the singlet fermion DM model.

## Rebuild to UFO

1. Launch Mathematica
2. Load FeynRules: `<< FeynRules``
3. Load model: `LoadModel["scalar_portal_singlet.fr"]`
4. Validate: `CheckHermiticity[Lagrangian]`
5. Generate UFO: `WriteUFO[Lagrangian, Output -> "scalar_portal_singlet"]`

The UFO output directory should be moved to `../scalar_portal_singlet/`.

## References

- FeynRules 2.0: Alloul et al., Comput. Phys. Commun. 185 (2014) 2250
- FeynRules manual: arxiv:1310.1921
