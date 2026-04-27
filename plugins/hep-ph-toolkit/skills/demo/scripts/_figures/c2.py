"""Model C, Figure 2 (= paper Fig. 7): Omega h^2 evolution (Boltzmann) via MadDM.

TODO:
  - Fix (g_tilde, sin_theta, m_V, m_H2, m_Psi) to Fig. 7 benchmark.
  - _runners.run_maddm(observables=['relic'], dm_pdg=<V>) — MadDM integrates
    the Boltzmann equation internally; we parse Y(x) if the flag
    'print_out' is available, else just omega_h2 at multiple m_V values to
    trace the freeze-out curve.
  - NEVER reimplement the Boltzmann integral here.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model C Figure 2 (Omega h^2 Boltzmann evolution) is stubbed. "
        "Needs: MadDM relic-density call via _runners.run_maddm with the "
        "Dark-SU(3) UFO; parse the freeze-out trace (Y vs x) from MadDM's "
        "output files. Do NOT reimplement the Boltzmann equation."
    )
