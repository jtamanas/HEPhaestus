"""
test_slha_adapter.py — unit tests for slha_adapter.py.

Parses the committed 2HDM Type-II benchmark SLHA fixture. Tests:
- Masses parsed correctly from Block MASS
- Coupling blocks parsed (Fermions + Bosons)
- Decay widths extracted
- Missing-blocks fatal path emits exactly one HIGGSTOOLS_SLHA_MISSING_BLOCKS blocker
"""
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_2HDM = FIXTURE_DIR / "2hdm_type2_benchmark.slha"


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


class TestSlhaAdapterParsing:
    """Test parsing of the committed 2HDM Type-II benchmark fixture."""

    def test_fixture_exists(self):
        """The committed 2HDM benchmark fixture exists."""
        assert FIXTURE_2HDM.exists(), f"Fixture missing: {FIXTURE_2HDM}"

    def test_parse_masses(self, slha_adapter):
        """Masses of all four Higgs states parsed correctly."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        masses = result["masses"]
        assert abs(masses.get(25, 0) - 125.0) < 1.0, f"h mass: {masses.get(25)}"
        assert abs(masses.get(35, 0) - 500.0) < 10.0, f"H mass: {masses.get(35)}"
        assert abs(masses.get(36, 0) - 450.0) < 10.0, f"A mass: {masses.get(36)}"
        assert abs(masses.get(37, 0) - 500.0) < 10.0, f"H+ mass: {masses.get(37)}"

    def test_parse_boson_couplings(self, slha_adapter):
        """HiggsBoundsInputHiggsCouplingsBosons block parsed."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert "boson_couplings" in result, "Missing boson_couplings in result"
        # h (pdg 25) should have near-unity WW/ZZ couplings
        h_couplings = result["boson_couplings"].get(25, {})
        assert h_couplings, f"No boson couplings for h (pdg 25): {result['boson_couplings']}"
        ww = h_couplings.get("ww", 0.0)
        assert abs(ww - 0.999) < 0.01, f"h WW coupling: {ww}"

    def test_parse_fermion_couplings(self, slha_adapter):
        """HiggsBoundsInputHiggsCouplingsFermions block parsed."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert "fermion_couplings" in result, "Missing fermion_couplings in result"
        h_fc = result["fermion_couplings"].get(25, {})
        assert h_fc, f"No fermion couplings for h: {result['fermion_couplings']}"
        bb = h_fc.get("bb", 0.0)
        assert abs(bb - 0.999) < 0.01, f"h bb coupling: {bb}"

    def test_parse_decay_widths(self, slha_adapter):
        """Decay widths extracted for neutral and charged Higgs."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert "widths" in result
        assert 25 in result["widths"], "Missing width for h (pdg 25)"
        assert 37 in result["widths"], "Missing width for H+ (pdg 37)"
        assert result["widths"][25] > 0
        assert result["widths"][37] > 0

    def test_charged_higgs_coupling_present(self, slha_adapter):
        """Charged Higgs (H+) coupling entry present for HB charged-channel use."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        # H+ (pdg 37) should have fermion coupling entries
        hp_fc = result["fermion_couplings"].get(37, {})
        assert hp_fc, f"No fermion couplings for H+ (pdg 37). fermion_couplings: {result['fermion_couplings']}"

    def test_n_neutral_n_charged_counts(self, slha_adapter):
        """n_neutral and n_charged correctly detected from coupling blocks."""
        slha_text = FIXTURE_2HDM.read_text()
        result = slha_adapter.parse_slha(slha_text)
        assert result["n_neutral"] == 3, f"Expected 3 neutral Higgs, got {result['n_neutral']}"
        assert result["n_charged"] == 1, f"Expected 1 charged Higgs, got {result['n_charged']}"


class TestSlhaAdapterMissingBlocks:
    """Test the missing-blocks fatal path."""

    def test_missing_both_blocks_raises_fatal(self, slha_adapter):
        """Both HiggsBoundsInput blocks absent → raises SlhaMissingBlocksError."""
        slha_no_hb_blocks = """
Block MASS
   25   125.0
DECAY  25  4.0e-03
    1.0  2  5  -5
"""
        with pytest.raises(slha_adapter.SlhaMissingBlocksError) as exc_info:
            slha_adapter.parse_slha(slha_no_hb_blocks)
        err = exc_info.value
        assert err.code == "HIGGSTOOLS_SLHA_MISSING_BLOCKS"
        assert "WriteHiggsBoundsBlocks" in str(err.user_instruction)

    def test_missing_blocks_error_has_user_instruction(self, slha_adapter):
        """SlhaMissingBlocksError carries actionable user_instruction."""
        slha_empty = "Block MASS\n   25   125.0\n"
        try:
            slha_adapter.parse_slha(slha_empty)
        except slha_adapter.SlhaMissingBlocksError as e:
            assert e.user_instruction, "user_instruction should not be empty"
            assert "SPheno" in e.user_instruction or "WriteHiggsBoundsBlocks" in e.user_instruction

    def test_legacy_higgsbounds_block_fallback(self, slha_adapter):
        """Legacy HiggsBounds block accepted with warning when new blocks absent."""
        slha_legacy = """
Block MASS
   25   125.0
Block HiggsBounds
   1   1.0   1.0   1.0
"""
        # Should not raise — should warn and use legacy block
        result = slha_adapter.parse_slha(slha_legacy, allow_legacy=True)
        assert result is not None
        assert result.get("used_legacy_block") is True

    def test_missing_mass_block_raises(self, slha_adapter):
        """Missing MASS block raises an appropriate error."""
        slha_no_mass = """
Block HiggsBoundsInputHiggsCouplingsBosons
   1   1   0   1   1.0   1.0   1.0   1.0   1.0
"""
        with pytest.raises(Exception):
            slha_adapter.parse_slha(slha_no_mass)


class TestCouplingBlockFormatDetection:
    """FU-wsj-01: _parse_coupling_block must handle both SPheno row-index and PDG-triplet formats."""

    # Minimal SLHA preamble shared by both tests
    _SLHA_PREFIX = """\
Block MASS
   25   125.0
   35   500.0
   36   450.0
   37   500.0
DECAY  25  4.0e-03
    1.0  2  5  -5
"""

    def test_spheno_rowindex_format_no_raise(self, slha_adapter):
        """SPheno row-index format (n_Higgs n_neutral n_charged CP vals...) must parse without error."""
        slha_spheno = self._SLHA_PREFIX + """\
Block HiggsBoundsInputHiggsCouplingsBosons
   1   1   0   1   1.00   1.00   0.00   0.00   1.00
   2   1   0   1   0.00   0.00   0.00   0.00   0.00
   3   1   0  -1   0.00   0.00   0.00   0.00   1.00
   4   0   1   1   0.00   0.00   0.00   0.00   0.00
Block HiggsBoundsInputHiggsCouplingsFermions
   1   1   0   1   1.00   1.00   1.00
   2   1   0   1   0.10   1.00   1.00
   3   1   0  -1   0.20   5.00   5.00
   4   0   1   1   0.20   5.00   5.00
"""
        result = slha_adapter.parse_slha(slha_spheno)
        assert result is not None
        assert result["boson_couplings"], "boson_couplings should not be empty"
        assert result["fermion_couplings"], "fermion_couplings should not be empty"
        # h (pdg 25) boson coupling ww should be ~1.0
        h_bc = result["boson_couplings"].get(25, {})
        assert abs(h_bc.get("ww", 0.0) - 1.00) < 0.01, f"h ww={h_bc.get('ww')}"

    def test_pdg_triplet_format_no_raise(self, slha_adapter):
        """PDG-triplet format (coupling_val nPDG PDG1 PDG2 [PDG3]) must parse without raising ValueError."""
        slha_pdg = self._SLHA_PREFIX + """\
Block HiggsBoundsInputHiggsCouplingsBosons
   1.0100   3    25    24    24
   0.0010   3    35    24    24
   0.0000   3    36    24    24
   1.0100   3    25    23    23
   0.0010   3    35    23    23
   0.0000   3    36    23    23
   0.8400   3    25    21    21
   0.0300   3    35    21    21
Block HiggsBoundsInputHiggsCouplingsFermions
   1.4200   0.0000   3    25     5     5
   94.055   0.0000   3    35     5     5
   1.0100   0.0000   3    25     6     6
   0.0133   0.0000   3    35     6     6
   1.4360   0.0000   3    25    15    15
   100.93   0.0000   3    35    15    15
"""
        # Must not raise — PDG-triplet format should be detected and parsed
        result = slha_adapter.parse_slha(slha_pdg)
        assert result is not None
        assert result["boson_couplings"] or result["fermion_couplings"], \
            "At least one coupling dict should be populated from PDG-triplet format"
        # h (pdg 25) should have ww coupling ~1.01 from the PDG-triplet block
        h_bc = result["boson_couplings"].get(25, {})
        assert "ww" in h_bc, f"h boson couplings missing 'ww'; got keys: {list(h_bc.keys())}"
        assert abs(h_bc["ww"] - 1.01) < 0.05, f"h ww={h_bc.get('ww')}"


# ---------------------------------------------------------------------------
# A3: real SPheno/SARAH build emits HiggsCouplings{Bosons,Fermions} (no
# "HiggsBoundsInput" prefix) + two-value fermion rows. The adapter must accept
# the aliased block names and parse the 2-value fermion format. Fixture is the
# verbatim SPheno.spc from the diagnosis FIXED_template run (real blocks).
# ---------------------------------------------------------------------------
FIXTURE_SD_SPHENO = FIXTURE_DIR / "singlet_doublet_spheno.slha"


class TestSingletDoubletSphenoAlias:
    def test_fixture_uses_unprefixed_block_names(self):
        text = FIXTURE_SD_SPHENO.read_text()
        assert "Block HiggsCouplingsBosons" in text
        assert "Block HiggsCouplingsFermions" in text
        # The HiggsBounds5 canonical prefix is intentionally ABSENT here — this
        # is exactly what the alias fix exists to handle.
        assert "HiggsBoundsInputHiggsCouplings" not in text

    def test_parse_does_not_raise_missing_blocks(self, slha_adapter):
        text = FIXTURE_SD_SPHENO.read_text()
        # Must NOT raise SlhaMissingBlocksError (the prereq
        # HIGGSTOOLS_SLHA_MISSING_BLOCKS gate passes).
        result = slha_adapter.parse_slha(text)
        assert result["boson_couplings"], "boson couplings not parsed via alias"

    def test_boson_couplings_extracted(self, slha_adapter):
        result = slha_adapter.parse_slha(FIXTURE_SD_SPHENO.read_text())
        h = result["boson_couplings"][25]
        assert abs(h["ww"] - 1.0) < 1e-6, h.get("ww")
        assert abs(h["aa"] - 1.0426) < 1e-3, h.get("aa")   # loop-induced gamma gamma
        assert abs(h["gg"] - 1.0218) < 1e-3, h.get("gg")   # loop-induced g g

    def test_fermion_two_value_rows_parsed(self, slha_adapter):
        """The 2-value fermion rows (scalar + pseudoscalar before ncomb) must
        parse — pre-fix they were silently dropped (int(pseudoscalar) fails)."""
        result = slha_adapter.parse_slha(FIXTURE_SD_SPHENO.read_text())
        f = result["fermion_couplings"].get(25, {})
        assert f, "fermion couplings empty — 2-value rows not parsed"
        # All tree-level fermion couplings are SM-like (1.0) in this benchmark.
        assert abs(f.get("bb", 0.0) - 1.0) < 1e-6, f
        assert abs(f.get("tt", 0.0) - 1.0) < 1e-6, f
