"""Model A, Figure 3: Omega h^2 vs m_chi (15 points) via MadDM.

TODO:
  - Grid 15 points in m_chi (via m_S) from ~50 GeV to ~1 TeV at fixed
    m_D=500 GeV, y=1, theta=0.
  - For each point: write the SLHA, run SPheno via _runners.run_spheno,
    then _runners.run_maddm(ufo, param_card, observables=["relic"],
    dm_pdg=9000001) and collect omega_h2.
  - Overlay the Planck 2018 band (0.1200 +- 0.0012) as a horizontal
    shaded region.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model A Figure 3 (Omega h^2 vs m_chi) is stubbed. "
        "Needs: 15-point MadDM scan via _runners.run_maddm with observables=['relic'] "
        "against the SARAH UFO at args.model_hash, plus a Planck-2018 horizontal "
        "band overlay."
    )
