"""
Integration golden test: XENON1T 2018 exclusion.

σ_SI_p = σ_SI_n = 1e-46 cm², σ_SD = 0, m_DM = 100 GeV.

Re-baselined 2026-07-11 against the Wilks-statistic driver (see
plugins/hep-ph-toolkit/skills/ddcalc/scripts/ddcalc_driver.c and
/Users/yianni/.claude/jobs/c703354a/tmp/ddcalc-pvalue-fix/HANDOFF.md). The
exclusion statistic is now the one-parameter profile-likelihood-ratio
delta_chi2 = -2 (lnL_signal - lnL_background), with p_value the chi^2_1
survival function and excluded_90cl = (p_value < 0.1) <=> (delta_chi2 > 2.706).
Values measured directly from the compiled DDCalc 2.2.0 driver at this point:

    lnL_signal = -4.397586, lnL_background = -3.650766 (background eval'd
    internally by the driver as the zero-cross-section WIMP handle),
    delta_chi2 = 1.493639, significance = 1.222145,
    p_value = erfc(sqrt(delta_chi2/2)) = 0.2216527,
    excluded_90cl = False (delta_chi2 < 2.706).

DDCalc's simplified single-bin XENON1T likelihood is ~1.7x weaker than the
observed 1t-yr result (arXiv:1805.12562): it crosses 90% CL near ~1.4e-46 cm²
at this mass vs the published ~8e-47 cm². This fixture point (1e-46 cm²) sits
below that crossing, so XENON1T_2018 alone does NOT exclude it, even though the
overall verdict is still "excluded" because LZ_projected (native, far more
sensitive at 100 GeV) does.

REQUIRES: HEPPH_RUN_NETWORK_TESTS=1 AND DDCalc installed at ddcalc_path.
(Despite the env var name, this test requires no network access — only a
local DDCalc install and a C compiler to build the driver. Gated behind the
same flag as the other integration tests for consistency and because it is
slow (compiles + links against libDDCalc.a).)
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

    def test_xenon1t_not_excluded_100gev(self):
        """σ_SI = 1e-46 cm², m_DM = 100 GeV → XENON1T_2018 alone excluded_90cl=False.

        Measured (2026-07-11) against the Wilks-statistic driver: delta_chi2 = 1.49
        (p = 0.222), below the delta_chi2 > 2.706 threshold. DDCalc's single-bin
        XENON1T model crosses 90% CL near ~1.4e-46 cm² at this mass, so 1e-46 cm² is
        not excluded by XENON1T_2018 specifically (the overall verdict is still
        "excluded" via LZ_projected — see test_verdict_excluded).
        """
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        assert result["status"] == "ok"
        xenon = result["experiments"]["XENON1T_2018"]

        assert xenon["excluded_90cl"] is False, (
            f"Expected XENON1T_2018 NOT excluded at 100 GeV/1e-46 cm²; got excluded_90cl=True"
        )

    def test_xenon1t_pvalue_measured(self):
        """p_value and delta_chi2 must match the measured golden values."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        xenon = result["experiments"]["XENON1T_2018"]
        pval = xenon.get("p_value", -1.0)
        expected = 0.2216527
        assert abs(pval - expected) / expected < 0.05, (
            f"p_value = {pval}, expected ~{expected} (±5%)"
        )
        assert 0.0 <= pval <= 1.0, f"p_value out of [0,1]: {pval}"
        # Wilks statistic goldens
        assert xenon["delta_chi2"] == pytest.approx(1.493639, rel=0.02)
        assert xenon["significance"] == pytest.approx(1.222145, rel=0.02)

    def test_xenon1t_logl_tolerance(self):
        """logL should be within ±10% of the measured value (-4.397586)."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        xenon = result["experiments"]["XENON1T_2018"]
        logL = xenon.get("logL", 0.0)
        expected = -4.397586
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
