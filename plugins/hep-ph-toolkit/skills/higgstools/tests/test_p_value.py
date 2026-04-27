"""
test_p_value.py — unit tests for p_value.py.

Tests:
- (chi2=10, ndf=5) matches scipy.stats.chi2.sf to 1e-12
- p-value is in [0, 1]
- ndf from HS native output (no Python-side ndf synthesis)
"""
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@pytest.fixture
def p_value_mod():
    """Import p_value module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "p_value",
        SKILL_DIR / "scripts" / "p_value.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestPValue:
    """Test p_value.compute_p_value against scipy reference."""

    def test_chi2_10_ndf_5_matches_scipy(self, p_value_mod):
        """p_value(chi2=10, ndf=5) matches scipy.stats.chi2.sf to 1e-12."""
        import scipy.stats
        expected = scipy.stats.chi2.sf(10.0, 5)
        got = p_value_mod.compute_p_value(10.0, 5)
        assert abs(got - expected) < 1e-12, \
            f"p_value mismatch: got {got}, expected {expected}"

    def test_p_value_in_unit_interval(self, p_value_mod):
        """p_value is always in [0, 1]."""
        for chi2, ndf in [(0.1, 1), (5.0, 5), (100.0, 80), (1000.0, 100)]:
            pv = p_value_mod.compute_p_value(chi2, ndf)
            assert 0.0 <= pv <= 1.0, f"p_value out of range for chi2={chi2}, ndf={ndf}: {pv}"

    def test_zero_chi2_gives_pvalue_one(self, p_value_mod):
        """chi2=0 → p-value=1.0 (null hypothesis perfectly satisfied)."""
        pv = p_value_mod.compute_p_value(0.0, 5)
        assert abs(pv - 1.0) < 1e-12

    def test_large_chi2_gives_small_pvalue(self, p_value_mod):
        """Very large chi2 → p-value near 0."""
        pv = p_value_mod.compute_p_value(1000.0, 10)
        assert pv < 1e-10

    def test_chi2_equals_ndf_gives_near_half(self, p_value_mod):
        """chi2 near ndf → p-value near 0.5."""
        import scipy.stats
        ndf = 10
        chi2 = float(ndf)
        pv = p_value_mod.compute_p_value(chi2, ndf)
        expected = scipy.stats.chi2.sf(chi2, ndf)
        assert abs(pv - expected) < 1e-12

    def test_rates_and_masses_independently(self, p_value_mod):
        """compute_p_value called independently for rates and masses."""
        import scipy.stats
        pv_rates = p_value_mod.compute_p_value(85.0, 80)
        pv_masses = p_value_mod.compute_p_value(4.0, 5)
        assert abs(pv_rates - scipy.stats.chi2.sf(85.0, 80)) < 1e-12
        assert abs(pv_masses - scipy.stats.chi2.sf(4.0, 5)) < 1e-12
