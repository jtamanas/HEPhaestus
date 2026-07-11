"""
Integration golden test: XENON1T 2018 exclusion.

σ_SI_p = σ_SI_n = 1e-46 cm², σ_SD = 0, m_DM = 100 GeV.

Re-baselined 2026-07-11 against the fixed driver (see
plugins/hep-ph-toolkit/skills/ddcalc/scripts/ddcalc_driver.c and
/Users/yianni/.claude/jobs/c703354a/tmp/ddcalc-diag/DIAGNOSIS.md). The prior
golden values (excluded_90cl=True, p_value < 1e-3, logL ≈ -17.3) were
hand-guessed under the same "p = exp(logL)" misconception that caused the
p-value bug itself, and never actually ran (this test only executes under
HEPPH_RUN_NETWORK_TESTS=1, so the drift went unnoticed). The values below
were measured directly by running the compiled DDCalc 2.2.0 driver at this
exact physics point:

    lnL_signal = -4.397586, lnL_background = -3.650766 (background eval'd
    internally by the driver as the zero-cross-section WIMP handle),
    p_value = exp(lnL_signal - lnL_background) = 0.4738713,
    excluded_90cl = False (p > 0.1).

DDCalc's simplified single-bin XENON1T likelihood crosses 90% CL near
~2e-46 cm² at this mass, not the real experiment's published ~4e-47 cm²
limit — this fixture point (1e-46 cm²) sits just below that crossing, so
XENON1T_2018 alone does NOT exclude it, even though the overall verdict is
still "excluded" because LZ_2022 (native, more sensitive at 100 GeV) does.

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

        Measured (2026-07-11) against the fixed likelihood-ratio driver: p = 0.474,
        well above the 0.1 threshold. DDCalc's single-bin XENON1T model crosses 90%
        CL near ~2e-46 cm² at this mass, so 1e-46 cm² is not excluded by XENON1T_2018
        specifically (the overall verdict is still "excluded" via LZ_2022 — see
        test_verdict_excluded).
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
        """p_value must match the measured golden value (0.4738713 ± 5%)."""
        self._get_ddcalc_path()
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = self._run_ddcalc(sigma_json)

        xenon = result["experiments"]["XENON1T_2018"]
        pval = xenon.get("p_value", -1.0)
        expected = 0.4738713
        assert abs(pval - expected) / expected < 0.05, (
            f"p_value = {pval}, expected ~{expected} (±5%)"
        )
        assert 0.0 <= pval <= 1.0, f"p_value out of [0,1]: {pval}"

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
