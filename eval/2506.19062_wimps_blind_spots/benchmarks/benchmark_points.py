"""
Benchmark parameter points extracted from arXiv:2506.19062.

Each benchmark defines:
  - params: input parameters for the model
  - checks: list of quantities to compare, each with:
    - label: human-readable description
    - quantity: which function to call
    - expected: expected numerical value (from the paper or derived)
    - tolerance: acceptable relative difference (default 5%)
    - unit: physical units

Benchmarks are extracted from:
  - Figure captions (specific parameter choices for plots)
  - Text descriptions of scan ranges
  - Known analytical limits (blind spots, asymptotic behavior)
"""

import numpy as np

# ======================================================================
# Singlet-Doublet Model Benchmarks
# ======================================================================

SD_BENCHMARKS = {
    # ------------------------------------------------------------------
    # BP1: Figure 2 benchmark — m_S=150, m_D=500, y=1, theta=0
    # Used as the reference point for the SD+2HDM plots
    # ------------------------------------------------------------------
    "fig2_reference": {
        "params": {
            "m_S": 150.0,
            "m_D": 500.0,
            "y": 1.0,
            "theta": 0.0,  # tan(theta)=0 => theta=0
        },
        "checks": [
            {
                "label": "DM mass from diagonalization",
                "quantity": "m_chi1",
                "expected": 147.0,  # approximate, from m_S with small mixing
                "tolerance": 0.05,
                "unit": "GeV",
            },
            {
                "label": "Charged fermion mass",
                "quantity": "m_psi",
                "expected": 500.0,
                "tolerance": 1e-10,
                "unit": "GeV",
            },
            {
                "label": "Higgs coupling at theta=0",
                "quantity": "y_h_chi1chi1",
                "expected": None,  # compute from diagonalization
                "tolerance": 0.01,
                "unit": "",
            },
            {
                "label": "Blind spot parameter",
                "quantity": "blind_spot",
                "expected": 147.0,  # m_chi1 + m_D*sin(0) = m_chi1
                "tolerance": 0.05,
                "unit": "GeV",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP2: Near blind spot — theta chosen so m_chi1 + m_D*sin(2*theta) ~ 0
    # ------------------------------------------------------------------
    "near_blind_spot": {
        "params": {
            "m_S": 150.0,
            "m_D": 500.0,
            "y": 1.0,
            "theta": -0.148,  # sin(2*theta) ~ -0.29 => 150 + 500*(-0.29) ~ 5
        },
        "checks": [
            {
                "label": "Blind spot parameter (should be near zero)",
                "quantity": "blind_spot",
                "expected": 5.0,  # approximately
                "tolerance": 0.5,
                "unit": "GeV",
            },
            {
                "label": "Tree-level SI cross-section (should be suppressed)",
                "quantity": "sigma_SI_tree",
                "expected": 1e-48,  # order of magnitude, suppressed
                "tolerance": 1.0,  # order-of-magnitude check
                "unit": "cm^2",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP3: Exact blind spot
    # m_chi1 + m_D * sin(2*theta) = 0 => sin(2*theta) = -m_chi1/m_D
    # ------------------------------------------------------------------
    "exact_blind_spot": {
        "params": {
            "m_S": 150.0,
            "m_D": 500.0,
            "y": 1.0,
            "theta": None,  # to be computed: arcsin(-m_chi1/m_D)/2
        },
        "checks": [
            {
                "label": "Tree-level SI cross-section (exactly zero)",
                "quantity": "sigma_SI_tree",
                "expected": 0.0,
                "tolerance": 1e-50,  # absolute, not relative
                "unit": "cm^2",
            },
            {
                "label": "One-loop SI sets the floor",
                "quantity": "sigma_SI_loop",
                "expected": None,  # to be determined from loop calculation
                "tolerance": 0.10,
                "unit": "cm^2",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP4: Large mass, perturbative couplings
    # ------------------------------------------------------------------
    "heavy_dm": {
        "params": {
            "m_S": 1000.0,
            "m_D": 1200.0,
            "y": 0.5,
            "theta": 0.3,
        },
        "checks": [
            {
                "label": "DM mass from diagonalization",
                "quantity": "m_chi1",
                "expected": 990.0,  # approximate
                "tolerance": 0.05,
                "unit": "GeV",
            },
            {
                "label": "Tree-level SI cross-section",
                "quantity": "sigma_SI_tree",
                "expected": None,  # compute analytically
                "tolerance": 0.05,
                "unit": "cm^2",
            },
        ],
    },
}


# ======================================================================
# Singlet-Doublet + 2HDM Benchmarks
# ======================================================================

SD2HDM_BENCHMARKS = {
    # From Figure 2 caption: (m_S, m_D) = (150, 500), tan_beta = 5
    # Lines: (y, M) = (1, 200), (1, 300), (1, 500), (0.5, 500) GeV
    "fig2_type_I_uu_y1_m200": {
        "params": {
            "m_S": 150.0,
            "m_D": 500.0,
            "y": 1.0,
            "tan_beta": 5.0,
            "m_H": 200.0,
            "m_A": 200.0,
            "m_Hpm": 200.0,
            "config": "uu",
            "type": "I",
        },
        "checks": [
            {
                "label": "h coupling (alignment limit)",
                "quantity": "y_h_chi1chi1",
                "expected": None,  # from Eq. 15
                "tolerance": 0.01,
                "unit": "",
            },
            {
                "label": "H coupling",
                "quantity": "y_H_chi1chi1",
                "expected": None,  # from Eq. 15
                "tolerance": 0.01,
                "unit": "",
            },
        ],
    },
    "fig2_type_II_ud_y1_m300": {
        "params": {
            "m_S": 150.0,
            "m_D": 500.0,
            "y": 1.0,
            "tan_beta": 5.0,
            "m_H": 300.0,
            "m_A": 300.0,
            "m_Hpm": 300.0,
            "config": "ud",
            "type": "II",
        },
        "checks": [
            {
                "label": "h coupling (alignment limit)",
                "quantity": "y_h_chi1chi1",
                "expected": None,
                "tolerance": 0.01,
                "unit": "",
            },
        ],
    },
}


# ======================================================================
# 2HDM+a Benchmarks
# ======================================================================

THDMA_BENCHMARKS = {
    # ------------------------------------------------------------------
    # BP1: Reference point, moderate mixing
    # ------------------------------------------------------------------
    "moderate_mixing": {
        "params": {
            "m_chi": 200.0,
            "m_a": 200.0,
            "m_H": 600.0,
            "m_A": 600.0,
            "m_Hpm": 600.0,
            "y_chi": 1.0,
            "sin_theta": 0.35,
            "tan_beta": 1.0,
            "lambda_3": 3.0,
            "lambda_1P": 0.0,
            "lambda_2P": 0.0,
        },
        "checks": [
            {
                "label": "Pseudoscalar mixing angle",
                "quantity": "theta_mix",
                "expected": np.arcsin(0.35),
                "tolerance": 0.01,
                "unit": "rad",
            },
            {
                "label": "DM-a coupling",
                "quantity": "g_chi_a",
                "expected": 1.0 * np.sqrt(1 - 0.35**2),  # y_chi * cos(theta)
                "tolerance": 1e-10,
                "unit": "",
            },
            {
                "label": "DM-A coupling",
                "quantity": "g_chi_A",
                "expected": 1.0 * 0.35,  # y_chi * sin(theta)
                "tolerance": 1e-10,
                "unit": "",
            },
            {
                "label": "Trilinear lambda_haa (lambda_1P=lambda_2P=0)",
                "quantity": "lambda_haa",
                "expected": 0.0,  # both portal couplings zero
                "tolerance": 1e-10,
                "unit": "GeV",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP2: Non-zero portal couplings
    # ------------------------------------------------------------------
    "nonzero_portal": {
        "params": {
            "m_chi": 100.0,
            "m_a": 150.0,
            "m_H": 600.0,
            "m_A": 600.0,
            "m_Hpm": 600.0,
            "y_chi": 0.5,
            "sin_theta": 0.1,
            "tan_beta": 3.0,
            "lambda_3": 1.0,
            "lambda_1P": 2.0,
            "lambda_2P": -1.0,
        },
        "checks": [
            {
                "label": "Trilinear lambda_haa",
                "quantity": "lambda_haa",
                "expected": None,  # compute from Eq. 25
                "tolerance": 0.01,
                "unit": "GeV",
            },
            {
                "label": "Trilinear lambda_Haa",
                "quantity": "lambda_Haa",
                "expected": None,  # compute from Eq. 25
                "tolerance": 0.01,
                "unit": "GeV",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP3: Collider-stable pseudoscalar regime (Fig. 6)
    # sin(theta) ~ 1e-8, very small mixing
    # ------------------------------------------------------------------
    "collider_stable_a": {
        "params": {
            "m_chi": 200.0,
            "m_a": 100.0,
            "m_H": 600.0,
            "m_A": 600.0,
            "m_Hpm": 600.0,
            "y_chi": 1.0,
            "sin_theta": 1e-8,
            "tan_beta": 5.0,
            "lambda_3": 1.0,
            "lambda_1P": 1.0,
            "lambda_2P": 1.0,
        },
        "checks": [
            {
                "label": "DM-a coupling (essentially y_chi)",
                "quantity": "g_chi_a",
                "expected": 1.0,  # cos(1e-8) ~ 1
                "tolerance": 1e-8,
                "unit": "",
            },
            {
                "label": "SI cross-section deep in neutrino floor",
                "quantity": "sigma_SI_loop",
                "expected": None,  # expected to be below neutrino floor
                "tolerance": 1.0,
                "unit": "cm^2",
            },
        ],
    },
}


# ======================================================================
# Dark SU(3) Benchmarks
# ======================================================================

DSU3_BENCHMARKS = {
    # ------------------------------------------------------------------
    # BP1: Vector DM, reference point
    # ------------------------------------------------------------------
    "vector_reference": {
        "params": {
            "g_tilde": 1.0,
            "sin_theta": 0.1,
            "m_H2": 300.0,
            "m_V": 200.0,
            "m_Psi": 300.0,  # fixed in vector/vector scenario
        },
        "checks": [
            {
                "label": "Vector DM SI cross-section (tree-level)",
                "quantity": "sigma_SI_vector",
                "expected": None,  # compute from Higgs portal
                "tolerance": 0.05,
                "unit": "cm^2",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP2: Scalar DM exact blind spot verification
    # The scalar Psi has sigma_SI = 0 EXACTLY for all parameters
    # ------------------------------------------------------------------
    "scalar_blind_spot": {
        "params": {
            "g_tilde": 1.0,
            "sin_theta": 0.1,
            "m_H2": 300.0,
            "m_V": 500.0,
            "m_Psi": 200.0,
        },
        "checks": [
            {
                "label": "Scalar DM SI amplitude (exact zero, Eq. 29)",
                "quantity": "blind_spot_amplitude",
                "expected": 0.0,
                "tolerance": 1e-12,  # numerical precision
                "unit": "",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP3: Scalar blind spot at different parameters (universality check)
    # ------------------------------------------------------------------
    "scalar_blind_spot_2": {
        "params": {
            "g_tilde": 3.5,
            "sin_theta": 0.5,
            "m_H2": 50.0,
            "m_V": 1000.0,
            "m_Psi": 100.0,
        },
        "checks": [
            {
                "label": "Scalar DM SI amplitude (exact zero, any params)",
                "quantity": "blind_spot_amplitude",
                "expected": 0.0,
                "tolerance": 1e-12,
                "unit": "",
            },
        ],
    },
    # ------------------------------------------------------------------
    # BP4: Large mixing, strong coupling
    # ------------------------------------------------------------------
    "strong_coupling": {
        "params": {
            "g_tilde": 5.0,
            "sin_theta": 0.5,
            "m_H2": 500.0,
            "m_V": 100.0,
            "m_Psi": 300.0,
        },
        "checks": [
            {
                "label": "Vector DM SI cross-section",
                "quantity": "sigma_SI_vector",
                "expected": None,
                "tolerance": 0.05,
                "unit": "cm^2",
            },
        ],
    },
}
