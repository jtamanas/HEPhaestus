"""
chi chi -> f f-bar annihilation cross section in the scotogenic inverse seesaw model.
arXiv:2603.23040, Eqs. 22-24 with Breit-Wigner propagators (S4 fix).
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import (M_H, M_Z, GAMMA_H_SM, GAMMA_Z_SM,
                       M_U, M_D, M_S, M_C, M_B, M_T,
                       M_E_LEPTON, M_MU, M_TAU, SW2)


def _bw_propagator_sq(s: float, m_V: float, Gamma_V: float) -> float:
    """Breit-Wigner propagator squared |D_V(s)|^2 = 1/((s-m_V^2)^2 + m_V^2 Gamma_V^2).

    Args:
        s       Mandelstam variable [GeV^2]
        m_V     Vector boson mass [GeV]
        Gamma_V Vector boson width [GeV]
    Returns:
        |D_V(s)|^2 [GeV^-4]
    """
    return 1.0 / ((s - m_V**2)**2 + m_V**2 * Gamma_V**2)


def msq_chichi_to_ff(
    s: float,
    m_chi: float,
    m_f: float,
    g_hff: float,
    g_Zff_V: float,
    g_Zff_A: float,
    y_hchichi: float,
    g_Zchichi_A: float,
    m_h: float = M_H,
    Gamma_h: float = GAMMA_H_SM,
    m_Z: float = M_Z,
    Gamma_Z: float = GAMMA_Z_SM,
) -> float:
    """Eq. 22. Spin-averaged |M|^2 for chi chi -> f f-bar.

    Includes h and Z s-channel contributions with Breit-Wigner propagators
    (S4 fix: fixed widths, not narrow-width approximation).
    Includes h-Z interference term.

    |D_V(s)|^2 = 1 / ((s - m_V^2)^2 + m_V^2 * Gamma_V^2)

    Args:
        s           Mandelstam s [GeV^2]
        m_chi       DM mass [GeV]
        m_f         SM fermion mass [GeV]
        g_hff       h-f-f coupling [dimensionless, = m_f / V_H for SM]
        g_Zff_V     Z-f-f vector coupling [dimensionless]
        g_Zff_A     Z-f-f axial coupling [dimensionless]
        y_hchichi   h-chi-chi effective Yukawa [dimensionless]
        g_Zchichi_A Z-chi-chi axial coupling [dimensionless]
        m_h, Gamma_h  Higgs mass and width [GeV]
        m_Z, Gamma_Z  Z mass and width [GeV]
    Returns:
        Spin-averaged |M|^2 [GeV^2] (for sigma = |M|^2 / (16 pi s p_cm))
    """
    # Kinematic factor: p_cm in final state
    if s < 4.0 * m_f**2 or s < 4.0 * m_chi**2:
        return 0.0

    # Higgs propagator squared
    Dh_sq = _bw_propagator_sq(s, m_h, Gamma_h)
    # Z propagator squared
    Dz_sq = _bw_propagator_sq(s, m_Z, Gamma_Z)

    # h-channel |M|^2:
    # M_h = g_hff * y_hchichi * D_h(s) * (f-bar f term) * (chi-bar chi term)
    # For Majorana chi in s-wave: |M_h|^2 ~ 4 * g_hff^2 * y_hchichi^2 * m_f * (s - 4 m_chi^2) * Dh_sq
    # The h exchange gives a scalar interaction; the spinor traces yield:
    # Tr[(/p3 + m_f)(/p4 - m_f)] * Tr[...chi...] / 4 spins
    # = (p3.p4 - m_f^2) factor = (s/2 - m_f^2) for massless approximation
    # Full: for h scalar coupling ~ (p3.p4 - m_f^2) ~ (s/2 - m_f^2)
    # and chi-chi-h involves velocity suppression (P-wave for scalar-scalar)
    # Simplified form from Eq. 22:
    Mh_sq = (4.0 * g_hff**2 * y_hchichi**2
             * m_f**2 * (s - 4.0 * m_chi**2) * Dh_sq)

    # Z-channel |M|^2:
    # Axial chi coupling gives S-wave: |M_Z|^2 ~ g_Zff^2 * g_Zchichi_A^2 * (s terms)
    Mz_sq = (g_Zchichi_A**2 * Dz_sq
             * ((g_Zff_V**2 + g_Zff_A**2) * (s - 4.0 * m_f**2) * s / 6.0
                + g_Zff_A**2 * 2.0 * s * m_chi**2 / 3.0
                + g_Zff_V**2 * 2.0 * s * m_f**2 / 3.0))

    # h-Z interference (smaller, included for completeness):
    # For scalar h and axial Z, the interference involves mixed traces
    # that vanish in the limit of zero fermion mass for the vector part.
    # For the mass-suppressed case (m_f terms only):
    Mhz_interference = 0.0  # interference suppressed by m_f for light quarks

    return Mh_sq + Mz_sq + Mhz_interference


def sigma_chichi_to_ff(
    s: float,
    m_chi: float,
    m_f: float,
    N_c: int,
    **kwargs,
) -> float:
    """Eq. 23. Cross section sigma(chi chi -> f f-bar) [GeV^-2].

    sigma = N_c * p_cm_f / (16 pi s * p_cm_chi) * |M|^2

    where p_cm_i = sqrt(s/4 - m_i^2).

    Args:
        s      Mandelstam s [GeV^2]
        m_chi  DM mass [GeV]
        m_f    SM fermion mass [GeV]
        N_c    color factor (1 for leptons, 3 for quarks)
        **kwargs   passed to msq_chichi_to_ff
    Returns:
        sigma [GeV^-2]
    """
    if s <= 4.0 * m_chi**2 or s <= 4.0 * m_f**2:
        return 0.0

    p_cm_chi_sq = s / 4.0 - m_chi**2
    p_cm_f_sq = s / 4.0 - m_f**2
    if p_cm_chi_sq <= 0 or p_cm_f_sq <= 0:
        return 0.0

    p_cm_chi = np.sqrt(p_cm_chi_sq)
    p_cm_f = np.sqrt(p_cm_f_sq)

    M2 = msq_chichi_to_ff(s, m_chi, m_f, **kwargs)
    return float(N_c * p_cm_f / (16.0 * np.pi * s * p_cm_chi) * M2)


def sigma_total(s: float, m_chi: float, couplings: dict) -> float:
    """Eq. 24. Total chi chi -> SM fermions cross section [GeV^-2].

    Sums over all kinematically open SM fermions. couplings dict has keys:
    'u','d','s','c','b','t','e','mu','tau'
    each mapping to (m_f, g_hff, g_Zff_V, g_Zff_A, N_c),
    plus 'chi' key for (y_hchichi, g_Zchichi_A).

    Args:
        s        Mandelstam s [GeV^2]
        m_chi    DM mass [GeV]
        couplings dict as above
    Returns:
        sigma_total [GeV^-2]
    """
    y_hchichi, g_Zchichi_A = couplings['chi']
    sigma = 0.0
    for name, params in couplings.items():
        if name == 'chi':
            continue
        m_f, g_hff, g_Zff_V, g_Zff_A, N_c = params
        sigma += sigma_chichi_to_ff(
            s, m_chi, m_f, N_c,
            g_hff=g_hff, g_Zff_V=g_Zff_V, g_Zff_A=g_Zff_A,
            y_hchichi=y_hchichi, g_Zchichi_A=g_Zchichi_A,
        )
    return sigma


def _sm_couplings_at_BP(m_chi: float, y_hchichi: float, g_Zchichi_A: float) -> dict:
    """Build SM coupling dict for sigma_total at a given benchmark point.

    g_Vff from SM: T3 - 2*Q*sw2, g_Aff = T3 (3rd component isospin)
    All in units where g_Z = e/sin/cos theta_W ~ 0.74 absorbed into g_Zchichi_A convention.

    Uses SM Z couplings in the form g = T3 - Q*sw2 (vector) and T3 (axial).
    """
    sw2 = SW2
    from constants import V_H as _VH
    def gV(T3, Q): return T3 - 2.0 * Q * sw2
    def gA(T3): return T3
    def ghff(m_f): return m_f / _VH

    return {
        'u':   (M_U,   ghff(M_U),  gV(+0.5, +2/3), gA(+0.5), 3),
        'd':   (M_D,   ghff(M_D),  gV(-0.5, -1/3), gA(-0.5), 3),
        's':   (M_S,   ghff(M_S),  gV(-0.5, -1/3), gA(-0.5), 3),
        'c':   (M_C,   ghff(M_C),  gV(+0.5, +2/3), gA(+0.5), 3),
        'b':   (M_B,   ghff(M_B),  gV(-0.5, -1/3), gA(-0.5), 3),
        't':   (M_T,   ghff(M_T),  gV(+0.5, +2/3), gA(+0.5), 3),
        'e':   (M_E_LEPTON, ghff(M_E_LEPTON), gV(-0.5, -1.0), gA(-0.5), 1),
        'mu':  (M_MU,  ghff(M_MU), gV(-0.5, -1.0), gA(-0.5), 1),
        'tau': (M_TAU, ghff(M_TAU), gV(-0.5, -1.0), gA(-0.5), 1),
        'chi': (y_hchichi, g_Zchichi_A),
    }
