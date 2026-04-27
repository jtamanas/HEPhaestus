"""test_ufo_conversion.py — integration test: UFO → CalcHEP project conversion.

GATED: requires HEPPH_RUN_NETWORK_TESTS=1 and a prior /micromegas-install run.
Tests SARAH-emitted singletDM UFO → CalcHEP project smoke.
"""
import os
import subprocess
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"
_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent / "scripts"
_UFO_TO_CALCHEP = _SCRIPTS / "ufo_to_calchep.sh"
_FIXTURES = _SCRIPT_DIR / "fixtures"


@pytest.mark.skipif(not _NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS not set")
class TestUFOConversion:
    def test_singletdm_ufo_converts(self, tmp_path):
        """SARAH-emitted singletDM UFO → CalcHEP project succeeds."""
        ufo_dir = _FIXTURES / "ufo_singletDM"
        result = subprocess.run(
            ["bash", str(_UFO_TO_CALCHEP), str(ufo_dir), "singletDM",
             "--output", str(tmp_path / "project")],
            capture_output=True, text=True,
            env={**os.environ, "HEPPH_STATE_ROOT": str(tmp_path / "state")},
        )
        assert result.returncode == 0, (
            f"ufo_to_calchep.sh failed: {result.stderr[:500]}"
        )

    def test_invalid_ufo_dir_emits_blocker(self, tmp_path):
        """Non-existent UFO dir → UFO_CONVERT_FAILED blocker."""
        import json
        result = subprocess.run(
            ["bash", str(_UFO_TO_CALCHEP), str(tmp_path / "nonexistent"), "singletDM"],
            capture_output=True, text=True,
            env={**os.environ, "HEPPH_STATE_ROOT": str(tmp_path / "state")},
        )
        assert result.returncode != 0
        for line in result.stderr.splitlines():
            if line.strip().startswith("{"):
                try:
                    b = json.loads(line)
                    assert b["code"] == "UFO_CONVERT_FAILED"
                    return
                except (json.JSONDecodeError, KeyError):
                    continue
        pytest.fail(f"No UFO_CONVERT_FAILED blocker in stderr: {result.stderr[:500]}")
