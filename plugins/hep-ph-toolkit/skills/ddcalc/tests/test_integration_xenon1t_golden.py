"""
Integration golden test: XENON1T 2018 exclusion.

σ_SI_p = σ_SI_n = 1e-46 cm², σ_SD = 0, m_DM = 100 GeV → XENON1T 2018 excluded.
Expected: excluded_90cl=True, p_value < 1e-3, logL within ±10%.

REQUIRES: HEPPH_RUN_NETWORK_TESTS=1 AND DDCalc installed at ddcalc_path.
Schema round-trip: both sigma_micromegas_sample.json and sigma_looptools_sample.json
must pass validation and produce the SAME verdict for the same physics input.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))

NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestXENON1TGolden:
    """Integration tests requiring a real DDCalc installation."""

    def _get_ddcalc_path(self) -> str:
        """Read ddcalc_path from config."""
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
        config_file = config_dir / "config.json"
        if not config_file.exists():
            pytest.skip("ddcalc_path not configured")
        with open(config_file) as f:
            path = json.load(f).get("ddcalc_path", "")
        if not path:
            pytest.skip("ddcalc_path not configured")
        return path

    def _run_ddcalc(self, sigma_json_path: str) -> dict:
        """Run the full ddcalc pipeline and return the result dict."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_ddcalc.py"), "run",
             "--sigma-json", sigma_json_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(f"run_ddcalc.py failed:\n{result.stderr}")
        return json.loads(result.stdout)

    def test_xenon1t_excluded_100gev(self):
        """σ_SI = 1e-46 cm², m_DM = 100 GeV → XENON1T 2018 excluded_90cl=True."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        assert result["status"] == "ok"
        xenon = result["experiments"]["XENON1T_2018"]

        assert xenon["excluded_90cl"] is True, (
            f"Expected XENON1T_2018 excluded at 100 GeV/1e-46 cm²; got excluded_90cl=False"
        )

    def test_xenon1t_pvalue_threshold(self):
        """p_value must be < 1e-3 for the golden point."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        xenon = result["experiments"]["XENON1T_2018"]
        pval = xenon.get("p_value", 1.0)
        assert pval < 1e-3, (
            f"Expected p_value < 1e-3 for XENON1T golden point, got {pval}"
        )

    def test_xenon1t_logl_tolerance(self):
        """logL should be within ±10% of known value (~-17.3)."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        xenon = result["experiments"]["XENON1T_2018"]
        logL = xenon.get("logL", 0.0)
        expected = -17.3
        assert abs(logL - expected) / abs(expected) < 0.10, (
            f"logL = {logL}, expected ~{expected} (±10%)"
        )

    def test_verdict_excluded(self):
        """Overall verdict must be 'excluded'."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)
        assert result["verdict"] == "excluded"

    def test_schema_round_trip_micromegas_vs_looptools(self):
        """Both source fixtures (same physics) produce identical verdicts."""
        self._get_ddcalc_path()
        # Both fixtures have same m_DM=100 GeV, sigma=1e-46 cm²
        result_mm = self._run_ddcalc(str(FIXTURES_DIR / "sigma_micromegas_sample.json"))
        result_lt = self._run_ddcalc(str(FIXTURES_DIR / "sigma_looptools_sample.json"))

        assert result_mm["verdict"] == result_lt["verdict"], (
            f"Verdict mismatch: micromegas={result_mm['verdict']}, "
            f"looptools={result_lt['verdict']}"
        )
