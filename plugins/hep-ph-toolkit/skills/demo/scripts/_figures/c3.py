"""Model C, Figure 3 (= paper Fig. 8): sigma_SI(vector) vs m_V, 20 points.

TODO:
  - 20 points in m_V in [10, 500] GeV at fixed (g_tilde, sin_theta, m_H2,
    m_Psi) from DSU3_BENCHMARKS['vector_reference'].
  - _runners.run_mg5 with the Dark-SU(3) UFO, process V u > V u (Higgs
    portal). Convert quark-level xsec to per-nucleon sigma_SI.
  - Analytical overlay: sigma_SI_vector from
    eval/.../models/dark_su3.py evaluated on the same grid.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model C Figure 3 (sigma_SI(vector) vs m_V) is stubbed. "
        "Needs: 20-point MG5 scan with the Dark-SU(3) UFO, plus analytical "
        "overlay from sigma_SI_vector in "
        "eval/2506.19062_wimps_blind_spots/models/dark_su3.py."
    )
