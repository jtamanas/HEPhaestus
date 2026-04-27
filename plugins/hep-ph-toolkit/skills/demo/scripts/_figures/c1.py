"""Model C (Dark SU(3)), Figure 1: scalar DM sigma_SI ~ 0 cancellation demo.

Five parameter points spanning g_tilde, sin_theta, m_H2 — each one shows
sigma_SI(Psi) consistent with zero at MG5 numerical precision (Eq. 29).

TODO:
  - Pick 5 benchmark points (DSU3_BENCHMARKS['scalar_blind_spot',
    'scalar_blind_spot_2', ...]).
  - For each: _runners.run_mg5 with the dark-SU(3) UFO, process
    Psi u > Psi u / z, collect sigma_pb. Expect |sigma_SI| < 1e-55 cm^2.
  - Analytical overlay: sigma_SI_scalar_exact_cancellation from
    eval/.../models/dark_su3.py — reports the amplitude which is
    identically zero for the Psi. Make that visually obvious.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model C Figure 1 (scalar DM exact cancellation) is stubbed. "
        "Needs: 5-point MG5 scan with the Dark-SU(3) UFO; compare against "
        "sigma_SI_scalar_exact_cancellation from "
        "eval/2506.19062_wimps_blind_spots/models/dark_su3.py."
    )
