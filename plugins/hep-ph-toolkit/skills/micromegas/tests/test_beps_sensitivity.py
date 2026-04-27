"""test_beps_sensitivity.py — test Beps coannihilation sensitivity probe.

Mocked run_point returns Ωh² differing >20% between Beps values → RELIC_BEPS_SENSITIVE.
"""
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from run_point import run_beps_probe


class TestBepsSensitivity:
    def test_large_diff_triggers_blocker(self):
        """25% relative difference between Beps=1e-4 and 1e-6 → RELIC_BEPS_SENSITIVE."""
        omega_fine = 0.120    # Beps=1e-6
        omega_coarse = 0.150  # Beps=1e-4, 25% larger

        result = run_beps_probe(omega_fine, omega_coarse)
        assert result is not None, "Expected RELIC_BEPS_SENSITIVE for 25% diff"
        assert result["blocker_code"] == "RELIC_BEPS_SENSITIVE"
        assert result["mode"] == "recoverable"
        assert result["rel_diff"] > 0.20

    def test_small_diff_ok(self):
        """5% relative difference → no blocker."""
        omega_fine = 0.120
        omega_coarse = 0.126  # 5% larger

        result = run_beps_probe(omega_fine, omega_coarse)
        assert result is None, f"Unexpected blocker for small diff: {result}"

    def test_exactly_20_percent_ok(self):
        """Exactly 20% → boundary: should not trigger (>20% threshold)."""
        omega_fine = 0.100
        omega_coarse = 0.120  # exactly 20%

        result = run_beps_probe(omega_fine, omega_coarse)
        assert result is None, f"20% should not trigger RELIC_BEPS_SENSITIVE: {result}"

    def test_none_omega_fine_ok(self):
        """None omega_fine → no probe (can't compute)."""
        result = run_beps_probe(None, 0.120)
        assert result is None

    def test_none_omega_coarse_ok(self):
        """None omega_coarse → no probe."""
        result = run_beps_probe(0.120, None)
        assert result is None

    def test_negative_omega_ok(self):
        """Negative omega → no probe (unconverged)."""
        result = run_beps_probe(-0.1, 0.120)
        assert result is None

    def test_beps_sensitivity_info_in_result(self):
        """Result dict includes omega values and rel_diff."""
        omega_fine = 0.100
        omega_coarse = 0.200  # 100% diff

        result = run_beps_probe(omega_fine, omega_coarse)
        assert result is not None
        assert "omega_h2_fine" in result
        assert "omega_h2_coarse" in result
        assert "rel_diff" in result
        assert result["omega_h2_fine"] == omega_fine
        assert result["omega_h2_coarse"] == omega_coarse
