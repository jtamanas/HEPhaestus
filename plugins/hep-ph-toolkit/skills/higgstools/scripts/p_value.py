"""
p_value.py — thin scipy.stats.chi2.sf wrapper for HiggsSignals p-values.

IMPORTANT: (chi2, ndf) pairs MUST come from HS native output
(HiggsSignals_get_Peak_Chisq). Never compute ndf Python-side from
len(channels) or any other channel count.

This module is intentionally minimal — it is a thin wrapper with no
physics logic beyond calling scipy.
"""
from __future__ import annotations

import sys

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import scipy.stats  # noqa: E402


def compute_p_value(chi2: float, ndf: int) -> float:
    """
    Compute p-value from chi2 and ndf using scipy.stats.chi2.sf.

    p_value = P(chi2 >= observed | ndf) = 1 - CDF(chi2, ndf)
            = scipy.stats.chi2.sf(chi2, ndf)

    Parameters
    ----------
    chi2 : float
        Observed chi2 value from HiggsSignals native output.
    ndf : int
        Number of degrees of freedom from HiggsSignals native output
        (HiggsSignals_get_Peak_Chisq). NOT computed from Python-side channel count.

    Returns
    -------
    float
        p-value in [0, 1].

    Notes
    -----
    p-values assume the null hypothesis of SM + best-fit HS nuisance parameters;
    they are *not* a global goodness-of-fit. See HS manual §4.3.
    """
    return float(scipy.stats.chi2.sf(chi2, ndf))
