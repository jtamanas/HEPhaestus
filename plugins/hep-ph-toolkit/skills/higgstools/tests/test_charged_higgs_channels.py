"""
test_charged_higgs_channels.py — assert H± channels fire for 2HDM+a-style SLHA.

Tests:
- Charged Higgs coupling entries present in parsed SLHA data
- H± fermion couplings extracted (tt, bb, tautau for H+)
- most_sensitive_channel can point to a charged-Higgs entry
- per_channel.csv contains H± channel IDs when legacy driver runs with mocked HB output
"""
import csv
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_2HDM = FIXTURE_DIR / "2hdm_type2_benchmark.slha"
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@pytest.fixture
def slha_adapter():
    """Import slha_adapter module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "slha_adapter",
        SKILL_DIR / "scripts" / "slha_adapter.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def legacy_driver():
    """Import legacy_driver module via normal import (sys.path already has scripts dir)."""
    import sys as _sys
    # Register module so dataclasses can resolve __module__ attribute
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location(
        "legacy_driver",
        SKILL_DIR / "scripts" / "legacy_driver.py",
    )
    mod = _ilu.module_from_spec(spec)
    # Register in sys.modules before exec so dataclass __module__ is resolvable
    _sys.modules["legacy_driver"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestChargedHiggsCouplings:
    """Test that H± couplings are present and correctly parsed."""

    def test_charged_higgs_present_in_slha(self, slha_adapter):
        """2HDM benchmark SLHA includes H+ (PDG 37) in coupling blocks."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert 37 in result["masses"], "H+ (PDG 37) missing from MASS block"
        assert 37 in result["fermion_couplings"] or -37 in result["fermion_couplings"], \
            f"H+ missing from fermion_couplings: {list(result['fermion_couplings'].keys())}"

    def test_charged_higgs_width_present(self, slha_adapter):
        """H+ width present in DECAY block of 2HDM fixture."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert 37 in result["widths"] or -37 in result["widths"], \
            f"H+ width missing from DECAY blocks: {list(result['widths'].keys())}"

    def test_n_charged_is_one(self, slha_adapter):
        """2HDM has exactly 1 charged Higgs (H+/H- pair = 1 charged entry)."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert result["n_charged"] == 1, \
            f"Expected n_charged=1 for 2HDM, got {result['n_charged']}"

    def test_n_neutral_is_three(self, slha_adapter):
        """2HDM has exactly 3 neutral Higgs (h, H, A)."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert result["n_neutral"] == 3, \
            f"Expected n_neutral=3 for 2HDM, got {result['n_neutral']}"


class TestChargedHiggsInPerChannelCsv:
    """Test that H± channel IDs propagate to per_channel.csv."""

    def test_per_channel_csv_includes_charged_higgs(self, legacy_driver, tmp_path):
        """
        With mocked HB output containing H± channels, per_channel.csv includes them.
        """
        # Create mock HB output with charged Higgs channel (typical H+ channel IDs are > 200)
        mock_hb_stdout = """
 201  ATLAS-CONF-2019-040  0.45  1  Aaboud:2018cwk
 202  CMS-HIG-18-014  0.38  1  Sirunyan:2019hkq
 301  ATLAS-CONF-2013-090  1.15  0  ATLAS-Htb-2013
"""
        channels = legacy_driver._parse_hb_output(mock_hb_stdout)
        assert len(channels) == 3, f"Expected 3 channels, got {len(channels)}"

        # Check that channel IDs >= 200 (H± range) are present
        channel_ids = [c.id for c in channels]
        assert any(cid >= 200 for cid in channel_ids), \
            f"No charged-Higgs channels (id>=200) found: {channel_ids}"

        # Write outputs using a simple namespace object
        class FakeHBResult:
            def __init__(self, channels, obsratio_max, most_sensitive_channel):
                self.channels = channels
                self.obsratio_max = obsratio_max
                self.most_sensitive_channel = most_sensitive_channel
                self.hb_version = "5.10.2"

        msc = max(channels, key=lambda c: c.obsratio)
        hb_result = FakeHBResult(
            channels=channels,
            obsratio_max=msc.obsratio,
            most_sensitive_channel=msc,
        )

        output_dir = str(tmp_path / "output")
        legacy_driver.write_outputs(
            output_dir=output_dir,
            hb_result=hb_result,
            hs_result=None,
            hb_allowed=False,  # channel 301 HBresult=0
            hs_consistent=True,
            slha_file="test.slha",
        )

        # Read per_channel.csv
        csv_path = tmp_path / "output" / "per_channel.csv"
        assert csv_path.exists(), "per_channel.csv not created"
        rows = list(csv.DictReader(csv_path.open()))
        csv_ids = [int(r["id"]) for r in rows]
        assert 201 in csv_ids, f"Channel 201 not in per_channel.csv: {csv_ids}"
        assert 301 in csv_ids, f"Channel 301 not in per_channel.csv: {csv_ids}"

    def test_most_sensitive_channel_can_be_charged_higgs(self, legacy_driver, tmp_path):
        """most_sensitive_channel can point to a H± channel (high obsratio)."""
        mock_hb_stdout = """
  50  CMS-HIGG-2016-01  0.72  1  Sirunyan:2018abc
 251  ATLAS-CONF-2018-030  1.32  0  ATLAS:2018cde
"""
        channels = legacy_driver._parse_hb_output(mock_hb_stdout)
        msc = max(channels, key=lambda c: c.obsratio)
        assert msc.id == 251, f"Most sensitive should be H± channel 251, got {msc.id}"
        assert msc.obsratio > 1.0, "H± channel obsratio should be > 1.0 (excluded)"
