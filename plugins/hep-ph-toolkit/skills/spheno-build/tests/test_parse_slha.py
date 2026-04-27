"""
test_parse_slha.py — Unit tests for parse_slha.parse().

Covers all four fixture files:
    clean_spectrum.spc  — valid, no problems
    problem_block.spc   — Block PROBLEM code 1
    spinfo_warning.spc  — Block SPINFO item 4
    scan_recoverable_trigger.spc — deterministic recoverable trigger

Test isolation: uses HEPPH_STATE_ROOT and XDG_CONFIG_HOME per global invariant §2.3.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load parse_slha module
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_FIXTURES = _HERE / "fixtures" / "slha"


def _load_parse_slha():
    spec = importlib.util.spec_from_file_location("parse_slha", _SCRIPTS / "parse_slha.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parse_slha():
    return _load_parse_slha()


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    """Set HEPPH_STATE_ROOT and XDG_CONFIG_HOME to tmp dirs."""
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# ---------------------------------------------------------------------------
# Test: clean_spectrum.spc
# ---------------------------------------------------------------------------
class TestCleanSpectrum:
    def test_masses_non_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        assert result["masses"], "Expected non-empty masses dict"

    def test_problems_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        assert result["problems"] == [], f"Expected no problems, got {result['problems']}"

    def test_spinfo_warnings_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        assert result["spinfo_warnings"] == []

    def test_known_mass(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        # PDG 25 = Higgs, mass ~125 GeV in fixture
        assert "25" in result["masses"]
        assert abs(result["masses"]["25"] - 125.0) < 1.0

    def test_widths_present(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        assert "25" in result["widths"]

    def test_nmix_present(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "clean_spectrum.spc")
        assert "NMIX" in result["mixing"]
        nmix = result["mixing"]["NMIX"]
        assert "1" in nmix  # row 1 present


# ---------------------------------------------------------------------------
# Test: problem_block.spc
# ---------------------------------------------------------------------------
class TestProblemBlock:
    def test_problems_contains_1(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "problem_block.spc")
        assert 1 in result["problems"], f"Expected problem code 1, got {result['problems']}"

    def test_masses_non_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "problem_block.spc")
        assert result["masses"]

    def test_spinfo_warnings_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "problem_block.spc")
        assert result["spinfo_warnings"] == []

    def test_classify_spectrum_problem(self, parse_slha):
        """Caller should map problems ∩ {1,2,3} → SPHENO_SPECTRUM_PROBLEM."""
        result = parse_slha.parse(_FIXTURES / "problem_block.spc")
        assert set(result["problems"]) & {1, 2, 3}


# ---------------------------------------------------------------------------
# Test: spinfo_warning.spc (Block SPINFO item 4)
# ---------------------------------------------------------------------------
class TestSpinfoWarning:
    def test_spinfo_item_4_present(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "spinfo_warning.spc")
        assert "4" in result["spinfo"], "Expected SPINFO item 4"

    def test_spinfo_warnings_non_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "spinfo_warning.spc")
        assert result["spinfo_warnings"], "Expected non-empty spinfo_warnings"

    def test_spinfo_warning_text(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "spinfo_warning.spc")
        combined = " ".join(result["spinfo_warnings"]).lower()
        assert "rge" in combined or "converge" in combined or "reliable" in combined

    def test_masses_present(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "spinfo_warning.spc")
        assert result["masses"]

    def test_problems_empty(self, parse_slha):
        result = parse_slha.parse(_FIXTURES / "spinfo_warning.spc")
        assert result["problems"] == []


# ---------------------------------------------------------------------------
# Test: scan_recoverable_trigger.spc
# ---------------------------------------------------------------------------
class TestScanRecoverableTrigger:
    def test_problem_code_1(self, parse_slha):
        """Deterministic: this fixture always has problem code 1."""
        result = parse_slha.parse(_FIXTURES / "scan_recoverable_trigger.spc")
        assert 1 in result["problems"]

    def test_triggers_recoverable_classification(self, parse_slha):
        """Verify the caller classification logic is triggered."""
        result = parse_slha.parse(_FIXTURES / "scan_recoverable_trigger.spc")
        # Simulate caller logic: problems ∩ {1,2,3} → SPHENO_SPECTRUM_PROBLEM
        assert set(result["problems"]) & {1, 2, 3}

    def test_masses_present(self, parse_slha):
        """Fixture has masses even with Block PROBLEM (SPheno continues partially)."""
        result = parse_slha.parse(_FIXTURES / "scan_recoverable_trigger.spc")
        assert result["masses"]

    def test_spinfo_warnings_absent(self, parse_slha):
        """This fixture uses Block PROBLEM, not SPINFO 4."""
        result = parse_slha.parse(_FIXTURES / "scan_recoverable_trigger.spc")
        assert result["spinfo_warnings"] == []


# ---------------------------------------------------------------------------
# Test: return dict structure
# ---------------------------------------------------------------------------
class TestReturnStructure:
    @pytest.mark.parametrize("fixture", [
        "clean_spectrum.spc",
        "problem_block.spc",
        "spinfo_warning.spc",
        "scan_recoverable_trigger.spc",
    ])
    def test_required_keys(self, parse_slha, fixture):
        result = parse_slha.parse(_FIXTURES / fixture)
        required = {"masses", "widths", "problems", "mixing", "spinfo", "spinfo_warnings"}
        assert required <= set(result.keys()), (
            f"Missing keys in {fixture}: {required - set(result.keys())}"
        )

    @pytest.mark.parametrize("fixture", [
        "clean_spectrum.spc",
        "problem_block.spc",
        "spinfo_warning.spc",
        "scan_recoverable_trigger.spc",
    ])
    def test_problems_is_list_of_int(self, parse_slha, fixture):
        result = parse_slha.parse(_FIXTURES / fixture)
        assert isinstance(result["problems"], list)
        for p in result["problems"]:
            assert isinstance(p, int), f"Problem code {p!r} is not int"

    @pytest.mark.parametrize("fixture", [
        "clean_spectrum.spc",
        "problem_block.spc",
        "spinfo_warning.spc",
        "scan_recoverable_trigger.spc",
    ])
    def test_spinfo_warnings_is_list_of_str(self, parse_slha, fixture):
        result = parse_slha.parse(_FIXTURES / fixture)
        assert isinstance(result["spinfo_warnings"], list)
        for w in result["spinfo_warnings"]:
            assert isinstance(w, str)


# ---------------------------------------------------------------------------
# Test: SARAH-style mixing block names (ZNMIX / UMMIX / UPMIX) — WS-A
# ---------------------------------------------------------------------------
class TestSarahMixingBlockNames:
    """SARAH writes ZNMIX/UMMIX/UPMIX instead of SLHA-standard NMIX/UMIX/VMIX.
    The analytic backend emits the SARAH names; parse_slha.py must accept them.
    """

    def _make_slha(self, tmp_path, extra_block: str):
        text = (
            "Block MASS\n"
            "    25   1.250E+02  # h\n"
            + extra_block
        )
        p = tmp_path / "mix.spc"
        p.write_text(text)
        return p

    def test_znmix_parsed_as_2index_grid(self, parse_slha, tmp_path):
        spc = self._make_slha(tmp_path,
            "Block ZNMIX\n"
            "   1 1   0.5\n"
            "   1 2   0.8660254\n"
            "   2 1  -0.8660254\n"
            "   2 2   0.5\n"
        )
        r = parse_slha.parse(spc)
        assert "ZNMIX" in r["mixing"]
        assert r["mixing"]["ZNMIX"]["1"]["1"] == 0.5
        assert abs(r["mixing"]["ZNMIX"]["2"]["1"] + 0.8660254) < 1e-9

    def test_ummix_1x1(self, parse_slha, tmp_path):
        spc = self._make_slha(tmp_path,
            "Block UMMIX\n"
            "   1 1   1.0\n"
        )
        r = parse_slha.parse(spc)
        assert r["mixing"]["UMMIX"]["1"]["1"] == 1.0

    def test_upmix_1x1(self, parse_slha, tmp_path):
        spc = self._make_slha(tmp_path,
            "Block UPMIX\n"
            "   1 1   1.0\n"
        )
        r = parse_slha.parse(spc)
        assert r["mixing"]["UPMIX"]["1"]["1"] == 1.0
