"""
Gondolo-Gelmini thermal average of <sigma v> for chi chi -> SM fermions.
arXiv:2603.23040, Eq. 21.
"""

import sys
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.special import k1 as _scipy_k1, k0 as _scipy_k0

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import M_H, M_Z, GEV_TO_CMCUBEDSEC

# Bessel functions K1, K2 for Gondolo-Gelmini kernel
def _K1(z):
    return _scipy_k1(z)

def _K2(z):
    # K2(z) = (2/z)*K1(z) + K0(z) [recursion relation]
    from scipy.special import kn
    return kn(2, z)


def gondolo_gelmini_kernel(s: float, m_chi: float, T: float, sigma_fn, sigma_kwargs: dict) -> float:
    """Gondolo-Gelmini integrand (unnormalized kernel) [cm^3/s * GeV^2].

    Corrected kernel (brainstorm N7):
      K1(sqrt(s)/T) * sqrt(s) * (s - 4*m_chi^2) * sigma(s) / (8 * m_chi^4 * T * K2^2(m_chi/T))

    Returns the kernel evaluated at a single s value.

    Args:
        s          Mandelstam s [GeV^2]
        m_chi      DM mass [GeV]
        T          temperature [GeV]
        sigma_fn   callable: sigma(s, **sigma_kwargs) -> [GeV^-2]
        sigma_kwargs  keyword arguments for sigma_fn
    Returns:
        kernel value [GeV^2 * GeV^-2] = dimensionless (integrated -> <sigma v> in cm^3/s)
    """
    s_threshold = 4.0 * m_chi**2
    if s <= s_threshold:
        return 0.0

    sqrt_s = np.sqrt(s)
    z = sqrt_s / T
    z0 = m_chi / T

    K1_val = _K1(z)
    K2_val = _K2(z0)

    if K2_val == 0.0 or K1_val == 0.0:
        return 0.0

    sigma = sigma_fn(s, **sigma_kwargs)
    kernel = K1_val * sqrt_s * (s - s_threshold) * sigma / (8.0 * m_chi**4 * T * K2_val**2)
    return kernel


def sigma_v_moller_thermal_avg(
    m_chi: float,
    x: float,
    couplings: dict,
    s_hint_points: list = None,
    sigma_fn=None,
) -> float:
    """Eq. 21. Thermally-averaged <sigma v_Moller> via Gondolo-Gelmini [cm^3/s].

    Corrected kernel (brainstorm N7):
      <sigma v> = integral_{4m^2}^{s_max} ds * K1(sqrt(s)/T) * sqrt(s) * (s-4m^2) * sigma(s)
                  / (8 m^4 T K2^2(m/T))

    Integration via scipy.integrate.quad with s_hint_points for resonance peaks.
    Upper limit: s_max = max(100*(2*m_chi)^2, 4*m_h^2).

    Upper-limit rationale (N3 fix): for m_chi~60 GeV, 100*(2m_chi)^2~1.4e6 GeV^2
    dominates 4*m_h^2~6.27e4 GeV^2; for m_chi > 1 TeV, 4*m_h^2 no longer matters
    and 100*(2*m_chi)^2 handles the suppressed tail.

    B2 fix: sigma_fn is dependency-injected from refs.py so that this function
    never does a lazy ``from cross_sections.annihilation import sigma_total``
    at call time (which fails when sys.path has been restored).  When called
    directly from test_benchmarks.py the default falls back to a local import
    that works because sys.path includes the paper dir at that point.

    Args:
        m_chi   DM mass [GeV]
        x       x = m_chi/T (freeze-out parameter, dimensionless)
        couplings  dict for sigma_total (see annihilation.py)
        s_hint_points  list of s values for quad hint (default: [m_h^2, m_Z^2])
        sigma_fn  callable sigma_total(s, m_chi, couplings) [GeV^-2]; if None,
                  imported locally from cross_sections.annihilation (works when
                  this module is loaded with the paper dir on sys.path).
    Returns:
        <sigma v> [cm^3/s]
    """
    if sigma_fn is None:
        from cross_sections.annihilation import sigma_total as sigma_fn  # type: ignore[assignment]

    if s_hint_points is None:
        s_hint_points = [M_H**2, M_Z**2]

    T = m_chi / x
    s_lower = 4.0 * m_chi**2
    s_upper = max(100.0 * (2.0 * m_chi)**2, 4.0 * M_H**2)

    def integrand(s):
        return gondolo_gelmini_kernel(
            s, m_chi, T,
            sigma_fn=sigma_fn,
            sigma_kwargs={'m_chi': m_chi, 'couplings': couplings},
        )

    # Build hint points within integration range
    points = [p for p in s_hint_points if s_lower < p < s_upper]

    result, _ = quad(
        integrand,
        s_lower,
        s_upper,
        points=points if points else None,
        limit=200,
        epsabs=1e-35,
        epsrel=1e-8,
    )

    # Convert from GeV^-2 * natural units to cm^3/s
    return float(result * GEV_TO_CMCUBEDSEC)
