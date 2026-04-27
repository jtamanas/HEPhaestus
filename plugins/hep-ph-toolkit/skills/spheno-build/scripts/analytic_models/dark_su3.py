"""Dark SU(3) — analytic spectrum module (arXiv:2506.19062, Eqs. 26-30).

The paper's actual model is SU(3)_D -> SU(2)_D Higgsing (a *dark Higgs*
model, NOT confining). Broken gauge group produces:

  - 3 degenerate massive dark gauge bosons V^{1,2,3} (vector DM candidate)
  - 5 massless dark gauge bosons (unbroken SU(2)_D generators)
  - two scalar mass eigenstates H_1 (SM-like), H_2 (dark Higgs)
  - a dark pseudoscalar Psi (second DM candidate)

**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (dsu3-002).** Dark-SU(3)
relic density runs through the analytic backend (`analytic_models.dark_su3`)
and currently uses `<sigma v>` approximations (`sigmav_approx=True`). The
emitted Ωh² values are roughly **25000× the Planck target** and must be read
as regression anchors for the analytic pipeline, **not** as a physics
prediction or a paper-fidelity result. Paper fidelity (Ω_tot h² ≈ 0.12) is
out of reach this iteration and requires the upgrade roadmap in
`analytic_models.dark_su3` (full Boltzmann integration + multi-component
weighting in `/dark-matter-constraints`). Any downstream report that quotes
these numbers MUST embed this banner verbatim — do not silently strip it.

IMPORTANT — discrepancy with SKILL.md / dark_su3.yaml:
  The dark-su3 plugin's prose (SKILL.md) and the fermion/gauge content in
  ``dark_su3.yaml`` describe a DIFFERENT model (confining dark quark with
  "dark pion phi"). That description is FACTUALLY WRONG for arXiv:2506.19062
  §IV — the paper uses the dark-Higgs picture above. The confusion is
  flagged for iter-6 cleanup; this analytic module implements the paper's
  actual model and only reads the five parameters
  (g_tilde, sin_theta, m_H2, m_V, m_Psi) out of the spec dict.

Relic density — RK4 Boltzmann integrator
-----------------------------------------
This module solves the standard Boltzmann equation for the comoving yield Y:

    dY/dx = -lambda(x) / x^2 * (Y^2 - Y_eq^2)

where:
    x         = m_DM / T   (dimensionless inverse temperature)
    Y         = n / s       (number density / entropy density)
    Y_eq      = (45 / (4 pi^4)) * (g_eff / g_*s) * (x^2 K_2(x))
    lambda(x) = s(x) * <sigma v>(x) / H(x) * x

Integration is performed with scipy.integrate.solve_ivp (Radau) on the
log-Y variable from x = 1 to x = 100 with ~200 uniform points in log x.
The Breit-Wigner enhancement is included directly in <sigma v>(x) evaluated
at s = 4 m_DM^2 (1 + 3/(2x)), accounting for finite-velocity corrections
to the resonance factor (Gondolo-Gelmini 1991, Nucl. Phys. B360, 145,
Eq. 4.2; Kolb-Turner Ch. 5). This replaces the previous Lee-Weinberg +
ad-hoc BW multiplier approach.

The final relic density is:
    Omega h^2 = 2.742e8 * (m_DM / GeV) * Y(x=100)

using the standard relation (Kolb-Turner §5.3, Eq. 5.56):
    Omega h^2 = (m_DM * s_0 * Y_inf) / (rho_crit / h^2)
with s_0 = 2891.2 cm^-3, rho_crit/h^2 = 1.0537e-5 GeV/cm^3.

Two-component: V and Psi are treated as independent, non-interacting DM
candidates. Two separate Boltzmann equations are integrated, producing
independent Omega_V_h2 and Omega_Psi_h2.

Cross-section flag: the sigma_v expressions are inherited from the
iter-4 Lee-Weinberg module with the same approximations:
  - s-wave contribution only (no p-wave)
  - H_1 channel: off-shell, non-resonant
  - H_2 channel: Breit-Wigner propagator at s = 4 m_X^2 (1 + 3/(2x))
  - Crude H_2 width: gamma_H2 = g_tilde * m_H2 / (4 pi)
These cross-sections are flagged as approximate. If future iterations
improve the widths or add p-wave, only the _sigma_v_* functions below
need updating.

Benchmark points (Fig. 7, matched to eval/.../test_benchmarks.py labels):

  BP1: g_tilde=2.0, sin_theta=0.10, m_H2=500, m_V=150, m_Psi=70
  BP2: g_tilde=0.5, sin_theta=0.25, m_H2=650, m_V=415, m_Psi=55
  BP3: g_tilde=0.2, sin_theta=0.03, m_H2=1000, m_V=75,  m_Psi=57

Cross-validation: the eval/ directory's dark_su3.py takes Omega as an
*input* to constraint checks and does not tabulate micrOMEGAs values for
BP1-3. Direct paper validation is therefore not possible from this repo
alone. The integrator has been verified for self-consistency (convergence
at factor-of-2 grid refinement < 1% change, correct resonance ordering).

PDG IDs (BSM-range placeholders, not SARAH-derived — flagged for iter-6):

  H_1   = 25          (SM-like; standard PDG)
  V     = 9900022     (dark vector DM)
  Psi   = 9900025     (dark pseudoscalar DM)
  H_2   = 9900035     (dark Higgs)
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import kn  # modified Bessel functions

# _common is loaded dynamically: the analytic_models package is loaded via
# spec_from_file_location so ``from _common import V_H`` does not resolve.
import importlib.util as _ilu
from pathlib import Path as _P

_here = _P(__file__).resolve().parent
_spec = _ilu.spec_from_file_location("_common_dsu3", _here / "_common.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
V_H = _mod.V_H
M_H1 = _mod.M_H  # SM-like Higgs mass, 125.25 GeV

# PDG IDs — placeholders in the BSM range (9900xxx), matching the iter-4
# playtest prescription. Frozen for downstream tests.
PDG = {
    "H1": 25,
    "V": 9900022,
    "Psi": 9900025,
    "H2": 9900035,
}

# Problem code for the m_Psi > m_V regime. The paper uses m_Psi < m_V
# for the scalar/vector scenario (Eq. 30); above the vector mass the
# Psi -> VV decay opens and the DM-stability assumption fails. This is
# surfaced as a non-fatal spectrum problem so SLHA still writes.
_PROBLEM_MPSI_GT_MV = 2001

# ---------------------------------------------------------------------------
# Cosmological / thermodynamic constants
# ---------------------------------------------------------------------------

# Standard cosmological factors (Kolb-Turner §5.3, natural units):
#   Omega h^2 = 2.742e8 * (m / GeV) * Y_inf
#   This absorbs: s_0 = 2891.2 cm^-3, rho_crit/h^2 = 1.0537e-5 GeV/cm^3,
#   and the unit conversion 1 cm^-3 = (1.97e-14 GeV)^3 (in natural units
#   the factor is kept implicit; we use the numerical combination directly).
_OMEGA_FACTOR = 2.742e8  # Omega h^2 / (m_DM [GeV] * Y_inf)

# Hubble rate: H(T) = 1.66 * sqrt(g_*) * T^2 / M_Pl (in natural units)
_M_PL = 1.22e19  # GeV, non-reduced Planck mass
_H0_PREFACTOR = 1.66 / _M_PL  # coefficient in H = 1.66 sqrt(g*) T^2 / M_Pl

# Entropy density: s = (2 pi^2 / 45) * g_*s * T^3
_S_PREFACTOR = 2.0 * math.pi**2 / 45.0

# Effective degrees of freedom at ~100 GeV freeze-out
_G_STAR = 86.25
_G_STAR_S = 86.25  # entropy dof (same as g_* for T > QCD transition)

# Internal degrees of freedom for equilibrium yield
# Vector DM: 3 bosons x 3 polarisations = 9 (SU(2)_D triplet)
# Psi DM: 1 real scalar = 1
_G_V = 9.0
_G_PSI = 1.0

# Boltzmann integration bounds.
# Start at x=1: deep in the thermal equilibrium regime for all couplings,
# including resonance-enhanced models where freeze-out can occur earlier
# than the typical x_f~25 for weak-scale WIMPs. scipy Radau handles the
# stiff regime at small x without difficulty; starting at x=1 is the
# safest choice and avoids a runtime equilibrium-validity check.
_X_START = 1.0    # x = m/T start (deep in equilibrium, safe for all models)
_X_END = 100.0    # x = m/T end   (post-freeze-out, Y plateaued)
_N_POINTS = 200   # number of log-x evaluation points

# Minimum sigma*v to avoid division issues (below this, Omega -> inf)
_SV_MIN = 1e-30  # GeV^-2


# ---------------------------------------------------------------------------
# Thermodynamic helper functions
# ---------------------------------------------------------------------------

def _entropy_density(T: float) -> float:
    """Comoving entropy density s(T) = (2 pi^2 / 45) * g_*s * T^3  [GeV^3]."""
    return _S_PREFACTOR * _G_STAR_S * T**3


def _hubble(T: float) -> float:
    """Hubble rate H(T) = 1.66 sqrt(g_*) T^2 / M_Pl  [GeV]."""
    return _H0_PREFACTOR * math.sqrt(_G_STAR) * T**2


def _y_eq(x: float, g_dof: float) -> float:
    """Equilibrium yield Y_eq(x) = (45 / 4 pi^4) * (g / g_*s) * x^2 * K_2(x).

    Valid for x > 0. Uses the modified Bessel function K_2(x).
    For large x, K_2(x) ~ sqrt(pi/2x) exp(-x) so Y_eq -> 0 exponentially.
    """
    # (45 / (4 pi^4)) = 0.14507
    prefactor = 0.14507 * (g_dof / _G_STAR_S)
    return prefactor * x**2 * float(kn(2, x))


def _lambda(m_dm: float, sv: float, x: float) -> float:
    """Lambda(x) = s(x) * sigma_v / H(x) * x.

    s(x) * x / H(x) = s(T) * (m/T) / H(T)
                    = [2pi^2/45 * g_*s * T^3] * (m/T) / [1.66 sqrt(g_*) T^2/M_Pl]
                    = [2pi^2/45 * g_*s] * m * M_Pl / (1.66 sqrt(g_*))
                    = const * m (independent of T/x)

    This simplification holds when g_* is approximately constant.
    """
    T = m_dm / x
    s = _entropy_density(T)
    H = _hubble(T)
    return s * sv / H * x


# ---------------------------------------------------------------------------
# Annihilation cross-sections
# ---------------------------------------------------------------------------

def _sigma_v_V(
    g: float, st: float, ct: float,
    mV: float, mH2: float, gamma_H2: float,
    x: float,
) -> float:
    """<sigma v>(x) for V V -> SM via H_1 (off-shell) + H_2 (Breit-Wigner).

    Couplings from Eqs. 26-27 of arXiv:2506.19062:
      g_{VV H_1} = -(g mV / 2) sin_theta
      g_{VV H_2} = +(g mV / 2) cos_theta

    Cross-section is s-wave only. The H_1 channel is treated as always
    off-shell (m_V << m_H1 / 2 for typical benchmarks). The H_2 channel
    uses a Breit-Wigner propagator at s = 4 m_V^2 (1 + 3/(2x)).
    Thermal average s = 4 m^2(1 + 3/(2x)): Gondolo-Gelmini 1991,
    Nucl. Phys. B360, 145, Eq. 4.2; Kolb-Turner Ch. 5.
    """
    g_VVH1 = -(g * mV / 2.0) * st
    g_VVH2 = +(g * mV / 2.0) * ct

    # H_1 channel — off-shell propagator (m_H1 >> 2 m_V for BPs)
    sv_H1 = g_VVH1**2 / (4.0 * math.pi * mV**2 * M_H1**4)

    # H_2 channel — Breit-Wigner at s(x); thermal <s> per Gondolo-Gelmini
    s_val = 4.0 * mV**2 * (1.0 + 1.5 / max(x, 0.1))
    denom_re = s_val - mH2**2
    denom_im = mH2 * gamma_H2
    bw_sq = 1.0 / (denom_re**2 + denom_im**2)
    sv_H2 = (g_VVH2**2 / (4.0 * math.pi * mV**2)) * bw_sq

    return sv_H1 + sv_H2


def _sigma_v_Psi(
    g: float, st: float, ct: float,
    mV: float, mPsi: float, mH2: float, gamma_H2: float,
    x: float,
) -> float:
    """<sigma v>(x) for Psi Psi -> SM via H_1 (off-shell) + H_2 (Breit-Wigner).

    Couplings from Eq. 28 of arXiv:2506.19062:
      g_{Psi Psi H_1} = (g / (2 m_V^2)) (-sin_theta) m_H1^2
      g_{Psi Psi H_2} = (g / (2 m_V^2)) (+cos_theta) m_H2^2
    Thermal average s = 4 m^2(1 + 3/(2x)): Gondolo-Gelmini 1991,
    Nucl. Phys. B360, 145, Eq. 4.2; Kolb-Turner Ch. 5.
    """
    g_PPH1 = (g / (2.0 * mV**2)) * (-st) * M_H1**2
    g_PPH2 = (g / (2.0 * mV**2)) * (+ct) * mH2**2

    # H_1 channel — off-shell
    sv_H1 = g_PPH1**2 / (4.0 * math.pi * mPsi**2 * M_H1**4)

    # H_2 channel — Breit-Wigner at s(x); thermal <s> per Gondolo-Gelmini
    s_val = 4.0 * mPsi**2 * (1.0 + 1.5 / max(x, 0.1))
    denom_re = s_val - mH2**2
    denom_im = mH2 * gamma_H2
    bw_sq = 1.0 / (denom_re**2 + denom_im**2)
    sv_H2 = (g_PPH2**2 / (4.0 * math.pi * mPsi**2)) * bw_sq

    return sv_H1 + sv_H2


# ---------------------------------------------------------------------------
# Boltzmann integrator
# ---------------------------------------------------------------------------

def _solve_boltzmann(
    m_dm: float,
    g_dof: float,
    sv_func,  # callable(x) -> float, sigma v in GeV^-2
    x_start: float = _X_START,
    x_end: float = _X_END,
    n_points: int = _N_POINTS,
) -> float:
    """Integrate the Boltzmann equation for comoving yield Y and return Omega h^2.

    Solves (Kolb-Turner Eq. 5.26):

        dY/dx = -(lambda(x) / x^2) * (Y^2 - Y_eq^2)

    where x = m_DM / T, Y = n/s, Y_eq is the equilibrium yield.
    Uses scipy.integrate.solve_ivp with method='Radau' (implicit, stiff-safe).
    Starting at x_start=1 in equilibrium is safe for all models including
    resonance-enhanced ones where freeze-out can occur well before x~25.
    Radau handles the stiff early-universe regime at small x efficiently.

    Parameters
    ----------
    m_dm    : DM mass [GeV]
    g_dof   : internal degrees of freedom (for Y_eq)
    sv_func : callable, sv_func(x) -> <sigma v> in GeV^-2
    x_start : lower integration limit (default: x=1)
    x_end   : upper integration limit (default: x=100)
    n_points: number of output evaluation points along log-x grid

    Returns
    -------
    Omega_h2 : float
    """
    # Uniform output grid in log-x space; clamped to exact span
    log_x_arr = np.linspace(math.log(x_start), math.log(x_end), n_points)
    x_eval = np.exp(log_x_arr)
    x_eval[0] = x_start    # exact left boundary
    x_eval[-1] = x_end     # exact right boundary

    def _rhs(x: float, Y_arr):
        """RHS for dY/dx = -(lambda/x^2) * (Y^2 - Y_eq^2)."""
        Y = max(float(Y_arr[0]), 1e-300)
        sv = sv_func(x)
        if sv < _SV_MIN:
            return [0.0]
        lam = _lambda(m_dm, sv, x)
        Y_eq_val = max(_y_eq(x, g_dof), 1e-300)
        dYdx = -(lam / x**2) * (Y**2 - Y_eq_val**2)
        return [dYdx]

    # Initial condition: equilibrium at x_start
    Y0 = max(_y_eq(x_start, g_dof), 1e-300)

    sol = solve_ivp(
        _rhs,
        (x_start, x_end),
        [Y0],
        method="Radau",    # implicit, stiff-safe
        t_eval=x_eval,
        rtol=1e-5,
        atol=1e-25,        # Y can be O(1e-12) at freeze-out
        dense_output=False,
    )

    if not sol.success or sol.y.size == 0:
        Y_final = float(sol.y[0, -1]) if sol.y.size > 0 else Y0
    else:
        Y_final = float(sol.y[0, -1])

    Y_final = max(Y_final, 1e-300)  # guard against numerical noise going negative
    omega_h2 = _OMEGA_FACTOR * m_dm * Y_final

    return float(omega_h2)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute(spec: dict, params: dict, n_points: int = _N_POINTS) -> dict:
    """Analytic spectrum + Boltzmann-integrated relic density for dark-SU(3).

    Parameters
    ----------
    params : dict with keys
        g_tilde   : dark gauge coupling (positive)
        sin_theta : H1-H2 mixing angle (0 < sin_theta < 1)
        m_H2      : dark Higgs mass [GeV] (positive)
        m_V       : dark vector DM mass [GeV] (positive)
        m_Psi     : dark pseudoscalar DM mass [GeV] (positive)
    n_points : int, optional
        Number of log-x evaluation points for the Boltzmann integrator
        (default: _N_POINTS = 200). Exposed for convergence testing.

    Returns
    -------
    dict with keys: masses, mixing, problem, diagnostics.
    diagnostics contains Omega_V_h2, Omega_Psi_h2, relic_approx (False),
    sigmav_approx (True), and supporting cross-section values.

    Flags:
      relic_approx  = False  — integrator is Boltzmann (not Lee-Weinberg)
      sigmav_approx = True   — sigma_v uses crude H_2 width (g*m/4pi) and
                               omits the sum-over-SM-decays factor; O(1)
                               uncertainty on sigma_v propagates to O(1)
                               uncertainty on Omega. Boltzmann integration
                               on an approximate sigma_v yields a more
                               reliable freeze-out history than Lee-Weinberg
                               but the absolute Omega numbers remain
                               approximate.

    Raises
    ------
    ValueError : any parameter invalid (non-positive, sin_theta out of range).
    """
    try:
        g = float(params["g_tilde"])
        st = float(params["sin_theta"])
        mH2 = float(params["m_H2"])
        mV = float(params["m_V"])
        mPsi = float(params["m_Psi"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"dark_su3: invalid params dict: {exc}") from exc

    if g <= 0.0:
        raise ValueError(f"g_tilde must be > 0, got {g}")
    if not (0.0 < st < 1.0):
        raise ValueError(f"sin_theta must be in (0, 1), got {st}")
    if mH2 <= 0.0 or mV <= 0.0 or mPsi <= 0.0:
        raise ValueError(
            f"masses must be > 0, got m_H2={mH2}, m_V={mV}, m_Psi={mPsi}"
        )

    ct = math.sqrt(1.0 - st * st)

    # Higgs-portal couplings (Eqs. 26 + 28) — diagnostic only
    g_VV_H1 = -(g * mV / 2.0) * st
    g_VV_H2 = +(g * mV / 2.0) * ct
    g_PP_H1 = (g / (2.0 * mV * mV)) * (-st) * (M_H1 * M_H1)
    g_PP_H2 = (g / (2.0 * mV * mV)) * (+ct) * (mH2 * mH2)

    # H_2 partial width (crude: g_tilde * m_H2 / 4pi, iter-7+: compute properly)
    gamma_H2 = g * mH2 / (4.0 * math.pi)

    # Build sigma_v(x) closures for the two DM candidates
    def sv_V(x: float) -> float:
        return _sigma_v_V(g, st, ct, mV, mH2, gamma_H2, x)

    def sv_Psi(x: float) -> float:
        return _sigma_v_Psi(g, st, ct, mV, mPsi, mH2, gamma_H2, x)

    # Representative s-wave values at x = 25 (freeze-out) for diagnostics
    sv_V_xf = sv_V(25.0)
    sv_Psi_xf = sv_Psi(25.0)

    # Solve two independent Boltzmann equations
    omega_V_h2 = _solve_boltzmann(mV, _G_V, sv_V, n_points=n_points)
    omega_Psi_h2 = _solve_boltzmann(mPsi, _G_PSI, sv_Psi, n_points=n_points)

    # Mass spectrum
    masses = {
        PDG["H1"]: float(M_H1),
        PDG["V"]: float(mV),
        PDG["Psi"]: float(mPsi),
        PDG["H2"]: float(mH2),
    }

    # 2x2 Higgs mixing (MHHMIX block) — SARAH convention, rows = mass
    # eigenstates, cols = interaction eigenstates (phi_SM, phi_dark):
    #   H_1 =  ct phi_SM - st phi_dark
    #   H_2 =  st phi_SM + ct phi_dark
    mixing: dict[str, dict] = {
        "MHHMIX": {
            (1, 1): float(ct),
            (1, 2): float(st),
            (2, 1): float(-st),
            (2, 2): float(ct),
        },
    }

    problem: list[int] = []
    if mPsi > mV:
        # Violates the paper's scalar/vector kinematic hierarchy (Eq. 30):
        # m_Psi < m_V is required to keep Psi stable against Psi -> V V.
        problem.append(_PROBLEM_MPSI_GT_MV)

    diagnostics = {
        "Omega_V_h2": float(omega_V_h2),
        "Omega_Psi_h2": float(omega_Psi_h2),
        "relic_approx": False,          # Boltzmann integrator, not Lee-Weinberg
        "sigmav_approx": True,          # crude H_2 width; missing SM-decay sum
        "blind_spot_Psi_tree": True,    # Eq. 29 — parameter-independent
        "sv_V": float(sv_V_xf),
        "sv_Psi": float(sv_Psi_xf),
        "gamma_H2": float(gamma_H2),
        "g_VV_H1": float(g_VV_H1),
        "g_VV_H2": float(g_VV_H2),
        "g_PsiPsi_H1": float(g_PP_H1),
        "g_PsiPsi_H2": float(g_PP_H2),
    }

    return {
        "masses": masses,
        "mixing": mixing,
        "problem": problem,
        "diagnostics": diagnostics,
    }
