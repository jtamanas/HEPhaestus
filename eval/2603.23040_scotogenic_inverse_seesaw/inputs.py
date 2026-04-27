"""
Paper-specific inputs for arXiv:2603.23040 (Scotogenic Inverse Seesaw).

NuFIT convention (binding per plan §0.5.2): NuFIT 5.2 (Nov 2022), normal ordering.
Citation: I. Esteban, M.C. Gonzalez-Garcia, M. Maltoni, T. Schwetz, A. Zhou,
  NuFIT 5.2 (2022), www.nu-fit.org.

B3 FIX (Round-2): Plan §0.5.2 mandates NuFIT 5.2 as the binding default.
The Phase-1 unilateral switch to NuFIT 6.0 (detected deviations theta23 4.5%,
delta_CP 10.6%, m1 ×10) is reversed here.  NuFIT 6.0 is retained as an
alternative constant for reference; see impl-deviations.md for the full accounting
of what changed between 5.2 and 6.0 and why the plan's halt trigger would fire.
"""

import numpy as np
from numpy.typing import NDArray
from constants import DELTA_U_P, DELTA_D_P, DELTA_S_P

# ======================================================================
# NuFIT 6.0 oscillation parameters (normal ordering, NO)
# Values from paper text: sin^2 form converted to degrees
# ======================================================================
# sin^2(theta) values as given in paper
_sin2_theta12 = 0.307
_sin2_theta13 = 0.0216
_sin2_theta23 = 0.534
_delta_CP_pi  = 1.21   # delta_CP in units of pi

# Convert to degrees for NUFIT_6_0 dict
import math as _math
NUFIT_6_0 = {
    "theta12_deg": float(_math.degrees(_math.asin(_math.sqrt(_sin2_theta12)))),  # ~33.63
    "theta13_deg": float(_math.degrees(_math.asin(_math.sqrt(_sin2_theta13)))),  # ~8.47
    "theta23_deg": float(_math.degrees(_math.asin(_math.sqrt(_sin2_theta23)))),  # ~46.9
    "delta_CP_deg": float(_delta_CP_pi * 180.0),                                  # ~217.8
    "dm21_sq_eV2": 7.5e-5,    # Delta m^2_21 [eV^2]
    "dm31_sq_eV2": 2.52e-3,   # Delta m^2_31 [eV^2] = dm32 + dm21 ~ 2.45e-3 + 7.5e-5 ~ 2.525e-3
}

# Keep NUFIT_5_2 for plan-compliance reference (not used in computations)
NUFIT_5_2 = {
    "theta12_deg": 33.41,
    "theta13_deg": 8.58,
    "theta23_deg": 49.1,
    "delta_CP_deg": 197.0,
    "dm21_sq_eV2": 7.41e-5,
    "dm31_sq_eV2": 2.511e-3,
}

# B3 fix: NuFIT 5.2 is the binding default per plan §0.5.2.
NUFIT = NUFIT_5_2


def build_PMNS(nufit: dict = None) -> NDArray:
    """Build PMNS matrix from oscillation parameters.

    Uses PDG standard parameterization:
      U = R23(theta23) * diag(1,1,e^{-i delta}) * R13(theta13)
            * diag(1,1,e^{+i delta}) * R12(theta12)
    Majorana phases set to zero (R = I_3 convention).

    Returns (3,3) complex unitary matrix.
    """
    if nufit is None:
        nufit = NUFIT

    t12 = np.radians(nufit["theta12_deg"])
    t13 = np.radians(nufit["theta13_deg"])
    t23 = np.radians(nufit["theta23_deg"])
    delta = np.radians(nufit["delta_CP_deg"])

    c12 = np.cos(t12); s12 = np.sin(t12)
    c13 = np.cos(t13); s13 = np.sin(t13)
    c23 = np.cos(t23); s23 = np.sin(t23)

    eid = np.exp(1j * delta)

    # PMNS matrix in PDG convention
    U = np.array([
        [c12*c13,                   s12*c13,                   s13*np.exp(-1j*delta)],
        [-s12*c23 - c12*s23*s13*eid, c12*c23 - s12*s23*s13*eid, s23*c13              ],
        [ s12*s23 - c12*c23*s13*eid,-c12*s23 - s12*c23*s13*eid, c23*c13              ],
    ], dtype=complex)

    return U


def M_NU_DIAG_NO(m1_eV: float = 1.0e-3, nufit: dict = None) -> NDArray:
    """Neutrino mass eigenvalues for normal ordering [eV].

    Lightest-mass convention: m1 = 1e-3 eV (plan §3 Step 3 default, binding).

    B3 fix: reverted from 0.01 eV back to the plan-specified 1e-3 eV.
    The Phase-1 deviation (m1 ×10) is documented in impl-deviations.md and
    would have triggered the plan's §0.5.2 halt; it is not adopted here.

    Returns array [m1, m2, m3] in eV.
    """
    if nufit is None:
        nufit = NUFIT
    dm21 = nufit["dm21_sq_eV2"]
    dm31 = nufit["dm31_sq_eV2"]
    m1 = m1_eV
    m2 = np.sqrt(m1**2 + dm21)
    m3 = np.sqrt(m1**2 + dm31)
    return np.array([m1, m2, m3])


# Scalar triplet masses [GeV] — fixed in paper
M_PHI_TRIPLET = (1000.0, 1200.0, 1400.0)

# Velocity convention: v/c [dimensionless]
# DEVIATION NOTE: Plan specified v_rel=1e-3 as paper's benchmark.
# Paper uses this for direct detection calculations.
# If paper re-read shows different convention, re-pin T12 and T16.
V_REL_DEFAULT = 1.0e-3

# Freeze-out x = m_chi / T
X_FO_DEFAULT = 20.0

# ======================================================================
# Experimental limits (context only, not used by graders)
# ======================================================================
BR_MU_E_GAMMA_MEGII = 3.1e-13   # MEG II limit B(mu->e gamma) 90% CL
BR_H_INV_ATLAS = 0.107           # ATLAS BR(h->inv) 95% CL
# SI/SD limits at BP3 are model-dependent — not pinned here
