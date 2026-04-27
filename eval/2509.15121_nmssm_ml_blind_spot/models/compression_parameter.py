"""
Compression parameter for compressed NMSSM neutralino spectrum.
arXiv:2509.15121, Eq. (6).

The compression parameter epsilon quantifies the relative mass splitting
between the NLSP (chi2) and LSP (chi1):

    epsilon = m_chi2 / m_chi1 - 1

All masses are taken as absolute values |m|.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def compression_parameter(m_chi1: float, m_chi2: float, m_chi3: float = None) -> float:
    """
    Compression parameter epsilon. arXiv:2509.15121, Eq. (6):

        epsilon = m_chi2 / m_chi1 - 1

    Quantifies the relative mass splitting between the NLSP (chi2) and the
    LSP (chi1). A small epsilon means a compressed spectrum where soft decay
    products from chi2 -> chi1 + X are hard to detect.

    Notes:
      - All masses are taken as |m| (absolute values).
      - The formula uses only chi1 and chi2. The m_chi3 argument is accepted
        but unused; it is present for API compatibility with callers that
        pass all three neutralino masses.
      - Phase-1 re-read confirms Eq. (6): epsilon = m_chi2/m_chi1 - 1
        (NOT (m_chi3 - m_chi1)/m_chi1 which was the initial draft suggestion).

    Parameters
    ----------
    m_chi1 : float — LSP mass |m_chi1| [GeV]
    m_chi2 : float — NLSP mass |m_chi2| [GeV]
    m_chi3 : float, optional — ignored; accepted for API compatibility

    Returns
    -------
    float : dimensionless compression parameter epsilon >= 0
    """
    return abs(m_chi2) / abs(m_chi1) - 1.0
