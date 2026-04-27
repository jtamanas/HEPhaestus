"""
Dark SU(3) gauge model.
arXiv:2506.19062, Eqs. (26)-(30).

A confining dark SU(3) gauge group is broken to SU(2) by a dark Higgs in
the fundamental representation. This produces:
  - 3 massive dark gauge bosons V^{1,2,3} (degenerate, form DM candidate)
  - 5 massless dark gauge bosons (confined, identified with dark gluons)
  - 2 scalar mass eigenstates H_1 (SM-like, 125 GeV), H_2 (dark Higgs)
  - A dark pseudoscalar Psi (second DM component)

The model has a two-component DM scenario: vector V and scalar Psi.
The scalar Psi has an EXACT blind spot (Eq. 29) — its SI cross-section
vanishes identically due to a cancellation between H_1 and H_2 exchange.

Parameters:
  g_tilde   : dark SU(3) gauge coupling
  sin_theta : scalar mixing angle (H_1-H_2)
  m_H2      : dark Higgs mass [GeV]
  m_V       : dark vector boson mass [GeV]
  m_Psi     : dark pseudoscalar mass [GeV]

Scan ranges (Eq. 30):
  g_tilde in [1e-2, 10]
  sin_theta in [1e-3, 1/sqrt(2)]
  m_H2 in [1, 1000] GeV

  Vector/vector scenario: m_Psi = 300 GeV fixed, m_V in [1, 300] GeV
  Scalar/vector scenario: m_Psi in [1, 300] GeV, m_V in [1, 1000] GeV, m_Psi < m_V
"""

import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import V_H, M_H as M_H1, M_P, reduced_mass


def vector_mass(g_tilde: float, v_dark: float) -> float:
    """
    Dark vector boson mass.

    m_V = g_tilde * v_dark / 2

    where v_dark is the dark Higgs VEV.
    """
    return g_tilde * v_dark / 2.0


def pseudoscalar_mass(g_tilde: float, v_dark: float) -> float:
    """
    Dark pseudoscalar mass.

    m_Psi = g_tilde * v_dark / (2 * sqrt(2))
    """
    return g_tilde * v_dark / (2.0 * np.sqrt(2))


def coupling_VV_Hi(g_tilde: float, m_V: float, m_Hi: float,
                   is_H1: bool, sin_theta: float) -> float:
    """
    Vector DM coupling to Higgs mass eigenstate H_i (Eq. 26, line 1).

    From the Lagrangian:
      L ⊃ (g̃ m_V / 2) (-sin θ H₁ + cos θ H₂) V_μ^a V^{μa}

    So the VV-H₁ coupling has a MINUS sign from the mixing rotation:
      g_{VV H₁} = -(g̃ m_V / 2) sin θ
      g_{VV H₂} = +(g̃ m_V / 2) cos θ
    """
    cos_theta = np.sqrt(1 - sin_theta**2)
    prefactor = g_tilde * m_V / 2.0
    if is_H1:
        return -prefactor * sin_theta  # minus sign from Eq. 26
    else:
        return prefactor * cos_theta


def coupling_PsiPsi_Hi(g_tilde: float, m_V: float, m_Hi: float,
                       is_H1: bool, sin_theta: float) -> float:
    """
    Scalar DM coupling to Higgs mass eigenstate (Eq. 28).

    g_{Psi Psi H_i} = (g_tilde / (2 * m_V^2)) * delta_i * m_{H_i}^2

    The mixing rotation is:
      H1 =  cos(theta) phi_SM - sin(theta) phi_dark
      H2 =  sin(theta) phi_SM + cos(theta) phi_dark

    The Psi coupling comes from the dark component, so:
      delta_1 = -sin(theta) for H_1
      delta_2 =  cos(theta) for H_2

    The relative minus sign is what produces the exact blind spot (Eq. 29).

    Returns
    -------
    g : float — coupling strength
    """
    cos_theta = np.sqrt(1 - sin_theta**2)
    if is_H1:
        delta = -sin_theta  # minus from rotation matrix
    else:
        delta = cos_theta
    return (g_tilde / (2.0 * m_V**2)) * delta * m_Hi**2


def sigma_SI_scalar_exact_cancellation(
    g_tilde: float, m_V: float, sin_theta: float,
    m_H2: float, m_H1: float = M_H1
) -> float:
    """
    Verify the exact blind spot for scalar DM (Eq. 29).

    sigma_{Psi p}^SI ~ |g_{Psi Psi H1} * cos(theta) / m_H1^2
                       + g_{Psi Psi H2} * sin(theta) / m_H2^2|^2

    This should be EXACTLY zero for all parameter values.

    Returns the amplitude (should be zero within numerical precision).
    """
    cos_theta = np.sqrt(1 - sin_theta**2)

    g1 = coupling_PsiPsi_Hi(g_tilde, m_V, m_H1, True, sin_theta)
    g2 = coupling_PsiPsi_Hi(g_tilde, m_V, m_H2, False, sin_theta)

    # The amplitude for SI scattering
    # H1 propagator contributes: g1 * (H1-nucleon coupling) / m_H1^2
    # H2 propagator contributes: g2 * (H2-nucleon coupling) / m_H2^2
    # H1-nucleon coupling ~ cos(theta) * m_q/v
    # H2-nucleon coupling ~ sin(theta) * m_q/v (from mixing)
    amplitude = g1 * cos_theta / m_H1**2 + g2 * sin_theta / m_H2**2

    return amplitude


def sigma_SI_vector(
    g_tilde: float, m_V: float, sin_theta: float,
    m_H2: float, m_H1: float = M_H1, m_target: float = M_P,
    f_N: float = None,
) -> float:
    """
    Tree-level SI cross-section for vector DM scattering off a nucleon.

    The vector boson V couples to nucleons through Higgs exchange (Eq. 26).
    Two diagrams: H_1 exchange (with minus sign) and H_2 exchange.

    sigma_SI = (mu^2 / pi) * (f_N * m_N / v)^2 * |A|^2

    where A = g_{VV H₁} cos θ / m²_{H₁} + g_{VV H₂} sin θ / m²_{H₂}

    Uses Hoferichter et al. (2017) nucleon form factors by default.

    Returns
    -------
    sigma_SI : float [GeV^-2]
    """
    if f_N is None:
        from constants import F_U_P, F_D_P, F_S_P
        f_TG = 1.0 - F_U_P - F_D_P - F_S_P
        f_N = F_U_P + F_D_P + F_S_P + (2.0 / 9.0) * f_TG
    cos_theta = np.sqrt(1 - sin_theta**2)
    mu = reduced_mass(m_V, m_target)

    # VV-Hi couplings (dimension: coupling * v_dark or v)
    # Higgs-nucleon: f_N * m_N / v * {cos_theta for H1, sin_theta for H2}
    # Combined amplitude
    g_V_H1 = coupling_VV_Hi(g_tilde, m_V, m_H1, True, sin_theta)
    g_V_H2 = coupling_VV_Hi(g_tilde, m_V, m_H2, False, sin_theta)

    A = (g_V_H1 * cos_theta / m_H1**2
         + g_V_H2 * sin_theta / m_H2**2)

    # Full cross-section with nucleon form factor
    sigma = (mu**2 / np.pi) * (f_N * m_target / V_H)**2 * A**2

    return sigma


def relic_density_fraction(
    m_V: float, m_Psi: float,
    omega_V: float, omega_Psi: float,
    omega_total: float = 0.12
) -> tuple[float, float]:
    """
    Relic density fractions for two-component DM.

    f_V = Omega_V / Omega_total
    f_Psi = Omega_Psi / Omega_total

    These fractions rescale the direct detection cross-section:
    effective sigma = f_i * sigma_i
    """
    f_V = omega_V / omega_total
    f_Psi = omega_Psi / omega_total
    return f_V, f_Psi


def scan_ranges_vector_vector() -> dict:
    """Scan ranges for the vector/vector scenario (Eq. 30)."""
    return {
        "g_tilde": (1e-2, 10.0),
        "sin_theta": (1e-3, 1.0 / np.sqrt(2)),
        "m_H2": (1.0, 1000.0),
        "m_V": (1.0, 300.0),
        "m_Psi": 300.0,  # fixed
    }


def scan_ranges_scalar_vector() -> dict:
    """Scan ranges for the scalar/vector scenario (Eq. 30)."""
    return {
        "g_tilde": (1e-2, 10.0),
        "sin_theta": (1e-3, 1.0 / np.sqrt(2)),
        "m_H2": (1.0, 1000.0),
        "m_V": (1.0, 1000.0),
        "m_Psi": (1.0, 300.0),  # must satisfy m_Psi < m_V
    }
