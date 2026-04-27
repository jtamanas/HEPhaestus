"""
Benchmark points for arXiv:2603.23040 (Scotogenic Inverse Seesaw).

Parameter convention: (M_R, mu_S, M_N) where
  M_R = m_E [GeV]    vector-like doublet mass
  mu_S     [GeV]     symmetric mixing scale (mu_1 = mu_2 = mu_S)
  M_N = m_N [GeV]    Majorana singlet mass

BP masses confirmed by Phase-1 re-read: m_chi = 42, 59, 61 GeV.
"""

# Scalar triplet masses [GeV] — fixed in paper
M_PHI_TRIPLET = (1000.0, 1200.0, 1400.0)

SCOTO_BENCHMARKS = {
    "BP1": {
        "params": {
            "M_R": 42.0,    # [GeV] vector-like doublet mass
            "mu_S": 0.05,   # [GeV] symmetric mixing scale
            "M_N": 42.0,    # [GeV] Majorana singlet mass
        },
        "checks": [
            {
                "label": "m_chi1",
                "quantity": "|X_1|",
                "expected": 42.0,
                "tolerance": 1e-4,
                "unit": "GeV",
            },
        ],
        "description": "BP1: m_chi ~ 42 GeV, off Higgs funnel",
    },
    "BP2": {
        "params": {
            "M_R": 59.0,    # [GeV]
            "mu_S": 0.05,   # [GeV]
            "M_N": 59.0,    # [GeV]
        },
        "checks": [
            {
                "label": "m_chi1",
                "quantity": "|X_1|",
                "expected": 59.0,
                "tolerance": 1e-4,
                "unit": "GeV",
            },
        ],
        "description": "BP2: m_chi ~ 59 GeV, near Higgs funnel",
    },
    "BP3": {
        "params": {
            "M_R": 61.0,    # [GeV]
            "mu_S": 0.05,   # [GeV]
            "M_N": 61.0,    # [GeV]
        },
        "checks": [
            {
                "label": "m_chi1",
                "quantity": "|X_1|",
                "expected": 61.0,
                "tolerance": 1e-4,
                "unit": "GeV",
            },
        ],
        "description": "BP3: m_chi ~ 61 GeV, near Higgs funnel (inside viable window)",
    },
}
