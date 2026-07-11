"""
Unit test: _parse_driver_stdout.py against captured fixture.
"""
from pathlib import Path
import sys
import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))
from _parse_driver_stdout import parse_driver_stdout  # noqa: E402


FIXTURE_FILE = FIXTURES_DIR / "driver_stdout_xenon1t.txt"


class TestParseDriverStdout:
    def test_fixture_parses_ok(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        assert result["status"] == "ok"
        assert result["ddcalc_version"] == "2.2.0"

    def test_xenon1t_experiment_present(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        assert "XENON1T_2018" in result["experiments"]

    def test_xenon1t_excluded(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        exp = result["experiments"]["XENON1T_2018"]
        assert exp["excluded_90cl"] is True
        assert exp["logL"] == pytest.approx(-27.40538, rel=1e-3)
        # New Wilks fields (fixture regenerated from the real driver, m=100 GeV,
        # sigma_SI = 1e-45 cm^2): p = erfc(sqrt(delta_chi2/2)).
        assert exp["delta_chi2"] == pytest.approx(47.50922, rel=1e-3)
        assert exp["significance"] == pytest.approx(6.892693, rel=1e-3)
        assert exp["p_value"] == pytest.approx(5.47e-12, rel=0.05)

    def test_delta_chi2_finite_where_pvalue_underflows(self):
        """LZ_projected at this point underflows PVALUE to a hard 0.0, but
        delta_chi2 stays finite — the property that makes limit bisection
        (which must bracket on delta_chi2, never p) robust."""
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        lz = result["experiments"]["LZ_projected"]
        assert lz["p_value"] == 0.0
        assert lz["delta_chi2"] == pytest.approx(2033.188, rel=1e-3)
        assert lz["excluded_90cl"] is True

    def test_pico_not_excluded(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        pico = result["experiments"]["PICO_60_2019"]
        assert pico["excluded_90cl"] is False
        assert pico["delta_chi2"] == 0.0

    def test_all_six_experiments_parsed(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        expected = {"XENON1T_2018", "LUX_2016", "PandaX_2017", "PICO_60_2019",
                    "DarkSide_50", "LZ_projected"}
        assert set(result["experiments"].keys()) == expected

    def test_missing_status_raises(self):
        bad_text = "EXPERIMENT: X\nLOGL: -1.0\nPVALUE: 0.5\nEXCLUDED90: 0\n---\n"
        with pytest.raises(ValueError, match="STATUS"):
            parse_driver_stdout(bad_text)

    def test_excluded_90cl_is_bool(self):
        text = FIXTURE_FILE.read_text()
        result = parse_driver_stdout(text)
        for name, exp in result["experiments"].items():
            assert isinstance(exp["excluded_90cl"], bool), (
                f"excluded_90cl for {name} should be bool, got {type(exp['excluded_90cl'])}"
            )
