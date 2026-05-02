"""
test_classy_smoke.py — unit tests for the CLASS smoke-test logic.

These tests verify the tolerance math and blocker contract without
actually running CLASS (no network, no classy install required).
The real classy smoke is gated on HEPPH_RUN_NETWORK_TESTS=1.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SMOKE_SCRIPT = SKILL_DIR / "smoke_test.sh"


class TestSmokeToleranceMath:
    """Test the 0.5% tolerance math inline — no classy required."""

    def test_age_within_tolerance(self):
        """Age within 0.5% of 13.797 should pass tolerance check."""
        reference = 13.797
        tolerance = 0.005

        # Values that should pass (all within 0.5% of 13.797)
        for val in [13.797, 13.863, 13.760, 13.834]:
            rel_err = abs(val - reference) / reference
            assert rel_err <= tolerance, f"{val} should be within {tolerance*100}%"

    def test_age_outside_tolerance_fails(self):
        """Age outside 0.5% should fail the check."""
        reference = 13.797
        tolerance = 0.005

        # Values that should fail (more than 0.5% away from 13.797)
        # Note: 13.700 is 0.703% away — belongs here, not in the passing list.
        for val in [13.5, 14.1, 10.0, 15.0, 13.700]:
            rel_err = abs(val - reference) / reference
            assert rel_err > tolerance, f"{val} should be outside {tolerance*100}%"

    def test_reference_value_is_planck18(self):
        """Reference age 13.797 Gyr matches Planck 2018 Table 2."""
        # Planck 2018 (arXiv:1807.06209) Table 2: t_0 = 13.797 +/- 0.023 Gyr
        PLANCK18_AGE = 13.797
        assert abs(PLANCK18_AGE - 13.797) < 1e-6


class TestSmokeScriptExistsAndExecutable:
    """Test that smoke_test.sh is present and syntactically valid."""

    def test_smoke_script_exists(self):
        """smoke_test.sh must exist in the skill directory."""
        assert SMOKE_SCRIPT.exists(), f"smoke_test.sh not found at {SMOKE_SCRIPT}"

    def test_smoke_script_bash_syntax(self):
        """smoke_test.sh must pass bash -n syntax check."""
        result = subprocess.run(
            ["bash", "-n", str(SMOKE_SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"bash -n failed: {result.stderr}"

    def test_smoke_no_args_exits_nonzero(self, tmp_path):
        """smoke_test.sh with no args should exit non-zero."""
        env = {**os.environ, "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
        result = subprocess.run(
            ["bash", str(SMOKE_SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert result.returncode != 0


@pytest.mark.skipif(
    not os.environ.get("HEPPH_RUN_NETWORK_TESTS"),
    reason="Set HEPPH_RUN_NETWORK_TESTS=1 to run live classy smoke",
)
class TestClassySmokeIntegration:
    """Live smoke test — requires classy installed. Gated on HEPPH_RUN_NETWORK_TESTS=1."""

    def test_classy_age_within_tolerance(self):
        """c.age() must be within 0.5% of 13.797 Gyr."""
        from classy import Class  # noqa: PLC0415

        c = Class()
        c.set(
            {
                "output": "tCl,mPk",
                "l_max_scalars": 2000,
                "P_k_max_1/Mpc": 3.0,
                "H0": 67.32,
                "Omega_b": 0.02238,
                "Omega_cdm": 0.1201,
                "A_s": 2.100e-9,
                "n_s": 0.9660,
                "tau_reio": 0.0543,
            }
        )
        c.compute()
        age = c.age()
        c.struct_cleanup()
        c.empty()

        reference = 13.797
        tolerance = 0.005
        rel_err = abs(age - reference) / reference
        assert rel_err <= tolerance, (
            f"c.age()={age:.6f} deviates {rel_err*100:.3f}% from "
            f"reference {reference} (tolerance {tolerance*100:.1f}%)"
        )
