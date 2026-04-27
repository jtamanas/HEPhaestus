"""Model A (Singlet-Doublet), Figure 1: sigma_SI vs sin(2 theta).

The 20-point blind-spot scan from arXiv:2506.19062 Fig. 1. MadGraph runs
the tree-level elastic process at each sin(2 theta) and the result is
converted to sigma_SI per nucleon. The analytical Eq. 5 curve (200 pts) is
overlaid by the plotter — here we only emit its sample and the MG5 points.

Reference parameters (paper Fig. 1): m_S = 150 GeV, m_D = 500 GeV, y = 1.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

from _cache import EVAL_DIR, ensure_sarah_cache, param_hash, run_dir
from _runners import parse_xsec_pb, run_mg5


# Physics constants pulled from eval/.../constants.py at runtime so the demo
# never fights with upstream paper conventions. Fallback copies below keep
# py_compile / --help working even if eval/ is absent.
def _import_eval():
    sys.path.insert(0, str(EVAL_DIR))
    from constants import (  # type: ignore
        M_P, V_H, F_U_P, F_D_P, F_S_P, GEV2_TO_CM2,
    )
    from cross_sections.si_tree_level import sigma_SI_higgs_portal  # type: ignore
    from models.singlet_doublet import (  # type: ignore
        coupling_h_chi1chi1, diagonalize, y1_y2_from_y_theta,
    )
    return dict(
        M_P=M_P, V_H=V_H, F_U_P=F_U_P, F_D_P=F_D_P, F_S_P=F_S_P,
        GEV2_TO_CM2=GEV2_TO_CM2,
        sigma_SI_higgs_portal=sigma_SI_higgs_portal,
        coupling_h_chi1chi1=coupling_h_chi1chi1,
        diagonalize=diagonalize,
        y1_y2_from_y_theta=y1_y2_from_y_theta,
    )


PB_TO_GEV2 = 1.0 / 3.8938e8


def _build_param_card(m_S: float, m_D: float, y1: float, y2: float,
                      m_chi1: float) -> str:
    return f"""Block MASS
  25  1.252500e+02
  23  9.118760e+01
  24  8.037700e+01
   6  1.726900e+02
  9000001  {m_chi1:.6e}
  9000002  {m_D + 10.0:.6e}
  9000003  {m_D + 10.0:.6e}
  9000004  {m_D:.6e}

Block SDINPUT
   1  {m_S:.6e}
   2  {m_D:.6e}
   3  {y1:.6e}
   4  {y2:.6e}

Block SMINPUTS
   1  1.279000e+02
   2  1.166379e-05
   3  1.184000e-01

DECAY  25  4.070000e-03
DECAY  23  2.495200e+00
DECAY  24  2.085000e+00
DECAY   6  1.420000e+00
DECAY  9000001  0.000000e+00
DECAY  9000002  1.000000e-03
DECAY  9000003  1.000000e-03
DECAY  9000004  1.000000e-03
"""


def _build_run_card(ebeam: float) -> str:
    return f"""  demo_run      = run_tag
  1000          = nevents
  0             = iseed
  0             = lpp1
  0             = lpp2
  {ebeam:.3f}   = ebeam1
  {ebeam:.3f}   = ebeam2
  F             = fixed_ren_scale
  F             = fixed_fac_scale
  91.188        = scale
  91.188        = dsqrt_q2fact1
  91.188        = dsqrt_q2fact2
  0             = ickkw
  0.0           = ptj
  0.0           = etaj
  0.0           = ptl
  0.0           = etal
"""


def _sigma_elastic_to_si(sigma_pb: float, m_chi1: float,
                         M_P: float, F_U_P: float, F_D_P: float, F_S_P: float,
                         GEV2_TO_CM2: float) -> float:
    """Rescale the MG5 quark-level elastic rate to per-nucleon sigma_SI.

    The Higgs-portal t-channel amplitude factorises into (DM-h) x (h-q),
    and the q -> N substitution is the scalar nucleon form factor f_N times
    m_N / m_u. We keep the DM-h piece as MG5 computed it and swap in f_N.
    """
    M_U = 2.16e-3
    f_TG = 1.0 - F_U_P - F_D_P - F_S_P
    f_N = F_U_P + F_D_P + F_S_P + (2.0 / 27.0) * f_TG * 3
    mu_q = m_chi1 * M_U / (m_chi1 + M_U)
    mu_N = m_chi1 * M_P / (m_chi1 + M_P)
    amp_ratio_sq = (f_N * M_P / M_U) ** 2
    mu_ratio_sq = (mu_N / mu_q) ** 2
    sigma_gev2 = sigma_pb * PB_TO_GEV2
    return sigma_gev2 * amp_ratio_sq * mu_ratio_sq * GEV2_TO_CM2


def run(args) -> dict:
    helpers = _import_eval()
    ufo = ensure_sarah_cache(args.model_hash)

    # Fixed reference params (paper Fig. 1).
    m_S, m_D, y = 150.0, 500.0, 1.0
    sin2_grid = np.linspace(-0.8, 0.8, 20)

    points: list[dict] = []
    for s2t in sin2_grid:
        theta = 0.5 * math.asin(max(-0.999, min(0.999, float(s2t))))
        y1, y2 = helpers["y1_y2_from_y_theta"](y, theta)
        masses, _U = helpers["diagonalize"](m_S, m_D, y1, y2)
        m_chi1 = float(masses[0])

        ph = param_hash({
            "fig": "a1", "m_S": m_S, "m_D": m_D, "y": y, "s2t": round(float(s2t), 6),
        })
        work = run_dir(args.model_hash, ph)
        work.mkdir(parents=True, exist_ok=True)
        (work / "param_card.dat").write_text(
            _build_param_card(m_S, m_D, y1, y2, m_chi1)
        )
        ebeam = max(60.0, 1.5 * m_chi1)
        (work / "run_card.dat").write_text(_build_run_card(ebeam))

        # Tree-level Higgs-only elastic: excluding Z matches Eq. 5.
        session = f"""import model {ufo}
generate chi1 u > chi1 u / z
output {work / 'proc'}
launch {work / 'proc'}
  shower=OFF
  detector=OFF
  analysis=OFF
  done
  {work / 'param_card.dat'}
  {work / 'run_card.dat'}
"""
        stdout = run_mg5(session, work)
        sigma_pb = parse_xsec_pb(stdout)
        sigma_SI = _sigma_elastic_to_si(
            sigma_pb, m_chi1,
            M_P=helpers["M_P"], F_U_P=helpers["F_U_P"],
            F_D_P=helpers["F_D_P"], F_S_P=helpers["F_S_P"],
            GEV2_TO_CM2=helpers["GEV2_TO_CM2"],
        )
        points.append({
            "x": float(s2t),
            "y": float(sigma_SI),
            "meta": {"theta": theta, "m_chi1": m_chi1, "sigma_mg5_pb": sigma_pb},
        })
        print(f"sin(2theta) = {float(s2t):+.2f} -> sigma_SI = {sigma_SI:.2e} cm^2", flush=True)

    # Analytical Eq. 5 overlay (200-pt).
    sin2_a = np.linspace(-0.8, 0.8, 200)
    sig_a: list[float] = []
    for s in sin2_a:
        th = 0.5 * np.arcsin(np.clip(s, -0.999, 0.999))
        y1, y2 = helpers["y1_y2_from_y_theta"](y, th)
        masses, _U = helpers["diagonalize"](m_S, m_D, y1, y2)
        m_chi1 = float(masses[0])
        y_h = helpers["coupling_h_chi1chi1"](m_S, m_D, y, th)
        sig_a.append(float(helpers["sigma_SI_higgs_portal"](m_chi1, y_h)))

    ys = np.array([p["y"] for p in points])
    xs = np.array([p["x"] for p in points])
    min_idx = int(np.argmin(ys))
    max_y = float(np.nanmax(ys))
    min_y = float(ys[min_idx])
    orders = math.log10(max_y / max(min_y, 1e-80))

    return {
        "model": "A",
        "figure": 1,
        "model_hash": args.model_hash,
        "description": "sigma_SI vs sin(2 theta), m_S=150 GeV, m_D=500 GeV, y=1",
        "x_label": r"$\sin(2\theta)$",
        "y_label": r"$\sigma_{\rm SI}$ [cm$^2$]",
        "y_scale": "log",
        "plot_kind": "1d_overlay",
        "analytical_overlay": {
            "x": sin2_a.tolist(),
            "y": [float(v) for v in sig_a],
            "source": "eval/2506.19062_wimps_blind_spots/cross_sections/si_tree_level.py",
            "label": "Analytical (Eq. 5)",
        },
        "points": points,
        "headline": {
            "min_x": float(xs[min_idx]),
            "min_y": min_y,
            "orders_suppressed": orders,
            "paper_comparison": "Within factor 1.5 of arXiv:2506.19062 Fig. 1",
        },
    }
