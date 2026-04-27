"""test_parse_slha_mass_block.py — unit tests for parse_slha_mass_block.py."""
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from parse_slha_mass_block import SLHAParseError, read_masses, _parse_mass_block

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestReadMasses:
    def test_singletDM_fixture(self):
        masses = read_masses(_FIXTURES / "slha_singletDM.spc")
        assert 9000001 in masses
        assert abs(masses[9000001] - 100.0) < 1e-6
        assert 25 in masses
        assert abs(masses[25] - 125.0) < 1e-6

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_masses("/nonexistent/path.spc")

    def test_all_masses_positive(self):
        """read_masses returns absolute values."""
        masses = read_masses(_FIXTURES / "slha_singletDM.spc")
        for pdg, m in masses.items():
            assert m >= 0, f"Negative mass for PDG {pdg}: {m}"


class TestParseMassBlock:
    def test_standard_block(self):
        text = """
Block MASS
  25    125.0   # h
  1000022  200.0  # neutralino
"""
        masses = _parse_mass_block(text)
        assert masses[25] == 125.0
        assert masses[1000022] == 200.0

    def test_negative_mass_abs_value(self):
        text = "Block MASS\n  1000022  -200.0  # neutralino\n"
        masses = _parse_mass_block(text)
        assert masses[1000022] == 200.0

    def test_no_mass_block_raises(self):
        text = "Block SPINFO\n  1  SPheno\n"
        with pytest.raises(SLHAParseError):
            _parse_mass_block(text)

    def test_malformed_entry_raises(self):
        text = "Block MASS\n  notanint  125.0\n"
        with pytest.raises(SLHAParseError):
            _parse_mass_block(text)

    def test_comment_stripped(self):
        text = "Block MASS\n  25  125.0  # Higgs\n"
        masses = _parse_mass_block(text)
        assert 25 in masses

    def test_case_insensitive_block(self):
        text = "BLOCK mass\n  25  125.0\n"
        masses = _parse_mass_block(text)
        assert 25 in masses
