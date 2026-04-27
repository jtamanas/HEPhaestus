"""Model B, Figure 2 (= paper Fig. 3): sigma_SI 2D scan in (m_chi, tan_beta).

TODO:
  - ~100-point (10x10) scan: m_chi in [100, 1000] GeV, tan_beta in [1, 50].
  - Fix config='uu', m_H=m_A=m_Hpm=200 GeV, y=1 per paper Fig. 3.
  - Per grid point: derive (m_S, theta) to realise m_chi, then run_mg5 with
    the SD+2HDM UFO; convert quark-level xsec to per-nucleon sigma_SI.
  - Overlay LZ 2022 exclusion contour if available in benchmarks/.
"""

from __future__ import annotations


def run(args) -> dict:
    raise NotImplementedError(
        "Model B Figure 2 (sigma_SI 2D in m_chi vs tan_beta) is stubbed. "
        "Needs: ~100-point MG5 scan with the SD+2HDM UFO, plus exclusion "
        "contour overlay from benchmarks/benchmark_points.py."
    )
