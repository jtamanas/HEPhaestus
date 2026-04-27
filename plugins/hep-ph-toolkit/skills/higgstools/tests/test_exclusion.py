"""
test_exclusion.py — unit tests for exclusion.py.

Tests:
- hb_allowed = AND of per-channel HBresult (all pass, one fails)
- hs_consistent = Δχ² threshold edge cases
- --delta-chi2 override
"""
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@pytest.fixture
def exclusion():
    """Import exclusion module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "exclusion",
        SKILL_DIR / "scripts" / "exclusion.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@dataclass
class FakeChannel:
    id: int
    expref: str
    obsratio: float
    hb_result: int
    reference: str = ""


class TestHbAllowed:
    """Test hb_allowed = AND of per-channel HBresult."""

    def test_all_channels_pass(self, exclusion):
        """All channels HBresult=1 → hb_allowed=True."""
        channels = [
            FakeChannel(1, "ATLAS-A", 0.5, 1),
            FakeChannel(2, "CMS-B", 0.7, 1),
            FakeChannel(3, "ATLAS-C", 0.3, 1),
        ]
        assert exclusion.compute_hb_allowed(channels) is True

    def test_one_channel_fails(self, exclusion):
        """One channel HBresult=0 → hb_allowed=False (AND semantics)."""
        channels = [
            FakeChannel(1, "ATLAS-A", 0.5, 1),
            FakeChannel(2, "CMS-B", 1.2, 0),   # excluded
            FakeChannel(3, "ATLAS-C", 0.3, 1),
        ]
        assert exclusion.compute_hb_allowed(channels) is False

    def test_empty_channel_list(self, exclusion):
        """Empty channel list → hb_allowed=True (vacuously true)."""
        assert exclusion.compute_hb_allowed([]) is True

    def test_all_channels_excluded(self, exclusion):
        """All channels HBresult=0 → hb_allowed=False."""
        channels = [
            FakeChannel(1, "ATLAS-A", 1.5, 0),
            FakeChannel(2, "CMS-B", 2.0, 0),
        ]
        assert exclusion.compute_hb_allowed(channels) is False

    def test_single_channel_pass(self, exclusion):
        """Single channel passing → True."""
        assert exclusion.compute_hb_allowed([FakeChannel(1, "X", 0.9, 1)]) is True

    def test_single_channel_fail(self, exclusion):
        """Single channel failing → False."""
        assert exclusion.compute_hb_allowed([FakeChannel(1, "X", 1.1, 0)]) is False

    def test_obsratio_above_one_but_hb_result_one(self, exclusion):
        """obsratio > 1 but HBresult=1 (tool decided not excluded) → True."""
        # This tests that we use HBresult, not obsratio directly
        channels = [FakeChannel(1, "X", 1.05, 1)]  # HB tool says allowed
        assert exclusion.compute_hb_allowed(channels) is True


class TestHsConsistent:
    """Test hs_consistent = Δχ² vs cached SM ref < threshold."""

    def test_consistent_below_threshold(self, exclusion):
        """chi2_total - chi2_sm_ref < 6.18 → hs_consistent=True."""
        assert exclusion.compute_hs_consistent(
            chi2_total=90.0, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is True

    def test_inconsistent_above_threshold(self, exclusion):
        """chi2_total - chi2_sm_ref > 6.18 → hs_consistent=False."""
        assert exclusion.compute_hs_consistent(
            chi2_total=95.0, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is False

    def test_exactly_at_threshold(self, exclusion):
        """chi2_total - chi2_sm_ref == 6.18 → hs_consistent=False (strict <)."""
        assert exclusion.compute_hs_consistent(
            chi2_total=91.18, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is False

    def test_just_below_threshold(self, exclusion):
        """chi2_total - chi2_sm_ref = 6.17 → True."""
        assert exclusion.compute_hs_consistent(
            chi2_total=91.17, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is True

    def test_custom_delta_chi2(self, exclusion):
        """--delta-chi2 override changes threshold."""
        # With delta=2.30 (1D 90% CL), more restrictive
        assert exclusion.compute_hs_consistent(
            chi2_total=88.0, chi2_sm_ref=85.0, delta_chi2=2.30
        ) is False  # 3.0 > 2.30
        # With delta=11.83 (2D 99.7% CL), more permissive
        assert exclusion.compute_hs_consistent(
            chi2_total=96.0, chi2_sm_ref=85.0, delta_chi2=11.83
        ) is True  # 11.0 < 11.83

    def test_sm_ref_exactly_matches(self, exclusion):
        """chi2_total == chi2_sm_ref → Δχ²=0 → True."""
        assert exclusion.compute_hs_consistent(
            chi2_total=85.0, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is True

    def test_chi2_below_sm_ref(self, exclusion):
        """chi2_total < chi2_sm_ref (better than SM) → True."""
        assert exclusion.compute_hs_consistent(
            chi2_total=80.0, chi2_sm_ref=85.0, delta_chi2=6.18
        ) is True
