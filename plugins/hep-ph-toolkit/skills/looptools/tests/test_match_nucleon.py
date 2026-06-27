"""Tier-1 — match_nucleon owned physics-glue (golden numeric + properties).

The golden values are PROVISIONAL (derived from placeholder driver couplings);
they pin the textbook σ = (4/π) μ² f² transport, NOT a physics prediction.  The
Tier-3 smoke replaces the upstream couplings.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import match_nucleon as mn


def test_reduced_mass():
    mu = mn.reduced_mass(100.0, mn.M_PROTON_GEV)
    assert mu == pytest.approx(100.0 * mn.M_PROTON_GEV / (100.0 + mn.M_PROTON_GEV))


def test_golden_si_proton():
    """Independent hand-computation of σ_SI(p) for f_p=2.7e-9 GeV^-2, m_dm=100."""
    mu = 100.0 * mn.M_PROTON_GEV / (100.0 + mn.M_PROTON_GEV)
    expected = (4 / math.pi) * mu * mu * (2.7e-9) ** 2 * (1.973269804e-14) ** 2
    out = mn.match(100.0, 2.7e-9, 2.6e-9)
    assert out["sigma_si_proton_cm2"] == pytest.approx(expected, rel=1e-12)
    # Frozen golden value (regression anchor).
    assert out["sigma_si_proton_cm2"] == pytest.approx(3.1228882913186946e-45, rel=1e-9)


def test_golden_si_neutron():
    out = mn.match(100.0, 2.7e-9, 2.6e-9)
    assert out["sigma_si_neutron_cm2"] == pytest.approx(2.9037615023516756e-45, rel=1e-9)


def test_sd_null_by_default():
    out = mn.match(100.0, 2.7e-9, 2.6e-9)
    assert out["sigma_sd_proton_cm2"] is None
    assert out["sigma_sd_neutron_cm2"] is None


def test_sd_input_raises_not_implemented():
    """Non-null SD couplings must NOT be silently matched with the SI formula
    (different spin factor + operator normalisation). v1 refuses them."""
    with pytest.raises(NotImplementedError):
        mn.match(100.0, 2.7e-9, 2.6e-9, f_p_sd_gev_minus2=1.0e-9, f_n_sd_gev_minus2=1.0e-9)
    # Either nucleon supplied alone also raises.
    with pytest.raises(NotImplementedError):
        mn.match(100.0, 2.7e-9, 2.6e-9, f_p_sd_gev_minus2=1.0e-9)
    with pytest.raises(NotImplementedError):
        mn.match(100.0, 2.7e-9, 2.6e-9, f_n_sd_gev_minus2=1.0e-9)


def test_sigma_scales_as_f_squared():
    a = mn.match(100.0, 1.0e-9, 1.0e-9)["sigma_si_proton_cm2"]
    b = mn.match(100.0, 2.0e-9, 1.0e-9)["sigma_si_proton_cm2"]
    assert b == pytest.approx(4.0 * a, rel=1e-9)


def test_reduced_mass_plateau_heavy_dm():
    """For m_dm >> m_N, μ → m_N, so σ ∝ μ² saturates."""
    s1 = mn.match(1.0e4, 1.0e-9, 1.0e-9)["sigma_si_proton_cm2"]
    s2 = mn.match(1.0e6, 1.0e-9, 1.0e-9)["sigma_si_proton_cm2"]
    assert s2 == pytest.approx(s1, rel=1e-2)


def test_nonpositive_mass_raises():
    with pytest.raises(ValueError):
        mn.match(0.0, 1.0e-9, 1.0e-9)
