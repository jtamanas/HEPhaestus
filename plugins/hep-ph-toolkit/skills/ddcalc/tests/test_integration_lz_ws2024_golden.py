"""
Integration golden test: LZ WS2024 exclusion.

σ_SI = 1e-46 cm², m_DM = 100 GeV → LZ WS2024 excluded_90cl=True, p_value < 1e-6.

REQUIRES: HEPPH_RUN_NETWORK_TESTS=1 AND overlay 'lz_xenonnt_pandax4t_2024' installed.
SKIPS with reason="native-only v1" when no overlay is configured (Step 0 decision).
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


def _get_experiment_set() -> str:
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if not config_file.exists():
        return "native"
    try:
        with open(config_file) as f:
            return json.load(f).get("ddcalc_experiment_set", "native") or "native"
    except Exception:
        return "native"


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestLZWS2024Golden:
    """Integration tests for LZ WS2024 overlay (skipped in native-only v1)."""

    def test_lz_ws2024_skipped_without_overlay(self):
        """In native-only v1, this test class is skipped."""
        exp_set = _get_experiment_set()
        if exp_set == "native" or "lz" not in exp_set.lower():
            pytest.skip("native-only v1: LZ WS2024 overlay not installed")
        # If overlay is present, the test below should run instead.

    @pytest.mark.skipif(
        _get_experiment_set() == "native",
        reason="native-only v1: LZ WS2024 overlay not installed",
    )
    def test_lz_ws2024_excluded_100gev(self):
        """
        With LZ WS2024 overlay: σ_SI = 1e-46 cm², m_DM = 100 GeV
        → LZ_WS2024 excluded_90cl=True, p_value < 1e-6.
        """
        sigma_json = str(FIXTURES_DIR / "sigma_micromegas_sample.json")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_ddcalc.py"), "run",
             "--sigma-json", sigma_json],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(f"run_ddcalc.py failed:\n{result.stderr}")

        output = json.loads(result.stdout)
        assert "LZ_WS2024" in output["experiments"], (
            "LZ_WS2024 not in experiments — overlay may not be applied"
        )
        lz = output["experiments"]["LZ_WS2024"]
        assert lz["excluded_90cl"] is True
        assert lz["p_value"] < 1e-6, (
            f"Expected p_value < 1e-6 for LZ golden point, got {lz['p_value']}"
        )
