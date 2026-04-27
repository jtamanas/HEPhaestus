"""
exclusion.py — HiggsBounds and HiggsSignals exclusion logic.

HiggsBounds-5 convention:
    hb_allowed = AND of per-channel HBresult values.
    A point is HB-excluded iff any channel's HBresult == 0.

HiggsSignals-2 convention:
    hs_consistent = (chi2_total - chi2_sm_ref) < delta_chi2
    Default delta_chi2 = 6.18 (2D 95% CL, two free parameters).
    chi2_sm_ref is cached at install time.

No analytic fallback. No Python-side coupling synthesis.
"""
from __future__ import annotations

import sys
from typing import Any, Protocol

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


class Channel(Protocol):
    """Protocol for a HiggsBounds channel result."""
    id: int
    expref: str
    obsratio: float
    hb_result: int


def compute_hb_allowed(channels: list[Any]) -> bool:
    """
    Compute HiggsBounds allowed flag.

    A point is HB-allowed iff ALL per-channel HBresult values equal 1.
    This is the AND-of-per-channel convention from HB-5's API.

    Parameters
    ----------
    channels : list
        List of channel objects with .hb_result attribute (0=excluded, 1=allowed).

    Returns
    -------
    bool
        True if all channels have HBresult=1 (or list is empty), False otherwise.
    """
    return all(ch.hb_result == 1 for ch in channels)


def compute_hs_consistent(
    chi2_total: float,
    chi2_sm_ref: float,
    delta_chi2: float = 6.18,
) -> bool:
    """
    Compute HiggsSignals consistency flag.

    A point is HS-consistent iff:
        (chi2_total - chi2_sm_ref) < delta_chi2

    The default delta_chi2 = 6.18 corresponds to the 2D 95% CL exclusion
    contour (two free parameters), as used in arXiv:2506.19062.
    User-tunable via --delta-chi2.

    Parameters
    ----------
    chi2_total : float
        Total chi2 from HiggsSignals for this parameter point.
    chi2_sm_ref : float
        SM reference chi2 cached at install time.
    delta_chi2 : float
        Threshold Δχ² (strict less-than). Default 6.18.

    Returns
    -------
    bool
        True if (chi2_total - chi2_sm_ref) < delta_chi2.
    """
    return (chi2_total - chi2_sm_ref) < delta_chi2
