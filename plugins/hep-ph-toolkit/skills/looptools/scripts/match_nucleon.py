"""
match_nucleon.py — loop amplitude → DM–nucleon cross-section matching.

SCOPE / PHYSICS OWNERSHIP (read before editing — see the build plan §8 dec. #4
and §9 risk #3):

  This module owns the *minimal* transport step: given the EFFECTIVE
  DM–nucleon couplings f_p, f_n (units GeV^-2) that the Wolfram/LoopTools
  driver (`run_eval.wls`) emits, it returns the standard coherent
  spin-independent (SI) cross-section per nucleon.

  The risky quark→nucleon form-factor contraction (scalar Wilson coefficients
  α_q → nucleon coupling f_N, with the default_2018 / A1 σ-term presets and
  the heavy-quark 2/27·f_TG gluon matching) is DELEGATED to the FormCalc side
  inside `run_eval.wls`, which is the right place to know the quark content and
  is exercised only by the Tier-3 smoke.  Keeping that out of Python is a
  deliberate decision: it is the one factor we cannot verify here without the
  real tools, so we do not re-derive it in code we can only fixture-test.

  The formula owned here is textbook and verifiable by hand:

      σ_SI^N = (4/π) · μ_N² · f_N²                         [natural units, GeV^-2]
      σ_SI^N [cm²] = σ_SI^N [GeV^-2] · (ħc)²

  with μ_N = m_DM·m_N/(m_DM+m_N) the DM–nucleon reduced mass.

  σ_SD is returned as None in v1 (the 2HDM+a charged-Higgs/W box yields
  predominantly SI; SD is sub-leading and is not half-validated — build plan
  §8 dec. #3).  A driver may supply f_p_sd/f_n_sd; if non-null they are matched
  with the same coherent formula and labelled provisional.

CITATIONS:
  - Coherent SI cross-section:  Jungman, Kamionkowski & Griest,
    Phys. Rept. 267 (1996) 195, Eq. (8.1)–(8.3); standard form
    σ = (4/π) μ² f²  (per-nucleon, before nuclear A² coherence which DDCalc
    applies downstream).
  - (ħc) = 0.1973269804 GeV·fm  (CODATA 2018).
"""
from __future__ import annotations

from typing import Optional

# CODATA-2018 conversion: ħc = 1.973269804e-14 GeV·cm  ⇒  1 GeV^-2 = (ħc)² cm².
HBAR_C_GEV_CM = 1.973269804e-14
GEV2_TO_CM2 = HBAR_C_GEV_CM ** 2          # 3.8937937e-28 cm² per GeV^-2

# Nucleon masses (GeV), PDG 2022.
M_PROTON_GEV = 0.93827208816
M_NEUTRON_GEV = 0.93956542052

FOUR_OVER_PI = 4.0 / 3.141592653589793


def reduced_mass(m_dm_gev: float, m_nucleon_gev: float) -> float:
    """DM–nucleon reduced mass μ = m_DM m_N / (m_DM + m_N)  [GeV]."""
    return m_dm_gev * m_nucleon_gev / (m_dm_gev + m_nucleon_gev)


def sigma_coherent_cm2(
    m_dm_gev: float,
    f_nucleon_gev_minus2: float,
    m_nucleon_gev: float,
) -> float:
    """σ = (4/π) μ² f²  in cm², from an effective DM–nucleon coupling f [GeV^-2]."""
    mu = reduced_mass(m_dm_gev, m_nucleon_gev)
    sigma_gev_minus2 = FOUR_OVER_PI * mu * mu * f_nucleon_gev_minus2 ** 2
    return sigma_gev_minus2 * GEV2_TO_CM2


def match(
    m_dm_gev: float,
    f_p_si_gev_minus2: float,
    f_n_si_gev_minus2: float,
    f_p_sd_gev_minus2: Optional[float] = None,
    f_n_sd_gev_minus2: Optional[float] = None,
) -> dict:
    """Match driver effective couplings to per-nucleon cross-sections (cm²).

    Returns a dict with the four scattering/v1 σ fields.  SD entries are always
    None in v1; supplying a non-null SD coupling raises NotImplementedError
    rather than silently mis-computing it (see below).
    """
    if m_dm_gev <= 0:
        raise ValueError(f"m_dm_gev must be > 0, got {m_dm_gev}")

    # σ_SD is null in v1 (build plan §8 dec. #3).  The coherent SI formula
    # σ = (4/π) μ² f² does NOT carry the spin-dependent structure (the SD
    # cross-section has an extra 3·(J+1)/J spin-coupling factor and a different
    # operator normalisation), so applying it to SD couplings would be silently
    # wrong.  Refuse non-null SD input rather than half-validate it.
    if f_p_sd_gev_minus2 is not None or f_n_sd_gev_minus2 is not None:
        raise NotImplementedError(
            "σ_SD matching is not implemented in v1: the coherent SI formula "
            "σ = (4/π) μ² f² is wrong for spin-dependent couplings (missing the "
            "3·(J+1)/J spin factor and the SD operator normalisation). The 2HDM+a "
            "charged-Higgs/W box is predominantly SI; v1 emits σ_SD null. Implement "
            "a dedicated SD matching (validated against the Tier-3 smoke) before "
            "passing non-null SD couplings."
        )

    return {
        "sigma_si_proton_cm2": sigma_coherent_cm2(
            m_dm_gev, f_p_si_gev_minus2, M_PROTON_GEV
        ),
        "sigma_si_neutron_cm2": sigma_coherent_cm2(
            m_dm_gev, f_n_si_gev_minus2, M_NEUTRON_GEV
        ),
        "sigma_sd_proton_cm2": None,
        "sigma_sd_neutron_cm2": None,
    }
