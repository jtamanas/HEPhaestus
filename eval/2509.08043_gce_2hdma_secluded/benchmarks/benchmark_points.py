"""
Benchmark parameter points for arXiv:2509.08043.

2HDM+a benchmarks (THDMA_BENCHMARKS): 6 points varying one axis at a time
around the anchor BP-A (m_A=800, m_a=50, m_chi=30, θ=0.1, g_χ=0.5, tan_β=1).

Secluded hypercharge benchmarks: NOT included. S0 E1=NOT_FOUND — the paper
does not explicitly state a (m_χ, m_Z', g_D) triplet for the thermal anchor.
See README and paper_extracted.md for details.

Sigma_SI targets in THDMA_BENCHMARKS["checks"] are computed from sigma_SI_exact
(the same formula implemented in cross_sections/sigma_si_2hdma_exact.py) for
self-consistency. See hand_calc_ledger.md for the independent step-by-step derivation.
"""

import numpy as np

# =========================================================================
# 2HDM+a Benchmark Points (THDMA_BENCHMARKS)
# =========================================================================
# Anchor BP-A: m_A=800, m_a=50, m_chi=30 GeV, θ=0.1, g_χ=0.5, tan_β=1
# All other BPs vary ONE parameter at a time from the anchor.
# =========================================================================

THDMA_BENCHMARKS = {
    # -----------------------------------------------------------------------
    # BP-A: Anchor (GCE-fit benchmark from paper Eq. 50 / Fig. 9)
    # -----------------------------------------------------------------------
    "BP-A": {
        "params": {
            "m_chi": 30.0,
            "m_a": 50.0,
            "m_A": 800.0,
            "theta": 0.1,
            "g_chi": 0.5,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at anchor BP-A",
                "quantity": "sigma_SI",
                "expected": 2.371446e-49,  # cm^2 — from hand_calc_ledger.md BP-A
                "tolerance": 0.02,
                "unit": "cm^2",
            },
            {
                "label": "G(x=0.36, 0) loop function at anchor",
                "quantity": "G_loop",
                "expected": 0.579703,
                "tolerance": 1e-4,
                "unit": "",
            },
        ],
    },
    # -----------------------------------------------------------------------
    # BP-B: Vary m_A (doubled to 1600 GeV) — σ ~ m_A^4, expect ×16 increase
    # -----------------------------------------------------------------------
    "BP-B": {
        "params": {
            "m_chi": 30.0,
            "m_a": 50.0,
            "m_A": 1600.0,
            "theta": 0.1,
            "g_chi": 0.5,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at BP-B (vary m_A)",
                "quantity": "sigma_SI",
                "expected": 3.816666e-48,  # cm^2 — from hand_calc_ledger.md BP-B
                "tolerance": 0.02,
                "unit": "cm^2",
            },
        ],
    },
    # -----------------------------------------------------------------------
    # BP-C: Vary m_a (halved to 25 GeV) — σ ~ m_a^{-4}, expect ×16 increase
    # Also changes x = m_chi^2/m_a^2 = 30^2/25^2 = 1.44 → G changes
    # -----------------------------------------------------------------------
    "BP-C": {
        "params": {
            "m_chi": 30.0,
            "m_a": 25.0,
            "m_A": 800.0,
            "theta": 0.1,
            "g_chi": 0.5,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at BP-C (vary m_a)",
                "quantity": "sigma_SI",
                "expected": 1.497941e-48,  # cm^2 — from hand_calc_ledger.md BP-C
                "tolerance": 0.02,
                "unit": "cm^2",
            },
        ],
    },
    # -----------------------------------------------------------------------
    # BP-D: Vary m_chi (doubled to 60 GeV) — σ ~ m_chi^2, expect ×4 increase
    # Also changes x = 60^2/50^2 = 1.44 → G changes; mu changes
    # -----------------------------------------------------------------------
    "BP-D": {
        "params": {
            "m_chi": 60.0,
            "m_a": 50.0,
            "m_A": 800.0,
            "theta": 0.1,
            "g_chi": 0.5,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at BP-D (vary m_chi)",
                "quantity": "sigma_SI",
                "expected": 3.838448e-49,  # cm^2 — from hand_calc_ledger.md BP-D
                "tolerance": 0.02,
                "unit": "cm^2",
            },
        ],
    },
    # -----------------------------------------------------------------------
    # BP-E: Vary θ (halved to 0.05) — σ ~ sin^4(2θ), expect ×(sin(0.1)/sin(0.2))^4
    # For small θ: ≈ (0.05/0.1)^4 = 0.0625 → 16× decrease
    # -----------------------------------------------------------------------
    "BP-E": {
        "params": {
            "m_chi": 30.0,
            "m_a": 50.0,
            "m_A": 800.0,
            "theta": 0.05,
            "g_chi": 0.5,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at BP-E (vary theta)",
                "quantity": "sigma_SI",
                "expected": 1.512146e-50,  # cm^2 — from hand_calc_ledger.md BP-E
                "tolerance": 0.02,
                "unit": "cm^2",
            },
        ],
    },
    # -----------------------------------------------------------------------
    # BP-F: Vary g_chi (doubled to 1.0) — σ ~ g_chi^4, expect ×16 increase
    # -----------------------------------------------------------------------
    "BP-F": {
        "params": {
            "m_chi": 30.0,
            "m_a": 50.0,
            "m_A": 800.0,
            "theta": 0.1,
            "g_chi": 1.0,
            "tan_beta": 1.0,
            "sigma_mq": 0.330,
        },
        "checks": [
            {
                "label": "sigma_SI_exact at BP-F (vary g_chi)",
                "quantity": "sigma_SI",
                "expected": 3.794313e-48,  # cm^2 — from hand_calc_ledger.md BP-F
                "tolerance": 0.02,
                "unit": "cm^2",
            },
        ],
    },
}


def thdma_anchor() -> dict:
    """Return BP-A as a flat parameter dict (used by harness refs.py BL6 consistency).

    Returns
    -------
    dict : flat dict with keys m_chi, m_a, m_A, theta, g_chi, tan_beta, sigma_mq
    """
    return dict(THDMA_BENCHMARKS["BP-A"]["params"])
