"""
neutrino_fog.py — neutrino floor interpolation.

Default: DDCalc built-in (no external data required).
Opt-in: O'Hare 2021 SI Xenon floor (MIT license, vendored CSV).

Usage:
    fog = NeutrinoFog()  # uses DDCalc built-in
    fog = NeutrinoFog(source="ohare_2021")  # uses vendored CSV

    sigma_floor = fog.sigma_si_floor(m_dm_gev=100.0)
    n_sigma = fog.n_sigma_above_floor(m_dm_gev, sigma_si)
    info = fog.to_dict()
"""
from __future__ import annotations

import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OHARE_CSV = DATA_DIR / "neutrino_fog_ohare_2021.csv"

# SHA256 of vendored CSV (from data/NOTICE)
OHARE_2021_SHA256 = "da5eadf0df53d6a6d22835e4eecc9fe4d434decd9eed439310236893ed60f1fb"
OHARE_2021_COMMIT = "0df3d0cd2322602dc147a66d94055f7f64879d80"


def _log_interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Log-log linear interpolation. Extrapolates at boundaries."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    # Binary search
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    # Log-log interpolation
    t = math.log(x / xs[lo]) / math.log(xs[hi] / xs[lo])
    log_y = math.log(ys[lo]) + t * math.log(ys[hi] / ys[lo])
    return math.exp(log_y)


class NeutrinoFog:
    """
    Neutrino floor provider.

    source: "ddcalc_builtin_2.2.0" (default) | "ohare_2021"
    """

    SUPPORTED_SOURCES = {"ddcalc_builtin_2.2.0", "ohare_2021"}

    def __init__(self, source: str = "ddcalc_builtin_2.2.0"):
        if source not in self.SUPPORTED_SOURCES:
            raise ValueError(
                f"Neutrino fog source '{source}' not supported in v1. "
                f"Valid: {self.SUPPORTED_SOURCES}"
            )
        self.source = source
        self._ms: list[float] | None = None
        self._sigmas: list[float] | None = None

        if source == "ohare_2021":
            self._load_ohare()

    def _load_ohare(self):
        """Load the vendored O'Hare 2021 CSV."""
        if not OHARE_CSV.exists():
            raise FileNotFoundError(
                f"O'Hare 2021 CSV not found: {OHARE_CSV}. "
                "This file should be vendored at data/neutrino_fog_ohare_2021.csv."
            )
        ms, sigmas = [], []
        with open(OHARE_CSV) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    ms.append(float(parts[0]))
                    sigmas.append(float(parts[1]))
        self._ms = ms
        self._sigmas = sigmas

    def sigma_si_floor(self, m_dm_gev: float) -> float | None:
        """
        Return the SI neutrino floor σ [cm²] at m_DM [GeV].
        Returns None for DDCalc built-in (not interpolated externally).
        """
        if self.source == "ohare_2021":
            if self._ms is None:
                return None
            return _log_interp(m_dm_gev, self._ms, self._sigmas)
        # DDCalc built-in: not accessible without linking
        return None

    def n_sigma_above_floor(self, m_dm_gev: float, sigma_si: float) -> float | None:
        """
        Number of log-log 'sigma' the point is above the floor.
        Returns None if floor is not computable (DDCalc built-in).
        """
        floor = self.sigma_si_floor(m_dm_gev)
        if floor is None or floor <= 0 or sigma_si <= 0:
            return None
        return math.log10(sigma_si / floor)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "definition": "discovery_limit_90cl",
            "commit_sha": OHARE_2021_COMMIT if self.source == "ohare_2021" else None,
        }
