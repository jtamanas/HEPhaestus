"""Model B (SD+2HDM), Figure 1 (= paper Fig. 2): sigma_SI vs tan(theta).

TODO:
  - 20-point scan over tan(theta) in [-20, 20], log-spaced.
  - Use _runners.run_mg5 with the SD+2HDM UFO at args.model_hash (process
    chi1 u > chi1 u / z a) to capture both h and H exchange.
  - Analytical overlay: sigma_SI_two_higgs from
    eval/.../cross_sections/si_tree_level.py with y_h, y_H from
    eval/.../models/singlet_doublet_2hdm.py (coupling_{h,H}_chi1chi1_2hdm).
  - Fix (m_S, m_D, y, tan_beta, m_H, config) to the paper Fig. 2 benchmark
    (benchmarks/benchmark_points.py :: SD2HDM_BENCHMARKS['fig2_type_I_uu_y1_m200']).
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model B Figure 1 (sigma_SI vs tan(theta)) is stubbed. "
        "Needs: 20-point MG5 scan with the SD+2HDM UFO, plus analytical "
        "overlay from sigma_SI_two_higgs in "
        "eval/2506.19062_wimps_blind_spots/cross_sections/si_tree_level.py."
    )
