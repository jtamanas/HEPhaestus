"""Model A, Figure 2: sigma_SI 2D scan in (m_chi, y_h), ~100 points.

TODO:
  - Build a ~10x10 grid over (m_chi, y_h) consistent with paper Fig. 1 right
    panel; derive (m_S, m_D, y, theta) that realise each grid point.
  - For each grid point: run_mg5(chi1 u > chi1 u / z), convert to sigma_SI,
    collect {x=m_chi, y=y_h, z=sigma_SI}.
  - Analytical overlay: sigma_SI_higgs_portal from eval/.../si_tree_level.py
    evaluated on the same grid.
  - plot_kind: "2d_heatmap" with a log-sigma colormap + an exclusion
    contour at LZ 2022 limit if available in benchmarks/benchmark_points.py.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model A Figure 2 (sigma_SI 2D scan in m_chi vs y_h) is stubbed. "
        "Needs: ~100-point MG5 scan via _runners.run_mg5 with the "
        "singlet-doublet UFO at args.model_hash, plus the Eq. 5 analytical "
        "grid from eval/2506.19062_wimps_blind_spots/cross_sections/si_tree_level.py."
    )
