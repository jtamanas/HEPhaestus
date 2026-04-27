"""Model B, Figure 3: Omega h^2 vs m_chi via MadDM for SD+2HDM.

TODO:
  - 15-point grid in m_chi at fixed tan_beta=5, config='uu', m_H=200 GeV.
  - _runners.run_maddm(observables=['relic'], dm_pdg=<singlet-doublet chi1
    PDG from the SD+2HDM UFO>); plot against Planck 2018 band.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model B Figure 3 (Omega h^2 vs m_chi) is stubbed. "
        "Needs: 15-point MadDM relic scan with the SD+2HDM UFO at args.model_hash."
    )
